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
    render_lead_html,
    render_latex_cmd,
    render_list_html,
    rst_escape,
)
from .renderers_safety import (
    PH_BOTTOM,
    PH_BOTTOM_HTML,
    PH_LEAD_TOP,
    PH_LEAD_TOP_HTML,
    PH_SAVE_TITLE,
    PH_SAVE_TITLE_HTML,
    PH_TITLE_MAIN,
    PH_TITLE_MAIN_HTML,
    PH_TITLE_OPERATING,
    PH_TITLE_OPERATING_HTML,
    PH_TOP,
    PH_TOP_HTML,
    PH_WARNING_TITLE,
    PH_WARNING_TITLE_HTML,
    collect_safety_content,
    render_safety_page,
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

Renderer = Callable[[str, list[dict[str, str]], str, str, dict[str, str]], str]

PAGE_RENDERERS: dict[str, Renderer] = {
    "safety": render_safety_page,
    "spec": render_spec_page,
    "symbols": render_symbols_page,
}


def get_renderer(page_id: str) -> Renderer | None:
    return PAGE_RENDERERS.get((page_id or "").strip())

