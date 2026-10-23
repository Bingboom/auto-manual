"""Atomic replacement of the files the package writes: the intake and the pending push."""
from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
from typing import Any


def write_atomic(path: Path, payload: bytes) -> None:
    """Replace ``path`` with ``payload`` in one step, so a failed write keeps the last good file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix="." + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        # Reopen the candidate before replacing the last good file.
        if Path(temporary).read_bytes() != payload:
            raise OSError("candidate readback mismatch")
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def write_json(path: Path, value: Any) -> None:
    """``value`` as sorted, indented UTF-8 JSON ending in a newline, written atomically."""
    write_atomic(path, (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"))
