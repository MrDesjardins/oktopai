#!/usr/bin/env python3
"""Generate deterministic trajectory tasks from families absent from v2 training."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


FAMILIES = (
    {
        "name": "union-return",
        "task": "Repair a union value returned from a string-only function and verify it with strict TypeScript.",
        "before": "function {name}(value: string | number): string {{ return value; }}\n",
        "after": "function {name}(value: string | number): string {{ return typeof value === 'string' ? value : String(value); }}\n",
        "diagnosis": "The string or number union is not assignable to string.",
        "repair": "Converted the numeric union branch to a string before returning it.",
    },
    {
        "name": "discriminated-union",
        "task": "Repair a discriminated union property use and verify it with strict TypeScript.",
        "before": "function {name}(shape: {{ kind: 'count'; value: number }} | {{ kind: 'label'; value: string }}) {{ return shape.value.toFixed(2); }}\n",
        "after": "function {name}(shape: {{ kind: 'count'; value: number }} | {{ kind: 'label'; value: string }}): string {{ return shape.kind === 'count' ? shape.value.toFixed(2) : shape.value; }}\n",
        "diagnosis": "Property toFixed does not exist on every union member.",
        "repair": "Narrowed the union by its discriminant before calling toFixed.",
    },
    {
        "name": "array-union",
        "task": "Repair a method call on an array union and verify it with strict TypeScript.",
        "before": "function {name}(value: string[] | number[]) {{ return value[0].toFixed(2); }}\n",
        "after": "function {name}(value: string[] | number[]): string {{ const item = value[0]; return typeof item === 'number' ? item.toFixed(2) : item; }}\n",
        "diagnosis": "The array element may be a string without toFixed.",
        "repair": "Narrowed the array element before calling the number method.",
    },
    {
        "name": "object-literal-mismatch",
        "task": "Repair an object literal that violates its declared property type and verify it with strict TypeScript.",
        "before": "const {name}: {{ label: string; count: number }} = {{ label: 7, count: 1 }};\n",
        "after": "const {name}: {{ label: string; count: number }} = {{ label: 'ok', count: 1 }};\n",
        "diagnosis": "Number is not assignable to the string label property.",
        "repair": "Changed the label value to a string matching the declared type.",
    },
    {
        "name": "record-method",
        "task": "Repair an invalid method call on a record value and verify it with strict TypeScript.",
        "before": "function {name}(record: Record<string, number>, key: string) {{ return record[key].toUpperCase(); }}\n",
        "after": "function {name}(record: Record<string, number>, key: string): string {{ return record[key].toFixed(2); }}\n",
        "diagnosis": "Record values are numbers and do not provide toUpperCase.",
        "repair": "Called the numeric toFixed method on the record value.",
    },
)


def make(index: int) -> dict[str, object]:
    family = FAMILIES[index % len(FAMILIES)]
    family_index = index // len(FAMILIES)
    name = f"{family['name'].replace('-', '')}{family_index:04d}"
    before = str(family["before"]).format(name=name)
    after = str(family["after"]).format(name=name)
    final = f"{family['repair']} Strict compilation passes."
    return {
        "id": f"typescript-trajectory-unseen-{index:06d}",
        "domain": "typescript",
        "family": family["name"],
        "split": "test",
        "task": family["task"],
        "repository_facts": {"package_manager": "npm", "compiler": "typescript", "strict": True},
        "repository_files": {"src/index.ts": before},
        "trajectory": [
            {"event": "inspect", "tool": "read_file", "args": {"path": "src/index.ts"}, "result_summary": before.strip()},
            {"event": "diagnose", "tool": "run", "args": {"command": "tsc --noEmit --strict"}},
            {"event": "observe", "exit_code": 2, "output_summary": str(family["diagnosis"])},
            {"event": "edit", "tool": "apply_patch", "args": {"path": "src/index.ts", "content": after}, "result_summary": str(family["repair"])},
            {"event": "retry", "content": "The strict compiler identified the type error; retrying after the repair."},
            {"event": "diagnose", "tool": "run", "args": {"command": "tsc --noEmit --strict"}},
            {"event": "observe", "exit_code": 0, "output_summary": "Compilation passed."},
            {"event": "final", "content": final},
        ],
        "final": final,
        "verification": {"compiler": "strict", "status": "pending-replay"},
        "provenance": {"kind": "programmatic-unseen-evaluation-seed", "synthetic": True, "license": "CC0-like project seed"},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=50)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.count < len(FAMILIES) or args.count % len(FAMILIES):
        parser.error(f"count must be a positive multiple of {len(FAMILIES)}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(json.dumps(make(i), ensure_ascii=False) for i in range(args.count)) + "\n", encoding="utf-8")
    print(json.dumps({"records": args.count, "families": len(FAMILIES), "split": "test", "output": str(args.output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
