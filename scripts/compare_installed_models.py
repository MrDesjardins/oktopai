"""Compare already-installed Ollama models on identical local coding tasks.

This script never pulls models and never contacts a cloud provider. It uses the
local Ollama API and writes raw outputs for later human or automated scoring.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from oktopai.runtimes.ollama import OllamaRuntime

TASKS = [
    {
        "id": "typescript-generic",
        "expert": "typescript",
        "prompt": "Fix this TypeScript generic issue. Explain the error and provide the smallest correct change.\n\n```ts\nfunction pluck<T, K extends keyof T>(items: T[], key: K): T[K][] {\n  return items.map(item => item[key]);\n}\n\nconst names = pluck([{ name: 'Ada' }], 'missing');\n```",
    },
    {
        "id": "react-rerender",
        "expert": "react",
        "prompt": "Why does this React component rerender unnecessarily? Give a precise explanation and a minimal fix.\n\n```tsx\nfunction List({ items, onSelect }) {\n  const sorted = items.slice().sort();\n  return <Items items={sorted} onSelect={(item) => onSelect(item)} />;\n}\n```",
    },
    {
        "id": "next-boundary",
        "expert": "nextjs",
        "prompt": "Identify the Next.js server/client component problem and provide a minimal correction.\n\n```tsx\n// app/page.tsx\nimport { useState } from 'react';\n\nexport default function Page() {\n  const [open, setOpen] = useState(false);\n  return <button onClick={() => setOpen(!open)}>{String(open)}</button>;\n}\n```",
    },
    {
        "id": "test-generation",
        "expert": "testing",
        "prompt": "Write a focused Vitest test for this function, including one edge case. Do not invent external dependencies.\n\n```ts\nexport function divide(a: number, b: number): number {\n  if (b === 0) throw new Error('division by zero');\n  return a / b;\n}\n```",
    },
]

SYSTEM = {
    "typescript": "You are a TypeScript specialist. Be precise about compiler behavior. Return a concise explanation and corrected code.",
    "react": "You are a React specialist. Focus on actual render identity, hooks, props, and minimal fixes. Avoid generic lists.",
    "nextjs": "You are a Next.js specialist. Focus on App Router server/client boundaries and current framework conventions.",
    "testing": "You are a testing specialist. Produce executable, focused tests and state assumptions explicitly.",
}

def main() -> int:
    runtime = OllamaRuntime()
    installed = runtime.list_models()
    output_dir = ROOT / ".oktopai"
    output_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for model in installed:
        for task in TASKS:
            messages = [
                {"role": "system", "content": SYSTEM[task["expert"]]},
                {"role": "user", "content": task["prompt"]},
            ]
            started = time.perf_counter()
            try:
                result = runtime.generate(model, messages, keep_alive=300)
                records.append({
                    "model": model,
                    "task_id": task["id"],
                    "expert": task["expert"],
                    "cold": result.cold,
                    "load_ms": result.load_ms,
                    "generation_ms": result.generation_ms,
                    "total_ms": (time.perf_counter() - started) * 1000,
                    "output": result.text,
                })
                print(f"{model} / {task['id']}: {result.generation_ms:.0f} ms")
            except Exception as exc:  # keep the comparison useful if one model fails
                records.append({"model": model, "task_id": task["id"], "expert": task["expert"], "error": str(exc)})
                print(f"{model} / {task['id']}: ERROR {exc}")
    report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "models": installed,
        "tasks": [{"id": task["id"], "expert": task["expert"]} for task in TASKS],
        "records": records,
        "note": "Raw local outputs. No automated quality ranking is claimed.",
    }
    path = output_dir / "installed-model-comparison.json"
    path.write_text(json.dumps(report, indent=2))
    print(f"Saved {path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
