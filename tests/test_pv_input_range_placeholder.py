from __future__ import annotations

import hashlib
import unittest
from pathlib import Path

# The ko goldens moved once when the ko templates stopped printing the ambiguous
# 은(는) form and started naming a particle pair (|PRODUCT_NAME_JOSA_EUN|); the
# rendered diff was exactly those placeholder tokens, nothing else.
# The en/de/it/uk goldens moved when the solar and car figures' alt text
# stopped calling the figure a placeholder; the rendered diff was exactly
# those :alt: lines, nothing else.
from tools.page_contracts import load_page_contracts, required_page_values_for_lang
from tools.utils.spec_master import resolve_template_substitutions_from_spec_master
from tools.word.bundle_common import apply_rst_substitutions


ROOT = Path(__file__).resolve().parents[1]
SPEC_MASTER = ROOT / "tests" / "fixtures" / "phase2" / "Spec_Master.csv"
LONG_TAIL_SPEC_MASTER = ROOT / "tests" / "fixtures" / "pv_input_range" / "Spec_Master.csv"

CASES = {
    "en": (SPEC_MASTER, "JE-1000F", "US", "0c6a185ebc344c0b647aa3cd39d04b94bad3d70a81877155e526dfc592eb6003"),
    "fr": (SPEC_MASTER, "JE-1000F", "US", "d1b136c55a74e9edba2b26fccf6293a1585cf508e6fc9d5a0020b2c4d8047e1d"),
    "es": (SPEC_MASTER, "JE-1000F", "US", "2a22ee4048cc16df40f0bff81e13c7b46a6ecf60a6b13ef22dcdbf1ef6e78453"),
    "pt-BR": (LONG_TAIL_SPEC_MASTER, "JE-1500D", "pt-BR", "1e734e6b9e80f01c466d0258e1a424dfb2a0eec892bde47a69321b04d67ca5d4"),
    "de": (SPEC_MASTER, "JE-1000F", "EU", "7cc8c3a39d975ee532849059bd3a863afcd68c598214e2766f1ba7f2c6f64d9f"),
    "it": (SPEC_MASTER, "JE-1000F", "EU", "dcd26c720708a4e64ec8bf0638e7b963e6dee27ccf796e2ababa1ba405037690"),
    "uk": (SPEC_MASTER, "JE-1000F", "EU", "2b349ebcfabcda306390354d8064d110252f7bcc029a6c61e0d2c967397af7e4"),
    "ko": (LONG_TAIL_SPEC_MASTER, "JE-1000F", "KR", "a09684b4cb7f405158c3099cce2642b86042123d51c8df38c5dbbe24e144d9de"),
}


class PvInputRangePlaceholderTests(unittest.TestCase):
    def test_page_contract_requires_semantic_page_value(self) -> None:
        contracts = load_page_contracts(ROOT / "docs" / "templates" / "contracts")
        contract = next(item for item in contracts if item.page_id == "08_charging_methods")

        self.assertEqual(8, len(contract.source_files))
        self.assertEqual(
            ("PV_INPUT_RANGE", "DC_INPUT_CONNECTOR"),
            contract.required_placeholders["default"],
        )
        selectors = required_page_values_for_lang(contract, "ko")
        self.assertEqual(2, len(selectors))
        selector = next(item for item in selectors if item.row_key == "pv_input_range")
        self.assertEqual(("charging_methods",), selector.pages)
        self.assertEqual("page_value", selector.usage_type)

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
                self.assertIn("DC_INPUT_CONNECTOR", substitutions)
                rendered = apply_rst_substitutions(
                    source,
                    {
                        "PV_INPUT_RANGE": substitutions["PV_INPUT_RANGE"],
                        "DC_INPUT_CONNECTOR": substitutions["DC_INPUT_CONNECTOR"],
                    },
                    {},
                )
                self.assertNotIn("|PV_INPUT_RANGE|", rendered)
                self.assertNotIn("|DC_INPUT_CONNECTOR|", rendered)
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
