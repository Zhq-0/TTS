#!/usr/bin/env python3
"""Generate a multi-scenario evaluation for the 20-speaker Genshin fine-tune."""

from __future__ import annotations

import gc
import json
import os
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import numpy as np
import soundfile as sf
import torch

from omnivoice import OmniVoice


ROOT = Path(__file__).resolve().parents[1]
DEV_MANIFEST = ROOT / "data" / "genshin_20_speakers" / "manifests" / "dev.jsonl"
EVAL_DIR = ROOT / "evaluation" / "genshin_20_speakers_1200_extended"
OUTPUT_DIR = ROOT / "outputs" / "genshin_20_speakers_1200_extended"
MODELS = (
    ("base", ROOT / "pretrained_models" / "OmniVoice"),
    ("finetuned_best", ROOT / "exp" / "genshin_20_speakers_1200_sdpa" / "best"),
)
SEEN_SPEAKERS = ("Paimon", "Zhongli", "Nahida", "Arataki Itto")
UNSEEN_REFERENCE = {
    "speaker": "AISHELL3_SSB0273_unseen",
    "audio_path": (
        r"<HF_CACHE_DIR>\datasets--AISHELL--AISHELL-3\snapshots"
        r"\f20d5db4a31fe779ef07bb1af4ea92da5c786622\train\wav\SSB0273\SSB02730079.wav"
    ),
    "text": "并首次明确要求加强养老产业和健康服务业的用地保障",
}
TEST_CASES = (
    (
        "long_zh",
        "中文长文本",
        "zh",
        "zh",
        (
            "今天我们进行一次长中文语音合成测试。系统需要准确朗读每一个词语，并在连续表达时保持稳定的音色、自然的语速和清晰的停顿。测试过程中，我们会关注是否出现漏字、重复、异常停顿或者声音漂移。最后，将结合生成耗时、字符错误率、词错误率、自然度和说话人相似度，对本次实验结果进行完整记录。",
            "清晨的城市逐渐苏醒，街道上的车辆和行人慢慢增多。有人准备开始一天的工作，有人带着早餐匆匆赶路，也有人在公园里安静地散步。随着阳光穿过云层，周围的建筑和树木显得更加清晰，新的一天也在平稳而有序的节奏中展开。",
            "为了验证语音系统在长时间连续表达中的稳定性，我们准备了一段包含多个句子和不同停顿位置的测试内容。模型不仅需要保证文字完整，还要控制合理的语速、重音与句间停顿，并尽量避免音色漂移、重复朗读或突然加速等问题。",
        ),
    ),
    (
        "polyphone",
        "多音字文本",
        "zh",
        "zh",
        (
            "银行门口的人沿着人行道行走，工作人员认真核对每一行记录。",
            "音乐老师强调快乐学习的重要性，并带领大家提高练习效率。",
            "他重新测量物品的重量，又重复检查数据，最后率领团队完成任务。",
        ),
    ),
    (
        "game_terms",
        "游戏专有词与角色名文本",
        "zh",
        "zh",
        (
            "派蒙和旅行者离开蒙德后，准备前往璃月港拜访钟离。",
            "纳西妲在须弥城遇见艾尔海森和提纳里，并讨论世界树的变化。",
            "八重神子邀请雷电将军前往鸣神大社，荒泷一斗则在花见坂等待久岐忍。",
        ),
    ),
    (
        "mixed",
        "中英混合文本",
        "zh",
        "zh",
        (
            "今天的 meeting 很顺利，我们下午继续测试 OmniVoice。",
            "系统会记录 generation time、audio duration 和 RTF，然后使用 Whisper 计算 CER 与 WER。",
            "完成 multilingual speech synthesis 测试后，我们将比较 speaker similarity 和 naturalness score。",
        ),
    ),
    (
        "english",
        "英文文本",
        "en",
        "en",
        (
            "Today is a good day to learn something new.",
            "The speech synthesis system should pronounce every word clearly and maintain a natural speaking rhythm.",
            "During this evaluation, we compare pronunciation accuracy, generation speed, naturalness, and speaker similarity.",
        ),
    ),
)
UNSEEN_CASES = (
    (
        "unseen_short",
        "未见说话人短文本",
        "zh",
        "zh",
        "今天阳光很好，我们准备开始新的语音合成测试。",
    ),
    (
        "unseen_polyphone",
        "未见说话人多音字文本",
        "zh",
        "zh",
        "银行门口的人沿着人行道行走，音乐老师正在提高练习效率。",
    ),
    (
        "unseen_long",
        "未见说话人长文本",
        "zh",
        "zh",
        "今天我们使用一段从未参与微调的说话人音频进行零样本声音克隆测试。系统需要准确生成目标文本，同时保持参考音频中的音色特征、自然语速和清晰停顿。测试完成后，我们会比较基础模型和微调模型在未见说话人上的泛化能力。",
    ),
)


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def sync() -> None:
    if torch.cuda.is_available():
        torch.cuda.synchronize()


def seed() -> None:
    torch.manual_seed(0)
    torch.cuda.manual_seed_all(0)


