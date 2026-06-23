# dots.tts-soar Genshin 20 Speakers 350-shot LoRA 1000-step

## Data

- Dataset: `genshin_20_speakers_high_quality_350shot`
- Speakers: 20
- Per speaker: 350 train + 35 validation
- Train: 7000 samples, 9.791 hours
- Validation: 700 samples, 1.115 hours
- Selection: strict quality ranking first; ranked fallback was used for Kaedehara Kazuha and Gorou.

## Training Setup

- Base model: `rednote-hilab/dots.tts-soar`
- Pretrained path: `<HF_CACHE_DIR>/models--rednote-hilab--dots.tts-soar/snapshots/e3520f75254d0020a0406db31c51a79d00d22d55`
- Trainable method: LoRA only
- LoRA modules: `core.llm`, `core.velocity_field_predictor`
- LoRA targets: `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`, `fc1`, `fc2`
- LoRA rank / alpha / dropout: 8 / 16.0 / 0.05
- Trainable parameters: 11,886,592 / 2,398,021,214
- Max train steps: 1000
- Learning rate: 3e-6, cosine schedule with 50 warmup steps
- Micro-batch limit: 8.0 seconds audio, 768 text tokens

## Checkpoints

- Run dir: `runs/dots_tts_soar_genshin_20spk_350shot_lora_1000step`
- Kept checkpoints:
  - `checkpoint-00000500`
  - `checkpoint-00000750`
  - `checkpoint-00001000`
- Logs:
  - `train_soar_lora_1000step_stdout.log`
  - `train_soar_lora_1000step_stderr.log`

## Validation

| Step | validation loss | fm loss | eos loss | Note |
|---:|---:|---:|---:|---|
| 250 | 0.8063 | 0.7813 | 0.0250 | first checkpoint, later removed by retention |
| 500 | 0.6975 | 0.6719 | 0.0256 | best validation loss among kept checkpoints |
| 750 | 0.7466 | 0.7207 | 0.0259 | stable but worse than step 500 |
| 1000 | 1.0180 | 0.9923 | 0.0256 | final checkpoint, validation regressed |

## Notes

- Training completed without OOM.
- Observed GPU memory during training was about 16.7 GB to 21.7 GB while other Python GPU processes remained running.
- Some samples longer than the 8-second micro-batch limit were skipped by the batcher. This was intentional for this smoke test to keep memory stable.
- Next evaluation should compare both `checkpoint-00000500` and `checkpoint-00001000` against the pretrained SOAR baseline; do not assume the final checkpoint is the best.
