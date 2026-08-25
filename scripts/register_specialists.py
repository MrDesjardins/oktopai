"""Register local specialist Modelfiles without creating or downloading models."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from oktopai.artifacts import Artifact, ArtifactRegistry

ROOT = Path(__file__).resolve().parents[1]
def main():
    registry = ArtifactRegistry(ROOT / ".oktopai")
    for path in sorted((ROOT / "config/specialists").glob("*.Modelfile")):
        record = registry.register(Artifact(path.stem, "prompt-v1", "modelfile", "qwen2.5-coder:7b", str(path)))
        print(record["name"], record.get("digest", ""))
if __name__ == "__main__": main()
