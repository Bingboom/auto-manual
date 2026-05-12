from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TemplateIdentityLiteralTests(unittest.TestCase):
    def test_reusable_templates_should_not_hardcode_je1000_product_name(self) -> None:
        template_paths = [
            ROOT / "docs/templates/page_eu-en/05_operation_guide_placeholder.rst",
            ROOT / "docs/templates/page_eu-de/05_operation_guide_placeholder.rst",
            ROOT / "docs/templates/page_eu-it/05_operation_guide_placeholder.rst",
            ROOT / "docs/templates/page_eu-uk/05_operation_guide_placeholder.rst",
            ROOT / "docs/templates/page_us-en/05_operation_guide_placeholder.rst",
            ROOT / "docs/templates/page_shared/fr/08_charging_methods.rst",
        ]

        for template_path in template_paths:
            with self.subTest(path=template_path.relative_to(ROOT).as_posix()):
                text = template_path.read_text(encoding="utf-8")
                self.assertNotIn("Jackery Explorer 1000", text)
                self.assertIn("|PRODUCT_NAME|", text)


if __name__ == "__main__":
    unittest.main()
