from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PrefaceTemplateTests(unittest.TestCase):
    def test_shared_source_preface_should_keep_multilingual_notice_blocks(self) -> None:
        text = (ROOT / "docs" / "templates" / "page_shared" / "en" / "00_preface.rst").read_text(encoding="utf-8")

        self.assertIn("|MANUAL_LANGUAGE_SCOPE|", text)
        self.assertIn("**IMPORTANT**", text)
        self.assertIn("FR IMPORTANT", text)
        self.assertIn("ES IMPORTANTE", text)

    def test_eu_preface_should_cover_all_merged_languages(self) -> None:
        text = (ROOT / "docs" / "templates" / "page_eu" / "00_preface.rst").read_text(encoding="utf-8")
        config_text = (ROOT / "config.eu.yaml").read_text(encoding="utf-8")
        manifest_text = (ROOT / "docs" / "manifests" / "manual_eu.yaml").read_text(encoding="utf-8")

        self.assertIn("templates/page_eu/00_preface.rst", manifest_text)
        self.assertIn("English / French / Spanish / German / Italian / Ukrainian", config_text)
        for marker in (
            "**IMPORTANT**",
            "**FR IMPORTANT**",
            "**ES IMPORTANTE**",
            "**DE WICHTIG**",
            "**IT IMPORTANTE**",
            "**UK ВАЖЛИВО**",
        ):
            self.assertIn(marker, text)

    def test_eu_english_safety_should_not_use_us_only_safety_copy(self) -> None:
        text = (ROOT / "docs" / "templates" / "page_eu-en" / "safety_en.rst").read_text(encoding="utf-8")

        self.assertIn("SAFETY PRECAUTIONS FOR USE", text)
        self.assertIn("USER MAINTENANCE INSTRUCTIONS", text)
        for marker in (
            "GROUNDING INSTRUCTION",
            "18 inches",
            "(265°F)",
            "SAVE THESE INSTRUCTIONS",
            "workshop or repair facility",
        ):
            self.assertNotIn(marker, text)


if __name__ == "__main__":
    unittest.main()
