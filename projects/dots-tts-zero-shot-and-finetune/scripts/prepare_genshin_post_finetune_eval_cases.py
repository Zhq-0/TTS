#!/usr/bin/env python3
"""Prepare held-out Genshin cases for pre/post dots.tts fine-tune comparison."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPERIMENT_DIR = (
    ROOT
    / "experiments"
    / "small_multispeaker_finetune"
    / "genshin_20_speakers_high_quality_60shot"
)

SAFE_RE = re.compile(r"[^a-z0-9]+")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment-dir", type=Path, default=DEFAULT_EXPERIMENT_DIR)
    parser.add_argument("--val-manifest", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--cases-per-speaker", type=int, default=1)
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON at {path}:{line_number}") from exc
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def slugify(value: str) -> str:
    slug = SAFE_RE.sub("_", value.lower()).strip("_")
    return slug or "speaker"


def build_cases(rows: list[dict[str, Any]], cases_per_speaker: int) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["speaker"])].append(row)

    cases = []
    for speaker in sorted(grouped):
        speaker_rows = sorted(grouped[speaker], key=lambda row: str(row["fid"]))
        required = cases_per_speaker + 1
        if len(speaker_rows) < required:
            raise RuntimeError(
                f"Speaker {speaker!r} has {len(speaker_rows)} val rows, need {required}."
            )
        prompt_row = speaker_rows[0]
        for index, target_row in enumerate(speaker_rows[1 : 1 + cases_per_speaker], start=1):
            speaker_slug = slugify(speaker)
            case_id = f"{speaker_slug}_heldout_{index:02d}"
            cases.append(
                {
                    "id": case_id,
                    "name": f"{speaker} held-out {index}",
                    "category": "genshin_post_finetune_known_speaker",
                    "speaker": speaker,
                    "language_id": "zh",
                    "asr_language": "zh",
                    "language": "ZH",
                    "prompt_audio": str(Path(prompt_row["audio"]).resolve()),
                    "prompt_text": prompt_row["text"],
                    "text": target_row["text"],
                    "output_name": f"{case_id}.wav",
                    "prompt_fid": prompt_row["fid"],
                    "target_fid": target_row["fid"],
                    "notes": (
                        "Held-out Genshin validation case for comparing the original "
                        "dots.tts-mf checkpoint against the fine-tuned checkpoint."
                    ),
                }
            )
    return cases


def main() -> None:
    args = parse_args()
    experiment_dir = args.experiment_dir.resolve()
    val_manifest = args.val_manifest or experiment_dir / "val.jsonl"
    output_dir = args.output_dir or experiment_dir / "evaluation"
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = read_jsonl(val_manifest)
    cases = build_cases(rows, args.cases_per_speaker)
    cases_path = output_dir / "cases.jsonl"
    write_jsonl(cases_path, cases)

    metadata = {
        "source_val_manifest": str(val_manifest.resolve()),
        "cases_path": str(cases_path.resolve()),
        "speaker_count": len({case["speaker"] for case in cases}),
        "case_count": len(cases),
        "cases_per_speaker": args.cases_per_speaker,
        "metric_plan": [
            "RTF from generation_results.json",
            "WER and CER from official-style ASR transcript",
            "SIM from Seed-TTS-Eval WavLM-large speaker verification",
        ],
    }
    (output_dir / "cases_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Saved cases: {cases_path}")
    print(f"Case count: {len(cases)}")


if __name__ == "__main__":
    main()
