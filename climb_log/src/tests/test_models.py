from __future__ import annotations

from datetime import datetime

import pytest

from climb_log.models import ClimbResult, FallCause, TryRecord, WallAngle


def make_record(**kwargs) -> TryRecord:
    defaults = dict(
        id="test-id",
        video_path="test.MOV",
        result=ClimbResult.FALL,
        recorded_at=datetime(2026, 5, 30, 14, 0, 0),
    )
    defaults.update(kwargs)
    return TryRecord(**defaults)


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


class TestTryRecord:
    def test_is_fall_when_result_is_fall(self):
        record = make_record(result=ClimbResult.FALL)
        assert record.is_fall() is True

    def test_is_not_fall_when_result_is_top(self):
        record = make_record(result=ClimbResult.TOP)
        assert record.is_fall() is False

    def test_to_dict_roundtrip_minimal(self):
        record = make_record()
        assert TryRecord.from_dict(record.to_dict()) == record

    def test_to_dict_roundtrip_full(self):
        record = make_record(
            result=ClimbResult.FALL,
            fall_causes=[FallCause.FOOT_SLIP, FallCause.PUMP],
            grade="3級",
            wall_angle=WallAngle.OVERHANG,
            note="テストメモ",
        )
        assert TryRecord.from_dict(record.to_dict()) == record

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
