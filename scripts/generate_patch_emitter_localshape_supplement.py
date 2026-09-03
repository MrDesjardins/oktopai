#!/usr/bin/env python3
"""Generate synthetic React/desktop-shaped patch-emitter examples."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def make(index: int, family: str) -> dict:
    indent = " " * (4 + (index % 2) * 2)
    filler = "".join(f"function helper{index}_{n}(value: number): number {{ return value + {n}; }}\n" for n in range(35))
    if family == "literal-union":
        prefix = 'type CompanionMode = "idle" | "walk" | "jump" | "focused";\ntype RenderFrame = { mode: CompanionMode };\n'
        opening = "const frame: RenderFrame = {\n"
        bad = f'{indent}mode: "unknown",\n'
        fixed = f'{indent}mode: "idle",\n'
        issue = 'the object state literal must belong to the CompanionMode union'
        diagnostic_offset = 0
        message = 'Type \'"unknown"\' is not assignable to type \'CompanionMode\'.'
    elif family == "nullable-property":
        prefix = "type RenderFrame = { speech?: string };\ndeclare const next: { speech: string | null };\n"
        opening = "function update() {\n  return {\n"
        bad = f'{indent}speech: next.speech\n'
        fixed = f'{indent}speech: next.speech ?? undefined\n'
        issue = "the nullable native speech field must become an optional string"
        diagnostic_offset = -2
        message = "Type 'string | null' is not assignable to type 'string | undefined'."
    else:
        prefix = "declare const canvas: { width: number };\ndeclare const desktopDevicePixelRatio: number;\nconst width = 176;\nconst height = 156;\n"
        opening = ""
        bad = f'{indent}const ratio = desktopDevicePixelRatio || "1";\n'
        fixed = f'{indent}const ratio = desktopDevicePixelRatio || 1;\n'
        issue = "the device-pixel ratio fallback must remain numeric"
        diagnostic_offset = 4
        message = "The right-hand side of an arithmetic operation must be numeric."
    suffix = "};\n" if family == "literal-union" else ("  };\n}\nconst frame: RenderFrame = update();\n" if family == "nullable-property" else "")
    body = bad + (f"{indent}const scaled = width * ratio;\n" if family == "number-mismatch" else "")
    source = prefix + filler + opening + body + suffix
    target_line = source.count("\n", 0, source.find(bad)) + 1
    diagnostic_line = target_line + diagnostic_offset
    diagnostic = f"src/index.ts({diagnostic_line},5): error TS2322: {message}"
    path = "src/index.ts"
    replacements = [{"old": bad, "new": fixed}]
    return {
        "id": f"patch-emitter-localshape-{family}-{index:03d}",
        "domain": "typescript-patch-emitter",
        "split": "validation" if index % 10 == 0 else "train",
        "task": f"Repair the {family} TypeScript error in {path}: {issue}. The diagnostic may identify a nearby or downstream expression. Emit one minimal exact replacement only.",
        "repository_facts": {"compiler": "typescript", "strict": True, "family": family, "large_file": True, "edit_mode": "exact-replacements"},
        "repository_files": {path: source},
        "compiler_diagnostic": diagnostic,
        "trajectory": [
            {"event": "inspect", "tool": "read_file", "args": {"path": path}},
            {"event": "diagnose", "tool": "run", "args": {"command": "tsc --noEmit --strict"}},
            {"event": "observe", "exit_code": 2},
            {"event": "edit", "tool": "apply_patch", "args": {"path": path, "replacements": replacements}},
            {"event": "diagnose", "tool": "run", "args": {"command": "tsc --noEmit --strict"}},
            {"event": "observe", "exit_code": 0},
            {"event": "final", "content": "Applied one minimal replacement and verified TypeScript compilation."},
        ],
        "final": "Applied one minimal replacement and verified TypeScript compilation.",
        "provenance": {"kind": "programmatic-local-shape-supplement", "synthetic": True, "license": "CC0-like project seed"},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--count-per-family", type=int, default=20)
    args = parser.parse_args()
    families = ("literal-union", "nullable-property", "number-mismatch")
    rows = [make(index, family) for family in families for index in range(args.count_per_family)]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "records": len(rows), "families": len(families)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
