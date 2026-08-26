#!/usr/bin/env python3
"""Merge local TypeScript corpora without leaking test records into training."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", action="append", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows: list[dict] = []
    seen: set[str] = set()
    for source in args.input:
        for line in source.read_text(encoding="utf-8").splitlines():
            item = json.loads(line)
            if item.get("split") == "test" or item.get("id") in seen:
                continue
            seen.add(item["id"])
            item["provenance"] = {**item.get("provenance", {}), "merged_from": str(source)}
            rows.append(item)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "records": len(rows), "sources": [str(p) for p in args.input]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
