#!/usr/bin/env python3
"""Run a reproducible dots.tts zero-shot cloning suite."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf
import torch

from dots_tts.runtime import DotsTtsRuntime
from dots_tts.utils.logging import configure_logging
from dots_tts.utils.util import seed_everything


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPERIMENT_DIR = ROOT / "experiments" / "zero_shot_comparison"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DEFAULT_EXPERIMENT_DIR / "cases.jsonl")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_EXPERIMENT_DIR / "outputs" / "dots_tts_mf")
    parser.add_argument("--model-name-or-path", default="rednote-hilab/dots.tts-mf")
    parser.add_argument("--cache-dir", default="<HF_CACHE_DIR>")
    parser.add_argument("--precision", default="bfloat16")
    parser.add_argument("--num-steps", type=int, default=4)
    parser.add_argument("--guidance-scale", type=float, default=1.2)
    parser.add_argument("--speaker-scale", type=float, default=1.5)
    parser.add_argument("--max-generate-length", type=int, default=1200)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--case-id", action="append", default=[])
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--profile-inference", action="store_true")
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


def audio_seconds(path: Path) -> float:
    info = sf.info(path)
    return float(info.frames / info.samplerate)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def markdown_cell(value: Any) -> str:
    return str(value).replace("|", r"\|").replace("\n", "<br>")


def build_report(payload: dict[str, Any]) -> str:
    rows = payload["results"]
    completed = [row for row in rows if row["status"] == "ok"]
    lines = [
        "# dots.tts Zero-shot 克隆实验",
        "",
        "## 实验配置",
        "",
        f"- 时间：`{payload['timestamp']}`",
        f"- 模型：`{payload['model_name_or_path']}`",
        f"- 本地模型目录：`{payload.get('resolved_pretrained_path', '')}`",
        f"- 设备：`{payload['device']}`",
        f"- Python：`{payload['python']}`",
        f"- PyTorch：`{payload['torch']}`",
        f"- seed：`{payload['seed']}`",
        f"- 采样步数：`{payload['num_steps']}`",
        f"- guidance scale：`{payload['guidance_scale']}`",
        f"- speaker scale：`{payload['speaker_scale']}`",
        f"- max generate length：`{payload['max_generate_length']}`",
        f"- 模型加载耗时：{payload['model_load_seconds']:.3f} 秒",
        "",
        "## 生成结果",
        "",
        "| 项目 | 状态 | 参考音频 | 参考文本 | 目标语言 | 生成耗时 | 音频时长 | RTF | 峰值 | Clip 样本 | 输出 |",
        "|---|---|---|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        prompt_text = row.get("prompt_text") or "(x-vector only)"
        generation = f"{row['generation_seconds']:.3f} 秒" if row.get("generation_seconds") is not None else "-"
        duration = f"{row['audio_seconds']:.3f} 秒" if row.get("audio_seconds") is not None else "-"
        rtf = f"{row['rtf']:.3f}" if row.get("rtf") is not None else "-"
        peak = f"{row['peak']:.4f}" if row.get("peak") is not None else "-"
        clips = row.get("clipped_samples", "-")
        output = f"`{Path(row['output_wav']).name}`" if row.get("output_wav") else "-"
        lines.append(
            f"| {markdown_cell(row['name'])} | {row['status']} | "
            f"`{Path(row['prompt_audio']).name}` | {markdown_cell(prompt_text)} | "
            f"{row.get('language') or '-'} | {generation} | {duration} | {rtf} | "
            f"{peak} | {clips} | {output} |"
        )
    if completed:
        total_generation = sum(row["generation_seconds"] for row in completed)
        total_audio = sum(row["audio_seconds"] for row in completed)
        mean_rtf = sum(row["rtf"] for row in completed) / len(completed)
        overall_rtf = total_generation / total_audio if total_audio else float("inf")
        lines.extend(
            [
                "",
                "## 汇总",
                "",
                f"- 完成：{len(completed)} / {len(rows)}",
                f"- 平均 RTF：{mean_rtf:.3f}",
                f"- 总体 RTF：{overall_rtf:.3f}",
                f"- 总生成耗时：{total_generation:.3f} 秒",
                f"- 总音频时长：{total_audio:.3f} 秒",
            ]
        )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 英文用例使用 `cross_lingual_prompt.wav`，本地没有该音频的人工转写，因此采用 x-vector-only 克隆。",
            "- 自动自然度和音色相似度由 `scripts/evaluate_zero_shot_suite.py` 另行计算。",
            "- 主观听感请在 `manual_listening_evaluation.md` 中补评分。",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    configure_logging()
    seed_everything(args.seed)

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
    manual_path = args.output_dir / "manual_listening_evaluation.md"

    start_load = time.perf_counter()
    runtime = DotsTtsRuntime.from_pretrained(
        args.model_name_or_path,
        cache_dir=args.cache_dir,
        precision=args.precision,
        max_generate_length=args.max_generate_length,
    )
    model_load_seconds = time.perf_counter() - start_load

    rows: list[dict[str, Any]] = []
    for case in cases:
        output_wav = args.output_dir / case["output_name"]
        row = {
            **case,
            "model": "dots.tts",
            "model_name_or_path": args.model_name_or_path,
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

            result = runtime.generate(
                text=case["text"],
                prompt_audio_path=str(prompt_audio),
                prompt_text=case.get("prompt_text") or None,
                language=case.get("language") or None,
                num_steps=args.num_steps,
                guidance_scale=args.guidance_scale,
                speaker_scale=args.speaker_scale,
                profile_inference=args.profile_inference,
            )
            audio = result["audio"].detach().float().cpu().squeeze().numpy()
            sf.write(output_wav, audio, int(result["sample_rate"]))
            peak, clips = peak_and_clips(audio)
            row.update(
                {
                    "status": "ok",
                    "generation_seconds": float(result["time_used"]),
                    "audio_seconds": float(audio.shape[-1] / result["sample_rate"]),
                    "rtf": float(result["rtf"]),
                    "sample_rate": int(result["sample_rate"]),
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
        "model": "dots.tts",
        "model_name_or_path": args.model_name_or_path,
        "resolved_pretrained_path": str(runtime.pretrained_path),
        "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
        "python": platform.python_version(),
        "torch": torch.__version__,
        "seed": args.seed,
        "precision": args.precision,
        "num_steps": args.num_steps,
        "guidance_scale": args.guidance_scale,
        "speaker_scale": args.speaker_scale,
        "max_generate_length": args.max_generate_length,
        "model_load_seconds": model_load_seconds,
        "results": rows,
    }
    payload_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    report_path.write_text(build_report(payload), encoding="utf-8")

    if not manual_path.exists():
        manual_lines = [
            "# dots.tts Zero-shot 人工试听记录",
            "",
            "| 项目 | 发音准确性 /5 | 音色相似度 /5 | 自然度 /5 | 稳定性 /5 | 问题记录 |",
            "|---|---:|---:|---:|---:|---|",
        ]
        for row in rows:
            manual_lines.append(f"| {row['name']} | /5 | /5 | /5 | /5 | |")
        manual_path.write_text("\n".join(manual_lines) + "\n", encoding="utf-8")

    print(f"Saved results: {payload_path}")
    print(f"Saved report: {report_path}")


if __name__ == "__main__":
    main()
