from __future__ import annotations

import json
from datetime import datetime
from uuid import uuid4

from climb_log.dashboard import (
    compute_stats,
    focus_points,
    render_json,
    render_terminal,
)
from climb_log.models import ClimbResult, FallCause, Record


def make_fall(cause: FallCause | None = None, id: str | None = None) -> Record:
    return Record(
        id=id or str(uuid4()),
        filename="v.MOV",
        result=ClimbResult.FALL,
        recorded_at=datetime(2026, 5, 30),
        fall_causes=[cause] if cause else [],
    )


def make_top(id: str | None = None) -> Record:
    return Record(
        id=id or str(uuid4()),
        filename="v.MOV",
        result=ClimbResult.TOP,
        recorded_at=datetime(2026, 5, 30),
    )


class TestComputeStats:
    def test_counts_total_correctly(self):
        stats = compute_stats([make_fall(), make_top(), make_fall()])
        assert stats.total_tries == 3

    def test_counts_fall_and_top_separately(self):
        stats = compute_stats([make_fall(), make_fall(), make_top()])
        assert stats.fall_count == 2
        assert stats.top_count == 1

    def test_empty_records_returns_zeros(self):
        stats = compute_stats([])
        assert stats.total_tries == 0
        assert stats.fall_count == 0
        assert stats.top_count == 0

    def test_fall_cause_counts_aggregated(self):
        records = [
            make_fall(FallCause.FOOT_SLIP),
            make_fall(FallCause.FOOT_SLIP),
            make_fall(FallCause.PUMP),
        ]
        stats = compute_stats(records)
        assert stats.fall_cause_counts[FallCause.FOOT_SLIP] == 2
        assert stats.fall_cause_counts[FallCause.PUMP] == 1

    def test_cause_not_in_counts_when_zero(self):
        stats = compute_stats([make_fall(FallCause.FOOT_SLIP)])
        assert FallCause.PUMP not in stats.fall_cause_counts


class TestFocusPoints:
    def test_returns_most_frequent_cause(self):
        records = [make_fall(FallCause.FOOT_SLIP)] * 5 + [make_fall(FallCause.PUMP)]
        stats = compute_stats(records)
        points = focus_points(stats)
        assert len(points) >= 1
        assert any("Foot slip" in p for p in points)

    def test_returns_empty_for_no_falls(self):
        stats = compute_stats([make_top()])
        assert focus_points(stats) == []


class TestRenderTerminal:
    def test_includes_total_count(self):
        stats = compute_stats([make_fall(), make_fall(), make_top()])
        text = render_terminal(stats)
        assert "3" in text

    def test_includes_fall_rate(self):
        stats = compute_stats([make_fall(), make_top()])
        text = render_terminal(stats)
        assert "50" in text

    def test_handles_zero_total(self):
        stats = compute_stats([])
        text = render_terminal(stats)
        assert text is not None


class TestRenderJson:
    def test_returns_valid_json(self):
        stats = compute_stats([make_fall(), make_top()])
        data = json.loads(render_json(stats))
        assert data["total_tries"] == 2
        assert data["top_count"] == 1
        assert data["fall_count"] == 1

    def test_includes_fall_rate(self):
        stats = compute_stats([make_fall(), make_top()])
        data = json.loads(render_json(stats))
        assert data["fall_rate"] == 50.0

    def test_fall_causes_keyed_by_value(self):
        stats = compute_stats(
            [make_fall(FallCause.FOOT_SLIP), make_fall(FallCause.FOOT_SLIP)]
        )
        data = json.loads(render_json(stats))
        assert data["fall_causes"]["foot_slip"] == 2

    def test_handles_empty_stats(self):
        data = json.loads(render_json(compute_stats([])))
        assert data["total_tries"] == 0
        assert data["fall_rate"] == 0.0
        assert data["fall_causes"] == {}
