#!/usr/bin/env python3
"""Continue TypeScript work after v2 validation with a gated fresh lineage."""

from __future__ import annotations

import json
import os
import subprocess
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv-training/bin/python"
BASE = ROOT / ".oktopai/hf-bases/qwen2.5-coder-3b"
V2 = ROOT / ".oktopai/datasets/typescript-targeted-contract-v2-verified-20260829.jsonl"
EXTERNAL = ROOT / ".oktopai/datasets/typescript-external-training-gated.jsonl"
GAP = ROOT / ".oktopai/datasets/typescript-gap-v1-verified-20260830.jsonl"
TASKS = ROOT / "benchmarks/typescript-heldout-980.json"
REPORT = ROOT / ".oktopai/evaluations/typescript-targeted-v2-3b-heldout-980-seed-20260827.json"
ANALYSIS = ROOT / ".oktopai/evaluations/typescript-targeted-v2-980-family-analysis.json"
MIXED = ROOT / ".oktopai/datasets/typescript-targeted-v3-mixed-20260830.jsonl"
ADAPTER = ROOT / ".oktopai/adapters/typescript-targeted-v3-mixed-3b"
EVAL_DIR = ROOT / ".oktopai/evaluations"
ENV = {"HF_HOME": str(ROOT / ".oktopai/hf-cache"), "HF_DATASETS_CACHE": str(ROOT / ".oktopai/hf-cache/datasets"), "TRANSFORMERS_CACHE": str(ROOT / ".oktopai/hf-cache/transformers")}


def run(command: list[str]) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, env={**os.environ, **ENV}, check=True)


def report_complete() -> bool:
    try:
        data = json.loads(REPORT.read_text(encoding="utf-8"))
        return data.get("complete", True) is True and len(data.get("records", [])) == 980
    except (OSError, json.JSONDecodeError, TypeError):
        return False


def analyze() -> dict[str, object]:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    tasks = {item["id"]: item for item in json.loads(TASKS.read_text(encoding="utf-8"))["tasks"]}
    families: dict[str, dict[str, float]] = defaultdict(lambda: {"tasks": 0, "base_verified": 0, "adapter_verified": 0, "base_score": 0, "adapter_score": 0})
    for row in report["records"]:
        task = tasks[row["task_id"]]
        family = next((tag for tag in task.get("tags", []) if tag not in {"typescript", "generated-heldout"}), "unknown")
        item = families[family]
        item["tasks"] += 1
        item["base_verified"] += row["base"]["verification"]["status"] == "verified"
        item["adapter_verified"] += row["adapter"]["verification"]["status"] == "verified"
        item["base_score"] += row["base"]["verification"]["score"]
        item["adapter_score"] += row["adapter"]["verification"]["score"]
    for item in families.values():
        item["base_score"] /= item["tasks"]
        item["adapter_score"] /= item["tasks"]
    base = sum(v["base_verified"] for v in families.values())
    adapter = sum(v["adapter_verified"] for v in families.values())
    regressions = {name: item for name, item in families.items() if item["adapter_verified"] < item["base_verified"]}
    result = {"report": str(REPORT), "tasks": 980, "base_verified": base, "adapter_verified": adapter, "families": dict(families), "regressions": regressions, "gate": adapter >= base, "requires_gap_repair": bool(regressions)}
    ANALYSIS.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def valid_eval(path: Path, count: int) -> bool:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return len(data.get("records", [])) == count and data.get("complete", True) is True
    except (OSError, json.JSONDecodeError, TypeError):
        return False


def evaluate(path: Path, count: int, seed: int) -> None:
    if valid_eval(path, count):
        return
    run([str(PYTHON), "scripts/evaluate_adapter.py", "--base-model", str(BASE), "--adapter", str(ADAPTER), "--tasks", str(TASKS), "--domain", "typescript", "--max-tasks", str(count), "--shuffle-seed", str(seed), "--max-new-tokens", "256", "--device", "cuda", "--output", str(path), "--resume"])


def main() -> int:
    deadline = time.monotonic() + 12 * 60 * 60
    while not report_complete() and time.monotonic() < deadline:
        time.sleep(60)
    if not report_complete():
        raise SystemExit("v2 validation did not complete within the 12-hour follow-up window")
    decision = analyze()
    print(json.dumps(decision, indent=2), flush=True)
    if not decision["gate"]:
        return 0
    run([str(PYTHON), "scripts/generate_typescript_gap_data.py", "--count", "1200", "--output", str(GAP)])
    run([str(PYTHON), "scripts/merge_training_corpora.py", "--input", str(V2), "--input", str(EXTERNAL), "--input", str(GAP), "--output", str(MIXED)])
    had_checkpoint = any(ADAPTER.glob("checkpoint-*"))
    ADAPTER.mkdir(parents=True, exist_ok=True)
    for target in (3_000, 5_000, 8_000):
        command = [str(PYTHON), "scripts/train_lora.py", "--data", str(MIXED), "--base-model", str(BASE), "--output", str(ADAPTER), "--train", "--device", "cuda", "--max-steps", str(target), "--epochs", "3", "--loss-mode", "completion-only", "--no-eval"]
        if had_checkpoint:
            command.append("--resume")
        run(command)
        had_checkpoint = True
        evaluate(EVAL_DIR / f"typescript-targeted-v3-mixed-3b-step-{target}-heldout-200-seed-20260826.json", 200, 20260826)
        if time.monotonic() >= deadline:
            break
    if time.monotonic() < deadline and (ADAPTER / "adapter_model.safetensors").exists():
        evaluate(EVAL_DIR / "typescript-targeted-v3-mixed-3b-final-heldout-980-seed-20260827.json", 980, 20260827)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
