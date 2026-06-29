from argparse import ArgumentParser
from collections import defaultdict
from pathlib import Path
import importlib.util
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import jieba
import onnxruntime
from opencc import OpenCC
from pypinyin import lazy_pinyin, Style
import torch
import torchaudio
import torchaudio.compliance.kaldi as kaldi
import whisper


EXPERIMENT_DIR = Path(__file__).resolve().parent
MODEL_DIR = ROOT / "pretrained_models" / "Fun-CosyVoice3-0.5B"
OUTPUT_DIR = EXPERIMENT_DIR / "outputs" / "extended_comparison"
EVAL_DIR = EXPERIMENT_DIR / "evaluation" / "extended_comparison"
OMNIVOICE_EVAL_MODEL_DIR = ROOT.parent / "OmniVoice" / "pretrained_models" / "TTS_eval_models"
OMNIVOICE_UTMOS_PY = ROOT.parent / "OmniVoice" / "omnivoice" / "eval" / "models" / "utmos.py"
DEFAULT_VARIANTS = ("base", "clean_epoch_2")
opencc = OpenCC("t2s")


def parse_args():
    parser = ArgumentParser(description="Evaluate extended CosyVoice3 comparison outputs.")
    parser.add_argument("--variants", nargs="+", default=list(DEFAULT_VARIANTS))
    parser.add_argument("--whisper-model", default="medium")
    parser.add_argument("--skip-utmos", action="store_true")
    return parser.parse_args()


def levenshtein(reference, hypothesis):
    previous = list(range(len(hypothesis) + 1))
    for ref_index, ref_item in enumerate(reference, start=1):
        current = [ref_index]
        for hyp_index, hyp_item in enumerate(hypothesis, start=1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[hyp_index] + 1,
                    previous[hyp_index - 1] + (ref_item != hyp_item),
                )
            )
        previous = current
    return previous[-1]


def normalize_text(text):
    text = opencc.convert(text).lower()
    return "".join(re.findall(r"[\u4e00-\u9fffA-Za-z0-9]+", text))


def to_pinyin(text, with_tone):
    style = Style.TONE3 if with_tone else Style.NORMAL
    return lazy_pinyin(
        text,
        style=style,
        neutral_tone_with_five=with_tone,
        errors=lambda characters: list(characters),
    )


def safe_divide(numerator, denominator):
    return numerator / denominator if denominator else 0.0


def calculate_error_rates(reference, hypothesis):
    reference_normalized = normalize_text(reference)
    hypothesis_normalized = normalize_text(hypothesis)
    char_errors = levenshtein(reference_normalized, hypothesis_normalized)
    reference_words = list(jieba.cut(reference_normalized))
    hypothesis_words = list(jieba.cut(hypothesis_normalized))
    word_errors = levenshtein(reference_words, hypothesis_words)
    reference_pinyin_tone = to_pinyin(reference_normalized, with_tone=True)
    hypothesis_pinyin_tone = to_pinyin(hypothesis_normalized, with_tone=True)
    pinyin_tone_errors = levenshtein(reference_pinyin_tone, hypothesis_pinyin_tone)
    reference_pinyin_no_tone = to_pinyin(reference_normalized, with_tone=False)
    hypothesis_pinyin_no_tone = to_pinyin(hypothesis_normalized, with_tone=False)
    pinyin_no_tone_errors = levenshtein(reference_pinyin_no_tone, hypothesis_pinyin_no_tone)
    return {
        "reference_normalized": reference_normalized,
        "hypothesis_normalized": hypothesis_normalized,
        "character_errors": char_errors,
        "reference_characters": len(reference_normalized),
        "cer": safe_divide(char_errors, len(reference_normalized)),
        "reference_words": reference_words,
        "hypothesis_words": hypothesis_words,
        "word_errors": word_errors,
        "reference_word_count": len(reference_words),
        "wer": safe_divide(word_errors, len(reference_words)),
        "pinyin_errors_with_tone": pinyin_tone_errors,
        "reference_pinyin_count_with_tone": len(reference_pinyin_tone),
        "pinyin_error_rate_with_tone": safe_divide(pinyin_tone_errors, len(reference_pinyin_tone)),
        "pinyin_errors_without_tone": pinyin_no_tone_errors,
        "reference_pinyin_count_without_tone": len(reference_pinyin_no_tone),
        "pinyin_error_rate_without_tone": safe_divide(pinyin_no_tone_errors, len(reference_pinyin_no_tone)),
    }


def load_rows(variants):
    rows = []
    for variant in variants:
        path = OUTPUT_DIR / variant / "results.json"
        if not path.exists():
            raise FileNotFoundError(path)
        rows.extend(json.loads(path.read_text(encoding="utf-8")))
    return [row for row in rows if row.get("status") == "ok"]


def create_campplus_session():
    options = onnxruntime.SessionOptions()
    options.graph_optimization_level = onnxruntime.GraphOptimizationLevel.ORT_ENABLE_ALL
    options.intra_op_num_threads = 1
    return onnxruntime.InferenceSession(
        str(MODEL_DIR / "campplus.onnx"),
        sess_options=options,
        providers=["CPUExecutionProvider"],
    )


