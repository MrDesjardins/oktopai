from __future__ import annotations

from dataclasses import dataclass, asdict
import json
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import tempfile
from typing import Any

@dataclass(frozen=True)
class Verification:
    status: str
    score: float
    checks: tuple[str, ...]
    failures: tuple[str, ...]
    executable: bool

def _code_blocks(text: str) -> list[str]:
    return re.findall(r"```(?:[a-zA-Z0-9_+-]+)?\s*\n?(.*?)```", text, re.DOTALL)

def verify_output(text: str, checks: dict[str, Any]) -> Verification:
    haystack = text
    passed: list[str] = []
    failures: list[str] = []
    required = checks.get("required", [])
    required_any = checks.get("required_any", [])
    for item in required:
        if item.lower() in haystack.lower(): passed.append(f"required:{item}")
        else: failures.append(f"missing:{item}")
    if required_any:
        if any(item.lower() in haystack.lower() for item in required_any): passed.append("required_any")
        else: failures.append("missing_any:" + "|".join(required_any))
    for item in checks.get("forbidden", []):
        if item.lower() in haystack.lower(): failures.append(f"forbidden:{item}")
        else: passed.append(f"absent:{item}")
    mode = checks.get("mode", "checklist")
    executable = False
    if mode == "python_compile":
        executable = True
        blocks = _code_blocks(text)
        source = blocks[0] if blocks else text
        try:
            compile(source, "benchmark_output.py", "exec")
            passed.append("python:compile")
        except SyntaxError as exc:
            failures.append(f"python:compile:{exc.msg}")
    elif mode == "sql_fixture":
        executable = True
        blocks = _code_blocks(text)
        source = next((block for block in blocks if "select" in block.lower()), text)
        try:
            connection = sqlite3.connect(":memory:")
            connection.executescript("CREATE TABLE customers(id INTEGER PRIMARY KEY, name TEXT); CREATE TABLE orders(id INTEGER PRIMARY KEY, customer_id INTEGER); INSERT INTO customers VALUES (0, 'Zero'), (1, 'Ada'), (2, 'Grace'); INSERT INTO orders VALUES (10, 1);")
            rows = connection.execute(source).fetchall()
            expected = [tuple(row) for row in checks.get("expected_rows", [])]
            if rows == expected: passed.append("sql:fixture-result")
            else: failures.append(f"sql:unexpected-result:{rows!r}")
            connection.close()
        except sqlite3.Error as exc:
            failures.append(f"sql:execute:{exc}")
    elif mode == "typescript_fixture":
        # Prefer a real compiler when one is already installed. Never install one
        # implicitly; this preserves the offline/no-download benchmark contract.
        local_tsc = Path(__file__).resolve().parents[2] / "benchmarks/nextjs_fixture/node_modules/.bin/tsc"
        tsc = shutil.which("tsc") or (str(local_tsc) if local_tsc.exists() else None)
        executable = bool(tsc)
        source = next(iter(_code_blocks(text)), text)
        required_source = checks.get("required_source", [])
        for item in required_source:
            if item not in source: failures.append(f"typescript:missing-source:{item}")
        if not executable:
            passed.append("typescript:fixture-contract-only")
        else:
            with tempfile.TemporaryDirectory(prefix="oktopai-ts-") as directory:
                source_path = Path(directory) / "candidate.ts"
                source_path.write_text(source)
                result = subprocess.run([tsc, "--noEmit", "--strict", str(source_path)], capture_output=True, text=True)
                if result.returncode == 0:
                    passed.append("typescript:compile")
                else:
                    failures.append("typescript:compile:" + ((result.stderr if result is not None else "compiler unavailable").strip()[:300]))
    elif mode == "framework_fixture":
        # React/Next executable rendering requires project dependencies. This
        # validator checks the complete fixture contract without installing them.
        executable = False
        source = next(iter(_code_blocks(text)), text)
        for item in checks.get("required_source", []):
            if item in source: passed.append(f"framework:source:{item}")
            else: failures.append(f"framework:missing-source:{item}")
        passed.append("framework:fixture-contract-only")
    elif mode == "test_fixture":
        executable = False
        source = next(iter(_code_blocks(text)), text)
        for item in checks.get("required_source", []):
            if item in source: passed.append(f"test:source:{item}")
            else: failures.append(f"test:missing-source:{item}")
        passed.append("test:fixture-contract-only")
    total = len(passed) + len(failures)
    score = len(passed) / total if total else 0.0
    status = "verified" if executable and not failures else ("fixture_pass" if mode != "checklist" and not failures else ("checklist_pass" if not failures else "failed"))
    return Verification(status, score, tuple(passed), tuple(failures), executable)

def load_tasks(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text())["tasks"]

def save_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(record, ensure_ascii=False) for record in records) + ("\n" if records else ""))
