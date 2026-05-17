import pytest
import cv2
import numpy as np
from pathlib import Path
from fastapi.testclient import TestClient
from api.main import app
from tests.conftest import wait_for_job_completion

client = TestClient(app)


@pytest.mark.skip(reason="統合テストは実際の動画ファイルが必要")
def test_output_matches_cli_implementation(sample_video_path):
    """
    API経由の出力が既存CLI実装と同じか検証

    Note: 実際のテストには以下が必要:
    - 実際の動画ファイル
    - MediaPipeモデルファイル
    - Redis実行中
    - Celery worker実行中
    """
    with open(sample_video_path, "rb") as f:
        response = client.post(
            "/api/analyze",
            files={"video": ("test.mp4", f, "video/mp4")},
            data={"trail": 120, "use_gpu": False},
        )

    assert response.status_code == 200
    job_id = response.json()["job_id"]

    wait_for_job_completion(client, job_id, timeout=60)

    api_output = f"/tmp/{job_id}_api_output.mp4"
    response = client.get(f"/api/jobs/{job_id}/result")
    assert response.status_code == 200

    with open(api_output, "wb") as f:
        f.write(response.content)

    from position_analyzer.main import main
    import sys

    cli_output = f"/tmp/{job_id}_cli_output.mp4"
    old_argv = sys.argv
    sys.argv = ["main", "-i", sample_video_path, "-o", cli_output, "--trail", "120"]
    main()
    sys.argv = old_argv

    api_video = cv2.VideoCapture(api_output)
    cli_video = cv2.VideoCapture(cli_output)

    frame_count = 0
    while True:
        ret_api, frame_api = api_video.read()
        ret_cli, frame_cli = cli_video.read()

        if not ret_api or not ret_cli:
            break

        diff = cv2.absdiff(frame_api, frame_cli)
        assert np.max(diff) < 5, f"Frame {frame_count}: 差分が大きすぎます"
        frame_count += 1

    api_video.release()
    cli_video.release()

    assert frame_count > 0, "動画が空です"
