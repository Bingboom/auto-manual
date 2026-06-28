"""Load a local ``.env``-style file into the process environment at startup.

Phase2 sync (and the review / queue / backport flows that reuse the same
Feishu bindings) need a batch of ``FEISHU_PHASE2_*`` and
``FEISHU_TRANSLATION_MEMORY_*`` variables. Those secrets live in
``~/.auto-manual-phase2.env`` ($HOME, never committed to git) and were
historically only available if the operator manually ``source``-d the file
before running ``build.py``. Command runners (e.g. the OpenClaw gateway that
backs BlockClaw) spawn shells that never source it, so ``sync-data`` failed
its preflight with "Required environment variables are not set" even though
the values existed on disk.

This module loads that file once, early in ``build.py``'s entrypoint, so any
``build.py`` invocation picks the values up regardless of which shell spawned
it — without needing a manual ``source`` or an OpenClaw restart. It is
deliberately conservative:

* it is a no-op when the file is absent (so CI and fresh checkouts are
  unaffected);
* it never overrides a variable that is already set to a non-empty value, so
  an explicit ``export`` / ``source`` in the operator's shell still wins.

The file path defaults to ``~/.auto-manual-phase2.env`` and can be redirected
with the ``AUTO_MANUAL_PHASE2_ENV_FILE`` environment variable (used by tests).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping, MutableMapping

DEFAULT_ENV_FILENAME = ".auto-manual-phase2.env"
ENV_FILE_OVERRIDE = "AUTO_MANUAL_PHASE2_ENV_FILE"

_QUOTES = ("'", '"')


def _default_env_path(environ: Mapping[str, str]) -> Path:
    override = str(environ.get(ENV_FILE_OVERRIDE, "")).strip()
    if override:
        return Path(override).expanduser()
    return Path.home() / DEFAULT_ENV_FILENAME


def parse_env_file(text: str) -> dict[str, str]:
    """Parse ``export KEY=VALUE`` / ``KEY=VALUE`` lines into a mapping.

    Blank lines and ``#`` comment lines are ignored. A leading ``export`` is
    stripped. Surrounding single or double quotes are removed from the value.
    Inline comments are intentionally *not* stripped, because a ``#`` may be a
    legitimate part of a token/value. Malformed lines (no ``=`` or a key that
    is not a valid identifier) are skipped rather than raising.
    """

    values: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export ") or line.startswith("export\t"):
            line = line[len("export "):].strip()
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if not key or not key.isidentifier():
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in _QUOTES:
            value = value[1:-1]
        values[key] = value
    return values


def load_local_env_file(
    path: str | os.PathLike[str] | None = None,
    *,
    environ: MutableMapping[str, str] | None = None,
    override: bool = False,
) -> list[str]:
    """Load the local phase2 env file into ``environ`` if it exists.

    Returns the list of variable names that were applied (empty if the file is
    absent/unreadable or every key was already set). When ``override`` is
    ``False`` (the default), a variable that is already present with a
    non-empty value is left untouched so explicit shell settings win.
    """

    env = environ if environ is not None else os.environ
    env_path = Path(path).expanduser() if path is not None else _default_env_path(env)

    try:
        text = env_path.read_text(encoding="utf-8")
    except (FileNotFoundError, NotADirectoryError, IsADirectoryError, PermissionError, OSError):
        return []

    applied: list[str] = []
    for key, value in parse_env_file(text).items():
        if not override and str(env.get(key, "")).strip():
            continue
        env[key] = value
        applied.append(key)
    return applied
