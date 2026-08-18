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

CHARGING_CASES = {
    "en": (SPEC_MASTER, "JE-1000F", "US", "d7529e0ce6e7c02591c42251e6bc9cc18339e929608d5a853e031efac0c9bf79"),
    "fr": (SPEC_MASTER, "JE-1000F", "US", "a7753076fbe10257c7dc5ecf7fb9095bcc920afb137b02fb8542fe0ab4e01a52"),
    "es": (SPEC_MASTER, "JE-1000F", "US", "df5714e532914ca36e533ef67f3d31b2375e3d4f46a02a1aca3d02ace1d85e73"),
    "pt-BR": (LONG_TAIL_SPEC_MASTER, "JE-1500D", "pt-BR", "78a2169e709ea3b2814f066afff47e3fa2d7bee26d25cf37e32812d69e144f45"),
    "de": (SPEC_MASTER, "JE-1000F", "EU", "58e3ccbeaf293bdaa3e236fad51eaea01c4af1dc6f16156794040e78f9f3e304"),
    "it": (SPEC_MASTER, "JE-1000F", "EU", "538455b593163c25c96d5e4eb9de4ea7d9ecbe6030c355e701aaf6708b7fd3c9"),
    "uk": (SPEC_MASTER, "JE-1000F", "EU", "59cb400cc4281f1285808960b2946eff99f9a8f8c1e097b19df4d3e289894cbe"),
    "ko": (LONG_TAIL_SPEC_MASTER, "JE-1000F", "KR", "e5d0cd2f86240e1d606b6fde996e05b55e9cf254ef4d77affb64348fc19aa1d5"),
}

UPS_CASES = {
    "en": (SPEC_MASTER, "JE-1000F", "US", "ebda8dfde504619ee86f9fec5637931487d53d3598d00bdcbd635036dae207c8"),
    "fr": (SPEC_MASTER, "JE-1000F", "US", "7e86629d410104f7d8be9c07a7d0f9cb0345281d568307c1522f8d7ab0d1d4b8"),
    "es": (SPEC_MASTER, "JE-1000F", "US", "5357dde7f545649c6c473c2dcb8e0931bfb881efa1a375f2690176d023caee10"),
    "pt-BR": (LONG_TAIL_SPEC_MASTER, "JE-1500D", "pt-BR", "f56a0f8826321887c66267462fae53c0121623224826af2090bea548d69f8b27"),
    "de": (SPEC_MASTER, "JE-1000F", "EU", "8db266d60cb81c87bec75edb7e9bf636f977ca22292371d80cd67608ae4e3028"),
    "it": (SPEC_MASTER, "JE-1000F", "EU", "f2e6a41184ca3a17194a542a4d74de42680eec5a94eff3f55d22edbb55ea7622"),
    "uk": (SPEC_MASTER, "JE-1000F", "EU", "2691fe1006dbe89008d0596e556ef53805bbd0a49238930a5795f7d73e0850d6"),
    "ko": (LONG_TAIL_SPEC_MASTER, "JE-1000F", "KR", "2c64eed85ef863b246f4352b61dbe049674b46ebecf97d544e5e242b459c5227"),
}


class Dc8020UpsPlaceholderTests(unittest.TestCase):
    def test_page_contracts_require_semantic_page_values(self) -> None:
        contracts = {
            item.page_id: item
            for item in load_page_contracts(ROOT / "docs" / "templates" / "contracts")
        }

        charging = contracts["08_charging_methods"]
        self.assertEqual(8, len(charging.source_files))
        self.assertEqual(
            ("PV_INPUT_RANGE", "DC_INPUT_CONNECTOR"),
            charging.required_placeholders["default"],
        )
        self.assertEqual(
            ["pv_input_range", "dc_input_connector"],
            [item.row_key for item in required_page_values_for_lang(charging, "uk")],
        )

        ups = contracts["06_ups_mode"]
        self.assertEqual(8, len(ups.source_files))
        self.assertEqual(("UPS_TRANSFER_TIME",), ups.required_placeholders["default"])
        selectors = required_page_values_for_lang(ups, "ko")
        self.assertEqual(1, len(selectors))
        self.assertEqual("ups_transfer_time", selectors[0].row_key)
        self.assertEqual(("ups_mode",), selectors[0].pages)
        self.assertEqual("page_value", selectors[0].usage_type)

    def test_charging_templates_resolve_to_pre_migration_bytes(self) -> None:
        for lang, (spec_master, model, region, expected_sha256) in CHARGING_CASES.items():
            with self.subTest(lang=lang):
                path = ROOT / "docs" / "templates" / "page_shared" / lang / "08_charging_methods.rst"
                source = path.read_text(encoding="utf-8")
                substitutions = resolve_template_substitutions_from_spec_master(
                    spec_master,
                    model=model,
                    region=region,
                    lang=lang,
                )

                self.assertEqual(4, source.count("|DC_INPUT_CONNECTOR|"))
                self.assertIn("DC_INPUT_CONNECTOR", substitutions)
                rendered = apply_rst_substitutions(
                    source,
                    {"DC_INPUT_CONNECTOR": substitutions["DC_INPUT_CONNECTOR"]},
                    {},
                )
                self.assertNotIn("|DC_INPUT_CONNECTOR|", rendered)
                self.assertEqual(
                    expected_sha256,
                    hashlib.sha256(rendered.encode("utf-8")).hexdigest(),
                )

    def test_ups_templates_resolve_to_pre_migration_bytes(self) -> None:
        for lang, (spec_master, model, region, expected_sha256) in UPS_CASES.items():
            with self.subTest(lang=lang):
                path = ROOT / "docs" / "templates" / "page_shared" / lang / "06_ups_mode.rst"
                source = path.read_text(encoding="utf-8")
                substitutions = resolve_template_substitutions_from_spec_master(
                    spec_master,
                    model=model,
                    region=region,
                    lang=lang,
                )

                self.assertEqual(1, source.count("|UPS_TRANSFER_TIME|"))
                self.assertTrue("0 ms" in source or "0 мс" in source)
                self.assertIn("UPS_TRANSFER_TIME", substitutions)
                rendered = apply_rst_substitutions(
                    source,
                    {"UPS_TRANSFER_TIME": substitutions["UPS_TRANSFER_TIME"]},
                    {},
                )
                self.assertNotIn("|UPS_TRANSFER_TIME|", rendered)
                self.assertEqual(
                    expected_sha256,
                    hashlib.sha256(rendered.encode("utf-8")).hexdigest(),
                )

    def test_japanese_and_chinese_templates_remain_outside_this_slice(self) -> None:
        for page in ("06_ups_mode.rst", "08_charging_methods.rst"):
            for family in ("page_jp", "page_zh"):
                with self.subTest(page=page, family=family):
                    source = (ROOT / "docs" / "templates" / family / page).read_text(encoding="utf-8")
                    self.assertNotIn("|DC_INPUT_CONNECTOR|", source)
                    self.assertNotIn("|UPS_TRANSFER_TIME|", source)


if __name__ == "__main__":
    unittest.main()
