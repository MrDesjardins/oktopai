#!/usr/bin/env python3
"""Run a resumable, local-only TypeScript research queue.

This is intentionally conservative about promotion: it can spend hours making
and training candidates, but it never declares an adapter production-ready.
Every stage is recorded in ``experiments/runs.jsonl`` and existing artifacts
are reused.  It is suitable for unattended execution on the configured CUDA
machine.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv-training/bin/python"
BASE = ROOT / ".oktopai/hf-bases/qwen2.5-coder-0.5b"
DATA = ROOT / ".oktopai/datasets/typescript-synthetic-v3.jsonl"
TASKS = ROOT / "benchmarks/typescript-heldout-980.json"


def record(kind: str, name: str, status: str, metadata: dict) -> None:
    subprocess.run(
        [sys.executable, "scripts/record_experiment.py", "--kind", kind,
         "--name", name, "--status", status, "--metadata", json.dumps(metadata)],
        cwd=ROOT,
        check=False,
    )


def run(command: list[str], env: dict[str, str]) -> None:
    merged = os.environ.copy()
    merged.update(env)
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, env=merged, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=int, default=50_000)
    parser.add_argument("--steps", type=int, default=5_000)
    parser.add_argument("--eval-tasks", type=int, default=100)
    parser.add_argument("--skip-training", action="store_true")
    args = parser.parse_args()
    env = {
        "HF_HOME": str(ROOT / ".oktopai/hf-cache"),
        "HF_DATASETS_CACHE": str(ROOT / ".oktopai/hf-cache/datasets"),
        "TRANSFORMERS_CACHE": str(ROOT / ".oktopai/hf-cache/transformers"),
    }

    if not DATA.exists():
        record("data", "typescript-synthetic-v3", "started", {"records": args.records, "families": 10})
        run([sys.executable, "scripts/generate_typescript_synthetic.py", "--count", str(args.records),
             "--version", "typescript-synthetic-v3", "--output", str(DATA), "--verify"], env)
        record("data", "typescript-synthetic-v3", "completed", {"path": str(DATA), "records": args.records})

    adapter = ROOT / ".oktopai/adapters/typescript-v3-5000"
    if not args.skip_training and not (adapter / "adapter_model.safetensors").exists():
        record("training", "typescript-v3-5000", "started", {"dataset": str(DATA), "steps": args.steps, "device": "cuda"})
        run([str(PYTHON), "scripts/train_lora.py", "--data", str(DATA), "--base-model", str(BASE),
             "--output", str(adapter), "--train", "--device", "cuda", "--max-steps", str(args.steps), "--no-eval"], env)
        record("training", "typescript-v3-5000", "completed", {"adapter": str(adapter), "steps": args.steps, "device": "cuda"})

    if adapter.exists():
        evaluation = ROOT / ".oktopai/evaluations/typescript-v3-independent.json"
        record("evaluation", "typescript-v3-independent", "started", {"tasks": args.eval_tasks, "device": "cuda"})
        run([str(PYTHON), "scripts/evaluate_adapter.py", "--base-model", str(BASE), "--adapter", str(adapter),
             "--tasks", str(TASKS), "--domain", "typescript", "--max-tasks", str(args.eval_tasks),
             "--shuffle-seed", "20260826", "--max-new-tokens", "256", "--device", "cuda", "--output", str(evaluation)], env)
        record("evaluation", "typescript-v3-independent", "completed", {"evaluation": str(evaluation), "tasks": args.eval_tasks})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
