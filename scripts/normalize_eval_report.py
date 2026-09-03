#!/usr/bin/env python3
"""Rewrite an evaluation report's base/adapter paths to absolute local paths."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--base-model", type=Path, required=True)
    parser.add_argument("--adapter", type=Path, required=True)
    args = parser.parse_args()
    report = json.loads(args.input.read_text(encoding="utf-8"))
    report["base_model"] = str(args.base_model.resolve())
    report["adapter"] = str(args.adapter.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "records": len(report.get("records", [])), "base_model": report["base_model"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
