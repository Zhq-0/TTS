#!/usr/bin/env python3
"""Select and extract high-quality data for a 20-speaker Genshin fine-tune."""

from __future__ import annotations

import io
import json
import re
from collections import defaultdict
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
import soundfile as sf


ROOT = Path(__file__).resolve().parents[1]
DATASET_ROOT = ROOT.parent / "genshin-voice-zh"
METADATA_PATH = DATASET_ROOT / "result.json"
PARQUET_DIR = DATASET_ROOT / "data"
OUTPUT_ROOT = ROOT / "data" / "genshin_20_speakers"
MANIFEST_DIR = OUTPUT_ROOT / "manifests"
AUDIO_DIR = OUTPUT_ROOT / "audio"

SPEAKER_COUNT = 20
TRAIN_PER_SPEAKER = 60
DEV_PER_SPEAKER = 10
CANDIDATES_PER_SPEAKER = 120

PLACEHOLDER_RE = re.compile(r"\{[^}]+\}|#[A-Za-z0-9_]+|<[^>]+>")
CHINESE_RE = re.compile(r"[\u4e00-\u9fff]")
SAFE_RE = re.compile(r"[^a-z0-9]+")


def clean_text(text: str) -> bool:
    text = text.strip()
    chinese_count = len(CHINESE_RE.findall(text))
    return (
        12 <= len(text) <= 80
        and chinese_count >= 8
        and chinese_count / max(len(text), 1) >= 0.45
        and not PLACEHOLDER_RE.search(text)
        and not text.startswith("#")
    )


def text_score(text: str) -> float:
    score = abs(len(text) - 32) * 0.04
    score += text.count("…") * 0.25
    score += text.count("——") * 0.25
    if text[-1:] not in "。！？!?":
        score += 0.5
    return score


def slugify(name: str) -> str:
    slug = SAFE_RE.sub("_", name.lower()).strip("_")
    return slug or f"speaker_{abs(hash(name)) & 0xFFFFFFFF:08x}"


def audio_metrics(audio_bytes: bytes) -> tuple[np.ndarray, int, dict]:
    waveform, sample_rate = sf.read(io.BytesIO(audio_bytes), dtype="float32", always_2d=True)
    mono = waveform.mean(axis=1)
    duration = len(mono) / sample_rate
    peak = float(np.max(np.abs(mono)))
    rms = float(np.sqrt(np.mean(np.square(mono))))
    rms_dbfs = float(20 * np.log10(rms + 1e-12))
    silence_ratio = float(np.mean(np.abs(mono) < 0.005))
    clipped_ratio = float(np.mean(np.abs(mono) >= 0.999))
    metrics = {
        "duration_seconds": duration,
        "sample_rate": sample_rate,
        "peak": peak,
        "rms_dbfs": rms_dbfs,
        "silence_ratio": silence_ratio,
        "clipped_ratio": clipped_ratio,
    }
    return waveform, sample_rate, metrics


def audio_score(metrics: dict, text: str) -> float:
    score = abs(metrics["duration_seconds"] - 5.0)
    score += abs(metrics["rms_dbfs"] + 20.0) * 0.12
    score += metrics["silence_ratio"] * 3.0
    score += text_score(text)
    if not 2.5 <= metrics["duration_seconds"] <= 10.0:
        score += 30
    if not -35 <= metrics["rms_dbfs"] <= -8:
        score += 30
    if metrics["silence_ratio"] > 0.55:
        score += 30
    if metrics["clipped_ratio"] > 0:
        score += 30
    return score


def choose_candidate_indices(metadata: list[dict]) -> tuple[list[str], dict[int, dict], dict]:
    grouped = defaultdict(list)
    for index, row in enumerate(metadata):
        speaker = row.get("speaker", "").strip()
        text = row.get("transcription", "").strip()
        if (
            speaker
            and row.get("language") == "Chinese"
            and row.get("type") == "Dialog"
            and clean_text(text)
        ):
            grouped[speaker].append(
                {
                    "global_index": index,
                    "speaker": speaker,
                    "text": text,
                    "source_file": row["file_name"],
                    "text_score": text_score(text),
                }
            )

    ranked_speakers = sorted(grouped, key=lambda speaker: (-len(grouped[speaker]), speaker))
    selected_speakers = ranked_speakers[:SPEAKER_COUNT]
    candidates = {}
    for speaker in selected_speakers:
        rows = sorted(grouped[speaker], key=lambda row: (row["text_score"], row["global_index"]))
        # Spread candidates across the speaker's full metadata range instead of taking one scene.
        if len(rows) > CANDIDATES_PER_SPEAKER:
            positions = np.linspace(0, len(rows) - 1, CANDIDATES_PER_SPEAKER, dtype=int)
            rows = [rows[position] for position in positions]
        for row in rows:
            candidates[row["global_index"]] = row
    eligible_counts = {speaker: len(grouped[speaker]) for speaker in selected_speakers}
    return selected_speakers, candidates, eligible_counts


