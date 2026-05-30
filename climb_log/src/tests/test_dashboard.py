from __future__ import annotations

from datetime import datetime
from pathlib import Path
from uuid import uuid4

import pytest

from climb_log.dashboard import DashboardStats, compute_stats, focus_points, render_image, render_terminal
from climb_log.models import ClimbResult, FallCause, TryRecord


def make_fall(cause: FallCause | None = None, id: str | None = None) -> TryRecord:
    return TryRecord(
        id=id or str(uuid4()),
        video_path="v.MOV",
        result=ClimbResult.FALL,
        recorded_at=datetime(2026, 5, 30),
        fall_causes=[cause] if cause else [],
    )


def make_top(id: str | None = None) -> TryRecord:
    return TryRecord(
        id=id or str(uuid4()),
        video_path="v.MOV",
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

    def test_period_label_is_set(self):
        stats = compute_stats([], period_label="2026年5月")
        assert stats.period_label == "2026年5月"


class TestFocusPoints:
    def test_returns_most_frequent_cause(self):
        records = [make_fall(FallCause.FOOT_SLIP)] * 5 + [make_fall(FallCause.PUMP)]
        stats = compute_stats(records)
        points = focus_points(stats)
        assert len(points) >= 1
        assert any("足切れ" in p for p in points)

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


class TestRenderImage:
    def test_saves_png_file(self, tmp_path: Path):
        stats = compute_stats(
            [make_fall(FallCause.FOOT_SLIP), make_fall(FallCause.PUMP), make_top()]
        )
        output = tmp_path / "dashboard.png"
        render_image(stats, output)
        assert output.exists()
        assert output.stat().st_size > 0

    def test_saves_file_for_empty_stats(self, tmp_path: Path):
        stats = compute_stats([])
        output = tmp_path / "empty.png"
        render_image(stats, output)
        assert output.exists()
