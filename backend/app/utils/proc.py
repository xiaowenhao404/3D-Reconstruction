"""异步子进程封装：运行外部命令并按行回调 stdout（用于解析进度）。"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Awaitable, Callable, Optional, Sequence

logger = logging.getLogger(__name__)

# 行回调：接收一行 stdout 文本
LineCallback = Callable[[str], Awaitable[None]]


class CommandError(RuntimeError):
    """命令以非零退出码结束。"""

    def __init__(self, cmd: Sequence[str], code: int, tail: str) -> None:
        self.code = code
        self.tail = tail
        super().__init__(f"命令失败 (exit {code}): {' '.join(map(str, cmd))}\n{tail}")


async def run_command(
    cmd: Sequence[str],
    *,
    cwd: Optional[Path] = None,
    on_line: Optional[LineCallback] = None,
    env: Optional[dict] = None,
) -> str:
    """运行命令，实时按行回调 stdout（stderr 合并）。

    Returns:
        完整 stdout 文本。
    Raises:
        CommandError: 退出码非零。
    """
    logger.info("运行命令: %s", " ".join(map(str, cmd)))
    proc = await asyncio.create_subprocess_exec(
        *map(str, cmd),
        cwd=str(cwd) if cwd else None,
        env=env,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    lines: list[str] = []
    assert proc.stdout is not None
    async for raw in proc.stdout:
        line = raw.decode("utf-8", errors="replace").rstrip("\r\n")
        lines.append(line)
        if on_line is not None:
            try:
                await on_line(line)
            except Exception as exc:  # noqa: BLE001 进度回调异常不应中断命令
                logger.warning("on_line 回调异常: %s", exc)

    code = await proc.wait()
    output = "\n".join(lines)
    if code != 0:
        raise CommandError(cmd, code, "\n".join(lines[-20:]))
    return output


__all__ = ["run_command", "CommandError", "LineCallback"]
