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


def step_action_name(step: object) -> str | None:
    """Return a workflow step's action without its version ref.

    ``{"uses": "actions/cache@v6"}`` -> ``"actions/cache"``; ``None`` for a
    ``run:`` step. Workflow guards assert policy (retention windows, step
    order, which surfaces get uploaded), so they must match on the action
    itself — pinning the version in the assertion turns every routine
    dependabot bump red, and a version-pinned *matcher* is worse: it silently
    stops finding the steps it was meant to police.
    """
    if not isinstance(step, dict):
        return None
    uses = step.get("uses")
    if not isinstance(uses, str):
        return None
    return uses.split("@", 1)[0]


def step_uses_action(step: object, action: str) -> bool:
    """True when ``step`` uses ``action`` at any version ref or pinned sha."""
    return step_action_name(step) == action
