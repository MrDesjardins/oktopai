#!/usr/bin/env python3
"""Turn teacher answers into student records only after local verification.

Input records must contain ``task`` fields from the use-case corpus and a
teacher ``completion``. Code blocks are extracted, compiled with strict
TypeScript, and saved with verification evidence. No answer is trusted merely
because a teacher produced it.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tsc", default=None)
    args = parser.parse_args()
    tsc = args.tsc or shutil.which("tsc")
    if not tsc:
        raise SystemExit("TypeScript compiler not found; install/use the project fixture compiler")
    accepted: list[dict] = []
    rejected = 0
    for line in args.input.read_text(encoding="utf-8").splitlines():
        item = json.loads(line)
        task = item.get("task", item)
        completion = item.get("completion", "")
        blocks = re.findall(r"```(?:typescript|tsx|ts)?\s*\n(.*?)```", completion, re.IGNORECASE | re.DOTALL)
        code = "\n\n".join(blocks) if blocks else completion.strip()
        if not code:
            rejected += 1
            continue
        with tempfile.TemporaryDirectory(prefix="oktopai-teacher-verify-") as directory:
            path = Path(directory) / "candidate.ts"
            path.write_text(code, encoding="utf-8")
            result = subprocess.run([tsc, "--noEmit", "--strict", "--target", "ES2020", str(path)], capture_output=True, text=True)
        if result.returncode != 0:
            rejected += 1
            continue
        record = {
            "id": task["id"],
            "domain": "typescript",
            "family": task.get("task_family", "unknown"),
            "split": "train",
            "messages": [
                {"role": "system", "content": "You are a precise TypeScript specialist. Return compiler-valid code."},
                {"role": "user", "content": task["prompt"]},
            ],
            "completion": code,
            "source_code": task.get("source_code", ""),
            "provenance": {**task.get("provenance", {}), "teacher": item.get("teacher"), "verification_status": "tsc-strict"},
        }
        accepted.append(record)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in accepted) + ("\n" if accepted else ""), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "accepted": len(accepted), "rejected": rejected}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
