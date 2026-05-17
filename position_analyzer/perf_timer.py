import time
from typing import Any


class PerfTimer:
    def __init__(self) -> None:
        self._checkpoints: dict[str, list[float]] = {}
        self._active: dict[str, float] = {}

    def checkin(self, name: str) -> None:
        if name in self._active:
            raise ValueError(f"Timer '{name}' is already checked in")
        self._active[name] = time.perf_counter()

    def checkout(self, name: str) -> None:
        if name not in self._active:
            raise ValueError(f"Timer '{name}' is not checked in")
        start = self._active.pop(name)
        elapsed = time.perf_counter() - start
        if name not in self._checkpoints:
            self._checkpoints[name] = []
        self._checkpoints[name].append(elapsed)

    def get_total(self, name: str) -> float:
        if name not in self._checkpoints:
            return 0.0
        return sum(self._checkpoints[name])

    def get_count(self, name: str) -> int:
        if name not in self._checkpoints:
            return 0
        return len(self._checkpoints[name])

    def to_dict(self) -> dict[str, Any]:
        result = {}
        for name, times in self._checkpoints.items():
            result[name] = {
                "total_sec": round(sum(times), 2),
                "count": len(times),
                "avg_sec": round(sum(times) / len(times), 2) if times else 0.0,
            }
        return result