def build_jobs(references: dict[str, dict]) -> list[dict]:
    jobs = []
    for speaker in SEEN_SPEAKERS:
        for category_id, category_name, language_id, asr_language, texts in TEST_CASES:
            for index, text in enumerate(texts, start=1):
                jobs.append(
                    {
                        "speaker": speaker,
                        "reference": references[speaker],
                        "seen_status": "seen",
                        "category_id": category_id,
                        "category_name": category_name,
                        "case_id": f"{category_id}_{index}",
                        "case_name": f"{category_name} {index}",
                        "language_id": language_id,
                        "asr_language": asr_language,
                        "text": text,
                    }
                )
    for case_id, case_name, language_id, asr_language, text in UNSEEN_CASES:
        jobs.append(
            {
                "speaker": UNSEEN_REFERENCE["speaker"],
                "reference": UNSEEN_REFERENCE,
                "seen_status": "unseen",
                "category_id": "unseen_zero_shot",
                "category_name": "未见说话人 zero-shot",
                "case_id": case_id,
                "case_name": case_name,
                "language_id": language_id,
                "asr_language": asr_language,
                "text": text,
            }
        )
    return jobs


def main() -> None:
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dev_rows = [json.loads(line) for line in DEV_MANIFEST.read_text(encoding="utf-8").splitlines()]
    references = {}
    for row in dev_rows:
        references.setdefault(row["speaker"], row)
    references[UNSEEN_REFERENCE["speaker"]] = UNSEEN_REFERENCE
    jobs = build_jobs(references)

    results = []
    model_summaries = []
    for model_name, model_path in MODELS:
        sync()
        started = perf_counter()
        model = OmniVoice.from_pretrained(model_path, device_map="cuda:0", dtype=torch.float16)
        sync()
        model_load_seconds = perf_counter() - started

        prompts = {}
        prompt_seconds = {}
        for speaker in (*SEEN_SPEAKERS, UNSEEN_REFERENCE["speaker"]):
            reference = references[speaker]
            sync()
            started = perf_counter()
            prompts[speaker] = model.create_voice_clone_prompt(
                ref_audio=reference["audio_path"],
                ref_text=reference["text"],
            )
            sync()
            prompt_seconds[speaker] = perf_counter() - started

        model.generate(
            text="这是一次不计时的预热测试。",
            language="zh",
            voice_clone_prompt=prompts[SEEN_SPEAKERS[0]],
            num_step=32,
        )
        sync()

        model_dir = OUTPUT_DIR / model_name
        model_dir.mkdir(parents=True, exist_ok=True)
        model_rows = []
        for job in jobs:
            seed()
            sync()
            started = perf_counter()
            audio = model.generate(
                text=job["text"],
                language=job["language_id"],
                voice_clone_prompt=prompts[job["speaker"]],
                num_step=32,
            )[0]
            sync()
            generation_seconds = perf_counter() - started
            output_path = (
                model_dir
                / job["category_id"]
                / f"{slugify(job['speaker'])}_{job['case_id']}.wav"
            )
            output_path.parent.mkdir(parents=True, exist_ok=True)
            sf.write(output_path, audio, model.sampling_rate)
            audio_seconds = len(audio) / model.sampling_rate
            row = {
                "id": f"{model_name}_{slugify(job['speaker'])}_{job['case_id']}",
                "model_name": model_name,
                "model_path": str(model_path),
                **{key: value for key, value in job.items() if key != "reference"},
                "reference_audio": job["reference"]["audio_path"],
                "reference_text": job["reference"]["text"],
                "output_wav": str(output_path),
                "generation_seconds": generation_seconds,
                "audio_seconds": audio_seconds,
                "rtf": generation_seconds / audio_seconds,
                "peak": float(np.max(np.abs(audio))),
                "clipped_samples": int(np.count_nonzero(np.abs(audio) >= 1.0)),
            }
            results.append(row)
            model_rows.append(row)
            print(
                f"{row['id']}: generation={generation_seconds:.3f}s "
                f"audio={audio_seconds:.3f}s rtf={row['rtf']:.3f}"
            )
        model_summaries.append(
            {
                "model_name": model_name,
                "model_path": str(model_path),
                "model_load_seconds": model_load_seconds,
                "mean_prompt_prepare_seconds": float(np.mean(list(prompt_seconds.values()))),
                "generation_seconds": sum(row["generation_seconds"] for row in model_rows),
                "audio_seconds": sum(row["audio_seconds"] for row in model_rows),
            }
        )
        del model
        prompts.clear()
        gc.collect()
        torch.cuda.empty_cache()

    payload = {
        "timestamp": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "device": torch.cuda.get_device_name(0),
        "num_step": 32,
        "batch_size": 1,
        "seed": 0,
        "seen_speakers": list(SEEN_SPEAKERS),
        "unseen_reference": UNSEEN_REFERENCE,
        "models": model_summaries,
        "results": results,
    }
    path = EVAL_DIR / "generation_results.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved generation results: {path}")


if __name__ == "__main__":
    main()
