#!/usr/bin/env python3
"""Generate varied numeric source-localization examples for patch emitters."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


PATTERNS = (
    ("ratio", "rawRatio", "number", 'rawRatio || "1"', "rawRatio || 1"),
    ("zoom", "configuredZoom", "number | undefined", 'configuredZoom ?? "1.0"', "configuredZoom ?? 1.0"),
    ("scale", "userScale", "number | null", 'userScale ? userScale : "1"', "userScale ? userScale : 1"),
    ("factor", "rawFactor", "number", 'rawFactor >= 0 ? rawFactor : "1"', "rawFactor >= 0 ? rawFactor : 1"),
)


def make(index: int) -> dict:
    name, variable, variable_type, bad_expr, good_expr = PATTERNS[index % len(PATTERNS)]
    indent = " " * (2 + (index % 4) * 2)
    filler = "".join(f"function helper_{index}_{n}(value: number) {{ return value + {n}; }}\n" for n in range(14 + index % 9))
    path = "src/index.ts"
    prefix = (
        f"declare const {variable}: {variable_type};\n"
        "declare const canvas: { width: number; height: number };\n"
        "const width = 176;\nconst height = 156;\n"
    )
    source = prefix + filler + (
        f"{indent}const {name} = {bad_expr};\n"
        f"{indent}const scaled = width * {name};\n"
        f"{indent}if (canvas.width !== scaled) {{ canvas.width = scaled; }}\n"
    )
    old = f"{indent}const {name} = {bad_expr};\n"
    new = f"{indent}const {name} = {good_expr};\n"
    source_line = source.count("\n", 0, source.find(old)) + 1
    diagnostic_line = source_line + 1 + (index % 2)
    diagnostic = f"{path}({diagnostic_line},24): error TS2362: The left-hand side of an arithmetic operation must be a number."
    wording = (
        "The error location may be downstream from the source expression. Trace the value backward, "
        "change the earlier non-numeric fallback, and emit exactly one minimal changed replacement."
    )
    replacements = [{"old": old, "new": new}]
    return {
        "id": f"patch-emitter-numeric-variant-{index:03d}",
        "domain": "typescript-patch-emitter",
        "split": "validation" if index % 10 == 0 else "train",
        "task": f"Repair the numeric TypeScript error in {path}. {wording} Never emit an unchanged replacement.",
        "repository_facts": {"compiler": "typescript", "strict": True, "family": "numeric-source-localization-variant", "large_file": True, "edit_mode": "exact-replacements"},
        "repository_files": {path: source},
        "compiler_diagnostic": diagnostic,
        "trajectory": [
            {"event": "inspect", "tool": "read_file", "args": {"path": path}},
            {"event": "diagnose", "tool": "run", "args": {"command": "tsc --noEmit --strict"}},
            {"event": "observe", "exit_code": 2},
            {"event": "edit", "tool": "apply_patch", "args": {"path": path, "replacements": replacements}},
            {"event": "diagnose", "tool": "run", "args": {"command": "tsc --noEmit --strict"}},
            {"event": "observe", "exit_code": 0},
            {"event": "final", "content": "Traced the diagnostic to the earlier numeric fallback, changed it, and verified compilation."},
        ],
        "final": "Traced the diagnostic to the earlier numeric fallback, changed it, and verified compilation.",
        "provenance": {"kind": "programmatic-numeric-localization-variant", "synthetic": True, "license": "CC0-like project seed"},
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
