from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools import page_contracts


class TestPageContracts(unittest.TestCase):
    def test_load_page_contracts_should_parse_default_and_lang_specific_placeholders(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            contracts_dir = Path(td)
            (contracts_dir / "03_product_overview.yaml").write_text(
                "\n".join(
                    [
                        "page_id: 03_product_overview",
                        "source_files:",
                        "  - templates/page_us-en/03_product_overview_placeholder.rst",
                        "required_placeholders:",
                        "  default:",
                        "    - MAIN_POWER_BUTTON_LABEL",
                        "  en:",
                        "    - FRONT_TOTAL_OUTPUT_LABEL",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            contracts = page_contracts.load_page_contracts(contracts_dir)

            self.assertEqual(1, len(contracts))
            contract = contracts[0]
            self.assertEqual("03_product_overview", contract.page_id)
            self.assertEqual(
                ("MAIN_POWER_BUTTON_LABEL", "FRONT_TOTAL_OUTPUT_LABEL"),
                page_contracts.required_placeholders_for_lang(contract, "en"),
            )
            self.assertEqual((), page_contracts.required_copy_keys_for_lang(contract, "en"))
            self.assertEqual(
                ("MAIN_POWER_BUTTON_LABEL",),
                page_contracts.required_placeholders_for_lang(contract, "ja"),
            )

    def test_find_contract_for_source_should_match_normalized_relative_paths(self) -> None:
        contract = page_contracts.PageContract(
            page_id="03_product_overview",
            source_files=("templates/page_us-en/03_product_overview_placeholder.rst",),
            required_placeholders={"default": ("MAIN_POWER_BUTTON_LABEL",)},
            required_copy_keys={},
            required_spec_keys={},
            required_page_values={},
            required_assets={},
            allowed_languages=(),
            allowed_regions=(),
            allowed_models=(),
        )

        matched = page_contracts.find_contract_for_source(
            r"templates\page_us-en\03_product_overview_placeholder.rst",
            [contract],
        )

        self.assertIsNotNone(matched)
        assert matched is not None
        self.assertEqual("03_product_overview", matched.page_id)

    def test_product_overview_contract_should_apply_to_zh_template(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        contracts = page_contracts.load_page_contracts(repo_root / "docs" / "templates" / "contracts")

        self.assertIsNotNone(
            page_contracts.find_contract_for_source(
                "templates/page_zh/03_product_overview_placeholder.rst",
                contracts,
            )
        )
        self.assertIsNotNone(
            page_contracts.find_contract_for_source(
                "templates/page_jp/03_product_overview_placeholder.rst",
                contracts,
            )
        )
        contract = page_contracts.find_contract_for_source(
            "templates/page_zh/03_product_overview_placeholder.rst",
            contracts,
        )
        assert contract is not None
        # required_copy_keys is tiered too (skeleton slice S4), so a bare lang is
        # refused here for the same reason it is on required_placeholders.
        self.assertIn(
            "product_overview.page_title",
            page_contracts.required_copy_keys_for_lang(
                contract,
                page_contracts.ContractContext(lang="zh", category="MAIN", region="CN"),
            ),
        )

    def test_load_page_contracts_should_parse_page_value_selectors_and_scope(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            contracts_dir = Path(td)
            (contracts_dir / "05_operation_guide.yaml").write_text(
                "\n".join(
                    [
                        "page_id: 05_operation_guide",
                        "source_files:",
                        "  - templates/page_en/05_operation_guide_placeholder.rst",
                        "required_placeholders:",
                        "  default:",
                        "    - PRODUCT_NAME",
                        "required_copy_keys:",
                        "  en:",
                        "    - operation_guide.page_title",
                        "required_spec_keys:",
                        "  default:",
                        "    - product_name",
                        "required_page_values:",
                        "  default:",
                        "    - row_key: main_power_button",
                        "      pages: [Product overview]",
                        "      usage_type: page_value",
                        "      value_role: label",
                        "required_assets:",
                        "  en:",
                        "    - templates/word_template/common_assets/overview/front_product.jpg",
                        "allowed_languages: [en]",
                        "allowed_regions: [US]",
                        "allowed_models: [JE-1000F]",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            contracts = page_contracts.load_page_contracts(contracts_dir)

            self.assertEqual(1, len(contracts))
            contract = contracts[0]
            self.assertEqual(("product_name",), page_contracts.required_spec_keys_for_lang(contract, "en"))
            self.assertEqual(("operation_guide.page_title",), page_contracts.required_copy_keys_for_lang(contract, "en"))
            page_values = page_contracts.required_page_values_for_lang(contract, "en")
            self.assertEqual(1, len(page_values))
            self.assertEqual("main_power_button", page_values[0].row_key)
            self.assertEqual(("Product overview",), page_values[0].pages)
            self.assertEqual("page_value", page_values[0].usage_type)
            self.assertEqual("label", page_values[0].value_role)
            self.assertEqual(
                ("templates/word_template/common_assets/overview/front_product.jpg",),
                page_contracts.required_assets_for_lang(contract, "en"),
            )
            self.assertTrue(
                page_contracts.contract_applies_to(
                    contract,
                    lang="en",
                    model="JE-1000F",
                    region="US",
                )
            )
            self.assertFalse(
                page_contracts.contract_applies_to(
                    contract,
                    lang="ja",
                    model="JE-1000F",
                    region="US",
                )
            )

    def test_load_page_contracts_should_reject_page_value_selector_without_row_key(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            contracts_dir = Path(td)
            (contracts_dir / "bad.yaml").write_text(
                "\n".join(
                    [
                        "page_id: bad",
                        "source_files:",
                        "  - templates/page_en/bad.rst",
                        "required_page_values:",
                        "  default:",
                        "    - usage_type: page_value",
                        "      value_role: label",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(RuntimeError, "row_key is required"):
                page_contracts.load_page_contracts(contracts_dir)


if __name__ == "__main__":
    unittest.main()


class ContractTierTests(unittest.TestCase):
    """Skeleton slice S2: one shared contract serving several families."""

    def _contract(self):
        from tools.page_contracts import find_contract_for_source, load_page_contracts

        repo_root = Path(__file__).resolve().parents[1]
        contracts = load_page_contracts(repo_root / "docs" / "templates" / "contracts")
        contract = find_contract_for_source(
            "templates/page_us-en/03_product_overview_placeholder.rst", contracts
        )
        self.assertIsNotNone(contract)
        return contract

    def test_host_placeholder_set_is_unchanged_by_tiering(self) -> None:
        from tools.page_contracts import ContractContext, required_placeholders_for_lang

        contract = self._contract()
        us_en = required_placeholders_for_lang(
            contract, ContractContext(lang="en", category="MAIN", region="US")
        )
        # 18 pre-tiering `default` entries + the 2 language-scoped total-output
        # placeholders the US overview carries.
        self.assertEqual(20, len(us_en))
        self.assertIn("SIDE_AC_INPUT_LABEL", us_en)
        self.assertIn("FRONT_TOTAL_OUTPUT_LABEL", us_en)

        # page_jp carries no FRONT_TOTAL_OUTPUT_* (verified in the template), so
        # JP must keep resolving to the 18 host placeholders only.
        jp_ja = required_placeholders_for_lang(
            contract, ContractContext(lang="ja", category="MAIN", region="JP")
        )
        self.assertEqual(18, len(jp_ja))
        self.assertNotIn("FRONT_TOTAL_OUTPUT_LABEL", jp_ja)

    def test_battery_pack_selects_only_its_own_parts(self) -> None:
        from tools.page_contracts import ContractContext, required_placeholders_for_lang

        contract = self._contract()
        bp_en = required_placeholders_for_lang(
            contract, ContractContext(lang="en", category="BP", region="US")
        )
        # Two expansion ports, A and B: the shipped overview page shows they are
        # physically distinct (S4 correction to S2's single-port reading).
        self.assertEqual(
            {
                "MAIN_POWER_BUTTON_LABEL",
                "SIDE_DC_EXPANSION_PORT_A_LABEL",
                "SIDE_DC_EXPANSION_PORT_A_SPEC",
                "SIDE_DC_EXPANSION_PORT_B_LABEL",
                "SIDE_DC_EXPANSION_PORT_B_SPEC",
            },
            set(bp_en),
        )
        # The conjunction guard: BP shares en/fr/es with the host but must not
        # inherit a language-scoped host requirement.
        self.assertNotIn("FRONT_TOTAL_OUTPUT_LABEL", bp_en)
        self.assertNotIn("SIDE_AC_INPUT_LABEL", bp_en)

    def test_copy_keys_tier_by_family_without_changing_the_host_set(self) -> None:
        from tools.page_contracts import ContractContext, required_copy_keys_for_lang

        contract = self._contract()
        host = required_copy_keys_for_lang(
            contract, ContractContext(lang="en", category="MAIN", region="US")
        )
        # Exactly the seven keys the map carried under bare `en` before tiering.
        self.assertEqual(7, len(host))
        self.assertIn("product_overview.right_side_view", host)
        self.assertIn("product_overview.part.led_light", host)

        bp = required_copy_keys_for_lang(
            contract, ContractContext(lang="en", category="BP", region="US")
        )
        # The battery pack's ports are on the left side and it has no LED light.
        self.assertIn("product_overview.left_side_view", bp)
        self.assertNotIn("product_overview.right_side_view", bp)
        self.assertNotIn("product_overview.part.led_light", bp)
        self.assertNotIn("product_overview.part.led_light_button", bp)

    def test_bare_lang_is_refused_on_a_tiered_map(self) -> None:
        from tools.page_contracts import required_placeholders_for_lang

        # A bare lang carries no category, so it would silently resolve to a
        # near-empty requirement set — a weakened gate reporting success.
        with self.assertRaises(RuntimeError):
            required_placeholders_for_lang(self._contract(), "en")

    def test_unknown_category_is_refused_instead_of_falling_back_to_default(self) -> None:
        from tools.page_contracts import ContractContext, required_placeholders_for_lang

        contract = self._contract()
        for category in ("Bp", None):
            with self.subTest(category=category):
                with self.assertRaisesRegex(RuntimeError, "is not declared"):
                    required_placeholders_for_lang(
                        contract,
                        ContractContext(lang="en", category=category, region="US"),
                    )

    def test_conjunction_requires_every_atom(self) -> None:
        from tools.page_contracts import ContractContext, _requirements_for_context

        requirements = {
            "default": ("D",),
            "category:MAIN": ("M",),
            # Explicitly declaring an empty BP tier makes default-only behavior
            # intentional instead of indistinguishable from a category typo.
            "category:BP": (),
            "category:MAIN+en": ("ME",),
            "capability:UPS": ("C",),
        }
        main_en = _requirements_for_context(
            requirements, ContractContext(lang="en", category="MAIN")
        )
        self.assertEqual(("D", "M", "ME"), main_en)
        # Same language, different category: the conjunction must not fire.
        bp_en = _requirements_for_context(
            requirements, ContractContext(lang="en", category="BP")
        )
        self.assertEqual(("D",), bp_en)
        # Capability atoms only fire when the capability is TRUE.
        with_cap = _requirements_for_context(
            requirements,
            ContractContext(lang="en", category="MAIN", capabilities=frozenset({"UPS"})),
        )
        self.assertEqual(("D", "M", "C", "ME"), with_cap)

    def test_empty_conjunction_atom_is_rejected_at_load(self) -> None:
        import tempfile

        from tools.page_contracts import load_page_contracts

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.yaml"
            path.write_text(
                "page_id: bad\n"
                "source_files: [templates/x.rst]\n"
                "required_placeholders:\n"
                "  category:MAIN+: [A]\n",
                encoding="utf-8",
            )
            with self.assertRaises(RuntimeError):
                load_page_contracts(Path(tmp))
