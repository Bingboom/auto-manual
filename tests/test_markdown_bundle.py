from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest import mock

from tools import markdown_bundle


class MarkdownBundleTests(unittest.TestCase):
    def test_resolve_markdown_writer_should_prefer_native_myst(self) -> None:
        with mock.patch.object(
            markdown_bundle.subprocess,
            "run",
            return_value=SimpleNamespace(stdout="gfm\nmyst\ncommonmark_x\n"),
        ):
            self.assertEqual("myst", markdown_bundle.resolve_markdown_writer("pandoc"))

    def test_resolve_markdown_writer_should_fallback_to_myst_compatible_commonmark(self) -> None:
        with mock.patch.object(
            markdown_bundle.subprocess,
            "run",
            return_value=SimpleNamespace(stdout="gfm\ncommonmark_x\nmarkdown\n"),
        ):
            self.assertEqual(markdown_bundle.MYST_COMPATIBLE_WRITER, markdown_bundle.resolve_markdown_writer("pandoc"))


if __name__ == "__main__":
    unittest.main()
