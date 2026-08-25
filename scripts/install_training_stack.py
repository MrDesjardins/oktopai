"""Provision the optional training environment.

Dry-run by default. Use --install only after reviewing disk/RAM impact. This
creates .venv-training in the repository and never installs system-wide.
"""
from pathlib import Path
import argparse, subprocess, sys

ROOT=Path(__file__).resolve().parents[1]
def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--install",action="store_true"); parser.add_argument("--python",default=sys.executable); args=parser.parse_args()
    venv=ROOT/".venv-training"; pip=venv/"bin/pip"; python=venv/"bin/python"
    commands=[[args.python,"-m","venv",str(venv)],[str(pip),"install","--upgrade","pip"],[str(pip),"install","-r",str(ROOT/"training/requirements.txt")]]
    print("Training stack: optional PyTorch/Transformers/PEFT/TRL environment")
    print("Impact: downloads Python packages, PyTorch runtime, and potentially several GB of cache/storage; no base model is downloaded by this script.")
    if not args.install:
        print("Dry run. Re-run with --install to create .venv-training and install training packages.")
        for command in commands: print(" "," ".join(command))
        return 0
    for command in commands: subprocess.run(command,check=True)
    print(f"Installed training environment at {venv}")
if __name__ == "__main__": main()
