from __future__ import annotations
import json
from pathlib import Path
from .experts import ExpertRegistry
from .lifecycle import LifecycleManager
from .router import Router
from .runtimes.base import RuntimeUnavailable
from .signals import detect_signals

def run(registry: ExpertRegistry, runtime, telemetry, max_warm_models: int = 1) -> None:
    """Serve newline-delimited local requests until stdin closes.

    This deliberately uses stdin/stdout rather than adding a web framework.
    It keeps the lifecycle manager alive across requests and is easy to wrap
    in a future editor integration.
    """
    lifecycle = LifecycleManager(runtime, registry, telemetry, max_warm_models)
    for line in __import__("sys").stdin:
        if not line.strip(): continue
        request = json.loads(line); action = request.get("action", "route"); prompt = request.get("prompt", "")
        file_path = request.get("file"); content = request.get("content")
        if file_path and content is None:
            try: content = Path(file_path).read_text()
            except OSError as exc: print(json.dumps({"error": str(exc)}), flush=True); continue
        decision = Router(registry).route(prompt, detect_signals(prompt, file_path, content, Path.cwd()), request.get("expert"))
        if action == "route":
            print(json.dumps({"selected":decision.selected,"score":decision.score,"confidence":decision.confidence,"reasons":decision.reasons}), flush=True); continue
        try:
            warm = lifecycle.ensure_warm(decision.selected)
            if action == "preload":
                print(json.dumps({"selected":decision.selected,"model":warm.model,"cold":warm.cold,"load_ms":warm.latency_ms,"evicted":warm.evicted}), flush=True); continue
            expert = registry.get(decision.selected)
            messages = [{"role":"system","content":expert.system_prompt},{"role":"user","content":prompt}]
            if file_path: messages[-1]["content"] += f"\n\nFile: {file_path}\n{content or ''}"
            result = runtime.generate(expert.model, messages, expert.warm_retention_seconds); lifecycle.mark_used(expert.name)
            print(json.dumps({"selected":expert.name,"model":expert.model,"cold":result.cold,"load_ms":warm.latency_ms,"generation_ms":result.generation_ms,"text":result.text}), flush=True)
        except RuntimeUnavailable as exc: print(json.dumps({"error":str(exc),"selected":decision.selected}), flush=True)
