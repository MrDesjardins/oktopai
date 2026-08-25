from dataclasses import dataclass
from .experts import Expert, ExpertRegistry
from .signals import RepositorySignals

@dataclass(frozen=True)
class Candidate:
    expert: str
    score: int
    reasons: tuple[str, ...]

@dataclass(frozen=True)
class RouteDecision:
    selected: str
    score: int
    confidence: float
    alternatives: tuple[Candidate, ...]
    reasons: tuple[str, ...]
    override: bool = False

class Router:
    def __init__(self, registry: ExpertRegistry): self.registry = registry

    def route(self, prompt: str, signals: RepositorySignals, override: str | None = None) -> RouteDecision:
        if override:
            expert = self.registry.get(override)
            return RouteDecision(expert.name, 999, 1.0, (), (f"Explicit expert override: {expert.name}",), True)
        scored: list[Candidate] = []
        prompt_lower = prompt.lower()
        for expert in self.registry.experts.values():
            score = expert.priority
            reasons: list[str] = [f"priority +{expert.priority}"]
            if signals.extension and signals.extension in expert.extensions:
                score += 35; reasons.append(f"file extension {signals.extension} +35")
            matched_deps = [d for d in expert.dependency_signals if any(d.lower() in x.lower() for x in (*signals.dependencies, *signals.imports))]
            if matched_deps:
                score += 30 * len(matched_deps); reasons.append(f"dependency/import signal: {', '.join(matched_deps)}")
            for tag in expert.domain_tags:
                if tag.lower() in prompt_lower:
                    score += 12; reasons.append(f"prompt tag '{tag}' +12")
            if any(tag in signals.task_signals for tag in expert.domain_tags):
                score += 8; reasons.append("task signal match +8")
            if expert.name == "nextjs" and any("next" in x.lower() for x in signals.config_files):
                score += 20; reasons.append("Next.js repository configuration +20")
            if expert.name == "nextjs" and ("next.js" in prompt_lower or "nextjs" in prompt_lower):
                score += 25; reasons.append("explicit Next.js task signal +25")
            if expert.name == "general-coding" and not signals.extension and not signals.dependencies and not signals.imports:
                score += 25; reasons.append("no specialist file or repository signal; general fallback +25")
            scored.append(Candidate(expert.name, score, tuple(reasons)))
        scored.sort(key=lambda c: (-c.score, c.expert))
        top = scored[0]
        margin = top.score - (scored[1].score if len(scored) > 1 else 0)
        confidence = min(1.0, max(0.0, 0.5 + margin / max(100, top.score * 2)))
        return RouteDecision(top.expert, top.score, confidence, tuple(scored[1:4]), top.reasons)
