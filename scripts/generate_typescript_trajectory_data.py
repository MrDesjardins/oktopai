#!/usr/bin/env python3
"""Create a small deterministic inspect/diagnose/edit/retry corpus."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def make(index: int) -> dict[str, object]:
    name = f"value{index:04d}"
    before = f"function {name}(value: unknown) {{ return value.length; }}\n"
    after = f"function {name}(value: unknown): number {{ return typeof value === 'string' ? value.length : 0; }}\n"
    return {
        "id": f"typescript-trajectory-v1-{index:06d}",
        "domain": "typescript", "split": "validation" if index % 10 == 0 else "train",
        "task": "Repair the unsafe unknown-value length access and verify it with strict TypeScript.",
        "repository_facts": {"package_manager": "npm", "compiler": "typescript", "strict": True},
        "repository_files": {"src/index.ts": before},
        "trajectory": [
            {"event": "inspect", "tool": "read_file", "args": {"path": "src/index.ts"}, "result_summary": before.strip()},
            {"event": "diagnose", "tool": "run", "args": {"command": "tsc --noEmit --strict"}},
            {"event": "observe", "exit_code": 2, "output_summary": "Object is of type unknown."},
            {"event": "edit", "tool": "apply_patch", "args": {"path": "src/index.ts", "content": after}, "result_summary": "Replaced unsafe access with a type guard."},
            {"event": "retry", "content": "The first compile failed because unknown must be narrowed before reading length."},
            {"event": "diagnose", "tool": "run", "args": {"command": "tsc --noEmit --strict"}},
            {"event": "observe", "exit_code": 0, "output_summary": "Compilation passed."},
            {"event": "final", "content": "Narrowed the unknown value before accessing length; strict compilation passes."}
        ],
        "final": "Narrowed the unknown value before accessing length; strict compilation passes.",
        "verification": {"compiler": "strict", "status": "pending-replay"},
        "provenance": {"kind": "programmatic-trajectory-seed", "synthetic": True, "license": "CC0-like project seed"}
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(json.dumps(make(i), ensure_ascii=False) for i in range(args.count)) + "\n", encoding="utf-8")
    print(json.dumps({"records": args.count, "output": str(args.output), "verified": "pending-replay"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
