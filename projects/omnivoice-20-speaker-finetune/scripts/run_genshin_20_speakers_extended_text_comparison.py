#!/usr/bin/env python3
"""Generate base/fine-tuned OmniVoice outputs for the extended Genshin text set."""

from __future__ import annotations

import argparse
import gc
import json
import os
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import numpy as np
import soundfile as sf
import torch

from omnivoice import OmniVoice


ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "evaluation" / "genshin_20_speakers_extended_texts" / "cases.jsonl"
OUTPUT_DIR = ROOT / "outputs" / "genshin_20_speakers_extended_texts"
EVAL_DIR = ROOT / "evaluation" / "genshin_20_speakers_extended_texts"
MODELS = (
    ("base", ROOT / "pretrained_models" / "OmniVoice"),
    ("finetuned_best", ROOT / "exp" / "genshin_20_speakers_1200_sdpa" / "best"),
)


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def sync() -> None:
    if torch.cuda.is_available():
        torch.cuda.synchronize()


def seed() -> None:
    torch.manual_seed(0)
    torch.cuda.manual_seed_all(0)


def audio_seconds(path: Path) -> float:
    info = sf.info(path)
    return info.frames / info.samplerate


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, default=CASES_PATH)
    parser.add_argument("--skip-existing", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    cases = [
        json.loads(line)
        for line in args.cases.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    results = []
    model_summaries = []
    for model_name, model_path in MODELS:
        sync()
        started = perf_counter()
        model = OmniVoice.from_pretrained(model_path, device_map="cuda:0", dtype=torch.float16)
        sync()
        model_load_seconds = perf_counter() - started

        prompt_cache = {}
        prompt_seconds = {}
        for case in cases:
            reference_audio = case["reference_audio"]
            if reference_audio in prompt_cache:
                continue
            sync()
            started = perf_counter()
            prompt_cache[reference_audio] = model.create_voice_clone_prompt(
                ref_audio=reference_audio,
                ref_text=case["reference_text"],
            )
            sync()
            prompt_seconds[reference_audio] = perf_counter() - started

        model.generate(
            text="这是一次不计时的预热测试。",
            language="zh",
            voice_clone_prompt=next(iter(prompt_cache.values())),
            num_step=32,
        )
        sync()

        model_rows = []
        for case in cases:
            output_path = (
                OUTPUT_DIR
                / model_name
                / case["category"]
                / f"{case['case_id']}_{slugify(case['speaker'])}.wav"
            )
            output_path.parent.mkdir(parents=True, exist_ok=True)
            if args.skip_existing and output_path.is_file():
                generation_seconds = 0.0
                seconds = audio_seconds(output_path)
                peak = None
                clipped_samples = None
            else:
                seed()
                sync()
                started = perf_counter()
                audio = model.generate(
                    text=case["text"],
                    language=case["language_id"],
                    voice_clone_prompt=prompt_cache[case["reference_audio"]],
                    num_step=32,
                )[0]
                sync()
                generation_seconds = perf_counter() - started
                sf.write(output_path, audio, model.sampling_rate)
                seconds = len(audio) / model.sampling_rate
                peak = float(np.max(np.abs(audio)))
                clipped_samples = int(np.count_nonzero(np.abs(audio) >= 1.0))

            row = {
                "id": f"{model_name}_{case['case_id']}_{slugify(case['speaker'])}",
                "model_name": model_name,
                "model_path": str(model_path),
                **case,
                "output_wav": str(output_path),
                "generation_seconds": generation_seconds,
                "audio_seconds": seconds,
                "rtf": generation_seconds / seconds if generation_seconds > 0 else None,
                "peak": peak,
                "clipped_samples": clipped_samples,
            }
            results.append(row)
            model_rows.append(row)
            print(
                f"{row['id']}: generation={generation_seconds:.3f}s "
                f"audio={seconds:.3f}s rtf={row['rtf'] if row['rtf'] is not None else 'skip'}"
            )

        generated_rows = [row for row in model_rows if row["generation_seconds"] > 0]
        model_summaries.append(
            {
                "model_name": model_name,
                "model_path": str(model_path),
                "model_load_seconds": model_load_seconds,
                "mean_prompt_prepare_seconds": float(np.mean(list(prompt_seconds.values()))),
                "generation_seconds": sum(row["generation_seconds"] for row in model_rows),
                "audio_seconds": sum(row["audio_seconds"] for row in generated_rows)
                if generated_rows
                else sum(row["audio_seconds"] for row in model_rows),
            }
        )
        del model
        prompt_cache.clear()
        gc.collect()
        torch.cuda.empty_cache()

    payload = {
        "timestamp": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
        "num_step": 32,
        "batch_size": 1,
        "seed": 0,
        "cases_path": str(args.cases),
        "case_count": len(cases),
        "category_counts": Counter(case["category"] for case in cases),
        "models": model_summaries,
        "results": results,
    }
    path = EVAL_DIR / "generation_results.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved generation results: {path}")


if __name__ == "__main__":
    main()
