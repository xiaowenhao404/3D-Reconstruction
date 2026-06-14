"""模型注册表：读写 ``workspace/models.json``，统一管理三类模型来源
（bundled / generated / imported）。进程内单例，简单文件锁保证一致性。
"""
from __future__ import annotations

import json
import logging
import threading
from pathlib import Path

from app.config import get_settings
from app.schemas import ModelEntry

logger = logging.getLogger(__name__)


class ModelRegistry:
    """``models.json`` 的内存索引 + 持久化。"""

    def __init__(self, json_path: Path) -> None:
        self._path = json_path
        self._lock = threading.Lock()
        self._models: dict[str, ModelEntry] = {}
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            for item in data.get("models", []):
                entry = ModelEntry(**item)
                self._models[entry.id] = entry
        except (json.JSONDecodeError, OSError, ValueError) as exc:
            logger.error("加载 models.json 失败: %s", exc)

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"models": [m.model_dump() for m in self._models.values()]}
        tmp = self._path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self._path)

    def list(self) -> list[ModelEntry]:
        return list(self._models.values())

    def get(self, model_id: str) -> ModelEntry | None:
        return self._models.get(model_id)

    def add(self, entry: ModelEntry) -> ModelEntry:
        with self._lock:
            self._models[entry.id] = entry
            self._save()
        return entry

    def remove(self, model_id: str) -> bool:
        with self._lock:
            if model_id in self._models:
                del self._models[model_id]
                self._save()
                return True
        return False


_registry: ModelRegistry | None = None


def get_registry() -> ModelRegistry:
    global _registry
    if _registry is None:
        _registry = ModelRegistry(get_settings().models_json)
    return _registry


__all__ = ["ModelRegistry", "get_registry"]
