#!/usr/bin/env python3
"""Extract a high-quality multi-speaker Genshin dataset for dots.tts training."""

from __future__ import annotations

import argparse
import io
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.parquet as pq
import soundfile as sf


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET_ROOT = Path("<GENSHIN_DATASET_ROOT>")
DEFAULT_OUTPUT_DIR = (
    ROOT
    / "experiments"
    / "small_multispeaker_finetune"
    / "genshin_20_speakers_high_quality_200shot"
)
DEFAULT_PRETRAINED = Path(
    "<HF_CACHE_DIR>/models--rednote-hilab--dots.tts-mf/"
    "snapshots/25c53fb462e57087e52237daa5ea30df1c5cc328"
)

PLACEHOLDER_RE = re.compile(r"\{[^}]+\}|#[A-Za-z0-9_]+|<[^>]+>")
CHINESE_RE = re.compile(r"[\u4e00-\u9fff]")
SAFE_RE = re.compile(r"[^a-z0-9]+")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--speaker-count", type=int, default=20)
    parser.add_argument(
        "--speaker-search-count",
        type=int,
        default=None,
        help="Score this many high-count speakers, then keep the first speaker-count speakers with enough usable samples.",
    )
    parser.add_argument("--train-per-speaker", type=int, default=200)
    parser.add_argument("--val-per-speaker", type=int, default=20)
    parser.add_argument("--candidates-per-speaker", type=int, default=500)
    parser.add_argument("--min-duration", type=float, default=2.5)
    parser.add_argument("--max-duration", type=float, default=10.0)
    parser.add_argument("--min-rms-dbfs", type=float, default=-35.0)
    parser.add_argument("--max-rms-dbfs", type=float, default=-8.0)
    parser.add_argument("--max-silence-ratio", type=float, default=0.55)
    parser.add_argument(
        "--allow-ranked-fallback",
        action="store_true",
        help="If a speaker has too few strict usable samples, fill from the next best ranked samples.",
    )
    parser.add_argument("--pretrained-model-path", type=Path, default=DEFAULT_PRETRAINED)
    parser.add_argument("--max-train-steps", type=int, default=1000)
    parser.add_argument("--learning-rate", type=float, default=5.0e-6)
    parser.add_argument("--run-name", default="dots_tts_mf_genshin_20spk_200shot_lr5e6")
    return parser.parse_args()


def slugify(name: str) -> str:
    slug = SAFE_RE.sub("_", name.lower()).strip("_")
    return slug or f"speaker_{abs(hash(name)) & 0xFFFFFFFF:08x}"


def clean_text(text: str) -> bool:
    text = text.strip()
    chinese_count = len(CHINESE_RE.findall(text))
    return (
        12 <= len(text) <= 90
        and chinese_count >= 8
        and chinese_count / max(len(text), 1) >= 0.45
        and not PLACEHOLDER_RE.search(text)
        and not text.startswith("#")
    )


def text_score(text: str) -> float:
    text = text.strip()
    score = abs(len(text) - 32) * 0.04
    score += text.count("…") * 0.12
    score += text.count("——") * 0.15
    score += text.count("「") * 0.03
    if text[-1:] not in "。！？!?…」":
        score += 0.5
    return score


def audio_metrics(audio_bytes: bytes) -> tuple[int, dict[str, float]]:
    waveform, sample_rate = sf.read(io.BytesIO(audio_bytes), dtype="float32", always_2d=True)
    mono = waveform.mean(axis=1)
    duration = len(mono) / sample_rate
    peak = float(np.max(np.abs(mono))) if mono.size else 0.0
    rms = float(np.sqrt(np.mean(np.square(mono)))) if mono.size else 0.0
    rms_dbfs = float(20 * np.log10(rms + 1e-12))
    silence_ratio = float(np.mean(np.abs(mono) < 0.005)) if mono.size else 1.0
    clipped_ratio = float(np.mean(np.abs(mono) >= 0.999)) if mono.size else 0.0
    return sample_rate, {
        "duration_seconds": float(duration),
        "sample_rate": float(sample_rate),
        "peak": peak,
        "rms_dbfs": rms_dbfs,
        "silence_ratio": silence_ratio,
        "clipped_ratio": clipped_ratio,
    }


