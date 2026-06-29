$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

$env:HF_HUB_OFFLINE = "1"
$env:TRANSFORMERS_OFFLINE = "1"

Set-Location $ProjectRoot

& $Python scripts\prepare_genshin_20_speakers_extended_text_cases.py
if ($LASTEXITCODE -ne 0) {
    throw "Preparing extended text cases failed."
}

& $Python scripts\run_genshin_20_speakers_extended_text_comparison.py
if ($LASTEXITCODE -ne 0) {
    throw "Generating extended text comparison audio failed."
}

& $Python scripts\evaluate_genshin_20_speakers_extended_text_comparison.py
if ($LASTEXITCODE -ne 0) {
    throw "Evaluating extended text comparison failed."
}
