"""模型产物处理：将训练得到的 PLY 整理到模型库目录。

Phase 2：直接以 PLY 提供给前端查看器（查看器原生支持 .ply）。
Phase 4：接入 PLY -> .ksplat 无损压缩（mkkellogg Node 转换器），显著减小体积。
"""
from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Awaitable, Callable, Optional

logger = logging.getLogger(__name__)

ProgressCb = Callable[[float, str], Awaitable[None]]


async def finalize_model(
    ply_path: Path,
    output_dir: Path,
    model_id: str,
    progress: Optional[ProgressCb] = None,
) -> Path:
    """将 PLY 拷贝到模型库目录，返回最终可服务的模型文件路径。

    后续可在此追加 .ksplat 压缩步骤。
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    dst = output_dir / f"{model_id}.ply"
    if progress:
        await progress(20, "整理模型产物")
    shutil.copy2(ply_path, dst)
    if progress:
        await progress(100, "产物就绪")
    logger.info("模型产物已就绪: %s (%.1f MB)", dst, dst.stat().st_size / 1024 / 1024)
    return dst


def file_size_mb(path: Path) -> float:
    return path.stat().st_size / 1024 / 1024 if path.exists() else 0.0


__all__ = ["finalize_model", "file_size_mb", "ProgressCb"]