def load_audio_mono(wav_path, target_rate=None):
    audio, sample_rate = torchaudio.load(wav_path)
    audio = audio.mean(dim=0, keepdim=True)
    if target_rate and sample_rate != target_rate:
        audio = torchaudio.transforms.Resample(sample_rate, target_rate)(audio)
        sample_rate = target_rate
    return audio, sample_rate


def extract_embedding(session, wav_path):
    audio, _ = load_audio_mono(wav_path, target_rate=16000)
    feature = kaldi.fbank(audio, num_mel_bins=80, dither=0, sample_frequency=16000)
    feature = feature - feature.mean(dim=0, keepdim=True)
    embedding = session.run(
        None,
        {session.get_inputs()[0].name: feature.unsqueeze(dim=0).numpy()},
    )[0].flatten()
    return torch.from_numpy(embedding)


def load_asr_audio(wav_path):
    audio, _ = load_audio_mono(wav_path, target_rate=16000)
    return audio.squeeze(0).numpy()


def create_utmos_model():
    model_path = OMNIVOICE_EVAL_MODEL_DIR / "mos" / "utmos22_strong_step7459_v1.pt"
    if not model_path.exists() or not OMNIVOICE_UTMOS_PY.exists():
        return None
    spec = importlib.util.spec_from_file_location("omnivoice_utmos_model", OMNIVOICE_UTMOS_PY)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = module.UTMOS22Strong()
    model.load_state_dict(torch.load(model_path, map_location="cpu"))
    model.to(device).eval()
    return model


def evaluate_utmos(model, wav_path):
    if model is None:
        return None
    device = next(model.parameters()).device
    audio, _ = load_audio_mono(wav_path, target_rate=16000)
    with torch.inference_mode():
        return float(model(audio.squeeze(0).to(device).unsqueeze(0), 16000).item())


def mean(rows, key):
    values = [row[key] for row in rows if row.get(key) is not None]
    return sum(values) / len(values) if values else 0.0


def weighted_rate(rows, errors_key, count_key):
    errors = sum(row.get(errors_key, 0) for row in rows)
    count = sum(row.get(count_key, 0) for row in rows)
    return safe_divide(errors, count)


def summarize(rows):
    return {
        "n": len(rows),
        "cer": weighted_rate(rows, "character_errors", "reference_characters"),
        "wer": weighted_rate(rows, "word_errors", "reference_word_count"),
        "pinyin_error_rate_without_tone": weighted_rate(
            rows, "pinyin_errors_without_tone", "reference_pinyin_count_without_tone"
        ),
        "mean_sim": mean(rows, "speaker_cosine_similarity"),
        "mean_utmos": mean(rows, "utmos"),
        "mean_rtf": mean(rows, "rtf"),
        "overall_rtf": safe_divide(
            sum(row.get("generation_seconds", 0.0) for row in rows),
            sum(row.get("audio_seconds", 0.0) for row in rows),
        ),
    }


def percent(value):
    return f"{value * 100:.2f}%"


def grouped_summaries(rows, key):
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row[key], row["variant"])].append(row)
    return [
        {"group": group, "variant": variant, **summarize(group_rows)}
        for (group, variant), group_rows in sorted(grouped.items())
    ]


def pairwise_stats(rows):
    by_case = defaultdict(dict)
    for row in rows:
        by_case[row["case_id"]][row["variant"]] = row
    complete = [values for values in by_case.values() if all(v in values for v in DEFAULT_VARIANTS)]
    return {
        "complete_pairs": len(complete),
        "sim_improved": sum(v["clean_epoch_2"]["speaker_cosine_similarity"] > v["base"]["speaker_cosine_similarity"] for v in complete),
        "wer_improved": sum(v["clean_epoch_2"]["wer"] < v["base"]["wer"] for v in complete),
        "cer_improved": sum(v["clean_epoch_2"]["cer"] < v["base"]["cer"] for v in complete),
        "utmos_improved": sum(v["clean_epoch_2"].get("utmos", 0.0) > v["base"].get("utmos", 0.0) for v in complete),
    }


