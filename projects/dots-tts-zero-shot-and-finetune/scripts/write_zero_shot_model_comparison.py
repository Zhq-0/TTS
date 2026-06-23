#!/usr/bin/env python3
"""Write a cross-model comparison report for zero-shot experiments."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_DIR = ROOT / "experiments" / "zero_shot_comparison"
OUTPUTS = {
    "dots.tts-mf": EXPERIMENT_DIR / "outputs" / "dots_tts_mf" / "automatic_metrics.json",
    "CosyVoice3": EXPERIMENT_DIR / "outputs" / "cosyvoice3" / "automatic_metrics.json",
}


def load_payload(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def ok_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [row for row in payload["results"] if row.get("status") == "ok"]


def mean(rows: list[dict[str, Any]], key: str) -> float | None:
    values = [row[key] for row in rows if row.get(key) is not None]
    return float(np.mean(values)) if values else None


def weighted_rate(
    rows: list[dict[str, Any]],
    error_field: str,
    count_field: str,
) -> float | None:
    errors = sum(row[error_field] for row in rows if row.get(error_field) is not None)
    count = sum(row[count_field] for row in rows if row.get(count_field) is not None)
    return errors / count if count else None


def overall_rtf(rows: list[dict[str, Any]]) -> float:
    generation = sum(row["generation_seconds"] for row in rows)
    audio = sum(row["audio_seconds"] for row in rows)
    return generation / audio


def fmt(value: float | None) -> str:
    return "-" if value is None else f"{value:.3f}"


def pct(value: float | None) -> str:
    return "-" if value is None else f"{value:.2%}"


def main() -> None:
    payloads = {name: load_payload(path) for name, path in OUTPUTS.items()}
    summaries = {}
    for name, payload in payloads.items():
        rows = ok_rows(payload)
        summaries[name] = {
            "completed": len(rows),
            "mean_cer": mean(rows, "cer"),
            "weighted_cer": weighted_rate(rows, "character_errors", "reference_characters"),
            "mean_wer": mean(rows, "wer"),
            "weighted_wer": weighted_rate(rows, "word_errors", "reference_word_count"),
            "mean_rtf": mean(rows, "rtf"),
            "overall_rtf": overall_rtf(rows),
            "mean_utmos": mean(rows, "utmos"),
            "mean_sim_o": mean(rows, "sim_o"),
        }

    case_ids = [row["id"] for row in ok_rows(next(iter(payloads.values())))]
    rows_by_model = {
        name: {row["id"]: row for row in ok_rows(payload)}
        for name, payload in payloads.items()
    }

    lines = [
        "# Zero-shot 克隆模型对比",
        "",
        "## 结论快照",
        "",
        "| 模型 | 完成数 | 加权 CER | 加权 WER | 平均 RTF | 总体 RTF | 平均 UTMOS | 平均 SIM-o |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, summary in summaries.items():
        lines.append(
            f"| {name} | {summary['completed']} | {pct(summary['weighted_cer'])} | "
            f"{pct(summary['weighted_wer'])} | {fmt(summary['mean_rtf'])} | "
            f"{fmt(summary['overall_rtf'])} | {fmt(summary['mean_utmos'])} | "
            f"{fmt(summary['mean_sim_o'])} |"
        )

    lines.extend(
        [
            "",
            "## 分项结果",
            "",
            "| 用例 | 模型 | CER | WER | RTF | UTMOS | SIM-o | 音频时长 | 输出 |",
            "|---|---|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for case_id in case_ids:
        for model_name in payloads:
            row = rows_by_model[model_name].get(case_id)
            if row is None:
                continue
            output_dir = "dots_tts_mf" if model_name.startswith("dots") else "cosyvoice3"
            lines.append(
                f"| {row['name']} | {model_name} | {pct(row.get('cer'))} | "
                f"{pct(row.get('wer'))} | {fmt(row.get('rtf'))} | "
                f"{fmt(row.get('utmos'))} | {fmt(row.get('sim_o'))} | "
                f"{row['audio_seconds']:.3f} 秒 | "
                f"`outputs/{output_dir}/{Path(row['output_wav']).name}` |"
            )

    lines.extend(["", "## 自动判断", ""])
    for case_id in case_ids:
        candidates = [
            (model_name, rows_by_model[model_name][case_id])
            for model_name in payloads
            if case_id in rows_by_model[model_name]
        ]
        fastest = min(candidates, key=lambda item: item[1]["rtf"])
        best_utmos = max(candidates, key=lambda item: item[1]["utmos"])
        best_sim = max(candidates, key=lambda item: item[1]["sim_o"])
        best_cer = min(candidates, key=lambda item: item[1].get("cer", float("inf")))
        best_wer = min(candidates, key=lambda item: item[1].get("wer", float("inf")))
        case_name = candidates[0][1]["name"]
        lines.append(
            f"- {case_name}：CER 最低 `{best_cer[0]}`；WER 最低 `{best_wer[0]}`；"
            f"RTF 最低 `{fastest[0]}`；UTMOS 最高 `{best_utmos[0]}`；SIM-o 最高 `{best_sim[0]}`。"
        )

    lines.extend(
        [
            "",
            "## Whisper 回识别文本",
            "",
            "| 用例 | 模型 | 目标文本 | Whisper medium 回识别文本 |",
            "|---|---|---|---|",
        ]
    )
    for case_id in case_ids:
        for model_name in payloads:
            row = rows_by_model[model_name].get(case_id)
            if row is None:
                continue
            target = str(row.get("text", "")).replace("|", r"\|")
            transcript = str(row.get("whisper_transcript", "")).replace("|", r"\|")
            lines.append(f"| {row['name']} | {model_name} | {target} | {transcript} |")

    lines.extend(
        [
            "",
            "## 限制",
            "",
            "- CER/WER 来自 Whisper medium 回识别；ASR 错误也会计入指标，不能直接等同真人听写错误。",
            "- UTMOS 和 SIM-o 是自动指标，不能替代人工试听。",
            "- 英文用例使用 `cross_lingual_prompt.wav`，没有人工参考文本，因此两个模型都按无参考文本的 x-vector/cross-lingual 模式生成。",
            "- CosyVoice3 的长文本由官方前端切成 4 段后拼接；dots.tts 本轮是单次生成。",
            "- 部分输出存在超过绝对幅值 1.0 的样本，脚本已记录 clip count，试听时需要关注是否有爆音。",
            "",
            "## 产物",
            "",
            "- dots.tts：`experiments/zero_shot_comparison/outputs/dots_tts_mf`",
            "- CosyVoice3：`experiments/zero_shot_comparison/outputs/cosyvoice3`",
            "- 小数据微调准备：`experiments/small_multispeaker_finetune/genshin_20_speakers_5shot`",
            "",
        ]
    )

    payload = {"summaries": summaries, "models": list(payloads)}
    (EXPERIMENT_DIR / "comparison_summary.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (EXPERIMENT_DIR / "model_comparison.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )
    print(f"Saved report: {EXPERIMENT_DIR / 'model_comparison.md'}")


if __name__ == "__main__":
    main()
