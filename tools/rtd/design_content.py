"""Shared pieces of the 设计规范 page: its error type, its notes file and inline formatting.

The notes are committed data (tools/rtd_portal_assets/design_system/content.yaml);
every value the page shows is read from the repository at build time by
tools/rtd/design_system.py, design_assets.py and design_print.py.
"""
from __future__ import annotations

from html import escape
from pathlib import Path
import re
from typing import Any

from markupsafe import Markup
import yaml

CONTENT_DIR = "design_system"

_INLINE = re.compile(r"`([^`]+)`|\*\*([^*]+)\*\*|\*([^*\s][^*]*)\*")


class DesignSystemError(ValueError):
    """The committed design-system data no longer matches the repository."""


def inline(text: str) -> Markup:
    """Escape text, then allow only `code`, **strong** and *em*."""
    parts, position = [], 0
    for match in _INLINE.finditer(text):
        parts.append(escape(text[position:match.start()]))
        code, strong, emphasis = match.groups()
        if code is not None:
            parts.append(f"<code>{escape(code)}</code>")
        elif strong is not None:
            parts.append(f"<strong>{escape(strong)}</strong>")
        else:
            parts.append(f"<em>{escape(emphasis)}</em>")
        position = match.end()
    parts.append(escape(text[position:]))
    return Markup("".join(parts))


SCHEMA_VERSION = 3  # 2: the 概览 tab reads style, foundations, principles, usage and showcase.
# 3: colours carry a group (color_groups), asset groups a render note, print an overrides note and lead rows.


def load_content(assets: Path) -> dict[str, Any]:
    data = yaml.safe_load((assets / CONTENT_DIR / "content.yaml").read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION:
        raise DesignSystemError(f"design_system/content.yaml needs schema_version {SCHEMA_VERSION}")
    return data


__all__ = ["CONTENT_DIR", "DesignSystemError", "inline", "load_content"]
