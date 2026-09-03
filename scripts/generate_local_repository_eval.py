#!/usr/bin/env python3
"""Generate evaluation-only trajectories from a clean local TypeScript repo."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path("/home/miste/code/desktop-ai-companion")
OUT = ROOT / ".oktopai/datasets/typescript-trajectories-local-repository-eval-v1.jsonl"


def make(index: int, family: str, broken: str, fixed: str, issue: str) -> dict:
    source = (SOURCE / "apps/desktop/src/main.tsx").read_text(encoding="utf-8")
    if fixed not in source:
        raise ValueError(f"source repair anchor not found: {fixed}")
    broken_source = source.replace(fixed, broken, 1)
    fixed_source = source
    files = {
        "package.json": (SOURCE / "apps/desktop/package.json").read_text(encoding="utf-8"),
        "package-lock.json": (SOURCE / "apps/desktop/package-lock.json").read_text(encoding="utf-8"),
        "tsconfig.json": (SOURCE / "apps/desktop/tsconfig.json").read_text(encoding="utf-8"),
        "vite.config.ts": (SOURCE / "apps/desktop/vite.config.ts").read_text(encoding="utf-8"),
        "index.html": (SOURCE / "apps/desktop/index.html").read_text(encoding="utf-8"),
        "src/main.tsx": broken_source,
        "src/styles.css": (SOURCE / "apps/desktop/src/styles.css").read_text(encoding="utf-8"),
    }
    trajectory = [
        {"event": "inspect", "tool": "read_file", "args": {"path": "src/main.tsx"}},
        {"event": "diagnose", "tool": "run", "args": {"command": "tsc --noEmit --incremental false --pretty false"}},
        {"event": "observe", "exit_code": 2},
        {"event": "edit", "tool": "apply_patch", "args": {"path": "src/main.tsx", "content": fixed_source}},
        {"event": "diagnose", "tool": "run", "args": {"command": "tsc --noEmit --incremental false --pretty false"}},
        {"event": "observe", "exit_code": 0},
        {"event": "final", "content": "Applied the minimal repair in the local repository and verified the full TypeScript project typecheck."},
    ]
    return {
        "id": f"local-repository-eval-v1-{index:03d}",
        "domain": "typescript-local-repository",
        "split": "validation",
        "task": f"Repair the {family} TypeScript error in src/main.tsx: {issue} This is a large-file task: use exact once-only replacements, not abbreviated content. Inspect the surrounding repository context, edit only the target file, and verify the full desktop project typecheck. Emit the canonical trajectory JSON contract.",
        "repository_facts": {"root": "apps/desktop", "validator": "tsc --noEmit --incremental false --pretty false", "family": family, "source_repository": "local checkout desktop-ai-companion", "evaluation_only": True, "large_file": True, "edit_mode": "exact-replacements"},
        "repository_files": files,
        "trajectory": trajectory,
        "final": trajectory[-1]["content"],
        "provenance": {"kind": "local-repository-evaluation", "repository": "desktop-ai-companion", "source_root": str(SOURCE), "training": False, "license_review_required": True, "variant": index},
    }


def main() -> int:
    mutations = [
        ("literal-mismatch", 'mode: "unknown",', 'mode: "idle",', "the state literal must belong to the CompanionMode union"),
        ("literal-mismatch", 'return "unknown";', 'return "idle";', "the fallback animation mode must belong to the declared mode union"),
        ("nullable-property", 'speech: next.speech_bubble', 'speech: next.speech_bubble ?? undefined', "a nullable native response field must be converted to an optional string"),
        ("number-mismatch", 'const ratio = window.devicePixelRatio || "1";', 'const ratio = window.devicePixelRatio || 1;', "canvas dimensions require a numeric device-pixel ratio"),
    ]
    rows = [make(index, *mutations[index % len(mutations)]) for index in range(20)]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUT), "records": len(rows), "families": len(mutations), "split": "validation", "source": str(SOURCE)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
