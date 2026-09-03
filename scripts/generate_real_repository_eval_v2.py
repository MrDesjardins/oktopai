#!/usr/bin/env python3
"""Generate a disjoint project-level trajectory evaluation suite."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "benchmarks/nextjs_fixture"
OUT = ROOT / ".oktopai/datasets/typescript-trajectories-real-repository-eval-v2.jsonl"


def base_files(path: str, broken: str) -> dict[str, str]:
    return {
        "package.json": (FIXTURE / "package.json").read_text(),
        "tsconfig.json": (FIXTURE / "tsconfig.json").read_text(),
        "next-env.d.ts": (FIXTURE / "next-env.d.ts").read_text(),
        "next.config.mjs": (FIXTURE / "next.config.mjs").read_text(),
        "app/page.tsx": (FIXTURE / "app/page.tsx").read_text(),
        path: broken,
    }


def make(index: int, family: str, name: str, broken: str, fixed: str, issue: str, path: str) -> dict:
    files = base_files(path, broken)
    trajectory = [
        {"event": "inspect", "tool": "read_file", "args": {"path": path}},
        {"event": "diagnose", "tool": "run", "args": {"command": "tsc --noEmit --pretty false"}},
        {"event": "observe", "exit_code": 2},
        {"event": "edit", "tool": "apply_patch", "args": {"path": path, "content": fixed}},
        {"event": "diagnose", "tool": "run", "args": {"command": "tsc --noEmit --pretty false"}},
        {"event": "observe", "exit_code": 0},
        {"event": "final", "content": "Applied the minimal repair and verified the full project typecheck."},
    ]
    return {
        "id": f"real-repository-eval-v2-{index:03d}",
        "domain": "typescript-nextjs-repository",
        "split": "validation",
        "task": f"Repair the {family} TypeScript error in {path}: {issue} Edit only the necessary source file and verify the full Next.js project typecheck. Emit the canonical trajectory JSON contract.",
        "repository_facts": {"root": "benchmarks/nextjs_fixture", "validator": "tsc --noEmit --pretty false", "family": family, "heldout_generation": "real-repository-v2"},
        "repository_files": files,
        "trajectory": trajectory,
        "final": trajectory[-1]["content"],
        "provenance": {"source": "local repository fixture", "family": family, "variant": index},
    }


def main() -> int:
    templates = [
        ("generic-lookup", "getValue", "export function getValue<T>(obj: T, key: string) { return obj[key]; }", "export function getValue<T, K extends keyof T>(obj: T, key: K): T[K] { return obj[key]; }", "a string key indexes an unconstrained generic object", "lib/lookup.ts"),
        ("async-return", "loadValue", "export async function loadValue(): Promise<string> { return 42; }", "export async function loadValue(): Promise<string> { return \"42\"; }", "the async function returns a number instead of its declared string", "lib/asyncValue.ts"),
        ("union-narrowing", "formatValue", "export function formatValue(value: string | number) { return value.toUpperCase(); }", "export function formatValue(value: string | number) { return typeof value === \"string\" ? value.toUpperCase() : value.toFixed(2); }", "a union value calls a string-only method without narrowing", "lib/formatValue.ts"),
        ("array-narrowing", "joinValues", "export function joinValues(value: string | string[]) { return value.join(\",\"); }", "export function joinValues(value: string | string[]) { return Array.isArray(value) ? value.join(\",\") : value; }", "a union value calls array join without proving it is an array", "lib/joinValues.ts"),
        ("object-record-mismatch", "readConfig", "export const readConfig: { port: number } = { port: \"3000\" };", "export const readConfig: { port: number } = { port: 3000 };", "an object literal provides a string where the project requires a number", "lib/config.ts"),
    ]
    rows = [make(index, *templates[index % len(templates)]) for index in range(40)]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n")
    print(json.dumps({"output": str(OUT), "records": len(rows), "families": len(templates), "split": "validation"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
