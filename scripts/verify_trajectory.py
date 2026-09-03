#!/usr/bin/env python3
"""Validate and independently replay a JSONL TypeScript trajectory corpus."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from oktopai.trajectory import apply_replacements, validate_trajectory

ROOT = Path(__file__).resolve().parents[1]
DESKTOP_TSC = Path("/home/miste/code/desktop-ai-companion/apps/desktop/node_modules/.bin/tsc")
FIXTURE_TSC = ROOT / "benchmarks/nextjs_fixture/node_modules/.bin/tsc"


def replay(record: dict[str, Any], tsc: str) -> list[str]:
    errors = [f"{i.code}: {i.message}" for i in validate_trajectory(record)]
    if errors:
        return errors
    edit_paths = [
        event.get("args", {}).get("path")
        for event in record.get("trajectory", [])
        if event.get("event") == "edit" and isinstance(event.get("args"), dict)
    ]
    target_path = next((path for path in reversed(edit_paths) if isinstance(path, str)), "src/index.ts")
    with tempfile.TemporaryDirectory(prefix="oktopai-trajectory-") as directory:
        root = Path(directory)
        for path, content in record.get("repository_files", {}).items():
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        observed: list[int] = []
        for event in record["trajectory"]:
            if event.get("event") == "edit":
                target = root / event["args"]["path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                args = event["args"]
                content = args.get("content")
                if content is None:
                    content = apply_replacements(target.read_text(encoding="utf-8"), args["replacements"])
                target.write_text(content, encoding="utf-8")
            if event.get("event") == "diagnose":
                # Synthetic trajectory fixtures are standalone files. Exclude
                # the default DOM library so fixture globals such as
                # devicePixelRatio do not collide with lib.dom declarations.
                result = subprocess.run([tsc, "--noEmit", "--strict", "--lib", "es2020", str(root / target_path)], capture_output=True, text=True)
                observed.append(result.returncode)
        claimed = [event["exit_code"] for event in record["trajectory"] if event.get("event") == "observe"]
        if claimed != observed:
            errors.append(f"observation_mismatch: claimed={claimed}, observed={observed}")
        if observed and observed[-1] != 0:
            errors.append("final_compilation_failed")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--tsc", default=shutil.which("tsc") or str(
        DESKTOP_TSC if DESKTOP_TSC.exists() else FIXTURE_TSC
    ))
    parser.add_argument("--limit", type=int, default=None, help="verify only the first N non-empty records")
    parser.add_argument("--jobs", type=int, default=1, help="run independent record replays concurrently")
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error("--jobs must be positive")
    failures: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    for line in args.input.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        if args.limit is not None and len(records) >= args.limit:
            break
        records.append(json.loads(line))
    total = len(records)
    with ThreadPoolExecutor(max_workers=args.jobs) as executor:
        checked = list(executor.map(lambda record: (record, replay(record, args.tsc)), records))
    passed = 0
    for record, errors in checked:
        if errors:
            failures.append({"id": record.get("id"), "errors": errors})
        else:
            passed += 1
    result = {"input": str(args.input), "records": total, "passed": passed, "failed": len(failures), "failures": failures, "verified": total > 0 and not failures}
    print(json.dumps(result, indent=2))
    return 0 if result["verified"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
