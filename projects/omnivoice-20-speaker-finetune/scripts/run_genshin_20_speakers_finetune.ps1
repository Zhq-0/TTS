$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Accelerate = Join-Path $ProjectRoot ".venv\Scripts\accelerate.exe"

$env:HF_HUB_OFFLINE = "1"
$env:TRANSFORMERS_OFFLINE = "1"

Set-Location $ProjectRoot
& $Accelerate launch `
    --gpu_ids 0 `
    --num_processes 1 `
    -m omnivoice.cli.train `
    --train_config configs/genshin_20_speakers_finetune_sdpa.json `
    --data_config configs/genshin_20_speakers_data.json `
    --output_dir exp/genshin_20_speakers_1200_sdpa

if ($LASTEXITCODE -ne 0) {
    throw "Genshin 20-speaker fine-tuning failed."
}
