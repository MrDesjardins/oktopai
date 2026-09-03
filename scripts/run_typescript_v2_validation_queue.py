#!/usr/bin/env python3
"""Run extended held-out validation for the isolated TypeScript v2 probe."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv-training/bin/python"
BASE = ROOT / ".oktopai/hf-bases/qwen2.5-coder-3b"
ADAPTER = ROOT / ".oktopai/adapters/typescript-targeted-v2-3b-probe"
TASKS = ROOT / "benchmarks/typescript-heldout-980.json"
EVAL_DIR = ROOT / ".oktopai/evaluations"
ENV = {"HF_HOME": str(ROOT / ".oktopai/hf-cache"), "HF_DATASETS_CACHE": str(ROOT / ".oktopai/hf-cache/datasets"), "TRANSFORMERS_CACHE": str(ROOT / ".oktopai/hf-cache/transformers")}


def valid(path: Path, count: int) -> bool:
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
        return (report.get("base_model") == str(BASE)
                and report.get("adapter") == str(ADAPTER)
                and len(report.get("records", [])) == count
                and report.get("complete", True) is True)
    except (OSError, json.JSONDecodeError, TypeError):
        return False


def run(output: Path, count: int, seed: int) -> None:
    if valid(output, count):
        print(f"skip valid {output}", flush=True)
        return
    command = [str(PYTHON), "scripts/evaluate_adapter.py", "--base-model", str(BASE), "--adapter", str(ADAPTER), "--tasks", str(TASKS), "--domain", "typescript", "--max-tasks", str(count), "--shuffle-seed", str(seed), "--max-new-tokens", "256", "--device", "cuda", "--output", str(output), "--resume"]
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, env={**os.environ, **ENV}, check=True)


def summary(path: Path) -> dict[str, object]:
    report = json.loads(path.read_text(encoding="utf-8"))
    result: dict[str, object] = {"report": str(path), "tasks": len(report["records"])}
    for label in ("base", "adapter"):
        rows = [row[label] for row in report["records"]]
        result[label] = {
            "verified": sum(row["verification"]["status"] == "verified" for row in rows),
            "score": sum(row["verification"]["score"] for row in rows) / len(rows),
            "tokens_per_second": sum(row["tokens_per_second"] for row in rows) / len(rows),
        }
    return result


def main() -> int:
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    reports = [
        (EVAL_DIR / "typescript-targeted-v2-3b-heldout-200-seed-20260826.json", 200, 20260826),
        (EVAL_DIR / "typescript-targeted-v2-3b-heldout-980-seed-20260827.json", 980, 20260827),
    ]
    for output, count, seed in reports:
        run(output, count, seed)
    result = {"base_model": str(BASE), "adapter": str(ADAPTER), "reports": [summary(path) for path, _, _ in reports]}
    path = EVAL_DIR / "typescript-targeted-v2-validation-summary.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
