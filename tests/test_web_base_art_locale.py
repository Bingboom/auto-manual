from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import re
import shutil
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from bs4 import BeautifulSoup
from PIL import Image

from tests.test_web_presentation_contract import _write_layered_contract
from tools.component_specs.operation_html import parse_operation_components
from tools.component_specs.operation import operation_semantic_projection
from tools.web_base_art_locale import base_art_locale_layouts, resolve_base_art_figure
from tools.web_composite_presentation import WebCompositeContext
from tools.web_figure_coverage import build_web_figure_coverage, enforce_required_web_figure_coverage
from tools.web_operation_component import render_operation_component
from tools.web_presentation import WebPresentationError, load_web_manual_contract
from tools.web_document_source import load_web_document
from tools.web_document_ir import render_document_fragments
from tools.manual_ir import read_manual_ir
from tools.word_bundle_html import _convert_rst_fragment_to_html


SLOT = "operation.main-power"
SOURCE = Path("page/05_operation_guide_placeholder.rst")


def _figure() -> dict:
    return {
        "id": "main-power", "image_key": "operation/main_power",
        "web_replace_key": SLOT, "layout": "status-right",
        "step_ids": ["on", "off"], "capture_following_lines": 1,
        "base_art_layout_by_locale": {
            "en": {"art_sha256": "a" * 64, "copy_layout": "flow"},
            "de": {"art_sha256": "b" * 64, "copy_layout": "flow"},
        },
    }


def _overlay(figure: dict | None = None) -> dict:
    return {
        "overlay_id": "locale-pilot", "target": {"model": "MODEL", "region": "EU"},
        "skeleton_profile": "test-skeleton",
        "capabilities": {"figures": False, "legacy_target_components": False},
        "contract_overrides": {"operations": {"source_patterns": ["*05_operation*"],
                                               "figures": [figure or _figure()]}},
        "figure_coverage": {"policy_id": "pilot", "locales": ["en", "de", "fr", "es", "it", "uk"],
                            "required_slots": [SLOT],
                            "allowed_statuses": ["finished-panel", "approved-composite"],
                            "slot_status_overrides": {SLOT: ["base-art-live-copy"]}},
    }


def _contract(overlay: dict | None = None) -> dict:
    with tempfile.TemporaryDirectory() as td:
        entry = _write_layered_contract(Path(td), overlays=[overlay or _overlay()])
        return load_web_manual_contract(entry, model="MODEL", region="EU")


def _carrier(language: str) -> str:
    steps = ("Ein: Einmal drücken.", "Aus: 3 s lang gedrückt halten.") if language == "de" else (
        "On: Press once.", "Off: Press and hold for 3s.")
    return '<img src="main_power.png" alt="Power"><div class="line-block">' + ''.join(
        f'<div class="line">{s}</div>' for s in (*steps, "Standby copy.")
    ) + '</div>'


