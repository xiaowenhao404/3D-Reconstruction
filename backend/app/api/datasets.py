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
    """扫描 datasets 目录（含 1-2 层嵌套），返回含 images/ 子目录的数据集。"""
    settings = get_settings()
    out: list[dict] = []
    root = settings.datasets_dir
    if not root.exists():
        return out

    def add_scene(scene_dir: Path, scene_id: str) -> None:
        images = scene_dir / "images"
        if images.exists():
            n = count_images(images)
            if n > 0:
                out.append({
                    "id": scene_id,
                    "name": scene_id,
                    "num_images": n,
                    "scene_type": _scene_type(scene_id),
                    "has_poses": (scene_dir / "sparse" / "0").exists(),
                    "thumb": None,
                })

    for d in sorted(root.iterdir()):
        if not d.is_dir():
            continue
        if (d / "images").exists():
            add_scene(d, d.name)
        else:  # 向下再找一层（如 tandt/train）
            for sub in sorted(d.iterdir()):
                if sub.is_dir():
                    add_scene(sub, f"{d.name}/{sub.name}")
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
