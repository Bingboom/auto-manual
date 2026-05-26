#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Callable

from .renderers_common import (
    apply_vars,
    build_list_block,
    html_escape,
    latex_arg_escape,
    render_bullet_rst,
    rst_escape,
)
from .renderers_lcd_icons import (
    PH_LCD_ICONS_HEADING_RST,
    PH_LCD_ICONS_IMAGE_ALT,
    PH_LCD_ICONS_TABLE_RST,
    render_lcd_icons_page,
)
from .renderers_spec import (
    PH_SPEC_FOOTNOTES_HTML,
    PH_SPEC_FOOTNOTES_LATEX,
    PH_SPEC_NOTES_HTML,
    PH_SPEC_NOTES_LATEX,
    PH_SPEC_SECTIONS_HTML,
    PH_SPEC_SECTIONS_LATEX,
    PH_SPEC_TITLE_MAIN,
    PH_SPEC_TITLE_MAIN_HTML,
    collect_spec_content,
    render_spec_page,
)
from .renderers_symbols import (
    PH_SYMBOLS_ICON_TABLE_RST,
    PH_SYMBOLS_SIGNAL_SECTION_RST,
    render_symbols_page,
)
from .renderers_troubleshooting import (
    PH_TROUBLESHOOTING_ROWS_RST,
    render_troubleshooting_page,
)

Renderer = Callable[[str, list[dict[str, str]], str, str, dict[str, str]], str]

PAGE_RENDERERS: dict[str, Renderer] = {
    "spec": render_spec_page,
    "symbols": render_symbols_page,
    "lcd_icons": render_lcd_icons_page,
    "troubleshooting": render_troubleshooting_page,
}


def get_renderer(page_id: str) -> Renderer | None:
    return PAGE_RENDERERS.get((page_id or "").strip())
