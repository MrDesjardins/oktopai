#!/usr/bin/env python3
"""Evaluate structured trajectory emission and replay for a local adapter."""

from __future__ import annotations

import argparse
import gc
import json
import time
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]

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


def prompt_for(record: dict, tokenizer) -> str:
    messages = record.get("messages") or [{"role": "user", "content": json.dumps({
        "task": record["task"], "repository_facts": record["repository_facts"],
        "repository_files": record.get("repository_files", {}),
        "trajectory_contract": TRAJECTORY_CONTRACT,
    }, ensure_ascii=False, separators=(",", ":"))}]
    if getattr(tokenizer, "chat_template", None):
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    return "\n".join(m["role"] + ": " + m["content"] for m in messages) + "\nassistant: "


def generate(model, tokenizer, prompt: str, device: str, max_new_tokens: int) -> tuple[str, float, int]:
    encoded = {key: value.to(device) for key, value in tokenizer(prompt, return_tensors="pt").items()}
    started = time.perf_counter()
    output = model.generate(**encoded, max_new_tokens=max_new_tokens, do_sample=False)
    elapsed = time.perf_counter() - started
    count = int(output.shape[-1] - encoded["input_ids"].shape[-1])
    text = tokenizer.decode(output[0][encoded["input_ids"].shape[-1]:], skip_special_tokens=True)
    return text, elapsed, count


def parse_completion(text: str) -> tuple[dict | None, str | None]:
    candidate = text.strip()
    if "```" in candidate:
        parts = candidate.split("```")
        candidate = next((part.strip().removeprefix("json").strip() for part in parts if part.strip().startswith("{")), candidate)
    try:
        value = json.loads(candidate)
    except json.JSONDecodeError as exc:
        return None, f"json-parse:{exc.msg}"
    if not isinstance(value, dict):
        return None, "json-not-object"
    return value, None


def summarize_results(results: list[dict], label: str) -> dict:
    """Aggregate protocol metrics by repository task family."""
    families: dict[str, dict[str, int]] = {}
    for result in results:
        family = result.get("family", "unknown")
        summary = families.setdefault(family, {"records": 0, "parseable": 0, "raw_contract_valid": 0, "contract_valid": 0, "normalization_applied": 0})
        value = result[label]
        summary["records"] += 1
        summary["parseable"] += int(value.get("parsed") is not None)
        summary["raw_contract_valid"] += int(value.get("raw_contract_valid", False))
        summary["contract_valid"] += int(value.get("contract_valid", False))
        summary["normalization_applied"] += int(value.get("normalization_applied", False))
    return families


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-model", type=Path, required=True)
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-new-tokens", type=int, default=1024)
    parser.add_argument("--split", default="validation")
    parser.add_argument("--limit", type=int, default=None, help="Optionally evaluate only the first N records (smoke test).")
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    args = parser.parse_args()
    try:
        import torch
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from oktopai.trajectory import normalize_trajectory, validate_trajectory
    except ImportError as exc:
        raise SystemExit(f"evaluation dependencies unavailable: {exc}")
    if args.device == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA requested but unavailable")
    records = [json.loads(line) for line in args.data.read_text(encoding="utf-8").splitlines() if line.strip()]
    records = [row for row in records if row.get("split") == args.split]
    if args.limit is not None:
        records = records[:args.limit]
    if not records:
        raise SystemExit(f"trajectory evaluation input contains no records with split={args.split!r}")
    device = args.device
    tokenizer = AutoTokenizer.from_pretrained(str(args.base_model), local_files_only=True)
    prompts = {record["id"]: prompt_for(record, tokenizer) for record in records}
    base = AutoModelForCausalLM.from_pretrained(str(args.base_model), local_files_only=True).to(device)
    base_outputs = {}
    for record in records:
        base_outputs[record["id"]] = generate(base, tokenizer, prompts[record["id"]], device, args.max_new_tokens)
    del base
    gc.collect()
    if device == "cuda":
        torch.cuda.empty_cache()
    adapter_base = AutoModelForCausalLM.from_pretrained(str(args.base_model), local_files_only=True).to(device)
    adapter = PeftModel.from_pretrained(adapter_base, str(args.adapter), local_files_only=True)
    results = []
    generated_records = []
    for record in records:
        base_text, base_seconds, base_tokens = base_outputs[record["id"]]
        adapter_text, adapter_seconds, adapter_tokens = generate(adapter, tokenizer, prompts[record["id"]], device, args.max_new_tokens)
        result = {"id": record["id"], "family": record.get("repository_facts", {}).get("family", "unknown"), "base": {"output": base_text, "seconds": base_seconds, "new_tokens": base_tokens},
                  "adapter": {"output": adapter_text, "seconds": adapter_seconds, "new_tokens": adapter_tokens}}
        for label, text in (("base", base_text), ("adapter", adapter_text)):
            parsed, error = parse_completion(text)
            result[label]["parse_error"] = error
            result[label]["parsed"] = parsed
            if parsed is not None:
                raw_candidate = {key: record[key] for key in ("id", "domain", "split", "task", "repository_facts", "repository_files", "provenance") if key in record}
                raw_candidate.update({"trajectory": parsed.get("trajectory"), "final": parsed.get("final"), "verification": {"status": "pending-replay"}})
                raw_issues = validate_trajectory(raw_candidate)
                candidate = normalize_trajectory(raw_candidate)
                issues = validate_trajectory(candidate)
                result[label]["raw_contract_valid"] = not raw_issues
                result[label]["raw_contract_issues"] = [issue.__dict__ for issue in raw_issues]
                result[label]["normalization_applied"] = candidate != raw_candidate
                result[label]["contract_valid"] = not issues
                result[label]["contract_issues"] = [issue.__dict__ for issue in issues]
                if label == "adapter" and not issues:
                    generated_records.append(candidate)
            else:
                result[label]["contract_valid"] = False
                result[label]["contract_issues"] = [{"code": "parse_error", "message": error}]
        results.append(result)
    report = {"base_model": str(args.base_model.resolve()), "adapter": str(args.adapter.resolve()),
              "data": str(args.data.resolve()), "records": results, "generated_adapter_records": len(generated_records),
              "family_summary": {"base": summarize_results(results, "base"), "adapter": summarize_results(results, "adapter")},
              "max_new_tokens": args.max_new_tokens, "device": device,
              "warning": "Tiny held-out trajectory split; diagnostic only."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    candidate_path = args.output.with_name(args.output.stem + "-replay.jsonl")
    candidate_path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in generated_records) + ("\n" if generated_records else ""), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "records": len(results), "adapter_contract_valid": sum(r["adapter"].get("contract_valid", False) for r in results), "replay_input": str(candidate_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
