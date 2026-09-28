from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import urlparse, unquote

from bs4 import BeautifulSoup

from tests.test_web_presentation_contract import _write_layered_contract
from tools.manual_ir import read_manual_ir, write_manual_ir
from tools.web_document_ir import render_document_fragments
from tools.web_document_source import load_web_document
from tools.web_figure_coverage import attach_web_figure_coverage
from tools.web_finished_overview import (
    bind_finished_images, find_finished_operation_images,
    find_finished_reference_images, find_source_images,
    finished_overview_views,
)
from tools.web_presentation import (
    WebPresentationError, load_web_manual_contract, transform_web_fragment,
)


VIEWS = [
    {"id": "front", "image_key": "overview/front_product",
     "source_image": "front_product.jpg", "web_replace_key": "product-overview.front"},
    {"id": "right", "image_key": "overview/right_side_ports",
     "source_image": "right_side_ports.png", "web_replace_key": "product-overview.right"},
]


def _overlay() -> dict:
    return {
        "overlay_id": "finished-overview-pilot",
        "target": {"model": "MODEL", "region": "EU"},
        "skeleton_profile": "test-skeleton",
        "capabilities": {"figures": True, "legacy_target_components": False},
        "contract_overrides": {"product_overview": {
            "presentation_mode": "finished-panel", "finished_views": deepcopy(VIEWS),
        }},
        "figure_coverage": {
            "policy_id": "finished-overview-pilot", "locales": ["en", "de"],
            "required_slots": ["product-overview.front", "product-overview.right"],
            "allowed_statuses": ["finished-panel", "approved-composite"],
        },
    }


def _contract(overlay: dict | None = None) -> dict:
    with tempfile.TemporaryDirectory() as td:
        entry = _write_layered_contract(Path(td), overlays=[overlay or _overlay()])
        return load_web_manual_contract(entry, model="MODEL", region="EU")


