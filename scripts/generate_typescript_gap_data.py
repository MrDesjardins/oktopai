#!/usr/bin/env python3
"""Generate verified gap records for mapped types and async APIs."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def make(index: int, family: str) -> dict[str, object]:
    n = f"{index + 1:06d}"
    if family == "mapped-type":
        source = f"type User{n} = {{ id: string; active: boolean }};\nfunction patch{n}(user: User{n}) {{ return {{ id: user.id }}; }}"
        answer = f"type User{n} = {{ id: string; active: boolean }};\ntype Patch{n}<T> = {{ [K in keyof T]?: T[K] }};\nfunction patch{n}(user: User{n}): Patch{n}<User{n}> {{ return {{ id: user.id }}; }}"
        instruction = "Use a mapped type to model a safe partial patch without assertions."
    else:
        source = f"async function fetch{n}(id: string) {{ return {{ id, ok: true }}; }}"
        answer = f"async function fetch{n}(id: string): Promise<{{ id: string; ok: boolean }}> {{ return {{ id, ok: true }}; }}"
        instruction = "Declare the complete Promise result contract for this async API."
    digest = hashlib.sha256(f"typescript-gap-v1:{index}:{family}".encode()).hexdigest()
    bucket = int(digest[:8], 16) % 100
    return {
        "id": f"typescript-gap-v1-{index:06d}",
        "domain": "typescript", "family": family,
        "split": "test" if bucket < 10 else "validation" if bucket < 25 else "train",
        "messages": [{"role": "system", "content": "Return only compiler-valid TypeScript in one fenced code block."}, {"role": "user", "content": f"{instruction}\n\n```typescript\n{source}\n```"}],
        "completion": f"```typescript\n{answer}\n```", "source_code": source,
        "expected": {"compiler": "strict", "must_not_contain": ["any", " as "]},
        "provenance": {"kind": "programmatic-gap-contract", "synthetic": True, "license": "CC0-like project seed"},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=1200)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    records = [make(i, "mapped-type" if i % 2 == 0 else "async-return") for i in range(args.count)]
    tsc = shutil.which("tsc") or str(ROOT / "benchmarks/nextjs_fixture/node_modules/.bin/tsc")
    with tempfile.TemporaryDirectory(prefix="oktopai-gap-") as directory:
        source = Path(directory) / "gap.ts"
        source.write_text("\n\n".join(row["completion"].split("\n", 1)[1].rsplit("\n", 1)[0] for row in records), encoding="utf-8")
        result = subprocess.run([tsc, "--noEmit", "--strict", "--target", "ES2020", str(source)], capture_output=True, text=True)
    if result.returncode:
        raise SystemExit(result.stderr)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(json.dumps(row) for row in records) + "\n", encoding="utf-8")
    print(json.dumps({"records": len(records), "output": str(args.output), "families": {"mapped-type": args.count // 2, "async-return": args.count - args.count // 2}, "verified": True}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
