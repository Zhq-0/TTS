#!/usr/bin/env python3
"""Write a model comparison report from Seed-TTS-Eval style metrics."""

from __future__ import annotations

import json
import argparse
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_DIR = ROOT / "experiments" / "zero_shot_comparison"
MODEL_METRICS = {
    "dots.tts-mf": EXPERIMENT_DIR / "outputs" / "dots_tts_mf" / "official_style_metrics.json",
    "CosyVoice3": EXPERIMENT_DIR / "outputs" / "cosyvoice3" / "official_style_metrics.json",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment-dir", type=Path, default=EXPERIMENT_DIR)
    parser.add_argument(
        "--model",
        action="append",
        default=[],
        metavar="NAME=RELATIVE_OR_ABSOLUTE_METRICS_JSON",
        help=(
            "Metrics JSON to include. May be repeated. Defaults to dots.tts-mf "
            "and CosyVoice3 under the experiment outputs directory."
        ),
    )
    parser.add_argument("--output-name", default="official_style_model_comparison.md")
    parser.add_argument("--summary-name", default="official_style_comparison_summary.json")
    return parser.parse_args()


def parse_model_metrics(args: argparse.Namespace, experiment_dir: Path) -> dict[str, Path]:
    if not args.model:
        return {
            "dots.tts-mf": experiment_dir / "outputs" / "dots_tts_mf" / "official_style_metrics.json",
            "CosyVoice3": experiment_dir / "outputs" / "cosyvoice3" / "official_style_metrics.json",
        }

    model_metrics: dict[str, Path] = {}
    for item in args.model:
        if "=" not in item:
            raise ValueError(f"Invalid --model value {item!r}; expected NAME=PATH.")
        name, path_text = item.split("=", 1)
        name = name.strip()
        if not name:
            raise ValueError(f"Invalid --model value {item!r}; empty model name.")
        path = Path(path_text.strip())
        if not path.is_absolute():
            path = experiment_dir / path
        model_metrics[name] = path
    return model_metrics


def load_metrics(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def ok_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [row for row in payload["results"] if row.get("status") == "ok"]


def mean(rows: list[dict[str, Any]], field: str) -> float | None:
    values = [row[field] for row in rows if row.get(field) is not None]
    return float(np.mean(values)) if values else None


def pct(value: float | None) -> str:
    return "-" if value is None else f"{value:.2%}"


def fmt(value: float | None, digits: int = 3) -> str:
    return "-" if value is None else f"{value:.{digits}f}"


def min_metric(row: dict[str, Any], field: str) -> float:
    value = row.get(field)
    return float("inf") if value is None else float(value)


def max_metric(row: dict[str, Any], field: str) -> float:
    value = row.get(field)
    return float("-inf") if value is None else float(value)


def relpath(path: str | None, experiment_dir: Path) -> str:
    if not path:
        return "-"
    try:
        return str(Path(path).resolve().relative_to(experiment_dir.resolve())).replace("\\", "/")
    except ValueError:
        return path.replace("\\", "/")


def markdown_cell(value: Any) -> str:
    return str(value).replace("|", r"\|").replace("\n", "<br>")


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "completed": len(rows),
        "mean_official_wer": mean(rows, "official_wer"),
        "mean_official_cer": mean(rows, "official_cer"),
        "mean_official_sim": mean(rows, "official_sim"),
        "mean_rtf": mean(rows, "rtf"),
    }


def main() -> None:
    args = parse_args()
    experiment_dir = args.experiment_dir.resolve()
    model_metrics = parse_model_metrics(args, experiment_dir)
    payloads = {name: load_metrics(path) for name, path in model_metrics.items()}
    rows_by_model = {name: ok_rows(payload) for name, payload in payloads.items()}
    summaries = {name: summarize(rows) for name, rows in rows_by_model.items()}

    lines = [
        "# Seed-TTS-Eval Style 模型对比",
        "",
        "## 结论快照",
        "",
        "| 模型 | 完成数 | 官方风格 WER | 官方风格 CER | 官方风格 SIM | 平均 RTF |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, summary in summaries.items():
        lines.append(
            f"| {name} | {summary['completed']} | {pct(summary['mean_official_wer'])} | "
            f"{pct(summary['mean_official_cer'])} | {fmt(summary['mean_official_sim'])} | "
            f"{fmt(summary['mean_rtf'])} |"
        )

    lines.extend(
        [
            "",
            "## 分项结果",
            "",
            "| 用例 | 模型 | 语言 | WER | CER | SIM | RTF | 输出 |",
            "|---|---|---|---:|---:|---:|---:|---|",
        ]
    )
    case_order: list[str] = []
    rows_by_case: dict[str, dict[str, dict[str, Any]]] = {}
    for model_name, rows in rows_by_model.items():
        for row in rows:
            case_name = row["name"]
            if case_name not in rows_by_case:
                rows_by_case[case_name] = {}
                case_order.append(case_name)
            rows_by_case[case_name][model_name] = row

    for case_name in case_order:
        for model_name in model_metrics:
            row = rows_by_case.get(case_name, {}).get(model_name)
            if row is None:
                continue
            lines.append(
                f"| {markdown_cell(case_name)} | {model_name} | "
                f"{row.get('asr_language') or row.get('language_id') or '-'} | "
                f"{pct(row.get('official_wer'))} | {pct(row.get('official_cer'))} | "
                f"{fmt(row.get('official_sim'))} | "
                f"{fmt(row.get('rtf'))} | `{relpath(row.get('output_wav'), experiment_dir)}` |"
            )

    lines.extend(["", "## 自动判断", ""])
    for case_name in case_order:
        candidates = [
            (model_name, rows_by_case[case_name][model_name])
            for model_name in model_metrics
            if model_name in rows_by_case[case_name]
        ]
        if len(candidates) < 2:
            continue
        parts = []
        if any(row.get("official_wer") is not None for _, row in candidates):
            best_wer = min(candidates, key=lambda item: min_metric(item[1], "official_wer"))
            parts.append(f"WER 最低 `{best_wer[0]}`")
        else:
            parts.append("WER 不适用")
        if any(row.get("official_cer") is not None for _, row in candidates):
            best_cer = min(candidates, key=lambda item: min_metric(item[1], "official_cer"))
            parts.append(f"CER 最低 `{best_cer[0]}`")
        if any(row.get("official_sim") is not None for _, row in candidates):
            best_sim = max(candidates, key=lambda item: max_metric(item[1], "official_sim"))
            parts.append(f"SIM 最高 `{best_sim[0]}`")
        if any(row.get("rtf") is not None for _, row in candidates):
            fastest = min(candidates, key=lambda item: min_metric(item[1], "rtf"))
            parts.append(f"RTF 最低 `{fastest[0]}`")
        lines.append(f"- {case_name}：" + "；".join(parts) + "。")

    lines.extend(
        [
            "",
            "## ASR 回识别文本",
            "",
            "| 用例 | 模型 | 目标文本 | 官方风格 ASR 回识别文本 |",
            "|---|---|---|---|",
        ]
    )
    for case_name in case_order:
        for model_name in model_metrics:
            row = rows_by_case.get(case_name, {}).get(model_name)
            if row is None:
                continue
            lines.append(
                f"| {markdown_cell(case_name)} | {model_name} | "
                f"{markdown_cell(row.get('text', ''))} | "
                f"{markdown_cell(row.get('official_asr_transcript', ''))} |"
            )

    lines.extend(
        [
            "",
            "## 口径说明",
            "",
            "- WER/CER/SIM 复用 Seed-TTS-Eval 风格：英文 `Whisper-large-v3`，中文 `Paraformer-zh`，SIM 为 WavLM-large speaker verification。",
            "- CER 使用同一 ASR 回识别文本，去标点和空格后按字符编辑距离计算。",
            "- 本报告使用当前自定义 4 条样本，不是完整 Seed-TTS-Eval 官方测试集；因此不能直接和论文/README 表格数值比较。",
            "- 与 `model_comparison.md` 的差异：这里替换了 ASR/SIM 口径；`model_comparison.md` 仍保留本地 Whisper-medium/OmniVoice 自动评估口径。",
            "",
        ]
    )

    output_path = experiment_dir / args.output_name
    summary_path = experiment_dir / args.summary_name
    output_path.write_text("\n".join(lines), encoding="utf-8")
    summary_path.write_text(
        json.dumps({"summaries": summaries, "models": list(model_metrics)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Saved report: {output_path}")
    print(f"Saved summary: {summary_path}")


if __name__ == "__main__":
    main()
