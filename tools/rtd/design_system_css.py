"""Read declared values from the live Web stylesheet for the 设计系统 page.

A deliberately small reader: comments are dropped, top-level and grouping
(@media / @supports / @container) rules are kept in cascade order, and every
other at-rule is skipped. It answers "what does this exact selector declare",
which is all the page needs; it is not a general CSS engine.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

from tools.utils.path_utils import get_paths
from tools.web.stylesheets import WEB_STYLESHEET_PARTS

_COMMENT = re.compile(r"/\*.*?\*/", re.S)
_GROUPING = ("@media", "@supports", "@container")


@dataclass(frozen=True)
class CssRule:
    context: str
    selectors: tuple[str, ...]
    declarations: dict[str, str]


def live_stylesheet_text() -> str:
    """The published web_manual.css, assembled exactly as tools.web.stylesheets does."""
    contracts = get_paths().renderer_contracts_dir
    return "\n\n".join(
        (contracts / name).read_text(encoding="utf-8").rstrip() for name in WEB_STYLESHEET_PARTS
    ) + "\n"


def _split_top_level(text: str, separator: str) -> list[str]:
    parts, depth, quote, start = [], 0, "", 0
    for index, char in enumerate(text):
        if quote:
            if char == quote:
                quote = ""
        elif char in "\"'":
            quote = char
        elif char in "([":
            depth += 1
        elif char in ")]":
            depth -= 1
        elif char == separator and depth == 0:
            parts.append(text[start:index])
            start = index + 1
    parts.append(text[start:])
    return parts


def _normalize(selector: str) -> str:
    return " ".join(selector.split())


def _declarations(block: str) -> dict[str, str]:
    result = {}
    for item in _split_top_level(block, ";"):
        name, colon, value = item.partition(":")
        if colon and name.strip():
            result[name.strip().lower()] = " ".join(value.replace("!important", "").split())
    return result


def _block_end(text: str, open_index: int) -> int:
    depth = 0
    for index in range(open_index, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return index
    raise ValueError("unbalanced braces in the Web stylesheet")


def _parse(text: str, context: str, rules: list[CssRule]) -> None:
    position = 0
    while True:
        open_index = text.find("{", position)
        if open_index < 0:
            return
        prelude = text[position:open_index].strip()
        close_index = _block_end(text, open_index)
        body = text[open_index + 1:close_index]
        if prelude.startswith("@"):
            if prelude.startswith(_GROUPING):
                _parse(body, " ".join(filter(None, (context, _normalize(prelude)))), rules)
        elif prelude:
            selectors = tuple(_normalize(item) for item in _split_top_level(prelude, ",") if item.strip())
            rules.append(CssRule(context, selectors, _declarations(body)))
        position = close_index + 1


def parse_css(text: str) -> list[CssRule]:
    rules: list[CssRule] = []
    _parse(_COMMENT.sub("", text), "", rules)
    return rules


def declared(rules: list[CssRule], selector: str, prop: str, *, context: str = "") -> str | None:
    """The last value a rule with exactly this selector declares, in cascade order."""
    wanted, value = _normalize(selector), None
    for rule in rules:
        if rule.context == context and wanted in rule.selectors and prop in rule.declarations:
            value = rule.declarations[prop]
    return value


def class_names(rules: list[CssRule]) -> set[str]:
    """Every class the stylesheet can select, for preview-markup drift checks."""
    names: set[str] = set()
    for rule in rules:
        for selector in rule.selectors:
            names.update(re.findall(r"\.(-?[_a-zA-Z][\w-]*)", selector))
    return names


__all__ = ["CssRule", "class_names", "declared", "live_stylesheet_text", "parse_css"]
