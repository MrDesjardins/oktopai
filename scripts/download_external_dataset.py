#!/usr/bin/env python3
"""Download a bounded Hugging Face dataset slice with reproducible metadata.

This intentionally does not convert records into training data. Imported rows
must be normalized, deduplicated, licensed, and verified separately.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True, help="Hugging Face dataset ID")
    parser.add_argument("--split", default="train")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-records", type=int, default=10_000)
    args = parser.parse_args()

    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise SystemExit("Install the training stack before using this importer") from exc

    if args.max_records <= 0:
        raise SystemExit("--max-records must be positive")

    dataset = load_dataset(args.dataset, split=args.split, streaming=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with args.output.open("w", encoding="utf-8") as handle:
        for row in dataset:
            handle.write(json.dumps(dict(row), ensure_ascii=False) + "\n")
            count += 1
            if count >= args.max_records:
                break

    manifest: dict[str, Any] = {
        "schema_version": "1.0",
        "dataset": args.dataset,
        "split": args.split,
        "records": count,
        "bounded": True,
        "raw_jsonl": str(args.output),
        "sha256": sha256(args.output),
        "downloaded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "training_eligible": False,
        "next_steps": ["review provenance and license", "normalize", "deduplicate", "language-specific verification"],
    }
    manifest_path = args.output.with_suffix(args.output.suffix + ".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
