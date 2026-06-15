"""系统配置：路径、外部工具、训练默认超参。

所有路径在导入时解析并确保目录存在；通过环境变量（前缀 ``GS_``）可覆盖。
"""
from __future__ import annotations

import shutil
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/config.py -> 仓库根目录
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """运行期配置（不可变，单例）。"""

    model_config = SettingsConfigDict(env_prefix="GS_", frozen=True)

    # ── 工作区路径（产物默认落盘根目录，可在发起任务时覆盖输出路径） ──
    workspace_dir: Path = PROJECT_ROOT / "workspace"
    datasets_dir: Path = PROJECT_ROOT / "datasets"
    third_party_dir: Path = PROJECT_ROOT / "third_party"

    # ── 外部工具 ──
    # 训练用 Python（backend/.venv，含 torch+gsplat）
    train_python: Path = PROJECT_ROOT / "backend" / ".venv" / "Scripts" / "python.exe"
    # 自研精简训练脚本（只依赖 gsplat 本体）
    train_script: Path = PROJECT_ROOT / "backend" / "train" / "train_gsplat.py"
    # gsplat 仓库（提供 examples，作参考；训练不再依赖）
    gsplat_repo: Path = PROJECT_ROOT / "third_party" / "gsplat"
    # COLMAP / GLOMAP 可执行文件（留空则从 PATH 查找）
    colmap_bin: str = "colmap"
    glomap_bin: str = "glomap"

    # ── 训练默认超参（8GB 显存：data_factor=4 防 OOM） ──
    default_max_steps: int = 30000
    default_data_factor: int = 4
    ssim_lambda: float = 0.2

    @property
    def uploads_dir(self) -> Path:
        return self.workspace_dir / "uploads"

    @property
    def tasks_dir(self) -> Path:
        return self.workspace_dir / "tasks"

    @property
    def models_dir(self) -> Path:
        return self.workspace_dir / "models"

    @property
    def models_json(self) -> Path:
        return self.workspace_dir / "models.json"

    @property
    def simple_trainer(self) -> Path:
        return self.gsplat_repo / "examples" / "simple_trainer.py"

    def ensure_dirs(self) -> None:
        """创建运行所需目录。"""
        for d in (
            self.workspace_dir,
            self.uploads_dir,
            self.tasks_dir,
            self.models_dir,
            self.datasets_dir,
        ):
            d.mkdir(parents=True, exist_ok=True)

    def resolve_colmap(self) -> str | None:
        """返回可用的 colmap 路径：优先配置/PATH，其次内置 third_party。"""
        found = shutil.which(self.colmap_bin) or (
            self.colmap_bin if Path(self.colmap_bin).exists() else None
        )
        if found:
            return found
        bundled = self.third_party_dir / "colmap_dist" / "bin" / "colmap.exe"
        return str(bundled) if bundled.exists() else None

    def resolve_glomap(self) -> str | None:
        found = shutil.which(self.glomap_bin) or (
            self.glomap_bin if Path(self.glomap_bin).exists() else None
        )
        if found:
            return found
        bundled = self.third_party_dir / "colmap_dist" / "bin" / "glomap.exe"
        return str(bundled) if bundled.exists() else None


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_dirs()
    return settings


__all__ = ["Settings", "get_settings", "PROJECT_ROOT"]
