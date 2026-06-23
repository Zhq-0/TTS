$ErrorActionPreference = "Stop"

$Root = (Resolve-Path "$PSScriptRoot\..\..\..").Path
$PythonDir = Join-Path $Root ".venv\Scripts"
$ModelDir = Join-Path $Root "pretrained_models\Fun-CosyVoice3-0.5B"
$DataDir = Join-Path $PSScriptRoot "data\four_characters"
$CleanTrainDir = Join-Path $DataDir "train_clean"
$CleanDevDir = Join-Path $DataDir "dev_clean"
$OutputDir = Join-Path $PSScriptRoot "exp\four_characters_llm_clean_3epoch"
$TensorboardDir = Join-Path $PSScriptRoot "tensorboard\four_characters_llm_clean_3epoch"

if (-not (Test-Path "$CleanTrainDir\parquet\data.list")) {
  throw "CosyVoice3 clean training data is missing. Run prepare_data.ps1 first."
}
if (-not (Test-Path "$CleanDevDir\parquet\data.list")) {
  throw "CosyVoice3 clean validation data is missing. Run prepare_data.ps1 first."
}

$env:PYTHONPATH = "$Root;$Root\third_party\Matcha-TTS"
$env:OMP_NUM_THREADS = "1"
$env:COSYVOICE_DDP_FIND_UNUSED_PARAMETERS = "false"
$env:COSYVOICE_DDP_GRADIENT_AS_BUCKET_VIEW = "true"

& "$PythonDir\torchrun.exe" --standalone --nproc_per_node=1 `
  "$Root\cosyvoice\bin\train.py" `
  --train_engine torch_ddp `
  --config "$PSScriptRoot\conf\cosyvoice3_four_characters.yaml" `
  --train_data "$CleanTrainDir\parquet\data.list" `
  --cv_data "$CleanDevDir\parquet\data.list" `
  --qwen_pretrain_path "$ModelDir\CosyVoice-BlankEN" `
  --onnx_path $ModelDir `
  --model llm `
  --checkpoint "$ModelDir\llm.pt" `
  --model_dir $OutputDir `
  --tensorboard_dir $TensorboardDir `
  --ddp.dist_backend gloo `
  --num_workers 0 `
  --prefetch 2 `
  --timeout 300 `
  --use_amp
if ($LASTEXITCODE -ne 0) { throw "CosyVoice3 clean-data LLM training failed" }
