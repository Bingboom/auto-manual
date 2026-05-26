from __future__ import annotations

import unittest

from tools.config_pages import (
    CoverPdfPage,
    CsvPage,
    GeneratedPage,
    PdfInsertPage,
    RstIncludePage,
    parse_config_pages,
    parse_config_pages_or_raise,
)


class TestConfigPages(unittest.TestCase):
    def test_parse_config_pages_should_build_typed_pages(self) -> None:
        pages, issues = parse_config_pages(
            [
                {"type": "cover_pdf", "file": "cover.pdf"},
                {"type": "csv_page", "page": "safety", "source": "phase2", "langs": ["en"]},
                {
                    "type": "generated_page",
                    "page": "03_product_overview",
                    "engine": "draft_v1",
                    "recipe": "templates/recipes/03_product_overview.yaml",
                    "template": "templates/page/03_product_overview_placeholder.rst",
                    "langs": ["en"],
                    "include_dir": "generated/{model}/draft",
                },
                {"type": "pdf_insert", "file_map": {"en": "overview.pdf"}, "langs": ["en"]},
                {"type": "rst_include", "file": "templates/chapter.rst", "lang": "en"},
            ],
            default_languages=["en"],
        )

        self.assertEqual([], issues)
        self.assertIsInstance(pages[0], CoverPdfPage)
        self.assertIsInstance(pages[1], CsvPage)
        self.assertIsInstance(pages[2], GeneratedPage)
        self.assertIsInstance(pages[3], PdfInsertPage)
        self.assertIsInstance(pages[4], RstIncludePage)

    def test_parse_config_pages_should_apply_default_languages(self) -> None:
        pages, issues = parse_config_pages(
            [
                {"type": "csv_page", "page": "spec", "source": "phase2"},
                {"type": "pdf_insert", "file_map": {"en": "a.pdf", "fr": "b.pdf"}},
            ],
            default_languages=["en", "fr"],
        )
        self.assertEqual([], issues)
        self.assertEqual(("en", "fr"), pages[0].langs)
        self.assertEqual(("en", "fr"), pages[1].langs)

    def test_parse_config_pages_should_report_invalid_fields(self) -> None:
        _pages, issues = parse_config_pages(
            [
                {"type": "csv_page", "page": "spec", "source": "other"},
                {"type": "generated_page", "page": "spec", "engine": "other", "recipe": "x", "template": "y"},
                {"type": "rst_include", "file": " ", "lang": 1},
            ],
            default_languages=["en"],
        )
        error_msgs = [i.msg for i in issues if i.level == "ERROR"]
        self.assertTrue(any("csv_page.source invalid" in msg for msg in error_msgs))
        self.assertTrue(any("generated_page.engine invalid" in msg for msg in error_msgs))
        self.assertTrue(any("rst_include requires non-empty file" in msg for msg in error_msgs))

    def test_parse_config_pages_or_raise_should_fail_fast_on_first_error(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "config.pages: pages\\[1\\]\\.type invalid"):
            parse_config_pages_or_raise(
                [{"type": "unknown"}],
                default_languages=["en"],
                error_prefix="config.pages",
            )


if __name__ == "__main__":
    unittest.main()