def write_report(rows, variants, whisper_model, skip_utmos):
    by_variant = {variant: [row for row in rows if row["variant"] == variant] for variant in variants}
    summaries = {variant: summarize(items) for variant, items in by_variant.items()}
    split_summaries = grouped_summaries(rows, "split")
    category_summaries = grouped_summaries(rows, "category")
    pairwise = pairwise_stats(rows)
    lines = [
        "# CosyVoice3 四角色 LLM-only 微调补测",
        "",
        "## 实验条件",
        "",
        "- 对比模型：`base` 与 `clean_epoch_2`。",
        "- 测试规模：已见 4 角色每人 25 条文本，未见 8 角色每人 10 条文本，共 180 个 case；两模型共 360 条生成音频。",
        "- 文本类型：困难短句、普通短句、游戏专有词、中长文本、中英混合。",
        "- 评测方式：base 与 clean_epoch_2 使用相同 prompt audio、prompt text、target text 和随机种子。",
        f"- ASR：Whisper `{whisper_model}` 回识别后计算 CER/WER；SIM 使用 CampPlus prompt-output cosine similarity。",
        "- RTF 仅作为推理耗时记录，不作为微调收益结论。",
    ]
    if skip_utmos:
        lines.append("- UTMOS：本次按参数跳过。")
    else:
        lines.append("- UTMOS：UTMOS22Strong 无参考自然度估计。")
    lines.extend(
        [
            "",
            "## 总体结果",
            "",
            "| 模型 | n | CER | WER | 拼音错误率 | SIM | UTMOS | 总体 RTF |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for variant in variants:
        row = summaries[variant]
        lines.append(
            f"| {variant} | {row['n']} | {percent(row['cer'])} | {percent(row['wer'])} | "
            f"{percent(row['pinyin_error_rate_without_tone'])} | {row['mean_sim']:.4f} | "
            f"{row['mean_utmos']:.4f} | {row['overall_rtf']:.4f} |"
        )
    lines.extend(
        [
            "",
            "## 已见 / 未见说话人",
            "",
            "| split | 模型 | n | CER | WER | SIM | UTMOS |",
            "|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in split_summaries:
        lines.append(
            f"| {row['group']} | {row['variant']} | {row['n']} | {percent(row['cer'])} | "
            f"{percent(row['wer'])} | {row['mean_sim']:.4f} | {row['mean_utmos']:.4f} |"
        )
    lines.extend(
        [
            "",
            "## 分文本类型结果",
            "",
            "| 类别 | 模型 | n | CER | WER | SIM | UTMOS |",
            "|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in category_summaries:
        lines.append(
            f"| {row['group']} | {row['variant']} | {row['n']} | {percent(row['cer'])} | "
            f"{percent(row['wer'])} | {row['mean_sim']:.4f} | {row['mean_utmos']:.4f} |"
        )
    lines.extend(
        [
            "",
            "## 成对统计",
            "",
            f"- 完整成对 case：{pairwise['complete_pairs']}。",
            f"- clean_epoch_2 CER 更低：{pairwise['cer_improved']} 个。",
            f"- clean_epoch_2 WER 更低：{pairwise['wer_improved']} 个。",
            f"- clean_epoch_2 SIM 更高：{pairwise['sim_improved']} 个。",
            f"- clean_epoch_2 UTMOS 更高：{pairwise['utmos_improved']} 个。",
            "",
            "## 文件位置",
            "",
            "- cases：`evaluation/extended_comparison/cases.jsonl`",
            "- 自动指标：`evaluation/extended_comparison/automatic_metrics.json`",
            "- 合成音频：`outputs/extended_comparison`",
        ]
    )
    (EVAL_DIR / "extended_comparison_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    summary = {
        "summaries": summaries,
        "split_summaries": split_summaries,
        "category_summaries": category_summaries,
        "pairwise": pairwise,
    }
    (EVAL_DIR / "extended_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main():
    args = parse_args()
    variants = tuple(args.variants)
    rows = load_rows(variants)
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    campplus = create_campplus_session()
    asr_model = whisper.load_model(args.whisper_model)
    utmos = None if args.skip_utmos else create_utmos_model()
    prompt_cache = {}
    results = []
    for index, row in enumerate(rows, start=1):
        transcript = asr_model.transcribe(
            load_asr_audio(row["output_wav"]),
            language="zh",
            task="transcribe",
            temperature=0,
            beam_size=5,
            condition_on_previous_text=False,
            fp16=torch.cuda.is_available(),
        )["text"].strip()
        rates = calculate_error_rates(row["target_text"], transcript)
        prompt_wav = row["prompt_wav"]
        if prompt_wav not in prompt_cache:
            prompt_cache[prompt_wav] = extract_embedding(campplus, prompt_wav)
        output_embedding = extract_embedding(campplus, row["output_wav"])
        similarity = torch.nn.functional.cosine_similarity(
            prompt_cache[prompt_wav].unsqueeze(0),
            output_embedding.unsqueeze(0),
        ).item()
        result = {
            **row,
            "whisper_model": args.whisper_model,
            "whisper_transcript": transcript,
            **rates,
            "speaker_cosine_similarity": similarity,
            "utmos": evaluate_utmos(utmos, row["output_wav"]),
        }
        results.append(result)
        print(
            f"[{index}/{len(rows)}] {row['variant']} {row['case_id']}: "
            f"CER={rates['cer']:.2%}, WER={rates['wer']:.2%}, "
            f"SIM={similarity:.4f}, UTMOS={result['utmos']}"
        )
    (EVAL_DIR / "automatic_metrics.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    write_report(results, variants, args.whisper_model, args.skip_utmos)


if __name__ == "__main__":
    main()
