from __future__ import annotations

import unittest

from tools.phase1 import renderers


class TestPhase1Renderers(unittest.TestCase):
    def _template(self) -> str:
        return "\n".join(
            [
                renderers.PH_TITLE_MAIN,
                renderers.PH_WARNING_TITLE,
                renderers.PH_TITLE_OPERATING,
                renderers.PH_LEAD_TOP,
                renderers.PH_SAVE_TITLE,
                renderers.PH_TOP,
                renderers.PH_BOTTOM,
            ]
        ) + "\n"

    def _blocks(self) -> list[dict[str, str]]:
        return [
            {
                "block_type": "title_main",
                "order": "1",
                "sku_scope": "ALL",
                "enabled": "1",
                "meta_json": "{}",
                "text_en": "IMPORTANT SAFETY INFORMATION",
            },
            {
                "block_type": "warning_title",
                "order": "2",
                "sku_scope": "ALL",
                "enabled": "1",
                "meta_json": "{}",
                "text_en": "WARNING TITLE",
            },
            {
                "block_type": "title_operating",
                "order": "3",
                "sku_scope": "ALL",
                "enabled": "1",
                "meta_json": "{}",
                "text_en": "OPERATING INSTRUCTIONS",
            },
            {
                "block_type": "lead_top",
                "order": "4",
                "sku_scope": "ALL",
                "enabled": "1",
                "meta_json": "{}",
                "text_en": "Lead paragraph",
            },
            {
                "block_type": "save_title",
                "order": "5",
                "sku_scope": "ALL",
                "enabled": "1",
                "meta_json": "{}",
                "text_en": "SAVE THESE INSTRUCTIONS",
            },
            {
                "block_type": "list_item",
                "order": "6",
                "sku_scope": "ALL",
                "enabled": "1",
                "meta_json": '{"list_part": "top"}',
                "text_en": "Top list item",
            },
            {
                "block_type": "list_item",
                "order": "7",
                "sku_scope": "ALL",
                "enabled": "1",
                "meta_json": '{"list_part": "bottom"}',
                "text_en": "Bottom list item",
            },
        ]

    def test_render_safety_page_happy_path(self) -> None:
        out = renderers.render_safety_page(
            template=self._template(),
            blocks=self._blocks(),
            sku_id="JB1000",
            lang="en",
            vars_map={},
        )
        self.assertIn("IMPORTANT SAFETY INFORMATION", out)
        self.assertIn("Top list item", out)
        self.assertIn("Bottom list item", out)

    def test_latex_escape_should_escape_common_special_chars(self) -> None:
        text = r"50%_off #1 & more $x$ \\macro ~^"
        escaped = renderers.latex_arg_escape(text)

        # Desired: common LaTeX-sensitive characters are escaped.
        self.assertIn(r"\%", escaped)
        self.assertIn(r"\_", escaped)
        self.assertIn(r"\#", escaped)
        self.assertIn(r"\&", escaped)
        self.assertIn(r"\$", escaped)

    def test_invalid_meta_json_should_fail_fast_with_clear_error(self) -> None:
        blocks = self._blocks()
        # Break top list metadata to reproduce silent-fail path.
        for row in blocks:
            if row.get("block_type") == "list_item" and "Top" in row.get("text_en", ""):
                row["meta_json"] = "{bad-json"

        with self.assertRaisesRegex(ValueError, "meta_json|json|line"):
            renderers.render_safety_page(
                template=self._template(),
                blocks=blocks,
                sku_id="JB1000",
                lang="en",
                vars_map={},
            )

    def _spec_template(self) -> str:
        return "\n".join(
            [
                renderers.PH_SPEC_TITLE_MAIN,
                renderers.PH_SPEC_TITLE_MAIN_HTML,
                renderers.PH_SPEC_SECTIONS_LATEX,
                renderers.PH_SPEC_NOTES_LATEX,
                renderers.PH_SPEC_FOOTNOTES_LATEX,
                renderers.PH_SPEC_SECTIONS_HTML,
                renderers.PH_SPEC_NOTES_HTML,
                renderers.PH_SPEC_FOOTNOTES_HTML,
            ]
        ) + "\n"

    def _spec_blocks(self) -> list[dict[str, str]]:
        return [
            {
                "block_type": "title_main",
                "order": "100",
                "sku_scope": "ALL",
                "enabled": "1",
                "meta_json": "{}",
                "text_en": "SPECIFICATIONS",
            },
            {
                "block_type": "section_title",
                "order": "110",
                "sku_scope": "ALL",
                "enabled": "1",
                "meta_json": "{}",
                "text_en": "GENERAL INFO",
            },
            {
                "block_type": "row_item",
                "order": "111",
                "sku_scope": "ALL",
                "enabled": "1",
                "meta_json": "{}",
                "text_en": "Product Name || Demo Product",
            },
            {
                "block_type": "row_item",
                "order": "112",
                "sku_scope": "ALL",
                "enabled": "1",
                "meta_json": "{}",
                "text_en": "Model No. || DEMO-1000",
            },
            {
                "block_type": "note_line",
                "order": "150",
                "sku_scope": "ALL",
                "enabled": "1",
                "meta_json": "{}",
                "text_en": "* Demo note line",
            },
            {
                "block_type": "footnote",
                "order": "160",
                "sku_scope": "ALL",
                "enabled": "1",
                "meta_json": "{}",
                "text_en": "(1) Demo footnote",
            },
        ]

    def test_render_spec_page_happy_path(self) -> None:
        out = renderers.render_spec_page(
            template=self._spec_template(),
            blocks=self._spec_blocks(),
            sku_id="JB1000",
            lang="en",
            vars_map={},
        )
        self.assertIn("SPECIFICATIONS", out)
        self.assertIn("GENERAL INFO", out)
        self.assertIn("Product Name", out)
        self.assertIn("Demo footnote", out)

    def test_render_spec_page_row_without_delimiter_should_fail(self) -> None:
        blocks = self._spec_blocks()
        for row in blocks:
            if row.get("block_type") == "row_item":
                row["text_en"] = "bad row format"
                break

        with self.assertRaisesRegex(ValueError, "left \\|\\| right"):
            renderers.render_spec_page(
                template=self._spec_template(),
                blocks=blocks,
                sku_id="JB1000",
                lang="en",
                vars_map={},
            )


if __name__ == "__main__":
    unittest.main()
