from types import SimpleNamespace
import unittest

from tools.web_figure_coverage import (
    WEB_FIGURE_COVERAGE_SCHEMA,
    build_web_figure_coverage,
    validate_web_figure_coverage,
)


class WebFigureCoverageTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
