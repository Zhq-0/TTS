#!/usr/bin/env python3
"""Prepare a small multi-speaker Genshin manifest for dots.tts fine-tuning."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = Path("<OMNIVOICE_ROOT>/data/genshin_20_speakers/manifests/selection_details.jsonl")
DEFAULT_OUTPUT = ROOT / "experiments" / "small_multispeaker_finetune" / "genshin_20_speakers_5shot"
DEFAULT_PRETRAINED = Path(
    "<HF_CACHE_DIR>/models--rednote-hilab--dots.tts-mf/snapshots/25c53fb462e57087e52237daa5ea30df1c5cc328"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--train-per-speaker", type=int, default=5)
    parser.add_argument("--val-per-speaker", type=int, default=2)
    parser.add_argument("--pretrained-model-path", type=Path, default=DEFAULT_PRETRAINED)
    parser.add_argument("--max-train-steps", type=int, default=1000)
    parser.add_argument("--learning-rate", type=float, default=1.0e-5)
    parser.add_argument("--run-name", type=str, default=None)
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def select_rows(rows: list[dict[str, Any]], split: str, count: int) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("split") == split:
            grouped[row["speaker"]].append(row)
    selected = []
    for speaker in sorted(grouped):
        ranked = sorted(
            grouped[speaker],
            key=lambda row: (row.get("selection_score", 999.0), row["id"]),
        )
        selected.extend(ranked[:count])
    return selected


def to_manifest_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "fid": row["id"],
        "audio": row["audio_path"],
        "text": row["text"],
        "speaker": row["speaker"],
        "language_id": row.get("language_id", "zh"),
        "source_split": row.get("split"),
        "duration_seconds": row.get("selection_metrics", {}).get("duration_seconds"),
        "selection_score": row.get("selection_score"),
    }


def write_config(
    output_dir: Path,
    pretrained_model_path: Path,
    *,
    train_per_speaker: int,
    max_train_steps: int,
    learning_rate: float,
    run_name: str | None,
) -> None:
    train_manifest = (output_dir / "train.jsonl").as_posix()
    val_manifest = (output_dir / "val.jsonl").as_posix()
    resolved_run_name = run_name or f"dots_tts_mf_{train_per_speaker}shot"
    source_prefix = f"genshin_{train_per_speaker}shot"
    run_dir = (output_dir / "runs" / resolved_run_name).as_posix()
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
  num_tokens_per_epoch: 300000
  num_workers: 0
  pin_memory: true
  max_audio_seconds_in_batch: 30.0
  max_text_tokens_in_batch: 2048
  max_samples_per_batch: null
  bucketing_pool_size: 64
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
  max_audio_seconds_in_batch: 30.0
  max_text_tokens_in_batch: 2048
  max_samples_per_batch: null
  bucketing_pool_size: 64
train:
  pretrained_model_path: {pretrained_model_path.as_posix()}
  output_dir: {run_dir}
  seed: 2026
  learning_rate: {learning_rate:.8g}
  weight_decay: 0.01
  warmup_steps: 50
  max_train_steps: {max_train_steps}
  gradient_accumulation_steps: 2
  grad_clip_norm: 1.0
  save_interval: 100
  max_checkpoints_to_keep: 10
  log_interval: 10
  eval_interval: 100
  max_eval_batches: 10
  run_eval_on_start: true
loss:
  ce_weight: 1.0
  fm_weight: 1.0
  eos_weight: 1.0
"""
    (output_dir / "dots_tts_finetune.yaml").write_text(config, encoding="utf-8")


def write_readme(output_dir: Path, summary: dict[str, Any]) -> None:
    lines = [
        f"# Genshin 20 Speakers {summary['train_per_speaker']}-shot dots.tts 微调准备",
        "",
        "## 数据",
        "",
        f"- 说话人数：{summary['speaker_count']}",
        f"- 训练集：{summary['train_samples']} 条，约 {summary['train_hours']:.3f} 小时",
        f"- 验证集：{summary['val_samples']} 条，约 {summary['val_hours']:.3f} 小时",
        f"- 每个说话人训练 {summary['train_per_speaker']} 条、验证 {summary['val_per_speaker']} 条，按原始 selection_score 选择较干净样本。",
        f"- 预训练模型：`{summary['pretrained_model_path']}`",
        f"- 训练步数：{summary['max_train_steps']}，学习率：{summary['learning_rate']}",
        "",
        "## 文件",
        "",
        "- `train.jsonl`：dots.tts 训练 manifest",
        "- `val.jsonl`：dots.tts 验证 manifest",
        "- `selection_details.jsonl`：原始筛选明细和质量指标",
        "- `metadata.json`：数据统计和说话人列表",
        "- `dots_tts_finetune.yaml`：训练配置草案",
        "",
        "## 后续命令",
        "",
        "```powershell",
        "<ANACONDA_ROOT>\\envs\\dots_tts\\python.exe -m pip install -e .[full] -c constraints/recommended.txt",
        f"<ANACONDA_ROOT>\\envs\\dots_tts\\python.exe -m accelerate.commands.launch scripts\\train_dots_tts.py --config {output_dir / 'dots_tts_finetune.yaml'}",
        "```",
        "",
        "如已安装训练依赖，可直接运行上面的 accelerate 命令启动或续训。",
        "",
    ]
    (output_dir / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    rows = read_jsonl(args.source)
    train_source = select_rows(rows, "train", args.train_per_speaker)
    val_source = select_rows(rows, "dev", args.val_per_speaker)
    train = [to_manifest_row(row) for row in train_source]
    val = [to_manifest_row(row) for row in val_source]

    write_jsonl(args.output_dir / "train.jsonl", train)
    write_jsonl(args.output_dir / "val.jsonl", val)
    write_jsonl(args.output_dir / "selection_details.jsonl", train_source + val_source)
    speakers = sorted({row["speaker"] for row in train + val})
    summary = {
        "source": str(args.source),
        "output_dir": str(args.output_dir),
        "pretrained_model_path": str(args.pretrained_model_path),
        "speaker_count": len(speakers),
        "speakers": speakers,
        "train_per_speaker": args.train_per_speaker,
        "val_per_speaker": args.val_per_speaker,
        "max_train_steps": args.max_train_steps,
        "learning_rate": args.learning_rate,
        "train_samples": len(train),
        "val_samples": len(val),
        "train_seconds": sum(row.get("duration_seconds") or 0 for row in train),
        "val_seconds": sum(row.get("duration_seconds") or 0 for row in val),
    }
    summary["train_hours"] = summary["train_seconds"] / 3600
    summary["val_hours"] = summary["val_seconds"] / 3600
    (args.output_dir / "metadata.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    write_config(
        args.output_dir,
        args.pretrained_model_path,
        train_per_speaker=args.train_per_speaker,
        max_train_steps=args.max_train_steps,
        learning_rate=args.learning_rate,
        run_name=args.run_name,
    )
    write_readme(args.output_dir, summary)
    print(f"Saved manifest directory: {args.output_dir}")


if __name__ == "__main__":
    main()
