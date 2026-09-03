#!/usr/bin/env python3
"""Run the next reproducibility and gated-external TypeScript work package."""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv-training/bin/python"
BASE_05B = ROOT / ".oktopai/hf-bases/qwen2.5-coder-0.5b"
BASE_3B = ROOT / ".oktopai/hf-bases/qwen2.5-coder-3b"
DATA = ROOT / ".oktopai/datasets/typescript-external-training-gated.jsonl"
TASKS = ROOT / "benchmarks/typescript-heldout-980.json"
EVAL_DIR = ROOT / ".oktopai/evaluations"
ADAPTER_05B = ROOT / ".oktopai/adapters/typescript-focused-mixed-24h-loop"
ADAPTER_3B = ROOT / ".oktopai/adapters/typescript-external-gated-10h"
STEPS = (500, 1_000, 2_000, 3_000, 5_000, 8_000)


def record(kind: str, name: str, status: str, metadata: dict[str, object]) -> None:
    subprocess.run(
        [str(PYTHON), "scripts/record_experiment.py", "--kind", kind,
         "--name", name, "--status", status, "--metadata", json.dumps(metadata)],
        cwd=ROOT, check=False,
    )


def run(command: list[str], env: dict[str, str]) -> None:
    merged = os.environ.copy()
    merged.update(env)
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, env=merged, check=True)


def summarize(path: Path) -> dict[str, object]:
    result = json.loads(path.read_text(encoding="utf-8"))
    rows = result["records"]
    summary: dict[str, object] = {"tasks": len(rows)}
    for label in ("base", "adapter"):
        values = [row[label] for row in rows]
        summary[label] = {
            "verified": sum(x["verification"]["status"] == "verified" for x in values),
            "score": sum(x["verification"]["score"] for x in values) / len(values),
            "tok_per_sec": sum(x["tokens_per_second"] for x in values) / len(values),
        }
    return summary


def evaluate(adapter: Path, base: Path, output: Path, seed: int, tasks: int) -> None:
    run([str(PYTHON), "scripts/evaluate_adapter.py", "--base-model", str(base),
         "--adapter", str(adapter), "--tasks", str(TASKS), "--domain", "typescript",
         "--max-tasks", str(tasks), "--shuffle-seed", str(seed),
         "--max-new-tokens", "256", "--device", "cuda", "--output", str(output)], ENV)


ENV = {
    "HF_HOME": str(ROOT / ".oktopai/hf-cache"),
    "HF_DATASETS_CACHE": str(ROOT / ".oktopai/hf-cache/datasets"),
    "TRANSFORMERS_CACHE": str(ROOT / ".oktopai/hf-cache/transformers"),
}


def main() -> int:
    started = time.monotonic()
    record("pipeline", "typescript-next-10h", "started", {
        "purpose": "second-seed reproducibility plus gated external 3B probe",
        "max_duration_hours": 10, "promotion": "not automatic",
    })

    reproducibility = EVAL_DIR / "typescript-focused-mixed-24h-final-heldout-seed-20260827.json"
    record("evaluation", "typescript-focused-mixed-24h-final-seed-20260827", "started", {
        "adapter": str(ADAPTER_05B), "base_model": str(BASE_05B), "tasks": 200,
        "shuffle_seed": 20260827, "output": str(reproducibility),
    })
    evaluate(ADAPTER_05B, BASE_05B, reproducibility, 20260827, 200)
    record("evaluation", "typescript-focused-mixed-24h-final-seed-20260827", "completed", {
        "output": str(reproducibility), **summarize(reproducibility),
        "promotion": "manual gate required",
    })

    ADAPTER_3B.mkdir(parents=True, exist_ok=True)
    resumed = (ADAPTER_3B / "adapter_model.safetensors").exists()
    for target in STEPS:
        if time.monotonic() - started >= 10 * 60 * 60:
            break
        name = f"typescript-external-gated-10h-step-{target}"
        record("training", name, "started", {
            "data": str(DATA), "base_model": str(BASE_3B), "adapter": str(ADAPTER_3B),
            "target_steps": target, "resume": resumed, "device": "cuda",
        })
        command = [str(PYTHON), "scripts/train_lora.py", "--data", str(DATA),
                   "--base-model", str(BASE_3B), "--output", str(ADAPTER_3B), "--train",
                   "--device", "cuda", "--max-steps", str(target), "--epochs", "3",
                   "--loss-mode", "completion-only", "--no-eval"]
        if resumed:
            command.append("--resume")
        run(command, ENV)
        resumed = True
        record("training", name, "completed", {
            "data": str(DATA), "adapter": str(ADAPTER_3B), "target_steps": target,
            "device": "cuda",
        })
        output = EVAL_DIR / f"typescript-external-gated-10h-step-{target}-heldout-50.json"
        record("evaluation", name, "started", {
            "adapter": str(ADAPTER_3B), "tasks": 50, "shuffle_seed": 20260826,
            "output": str(output),
        })
        evaluate(ADAPTER_3B, BASE_3B, output, 20260826, 50)
        record("evaluation", name, "completed", {
            "output": str(output), **summarize(output),
            "promotion": "manual gate required",
        })

    final = EVAL_DIR / "typescript-external-gated-10h-final-heldout-200.json"
    if (ADAPTER_3B / "adapter_model.safetensors").exists() and time.monotonic() - started < 10 * 60 * 60:
        record("evaluation", "typescript-external-gated-10h-final", "started", {
            "adapter": str(ADAPTER_3B), "tasks": 200, "shuffle_seed": 20260827,
            "output": str(final),
        })
        evaluate(ADAPTER_3B, BASE_3B, final, 20260827, 200)
        record("evaluation", "typescript-external-gated-10h-final", "completed", {
            "output": str(final), **summarize(final),
            "promotion": "manual gate required",
        })
    record("pipeline", "typescript-next-10h", "completed", {
        "reproducibility": str(reproducibility), "adapter": str(ADAPTER_3B),
        "final_evaluation": str(final), "promotion": "not automatic",
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
