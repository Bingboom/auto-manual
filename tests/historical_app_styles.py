"""Keep pre-#1382 cold-replay comparisons on their reviewed stylesheet list.

The original tests still compare every output byte, including CSS and its IR
hash. Current-style assembly and four-control layouts are tested separately.
This changes only the dependency supplied during those historical tests.
"""
from functools import wraps
from unittest import mock

from tools.web import stylesheets


def pre_four_control_styles(test):
    """Run an immutable edition's byte comparison before the new module exists."""
    @wraps(test)
    def run(*args, **kwargs):
        parts = tuple(part for part in stylesheets.WEB_STYLESHEET_PARTS
                      if part != "web_app_control_labels.css")
        with mock.patch.object(stylesheets, "WEB_STYLESHEET_PARTS", parts):
            return test(*args, **kwargs)
    return run
