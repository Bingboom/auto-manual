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

    def test_generated_page_should_apply_model_recipe_and_template_override(self) -> None:
        pages, issues = parse_config_pages(
            [
                {
                    "type": "generated_page",
                    "page": "03_product_overview",
                    "engine": "draft_v1",
                    "recipe": "templates/recipes/shared.yaml",
                    "template": "templates/page/shared.rst",
                    "model_overrides": {
                        "JE-300E": {
                            "recipe": "templates/recipes/je300e.yaml",
                            "template": "templates/page/je300e.rst",
                        }
                    },
                }
            ],
            default_languages=["en"],
            model="JE-300E",
        )

        self.assertEqual([], issues)
        self.assertEqual("templates/recipes/je300e.yaml", pages[0].recipe)
        self.assertEqual("templates/page/je300e.rst", pages[0].template)

    def test_generated_page_should_keep_shared_paths_for_other_models(self) -> None:
        pages, issues = parse_config_pages(
            [
                {
                    "type": "generated_page",
                    "page": "03_product_overview",
                    "engine": "draft_v1",
                    "recipe": "templates/recipes/shared.yaml",
                    "template": "templates/page/shared.rst",
                    "model_overrides": {
                        "JE-300E": {
                            "recipe": "templates/recipes/je300e.yaml",
                            "template": "templates/page/je300e.rst",
                        }
                    },
                }
            ],
            default_languages=["en"],
            model="JE-1000F",
        )

        self.assertEqual([], issues)
        self.assertEqual("templates/recipes/shared.yaml", pages[0].recipe)
        self.assertEqual("templates/page/shared.rst", pages[0].template)

    def test_generated_page_should_reject_invalid_model_override(self) -> None:
        _pages, issues = parse_config_pages(
            [
                {
                    "type": "generated_page",
                    "page": "03_product_overview",
                    "engine": "draft_v1",
                    "recipe": "shared.yaml",
                    "template": "shared.rst",
                    "model_overrides": {"JE-300E": {"unknown": "bad"}},
                }
            ],
            default_languages=["en"],
            model="JE-300E",
        )

        self.assertTrue(
            any("has unsupported fields: unknown" in issue.msg for issue in issues)
        )

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

    def test_rst_include_lang_blocks_defaults_off_and_parses(self) -> None:
        pages, issues = parse_config_pages(
            [
                {"type": "rst_include", "file": "a.rst", "lang": "en"},
                {"type": "rst_include", "file": "b.rst", "lang": "en",
                 "lang_blocks": True},
            ],
            default_languages=["en"],
        )
        self.assertEqual([], issues)
        self.assertFalse(pages[0].lang_blocks)
        self.assertTrue(pages[1].lang_blocks)

    def test_lang_blocks_must_be_boolean(self) -> None:
        _pages, issues = parse_config_pages(
            [{"type": "rst_include", "file": "a.rst", "lang": "en",
              "lang_blocks": "yes"}],
            default_languages=["en"],
        )
        self.assertTrue(any("lang_blocks must be a boolean" in i.msg
                            for i in issues if i.level == "ERROR"))

    def test_lang_blocks_is_rejected_on_other_page_types(self) -> None:
        # A mis-annotated page must fail rather than silently trim nothing.
        _pages, issues = parse_config_pages(
            [{"type": "csv_page", "page": "spec", "source": "phase2",
              "lang_blocks": True}],
            default_languages=["en"],
        )
        self.assertTrue(any("only supported on rst_include" in i.msg
                            for i in issues if i.level == "ERROR"))

    def test_rst_include_ordinal_neutral_defaults_off_and_parses(self) -> None:
        pages, issues = parse_config_pages(
            [
                {"type": "rst_include", "file": "a.rst", "lang": "en"},
                {"type": "rst_include", "file": "b.rst", "lang": "en",
                 "ordinal_neutral": True},
            ],
            default_languages=["en"],
        )
        self.assertEqual([], issues)
        self.assertFalse(pages[0].ordinal_neutral)
        self.assertTrue(pages[1].ordinal_neutral)

    def test_ordinal_neutral_must_be_boolean(self) -> None:
        _pages, issues = parse_config_pages(
            [{"type": "rst_include", "file": "a.rst", "lang": "en",
              "ordinal_neutral": "yes"}],
            default_languages=["en"],
        )
        self.assertTrue(any("ordinal_neutral must be a boolean" in i.msg
                            for i in issues if i.level == "ERROR"))

    def test_ordinal_neutral_is_rejected_on_other_page_types(self) -> None:
        # A mis-annotated page must fail rather than silently renumber the tail.
        _pages, issues = parse_config_pages(
            [{"type": "csv_page", "page": "spec", "source": "phase2",
              "ordinal_neutral": True}],
            default_languages=["en"],
        )
        self.assertTrue(any(
            "ordinal_neutral is only supported on rst_include" in i.msg
            for i in issues if i.level == "ERROR"))

    def test_parse_config_pages_or_raise_should_fail_fast_on_first_error(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "config.pages: pages\\[1\\]\\.type invalid"):
            parse_config_pages_or_raise(
                [{"type": "unknown"}],
                default_languages=["en"],
                error_prefix="config.pages",
            )


if __name__ == "__main__":
    unittest.main()
