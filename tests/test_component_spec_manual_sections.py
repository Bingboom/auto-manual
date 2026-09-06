from __future__ import annotations

from pathlib import Path
import shutil
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from bs4 import BeautifulSoup

from tools.component_specs.lcd_mode import (
    LCD_MODE_COMPONENT_ID,
    lcd_mode_component_spec,
)
from tools.component_specs.lcd_mode_adapters import (
    idml_lcd_mode_payload,
    latex_lcd_mode_projection,
    web_lcd_mode_projection,
    word_lcd_mode_projection,
)
from tools.component_specs.operation import (
    OPERATION_COMPONENT_ID,
    operation_component_spec,
)
from tools.component_specs.operation_adapters import (
    idml_operation_payload,
    latex_operation_projection,
    web_operation_projection,
    word_operation_projection,
)
from tools.component_specs.registry import (
    load_component_registry,
    validate_component_spec,
)
from tools.component_specs.theme import load_manual_theme
from tools.component_specs.warranty import (
    WARRANTY_LEAD_COMPONENT_ID,
    WARRANTY_SECTION_COMPONENT_ID,
    WARRANTY_YEARS_COMPONENT_ID,
    warranty_lead_component_spec,
    warranty_section_component_spec,
    warranty_years_component_spec,
)
from tools.component_specs.warranty_adapters import (
    idml_warranty_payload,
    latex_warranty_projection,
    web_warranty_projection,
    word_warranty_projection,
)
from tools.manual_ir.whole_document_components import discover_registered_components
from tools.manual_ir import read_manual_ir
from tools.render_contract import load_render_contract
from tools.utils.path_utils import Paths
from tools.web_composite_manifest import load_web_composite_manifest
from tools.web_composite_presentation import WebCompositeContext
from tools.web_document_ir import render_document_fragments
from tools.web_document_source import load_web_document
from tools.web_operation_component import render_operation_component
from tools.web_presentation import WebPresentationError, load_web_manual_contract
from tools.word_bundle_html import (
    _publish_rst_fragment_to_html,
    _rewrite_word_friendly_fragment,
)
from tools.word_bundle_html_only import _build_word_only_tags


ROOT = Path(__file__).resolve().parents[1]
PATHS = Paths(root=ROOT)


def _step(step_id: str, *parts: tuple[str, str, str]) -> dict[str, object]:
    return {
        "id": step_id,
        "parts": [
            {"role": role, "html": html, "text": text}
            for role, html, text in parts
        ],
    }


class ManualSectionComponentSpecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_component_registry(PATHS.component_registry_contract)
        cls.theme = load_manual_theme(component_registry=cls.registry)

    def test_registry_theme_and_style_contract_own_all_five_ids(self) -> None:
        component_ids = {
            OPERATION_COMPONENT_ID,
            LCD_MODE_COMPONENT_ID,
            WARRANTY_LEAD_COMPONENT_ID,
            WARRANTY_SECTION_COMPONENT_ID,
            WARRANTY_YEARS_COMPONENT_ID,
        }
        self.assertTrue(component_ids.issubset(self.registry["components"]))
        themed = {
            component_id
            for projection in self.theme["component_roles"].values()
            for component_id in projection["component_ids"]
        }
        self.assertTrue(component_ids.issubset(themed))
        styles = load_render_contract(PATHS.manual_style_contract)["styles"]
        self.assertTrue(component_ids.issubset(styles))
        for component_id in component_ids:
            with self.subTest(component_id=component_id):
                definition = self.registry["components"][component_id]
                self.assertEqual(component_id, definition["style_id"])
                self.assertEqual(
                    styles[component_id]["theme_token_roles"],
                    definition["token_roles"],
                )
                self.assertEqual(
                    {"web", "latex", "idml", "word"},
                    set(definition["adapters"]),
                )

    def test_operation_four_renderer_projections_preserve_copy_and_art(self) -> None:
        spec = operation_component_spec(
            operation_id="ac-output",
            accessibility_label="AC output on/off operation.",
            layout="status-right",
            steps=(
                _step("on", ("label", "<strong>On</strong>", "On"),
                      ("instruction", "Press once", "Press once")),
                _step("off", ("label", "<strong>Off</strong>", "Off"),
                      ("instruction", "Press once", "Press once")),
            ),
            prerequisite_html="<p><strong>Prerequisite</strong>: powered on.</p>",
            supporting_copy=(),
            artwork_ref="asset:operation/ac_output",
            source_ref="page/operations.rst#ac-output",
            language="en",
            registry=self.registry,
            theme=self.theme,
        )
        self.assertEqual([], validate_component_spec(spec, self.registry))
        web = web_operation_projection(
            spec,
            {
                "id": "ac-output",
                "image_key": "operation/ac_output",
                "layout": "status-right",
                "step_ids": ["on", "off"],
                "web_replace_key": "operation.ac-output",
            },
        )
        self.assertEqual("hb-operation-figure", web["composition_class"])
        self.assertEqual("operation.ac-output", web["web_replace_key"])
        self.assertEqual("HBOperationPanel", latex_operation_projection(spec)["macro"])
        self.assertEqual(
            {
                "kind": "oppanel",
                "image": "asset:operation/ac_output",
                "prereq": "Prerequisite: powered on.",
                "rows": [("On", "Press once"), ("Off", "Press once")],
                "tail": "",
            },
            idml_operation_payload(spec),
        )
        self.assertEqual("hb-operation-word-panel", word_operation_projection(spec)["panel_class"])

    def test_operation_replay_restores_supporting_copy_before_residual_lines(self) -> None:
        spec = operation_component_spec(
            operation_id="main-power",
            accessibility_label="Fonction marche/arrêt.",
            layout="status-right",
            steps=(
                _step("on", ("summary", "Marche : appuyez une fois.", "Marche : appuyez une fois.")),
                _step("off", ("summary", "Arrêt : maintenez pendant 3 secondes.", "Arrêt : maintenez pendant 3 secondes.")),
            ),
            prerequisite_html="",
            supporting_copy=(
                "<strong>Temps de veille par défaut :</strong> 2 heures.",
                "Arrêt automatique après 2 heures.",
                "*Réglable dans l'application Jackery.",
            ),
            artwork_ref="assets/ir/op_main_power.png",
            source_ref="page/p26_05_operation_guide_placeholder.rst#operation-main-power",
            language="fr",
            registry=self.registry,
            theme=self.theme,
        )
        carrier = """
        <img src="assets/ir/op_main_power.png" alt="Fonction marche/arrêt.">
        <div class="line-block">
          <div class="line">Marche : appuyez une fois.</div>
          <div class="line">Arrêt : maintenez pendant 3 secondes.</div>
          <div class="line">Conserver cette explication après le panneau.</div>
        </div>
        """
        rendered = render_operation_component(
            spec,
            carrier,
            source_path=Path("page/p26_05_operation_guide_placeholder.rst"),
            presentation={
                "id": "main-power",
                "image_key": "operation/main_power",
                "layout": "status-right",
                "step_ids": ["on", "off"],
                "capture_following_lines": 3,
                "web_replace_key": "operation.main-power",
            },
            composites=WebCompositeContext(
                manifest=None,
                model="JE-1000F",
                region="US",
                language="fr",
                error_type=WebPresentationError,
            ),
        )
        soup = BeautifulSoup(rendered, "html.parser")
        supporting = soup.select_one(".hb-operation-supporting-copy")
        self.assertIsNotNone(supporting)
        self.assertEqual(
            3,
            len(supporting.find_all(class_="line", recursive=False)) if supporting else 0,
        )
        self.assertEqual(1, rendered.count("Temps de veille par défaut"))
        residual = soup.select_one(".line-block > .line")
        self.assertIsNotNone(residual)
        self.assertIn(
            "Conserver cette explication",
            residual.get_text(" ", strip=True) if residual else "",
        )

    def test_lcd_mode_four_renderer_projections_keep_hybrid_table(self) -> None:
        groups = (
            {
                "state_html": "Shortly On",
                "state_text": "Shortly On",
                "actions": [
                    {"action_html": action, "action_text": action,
                     "description_html": copy, "description_text": copy}
                    for action, copy in (
                        ("Turn on", "Press POWER."),
                        ("Turn off", "Press POWER."),
                        ("Auto-off", "Sleeps after 2 minutes."),
                    )
                ],
            },
            {
                "state_html": "Steady On",
                "state_text": "Steady On",
                "actions": [
                    {"action_html": action, "action_text": action,
                     "description_html": copy, "description_text": copy}
                    for action, copy in (
                        ("Turn on", "Press POWER twice."),
                        ("Turn off", "Press POWER."),
                        ("Auto-off", "Sleeps after inactivity."),
                    )
                ],
            },
        )
        spec = lcd_mode_component_spec(
            accessibility_label="LCD display mode",
            groups=groups,
            artwork_ref="asset:operation/lcd_mode",
            source_ref="page/operations.rst#lcd-mode",
            language="en",
            registry=self.registry,
            theme=self.theme,
        )
        self.assertEqual([], validate_component_spec(spec, self.registry))
        self.assertEqual("hb-lcd-mode-composition", web_lcd_mode_projection(spec)["composition_class"])
        self.assertEqual("HBLcdModeTable", latex_lcd_mode_projection(spec)["environment"])
        self.assertEqual("lcdmode", idml_lcd_mode_payload(spec)["kind"])
        self.assertEqual(2, len(idml_lcd_mode_payload(spec)["groups"]))
        self.assertTrue(word_lcd_mode_projection(spec)["editable_table"])

    def test_warranty_four_renderer_projections_preserve_badges_and_blocks(self) -> None:
        lead = warranty_lead_component_spec(
            accessibility_label="GARANZIA",
            lead_html="<p><strong>Canali autorizzati.</strong></p>",
            local_note_html="<p>Si applicano le leggi locali.</p>",
            source_ref="page/11_warranty.rst#lead",
            language="it",
            registry=self.registry,
            theme=self.theme,
        )
        section = warranty_section_component_spec(
            title="Esclusioni",
            section_index=5,
            blocks=(
                {"kind": "paragraph", "html": "<p>Non si applica a:</p>", "text": "Non si applica a:"},
                {"kind": "list", "html": "<ul><li>Uso improprio.</li></ul>", "items": ["Uso improprio."]},
            ),
            source_ref="page/11_warranty.rst#section-5",
            language="it",
            registry=self.registry,
            theme=self.theme,
        )
        years = warranty_years_component_spec(
            title="Periodo di garanzia",
            periods=(
                {"number": "3", "unit": "ANNI", "label": "Garanzia standard",
                 "body_html": "<p>36 mesi.</p>", "body_text": "36 mesi."},
                {"number": "2", "unit": "ANNI", "label": "Garanzia estesa",
                 "body_html": "<p>Registrare il prodotto.</p>", "body_text": "Registrare il prodotto."},
            ),
            source_ref="page/11_warranty.rst#years",
            language="it",
            registry=self.registry,
            theme=self.theme,
        )
        for spec in (lead, section, years):
            self.assertEqual([], validate_component_spec(spec, self.registry))
            self.assertIn("component_class", web_warranty_projection(spec))
            self.assertIn("kind", idml_warranty_payload(spec))
            self.assertIn("editable", word_warranty_projection(spec))
            self.assertTrue(latex_warranty_projection(spec))
        self.assertEqual(
            [{"kind": "warrantynote", "text": "Si applicano le leggi locali."}],
            idml_warranty_payload(lead)["following_blocks"],
        )
        self.assertEqual("warrantyyears", idml_warranty_payload(years)["kind"])
        self.assertEqual(["3", "2"], [item["number"] for item in idml_warranty_payload(years)["items"]])
        self.assertEqual(["ANNI", "ANNI"], [item["unit"] for item in idml_warranty_payload(years)["items"]])

    def test_real_eu_languages_discover_five_operations_lcd_and_warranty_badges(self) -> None:
        contract = load_web_manual_contract()
        for language, unit in (("en", "YEARS"), ("fr", "ANS"), ("es", "AÑOS"),
                               ("de", "JAHRE"), ("it", "ANNI")):
            with self.subTest(language=language):
                tags = _build_word_only_tags(model="JE-1000F", region="EU", lang=language)
                operation_path = ROOT / "docs" / "templates" / f"page_eu-{language}" / "05_operation_guide_placeholder.rst"
                operation_html = _rewrite_word_friendly_fragment(
                    _publish_rst_fragment_to_html(
                        operation_path.read_text(encoding="utf-8"),
                        operation_path,
                        active_tags=tags,
                    ),
                    lang=language,
                )
                operation_claims = discover_registered_components(
                    BeautifulSoup(operation_html, "html.parser"),
                    source_path=(
                        ROOT
                        / "docs"
                        / "_build"
                        / "JE-1000F"
                        / "EU"
                        / language
                        / "rst"
                        / "page"
                        / operation_path.name
                    ),
                    contract=contract,
                    model="JE-1000F",
                    region="EU",
                    language=language,
                )
                ids = [claim.spec.component_id for claim in operation_claims]
                self.assertEqual(5, ids.count(OPERATION_COMPONENT_ID))
                self.assertEqual(1, ids.count(LCD_MODE_COMPONENT_ID))

                warranty_path = ROOT / "docs" / "templates" / "page_shared" / language / "11_warranty.rst"
                warranty_html = _rewrite_word_friendly_fragment(
                    _publish_rst_fragment_to_html(
                        warranty_path.read_text(encoding="utf-8"),
                        warranty_path,
                        active_tags=tags,
                    ),
                    lang=language,
                )
                warranty_claims = discover_registered_components(
                    BeautifulSoup(warranty_html, "html.parser"),
                    source_path=warranty_path,
                    contract=contract,
                    model="JE-1000F",
                    region="EU",
                    language=language,
                )
                warranty_ids = [claim.spec.component_id for claim in warranty_claims]
                self.assertEqual(1, warranty_ids.count(WARRANTY_LEAD_COMPONENT_ID))
                self.assertEqual(5, warranty_ids.count(WARRANTY_SECTION_COMPONENT_ID))
                self.assertEqual(1, warranty_ids.count(WARRANTY_YEARS_COMPONENT_ID))
                years = next(
                    claim.spec for claim in warranty_claims
                    if claim.spec.component_id == WARRANTY_YEARS_COMPONENT_ID
                )
                self.assertEqual(["3", "2"], [item["number"] for item in years.slot("periods").content])
                self.assertEqual([unit, unit], [item["unit"] for item in years.slot("periods").content])

    def test_kr_skeleton_keeps_operations_as_flow_and_parses_compact_warranty_units(self) -> None:
        operation_path = (
            ROOT
            / "docs"
            / "templates"
            / "page_eu-kr"
            / "05_operation_guide_placeholder.rst"
        )
        operation_html = _rewrite_word_friendly_fragment(
            _publish_rst_fragment_to_html(
                operation_path.read_text(encoding="utf-8"),
                operation_path,
                active_tags=_build_word_only_tags(
                    model="JE-3000C", region="KR", lang="ko"
                ),
            ),
            lang="ko",
        )
        claims = discover_registered_components(
            BeautifulSoup(operation_html, "html.parser"),
            source_path=(
                ROOT
                / "docs"
                / "_build"
                / "JE-3000C"
                / "KR"
                / "ko"
                / "rst"
                / "page"
                / operation_path.name
            ),
            contract=load_web_manual_contract(),
            model="JE-3000C",
            region="KR",
            language="ko",
        )
        ids = [claim.spec.component_id for claim in claims]
        self.assertNotIn(OPERATION_COMPONENT_ID, ids)
        self.assertEqual(1, ids.count(LCD_MODE_COMPONENT_ID))

        warranty_path = (
            ROOT / "docs" / "templates" / "page_shared" / "ko" / "11_warranty.rst"
        )
        warranty_html = _rewrite_word_friendly_fragment(
            _publish_rst_fragment_to_html(
                warranty_path.read_text(encoding="utf-8"),
                warranty_path,
                active_tags=_build_word_only_tags(
                    model="JE-3000C", region="KR", lang="ko"
                ),
            ),
            lang="ko",
        )
        warranty_claims = discover_registered_components(
            BeautifulSoup(warranty_html, "html.parser"),
            source_path=(
                ROOT
                / "docs"
                / "_build"
                / "JE-3000C"
                / "KR"
                / "ko"
                / "rst"
                / "page"
                / warranty_path.name
            ),
            contract=load_web_manual_contract(),
            model="JE-3000C",
            region="KR",
            language="ko",
        )
        years = next(
            claim.spec
            for claim in warranty_claims
            if claim.spec.component_id == WARRANTY_YEARS_COMPONENT_ID
        )
        self.assertEqual(["3", "2"], [item["number"] for item in years.slot("periods").content])
        self.assertEqual(["년", "년"], [item["unit"] for item in years.slot("periods").content])

    def test_real_us_cold_replay_uses_embedded_components_and_keeps_composite_hashes(
        self,
    ) -> None:
        source_operation = (
            ROOT
            / "docs"
            / "_review"
            / "JE-1000F"
            / "US"
            / "page"
            / "05_operation_guide_placeholder.rst"
        )
        source_warranty = (
            ROOT
            / "docs"
            / "_review"
            / "JE-1000F"
            / "US"
            / "page"
            / "11_warranty.rst"
        )
        asset_root = (
            ROOT / "docs" / "templates" / "word_template" / "common_assets" / "operation"
        )
        replacements = {
            f"asset:operation/{name}": str(asset_root / f"{name}.png")
            for name in (
                "main_power",
                "ac_output",
                "dc_usb_output",
                "energy_saving",
                "led_light",
                "lcd_mode",
            )
        }
        manifest = load_web_composite_manifest(
            ROOT / "tests" / "fixtures" / "phase2" / "web_composite_manifest.json"
        )
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            page_dir = root / "docs" / "_build" / "JE-1000F" / "US" / "en" / "page"
            page_dir.mkdir(parents=True)
            operation_path = page_dir / source_operation.name
            operation_text = source_operation.read_text(encoding="utf-8")
            for logical_ref, file_path in replacements.items():
                operation_text = operation_text.replace(logical_ref, file_path)
            operation_path.write_text(operation_text, encoding="utf-8")
            warranty_path = page_dir / source_warranty.name
            warranty_path.write_text(
                source_warranty.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            output = root / "package"
            materialized = SimpleNamespace(
                model="JE-1000F",
                region="US",
                lang="en",
                languages=("en",),
                bundle_dir=page_dir.parent,
                title="JE-1000F US component replay",
            )
            load_web_document(
                materialized,
                page_paths=(operation_path, warranty_path),
                declarations={},
                page_languages={operation_path.name: "en", warranty_path.name: "en"},
                active_tags=_build_word_only_tags(
                    model="JE-1000F", region="US", lang="en"
                ),
                output_dir=output,
                composite_manifest=manifest,
            )
            shutil.rmtree(page_dir)
            source_projector_error = AssertionError(
                "source projector called during embedded replay"
            )
            with (
                patch(
                    "tools.manual_ir.whole_document_components.parse_operation_components",
                    side_effect=source_projector_error,
                ),
                patch(
                    "tools.manual_ir.whole_document_components.parse_lcd_mode_html",
                    side_effect=source_projector_error,
                ),
                patch(
                    "tools.manual_ir.whole_document_components.parse_warranty_html",
                    side_effect=source_projector_error,
                ),
                patch(
                    "tools.web_presentation._transform_lcd_mode_table",
                    side_effect=source_projector_error,
                ),
                patch(
                    "tools.web_presentation._transform_warranty",
                    side_effect=source_projector_error,
                ),
            ):
                fragments = render_document_fragments(
                    read_manual_ir(output / "manual.ir.json"),
                    package_root=output,
                )
            soup = BeautifulSoup("".join(fragments), "html.parser")
            self.assertEqual(5, len(soup.select("figure.hb-operation-figure")))
            self.assertEqual(
                5,
                len(soup.select("figure.hb-operation-figure.hb-has-composite-art")),
            )
            self.assertEqual(1, len(soup.select("figure.hb-lcd-mode-composition")))
            replayed = "".join(fragments)
            self.assertEqual(1, replayed.count("Default standby time"))
            self.assertEqual(
                1,
                replayed.count(
                    "When Energy Saving Mode is enabled, the product will "
                    "automatically shut down after 12 hours"
                ),
            )
            self.assertEqual(
                [("3", "YEARS"), ("2", "YEARS")],
                [
                    (
                        badge.get_text(" ", strip=True),
                        badge.find_next(class_="hb-warranty-years-unit").get_text(
                            " ", strip=True
                        ),
                    )
                    for badge in soup.select(".hb-warranty-year-badge")
                ],
            )
            expected_hashes = {
                entry.web_replace_key: entry.source_fragment_sha256
                for entry in manifest.entries
                if entry.web_replace_key.startswith("operation.")
                and entry.locale == "en"
            }
            actual_hashes = {
                str(figure["data-web-replace-key"]): str(
                    figure["data-source-fragment-sha256"]
                )
                for figure in soup.select("figure.hb-operation-figure")
            }
            self.assertEqual(expected_hashes, actual_hashes)


if __name__ == "__main__":
    unittest.main()
