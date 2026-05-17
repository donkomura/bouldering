import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from api.main import app

client = TestClient(app)


@patch("api.main.redis_client")
@patch("api.main.analyze_video_task")
def test_upload_video(mock_task, mock_redis, mock_video_file):
    """動画アップロードテスト"""
    mock_task.delay = MagicMock()

    response = client.post(
        "/api/analyze",
        files={"video": ("test.mp4", mock_video_file, "video/mp4")},
        data={"trail": 120, "use_gpu": False},
    )

    assert response.status_code == 200
    assert "job_id" in response.json()
    assert response.json()["status"] == "queued"
    mock_task.delay.assert_called_once()


@patch("api.main.redis_client")
def test_get_job_status(mock_redis):
    """ジョブステータス取得テスト"""
    job_id = "test-job-123"
    mock_redis.get.return_value = json.dumps(
        {"job_id": job_id, "status": "processing"}
    )

    response = client.get(f"/api/jobs/{job_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "processing"


@patch("api.main.redis_client")
def test_job_not_found(mock_redis):
    """存在しないジョブIDのエラーハンドリング"""
    mock_redis.get.return_value = None

    response = client.get("/api/jobs/non-existent")
    assert response.status_code == 404


def test_health_check():
    """ヘルスチェックエンドポイント"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
