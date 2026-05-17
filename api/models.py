from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalyzeRequest(BaseModel):
    trail: int = Field(default=120, description="軌跡を残すフレーム数")
    keep_trail: bool = Field(default=False, description="軌跡を動画中ずっと残す")
    use_gpu: bool = Field(default=False, description="GPU を使用して推論を実行する")


class AnalysisJob(BaseModel):
    job_id: str
    status: JobStatus
    progress: Optional[float] = None
    result_url: Optional[str] = None
    error: Optional[str] = None


class ProgressUpdate(BaseModel):
    progress: float = Field(ge=0.0, le=1.0, description="進捗率（0.0-1.0）")
    frame: int = Field(description="現在のフレーム番号")
    total: int = Field(description="総フレーム数")
