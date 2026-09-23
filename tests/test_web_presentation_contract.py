from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.web_presentation import WebPresentationError, load_web_manual_contract
from tools.web_presentation_contract import merge_contract_layers
from tools.operation_artwork_mode import operation_artwork_mode


COMPATIBILITY_CANONICAL_SHA256 = (
    "94bd58aa689301f8090d8c7d40e89d99b8224cf2cafe61e2beb20fd3cb9de8db"
)


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _write_layered_contract(
    root: Path,
    *,
    overlays: list[dict[str, object]],
    debt_targets: list[dict[str, object]] | None = None,
    shared_schema: str = "web-manual-shared-base/v1",
) -> Path:
    contracts = root / "contracts"
    contracts.mkdir()
    (contracts / "shared.json").write_text(
        json.dumps(
            {
                "schema_version": shared_schema,
                "base_id": "test-base",
                "contract": {
                    "preface": {"targets": []},
                    "figure_coverage": {"requirements": []},
                    "product_overview": {
                        "source_patterns": ["*03_product_overview_placeholder"]
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    (contracts / "skeleton.json").write_text(
        json.dumps(
            {
                "schema_version": "web-manual-skeleton-profile/v1",
                "profile_id": "test-skeleton",
                "contract": {},
            }
        ),
        encoding="utf-8",
    )
    (contracts / "overlays.json").write_text(
        json.dumps(
            {
                "schema_version": "web-manual-target-overlays/v1",
                "overlays": overlays,
            }
        ),
        encoding="utf-8",
    )
    (contracts / "figure_debt.json").write_text(
        json.dumps(
            {
                "schema_version": "web-figure-debt-baseline/v1",
                "targets": debt_targets or [],
            }
        ),
        encoding="utf-8",
    )
    entry = contracts / "web_manual.json"
    entry.write_text(
        json.dumps(
            {
                "schema_version": "web-manual-presentation-stack/v1",
                "shared_base": "shared.json",
                "skeleton_profiles": {"test-skeleton": "skeleton.json"},
                "compatibility_skeleton_profile": "test-skeleton",
                "target_overlays": ["overlays.json"],
                "figure_debt_baseline": "figure_debt.json",
            }
        ),
        encoding="utf-8",
    )
    return entry


class WebPresentationContractTests(unittest.TestCase):
    def test_compatibility_materialization_matches_the_pinned_contract(self) -> None:
        contract = load_web_manual_contract()
        legacy_shape = dict(contract)
        legacy_shape.pop("presentation_layers")
        legacy_shape["schema_version"] = "web-manual-presentation/v1"
        legacy_shape["figure_targets"] = [
            target
            for target in legacy_shape["figure_targets"]
            if target["model"] == "JE-1000F"
        ]
        legacy_requirement = deepcopy(
            next(
                requirement
                for requirement in legacy_shape["figure_coverage"]["requirements"]
                if requirement["target"]
                == {"model": "JE-1000F", "region": "EU"}
            )
        )
        legacy_requirement.pop("policy_id")
        legacy_requirement.pop("known_debt")
        legacy_shape["figure_coverage"]["requirements"] = [legacy_requirement]

        self.assertEqual("web-manual-presentation/v2", contract["schema_version"])
        self.assertEqual(
            COMPATIBILITY_CANONICAL_SHA256,
            _canonical_sha256(legacy_shape),
        )

    def test_charger_target_uses_its_own_finished_art_contract(self) -> None:
        contract = load_web_manual_contract(model="JA-AD600A", region="EU")

        self.assertEqual("charger-v1", contract["presentation_layers"]["skeleton_profile"])
        self.assertEqual(
            [{"model": "JA-AD600A", "region": "EU"}],
            contract["figure_targets"],
        )
        self.assertEqual([], contract["preface"]["targets"])
        requirement = contract["figure_coverage"]["requirements"][0]
        self.assertEqual("ja-ad600a-eu-en-finished-figures-v1", requirement["policy_id"])
        self.assertEqual(5, len(requirement["required_slots"]))
        self.assertEqual(
            ["finished-panel", "approved-composite"],
            requirement["allowed_statuses"],
        )
        self.assertIsNone(contract["operations"]["lcd_mode_table"])
        self.assertIsNone(contract["operations"]["auto_resume_table"])

    def test_trolley_uses_charger_accessory_profile_without_power_features(self) -> None:
        contract = load_web_manual_contract(model="JAAC-WHE-100-EUA1", region="EU")

        self.assertEqual("charger-v1", contract["presentation_layers"]["skeleton_profile"])
        self.assertEqual([], contract["figure_targets"])
        self.assertEqual([], contract["preface"]["targets"])
        self.assertIsNone(contract["operations"]["lcd_mode_table"])
        self.assertIsNone(contract["operations"]["auto_resume_table"])

    def test_us_and_eu_share_one_skeleton_but_keep_target_grants_isolated(self) -> None:
        us = load_web_manual_contract(model="JE-1000F", region="US")
        eu = load_web_manual_contract(model="JE-1000F", region="EU")

        self.assertEqual(
            us["presentation_layers"]["skeleton_profile"],
            eu["presentation_layers"]["skeleton_profile"],
        )
        self.assertEqual("portable-power-station-v1", us["presentation_layers"]["skeleton_profile"])
        self.assertEqual([{"model": "JE-1000F", "region": "US"}], us["figure_targets"])
        self.assertEqual([{"model": "JE-1000F", "region": "EU"}], eu["figure_targets"])
        self.assertEqual([{"model": "JE-1000F", "region": "US"}], us["preface"]["targets"])
        self.assertEqual([], eu["preface"]["targets"])
        self.assertEqual(
            "je1000f-us-finished-figures-v1",
            us["figure_coverage"]["requirements"][0]["policy_id"],
        )
        self.assertEqual("JE-1000F", eu["figure_coverage"]["requirements"][0]["target"]["model"])
        self.assertEqual("EU", eu["figure_coverage"]["requirements"][0]["target"]["region"])
        us_modes = {
            figure["id"]: figure.get("presentation_mode")
            for figure in us["operations"]["figures"]
        }
        eu_modes = {
            figure["id"]: figure.get("presentation_mode")
            for figure in eu["operations"]["figures"]
        }
        self.assertEqual(
            {
                "main-power": "base-art-live-copy",
                "ac-output": "base-art-live-copy",
                "dc-usb-output": "base-art-live-copy",
                "energy-saving": "base-art-live-copy",
                "led-light": "base-art-live-copy",
            },
            {key: value for key, value in us_modes.items() if value},
        )
        for operation_id, presentation_mode in us_modes.items():
            self.assertEqual(
                presentation_mode,
                operation_artwork_mode(
                    model="JE-1000F",
                    region="US",
                    operation_id=operation_id,
                ),
            )
        self.assertFalse(any(eu_modes.values()))
        reference_modes = {
            region: {
                figure["id"]: figure["presentation_mode"]
                for figure in contract["reference_figures"]["figures"]
                if figure.get("presentation_mode")
            }
            for region, contract in (("US", us), ("EU", eu))
        }
        self.assertEqual(
            {"US": {"charging-car": "base-art-live-copy"}, "EU": {}},
            reference_modes,
        )
        self.assertNotIn("instance_id", us["product_overview"])

    def test_us_and_kr_debt_is_explicit_without_weakening_final_statuses(self) -> None:
        us = load_web_manual_contract(model="JE-1000F", region="US")
        kr = load_web_manual_contract(model="JE-3000C", region="KR")

        us_requirement = us["figure_coverage"]["requirements"][0]
        self.assertEqual(["en", "fr", "es"], us_requirement["locales"])
        self.assertEqual(11, len(us_requirement["required_slots"]))
        self.assertEqual(
            ["finished-panel", "approved-composite"],
            us_requirement["allowed_statuses"],
        )
        self.assertEqual(
            {
                "operation.main-power": ["base-art-live-copy"],
                "operation.ac-output": ["base-art-live-copy"],
                "operation.dc-usb-output": ["base-art-live-copy"],
                "operation.energy-saving": ["base-art-live-copy"],
                "operation.led-light": ["base-art-live-copy"],
                "reference.charging-car": ["base-art-live-copy"],
            },
            us_requirement["slot_status_overrides"],
        )
        self.assertEqual(9, len(us_requirement["known_debt"]))
        self.assertEqual(
            {"editable-fallback"},
            {entry["status"] for entry in us_requirement["known_debt"]},
        )

        self.assertEqual([], kr["figure_targets"])
        kr_requirement = kr["figure_coverage"]["requirements"][0]
        self.assertEqual(["ko"], kr_requirement["locales"])
        self.assertEqual(9, len(kr_requirement["required_slots"]))
        self.assertEqual(9, len(kr_requirement["known_debt"]))
        self.assertEqual(
            {"missing"},
            {entry["status"] for entry in kr_requirement["known_debt"]},
        )

    def test_eu_finished_art_policy_covers_italian_and_forbids_html_fallback(self) -> None:
        eu = load_web_manual_contract(model="JE-1000F", region="EU")
        requirement = eu["figure_coverage"]["requirements"][0]

        self.assertIn("it", requirement["locales"])
        self.assertEqual(
            ["finished-panel", "approved-composite"],
            requirement["allowed_statuses"],
        )
        self.assertNotIn("editable-fallback", requirement["allowed_statuses"])
        self.assertEqual(11, len(requirement["required_slots"]))
        self.assertEqual(
            {
                "product-overview.front",
                "product-overview.right",
                "operation.main-power",
                "operation.ac-output",
                "operation.dc-usb-output",
                "operation.energy-saving",
                "operation.led-light",
                "reference.charging-ac-wall",
                "reference.charging-solar-direct",
                "reference.charging-solar-adapter",
                "reference.charging-car",
            },
            set(requirement["required_slots"]),
        )

    def test_non_figure_target_can_select_the_skeleton_without_inheriting_art_grants(self) -> None:
        kr = load_web_manual_contract(model="JE-3000C", region="KR")

        self.assertEqual("portable-power-station-v1", kr["presentation_layers"]["skeleton_profile"])
        self.assertEqual([], kr["figure_targets"])
        self.assertEqual([], kr["preface"]["targets"])
        self.assertEqual(
            "je3000c-kr-finished-figures-v1",
            kr["figure_coverage"]["requirements"][0]["policy_id"],
        )
        self.assertEqual("operation/lcd_mode", kr["operations"]["lcd_mode_table"]["image_key"])

    def test_unknown_target_receives_only_shared_semantics(self) -> None:
        contract = load_web_manual_contract(model="OTHER", region="XX")

        self.assertIsNone(contract["presentation_layers"]["skeleton_profile"])
        self.assertIsNone(contract["presentation_layers"]["target_overlay"])
        self.assertEqual([], contract["figure_targets"])
        self.assertEqual(
            ["*03_product_overview_placeholder"],
            contract["product_overview"]["source_patterns"],
        )
        self.assertEqual(
            ["*05_operation_guide_placeholder"],
            contract["operations"]["source_patterns"],
        )
        self.assertEqual(4, contract["operations"]["auto_resume_table"]["body_rows"])
        self.assertEqual(
            3,
            contract["operations"]["key_combination_table"]["minimum_body_rows"],
        )
        self.assertEqual(
            "operation/lcd_mode",
            contract["operations"]["lcd_mode_table"]["image_key"],
        )
        self.assertEqual(6, contract["operations"]["lcd_mode_table"]["body_rows"])
        self.assertEqual(
            ["*12_app_setup_placeholder"],
            contract["reference_figures"]["source_patterns"],
        )
        self.assertEqual(
            ["app-add-device"],
            [figure["id"] for figure in contract["reference_figures"]["figures"]],
        )
        self.assertEqual(["*11_warranty"], contract["warranty"]["source_patterns"])
        self.assertEqual(["box_contents_*"], contract["in_the_box"]["semantic_source_patterns"])

    def test_mapping_and_id_keyed_lists_merge_without_repeating_the_skeleton(self) -> None:
        base = {
            "nested": {"kept": 1, "changed": "base"},
            "figures": [
                {"id": "first", "rect": [1, 2, 3, 4], "copy": "kept"},
                {"id": "second", "rect": [5, 6, 7, 8]},
            ],
            "ordinary": ["base", "values"],
        }
        overlay = {
            "nested": {"changed": "target"},
            "figures": [
                {"id": "first", "rect": [9, 10, 11, 12]},
                {"id": "third", "rect": [13, 14, 15, 16]},
            ],
            "ordinary": ["replacement"],
        }

        merged = merge_contract_layers(base, overlay, field="target.contract_overrides")

        self.assertEqual({"kept": 1, "changed": "target"}, merged["nested"])
        self.assertEqual(["first", "second", "third"], [item["id"] for item in merged["figures"]])
        self.assertEqual("kept", merged["figures"][0]["copy"])
        self.assertEqual([9, 10, 11, 12], merged["figures"][0]["rect"])
        self.assertEqual(["replacement"], merged["ordinary"])

    def test_id_keyed_overlay_rejects_duplicate_ids(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate id 'one'"):
            merge_contract_layers(
                [{"id": "one", "value": 1}],
                [{"id": "one", "value": 2}, {"id": "one", "value": 3}],
                field="figures",
            )

    def test_layer_paths_cannot_escape_the_contract_directory(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            contracts = root / "contracts"
            contracts.mkdir()
            outside = root / "outside.json"
            outside.write_text("{}", encoding="utf-8")
            entry = contracts / "web_manual.json"
            entry.write_text(
                json.dumps(
                    {
                        "schema_version": "web-manual-presentation-stack/v1",
                        "shared_base": "../outside.json",
                        "compatibility_skeleton_profile": "demo",
                        "skeleton_profiles": {},
                        "target_overlays": [],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(WebPresentationError, "escapes contract directory"):
                load_web_manual_contract(entry)

    def test_model_and_region_must_be_resolved_together(self) -> None:
        with self.assertRaisesRegex(WebPresentationError, "supplied together"):
            load_web_manual_contract(model="JE-1000F")

    def test_duplicate_target_overlay_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            target = {"model": "MODEL", "region": "REGION"}
            overlays = [
                {
                    "overlay_id": overlay_id,
                    "target": target,
                    "skeleton_profile": "test-skeleton",
                }
                for overlay_id in ("one", "two")
            ]
            entry = _write_layered_contract(Path(td), overlays=overlays)

            with self.assertRaisesRegex(WebPresentationError, "duplicate target overlay"):
                load_web_manual_contract(entry)

    def test_unknown_skeleton_and_bad_shared_schema_are_rejected(self) -> None:
        overlay = {
            "overlay_id": "one",
            "target": {"model": "MODEL", "region": "REGION"},
            "skeleton_profile": "unknown",
        }
        with tempfile.TemporaryDirectory() as td:
            entry = _write_layered_contract(Path(td), overlays=[overlay])
            with self.assertRaisesRegex(WebPresentationError, "unknown profile"):
                load_web_manual_contract(entry)
        with tempfile.TemporaryDirectory() as td:
            entry = _write_layered_contract(
                Path(td),
                overlays=[{**overlay, "skeleton_profile": "test-skeleton"}],
                shared_schema="bad-schema",
            )
            with self.assertRaisesRegex(WebPresentationError, "shared base schema"):
                load_web_manual_contract(entry)

    def test_coverage_cannot_rebind_the_overlay_target(self) -> None:
        overlay = {
            "overlay_id": "one",
            "target": {"model": "MODEL", "region": "REGION"},
            "skeleton_profile": "test-skeleton",
            "figure_coverage": {
                "target": {"model": "OTHER", "region": "OTHER"},
            },
        }
        with tempfile.TemporaryDirectory() as td:
            entry = _write_layered_contract(Path(td), overlays=[overlay])
            with self.assertRaisesRegex(WebPresentationError, "cannot override"):
                load_web_manual_contract(entry)

    def test_figure_capability_requires_complete_strict_coverage(self) -> None:
        base_overlay = {
            "overlay_id": "one",
            "target": {"model": "JE-1000F", "region": "US"},
            "skeleton_profile": "test-skeleton",
            "capabilities": {"figures": True},
        }
        with tempfile.TemporaryDirectory() as td:
            entry = _write_layered_contract(Path(td), overlays=[base_overlay])
            with self.assertRaisesRegex(WebPresentationError, "requires figure_coverage"):
                load_web_manual_contract(entry, model="JE-1000F", region="US")

        invalid = {
            **base_overlay,
            "figure_coverage": {
                "policy_id": "test-policy",
                "locales": ["en"],
                "required_slots": [
                    "product-overview.front",
                    "product-overview.right",
                ],
                "allowed_statuses": [
                    "finished-panel",
                    "approved-composite",
                    "editable-fallback",
                ],
            },
        }
        with tempfile.TemporaryDirectory() as td:
            entry = _write_layered_contract(Path(td), overlays=[invalid])
            with self.assertRaisesRegex(WebPresentationError, "only finished artwork"):
                load_web_manual_contract(entry, model="JE-1000F", region="US")

        incomplete = deepcopy(invalid)
        incomplete["figure_coverage"]["allowed_statuses"] = [
            "finished-panel",
            "approved-composite",
        ]
        incomplete["figure_coverage"]["required_slots"] = [
            "product-overview.front"
        ]
        with tempfile.TemporaryDirectory() as td:
            entry = _write_layered_contract(Path(td), overlays=[incomplete])
            with self.assertRaisesRegex(WebPresentationError, "required_slots are incomplete"):
                load_web_manual_contract(entry, model="JE-1000F", region="US")

    def test_footer_panel_base_art_declares_art_width_and_step_markers(self) -> None:
        def overlay(layout: dict[str, object]) -> dict[str, object]:
            return {
                "overlay_id": "one",
                "target": {"model": "MODEL", "region": "REGION"},
                "skeleton_profile": "test-skeleton",
                "figure_coverage": {
                    "policy_id": "test-policy",
                    "locales": ["en"],
                    "required_slots": ["operation.led-light"],
                    "allowed_statuses": ["finished-panel", "approved-composite"],
                    "slot_status_overrides": {"operation.led-light": ["base-art-live-copy"]},
                },
                "contract_overrides": {"operations": {"figures": [{
                    "id": "led-light",
                    "web_replace_key": "operation.led-light",
                    "layout": "footer-panel",
                    "step_ids": ["light", "sos", "off"],
                    # The lead is its own panel: no drawn pill, rect or tone.
                    "capture_prerequisite": True,
                    "presentation_mode": "base-art-live-copy",
                    "base_art_layout": layout,
                }]}},
            }

        layout = {
            "art_sha256": "d" * 64,
            "art_width": 56.8,
            "step_markers": ["bulb-lit", "sos", "bulb-off"],
        }
        with tempfile.TemporaryDirectory() as td:
            entry = _write_layered_contract(Path(td), overlays=[overlay(layout)])
            load_web_manual_contract(entry, model="MODEL", region="REGION")
        for label, candidate, message in (
            ("no art width", {k: v for k, v in layout.items() if k != "art_width"}, "art_width"),
            ("marker per step", {**layout, "step_markers": ["bulb-lit", "sos"]}, "step_markers"),
            ("unknown marker", {**layout, "step_markers": ["bulb-lit", "star", "bulb-off"]}, "step_markers"),
        ):
            with self.subTest(label), tempfile.TemporaryDirectory() as td:
                entry = _write_layered_contract(Path(td), overlays=[overlay(candidate)])
                with self.assertRaisesRegex(WebPresentationError, message):
                    load_web_manual_contract(entry, model="MODEL", region="REGION")

    def test_base_art_mode_requires_an_exact_coverage_grant(self) -> None:
        layout: dict[str, object] = {
            "art_sha256": "a" * 64,
            "step_anchors": [[76.5, 15.4], [76.5, 34.2]],
            "step_width": 22.5,
        }

        def overlay(
            *,
            mode: str = "base-art-live-copy",
            coverage: dict[str, object] | None = None,
            base_art_layout: dict[str, object] | None = None,
            capture_prerequisite: bool = False,
        ) -> dict[str, object]:
            figure: dict[str, object] = {
                "id": "main-power",
                "web_replace_key": "operation.main-power",
                "layout": "status-right",
                "step_ids": ["on", "off"],
                "presentation_mode": mode,
            }
            if capture_prerequisite:
                figure["capture_prerequisite"] = True
            if base_art_layout is not None:
                figure["base_art_layout"] = base_art_layout
            value: dict[str, object] = {
                "overlay_id": "one",
                "target": {"model": "MODEL", "region": "REGION"},
                "skeleton_profile": "test-skeleton",
                "contract_overrides": {"operations": {"figures": [figure]}},
            }
            if coverage is not None:
                value["figure_coverage"] = coverage
            return value

        def policy(overrides: dict[str, list[str]]) -> dict[str, object]:
            return {
                "policy_id": "test-policy",
                "locales": ["en"],
                "required_slots": ["operation.main-power"],
                "allowed_statuses": ["finished-panel", "approved-composite"],
                "slot_status_overrides": overrides,
            }

        grant = policy({"operation.main-power": ["base-art-live-copy"]})
        rejected = (
            (
                "no coverage grant",
                overlay(base_art_layout=layout),
                "require figure_coverage",
            ),
            (
                "unknown mode",
                overlay(mode="base-art", coverage=policy({}), base_art_layout=layout),
                "unsupported presentation_mode",
            ),
            (
                "grant outside required slots",
                overlay(
                    coverage=policy({"operation.ac-output": ["base-art-live-copy"]}),
                    base_art_layout=layout,
                ),
                "outside required_slots",
            ),
            (
                "grant missing for a declared mode",
                overlay(coverage=policy({}), base_art_layout=layout),
                "exactly match",
            ),
            ("no measured layout", overlay(coverage=grant), "base_art_layout is required"),
            (
                "layout names an unknown key",
                overlay(coverage=grant, base_art_layout={**layout, "leader_path": []}),
                "unknown keys",
            ),
            (
                "layout without the measured art",
                overlay(coverage=grant, base_art_layout={**layout, "art_sha256": "x"}),
                "must name the measured art",
            ),
            (
                "one anchor for two steps",
                overlay(
                    coverage=grant,
                    base_art_layout={**layout, "step_anchors": [[76.5, 15.4]]},
                ),
                "one anchor per step",
            ),
            (
                "anchor outside the art",
                overlay(
                    coverage=grant,
                    base_art_layout={**layout, "step_anchors": [[76.5, 15.4], [101, 2]]},
                ),
                "percentages",
            ),
            (
                "pill without its measured tone",
                overlay(
                    coverage=grant,
                    capture_prerequisite=True,
                    base_art_layout={**layout, "prerequisite_rect": [1, 2, 40, 6]},
                ),
                "prerequisite_fill",
            ),
            (
                "pill tone that is not #rrggbb",
                overlay(
                    coverage=grant,
                    capture_prerequisite=True,
                    base_art_layout={
                        **layout,
                        "prerequisite_rect": [1, 2, 40, 6],
                        "prerequisite_fill": "#E8E8E8",
                    },
                ),
                "prerequisite_fill",
            ),
        )
        for label, candidate, message in rejected:
            with self.subTest(label), tempfile.TemporaryDirectory() as td:
                entry = _write_layered_contract(Path(td), overlays=[candidate])
                with self.assertRaisesRegex(WebPresentationError, message):
                    load_web_manual_contract(entry, model="MODEL", region="REGION")

        paired = overlay(coverage=grant, base_art_layout=layout)
        with tempfile.TemporaryDirectory() as td:
            entry = _write_layered_contract(Path(td), overlays=[paired])
            contract = load_web_manual_contract(entry, model="MODEL", region="REGION")
        pill = overlay(
            coverage=grant,
            capture_prerequisite=True,
            base_art_layout={
                **layout,
                "prerequisite_rect": [1, 2, 40, 6],
                "prerequisite_fill": "#e8e8e8",
            },
        )
        with tempfile.TemporaryDirectory() as td:
            entry = _write_layered_contract(Path(td), overlays=[pill])
            load_web_manual_contract(entry, model="MODEL", region="REGION")
        requirement = contract["figure_coverage"]["requirements"][0]
        self.assertEqual(
            {"operation.main-power": ["base-art-live-copy"]},
            requirement["slot_status_overrides"],
        )

    def test_reference_base_art_places_each_captured_line_once(self) -> None:
        vehicle = {"line": 0, "rect": [64.0, 30.6, 18.0, 8.96]}
        note = {"line": 1, "rect": [55.0, 3.73, 42.12, 11.19], "fill": "#ffffff"}
        layout: dict[str, object] = {
            "art_sha256": "c" * 64,
            "panel_top": 6.15,
            "panel_fill": "#f2f3f3",
            "labels": [vehicle, note],
        }

        def overlay(
            base_art_layout: dict[str, object] | None,
            *,
            mode: str = "base-art-live-copy",
            granted: bool = True,
        ) -> dict[str, object]:
            figure: dict[str, object] = {
                "id": "charging-car",
                "web_replace_key": "reference.charging-car",
                "capture_following_lines": 2,
                "presentation_mode": mode,
            }
            if base_art_layout is not None:
                figure["base_art_layout"] = base_art_layout
            return {
                "overlay_id": "one",
                "target": {"model": "MODEL", "region": "REGION"},
                "skeleton_profile": "test-skeleton",
                "figure_coverage": {
                    "policy_id": "test-policy",
                    "locales": ["en"],
                    "required_slots": ["reference.charging-car"],
                    "allowed_statuses": ["finished-panel", "approved-composite"],
                    "slot_status_overrides": (
                        {"reference.charging-car": ["base-art-live-copy"]}
                        if granted
                        else {}
                    ),
                },
                "contract_overrides": {"reference_figures": {"figures": [figure]}},
            }

        def placed(**changes: object) -> dict[str, object]:
            return {**layout, "labels": [vehicle, {**note, **changes}]}

        with tempfile.TemporaryDirectory() as td:
            entry = _write_layered_contract(Path(td), overlays=[overlay(layout)])
            contract = load_web_manual_contract(entry, model="MODEL", region="REGION")
        self.assertEqual(
            {"reference.charging-car": ["base-art-live-copy"]},
            contract["figure_coverage"]["requirements"][0]["slot_status_overrides"],
        )
        rejected = (
            ("grant missing for a declared mode", overlay(layout, granted=False), "exactly match"),
            ("unknown mode", overlay(layout, mode="base-art"), "unsupported presentation_mode"),
            ("no measured layout", overlay(None), "base_art_layout is required"),
            ("layout names an unknown key", overlay({**layout, "leader_path": []}), "unknown keys"),
            ("layout without the measured art", overlay({**layout, "art_sha256": "x"}), "must name the measured art"),
            ("band outside the panel", overlay({**layout, "panel_top": 101}), "panel_top"),
            ("panel tone that is not #rrggbb", overlay({**layout, "panel_fill": "#F2F3F3"}), "panel_fill"),
            ("a captured line left unplaced", overlay({**layout, "labels": [vehicle]}), "place each captured"),
            ("a line placed twice", overlay(placed(line=0)), "distinct captured line"),
            ("a line that was not captured", overlay(placed(line=2)), "distinct captured line"),
            ("rect outside the panel", overlay(placed(rect=[55, 3.73, 42.12, 111])), "rect must be 4 percentages"),
            ("pill tone that is not #rrggbb", overlay(placed(fill="white")), "fill must be a #rrggbb tone"),
            ("label names a leader", overlay(placed(leader=[1, 2])), "must name only"),
        )
        for label, candidate, message in rejected:
            with self.subTest(label), tempfile.TemporaryDirectory() as td:
                entry = _write_layered_contract(Path(td), overlays=[candidate])
                with self.assertRaisesRegex(WebPresentationError, message):
                    load_web_manual_contract(entry, model="MODEL", region="REGION")

    def test_debt_baseline_cannot_grant_an_unmatched_or_rebound_exception(self) -> None:
        policy = {
            "policy_id": "test-policy",
            "locales": ["en"],
            "required_slots": [
                "product-overview.front",
                "product-overview.right",
            ],
            "allowed_statuses": ["finished-panel", "approved-composite"],
        }
        overlay = {
            "overlay_id": "one",
            "target": {"model": "JE-1000F", "region": "US"},
            "skeleton_profile": "test-skeleton",
            "capabilities": {"figures": True},
            "figure_coverage": policy,
        }
        debt = {
            "target": {"model": "OTHER", "region": "XX"},
            "policy_id": "test-policy",
            "known_debt": [],
        }
        with tempfile.TemporaryDirectory() as td:
            entry = _write_layered_contract(
                Path(td), overlays=[overlay], debt_targets=[debt]
            )
            with self.assertRaisesRegex(WebPresentationError, "has no target overlay"):
                load_web_manual_contract(entry, model="JE-1000F", region="US")

        rebound = {
            **debt,
            "target": {"model": "JE-1000F", "region": "US"},
            "policy_id": "other-policy",
        }
        with tempfile.TemporaryDirectory() as td:
            entry = _write_layered_contract(
                Path(td), overlays=[overlay], debt_targets=[rebound]
            )
            with self.assertRaisesRegex(WebPresentationError, "policy_id does not match"):
                load_web_manual_contract(entry, model="JE-1000F", region="US")


if __name__ == "__main__":
    unittest.main()
