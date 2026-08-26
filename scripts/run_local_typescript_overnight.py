#!/usr/bin/env python3
"""Complete a resumable local TypeScript data/training/evaluation cycle."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv-training/bin/python"


def record(kind: str, name: str, status: str, metadata: dict[str, object]) -> None:
    subprocess.run(
        [sys.executable, "scripts/record_experiment.py", "--kind", kind, "--name", name,
         "--status", status, "--metadata", json.dumps(metadata)],
        cwd=ROOT,
        check=False,
    )


def run(command: list[str]) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def line_count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.open(encoding="utf-8") if line.strip())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--teacher", type=Path, default=ROOT / ".oktopai/teacher-traces/typescript-repository-qwen7b-v1.jsonl")
    parser.add_argument("--expected", type=int, default=2450)
    parser.add_argument("--wait-seconds", type=int, default=60)
    parser.add_argument("--max-steps", type=int, default=6000)
    parser.add_argument("--min-accepted", type=int, default=250)
    args = parser.parse_args()
    accepted = ROOT / ".oktopai/datasets/typescript-repository-qwen7b-verified-v1.jsonl"
    adapter = ROOT / ".oktopai/adapters/typescript-repository-qwen7b-student-v1"
    evaluation = ROOT / ".oktopai/evaluations/typescript-repository-qwen7b-student-v1-heldout-200.json"

    record("pipeline", "typescript-local-overnight-v1", "started", {
        "teacher": str(args.teacher), "expected_records": args.expected,
        "max_steps": args.max_steps, "device": "cuda",
    })
    while line_count(args.teacher) < args.expected:
        count = line_count(args.teacher)
        print(json.dumps({"waiting_for_teacher_records": args.expected, "completed": count}), flush=True)
        time.sleep(args.wait_seconds)

    tsc = ROOT / "benchmarks/nextjs_fixture/node_modules/.bin/tsc"
    run([str(sys.executable), "scripts/ingest_verified_teacher_data.py", "--input", str(args.teacher), "--output", str(accepted), "--tsc", str(tsc), "--timeout", "30", "--workers", "8"])
    accepted_count = line_count(accepted)
    record("verification", "typescript-repository-qwen7b-v1", "completed", {
        "teacher_records": args.expected, "accepted_records": accepted_count,
        "output": str(accepted), "compiler": "strict TypeScript",
    })
    if accepted_count < args.min_accepted:
        record("pipeline", "typescript-local-overnight-v1", "stopped", {
            "reason": "acceptance_gate_failed", "accepted_records": accepted_count,
            "minimum_required": args.min_accepted,
        })
        print(json.dumps({"status": "stopped", "reason": "acceptance_gate_failed", "accepted": accepted_count}, indent=2))
        return 3

    record("training", "typescript-repository-qwen7b-student-v1", "started", {
        "data": str(accepted), "records": accepted_count, "steps": args.max_steps,
        "device": "cuda", "base_model": ".oktopai/hf-bases/qwen2.5-coder-3b",
    })
    run([str(PYTHON), "scripts/train_lora.py", "--data", str(accepted),
         "--base-model", str(ROOT / ".oktopai/hf-bases/qwen2.5-coder-3b"),
         "--output", str(adapter), "--train", "--device", "cuda",
         "--max-steps", str(args.max_steps), "--epochs", "3", "--no-eval"])
    record("training", "typescript-repository-qwen7b-student-v1", "completed", {
        "data": str(accepted), "records": accepted_count, "steps": args.max_steps,
        "adapter": str(adapter), "device": "cuda",
    })
    run([str(PYTHON), "scripts/evaluate_adapter.py",
         "--base-model", str(ROOT / ".oktopai/hf-bases/qwen2.5-coder-3b"),
         "--adapter", str(adapter), "--tasks", str(ROOT / "benchmarks/typescript-heldout-980.json"),
         "--domain", "typescript", "--max-tasks", "200", "--shuffle-seed", "20260826",
         "--max-new-tokens", "256", "--device", "cuda", "--output", str(evaluation)])
    record("evaluation", "typescript-repository-qwen7b-student-v1-heldout-200", "completed", {
        "adapter": str(adapter), "tasks": 200, "device": "cuda", "raw": str(evaluation),
        "quality_gate": "manual_review_required",
    })
    print(json.dumps({"status": "completed", "accepted": accepted_count, "adapter": str(adapter), "evaluation": str(evaluation)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
