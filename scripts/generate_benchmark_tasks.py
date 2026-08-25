#!/usr/bin/env python3
"""Create a large deterministic benchmark from verified TypeScript records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


FAMILY_CHECKS: dict[str, dict[str, Any]] = {
    "generic-indexed-access": {"required": ["keyof", "T[K]"], "forbidden": ["any"]},
    "null-narrowing": {"required_any": ["if", "typeof", "Array.isArray"], "forbidden": ["as any"]},
    "discriminated-union": {"required_any": ["kind", "==="]},
    "record-dictionary": {"required": ["Record"]},
    "readonly-generic": {"required": ["readonly"]},
    "async-return": {"required": ["Promise"]},
    "overload-signature": {"required": ["function"]},
    "mapped-type": {"required": ["keyof", "in"]},
    "type-predicate": {"required": ["value is string"]},
    "object-constraint": {"required": ["extends object"]},
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--count", type=int, default=3000)
    parser.add_argument("--split", choices=("any", "train", "validation", "test"), default="any")
    args = parser.parse_args()
    records = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines() if line]
    if args.split != "any":
        records = [record for record in records if record.get("split") == args.split]
    tasks: list[dict[str, Any]] = []
    for record in records[: args.count]:
        family = record.get("family", "typescript")
        checks: dict[str, Any] = dict(FAMILY_CHECKS.get(family, {}))
        checks.update({"mode": "typescript_fixture", "required_source": []})
        source_code = record.get("source_code", "")
        prompt = record["messages"][-1]["content"]
        if source_code and source_code not in prompt:
            prompt += "\n\nSource:\n```typescript\n" + source_code + "\n```"
        tasks.append({
            "id": f"generated-{record['id']}",
            "expert": "typescript",
            "domain": "typescript",
            "difficulty": "generated",
            "file_path": f"src/generated/{family}.ts",
            "file_text": source_code,
            "prompt": prompt,
            "checks": checks,
            "tags": ["typescript", family, "generated-heldout"],
            "provenance": record.get("provenance", {}),
        })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({
        "schema_version": "1.0",
        "name": "oktopai-typescript-generated",
        "description": "Large deterministic TypeScript routing and executable-response benchmark.",
        "source": str(args.input),
        "source_split": args.split,
        "tasks": tasks,
    }, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "tasks": len(tasks)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
