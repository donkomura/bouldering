from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from climb_log.models import ClimbResult, FallCause, Record


class CreateRecordRequest(BaseModel):
    filename: str
    result: ClimbResult
    fall_causes: list[FallCause] = Field(default_factory=list)
    grade: str | None = None
    wall_angle: int | None = None


class RecordResponse(BaseModel):
    id: str
    filename: str
    result: ClimbResult
    recorded_at: datetime
    fall_causes: list[FallCause]
    grade: str | None
    wall_angle: int | None

    @classmethod
    def from_record(cls, record: Record) -> RecordResponse:
        return cls(
            id=record.id,
            filename=record.filename,
            result=record.result,
            recorded_at=record.recorded_at,
            fall_causes=record.fall_causes,
            grade=record.grade,
            wall_angle=record.wall_angle,
        )


class DashboardResponse(BaseModel):
    total_tries: int
    top_count: int
    fall_count: int
    fall_rate: float
    fall_causes: dict[str, int]
    focus_points: list[str]