class FinishedOverviewTests(unittest.TestCase):
    def test_contract_derives_two_slots_and_rejects_invalid_opt_in(self):
        contract = _contract()
        req = contract["figure_coverage"]["requirements"][0]
        self.assertEqual(["product-overview.front", "product-overview.right"], req["required_slots"])
        for bad in (
            {"presentation_mode": "other"},
            {"finished_views": deepcopy(VIEWS)},
            {"presentation_mode": "finished-panel", "finished_views": []},
            {"presentation_mode": "finished-panel", "finished_views": [VIEWS[0], VIEWS[0]]},
            {"presentation_mode": "finished-panel", "finished_views": [
                {**VIEWS[0], "id": []}, VIEWS[1]]},
            {"presentation_mode": "finished-panel", "finished_views": [
                {**VIEWS[0], "web_replace_key": "product-overview.wrong"}, VIEWS[1]]},
            {"presentation_mode": "finished-panel", "finished_views": [
                {**VIEWS[0], "source_image": "../front_product.jpg"}, VIEWS[1]]},
        ):
            with self.subTest(bad=bad), self.assertRaises(WebPresentationError):
                _contract({**_overlay(), "contract_overrides": {"product_overview": bad}})
        with self.assertRaisesRegex(WebPresentationError, "requires figures=true"):
            overlay = _overlay()
            overlay["capabilities"]["figures"] = False
            _contract(overlay)
        full_contract = deepcopy(load_web_manual_contract(model="JE-1000F", region="EU"))
        full_contract["product_overview"].update({
            "presentation_mode": "finished-panel", "finished_views": deepcopy(VIEWS),
        })
        with self.assertRaisesRegex(WebPresentationError, "requires frozen Web illustration assembly"):
            transform_web_fragment(
                '<section><img src="assets/overview/front_product.jpg"></section>',
                source_path=Path("docs/_build/JE-1000F/EU/en/page/03_product_overview_placeholder.rst"),
                contract=full_contract, model="JE-1000F", region="EU", language="en",
            )

    def test_exact_source_and_manifest_binding_rejects_missing_or_duplicate(self):
        html = ('<section id="front-view"><img src="assets/overview/front_product.jpg"></section>'
                '<section id="right-side-view"><img src="assets/overview/right_side_ports.png"></section>')
        views = finished_overview_views({
            **_overlay()["contract_overrides"]["product_overview"],
            "source_patterns": ["*03_product_overview_placeholder"],
        })
        soup = BeautifulSoup(html, "html.parser")
        images = find_source_images(soup, views, source_path="overview.rst")
        for view, image in images.items():
            image["data-web-finished-panel-path"] = f"{view}.png"
            image["data-web-finished-panel-sha256"] = "a" * 64
            image["alt"] = "copy"
        entries = {("en", v["source_image"]): {
            "path": f"{view}.png", "sha256": "a" * 64,
            "replaces": [v["source_image"]], "covered_annotations": [{"text": "copy"}],
        } for view, v in views.items()}
        bind_finished_images(soup, images, views, entries, language="en", source_path="overview.rst")
        self.assertEqual(2, len(soup.select("figure[data-web-replace-key]")))
        for changed in (html.replace('front_product.jpg', 'other.jpg'),
                        html.replace('</section>', '<img src="assets/overview/front_product.jpg"></section>', 1)):
            with self.assertRaisesRegex(ValueError, "one source image|source image disagrees"):
                find_source_images(BeautifulSoup(changed, "html.parser"), views, source_path="overview.rst")
        with self.assertRaisesRegex(ValueError, "lacks approved artwork"):
            bind_finished_images(BeautifulSoup(html, "html.parser"),
                find_source_images(BeautifulSoup(html, "html.parser"), views, source_path="overview.rst"),
                views, {}, language="en", source_path="overview.rst")
        for changed in (
            {**entries, ("en", VIEWS[0]["source_image"]): {
                **entries[("en", VIEWS[0]["source_image"])], "sha256": "b" * 64,
            }},
            {**entries, ("en", VIEWS[0]["source_image"]): {
                **entries[("en", VIEWS[0]["source_image"])], "replaces": ["wrong.jpg"],
            }},
        ):
            with self.assertRaisesRegex(ValueError, "lacks approved artwork"):
                bind_finished_images(soup, images, views, changed,
                    language="en", source_path="overview.rst")

    def test_two_language_package_replays_only_verified_finished_art(self):
        contract = deepcopy(load_web_manual_contract(model="JE-1000F", region="EU"))
        contract["product_overview"].update({
            "presentation_mode": "finished-panel", "finished_views": deepcopy(VIEWS),
        })
        contract["figure_targets"] = [{"model": "MODEL", "region": "EU"}]
        contract["figure_coverage"]["requirements"] = [{
            "target": {"model": "MODEL", "region": "EU"},
            "locales": ["en", "de"],
            "required_slots": ["product-overview.front", "product-overview.right"],
            "allowed_statuses": ["finished-panel", "approved-composite"],
        }]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pages = []
            manifests = {}
            hashes = {}
            for language in ("en", "de"):
                page_dir = root / "docs" / "_build" / "MODEL" / "EU" / language / "page"
                page_dir.mkdir(parents=True)
                page = page_dir / ("03_product_overview_placeholder.rst" if language == "en"
                                   else "p42_03_product_overview_placeholder.rst")
                page.write_text('''.. raw:: html

   <section><h1>Overview</h1><section id="front-view"><h2>Front</h2><img src="assets/overview/front_product.jpg"><table><tr><td>Front source copy</td></tr></table></section><section id="right-side-view"><h2>Right</h2><img src="assets/overview/right_side_ports.png"><table><tr><td>Right source copy</td></tr></table></section></section>
''')
                pages.append(page)
                asset_dir = root / language
                asset_dir.mkdir()
                entries = []
                for view in VIEWS:
                    art = asset_dir / f"{view['id']}.png"
                    art.write_bytes((language + view["id"]).encode())
                    digest = hashlib.sha256(art.read_bytes()).hexdigest()
                    hashes[(language, view["id"])] = digest
                    entries.append({"path": art.name, "replaces": [view["source_image"]],
                                    "sha256": digest, "covered_annotations": [{
                                        "selector": f"#{view['id'] if view['id'] == 'front' else 'right-side'}-view > table",
                                        "text": f"{view['id'].title()} source copy",
                                    }]})
                manifest = asset_dir / "illustrations.json"
                manifest.write_text(json.dumps({"schema_version": "web-illustrations/v1",
                    "model": "MODEL", "region": "EU", "language": language,
                    "illustrations": entries}))
                manifests[language] = manifest
            materialized = SimpleNamespace(model="MODEL", region="EU", lang="", languages=("en", "de"),
                                           bundle_dir=root, title="Fixture")
            output = root / "package"
            with patch("tools.web_document_source.load_web_manual_contract", return_value=contract):
                load_web_document(materialized, page_paths=pages, declarations={},
                    page_languages={p.name: lang for p, lang in zip(pages, ("en", "de"), strict=True)},
                    active_tags=set(), output_dir=output, composite_manifest=None,
                    illustration_manifests=manifests)
            assembled = read_manual_ir(output / "manual.ir.json")
            assembled = attach_web_figure_coverage(
                assembled, render_document_fragments(assembled, package_root=output),
            )
            write_manual_ir(assembled, output / "manual.ir.json")
            raw = json.loads((output / "manual.ir.json").read_text())
            self.assertNotIn("overview_instance", raw["metadata"])
            self.assertNotIn("HB-SPECIAL-OVERVIEW", json.dumps(raw["pages"]))
            self.assertEqual(4, len(raw["metadata"]["web_figure_coverage"]["slots"]))
            self.assertEqual(
                {"finished-panel"},
                {slot["status"] for slot in raw["metadata"]["web_figure_coverage"]["slots"]},
            )
            for page in pages:
                page.unlink()
            with patch("tools.web_presentation.load_web_manual_contract", side_effect=AssertionError("live read")):
                fragments = render_document_fragments(read_manual_ir(output / "manual.ir.json"), package_root=output)
            self.assertEqual(2, len(fragments))
            for language, fragment in zip(("en", "de"), fragments, strict=True):
                soup = BeautifulSoup(fragment, "html.parser")
                self.assertEqual(2, len(soup.select("figure[data-web-replace-key]")))
                for view in ("front", "right"):
                    image = soup.select_one(f'figure[data-web-replace-key="product-overview.{view}"] img')
                    self.assertEqual(hashes[(language, view)], hashlib.sha256(
                        Path(unquote(urlparse(image["src"]).path)).read_bytes()).hexdigest())
                    self.assertEqual(1, image["alt"].count(f"{view.title()} source copy"))
                self.assertEqual(0, len(soup.select(".hb-figure-callout, .hb-leader-layer, table")))
            frozen_path = output / "manual.ir.json"
            frozen = json.loads(frozen_path.read_text())
            for corrupt in (
                {"presentation_mode": "unrecognized", "finished_views": deepcopy(VIEWS)},
                {"presentation_mode": "finished-panel", "finished_views": [deepcopy(VIEWS[0])]},
                {"presentation_mode": "finished-panel", "finished_views": [
                    {**VIEWS[0], "web_replace_key": "product-overview.wrong"}, VIEWS[1],
                ]},
            ):
                changed = deepcopy(frozen)
                changed["metadata"]["web_contract"]["product_overview"].update(corrupt)
                frozen_path.write_text(json.dumps(changed))
                with self.subTest(corrupt=corrupt), self.assertRaisesRegex(
                    ValueError, "metadata.web_contract.product_overview",
                ):
                    read_manual_ir(frozen_path)
            frozen_path.write_text(json.dumps(frozen))
            asset = next(output.glob("assets/ir/*/front.png"))
            original = asset.read_bytes()
            asset.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "document asset missing or changed"):
                render_document_fragments(read_manual_ir(frozen_path), package_root=output)
            asset.write_bytes(original)

    def test_finished_operation_requires_manifest_and_never_consumes_flow_copy(self):
        soup = BeautifulSoup(
            '<section><img src="assets/operation/op_main_power.png"></section>',
            "html.parser",
        )
        figure = deepcopy(load_web_manual_contract(model="JE-1000F", region="EU")
                          ["operations"]["figures"][0])
        source = ("en", "op_main_power.png")
        self.assertEqual({}, find_finished_operation_images(
            soup, [figure], {}, language="en", source_path="operation.rst",
        ))
        entry = {"replaces": [source[1]], "covered_annotations": [{
            "selector": "section > div", "text": "On: Press once",
        }]}
        selected = find_finished_operation_images(
            soup, [figure], {source: entry}, language="en", source_path="operation.rst",
        )
        self.assertEqual(["operation.main-power"], list(selected))
        flow_figure = {**figure, "base_art_layout_by_locale": {
            "en": {"copy_layout": "flow", "art_sha256": "a" * 64},
        }}
        with self.assertRaisesRegex(ValueError, "still has a copy-consuming finished manifest"):
            find_finished_operation_images(
                soup, [flow_figure], {source: entry},
                language="en", source_path="operation.rst",
            )

    def test_finished_operation_consumes_copy_before_claims_and_replays_slot(self):
        contract = deepcopy(load_web_manual_contract(model="JE-1000F", region="EU"))
        target = {"model": "MODEL", "region": "EU"}
        contract["figure_targets"] = [target]
        contract["product_overview"]["source_patterns"] = []
        contract["operations"]["figures"] = contract["operations"]["figures"][:1]
        for key in ("auto_resume_table", "key_combination_table", "lcd_mode_table"):
            contract["operations"][key] = None
        contract["figure_coverage"]["requirements"] = [{
            "target": target, "locales": ["en"],
            "required_slots": ["operation.main-power"],
            "allowed_statuses": ["finished-panel", "approved-composite"],
        }]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            page = root / "docs/_build/MODEL/EU/en/page/05_operation_guide_placeholder.rst"
            page.parent.mkdir(parents=True)
            source = '''.. raw:: html

   <section id="power-on-off"><img src="assets/operation/op_main_power.png"><div class="line-block"><div class="line">On: Press once.</div><div class="line">Off: Hold for 3s.</div></div></section>
'''
            page.write_text(source)
            art = root / "finished.png"
            art.write_bytes(b"approved-finished-operation")
            manifest = root / "illustrations.json"
            manifest.write_text(json.dumps({
                "schema_version": "web-illustrations/v1",
                "model": "MODEL", "region": "EU", "language": "en",
                "illustrations": [{
                    "path": art.name, "sha256": hashlib.sha256(art.read_bytes()).hexdigest(),
                    "replaces": ["op_main_power.png"],
                    "covered_annotations": [{
                        "selector": "#power-on-off > .line-block",
                        "text": "On: Press once. Off: Hold for 3s.",
                    }],
                }],
            }))
            materialized = SimpleNamespace(
                model="MODEL", region="EU", lang="en", languages=("en",),
                bundle_dir=root, title="Finished Operation",
            )
            output = root / "package"
            with patch("tools.web_document_source.load_web_manual_contract", return_value=contract):
                ir = load_web_document(
                    materialized, page_paths=[page], declarations={},
                    page_languages={page.name: "en"}, active_tags=set(),
                    output_dir=output, composite_manifest=None,
                    illustration_manifest=manifest,
                )
            covered = attach_web_figure_coverage(
                ir, render_document_fragments(ir, package_root=output),
            )
            write_manual_ir(covered, output / "manual.ir.json")
            page.unlink()
            fragment = render_document_fragments(
                read_manual_ir(output / "manual.ir.json"), package_root=output,
            )[0]
            soup = BeautifulSoup(fragment, "html.parser")
            self.assertEqual(1, len(soup.select(
                'figure[data-web-replace-key="operation.main-power"]',
            )))
            self.assertNotIn("On: Press once.", soup.get_text(" ", strip=True))
            self.assertIn("On: Press once.", soup.select_one("figure img")["alt"])
            page.write_text(source.replace("On: Press once.", "On: Press twice."))
            with patch("tools.web_document_source.load_web_manual_contract", return_value=contract):
                with self.assertRaisesRegex(ValueError, "covered illustration annotation changed"):
                    load_web_document(
                        materialized, page_paths=[page], declarations={},
                        page_languages={page.name: "en"}, active_tags=set(),
                        output_dir=root / "bad-package", composite_manifest=None,
                        illustration_manifest=manifest,
                    )

    def test_finished_charging_selection_needs_exact_manifest(self):
        figure = next(
            entry for entry in load_web_manual_contract(model="JE-1000F", region="EU")
            ["reference_figures"]["figures"]
            if entry.get("id") == "charging-ac-wall"
        )
        soup = BeautifulSoup(
            '<section><img src="assets/charging/ac_wall.png"></section>',
            "html.parser",
        )
        self.assertEqual({}, find_finished_reference_images(
            soup, [figure], {}, language="en", source_path="charging.rst",
        ))
        entry = {"replaces": ["ac_wall.png"]}
        selected = find_finished_reference_images(
            soup, [figure], {("en", "ac_wall.png"): entry},
            language="en", source_path="charging.rst",
        )
        self.assertEqual(["reference.charging-ac-wall"], list(selected))
        with self.assertRaisesRegex(ValueError, "needs one source image"):
            find_finished_reference_images(
                BeautifulSoup(str(soup) + str(soup), "html.parser"),
                [figure], {("en", "ac_wall.png"): entry},
                language="en", source_path="charging.rst",
            )

    def test_finished_charging_consumes_adjacent_copy_before_reference_claim(self):
        contract = deepcopy(load_web_manual_contract(model="JE-1000F", region="EU"))
        target = {"model": "MODEL", "region": "EU"}
        contract["figure_targets"] = [target]
        contract["product_overview"]["source_patterns"] = []
        contract["reference_figures"]["figures"] = [
            figure for figure in contract["reference_figures"]["figures"]
            if figure.get("id") == "charging-ac-wall"
        ]
        contract["figure_coverage"]["requirements"] = [{
            "target": target, "locales": ["en"],
            "required_slots": ["reference.charging-ac-wall"],
            "allowed_statuses": ["finished-panel", "approved-composite"],
        }]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            page = root / "docs/_build/MODEL/EU/en/page/charging.rst"
            page.parent.mkdir(parents=True)
            source = '''.. raw:: html

   <section id="ac-wall"><h2>AC wall charging</h2><p>Connect the charging cable.</p><img src="assets/charging/ac_wall.png"></section>
'''
            page.write_text(source)
            art = root / "charging-finished.png"
            art.write_bytes(b"approved-charging")
            manifest = root / "illustrations.json"
            manifest.write_text(json.dumps({
                "schema_version": "web-illustrations/v1",
                "model": "MODEL", "region": "EU", "language": "en",
                "illustrations": [{
                    "path": art.name, "sha256": hashlib.sha256(art.read_bytes()).hexdigest(),
                    "replaces": ["ac_wall.png"],
                    "covered_annotations": [{
                        "selector": "#ac-wall > p", "text": "Connect the charging cable.",
                    }],
                }],
            }))
            materialized = SimpleNamespace(
                model="MODEL", region="EU", lang="en", languages=("en",),
                bundle_dir=root, title="Finished Charging",
            )
            output = root / "package"
            with patch("tools.web_document_source.load_web_manual_contract", return_value=contract):
                ir = load_web_document(
                    materialized, page_paths=[page], declarations={},
                    page_languages={page.name: "en"}, active_tags=set(),
                    output_dir=output, composite_manifest=None,
                    illustration_manifest=manifest,
                )
            covered = attach_web_figure_coverage(
                ir, render_document_fragments(ir, package_root=output),
            )
            write_manual_ir(covered, output / "manual.ir.json")
            page.unlink()
            soup = BeautifulSoup(render_document_fragments(
                read_manual_ir(output / "manual.ir.json"), package_root=output,
            )[0], "html.parser")
            self.assertEqual(1, len(soup.select(
                'figure[data-web-replace-key="reference.charging-ac-wall"]',
            )))
            self.assertNotIn("Connect the charging cable.", soup.get_text(" ", strip=True))
            self.assertIn("Connect the charging cable.", soup.select_one("figure img")["alt"])


if __name__ == "__main__":
    unittest.main()
