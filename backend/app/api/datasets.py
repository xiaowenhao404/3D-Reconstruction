"""数据集接口：列出内置数据集（可重建的图片组）。"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter

from app.config import get_settings
from app.utils.file_handler import count_images

router = APIRouter(prefix="/datasets", tags=["datasets"])


def _scene_type(name: str) -> str:
    lname = name.lower()
    if any(k in lname for k in ("garden", "stump", "bicycle", "outdoor")):
        return "outdoor"
    if any(k in lname for k in ("bonsai", "kitchen", "room", "counter")):
        return "indoor"
    return "object"


@router.get("")
def list_datasets() -> list[dict]:
    """扫描 datasets 目录，返回含 images/ 子目录的数据集。"""
    settings = get_settings()
    out: list[dict] = []
    root = settings.datasets_dir
    if not root.exists():
        return out
    for d in sorted(root.iterdir()):
        images = d / "images"
        if d.is_dir() and images.exists():
            n = count_images(images)
            if n > 0:
                out.append({
                    "id": d.name,
                    "name": d.name,
                    "num_images": n,
                    "scene_type": _scene_type(d.name),
                    "thumb": None,
                })
    return out


@router.get("/{dataset_id}")
def get_dataset(dataset_id: str) -> dict:
    settings = get_settings()
    images = settings.datasets_dir / dataset_id / "images"
    samples = []
    if images.exists():
        samples = [p.name for p in sorted(images.iterdir())[:8] if p.is_file()]
    return {
        "id": dataset_id,
        "name": dataset_id,
        "num_images": count_images(images),
        "samples": samples,
    }


__all__ = ["router"]
