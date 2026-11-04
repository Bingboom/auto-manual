"""Keep pre-#1382 cold-replay comparisons on their reviewed stylesheet list.

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


def _pre_rowspan_divider_contracts(target: Path) -> Path:
    source = stylesheets.get_paths().renderer_contracts_dir
    for name in stylesheets.WEB_STYLESHEET_PARTS:
        text = (source / name).read_text(encoding="utf-8")
        if name == stylesheets.WEB_STYLESHEET_NAME:
            if _ROWSPAN_DIVIDER_RULE not in text:
                raise AssertionError("troubleshooting divider rule changed; update the historical stylesheet")
            text = text.replace(_ROWSPAN_DIVIDER_RULE, _PRE_ROWSPAN_DIVIDER_RULE)
        (target / name).write_text(text, encoding="utf-8")
    return target


def pre_four_control_styles(test):
    """Run an immutable edition's byte comparison before the new module exists."""
    @wraps(test)
    def run(*args, **kwargs):
        parts = tuple(part for part in stylesheets.WEB_STYLESHEET_PARTS
                      if part != "web_app_control_labels.css")
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(stylesheets, "WEB_STYLESHEET_PARTS", parts):
            contracts = _pre_rowspan_divider_contracts(Path(tmp))
            paths = SimpleNamespace(renderer_contracts_dir=contracts)
            with mock.patch.object(stylesheets, "get_paths", return_value=paths):
                return test(*args, **kwargs)
    return run