def audio_score(metrics: dict[str, float], text: str, args: argparse.Namespace) -> float:
    score = abs(metrics["duration_seconds"] - 5.0)
    score += abs(metrics["rms_dbfs"] + 20.0) * 0.12
    score += metrics["silence_ratio"] * 3.0
    score += text_score(text)
    if not args.min_duration <= metrics["duration_seconds"] <= args.max_duration:
        score += 30.0
    if not args.min_rms_dbfs <= metrics["rms_dbfs"] <= args.max_rms_dbfs:
        score += 30.0
    if metrics["silence_ratio"] > args.max_silence_ratio:
        score += 30.0
    if metrics["clipped_ratio"] > 0:
        score += 30.0
    return float(score)


def load_metadata(dataset_root: Path) -> list[dict[str, Any]]:
    metadata_path = dataset_root / "result.json"
    if not metadata_path.is_file():
        raise FileNotFoundError(metadata_path)
    return json.loads(metadata_path.read_text(encoding="utf-8"))


def choose_candidate_indices(
    metadata: list[dict[str, Any]],
    *,
    speaker_count: int,
    candidates_per_speaker: int,
) -> tuple[list[str], dict[int, dict[str, Any]], dict[str, int]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for index, row in enumerate(metadata):
        speaker = str(row.get("speaker") or "").strip()
        text = str(row.get("transcription") or "").strip()
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
                    "source_file": row.get("file_name", ""),
                    "text_score": text_score(text),
                }
            )

    selected_speakers = sorted(grouped, key=lambda speaker: (-len(grouped[speaker]), speaker))[
        :speaker_count
    ]
    candidates: dict[int, dict[str, Any]] = {}
    for speaker in selected_speakers:
        rows = sorted(grouped[speaker], key=lambda row: (row["text_score"], row["global_index"]))
        if len(rows) > candidates_per_speaker:
            rows = rows[:candidates_per_speaker]
        for row in rows:
            candidates[int(row["global_index"])] = row
    return selected_speakers, candidates, {speaker: len(grouped[speaker]) for speaker in selected_speakers}


def iter_parquet_rows(parquet_dir: Path, wanted: set[int], columns: list[str]):
    remaining = set(wanted)
    global_offset = 0
    for parquet_path in sorted(parquet_dir.glob("*.parquet")):
        parquet = pq.ParquetFile(parquet_path)
        for row_group_index in range(parquet.num_row_groups):
            row_count = parquet.metadata.row_group(row_group_index).num_rows
            local_indices = sorted(
                index - global_offset
                for index in remaining
                if global_offset <= index < global_offset + row_count
            )
            if local_indices:
                table = parquet.read_row_group(row_group_index, columns=columns)
                rows = table.to_pylist()
                for local_index in local_indices:
                    global_index = global_offset + local_index
                    yield global_index, rows[local_index]
                    remaining.remove(global_index)
            global_offset += row_count
    if remaining:
        raise RuntimeError(f"Could not locate {len(remaining)} selected dataset rows")


def score_candidates(
    parquet_dir: Path,
    candidates: dict[int, dict[str, Any]],
    args: argparse.Namespace,
) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for global_index, source in iter_parquet_rows(
        parquet_dir,
        set(candidates),
        ["audio", "transcription", "speaker"],
    ):
        expected = candidates[global_index]
        if source["speaker"] != expected["speaker"] or source["transcription"] != expected["text"]:
            raise RuntimeError(f"Metadata order mismatch at row {global_index}")
        sample_rate, metrics = audio_metrics(source["audio"]["bytes"])
        grouped[expected["speaker"]].append(
            {
                **expected,
                "sample_rate": sample_rate,
                "selection_metrics": metrics,
                "selection_score": audio_score(metrics, expected["text"], args),
            }
        )
    return grouped


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def extract_audio_files(
    parquet_dir: Path,
    chosen_by_index: dict[int, dict[str, Any]],
    output_audio_dir: Path,
) -> None:
    for global_index, source in iter_parquet_rows(
        parquet_dir,
        set(chosen_by_index),
        ["audio", "transcription", "speaker"],
    ):
        row = chosen_by_index[global_index]
        waveform, sample_rate = sf.read(
            io.BytesIO(source["audio"]["bytes"]), dtype="float32", always_2d=True
        )
        audio_path = Path(row["audio_path"])
        audio_path.parent.mkdir(parents=True, exist_ok=True)
        sf.write(audio_path, waveform, sample_rate, subtype="PCM_16")


