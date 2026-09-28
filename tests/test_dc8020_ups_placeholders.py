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

# The ko goldens moved once when the ko templates stopped printing the ambiguous
# 은(는) form and started naming a particle pair (|PRODUCT_NAME_JOSA_EUN|); the
# rendered diff was exactly those placeholder tokens, nothing else. The ko UPS
# golden moved again when the UPS transfer sentence adopted the 본 제품 simplification
# (|PRODUCT_NAME_JOSA_EUN| → literal 본 제품은), a family-wide KR wording backport.
# The ko charging golden moved for the same 본 제품 simplification in 08_charging_methods
# (solar DC8020 intro + Voc DC-input sentence: |PRODUCT_NAME…| → literal 본 제품).
# The en/de/it/uk charging and en/de/it UPS goldens moved when those figures'
# alt text stopped calling the figure a placeholder; the rendered diff was
# exactly those :alt: lines, nothing else.
# The en/fr/es/de/it/uk UPS goldens moved again when the shared UPS template took
# the UPS WARNING and the fourth CAUTION bullet of the JE-3000C EUUK
# V2.0-2026-09-15 print for every model that uses it (operator rulings
# 2026-09-27), for the Web and Word only: a `.. only:: not latex` block holds the
# WARNING and the four-bullet CAUTION, and main's CAUTION follows unchanged under
# `.. only:: latex`. Dropping the `not latex` block and unwrapping the `latex`
# one gives main's rendered bytes exactly
# (tests/test_je3000c_0915_warnings.py pins that print branch). The ko and pt-BR
# goldens stay: the print has no block for those languages.
# The same six goldens moved once more for the JE-3000C/EU print-gap corrections
# (operator ruling 「JE-3000C 旧差异按印刷对齐」, 2026-09-27): a
# `.. only:: model_je_3000c` branch sets the UPS figure after all of the UPS text,
# as the JE-3000C print does, and the fr/de/it/uk branches carry that print's
# wording; every other model reads the unchanged text under
# `.. only:: not model_je_3000c` (tests/test_je3000c_eu_print_gaps.py pins that
# view to main's bytes). The fr/de/it/uk carriers therefore hold
# |UPS_TRANSFER_TIME| twice, once per branch.
CHARGING_CASES = {
    "en": (SPEC_MASTER, "JE-1000F", "US", "e1a8849432196fef888b16d1fd289a13920e79a05632dd005a2cfc44c7f007f5"),
    "fr": (SPEC_MASTER, "JE-1000F", "US", "a7753076fbe10257c7dc5ecf7fb9095bcc920afb137b02fb8542fe0ab4e01a52"),
    "es": (SPEC_MASTER, "JE-1000F", "US", "df5714e532914ca36e533ef67f3d31b2375e3d4f46a02a1aca3d02ace1d85e73"),
    "pt-BR": (LONG_TAIL_SPEC_MASTER, "JE-1500D", "pt-BR", "78a2169e709ea3b2814f066afff47e3fa2d7bee26d25cf37e32812d69e144f45"),
    "de": (SPEC_MASTER, "JE-1000F", "EU", "8466079e2070ecdfbadc777c4c2bc69f101dde9f248f5d85367f16232bb57c19"),
    "it": (SPEC_MASTER, "JE-1000F", "EU", "7a61c39d6e9e61dc440fefb5cbac66c6388049fa6f7a9a06867fcc35ed8c2051"),
    "uk": (SPEC_MASTER, "JE-1000F", "EU", "f86471a4b029af64e396444ce7543a50da1fcaef1c46e22e41e1ed5a5b73d24b"),
    "ko": (LONG_TAIL_SPEC_MASTER, "JE-1000F", "KR", "2f91c9eb6ed9585dc80feedf783b8d0db7df60ecd24abe55d7d783e4924f51ee"),
}

UPS_CASES = {
    "en": (SPEC_MASTER, "JE-1000F", "US", "6b5b113e4b16fee5461b0069785c22788f18bd2c27c87812f02606666f252402"),
    "fr": (SPEC_MASTER, "JE-1000F", "US", "e1bceddd1ea668a41a40fb8b10f587a2417f2ed8284b757d350ebbd29a4a5517"),
    "es": (SPEC_MASTER, "JE-1000F", "US", "1ac2a973efb80d9a54786e83c624e65bb3936a407a8229bc70996e6f0620d32c"),
    "pt-BR": (LONG_TAIL_SPEC_MASTER, "JE-1500D", "pt-BR", "f56a0f8826321887c66267462fae53c0121623224826af2090bea548d69f8b27"),
    "de": (SPEC_MASTER, "JE-1000F", "EU", "b86e5263fd8e5b10d3c4a500a1a932a9c7ada4eaa5db527940e01dc354d6a775"),
    "it": (SPEC_MASTER, "JE-1000F", "EU", "217d146b467be72189ca0523c5d4bea74475562cc5512bc6cba355d0934e614a"),
    "uk": (SPEC_MASTER, "JE-1000F", "EU", "e2d4b1e55bf495a29f4877dd805759f114128b7e8a27d987413705b0dcab48e5"),
    "ko": (LONG_TAIL_SPEC_MASTER, "JE-1000F", "KR", "82bd0c003e01800f9a67ce244f443cec8537924184ee282572b7e64776f14c2a"),
}
# Carriers whose `.. only:: model_je_3000c` branch rewords the UPS text: one
# |UPS_TRANSFER_TIME| per branch.
UPS_TRANSFER_TIME_COUNT = {"fr": 2, "de": 2, "it": 2, "uk": 2}


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

                self.assertEqual(UPS_TRANSFER_TIME_COUNT.get(lang, 1), source.count("|UPS_TRANSFER_TIME|"))
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
