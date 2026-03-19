from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any


class TelemetryRecorder:
    def __init__(self, repo_root: str | Path) -> None:
        root = Path(repo_root)
        self.logs_dir = root / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.events_path = self.logs_dir / "agent_events.jsonl"
        self.logger = logging.getLogger("ai_studio")
        self.logger.setLevel(logging.INFO)
        if not any(isinstance(handler, logging.FileHandler) and Path(handler.baseFilename) == self.logs_dir / "app.log" for handler in self.logger.handlers):
            handler = logging.FileHandler(self.logs_dir / "app.log", encoding="utf-8")
            handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
            self.logger.addHandler(handler)

    def info(self, message: str, **extra: Any) -> None:
        if extra:
            self.logger.info("%s | %s", message, json.dumps(extra, ensure_ascii=True, sort_keys=True, default=str))
        else:
            self.logger.info(message)

    def error(self, message: str, **extra: Any) -> None:
        if extra:
            self.logger.error("%s | %s", message, json.dumps(extra, ensure_ascii=True, sort_keys=True, default=str))
        else:
            self.logger.error(message)

    def append_event(self, event_type: str, payload: dict[str, Any]) -> None:
        record = {"event_type": event_type, **payload}
        with self.events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=True, sort_keys=True, default=str) + "\n")
