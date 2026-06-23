#!/usr/bin/env python3
"""Run CosyVoice3 on the same zero-shot comparison cases."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf
import torch
import torchaudio


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPERIMENT_DIR = ROOT / "experiments" / "zero_shot_comparison"
DEFAULT_COSYVOICE_ROOT = Path("<COSYVOICE_ROOT>")
DEFAULT_MODEL_DIR = DEFAULT_COSYVOICE_ROOT / "pretrained_models" / "Fun-CosyVoice3-0.5B"
SYSTEM_PROMPT = "You are a helpful assistant.<|endofprompt|>"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DEFAULT_EXPERIMENT_DIR / "cases.jsonl")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_EXPERIMENT_DIR / "outputs" / "cosyvoice3")
    parser.add_argument("--cosyvoice-root", type=Path, default=DEFAULT_COSYVOICE_ROOT)
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--case-id", action="append", default=[])
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--fp16", action="store_true")
    return parser.parse_args()


def read_cases(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            rows.append(json.loads(stripped))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {path}:{line_number}: {exc}") from exc
    return rows


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audio_seconds(path: Path) -> float:
    info = sf.info(path)
    return float(info.frames / info.samplerate)


def peak_and_clips(audio: np.ndarray) -> tuple[float, int]:
    if audio.size == 0:
        return 0.0, 0
    abs_audio = np.abs(audio)
    return float(abs_audio.max()), int(np.count_nonzero(abs_audio >= 1.0))


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def build_report(payload: dict[str, Any]) -> str:
    rows = payload["results"]
    ok_rows = [row for row in rows if row.get("status") == "ok"]
    lines = [
        "# CosyVoice3 Zero-shot 克隆实验",
        "",
        "## 实验配置",
        "",
        f"- 时间：`{payload['timestamp']}`",
        f"- 模型目录：`{payload['model_dir']}`",
        f"- 设备：`{payload['device']}`",
        f"- Python：`{payload['python']}`",
        f"- PyTorch：`{payload['torch']}`",
        f"- fp16：`{payload['fp16']}`",
        f"- 模型加载耗时：{payload['model_load_seconds']:.3f} 秒",
        "",
        "## 生成结果",
        "",
        "| 项目 | 状态 | 模式 | 生成耗时 | 音频时长 | RTF | 峰值 | Clip 样本 | 输出 |",
        "|---|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        generation = f"{row['generation_seconds']:.3f} 秒" if row.get("generation_seconds") is not None else "-"
        duration = f"{row['audio_seconds']:.3f} 秒" if row.get("audio_seconds") is not None else "-"
        rtf = f"{row['rtf']:.3f}" if row.get("rtf") is not None else "-"
        peak = f"{row['peak']:.4f}" if row.get("peak") is not None else "-"
        output = f"`{Path(row['output_wav']).name}`" if row.get("output_wav") else "-"
        lines.append(
            f"| {row['name']} | {row['status']} | {row.get('cosyvoice_mode', '-')} | "
            f"{generation} | {duration} | {rtf} | {peak} | {row.get('clipped_samples', '-')} | {output} |"
        )
    if ok_rows:
        total_generation = sum(row["generation_seconds"] for row in ok_rows)
        total_audio = sum(row["audio_seconds"] for row in ok_rows)
        lines.extend(
            [
                "",
                "## 汇总",
                "",
                f"- 完成：{len(ok_rows)} / {len(rows)}",
                f"- 平均 RTF：{np.mean([row['rtf'] for row in ok_rows]):.3f}",
                f"- 总体 RTF：{total_generation / total_audio:.3f}",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    cosyvoice_root = args.cosyvoice_root.resolve()
    sys.path.insert(0, str(cosyvoice_root))
    sys.path.append(str(cosyvoice_root / "third_party" / "Matcha-TTS"))

    from cosyvoice.cli.cosyvoice import AutoModel

    cases = read_cases(args.cases)
    if args.case_id:
        selected = set(args.case_id)
        cases = [case for case in cases if case["id"] in selected]
    if args.limit is not None:
        cases = cases[: args.limit]
    if not cases:
        raise ValueError("No cases selected.")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    results_path = args.output_dir / "results.jsonl"
    payload_path = args.output_dir / "generation_results.json"
    report_path = args.output_dir / "comparison_report.md"

    load_start = time.perf_counter()
    model = AutoModel(model_dir=str(args.model_dir), fp16=args.fp16)
    model_load_seconds = time.perf_counter() - load_start

    rows: list[dict[str, Any]] = []
    for case in cases:
        output_wav = args.output_dir / case["output_name"]
        row = {
            **case,
            "model": "cosyvoice3",
            "model_dir": str(args.model_dir),
            "output_wav": str(output_wav.resolve()),
            "prompt_seconds": None,
            "generation_seconds": None,
            "audio_seconds": None,
            "rtf": None,
            "peak": None,
            "clipped_samples": None,
            "sha256": None,
            "status": "pending",
            "error": None,
        }
        try:
            prompt_audio = Path(case["prompt_audio"])
            if not prompt_audio.is_file():
                raise FileNotFoundError(f"Prompt audio not found: {prompt_audio}")
            row["prompt_seconds"] = audio_seconds(prompt_audio)
            if output_wav.exists() and not args.overwrite:
                audio, sample_rate = sf.read(output_wav, dtype="float32", always_2d=True)
                waveform = audio.mean(axis=1)
                peak, clips = peak_and_clips(waveform)
                row.update(
                    {
                        "status": "ok",
                        "audio_seconds": len(waveform) / sample_rate,
                        "peak": peak,
                        "clipped_samples": clips,
                        "sha256": file_sha256(output_wav),
                    }
                )
                rows.append(row)
                print(f"skip existing {case['id']}: {output_wav}")
                continue

            prompt_text = case.get("prompt_text") or ""
            requested_mode = case.get("cosyvoice_mode") or ""
            start = time.perf_counter()
            chunks = []
            if requested_mode == "instruct2":
                row["cosyvoice_mode"] = "instruct2"
                instruct_text = case.get("instruct_text")
                if not instruct_text:
                    raise ValueError("cosyvoice_mode=instruct2 requires instruct_text.")
                generator = model.inference_instruct2(
                    case["text"],
                    instruct_text,
                    str(prompt_audio),
                    stream=False,
                )
            elif requested_mode == "cross_lingual":
                row["cosyvoice_mode"] = "cross_lingual_xvec"
                generator = model.inference_cross_lingual(
                    SYSTEM_PROMPT + case["text"],
                    str(prompt_audio),
                    stream=False,
                )
            elif prompt_text:
                row["cosyvoice_mode"] = "zero_shot"
                generator = model.inference_zero_shot(
                    case["text"],
                    SYSTEM_PROMPT + prompt_text,
                    str(prompt_audio),
                    stream=False,
                )
            else:
                row["cosyvoice_mode"] = "cross_lingual_xvec"
                generator = model.inference_cross_lingual(
                    SYSTEM_PROMPT + case["text"],
                    str(prompt_audio),
                    stream=False,
                )
            for item in generator:
                chunks.append(item["tts_speech"].detach().cpu())
            generation_seconds = time.perf_counter() - start
            if not chunks:
                raise RuntimeError("CosyVoice3 returned no audio chunks.")
            speech = torch.cat(chunks, dim=1)
            torchaudio.save(str(output_wav), speech, model.sample_rate)
            waveform = speech.squeeze(0).numpy()
            peak, clips = peak_and_clips(waveform)
            row.update(
                {
                    "status": "ok",
                    "generation_seconds": generation_seconds,
                    "audio_seconds": float(speech.shape[1] / model.sample_rate),
                    "rtf": float(generation_seconds / (speech.shape[1] / model.sample_rate)),
                    "sample_rate": int(model.sample_rate),
                    "peak": peak,
                    "clipped_samples": clips,
                    "sha256": file_sha256(output_wav),
                }
            )
            print(
                f"{case['id']}: generation={row['generation_seconds']:.3f}s "
                f"audio={row['audio_seconds']:.3f}s rtf={row['rtf']:.3f}"
            )
        except Exception as exc:
            row["status"] = "error"
            row["error"] = repr(exc)
            print(f"{case['id']}: ERROR {exc!r}")
        rows.append(row)
        write_jsonl(results_path, rows)

    payload = {
        "timestamp": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "model": "cosyvoice3",
        "model_dir": str(args.model_dir.resolve()),
        "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
        "python": platform.python_version(),
        "torch": torch.__version__,
        "fp16": args.fp16,
        "model_load_seconds": model_load_seconds,
        "results": rows,
    }
    payload_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    report_path.write_text(build_report(payload), encoding="utf-8")
    print(f"Saved results: {payload_path}")
    print(f"Saved report: {report_path}")


if __name__ == "__main__":
    main()
