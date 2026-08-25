"""Convert a merged local Transformers checkpoint to GGUF via llama.cpp.

The converter is intentionally external and never downloaded implicitly.
"""
from pathlib import Path
import argparse, json, subprocess, sys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--llama-cpp", type=Path, required=True, help="Local llama.cpp checkout")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--quantization", default="q4_k_m")
    parser.add_argument("--export", action="store_true")
    args = parser.parse_args()
    converter = args.llama_cpp / "convert_hf_to_gguf.py"
    quantizer = args.llama_cpp / "llama-quantize"
    if not quantizer.exists():
        quantizer = args.llama_cpp / "build/bin/llama-quantize"
    plan = {"model": str(args.model), "llama_cpp": str(args.llama_cpp), "output": str(args.output), "quantization": args.quantization, "converter_exists": converter.exists(), "quantizer_exists": quantizer.exists(), "export": args.export}
    if not args.export:
        print(json.dumps(plan, indent=2)); return 0
    if not converter.exists() or not quantizer.exists():
        print(json.dumps(plan, indent=2), file=sys.stderr)
        print("Expected convert_hf_to_gguf.py and llama-quantize in the local llama.cpp checkout", file=sys.stderr)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    f16 = args.output.with_name(args.output.stem + ".f16.gguf")
    python = Path(__file__).resolve().parents[1] / ".venv-training/bin/python"
    interpreter = str(python) if python.exists() else sys.executable
    subprocess.run([interpreter, str(converter), str(args.model), "--outfile", str(f16), "--outtype", "f16"], check=True)
    subprocess.run([str(quantizer), str(f16), str(args.output), args.quantization], check=True)
    print(json.dumps({**plan, "exported": True, "f16": str(f16)}, indent=2)); return 0


if __name__ == "__main__": raise SystemExit(main())
