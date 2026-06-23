$ErrorActionPreference = "Stop"

$Root = (Resolve-Path "$PSScriptRoot\..").Path
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Tokenizer = Join-Path $Root "pretrained_models\OmniVoice\audio_tokenizer"
$DataRoot = Join-Path $Root "data\genshin_20_speakers"

Set-Location $Root
& $Python (Join-Path $PSScriptRoot "prepare_genshin_20_speakers_finetune.py")
if ($LASTEXITCODE -ne 0) { throw "Failed to select 20-speaker data." }

foreach ($Split in @("train", "dev")) {
    $Manifest = Join-Path $DataRoot "manifests\$Split.jsonl"
    $TokenRoot = "data/genshin_20_speakers/tokens/$Split"
    New-Item -ItemType Directory -Force -Path $TokenRoot | Out-Null

    & $Python -m omnivoice.scripts.extract_audio_tokens `
        --input_jsonl $Manifest `
        --tar_output_pattern "$TokenRoot/audios/shard-%06d.tar" `
        --jsonl_output_pattern "$TokenRoot/txts/shard-%06d.jsonl" `
        --tokenizer_path $Tokenizer `
        --nj_per_gpu 1 `
        --loader_workers 0 `
        --samples_per_shard 100 `
        --min_num_shards 1 `
        --shuffle True `
        --shuffle-seed 42
    if ($LASTEXITCODE -ne 0) { throw "Failed to tokenize $Split data." }

    & (Join-Path $PSScriptRoot "normalize_webdataset_manifests.ps1") `
        -ManifestPath (Join-Path $DataRoot "tokens\$Split\data.lst") `
        -ProjectRoot $Root
}
