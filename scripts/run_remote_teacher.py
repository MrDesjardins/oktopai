#!/usr/bin/env python3
"""Generate resumable teacher answers through a local Ollama HTTP server.

This script records raw teacher output only. Verification is deliberately a
separate stage so the same answers can be checked locally and independently.
"""

from __future__ import annotations

import argparse
import gzip
import json
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


def generate(url: str, model: str, prompt: str, max_tokens: int, task_family: str) -> dict:
    if task_family in {"explain", "review"}:
        system = (
            "You are a senior TypeScript reviewer. Explain the source-grounded "
            "reasoning first. If code is needed, put only compilable TypeScript "
            "in a fenced ```typescript block. Never claim a command was run."
        )
    elif task_family == "test":
        system = (
            "You are a senior TypeScript test engineer. Return a focused, "
            "compilable test or testable TypeScript change in a fenced "
            "```typescript block. Include no fabricated test results."
        )
    else:
        system = (
            "You are a senior TypeScript engineer. Return the smallest "
            "compiler-valid TypeScript change in exactly one fenced "
            "```typescript block. Do not put prose inside the code block."
        )
    payload = {
        "model": model,
        "system": system,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": max_tokens},
        "keep_alive": "10m",
    }
    request = urllib.request.Request(
        f"{url.rstrip('/')}/api/generate",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    started = time.perf_counter()
    with urllib.request.urlopen(request, timeout=600) as response:
        result = json.loads(response.read())
    seconds = time.perf_counter() - started
    result["elapsed_seconds"] = seconds
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--ollama-url", default="http://127.0.0.1:11434")
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--max-tokens", type=int, default=512)
    parser.add_argument("--workers", type=int, default=1,
                        help="Concurrent Ollama requests; use a small bounded value")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    completed = set()
    if args.output.exists():
        for line in args.output.read_text(encoding="utf-8").splitlines():
            if line.strip():
                completed.add(json.loads(line)["task_id"])
    count = 0
    source = gzip.open(args.input, "rt", encoding="utf-8") if args.input.suffix == ".gz" else args.input.open(encoding="utf-8")
    def answer(index: int, task: dict) -> tuple[int, dict]:
        result = generate(args.ollama_url, args.model, task["prompt"], args.max_tokens, task.get("task_family", "repair"))
        return index, {
                "task_id": task["id"],
                "task": task,
                "teacher": args.model,
                "completion": result.get("response", ""),
                "prompt_tokens": result.get("prompt_eval_count"),
                "completion_tokens": result.get("eval_count"),
                "generation_seconds": result.get("elapsed_seconds"),
                "generation_duration_ns": result.get("eval_duration"),
                "created_at": time.time(),
            }

    pending: list[tuple[int, dict]] = []
    for index, line in enumerate(source):
        if index < args.offset:
            continue
        if len(pending) >= args.limit:
            break
        task = json.loads(line)
        if task["id"] not in completed:
            pending.append((index, task))
    with source, args.output.open("a", encoding="utf-8") as handle:
        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
            futures = [pool.submit(answer, index, task) for index, task in pending]
            for future in as_completed(futures):
                index, record = future.result()
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
                handle.flush()
                count += 1
                print(json.dumps({"index": index, "completed": count, "task_id": record["task_id"], "seconds": record["generation_seconds"]}), flush=True)
    print(json.dumps({"output": str(args.output), "generated": count, "resumable_records": len(completed) + count, "model": args.model}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
