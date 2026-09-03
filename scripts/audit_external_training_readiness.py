#!/usr/bin/env python3
"""Audit an external corpus before it is mixed into student training data."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


def records(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def content_hash(item: dict[str, Any]) -> str:
    prompt = item.get("prompt") or next(
        (m.get("content", "") for m in item.get("messages", []) if m.get("role") == "user"), ""
    )
    completion = item.get("completion") or item.get("original_completion", "")
    payload = json.dumps([prompt.strip(), completion.strip()], ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def counts(items: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(item.get(key, "unknown")) for item in items).items()))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--external", type=Path, required=True)
    parser.add_argument("--teacher", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    external = records(args.external)
    teacher = records(args.teacher)
    external_ids = [str(item.get("id", "")) for item in external]
    teacher_ids = {str(item.get("id", "")) for item in teacher}
    external_hashes = [content_hash(item) for item in external]
    teacher_hashes = {content_hash(item) for item in teacher}
    source_counts = Counter(str(item.get("provenance", {}).get("source", item.get("source_file", "unknown"))) for item in external)
    unsafe_any = sum(1 for item in external if re.search(r"\b(as\s+any|:\s*any\b|<any>)", str(item.get("completion", ""))))
    max_source_share = max(source_counts.values(), default=0) / len(external) if external else 0.0
    identity_gate = len(external_ids) == len(set(external_ids)) and not (set(external_hashes) & teacher_hashes)
    balance_gate = max_source_share <= 0.70 and unsafe_any == 0
    report = {
        "external_path": str(args.external),
        "teacher_path": str(args.teacher),
        "external_records": len(external),
        "teacher_records": len(teacher),
        "external_unique_ids": len(set(external_ids)),
        "external_duplicate_ids": len(external_ids) - len(set(external_ids)),
        "external_unique_prompt_completion_pairs": len(set(external_hashes)),
        "external_duplicate_prompt_completion_pairs": len(external_hashes) - len(set(external_hashes)),
        "id_overlap_with_teacher": len(set(external_ids) & teacher_ids),
        "prompt_completion_overlap_with_teacher": len(set(external_hashes) & teacher_hashes),
        "splits": counts(external, "split"),
        "families": counts(external, "family"),
        "sources": dict(sorted(source_counts.items())),
        "unsafe_any_targets": unsafe_any,
        "max_source_share": round(max_source_share, 4),
        "identity_gate": "pass" if identity_gate else "fail",
        "balance_gate": "pass" if balance_gate else "review",
        "readiness": "pass" if identity_gate and balance_gate else "review",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
