#!/usr/bin/env python3
"""Verify mixed trajectory corpora with the correct repository replay lane."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from verify_real_repository_trajectory import replay as replay_real
from verify_trajectory import replay as replay_synthetic


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    failures = []
    total = 0
    for line in args.input.read_text().splitlines():
        if not line.strip():
            continue
        total += 1
        row = json.loads(line)
        family = row.get("provenance", {}).get("family")
        errors = replay_real(row, str(Path(__file__).resolve().parents[1] / "benchmarks/nextjs_fixture/node_modules/.bin/tsc")) if family == "real-repository-supplement" else replay_synthetic(row, str(Path(__file__).resolve().parents[1] / "benchmarks/nextjs_fixture/node_modules/.bin/tsc"))
        if errors:
            failures.append({"id": row.get("id"), "lane": "real" if family == "real-repository-supplement" else "synthetic", "errors": errors})
    result = {"input": str(args.input), "records": total, "passed": total - len(failures), "failed": len(failures), "failures": failures, "verified": total > 0 and not failures}
    print(json.dumps(result, indent=2))
    return 0 if result["verified"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
