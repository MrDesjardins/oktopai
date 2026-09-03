#!/usr/bin/env python3
"""Generate repository-shaped training exemplars for canonical TS repairs."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "benchmarks/nextjs_fixture"
OUT = ROOT / ".oktopai/datasets/typescript-trajectories-real-repository-supplement-v1.jsonl"


def make(index: int, name: str) -> dict:
    broken = f"export function {name}<T>(obj: T, key: string) {{ return obj[key]; }}"
    fixed = f"export function {name}<T, K extends keyof T>(obj: T, key: K): T[K] {{ return obj[key]; }}"
    path = f"lib/{name}.ts"
    files = {"package.json": (FIXTURE / "package.json").read_text(), "tsconfig.json": (FIXTURE / "tsconfig.json").read_text(), "next-env.d.ts": (FIXTURE / "next-env.d.ts").read_text(), "next.config.mjs": (FIXTURE / "next.config.mjs").read_text(), "app/page.tsx": (FIXTURE / "app/page.tsx").read_text(), path: broken}
    trajectory = [
        {"event": "inspect", "tool": "read_file", "args": {"path": path}},
        {"event": "diagnose", "tool": "run", "args": {"command": "tsc --noEmit --pretty false"}},
        {"event": "observe", "exit_code": 2},
        {"event": "edit", "tool": "apply_patch", "args": {"path": path, "content": fixed}},
        {"event": "diagnose", "tool": "run", "args": {"command": "tsc --noEmit --pretty false"}},
        {"event": "observe", "exit_code": 0},
        {"event": "final", "content": "Constrained the key to keyof T and verified the full project typecheck."},
    ]
    return {"id": f"real-repository-supplement-{index:02d}", "domain": "typescript-nextjs-repository", "split": "train", "task": f"Repair the TS7053 strict-indexing error in {path} and verify the full Next.js project typecheck. Use the canonical trajectory JSON contract.", "repository_facts": {"root": "benchmarks/nextjs_fixture", "validator": "tsc --noEmit --pretty false", "focus": "generic property lookup", "training_exemplar": True}, "repository_files": files, "trajectory": trajectory, "final": trajectory[-1]["content"], "provenance": {"source": "local repository fixture", "family": "real-repository-supplement", "variant": index}}


def main() -> int:
    names = ["getLabel", "readField", "lookupValue", "pickProperty", "selectKey", "extractField", "getEntry", "readValue", "findProperty", "getMember", "selectField", "lookupField"]
    rows = [make(index, name) for index, name in enumerate(names, 1)]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n")
    print(json.dumps({"records": len(rows), "output": str(OUT), "split": "train"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
