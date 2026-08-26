#!/usr/bin/env python3
"""Build repository-grounded TypeScript teacher tasks.

The output is a candidate corpus, not training truth. A teacher (local or
external) may answer these tasks, after which answers must pass the project
verifier before entering student training. The script intentionally stores
provenance and deterministic task IDs so the same repository snapshot can be
reproduced.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

STYLES = (
    ("explain", "Explain the TypeScript behavior in this example and identify the key type-system rule."),
    ("diagnose", "Diagnose the likely strict TypeScript error in this example and propose a minimal fix."),
    ("refactor", "Refactor this example for clearer, safer TypeScript while preserving runtime behavior."),
    ("generic", "Improve the generic types in this example without using any or unsafe assertions."),
    ("api-contract", "Make the public API types precise, including nullability and return types."),
    ("module", "Review the imports, exports, and module boundary for strict TypeScript correctness."),
    ("test", "Design a focused TypeScript test for this behavior and type the test safely."),
    ("migration", "Suggest a minimal migration for this code to stricter modern TypeScript settings."),
    ("review", "Perform a TypeScript code review and return concrete, compiler-valid improvements."),
    ("repair", "Return the smallest compiler-valid repair for this TypeScript example."),
)

ANGLES = (
    "Work under --strict and do not use any.",
    "Return the smallest safe patch and preserve runtime behavior.",
    "Explain the compiler reasoning before giving the code change.",
    "Assume this code is part of a public library API.",
    "Include nullability and undefined cases explicitly.",
    "Consider the behavior when a dependency is upgraded.",
    "Prefer inferred types where inference is clearer than annotations.",
    "Consider both ESM and CommonJS consumers where modules are involved.",
    "Include a focused type-level or runtime test when appropriate.",
    "Review the result for maintainability and accidental type widening.",
)


def snippets(text: str, max_chars: int) -> list[str]:
    text = text.strip()
    if len(text) <= max_chars:
        return [text]
    blocks = re.split(r"\n\s*\n", text)
    selected: list[str] = []
    current = ""
    for block in blocks:
        if len(block) > max_chars:
            continue
        candidate = f"{current}\n\n{block}".strip()
        if len(candidate) > max_chars:
            if current:
                selected.append(current)
            current = block
        else:
            current = candidate
    if current:
        selected.append(current)
    return selected


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--limit", type=int, default=10_000)
    parser.add_argument("--max-files", type=int, default=5_000)
    parser.add_argument("--max-chars", type=int, default=8_000)
    parser.add_argument("--styles", default=",".join(style for style, _ in STYLES))
    parser.add_argument("--angles", default=",".join(str(index) for index in range(len(ANGLES))), help="comma-separated perspective indexes")
    args = parser.parse_args()
    wanted = set(args.styles.split(","))
    styles = [(name, prompt) for name, prompt in STYLES if name in wanted]
    if not styles:
        raise SystemExit("--styles did not select a known task style")
    angle_indexes = [int(value) for value in args.angles.split(",")]
    if any(index < 0 or index >= len(ANGLES) for index in angle_indexes):
        raise SystemExit(f"--angles values must be between 0 and {len(ANGLES) - 1}")

    root = args.source.resolve()
    rows: list[dict[str, object]] = []
    seen: set[str] = set()
    files = sorted(root.rglob("*.ts")) + sorted(root.rglob("*.tsx"))
    ignored = {"node_modules", ".git", "dist", "built", "coverage"}
    for path in files:
        if len(rows) >= args.limit or len(seen) >= args.max_files:
            break
        if ignored.intersection(path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if len(text.strip()) < 40:
            continue
        relative = path.relative_to(root).as_posix()
        for part_index, snippet in enumerate(snippets(text, args.max_chars)):
            source_hash = hashlib.sha256(snippet.encode()).hexdigest()[:16]
            if source_hash in seen:
                continue
            seen.add(source_hash)
            for style, instruction in styles:
                for angle_index in angle_indexes:
                    if len(rows) >= args.limit:
                        break
                    angle = ANGLES[angle_index]
                    task_key = f"{args.repository}:{args.commit}:{relative}:{part_index}:{style}:{angle_index}:{source_hash}"
                    task_id = "ts-usecase-" + hashlib.sha256(task_key.encode()).hexdigest()[:20]
                    rows.append({
                        "id": task_id,
                        "domain": "typescript",
                        "task_family": style,
                        "task_angle": angle_index,
                        "split": "candidate",
                        "prompt": f"{instruction} {angle}\n\nSource file: {relative}\n```typescript\n{snippet}\n```",
                        "source_code": snippet,
                        "source_path": relative,
                        "provenance": {
                            "kind": "public-repository-pattern",
                            "repository": args.repository,
                            "commit": args.commit,
                            "license_review_required": True,
                            "teacher_answer_required": True,
                            "source_hash": source_hash,
                            "angle": angle,
                        },
                    })
                if len(rows) >= args.limit:
                    break
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps({"output": str(args.output), "records": len(rows), "source_files": len(seen), "styles": [x[0] for x in styles]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
