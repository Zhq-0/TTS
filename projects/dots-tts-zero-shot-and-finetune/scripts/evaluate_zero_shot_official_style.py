#!/usr/bin/env python3
"""Evaluate zero-shot outputs with Seed-TTS-Eval style ASR and SIM metrics."""

from __future__ import annotations

import argparse
import gc
import json
import os
import string
import sys
import types
from pathlib import Path
from typing import Any

import numpy as np
import scipy.signal
import soundfile as sf
import torch
from jiwer import compute_measures
from tqdm import tqdm
from zhon.hanzi import punctuation as zh_punctuation


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "experiments" / "zero_shot_comparison" / "outputs" / "dots_tts_mf"
DEFAULT_SEED_TTS_EVAL_ROOT = Path("<AUDIO_WORKSPACE>/seed-tts-eval")
DEFAULT_HF_CACHE_DIR = Path("<HF_CACHE_DIR>")
DEFAULT_WAVLM_CHECKPOINT = (
    Path("<OMNIVOICE_ROOT>")
    / "pretrained_models"
    / "TTS_eval_models"
    / "speaker_similarity"
    / "wavlm_large_finetune.pth"
)

PUNCTUATION_ALL = zh_punctuation + string.punctuation


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--seed-tts-eval-root", type=Path, default=DEFAULT_SEED_TTS_EVAL_ROOT)
    parser.add_argument("--hf-cache-dir", type=Path, default=DEFAULT_HF_CACHE_DIR)
    parser.add_argument("--wavlm-checkpoint", type=Path, default=DEFAULT_WAVLM_CHECKPOINT)
    parser.add_argument("--skip-asr", action="store_true")
    parser.add_argument("--skip-sim", action="store_true")
    parser.add_argument("--device", default="cuda:0" if torch.cuda.is_available() else "cpu")
    return parser.parse_args()


def load_generation(output_dir: Path) -> dict[str, Any]:
    path = output_dir / "generation_results.json"
    if not path.is_file():
        raise FileNotFoundError(f"Generation results not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def official_normalize_for_wer(hypothesis: str, reference: str, language: str) -> tuple[str, str]:
    """Match Seed-TTS-Eval run_wer.py text cleanup as closely as possible."""
    for char in PUNCTUATION_ALL:
        if char == "'":
            continue
        reference = reference.replace(char, "")
        hypothesis = hypothesis.replace(char, "")

    reference = reference.replace("  ", " ")
    hypothesis = hypothesis.replace("  ", " ")

    if language == "zh":
        reference = " ".join([char for char in reference])
        hypothesis = " ".join([char for char in hypothesis])
    elif language == "en":
        reference = reference.lower()
        hypothesis = hypothesis.lower()
    else:
        raise ValueError(f"Unsupported ASR language: {language!r}")
    return hypothesis, reference


def official_wer(hypothesis: str, reference: str, language: str) -> dict[str, Any]:
    normalized_hypothesis, normalized_reference = official_normalize_for_wer(
        hypothesis, reference, language
    )
    measures = compute_measures(normalized_reference, normalized_hypothesis)
    ref_list = normalized_reference.split(" ")
    ref_count = len(ref_list) if ref_list else 0
    substitutions = int(measures["substitutions"])
    deletions = int(measures["deletions"])
    insertions = int(measures["insertions"])
    return {
        "official_reference_normalized": normalized_reference,
        "official_hypothesis_normalized": normalized_hypothesis,
        "official_wer": float(measures["wer"]),
        "official_insertions": insertions,
        "official_deletions": deletions,
        "official_substitutions": substitutions,
        "official_reference_token_count": ref_count,
        "official_error_count": substitutions + deletions + insertions,
    }


def edit_distance(reference: list[str], hypothesis: list[str]) -> int:
    if not reference:
        return len(hypothesis)
    previous = list(range(len(hypothesis) + 1))
    for ref_index, ref_token in enumerate(reference, start=1):
        current = [ref_index]
        for hyp_index, hyp_token in enumerate(hypothesis, start=1):
            substitution_cost = 0 if ref_token == hyp_token else 1
            current.append(
                min(
                    previous[hyp_index] + 1,
                    current[hyp_index - 1] + 1,
                    previous[hyp_index - 1] + substitution_cost,
                )
            )
        previous = current
    return previous[-1]


def official_cer(hypothesis: str, reference: str, language: str) -> dict[str, Any]:
    normalized_hypothesis, normalized_reference = official_normalize_for_wer(
        hypothesis, reference, language
    )
    reference_chars = list(normalized_reference.replace(" ", ""))
    hypothesis_chars = list(normalized_hypothesis.replace(" ", ""))
    reference_count = len(reference_chars)
    errors = edit_distance(reference_chars, hypothesis_chars)
    return {
        "official_cer": float(errors / reference_count) if reference_count else None,
        "official_character_error_count": int(errors),
        "official_reference_character_count": int(reference_count),
    }


class OfficialAsr:
    def __init__(self, *, device: str, cache_dir: Path) -> None:
        self.device = device
        self.cache_dir = cache_dir
        self._en_model = None
        self._en_processor = None
        self._zh_model = None

    def transcribe(self, wav_path: str, language: str) -> str:
        if language == "en":
            return self._transcribe_en(wav_path)
        if language == "zh":
            return self._transcribe_zh(wav_path)
        raise ValueError(f"Unsupported ASR language: {language!r}")

    def _load_en(self):
        if self._en_model is None:
            from transformers import WhisperForConditionalGeneration, WhisperProcessor

            model_id = "openai/whisper-large-v3"
            self._en_processor = WhisperProcessor.from_pretrained(
                model_id, cache_dir=str(self.cache_dir)
            )
            self._en_model = WhisperForConditionalGeneration.from_pretrained(
                model_id, cache_dir=str(self.cache_dir)
            ).to(self.device)
            self._en_model.eval()
        return self._en_processor, self._en_model

    def _load_zh(self):
        if self._zh_model is None:
            from funasr import AutoModel

            self._zh_model = AutoModel(model="paraformer-zh")
        return self._zh_model

    def _transcribe_en(self, wav_path: str) -> str:
        processor, model = self._load_en()
        wav, sample_rate = sf.read(wav_path)
        if wav.ndim == 2:
            wav = wav.mean(axis=1)
        if sample_rate != 16000:
            wav = scipy.signal.resample(wav, int(len(wav) * 16000 / sample_rate))
        input_features = processor(
            wav, sampling_rate=16000, return_tensors="pt"
        ).input_features.to(device=self.device, dtype=model.dtype)
        forced_decoder_ids = processor.get_decoder_prompt_ids(
            language="english", task="transcribe"
        )
        with torch.no_grad():
            predicted_ids = model.generate(
                input_features, forced_decoder_ids=forced_decoder_ids
            )
        return processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]

    def _transcribe_zh(self, wav_path: str) -> str:
        import zhconv

        model = self._load_zh()
        result = model.generate(input=wav_path, batch_size_s=300)
        return zhconv.convert(result[0]["text"], "zh-cn")


