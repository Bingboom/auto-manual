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
        slot_status_overrides: dict[str, list[str]] | None = None,
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
                                "slot_status_overrides": slot_status_overrides or {},
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
                "asset_sha256": {},
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
                "asset_sha256": {},
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
                "asset_sha256": {},
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

    def test_base_art_live_copy_records_the_frozen_source_identity(self) -> None:
        ir = SimpleNamespace(
            model="JE-1000F",
            region="US",
            pages=(SimpleNamespace(page_id="05_operation_guide_placeholder.rst"),),
            metadata={
                "web_contract": {
                    "product_overview": {"source_patterns": []},
                    "operations": {
                        "source_patterns": ["*05_operation_guide_placeholder"],
                        "figures": [
                            {
                                "id": "main-power",
                                "web_replace_key": "operation.main-power",
                                "base_art_layout": {"art_sha256": "e" * 64},
                            }
                        ],
                    },
                    "reference_figures": {"figures": []},
                },
                "illustration_provenance": {"illustrations": []},
                "composites": [],
                "asset_sha256": {
                    "assets/ir/main_power_123456789abc.png": "e" * 64,
                },
            },
        )
        fragment = (
            '<figure class="hb-operation-figure hb-base-art-live-copy" '
            'data-web-replace-key="operation.main-power" '
            'data-web-presentation-mode="base-art-live-copy" '
            'data-web-base-art-ref="operation/main_power">'
            '<div class="hb-operation-stage">'
            '<img src="file:///tmp/package/assets/ir/main_power_123456789abc.png">'
            '<div class="hb-operation-steps">Live searchable copy</div>'
            '</div></figure>'
        )

        coverage = build_web_figure_coverage(ir, (fragment,))

        self.assertEqual("base-art-live-copy", coverage["slots"][0]["status"])
        self.assertEqual("operation/main_power", coverage["slots"][0]["asset_ref"])
        self.assertEqual(["main_power.png"], coverage["slots"][0]["source_images"])
        self.assertEqual(
            {
                "path": "assets/ir/main_power_123456789abc.png",
                "sha256": "e" * 64,
            },
            coverage["slots"][0]["asset"],
        )
        validate_web_figure_coverage(coverage)

        self.assertEqual(1, coverage["summary"]["by_status"]["base-art-live-copy"])
        self.assertEqual(
            1,
            coverage["summary"]["by_section"]["operation"]["by_status"][
                "base-art-live-copy"
            ],
        )

        del coverage["slots"][0]["asset"]
        with self.assertRaisesRegex(ValueError, "invalid base-art evidence"):
            validate_web_figure_coverage(coverage)

        # Anchors measured on one art version may not position another.
        figure = ir.metadata["web_contract"]["operations"]["figures"][0]
        figure["base_art_layout"]["art_sha256"] = "d" * 64
        with self.assertRaisesRegex(ValueError, "was measured on art dddddddddddd"):
            build_web_figure_coverage(ir, (fragment,))
        del figure["base_art_layout"]
        with self.assertRaisesRegex(ValueError, "no measured art hash"):
            build_web_figure_coverage(ir, (fragment,))

    def test_base_art_reference_figure_binds_the_art_its_rects_were_measured_on(self) -> None:
        figure = {
            "id": "charging-car",
            "source_patterns": ["*08_charging_methods"],
            "image_key": "charging/car_charge",
            "web_replace_key": "reference.charging-car",
            "base_art_layout": {"art_sha256": "f" * 64},
        }
        ir = SimpleNamespace(
            model="JE-1000F",
            region="US",
            pages=(SimpleNamespace(page_id="08_charging_methods.rst"),),
            metadata={
                "web_contract": {
                    "product_overview": {"source_patterns": []},
                    "operations": {"source_patterns": [], "figures": []},
                    "reference_figures": {"figures": [figure]},
                },
                "illustration_provenance": {"illustrations": []},
                "composites": [],
                "asset_sha256": {
                    "assets/ir/car_charge_123456789abc.png": "f" * 64,
                },
            },
        )
        fragment = (
            '<figure class="hb-reference-figure hb-base-art-live-copy" '
            'data-reference-id="charging-car" '
            'data-web-replace-key="reference.charging-car" '
            'data-web-presentation-mode="base-art-live-copy" '
            'data-web-base-art-ref="charging/car_charge">'
            '<div class="hb-reference-semantic"><div class="hb-reference-art-panel">'
            '<img src="file:///tmp/package/assets/ir/car_charge_123456789abc.png">'
            '<span class="hb-reference-live-label">Vehicle</span>'
            '</div></div></figure>'
        )

        coverage = build_web_figure_coverage(ir, (fragment,))

        (slot,) = coverage["slots"]
        self.assertEqual(
            ("charging", "reference.charging-car", "base-art-live-copy"),
            (slot["section"], slot["slot_id"], slot["status"]),
        )
        self.assertEqual("charging/car_charge", slot["asset_ref"])
        self.assertEqual(
            {"path": "assets/ir/car_charge_123456789abc.png", "sha256": "f" * 64},
            slot["asset"],
        )
        validate_web_figure_coverage(coverage)

        # Rects measured on one art version may not position another.
        figure["base_art_layout"]["art_sha256"] = "d" * 64
        with self.assertRaisesRegex(ValueError, "was measured on art dddddddddddd"):
            build_web_figure_coverage(ir, (fragment,))

    def test_reports_without_base_art_keep_the_frozen_v1_summary_shape(self) -> None:
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
                "composites": [],
                "asset_sha256": {},
            },
        )
        fragment = (
            '<figure class="hb-operation-figure" '
            'data-web-replace-key="operation.main-power">'
            '<div class="hb-operation-stage">'
            '<div class="hb-operation-steps">Live searchable copy</div>'
            '</div></figure>'
        )
        legacy_counts = {
            "finished-panel": 0,
            "approved-composite": 0,
            "editable-fallback": 0,
            "missing": 0,
        }

        coverage = build_web_figure_coverage(ir, (fragment,))

        by_status = coverage["summary"]["by_status"]
        self.assertEqual(set(legacy_counts), set(by_status))
        self.assertEqual(
            set(legacy_counts),
            set(coverage["summary"]["by_section"]["operation"]["by_status"]),
        )
        # A report frozen before base-art-live-copy existed carries exactly the
        # four v1 status keys; cold replay must keep accepting it unchanged.
        stored = {
            **coverage,
            "summary": {
                "total": coverage["summary"]["total"],
                "by_status": {**legacy_counts, **by_status},
                "by_section": {
                    section: {
                        "total": value["total"],
                        "by_status": {**legacy_counts, **value["by_status"]},
                    }
                    for section, value in coverage["summary"]["by_section"].items()
                },
            },
        }
        validate_web_figure_coverage(stored)

    def test_base_art_live_copy_rejects_an_unfrozen_rendered_image(self) -> None:
        ir = SimpleNamespace(
            model="JE-1000F",
            region="US",
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
                "composites": [],
                "asset_sha256": {},
            },
        )
        fragment = (
            '<figure class="hb-operation-figure hb-base-art-live-copy" '
            'data-web-replace-key="operation.main-power" '
            'data-web-presentation-mode="base-art-live-copy" '
            'data-web-base-art-ref="operation/main_power">'
            '<img src="file:///tmp/package/assets/ir/main_power.png">'
            '</figure>'
        )

        with self.assertRaisesRegex(ValueError, "frozen asset evidence"):
            build_web_figure_coverage(ir, (fragment,))

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

    def test_base_art_live_copy_requires_an_exact_slot_grant(self) -> None:
        coverage = {
            "model": "JE-1000F",
            "region": "EU",
            "slots": [
                {
                    "locale": "it",
                    "slot_id": "operation.main-power",
                    "status": "base-art-live-copy",
                }
            ],
        }

        with self.assertRaisesRegex(ValueError, "unregistered debt"):
            enforce_required_web_figure_coverage(self._required_ir(), coverage)

        enforce_required_web_figure_coverage(
            self._required_ir(
                slot_status_overrides={
                    "operation.main-power": ["base-art-live-copy"],
                }
            ),
            coverage,
        )

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
