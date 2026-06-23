#!/usr/bin/env python3
"""Evaluate and report the extended 20-speaker Genshin fine-tune benchmark."""

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
EVAL_DIR = ROOT / "evaluation" / "genshin_20_speakers_1200_extended"


def percent(value: float | None) -> str:
    return "-" if value is None else f"{value:.2%}"


def evaluate_whisper(rows: list[dict]) -> None:
    model = whisper.load_model("medium", device="cuda")
    for row in rows:
        transcript = model.transcribe(
            load_whisper_audio(Path(row["output_wav"])),
            language=row["asr_language"],
            fp16=True,
        )["text"].strip()
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
    reference_embeddings = {}
    with torch.no_grad():
        for row in rows:
            reference = row["reference_audio"]
            if reference not in reference_embeddings:
                waveform = load_eval_waveform(reference, 16000, device="cuda")
                reference_embeddings[reference] = model([waveform])
            speech = load_eval_waveform(row["output_wav"], 16000, device="cuda")
            embedding = model([speech])
            row["sim_o"] = torch.nn.functional.cosine_similarity(
                reference_embeddings[reference], embedding, dim=-1
            ).item()
    del model
    gc.collect()
    torch.cuda.empty_cache()


def summarize(rows: list[dict]) -> dict:
    total_generation = sum(row["generation_seconds"] for row in rows)
    total_audio = sum(row["audio_seconds"] for row in rows)
    return {
        "count": len(rows),
        "weighted_cer": weighted_rate(rows, "character_errors", "reference_characters"),
        "weighted_wer": weighted_rate(rows, "word_errors", "reference_word_count"),
        "weighted_pinyin_tone_error_rate": weighted_rate(
            rows, "pinyin_errors_with_tone", "reference_pinyin_count_with_tone"
        ),
        "weighted_pinyin_error_rate": weighted_rate(
            rows, "pinyin_errors_without_tone", "reference_pinyin_count_without_tone"
        ),
        "mean_utmos": float(np.mean([row["utmos"] for row in rows])),
        "mean_sim_o": float(np.mean([row["sim_o"] for row in rows])),
        "mean_rtf": float(np.mean([row["rtf"] for row in rows])),
        "overall_rtf": total_generation / total_audio,
        "clipped_outputs": sum(row["clipped_samples"] > 0 for row in rows),
    }