class OfficialSpeakerSimilarity:
    def __init__(self, *, seed_tts_eval_root: Path, checkpoint: Path, device: str) -> None:
        if not checkpoint.is_file():
            raise FileNotFoundError(checkpoint)
        self.checkpoint = checkpoint
        self.device = device
        self.model = None
        speaker_verification_dir = (
            seed_tts_eval_root
            / "thirdparty"
            / "UniSpeech"
            / "downstreams"
            / "speaker_verification"
        )
        if not speaker_verification_dir.is_dir():
            raise FileNotFoundError(speaker_verification_dir)

        # The official directory has a select.py that shadows the stdlib select
        # module on Windows. Preload stdlib select and stub fire, which is only
        # needed by the official script's CLI entrypoint.
        import select  # noqa: F401

        sys.modules.setdefault("fire", types.SimpleNamespace(Fire=lambda *args, **kwargs: None))
        sys.path.insert(0, str(speaker_verification_dir))
        from verification import verification  # type: ignore

        self._verification = verification

    def score(self, synthesized_wav: str, prompt_wav: str) -> float:
        use_gpu = self.device.startswith("cuda")
        sim, self.model = self._verification(
            "wavlm_large",
            synthesized_wav,
            prompt_wav,
            use_gpu=use_gpu,
            checkpoint=str(self.checkpoint),
            wav1_start_sr=0,
            wav2_start_sr=0,
            wav1_end_sr=-1,
            wav2_end_sr=-1,
            model=self.model,
            device=self.device,
        )
        return float(sim.detach().cpu().item())


def mean(rows: list[dict[str, Any]], field: str) -> float | None:
    values = [row[field] for row in rows if row.get(field) is not None]
    return float(np.mean(values)) if values else None


def percent(value: float | None) -> str:
    return "-" if value is None else f"{value:.2%}"


def metric(value: float | None, digits: int = 3) -> str:
    return "-" if value is None else f"{value:.{digits}f}"


