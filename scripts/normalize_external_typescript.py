#!/usr/bin/env python3
"""Normalize external TypeScript candidates without granting training eligibility."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def text(value: Any) -> str:
    return value if isinstance(value, str) else ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source", required=True)
    args = parser.parse_args()

    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    stats = {"input": 0, "instruction_rows": 0, "code_only_rows": 0, "duplicates": 0}
    for line_number, line in enumerate(args.input.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        stats["input"] += 1
        raw = json.loads(line)
        prompt = text(raw.get("instruction")) or text(raw.get("problem_description"))
        completion = text(raw.get("output")) or text(raw.get("content"))
        if not completion:
            continue
        kind = "instruction" if prompt else "code-only"
        stats[f"{kind.replace('-', '_')}_rows"] += 1
        if not prompt:
            prompt = "Analyze or improve this TypeScript code while preserving its intended API."
        key = hashlib.sha256(f"{prompt}\n{completion}".encode()).hexdigest()
        if key in seen:
            stats["duplicates"] += 1
            continue
        seen.add(key)
        records.append(
            {
                "id": f"external-{args.source.replace('/', '-')}-{line_number:06d}",
                "domain": "typescript",
                "family": "external-unclassified",
                "split": "candidate",
                "messages": [
                    {"role": "system", "content": "You are a precise TypeScript specialist. Return compiler-valid code."},
                    {"role": "user", "content": prompt},
                ],
                "completion": completion,
                "source_code": completion,
                "provenance": {
                    "source": args.source,
                    "source_line": line_number,
                    "source_kind": kind,
                    "training_eligible": False,
                    "verification_status": "unverified",
                },
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in records) + ("\n" if records else ""), encoding="utf-8")
    print(json.dumps({**stats, "output": str(args.output), "records": len(records)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
