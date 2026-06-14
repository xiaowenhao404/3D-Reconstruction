"""模型库接口：列出、详情、下载文件、另存为、删除。"""
from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.core.registry import get_registry
from app.schemas import ModelEntry, SaveAsRequest

router = APIRouter(prefix="/models", tags=["models"])


@router.get("")
def list_models() -> list[ModelEntry]:
    return get_registry().list()


@router.get("/{model_id}")
def get_model(model_id: str) -> ModelEntry:
    entry = get_registry().get(model_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="模型不存在")
    return entry


@router.get("/{model_id}/file")
def get_model_file(model_id: str) -> FileResponse:
    """流式返回模型文件本体（供前端查看器加载，支持任意来源/路径）。"""
    entry = get_registry().get(model_id)
    if entry is None or not entry.abs_path:
        raise HTTPException(status_code=404, detail="模型不存在")
    path = Path(entry.abs_path)
    if not path.exists():
        raise HTTPException(status_code=410, detail="模型文件已丢失")
    return FileResponse(path, filename=path.name)


@router.post("/{model_id}/save-as")
def save_as(model_id: str, req: SaveAsRequest) -> dict:
    """将模型另存到自定义路径（满足"自选保存位置"）。"""
    entry = get_registry().get(model_id)
    if entry is None or not Path(entry.abs_path).exists():
        raise HTTPException(status_code=404, detail="模型不存在")
    target = Path(req.target_path)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(entry.abs_path, target)
    except OSError as exc:
        raise HTTPException(status_code=400, detail=f"保存失败: {exc}") from exc
    return {"ok": True, "saved_to": str(target)}


@router.delete("/{model_id}")
def delete_model(model_id: str, delete_file: bool = False) -> dict:
    entry = get_registry().get(model_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="模型不存在")
    if delete_file and entry.abs_path and Path(entry.abs_path).exists():
        try:
            Path(entry.abs_path).unlink()
        except OSError:
            pass
    get_registry().remove(model_id)
    return {"ok": True}


__all__ = ["router"]
