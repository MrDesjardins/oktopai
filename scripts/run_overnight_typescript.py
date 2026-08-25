#!/usr/bin/env python3
"""Run resumable overnight TypeScript experiments after the active run ends."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv-training/bin/python"
DATA = ROOT / ".oktopai/datasets/typescript-v8-data.jsonl"
BASE = ROOT / ".oktopai/hf-bases/qwen2.5-coder-0.5b"
TASKS = ROOT / "benchmarks/typescript-heldout-980.json"


def record(kind: str, name: str, status: str, metadata: dict) -> None:
    subprocess.run([sys.executable, "scripts/record_experiment.py", "--kind", kind, "--name", name, "--status", status, "--metadata", json.dumps(metadata)], cwd=ROOT, check=False)


def run(command: list[str], env: dict[str, str]) -> None:
    merged = os.environ.copy()
    merged.update(env)
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, env=merged, check=True)


def wait_for_adapter(path: Path) -> None:
    while not (path / "adapter_model.safetensors").exists():
        print(f"waiting for {path}", flush=True)
        time.sleep(30)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-long-run", action="store_true")
    parser.add_argument("--steps", type=int, default=2500)
    args = parser.parse_args()
    env = {"HF_HOME": str(ROOT / ".oktopai/hf-cache"), "HF_DATASETS_CACHE": str(ROOT / ".oktopai/hf-cache/datasets"), "TRANSFORMERS_CACHE": str(ROOT / ".oktopai/hf-cache/transformers")}
    v10 = ROOT / ".oktopai/adapters/typescript-v10-gpu"
    wait_for_adapter(v10)
    if not args.skip_long_run:
        name = "typescript-overnight-sft"
        record("training", name, "started", {"dataset": str(DATA), "steps": args.steps, "device": "cuda", "controller": __file__})
        try:
            run([str(PYTHON), "scripts/train_lora.py", "--data", str(DATA), "--base-model", str(BASE), "--output", str(ROOT / ".oktopai/adapters/typescript-overnight-sft"), "--train", "--device", "cuda", "--max-steps", str(args.steps), "--no-eval"], env)
            record("training", name, "completed", {"steps": args.steps, "adapter": ".oktopai/adapters/typescript-overnight-sft", "device": "cuda"})
        except subprocess.CalledProcessError as exc:
            record("training", name, "failed", {"returncode": exc.returncode})
            return exc.returncode
    candidate = ROOT / ".oktopai/adapters/typescript-overnight-sft" if not args.skip_long_run else v10
    evaluation = ROOT / ".oktopai/evaluations/overnight-heldout-200.json"
    run([str(PYTHON), "scripts/evaluate_adapter.py", "--base-model", str(BASE), "--adapter", str(candidate), "--tasks", str(TASKS), "--domain", "typescript", "--max-tasks", "200", "--shuffle-seed", "20260825", "--max-new-tokens", "256", "--device", "cuda", "--output", str(evaluation)], env)
    record("evaluation", "typescript-overnight-heldout-200", "completed", {"adapter": str(candidate), "tasks": 200, "device": "cuda", "quality_gate": "manual review required"})
    print(json.dumps({"candidate": str(candidate), "evaluation": str(evaluation), "next": "merge/export only after quality gate"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
