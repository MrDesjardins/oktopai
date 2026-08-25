from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import time

@dataclass
class Event:
    kind: str
    data: dict
    timestamp: str = ""
    monotonic_ms: float = 0.0

class Telemetry:
    def __init__(self, path: Path | None = None): self.path = path
    def emit(self, kind: str, **data) -> Event:
        event = Event(kind, data, datetime.now(timezone.utc).isoformat(), time.monotonic_ns() / 1_000_000)
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a") as handle: handle.write(json.dumps(asdict(event)) + "\n")
        return event
