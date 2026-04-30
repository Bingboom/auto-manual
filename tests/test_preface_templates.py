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


if __name__ == "__main__":
    unittest.main()
