#!/usr/bin/env python3
"""Analyze teacher output shape and verified acceptance by task family."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--accepted", type=Path)
    args = parser.parse_args()
    accepted = set()
    if args.accepted and args.accepted.exists():
        accepted = {json.loads(line)["id"] for line in args.accepted.read_text().splitlines() if line.strip()}
    shape = Counter()
    family = defaultdict(Counter)
    records = [json.loads(line) for line in args.input.read_text().splitlines() if line.strip()]
    for item in records:
        task = item.get("task", item)
        completion = item.get("completion", "")
        blocks = re.findall(r"```(?:typescript|tsx|ts)?\s*\n(.*?)```", completion, re.I | re.S)
        if not completion.strip():
            label = "empty"
        elif blocks:
            label = "fenced_code"
        elif task.get("task_family") in {"explain", "review"}:
            label = "prose_or_no_code"
        else:
            label = "unfenced_code_or_prose"
        shape[label] += 1
        family[task.get("task_family", "unknown")]["total"] += 1
        family[task.get("task_family", "unknown")]["accepted"] += int(task.get("id") in accepted)
    print(json.dumps({"records": len(records), "shape": shape, "families": family}, default=dict, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
