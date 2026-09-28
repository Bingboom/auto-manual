"""Exact, source-positioned recovery of missing PDF text glyphs."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest
from unittest.mock import patch

from tools.frozen_pdf_glyphs import recover_pdf_glyphs
from tools.frozen_pdf_intake import load_pdf_book


ROOT = Path(__file__).resolve().parents[1]
RECIPE = ROOT / "manual_sources/JE-1000F/EU/nine-language/git-20260927-c38415f5/four-language"
PDF = Path("/private/tmp/je1000f-nine-language-intake/HTE153-nine-language-native-text-check.pdf")
AI = Path("/private/tmp/je1000f-nine-language-intake/HTE153-EU-9国语言-0923.ai")


@unittest.skipUnless(PDF.is_file() and AI.is_file(), "frozen native PDF and AI are unavailable")
class FrozenPDFGlyphTests(unittest.TestCase):
    def test_four_real_locales_recover_only_matching_ai_glyphs(self):
        for language in ("uk", "pt", "nl", "pl"):
            with self.subTest(language=language):
                original = load_pdf_book(PDF, language, RECIPE)
                recovered = recover_pdf_glyphs(original, AI)
                self.assertEqual(5, len(original["provenance"]["unresolved_text"]))
                self.assertEqual([], original["provenance"]["corrections_applied"])
                self.assertEqual(15, len(recovered["provenance"]["corrections_applied"]))
                self.assertEqual(15, len(recovered["provenance"]["original_pdf_text"]))
                self.assertEqual(
                    original["provenance"]["ai"]["sha256"],
                    recovered["provenance"]["glyph_recovery"]["ai_sha256"],
                )
                specifications = recovered["source"]["tables"]["specifications"]
                self.assertEqual(16, sum(
                    row["value"].count("⎓")
                    for rows in specifications["groups"].values() for row in rows
                ))
                self.assertFalse(any(
                    "\ufffd" in row["value"]
                    for rows in specifications["groups"].values() for row in rows
                ))
                page_blocks = [block["text"] for page in recovered["source"]["pages"]
                               for block in page["blocks_visual_order"]]
                self.assertFalse(any("\x1f" in text or "\ufffd" in text for text in page_blocks))
                self.assertTrue(all(detail["physical_page"] and detail["bbox"] and detail["before"]
                                    and detail["after"] and detail["reason"]
                                    for detail in recovered["provenance"]["corrections_applied"]))
                self.assertEqual(original["source"]["pages"][0]["text"],
                                 recovered["source"]["pages"][0]["text"])

    def test_ai_hash_must_match_provenance(self):
        original = load_pdf_book(PDF, "pl", RECIPE)
        with patch("tools.frozen_pdf_glyphs.file_sha256", return_value="0" * 64):
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                recover_pdf_glyphs(original, AI)
        self.assertEqual([], original["provenance"]["corrections_applied"])

    def test_other_character_difference_fails_without_mutating_input(self):
        original = load_pdf_book(PDF, "pl", RECIPE)
        damaged = deepcopy(original)
        damaged["source"]["tables"]["specifications"]["groups"]["inputs"][1]["value"] = (
            damaged["source"]["tables"]["specifications"]["groups"]["inputs"][1]["value"]
            .replace("11 V", "99 V")
        )
        with self.assertRaisesRegex(ValueError, "beyond missing glyphs"):
            recover_pdf_glyphs(damaged, AI)
        self.assertEqual([], damaged["provenance"]["corrections_applied"])

    def test_page_block_requires_same_bbox_text(self):
        original = load_pdf_book(PDF, "nl", RECIPE)
        damaged = deepcopy(original)
        block = next(
            block for page in damaged["source"]["pages"]
            for block in page["blocks_visual_order"] if "\x1f" in block["text"]
        )
        block["text"] = "different copy " + block["text"]
        with self.assertRaisesRegex(ValueError, "beyond missing glyphs"):
            recover_pdf_glyphs(damaged, AI)
        self.assertEqual([], damaged["provenance"]["corrections_applied"])


if __name__ == "__main__":
    unittest.main()
