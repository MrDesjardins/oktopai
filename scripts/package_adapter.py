"""Write a provenance and compatibility manifest beside a PEFT adapter."""
from pathlib import Path
import argparse, hashlib, json

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--base-model", type=Path, required=True)
    parser.add_argument("--domain", required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--evaluation", type=Path, default=None)
    args = parser.parse_args()
    config = json.loads((args.adapter / "adapter_config.json").read_text())
    weights = args.adapter / "adapter_model.safetensors"
    manifest = {"schema_version": "1.0", "artifact": args.adapter.name, "domain": args.domain, "format": "peft-lora", "runtime": "transformers-peft", "ollama_compatible": False, "compatibility_note": "This adapter targets the downloaded 0.5B Transformers base and must not be attached to the unrelated 7B Ollama GGUF model.", "base_model": str(args.base_model), "base_model_sha256": sha256(args.base_model / "model.safetensors"), "adapter_sha256": sha256(weights), "adapter_config": config, "dataset": str(args.dataset), "dataset_sha256": sha256(args.dataset), "evaluation": str(args.evaluation) if args.evaluation else None, "license_review_required": True}
    path = args.adapter / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"manifest": str(path), "adapter_sha256": manifest["adapter_sha256"], "ollama_compatible": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
