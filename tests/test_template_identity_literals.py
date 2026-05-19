from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestTemplateIdentityLiterals(unittest.TestCase):
    def test_reusable_templates_should_not_pin_je1000_product_name(self) -> None:
        template_root = ROOT / "docs" / "templates"
        offenders: list[str] = []

        for path in template_root.rglob("*.rst"):
            text = path.read_text(encoding="utf-8")
            if "Jackery Explorer 1000" in text:
                offenders.append(path.relative_to(ROOT).as_posix())

        self.assertEqual([], offenders)
