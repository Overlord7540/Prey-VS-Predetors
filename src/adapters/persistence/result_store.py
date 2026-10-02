"""JSON records for experiment batches. Charts read these files later."""
from __future__ import annotations

import json
from pathlib import Path


class ResultStore:
    def save(self, record: dict, path: Path) -> None:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")

    def load(self, path: Path) -> dict:
        return json.loads(Path(path).read_text(encoding="utf-8"))
