"""训练服务：调用 gsplat 的 examples/simple_trainer.py 拟合 3D 高斯模型。

只用 gsplat 包本体 + 官方 example 脚本（不依赖 nerfstudio）。
进度通过解析 tqdm 风格的 "step/total" 输出换算。
注：精确 CLI 与 stdout 格式在 Phase 2 实测中校准。
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Awaitable, Callable, Optional

from app.config import get_settings
from app.utils.proc import run_command

logger = logging.getLogger(__name__)

ProgressCb = Callable[[float, str], Awaitable[None]]

# 匹配 tqdm / 日志中的 "12345/30000" 步数进度
_STEP_RE = re.compile(r"(\d+)\s*/\s*(\d+)")


async def run_gsplat(
    data_dir: Path,
    result_dir: Path,
    progress: Optional[ProgressCb] = None,
    max_steps: Optional[int] = None,
    data_factor: Optional[int] = None,
    strategy: str = "mcmc",
) -> Path:
    """训练 3DGS 模型，返回导出的 PLY 路径。

    Args:
        data_dir: COLMAP 数据目录（含 images/ 与 sparse/0/）。
        result_dir: 输出目录。
        strategy: "mcmc"（默认，自适应密度控制）或 "default"。
    """
    settings = get_settings()
    max_steps = max_steps or settings.default_max_steps
    data_factor = data_factor or settings.default_data_factor
    result_dir.mkdir(parents=True, exist_ok=True)

    async def _emit(p: float, msg: str) -> None:
        if progress:
            await progress(p, msg)

    await _emit(0, f"启动 gsplat 训练 ({strategy}, {max_steps} 步)")

    last_pct = {"v": 0.0}

    async def on_line(line: str) -> None:
        m = _STEP_RE.search(line)
        if m:
            cur, total = int(m.group(1)), int(m.group(2))
            if total == max_steps and total > 0:
                pct = min(100.0, cur / total * 100.0)
                # 降低事件频率：每升 1% 才推送
                if pct - last_pct["v"] >= 1.0:
                    last_pct["v"] = pct
                    await _emit(pct, line.strip()[:120])

    cmd = [
        settings.train_python,
        settings.simple_trainer,
        strategy,
        "--data_dir", data_dir,
        "--data_factor", str(data_factor),
        "--result_dir", result_dir,
        "--max_steps", str(max_steps),
        "--save_ply",
        "--disable_viewer",
    ]
    await run_command(cmd, cwd=settings.gsplat_repo, on_line=on_line)

    ply = _find_latest_ply(result_dir)
    if ply is None:
        raise RuntimeError(f"训练完成但未找到导出的 PLY（{result_dir}）")
    await _emit(100, "训练完成")
    return ply


def _find_latest_ply(result_dir: Path) -> Optional[Path]:
    """在 result_dir 下查找最新的 point_cloud PLY。"""
    candidates = sorted(result_dir.rglob("*.ply"), key=lambda p: p.stat().st_mtime)
    return candidates[-1] if candidates else None


__all__ = ["run_gsplat", "ProgressCb"]
