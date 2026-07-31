from __future__ import annotations

import hashlib
import unittest
from pathlib import Path

from tools.page_contracts import load_page_contracts, required_page_values_for_lang
from tools.utils.spec_master import resolve_template_substitutions_from_spec_master
from tools.word_bundle_common import apply_rst_substitutions


ROOT = Path(__file__).resolve().parents[1]
SPEC_MASTER = ROOT / "tests" / "fixtures" / "phase2" / "Spec_Master.csv"
LONG_TAIL_SPEC_MASTER = ROOT / "tests" / "fixtures" / "pv_input_range" / "Spec_Master.csv"

CASES = {
    "en": (SPEC_MASTER, "JE-1000F", "US", "635dff46139d296036f26d9c5937f3bf5239088d8d4ed3870c674d2544e3d788"),
    "fr": (SPEC_MASTER, "JE-1000F", "US", "d1b136c55a74e9edba2b26fccf6293a1585cf508e6fc9d5a0020b2c4d8047e1d"),
    "es": (SPEC_MASTER, "JE-1000F", "US", "2a22ee4048cc16df40f0bff81e13c7b46a6ecf60a6b13ef22dcdbf1ef6e78453"),
    "pt-BR": (LONG_TAIL_SPEC_MASTER, "JE-1500D", "pt-BR", "1e734e6b9e80f01c466d0258e1a424dfb2a0eec892bde47a69321b04d67ca5d4"),
    "de": (SPEC_MASTER, "JE-1000F", "EU", "bf7c790b17badebf1019eafd99d1616c937bdf755f9ce6b491e4095db7894e96"),
    "it": (SPEC_MASTER, "JE-1000F", "EU", "5e287d0de2c8448e3196ce9b1ca24cc11f0e6c22c0e3ef30267154b8f4aedc8d"),
    "uk": (SPEC_MASTER, "JE-1000F", "EU", "ac9ea9d794fe7968dcbd6f6999818e8dee12cdbcdab5cd3fc7da2e4b7055847c"),
    "ko": (LONG_TAIL_SPEC_MASTER, "JE-1000F", "KR", "028cc35e322607f5bd111bf353bc60e4b1eb72967c9530f5ffef967402c62086"),
}


class PvInputRangePlaceholderTests(unittest.TestCase):
    def test_page_contract_requires_semantic_page_value(self) -> None:
        contracts = load_page_contracts(ROOT / "docs" / "templates" / "contracts")
        contract = next(item for item in contracts if item.page_id == "08_charging_methods")

        self.assertEqual(8, len(contract.source_files))
        self.assertEqual(("PV_INPUT_RANGE",), contract.required_placeholders["default"])
        selectors = required_page_values_for_lang(contract, "ko")
        self.assertEqual(1, len(selectors))
        self.assertEqual("pv_input_range", selectors[0].row_key)
        self.assertEqual(("charging_methods",), selectors[0].pages)
        self.assertEqual("page_value", selectors[0].usage_type)

    def test_shared_templates_resolve_to_pre_migration_bytes(self) -> None:
        for lang, (spec_master, model, region, expected_sha256) in CASES.items():
            with self.subTest(lang=lang):
                path = ROOT / "docs" / "templates" / "page_shared" / lang / "08_charging_methods.rst"
                source = path.read_text(encoding="utf-8")
                substitutions = resolve_template_substitutions_from_spec_master(
                    spec_master,
                    model=model,
                    region=region,
                    lang=lang,
                )

                self.assertIn("|PV_INPUT_RANGE|", source)
                self.assertIn("PV_INPUT_RANGE", substitutions)
                rendered = apply_rst_substitutions(
                    source,
                    {"PV_INPUT_RANGE": substitutions["PV_INPUT_RANGE"]},
                    {},
                )
                self.assertNotIn("|PV_INPUT_RANGE|", rendered)
                self.assertEqual(
                    expected_sha256,
                    hashlib.sha256(rendered.encode("utf-8")).hexdigest(),
                )

    def test_japanese_and_chinese_templates_remain_outside_this_slice(self) -> None:
        paths = (
            ROOT / "docs" / "templates" / "page_jp" / "08_charging_methods.rst",
            ROOT / "docs" / "templates" / "page_zh" / "08_charging_methods.rst",
        )
        for path in paths:
            with self.subTest(path=path):
                self.assertNotIn("|PV_INPUT_RANGE|", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
