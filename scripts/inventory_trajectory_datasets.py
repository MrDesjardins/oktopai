#!/usr/bin/env python3
"""Inventory JSONL datasets for executable trajectory and provenance fields."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def is_admissible_source_record(record: dict[str, Any]) -> bool:
    provenance = record.get("provenance", {})
    if provenance.get("kind") != "public-github":
        return False
    license_id = provenance.get("license_spdx_id") or provenance.get("license")
    return (
        isinstance(record.get("trajectory"), list)
        and bool(record["trajectory"])
        and isinstance(record.get("repository_files"), dict)
        and isinstance(provenance.get("repository"), str)
        and isinstance(license_id, str)
        and bool(license_id.strip())
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()
    result = []
    for path in args.paths:
        records = trajectories = repository_snapshots = public_source = admissible = 0
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            records += 1
            trajectories += int(isinstance(record.get("trajectory"), list))
            repository_snapshots += int(isinstance(record.get("repository_files"), dict))
            public_source += int(record.get("provenance", {}).get("kind") == "public-github")
            admissible += int(is_admissible_source_record(record))
        result.append({"path": str(path), "records": records, "trajectory_records": trajectories, "repository_snapshots": repository_snapshots, "public_source_records": public_source, "admissible_source_records": admissible})
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
