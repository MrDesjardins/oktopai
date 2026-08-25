from dataclasses import asdict, dataclass, field
import json
from pathlib import Path

@dataclass
class Session:
    messages: list[dict] = field(default_factory=list)
    files: list[dict] = field(default_factory=list)
    repository_facts: list[str] = field(default_factory=list)
    expert_history: list[str] = field(default_factory=list)
    context_budget: int = 12000

    def add_user(self, content: str): self.messages.append({"role": "user", "content": content})
    def add_assistant(self, content: str): self.messages.append({"role": "assistant", "content": content})
    def add_file(self, path: str, content: str): self.files.append({"path": path, "content": content})
    def prompt(self, system_prompt: str) -> list[dict]:
        blocks = [system_prompt]
        if self.repository_facts: blocks.append("Repository facts:\n" + "\n".join(self.repository_facts))
        for file in self.files: blocks.append(f"File: {file['path']}\n{file['content']}")
        combined = "\n\n".join(blocks)
        messages = list(self.messages)
        message_chars = sum(len(str(message.get("content", ""))) for message in messages)
        available = max(0, self.context_budget - message_chars)
        if len(combined) > available: combined = combined[:available] + "\n[context truncated]"
        while messages and len(combined) + sum(len(str(message.get("content", ""))) for message in messages) > self.context_budget:
            messages.pop(0)
        return [{"role": "system", "content": combined}, *messages]
    def save(self, path: Path): path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(asdict(self), indent=2))
    @classmethod
    def load(cls, path: Path) -> "Session": return cls(**json.loads(path.read_text())) if path.exists() else cls()
