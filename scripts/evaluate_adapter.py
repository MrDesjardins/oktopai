"""Compare a local Transformers base model with a local PEFT adapter."""
from pathlib import Path
import argparse, json, time, random
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from oktopai.benchmarking import verify_output


def prompt_for(task: dict, tokenizer) -> str:
    messages = task.get("messages") or [{"role": "user", "content": task["prompt"]}]
    if getattr(tokenizer, "chat_template", None):
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    return "\n".join((m["role"] + ": " + m["content"]) for m in messages) + "\nassistant:"


def generate(model, tokenizer, text: str, max_new_tokens: int, device: str, max_seconds: float | None = None) -> tuple[str, float, int]:
    encoded = {key: value.to(device) for key, value in tokenizer(text, return_tensors="pt").items()}
    started = time.perf_counter()
    generation = {"max_new_tokens": max_new_tokens, "do_sample": False}
    if max_seconds is not None:
        generation["max_time"] = max_seconds
    output = model.generate(**encoded, **generation)
    elapsed = time.perf_counter() - started
    new_tokens = int(output.shape[-1] - encoded["input_ids"].shape[-1])
    return tokenizer.decode(output[0][encoded["input_ids"].shape[-1]:], skip_special_tokens=True), elapsed, new_tokens


def write_report(path: Path, base_model: Path, adapter: Path, domain: str, records: list[dict], complete: bool) -> None:
    result = {"base_model": str(base_model.resolve()), "adapter": str(adapter.resolve()), "domain": domain,
              "task_count": len(records), "records": records, "complete": complete,
              "warning": "This is a raw comparison, not a quality claim; apply executable validators and human review."}
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(result, indent=2) + "\n")
    temporary.replace(path)


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
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--resume", action="store_true", help="Resume completed records from the output checkpoint")
    parser.add_argument("--base-report", type=Path, default=None,
                        help="Reuse base outputs from a complete fixed-suite report and generate only the adapter")
    parser.add_argument("--max-seconds", type=float, default=None, help="Bound one generation to prevent pathological hangs")
    args = parser.parse_args()
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel
        import torch
    except ImportError as exc:
        raise SystemExit(f"Training dependencies unavailable: {exc}")

    tasks = [t for t in json.loads(args.tasks.read_text())["tasks"] if t.get("domain") == args.domain]
    if args.shuffle_seed is not None:
        random.Random(args.shuffle_seed).shuffle(tasks)
    tasks = tasks[args.offset:args.offset + args.max_tasks]
    if not tasks:
        raise SystemExit(f"No tasks found for domain {args.domain}")
    if args.device == "cuda" and not torch.cuda.is_available():
        raise SystemExit("--device cuda requested, but CUDA is unavailable")
    device = "cuda" if args.device == "auto" and torch.cuda.is_available() or args.device == "cuda" else "cpu"
    tokenizer = AutoTokenizer.from_pretrained(str(args.base_model), local_files_only=True)
    cached_base = {}
    if args.base_report is not None:
        report = json.loads(args.base_report.read_text())
        if report.get("base_model") != str(args.base_model.resolve()):
            raise SystemExit("--base-report base_model does not match --base-model")
        cached_base = {row["task_id"]: row["base"] for row in report.get("records", [])}
        missing = [task["id"] for task in tasks if task["id"] not in cached_base]
        if missing:
            raise SystemExit(f"--base-report is missing {len(missing)} requested task IDs")
    # Keep independent model instances. PeftModel wraps and may mutate the
    # supplied base object; sharing it makes the base-vs-adapter comparison
    # invalid and can produce identical outputs for both labels.
    base = None if cached_base else AutoModelForCausalLM.from_pretrained(str(args.base_model), local_files_only=True).to(device)
    adapter_base = AutoModelForCausalLM.from_pretrained(str(args.base_model), local_files_only=True).to(device)
    adapted = PeftModel.from_pretrained(adapter_base, str(args.adapter), local_files_only=True)
    output = args.output or ROOT / f".oktopai/adapter-evaluation-{args.domain}.json"
    records = []
    if args.resume and output.exists():
        try:
            checkpoint = json.loads(output.read_text())
            expected_base = str(args.base_model.resolve())
            expected_adapter = str(args.adapter.resolve())
            if (checkpoint.get("base_model") != expected_base
                    or checkpoint.get("adapter") != expected_adapter
                    or checkpoint.get("domain") != args.domain):
                raise SystemExit("Refusing to resume: existing report metadata does not match the requested base, adapter, or domain")
            records = checkpoint.get("records", [])
        except (OSError, json.JSONDecodeError, TypeError):
            records = []
    completed_ids = {record.get("task_id") for record in records}
    for task in tasks:
        if task["id"] in completed_ids:
            continue
        text = prompt_for(task, tokenizer)
        if cached_base:
            cached = cached_base[task["id"]]
            base_output, base_seconds, base_tokens = cached["output"], cached["seconds"], cached["new_tokens"]
            base_verification = SimpleNamespace(**cached["verification"])
        else:
            base_output, base_seconds, base_tokens = generate(base, tokenizer, text, args.max_new_tokens, device, args.max_seconds)
            base_verification = verify_output(base_output, task.get("checks", {}))
        adapter_output, adapter_seconds, adapter_tokens = generate(adapted, tokenizer, text, args.max_new_tokens, device, args.max_seconds)
        adapter_verification = verify_output(adapter_output, task.get("checks", {}))
        records.append({"task_id": task["id"], "base": {"output": base_output, "seconds": base_seconds, "new_tokens": base_tokens, "tokens_per_second": base_tokens / base_seconds if base_seconds else 0, "verification": base_verification.__dict__}, "adapter": {"output": adapter_output, "seconds": adapter_seconds, "new_tokens": adapter_tokens, "tokens_per_second": adapter_tokens / adapter_seconds if adapter_seconds else 0, "verification": adapter_verification.__dict__}})
        write_report(output, args.base_model, args.adapter, args.domain, records, complete=False)
    write_report(output, args.base_model, args.adapter, args.domain, records, complete=True)
    print(json.dumps({"output": str(output), "task_count": len(records)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
