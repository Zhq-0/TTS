# Genshin 20 Speakers 350-shot dots.tts fine-tune

## Data

- Speakers: 20
- Train: 7000 samples, 9.791 hours
- Val: 700 samples, 1.115 hours
- Per speaker: 350 train + 35 val
- Candidates scored per speaker: up to 2000
- Selection: clean Chinese dialog text, then ranked by duration, RMS level, silence ratio, clipping, and text score.
- Pretrained model: `<HF_CACHE_DIR>\models--rednote-hilab--dots.tts-soar\snapshots\e3520f75254d0020a0406db31c51a79d00d22d55`
- Learning rate: `3e-06`
- Max train steps: `1000`

## Files

- `train.jsonl`: dots.tts train manifest
- `val.jsonl`: dots.tts validation manifest
- `selection_details.jsonl`: selected rows and quality metrics
- `metadata.json`: dataset summary
- `dots_tts_finetune.yaml`: training config
