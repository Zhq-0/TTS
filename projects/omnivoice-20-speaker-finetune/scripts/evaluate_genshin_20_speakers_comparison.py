#!/usr/bin/env python3
"""Evaluate the OmniVoice 20-speaker Genshin fine-tune and write a Chinese report."""

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
EVAL_DIR = ROOT / "evaluation" / "genshin_20_speakers_1200_finetune"
DATA_SUMMARY = ROOT / "data" / "genshin_20_speakers" / "manifests" / "summary.json"


def percent(value: float | None) -> str:
    return "-" if value is None else f"{value:.2%}"


def evaluate_whisper(rows: list[dict]) -> None:
    model = whisper.load_model("medium", device="cuda")
    for row in rows:
        transcript = model.transcribe(
            load_whisper_audio(Path(row["output_wav"])), language="zh", fp16=True
        )["text"].strip()
        row["whisper_model"] = "medium"
        row["whisper_transcript"] = transcript
        row.update(error_rates(row["text"], transcript, "zh"))
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


def summaries(rows: list[dict], models: list[dict]) -> list[dict]:
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["model_name"]].append(row)
    output = []
    for model in models:
        model_rows = grouped[model["model_name"]]
        output.append(
            {
                **model,
                "weighted_cer": weighted_rate(model_rows, "character_errors", "reference_characters"),
                "weighted_wer": weighted_rate(model_rows, "word_errors", "reference_word_count"),
                "weighted_pinyin_tone_error_rate": weighted_rate(
                    model_rows, "pinyin_errors_with_tone", "reference_pinyin_count_with_tone"
                ),
                "weighted_pinyin_error_rate": weighted_rate(
                    model_rows, "pinyin_errors_without_tone", "reference_pinyin_count_without_tone"
                ),
                "mean_utmos": float(np.mean([row["utmos"] for row in model_rows])),
                "mean_sim_o": float(np.mean([row["sim_o"] for row in model_rows])),
                "mean_rtf": float(np.mean([row["rtf"] for row in model_rows])),
                "overall_rtf": sum(row["generation_seconds"] for row in model_rows)
                / sum(row["audio_seconds"] for row in model_rows),
                "clipped_outputs": sum(row["clipped_samples"] > 0 for row in model_rows),
            }
        )
    return output


