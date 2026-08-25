"""Merge a PEFT adapter into its exact local Transformers base model.

This creates a standalone Transformers checkpoint. It does not convert to GGUF
and it never downloads models implicitly.
"""
from pathlib import Path
import argparse, json, sys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-model", type=Path, required=True)
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--merge", action="store_true")
    args = parser.parse_args()
    summary = {"base_model": str(args.base_model), "adapter": str(args.adapter), "output": str(args.output), "merge": args.merge, "next": "re-run with --merge to write a standalone checkpoint"}
    if not args.merge:
        print(json.dumps(summary, indent=2))
        return 0
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel
    except ImportError as exc:
        print(f"Training dependencies unavailable: {exc}", file=sys.stderr)
        return 2
    if not (args.base_model / "config.json").exists():
        print(f"Base model is not a local Transformers checkpoint: {args.base_model}", file=sys.stderr)
        return 2
    if not (args.adapter / "adapter_config.json").exists():
        print(f"Adapter is not a PEFT artifact: {args.adapter}", file=sys.stderr)
        return 2
    args.output.mkdir(parents=True, exist_ok=True)
    tokenizer = AutoTokenizer.from_pretrained(str(args.base_model), local_files_only=True)
    base = AutoModelForCausalLM.from_pretrained(str(args.base_model), local_files_only=True)
    adapter = PeftModel.from_pretrained(base, str(args.adapter), local_files_only=True)
    merged = adapter.merge_and_unload()
    merged.save_pretrained(str(args.output), safe_serialization=True)
    tokenizer.save_pretrained(str(args.output))
    summary.update({"merged": True, "runtime": "transformers", "gguf_exported": False})
    (args.output / "export-status.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
