#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Callable

from .renderers_common import (
    apply_vars as apply_vars,
    latex_arg_escape as latex_arg_escape,
    rst_escape as rst_escape,
)
from .renderers_lcd_icons import (
    PH_LCD_ICONS_HEADING_RST as PH_LCD_ICONS_HEADING_RST,
    PH_LCD_ICONS_IMAGE_ALT as PH_LCD_ICONS_IMAGE_ALT,
    PH_LCD_ICONS_TABLE_RST as PH_LCD_ICONS_TABLE_RST,
    render_lcd_icons_page,
)
from .renderers_spec import (
    PH_SPEC_FOOTNOTES_HTML as PH_SPEC_FOOTNOTES_HTML,
    PH_SPEC_FOOTNOTES_LATEX as PH_SPEC_FOOTNOTES_LATEX,
    PH_SPEC_NOTES_HTML as PH_SPEC_NOTES_HTML,
    PH_SPEC_NOTES_LATEX as PH_SPEC_NOTES_LATEX,
    PH_SPEC_SECTIONS_HTML as PH_SPEC_SECTIONS_HTML,
    PH_SPEC_SECTIONS_LATEX as PH_SPEC_SECTIONS_LATEX,
    PH_SPEC_TITLE_MAIN as PH_SPEC_TITLE_MAIN,
    PH_SPEC_TITLE_MAIN_HTML as PH_SPEC_TITLE_MAIN_HTML,
    collect_spec_content as collect_spec_content,
    render_spec_page,
)
from .renderers_symbols import (
    PH_SYMBOLS_ICON_TABLE_RST as PH_SYMBOLS_ICON_TABLE_RST,
    PH_SYMBOLS_SIGNAL_SECTION_RST as PH_SYMBOLS_SIGNAL_SECTION_RST,
    render_symbols_page,
)
from .renderers_troubleshooting import (
    PH_TROUBLESHOOTING_ROWS_RST as PH_TROUBLESHOOTING_ROWS_RST,
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
