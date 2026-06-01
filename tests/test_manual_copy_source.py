from __future__ import annotations

import unittest

from tools.manual_copy_source import (
    ManualCopyConflictError,
    build_localized_copy_rows,
    build_spec_title_rows,
    build_status_word_rows,
)


class TestManualCopySource(unittest.TestCase):
    def test_build_localized_copy_rows_should_fallback_to_source_for_missing_tm_languages(self) -> None:
        rows, missing = build_localized_copy_rows(
            [
                {
                    "copy_key": "symbols.header_symbol",
                    "page_id": "symbols",
                    "copy_type": "table_header",
                    "Market": "ALL",
                    "Model": "ALL",
                    "Source_lang": "en",
                    "Is_Latest": "TRUE",
                    "Version": "V1.0",
                    "source_text": "Symbol",
                }
            ],
            [
                {
                    "en": "Symbol",
                    "zh": "符号",
                    "jp": "記号",
                    "用途标签": "manual_copy",
                }
            ],
        )

        self.assertEqual("符号", rows[0]["text_zh"])
        self.assertEqual("Symbol", rows[0]["text_fr"])
        self.assertIn(("symbols.header_symbol", "fr"), [(item.copy_key, item.target_lang) for item in missing])

    def test_build_localized_copy_rows_should_reject_conflicting_tm_rows(self) -> None:
        with self.assertRaises(ManualCopyConflictError):
            build_localized_copy_rows(
                [
                    {
                        "copy_key": "symbols.header_meaning",
                        "page_id": "symbols",
                        "copy_type": "table_header",
                        "Source_lang": "en",
                        "Is_Latest": "TRUE",
                        "source_text": "Meaning",
                    }
                ],
                [
                    {"en": "Meaning", "zh": "含义", "用途标签": "manual_copy"},
                    {"en": "Meaning", "zh": "意义", "用途标签": "manual_copy"},
                ],
            )

    def test_build_status_word_rows_should_keep_only_status_marker_rows(self) -> None:
        rows = build_status_word_rows(
            [
                {"en": "On", "zh": "点亮", "是否为 status word": "Y"},
                {"en": "Symbol", "zh": "符号", "用途标签": "manual_copy"},
            ]
        )

        self.assertEqual(1, len(rows))
        self.assertEqual("On", rows[0]["en"])
        self.assertEqual("Y", rows[0]["是否为 status word"])

    def test_build_spec_title_rows_should_derive_compatible_title_csv(self) -> None:
        rows = build_spec_title_rows(
            [
                {
                    "copy_key": "spec.section.input_ports",
                    "page_id": "specifications",
                    "copy_type": "section_title",
                    "Source_lang": "en",
                    "Is_Latest": "TRUE",
                    "source_text": "INPUT PORTS",
                    "section_order": "2",
                },
                {
                    "copy_key": "product_overview.page_title",
                    "page_id": "03_product_overview",
                    "copy_type": "page_title",
                    "Source_lang": "en",
                    "Is_Latest": "TRUE",
                    "source_text": "PRODUCT OVERVIEW",
                },
            ],
            [
                {
                    "en": "INPUT PORTS",
                    "zh": "输入端口",
                    "jp": "入力ポート",
                    "fr": "PORTS D'ENTREE",
                    "用途标签": "manual_copy",
                }
            ],
        )

        self.assertEqual(1, len(rows))
        self.assertEqual("INPUT PORTS", rows[0]["title_en"])
        self.assertEqual("输入端口", rows[0]["title_zh"])
        self.assertEqual("2", rows[0]["section_order"])


if __name__ == "__main__":
    unittest.main()
