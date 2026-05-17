import pytest
from fakeredis import FakeRedis
import io
import time
from pathlib import Path


@pytest.fixture
def fake_redis():
    """Redis モック"""
    return FakeRedis(decode_responses=True)


@pytest.fixture
def mock_video_file():
    """モック動画ファイル"""
    return io.BytesIO(b"fake video data")


@pytest.fixture
def sample_video_path(tmp_path):
    """テスト用動画ファイル"""
    video_path = tmp_path / "sample.mp4"
    video_path.write_bytes(b"fake video content")
    return str(video_path)


def wait_for_job_completion(client, job_id, timeout=60):
    """
    ジョブ完了まで待機

    Args:
        client: TestClient
        job_id: ジョブID
        timeout: タイムアウト秒数

    Raises:
        TimeoutError: タイムアウト時
    """
    start = time.time()
    while time.time() - start < timeout:
        response = client.get(f"/api/jobs/{job_id}")
        if response.status_code == 200:
            status = response.json()["status"]
            if status in ["completed", "failed"]:
                return
        time.sleep(1)
    raise TimeoutError(f"Job {job_id} did not complete in {timeout}s")
