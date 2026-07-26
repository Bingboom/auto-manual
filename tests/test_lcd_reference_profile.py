from __future__ import annotations

import unittest

from tools.idml.lcd_reference_profile import (
    LcdReferenceProfileError,
    apply_lcd_reference_profile,
    validate_lcd_reference_profile,
)


class LcdReferenceProfileTests(unittest.TestCase):
    def test_validator_accepts_language_governed_icon_size(self) -> None:
        profile = {
            "icon_size_pt_by_language": {"en": 14.2, "fr": 14.2},
            "row_presentation": [{"source_no": "8", "display_no": "8"}],
        }
        self.assertEqual([], validate_lcd_reference_profile(profile))

    def test_validator_rejects_invalid_icon_sizes(self) -> None:
        for sizes in ({}, {"en": True}, {"en": 0}, {"en": float("inf")}, {"EN!": 14}):
            with self.subTest(sizes=sizes):
                issues = validate_lcd_reference_profile({
                    "icon_size_pt_by_language": sizes,
                    "row_presentation": [{"source_no": "8", "display_no": "8"}],
                })
                self.assertTrue(issues)

    def test_validator_accepts_language_governed_row_height(self) -> None:
        profile = {
            "row_presentation": [{
                "source_no": "8",
                "display_no": "8",
                "row_height_pt_by_language": {
                    "en": 23.042,
                    "fr": 17.97,
                    "es": 16.792,
                },
            }],
        }
        self.assertEqual([], validate_lcd_reference_profile(profile))

    def test_validator_rejects_invalid_row_heights(self) -> None:
        for heights in (
            {},
            {"en": True},
            {"en": 0},
            {"en": float("inf")},
            {"EN!": 10},
        ):
            with self.subTest(heights=heights):
                issues = validate_lcd_reference_profile({
                    "row_presentation": [{
                        "source_no": "8",
                        "display_no": "8",
                        "row_height_pt_by_language": heights,
                    }],
                })
                self.assertTrue(issues)

    def test_apply_selects_requested_language_without_mutating_source(self) -> None:
        source = [{"source_no": "8", "no": "8", "name": "Indicator"}]
        profile = {
            "icon_size_pt_by_language": {"en": 14.2, "fr": 13.8},
            "row_presentation": [{
                "source_no": "8",
                "display_no": "8",
                "row_height_pt_by_language": {"en": 23.042, "fr": 17.97},
            }],
        }

        rendered = apply_lcd_reference_profile(source, profile, language="fr-FR")

        self.assertEqual("17.97", rendered[0]["row_height_pt"])
        self.assertEqual("13.8", rendered[0]["icon_size_pt"])
        self.assertNotIn("row_height_pt", source[0])
        self.assertNotIn("icon_size_pt", source[0])

    def test_apply_fails_closed_without_governed_language(self) -> None:
        source = [{"source_no": "8", "no": "8"}]
        profile = {
            "row_presentation": [{
                "source_no": "8",
                "display_no": "8",
                "row_height_pt_by_language": {"en": 23.042},
            }],
        }

        with self.assertRaisesRegex(LcdReferenceProfileError, "no governed height"):
            apply_lcd_reference_profile(source, profile, language="fr")

    def test_apply_fails_closed_without_governed_icon_language(self) -> None:
        source = [{"source_no": "8", "no": "8"}]
        profile = {
            "icon_size_pt_by_language": {"en": 14.2},
            "row_presentation": [{"source_no": "8", "display_no": "8"}],
        }

        with self.assertRaisesRegex(LcdReferenceProfileError, "no governed size"):
            apply_lcd_reference_profile(source, profile, language="fr")


if __name__ == "__main__":
    unittest.main()
