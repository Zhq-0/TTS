#!/usr/bin/env python3
"""Run pre/post fine-tune comparison for the Genshin dots.tts experiment."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPERIMENT_DIR = (
    ROOT
    / "experiments"
    / "small_multispeaker_finetune"
    / "genshin_20_speakers_high_quality_60shot"
)
DEFAULT_PRETRAINED = (
    Path("<HF_CACHE_DIR>")
    / "models--rednote-hilab--dots.tts-mf"
    / "snapshots"
    / "25c53fb462e57087e52237daa5ea30df1c5cc328"
)
DEFAULT_EVAL_PYTHON = Path("<OMNIVOICE_ROOT>/.venv/Scripts/python.exe")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment-dir", type=Path, default=DEFAULT_EXPERIMENT_DIR)
    parser.add_argument("--pretrained-model-path", type=Path, default=DEFAULT_PRETRAINED)
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--checkpoint", type=Path, default=None)
    parser.add_argument("--cases", type=Path, default=None)
    parser.add_argument("--eval-python", type=Path, default=DEFAULT_EVAL_PYTHON)
    parser.add_argument("--num-steps", type=int, default=4)
    parser.add_argument("--max-generate-length", type=int, default=1200)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--skip-generation", action="store_true")
    parser.add_argument("--skip-official-eval", action="store_true")
    return parser.parse_args()


def resolve_checkpoint(run_dir: Path, checkpoint: Path | None) -> Path:
    if checkpoint is not None:
        path = checkpoint.resolve()
        if (path / "model").is_dir():
            return path / "model"
        if path.is_dir():
            return path
        raise FileNotFoundError(path)

    latest_model = run_dir / "latest" / "model"
    if latest_model.is_dir():
        return latest_model.resolve()

    checkpoints = []
    for path in run_dir.glob("checkpoint-*"):
        if path.is_dir() and (path / "model").is_dir():
            suffix = path.name.removeprefix("checkpoint-")
            if suffix.isdigit():
                checkpoints.append((int(suffix), path / "model"))
    if not checkpoints:
        raise FileNotFoundError(
            f"No fine-tune checkpoint found under {run_dir}. "
            "Wait for at least one checkpoint or pass --checkpoint."
        )
    return sorted(checkpoints)[-1][1].resolve()


def run_command(command: list[str], *, cwd: Path) -> None:
    print("+ " + " ".join(command), flush=True)
    subprocess.run(command, cwd=str(cwd), check=True)


def rel(path: Path, base: Path) -> str:
    try:
        return str(path.resolve().relative_to(base.resolve())).replace("\\", "/")
    except ValueError:
        return str(path.resolve()).replace("\\", "/")


def main() -> None:
    args = parse_args()
    experiment_dir = args.experiment_dir.resolve()
    run_dir = (
        args.run_dir.resolve()
        if args.run_dir is not None
        else experiment_dir / "runs" / "dots_tts_mf_genshin_20spk_60shot"
    )
    cases = (args.cases or experiment_dir / "evaluation" / "cases.jsonl").resolve()
    if not cases.is_file():
        run_command(
            [
                sys.executable,
                "scripts/prepare_genshin_post_finetune_eval_cases.py",
                "--experiment-dir",
                str(experiment_dir),
            ],
            cwd=ROOT,
        )
    if not cases.is_file():
        raise FileNotFoundError(cases)

    finetuned_model = resolve_checkpoint(run_dir, args.checkpoint)
    eval_python = args.eval_python if args.eval_python.is_file() else Path(sys.executable)

    output_root = experiment_dir / "evaluation" / "outputs"
    pretrained_output = output_root / "pretrained_dots_tts_mf"
    finetuned_output = output_root / f"finetuned_{finetuned_model.parent.name}"
    output_root.mkdir(parents=True, exist_ok=True)

    if not args.skip_generation:
        for output_dir, model_path in [
            (pretrained_output, args.pretrained_model_path.resolve()),
            (finetuned_output, finetuned_model),
        ]:
            run_command(
                [
                    sys.executable,
                    "scripts/run_zero_shot_suite.py",
                    "--cases",
                    str(cases),
                    "--output-dir",
                    str(output_dir),
                    "--model-name-or-path",
                    str(model_path),
                    "--num-steps",
                    str(args.num_steps),
                    "--max-generate-length",
                    str(args.max_generate_length),
                    "--overwrite",
                ],
                cwd=ROOT,
            )

    if not args.skip_official_eval:
        for output_dir in [pretrained_output, finetuned_output]:
            run_command(
                [
                    str(eval_python),
                    "scripts/evaluate_zero_shot_official_style.py",
                    "--output-dir",
                    str(output_dir),
                    "--device",
                    args.device,
                ],
                cwd=ROOT,
            )

    run_command(
        [
            sys.executable,
            "scripts/write_zero_shot_official_style_comparison.py",
            "--experiment-dir",
            str(experiment_dir / "evaluation"),
            "--model",
            "pretrained dots.tts-mf=outputs/pretrained_dots_tts_mf/official_style_metrics.json",
            "--model",
            f"finetuned {finetuned_model.parent.name}=outputs/{finetuned_output.name}/official_style_metrics.json",
            "--output-name",
            "post_finetune_official_style_comparison.md",
            "--summary-name",
            "post_finetune_official_style_summary.json",
        ],
        cwd=ROOT,
    )

    payload: dict[str, Any] = {
        "timestamp": datetime.now().astimezone().isoformat(),
        "cases": str(cases),
        "pretrained_model_path": str(args.pretrained_model_path.resolve()),
        "finetuned_model_path": str(finetuned_model),
        "pretrained_output": str(pretrained_output),
        "finetuned_output": str(finetuned_output),
        "comparison_report": str(
            experiment_dir / "evaluation" / "post_finetune_official_style_comparison.md"
        ),
        "metrics": ["rtf", "official_wer", "official_cer", "official_sim"],
        "note": "Use this report for the trained-vs-untrained dots.tts-mf comparison.",
    }
    status_path = experiment_dir / "evaluation" / "post_finetune_comparison_run.json"
    status_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved comparison run metadata: {status_path}")
    print(f"Saved comparison report: {payload['comparison_report']}")


if __name__ == "__main__":
    main()
