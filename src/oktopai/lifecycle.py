from collections import OrderedDict
from dataclasses import dataclass
import time
from .experts import ExpertRegistry
from .runtimes.base import Runtime
from .signals import detect_signals
from .router import Router

@dataclass
class ModelState: model: str; last_used: float

@dataclass(frozen=True)
class WarmResult:
    model: str
    latency_ms: float
    cold: bool
    evicted: tuple[str, ...] = ()

class LifecycleManager:
    def __init__(self, runtime: Runtime, registry: ExpertRegistry, telemetry=None, max_warm_models: int = 1):
        self.runtime, self.registry, self.telemetry, self.max_warm_models = runtime, registry, telemetry, max_warm_models
        self.warm: OrderedDict[str, ModelState] = OrderedDict()
    def ensure_warm(self, expert_name: str):
        expert=self.registry.get(expert_name); model=expert.model
        if model in self.warm or self.runtime.is_loaded(model):
            self.warm[model]=ModelState(model,time.monotonic()); self.warm.move_to_end(model); self.telemetry and self.telemetry.emit("warm_start", expert=expert_name, model=model); return WarmResult(model, 0.0, False)
        evicted=[]
        while len(self.warm) >= self.max_warm_models:
            old,_=self.warm.popitem(last=False); evicted.append(old); self.telemetry and self.telemetry.emit("unload_started", model=old); ms=self.runtime.unload(old); self.telemetry and self.telemetry.emit("unload_completed", model=old, latency_ms=ms)
        self.telemetry and self.telemetry.emit("load_started", expert=expert_name, model=model); ms=self.runtime.preload(model, expert.warm_retention_seconds); self.warm[model]=ModelState(model,time.monotonic()); self.telemetry and self.telemetry.emit("load_completed", expert=expert_name, model=model, latency_ms=ms); return WarmResult(model, ms, True, tuple(evicted))
    def preload_for_file(self, prompt: str, file_path: str | None = None, file_text: str | None = None, repo_root=None, override: str | None = None):
        decision = Router(self.registry).route(prompt, detect_signals(prompt, file_path, file_text, repo_root), override)
        return decision, self.ensure_warm(decision.selected)
    def mark_used(self, expert_name):
        model=self.registry.get(expert_name).model
        if model in self.warm: self.warm[model].last_used=time.monotonic(); self.warm.move_to_end(model)
