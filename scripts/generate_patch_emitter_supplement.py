#!/usr/bin/env python3
"""Generate synthetic desktop-shaped patch-emitter trajectories."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def make(index: int, family: str, variant: str) -> dict:
    indent = " " * (2 + (index % 3) * 2)
    if family == "literal-union":
        prefix = 'type CompanionMode = "idle" | "walk" | "jump";\ntype Frame = { mode: CompanionMode };\n'
        bad = f"{indent}const frame: Frame = {{ mode: \"unknown\" }};\n"
        fixed = f"{indent}const frame: Frame = {{ mode: \"idle\" }};\n"
        issue = 'the state literal "unknown" must belong to the CompanionMode union'
        diagnostic = f"src/index.ts({prefix.count(chr(10)) + 1},1): error TS2322: Type '\"unknown\"' is not assignable to type 'CompanionMode'."
    elif family == "nullable-property":
        prefix = "type Frame = { speech?: string };\ndeclare const next: { speech: string | null };\n"
        bad = f"{indent}const frame: Frame = {{ speech: next.speech }};\n"
        fixed = f"{indent}const frame: Frame = {{ speech: next.speech ?? undefined }};\n"
        issue = "the nullable speech field must be converted to an optional string"
        diagnostic = f"src/index.ts({prefix.count(chr(10)) + 1},1): error TS2322: Type 'string | null' is not assignable to type 'string | undefined'."
    else:
        prefix = "declare const devicePixelRatio: number;\n"
        bad = f'{indent}const ratio: number = "1";\n'
        fixed = f"{indent}const ratio: number = 1;\n"
        issue = "the device-pixel ratio value must be numeric"
        diagnostic = f"src/index.ts({prefix.count(chr(10)) + 1},1): error TS2322: Type 'string' is not assignable to type 'number'."
    filler = "".join(f"function helper{index}_{n}(value: number): number {{ return value + {n}; }}\n" for n in range(24))
    source = prefix + filler + bad
    fixed_source = prefix + filler + fixed
    target_line = source.count("\n", 0, source.find(bad)) + 1
    if variant == "v2" and family == "nullable-property":
        diagnostic = diagnostic.replace(f"({target_line},", f"({target_line - 2},")
    if variant == "v2" and family == "number-mismatch":
        diagnostic = diagnostic.replace(f"({target_line},", f"({target_line + 3},")
    diagnostic = diagnostic.replace(f"({prefix.count(chr(10)) + 1},", f"({target_line},")
    path = "src/index.ts"
    return {
        "id": f"patch-emitter-supplement-{variant}-{family}-{index:03d}",
        "domain": "typescript-patch-emitter",
        "split": "validation" if index % 10 == 0 else "train",
        "task": f"Repair the {family} TypeScript error in {path}: {issue}. The compiler location may be downstream from the offending expression; inspect the numbered context and emit the compact replacement patch only.",
        "repository_facts": {"compiler": "typescript", "strict": True, "family": family, "large_file": True, "edit_mode": "exact-replacements"},
        "repository_files": {path: source},
        "compiler_diagnostic": diagnostic,
        "trajectory": [
            {"event": "inspect", "tool": "read_file", "args": {"path": path}},
            {"event": "diagnose", "tool": "run", "args": {"command": "tsc --noEmit --strict"}},
            {"event": "observe", "exit_code": 2},
            {"event": "edit", "tool": "apply_patch", "args": {"path": path, "replacements": [{"old": bad, "new": fixed}]}},
            {"event": "diagnose", "tool": "run", "args": {"command": "tsc --noEmit --strict"}},
            {"event": "observe", "exit_code": 0},
            {"event": "final", "content": "Applied the minimal replacement and verified TypeScript compilation."},
        ],
        "final": "Applied the minimal replacement and verified TypeScript compilation.",
        "provenance": {"kind": "programmatic-patch-emitter-supplement", "synthetic": True, "license": "CC0-like project seed"},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--count-per-family", type=int, default=20)
    parser.add_argument("--variant", default="v1")
    args = parser.parse_args()
    rows = [make(index, family, args.variant) for family in ("literal-union", "nullable-property", "number-mismatch") for index in range(args.count_per_family)]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "records": len(rows), "families": 3}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
