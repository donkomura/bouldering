from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from climb_log.models import Record

_SCHEMA_VERSION = 1


class TryStore:
    def __init__(self, path: Path = Path.home() / ".betalog" / "records.json"):
        self._path = path

    def add(self, record: Record) -> None:
        records = self._load()
        records.append(record)
        self._save(records)

    def list_all(self) -> list[Record]:
        return self._load()

    def list_since(self, since: datetime) -> list[Record]:
        return [r for r in self._load() if r.recorded_at >= since]

    def _load(self) -> list[Record]:
        if not self._path.exists():
            return []
        data = json.loads(self._path.read_text(encoding="utf-8"))
        return [Record.from_dict(r) for r in data.get("records", [])]

    def _save(self, records: list[Record]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": _SCHEMA_VERSION,
            "records": [r.to_dict() for r in records],
        }
        self._path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
