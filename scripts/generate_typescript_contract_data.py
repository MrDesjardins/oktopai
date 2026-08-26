#!/usr/bin/env python3
"""Generate deterministic, compiler-checked TypeScript repair/test examples."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "typescript-contract-v1"


def make(index: int, family_index: int) -> dict:
    n = index + 1
    suffix = f"{n:06d}"
    templates = [
        ("generic", f"function get{suffix}<T>(obj: T, key: string) {{ return obj[key]; }}", f"function get{suffix}<T, K extends keyof T>(obj: T, key: K): T[K] {{ return obj[key]; }}", "Repair the generic indexed access without any or assertions."),
        ("narrowing", f"function size{suffix}(value: string | string[] | null) {{ return value.length; }}", f"function size{suffix}(value: string | string[] | null): number {{ if (value === null) return 0; return value.length; }}", "Narrow the nullable union safely and declare the return type."),
        ("union", f"type Result{suffix} = {{ kind: 'ok'; value: string }} | {{ kind: 'error'; message: string }};\nfunction format{suffix}(result: Result{suffix}) {{ return result.value; }}", f"type Result{suffix} = {{ kind: 'ok'; value: string }} | {{ kind: 'error'; message: string }};\nfunction format{suffix}(result: Result{suffix}): string {{ return result.kind === 'ok' ? result.value : result.message; }}", "Use the discriminant to access the correct union property."),
        ("readonly", f"function first{suffix}<T>(items: T[]) {{ return items[0]; }}", f"function first{suffix}<T>(items: readonly T[]): T | undefined {{ return items[0]; }}", "Accept a readonly generic array and return an optional first item."),
        ("predicate", f"function isText{suffix}(value: unknown) {{ return typeof value === 'string'; }}", f"function isText{suffix}(value: unknown): value is string {{ return typeof value === 'string'; }}", "Add a type predicate so the guard narrows unknown to string."),
        ("async", f"async function load{suffix}() {{ return 'ready'; }}", f"async function load{suffix}(): Promise<string> {{ return 'ready'; }}", "Declare the precise Promise return type."),
        ("api-contract", f"type User{suffix} = {{ id: string; name?: string }};\nfunction label{suffix}(user: User{suffix}) {{ return user.name.toUpperCase(); }}", f"type User{suffix} = {{ id: string; name?: string }};\nfunction label{suffix}(user: User{suffix}): string {{ return user.name ?? user.id; }}", "Make the optional API field safe without an assertion."),
        ("test", f"function add{suffix}(a: number, b: number) {{ return a + b; }}", f"function add{suffix}(a: number, b: number): number {{ return a + b; }}\nfunction assert{suffix}(actual: number, expected: number): void {{ if (actual !== expected) throw new Error('assertion failed'); }}\nassert{suffix}(add{suffix}(2, 3), 5);", "Add a focused, compiler-valid type-level/runtime test for this function."),
    ]
    family, source, completion, instruction = templates[family_index % len(templates)]
    key = f"{VERSION}:{index}:{family}:{source}"
    digest = hashlib.sha256(key.encode()).hexdigest()
    bucket = int(digest[:8], 16) % 100
    split = "test" if bucket < 10 else ("validation" if bucket < 25 else "train")
    return {
        "id": f"{VERSION}-{index:06d}",
        "domain": "typescript",
        "family": family,
        "split": split,
        "messages": [
            {"role": "system", "content": "Return only compiler-valid TypeScript in one fenced code block."},
            {"role": "user", "content": f"{instruction}\n\n```typescript\n{source}\n```"},
        ],
        "completion": f"```typescript\n{completion}\n```",
        "source_code": source,
        "expected": {"compiler": "strict", "must_not_contain": ["any", " as "]},
        "provenance": {"kind": "programmatic-contract-template", "generator": VERSION, "synthetic": True, "license": "CC0-like project seed"},
    }


def verify(records: list[dict]) -> dict:
    tsc = shutil.which("tsc")
    fixture = ROOT / "benchmarks/nextjs_fixture/node_modules/.bin/tsc"
    tsc = tsc or (str(fixture) if fixture.exists() else None)
    if not tsc:
        return {"available": False, "verified": None}
    with tempfile.TemporaryDirectory(prefix="oktopai-contract-") as directory:
        path = Path(directory) / "contracts.ts"
        code = "\n\n".join(item["completion"].split("\n", 1)[1].rsplit("\n", 1)[0] for item in records)
        path.write_text(code, encoding="utf-8")
        result = subprocess.run([tsc, "--noEmit", "--strict", "--target", "ES2020", str(path)], capture_output=True, text=True)
    return {"available": True, "verified": result.returncode == 0, "stderr": result.stderr[-2000:]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=5000)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.count < 1:
        raise SystemExit("--count must be positive")
    records = [make(index, index % 8) for index in range(args.count)]
    verification = verify(records) if args.verify else {"available": None, "verified": None}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in records) + "\n", encoding="utf-8")
    print(json.dumps({"version": VERSION, "records": len(records), "output": str(args.output), "verification": verification, "splits": {split: sum(row["split"] == split for row in records) for split in ("train", "validation", "test")}}, indent=2))
    return 0 if verification.get("verified", True) else 2


if __name__ == "__main__":
    raise SystemExit(main())
