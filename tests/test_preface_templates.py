from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PrefaceTemplateTests(unittest.TestCase):
    def test_us_source_preface_should_not_embed_derived_language_notices(self) -> None:
        text = (ROOT / "docs" / "templates" / "page_us-en" / "00_preface.rst").read_text(encoding="utf-8")

        self.assertIn("**IMPORTANT**", text)
        self.assertNotIn("FR IMPORTANT", text)
        self.assertNotIn("ES IMPORTANTE", text)


if __name__ == "__main__":
    unittest.main()
