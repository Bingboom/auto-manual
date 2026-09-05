"""Compatibility entry for the public IR lcd Web consumer."""

from __future__ import annotations

from pathlib import Path
from bs4 import BeautifulSoup
from tools.web_table_ir import transform_declared_tables


def transform_lcd_icon_tables(
    soup: BeautifulSoup,
    *,
    source_path: Path,
    declared_page: bool = False,
    error_type: type[Exception] = ValueError,
    language: str | None = None,
    model: str | None = None,
    region: str | None = None,
) -> bool:
    return transform_declared_tables(
        soup,
        table_kind="lcd",
        source_path=source_path,
        declared_page=declared_page,
        error_type=error_type,
        language=language,
        model=model,
        region=region,
    )
