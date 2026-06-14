"""文件处理：异步保存上传、解压 ZIP、提取图像集。"""
from __future__ import annotations

import logging
import zipfile
from pathlib import Path
from typing import BinaryIO

logger = logging.getLogger(__name__)

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
_CHUNK = 1024 * 1024  # 1MB


async def save_upload(file: BinaryIO, dst: Path) -> int:
    """分块写入上传流，返回字节数（恒定内存占用）。"""
    dst.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    with open(dst, "wb") as out:
        while True:
            chunk = file.read(_CHUNK)
            if not chunk:
                break
            out.write(chunk)
            total += len(chunk)
    return total


def is_image(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_EXTS


def extract_images(src: Path, images_dir: Path) -> int:
    """将 ``src`` 解析为图像集到 ``images_dir``，返回图像数。

    支持：ZIP 包（解压并扁平化图像）或已是图像目录。
    """
    images_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    if src.is_file() and src.suffix.lower() == ".zip":
        with zipfile.ZipFile(src) as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                name = Path(info.filename).name
                if not is_image(Path(name)):
                    continue
                # 扁平化：避免 zip 中的目录层级与路径穿越
                target = images_dir / name
                with zf.open(info) as fsrc, open(target, "wb") as fdst:
                    fdst.write(fsrc.read())
                count += 1
    elif src.is_dir():
        for p in sorted(src.rglob("*")):
            if p.is_file() and is_image(p):
                (images_dir / p.name).write_bytes(p.read_bytes())
                count += 1
    return count


def count_images(images_dir: Path) -> int:
    if not images_dir.exists():
        return 0
    return sum(1 for p in images_dir.iterdir() if p.is_file() and is_image(p))


__all__ = ["save_upload", "extract_images", "is_image", "count_images", "IMAGE_EXTS"]
