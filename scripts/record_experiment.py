#!/usr/bin/env python3
"""Append a structured experiment event to the project ledger."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--status", choices=("started", "completed", "stopped", "failed"), required=True)
    parser.add_argument("--metadata", default="{}", help="JSON object with measurements and provenance")
    parser.add_argument("--output", type=Path, default=Path("experiments/runs.jsonl"))
    args = parser.parse_args()
    metadata: dict[str, Any] = json.loads(args.metadata)
    if not isinstance(metadata, dict):
        raise SystemExit("--metadata must be a JSON object")
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "kind": args.kind,
        "name": args.name,
        "status": args.status,
        "metadata": metadata,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
    print(json.dumps(event, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
