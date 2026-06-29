#!/usr/bin/env python3
"""Evaluate the extended OmniVoice 20-speaker text comparison."""

from __future__ import annotations

import gc
import json
import os
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
import whisper

from evaluate_personal_voice_multilingual import (
    ECAPA_TDNN_WAVLM,
    EVAL_MODEL_DIR,
    UTMOS22Strong,
    error_rates,
    load_eval_waveform,
    load_whisper_audio,
    weighted_rate,
)


ROOT = Path(__file__).resolve().parents[1]
EVAL_DIR = ROOT / "evaluation" / "genshin_20_speakers_extended_texts"
DATA_SUMMARY = ROOT / "data" / "genshin_20_speakers" / "manifests" / "summary.json"
CATEGORY_NAMES = {
    "short_text": "短文本",
    "medium_long_text": "中长文本",
    "game_terms": "游戏专有词",
    "zh_en_mixed": "中英混合",
}


def percent(value: float | None) -> str:
    return "-" if value is None else f"{value:.2%}"


def mean_optional(rows: list[dict], field: str) -> float:
    values = [row[field] for row in rows if row.get(field) is not None]
    return float(np.mean(values)) if values else 0.0


def evaluate_whisper(rows: list[dict]) -> None:
    model = whisper.load_model("medium", device="cuda")
    for row in rows:
        options = {"fp16": True}
        if row.get("asr_language"):
            options["language"] = row["asr_language"]
        transcript = model.transcribe(load_whisper_audio(Path(row["output_wav"])), **options)[
            "text"
        ].strip()
        row["whisper_model"] = "medium"
        row["whisper_transcript"] = transcript
        row.update(error_rates(row["text"], transcript, row["language_id"]))
        print(f"Whisper {row['id']}: {transcript}")
    del model
    gc.collect()
    torch.cuda.empty_cache()


def evaluate_utmos(rows: list[dict]) -> None:
    model_path = EVAL_MODEL_DIR / "mos" / "utmos22_strong_step7459_v1.pt"
    model = UTMOS22Strong()
    model.load_state_dict(torch.load(model_path, map_location="cpu"))
    model.to("cuda").eval()
    with torch.no_grad():
        for row in rows:
            speech = load_eval_waveform(row["output_wav"], 16000, device="cuda")
            row["utmos"] = model(speech.unsqueeze(0), 16000).item()
    del model
    gc.collect()
    torch.cuda.empty_cache()


def evaluate_similarity(rows: list[dict]) -> None:
    ssl_path = EVAL_MODEL_DIR / "speaker_similarity" / "wavlm_large"
    model_path = EVAL_MODEL_DIR / "speaker_similarity" / "wavlm_large_finetune.pth"
    model = ECAPA_TDNN_WAVLM(
        feat_dim=1024,
        channels=512,
        emb_dim=256,
        sr=16000,
        ssl_model_path=str(ssl_path) + os.sep,
    )
    state = torch.load(model_path, map_location="cpu")
    model.load_state_dict(state["model"], strict=False)
    model.to("cuda").eval()
    references = {}
    with torch.no_grad():
        for row in rows:
            reference_path = row["reference_audio"]
            if reference_path not in references:
                reference = load_eval_waveform(reference_path, 16000, device="cuda")
                references[reference_path] = model([reference])
            speech = load_eval_waveform(row["output_wav"], 16000, device="cuda")
            embedding = model([speech])
            row["sim_o"] = torch.nn.functional.cosine_similarity(
                references[reference_path], embedding, dim=-1
            ).item()
    del model
    gc.collect()
    torch.cuda.empty_cache()


def summarize_rows(rows: list[dict], extra: dict | None = None) -> dict:
    summary = {
        "n": len(rows),
        "weighted_cer": weighted_rate(rows, "character_errors", "reference_characters"),
        "weighted_wer": weighted_rate(rows, "word_errors", "reference_word_count"),
        "weighted_pinyin_tone_error_rate": weighted_rate(
            rows, "pinyin_errors_with_tone", "reference_pinyin_count_with_tone"
        ),
        "weighted_pinyin_error_rate": weighted_rate(
            rows, "pinyin_errors_without_tone", "reference_pinyin_count_without_tone"
        ),
        "mean_utmos": mean_optional(rows, "utmos"),
        "mean_sim_o": mean_optional(rows, "sim_o"),
        "mean_rtf": mean_optional(rows, "rtf"),
        "overall_rtf": sum(row["generation_seconds"] for row in rows)
        / sum(row["audio_seconds"] for row in rows),
        "clipped_outputs": sum((row.get("clipped_samples") or 0) > 0 for row in rows),
    }
    if extra:
        summary.update(extra)
    return summary


def build_summaries(rows: list[dict], models: list[dict]) -> tuple[list[dict], list[dict]]:
    model_rows = defaultdict(list)
    category_rows = defaultdict(list)
    for row in rows:
        model_rows[row["model_name"]].append(row)
        category_rows[(row["model_name"], row["category"])].append(row)
    overall = [
        summarize_rows(model_rows[model["model_name"]], model)
        for model in models
    ]
    by_category = []
    for (model_name, category), items in sorted(category_rows.items()):
        by_category.append(
            summarize_rows(
                items,
                {
                    "model_name": model_name,
                    "category": category,
                    "category_name": CATEGORY_NAMES.get(category, category),
                },
            )
        )
    return overall, by_category