def extract_candidates(candidates: dict[int, dict]) -> dict[str, list[dict]]:
    wanted = set(candidates)
    grouped = defaultdict(list)
    global_offset = 0
    for parquet_path in sorted(PARQUET_DIR.glob("*.parquet")):
        parquet = pq.ParquetFile(parquet_path)
        for row_group_index in range(parquet.num_row_groups):
            row_count = parquet.metadata.row_group(row_group_index).num_rows
            local_indices = sorted(
                index - global_offset
                for index in wanted
                if global_offset <= index < global_offset + row_count
            )
            if local_indices:
                table = parquet.read_row_group(
                    row_group_index,
                    columns=["audio", "transcription", "speaker"],
                )
                rows = table.to_pylist()
                for local_index in local_indices:
                    global_index = global_offset + local_index
                    source = rows[local_index]
                    expected = candidates[global_index]
                    if (
                        source["speaker"] != expected["speaker"]
                        or source["transcription"] != expected["text"]
                    ):
                        raise RuntimeError(f"Metadata order mismatch at row {global_index}")
                    waveform, sample_rate, metrics = audio_metrics(source["audio"]["bytes"])
                    grouped[expected["speaker"]].append(
                        {
                            **expected,
                            "waveform": waveform,
                            "sample_rate": sample_rate,
                            "selection_metrics": metrics,
                            "selection_score": audio_score(metrics, expected["text"]),
                        }
                    )
                    wanted.remove(global_index)
            global_offset += row_count
    if wanted:
        raise RuntimeError(f"Could not locate {len(wanted)} selected dataset rows")
    return grouped


def write_selected(selected_speakers: list[str], grouped: dict[str, list[dict]], counts: dict) -> None:
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    train_rows = []
    dev_rows = []
    detail_rows = []
    speaker_rows = []

    for speaker in selected_speakers:
        ranked = sorted(grouped[speaker], key=lambda row: (row["selection_score"], row["global_index"]))
        usable = [
            row
            for row in ranked
            if row["selection_score"] < 30
        ]
        required = TRAIN_PER_SPEAKER + DEV_PER_SPEAKER
        if len(usable) < required:
            raise RuntimeError(f"{speaker} only has {len(usable)} usable candidates, need {required}")
        chosen = usable[:required]
        speaker_dir = AUDIO_DIR / slugify(speaker)
        speaker_dir.mkdir(parents=True, exist_ok=True)
        for position, row in enumerate(chosen):
            sample_id = f"{slugify(speaker)}_{row['global_index']:06d}"
            audio_path = speaker_dir / f"{sample_id}.wav"
            sf.write(audio_path, row.pop("waveform"), row["sample_rate"], subtype="PCM_16")
            manifest_row = {
                "id": sample_id,
                "audio_path": str(audio_path),
                "text": row["text"],
                "language_id": "zh",
                "speaker": speaker,
            }
            detail = {
                **manifest_row,
                "global_index": row["global_index"],
                "source_file": row["source_file"],
                "selection_score": row["selection_score"],
                "selection_metrics": row["selection_metrics"],
                "split": "train" if position < TRAIN_PER_SPEAKER else "dev",
            }
            detail_rows.append(detail)
            if position < TRAIN_PER_SPEAKER:
                train_rows.append(manifest_row)
            else:
                dev_rows.append(manifest_row)
        speaker_rows.append(
            {
                "speaker": speaker,
                "eligible_metadata_samples": counts[speaker],
                "evaluated_candidates": len(grouped[speaker]),
                "selected_train_samples": TRAIN_PER_SPEAKER,
                "selected_dev_samples": DEV_PER_SPEAKER,
            }
        )

    def write_jsonl(path: Path, rows: list[dict]) -> None:
        path.write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
            encoding="utf-8",
        )

    write_jsonl(MANIFEST_DIR / "train.jsonl", train_rows)
    write_jsonl(MANIFEST_DIR / "dev.jsonl", dev_rows)
    write_jsonl(MANIFEST_DIR / "selection_details.jsonl", detail_rows)
    summary = {
        "speaker_count": len(selected_speakers),
        "speakers": speaker_rows,
        "train_samples": len(train_rows),
        "dev_samples": len(dev_rows),
        "train_total_seconds": sum(
            row["selection_metrics"]["duration_seconds"]
            for row in detail_rows
            if row["split"] == "train"
        ),
        "dev_total_seconds": sum(
            row["selection_metrics"]["duration_seconds"]
            for row in detail_rows
            if row["split"] == "dev"
        ),
    }
    (MANIFEST_DIR / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def main() -> None:
    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    selected_speakers, candidates, counts = choose_candidate_indices(metadata)
    print("Selected speakers:", ", ".join(selected_speakers))
    print(f"Evaluating {len(candidates)} audio candidates...")
    grouped = extract_candidates(candidates)
    write_selected(selected_speakers, grouped, counts)


if __name__ == "__main__":
    main()