class BaseArtLocaleTests(unittest.TestCase):
    def test_real_eu_templates_keep_steps_supporting_counts_and_warning_boundary(self):
        from tools.web_presentation import _transform_operation_figure

        root = Path(__file__).resolve().parents[1]
        figures = deepcopy(load_web_manual_contract(model="JE-1000F", region="EU")["operations"]["figures"][:3])
        for figure in figures:
            figure.pop("presentation_mode", None)
            figure.pop("base_art_layout", None)
            figure["base_art_layout_by_locale"] = _figure()["base_art_layout_by_locale"]
        cases = [
            ("JE-2000F", lang, 4, root / "docs" / "templates" / f"page_eu-{lang}" / SOURCE.name)
            for lang in ("en", "de")
        ] + [
            ("JE-1000F", lang, 3, root / "docs" / "_review" / "JE-1000F" / "EU" / "page" / name)
            for lang, name in (("en", SOURCE.name), ("de", "p53_" + SOURCE.name))
        ]
        for model, language, support_count, source in cases:
            figures[0]["capture_following_lines"] = support_count
            target = root / "docs" / "_build" / model / "EU" / language / SOURCE
            with tempfile.TemporaryDirectory() as td:
                html = _convert_rst_fragment_to_html(source.read_text(), target, Path(td), language=language)
            soup = BeautifulSoup(html, "html.parser")
            parsed = parse_operation_components(soup, source_path=target,
                                                 config={"figures": figures}, language=language)
            context = WebCompositeContext(None, model, "EU", language, ValueError)
            for figure, (spec, owned, _, semantic_only) in zip(figures, parsed, strict=True):
                # Real EU RST includes blank | lines before AC/DC steps and
                # between main-power steps/supporting copy. Both render paths
                # must agree on the parser's nonempty source-line ownership.
                projection = operation_semantic_projection(spec)
                self.assertEqual(2, len(projection["steps"]))
                support = projection["supporting_copy"]
                self.assertEqual(support_count if figure["id"] == "main-power" else 0, len(support))
                outside_note = ""
                if model == "JE-1000F" and figure["id"] == "main-power":
                    outside_note = semantic_only[-1].find_next_sibling(class_="line").get_text(" ", strip=True)
                for node in semantic_only:
                    node.extract()
                carrier = "".join(str(node) for node in owned)
                replay = render_operation_component(spec, carrier, source_path=target,
                                                     presentation=figure, composites=context)
                direct = BeautifulSoup(html, "html.parser")
                image = next(img for img in direct.find_all("img")
                             if figure["image_key"].split("/")[-1] in img["src"])
                _transform_operation_figure(direct, image=image,
                    spec=resolve_base_art_figure(figure, language), source_path=target, composites=context)
                for rendered in (BeautifulSoup(replay, "html.parser"), direct):
                    panel = rendered.select_one(f'figure[data-operation-id="{figure["id"]}"]')
                    steps = panel.select(".hb-operation-step")
                    self.assertEqual(2, len(steps))
                    for step, expected in zip(steps, projection["steps"], strict=True):
                        expected_text = " ".join(part["text"] for part in expected["parts"]).replace(":", "")
                        self.assertIn(expected_text, step.get_text(" ", strip=True))
                    self.assertEqual(len(support), len(panel.select(".hb-operation-supporting-copy > .line")))
                    for value in support:
                        text = BeautifulSoup(value, "html.parser").get_text(" ", strip=True)
                        self.assertEqual(1, panel.get_text(" ", strip=True).count(text))
                    self.assertNotIn("IEC/EN/UL 62368-1", panel.get_text())
                    if projection["prerequisite_html"]:
                        prerequisite = BeautifulSoup(projection["prerequisite_html"], "html.parser").get_text(" ", strip=True)
                        self.assertEqual(1, panel.get_text(" ", strip=True).count(prerequisite))
                    if outside_note:
                        self.assertNotIn(outside_note, panel.get_text(" ", strip=True))
                if outside_note:
                    self.assertEqual(1, direct.get_text(" ", strip=True).count(outside_note))
                    self.assertEqual(1, soup.get_text(" ", strip=True).count(outside_note))
                self.assertEqual(1, direct.get_text().count("IEC/EN/UL 62368-1"))

    def test_exact_selection_is_order_independent_and_does_not_mutate_contract(self):
        figure = _figure()
        before = deepcopy(figure)
        for order in (("en", "de", "fr"), ("fr", "de", "en")):
            for language in order:
                resolved = resolve_base_art_figure(figure, language)
                self.assertNotIn("base_art_layout_by_locale", resolved)
                if language in ("en", "de"):
                    self.assertEqual(figure["base_art_layout_by_locale"][language], resolved["base_art_layout"])
                    resolved["base_art_layout"]["art_sha256"] = "c" * 64
                else:
                    self.assertNotIn("presentation_mode", resolved)
                    self.assertNotIn("base_art_layout", resolved)
        self.assertEqual(before, figure)
        for language in ("fr", "es", "it", "uk"):
            expected = {k: v for k, v in figure.items() if k != "base_art_layout_by_locale"}
            self.assertEqual(expected, resolve_base_art_figure(figure, language))
        for language in (None, "", "und"):
            with self.assertRaisesRegex(ValueError, "explicit page language"):
                resolve_base_art_figure(figure, language)
        legacy = {"presentation_mode": "base-art-live-copy", "base_art_layout": {
            "art_sha256": "a" * 64, "copy_layout": "flow"}}
        self.assertEqual(legacy, resolve_base_art_figure(legacy, None))

    def test_invalid_scopes_hashes_and_parallel_modes_are_rejected(self):
        for changes in (
            {"presentation_mode": "base-art-live-copy"},
            {"base_art_layout": {"art_sha256": "a" * 64}},
            {"layout": "footer-panel"},
            {"base_art_layout_by_locale": {}},
            {"base_art_layout_by_locale": {"en": {"copy_layout": "flow"}}},
            {"base_art_layout_by_locale": {"de": {"art_sha256": "bad", "copy_layout": "flow"}}},
            {"base_art_layout_by_locale": {"EN": {"art_sha256": "a" * 64, "copy_layout": "flow"}}},
            {"base_art_layout_by_locale": {"und": {"art_sha256": "a" * 64, "copy_layout": "flow"}}},
            {"base_art_layout_by_locale": {"en": {"art_sha256": "a" * 64, "copy_layout": "flow", "step_width": 10}}},
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                base_art_locale_layouts({**_figure(), **changes})
        for mutate, message in (
            (lambda o: o["figure_coverage"].update(slot_status_overrides={}), "exactly match"),
            (lambda o: o["figure_coverage"].update(locales=["en"]), "outside coverage"),
            (lambda o: o["figure_coverage"].update(slot_status_override_locales={SLOT: ["en"]}), "derived"),
        ):
            overlay = _overlay()
            mutate(overlay)
            with self.subTest(message=message), self.assertRaisesRegex(WebPresentationError, message):
                _contract(overlay)

    def test_duplicate_json_locale_key_is_not_silently_overwritten(self):
        with tempfile.TemporaryDirectory() as td:
            entry = _write_layered_contract(Path(td), overlays=[_overlay()])
            path = entry.parent / "overlays.json"
            text = path.read_text()
            text = text.replace('"de": {"art_sha256":', '"en": {"art_sha256":')
            path.write_text(text)
            with self.assertRaisesRegex(WebPresentationError, "target overlay registry.*overlays.json.*duplicate contract JSON key 'en'"):
                load_web_manual_contract(entry, model="MODEL", region="EU")

    def test_scope_is_derived_and_nonpilot_locales_keep_finished_gate(self):
        contract = _contract()
        requirement = contract["figure_coverage"]["requirements"][0]
        self.assertEqual({SLOT: ["de", "en"]}, requirement["slot_status_override_locales"])
        ir = SimpleNamespace(model="MODEL", region="EU", metadata={"web_contract": contract})
        coverage = {"model": "MODEL", "region": "EU", "slots": [
            {"locale": language, "slot_id": SLOT,
             "status": "base-art-live-copy" if language in ("en", "de") else "finished-panel"}
            for language in ("en", "de", "fr", "es", "it", "uk")
        ]}
        enforce_required_web_figure_coverage(ir, coverage)
        for wrong in ("base-art-live-copy", "editable-fallback", "missing"):
            bad = deepcopy(coverage)
            bad["slots"][2]["status"] = wrong
            with self.assertRaisesRegex(ValueError, f"fr/{SLOT}={wrong}"):
                enforce_required_web_figure_coverage(ir, bad)
        requirement["slot_status_override_locales"][SLOT].append("fr")
        with self.assertRaisesRegex(ValueError, "frozen locale scope disagrees"):
            enforce_required_web_figure_coverage(ir, coverage)

    def test_parser_freezes_selected_hash_and_replay_checks_locale_and_layout(self):
        figure = _figure()
        for language in ("en", "de", "fr", "es", "it", "uk"):
            with self.subTest(language=language):
                parsed = parse_operation_components(
                    BeautifulSoup(_carrier(language), "html.parser"), source_path=SOURCE,
                    config={"figures": [figure]}, language=language,
                )
                spec = parsed[0][0]
                context = WebCompositeContext(None, "MODEL", "EU", language, ValueError)
                carrier = _carrier(language).replace('<div class="line">Standby copy.</div>', '')
                if language not in ("en", "de"):
                    self.assertEqual({}, spec.metadata)
                    legacy_figure = {k: v for k, v in figure.items() if k != "base_art_layout_by_locale"}
                    self.assertEqual(
                        render_operation_component(spec, carrier, source_path=SOURCE,
                                                   presentation=legacy_figure, composites=context),
                        render_operation_component(spec, carrier, source_path=SOURCE,
                                                   presentation=figure, composites=context),
                    )
                    continue
                layout = figure["base_art_layout_by_locale"][language]
                self.assertEqual(layout, spec.metadata["base_art_layout"])
                self.assertEqual(language, spec.metadata["base_art_locale"])
                rendered = render_operation_component(spec, carrier, source_path=SOURCE,
                                                       presentation=figure, composites=context)
                self.assertIn("hb-operation-copy-flow", rendered)
                self.assertEqual(1, rendered.count("Standby copy."))
                with self.assertRaisesRegex(ValueError, "language disagree"):
                    render_operation_component(spec, carrier, source_path=SOURCE, presentation=figure,
                                               composites=replace(context, language="de" if language == "en" else "en"))
                for change in (
                    {"base_art_layout": {**layout, "art_sha256": "f" * 64}},
                    {"base_art_locale": "fr"},
                    {"presentation_mode": None},
                ):
                    corrupt = replace(spec, metadata={**spec.metadata, **change})
                    with self.assertRaisesRegex(ValueError, "frozen base-art locale/layout disagrees"):
                        render_operation_component(corrupt, carrier, source_path=SOURCE,
                                                   presentation=figure, composites=context)

    def test_packaged_image_must_match_the_page_locale(self):
        contract = _contract()
        for language, digest in (("en", "a" * 64), ("de", "b" * 64)):
            path = f"assets/ir/{language}/main_power.png"
            ir = SimpleNamespace(model="MODEL", region="EU", pages=(SimpleNamespace(
                page_id="05_operation_guide_placeholder.rst", language=language),), metadata={
                    "web_contract": contract, "composites": [], "asset_sha256": {path: digest},
                    "illustration_provenance": {"illustrations": []},
                })
            fragment = (f'<figure class="hb-base-art-live-copy" data-web-replace-key="{SLOT}" '
                        'data-web-presentation-mode="base-art-live-copy" data-web-base-art-ref="operation/main_power">'
                        f'<img src="{path}"></figure>')
            self.assertEqual(digest, build_web_figure_coverage(ir, (fragment,))["slots"][0]["asset"]["sha256"])
            ir.metadata["asset_sha256"][path] = "c" * 64
            with self.assertRaisesRegex(ValueError, "frozen art"):
                build_web_figure_coverage(ir, (fragment,))

    def test_two_locale_package_replays_without_source_or_live_contract(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pages = []
            layouts = {}
            for language, color in (("en", "red"), ("de", "blue")):
                directory = root / "docs" / "_build" / "JE-1000F" / "EU" / language
                directory.mkdir(parents=True)
                image = directory / "main_power.png"
                Image.new("RGB", (12, 8), color).save(image)
                layouts[language] = {"art_sha256": hashlib.sha256(image.read_bytes()).hexdigest(),
                                     "copy_layout": "flow"}
                page = directory / f"{language}_05_operation_guide_placeholder.rst"
                source = (Path(__file__).resolve().parents[1] / "docs" / "templates"
                          / f"page_eu-{language}" / "05_operation_guide_placeholder.rst")
                text = source.read_text()
                for asset in set(re.findall(r"asset:([a-z_/]+)", text)):
                    candidate = directory / (asset.rsplit("/", 1)[-1] + ".png")
                    if not candidate.exists():
                        shutil.copyfile(image, candidate)
                    text = text.replace(f"asset:{asset}", str(candidate))
                page.write_text(text)
                pages.append(page)
            contract = load_web_manual_contract(model="JE-1000F", region="EU")
            figure = {**_figure(), "base_art_layout_by_locale": layouts}
            contract["operations"]["figures"] = [figure]
            contract["operations"]["source_patterns"] = ["*05_operation*"]
            requirement = _contract()["figure_coverage"]["requirements"][0]
            requirement["target"]["model"] = "JE-1000F"
            contract["figure_coverage"]["requirements"] = [requirement]
            output = root / "package"
            materialized = SimpleNamespace(model="JE-1000F", region="EU", lang="",
                languages=("en", "de"), bundle_dir=root, title="Synthetic locale-binding fixture")
            with patch("tools.web_document_source.load_web_manual_contract", return_value=contract):
                load_web_document(materialized, page_paths=pages, declarations={},
                    page_languages={p.name: p.name[:2] for p in pages}, active_tags=set(),
                    output_dir=output, composite_manifest=None)
            raw = json.loads((output / "manual.ir.json").read_text())
            found = {}
            def visit(value):
                if isinstance(value, dict):
                    if value.get("component_id") == "HB-SPECIAL-OPERATION":
                        found[value["language"]] = value["metadata"]
                    for child in value.values():
                        visit(child)
                elif isinstance(value, list):
                    for child in value:
                        visit(child)
            visit(raw)
            self.assertEqual({lang: {"presentation_mode": "base-art-live-copy",
                "base_art_layout": layout, "base_art_locale": lang} for lang, layout in layouts.items()}, found)
            shutil.rmtree(root / "docs")
            with (
                patch("tools.web_presentation.load_web_manual_contract", side_effect=AssertionError("live contract read")),
                patch("tools.manual_ir.whole_document_components.parse_operation_components", side_effect=AssertionError("source read")),
            ):
                ir = read_manual_ir(output / "manual.ir.json")
                fragments = render_document_fragments(ir, package_root=output)
            self.assertEqual(2, len(fragments))
            self.assertTrue(all("hb-operation-copy-flow" in f for f in fragments))
            self.assertEqual(1, fragments[0].count("Default standby time"))
            self.assertEqual(1, fragments[1].count("Standard-Standby-Zeit"))
            coverage = build_web_figure_coverage(ir, fragments)
            self.assertEqual({lang: layout["art_sha256"] for lang, layout in layouts.items()},
                             {s["locale"]: s["asset"]["sha256"] for s in coverage["slots"] if s["slot_id"] == SLOT})
            enforce_required_web_figure_coverage(ir, coverage)


if __name__ == "__main__":
    unittest.main()
