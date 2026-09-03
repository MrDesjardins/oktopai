#!/usr/bin/env python3
"""Run static quality checks on a trajectory JSONL corpus before training."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from oktopai.trajectory import validate_trajectory


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--require-repository-snapshot", action="store_true")
    args = parser.parse_args()
    failures = []
    ids = set()
    records = []
    for line_number, line in enumerate(args.input.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        record = json.loads(line)
        records.append(record)
        record_id = record.get("id")
        if not isinstance(record_id, str) or not record_id:
            failures.append({"line": line_number, "code": "missing_id"})
        elif record_id in ids:
            failures.append({"line": line_number, "id": record_id, "code": "duplicate_id"})
        ids.add(record_id)
        issues = validate_trajectory(record)
        failures.extend({"line": line_number, "id": record_id, "code": issue.code, "message": issue.message} for issue in issues)
        if args.require_repository_snapshot and not isinstance(record.get("repository_files"), dict):
            failures.append({"line": line_number, "id": record_id, "code": "missing_repository_snapshot"})
    splits = Counter(record.get("split", "missing") for record in records)
    families = Counter(record.get("repository_facts", {}).get("family", "unknown") for record in records)
    result = {"input": str(args.input), "records": len(records), "unique_ids": len(ids), "splits": dict(splits), "families": dict(families), "failed_checks": len(failures), "failures": failures[:20], "static_quality_pass": bool(records) and not failures}
    print(json.dumps(result, indent=2))
    return 0 if result["static_quality_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
