#!/usr/bin/env python3
"""Generate a balanced, strict-compiler-verified TypeScript v2 corpus."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = (
    "async-return", "module-api", "record-dictionary", "null-narrowing",
    "type-predicate", "readonly-generic", "generic-indexed-access",
    "discriminated-union",
)


def make(index: int, family: str) -> dict[str, object]:
    n = f"{index + 1:06d}"
    if family == "async-return":
        source = f"async function load{n}(id: string) {{ return id.length; }}"
        answer = f"async function load{n}(id: string): Promise<number> {{ return id.length; }}"
        instruction = "Declare the precise Promise return type for this async API."
    elif family == "module-api":
        source = f"type Config{n} = {{ endpoint: string; retries?: number }};\nfunction request{n}(config: Config{n}) {{ return config.endpoint; }}"
        answer = f"export type Config{n} = {{ endpoint: string; retries?: number }};\nexport function request{n}(config: Config{n}): string {{ return config.endpoint; }}"
        instruction = "Make this public module API explicit, safe, and exportable."
    elif family == "record-dictionary":
        source = f"function total{n}(values: {{ [key: string]: number }}, key: string) {{ return values[key]; }}"
        answer = f"function total{n}(values: Record<string, number>, key: string): number {{ return values[key] ?? 0; }}"
        instruction = "Repair the string dictionary contract without any or unsafe assertions."
    elif family == "null-narrowing":
        source = f"function title{n}(value: string | null) {{ return value.toUpperCase(); }}"
        answer = f"function title{n}(value: string | null): string {{ return value === null ? '' : value.toUpperCase(); }}"
        instruction = "Narrow the nullable input safely and declare the return type."
    elif family == "type-predicate":
        source = f"function isNumber{n}(value: unknown) {{ return typeof value === 'number'; }}"
        answer = f"function isNumber{n}(value: unknown): value is number {{ return typeof value === 'number'; }}"
        instruction = "Add a type predicate so callers can safely narrow unknown."
    elif family == "readonly-generic":
        source = f"function last{n}<T>(items: T[]) {{ return items[items.length - 1]; }}"
        answer = f"function last{n}<T>(items: readonly T[]): T | undefined {{ return items[items.length - 1]; }}"
        instruction = "Accept readonly generic input and declare the optional result."
    elif family == "generic-indexed-access":
        source = f"function pick{n}<T>(object: T, key: string) {{ return object[key]; }}"
        answer = f"function pick{n}<T, K extends keyof T>(object: T, key: K): T[K] {{ return object[key]; }}"
        instruction = "Repair the generic indexed access using a key constraint."
    else:
        source = f"type Outcome{n} = {{ kind: 'ok'; value: string }} | {{ kind: 'error'; message: string }};\nfunction text{n}(outcome: Outcome{n}) {{ return outcome.value; }}"
        answer = f"type Outcome{n} = {{ kind: 'ok'; value: string }} | {{ kind: 'error'; message: string }};\nfunction text{n}(outcome: Outcome{n}): string {{ return outcome.kind === 'ok' ? outcome.value : outcome.message; }}"
        instruction = "Use the discriminant to safely handle every union member."
    digest = hashlib.sha256(f"typescript-targeted-v2:{index}:{family}".encode()).hexdigest()
    bucket = int(digest[:8], 16) % 100
    split = "test" if bucket < 10 else "validation" if bucket < 25 else "train"
    return {
        "id": f"typescript-targeted-v2-{index:06d}",
        "domain": "typescript",
        "family": family,
        "split": split,
        "messages": [
            {"role": "system", "content": "Return only compiler-valid TypeScript in one fenced code block."},
            {"role": "user", "content": f"{instruction}\n\n```typescript\n{source}\n```"},
        ],
        "completion": f"```typescript\n{answer}\n```",
        "source_code": source,
        "expected": {"compiler": "strict", "must_not_contain": ["any", " as "]},
        "provenance": {"kind": "programmatic-targeted-contract-v2", "synthetic": True, "license": "CC0-like project seed"},
    }


def verify(records: list[dict[str, object]]) -> tuple[bool, str]:
    tsc = shutil.which("tsc")
    fixture_tsc = ROOT / "benchmarks/nextjs_fixture/node_modules/.bin/tsc"
    tsc = tsc or (str(fixture_tsc) if fixture_tsc.exists() else None)
    if not tsc:
        return False, "tsc unavailable"
    with tempfile.TemporaryDirectory(prefix="oktopai-targeted-v2-") as directory:
        path = Path(directory) / "corpus.ts"
        code = "\n\n".join(row["completion"].split("\n", 1)[1].rsplit("\n", 1)[0] for row in records)
        path.write_text(code, encoding="utf-8")
        result = subprocess.run([tsc, "--noEmit", "--strict", "--target", "ES2020", str(path)], capture_output=True, text=True)
    return result.returncode == 0, result.stderr[-2000:]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=4800)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    records = [make(index, FAMILIES[index % len(FAMILIES)]) for index in range(args.count)]
    verified, stderr = verify(records) if args.verify else (None, "not requested")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in records) + "\n", encoding="utf-8")
    print(json.dumps({"records": len(records), "output": str(args.output), "families": FAMILIES, "verification": {"verified": verified, "stderr": stderr}, "splits": {name: sum(row["split"] == name for row in records) for name in ("train", "validation", "test")}}, indent=2))
    return 0 if verified is not False else 2


if __name__ == "__main__":
    raise SystemExit(main())
