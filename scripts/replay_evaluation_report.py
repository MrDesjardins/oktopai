#!/usr/bin/env python3
"""Replay parsed adapter outputs from an evaluator report after normalization."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from oktopai.trajectory import normalize_trajectory, validate_trajectory


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = {row["id"]: row for row in (json.loads(line) for line in args.data.read_text().splitlines() if line.strip())}
    rows = []
    raw_valid = normalized_valid = 0
    for result in json.loads(args.report.read_text())["records"]:
        parsed = result["adapter"].get("parsed")
        if not isinstance(parsed, dict) or result["id"] not in source:
            continue
        base = {key: source[result["id"]][key] for key in ("id", "domain", "split", "task", "repository_facts", "repository_files", "provenance") if key in source[result["id"]]}
        raw = dict(base, trajectory=parsed.get("trajectory"), final=parsed.get("final"))
        normalized = normalize_trajectory(raw)
        raw_issues = validate_trajectory(raw)
        issues = validate_trajectory(normalized)
        raw_valid += not raw_issues
        normalized_valid += not issues
        if not issues:
            rows.append(normalized)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + ("\n" if rows else ""))
    print(json.dumps({"records": len(source), "raw_contract_valid": raw_valid, "normalized_contract_valid": normalized_valid, "replay_input": str(args.output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
