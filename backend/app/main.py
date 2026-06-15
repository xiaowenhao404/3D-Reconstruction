"""FastAPI 应用入口：注册路由、CORS、启动任务调度器。"""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import datasets, fs, import_model, jobs, models, uploads
from app.config import get_settings
from app.core.scheduler import scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="3DGS 重建系统 API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# import_model 在 models 之前注册，确保 /models/import 优先匹配
app.include_router(import_model.router, prefix="/api")
app.include_router(models.router, prefix="/api")
app.include_router(datasets.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
app.include_router(uploads.router, prefix="/api")
app.include_router(fs.router, prefix="/api")


@app.on_event("startup")
async def _startup() -> None:
    settings = get_settings()
    settings.ensure_dirs()
    scheduler.start()
    colmap = settings.resolve_colmap()
    logger.info("启动完成。workspace=%s colmap=%s", settings.workspace_dir, colmap or "未找到")


@app.get("/api/health")
def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "colmap": settings.resolve_colmap() is not None,
        "glomap": settings.resolve_glomap() is not None,
        "trainer": settings.train_script.exists(),
    }


__all__ = ["app"]
