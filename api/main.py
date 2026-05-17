import asyncio
import json
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
import redis

from api.models import AnalyzeRequest, AnalysisJob, JobStatus
from api.storage import save_upload_video, get_result_path, result_exists
from api.tasks import analyze_video_task

app = FastAPI(title="Bouldering Analysis API")

redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)


@app.post("/api/analyze", response_model=AnalysisJob)
async def analyze_video(
    video: UploadFile = File(...),
    trail: int = 120,
    keep_trail: bool = False,
    use_gpu: bool = False,
):
    """
    動画アップロード + 解析ジョブ作成

    Args:
        video: 解析する動画ファイル
        trail: 軌跡を残すフレーム数
        keep_trail: 軌跡を動画中ずっと残す
        use_gpu: GPU を使用して推論を実行する

    Returns:
        作成されたジョブ情報
    """
    job_id = str(uuid.uuid4())

    video_path = await save_upload_video(job_id, video)

    redis_client.set(
        f"job:{job_id}:status",
        json.dumps({"job_id": job_id, "status": JobStatus.QUEUED.value}),
    )

    analyze_video_task.delay(
        job_id=job_id,
        video_path=video_path,
        trail=trail,
        keep_trail=keep_trail,
        use_gpu=use_gpu,
    )

    return AnalysisJob(job_id=job_id, status=JobStatus.QUEUED)


@app.get("/api/jobs/{job_id}", response_model=AnalysisJob)
async def get_job_status(job_id: str):
    """
    ジョブステータス取得

    Args:
        job_id: ジョブID

    Returns:
        ジョブステータス情報
    """
    status_data = redis_client.get(f"job:{job_id}:status")

    if not status_data:
        raise HTTPException(status_code=404, detail="Job not found")

    status_dict = json.loads(status_data)
    return AnalysisJob(**status_dict)


@app.get("/api/jobs/{job_id}/progress")
async def job_progress_stream(job_id: str):
    """
    Server-Sent Eventsで進捗通知

    Args:
        job_id: ジョブID

    Returns:
        SSEストリーム
    """
    status_data = redis_client.get(f"job:{job_id}:status")
    if not status_data:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_generator():
        while True:
            progress_data = redis_client.get(f"job:{job_id}:progress")
            if progress_data:
                yield f"data: {progress_data}\n\n"

            status_data = redis_client.get(f"job:{job_id}:status")
            if status_data:
                status_dict = json.loads(status_data)
                if status_dict["status"] in [JobStatus.COMPLETED.value, JobStatus.FAILED.value]:
                    break

            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/jobs/{job_id}/result")
async def download_result(job_id: str):
    """
    結果動画ダウンロード

    Args:
        job_id: ジョブID

    Returns:
        結果動画ファイル
    """
    status_data = redis_client.get(f"job:{job_id}:status")
    if not status_data:
        raise HTTPException(status_code=404, detail="Job not found")

    status_dict = json.loads(status_data)
    if status_dict["status"] != JobStatus.COMPLETED.value:
        raise HTTPException(status_code=400, detail="Job not completed yet")

    result_path = get_result_path(job_id)
    if not result_exists(job_id):
        raise HTTPException(status_code=404, detail="Result file not found")

    return FileResponse(
        result_path, media_type="video/mp4", filename=f"{job_id}_output.mp4"
    )


@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {"status": "ok"}
