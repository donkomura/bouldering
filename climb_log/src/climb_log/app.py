from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, Query

from climb_log.dashboard import compute_stats, stats_to_dict
from climb_log.models import Record
from climb_log.schemas import CreateRecordRequest, DashboardResponse, RecordResponse
from climb_log.store import Store

_DEFAULT_STORE_PATH = Path.home() / ".betalog" / "records.json"


def _default_store_path() -> Path:
    env_path = os.environ.get("CLIMB_LOG_STORE_PATH")
    if env_path:
        return Path(env_path)
    return _DEFAULT_STORE_PATH


def get_store() -> Store:
    return Store(_default_store_path())


def create_app(store: Store | None = None) -> FastAPI:
    app = FastAPI(title="ClimbLog", description="Bouldering logging and analysis API")

    if store is not None:
        app.dependency_overrides[get_store] = lambda: store

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/records", status_code=201, response_model=RecordResponse)
    def create_record(
        body: CreateRecordRequest,
        store: Store = Depends(get_store),
    ) -> RecordResponse:
        record = Record(
            id=str(uuid.uuid4()),
            filename=body.filename,
            result=body.result,
            recorded_at=datetime.now(tz=timezone.utc).replace(tzinfo=None),
            fall_causes=list(body.fall_causes),
            grade=body.grade,
            wall_angle=body.wall_angle,
        )
        store.add(record)
        return RecordResponse.from_record(record)

    @app.get("/records", response_model=list[RecordResponse])
    def list_records(
        store: Store = Depends(get_store),
        since: datetime | None = Query(default=None),
    ) -> list[RecordResponse]:
        if since is not None:
            records = store.list_since(since)
        else:
            records = store.list_all()
        return [RecordResponse.from_record(r) for r in records]

    @app.get("/dashboard", response_model=DashboardResponse)
    def dashboard(store: Store = Depends(get_store)) -> DashboardResponse:
        stats = compute_stats(store.list_all())
        return DashboardResponse.model_validate(stats_to_dict(stats))

    return app
