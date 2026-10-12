"""Console logging that keeps the repo's ``print``-style output byte-identical.

Tools report progress with lines such as ``print("[review-start] ...")``, and
tests assert on that text by swapping ``sys.stdout``/``sys.stderr`` with
``contextlib.redirect_stdout``. This module routes those lines through
:mod:`logging` without changing them:

- the message is written verbatim: the ``[component] LEVEL`` wording stays in
  the message itself, so replacing ``print(msg)`` with ``log.info(msg)`` is a
  one-word, output-identical change;
- the stream is looked up when each line is written, so ``redirect_stdout``
  and unittest's buffering capture exactly what ``print`` did;
- ``AUTO_MANUAL_LOG_LEVEL`` (``DEBUG``/``INFO``/``WARNING``/``ERROR``, default
  ``INFO``) filters lines by level, which ``print`` never could.

A ``print(..., file=sys.stderr)`` call maps to the ``stream="stderr"`` logger
so each line keeps its stream::

    log = get_logger("review-start")
    err = get_logger("review-start", stream="stderr")
    log.info(f"[review-start] {command}")
    err.error(f"[review-start] FAILURE {key}: {exc}")

Two kinds of output are not log records and stay a plain ``print``: output
relayed verbatim from a child process, and a command's result (the rows,
report or ``--json`` payload a caller reads from stdout), which must appear at
every log level.
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Literal, TextIO

LEVEL_ENV = "AUTO_MANUAL_LOG_LEVEL"
ROOT_LOGGER = "auto_manual"
DEFAULT_LEVEL = logging.INFO
LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

Stream = Literal["stdout", "stderr"]
_STREAMS: tuple[Stream, ...] = ("stdout", "stderr")


class _ConsoleHandler(logging.Handler):
    """Write each record's message to the stream that is current at emit time."""

    def __init__(self, stream: Stream) -> None:
        super().__init__()
        self.stream_name: Stream = stream
        self.setFormatter(logging.Formatter("%(message)s"))

    def _target(self) -> TextIO:
        return sys.stderr if self.stream_name == "stderr" else sys.stdout

    def emit(self, record: logging.LogRecord) -> None:
        try:
            target = self._target()
            target.write(self.format(record) + "\n")
            target.flush()
        except Exception:  # noqa: BLE001 - mirrors logging.Handler.emit, which routes to handleError
            self.handleError(record)


def _parse_level(raw: str | None) -> tuple[int, str | None]:
    """Return ``(level, rejected_value)``; unknown values fall back to INFO."""

    text = (raw or "").strip().upper()
    if not text:
        return DEFAULT_LEVEL, None
    if text in LEVELS:
        return LEVELS[text], None
    return DEFAULT_LEVEL, raw


def configure(level: str | int | None = None) -> int:
    """(Re)apply the level: an explicit argument, else ``AUTO_MANUAL_LOG_LEVEL``.

    Installs one console handler per stream on first use and returns the
    numeric level now in effect. An unknown level name keeps ``INFO`` and says
    so once on stderr, rather than failing an unattended run over a typo.
    """

    if isinstance(level, int):
        resolved, rejected = level, None
    else:
        resolved, rejected = _parse_level(level if level is not None else os.environ.get(LEVEL_ENV))
    root = logging.getLogger(ROOT_LOGGER)
    root.setLevel(resolved)
    root.propagate = False
    for stream in _STREAMS:
        parent = logging.getLogger(f"{ROOT_LOGGER}.{stream}")
        parent.propagate = False
        if not any(isinstance(handler, _ConsoleHandler) for handler in parent.handlers):
            parent.addHandler(_ConsoleHandler(stream))
    if rejected is not None:
        print(
            f"[log] ignoring unknown {LEVEL_ENV}={rejected!r}; using INFO "
            f"(expected one of {', '.join(LEVELS)})",
            file=sys.stderr,
        )
    return resolved


def get_logger(component: str, *, stream: Stream = "stdout") -> logging.Logger:
    """Return the ``component`` logger that writes verbatim lines to ``stream``."""

    if stream not in _STREAMS:
        raise ValueError(f"stream must be one of {_STREAMS}, not {stream!r}")
    if not logging.getLogger(f"{ROOT_LOGGER}.{stream}").handlers:
        configure()
    return logging.getLogger(f"{ROOT_LOGGER}.{stream}.{component}")
