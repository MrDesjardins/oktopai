#!/usr/bin/env python3
"""Build deterministic chosen/rejected pairs from compiler-verified records.

Rejected answers are intentionally corrupted variants. They are candidates for
preference training, not automatically trusted labels; the verifier status is
stored with every pair.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def corrupt(text: str, family: str) -> str:
    replacements = {
        "generic-indexed-access": [("K extends keyof T", "K extends string"), ("T[K]", "T[string]")],
        "null-narrowing": [("if (value === null) return 0; ", ""), ("value.length", "(value as any).length")],
        "discriminated-union": [("result.kind === 'ok'", "true")],
        "record-dictionary": [("Record<string, number>", "Record<string, string>")],
        "readonly-generic": [("readonly T[]", "T[]")],
        "async-return": [(": Promise<string>", "")],
        "overload-signature": [("function parse", "function parse"), ("function parse", "function parse")],
        "mapped-type": [("[K in keyof T]", "[K: string]")],
        "type-predicate": [("value is string", "boolean")],
        "object-constraint": [("T extends object", "T")],
    }
    variants = replacements.get(family, [])
    rejected = text
    for old, new in variants:
        rejected = rejected.replace(old, new, 1)
    if rejected == text:
        rejected = re.sub(r"\breturn\b", "return undefined as any; // rejected\n//", text, count=1)
    return rejected


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=3000)
    args = parser.parse_args()
    pairs = []
    for line in args.input.read_text(encoding="utf-8").splitlines():
        item = json.loads(line)
        if item.get("split") not in ("train", "validation"):
            continue
        chosen = item.get("completion", "")
        rejected = corrupt(chosen, item.get("family", ""))
        if chosen == rejected:
            continue
        pairs.append({
            "id": f"preference-{item['id']}",
            "domain": item.get("domain", "typescript"),
            "family": item.get("family", "unknown"),
            "split": item.get("split", "train"),
            "messages": item.get("messages", []),
            "chosen": chosen,
            "rejected": rejected,
            "provenance": {"source": "deterministic-corruption", "parent_id": item["id"], "requires_verifier": True},
        })
        if len(pairs) >= args.limit:
            break
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(json.dumps(pair, ensure_ascii=False) for pair in pairs) + ("\n" if pairs else ""), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "pairs": len(pairs)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
