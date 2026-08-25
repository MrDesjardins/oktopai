import json, time
from urllib import request, error
from .base import GenerationResult, RuntimeCapabilities, RuntimeUnavailable

class OllamaRuntime:
    def __init__(self, host: str = "http://127.0.0.1:11434", telemetry=None): self.host = host.rstrip("/"); self.loaded: set[str] = set(); self.telemetry = telemetry
    def capabilities(self): return RuntimeCapabilities(preload=True, unload=True, keep_alive=True, streaming_timing=True)
    def _request(self, path: str, payload=None):
        try:
            data = json.dumps(payload).encode() if payload is not None else None
            req = request.Request(self.host + path, data=data, headers={"Content-Type":"application/json"})
            with request.urlopen(req, timeout=120) as response: return json.loads(response.read())
        except (OSError, error.URLError) as exc: raise RuntimeUnavailable(f"Ollama is unavailable at {self.host}. Start it with 'ollama serve'.") from exc
    def list_models(self): return [x.get("name", x.get("model", "")) for x in self._request("/api/tags").get("models", [])]
    def is_loaded(self, model):
        if model in self.loaded: return True
        try:
            loaded = self.loaded_models()
            if model in loaded: self.loaded.add(model); return True
        except RuntimeUnavailable: pass
        return False
    def loaded_models(self):
        try: return [x.get("name", x.get("model", "")) for x in self._request("/api/ps").get("models", [])]
        except RuntimeUnavailable: return sorted(self.loaded)
    def preload(self, model, keep_alive=900):
        start=time.perf_counter(); self._request("/api/generate", {"model":model,"prompt":"","stream":False,"keep_alive":keep_alive}); self.loaded.add(model); return (time.perf_counter()-start)*1000
    def generate(self, model, messages, keep_alive=900):
        cold=not self.is_loaded(model); start=time.perf_counter(); response=self._request("/api/chat", {"model":model,"messages":messages,"stream":False,"keep_alive":keep_alive}); elapsed=(time.perf_counter()-start)*1000; self.loaded.add(model)
        load_ms=float(response.get("load_duration", 0))/1_000_000
        completion_tokens=response.get("eval_count"); eval_duration=response.get("eval_duration", 0)
        tokens_per_second=(completion_tokens / (eval_duration / 1_000_000_000)) if completion_tokens and eval_duration else None
        return GenerationResult(response.get("message",{}).get("content", ""), load_ms, None, elapsed, cold, response.get("prompt_eval_count"), completion_tokens, tokens_per_second)
    def unload(self, model):
        start=time.perf_counter(); self._request("/api/generate", {"model":model,"prompt":"","stream":False,"keep_alive":0}); self.loaded.discard(model); return (time.perf_counter()-start)*1000
