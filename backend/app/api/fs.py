"""文件系统辅助接口：建议默认输出根目录、校验自定义保存路径可写。"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

from fastapi import APIRouter

from app.config import get_settings
from app.schemas import ValidatePathRequest, ValidatePathResponse

router = APIRouter(prefix="/fs", tags=["fs"])


@router.get("/suggest-root")
def suggest_root() -> dict:
    """返回默认产物根目录（workspace）。"""
    settings = get_settings()
    return {"root": str(settings.workspace_dir), "tasks": str(settings.tasks_dir)}


@router.post("/validate-path")
def validate_path(req: ValidatePathRequest) -> ValidatePathResponse:
    """校验目标路径是否可写（用于保存路径选择 UI 的实时反馈）。"""
    path = Path(req.path)
    target_dir = path if path.is_dir() or req.path.endswith(("/", "\\")) else path.parent
    exists = path.exists()
    writable = False
    message = ""
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        # 试写一个临时文件验证写权限
        with tempfile.NamedTemporaryFile(dir=target_dir, delete=True):
            pass
        writable = True
    except OSError as exc:
        message = f"不可写: {exc}"
    return ValidatePathResponse(
        ok=writable, exists=exists, writable=writable, message=message or "可写"
    )


__all__ = ["router"]
