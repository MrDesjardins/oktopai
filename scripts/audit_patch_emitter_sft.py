#!/usr/bin/env python3
"""Audit prepared patch-emitter SFT records before training."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--max-prompt-chars", type=int, default=2400)
    args = parser.parse_args()
    failures = []
    ids: set[str] = set()
    splits = Counter()
    records = 0
    for line_number, line in enumerate(args.input.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        records += 1
        row = json.loads(line)
        record_id = row.get("id")
        if not isinstance(record_id, str) or not record_id or record_id in ids:
            failures.append({"line": line_number, "code": "missing_or_duplicate_id", "id": record_id})
        ids.add(record_id)
        splits[row.get("split", "missing")] += 1
        messages = row.get("messages")
        if not isinstance(messages, list) or len(messages) != 1 or messages[0].get("role") != "user":
            failures.append({"line": line_number, "code": "invalid_messages", "id": record_id})
            continue
        prompt = messages[0].get("content", "")
        if len(prompt) > args.max_prompt_chars:
            failures.append({"line": line_number, "code": "prompt_too_large", "id": record_id, "chars": len(prompt)})
        try:
            request = json.loads(prompt)
            if "repository_files" in request:
                failures.append({"line": line_number, "code": "full_snapshot_in_prompt", "id": record_id})
            target = request.get("target", {})
            if not isinstance(target.get("diagnostic_locations"), list) or not target.get("diagnostic_locations"):
                failures.append({"line": line_number, "code": "missing_diagnostic_locations", "id": record_id})
            if not isinstance(target.get("source_localization_rule"), str) or not target["source_localization_rule"].strip():
                failures.append({"line": line_number, "code": "missing_source_localization_rule", "id": record_id})
        except json.JSONDecodeError as exc:
            failures.append({"line": line_number, "code": "invalid_prompt_json", "id": record_id, "message": str(exc)})
        try:
            completion = json.loads(row.get("completion", ""))
            replacements = completion["replacements"]
            if not isinstance(replacements, list) or not replacements:
                raise ValueError("replacements must be non-empty")
            for replacement in replacements:
                if not isinstance(replacement, dict) or not replacement.get("old") or not isinstance(replacement.get("new"), str):
                    raise ValueError("invalid replacement shape")
                if replacement["old"] == replacement["new"]:
                    raise ValueError("unchanged replacement")
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            failures.append({"line": line_number, "code": "invalid_completion", "id": record_id, "message": str(exc)})
    result = {"input": str(args.input), "records": records, "unique_ids": len(ids), "splits": dict(splits), "failed_checks": len(failures), "failures": failures[:20], "sft_preflight_pass": bool(records) and not failures}
    print(json.dumps(result, indent=2))
    return 0 if result["sft_preflight_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
