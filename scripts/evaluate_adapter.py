"""Compare a local Transformers base model with a local PEFT adapter."""
from pathlib import Path
import argparse, json, time, random
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from oktopai.benchmarking import verify_output


def prompt_for(task: dict) -> str:
    return "\n".join((m["role"] + ": " + m["content"]) for m in task["messages"]) if "messages" in task else task["prompt"]


def generate(model, tokenizer, text: str, max_new_tokens: int) -> tuple[str, float, int]:
    encoded = tokenizer(text, return_tensors="pt")
    started = time.perf_counter()
    output = model.generate(**encoded, max_new_tokens=max_new_tokens, do_sample=False)
    elapsed = time.perf_counter() - started
    new_tokens = int(output.shape[-1] - encoded["input_ids"].shape[-1])
    return tokenizer.decode(output[0][encoded["input_ids"].shape[-1]:], skip_special_tokens=True), elapsed, new_tokens


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-model", type=Path, required=True)
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--tasks", type=Path, default=ROOT / "benchmarks/tasks.json")
    parser.add_argument("--domain", default="typescript")
    parser.add_argument("--max-tasks", type=int, default=2)
    parser.add_argument("--max-new-tokens", type=int, default=128)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--shuffle-seed", type=int, default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel
    except ImportError as exc:
        raise SystemExit(f"Training dependencies unavailable: {exc}")

    tasks = [t for t in json.loads(args.tasks.read_text())["tasks"] if t.get("domain") == args.domain]
    if args.shuffle_seed is not None:
        random.Random(args.shuffle_seed).shuffle(tasks)
    tasks = tasks[args.offset:args.offset + args.max_tasks]
    if not tasks:
        raise SystemExit(f"No tasks found for domain {args.domain}")
    tokenizer = AutoTokenizer.from_pretrained(str(args.base_model), local_files_only=True)
    base = AutoModelForCausalLM.from_pretrained(str(args.base_model), local_files_only=True)
    adapted = PeftModel.from_pretrained(base, str(args.adapter), local_files_only=True)
    records = []
    for task in tasks:
        text = prompt_for(task) + "\nassistant:"
        base_output, base_seconds, base_tokens = generate(base, tokenizer, text, args.max_new_tokens)
        adapter_output, adapter_seconds, adapter_tokens = generate(adapted, tokenizer, text, args.max_new_tokens)
        base_verification = verify_output(base_output, task.get("checks", {}))
        adapter_verification = verify_output(adapter_output, task.get("checks", {}))
        records.append({"task_id": task["id"], "base": {"output": base_output, "seconds": base_seconds, "new_tokens": base_tokens, "tokens_per_second": base_tokens / base_seconds if base_seconds else 0, "verification": base_verification.__dict__}, "adapter": {"output": adapter_output, "seconds": adapter_seconds, "new_tokens": adapter_tokens, "tokens_per_second": adapter_tokens / adapter_seconds if adapter_seconds else 0, "verification": adapter_verification.__dict__}})
    result = {"base_model": str(args.base_model), "adapter": str(args.adapter), "domain": args.domain, "task_count": len(records), "records": records, "warning": "This is a raw comparison, not a quality claim; apply executable validators and human review."}
    output = args.output or ROOT / f".oktopai/adapter-evaluation-{args.domain}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"output": str(output), "task_count": len(records)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
