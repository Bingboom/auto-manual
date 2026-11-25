"""Keep pre-#1382 cold-replay comparisons on their reviewed stylesheet list and rules.

The original tests still compare every output byte, including CSS and its IR
hash. Current-style assembly and four-control layouts are tested separately.
This changes only the dependency supplied during those historical tests.
"""
import tempfile
from functools import wraps
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from tools.web import stylesheets

# #1666 kept the code/measures divider when the measures cell spans rows. The
# editions frozen before it were reviewed with the original selector.
_ROWSPAN_DIVIDER_RULE = (
    "/* A code cell can be the last DOM child while the measures cell spans rows. */\n"
    "#furo-main-content table.hb-troubleshooting-table tr > *:last-child:not(.hb-troubleshooting-code) {"
)
_PRE_ROWSPAN_DIVIDER_RULE = "#furo-main-content table.hb-troubleshooting-table tr > *:last-child {"

# The base-art label options (mobile_labels=scroll, label_density=compact) came
# later still; every edition frozen before #1666 was reviewed without them.
_BASE_ART_STYLESHEET = "web_base_art_components.css"
_LABEL_OPTION_SELECTOR = ':is([data-mobile-labels="overlay"], [data-mobile-labels="scroll"])'
_PRE_LABEL_OPTION_SELECTOR = '[data-mobile-labels="overlay"]'
_LABEL_OPTION_RULES = (
    "\n/* Scroll keeps the labels on the art at a readable size:",
    "\n/* Source-declared empty artwork region;",
)


def _pre_label_option_rules(text: str) -> str:
    start = text.find(_LABEL_OPTION_RULES[0])
    end = text.find(_LABEL_OPTION_RULES[1], start)
    if start < 0 or end < 0 or _LABEL_OPTION_SELECTOR not in text:
        raise AssertionError("base-art label option rules changed; update the historical stylesheet")
    return (text[:start] + text[end:]).replace(_LABEL_OPTION_SELECTOR, _PRE_LABEL_OPTION_SELECTOR)


def _pre_rowspan_divider_contracts(target: Path) -> Path:
    source = stylesheets.get_paths().renderer_contracts_dir
    for name in stylesheets.WEB_STYLESHEET_PARTS:
        text = (source / name).read_text(encoding="utf-8")
        if name == stylesheets.WEB_STYLESHEET_NAME:
            if _ROWSPAN_DIVIDER_RULE not in text:
                raise AssertionError("troubleshooting divider rule changed; update the historical stylesheet")
            text = text.replace(_ROWSPAN_DIVIDER_RULE, _PRE_ROWSPAN_DIVIDER_RULE)
        if name == _BASE_ART_STYLESHEET:
            text = _pre_label_option_rules(text)
        (target / name).write_text(text, encoding="utf-8")
    return target


def pre_rowspan_divider_styles(test):
    """Run a byte comparison of an edition frozen before the #1666 divider rule."""
    @wraps(test)
    def run(*args, **kwargs):
        with tempfile.TemporaryDirectory() as tmp:
            contracts = _pre_rowspan_divider_contracts(Path(tmp))
            paths = SimpleNamespace(renderer_contracts_dir=contracts)
            with mock.patch.object(stylesheets, "get_paths", return_value=paths):
                return test(*args, **kwargs)
    return run


def pre_four_control_styles(test):
    """Run an immutable edition's byte comparison before the new module exists."""
    @wraps(test)
    def run(*args, **kwargs):
        parts = tuple(part for part in stylesheets.WEB_STYLESHEET_PARTS
                      if part != "web_app_control_labels.css")
        with mock.patch.object(stylesheets, "WEB_STYLESHEET_PARTS", parts):
            return pre_rowspan_divider_styles(test)(*args, **kwargs)
    return run
