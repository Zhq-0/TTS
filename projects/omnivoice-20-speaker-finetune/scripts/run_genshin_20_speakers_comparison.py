#!/usr/bin/env python3
"""Generate fixed-condition base/fine-tuned outputs for 20 Genshin speakers."""

from __future__ import annotations

import gc
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import numpy as np
import soundfile as sf
import torch

from omnivoice import OmniVoice


ROOT = Path(__file__).resolve().parents[1]
DEV_MANIFEST = ROOT / "data" / "genshin_20_speakers" / "manifests" / "dev.jsonl"
OUTPUT_DIR = ROOT / "outputs" / "genshin_20_speakers_1200_finetune"
EVAL_DIR = ROOT / "evaluation" / "genshin_20_speakers_1200_finetune"
MODELS = (
    ("base", ROOT / "pretrained_models" / "OmniVoice"),
    ("finetuned_best", ROOT / "exp" / "genshin_20_speakers_1200_sdpa" / "best"),
)
TARGET_TEXT = "今天阳光很好，我们准备开始新的语音合成测试，请保持清晰自然的表达。"


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def sync() -> None:
    if torch.cuda.is_available():
        torch.cuda.synchronize()


def seed() -> None:
    torch.manual_seed(0)
    torch.cuda.manual_seed_all(0)


def main() -> None:
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    dev_rows = [json.loads(line) for line in DEV_MANIFEST.read_text(encoding="utf-8").splitlines()]
    references = {}
    for row in dev_rows:
        references.setdefault(row["speaker"], row)

    results = []
    model_summaries = []
    for model_name, model_path in MODELS:
        sync()
        started = perf_counter()
        model = OmniVoice.from_pretrained(model_path, device_map="cuda:0", dtype=torch.float16)
        sync()
        model_load_seconds = perf_counter() - started

        prompts = {}
        prompt_seconds = {}
        for speaker, reference in references.items():
            sync()
            started = perf_counter()
            prompts[speaker] = model.create_voice_clone_prompt(
                ref_audio=reference["audio_path"],
                ref_text=reference["text"],
            )
            sync()
            prompt_seconds[speaker] = perf_counter() - started

        model.generate(
            text="这是一次不计时的预热测试。",
            language="zh",
            voice_clone_prompt=next(iter(prompts.values())),
            num_step=32,
        )
        sync()

        model_dir = OUTPUT_DIR / model_name
        model_dir.mkdir(parents=True, exist_ok=True)
        model_rows = []
        for speaker, reference in sorted(references.items()):
            seed()
            sync()
            started = perf_counter()
            audio = model.generate(
                text=TARGET_TEXT,
                language="zh",
                voice_clone_prompt=prompts[speaker],
                num_step=32,
            )[0]
            sync()
            generation_seconds = perf_counter() - started
            output_path = model_dir / f"{slugify(speaker)}.wav"
            sf.write(output_path, audio, model.sampling_rate)
            audio_seconds = len(audio) / model.sampling_rate
            row = {
                "id": f"{model_name}_{slugify(speaker)}",
                "model_name": model_name,
                "model_path": str(model_path),
                "speaker": speaker,
                "text": TARGET_TEXT,
                "language_id": "zh",
                "asr_language": "zh",
                "reference_audio": reference["audio_path"],
                "reference_text": reference["text"],
                "output_wav": str(output_path),
                "generation_seconds": generation_seconds,
                "audio_seconds": audio_seconds,
                "rtf": generation_seconds / audio_seconds,
                "peak": float(np.max(np.abs(audio))),
                "clipped_samples": int(np.count_nonzero(np.abs(audio) >= 1.0)),
            }
            results.append(row)
            model_rows.append(row)
            print(
                f"{row['id']}: generation={generation_seconds:.3f}s "
                f"audio={audio_seconds:.3f}s rtf={row['rtf']:.3f}"
            )
        model_summaries.append(
            {
                "model_name": model_name,
                "model_path": str(model_path),
                "model_load_seconds": model_load_seconds,
                "mean_prompt_prepare_seconds": float(np.mean(list(prompt_seconds.values()))),
                "generation_seconds": sum(row["generation_seconds"] for row in model_rows),
                "audio_seconds": sum(row["audio_seconds"] for row in model_rows),
            }
        )
        del model
        prompts.clear()
        gc.collect()
        torch.cuda.empty_cache()

    payload = {
        "timestamp": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "device": torch.cuda.get_device_name(0),
        "num_step": 32,
        "batch_size": 1,
        "seed": 0,
        "target_text": TARGET_TEXT,
        "models": model_summaries,
        "results": results,
    }
    path = EVAL_DIR / "generation_results.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved generation results: {path}")


if __name__ == "__main__":
    main()
