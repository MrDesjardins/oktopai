from __future__ import annotations
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path

@dataclass(frozen=True)
class Artifact:
    name: str
    version: str
    kind: str
    base_model: str
    path: str
    status: str = "local"

def digest_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""): digest.update(block)
    return "sha256:" + digest.hexdigest()

class ArtifactRegistry:
    def __init__(self, root: Path): self.root = root; self.index = root / "artifacts.json"
    def list(self) -> list[dict]:
        return json.loads(self.index.read_text()) if self.index.exists() else []
    def register(self, artifact: Artifact) -> dict:
        records = [item for item in self.list() if item["name"] != artifact.name or item["version"] != artifact.version]
        record = asdict(artifact); artifact_path = Path(artifact.path)
        if artifact_path.exists(): record["digest"] = digest_file(artifact_path)
        records.append(record); self.root.mkdir(parents=True, exist_ok=True); self.index.write_text(json.dumps(records, indent=2)); return record
