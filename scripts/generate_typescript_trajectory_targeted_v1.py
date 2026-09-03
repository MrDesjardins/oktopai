#!/usr/bin/env python3
"""Generate verifier-backed trajectories targeting v2 transfer failures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


FAMILIES = ("record-numeric-method", "primitive-array-narrowing")


def fixture(family: str, index: int) -> tuple[str, str, str, str]:
    if family == "record-numeric-method":
        methods = ("toUpperCase()", "trim()", "charAt(0)", "toLowerCase()")
        bad = methods[index % len(methods)]
        before = f"function recordNumeric{index:04d}(record: Record<string, number>, key: string) {{ return record[key].{bad}; }}\n"
        after = f"function recordNumeric{index:04d}(record: Record<string, number>, key: string): string {{ return record[key].toFixed({index % 3}); }}\n"
        return before, after, "Record values are numbers and do not provide the requested string method.", "Used a numeric method consistent with Record<string, number>."
    variants = (
        "return value[0].toFixed(2);",
        "return value[index].toFixed(1);",
        "return value.at(0)?.toFixed(0) ?? '';",
        "return value[index].toUpperCase();",
    )
    bad = variants[index % len(variants)]
    after = f"function primitiveArray{index:04d}(value: string[] | number[], index = 0): string {{ const item = value[index]; return typeof item === 'number' ? item.toFixed({index % 3}) : item; }}\n"
    before = f"function primitiveArray{index:04d}(value: string[] | number[], index = 0) {{ {bad} }}\n"
    return before, after, "The array element may be a string and must be narrowed before using a number method.", "Used typeof on the primitive array element before calling toFixed."


def make(index: int, count: int) -> dict[str, object]:
    family = FAMILIES[index % len(FAMILIES)]
    family_index = index // len(FAMILIES)
    before, after, diagnosis, repair = fixture(family, family_index)
    final = f"{repair} Strict compilation passes."
    return {
        "id": f"typescript-trajectory-targeted-v1-{index:06d}",
        "domain": "typescript",
        "family": family,
        "split": "validation" if index % 4 == 0 else "train",
        "task": f"Repair a {family.replace('-', ' ')} error and verify it with strict TypeScript.",
        "repository_facts": {"package_manager": "npm", "compiler": "typescript", "strict": True},
        "repository_files": {"src/index.ts": before},
        "trajectory": [
            {"event": "inspect", "tool": "read_file", "args": {"path": "src/index.ts"}, "result_summary": before.strip()},
            {"event": "diagnose", "tool": "run", "args": {"command": "tsc --noEmit --strict"}},
            {"event": "observe", "exit_code": 2, "output_summary": diagnosis},
            {"event": "edit", "tool": "apply_patch", "args": {"path": "src/index.ts", "content": after}, "result_summary": repair},
            {"event": "retry", "content": "The compiler failure identified an invalid method or narrowing assumption; retrying after the type-aware repair."},
            {"event": "diagnose", "tool": "run", "args": {"command": "tsc --noEmit --strict"}},
            {"event": "observe", "exit_code": 0, "output_summary": "Compilation passed."},
            {"event": "final", "content": final},
        ],
        "final": final,
        "verification": {"compiler": "strict", "status": "pending-replay"},
        "provenance": {"kind": "programmatic-targeted-transfer-gap", "synthetic": True, "license": "CC0-like project seed"},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=40)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.count < 8 or args.count % 2:
        parser.error("count must be an even number of at least 8")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(json.dumps(make(i, args.count), ensure_ascii=False) for i in range(args.count)) + "\n", encoding="utf-8")
    print(json.dumps({"records": args.count, "families": list(FAMILIES), "output": str(args.output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
