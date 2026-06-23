from argparse import ArgumentParser
from collections import defaultdict
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import torch
import whisper

from evaluate_outputs import (
    calculate_error_rates,
    create_campplus_session,
    extract_embedding,
    format_percent,
    load_asr_audio,
    mean,
)


EXPERIMENT_DIR = Path(__file__).resolve().parent
OUTPUTS_DIR = EXPERIMENT_DIR / "outputs" / "unseen_speakers"
EVALUATION_DIR = EXPERIMENT_DIR / "evaluation" / "unseen_speakers"
DEFAULT_VARIANTS = ("base", "clean_epoch_2")


def parse_args():
    parser = ArgumentParser(description="Evaluate unseen-speaker CosyVoice3 comparison audio.")
    parser.add_argument("--test-set", choices=("common_line", "generic_short"), default="generic_short")
    parser.add_argument("--variants", nargs="+", default=list(DEFAULT_VARIANTS))
    parser.add_argument("--whisper-model", default="medium")
    return parser.parse_args()


def load_audio_metadata(test_set, variants):
    metadata = {}
    for variant in variants:
        result_path = OUTPUTS_DIR / test_set / variant / "results.json"
        if not result_path.exists():
            raise FileNotFoundError(f"missing generation result: {result_path}")
        rows = json.loads(result_path.read_text(encoding="utf-8"))
        metadata[variant] = {row["speaker_id"]: row for row in rows}
    speaker_ids = sorted(metadata[variants[0]].keys())
    for variant in variants[1:]:
        if sorted(metadata[variant].keys()) != speaker_ids:
            raise RuntimeError(f"speaker mismatch between {variants[0]} and {variant}")
    return metadata, speaker_ids


def write_markdown(evaluation_dir, test_set, variants, whisper_model, results):
    by_variant = defaultdict(list)
    for row in results:
        by_variant[row["variant"]].append(row)

    lines = [
        f"# CosyVoice3 unseen-speaker automatic metrics: {test_set}",
        "",
        f"- Whisper ASR: `{whisper_model}`",
        "- Speaker similarity: CampPlus cosine similarity between prompt audio and generated audio.",
        "- RTF: generation seconds / generated audio seconds.",
        "- Speakers are not included in the four-character LLM-only finetuning set.",
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
    for row in sorted(results, key=lambda item: (item["speaker_name"], item["variant"])):
        transcript = row["whisper_transcript"].replace("|", " ")
        lines.append(
            "| {speaker} | {variant} | {cer} | {wer} | {pin} | {sim:.4f} | {rtf:.3f} | {text} |".format(
                speaker=row["speaker_name"],
                variant=row["variant"],
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
    metadata, speaker_ids = load_audio_metadata(args.test_set, variants)
    evaluation_dir = EVALUATION_DIR / args.test_set
    evaluation_dir.mkdir(parents=True, exist_ok=True)

    campplus = create_campplus_session()
    asr_model = whisper.load_model(args.whisper_model)

    prompt_embeddings = {}
    results = []
    for speaker_id in speaker_ids:
        prompt_path = metadata[variants[0]][speaker_id]["prompt_wav"]
        prompt_embeddings[speaker_id] = extract_embedding(campplus, prompt_path)
        for variant in variants:
            row = metadata[variant][speaker_id]
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
                prompt_embeddings[speaker_id].unsqueeze(0),
                output_embedding.unsqueeze(0),
            ).item()
            result = {
                "speaker_id": speaker_id,
                "speaker_name": row["speaker"],
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
                f"{row['speaker']} {variant}: "
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