def build_report(payload: dict[str, Any]) -> str:
    rows = [row for row in payload["results"] if row.get("status") == "ok"]
    model_label = (
        payload.get("model_name_or_path")
        or payload.get("model_dir")
        or payload.get("model")
        or "-"
    )
    lines = [
        "# Seed-TTS-Eval Style Automatic Metrics",
        "",
        "## Summary",
        "",
        f"- Model: `{model_label}`",
        f"- Mean official-style WER: {percent(mean(rows, 'official_wer'))}",
        f"- Mean official-style CER: {percent(mean(rows, 'official_cer'))}",
        f"- Mean official-style SIM: {metric(mean(rows, 'official_sim'))}",
        "",
        "| Case | Language | WER | CER | SIM | Target text | ASR transcript |",
        "|---|---|---:|---:|---:|---|---|",
    ]
    for row in rows:
        target = str(row.get("text", "")).replace("|", r"\|")
        transcript = str(row.get("official_asr_transcript", "")).replace("|", r"\|")
        lines.append(
            f"| {row['name']} | {row.get('asr_language') or row.get('language_id') or '-'} | "
            f"{percent(row.get('official_wer'))} | {percent(row.get('official_cer'))} | "
            f"{metric(row.get('official_sim'))} | {target} | {transcript} |"
        )

    lines.extend(
        [
            "",
            "## Metric Notes",
            "",
            "- WER follows the Seed-TTS-Eval style: English uses `Whisper-large-v3`, Chinese uses `Paraformer-zh`.",
            "- CER uses the same ASR transcript and computes character edit distance after punctuation and whitespace cleanup.",
            "- Chinese WER is effectively character-token WER; English uses the official-style lowercase/punctuation normalization.",
            "- SIM reuses Seed-TTS-Eval WavLM-large speaker verification with `wavlm_large_finetune.pth`.",
            "- This report uses the current custom cases, not the full official Seed-TTS-Eval set.",
            "",
        ]
    )
    return "\n".join(lines)

def main() -> None:
    args = parse_args()
    payload = load_generation(args.output_dir)
    rows = [row for row in payload["results"] if row.get("status") == "ok"]
    if not rows:
        raise RuntimeError("No successful generation rows to evaluate.")

    if not args.skip_asr:
        asr = OfficialAsr(device=args.device, cache_dir=args.hf_cache_dir)
        for row in tqdm(rows, desc="official ASR"):
            language = row.get("asr_language") or row.get("language_id")
            if language not in {"zh", "en"}:
                row["official_asr_transcript"] = ""
                row["official_wer_note"] = f"Skipped unsupported ASR language: {language}"
                print(f"Official ASR {row['id']}: skipped unsupported language={language}")
                continue
            transcript = asr.transcribe(row["output_wav"], language)
            row["official_asr_transcript"] = transcript
            row.update(official_wer(transcript, row["text"], language))
            row.update(official_cer(transcript, row["text"], language))
            print(
                f"Official ASR {row['id']}: WER={row['official_wer']:.2%} "
                f"CER={row['official_cer']:.2%} "
                f"text={transcript}"
            )
        del asr
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    if not args.skip_sim:
        sim_model = OfficialSpeakerSimilarity(
            seed_tts_eval_root=args.seed_tts_eval_root,
            checkpoint=args.wavlm_checkpoint,
            device=args.device,
        )
        for row in tqdm(rows, desc="official SIM"):
            row["official_sim"] = sim_model.score(row["output_wav"], row["prompt_audio"])
            print(f"Official SIM {row['id']}: {row['official_sim']:.3f}")
        del sim_model
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    output_payload = {
        **payload,
        "official_style": {
            "seed_tts_eval_root": str(args.seed_tts_eval_root.resolve()),
            "wer_asr_en": "openai/whisper-large-v3",
            "wer_asr_zh": "funasr/paraformer-zh",
            "sim_model": "Seed-TTS-Eval WavLM-large speaker verification",
            "wavlm_checkpoint": str(args.wavlm_checkpoint.resolve()),
            "device": args.device,
            "dataset_note": "custom zero-shot comparison cases, not full Seed-TTS-Eval",
        },
        "results": payload["results"],
    }
    metrics_path = args.output_dir / "official_style_metrics.json"
    report_path = args.output_dir / "official_style_metrics.md"
    metrics_path.write_text(
        json.dumps(output_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    report_path.write_text(build_report(output_payload), encoding="utf-8")
    print(f"Saved metrics: {metrics_path}")
    print(f"Saved report: {report_path}")


if __name__ == "__main__":
    main()
