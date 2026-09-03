#!/usr/bin/env python3
"""Run a resumable fixed-suite adapter evaluation in small process chunks."""

from __future__ import annotations

import argparse
import json
import os
import random
import subprocess
from pathlib import Path


def valid(path: Path, base: str, adapter: str, count: int) -> bool:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return (data.get("base_model") == base and data.get("adapter") == adapter
                and data.get("complete", True) is True
                and len(data.get("records", [])) == count
                and len({row.get("task_id") for row in data["records"]}) == count)
    except (OSError, json.JSONDecodeError, TypeError):
        return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-model", type=Path, required=True)
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--tasks", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--chunk-size", type=int, default=5)
    parser.add_argument("--count", type=int, default=200)
    parser.add_argument("--max-new-tokens", type=int, default=64)
    parser.add_argument("--max-seconds", type=float, default=None)
    parser.add_argument("--subprocess-timeout", type=float, default=120.0)
    parser.add_argument("--base-report", type=Path, default=None)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    args = parser.parse_args()
    available = len(json.loads(args.tasks.read_text(encoding="utf-8"))["tasks"])
    task_count = min(args.count, available)
    base = str(args.base_model.resolve())
    adapter = str(args.adapter.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    records: list[dict] = []
    for offset in range(0, task_count, args.chunk_size):
        count = min(args.chunk_size, task_count - offset)
        chunk = args.output.with_name(f"{args.output.stem}-chunk-{offset:04d}-{offset + count:04d}.json")
        while not valid(chunk, base, adapter, count):
            command = [str(Path(__file__).resolve().parents[1] / ".venv-training/bin/python"),
                       str(Path(__file__).resolve().parents[0] / "evaluate_adapter.py"),
                       "--base-model", base, "--adapter", adapter, "--tasks", str(args.tasks.resolve()),
                       "--domain", "typescript", "--max-tasks", str(count), "--offset", str(offset),
                       "--shuffle-seed", str(args.seed), "--max-new-tokens", str(args.max_new_tokens),
                       "--device", args.device, "--output", str(chunk)]
            command.append("--resume")
            if args.base_report is not None:
                command.extend(["--base-report", str(args.base_report.resolve())])
            if args.max_seconds is not None:
                command.extend(["--max-seconds", str(args.max_seconds)])
            print("+", " ".join(command), flush=True)
            try:
                subprocess.run(command, cwd=Path(__file__).resolve().parents[1],
                               env={**os.environ, "HF_HOME": str(Path(__file__).resolve().parents[1] / ".oktopai/hf-cache")},
                               check=True, timeout=args.subprocess_timeout)
            except subprocess.TimeoutExpired:
                if valid(chunk, base, adapter, count):
                    print(json.dumps({"offset": offset, "completed_during_shutdown": str(chunk)}), flush=True)
                    continue
                # Preserve completed records and make the timed-out task explicit
                # so resume can advance without silently changing the suite.
                partial = json.loads(chunk.read_text(encoding="utf-8"))
                shuffled = json.loads(args.tasks.read_text(encoding="utf-8"))["tasks"]
                shuffled = [t for t in shuffled if t.get("domain") == "typescript"]
                random.Random(args.seed).shuffle(shuffled)
                expected = shuffled[offset:offset + count]
                done = {row.get("task_id") for row in partial.get("records", [])}
                missing = next((t for t in expected if t["id"] not in done), None)
                if missing is None:
                    raise
                partial.setdefault("records", []).append({
                    "task_id": missing["id"],
                    "timeout": True,
                    "base": {"output": "", "seconds": args.subprocess_timeout, "new_tokens": 0,
                             "tokens_per_second": 0, "verification": {"status": "failed", "score": 0.0,
                             "checks": [], "failures": ["generation-timeout"], "executable": False}},
                    "adapter": {"output": "", "seconds": args.subprocess_timeout, "new_tokens": 0,
                                "tokens_per_second": 0, "verification": {"status": "failed", "score": 0.0,
                                "checks": [], "failures": ["generation-timeout"], "executable": False}},
                })
                partial["complete"] = False
                chunk.write_text(json.dumps(partial, indent=2) + "\n", encoding="utf-8")
                print(json.dumps({"offset": offset, "timed_out_task": missing["id"]}), flush=True)
        data = json.loads(chunk.read_text(encoding="utf-8"))
        records.extend(data["records"])
        print(json.dumps({"offset": offset, "chunk": str(chunk), "records": len(records)}), flush=True)
    if len(records) != task_count or len({row.get("task_id") for row in records}) != task_count:
        raise SystemExit("chunk merge did not produce the expected unique task count")
    result = {"base_model": base, "adapter": adapter, "domain": "typescript", "task_count": task_count,
              "records": records, "complete": True, "generation_max_new_tokens": args.max_new_tokens,
              "warning": "Raw fixed-suite comparison; apply family gates and human review before promotion."}
    temporary = args.output.with_name(args.output.name + ".tmp")
    temporary.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    temporary.replace(args.output)
    print(json.dumps({"output": str(args.output), "records": task_count, "complete": True}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
