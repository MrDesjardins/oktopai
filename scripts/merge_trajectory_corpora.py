#!/usr/bin/env python3
"""Merge trajectory sources deterministically while preserving split metadata."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    records: list[dict] = []
    seen: set[str] = set()
    for source in args.input:
        for line in source.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            identifier = record.get("id")
            if not isinstance(identifier, str) or not identifier:
                raise ValueError(f"record missing id in {source}")
            if identifier in seen:
                raise ValueError(f"duplicate id: {identifier}")
            seen.add(identifier)
            records.append(record)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(json.dumps(record, ensure_ascii=False) for record in records) + "\n", encoding="utf-8")
    print(json.dumps({"records": len(records), "sources": [str(path) for path in args.input], "splits": dict(Counter(r.get("split", "missing") for r in records)), "unique_ids": len(seen), "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(), "output": str(args.output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