def build_report(payload: dict, data_summary: dict) -> str:
    rows = payload["results"]
    result_summaries = payload["summaries"]
    base = next(row for row in result_summaries if row["model_name"] == "base")
    tuned = next(row for row in result_summaries if row["model_name"] == "finetuned_best")
    speakers = "、".join(item["speaker"] for item in data_summary["speakers"])
    paired = defaultdict(dict)
    for row in rows:
        paired[row["speaker"]][row["model_name"]] = row
    sim_improved = sum(
        values["finetuned_best"]["sim_o"] > values["base"]["sim_o"]
        for values in paired.values()
    )
    utmos_improved = sum(
        values["finetuned_best"]["utmos"] > values["base"]["utmos"]
        for values in paired.values()
    )
    lines = [
        "# OmniVoice 原神 20 说话人 1200 条训练数据微调对比",
        "",
        "## 实验条件",
        "",
        f"- 说话人：{speakers}。",
        f"- 训练集：{data_summary['train_samples']} 条高质量音频，共 {data_summary['train_total_seconds'] / 60:.2f} 分钟；每位说话人 60 条。",
        f"- 验证集：{data_summary['dev_samples']} 条独立音频，共 {data_summary['dev_total_seconds'] / 60:.2f} 分钟；每位说话人 10 条。",
        "- 筛选规则：文本完整度、音频时长、响度、静音比例、削波情况及说话人可用样本量。",
        "- 微调配置：400 steps、学习率 `2e-6`、SDPA、BF16；每 100 steps 保存并评估一次。",
        "- 正式对比采用验证集 Loss 最低的检查点，并复制到 `best` 目录。",
        "- 推理条件：32 步、Batch 1、预热后计时、固定随机种子 0。",
        f"- 固定测试文本：{payload['target_text']}",
        "- 每位说话人均使用未参与训练的验证音频作为零样本克隆参考。",
        "",
        "## 训练检查点",
        "",
        "| 检查点 | 验证集 Loss |",
        "|---|---:|",
        "| checkpoint-100 | 4.1361 |",
        "| checkpoint-200（最佳） | **3.9543** |",
        "| checkpoint-300 | 4.1102 |",
        "| checkpoint-400 | 4.0033 |",
        "",
        "## 综合结果",
        "",
        "| 模型 | CER | WER | 带声调拼音错误率 | 不带声调拼音错误率 | UTMOS | SIM-o | 平均 RTF | 总体 RTF |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in result_summaries:
        lines.append(
            f"| {row['model_name']} | {percent(row['weighted_cer'])} | {percent(row['weighted_wer'])} "
            f"| {percent(row['weighted_pinyin_tone_error_rate'])} | {percent(row['weighted_pinyin_error_rate'])} "
            f"| {row['mean_utmos']:.4f} | {row['mean_sim_o']:.4f} | {row['mean_rtf']:.4f} | {row['overall_rtf']:.4f} |"
        )
    lines.extend(
        [
            "",
            "## 对比结论",
            "",
            f"- CER：基础模型 {percent(base['weighted_cer'])}，微调模型 {percent(tuned['weighted_cer'])}，变化 {percent(tuned['weighted_cer'] - base['weighted_cer'])}。",
            f"- WER：基础模型 {percent(base['weighted_wer'])}，微调模型 {percent(tuned['weighted_wer'])}，变化 {percent(tuned['weighted_wer'] - base['weighted_wer'])}。",
            f"- UTMOS：基础模型 {base['mean_utmos']:.4f}，微调模型 {tuned['mean_utmos']:.4f}。",
            f"- SIM-o：基础模型 {base['mean_sim_o']:.4f}，微调模型 {tuned['mean_sim_o']:.4f}。",
            f"- 总体 RTF：基础模型 {base['overall_rtf']:.4f}，微调模型 {tuned['overall_rtf']:.4f}；微调未改变模型结构，因此推理速度应接近。",
            f"- 逐说话人统计：微调模型在 20 个说话人中的 {sim_improved} 个 SIM-o 更高，{utmos_improved} 个 UTMOS 更高。",
            "- CER/WER 由 Whisper medium 回识别计算，可能同时包含 TTS 发音错误与 ASR 识别错误，需结合试听判断。",
            "- 当前测试只覆盖一条固定中文短文本，不能代表长文本、英文、中英混合文本和游戏专有词表现。",
            "",
            "## 逐说话人结果",
            "",
            "| 模型 | 说话人 | RTF | CER | WER | 拼音错误率（带/不带声调） | UTMOS | SIM-o | Whisper 回识别文本 | 输出音频 |",
            "|---|---|---:|---:|---:|---:|---:|---:|---|---|",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['model_name']} | {row['speaker']} | {row['rtf']:.4f} | {percent(row['cer'])} "
            f"| {percent(row['wer'])} | {percent(row['pinyin_error_rate_with_tone'])} / "
            f"{percent(row['pinyin_error_rate_without_tone'])} | {row['utmos']:.4f} | {row['sim_o']:.4f} "
            f"| {row['whisper_transcript']} | `{Path(row['output_wav']).relative_to(ROOT)}` |"
        )
    lines.extend(
        [
            "",
            "## 文件位置",
            "",
            "- 数据筛选详情：`data/genshin_20_speakers/manifests/selection_details.jsonl`",
            "- 训练检查点：`exp/genshin_20_speakers_1200_sdpa`",
            "- 合成音频：`outputs/genshin_20_speakers_1200_finetune`",
            "- 完整自动指标：`evaluation/genshin_20_speakers_1200_finetune/automatic_metrics.json`",
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
    payload["summaries"] = summaries(rows, payload["models"])
    metrics_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    data_summary = json.loads(DATA_SUMMARY.read_text(encoding="utf-8"))
    report_path = EVAL_DIR / "comparison_report.md"
    report_path.write_text(build_report(payload, data_summary), encoding="utf-8")
    print(f"Saved metrics: {metrics_path}")
    print(f"Saved report: {report_path}")


if __name__ == "__main__":
    main()
