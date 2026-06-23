from argparse import ArgumentParser
from pathlib import Path
import json
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "third_party" / "Matcha-TTS"))

import torch
import torchaudio

from cosyvoice.cli.cosyvoice import AutoModel


EXPERIMENT_DIR = Path(__file__).resolve().parent
SOURCE_EXPERIMENT_DIR = ROOT / "examples" / "genshin_voice" / "cosyvoice2"
MODEL_DIR = ROOT / "pretrained_models" / "Fun-CosyVoice3-0.5B"
INSTRUCT_TEXT = "You are a helpful assistant.<|endofprompt|>"
LLM_CHECKPOINTS = {
    "clean_epoch_0": EXPERIMENT_DIR / "exp" / "four_characters_llm_clean_3epoch" / "epoch_0_whole.pt",
    "clean_epoch_1": EXPERIMENT_DIR / "exp" / "four_characters_llm_clean_3epoch" / "epoch_1_whole.pt",
    "clean_epoch_2": EXPERIMENT_DIR / "exp" / "four_characters_llm_clean_3epoch" / "epoch_2_whole.pt",
}
DEV_DIR = EXPERIMENT_DIR / "data" / "four_characters" / "dev_clean"
SPEAKERS = ("paimon", "zhongli", "ganyu", "yae_miko")
SOURCE_RESULT_FILES = {
    "common_line": SOURCE_EXPERIMENT_DIR / "outputs" / "base" / "results.json",
    "generic_short": SOURCE_EXPERIMENT_DIR / "outputs" / "generic_short" / "base" / "results.json",
    "long_text": SOURCE_EXPERIMENT_DIR / "outputs" / "long_text" / "base" / "results.json",
    "character_lines": SOURCE_EXPERIMENT_DIR / "outputs" / "character_lines" / "base" / "results.json",
}


def parse_args():
    parser = ArgumentParser(description="Generate fixed-condition CosyVoice3 four-character evaluation audio.")
    parser.add_argument("--variant", choices=("base", *LLM_CHECKPOINTS), default="base")
    parser.add_argument("--test-set", choices=tuple(SOURCE_RESULT_FILES), default="common_line")
    return parser.parse_args()


def read_mapping(path):
    mapping = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        key, value = line.split(maxsplit=1)
        mapping[key] = value
    return mapping


def load_targets(test_set):
    rows = json.loads(SOURCE_RESULT_FILES[test_set].read_text(encoding="utf-8"))
    return {row["speaker"]: row["target_text"] for row in rows}


def select_prompts():
    wavs = read_mapping(DEV_DIR / "wav.scp")
    texts = read_mapping(DEV_DIR / "text")
    utt2spk = read_mapping(DEV_DIR / "utt2spk")
    selected = {}
    for speaker in SPEAKERS:
        candidates = []
        for utt, utt_speaker in utt2spk.items():
            if utt_speaker != speaker:
                continue
            info = torchaudio.info(wavs[utt])
            duration = info.num_frames / info.sample_rate
            candidates.append((abs(duration - 5.0), duration, utt))
        if not candidates:
            raise RuntimeError(f"no dev prompt found for {speaker}")
        _, duration, utt = min(candidates)
        selected[speaker] = {
            "utt": utt,
            "wav": wavs[utt],
            "text": texts[utt],
            "duration": duration,
        }
    return selected


def synchronize_cuda():
    if torch.cuda.is_available():
        torch.cuda.synchronize()


def load_llm_checkpoint(cosyvoice, checkpoint_path):
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    checkpoint = {
        key: value
        for key, value in checkpoint.items()
        if isinstance(value, torch.Tensor)
    }
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

    prompts = select_prompts()
    targets = load_targets(args.test_set)
    output_dir = EXPERIMENT_DIR / "outputs" / args.variant
    if args.test_set != "common_line":
        output_dir = EXPERIMENT_DIR / "outputs" / args.test_set / args.variant
    output_dir.mkdir(parents=True, exist_ok=True)

    cosyvoice = AutoModel(model_dir=str(MODEL_DIR), fp16=torch.cuda.is_available())
    if args.variant in LLM_CHECKPOINTS:
        load_llm_checkpoint(cosyvoice, LLM_CHECKPOINTS[args.variant])

    results = []
    for speaker, prompt in prompts.items():
        target_text = targets[speaker]
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
        output_name = f"{speaker}_{args.test_set}.wav"
        output_wav = output_dir / output_name
        torchaudio.save(str(output_wav), speech, cosyvoice.sample_rate)
        audio_seconds = speech.shape[1] / cosyvoice.sample_rate
        result = {
            "speaker": speaker,
            "variant": args.variant,
            "test_set": args.test_set,
            "target_text": target_text,
            "prompt_utt": prompt["utt"],
            "prompt_wav": prompt["wav"],
            "prompt_text": prompt["text"],
            "prompt_instruct_text": prompt_text,
            "prompt_seconds": round(prompt["duration"], 3),
            "output_wav": str(output_wav),
            "audio_seconds": round(audio_seconds, 3),
            "generation_seconds": round(generation_seconds, 3),
            "rtf": round(generation_seconds / audio_seconds, 3),
        }
        results.append(result)
        print(json.dumps(result, ensure_ascii=False))

    (output_dir / "results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
