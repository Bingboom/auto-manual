"""印刷规格 tab: print page, type, colour and component geometry from data/layout_params.csv.

The PDF (LaTeX) and IDML renderers read this one token table; the web never
does. Values are read at build time through tools.render_contract, the
repository's reader for the table; only the Chinese labels and the actual-size
page preview are committed (design_system/content.yaml, print_page.html and
print_page.css). A key the labels name that the table no longer has, or a
token the preview uses that the table no longer defines, fails like a retired
selector does.
"""
from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from tools.render_contract import LayoutToken, layout_tokens_sha256, load_layout_tokens
from tools.rtd.design_content import CONTENT_DIR, DesignSystemError, inline
from tools.utils.path_utils import Paths

PRINT_PAGE = "print_page"
# Units a CSS custom property carries as written; a ratio stays unitless.
CSS_UNITS = {"mm": "mm", "pt": "pt", "ratio": ""}
SAMPLE = "Charging 1024 Wh"

_KEY = re.compile(r"[a-z][a-z0-9_]*")
_NUMBER = re.compile(r"-?\d+(?:\.\d+)?")
_VAR = re.compile(r"var\(\s*(--[A-Za-z0-9_-]+)")
_DEFINED = re.compile(r"^\s*(--[A-Za-z0-9_-]+):", re.MULTILINE)


def value_text(token: LayoutToken) -> str:
    if token.unit in ("mm", "pt", "em", "ex"):
        return f"{token.value} {token.unit}"
    if token.unit == "ratio":
        return f"{round(float(token.value) * 100, 2):g}%"
    if token.unit == "cmyk":
        parts = zip("CMYK", token.value.split(","), strict=True)
        return " ".join(f"{ink}{round(float(part) * 100, 2):g}" for ink, part in parts)
    return token.value


def cmyk_screen(value: str) -> str:
    """Naive CMYK to sRGB, without colour management: for an on-screen chip only."""
    # Whole percentages keep 255 x 10% at 25.5 rather than 25.4999...
    c, m, y, k = (round(float(part) * 100, 4) for part in value.split(","))
    return "#" + "".join(f"{round(255 * (100 - ink) * (100 - k) / 10000):02x}" for ink in (c, m, y))


def tokens_css(tokens: dict[str, LayoutToken], font_family: str) -> str:
    """Base tokens as CSS custom properties (`--<key>`) for the page preview."""
    lines = ["/* Generated at build time from data/layout_params.csv for the 印刷规格 preview. */", ":root {"]
    for key, token in tokens.items():
        if not _KEY.fullmatch(key):
            continue
        if token.unit in CSS_UNITS and _NUMBER.fullmatch(token.value):
            lines.append(f"  --{key}: {token.value}{CSS_UNITS[token.unit]};")
        elif token.unit == "cmyk" and len(token.value.split(",")) == 4:
            lines.append(f"  --{key}: {cmyk_screen(token.value)};")
    lines += [f"  --print-font-family: {font_family};", "}"]
    return "\n".join(lines) + "\n"


def _token(tokens: dict[str, LayoutToken], key: str) -> LayoutToken:
    token = tokens.get(key)
    if token is None:
        raise DesignSystemError(f"print token {key} is no longer in data/layout_params.csv")
    return token


def _rows(tokens: dict[str, LayoutToken], labels: dict[str, str]) -> list[dict]:
    return [{"label": label, "key": key, "value": value_text(_token(tokens, key))} for key, label in labels.items()]


def _type_row(tokens: dict[str, LayoutToken], style: dict) -> dict:
    prefix = style["prefix"]
    size = _token(tokens, f"{prefix}_font_size")
    leading = tokens.get(f"{prefix}_font_leading")
    upper = tokens.get(f"{prefix}_force_upper")
    sample = [f"{prop}:{token.value}{token.unit}" for prop, token in (("font-size", size), ("line-height", leading))
              if token is not None and token.unit in ("pt", "mm") and _NUMBER.fullmatch(token.value)]
    if upper is not None and upper.value == "1":
        sample.append("text-transform:uppercase")
    return {
        "label": style["label"], "prefix": prefix, "size": value_text(size),
        "leading": value_text(leading) if leading else None,
        "upper": None if upper is None else upper.value == "1",
        "sample": style.get("sample", SAMPLE), "sample_style": ";".join(sample),
    }


def _colors(tokens: dict[str, LayoutToken], colors: dict[str, dict], screen_tokens: set[str]) -> list[dict]:
    rows = []
    for key, entry in colors.items():
        token = _token(tokens, key)
        if token.unit != "cmyk" or len(token.value.split(",")) != 4:
            raise DesignSystemError(f"print colour {key} is not a CMYK value")
        screen = entry.get("screen")
        if screen and screen not in screen_tokens:
            raise DesignSystemError(f"print colour {key}: the live stylesheet no longer declares {screen}")
        rows.append({"name": entry["name"], "swatch": entry["swatch"], "key": key, "value": value_text(token),
                     "chip": cmyk_screen(token.value), "screen": screen, "note": inline(entry.get("note", ""))})
    return rows


def _preview(assets: Path, defined: set[str]) -> dict[str, str]:
    css = (assets / CONTENT_DIR / f"{PRINT_PAGE}.css").read_text(encoding="utf-8")
    markup = (assets / CONTENT_DIR / f"{PRINT_PAGE}.html").read_text(encoding="utf-8")
    unknown = sorted(set(_VAR.findall(css)) - defined)
    if unknown:
        raise DesignSystemError(f"print page preview uses tokens the table no longer defines: {unknown}")
    if re.search(r"(?:src|href)\s*=", markup) or "@import" in css or "url(" in css:
        raise DesignSystemError("the print page preview may not load files")
    return {"css": css, "markup": markup}


def print_spec(content: dict, assets: Path, root: Path, *, font_family: str, screen_tokens: set[str]) -> dict[str, Any]:
    """The 印刷规格 context: base values only; `lang_*` density overrides stay in the table."""
    section = content["print"]
    tokens = load_layout_tokens(Paths(root=root).layout_params_csv)
    base = {key: token for key, token in tokens.items() if not key.startswith("lang_")}
    css = tokens_css(base, font_family)
    return {
        "intro": [inline(text) for text in section.get("intro", [])],
        "page": _rows(base, section["page"]),
        "type": [_type_row(base, style) for style in section["type"]],
        "colors": _colors(base, section["colors"], screen_tokens),
        "geometry": [{"title": group["title"], "rows": _rows(base, group["keys"])} for group in section["geometry"]],
        "sha256": layout_tokens_sha256(tokens), "token_count": len(base),
        "tokens_css": css, "preview": _preview(assets, set(_DEFINED.findall(css))),
    }


def print_page_document(markup: str) -> str:
    """The actual-size page preview; tokens.css and page.css sit beside it."""
    return (
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        '<meta name="robots" content="noindex,nofollow">\n'
        "<title>印刷页 · 设计系统预览</title>\n"
        '<link rel="stylesheet" href="tokens.css">\n<link rel="stylesheet" href="page.css">\n'
        f'</head>\n<body class="ds-print">\n<main class="pp-stage">\n{markup}</main>\n</body>\n</html>\n'
    )


__all__ = ["PRINT_PAGE", "cmyk_screen", "print_page_document", "print_spec", "tokens_css", "value_text"]
