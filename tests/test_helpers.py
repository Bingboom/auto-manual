from __future__ import annotations

import tempfile
from contextlib import ExitStack, contextmanager
from pathlib import Path
from typing import Any, Iterator, Sequence
from unittest import mock


@contextmanager
def patch_module_attrs(module: object, **replacements: Any) -> Iterator[None]:
    with ExitStack() as stack:
        for name, value in replacements.items():
            stack.enter_context(mock.patch.object(module, name, value))
        yield


@contextmanager
def temp_workspace() -> Iterator[Path]:
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


@contextmanager
def temp_test_root() -> Iterator[Path]:
    with temp_workspace() as root:
        yield root


def write_text(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def write_lines(path: Path, lines: Sequence[str]) -> Path:
    return write_text(path, "\n".join(lines) + "\n")
