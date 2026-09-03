#!/usr/bin/env python3
"""Generate numeric diagnostic-source localization examples."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def make(index: int) -> dict:
    indent = " " * (2 + (index % 3) * 2)
    fallback = '"1"' if index % 2 == 0 else '"1.0"'
    numeric = "1" if index % 2 == 0 else "1.0"
    filler = "".join(f"function helper_{index}_{n}(value: number) {{ return value + {n}; }}\n" for n in range(24 + index % 7))
    prefix = (
        "declare const canvas: { width: number; height: number };\n"
        "declare const desktopDevicePixelRatio: number;\n"
        "const width = 176;\nconst height = 156;\n"
    )
    source = prefix + filler + (
        f"{indent}const ratio = desktopDevicePixelRatio || {fallback};\n"
        f"{indent}const scaledWidth = width * ratio;\n"
        f"{indent}if (canvas.width !== scaledWidth) {{ canvas.width = scaledWidth; }}\n"
    )
    target = f"{indent}const ratio = desktopDevicePixelRatio || {fallback};\n"
    fixed = f"{indent}const ratio = desktopDevicePixelRatio || {numeric};\n"
    target_line = source.count("\n", 0, source.find(target)) + 1
    diagnostic_line = target_line + (3 + index % 3)
    path = "src/index.ts"
    diagnostic = (
        f"{path}({diagnostic_line},18): error TS2362: The left-hand side of an arithmetic operation must be a number."
    )
    replacements = [{"old": target, "new": fixed}]
    return {
        "id": f"patch-emitter-numeric-source-{index:03d}",
        "domain": "typescript-patch-emitter",
        "split": "validation" if index % 10 == 0 else "train",
        "task": (
            f"Repair the numeric TypeScript error in {path}. The compiler may point to a downstream "
            "arithmetic use; locate and repair the source expression that introduces the non-numeric fallback. "
            "Emit one minimal exact replacement only, and never emit an unchanged replacement."
        ),
        "repository_facts": {"compiler": "typescript", "strict": True, "family": "number-mismatch", "large_file": True, "edit_mode": "exact-replacements"},
        "repository_files": {path: source},
        "compiler_diagnostic": diagnostic,
        "trajectory": [
            {"event": "inspect", "tool": "read_file", "args": {"path": path}},
            {"event": "diagnose", "tool": "run", "args": {"command": "tsc --noEmit --strict"}},
            {"event": "observe", "exit_code": 2},
            {"event": "edit", "tool": "apply_patch", "args": {"path": path, "replacements": replacements}},
            {"event": "diagnose", "tool": "run", "args": {"command": "tsc --noEmit --strict"}},
            {"event": "observe", "exit_code": 0},
            {"event": "final", "content": "Repaired the numeric fallback at its source and verified compilation."},
        ],
        "final": "Repaired the numeric fallback at its source and verified compilation.",
        "provenance": {"kind": "programmatic-numeric-source-supplement", "synthetic": True, "license": "CC0-like project seed"},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--count", type=int, default=40)
    args = parser.parse_args()
    rows = [make(index) for index in range(args.count)]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "records": len(rows)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
