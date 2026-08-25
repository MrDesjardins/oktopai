"""Run the versioned oktopai benchmark against local Ollama models.

Examples:
  PYTHONPATH=src python3 scripts/run_benchmark.py --route-only
  PYTHONPATH=src python3 scripts/run_benchmark.py --model qwen2.5-coder:7b
  PYTHONPATH=src python3 scripts/run_benchmark.py --all-installed --limit 2
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from oktopai.benchmarking import load_tasks, save_jsonl, verify_output
from oktopai.experts import ExpertRegistry
from oktopai.router import Router
from oktopai.runtimes.base import RuntimeUnavailable
from oktopai.runtimes.ollama import OllamaRuntime
from oktopai.signals import detect_signals

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", type=Path, default=ROOT / "benchmarks/tasks.json")
    parser.add_argument("--model", action="append", help="Model to benchmark; repeat for a comparison")
    parser.add_argument("--all-installed", action="store_true")
    parser.add_argument("--route-only", action="store_true")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--keep-alive", type=int, default=300)
    args = parser.parse_args()
    registry = ExpertRegistry.from_toml(ROOT / "config/experts.toml")
    tasks = load_tasks(args.tasks)
    if args.limit: tasks = tasks[:args.limit]
    runtime = OllamaRuntime()
    if args.all_installed:
        try: models = runtime.list_models()
        except RuntimeUnavailable as exc: print(exc); return 2
    else:
        models = args.model or ["qwen2.5-coder:7b"]
    records = []
    route_start = time.perf_counter()
    for task in tasks:
        decision = Router(registry).route(task["prompt"], detect_signals(task["prompt"], task.get("file_path"), task.get("file_text", task["prompt"]), ROOT))
        records.append({"task_id": task["id"], "expected_expert": task["expert"], "selected_expert": decision.selected, "routing_correct": decision.selected == task["expert"], "routing_score": decision.score, "routing_confidence": decision.confidence})
    routing_ms = (time.perf_counter() - route_start) * 1000
    if not args.route_only:
        for model in models:
            for record, task in zip(records, tasks):
                expert = registry.get(record["selected_expert"])
                started = time.perf_counter()
                try:
                    result = runtime.generate(model, [{"role":"system", "content":expert.system_prompt}, {"role":"user", "content":task["prompt"]}], args.keep_alive)
                    verification = verify_output(result.text, task.get("checks", {}))
                    record.setdefault("runs", []).append({"model":model,"cold":result.cold,"load_ms":result.load_ms,"generation_ms":result.generation_ms,"prompt_tokens":result.prompt_tokens,"completion_tokens":result.completion_tokens,"tokens_per_second":result.tokens_per_second,"total_ms":(time.perf_counter()-started)*1000,"output":result.text,"verification":verification.__dict__})
                    print(f"{model} / {task['id']}: {verification.status} / {result.generation_ms:.0f} ms")
                except RuntimeUnavailable as exc:
                    record.setdefault("runs", []).append({"model":model,"error":str(exc)})
                    print(f"{model} / {task['id']}: ERROR {exc}")
    report = {"schema_version":"1.0","tasks_file":str(args.tasks),"models":models,"route_only":args.route_only,"routing_latency_ms":routing_ms,"routing_accuracy":sum(r["routing_correct"] for r in records)/len(records),"records":records,"generated_at":time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    output_dir = ROOT / ".oktopai"; output_dir.mkdir(exist_ok=True)
    (output_dir / "benchmark-report.json").write_text(json.dumps(report, indent=2))
    save_jsonl(output_dir / "benchmark-raw.jsonl", [run | {"task_id": record["task_id"]} for record in records for run in record.get("runs", []) if "output" in run])
    print(json.dumps({k:report[k] for k in ("models","route_only","routing_latency_ms","routing_accuracy")}, indent=2))
    print(f"Saved {output_dir / 'benchmark-report.json'}")
    return 0

if __name__ == "__main__": raise SystemExit(main())
