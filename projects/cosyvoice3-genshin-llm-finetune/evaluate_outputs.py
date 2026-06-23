from argparse import ArgumentParser
from collections import defaultdict
from pathlib import Path
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
OUTPUTS_DIR = EXPERIMENT_DIR / "outputs"
EVALUATION_DIR = EXPERIMENT_DIR / "evaluation"
SPEAKERS = ("paimon", "zhongli", "ganyu", "yae_miko")
SPEAKER_NAMES = {
    "paimon": "Paimon",
    "zhongli": "Zhongli",
    "ganyu": "Ganyu",
    "yae_miko": "Yae Miko",
}
DEFAULT_VARIANTS = ("base", "clean_epoch_0", "clean_epoch_1", "clean_epoch_2")


def parse_args():
    parser = ArgumentParser(description="Evaluate CosyVoice3 four-character fixed-condition outputs.")
    parser.add_argument(
        "--test-set",
        choices=("common_line", "character_lines", "generic_short", "long_text"),
        default="common_line",
    )
    parser.add_argument(
        "--variants",
        nargs="+",
        choices=DEFAULT_VARIANTS,
        default=list(DEFAULT_VARIANTS),
    )
    parser.add_argument("--whisper-model", default="medium")
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


opencc = OpenCC("t2s")


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
        "reference_pinyin_with_tone": reference_pinyin_tone,
        "hypothesis_pinyin_with_tone": hypothesis_pinyin_tone,
        "pinyin_errors_with_tone": pinyin_tone_errors,
        "reference_pinyin_count": len(reference_pinyin_tone),
        "pinyin_error_rate_with_tone": safe_divide(pinyin_tone_errors, len(reference_pinyin_tone)),
        "reference_pinyin_without_tone": reference_pinyin_no_tone,
        "hypothesis_pinyin_without_tone": hypothesis_pinyin_no_tone,
        "pinyin_errors_without_tone": pinyin_no_tone_errors,
        "pinyin_error_rate_without_tone": safe_divide(pinyin_no_tone_errors, len(reference_pinyin_no_tone)),
    }


def load_audio_metadata(test_set, variants):
    outputs_dir = OUTPUTS_DIR if test_set == "common_line" else OUTPUTS_DIR / test_set
    metadata = {}
    for variant in variants:
        result_path = outputs_dir / variant / "results.json"
        if not result_path.exists():
            raise FileNotFoundError(f"missing generation result: {result_path}")
        rows = json.loads(result_path.read_text(encoding="utf-8"))
        metadata[variant] = {row["speaker"]: row for row in rows}
    return metadata


def create_campplus_session():
    options = onnxruntime.SessionOptions()
    options.graph_optimization_level = onnxruntime.GraphOptimizationLevel.ORT_ENABLE_ALL
    options.intra_op_num_threads = 1
    return onnxruntime.InferenceSession(
        str(MODEL_DIR / "campplus.onnx"),
        sess_options=options,
        providers=["CPUExecutionProvider"],
    )


def extract_embedding(session, wav_path):
    audio, sample_rate = torchaudio.load(wav_path)
    audio = audio.mean(dim=0, keepdim=True)
    if sample_rate != 16000:
        audio = torchaudio.transforms.Resample(sample_rate, 16000)(audio)
    feature = kaldi.fbank(audio, num_mel_bins=80, dither=0, sample_frequency=16000)
    feature = feature - feature.mean(dim=0, keepdim=True)
    embedding = session.run(
        None,
        {session.get_inputs()[0].name: feature.unsqueeze(dim=0).numpy()},
    )[0].flatten()
    return torch.from_numpy(embedding)


def load_asr_audio(wav_path):
    audio, sample_rate = torchaudio.load(wav_path)
    audio = audio.mean(dim=0, keepdim=True)
    if sample_rate != 16000:
        audio = torchaudio.transforms.Resample(sample_rate, 16000)(audio)
    return audio.squeeze(0).numpy()


def mean(rows, key):
    values = [row[key] for row in rows if row.get(key) is not None]
    return sum(values) / len(values) if values else 0.0


def format_percent(value):
    return f"{value * 100:.2f}%"


