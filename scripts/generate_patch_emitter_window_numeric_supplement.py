#!/usr/bin/env python3
"""Generate window.devicePixelRatio source-localization examples."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def make(index: int) -> dict:
    indent = " " * (2 + (index % 4) * 2)
    fallback = '"1"' if index % 2 == 0 else '"1.0"'
    numeric = "1" if index % 3 else "1.0"
    filler = "".join(f"function helper_{index}_{n}(value: number) {{ return value + {n}; }}\n" for n in range(18 + index % 8))
    path = "src/window-ratio.ts"
    prefix = (
        "declare const window: { devicePixelRatio: number };\n"
        "declare const canvas: { width: number };\n"
        "const width = 176;\n"
    )
    bad = f'{indent}const ratio = window.devicePixelRatio || {fallback};\n'
    fixed = f'{indent}const ratio = window.devicePixelRatio || {numeric};\n'
    source = prefix + filler + bad + f"{indent}const scaled = width * ratio;\n"
    source_line = source.count("\n", 0, source.find(bad)) + 1
    diagnostic = f"{path}({source_line + 1},24): error TS2362: The left-hand side of an arithmetic operation must be a number."
    return {
        "id": f"patch-emitter-window-numeric-{index:03d}",
        "domain": "typescript-patch-emitter",
        "split": "validation" if index % 12 == 0 else "train",
        "task": f"Repair the numeric TypeScript error in {path}. The diagnostic points at a downstream arithmetic use; trace the value to the earlier window.devicePixelRatio fallback and emit one minimal changed replacement. Never emit an unchanged replacement.",
        "repository_facts": {"compiler": "typescript", "strict": True, "family": "window-numeric-source-localization", "large_file": True, "edit_mode": "exact-replacements"},
        "repository_files": {path: source},
        "compiler_diagnostic": diagnostic,
        "trajectory": [
            {"event": "inspect", "tool": "read_file", "args": {"path": path}},
            {"event": "diagnose", "tool": "run", "args": {"command": "tsc --noEmit --strict"}},
            {"event": "observe", "exit_code": 2},
            {"event": "edit", "tool": "apply_patch", "args": {"path": path, "replacements": [{"old": bad, "new": fixed}]}},
            {"event": "diagnose", "tool": "run", "args": {"command": "tsc --noEmit --strict"}},
            {"event": "observe", "exit_code": 0},
            {"event": "final", "content": "Traced the downstream diagnostic to the window numeric fallback, changed it, and verified compilation."},
        ],
        "final": "Traced the downstream diagnostic to the window numeric fallback, changed it, and verified compilation.",
        "provenance": {"kind": "programmatic-window-numeric-supplement", "synthetic": True, "license": "CC0-like project seed"},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--count", type=int, default=24)
    args = parser.parse_args()
    rows = [make(index) for index in range(args.count)]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "records": len(rows)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
