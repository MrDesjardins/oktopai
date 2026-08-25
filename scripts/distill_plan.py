"""Create a reproducible distillation plan; performs no training or downloads."""
from pathlib import Path
import argparse, json, subprocess, sys, time

ROOT=Path(__file__).resolve().parents[1]
def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--domain",required=True); parser.add_argument("--data",type=Path); parser.add_argument("--base-model",default="qwen2.5-coder:7b"); parser.add_argument("--student",default="1-3B student"); parser.add_argument("--output",type=Path,default=ROOT/".oktopai/distillation-plan.json"); args=parser.parse_args()
    if args.data is None: args.data=ROOT/".oktopai/datasets"/(args.domain+".jsonl")
    count=sum(1 for line in args.data.read_text().splitlines() if line.strip() and json.loads(line).get("domain") == args.domain) if args.data.exists() else 0
    training_python=ROOT/".venv-training/bin/python"; training_python=str(training_python if training_python.exists() else sys.executable)
    try:
        probe=subprocess.run([training_python,"-c","import torch,transformers,datasets,accelerate,peft,trl"],capture_output=True,text=True,timeout=30); training_available=probe.returncode==0
    except (OSError,subprocess.TimeoutExpired): training_available=False
    plan={"schema_version":"1.0","domain":args.domain,"base_model":args.base_model,"student_target":args.student,"dataset":str(args.data),"candidate_count":count,"training_python":training_python,"training_stack_available":training_available,"steps":["expand verified domain dataset","split by repository/task family","train LoRA/QLoRA adapter","evaluate held-out executable tasks","quantize student","package artifact manifest"],"created_at":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())}
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(plan,indent=2)); print(json.dumps(plan,indent=2))
if __name__ == "__main__": main()
