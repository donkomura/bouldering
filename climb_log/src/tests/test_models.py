from __future__ import annotations

from datetime import datetime

from climb_log.models import ClimbResult, FallCause, Record, WallAngle


def make_record(
    *,
    id: str = "test-id",
    video_path: str = "test.MOV",
    result: ClimbResult = ClimbResult.FALL,
    recorded_at: datetime = datetime(2026, 5, 30, 14, 0, 0),
    fall_causes: list[FallCause] | None = None,
    grade: str | None = None,
    wall_angle: WallAngle | None = None,
    note: str | None = None,
) -> Record:
    return Record(
        id=id,
        video_path=video_path,
        result=result,
        recorded_at=recorded_at,
        fall_causes=fall_causes or [],
        grade=grade,
        wall_angle=wall_angle,
        note=note,
    )


class TestClimbResult:
    def test_has_top_and_fall(self):
        assert ClimbResult.TOP.value == "top"
        assert ClimbResult.FALL.value == "fall"


class TestFallCause:
    def test_has_expected_values(self):
        values = {c.value for c in FallCause}
        assert "foot_slip" in values
        assert "pump" in values
        assert "sweaty_hands" in values
        assert "wrong_move" in values
        assert "other" in values


class TestWallAngle:
    def test_has_expected_values(self):
        values = {a.value for a in WallAngle}
        assert "slab" in values
        assert "vertical" in values
        assert "overhang" in values
        assert "roof" in values


class TestRecord:
    def test_is_fall_when_result_is_fall(self):
        record = make_record(result=ClimbResult.FALL)
        assert record.is_fall() is True

    def test_is_not_fall_when_result_is_top(self):
        record = make_record(result=ClimbResult.TOP)
        assert record.is_fall() is False

    def test_to_dict_roundtrip_minimal(self):
        record = make_record()
        assert Record.from_dict(record.to_dict()) == record

    def test_to_dict_roundtrip_full(self):
        record = make_record(
            result=ClimbResult.FALL,
            fall_causes=[FallCause.FOOT_SLIP, FallCause.PUMP],
            grade="3級",
            wall_angle=WallAngle.OVERHANG,
            note="テストメモ",
        )
        assert Record.from_dict(record.to_dict()) == record

    def test_to_dict_contains_required_keys(self):
        record = make_record()
        d = record.to_dict()
        assert "id" in d
        assert "video_path" in d
        assert "result" in d
        assert "recorded_at" in d
        assert "fall_causes" in d

    def test_fall_causes_default_is_empty(self):
        record = make_record()
        assert record.fall_causes == []

    def test_grade_default_is_none(self):
        record = make_record()
        assert record.grade is None

    def test_wall_angle_default_is_none(self):
        record = make_record()
        assert record.wall_angle is None
