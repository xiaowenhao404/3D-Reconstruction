"""任务调度器：单队列串行执行重建管线，避免多任务争抢显存。

管线：准备图像 -> SfM -> 训练 -> 整理产物 -> 注册模型。
全程通过 event_bus 推送进度（SSE）。
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.config import get_settings
from app.core.events import event_bus
from app.core.registry import get_registry
from app.schemas import (
    STAGE_WEIGHTS,
    CreateJobRequest,
    Engine,
    Job,
    JobStage,
    JobStatus,
    ModelEntry,
    ModelMetrics,
    ModelSource,
)
from app.services import compressor, sfm_service, trainer_service

logger = logging.getLogger(__name__)

# 阶段顺序（用于累加已完成阶段的权重）
_STAGE_ORDER = [
    JobStage.UPLOAD,
    JobStage.SFM,
    JobStage.UNDISTORT,
    JobStage.TRAIN,
    JobStage.COMPRESS,
]


class JobScheduler:
    """进程内单队列串行调度器。"""

    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._requests: dict[str, CreateJobRequest] = {}
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._worker: asyncio.Task | None = None

    def start(self) -> None:
        if self._worker is None:
            self._worker = asyncio.create_task(self._run_worker())

    # ── 对外接口 ──
    def submit(self, req: CreateJobRequest) -> Job:
        job_id = uuid.uuid4().hex[:12]
        settings = get_settings()
        out_root = Path(req.output_dir) if req.output_dir else settings.tasks_dir
        output_dir = out_root / job_id
        job = Job(
            job_id=job_id,
            name=req.name or f"重建-{job_id}",
            engine=req.engine,
            output_dir=str(output_dir),
        )
        self._jobs[job_id] = job
        self._queue.put_nowait(job_id)
        # 保存请求以供 worker 使用
        self._requests[job_id] = req
        return job

    def get(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    def list(self) -> list[Job]:
        return list(self._jobs.values())

    # ── worker ──
    async def _run_worker(self) -> None:
        while True:
            job_id = await self._queue.get()
            req = self._requests.get(job_id)
            job = self._jobs.get(job_id)
            if job is None or req is None:
                continue
            try:
                await self._run_pipeline(job, req)
            except Exception as exc:  # noqa: BLE001 任务失败不应拖垮 worker
                logger.exception("任务 %s 失败", job_id)
                job.status = JobStatus.FAILED
                job.error = str(exc)
                job.message = f"失败: {exc}"
                await self._publish(job)
            finally:
                await event_bus.finish(job_id)
                self._queue.task_done()

    async def _run_pipeline(self, job: Job, req: CreateJobRequest) -> None:
        settings = get_settings()
        job.status = JobStatus.RUNNING
        output_dir = Path(job.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # ── 阶段 1：SfM（若数据已含相机位姿 sparse/0 则跳过，直接训练） ──
        images_dir = self._resolve_images(req)
        await self._set_stage(job, JobStage.UPLOAD, 100, "图像就绪")

        pre_posed = images_dir.parent / "sparse" / "0"
        if pre_posed.exists():
            await self._set_stage(job, JobStage.SFM, 100, "检测到已有相机位姿，跳过 SfM")
            data_dir = images_dir.parent
        else:
            async def sfm_progress(p: float, msg: str) -> None:
                await self._set_stage(job, JobStage.SFM, p, msg)

            data_dir = await sfm_service.run_sfm(
                images_dir, output_dir / "colmap", progress=sfm_progress
            )

        # ── 阶段 2：训练 ──
        async def train_progress(p: float, msg: str) -> None:
            await self._set_stage(job, JobStage.TRAIN, p, msg)

        started = datetime.now(timezone.utc)
        ply = await trainer_service.run_gsplat(
            data_dir,
            output_dir / "train",
            progress=train_progress,
            max_steps=req.max_steps,
            data_factor=req.data_factor,
        )
        train_seconds = (datetime.now(timezone.utc) - started).total_seconds()

        # ── 阶段 3：整理产物 + 注册 ──
        async def comp_progress(p: float, msg: str) -> None:
            await self._set_stage(job, JobStage.COMPRESS, p, msg)

        model_id = f"gen-{job.job_id}"
        model_file = await compressor.finalize_model(
            ply, settings.models_dir, model_id, progress=comp_progress
        )
        entry = ModelEntry(
            id=model_id,
            name=job.name,
            source=ModelSource.GENERATED,
            format="ply",
            url=f"/api/models/{model_id}/file",
            abs_path=str(model_file),
            engine=Engine.GSPLAT,
            metrics=ModelMetrics(
                train_seconds=round(train_seconds, 1),
                ply_mb=round(compressor.file_size_mb(model_file), 1),
            ),
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        get_registry().add(entry)

        job.model_id = model_id
        job.status = JobStatus.SUCCEEDED
        job.stage = JobStage.DONE
        job.overall_progress = 100.0
        job.message = "重建完成"
        await self._publish(job)

    # ── 工具 ──
    def _resolve_images(self, req: CreateJobRequest) -> Path:
        settings = get_settings()
        if req.source == "dataset":
            if not req.dataset_id:
                raise ValueError("source=dataset 需提供 dataset_id")
            images = settings.datasets_dir / req.dataset_id / "images"
            if not images.exists():
                raise FileNotFoundError(f"数据集图像不存在: {images}")
            return images
        if req.source == "upload":
            if not req.upload_id:
                raise ValueError("source=upload 需提供 upload_id")
            images = settings.uploads_dir / req.upload_id / "images"
            if not images.exists():
                raise FileNotFoundError(f"上传图像不存在: {images}")
            return images
        raise ValueError(f"未知 source: {req.source}")

    async def _set_stage(self, job: Job, stage: JobStage, stage_progress: float, msg: str) -> None:
        job.stage = stage
        job.stage_progress = round(stage_progress, 1)
        job.overall_progress = round(self._overall(stage, stage_progress), 1)
        job.message = msg
        await self._publish(job)

    @staticmethod
    def _overall(stage: JobStage, stage_progress: float) -> float:
        done = 0.0
        for s in _STAGE_ORDER:
            if s == stage:
                break
            done += STAGE_WEIGHTS.get(s, 0.0)
        cur = STAGE_WEIGHTS.get(stage, 0.0) * (stage_progress / 100.0)
        return min(100.0, (done + cur) * 100.0)

    async def _publish(self, job: Job) -> None:
        await event_bus.publish(job.job_id, job.model_dump())


scheduler = JobScheduler()

__all__ = ["JobScheduler", "scheduler"]
