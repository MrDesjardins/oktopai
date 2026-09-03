#!/usr/bin/env python3
"""Generate a deterministic, family-balanced TypeScript repair trajectory corpus."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


FAMILIES = (
    {
        "name": "unknown-length",
        "task": "Repair an unsafe unknown-value length access and verify it with strict TypeScript.",
        "before": "function {name}(value: unknown) {{ return value.length; }}\n",
        "after": "function {name}(value: unknown): number {{ return typeof value === 'string' ? value.length : 0; }}\n",
        "diagnosis": "Object is of type unknown.",
        "repair": "Narrowed the unknown value before accessing length.",
    },
    {
        "name": "nullable-property",
        "task": "Repair a property access on a nullable value and verify it with strict TypeScript.",
        "before": "function {name}(value: {{ name: string }} | null) {{ return value.name; }}\n",
        "after": "function {name}(value: {{ name: string }} | null): string {{ return value?.name ?? ''; }}\n",
        "diagnosis": "Value is possibly null.",
        "repair": "Used optional chaining and a fallback for the nullable value.",
    },
    {
        "name": "unknown-property",
        "task": "Repair an unsafe property read from an unknown value and verify it with strict TypeScript.",
        "before": "function {name}(value: unknown) {{ return value.name; }}\n",
        "after": "function {name}(value: unknown): string {{ return typeof value === 'object' && value !== null && 'name' in value ? String(value.name) : ''; }}\n",
        "diagnosis": "Property access is not allowed on unknown.",
        "repair": "Added an object and property guard before reading name.",
    },
    {
        "name": "generic-string",
        "task": "Repair a generic value being used as a string and verify it with strict TypeScript.",
        "before": "function {name}<T>(value: T) {{ return value.toUpperCase(); }}\n",
        "after": "function {name}<T>(value: T): string {{ return typeof value === 'string' ? value.toUpperCase() : ''; }}\n",
        "diagnosis": "Generic T does not provide string methods.",
        "repair": "Narrowed the generic value to string before calling toUpperCase.",
    },
    {
        "name": "implicit-any",
        "task": "Repair an implicit-any function parameter and verify it with strict TypeScript.",
        "before": "function {name}(value) {{ return value.trim(); }}\n",
        "after": "function {name}(value: string): string {{ return value.trim(); }}\n",
        "diagnosis": "Parameter value implicitly has an any type.",
        "repair": "Added an explicit string annotation to the parameter.",
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
        "id": f"typescript-trajectory-v2-{index:06d}",
        "domain": "typescript",
        "family": family["name"],
        "split": "validation" if index % 5 == 0 else "train",
        "task": family["task"],
        "repository_facts": {"package_manager": "npm", "compiler": "typescript", "strict": True},
        "repository_files": {"src/index.ts": before},
        "trajectory": [
            {"event": "inspect", "tool": "read_file", "args": {"path": "src/index.ts"}, "result_summary": before.strip()},
            {"event": "diagnose", "tool": "run", "args": {"command": "tsc --noEmit --strict"}},
            {"event": "observe", "exit_code": 2, "output_summary": str(family["diagnosis"])},
            {"event": "edit", "tool": "apply_patch", "args": {"path": "src/index.ts", "content": after}, "result_summary": str(family["repair"])},
            {"event": "retry", "content": "The strict compiler identified the unsafe typing; retrying after the repair."},
            {"event": "diagnose", "tool": "run", "args": {"command": "tsc --noEmit --strict"}},
            {"event": "observe", "exit_code": 0, "output_summary": "Compilation passed."},
            {"event": "final", "content": final},
        ],
        "final": final,
        "verification": {"compiler": "strict", "status": "pending-replay"},
        "provenance": {"kind": "programmatic-trajectory-family-seed", "synthetic": True, "license": "CC0-like project seed"},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.count < len(FAMILIES) or args.count % len(FAMILIES):
        parser.error(f"count must be a positive multiple of {len(FAMILIES)}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(json.dumps(make(i), ensure_ascii=False) for i in range(args.count)) + "\n", encoding="utf-8")
    print(json.dumps({"records": args.count, "families": len(FAMILIES), "output": str(args.output), "verified": "pending-replay"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
