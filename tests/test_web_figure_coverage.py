from types import SimpleNamespace
import unittest

from tools.web_figure_coverage import (
    WEB_FIGURE_COVERAGE_SCHEMA,
    build_web_figure_coverage,
    enforce_required_web_figure_coverage,
    validate_web_figure_coverage,
)


class WebFigureCoverageTests(unittest.TestCase):
    def _required_ir(
        self,
        *,
        model: str = "JE-1000F",
        region: str = "EU",
        known_debt: list[dict[str, str]] | None = None,
    ):
        return SimpleNamespace(
            model=model,
            region=region,
            language="",
            metadata={
                "declared_languages": ["it"],
                "web_contract": {
                    "figure_coverage": {
                        "requirements": [
                            {
                                "target": {"model": "JE-1000F", "region": "EU"},
                                "locales": ["de", "it"],
                                "required_slots": ["operation.main-power"],
                                "allowed_statuses": [
                                    "finished-panel",
                                    "approved-composite",
                                ],
                                "known_debt": known_debt or [],
                            }
                        ]
                    }
                },
            },
        )

    def test_both_asset_carriers_and_uncovered_slots_share_one_inventory(self) -> None:
        contract = {
            "product_overview": {
                "source_patterns": ["*03_product_overview_placeholder"],
            },
            "operations": {
                "source_patterns": ["*05_operation_guide_placeholder"],
            },
            "reference_figures": {
                "figures": [
                    {
                        "id": "charging-car",
                        "source_patterns": ["*08_charging_methods"],
                        "image_key": "charging/car_charge",
                    }
                ],
            },
        }
        ir = SimpleNamespace(
            model="JE-1000F",
            region="EU",
            pages=(
                SimpleNamespace(page_id="03_product_overview_placeholder.rst"),
                SimpleNamespace(page_id="05_operation_guide_placeholder.rst"),
                SimpleNamespace(page_id="08_charging_methods.rst"),
            ),
            metadata={
                "web_contract": contract,
                "illustration_provenance": {
                    "schema_version": "web-illustrations/v1",
                    "illustrations": [
                        {
                            "path": "assets/overview-panel.png",
                            "replaces": ["front.png", "side.png"],
                            "sha256": "a" * 64,
                        }
                    ],
                },
                "composites": [
                    {
                        "asset_key": "operation.main-power.de",
                        "web_replace_key": "operation.main-power",
                        "locale": "de",
                        "path": "assets/main-power-de.png",
                        "content_sha256": "b" * 64,
                    }
                ],
            },
        )
        fragments = (
            '<img class="manual-finished-illustration" '
            'data-web-finished-panel-path="assets/overview-panel.png" '
            f'data-web-finished-panel-sha256="{"a" * 64}" src="overview.png">',
            '<figure class="hb-operation-figure hb-has-composite-art" '
            'data-web-replace-key="operation.main-power" '
            'data-web-composite-asset-key="operation.main-power.de" '
            'data-web-composite-locale="de" '
            f'data-web-composite-sha256="{"b" * 64}">'
            '<div class="hb-composite-stage"><img src="main-power-de.png"></div>'
            '<div class="hb-operation-stage"><img src="power.png"></div>'
            '</figure>'
            '<figure class="hb-operation-figure" '
            'data-web-replace-key="operation.ac-output">'
            '<div class="hb-operation-stage"><img src="ac.png"></div>'
            '</figure>'
            '<figure class="hb-lcd-mode-composition">'
            '<img src="lcd-mode.png"><table><tr><td>Live copy</td></tr></table>'
            '</figure>',
            '<img src="solar-direct.png"><img src="solar-adapter.png">',
        )

        coverage = build_web_figure_coverage(ir, fragments)

        self.assertEqual(WEB_FIGURE_COVERAGE_SCHEMA, coverage["schema_version"])
        self.assertEqual(
            [
                "finished-panel",
                "approved-composite",
                "editable-fallback",
                "editable-fallback",
                "missing",
                "missing",
            ],
            [slot["status"] for slot in coverage["slots"]],
        )
        self.assertEqual(
            {
                "finished-panel": 1,
                "approved-composite": 1,
                "editable-fallback": 2,
                "missing": 2,
            },
            coverage["summary"]["by_status"],
        )
        self.assertEqual(1, coverage["summary"]["by_section"]["overview"]["total"])
        self.assertEqual(3, coverage["summary"]["by_section"]["operation"]["total"])
        self.assertEqual(2, coverage["summary"]["by_section"]["charging"]["total"])
        self.assertEqual(
            ["front.png", "side.png"],
            coverage["slots"][0]["replaces"],
        )
        self.assertEqual(
            "assets/main-power-de.png",
            coverage["slots"][1]["asset"]["path"],
        )

    def test_inventory_validation_rejects_summary_drift(self) -> None:
        payload = {
            "schema_version": WEB_FIGURE_COVERAGE_SCHEMA,
            "model": "JE-1000F",
            "region": "EU",
            "slots": [],
            "summary": {
                "total": 1,
                "by_status": {
                    "finished-panel": 0,
                    "approved-composite": 0,
                    "editable-fallback": 0,
                    "missing": 0,
                },
                "by_section": {},
            },
        }

        with self.assertRaisesRegex(ValueError, "summary total"):
            validate_web_figure_coverage(payload)

    def test_materialized_page_slot_identifies_target_neutral_section(self) -> None:
        ir = SimpleNamespace(
            model="JBP-2000B",
            region="JP",
            pages=(SimpleNamespace(page_id="product_overview_ja.rst"),),
            metadata={
                "web_contract": {
                    "product_overview": {
                        "source_patterns": ["*03_product_overview_placeholder"],
                    },
                    "operations": {"source_patterns": []},
                    "reference_figures": {"figures": []},
                },
                "page_slots": {
                    "product_overview_ja.rst": "product_overview_ja",
                },
                "illustration_provenance": {
                    "illustrations": [
                        {
                            "path": "assets/jp-overview.png",
                            "replaces": ["front.png", "side.png"],
                            "sha256": "c" * 64,
                        }
                    ],
                },
                "composites": [],
            },
        )
        fragment = (
            '<img class="manual-finished-illustration" '
            'data-web-finished-panel-path="assets/jp-overview.png" '
            f'data-web-finished-panel-sha256="{"c" * 64}" src="overview.png">'
        )

        coverage = build_web_figure_coverage(ir, (fragment,))

        self.assertEqual(1, coverage["summary"]["total"])
        self.assertEqual("overview", coverage["slots"][0]["section"])
        self.assertEqual("finished-panel", coverage["slots"][0]["status"])

    def test_same_asset_hash_across_locales_is_disambiguated_by_locale(self) -> None:
        digest = "d" * 64
        ir = SimpleNamespace(
            model="JE-1000F",
            region="EU",
            pages=(SimpleNamespace(page_id="05_operation_guide_placeholder.rst"),),
            metadata={
                "web_contract": {
                    "product_overview": {"source_patterns": []},
                    "operations": {
                        "source_patterns": ["*05_operation_guide_placeholder"],
                    },
                    "reference_figures": {"figures": []},
                },
                "illustration_provenance": {"illustrations": []},
                "composites": [
                    {
                        "asset_key": "operation.energy-saving",
                        "locale": locale,
                        "path": f"assets/energy-saving-{locale}.png",
                        "content_sha256": digest,
                    }
                    for locale in ("de", "it")
                ],
            },
        )
        fragment = (
            '<figure class="hb-operation-figure hb-has-composite-art" '
            'data-web-replace-key="operation.energy-saving" '
            'data-web-composite-asset-key="operation.energy-saving" '
            'data-web-composite-locale="it" '
            f'data-web-composite-sha256="{digest}">'
            '<div class="hb-composite-stage"><img src="energy-saving-it.png"></div>'
            '</figure>'
        )

        coverage = build_web_figure_coverage(ir, (fragment,))

        self.assertEqual("approved-composite", coverage["slots"][0]["status"])
        self.assertEqual("it", coverage["slots"][0]["asset"]["locale"])
        self.assertEqual(
            "assets/energy-saving-it.png",
            coverage["slots"][0]["asset"]["path"],
        )

    def test_required_coverage_allows_composite_and_ignores_nonrequired_fallback(self) -> None:
        coverage = {
            "model": "JE-1000F",
            "region": "EU",
            "slots": [
                {
                    "locale": "it",
                    "slot_id": "operation.main-power",
                    "status": "approved-composite",
                },
                {
                    "locale": "it",
                    "slot_id": "semantic.lcd-mode-composition",
                    "status": "editable-fallback",
                },
            ],
        }

        enforce_required_web_figure_coverage(self._required_ir(), coverage)

    def test_eu_italian_textless_art_with_html_copy_remains_debt(self) -> None:
        coverage = {
            "model": "JE-1000F",
            "region": "EU",
            "slots": [
                {
                    "locale": "it",
                    "slot_id": "operation.main-power",
                    "status": "editable-fallback",
                }
            ],
        }

        with self.assertRaisesRegex(
            ValueError,
            "it/operation.main-power=editable-fallback",
        ):
            enforce_required_web_figure_coverage(self._required_ir(), coverage)

    def test_required_coverage_rejects_missing_or_duplicate_slot(self) -> None:
        coverage = {
            "model": "JE-1000F",
            "region": "EU",
            "slots": [],
        }
        with self.assertRaisesRegex(
            ValueError,
            "it/operation.main-power=count:0",
        ):
            enforce_required_web_figure_coverage(self._required_ir(), coverage)

    def test_exact_registered_debt_is_tolerated_but_cannot_change_status(self) -> None:
        debt = [
            {
                "locale": "it",
                "slot_id": "operation.main-power",
                "status": "editable-fallback",
            }
        ]
        coverage = {
            "model": "JE-1000F",
            "region": "EU",
            "slots": [
                {
                    "locale": "it",
                    "slot_id": "operation.main-power",
                    "status": "editable-fallback",
                }
            ],
        }

        enforce_required_web_figure_coverage(
            self._required_ir(known_debt=debt), coverage
        )

        coverage["slots"][0]["status"] = "missing"
        with self.assertRaisesRegex(ValueError, "registered:editable-fallback"):
            enforce_required_web_figure_coverage(
                self._required_ir(known_debt=debt), coverage
            )

    def test_paid_debt_requires_the_baseline_to_shrink_in_the_same_change(self) -> None:
        debt = [
            {
                "locale": "it",
                "slot_id": "operation.main-power",
                "status": "editable-fallback",
            }
        ]
        coverage = {
            "model": "JE-1000F",
            "region": "EU",
            "slots": [
                {
                    "locale": "it",
                    "slot_id": "operation.main-power",
                    "status": "approved-composite",
                }
            ],
        }

        with self.assertRaisesRegex(ValueError, "stale debt baseline"):
            enforce_required_web_figure_coverage(
                self._required_ir(known_debt=debt), coverage
            )

    def test_required_coverage_does_not_apply_to_other_target(self) -> None:
        coverage = {"model": "JBP-2000B", "region": "JP", "slots": []}

        enforce_required_web_figure_coverage(
            self._required_ir(model="JBP-2000B", region="JP"),
            coverage,
        )


if __name__ == "__main__":
    unittest.main()
