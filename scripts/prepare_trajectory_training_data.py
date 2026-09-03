#!/usr/bin/env python3
"""Convert verified trajectory records into deterministic SFT records and manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


TRAJECTORY_CONTRACT = {
    "output": "Output only one compact JSON object with trajectory (array) and final (string); no prose or markdown; include only required keys",
    "outer_envelope": "The first JSON key must be trajectory and the only top-level keys are trajectory and final; never copy fields from trajectory_contract into the output",
    "output_order": "Begin with {\"trajectory\":[ and end with ],\"final\":\"...\"}; emit the outer object before any event objects",
    "edit_content": "args.content is the complete file text; JSON escapes each real newline once, never emit literal backslash+n characters",
    "edit_content_completeness": "args.content must include the complete target file, including unchanged context; never emit a snippet or ellipsis",
    "events": ["inspect", "diagnose", "edit", "observe", "retry", "final"],
    "tools": ["read_file", "search", "run", "apply_patch"],
    "event_fields": {"inspect": "tool + args", "diagnose": "tool + args.command", "edit": "tool + args.path + (complete args.content or exact args.replacements)", "observe": "exit_code integer", "final": "content string"},
    "replacements": "each replacement has non-empty old and string new; old must occur exactly once",
    "replacement_minimality": "use the smallest changed span that fixes the error; do not copy unchanged surrounding lines or the whole file",
    "large_file_edit": "when repository_facts.large_file or edit_mode=exact-replacements, use args.replacements instead of complete content",
    "diagnose_command": "must start with tsc --noEmit, npx tsc --noEmit, or npm exec tsc --noEmit",
    "repair_order": "inspect/diagnose -> observe -> edit -> diagnose -> observe exit_code 0 -> final; verify after the last edit",
}


def canonical(record: dict) -> str:
    return json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def convert(record: dict) -> dict:
    trajectory = record["trajectory"]
    completion = json.dumps({"trajectory": trajectory, "final": record["final"]},
                            ensure_ascii=False, separators=(",", ":"))
    return {
        "id": record["id"],
        "domain": record.get("domain", "typescript"),
        "split": record.get("split", "train"),
        "messages": [{
            "role": "user",
            "content": json.dumps({
            "task": record["task"],
            "repository_facts": record["repository_facts"],
            "repository_files": record.get("repository_files", {}),
            "trajectory_contract": TRAJECTORY_CONTRACT,
        }, ensure_ascii=False, separators=(",", ":")),
        }],
        "completion": completion,
        "task": record["task"],
        "repository_facts": record["repository_facts"],
        "repository_files": record.get("repository_files", {}),
        "source_id": record["id"],
        "provenance": record.get("provenance", {}),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--base-model", type=Path, required=True)
    args = parser.parse_args()

    records = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines() if line.strip()]
    converted = [convert(record) for record in records]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in converted) + "\n", encoding="utf-8")

    source_hash = hashlib.sha256(args.input.read_bytes()).hexdigest()
    output_hash = hashlib.sha256(args.output.read_bytes()).hexdigest()
    splits = {split: sum(row["split"] == split for row in converted) for split in sorted({row["split"] for row in converted})}
    manifest = {
        "kind": "typescript-trajectory-sft-preflight-v1",
        "source": str(args.input.resolve()),
        "source_sha256": source_hash,
        "output": str(args.output.resolve()),
        "output_sha256": output_hash,
        "base_model": str(args.base_model.resolve()),
        "records": len(converted),
        "splits": splits,
        "completion_format": "compact JSON object containing trajectory and final",
        "training_args": {
            "loss_mode": "completion-only",
            "epochs": 4.0,
            "max_steps": 200,
            "batch_size": 1,
            "gradient_accumulation": 8,
            "device": "cuda",
        },
        "status": "preflight-only; no training started",
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"records": len(converted), "splits": splits, "output": str(args.output), "manifest": str(args.manifest)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
