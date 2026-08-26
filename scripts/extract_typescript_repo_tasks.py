#!/usr/bin/env python3
"""Extract candidate TypeScript tasks from a checked-out public repository.

Candidates are deliberately marked for teacher verification. A source file is
context, not a ground-truth answer, and this script never adds candidates to a
training corpus automatically.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


KEYWORDS = ("generic", "union", "narrow", "type", "infer", "module", "jsx", "decorator", "mapped")


def family(path: str) -> str:
    lowered = path.lower()
    for name, signals in {
        "generic": ("generic", "infer", "mapped"),
        "union-narrowing": ("union", "narrow", "discriminated"),
        "module": ("module", "import", "export", "declaration"),
        "jsx": ("jsx", "tsx"),
        "decorator": ("decorator",),
        "type-system": ("type",),
    }.items():
        if any(signal in lowered for signal in signals):
            return name
    return "compiler-conformance"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=1000)
    parser.add_argument("--max-chars", type=int, default=12000)
    args = parser.parse_args()
    candidates: list[dict[str, object]] = []
    root = args.source.resolve()
    for path in sorted((root / "tsc/testdata/tests/cases/conformance").rglob("*.ts")):
        relative = path.relative_to(root).as_posix()
        lowered = relative.lower()
        if not any(word in lowered for word in KEYWORDS):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if len(text) > args.max_chars or len(text.strip()) < 20:
            continue
        digest = hashlib.sha256(text.encode()).hexdigest()[:16]
        candidates.append({
            "id": f"typescript-repo-{digest}",
            "domain": "typescript",
            "task_type": "repository-context-teacher-review",
            "prompt": (
                "Use this TypeScript compiler conformance fixture as reference. "
                "Return one small, standalone, valid TypeScript example that "
                "teaches the same concept. Do not copy intentional errors from "
                "the fixture. The answer must compile under strict TypeScript."
            ),
            "source_code": text,
            "source_path": relative,
            "task_family": family(relative),
            "provenance": {
                "kind": "public-github",
                "repository": "microsoft/TypeScript",
                "license_review_required": True,
                "requires_teacher_verification": True,
            },
        })
        if len(candidates) >= args.limit:
            break
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for candidate in candidates:
            handle.write(json.dumps(candidate, ensure_ascii=False) + "\n")
    print(json.dumps({"output": str(args.output), "records": len(candidates), "review_required": True}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
