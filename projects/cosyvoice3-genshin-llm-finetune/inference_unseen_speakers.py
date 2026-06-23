from argparse import ArgumentParser
from pathlib import Path
import json
import re
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "third_party" / "Matcha-TTS"))

import torch
import torchaudio

from cosyvoice.cli.cosyvoice import AutoModel


EXPERIMENT_DIR = Path(__file__).resolve().parent
MODEL_DIR = ROOT / "pretrained_models" / "Fun-CosyVoice3-0.5B"
DEV_MANIFEST = ROOT.parent / "OmniVoice" / "data" / "genshin_20_speakers" / "manifests" / "dev.jsonl"
INSTRUCT_TEXT = "You are a helpful assistant.<|endofprompt|>"
LLM_CHECKPOINTS = {
    "clean_epoch_0": EXPERIMENT_DIR / "exp" / "four_characters_llm_clean_3epoch" / "epoch_0_whole.pt",
    "clean_epoch_1": EXPERIMENT_DIR / "exp" / "four_characters_llm_clean_3epoch" / "epoch_1_whole.pt",
    "clean_epoch_2": EXPERIMENT_DIR / "exp" / "four_characters_llm_clean_3epoch" / "epoch_2_whole.pt",
}
UNSEEN_SPEAKERS = (
    "Nahida",
    "Alhaitham",
    "Ningguang",
    "Tighnari",
    "Yelan",
    "Yoimiya",
    "Kamisato Ayaka",
    "Nilou",
)
TARGET_SETS = {
    "common_line": "欲买桂花同载酒，只可惜故人，何日再见呢？",
    "generic_short": "今天阳光很好，我们吃过早饭以后，一起去公园散步吧。",
}


def parse_args():
    parser = ArgumentParser(description="Generate unseen-speaker CosyVoice3 comparison audio.")
    parser.add_argument("--variant", choices=("base", *LLM_CHECKPOINTS), default="base")
    parser.add_argument("--test-set", choices=tuple(TARGET_SETS), default="generic_short")
    parser.add_argument("--speakers", nargs="+", default=list(UNSEEN_SPEAKERS))
    return parser.parse_args()


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def load_manifest():
    rows = []
    for line in DEV_MANIFEST.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def audio_seconds(path):
    info = torchaudio.info(path)
    return info.num_frames / info.sample_rate


def select_prompts(speakers):
    rows = load_manifest()
    selected = {}
    for speaker in speakers:
        candidates = []
        for row in rows:
            if row["speaker"] != speaker:
                continue
            text = row["text"].strip()
            if not text or any(marker in text for marker in "{}#"):
                continue
            duration = audio_seconds(row["audio_path"])
            if 3.0 <= duration <= 9.0:
                candidates.append((abs(duration - 5.0), duration, row))
        if not candidates:
            raise RuntimeError(f"no usable unseen prompt found for {speaker}")
        _, duration, row = min(candidates)
        selected[speaker] = {
            "id": row["id"],
            "speaker": speaker,
            "speaker_id": slugify(speaker),
            "wav": row["audio_path"],
            "text": row["text"],
            "duration": duration,
        }
    return selected


def synchronize_cuda():
    if torch.cuda.is_available():
        torch.cuda.synchronize()


def load_llm_checkpoint(cosyvoice, checkpoint_path):
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    checkpoint = {key: value for key, value in checkpoint.items() if isinstance(value, torch.Tensor)}
    incompatible = cosyvoice.model.llm.load_state_dict(checkpoint, strict=False)
    if incompatible.missing_keys or incompatible.unexpected_keys:
        raise RuntimeError(
            f"LLM checkpoint mismatch: missing={incompatible.missing_keys}, "
            f"unexpected={incompatible.unexpected_keys}"
        )


def main():
    args = parse_args()
    torch.manual_seed(0)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(0)

    prompts = select_prompts(args.speakers)
    target_text = TARGET_SETS[args.test_set]
    output_dir = EXPERIMENT_DIR / "outputs" / "unseen_speakers" / args.test_set / args.variant
    output_dir.mkdir(parents=True, exist_ok=True)

    cosyvoice = AutoModel(model_dir=str(MODEL_DIR), fp16=torch.cuda.is_available())
    if args.variant in LLM_CHECKPOINTS:
        load_llm_checkpoint(cosyvoice, LLM_CHECKPOINTS[args.variant])

    results = []
    for speaker, prompt in prompts.items():
        prompt_text = INSTRUCT_TEXT + prompt["text"]
        synchronize_cuda()
        start = perf_counter()
        speech_parts = []
        for item in cosyvoice.inference_zero_shot(
            target_text,
            prompt_text,
            prompt["wav"],
            stream=False,
            speed=1.0,
            text_frontend=True,
        ):
            speech_parts.append(item["tts_speech"].detach().cpu())
        synchronize_cuda()
        generation_seconds = perf_counter() - start

        speech = torch.cat(speech_parts, dim=1)
        output_wav = output_dir / f"{prompt['speaker_id']}_{args.test_set}.wav"
        torchaudio.save(str(output_wav), speech, cosyvoice.sample_rate)
        audio_duration = speech.shape[1] / cosyvoice.sample_rate
        result = {
            "speaker": speaker,
            "speaker_id": prompt["speaker_id"],
            "variant": args.variant,
            "test_set": args.test_set,
            "target_text": target_text,
            "prompt_id": prompt["id"],
            "prompt_wav": prompt["wav"],
            "prompt_text": prompt["text"],
            "prompt_instruct_text": prompt_text,
            "prompt_seconds": round(prompt["duration"], 3),
            "output_wav": str(output_wav),
            "audio_seconds": round(audio_duration, 3),
            "generation_seconds": round(generation_seconds, 3),
            "rtf": round(generation_seconds / audio_duration, 3),
        }
        results.append(result)
        print(json.dumps(result, ensure_ascii=False))

    (output_dir / "results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
