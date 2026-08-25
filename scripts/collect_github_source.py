#!/usr/bin/env python3
"""Acquire a shallow public GitHub repository with provenance metadata.

This intentionally collects source for inspection and task mining. It does not
pretend that raw source is supervised training data.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def run(*command: str, cwd: Path | None = None) -> str:
    return subprocess.check_output(command, cwd=cwd, text=True).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default="microsoft/TypeScript")
    parser.add_argument("--output", type=Path, default=Path(".oktopai/sources/github"))
    parser.add_argument("--depth", type=int, default=1)
    args = parser.parse_args()
    owner, name = args.repo.split("/", 1)
    target = args.output / f"{owner}-{name}"
    url = f"https://github.com/{args.repo}.git"
    if not (target / ".git").exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(("git", "clone", "--depth", str(args.depth), url, str(target)), check=True)
    commit = run("git", "rev-parse", "HEAD", cwd=target)
    files = run("git", "ls-files", cwd=target).splitlines()
    licenses = [p for p in files if Path(p).name.lower().startswith(("license", "copying"))]
    manifest = {
        "repository": args.repo,
        "url": url,
        "commit": commit,
        "shallow": args.depth == 1,
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "file_count": len(files),
        "license_files": licenses,
        "usage": "Source for inspection and compiler/test-grounded task mining; review license before redistribution.",
        "privacy": "Public repository; stored in the repo-local .oktopai cache; no cloud inference is performed.",
    }
    manifest_path = target.parent / f"{owner}-{name}.manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
