#!/usr/bin/env python3
"""Generate a balanced targeted corpus with regression-protection families."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


FAMILIES = (
    "record-numeric-method",
    "primitive-array-narrowing",
    "discriminated-union-protection",
    "object-literal-protection",
)
COUNTS = (20, 20, 10, 10)


def fixture(family: str, index: int) -> tuple[str, str, str, str]:
    if family == "record-numeric-method":
        methods = ("toUpperCase()", "trim()", "charAt(0)", "toLowerCase()")
        bad = methods[index % len(methods)]
        before = f"function recordNumeric{index:04d}(record: Record<string, number>, key: string) {{ return record[key].{bad}; }}\n"
        after = f"function recordNumeric{index:04d}(record: Record<string, number>, key: string): string {{ return record[key].toFixed({index % 3}); }}\n"
        return before, after, "Record values are numbers and do not provide the requested string method.", "Used a numeric method consistent with Record<string, number>."
    if family == "primitive-array-narrowing":
        bad = ("value[0].toFixed(2)", "value[index].toUpperCase()", "value[0].trim()", "value[index].charAt(0)")[index % 4]
        before = f"function primitiveArray{index:04d}(value: string[] | number[], index = 0) {{ return {bad}; }}\n"
        after = f"function primitiveArray{index:04d}(value: string[] | number[], index = 0): string {{ const item = value[index]; return typeof item === 'number' ? item.toFixed({index % 3}) : item; }}\n"
        return before, after, "The array element may be a string or number and must be narrowed before using a type-specific method.", "Used typeof on the primitive array element before calling the appropriate method."
    if family == "discriminated-union-protection":
        before = f"function discriminated{index:04d}(shape: {{ kind: 'count'; value: number }} | {{ kind: 'label'; value: string }}) {{ return shape.value.toFixed(2); }}\n"
        after = f"function discriminated{index:04d}(shape: {{ kind: 'count'; value: number }} | {{ kind: 'label'; value: string }}): string {{ return shape.kind === 'count' ? shape.value.toFixed(2) : shape.value; }}\n"
        return before, after, "Property toFixed does not exist on every union member.", "Narrowed the union by its discriminant before calling toFixed."
    before = f"const objectLiteral{index:04d}: {{ label: string; count: number }} = {{ label: 7, count: 1 }};\n"
    after = f"const objectLiteral{index:04d}: {{ label: string; count: number }} = {{ label: 'ok', count: 1 }};\n"
    return before, after, "Number is not assignable to the string label property.", "Changed the label value to a string matching the declared type."


def make(family: str, family_index: int, global_index: int) -> dict[str, object]:
    before, after, diagnosis, repair = fixture(family, family_index)
    final = f"{repair} Strict compilation passes."
    return {
        "id": f"typescript-trajectory-targeted-v2-{global_index:06d}",
        "domain": "typescript",
        "family": family,
        "split": "validation" if family_index % 5 == 0 else "train",
        "task": f"Repair a {family.replace('-', ' ')} error and verify it with strict TypeScript.",
        "repository_facts": {"package_manager": "npm", "compiler": "typescript", "strict": True},
        "repository_files": {"src/index.ts": before},
        "trajectory": [
            {"event": "inspect", "tool": "read_file", "args": {"path": "src/index.ts"}, "result_summary": before.strip()},
            {"event": "diagnose", "tool": "run", "args": {"command": "tsc --noEmit --strict"}},
            {"event": "observe", "exit_code": 2, "output_summary": diagnosis},
            {"event": "edit", "tool": "apply_patch", "args": {"path": "src/index.ts", "content": after}, "result_summary": repair},
            {"event": "retry", "content": "The compiler failure identified an invalid type assumption; retrying after the type-aware repair."},
            {"event": "diagnose", "tool": "run", "args": {"command": "tsc --noEmit --strict"}},
            {"event": "observe", "exit_code": 0, "output_summary": "Compilation passed."},
            {"event": "final", "content": final},
        ],
        "final": final,
        "verification": {"compiler": "strict", "status": "pending-replay"},
        "provenance": {"kind": "programmatic-targeted-regression-protection", "synthetic": True, "license": "CC0-like project seed"},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    records = []
    global_index = 0
    for family, count in zip(FAMILIES, COUNTS):
        for family_index in range(count):
            records.append(make(family, family_index, global_index))
            global_index += 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in records) + "\n", encoding="utf-8")
    print(json.dumps({"records": len(records), "families": dict(zip(FAMILIES, COUNTS)), "output": str(args.output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
