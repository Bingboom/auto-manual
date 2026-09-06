from __future__ import annotations

from pathlib import Path
import shutil
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from bs4 import BeautifulSoup

from tools.component_specs.app import (
    APP_COMPONENT_ID,
    app_add_device_component_spec,
    app_download_component_spec,
    app_inline_control_component_spec,
)
from tools.component_specs.app_adapters import (
    idml_app_payload,
    latex_app_projection,
    web_app_projection,
    word_app_projection,
)
from tools.component_specs.projection import project_manual_ir_components
from tools.component_specs.reference_figure import (
    REFERENCE_FIGURE_COMPONENT_ID,
    reference_figure_component_spec,
)
from tools.component_specs.reference_figure_adapters import (
    idml_reference_figure_payload,
    latex_reference_figure_projection,
    web_reference_figure_projection,
    word_reference_figure_projection,
)
from tools.component_specs.registry import load_component_registry
from tools.component_specs.theme import load_manual_theme
from tools.manual_ir import read_manual_ir
from tools.web_composite_manifest import load_web_composite_manifest
from tools.web_document_ir import render_document_fragments
from tools.web_document_source import load_web_document
from tools.web_presentation import load_web_manual_contract
from tools.word_bundle_html import _build_word_only_tags


ROOT = Path(__file__).resolve().parents[1]


def _eu_app_page(language: str) -> tuple[str, tuple[str, ...]]:
    localized = {
        "de": {
            "download": (
                'Suchen Sie nach "Jackery", um die App zu installieren.',
                "Scannen Sie alternativ den QR-Code, um die App herunterzuladen.",
            ),
            "inline": "2.1 Klicken Sie auf die Schaltfläche **+**, um Ihr Gerät hinzuzufügen.",
            "labels": (
                "Haupt-POWER-Taste",
                "AC-Einschalttaste",
                "DC / USB-Einschalttaste",
            ),
        },
        "it": {
            "download": (
                'Cerca "Jackery" per installare l\'app.',
                "In alternativa, scansiona il codice QR per scaricare l'app.",
            ),
            "inline": "2.1 Fai clic sul pulsante **+** per aggiungere il dispositivo.",
            "labels": (
                "Pulsante POWER principale",
                "Pulsante CA",
                "Pulsante di alimentazione DC / USB",
            ),
        },
    }[language]
    assets = ROOT / "docs/templates/word_template/common_assets/app"
    labels = tuple(str(value) for value in localized["labels"])
    page = f"""APP SETUP
=========

1. Download
-----------

.. image:: {assets / "download.png"}
   :alt: App download

{localized["download"][0]}

{localized["download"][1]}

2. Add device
-------------

{localized["inline"]}

2.2 Follow the localized setup instructions.

.. image:: {assets / "add_device.png"}
   :alt: App add device

| {labels[0]}
| {labels[1]}
| {labels[2]}

2.3 Continue in the App.

.. image:: {assets / "connect_result.png"}
   :alt: App setup result
"""
    return page, labels


