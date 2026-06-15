"""SfM 服务：封装 COLMAP（+ 可选 GLOMAP）从图像恢复相机位姿与稀疏点云，
并去畸变为 gsplat 可直接训练的数据布局。

注意：COLMAP/FreeImage 在 Windows 上无法读取含非 ASCII（如中文）的绝对路径图片，
因此本服务将图像暂存到 work_dir/images，并以 cwd=work_dir + 纯 ASCII 相对路径
调用 COLMAP，由操作系统按宽字符解析含中文的工作目录。
"""
from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Awaitable, Callable, Optional

from app.config import get_settings
from app.utils.file_handler import IMAGE_EXTS
from app.utils.proc import run_command

logger = logging.getLogger(__name__)

ProgressCb = Callable[[float, str], Awaitable[None]]


async def run_sfm(
    images_dir: Path,
    work_dir: Path,
    progress: Optional[ProgressCb] = None,
    use_glomap: bool = True,
) -> Path:
    """对 ``images_dir`` 运行 SfM，输出可供 gsplat 训练的数据目录。

    流程：暂存图像 -> feature_extractor -> matcher -> mapper -> image_undistorter
    Returns:
        去畸变后的数据目录（含 images/ 与 sparse/0/）。
    """
    settings = get_settings()
    colmap = settings.resolve_colmap()
    if colmap is None:
        raise RuntimeError("未找到 COLMAP，可执行文件不在 PATH，且 GS_COLMAP_BIN 未配置")

    work_dir.mkdir(parents=True, exist_ok=True)

    async def _emit(p: float, msg: str) -> None:
        if progress:
            await progress(p, msg)

    # ── 暂存图像到 work_dir/images（仅 ASCII 相对路径供 COLMAP 使用） ──
    await _emit(2, "准备图像")
    staged = work_dir / "images"
    staged.mkdir(exist_ok=True)
    n = 0
    for p in sorted(images_dir.iterdir()):
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS:
            shutil.copy2(p, staged / p.name)
            n += 1
    if n == 0:
        raise RuntimeError(f"未在 {images_dir} 找到图像")

    # 全部使用相对 work_dir 的 ASCII 路径
    db, images, sparse, undist = "database.db", "images", "sparse", "undistorted"

    # ① 特征提取（CPU SIFT：GPU SiftGPU 依赖 OpenGL，无窗口后台进程无法创建）
    await _emit(5, f"COLMAP 特征提取 (SIFT, CPU, {n} 图)")
    await run_command([
        colmap, "feature_extractor",
        "--database_path", db, "--image_path", images,
        "--ImageReader.camera_model", "PINHOLE",
        "--ImageReader.single_camera", "1",
        "--FeatureExtraction.use_gpu", "0",
        "--FeatureExtraction.max_image_size", "1600",
    ], cwd=work_dir)

    # ② 特征匹配（CUDA 暴力匹配，不依赖 OpenGL）
    await _emit(30, "COLMAP 特征匹配")
    await run_command([
        colmap, "exhaustive_matcher",
        "--database_path", db, "--FeatureMatching.use_gpu", "1",
    ], cwd=work_dir)

    # ③ 稀疏重建（优先 GLOMAP 全局求解，失败回退增量 mapper）
    (work_dir / sparse).mkdir(exist_ok=True)
    glomap = settings.resolve_glomap() if use_glomap else None
    if glomap is not None:
        await _emit(55, "GLOMAP 全局 SfM 求解位姿")
        await run_command([
            glomap, "mapper",
            "--database_path", db, "--image_path", images, "--output_path", sparse,
        ], cwd=work_dir)
    else:
        await _emit(55, "COLMAP 增量 SfM 求解位姿")
        await run_command([
            colmap, "mapper",
            "--database_path", db, "--image_path", images, "--output_path", sparse,
        ], cwd=work_dir)

    model0 = work_dir / sparse / "0"
    if not model0.exists():
        raise RuntimeError("SfM 未产出稀疏模型，可能图像重叠不足或纹理过弱")

    # ④ 去畸变（生成 gsplat 所需布局）
    await _emit(85, "COLMAP 去畸变")
    await run_command([
        colmap, "image_undistorter",
        "--image_path", images, "--input_path", f"{sparse}/0",
        "--output_path", undist, "--output_type", "COLMAP",
    ], cwd=work_dir)

    # gsplat 期望 sparse/0 布局；image_undistorter 输出 sparse/ 直接含模型文件
    undistorted = work_dir / undist
    out_sparse = undistorted / "sparse"
    out_sparse_0 = out_sparse / "0"
    if out_sparse.exists() and not out_sparse_0.exists():
        out_sparse_0.mkdir(parents=True, exist_ok=True)
        for f in out_sparse.iterdir():
            if f.is_file():
                shutil.move(str(f), str(out_sparse_0 / f.name))

    await _emit(100, "SfM 完成")
    return undistorted


__all__ = ["run_sfm", "ProgressCb"]
