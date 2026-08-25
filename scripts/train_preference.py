#!/usr/bin/env python3
"""Train a local LoRA preference adapter from verified chosen/rejected pairs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--base-model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-pairs", type=int, default=1000)
    parser.add_argument("--max-steps", type=int, default=300)
    parser.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    parser.add_argument("--train", action="store_true")
    args = parser.parse_args()
    if not args.train:
        print(json.dumps({"dry_run": True, "data": str(args.data), "output": str(args.output), "next": "add --train"}, indent=2))
        return 0
    import torch
    from datasets import Dataset
    from peft import LoraConfig
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from trl import DPOConfig, DPOTrainer

    if args.device == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA requested but torch.cuda.is_available() is false")
    rows = [json.loads(line) for line in args.data.read_text(encoding="utf-8").splitlines() if line][:args.max_pairs]
    if not rows:
        raise SystemExit("No preference pairs found")
    records = []
    for row in rows:
        user = "\n".join(message["content"] for message in row.get("messages", []) if message.get("role") == "user")
        records.append({"prompt": user, "chosen": row["chosen"], "rejected": row["rejected"]})
    dataset = Dataset.from_list(records)
    tokenizer = AutoTokenizer.from_pretrained(str(args.base_model), local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(str(args.base_model), local_files_only=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    lora = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, target_modules=["q_proj", "k_proj", "v_proj", "o_proj"], task_type="CAUSAL_LM")
    config = DPOConfig(output_dir=str(args.output), max_steps=args.max_steps, per_device_train_batch_size=2, gradient_accumulation_steps=4, learning_rate=5e-6, logging_steps=10, save_strategy="steps", save_steps=100, save_total_limit=2, report_to=[], max_length=1024, beta=0.1, use_cpu=args.device == "cpu")
    trainer = DPOTrainer(model=model, args=config, train_dataset=dataset, processing_class=tokenizer, peft_config=lora)
    trainer.train()
    trainer.save_model(str(args.output))
    tokenizer.save_pretrained(str(args.output))
    print(json.dumps({"output": str(args.output), "pairs": len(records), "steps": args.max_steps, "device": "cuda" if torch.cuda.is_available() and args.device == "cuda" else "cpu"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
