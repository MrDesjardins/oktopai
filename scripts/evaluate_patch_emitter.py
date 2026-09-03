#!/usr/bin/env python3
"""Evaluate a bounded patch-emitter adapter against held-out repair targets."""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
import time
from pathlib import Path

from oktopai.trajectory import apply_replacements


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


def prompt_for(record: dict, tokenizer) -> str:
    messages = record["messages"]
    if getattr(tokenizer, "chat_template", None):
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    return "\n".join(m["role"] + ": " + m["content"] for m in messages) + "\nassistant: "


def compiles_after_patch(source_record: dict, path: str, updated: str, node_modules: Path) -> bool:
    with tempfile.TemporaryDirectory(prefix="oktopai-patch-emitter-compile-") as directory:
        project = Path(directory)
        for source_path, content in source_record.get("repository_files", {}).items():
            target = project / source_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(updated if source_path == path else content, encoding="utf-8")
        (project / "node_modules").symlink_to(node_modules, target_is_directory=True)
        result = subprocess.run(
            [str(node_modules / ".bin/tsc"), "--noEmit", "--incremental", "false", "--pretty", "false"],
            cwd=project, capture_output=True, text=True, check=False,
        )
    return result.returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-model", type=Path, required=True)
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True, help="Patch-emitter SFT-shaped prompts.")
    parser.add_argument("--source-data", type=Path, required=True, help="Converted records containing snapshots and gold edits.")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-new-tokens", type=int, default=512)
    parser.add_argument("--split", default="validation")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--compile", action="store_true", help="Run the repository TypeScript compiler after each patch.")
    parser.add_argument("--node-modules", type=Path, default=Path("/home/miste/code/desktop-ai-companion/apps/desktop/node_modules"))
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    args = parser.parse_args()
    try:
        import torch
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as exc:
        raise SystemExit(f"evaluation dependencies unavailable: {exc}")
    if args.device == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA requested but unavailable")
    prompts = [json.loads(line) for line in args.data.read_text(encoding="utf-8").splitlines() if line.strip()]
    prompts = [row for row in prompts if row.get("split") == args.split]
    if args.limit is not None:
        prompts = prompts[:args.limit]
    sources = {row["id"]: row for row in (json.loads(line) for line in args.source_data.read_text(encoding="utf-8").splitlines() if line.strip())}
    tokenizer = AutoTokenizer.from_pretrained(str(args.base_model), local_files_only=True)
    base = AutoModelForCausalLM.from_pretrained(str(args.base_model), local_files_only=True).to(args.device)
    model = PeftModel.from_pretrained(base, str(args.adapter), local_files_only=True)
    results = []
    for record in prompts:
        source_record = sources.get(record["id"])
        started = time.perf_counter()
        encoded = tokenizer(prompt_for(record, tokenizer), return_tensors="pt")
        encoded = {key: value.to(args.device) for key, value in encoded.items()}
        output = model.generate(**encoded, max_new_tokens=args.max_new_tokens, do_sample=False)
        text = tokenizer.decode(output[0][encoded["input_ids"].shape[-1]:], skip_special_tokens=True)
        parsed, error = parse_completion(text)
        result = {"id": record["id"], "output": text, "new_tokens": int(output.shape[-1] - encoded["input_ids"].shape[-1]), "seconds": time.perf_counter() - started,
                  "parse_error": error, "contract_valid": False, "replay_valid": False, "compiled": False, "exact_fix": False, "issues": []}
        if parsed is not None:
            path = parsed.get("path")
            replacements = parsed.get("replacements")
            if not isinstance(path, str) or not isinstance(replacements, list) or not replacements:
                result["issues"].append("missing path or replacements")
            elif source_record is None:
                result["issues"].append("missing source record")
            else:
                source = source_record.get("repository_files", {}).get(path)
                if not isinstance(source, str):
                    result["issues"].append("target path absent from source snapshot")
                else:
                    try:
                        updated = apply_replacements(source, replacements)
                    except ValueError as exc:
                        result["issues"].append(str(exc))
                    else:
                        result["contract_valid"] = True
                        result["replay_valid"] = True
                        if args.compile:
                            result["compiled"] = compiles_after_patch(source_record, path, updated, args.node_modules)
                            if not result["compiled"]:
                                result["issues"].append("compiler replay failed")
                        gold_edit = next(event for event in source_record["trajectory"] if event.get("event") == "edit")
                        gold_args = gold_edit["args"]
                        gold_updated = apply_replacements(source, gold_args["replacements"])
                        result["exact_fix"] = updated == gold_updated
                        if not result["exact_fix"]:
                            result["issues"].append("replacement result differs from gold repair")
        results.append(result)
    report = {"base_model": str(args.base_model.resolve()), "adapter": str(args.adapter.resolve()), "data": str(args.data.resolve()),
              "source_data": str(args.source_data.resolve()), "records": results,
              "summary": {"records": len(results), "contract_valid": sum(r["contract_valid"] for r in results),
                          "replay_valid": sum(r["replay_valid"] for r in results), "compiled": sum(r["compiled"] for r in results),
                          "exact_fix": sum(r["exact_fix"] for r in results)},
              "max_new_tokens": args.max_new_tokens, "device": args.device, "warning": "Diagnostic held-out patch-emitter evaluation; no promotion."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), **report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