def write_markdown(evaluation_dir, test_set, variants, whisper_model, results):
    by_variant = defaultdict(list)
    for row in results:
        by_variant[row["variant"]].append(row)

    lines = [
        f"# CosyVoice3 automatic metrics: {test_set}",
        "",
        f"- Whisper ASR: `{whisper_model}`",
        "- Speaker similarity: CampPlus cosine similarity between prompt audio and generated audio.",
        "- RTF: generation seconds / generated audio seconds.",
        "",
        "## Variant averages",
        "",
        "| variant | n | CER | WER | pinyin tone | pinyin no tone | SIM | RTF | audio s | gen s |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for variant in variants:
        rows = by_variant[variant]
        lines.append(
            "| {variant} | {n} | {cer} | {wer} | {tone} | {no_tone} | {sim:.4f} | {rtf:.3f} | {audio:.3f} | {gen:.3f} |".format(
                variant=variant,
                n=len(rows),
                cer=format_percent(mean(rows, "cer")),
                wer=format_percent(mean(rows, "wer")),
                tone=format_percent(mean(rows, "pinyin_error_rate_with_tone")),
                no_tone=format_percent(mean(rows, "pinyin_error_rate_without_tone")),
                sim=mean(rows, "speaker_cosine_similarity"),
                rtf=mean(rows, "rtf"),
                audio=mean(rows, "audio_seconds"),
                gen=mean(rows, "generation_seconds"),
            )
        )

    lines.extend(
        [
            "",
            "## Per speaker",
            "",
            "| speaker | variant | CER | WER | pinyin no tone | SIM | RTF | ASR transcript |",
            "|---|---|---:|---:|---:|---:|---:|---|",
        ]
    )
    for speaker in SPEAKERS:
        for variant in variants:
            row = next(item for item in results if item["speaker"] == speaker and item["variant"] == variant)
            transcript = row["whisper_transcript"].replace("|", " ")
            lines.append(
                "| {speaker} | {variant} | {cer} | {wer} | {pin} | {sim:.4f} | {rtf:.3f} | {text} |".format(
                    speaker=SPEAKER_NAMES[speaker],
                    variant=variant,
                    cer=format_percent(row["cer"]),
                    wer=format_percent(row["wer"]),
                    pin=format_percent(row["pinyin_error_rate_without_tone"]),
                    sim=row["speaker_cosine_similarity"],
                    rtf=row["rtf"],
                    text=transcript,
                )
            )

    (evaluation_dir / "automatic_metrics.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    args = parse_args()
    variants = tuple(args.variants)
    evaluation_dir = EVALUATION_DIR if args.test_set == "common_line" else EVALUATION_DIR / args.test_set
    evaluation_dir.mkdir(parents=True, exist_ok=True)

    metadata = load_audio_metadata(args.test_set, variants)
    campplus = create_campplus_session()
    asr_model = whisper.load_model(args.whisper_model)

    prompt_embeddings = {}
    results = []
    for speaker in SPEAKERS:
        prompt_path = metadata[variants[0]][speaker]["prompt_wav"]
        prompt_embeddings[speaker] = extract_embedding(campplus, prompt_path)
        for variant in variants:
            row = metadata[variant][speaker]
            output_path = row["output_wav"]
            transcript = asr_model.transcribe(
                load_asr_audio(output_path),
                language="zh",
                task="transcribe",
                temperature=0,
                beam_size=5,
                condition_on_previous_text=False,
                fp16=torch.cuda.is_available(),
            )["text"].strip()
            rates = calculate_error_rates(row["target_text"], transcript)
            output_embedding = extract_embedding(campplus, output_path)
            similarity = torch.nn.functional.cosine_similarity(
                prompt_embeddings[speaker].unsqueeze(0),
                output_embedding.unsqueeze(0),
            ).item()
            result = {
                "speaker": speaker,
                "speaker_name": SPEAKER_NAMES[speaker],
                "variant": variant,
                "test_set": args.test_set,
                "target_text": row["target_text"],
                "prompt_wav": row["prompt_wav"],
                "output_wav": output_path,
                "audio_seconds": row["audio_seconds"],
                "generation_seconds": row["generation_seconds"],
                "rtf": row["rtf"],
                "whisper_model": args.whisper_model,
                "whisper_transcript": transcript,
                **rates,
                "speaker_cosine_similarity": similarity,
            }
            results.append(result)
            print(
                f"{SPEAKER_NAMES[speaker]} {variant}: "
                f"CER={rates['cer']:.2%}, WER={rates['wer']:.2%}, "
                f"pinyin_no_tone={rates['pinyin_error_rate_without_tone']:.2%}, "
                f"SIM={similarity:.4f}, RTF={row['rtf']:.3f}"
            )

    (evaluation_dir / "automatic_metrics.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    write_markdown(evaluation_dir, args.test_set, variants, args.whisper_model, results)


if __name__ == "__main__":
    main()
