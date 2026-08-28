#!/usr/bin/env python3
"""Apply conservative, explainable repairs to external TypeScript answers."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any


def extract_code(value: str) -> str:
    blocks = re.findall(r"```(?:typescript|tsx|ts)?\s*\n(.*?)```", value, re.I | re.S)
    return "\n\n".join(blocks) if blocks else value.strip()


def repair(prompt: str, answer: str) -> tuple[str, list[str]]:
    code = extract_code(answer)
    changes: list[str] = []
    # Common malformed generic emitted by the external dataset.
    fixed = re.sub(r"<T extends \{string \| number \| boolean\}\}>", "<T extends string | readonly unknown[]>", code)
    if fixed != code:
        code, changes = fixed, changes + ["repaired malformed generic constraint"]
    fixed = code.replace("({item} as any).length", "item.length")
    if fixed != code:
        code, changes = fixed, changes + ["removed malformed object wrapper and any cast"]
    # A task without an explicit input type is made precise only for this
    # unambiguous family; other semantic choices remain rejected.
    if re.search(r"function \w+.*takes a item and returns its length", prompt, re.I):
        match = re.search(r"function\s+(\w+)", code)
        if match and "item: T" in code and "extends string | readonly unknown[]" in code:
            name = match.group(1)
            code = f"function {name}(item: string | readonly unknown[]): number {{\n  return item.length;\n}}"
            changes.append("specialized ambiguous length task to string-or-readonly-array")
    return code, changes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--rejected-output", type=Path, required=True)
    parser.add_argument("--tsc", required=True)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--timeout", type=int, default=20)
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines() if line.strip()]

    def process(row: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        prompt = row["messages"][-1]["content"]
        code, changes = repair(prompt, row["completion"])
        rejected = {**row, "repair": {"changes": changes, "status": "rejected", "reason": "did not compile after conservative repair"}}
        if not code or not changes:
            rejected["repair"]["reason"] = "no safe direct repair rule applies"
            return None, rejected
        with tempfile.TemporaryDirectory(prefix="oktopai-direct-repair-") as directory:
            path = Path(directory) / "candidate.ts"
            path.write_text(code, encoding="utf-8")
            try:
                result = subprocess.run([args.tsc, "--noEmit", "--strict", "--target", "ES2020", str(path)], capture_output=True, text=True, timeout=args.timeout)
            except subprocess.TimeoutExpired:
                rejected["repair"]["reason"] = "compiler timeout"
                return None, rejected
        if result.returncode != 0:
            rejected["repair"]["diagnostics"] = result.stderr or result.stdout
            return None, rejected
        accepted = {**row, "completion": code, "source_code": code, "repair": {"changes": changes, "status": "verified", "compiler": "strict TypeScript"}}
        accepted["provenance"] = {**row.get("provenance", {}), "direct_repair": True, "verification_status": "tsc-strict"}
        return accepted, rejected

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        results = list(pool.map(process, rows))
    accepted = [item for item, _ in results if item is not None]
    rejected = [item for _, item in results]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in accepted) + ("\n" if accepted else ""), encoding="utf-8")
    args.rejected_output.write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in rejected) + ("\n" if rejected else ""), encoding="utf-8")
    print(json.dumps({"input": len(rows), "accepted": len(accepted), "rejected": len(rejected), "output": str(args.output), "rejected_output": str(args.rejected_output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
