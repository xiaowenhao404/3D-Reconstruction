"""Pydantic 数据模型：任务、模型注册项、请求/响应。"""
from __future__ import annotations

from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field

# ────────────────────────── 任务 ──────────────────────────


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


class JobStage(str, Enum):
    UPLOAD = "upload"
    SFM = "sfm"
    UNDISTORT = "undistort"
    TRAIN = "train"
    COMPRESS = "compress"
    DONE = "done"


# 各阶段在总进度中的权重（用于换算 overall_progress）
STAGE_WEIGHTS: dict[JobStage, float] = {
    JobStage.UPLOAD: 0.02,
    JobStage.SFM: 0.25,
    JobStage.UNDISTORT: 0.05,
    JobStage.TRAIN: 0.60,
    JobStage.COMPRESS: 0.08,
}


class Engine(str, Enum):
    GSPLAT = "gsplat"
    BRUSH = "brush"


class Job(BaseModel):
    job_id: str
    name: str
    status: JobStatus = JobStatus.QUEUED
    stage: JobStage = JobStage.UPLOAD
    stage_progress: float = 0.0  # 0-100 当前阶段
    overall_progress: float = 0.0  # 0-100 总体
    engine: Engine = Engine.GSPLAT
    message: str = ""
    output_dir: str = ""
    model_id: Optional[str] = None  # 完成后产出的模型 id
    error: Optional[str] = None


class CreateJobRequest(BaseModel):
    source: Literal["dataset", "upload"]
    dataset_id: Optional[str] = None
    upload_id: Optional[str] = None
    engine: Engine = Engine.GSPLAT
    name: Optional[str] = None
    # 输出根目录（默认 workspace；可填绝对路径以"存到指定位置"）
    output_dir: Optional[str] = None
    max_steps: Optional[int] = None
    data_factor: Optional[int] = None


# ────────────────────────── 模型注册项 ──────────────────────────


class ModelSource(str, Enum):
    BUNDLED = "bundled"
    GENERATED = "generated"
    IMPORTED = "imported"


class ModelMetrics(BaseModel):
    psnr: Optional[float] = None
    ssim: Optional[float] = None
    lpips: Optional[float] = None
    train_seconds: Optional[float] = None
    ply_mb: Optional[float] = None
    ksplat_mb: Optional[float] = None


class ModelEntry(BaseModel):
    id: str
    name: str
    source: ModelSource
    format: Literal["ply", "splat", "ksplat"]
    # 后端静态服务下的相对 URL（前端经 /static 访问）
    url: str
    # 绝对磁盘路径（用于"另存为"、定位）
    abs_path: str = ""
    engine: Optional[Engine] = None
    thumb: Optional[str] = None
    metrics: Optional[ModelMetrics] = None
    created_at: Optional[str] = None


class ImportRequest(BaseModel):
    path: str
    name: Optional[str] = None


class SaveAsRequest(BaseModel):
    target_path: str


class ValidatePathRequest(BaseModel):
    path: str


class ValidatePathResponse(BaseModel):
    ok: bool
    exists: bool
    writable: bool
    message: str = ""


__all__ = [
    "JobStatus",
    "JobStage",
    "STAGE_WEIGHTS",
    "Engine",
    "Job",
    "CreateJobRequest",
    "ModelSource",
    "ModelMetrics",
    "ModelEntry",
    "ImportRequest",
    "SaveAsRequest",
    "ValidatePathRequest",
    "ValidatePathResponse",
]
