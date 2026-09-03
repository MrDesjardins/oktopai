#!/usr/bin/env python3
"""Merge JSONL files while preserving the first record for each id."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("inputs", nargs="+", type=Path)
    args = parser.parse_args()
    rows = []
    seen: set[str] = set()
    for path in args.inputs:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            record_id = row.get("id")
            if not isinstance(record_id, str) or record_id in seen:
                raise ValueError(f"missing or duplicate id: {record_id!r}")
            seen.add(record_id)
            rows.append(row)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "records": len(rows), "unique_ids": len(seen)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