class AppReferenceComponentSpecTests(unittest.TestCase):
    def test_registered_variants_have_four_renderer_projections(self) -> None:
        registry = load_component_registry()
        theme = load_manual_theme(component_registry=registry)
        download = app_download_component_spec(
            accessibility_label="Download the App",
            columns=(
                {"role": "store", "html": "Install <strong>Jackery</strong>", "text": "Install Jackery"},
                {"role": "qr", "html": "Scan the QR code", "text": "Scan the QR code"},
            ),
            source_art_ref="download.png",
            store_art_ref="store.png",
            qr_art_ref="qr.png",
            source_ref="app.rst#download",
            language="en",
            registry=registry,
            theme=theme,
        )
        inline = app_inline_control_component_spec(
            accessibility_label="Add device",
            paragraph_html='<p>2.1 Click <strong>Add device</strong> button.</p>',
            paragraph_text="2.1 Click Add device button.",
            source_ref="app.rst#inline-add-device",
            language="en",
            registry=registry,
            theme=theme,
        )
        add_device = app_add_device_component_spec(
            accessibility_label="Add-device steps",
            reference_id="app-add-device",
            labels=(
                {"role": "main-power", "html": "POWER", "text": "POWER"},
                {"role": "dc-usb", "html": "DC / USB", "text": "DC / USB"},
                {"role": "ac-power", "html": "AC", "text": "AC"},
            ),
            source_art_ref="source.png",
            phone_art_ref="phones.png",
            control_art_ref="controls.png",
            source_ref="app.rst#app-add-device",
            language="en",
            registry=registry,
            theme=theme,
        )
        self.assertEqual(
            {"download", "inline-control", "add-device"},
            {download.variant, inline.variant, add_device.variant},
        )
        for spec in (download, inline, add_device):
            with self.subTest(variant=spec.variant):
                self.assertEqual(APP_COMPONENT_ID, spec.component_id)
                self.assertEqual(spec.variant, web_app_projection(spec)["variant"])
                self.assertTrue(latex_app_projection(spec)["adapter"])
                self.assertTrue(idml_app_payload(spec)["kind"])
                self.assertTrue(word_app_projection(spec)["editable"])

        reference = reference_figure_component_spec(
            reference_id="charging-car",
            accessibility_label="Car charging",
            caption_mode="live",
            captions=(
                {"html": "Vehicle", "text": "Vehicle"},
                {"html": "Cable sold separately", "text": "Cable sold separately"},
            ),
            adjacent_copy=None,
            source_art_ref="car.png",
            source_art_locale_policy="exact",
            source_fragment_sha256="a" * 64,
            source_ref="charging.rst#charging-car",
            language="en",
            image_key="charging/car_charge",
            web_replace_key="reference.charging-car",
            approved_composite={
                "asset_key": "web-composite/reference.charging-car",
                "asset_ref": "car_en.png",
                "locale": "en",
                "content_sha256": "b" * 64,
                "source_fragment_sha256": "a" * 64,
            },
            registry=registry,
            theme=theme,
        )
        self.assertEqual(REFERENCE_FIGURE_COMPONENT_ID, reference.component_id)
        self.assertEqual("approved-composite", reference.variant)
        self.assertEqual("exact", reference.assets[0].locale_policy)
        self.assertEqual("exact", reference.assets[1].locale_policy)
        self.assertEqual(
            "reference.charging-car",
            web_reference_figure_projection(reference)["web_replace_key"],
        )
        self.assertTrue(latex_reference_figure_projection(reference)["image"])
        self.assertEqual("referencefigure", idml_reference_figure_payload(reference)["kind"])
        self.assertTrue(word_reference_figure_projection(reference)["editable"])

    def test_real_us_cold_replay_uses_embedded_app_and_reference_components(self) -> None:
        app_source = ROOT / "docs/_review/JE-1000F/US/page/12_app_setup_placeholder.rst"
        charging_overview_source = ROOT / "docs/_review/JE-1000F/US/page/charging.rst"
        charging_source = ROOT / "docs/_review/JE-1000F/US/page/08_charging_methods.rst"
        app_assets = ROOT / "docs/templates/word_template/common_assets/app"
        charging_assets = ROOT / "docs/templates/word_template/common_assets/charging"
        replacements = {
            "asset:app/download": app_assets / "download.png",
            "asset:app/add_device": app_assets / "add_device.png",
            "asset:app/connect_result": app_assets / "connect_result.png",
            "asset:charging/ac_wall": charging_assets / "ac_wall.png",
            "asset:charging/solar_direct": charging_assets / "solar_direct.png",
            "asset:charging/solar_adapter": charging_assets / "solar_adapter.png",
            "asset:charging/car_charge": charging_assets / "car_charge.png",
        }
        manifest = load_web_composite_manifest(
            ROOT / "tests/fixtures/phase2/web_composite_manifest.json"
        )
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            page_dir = root / "docs/_build/JE-1000F/US/en/page"
            page_dir.mkdir(parents=True)
            pages = []
            for source in (app_source, charging_overview_source, charging_source):
                target = page_dir / source.name
                text = source.read_text(encoding="utf-8")
                for logical, physical in replacements.items():
                    text = text.replace(logical, str(physical))
                target.write_text(text, encoding="utf-8")
                pages.append(target)
            package = root / "package"
            materialized = SimpleNamespace(
                model="JE-1000F",
                region="US",
                lang="en",
                languages=("en",),
                bundle_dir=page_dir.parent,
                title="App/reference replay",
            )
            ir = load_web_document(
                materialized,
                page_paths=tuple(pages),
                declarations={},
                page_languages={page.name: "en" for page in pages},
                active_tags=_build_word_only_tags(
                    model="JE-1000F", region="US", lang="en"
                ),
                output_dir=package,
                composite_manifest=manifest,
            )
            specs = project_manual_ir_components(ir)
            self.assertEqual(3, sum(spec.component_id == APP_COMPONENT_ID for spec in specs))
            self.assertEqual(
                5,
                sum(spec.component_id == REFERENCE_FIGURE_COMPONENT_ID for spec in specs),
            )
            selected = [
                spec
                for spec in specs
                if spec.component_id == REFERENCE_FIGURE_COMPONENT_ID
                and spec.variant == "approved-composite"
            ]
            self.assertEqual(
                {"charging-car", "app-connect-result"},
                {str(spec.slot("reference_id").content) for spec in selected},
            )
            for spec in specs:
                for asset in spec.assets:
                    self.assertIn(asset.asset_ref, ir.metadata["asset_sha256"])

            shutil.rmtree(page_dir)
            source_projector_error = AssertionError(
                "legacy App/reference source projector called during replay"
            )
            with (
                patch(
                    "tools.manual_ir.whole_document_components.parse_app_download_html",
                    side_effect=source_projector_error,
                ),
                patch(
                    "tools.manual_ir.whole_document_components.parse_app_inline_control_html",
                    side_effect=source_projector_error,
                ),
                patch(
                    "tools.manual_ir.whole_document_components.parse_app_add_device_html",
                    side_effect=source_projector_error,
                ),
                patch(
                    "tools.manual_ir.whole_document_components.parse_reference_figure_html",
                    side_effect=source_projector_error,
                ),
                patch(
                    "tools.web_presentation.transform_app_download",
                    side_effect=source_projector_error,
                ),
                patch(
                    "tools.web_presentation.transform_app_control",
                    side_effect=source_projector_error,
                ),
                patch(
                    "tools.web_presentation._transform_reference_figures",
                    side_effect=source_projector_error,
                ),
            ):
                replayed = render_document_fragments(
                    read_manual_ir(package / "manual.ir.json"),
                    package_root=package,
                )
            soup = BeautifulSoup("".join(replayed), "html.parser")
            self.assertEqual(1, len(soup.select("figure.hb-app-download-composition")))
            self.assertEqual(1, len(soup.select(".hb-inline-add-device-icon")))
            self.assertEqual(1, len(soup.select("figure.hb-app-add-device-composition")))
            self.assertEqual(5, len(soup.select("figure.hb-reference-figure")))
            self.assertEqual(
                2,
                len(soup.select("figure.hb-reference-figure.hb-has-composite-art")),
            )
            expected_hashes = {
                entry.web_replace_key: entry.source_fragment_sha256
                for entry in manifest.entries
                if entry.locale in {"en", "shared"}
                and entry.web_replace_key
                in {"reference.charging-car", "reference.app-connect-result"}
            }
            self.assertEqual(
                expected_hashes,
                {
                    str(figure["data-web-replace-key"]): str(
                        figure["data-source-fragment-sha256"]
                    )
                    for figure in soup.select(
                        "figure.hb-reference-figure.hb-has-composite-art"
                    )
                },
            )

    def test_reference_component_records_shared_and_exact_locale_without_fallback(self) -> None:
        contract = load_web_manual_contract()
        app_connect = next(
            item
            for item in contract["reference_figures"]["figures"]
            if item["id"] == "app-connect-result"
        )
        charging_car = next(
            item
            for item in contract["reference_figures"]["figures"]
            if item["id"] == "charging-car"
        )
        self.assertEqual("shared", app_connect["composite_locale"])
        self.assertNotEqual("shared", charging_car.get("composite_locale"))

    def test_eu_de_it_app_components_cold_replay_keep_localized_copy(self) -> None:
        source_names = {
            "de": "p61_12_app_setup_placeholder.rst",
            "it": "p76_12_app_setup_placeholder.rst",
        }
        for language, source_name in source_names.items():
            with self.subTest(language=language), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                page_dir = root / f"docs/_build/JE-1000F/EU/{language}/page"
                page_dir.mkdir(parents=True)
                page_path = page_dir / source_name
                page, expected_labels = _eu_app_page(language)
                page_path.write_text(page, encoding="utf-8")
                package = root / "package"
                materialized = SimpleNamespace(
                    model="JE-1000F",
                    region="EU",
                    lang=language,
                    languages=(language,),
                    bundle_dir=page_dir.parent,
                    title=f"EU {language} App replay",
                )
                ir = load_web_document(
                    materialized,
                    page_paths=(page_path,),
                    declarations={},
                    page_languages={source_name: language},
                    active_tags=_build_word_only_tags(
                        model="JE-1000F", region="EU", lang=language
                    ),
                    output_dir=package,
                    composite_manifest=None,
                )
                specs = project_manual_ir_components(ir)
                self.assertEqual(
                    ["download", "inline-control", "add-device"],
                    [
                        spec.variant
                        for spec in specs
                        if spec.component_id == APP_COMPONENT_ID
                    ],
                )
                self.assertEqual({language}, {spec.language for spec in specs})
                add_device = next(
                    spec
                    for spec in specs
                    if spec.component_id == APP_COMPONENT_ID
                    and spec.variant == "add-device"
                )
                self.assertEqual(
                    list(expected_labels),
                    [item["text"] for item in add_device.slot("labels").content],
                )
                reference = next(
                    spec
                    for spec in specs
                    if spec.component_id == REFERENCE_FIGURE_COMPONENT_ID
                )
                self.assertEqual("semantic-fallback", reference.variant)

                shutil.rmtree(page_dir)
                replayed = render_document_fragments(
                    read_manual_ir(package / "manual.ir.json"),
                    package_root=package,
                )
                soup = BeautifulSoup("".join(replayed), "html.parser")
                self.assertEqual(
                    list(expected_labels),
                    [
                        label.get_text(" ", strip=True)
                        for label in soup.select(".hb-app-add-device-live-label")
                    ],
                )
                self.assertEqual(1, len(soup.select("figure.hb-reference-figure")))
                self.assertEqual([], soup.select("figure.hb-has-composite-art"))
                self.assertEqual([], soup.select(".hb-composite-stage"))


if __name__ == "__main__":
    unittest.main()
