#!/usr/bin/env python3
"""Make a smaller, deterministic trajectory corpus for JSON emission."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def compact(record: dict, single_line: bool = False) -> dict:
    events = []
    for event in record["trajectory"]:
        kind = event.get("event")
        if kind in {"inspect", "diagnose", "edit"}:
            args = dict(event["args"])
            if single_line and kind == "edit":
                args["content"] = " ".join(args["content"].splitlines())
            item = {"event": kind, "tool": event["tool"], "args": args}
            if kind == "inspect" and "result" in event:
                item["result"] = event["result"]
            events.append(item)
        elif kind == "observe":
            events.append({"event": "observe", "exit_code": event["exit_code"]})
        elif kind == "retry":
            events.append({"event": "retry"})
        elif kind == "final":
            events.append({"event": "final", "content": event["content"]})
    output = dict(record)
    output["trajectory"] = events
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--single-line", action="store_true")
    args = parser.parse_args()
    rows = [compact(json.loads(line), args.single_line) for line in args.input.read_text().splitlines() if line.strip()]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in rows) + "\n")
    print(json.dumps({"records": len(rows), "output": str(args.output), "compact": True, "single_line": args.single_line}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
