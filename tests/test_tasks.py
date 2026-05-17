import pytest
from unittest.mock import patch, MagicMock
from api.tasks import analyze_video_task


@patch("api.tasks.redis_client")
@patch("api.tasks.analyze_app")
def test_analyze_video_task(mock_analyze_app, mock_redis, tmp_path):
    """解析タスクテスト"""
    video_path = str(tmp_path / "input.mp4")
    mock_analyze_app.return_value = None

    analyze_video_task(
        job_id="test-job",
        video_path=video_path,
        trail=120,
        keep_trail=False,
        use_gpu=False,
    )

    mock_analyze_app.assert_called_once()
    args, kwargs = mock_analyze_app.call_args
    assert args[0].input_path == video_path
    assert args[0].trail == 120
    assert "progress_callback" in kwargs


@patch("api.tasks.redis_client")
@patch("api.tasks.analyze_app")
def test_analyze_video_task_with_error(mock_analyze_app, mock_redis, tmp_path):
    """解析タスクエラー時のテスト"""
    video_path = str(tmp_path / "input.mp4")
    mock_analyze_app.side_effect = Exception("Test error")

    with pytest.raises(Exception):
        analyze_video_task(
            job_id="test-job-error",
            video_path=video_path,
            trail=120,
            keep_trail=False,
            use_gpu=False,
        )

    assert mock_redis.set.called
