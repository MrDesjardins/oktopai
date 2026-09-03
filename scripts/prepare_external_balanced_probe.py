#!/usr/bin/env python3
"""Create a deterministic family-capped probe from gated external records."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


def rank(item: dict[str, Any]) -> str:
    return hashlib.sha256(str(item["id"]).encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--max-per-family", type=int, default=120)
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines() if line.strip()]
    chosen: list[dict[str, Any]] = []
    for family in sorted({str(row.get("family", "unknown")) for row in rows}):
        family_rows = sorted((row for row in rows if row.get("family") == family), key=rank)
        chosen.extend(family_rows[: args.max_per_family])
    chosen.sort(key=lambda row: str(row["id"]))
    source_counts = Counter(str(row.get("provenance", {}).get("source", "unknown")) for row in chosen)
    manifest = {
        "input": str(args.input),
        "output": str(args.output),
        "records": len(chosen),
        "max_per_family": args.max_per_family,
        "families": dict(sorted(Counter(str(row.get("family", "unknown")) for row in chosen).items())),
        "sources": dict(sorted(source_counts.items())),
        "splits": dict(sorted(Counter(str(row.get("split", "unknown")) for row in chosen).items())),
        "selection": "stable SHA-256 ID order within each family",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in chosen) + "\n", encoding="utf-8")
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
