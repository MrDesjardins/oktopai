#!/usr/bin/env python3
"""Replay trajectory records with a project-level TypeScript verification."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from oktopai.trajectory import apply_replacements, validate_trajectory

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "benchmarks/nextjs_fixture"


def replay(record: dict[str, Any], tsc: str) -> list[str]:
    errors = [f"{i.code}: {i.message}" for i in validate_trajectory(record)]
    if errors:
        return errors
    with tempfile.TemporaryDirectory(prefix="oktopai-real-repository-") as directory:
        project = Path(directory)
        for path, content in record.get("repository_files", {}).items():
            target = project / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        (project / "node_modules").symlink_to(FIXTURE / "node_modules", target_is_directory=True)
        observed: list[int] = []
        for event in record["trajectory"]:
            if event.get("event") == "edit":
                target = project / event["args"]["path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                args = event["args"]
                content = args.get("content")
                if content is None:
                    content = apply_replacements(target.read_text(encoding="utf-8"), args["replacements"])
                target.write_text(content, encoding="utf-8")
            if event.get("event") == "diagnose":
                result = subprocess.run([tsc, "--noEmit", "--pretty", "false"], cwd=project, capture_output=True, text=True)
                observed.append(result.returncode)
        claimed = [event["exit_code"] for event in record["trajectory"] if event.get("event") == "observe"]
        if claimed != observed:
            errors.append(f"observation_mismatch: claimed={claimed}, observed={observed}")
        if not observed or observed[-1] != 0:
            errors.append("final_project_typecheck_failed")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--tsc", default=str(FIXTURE / "node_modules/.bin/tsc"))
    args = parser.parse_args()
    failures = []
    total = 0
    for line in args.input.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        total += 1
        row = json.loads(line)
        issues = replay(row, args.tsc)
        if issues:
            failures.append({"id": row.get("id"), "errors": issues})
    result = {"input": str(args.input), "records": total, "passed": total - len(failures), "failed": len(failures), "failures": failures, "verified": total > 0 and not failures, "validator": "full project tsc --noEmit"}
    print(json.dumps(result, indent=2))
    return 0 if result["verified"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
