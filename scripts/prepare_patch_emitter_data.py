#!/usr/bin/env python3
"""Prepare patch-emitter SFT records with bounded source context only."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from oktopai.trajectory import apply_replacements, build_patch_emitter_request


def convert(record: dict, radius: int, max_chars: int) -> dict:
    edits = [event for event in record.get("trajectory", []) if event.get("event") == "edit"]
    if len(edits) != 1:
        raise ValueError(f"{record.get('id')}: expected exactly one edit")
    edit = edits[0]
    args = edit.get("args", {})
    path = args.get("path")
    replacements = args.get("replacements")
    if not isinstance(path, str) or not isinstance(replacements, list) or not replacements:
        raise ValueError(f"{record.get('id')}: expected replacement edit")
    source = record.get("repository_files", {}).get(path)
    if not isinstance(source, str):
        raise ValueError(f"{record.get('id')}: missing source snapshot for {path}")
    apply_replacements(source, replacements)
    first_anchor = replacements[0]["old"]
    offset = source.find(first_anchor)
    if offset < 0:
        raise ValueError(f"{record.get('id')}: replacement anchor not found")
    line = source.count("\n", 0, offset) + 1
    diagnostic = record.get("compiler_diagnostic") or f"{path}({line},1): error TS2322: TypeScript repair required by task."
    request = build_patch_emitter_request(record, diagnostic, radius=radius, max_chars=max_chars)
    request["target"]["replacements_must_be_minimal"] = True
    completion = json.dumps({"path": path, "replacements": replacements}, ensure_ascii=False, separators=(",", ":"))
    return {
        "id": record["id"],
        "domain": record.get("domain", "typescript"),
        "split": record.get("split", "train"),
        "messages": [{"role": "user", "content": json.dumps(request, ensure_ascii=False, separators=(",", ":"))}],
        "completion": completion,
        "task": record.get("task", ""),
        "target_path": path,
        "provenance": {"kind": "derived-patch-emitter", "source_id": record.get("id"), "evaluation_only": False},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--radius", type=int, default=3)
    parser.add_argument("--max-context-chars", type=int, default=2400)
    args = parser.parse_args()
    rows = [convert(json.loads(line), args.radius, args.max_context_chars)
            for line in args.input.read_text(encoding="utf-8").splitlines() if line.strip()]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")
    splits = {split: sum(row["split"] == split for row in rows) for split in sorted({row["split"] for row in rows})}
    manifest = {
        "kind": "typescript-patch-emitter-sft-v1",
        "source": str(args.input.resolve()),
        "source_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
        "output": str(args.output.resolve()),
        "output_sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
        "records": len(rows),
        "splits": splits,
        "radius": args.radius,
        "max_context_chars": args.max_context_chars,
        "full_repository_files_in_prompt": False,
        "status": "preflight-only; no training started",
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"records": len(rows), "splits": splits, "output": str(args.output), "manifest": str(args.manifest)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