def pairwise_counts(rows: list[dict]) -> dict:
    paired = defaultdict(dict)
    for row in rows:
        paired[row["case_id"]][row["model_name"]] = row
    complete = [values for values in paired.values() if {"base", "finetuned_best"} <= values.keys()]
    return {
        "complete_pairs": len(complete),
        "sim_improved": sum(v["finetuned_best"]["sim_o"] > v["base"]["sim_o"] for v in complete),
        "utmos_improved": sum(v["finetuned_best"]["utmos"] > v["base"]["utmos"] for v in complete),
        "cer_improved": sum(v["finetuned_best"]["cer"] < v["base"]["cer"] for v in complete),
        "wer_improved": sum(v["finetuned_best"]["wer"] < v["base"]["wer"] for v in complete),
    }


def build_report(payload: dict, data_summary: dict) -> str:
    overall = payload["summaries"]
    by_category = payload["category_summaries"]
    base = next(row for row in overall if row["model_name"] == "base")
    tuned = next(row for row in overall if row["model_name"] == "finetuned_best")
    pairwise = payload["pairwise"]
    lines = [
        "# OmniVoice 原神 20 说话人扩展文本评测",
        "",
        "## 实验条件",
        "",
        f"- 文本类别：短文本、中长文本、游戏专有词、中英混合；每类 50 条，共 {payload['case_count']} 个 text-speaker case。",
        "- 评测方式：每个 case 使用一个未参与训练的验证音频作为 zero-shot prompt；base 与 finetuned_best 使用相同 case。",
        f"- 训练集：{data_summary['train_samples']} 条高质量音频，共 {data_summary['train_total_seconds'] / 60:.2f} 分钟；每位说话人 60 条。",
        f"- 验证集：{data_summary['dev_samples']} 条独立音频，共 {data_summary['dev_total_seconds'] / 60:.2f} 分钟；每位说话人 10 条。",
        "- 推理条件：32 steps、batch 1、warmup 后计时、固定随机种子 0。",
        "- 指标：Whisper medium 回识别 CER/WER，UTMOS22Strong，WavLM-large + ECAPA-TDNN SIM-o，RTF。",
        "",
        "## 总体结果",
        "",
        "| 模型 | n | CER | WER | 拼音错误率 | UTMOS | SIM-o | 平均 RTF | 总体 RTF |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in overall:
        lines.append(
            f"| {row['model_name']} | {row['n']} | {percent(row['weighted_cer'])} | "
            f"{percent(row['weighted_wer'])} | {percent(row['weighted_pinyin_error_rate'])} | "
            f"{row['mean_utmos']:.4f} | {row['mean_sim_o']:.4f} | "
            f"{row['mean_rtf']:.4f} | {row['overall_rtf']:.4f} |"
        )
    lines.extend(
        [
            "",
            "## 分类别结果",
            "",
            "| 类别 | 模型 | n | CER | WER | UTMOS | SIM-o | 总体 RTF |",
            "|---|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in by_category:
        lines.append(
            f"| {row['category_name']} | {row['model_name']} | {row['n']} | "
            f"{percent(row['weighted_cer'])} | {percent(row['weighted_wer'])} | "
            f"{row['mean_utmos']:.4f} | {row['mean_sim_o']:.4f} | {row['overall_rtf']:.4f} |"
        )
    lines.extend(
        [
            "",
            "## 对比结论",
            "",
            f"- CER：base {percent(base['weighted_cer'])}，finetuned_best {percent(tuned['weighted_cer'])}，变化 {percent(tuned['weighted_cer'] - base['weighted_cer'])}。",
            f"- WER：base {percent(base['weighted_wer'])}，finetuned_best {percent(tuned['weighted_wer'])}，变化 {percent(tuned['weighted_wer'] - base['weighted_wer'])}。",
            f"- SIM-o：base {base['mean_sim_o']:.4f}，finetuned_best {tuned['mean_sim_o']:.4f}。",
            f"- RTF：base {base['overall_rtf']:.4f}，finetuned_best {tuned['overall_rtf']:.4f}。",
            f"- 成对统计：{pairwise['complete_pairs']} 个 case 中，finetuned_best 的 SIM-o 更高 {pairwise['sim_improved']} 个，WER 更低 {pairwise['wer_improved']} 个。",
            "- CER/WER 依赖 Whisper medium 回识别，可能混入 ASR 误差；中英混合文本尤其需要结合人工试听。",
            "",
            "## 文件位置",
            "",
            "- 用例：`evaluation/genshin_20_speakers_extended_texts/cases.jsonl`",
            "- 生成结果：`evaluation/genshin_20_speakers_extended_texts/generation_results.json`",
            "- 自动指标：`evaluation/genshin_20_speakers_extended_texts/automatic_metrics.json`",
            "- 合成音频：`outputs/genshin_20_speakers_extended_texts`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    generation_path = EVAL_DIR / "generation_results.json"
    metrics_path = EVAL_DIR / "automatic_metrics.json"
    payload = json.loads(generation_path.read_text(encoding="utf-8"))
    rows = payload["results"]
    evaluate_whisper(rows)
    evaluate_utmos(rows)
    evaluate_similarity(rows)
    payload["summaries"], payload["category_summaries"] = build_summaries(rows, payload["models"])
    payload["pairwise"] = pairwise_counts(rows)
    metrics_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    data_summary = json.loads(DATA_SUMMARY.read_text(encoding="utf-8"))
    report_path = EVAL_DIR / "comparison_report.md"
    report_path.write_text(build_report(payload, data_summary), encoding="utf-8")
    print(f"Saved metrics: {metrics_path}")
    print(f"Saved report: {report_path}")


if __name__ == "__main__":
    main()
