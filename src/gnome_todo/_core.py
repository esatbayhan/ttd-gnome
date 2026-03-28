"""Pure-Python helpers shared between app.py and tests."""

from __future__ import annotations

import json
import os
from pathlib import Path, PurePosixPath

from ttd_core import sort_key
from ttd_core import todo_dir_path as _lib_todo_dir_path
from ttd_core.task import TaskRef

from ._config import get_todo_dir

# Re-export so existing imports from ._core keep working.
__all__ = [
    "todo_dir_path",
    "has_configured_dir",
    "sort_key",
    "task_ref_to_token",
    "task_ref_from_token",
]


def todo_dir_path() -> Path:
    """Resolve the configured todo.txt.d directory."""
    return _lib_todo_dir_path(config_dir=get_todo_dir())


def has_configured_dir() -> bool:
    """Return True if a todo directory is configured via env vars or config file."""
    return bool(os.environ.get("TODO_DIR") or get_todo_dir())


def task_ref_to_token(ref: TaskRef) -> str:
    """Serialize a TaskRef to a compact string for drag-and-drop."""
    return json.dumps(
        {"relative_path": ref.relative_path, "line_index": ref.line_index},
        separators=(",", ":"),
    )


def _valid_relative_path(relative_path: str) -> bool:
    p = PurePosixPath(relative_path)
    if str(p) in {"", "."} or p.is_absolute():
        return False
    return all(part not in {"", ".", ".."} for part in p.parts)


def task_ref_from_token(token: str) -> TaskRef:
    """Deserialize a TaskRef from a drag-and-drop string token."""
    try:
        payload = json.loads(token)
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid task token") from exc
    if not isinstance(payload, dict):
        raise ValueError("Invalid task token")
    relative_path = payload.get("relative_path")
    if not isinstance(relative_path, str) or not _valid_relative_path(relative_path):
        raise ValueError("Invalid task token")
    try:
        line_index = int(payload["line_index"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Invalid task token") from exc
    if line_index < 0:
        raise ValueError("Invalid task token")
    return TaskRef(relative_path=relative_path, line_index=line_index)