def build_summaries(rows: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    by_category = defaultdict(list)
    by_model = defaultdict(list)
    by_case = defaultdict(list)
    for row in rows:
        by_category[(row["model_name"], row["category_id"], row["category_name"])].append(row)
        by_model[row["model_name"]].append(row)
        by_case[(row["model_name"], row["case_id"], row["case_name"])].append(row)
    category = [
        {
            "model_name": key[0],
            "category_id": key[1],
            "category_name": key[2],
            **summarize(value),
        }
        for key, value in by_category.items()
    ]
    overall = [
        {"model_name": model_name, **summarize(value)}
        for model_name, value in by_model.items()
    ]
    cases = [
        {
            "model_name": key[0],
            "case_id": key[1],
            "case_name": key[2],
            **summarize(value),
        }
        for key, value in by_case.items()
    ]
    return category, overall, cases


def summary_row(row: dict) -> str:
    return (
        f"| {row['model_name']} | {row['count']} | {percent(row['weighted_cer'])} "
        f"| {percent(row['weighted_wer'])} | {percent(row['weighted_pinyin_tone_error_rate'])} "
        f"| {row['mean_utmos']:.4f} | {row['mean_sim_o']:.4f} "
        f"| {row['mean_rtf']:.4f} | {row['overall_rtf']:.4f} |"
    )


def build_report(payload: dict) -> str:
    rows = payload["results"]
    category = payload["category_summaries"]
    overall = payload["overall_summaries"]
    cases = payload["case_summaries"]
    overall_map = {row["model_name"]: row for row in overall}
    category_map = {
        (row["category_id"], row["model_name"]): row
        for row in category
    }
    base = overall_map["base"]
    tuned = overall_map["finetuned_best"]
    lines = [
        "# OmniVoice 原神 20 说话人微调扩展评估",
        "",
        "## 实验条件",
        "",
        "- 对比模型：基础模型与 1200 条训练数据微调后的最佳模型 `best`（checkpoint-200）。",
        f"- 已见说话人：{'、'.join(payload['seen_speakers'])}。",
        f"- 未见说话人：`{payload['unseen_reference']['speaker']}`，参考音频来自 AISHELL-3，未参与原神数据微调。",
        "- 测试类别：中文长文本、多音字、游戏专有词与角色名、中英混合、英文、未见说话人 zero-shot。",
        "- 每个已见说话人对前五类各测试 3 条文本；未见说话人测试 3 条文本。",
        "- 合计：每个模型 63 条输出，共 126 条输出。",
        "- 推理条件：32 步、Batch 1、模型预热后计时、固定随机种子 0。",
        "- 指标：Whisper medium CER/WER、拼音错误率、UTMOS、SIM-o、RTF。",
        "",
        "## 总体多文本平均结果",
        "",
        "| 模型 | 数量 | CER | WER | 带声调拼音错误率 | UTMOS | SIM-o | 平均 RTF | 总体 RTF |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in overall:
        lines.append(summary_row(row))
    lines.extend(
        [
            "",
            "## 分类平均结果",
            "",
            "| 类别 | 模型 | 数量 | CER | WER | 带声调拼音错误率 | UTMOS | SIM-o | 平均 RTF | 总体 RTF |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in sorted(category, key=lambda item: (item["category_id"], item["model_name"])):
        lines.append(f"| {row['category_name']} |" + summary_row(row)[1:])
    long_base = category_map[("long_zh", "base")]
    long_tuned = category_map[("long_zh", "finetuned_best")]
    poly_base = category_map[("polyphone", "base")]
    poly_tuned = category_map[("polyphone", "finetuned_best")]
    game_base = category_map[("game_terms", "base")]
    game_tuned = category_map[("game_terms", "finetuned_best")]
    mixed_base = category_map[("mixed", "base")]
    mixed_tuned = category_map[("mixed", "finetuned_best")]
    english_base = category_map[("english", "base")]
    english_tuned = category_map[("english", "finetuned_best")]
    unseen_base = category_map[("unseen_zero_shot", "base")]
    unseen_tuned = category_map[("unseen_zero_shot", "finetuned_best")]
    lines.extend(
        [
            "",
            "## 对比结论",
            "",
            f"- 总体：微调模型 CER 从 {percent(base['weighted_cer'])} 降至 {percent(tuned['weighted_cer'])}，WER 从 {percent(base['weighted_wer'])} 降至 {percent(tuned['weighted_wer'])}；UTMOS 与 SIM-o 均略有提高，整体 RTF 基本不变。",
            f"- 中文长文本：CER 从 {percent(long_base['weighted_cer'])} 降至 {percent(long_tuned['weighted_cer'])}，SIM-o 从 {long_base['mean_sim_o']:.4f} 升至 {long_tuned['mean_sim_o']:.4f}，但 UTMOS 略降。",
            f"- 多音字：微调后 CER 从 {percent(poly_base['weighted_cer'])} 升至 {percent(poly_tuned['weighted_cer'])}，说明当前微调没有提升多音字稳定性。",
            f"- 游戏专有词与角色名：两组错误率均明显偏高，微调后 CER 从 {percent(game_base['weighted_cer'])} 升至 {percent(game_tuned['weighted_cer'])}；需要专门增加角色名和专有词训练文本，并结合人工试听排除 ASR 误识别。",
            f"- 中英混合：微调后 CER 从 {percent(mixed_base['weighted_cer'])} 降至 {percent(mixed_tuned['weighted_cer'])}，WER 从 {percent(mixed_base['weighted_wer'])} 降至 {percent(mixed_tuned['weighted_wer'])}，是本轮改善最明显的类别。",
            f"- 英文：基础与微调模型 CER/WER 均为 0；微调模型 SIM-o 从 {english_base['mean_sim_o']:.4f} 升至 {english_tuned['mean_sim_o']:.4f}，未观察到明显英文能力退化。",
            f"- 未见说话人 zero-shot：两组 CER/WER 均为 0，微调模型 SIM-o 从 {unseen_base['mean_sim_o']:.4f} 升至 {unseen_tuned['mean_sim_o']:.4f}，当前测试中未出现明显泛化能力退化。",
            "",
            "## 人工试听结论",
            "",
            "- 微调模型并非全面优于基础模型，主要改善了部分角色的音色与部分长文本流畅度。",
            "- 微调后的荒泷一斗长文本第 1 条、纳西妲游戏文本和钟离长文本主观表现更好。",
            "- 派蒙仍存在较明显的停顿异常、语速过慢、有气无力、重音错误与音色漂移问题。",
            "- 英文和中英混合文本中，`system` 等英语单词发音不清晰、英语片段不流畅及停顿异常较常见。",
            "- 多个游戏专有词文本存在停顿与流畅度问题；高 CER/WER 不能完整反映这些主观缺陷。",
            "- 长文本仍可能出现音色漂移、多个音色、机械感、卡顿和背景杂音。",
            "- 未列出的输出整体表现稍微正常。完整逐条记录见 `manual_listening_evaluation.md`。",
            "",
            "## 每条测试文本平均结果",
            "",
            "| 测试文本 | 模型 | 数量 | CER | WER | 带声调拼音错误率 | UTMOS | SIM-o | 平均 RTF | 总体 RTF |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in sorted(cases, key=lambda item: (item["case_id"], item["model_name"])):
        lines.append(f"| {row['case_name']} |" + summary_row(row)[1:])
    lines.extend(
        [
            "",
            "## Whisper 回识别与输出音频",
            "",
            "| 模型 | 类别 | 说话人 | 测试文本 | Whisper 回识别文本 | CER | WER | 输出音频 |",
            "|---|---|---|---|---|---:|---:|---|",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['model_name']} | {row['category_name']} | {row['speaker']} "
            f"| {row['text']} | {row['whisper_transcript']} | {percent(row['cer'])} "
            f"| {percent(row['wer'])} | `{Path(row['output_wav']).relative_to(ROOT)}` |"
        )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- CER/WER 同时受到合成发音和 Whisper 识别误差影响，角色名与游戏专有词尤其需要人工试听确认。",
            "- 英文输出的拼音错误率不适用，因此分类统计中该项为 0，不应作为英文指标使用。",
            "- SIM-o 衡量与对应参考音频的声纹嵌入余弦相似度；不同语言和文本长度会影响分数。",
            "",
            "## 文件位置",
            "",
            "- 合成音频：`outputs/genshin_20_speakers_1200_extended`",
            "- 完整指标：`evaluation/genshin_20_speakers_1200_extended/automatic_metrics.json`",
            "- 生成结果：`evaluation/genshin_20_speakers_1200_extended/generation_results.json`",
            "- 人工试听记录：`evaluation/genshin_20_speakers_1200_extended/manual_listening_evaluation.md`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    generation_path = EVAL_DIR / "generation_results.json"
    payload = json.loads(generation_path.read_text(encoding="utf-8"))
    rows = payload["results"]
    evaluate_whisper(rows)
    evaluate_utmos(rows)
    evaluate_similarity(rows)
    category, overall, cases = build_summaries(rows)
    payload["category_summaries"] = category
    payload["overall_summaries"] = overall
    payload["case_summaries"] = cases
    metrics_path = EVAL_DIR / "automatic_metrics.json"
    metrics_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    report_path = EVAL_DIR / "comparison_report.md"
    report_path.write_text(build_report(payload), encoding="utf-8")
    print(f"Saved metrics: {metrics_path}")
    print(f"Saved report: {report_path}")


if __name__ == "__main__":
    main()
