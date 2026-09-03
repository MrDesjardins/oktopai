#!/usr/bin/env python3
"""Run the corrected targeted TypeScript queue unattended.

The handoff called the adapter a 0.5B probe, but its PEFT manifest points to
the 3B base. This queue follows the manifest, reuses checkpoints, skips valid
reports, and never exports or promotes a model.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv-training/bin/python"
BASE = ROOT / ".oktopai/hf-bases/qwen2.5-coder-3b"
ADAPTER = ROOT / ".oktopai/adapters/typescript-targeted-0.5b-probe"
DATA = ROOT / ".oktopai/datasets/typescript-targeted-contract-verified-20260828.jsonl"
TASKS = ROOT / "benchmarks/typescript-heldout-980.json"
EVAL_DIR = ROOT / ".oktopai/evaluations"
TARGETS = (3_000, 5_000, 8_000, 12_000)
MAX_SECONDS = 10 * 60 * 60
ENV = {"HF_HOME": str(ROOT / ".oktopai/hf-cache"), "HF_DATASETS_CACHE": str(ROOT / ".oktopai/hf-cache/datasets"), "TRANSFORMERS_CACHE": str(ROOT / ".oktopai/hf-cache/transformers")}


def record(kind: str, name: str, status: str, metadata: dict[str, object]) -> None:
    subprocess.run([str(PYTHON), "scripts/record_experiment.py", "--kind", kind, "--name", name, "--status", status, "--metadata", json.dumps(metadata)], cwd=ROOT, env={**os.environ, **ENV}, check=False)


def valid_report(path: Path, expected_tasks: int) -> bool:
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
        return report.get("base_model") == str(BASE) and report.get("adapter") == str(ADAPTER) and len(report.get("records", [])) == expected_tasks
    except (OSError, json.JSONDecodeError, TypeError):
        return False


def run(command: list[str]) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, env={**os.environ, **ENV}, check=True)


def checkpoint_steps() -> list[int]:
    return sorted(int(path.name.removeprefix("checkpoint-")) for path in ADAPTER.glob("checkpoint-*") if path.name.removeprefix("checkpoint-").isdigit())


def evaluate(output: Path, seed: int, tasks: int) -> None:
    run([str(PYTHON), "scripts/evaluate_adapter.py", "--base-model", str(BASE), "--adapter", str(ADAPTER), "--tasks", str(TASKS), "--domain", "typescript", "--max-tasks", str(tasks), "--shuffle-seed", str(seed), "--max-new-tokens", "256", "--device", "cuda", "--output", str(output)])


def main() -> int:
    started = time.monotonic()
    ADAPTER.mkdir(parents=True, exist_ok=True)
    config = json.loads((ADAPTER / "adapter_config.json").read_text(encoding="utf-8"))
    if Path(config.get("base_model_name_or_path", "")).name != BASE.name:
        raise RuntimeError("targeted adapter manifest is not compatible with the 3B base")
    record("pipeline", "typescript-targeted-overnight-20260828", "started", {"base_model": str(BASE), "adapter": str(ADAPTER), "data": str(DATA), "targets": list(TARGETS), "max_duration_hours": 10, "promotion": "never automatic"})

    seed2 = EVAL_DIR / "typescript-targeted-3b-compatible-heldout-50-seed-20260827.json"
    if not valid_report(seed2, 50):
        evaluate(seed2, 20260827, 50)
    for target in TARGETS:
        if time.monotonic() - started >= MAX_SECONDS:
            break
        stage = EVAL_DIR / f"typescript-targeted-3b-step-{target}-heldout-50-seed-20260826.json"
        current = max(checkpoint_steps(), default=0)
        if current < target:
            name = f"typescript-targeted-3b-step-{target}"
            record("training", name, "started", {"target_steps": target, "resume_from": current})
            try:
                run([str(PYTHON), "scripts/train_lora.py", "--data", str(DATA), "--base-model", str(BASE), "--output", str(ADAPTER), "--train", "--device", "cuda", "--max-steps", str(target), "--epochs", "3", "--loss-mode", "completion-only", "--no-eval", "--resume"])
            except subprocess.CalledProcessError as exc:
                record("training", name, "failed", {"target_steps": target, "returncode": exc.returncode})
                return exc.returncode
        if not valid_report(stage, 50):
            evaluate(stage, 20260826, 50)
    final = EVAL_DIR / "typescript-targeted-3b-overnight-final-heldout-200-seed-20260827.json"
    if time.monotonic() - started < MAX_SECONDS and not valid_report(final, 200):
        evaluate(final, 20260827, 200)
    record("pipeline", "typescript-targeted-overnight-20260828", "completed", {"final_evaluation": str(final), "promotion": "not automatic"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
