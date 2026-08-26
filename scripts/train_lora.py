"""Train a specialist LoRA adapter when the optional stack is installed.

The default is a dry-run. This script never downloads a base model implicitly;
the caller must provide a local model path or an explicitly approved model id.
"""
from pathlib import Path
import argparse, json, os, sys

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--data",type=Path,required=True); parser.add_argument("--base-model",required=True); parser.add_argument("--output",type=Path,required=True); parser.add_argument("--train",action="store_true"); parser.add_argument("--epochs",type=float,default=2.0); parser.add_argument("--max-steps",type=int,default=-1,help="Bound CPU experiments; -1 uses all epoch steps"); parser.add_argument("--loss-mode",choices=["completion-only","full"],default="completion-only"); parser.add_argument("--no-eval",action="store_true",help="Skip validation during bounded throughput experiments"); parser.add_argument("--resume",action="store_true",help="Resume the latest Trainer checkpoint in --output"); parser.add_argument("--device",choices=["auto","cpu","cuda"],default="auto",help="Select training device; auto uses CUDA only when visible"); args=parser.parse_args()
    if not args.train:
        print(json.dumps({"dry_run":True,"base_model":args.base_model,"data":str(args.data),"output":str(args.output),"next":"re-run with --train after installing training requirements and verifying model/data licenses"},indent=2)); return 0
    try:
        from datasets import load_dataset
        from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments
        import torch
        from peft import LoraConfig, get_peft_model
    except ImportError as exc:
        print(f"Training dependencies are unavailable: {exc}. Run scripts/install_training_stack.py --install", file=sys.stderr); return 2
    cache = ROOT / ".oktopai" / "hf-cache"
    cache.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("HF_DATASETS_CACHE", str(cache / "datasets"))
    os.environ.setdefault("TRANSFORMERS_CACHE", str(cache / "transformers"))
    if args.device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("--device cuda requested, but torch.cuda.is_available() is false")
    if args.device == "cpu":
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
    all_data=load_dataset("json",data_files=str(args.data),split="train")
    if "split" in all_data.column_names:
        train_data=all_data.filter(lambda item: item["split"] == "train")
        validation_data=all_data.filter(lambda item: item["split"] == "validation")
    else:
        train_data=all_data
        validation_data=None
    if len(train_data) == 0:
        raise ValueError("Training dataset has no records with split='train'")
    tokenizer=AutoTokenizer.from_pretrained(args.base_model,local_files_only=True)
    use_bf16 = bool(args.device != "cpu" and torch.cuda.is_available() and torch.cuda.is_bf16_supported())
    model_kwargs = {"local_files_only": True}
    if use_bf16:
        model_kwargs["torch_dtype"] = torch.bfloat16
    model=AutoModelForCausalLM.from_pretrained(args.base_model,**model_kwargs)
    if use_bf16:
        model.gradient_checkpointing_enable()
        model.enable_input_require_grads()
    config=LoraConfig(r=16,lora_alpha=32,lora_dropout=0.05,target_modules=["q_proj","k_proj","v_proj","o_proj"],task_type="CAUSAL_LM")
    model=get_peft_model(model,config)
    def tokenize(item):
        messages=item["messages"]
        assistant={"role":"assistant","content":item["completion"]}
        if getattr(tokenizer, "chat_template", None):
            prompt=tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            text=tokenizer.apply_chat_template(messages+[assistant], tokenize=False, add_generation_prompt=False)
        else:
            prompt="\n".join(message["role"]+": "+message["content"] for message in messages)+"\nassistant: "
            text=prompt+item["completion"]
        encoded=tokenizer(text,truncation=True,max_length=2048)
        prompt_length=len(tokenizer(prompt,truncation=True,max_length=2048)["input_ids"])
        encoded["labels"]=list(encoded["input_ids"])
        if args.loss_mode=="completion-only":
            encoded["labels"]=[-100 if index < prompt_length else token for index, token in enumerate(encoded["labels"])]
        return encoded
    def collate(features):
        labels=[feature.pop("labels") for feature in features]
        batch=tokenizer.pad(features,padding=True,return_tensors="pt")
        width=batch["input_ids"].shape[1]
        batch["labels"]=torch.tensor([value+[-100]*(width-len(value)) for value in labels],dtype=torch.long)
        return batch
    tokenized=train_data.map(tokenize)
    tokenized_validation=validation_data.map(tokenize) if validation_data is not None and len(validation_data) else None
    trainer=Trainer(model=model,args=TrainingArguments(output_dir=str(args.output),num_train_epochs=args.epochs,max_steps=args.max_steps,per_device_train_batch_size=1,gradient_accumulation_steps=8,logging_steps=10,save_strategy="steps",save_steps=100,save_total_limit=3,eval_strategy="epoch" if tokenized_validation is not None and not args.no_eval else "no",bf16=use_bf16,gradient_checkpointing=use_bf16,report_to=[]),train_dataset=tokenized,eval_dataset=None if args.no_eval else tokenized_validation,data_collator=collate)
    trainer.train(resume_from_checkpoint=args.resume); model.save_pretrained(args.output); tokenizer.save_pretrained(args.output); print(f"Saved adapter to {args.output}; device={'cuda' if torch.cuda.is_available() else 'cpu'}"); return 0
if __name__ == "__main__": raise SystemExit(main())
