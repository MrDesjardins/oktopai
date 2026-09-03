#!/usr/bin/env python3
"""Run a bounded, resumable TypeScript adapter improvement loop.

The loop keeps one immutable experiment lineage, increases the training budget
only after each completed stage, evaluates every stage on the same held-out
seed, and records stage boundaries in the experiment ledger. It intentionally
does not export or promote any model.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv-training/bin/python"
DATA = ROOT / ".oktopai/datasets/typescript-focused-mixed-v1-6000.jsonl"
BASE = ROOT / ".oktopai/hf-bases/qwen2.5-coder-0.5b"
TASKS = ROOT / "benchmarks/typescript-heldout-980.json"
ADAPTER = ROOT / ".oktopai/adapters/typescript-focused-mixed-24h-loop"
EVAL_DIR = ROOT / ".oktopai/evaluations"
STEPS = (500, 1_000, 2_000, 3_000, 5_000, 8_000, 12_000)


def record(kind: str, name: str, status: str, metadata: dict[str, object]) -> None:
    subprocess.run(
        [str(PYTHON), "scripts/record_experiment.py", "--kind", kind,
         "--name", name, "--status", status, "--metadata", json.dumps(metadata)],
        cwd=ROOT,
        check=False,
    )


def run(command: list[str], env: dict[str, str]) -> None:
    merged = os.environ.copy()
    merged.update(env)
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, env=merged, check=True)


def summarize(path: Path) -> dict[str, object]:
    result = json.loads(path.read_text(encoding="utf-8"))
    summary: dict[str, object] = {"tasks": len(result["records"])}
    for label in ("base", "adapter"):
        rows = [item[label] for item in result["records"]]
        summary[label] = {
            "verified": sum(row["verification"]["status"] == "verified" for row in rows),
            "score": sum(row["verification"]["score"] for row in rows) / len(rows),
            "tok_per_sec": sum(row["tokens_per_second"] for row in rows) / len(rows),
        }
    return summary


def main() -> int:
    started = time.monotonic()
    env = {
        "HF_HOME": str(ROOT / ".oktopai/hf-cache"),
        "HF_DATASETS_CACHE": str(ROOT / ".oktopai/hf-cache/datasets"),
        "TRANSFORMERS_CACHE": str(ROOT / ".oktopai/hf-cache/transformers"),
    }
    ADAPTER.mkdir(parents=True, exist_ok=True)
    resumed = (ADAPTER / "adapter_model.safetensors").exists()
    record("training-loop", "typescript-focused-mixed-24h-loop", "started", {
        "data": str(DATA), "base_model": str(BASE), "adapter": str(ADAPTER),
        "step_budgets": list(STEPS), "device": "cuda", "heldout_seed": 20260826,
        "max_duration_hours": 24,
    })

    for target_steps in STEPS:
        if time.monotonic() - started >= 24 * 60 * 60:
            break
        name = f"typescript-focused-mixed-24h-step-{target_steps}"
        record("training", name, "started", {"target_steps": target_steps, "resume": resumed})
        try:
            command = [str(PYTHON), "scripts/train_lora.py", "--data", str(DATA),
                       "--base-model", str(BASE), "--output", str(ADAPTER), "--train",
                       "--device", "cuda", "--max-steps", str(target_steps),
                       "--loss-mode", "completion-only"]
            if resumed:
                command.append("--resume")
            run(command, env)
        except subprocess.CalledProcessError as exc:
            record("training", name, "failed", {"target_steps": target_steps, "returncode": exc.returncode})
            return exc.returncode
        resumed = True
        record("training", name, "completed", {"target_steps": target_steps, "adapter": str(ADAPTER), "device": "cuda"})

        evaluation = EVAL_DIR / f"typescript-focused-mixed-24h-step-{target_steps}-heldout-50.json"
        record("evaluation", name, "started", {"tasks": 50, "output": str(evaluation)})
        try:
            run([str(PYTHON), "scripts/evaluate_adapter.py", "--base-model", str(BASE),
                 "--adapter", str(ADAPTER), "--tasks", str(TASKS), "--domain", "typescript",
                 "--max-tasks", "50", "--shuffle-seed", "20260826", "--max-new-tokens", "256",
                 "--device", "cuda", "--output", str(evaluation)], env)
            summary = summarize(evaluation)
            record("evaluation", name, "completed", {"output": str(evaluation), **summary})
        except subprocess.CalledProcessError as exc:
            record("evaluation", name, "failed", {"output": str(evaluation), "returncode": exc.returncode})

    final = EVAL_DIR / "typescript-focused-mixed-24h-final-heldout-200.json"
    if (ADAPTER / "adapter_model.safetensors").exists() and time.monotonic() - started < 24 * 60 * 60:
        run([str(PYTHON), "scripts/evaluate_adapter.py", "--base-model", str(BASE),
             "--adapter", str(ADAPTER), "--tasks", str(TASKS), "--domain", "typescript",
             "--max-tasks", "200", "--shuffle-seed", "20260826", "--max-new-tokens", "256",
             "--device", "cuda", "--output", str(final)], env)
        record("evaluation", "typescript-focused-mixed-24h-final", "completed", {
            "output": str(final), "tasks": 200, **summarize(final), "promotion": "manual gate required",
        })
    record("training-loop", "typescript-focused-mixed-24h-loop", "completed", {
        "adapter": str(ADAPTER), "final_evaluation": str(final), "promotion": "not automatic",
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
