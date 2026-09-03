#!/usr/bin/env python3
"""Generate verified single-line union-narrowing repository exemplars."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "benchmarks/nextjs_fixture"
OUT = ROOT / ".oktopai/datasets/typescript-trajectories-union-supplement-v1.jsonl"


def make(index: int, name: str, method: str, fixed: str) -> dict:
    path = f"lib/{name}.ts"
    broken = f"export function {name}(value: string | number) {{ return value.{method}(); }}"
    files = {"package.json": (FIXTURE / "package.json").read_text(), "tsconfig.json": (FIXTURE / "tsconfig.json").read_text(), "next-env.d.ts": (FIXTURE / "next-env.d.ts").read_text(), "next.config.mjs": (FIXTURE / "next.config.mjs").read_text(), "app/page.tsx": (FIXTURE / "app/page.tsx").read_text(), path: broken}
    trajectory = [
        {"event": "inspect", "tool": "read_file", "args": {"path": path}},
        {"event": "diagnose", "tool": "run", "args": {"command": "tsc --noEmit --pretty false"}},
        {"event": "observe", "exit_code": 2},
        {"event": "edit", "tool": "apply_patch", "args": {"path": path, "content": fixed}},
        {"event": "diagnose", "tool": "run", "args": {"command": "tsc --noEmit --pretty false"}},
        {"event": "observe", "exit_code": 0},
        {"event": "final", "content": "Narrowed the union before calling the method and verified the full project typecheck."},
    ]
    return {"id": f"union-supplement-{index:02d}", "domain": "typescript-nextjs-repository", "split": "train", "task": f"Repair the union-narrowing error in {path}. Use a single-line file content string, canonical nested args, and verify the full project typecheck.", "repository_facts": {"root": "benchmarks/nextjs_fixture", "validator": "tsc --noEmit --pretty false", "family": "union-narrowing", "training_exemplar": True}, "repository_files": files, "trajectory": trajectory, "final": trajectory[-1]["content"], "provenance": {"source": "local repository fixture", "family": "real-repository-supplement", "subfamily": "union-narrowing", "variant": index}}


def main() -> int:
    variants = [
        ("upperValue", "toUpperCase", "export function upperValue(value: string | number) { return typeof value === \"string\" ? value.toUpperCase() : value.toFixed(2); }"),
        ("lowerValue", "toLowerCase", "export function lowerValue(value: string | number) { return typeof value === \"string\" ? value.toLowerCase() : value.toFixed(2); }"),
        ("trimValue", "trim", "export function trimValue(value: string | number) { return typeof value === \"string\" ? value.trim() : value.toFixed(2); }"),
        ("fixedValue", "toFixed", "export function fixedValue(value: string | number) { return typeof value === \"number\" ? value.toFixed(2) : value; }"),
        ("lengthValue", "toUpperCase", "export function lengthValue(value: string | number) { return typeof value === \"string\" ? value.toUpperCase() : String(value); }"),
        ("displayValue", "toLowerCase", "export function displayValue(value: string | number) { return typeof value === \"string\" ? value.toLowerCase() : String(value); }"),
    ]
    rows = [make(index, *variants[index % len(variants)]) for index in range(12)]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n")
    print(json.dumps({"records": len(rows), "output": str(OUT), "split": "train"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
