#!/usr/bin/env python3
"""Prepare the externally curated TypeScript corpus for a gated train run.

This does not claim that an open-source snippet is universally correct. It
only admits records that already carry strict compiler evidence, a usable
prompt/completion pair, and no obvious unsafe-target markers. Records rejected
here remain available in the curation and quarantine artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


FAMILIES: list[tuple[str, tuple[str, ...]]] = [
    ("generics", ("generic", "keyof", "t[k]", "conditional type", "mapped type")),
    ("narrowing", ("narrow", "type guard", "predicate", "unknown", "discriminated")),
    ("async", ("async", "await", "promise", "observable")),
    ("classes", ("class", "constructor", "inherit", "implements")),
    ("modules", ("import", "export", "module")),
    ("errors", ("error", "exception", "validation")),
    ("react", ("react", "component", "jsx", "rerender")),
]


def family(prompt: str, code: str) -> str:
    text = f"{prompt} {code}".lower()
    for name, signals in FAMILIES:
        if any(signal in text for signal in signals):
            return name
    return "core-types"


def split_for(identifier: str) -> str:
    # Stable split prevents accidental leakage across repeated runs.
    value = int(hashlib.sha256(identifier.encode()).hexdigest()[:8], 16) % 100
    return "test" if value < 10 else "validation" if value < 20 else "train"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()

    accepted: list[dict[str, Any]] = []
    rejected: Counter[str] = Counter()
    families: Counter[str] = Counter()
    for line in args.input.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        completion = item.get("completion", "")
        prompt = item.get("prompt", "")
        verification = item.get("verification", {})
        if item.get("disposition") != "verified_code" or item.get("training_eligible") is not True:
            rejected["missing_verified_code_disposition"] += 1
            continue
        if verification.get("status") != "passed":
            rejected["compiler_gate_missing"] += 1
            continue
        if not prompt.strip() or not completion.strip():
            rejected["empty_prompt_or_completion"] += 1
            continue
        if re.search(r"\b(as\s+any|:\s*any\b|<any>)", completion):
            rejected["unsafe_any"] += 1
            continue
        if "TODO" in completion or "@bad" in completion:
            rejected["unfinished_source_markers"] += 1
            continue
        item["family"] = family(prompt, completion)
        item["split"] = split_for(item["id"])
        item["training_eligible"] = True
        item["provenance"] = {
            **item.get("provenance", {}),
            "external_curation_gate": "passed",
            "open_source_provenance_is_not_correctness_proof": True,
        }
        accepted.append(item)
        families[item["family"]] += 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in accepted) + ("\n" if accepted else ""), encoding="utf-8")
    manifest = {
        "input": str(args.input),
        "output": str(args.output),
        "input_records": sum(accepted.__len__() for _ in [0]) + sum(rejected.values()),
        "accepted": len(accepted),
        "rejected": sum(rejected.values()),
        "splits": dict(Counter(x["split"] for x in accepted)),
        "families": dict(families),
        "rejection_reasons": dict(rejected),
        "gate": "strict compiler evidence + prompt/completion + no obvious unsafe target",
        "provenance_note": "Open-source origin supports provenance, not semantic correctness.",
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
