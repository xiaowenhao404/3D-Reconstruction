"""重建任务接口：发起、查询、SSE 进度流、取消。"""
from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.core.events import event_bus
from app.core.scheduler import scheduler
from app.schemas import CreateJobRequest, Job

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("")
def create_job(req: CreateJobRequest) -> Job:
    return scheduler.submit(req)


@router.get("")
def list_jobs() -> list[Job]:
    return scheduler.list()


@router.get("/{job_id}")
def get_job(job_id: str) -> Job:
    job = scheduler.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    return job


@router.get("/{job_id}/events")
async def job_events(job_id: str) -> StreamingResponse:
    """SSE 进度流：前端用 EventSource 订阅。"""
    if scheduler.get(job_id) is None:
        raise HTTPException(status_code=404, detail="任务不存在")

    async def gen():
        async for event in event_bus.subscribe(job_id):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0)  # 让出事件循环，及时刷新
        yield "event: end\ndata: {}\n\n"

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


__all__ = ["router"]
