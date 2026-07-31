from __future__ import annotations

import hashlib
import re
import unittest
from pathlib import Path

from tools.word_bundle_common import apply_rst_substitutions


ROOT = Path(__file__).resolve().parents[1]
LOCALIZED_COPY = ROOT / "tests" / "fixtures" / "phase2" / "Localized_Copy.csv"

COPY_KEYS = {
    "product_overview.page_title",
    "product_overview.front_view",
    "product_overview.right_side_view",
    "product_overview.part.handle",
    "product_overview.part.lcd",
    "product_overview.part.led_light_button",
    "product_overview.part.led_light",
}

CASES = {
    "es": (
        ROOT / "docs" / "templates" / "page_us-es" / "03_product_overview_placeholder.rst",
        "fe36023403e4c1067e11c57cd86742d7c02335ba6cafa4309648d38b2fe520e7",
    ),
    "fr": (
        ROOT / "docs" / "templates" / "page_us-fr" / "03_product_overview_placeholder.rst",
        "b5e4eb97f3c69510b00be70a0bd2f657231fa690c1b244453d78e1c946e2bf40",
    ),
    "pt-BR": (
        ROOT / "docs" / "templates" / "page_us-pt-br" / "03_product_overview_placeholder.rst",
        "9ba434f2170a8fe23a694d96dee3f10d74c4164739cb509c056b86e4a47493a4",
    ),
}


class ProductOverviewCopyPilotTests(unittest.TestCase):
    def test_localized_templates_resolve_to_pre_migration_bytes(self) -> None:
        for lang, (path, expected_sha256) in CASES.items():
            with self.subTest(lang=lang):
                source = path.read_text(encoding="utf-8")
                keys = set(re.findall(r"\{\{\s*copy:([A-Za-z0-9_.:-]+)\s*\}\}", source))
                self.assertTrue(COPY_KEYS.issubset(keys))

                rendered = apply_rst_substitutions(
                    source,
                    {},
                    {
                        "localized_copy_csv": str(LOCALIZED_COPY),
                        "lang": lang,
                        "model": "JE-1000F",
                        "region": "US",
                    },
                )
                self.assertNotIn("{{ copy:", rendered)
                self.assertEqual(
                    expected_sha256,
                    hashlib.sha256(rendered.encode("utf-8")).hexdigest(),
                )


if __name__ == "__main__":
    unittest.main()
