from dataclasses import dataclass, field
from pathlib import Path
import tomllib

@dataclass(frozen=True)
class Expert:
    name: str
    domain_tags: tuple[str, ...]
    model: str
    system_prompt: str
    extensions: tuple[str, ...] = ()
    dependency_signals: tuple[str, ...] = ()
    priority: int = 0
    memory_gb: float | None = None
    warm_retention_seconds: int = 900
    model_kind: str = "checkpoint"
    adapter: str | None = None
    base_model: str | None = None

@dataclass
class ExpertRegistry:
    experts: dict[str, Expert] = field(default_factory=dict)

    @classmethod
    def from_toml(cls, path: Path) -> "ExpertRegistry":
        with path.open("rb") as handle:
            data = tomllib.load(handle)
        experts = {}
        for raw in data.get("experts", []):
            expert = Expert(
                name=raw["name"], domain_tags=tuple(raw.get("domain_tags", [])),
                model=raw["model"], system_prompt=raw["system_prompt"],
                extensions=tuple(raw.get("extensions", [])),
                dependency_signals=tuple(raw.get("dependency_signals", [])),
                priority=int(raw.get("priority", 0)),
                memory_gb=raw.get("memory_gb"),
                warm_retention_seconds=int(raw.get("warm_retention_seconds", 900)),
                model_kind=raw.get("model_kind", "checkpoint"), adapter=raw.get("adapter"),
                base_model=raw.get("base_model"),
            )
            experts[expert.name] = expert
        return cls(experts)

    def get(self, name: str) -> Expert:
        try:
            return self.experts[name]
        except KeyError as exc:
            raise ValueError(f"Unknown expert '{name}'. Available: {', '.join(self.experts)}") from exc
