#!/usr/bin/env python3
"""Create held-out trajectories grounded in the local Next.js fixture."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "benchmarks/nextjs_fixture"
OUT = ROOT / ".oktopai/datasets/typescript-trajectories-real-repository-eval-v1.jsonl"


def record(index: int, page: str, broken: str, fixed: str, note: str) -> dict:
    files = {
        "package.json": (FIXTURE / "package.json").read_text(),
        "tsconfig.json": (FIXTURE / "tsconfig.json").read_text(),
        "next-env.d.ts": (FIXTURE / "next-env.d.ts").read_text(),
        "next.config.mjs": (FIXTURE / "next.config.mjs").read_text(),
        "app/page.tsx": page,
        "lib/getValue.ts": broken,
    }
    trajectory = [
        {"event": "inspect", "tool": "read_file", "args": {"path": "app/page.tsx"}, "result": page},
        {"event": "inspect", "tool": "read_file", "args": {"path": "lib/getValue.ts"}, "result": broken},
        {"event": "diagnose", "tool": "run", "args": {"command": "tsc --noEmit --pretty false"}},
        {"event": "observe", "exit_code": 2, "stdout": "TS7053 strict indexing error in lib/getValue.ts"},
        {"event": "edit", "tool": "apply_patch", "args": {"path": "lib/getValue.ts", "content": fixed}},
        {"event": "diagnose", "tool": "run", "args": {"command": "tsc --noEmit --pretty false"}},
        {"event": "observe", "exit_code": 0, "stdout": ""},
        {"event": "final", "content": note},
    ]
    return {
        "id": f"real-repository-eval-{index:02d}",
        "domain": "typescript-nextjs-repository",
        "split": "validation",
        "task": "Repair the TS7053 strict-indexing error reported in lib/getValue.ts (obj[key] where key is string) in this existing Next.js repository. Preserve strict mode, edit the smallest necessary source file, and verify the full project typecheck. Output only the required compact JSON trajectory object; do not write prose or markdown.",
        "repository_facts": {
            "root": "benchmarks/nextjs_fixture",
            "validator": "tsc --noEmit --pretty false using tsconfig.json",
            "focus": "generic property lookup used by the app",
            "trajectory_contract": {
                "output": "Output only one compact JSON object with trajectory (array) and final (string); no prose or markdown; include only required keys",
                "outer_envelope": "The first JSON key must be trajectory and the only top-level keys are trajectory and final; never copy fields from trajectory_contract into the output",
                "output_order": "Begin with {\"trajectory\":[ and end with ],\"final\":\"...\"}; emit the outer object before any event objects",
                "edit_content": "args.content is the complete file text; JSON escapes each real newline once, never emit literal backslash+n characters",
                "edit_content_completeness": "args.content must include the complete target file, including unchanged context; never emit a snippet or ellipsis",
                "events": ["inspect", "diagnose", "edit", "observe", "retry", "final"],
                "tools": ["read_file", "search", "run", "apply_patch"],
                "event_fields": {"inspect": "tool + args", "diagnose": "tool + args.command", "edit": "tool + args.path + (complete args.content or exact args.replacements)", "observe": "exit_code integer", "final": "content string"},
                "replacements": "each replacement has non-empty old and string new; old must occur exactly once",
                "large_file_edit": "when repository_facts.large_file or edit_mode=exact-replacements, use args.replacements instead of complete content",
                "diagnose_command": "must start with tsc --noEmit, npx tsc --noEmit, or npm exec tsc --noEmit",
                "repair_order": "inspect/diagnose -> observe -> edit -> diagnose -> observe exit_code 0 -> final; verify after the last edit",
            },
        },
        "repository_files": files,
        "trajectory": trajectory,
        "final": note,
        "provenance": {"source": "local repository fixture", "family": "real-repository", "mutation": index},
    }


def main() -> int:
    base_pages = [
        'import { useState } from "react";\n\nexport default function Page() {\n  const [open, setOpen] = useState(false);\n  return <button onClick={() => setOpen(!open)}>{String(open)}</button>;\n}\n',
        'import { useState } from "react";\nimport { getValue } from "../lib/getValue";\n\nexport default function Page() {\n  const [open, setOpen] = useState(false);\n  const label = getValue({ name: "Open" }, "name");\n  return <button aria-label={label} onClick={() => setOpen(!open)}>{String(open)}</button>;\n}\n',
    ]
    broken = 'export function getValue<T>(obj: T, key: string) {\n  return obj[key];\n}\n'
    fixed = 'export function getValue<T, K extends keyof T>(obj: T, key: K): T[K] {\n  return obj[key];\n}\n'
    rows = [record(i, base_pages[i % len(base_pages)], broken, fixed, "Project typecheck passes after constraining the key to keyof T.") for i in range(1, 9)]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n")
    print(json.dumps({"output": str(OUT), "records": len(rows), "split": "validation"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
