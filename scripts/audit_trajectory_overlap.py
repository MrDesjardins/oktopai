#!/usr/bin/env python3
"""Audit exact identifier and repair-pair overlap between train and eval JSONL."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def records(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def repair_pair(record: dict[str, Any]) -> tuple[str, str]:
    source = next((content for path, content in record.get("repository_files", {}).items() if path.startswith("lib/")), "")
    edit = next((event.get("args", {}).get("content", "") for event in record.get("trajectory", []) if event.get("event") == "edit"), "")
    return source, edit


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", type=Path, required=True)
    parser.add_argument("--eval", type=Path, required=True)
    args = parser.parse_args()
    train = records(args.train)
    evaluation = records(args.eval)
    train_ids = {record.get("id") for record in train}
    eval_ids = {record.get("id") for record in evaluation}
    train_pairs = {repair_pair(record) for record in train}
    exact = [record for record in evaluation if repair_pair(record) in train_pairs]
    result = {
        "train_records": len(train),
        "eval_records": len(evaluation),
        "id_overlap": len(train_ids & eval_ids),
        "exact_repair_pair_overlap": len(exact),
        "overlap_families": dict(Counter(record.get("repository_facts", {}).get("family", "unknown") for record in exact)),
        "clean": not (train_ids & eval_ids) and not exact,
    }
    print(json.dumps(result, indent=2))
    return 0 if result["clean"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