def write_config(output_dir: Path, args: argparse.Namespace) -> None:
    train_manifest = (output_dir / "train.jsonl").as_posix()
    val_manifest = (output_dir / "val.jsonl").as_posix()
    run_dir = (output_dir / "runs" / args.run_name).as_posix()
    source_prefix = f"genshin_{args.train_per_speaker}shot"
    config = f"""train_data:
  train_audio_sample_rate: 48000
  audio_samples_per_llm_token: 7680
  sources:
    - name: {source_prefix}_basic
      weight: 1.0
      pipeline: basic
      adapter:
        class_name: JsonlManifestSourceAdapter
        params:
          manifest_path: {train_manifest}
          shuffle: true
    - name: {source_prefix}_interleave
      weight: 1.0
      pipeline: interleave
      adapter:
        class_name: JsonlManifestSourceAdapter
        params:
          manifest_path: {train_manifest}
          shuffle: true
  num_tokens_per_epoch: 800000
  num_workers: 0
  pin_memory: true
  max_audio_seconds_in_batch: 12.0
  max_text_tokens_in_batch: 1024
  max_samples_per_batch: null
  bucketing_pool_size: 96
val_data:
  train_audio_sample_rate: 48000
  audio_samples_per_llm_token: 7680
  sources:
    - name: {source_prefix}_valid_basic
      weight: 1.0
      pipeline: basic
      adapter:
        class_name: JsonlManifestSourceAdapter
        params:
          manifest_path: {val_manifest}
          shuffle: false
    - name: {source_prefix}_valid_interleave
      weight: 1.0
      pipeline: interleave
      adapter:
        class_name: JsonlManifestSourceAdapter
        params:
          manifest_path: {val_manifest}
          shuffle: false
  num_workers: 0
  pin_memory: true
  max_audio_seconds_in_batch: 12.0
  max_text_tokens_in_batch: 1024
  max_samples_per_batch: null
  bucketing_pool_size: 96
train:
  pretrained_model_path: {args.pretrained_model_path.as_posix()}
  output_dir: {run_dir}
  seed: 2026
  learning_rate: {args.learning_rate:.8g}
  weight_decay: 0.01
  warmup_steps: 50
  max_train_steps: {args.max_train_steps}
  gradient_accumulation_steps: 2
  grad_clip_norm: 1.0
  save_interval: 100
  max_checkpoints_to_keep: 10
  log_interval: 10
  eval_interval: 100
  max_eval_batches: 5
  run_eval_on_start: false
loss:
  ce_weight: 1.0
  fm_weight: 1.0
  eos_weight: 1.0
"""
    (output_dir / "dots_tts_finetune.yaml").write_text(config, encoding="utf-8")


