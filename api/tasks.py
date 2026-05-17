import json
import redis
from api.celery_app import celery_app
from api.models import JobStatus
from api.storage import get_result_path
from position_analyzer.app import AppOptions, app as analyze_app

redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)


@celery_app.task
def analyze_video_task(
    job_id: str, video_path: str, trail: int, keep_trail: bool, use_gpu: bool
):
    """
    既存のPython解析ロジックを呼び出すCeleryタスク

    Args:
        job_id: ジョブID
        video_path: 入力動画パス
        trail: 軌跡を残すフレーム数
        keep_trail: 軌跡を動画中ずっと残す
        use_gpu: GPU を使用して推論を実行する
    """
    try:
        redis_client.set(
            f"job:{job_id}:status",
            json.dumps({"job_id": job_id, "status": JobStatus.PROCESSING.value}),
        )

        output_path = get_result_path(job_id)
        options = AppOptions(
            input_path=video_path,
            output_path=output_path,
            trail=trail,
            keep_trail=keep_trail,
            model_path="position_analyzer/pose_landmarker_lite.task",
            use_gpu=use_gpu,
        )

        def progress_callback(frame_index: int, total_frames: int):
            progress = frame_index / total_frames
            redis_client.set(
                f"job:{job_id}:progress",
                json.dumps(
                    {"progress": progress, "frame": frame_index, "total": total_frames}
                ),
            )

        analyze_app(options, progress_callback=progress_callback)

        redis_client.set(
            f"job:{job_id}:status",
            json.dumps(
                {
                    "job_id": job_id,
                    "status": JobStatus.COMPLETED.value,
                    "result_url": f"/api/jobs/{job_id}/result",
                }
            ),
        )

    except Exception as e:
        redis_client.set(
            f"job:{job_id}:status",
            json.dumps(
                {
                    "job_id": job_id,
                    "status": JobStatus.FAILED.value,
                    "error": str(e),
                }
            ),
        )
        raise
