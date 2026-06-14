"""导入接口：将已有的 .ply/.splat/.ksplat 文件注册进模型库直接查看（US-6）。"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.core.registry import get_registry
from app.schemas import ImportRequest, ModelEntry, ModelSource

router = APIRouter(prefix="/models", tags=["models"])

_FORMATS = {".ply": "ply", ".splat": "splat", ".ksplat": "ksplat"}


@router.post("/import")
def import_model(req: ImportRequest) -> ModelEntry:
    """按磁盘路径导入已有模型文件（不复制，原地引用）。"""
    path = Path(req.path)
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail=f"文件不存在: {path}")
    fmt = _FORMATS.get(path.suffix.lower())
    if fmt is None:
        raise HTTPException(status_code=400, detail="仅支持 .ply / .splat / .ksplat")

    model_id = f"imp-{uuid.uuid4().hex[:8]}"
    entry = ModelEntry(
        id=model_id,
        name=req.name or path.name,
        source=ModelSource.IMPORTED,
        format=fmt,  # type: ignore[arg-type]
        url=f"/api/models/{model_id}/file",
        abs_path=str(path.resolve()),
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    return get_registry().add(entry)


__all__ = ["router"]
