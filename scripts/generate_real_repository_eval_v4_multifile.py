#!/usr/bin/env python3
"""Generate evaluation-only multi-file repository trajectory tasks."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "benchmarks/nextjs_fixture"
OUT = ROOT / ".oktopai/datasets/typescript-trajectories-real-repository-eval-v4-multifile.jsonl"


def make(index: int, family: str, stem: str, helper: str, broken: str, fixed: str, issue: str) -> dict:
    name = f"{stem}{index:02d}"
    helper_path = f"lib/{name}Types.ts"
    target_path = f"lib/{name}.ts"
    files = {
        "package.json": (FIXTURE / "package.json").read_text(),
        "tsconfig.json": (FIXTURE / "tsconfig.json").read_text(),
        "next-env.d.ts": (FIXTURE / "next-env.d.ts").read_text(),
        "next.config.mjs": (FIXTURE / "next.config.mjs").read_text(),
        "app/page.tsx": (FIXTURE / "app/page.tsx").read_text(),
        helper_path: helper.replace("NAME", name),
        f"lib/{name}Constants.ts": f'export const {name.upper()}_VERSION = "1";',
        target_path: broken.replace("NAME", name),
    }
    fixed = fixed.replace("NAME", name)
    trajectory = [
        {"event": "inspect", "tool": "read_file", "args": {"path": target_path}},
        {"event": "diagnose", "tool": "run", "args": {"command": "tsc --noEmit --pretty false"}},
        {"event": "observe", "exit_code": 2},
        {"event": "edit", "tool": "apply_patch", "args": {"path": target_path, "content": fixed}},
        {"event": "diagnose", "tool": "run", "args": {"command": "tsc --noEmit --pretty false"}},
        {"event": "observe", "exit_code": 0},
        {"event": "final", "content": "Repaired the imported-type usage and verified the full multi-file project typecheck."},
    ]
    return {
        "id": f"real-repository-eval-v4-multifile-{index:03d}",
        "domain": "typescript-nextjs-repository",
        "split": "validation",
        "task": f"Repair the {family} TypeScript error in {target_path}: {issue} Inspect the imported context, edit only the target source file, and verify the full Next.js project typecheck. Emit the canonical trajectory JSON contract.",
        "repository_facts": {"root": "benchmarks/nextjs_fixture", "validator": "tsc --noEmit --pretty false", "family": family, "heldout_generation": "real-repository-v4-multifile", "files_in_scope": 3},
        "repository_files": files,
        "trajectory": trajectory,
        "final": trajectory[-1]["content"],
        "provenance": {"source": "local repository fixture", "family": family, "variant": index},
    }


def main() -> int:
    templates = [
        ("cross-file-property", "profileProperty", 'export type NAMEProfile = { label: string; count: number };', 'import { NAMEProfile } from "./NAMETypes"; export function NAME(profile: NAMEProfile) { return profile.missing; }', 'import { NAMEProfile } from "./NAMETypes"; export function NAME(profile: NAMEProfile) { return profile.label; }', "the target accesses a property absent from the imported profile type"),
        ("cross-file-union", "shapeArea", 'export type NAMEShape = { kind: "circle"; radius: number } | { kind: "square"; side: number };', 'import { NAMEShape } from "./NAMETypes"; export function NAME(shape: NAMEShape) { return shape.radius * shape.radius; }', 'import { NAMEShape } from "./NAMETypes"; export function NAME(shape: NAMEShape) { return shape.kind === "circle" ? shape.radius * shape.radius : shape.side * shape.side; }', "the imported discriminated union is used without narrowing"),
        ("cross-file-optional", "profileLabel", 'export type NAMEProfile = { label?: string };', 'import { NAMEProfile } from "./NAMETypes"; export function NAME(profile: NAMEProfile) { return profile.label.toUpperCase(); }', 'import { NAMEProfile } from "./NAMETypes"; export function NAME(profile: NAMEProfile) { return profile.label?.toUpperCase() ?? ""; }', "the imported optional property may be undefined"),
        ("cross-file-callback", "itemLabels", 'export type NAMEItem = { id: number; label: string };', 'import { NAMEItem } from "./NAMETypes"; export function NAME(items: NAMEItem[]) { return items.map((item: string) => item.toUpperCase()); }', 'import { NAMEItem } from "./NAMETypes"; export function NAME(items: NAMEItem[]) { return items.map((item: NAMEItem) => item.label.toUpperCase()); }', "the callback annotation conflicts with the imported array element type"),
        ("cross-file-generic", "recordValue", 'export type NAMERecord = { count: number; label: string };', 'import { NAMERecord } from "./NAMETypes"; export function NAME(value: NAMERecord, key: string) { return value[key]; }', 'import { NAMERecord } from "./NAMETypes"; export function NAME(value: NAMERecord, key: string) { return value[key as keyof NAMERecord]; }', "a string key indexes the imported record type without a key constraint"),
        ("cross-file-nullability", "profileValue", 'export type NAMEProfile = { value: string | null };', 'import { NAMEProfile } from "./NAMETypes"; export function NAME(profile: NAMEProfile) { return profile.value.trim(); }', 'import { NAMEProfile } from "./NAMETypes"; export function NAME(profile: NAMEProfile) { return profile.value?.trim() ?? ""; }', "the imported nullable value is used without a null check"),
    ]
    rows = [make(index, *templates[index % len(templates)]) for index in range(60)]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n")
    print(json.dumps({"output": str(OUT), "records": len(rows), "families": len(templates), "files_per_task": 8, "split": "validation"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
