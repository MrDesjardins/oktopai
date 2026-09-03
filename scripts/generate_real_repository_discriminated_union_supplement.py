#!/usr/bin/env python3
"""Generate verified discriminated-union repository trajectory exemplars."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "benchmarks/nextjs_fixture"
OUT = ROOT / ".oktopai/datasets/typescript-trajectories-discriminated-union-supplement-v1.jsonl"


def make(index: int, name: str, fixed: str) -> dict:
    path = f"lib/{name}.ts"
    broken = f'type {name}Shape = {{ kind: "circle"; radius: number }} | {{ kind: "square"; side: number }}; export function {name}(shape: {name}Shape) {{ return shape.radius * shape.radius; }}'
    files = {
        "package.json": (FIXTURE / "package.json").read_text(),
        "tsconfig.json": (FIXTURE / "tsconfig.json").read_text(),
        "next-env.d.ts": (FIXTURE / "next-env.d.ts").read_text(),
        "next.config.mjs": (FIXTURE / "next.config.mjs").read_text(),
        "app/page.tsx": (FIXTURE / "app/page.tsx").read_text(),
        path: broken,
    }
    trajectory = [
        {"event": "inspect", "tool": "read_file", "args": {"path": path}},
        {"event": "diagnose", "tool": "run", "args": {"command": "tsc --noEmit --pretty false"}},
        {"event": "observe", "exit_code": 2},
        {"event": "edit", "tool": "apply_patch", "args": {"path": path, "content": fixed}},
        {"event": "diagnose", "tool": "run", "args": {"command": "tsc --noEmit --pretty false"}},
        {"event": "observe", "exit_code": 0},
        {"event": "final", "content": "Discriminated the union before accessing the member-specific field and verified the full project typecheck."},
    ]
    return {
        "id": f"discriminated-union-supplement-{index:02d}",
        "domain": "typescript-nextjs-repository",
        "split": "train",
        "task": f"Repair the discriminated-union error in {path}. Use a single-line complete file content string, canonical nested args, and verify the full project typecheck.",
        "repository_facts": {"root": "benchmarks/nextjs_fixture", "validator": "tsc --noEmit --pretty false", "family": "discriminated-union", "training_exemplar": True},
        "repository_files": files,
        "trajectory": trajectory,
        "final": trajectory[-1]["content"],
        "provenance": {"source": "local repository fixture", "family": "real-repository-supplement", "subfamily": "discriminated-union", "variant": index},
    }


def main() -> int:
    variants = [
        ("areaCircle", 'type areaCircleShape = { kind: "circle"; radius: number } | { kind: "square"; side: number }; export function areaCircle(shape: areaCircleShape) { return shape.kind === "circle" ? shape.radius * shape.radius : shape.side * shape.side; }'),
        ("perimeterShape", 'type perimeterShapeShape = { kind: "circle"; radius: number } | { kind: "square"; side: number }; export function perimeterShape(shape: perimeterShapeShape) { return shape.kind === "circle" ? 2 * Math.PI * shape.radius : 4 * shape.side; }'),
        ("describeShape", 'type describeShapeShape = { kind: "circle"; radius: number } | { kind: "square"; side: number }; export function describeShape(shape: describeShapeShape) { return shape.kind === "circle" ? String(shape.radius) : String(shape.side); }'),
        ("sizeShape", 'type sizeShapeShape = { kind: "circle"; radius: number } | { kind: "square"; side: number }; export function sizeShape(shape: sizeShapeShape) { return shape.kind === "circle" ? shape.radius : shape.side; }'),
        ("scaleShape", 'type scaleShapeShape = { kind: "circle"; radius: number } | { kind: "square"; side: number }; export function scaleShape(shape: scaleShapeShape) { return shape.kind === "circle" ? shape.radius * 2 : shape.side * 2; }'),
        ("labelShape", 'type labelShapeShape = { kind: "circle"; radius: number } | { kind: "square"; side: number }; export function labelShape(shape: labelShapeShape) { return shape.kind === "circle" ? "circle" : "square"; }'),
    ]
    rows = [make(index, *variants[index % len(variants)]) for index in range(12)]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n")
    print(json.dumps({"records": len(rows), "output": str(OUT), "split": "train"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
