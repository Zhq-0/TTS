$ErrorActionPreference = "Stop"

$Root = (Resolve-Path "$PSScriptRoot\..\..\..").Path
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$ModelDir = Join-Path $Root "pretrained_models\Fun-CosyVoice3-0.5B"
$SourceDataDir = Join-Path $Root "examples\genshin_voice\cosyvoice2\data\four_characters"
$TargetDataDir = Join-Path $PSScriptRoot "data\four_characters"
$InstructText = "You are a helpful assistant.<|endofprompt|>"

if (-not (Test-Path $Python)) {
  throw "Python environment not found: $Python"
}
if (-not (Test-Path "$ModelDir\speech_tokenizer_v3.onnx")) {
  throw "CosyVoice3 speech tokenizer not found: $ModelDir\speech_tokenizer_v3.onnx"
}

function Copy-CleanSplit {
  param(
    [string]$Split
  )

  $Source = Join-Path $SourceDataDir $Split
  $Target = Join-Path $TargetDataDir $Split
  if (-not (Test-Path "$Source\wav.scp")) {
    throw "Source split missing: $Source"
  }

  New-Item -ItemType Directory -Force -Path $Target | Out-Null
  foreach ($Name in @("wav.scp", "text", "utt2spk", "spk2utt", "utt2embedding.pt", "spk2embedding.pt")) {
    Copy-Item -LiteralPath (Join-Path $Source $Name) -Destination (Join-Path $Target $Name) -Force
  }

  $InstructPath = Join-Path $Target "instruct"
  $InstructLines = Get-Content -LiteralPath (Join-Path $Target "text") -Encoding UTF8 | ForEach-Object {
    $SpaceIndex = $_.IndexOf(" ")
    if ($SpaceIndex -le 0) {
      throw "Invalid text line without utterance id: $_"
    }
    $Utt = $_.Substring(0, $SpaceIndex)
    "$Utt $InstructText"
  }
  $Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllLines($InstructPath, [string[]]$InstructLines, $Utf8NoBom)

  if (-not (Test-Path "$Target\utt2speech_token.pt")) {
    & $Python "$Root\tools\extract_speech_token.py" `
      --dir $Target `
      --onnx_path "$ModelDir\speech_tokenizer_v3.onnx" `
      --num_thread 4
    if ($LASTEXITCODE -ne 0) { throw "CosyVoice3 speech token extraction failed for $Split" }
  } else {
    Write-Host "Reuse existing CosyVoice3 speech tokens for $Split"
  }

  $ParquetDir = Join-Path $Target "parquet"
  New-Item -ItemType Directory -Force -Path $ParquetDir | Out-Null
  $ResolvedParquetDir = (Resolve-Path $ParquetDir).Path
  $ResolvedTargetDataDir = (Resolve-Path $TargetDataDir).Path
  if (-not $ResolvedParquetDir.StartsWith($ResolvedTargetDataDir, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Refuse to clean unexpected parquet directory: $ResolvedParquetDir"
  }
  Get-ChildItem -LiteralPath $ParquetDir -Force | Remove-Item -Recurse -Force
  & $Python "$Root\tools\make_parquet_list.py" `
    --num_utts_per_parquet 100 `
    --num_processes 1 `
    --src_dir $Target `
    --des_dir $ParquetDir
  if ($LASTEXITCODE -ne 0) { throw "Parquet creation failed for $Split" }
}

$env:PYTHONPATH = "$Root;$Root\third_party\Matcha-TTS"
Copy-CleanSplit -Split "train_clean"
Copy-CleanSplit -Split "dev_clean"

Write-Host "CosyVoice3 data prepared under $TargetDataDir"
