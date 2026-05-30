from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from climb_log.app import create_app
from climb_log.models import ClimbResult, FallCause, Record
from climb_log.store import Store


@pytest.fixture
def store(tmp_path: Path) -> Store:
    return Store(tmp_path / "records.json")


@pytest.fixture
def client(store: Store) -> TestClient:
    return TestClient(create_app(store=store))


class TestHealth:
    def test_returns_ok(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestCreateRecord:
    def test_creates_record(self, client: TestClient, store: Store):
        response = client.post(
            "/records",
            json={
                "filename": "test.MOV",
                "result": "fall",
                "fall_causes": ["foot_slip"],
                "grade": "V3",
                "wall_angle": 30,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "test.MOV"
        assert data["result"] == "fall"
        assert data["fall_causes"] == ["foot_slip"]
        assert data["grade"] == "V3"
        assert data["wall_angle"] == 30
        assert "id" in data
        assert "recorded_at" in data
        assert len(store.list_all()) == 1

    def test_missing_required_fields_returns_422(self, client: TestClient):
        response = client.post("/records", json={"result": "top"})
        assert response.status_code == 422


class TestListRecords:
    def test_returns_empty_list(self, client: TestClient):
        response = client.get("/records")
        assert response.status_code == 200
        assert response.json() == []

    def test_returns_all_records(self, client: TestClient, store: Store):
        record = Record(
            id="r1",
            filename="a.MOV",
            result=ClimbResult.TOP,
            recorded_at=datetime(2026, 5, 30, 12, 0, 0),
        )
        store.add(record)
        response = client.get("/records")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "r1"

    def test_filters_by_since(self, client: TestClient, store: Store):
        store.add(
            Record(
                id="old",
                filename="old.MOV",
                result=ClimbResult.FALL,
                recorded_at=datetime(2026, 1, 1),
            )
        )
        store.add(
            Record(
                id="new",
                filename="new.MOV",
                result=ClimbResult.TOP,
                recorded_at=datetime(2026, 5, 30),
            )
        )
        response = client.get("/records", params={"since": "2026-05-01T00:00:00"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "new"


class TestDashboard:
    def test_returns_stats(self, client: TestClient, store: Store):
        store.add(
            Record(
                id="f1",
                filename="f.MOV",
                result=ClimbResult.FALL,
                recorded_at=datetime(2026, 5, 30),
                fall_causes=[FallCause.FOOT_SLIP],
            )
        )
        store.add(
            Record(
                id="t1",
                filename="t.MOV",
                result=ClimbResult.TOP,
                recorded_at=datetime(2026, 5, 30),
            )
        )
        response = client.get("/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert data["total_tries"] == 2
        assert data["top_count"] == 1
        assert data["fall_count"] == 1
        assert data["fall_rate"] == 50.0
        assert data["fall_causes"]["foot_slip"] == 1

    def test_empty_stats(self, client: TestClient):
        response = client.get("/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert data["total_tries"] == 0
        assert data["fall_rate"] == 0.0
        assert data["fall_causes"] == {}
