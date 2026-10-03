from __future__ import annotations

from pathlib import Path
from typing import Any, Callable


def validate_loaded_config(
    cfg: dict,
    *,
    validate_cfg: Callable[..., list[Any]],
    printer: Callable[[str], None] = print,
) -> None:
    issues = validate_cfg(cfg, strict_files=False)
    errors = [issue for issue in issues if issue.level == "ERROR"]
    for issue in issues:
        printer(f"[build] config {issue.level.lower()}: {issue.msg}")
    if errors:
        raise RuntimeError("Config validation failed")


def validate_layout_csv(
    layout_csv_path: Path,
    *,
    validate_layout: Callable[[Path], list[Any]],
    printer: Callable[[str], None] = print,
) -> None:
    issues = validate_layout(layout_csv_path)
    errors = [issue for issue in issues if issue.level == "ERROR"]
    for issue in issues:
        printer(f"[build] layout {issue.level.lower()}: {issue.msg}")
    if errors:
        raise RuntimeError("Layout params validation failed")
