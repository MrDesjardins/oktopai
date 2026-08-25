from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class RuntimeCapabilities:
    preload: bool = False
    unload: bool = False
    keep_alive: bool = False
    streaming_timing: bool = False

@dataclass(frozen=True)
class GenerationResult:
    text: str
    load_ms: float = 0.0
    first_token_ms: float | None = None
    generation_ms: float = 0.0
    cold: bool = False
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    tokens_per_second: float | None = None

class RuntimeUnavailable(RuntimeError): pass

class Runtime(Protocol):
    def capabilities(self) -> RuntimeCapabilities: ...
    def list_models(self) -> list[str]: ...
    def loaded_models(self) -> list[str]: ...
    def is_loaded(self, model: str) -> bool: ...
    def preload(self, model: str, keep_alive: int = 900) -> float: ...
    def generate(self, model: str, messages: list[dict], keep_alive: int = 900) -> GenerationResult: ...
    def unload(self, model: str) -> float: ...
