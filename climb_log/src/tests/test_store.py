from __future__ import annotations

from datetime import datetime
from pathlib import Path

from climb_log.models import ClimbResult, FallCause, Record, WallAngle
from climb_log.store import Store


def make_record(id: str = "test-id", recorded_at: datetime | None = None) -> Record:
    return Record(
        id=id,
        video_path="test.MOV",
        result=ClimbResult.FALL,
        recorded_at=recorded_at or datetime(2026, 5, 30, 14, 0, 0),
        fall_causes=[FallCause.FOOT_SLIP],
        grade="3級",
        wall_angle=WallAngle.OVERHANG,
    )


class TestStore:
    def test_add_and_list_all(self, tmp_path: Path):
        store = Store(tmp_path / "records.json")
        record = make_record()
        store.add(record)
        assert store.list_all() == [record]

    def test_list_all_empty_when_no_records(self, tmp_path: Path):
        store = Store(tmp_path / "records.json")
        assert store.list_all() == []

    def test_persists_across_instances(self, tmp_path: Path):
        path = tmp_path / "records.json"
        Store(path).add(make_record(id="r1"))
        assert len(Store(path).list_all()) == 1

    def test_add_multiple_records(self, tmp_path: Path):
        store = Store(tmp_path / "records.json")
        store.add(make_record(id="r1"))
        store.add(make_record(id="r2"))
        assert len(store.list_all()) == 2

    def test_list_since_filters_old_records(self, tmp_path: Path):
        store = Store(tmp_path / "records.json")
        store.add(make_record(id="old", recorded_at=datetime(2026, 1, 1)))
        store.add(make_record(id="new", recorded_at=datetime(2026, 5, 30)))
        result = store.list_since(datetime(2026, 5, 1))
        assert len(result) == 1
        assert result[0].id == "new"

    def test_list_since_includes_exact_boundary(self, tmp_path: Path):
        store = Store(tmp_path / "records.json")
        boundary = datetime(2026, 5, 1)
        store.add(make_record(id="boundary", recorded_at=boundary))
        result = store.list_since(boundary)
        assert len(result) == 1

    def test_creates_parent_directory_if_not_exists(self, tmp_path: Path):
        nested = tmp_path / "deep" / "nested" / "records.json"
        Store(nested).add(make_record())
        assert nested.exists()

    def test_roundtrip_preserves_all_fields(self, tmp_path: Path):
        path = tmp_path / "records.json"
        record = make_record()
        Store(path).add(record)
        loaded = Store(path).list_all()[0]
        assert loaded == record