def write_readme(output_dir: Path, summary: dict[str, Any]) -> None:
    lines = [
        f"# Genshin 20 Speakers {summary['train_per_speaker']}-shot dots.tts fine-tune",
        "",
        "## Data",
        "",
        f"- Speakers: {summary['speaker_count']}",
        f"- Train: {summary['train_samples']} samples, {summary['train_hours']:.3f} hours",
        f"- Val: {summary['val_samples']} samples, {summary['val_hours']:.3f} hours",
        f"- Per speaker: {summary['train_per_speaker']} train + {summary['val_per_speaker']} val",
        f"- Candidates scored per speaker: up to {summary['candidates_per_speaker']}",
        "- Selection: clean Chinese dialog text, then ranked by duration, RMS level, silence ratio, clipping, and text score.",
        f"- Pretrained model: `{summary['pretrained_model_path']}`",
        f"- Learning rate: `{summary['learning_rate']}`",
        f"- Max train steps: `{summary['max_train_steps']}`",
        "",
        "## Files",
        "",
        "- `train.jsonl`: dots.tts train manifest",
        "- `val.jsonl`: dots.tts validation manifest",
        "- `selection_details.jsonl`: selected rows and quality metrics",
        "- `metadata.json`: dataset summary",
        "- `dots_tts_finetune.yaml`: training config",
        "",
    ]
    (output_dir / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir.resolve()
    audio_dir = output_dir / "audio"
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_dir.mkdir(parents=True, exist_ok=True)

    dataset_root = args.dataset_root.resolve()
    metadata = load_metadata(dataset_root)
    selected_speakers, candidates, eligible_counts = choose_candidate_indices(
        metadata,
        speaker_count=args.speaker_search_count or args.speaker_count,
        candidates_per_speaker=args.candidates_per_speaker,
    )
    print("Selected speakers:", ", ".join(selected_speakers))
    print(f"Scoring {len(candidates)} candidates...")
    grouped = score_candidates(dataset_root / "data", candidates, args)

    train_rows: list[dict[str, Any]] = []
    val_rows: list[dict[str, Any]] = []
    detail_rows: list[dict[str, Any]] = []
    chosen_by_index: dict[int, dict[str, Any]] = {}
    speaker_summaries: list[dict[str, Any]] = []

    required = args.train_per_speaker + args.val_per_speaker
    for speaker in selected_speakers:
        ranked = sorted(
            grouped[speaker],
            key=lambda row: (row["selection_score"], row["global_index"]),
        )
        usable = [row for row in ranked if row["selection_score"] < 30.0]
        if len(usable) < required:
            if args.allow_ranked_fallback and len(ranked) >= required:
                print(
                    f"Filling {speaker} with ranked fallback: "
                    f"{len(usable)} strict usable candidates, need {required}"
                )
                chosen = ranked[:required]
            else:
                print(f"Skipping {speaker}: {len(usable)} usable candidates, need {required}")
                continue
        else:
            chosen = usable[:required]
        for position, row in enumerate(chosen):
            split = "train" if position < args.train_per_speaker else "dev"
            sample_id = f"{slugify(speaker)}_{int(row['global_index']):06d}"
            audio_path = audio_dir / slugify(speaker) / f"{sample_id}.wav"
            manifest_row = {
                "fid": sample_id,
                "audio": str(audio_path),
                "text": row["text"],
                "speaker": speaker,
                "language_id": "zh",
                "source_split": split,
                "duration_seconds": row["selection_metrics"]["duration_seconds"],
                "selection_score": row["selection_score"],
            }
            detail_row = {
                "id": sample_id,
                "audio_path": str(audio_path),
                "text": row["text"],
                "language_id": "zh",
                "speaker": speaker,
                "global_index": row["global_index"],
                "source_file": row["source_file"],
                "selection_score": row["selection_score"],
                "selection_metrics": row["selection_metrics"],
                "split": split,
            }
            chosen_by_index[int(row["global_index"])] = detail_row
            detail_rows.append(detail_row)
            if split == "train":
                train_rows.append(manifest_row)
            else:
                val_rows.append(manifest_row)
        speaker_summaries.append(
            {
                "speaker": speaker,
                "eligible_metadata_samples": eligible_counts[speaker],
                "scored_candidates": len(grouped[speaker]),
                "usable_candidates": len(usable),
                "used_ranked_fallback": len(usable) < required,
                "selected_train_samples": args.train_per_speaker,
                "selected_val_samples": args.val_per_speaker,
                "best_selection_score": chosen[0]["selection_score"],
                "worst_selected_score": chosen[-1]["selection_score"],
            }
        )
        if len(speaker_summaries) >= args.speaker_count:
            break

    if len(speaker_summaries) < args.speaker_count:
        raise RuntimeError(
            f"Only found {len(speaker_summaries)} speakers with at least {required} usable samples; "
            f"need {args.speaker_count}."
        )

    print(f"Extracting {len(chosen_by_index)} selected wav files...")
    extract_audio_files(dataset_root / "data", chosen_by_index, audio_dir)

    write_jsonl(output_dir / "train.jsonl", train_rows)
    write_jsonl(output_dir / "val.jsonl", val_rows)
    write_jsonl(output_dir / "selection_details.jsonl", detail_rows)
    summary = {
        "dataset_root": str(dataset_root),
        "output_dir": str(output_dir),
        "pretrained_model_path": str(args.pretrained_model_path),
        "speaker_count": len(speaker_summaries),
        "speakers": speaker_summaries,
        "train_per_speaker": args.train_per_speaker,
        "val_per_speaker": args.val_per_speaker,
        "candidates_per_speaker": args.candidates_per_speaker,
        "train_samples": len(train_rows),
        "val_samples": len(val_rows),
        "train_seconds": sum(row["duration_seconds"] for row in train_rows),
        "val_seconds": sum(row["duration_seconds"] for row in val_rows),
        "learning_rate": args.learning_rate,
        "max_train_steps": args.max_train_steps,
        "run_name": args.run_name,
    }
    summary["train_hours"] = summary["train_seconds"] / 3600.0
    summary["val_hours"] = summary["val_seconds"] / 3600.0
    (output_dir / "metadata.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_config(output_dir, args)
    write_readme(output_dir, summary)
    print(f"Saved dataset: {output_dir}")
    print(f"Train samples: {len(train_rows)}")
    print(f"Val samples: {len(val_rows)}")


if __name__ == "__main__":
    main()
