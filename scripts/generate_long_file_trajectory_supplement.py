#!/usr/bin/env python3
"""Generate synthetic long-file trajectories using exact replacement edits."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / ".oktopai/datasets/typescript-trajectories-long-file-replacements-v2.jsonl"


def make(index: int) -> dict:
    name = f"longUnion{index:02d}"
    filler = "\n".join(f"function helper{index:02d}_{n}(value: number): number {{ return value + {n}; }}" for n in range(90))
    broken_line = f"export function {name}(value: string | number) {{ return value.toUpperCase(); }}"
    fixed_line = f"export function {name}(value: string | number) {{ return typeof value === \"string\" ? value.toUpperCase() : value.toFixed(2); }}"
    source = filler + "\n" + broken_line + "\n"
    fixed = filler + "\n" + fixed_line + "\n"
    path = "src/index.ts"
    trajectory = [
        {"event": "inspect", "tool": "read_file", "args": {"path": path}},
        {"event": "diagnose", "tool": "run", "args": {"command": "tsc --noEmit --strict"}},
        {"event": "observe", "exit_code": 2},
        {"event": "edit", "tool": "apply_patch", "args": {"path": path, "replacements": [{"old": broken_line, "new": fixed_line}]}},
        {"event": "diagnose", "tool": "run", "args": {"command": "tsc --noEmit --strict"}},
        {"event": "observe", "exit_code": 0},
        {"event": "final", "content": "Applied an exact once-only replacement in the long file and verified strict compilation."},
    ]
    return {
        "id": f"long-file-replacement-{index:03d}",
        "domain": "typescript",
        "family": "long-file-union-narrowing",
        "split": "train",
        "task": f"Repair the union-narrowing error in the long file {path}. Use an exact replacement edit rather than regenerating the complete file, then verify strict TypeScript compilation. Emit the canonical trajectory JSON contract.",
        "repository_facts": {"package_manager": "npm", "compiler": "typescript", "strict": True, "family": "long-file-union-narrowing", "long_file": True},
        "repository_files": {path: source},
        "trajectory": trajectory,
        "final": trajectory[-1]["content"],
        "provenance": {"kind": "programmatic-long-file-seed", "family": "programmatic-long-file", "synthetic": True, "license": "CC0-like project seed", "variant": index},
    }


def main() -> int:
    rows = [make(index) for index in range(60)]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUT), "records": len(rows), "split": "train", "edit_mode": "exact-replacements"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
