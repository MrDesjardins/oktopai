#!/usr/bin/env python3
"""Create repair prompts for rejected external TypeScript candidates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--normalized", action="append", type=Path, required=True)
    parser.add_argument("--verified", action="append", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    accepted = {row["id"] for path in args.verified for row in load(path)}
    repairs: list[dict[str, Any]] = []
    for path in args.normalized:
        for row in load(path):
            if row["id"] in accepted:
                continue
            prompt = row["messages"][-1]["content"]
            repairs.append({
                "id": row["id"],
                "domain": "typescript",
                "task_family": "external-repair",
                "prompt": (
                    "Repair the candidate below into one standalone, compiler-valid TypeScript example. "
                    "Preserve the intended task when possible. Use strict TypeScript, avoid any unless required, "
                    "include all needed declarations, and return only one fenced typescript code block.\n\n"
                    f"Task: {prompt}\n\nCandidate:\n```typescript\n{row['completion']}\n```"
                ),
                "source_code": row["completion"],
                "provenance": {**row.get("provenance", {}), "repair_of": row["id"], "repair_teacher": "qwen3-coder:30b"},
            })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in repairs) + ("\n" if repairs else ""), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "repairs": len(repairs), "accepted_excluded": len(accepted)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
