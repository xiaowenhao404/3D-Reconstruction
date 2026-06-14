"""SfM 服务：封装 COLMAP（+ 可选 GLOMAP）从图像恢复相机位姿与稀疏点云，
并去畸变为 gsplat 可直接训练的数据布局。

注：具体 CLI 参数与产物布局在 Phase 2 实测中对照官方工具校准。
"""
from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Awaitable, Callable, Optional

from app.config import get_settings
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

    流程：feature_extractor -> matcher -> (glomap|colmap) mapper -> image_undistorter
    Returns:
        去畸变后的数据目录（含 images/ 与 sparse/0/）。
    """
    settings = get_settings()
    colmap = settings.resolve_colmap()
    if colmap is None:
        raise RuntimeError("未找到 COLMAP，可执行文件不在 PATH，且 GS_COLMAP_BIN 未配置")

    db = work_dir / "database.db"
    sparse = work_dir / "sparse"
    undistorted = work_dir / "undistorted"
    work_dir.mkdir(parents=True, exist_ok=True)

    async def _emit(p: float, msg: str) -> None:
        if progress:
            await progress(p, msg)

    # ① 特征提取
    await _emit(5, "COLMAP 特征提取 (SIFT)")
    await run_command([
        colmap, "feature_extractor",
        "--database_path", db, "--image_path", images_dir,
        "--ImageReader.camera_model", "PINHOLE",
        "--ImageReader.single_camera", "1",
        "--SiftExtraction.use_gpu", "1",
    ])

    # ② 特征匹配
    await _emit(30, "COLMAP 特征匹配")
    await run_command([
        colmap, "exhaustive_matcher",
        "--database_path", db, "--SiftMatching.use_gpu", "1",
    ])

    # ③ 稀疏重建（优先 GLOMAP 全局求解，失败回退增量 mapper）
    sparse.mkdir(parents=True, exist_ok=True)
    glomap = settings.resolve_glomap() if use_glomap else None
    if glomap is not None:
        await _emit(55, "GLOMAP 全局 SfM 求解位姿")
        await run_command([
            glomap, "mapper",
            "--database_path", db, "--image_path", images_dir,
            "--output_path", sparse,
        ])
    else:
        await _emit(55, "COLMAP 增量 SfM 求解位姿")
        await run_command([
            colmap, "mapper",
            "--database_path", db, "--image_path", images_dir,
            "--output_path", sparse,
        ])

    # ④ 去畸变（生成 gsplat 所需布局）
    await _emit(85, "COLMAP 去畸变")
    model_dir = sparse / "0"
    if not model_dir.exists():
        raise RuntimeError(
            f"SfM 未产出稀疏模型（{model_dir} 不存在），可能图像重叠不足或纹理过弱"
        )
    await run_command([
        colmap, "image_undistorter",
        "--image_path", images_dir,
        "--input_path", model_dir,
        "--output_path", undistorted,
        "--output_type", "COLMAP",
    ])

    # gsplat 期望 sparse/0 布局；image_undistorter 输出 sparse/ 直接含模型文件
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
