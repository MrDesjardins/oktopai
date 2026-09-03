#!/usr/bin/env python3
"""Deduplicate JSONL records by ID while requiring duplicate payloads to match."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def fingerprint(row: dict) -> str:
    return hashlib.sha256(json.dumps(row, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows: list[dict] = []
    seen: dict[str, str] = {}
    duplicates = 0
    for line in args.input.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        record_id = row.get("id")
        if not isinstance(record_id, str):
            raise ValueError(f"missing string id: {record_id!r}")
        digest = fingerprint(row)
        previous = seen.get(record_id)
        if previous is not None:
            if previous != digest:
                raise ValueError(f"conflicting duplicate id: {record_id}")
            duplicates += 1
            continue
        seen[record_id] = digest
        rows.append(row)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")
    print(json.dumps({"input": str(args.input), "output": str(args.output), "input_records": len(rows) + duplicates, "output_records": len(rows), "identical_duplicates_removed": duplicates}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
