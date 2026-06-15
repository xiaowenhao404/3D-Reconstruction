"""上传接口：接收图像或 ZIP 包，解出图像集到 uploads/{id}/images。"""
from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile

from app.config import get_settings
from app.utils.file_handler import count_images, extract_images, is_image

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("")
async def create_upload(files: list[UploadFile]) -> dict:
    """接收多张图片或一个 ZIP 包，返回 upload_id 与图像数。"""
    if not files:
        raise HTTPException(status_code=400, detail="未收到文件")
    settings = get_settings()
    upload_id = uuid.uuid4().hex[:12]
    base = settings.uploads_dir / upload_id
    images = base / "images"
    raw = base / "raw"
    images.mkdir(parents=True, exist_ok=True)
    raw.mkdir(parents=True, exist_ok=True)

    for f in files:
        name = Path(f.filename or "file").name
        dst = raw / name
        with open(dst, "wb") as out:
            shutil.copyfileobj(f.file, out)
        if dst.suffix.lower() == ".zip":
            extract_images(dst, images)
        elif is_image(dst):
            shutil.copy2(dst, images / name)

    n = count_images(images)
    if n == 0:
        raise HTTPException(status_code=400, detail="未解析到任何图像（支持 jpg/png/zip）")
    return {"upload_id": upload_id, "num_images": n}


__all__ = ["router"]
