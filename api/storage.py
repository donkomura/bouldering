import os
from pathlib import Path
from fastapi import UploadFile


UPLOAD_DIR = Path("/tmp/uploads")
RESULT_DIR = Path("/tmp/results")

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RESULT_DIR.mkdir(parents=True, exist_ok=True)


async def save_upload_video(job_id: str, video: UploadFile) -> str:
    """
    アップロードされた動画をローカルに保存

    Args:
        job_id: ジョブID
        video: アップロードファイル

    Returns:
        保存されたファイルパス
    """
    video_path = UPLOAD_DIR / f"{job_id}.mp4"

    with open(video_path, "wb") as f:
        content = await video.read()
        f.write(content)

    return str(video_path)


def get_result_path(job_id: str) -> str:
    """
    結果動画のパスを取得

    Args:
        job_id: ジョブID

    Returns:
        結果動画のパス
    """
    return str(RESULT_DIR / f"{job_id}_output.mp4")


def result_exists(job_id: str) -> bool:
    """
    結果動画が存在するか確認

    Args:
        job_id: ジョブID

    Returns:
        存在する場合True
    """
    result_path = Path(get_result_path(job_id))
    return result_path.exists()
