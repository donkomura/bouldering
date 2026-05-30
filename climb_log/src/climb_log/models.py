from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ClimbResult(str, Enum):
    TOP = "top"
    FALL = "fall"


class FallCause(str, Enum):
    FOOT_SLIP = "foot_slip"
    PUMP = "pump"
    SWEATY_HANDS = "sweaty_hands"
    WRONG_MOVE = "wrong_move"
    OTHER = "other"


@dataclass
class Record:
    id: str
    filename: str
    result: ClimbResult
    recorded_at: datetime
    fall_causes: list[FallCause] = field(default_factory=list)
    grade: str | None = None
    wall_angle: int | None = None

    def is_fall(self) -> bool:
        return self.result == ClimbResult.FALL

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "filename": self.filename,
            "result": self.result.value,
            "recorded_at": self.recorded_at.isoformat(),
            "fall_causes": [c.value for c in self.fall_causes],
            "grade": self.grade,
            "wall_angle": self.wall_angle,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Record:
        return cls(
            id=data["id"],
            filename=data["filename"],
            result=ClimbResult(data["result"]),
            recorded_at=datetime.fromisoformat(data["recorded_at"]),
            fall_causes=[FallCause(c) for c in data.get("fall_causes", [])],
            grade=data.get("grade"),
            wall_angle=data.get("wall_angle"),
        )
