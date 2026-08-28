#!/usr/bin/env python3
"""Analyze verified external TypeScript candidates without training on them."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


def load(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def family(prompt: str) -> str:
    text = prompt.lower()
    signals = {
        "generics": ("generic", "keyof", "conditional type", "mapped type"),
        "narrowing": ("narrow", "type guard", "discriminated", "unknown"),
        "async": ("async", "promise", "await", "observable"),
        "modules": ("module", "import", "export", "declaration"),
        "jsx": ("jsx", "tsx", "react", "component"),
        "classes": ("class", "decorator", "inheritance", "implements"),
        "errors": ("error", "fix", "bug", "diagnostic", "compile"),
    }
    for name, terms in signals.items():
        if any(term in text for term in terms):
            return name
    return "other"


def digest(prompt: str, completion: str) -> str:
    normalized = re.sub(r"\s+", " ", f"{prompt}\n{completion}").strip().lower()
    return hashlib.sha256(normalized.encode()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", action="append", type=Path, required=True)
    parser.add_argument("--verified", action="append", type=Path, required=True)
    parser.add_argument("--teacher", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    teacher = load(args.teacher)
    teacher_keys = {digest(row.get("prompt", ""), row.get("completion", "")) for row in teacher}
    report: dict[str, Any] = {"sources": [], "combined": {}}
    all_verified_keys: set[str] = set()
    all_verified = 0
    all_raw = 0
    all_duplicates = 0
    combined_families: Counter[str] = Counter()
    for raw_path, verified_path in zip(args.raw, args.verified):
        raw = load(raw_path)
        verified = load(verified_path)
        keys = [digest(row.get("messages", [{}])[-1].get("content", ""), row.get("completion", "")) for row in verified]
        duplicate_count = len(keys) - len(set(keys))
        teacher_overlap = sum(key in teacher_keys for key in keys)
        families = Counter(family(row.get("messages", [{}])[-1].get("content", "")) for row in verified)
        code_fence = sum("```" in row.get("completion", "") for row in verified)
        any_count = sum(bool(re.search(r"\bany\b", row.get("completion", ""))) for row in verified)
        report["sources"].append({
            "raw": str(raw_path),
            "verified": str(verified_path),
            "raw_records": len(raw),
            "verified_records": len(verified),
            "acceptance_ratio": len(verified) / len(raw) if raw else 0,
            "verified_duplicates": duplicate_count,
            "overlap_with_teacher": teacher_overlap,
            "families": dict(families),
            "verified_with_code_fence": code_fence,
            "verified_with_any": any_count,
        })
        all_raw += len(raw)
        all_verified += len(verified)
        all_duplicates += duplicate_count
        combined_families.update(families)
        all_verified_keys.update(keys)
    report["combined"] = {
        "raw_records": all_raw,
        "verified_records": all_verified,
        "acceptance_ratio": all_verified / all_raw if all_raw else 0,
        "cross_source_duplicates": all_verified - len(all_verified_keys),
        "teacher_overlap": sum(key in teacher_keys for key in all_verified_keys),
        "families": dict(combined_families),
        "training_eligible": False,
        "decision": "candidate_only_until provenance review and balanced split",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
