"""Explicitly download a Transformers-compatible training base.

Dry-run by default. A model download is separate from Ollama inference and
must be explicitly requested with --download.
"""
from pathlib import Path
import argparse, json

ROOT=Path(__file__).resolve().parents[1]
def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--model",default="Qwen/Qwen2.5-Coder-0.5B-Instruct"); parser.add_argument("--output",type=Path,default=ROOT/".oktopai/hf-bases/qwen2.5-coder-0.5b"); parser.add_argument("--download",action="store_true"); args=parser.parse_args()
    print(json.dumps({"model":args.model,"output":str(args.output),"download":args.download,"impact":"A Transformers checkpoint may consume roughly 1–3 GB depending on precision/cache. This is separate from the existing GGUF Ollama model."},indent=2))
    if not args.download: print("Dry run. Re-run with --download after reviewing model license, disk, and network impact."); return 0
    try:
        from huggingface_hub import snapshot_download
    except ImportError: print("Install the training stack first: python3 scripts/install_training_stack.py --install"); return 2
    args.output.mkdir(parents=True,exist_ok=True); snapshot_download(args.model,local_dir=str(args.output)); print(f"Downloaded {args.model} to {args.output}"); return 0
if __name__ == "__main__": raise SystemExit(main())
