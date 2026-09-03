#!/usr/bin/env python3
"""Generate a broader, evaluation-only project-level trajectory gate."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "benchmarks/nextjs_fixture"
OUT = ROOT / ".oktopai/datasets/typescript-trajectories-real-repository-eval-v3.jsonl"


def base_files(path: str, broken: str) -> dict[str, str]:
    return {
        "package.json": (FIXTURE / "package.json").read_text(),
        "tsconfig.json": (FIXTURE / "tsconfig.json").read_text(),
        "next-env.d.ts": (FIXTURE / "next-env.d.ts").read_text(),
        "next.config.mjs": (FIXTURE / "next.config.mjs").read_text(),
        "app/page.tsx": (FIXTURE / "app/page.tsx").read_text(),
        path: broken,
    }


def make(index: int, family: str, stem: str, broken: str, fixed: str, issue: str) -> dict:
    name = f"{stem}{index:02d}"
    path = f"lib/{name}.ts"
    files = base_files(path, broken.replace("NAME", name))
    fixed = fixed.replace("NAME", name)
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
        "id": f"real-repository-eval-v3-{index:03d}",
        "domain": "typescript-nextjs-repository",
        "split": "validation",
        "task": f"Repair the {family} TypeScript error in {path}: {issue} Edit only the necessary source file and verify the full Next.js project typecheck. Emit the canonical trajectory JSON contract.",
        "repository_facts": {"root": "benchmarks/nextjs_fixture", "validator": "tsc --noEmit --pretty false", "family": family, "heldout_generation": "real-repository-v3"},
        "repository_files": files,
        "trajectory": trajectory,
        "final": trajectory[-1]["content"],
        "provenance": {"source": "local repository fixture", "family": family, "variant": index},
    }


def main() -> int:
    templates = [
        ("optional-property", "optionalName", 'export function NAME(user: { name?: string }) { return user.name.toUpperCase(); }', 'export function NAME(user: { name?: string }) { return user.name?.toUpperCase() ?? ""; }', "an optional property may be undefined before calling a string method"),
        ("function-assignability", "stringHandler", 'export const NAME: (value: string) => void = (value: number) => { console.log(value); };', 'export const NAME: (value: string) => void = (value: string) => { console.log(value); };', "a callback parameter type is incompatible with the declared function type"),
        ("promise-shape", "readCount", 'export async function NAME(): Promise<number> { return { value: 1 }; }', 'export async function NAME(): Promise<number> { return 1; }', "an async function returns an object instead of the declared number"),
        ("discriminated-union", "areaShape", 'type NAMEShape = { kind: "circle"; radius: number } | { kind: "square"; side: number }; export function NAME(shape: NAMEShape) { return shape.radius * shape.radius; }', 'type NAMEShape = { kind: "circle"; radius: number } | { kind: "square"; side: number }; export function NAME(shape: NAMEShape) { return shape.kind === "circle" ? shape.radius * shape.radius : shape.side * shape.side; }', "a union member field is used without discriminating the member"),
        ("nullability", "trimMaybe", 'export function NAME(value: string | null) { return value.trim(); }', 'export function NAME(value: string | null) { return value?.trim() ?? ""; }', "a nullable value calls a string method without a null check"),
        ("tuple-index", "firstPair", 'export function NAME(pair: [string, number]) { return pair[2]; }', 'export function NAME(pair: [string, number]) { return pair[0]; }', "a tuple is indexed outside its declared bounds"),
        ("readonly-mutation", "appendItem", 'export function NAME(items: readonly string[]) { items.push("x"); return items; }', 'export function NAME(items: readonly string[]) { return [...items, "x"]; }', "a readonly array is mutated with push"),
        ("callback-parameter", "labelValues", 'const NAMEValues = [1, 2, 3]; export const NAME = NAMEValues.map((value: string) => value.toUpperCase());', 'const NAMEValues = [1, 2, 3]; export const NAME = NAMEValues.map((value: number) => value.toFixed(2));', "a callback parameter annotation conflicts with the array element type"),
        ("literal-mismatch", "currentMode", 'type NAMEMode = "on" | "off"; export const NAME: NAMEMode = "maybe";', 'type NAMEMode = "on" | "off"; export const NAME: NAMEMode = "on";', "a string literal is not assignable to the declared literal union"),
        ("record-key", "readRecord", 'export function NAME(record: Record<string, number>, key: string) { return record[key].toUpperCase(); }', 'export function NAME(record: Record<string, number>, key: string) { return record[key].toFixed(2); }', "a record access must preserve the declared numeric value type"),
    ]
    rows = [make(index, *templates[index % len(templates)]) for index in range(80)]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n")
    print(json.dumps({"output": str(OUT), "records": len(rows), "families": len(templates), "split": "validation"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
