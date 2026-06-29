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
DEV_DIR = EXPERIMENT_DIR / "data" / "four_characters" / "dev_clean"
UNSEEN_MANIFEST = ROOT.parent / "OmniVoice" / "data" / "genshin_20_speakers" / "manifests" / "dev.jsonl"
OUTPUT_DIR = EXPERIMENT_DIR / "outputs" / "extended_comparison"
EVAL_DIR = EXPERIMENT_DIR / "evaluation" / "extended_comparison"
INSTRUCT_TEXT = "You are a helpful assistant.<|endofprompt|>"
LLM_CHECKPOINTS = {
    "clean_epoch_2": EXPERIMENT_DIR / "exp" / "four_characters_llm_clean_3epoch" / "epoch_2_whole.pt",
}
SEEN_SPEAKERS = {
    "paimon": "Paimon",
    "zhongli": "Zhongli",
    "ganyu": "Ganyu",
    "yae_miko": "Yae Miko",
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


TEXT_GROUPS = {
    "difficult_short": [
        "欲买桂花同载酒，只可惜故人，何日再见呢？",
        "霜雪落满旧庭院，故人却迟迟未归。",
        "浮世景色百千年依旧，人之在世却如白露与泡影。",
        "若你困于无风之地，我便为你奏响新的诗篇。",
        "此身虽在尘世，心却仍向星海远行。",
    ],
    "generic_short": [
        "今天阳光很好，我们一起去公园散步吧。",
        "请把这句话读得自然一些。",
        "明天上午九点，我们在车站门口集合。",
        "这段语音需要保持清晰稳定。",
        "如果准备好了，就请开始下一轮测试。",
    ],
    "game_terms": [
        "派蒙提醒大家，深境螺旋的挑战需要合理搭配元素反应。",
        "钟离说，契约既成，食言者当受食岩之罚。",
        "甘雨整理完璃月七星的文书后，准备去奥藏山休息。",
        "八重神子把新的轻小说放在柜台上，笑着看向旅行者。",
        "纳西妲正在分析梦境里的线索，并记录每一次异常波动。",
    ],
    "medium_text": [
        "为了保证对比公平，我们在测试时固定参考音频、目标文本和随机种子。",
        "小数据微调不一定带来全面提升，因此需要同时观察内容准确率和音色相似度。",
        "如果模型在短句上表现很好，还需要继续测试中长文本，避免只得到偶然结论。",
        "这次评测会覆盖已见角色和未见角色，用来判断微调是否影响 zero-shot 泛化能力。",
        "当基座模型已经很强时，微调更容易带来边际收益有限或者局部退化的问题。",
    ],
    "zh_en_mixed": [
        "我们使用 fixed seed 来减少 sampling randomness。",
        "如果 model 多说了 extra words，WER 会明显升高。",
        "这个 checkpoint 需要和 base model 使用同一个 prompt。",
        "zero-shot voice cloning 的关键是参考音频和目标文本都要稳定。",
        "请检查 speaker similarity 和 ASR transcript 是否一致。",
    ],
}


def parse_args():
    parser = ArgumentParser(description="Run extended CosyVoice3 base vs finetuned comparison.")
    parser.add_argument("--variant", choices=("base", *LLM_CHECKPOINTS), required=True)
    parser.add_argument("--limit-cases", type=int, default=0)
    return parser.parse_args()


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def read_mapping(path):
    mapping = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            key, value = line.split(maxsplit=1)
            mapping[key] = value
    return mapping


def audio_seconds(path):
    info = torchaudio.info(path)
    return info.num_frames / info.sample_rate


def select_seen_prompts():
    wavs = read_mapping(DEV_DIR / "wav.scp")
    texts = read_mapping(DEV_DIR / "text")
    utt2spk = read_mapping(DEV_DIR / "utt2spk")
    selected = {}
    for speaker_id, speaker_name in SEEN_SPEAKERS.items():
        candidates = []
        for utt, utt_speaker in utt2spk.items():
            if utt_speaker != speaker_id:
                continue
            duration = audio_seconds(wavs[utt])
            if 3.0 <= duration <= 9.0:
                candidates.append((abs(duration - 5.0), duration, utt))
        if not candidates:
            raise RuntimeError(f"no dev prompt found for {speaker_id}")
        _, duration, utt = min(candidates)
        selected[speaker_id] = {
            "split": "seen",
            "speaker_id": speaker_id,
            "speaker": speaker_name,
            "prompt_id": utt,
            "prompt_wav": wavs[utt],
            "prompt_text": texts[utt],
            "prompt_seconds": duration,
        }
    return selected


def load_unseen_manifest():
    rows = []
    for line in UNSEEN_MANIFEST.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def select_unseen_prompts():
    rows = load_unseen_manifest()
    selected = {}
    for speaker in UNSEEN_SPEAKERS:
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
        speaker_id = slugify(speaker)
        selected[speaker_id] = {
            "split": "unseen",
            "speaker_id": speaker_id,
            "speaker": speaker,
            "prompt_id": row["id"],
            "prompt_wav": row["audio_path"],
            "prompt_text": row["text"],
            "prompt_seconds": duration,
        }
    return selected


def build_cases():
    prompts = {}
    prompts.update(select_seen_prompts())
    prompts.update(select_unseen_prompts())
    cases = []
    for speaker_id, prompt in prompts.items():
        for category, texts in TEXT_GROUPS.items():
            selected_texts = texts if prompt["split"] == "seen" else texts[:2]
            for index, text in enumerate(selected_texts, start=1):
                case = {
                    **prompt,
                    "category": category,
                    "category_index": index,
                    "target_text": text,
                    "case_id": f"{prompt['split']}_{speaker_id}_{category}_{index:02d}",
                }
                cases.append(case)
    return cases


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


def write_case_files(cases):
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    case_path = EVAL_DIR / "cases.jsonl"
    case_path.write_text(
        "\n".join(json.dumps(case, ensure_ascii=False) for case in cases) + "\n",
        encoding="utf-8",
    )
    summary = {
        "case_count": len(cases),
        "splits": {},
        "categories": {},
        "speakers": {},
        "note": "Seen speakers use all 25 target texts; unseen speakers use 10 target texts.",
    }
    for case in cases:
        summary["splits"][case["split"]] = summary["splits"].get(case["split"], 0) + 1
        key = f"{case['split']}:{case['category']}"
        summary["categories"][key] = summary["categories"].get(key, 0) + 1
        summary["speakers"][case["speaker"]] = summary["speakers"].get(case["speaker"], 0) + 1
    (EVAL_DIR / "case_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main():
    args = parse_args()
    torch.manual_seed(0)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(0)

    cases = build_cases()
    if args.limit_cases > 0:
        cases = cases[: args.limit_cases]
    write_case_files(cases)

    variant_output_dir = OUTPUT_DIR / args.variant
    variant_output_dir.mkdir(parents=True, exist_ok=True)
    cosyvoice = AutoModel(model_dir=str(MODEL_DIR), fp16=torch.cuda.is_available())
    if args.variant in LLM_CHECKPOINTS:
        load_llm_checkpoint(cosyvoice, LLM_CHECKPOINTS[args.variant])

    results = []
    for case in cases:
        prompt_text = INSTRUCT_TEXT + case["prompt_text"]
        case_dir = variant_output_dir / case["split"] / case["category"]
        case_dir.mkdir(parents=True, exist_ok=True)
        output_wav = case_dir / f"{case['case_id']}.wav"
        result = {**case, "variant": args.variant, "output_wav": str(output_wav)}
        try:
            synchronize_cuda()
            start = perf_counter()
            speech_parts = []
            for item in cosyvoice.inference_zero_shot(
                case["target_text"],
                prompt_text,
                case["prompt_wav"],
                stream=False,
                speed=1.0,
                text_frontend=True,
            ):
                speech_parts.append(item["tts_speech"].detach().cpu())
            synchronize_cuda()
            generation_seconds = perf_counter() - start
            speech = torch.cat(speech_parts, dim=1)
            torchaudio.save(str(output_wav), speech, cosyvoice.sample_rate)
            audio_duration = speech.shape[1] / cosyvoice.sample_rate
            result.update(
                {
                    "status": "ok",
                    "audio_seconds": audio_duration,
                    "generation_seconds": generation_seconds,
                    "rtf": generation_seconds / audio_duration if audio_duration else None,
                }
            )
        except Exception as exc:
            result.update({"status": "error", "error": repr(exc)})
        results.append(result)
        print(json.dumps(result, ensure_ascii=False))

    (variant_output_dir / "results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
