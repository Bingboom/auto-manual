from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PrefaceTemplateTests(unittest.TestCase):
    def test_shared_source_preface_should_keep_multilingual_notice_blocks(self) -> None:
        text = (ROOT / "docs" / "templates" / "page_shared" / "en" / "00_preface.rst").read_text(encoding="utf-8")

        # The V2.0 JE-1000F master (2026-06-05) drops the language-scope
        # lead line and marks each section with a brand-dark language tag
        # (\HBLangTagLine) instead of a bold text heading; the bold
        # headings remain as the non-latex (html/word) fallback.
        self.assertNotIn("|MANUAL_LANGUAGE_SCOPE|", text)
        self.assertIn("\\HBLangTagLine{EN}{IMPORTANT}", text)
        self.assertIn("\\HBLangTagLine{FR}{IMPORTANT}", text)
        self.assertIn("\\HBLangTagLine{ES}{IMPORTANTE}", text)
        self.assertIn("**IMPORTANT**", text)
        self.assertIn("FR IMPORTANT", text)
        self.assertIn("ES IMPORTANTE", text)

    def test_us_review_preface_should_keep_latex_page_component_contract(self) -> None:
        text = (ROOT / "docs" / "_review" / "JE-1000F" / "US" / "page" / "00_preface.rst").read_text(
            encoding="utf-8"
        )

        self.assertIn(r"\HBPrefacePageBegin", text)
        self.assertIn(r"\HBLangTagLine{EN}{IMPORTANT}", text)
        self.assertIn(r"\HBLangTagLine{FR}{IMPORTANT}", text)
        self.assertIn(r"\HBLangTagLine{ES}{IMPORTANTE}", text)
        self.assertIn(r"\HBPrefacePageEnd", text)

    def test_us_inbox_pages_should_end_with_explicit_page_boundary(self) -> None:
        for lang in ("en", "fr", "es"):
            text = (
                ROOT / "docs" / "templates" / "page_shared" / lang / "02_whats_in_the_box.rst"
            ).read_text(encoding="utf-8")
            self.assertIn(r"\HBInBoxThree", text)
            self.assertIn(r"\HBTipBlock", text)
            self.assertIn(r"\HBPageBreak", text)

    def test_us_spanish_app_and_back_cover_should_use_page_components(self) -> None:
        app_text = (
            ROOT / "docs" / "templates" / "page_shared" / "es" / "12_app_setup_placeholder.rst"
        ).read_text(encoding="utf-8")
        back_text = (
            ROOT / "docs" / "templates" / "page_shared" / "en" / "99_back_cover.rst"
        ).read_text(encoding="utf-8")

        self.assertIn(r"\HBPageBreak", app_text)
        self.assertIn(r"\HBAppStep", app_text)
        self.assertIn(r"\HBAppNotice", app_text)
        self.assertIn(r"\HBBackCoverPage", back_text)

    def test_eu_preface_should_cover_all_merged_languages(self) -> None:
        text = (ROOT / "docs" / "templates" / "page_eu" / "00_preface.rst").read_text(encoding="utf-8")
        config_text = (ROOT / "configs/config.eu.yaml").read_text(encoding="utf-8")
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
        maintenance_text = (
            ROOT / "docs" / "templates" / "page_shared" / "en" / "01_user_maintenance_instructions.rst"
        ).read_text(encoding="utf-8")

        self.assertIn("IMPORTANT SAFETY INFORMATION", text)
        self.assertNotIn("USER MAINTENANCE INSTRUCTIONS", text)
        self.assertIn("USER MAINTENANCE INSTRUCTIONS", maintenance_text)
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
