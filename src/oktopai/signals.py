from dataclasses import dataclass
from pathlib import Path
import json
import re

@dataclass(frozen=True)
class RepositorySignals:
    extension: str | None = None
    path: str | None = None
    imports: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    config_files: tuple[str, ...] = ()
    task_signals: tuple[str, ...] = ()

def detect_signals(prompt: str, file_path: str | None = None, file_text: str | None = None,
                   repo_root: Path | None = None) -> RepositorySignals:
    path = Path(file_path) if file_path else None
    text = file_text or ""
    imports = set(re.findall(r"(?:from|import)\s+[\"']([^\"']+)", text))
    imports.update(re.findall(r"require\(\s*[\"']([^\"']+)", text))
    dependencies: set[str] = set()
    config_files: set[str] = set()
    root = repo_root or (path.parent if path else Path.cwd())
    package = root / "package.json"
    if package.is_file():
        config_files.add("package.json")
        try:
            payload = json.loads(package.read_text())
            for group in ("dependencies", "devDependencies", "peerDependencies"):
                dependencies.update(payload.get(group, {}).keys())
        except (OSError, json.JSONDecodeError):
            pass
    for name in ("tsconfig.json", "next.config.js", "next.config.mjs", "vite.config.ts", "jest.config.js", "vitest.config.ts", "pyproject.toml"):
        if (root / name).exists():
            config_files.add(name)
    words = set(re.findall(r"[a-z]+", prompt.lower()))
    task = tuple(sorted(words.intersection({"debug", "explain", "refactor", "test", "testing", "generate", "fix", "rerender", "rendering"})))
    return RepositorySignals(path.suffix.lower() if path else None, str(path) if path else None,
                             tuple(sorted(imports)), tuple(sorted(dependencies)), tuple(sorted(config_files)), task)
