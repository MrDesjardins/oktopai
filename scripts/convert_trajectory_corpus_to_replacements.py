#!/usr/bin/env python3
"""Convert complete-file edit trajectories into uniformly replacement-mode records."""

from __future__ import annotations

import argparse
import difflib
import json
from pathlib import Path


def convert(record: dict) -> dict:
    converted = json.loads(json.dumps(record))
    facts = converted.setdefault("repository_facts", {})
    facts["large_file"] = True
    facts["edit_mode"] = "exact-replacements"
    task = converted.get("task", "")
    if "exact once-only replacements" not in task:
        converted["task"] = task.rstrip(".") + ". Use exact once-only replacements with the smallest changed span; never copy unchanged context or the whole file."

    snapshots = converted.get("repository_files", {})
    for event in converted.get("trajectory", []):
        if event.get("event") != "edit":
            continue
        args = event.setdefault("args", {})
        if "replacements" in args:
            continue
        path = args.get("path")
        content = args.pop("content", None)
        if not isinstance(path, str) or not isinstance(content, str):
            raise ValueError(f"{converted.get('id')}: edit lacks path/content")
        original = snapshots.get(path)
        if not isinstance(original, str):
            raise ValueError(f"{converted.get('id')}: no repository snapshot for {path}")
        if original == content:
            raise ValueError(f"{converted.get('id')}: edit does not change {path}")
        original_lines = original.splitlines(keepends=True)
        content_lines = content.splitlines(keepends=True)
        replacements = []
        matcher = difflib.SequenceMatcher(None, original_lines, content_lines, autojunk=False)
        for tag, old_start, old_end, new_start, new_end in matcher.get_opcodes():
            if tag == "equal":
                continue
            old = "".join(original_lines[old_start:old_end])
            new = "".join(content_lines[new_start:new_end])
            if not old or original.count(old) != 1:
                raise ValueError(f"{converted.get('id')}: generated replacement is empty or ambiguous")
            replacements.append({"old": old, "new": new})
        if not replacements:
            raise ValueError(f"{converted.get('id')}: edit has no diff")
        args["replacements"] = replacements
    return converted


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = [convert(json.loads(line)) for line in args.input.read_text(encoding="utf-8").splitlines() if line.strip()]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")
    print(json.dumps({"input": str(args.input), "output": str(args.output), "records": len(rows)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
