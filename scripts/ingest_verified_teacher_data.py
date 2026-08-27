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
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tsc", default=None)
    parser.add_argument("--timeout", type=int, default=30, help="Maximum compiler seconds per record")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    tsc = args.tsc or shutil.which("tsc")
    if not tsc:
        raise SystemExit("TypeScript compiler not found; install/use the project fixture compiler")
    accepted: list[dict] = []
    rejected = 0
    items = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines() if line.strip()]

    def verify(item: dict) -> dict | None:
        task = item.get("task", item)
        completion = item.get("completion", "")
        blocks = re.findall(r"```(?:typescript|tsx|ts)?\s*\n(.*?)```", completion, re.IGNORECASE | re.DOTALL)
        code = "\n\n".join(blocks) if blocks else completion.strip()
        if not code:
            return None
        with tempfile.TemporaryDirectory(prefix="oktopai-teacher-verify-") as directory:
            path = Path(directory) / "candidate.ts"
            path.write_text(code, encoding="utf-8")
            try:
                result = subprocess.run([tsc, "--noEmit", "--strict", "--target", "ES2020", str(path)], capture_output=True, text=True, timeout=args.timeout)
            except subprocess.TimeoutExpired:
                return None
        if result.returncode != 0:
            return None
        return {
            "id": task["id"],
            "domain": "typescript",
            "family": task.get("task_family", task.get("family", "unknown")),
            "split": "train",
            "messages": [
                {"role": "system", "content": "You are a precise TypeScript specialist. Return compiler-valid code."},
                {
                    "role": "user",
                    "content": task.get(
                        "prompt",
                        next(
                            (
                                message.get("content", "")
                                for message in task.get("messages", [])
                                if message.get("role") == "user"
                            ),
                            "",
                        ),
                    ),
                },
            ],
            "completion": code,
            "source_code": task.get("source_code", ""),
            "provenance": {**task.get("provenance", {}), "teacher": item.get("teacher"), "verification_status": "tsc-strict"},
        }
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        for record in pool.map(verify, items):
            if record is None:
                rejected += 1
            else:
                accepted.append(record)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in accepted) + ("\n" if accepted else ""), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "accepted": len(accepted), "rejected": rejected}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
