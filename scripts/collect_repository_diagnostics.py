#!/usr/bin/env python3
"""Collect real compiler diagnostics for evaluation-only repository snapshots."""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path


def collect(record: dict, node_modules: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix="oktopai-diagnostic-") as directory:
        project = Path(directory)
        for path, content in record.get("repository_files", {}).items():
            target = project / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        (project / "node_modules").symlink_to(node_modules, target_is_directory=True)
        result = subprocess.run(
            [str(node_modules / ".bin/tsc"), "--noEmit", "--incremental", "false", "--pretty", "false"],
            cwd=project, capture_output=True, text=True, check=False,
        )
    if result.returncode == 0:
        raise ValueError(f"{record.get('id')}: broken snapshot unexpectedly typechecks")
    updated = dict(record)
    updated["compiler_diagnostic"] = (result.stdout + result.stderr).strip()
    return updated


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--node-modules", type=Path, default=Path("/home/miste/code/desktop-ai-companion/apps/desktop/node_modules"))
    args = parser.parse_args()
    rows = [collect(json.loads(line), args.node_modules) for line in args.input.read_text(encoding="utf-8").splitlines() if line.strip()]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")
    print(json.dumps({"input": str(args.input), "output": str(args.output), "records": len(rows), "diagnostics": len(rows)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
