from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import unittest

from tools.idml.control_labels import (
    approved_app_control_labels,
    extract_overview_control_labels,
    matches_base_label_block,
    validate_app_control_label_contract,
)
from tools.manual_ir import ManualBlock, ManualIR, ManualPage


BASE_LABELS = {
    "en": {
        "main_power": "POWER Button",
        "dc_usb": "DC / USB Power Button",
        "ac": "AC Power Button",
    },
    "fr": {
        "main_power": "Bouton d'alimentation",
        "dc_usb": "Bouton d’alimentation CC / USB",
        "ac": "Bouton Power CA",
    },
    "es": {
        "main_power": "Botón de encendido",
        "dc_usb": "Botón de energía CC / USB",
        "ac": "Botón Power CA",
    },
}
RENDER_LABELS = {
    "en": {
        "main_power": "Main Power Button",
        "dc_usb": "DC/USB Power Button",
        "ac": "AC Power Button",
    },
    "fr": {
        "main_power": "Bouton POWER",
        "dc_usb": "Bouton d’alimentation CC/USB",
        "ac": "Bouton d’alimentation CA",
    },
    "es": {
        "main_power": "Botón de encendido principal",
        "dc_usb": "Botón de energía CC/USB",
        "ac": "Botón de energía CA",
    },
}


def _block(kind: str, payload: object, index: int) -> ManualBlock:
    return ManualBlock(
        block_id=f"block-{index}",
        source_ref=f"page/source.rst#block-{index}",
        kind=kind,
        payload=payload,
        content_sha256=str(index) * 64,
    )


def _overview_page(language: str, *, ordinal: int) -> ManualPage:
    labels = BASE_LABELS[language]
    table = [
        [f"**{labels['main_power']}**", "**LCD**"],
        ["**Port**", "**LED**"],
        [f"**{labels['dc_usb']}**", "**Light**"],
        ["**Output**", f"**{labels['ac']}**"],
    ]
    prefix = "" if language == "en" else f"p{24 if language == 'fr' else 40}_"
    name = f"{prefix}03_product_overview_placeholder.rst"
    return ManualPage(
        page_id=f"overview-{language}-{ordinal}",
        source_ref=f"page/{name}",
        source_path=f"page/{name}",
        language=language,
        source_sha256=str(ordinal) * 64,
        skipped_raw=0,
        blocks=(
            _block("h1", f"overview-{language}", ordinal),
            _block("table", table, ordinal + 3),
        ),
    )


def _app_page() -> ManualPage:
    return ManualPage(
        page_id="app-en",
        source_ref="page/12_app_setup_placeholder.rst",
        source_path="page/12_app_setup_placeholder.rst",
        language="en",
        source_sha256="9" * 64,
        skipped_raw=0,
        blocks=(_block("image", "app/add_device_je1000f_us.png", 9),),
    )


def _manual_ir(pages: tuple[ManualPage, ...] | None = None) -> ManualIR:
    return ManualIR(
        model="JE-1000F",
        region="US",
        language="en",
        source="test",
        bundle_root=".",
        bundle_sha256="0" * 64,
        snapshot_sha256="1" * 64,
        layout_params_sha256="2" * 64,
        style_contract_sha256="3" * 64,
        content_sha256="4" * 64,
        pages=pages or (
            _overview_page("en", ordinal=1),
            _overview_page("fr", ordinal=2),
            _overview_page("es", ordinal=3),
            _app_page(),
        ),
    )


def _idml_contract() -> dict[str, object]:
    return {
        "forbidden_visible_whole_page_links": ["flattened.pdf"],
        "editable_components": {
            "app_add_device": {
                "control_labels": {
                    language: {
                        "base_labels_by_role": deepcopy(BASE_LABELS[language]),
                        "render_labels_by_role": deepcopy(RENDER_LABELS[language]),
                    }
                    for language in ("en", "fr", "es")
                },
            },
        },
    }


class ControlLabelContractTests(unittest.TestCase):
    def test_extracts_three_languages_from_fixed_overview_slots(self) -> None:
        self.assertEqual(
            BASE_LABELS,
            extract_overview_control_labels(_manual_ir(), ("en", "fr", "es")),
        )

    def test_missing_duplicate_page_and_duplicate_language_fail_closed(self) -> None:
        ir = _manual_ir()
        cases = (
            (
                replace(ir, pages=tuple(
                    page for page in ir.pages if page.language != "fr"
                )),
                ("en", "fr", "es"),
                "exactly one Product Overview page for fr; found 0",
            ),
            (
                replace(ir, pages=ir.pages + (_overview_page("en", ordinal=7),)),
                ("en", "fr", "es"),
                "exactly one Product Overview page for en; found 2",
            ),
            (ir, ("en", "en"), "languages must be unique"),
        )
        for candidate, languages, message in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(ValueError, message):
                    extract_overview_control_labels(candidate, languages)

    def test_malformed_overview_table_slots_fail_closed(self) -> None:
        ir = _manual_ir()
        en = ir.pages[0]
        table = deepcopy(en.blocks[1].payload)
        malformed = []
        malformed.append((replace(en, blocks=(en.blocks[0],)), "requires a first table"))

        short = deepcopy(table)
        short.pop()
        malformed.append((
            replace(en, blocks=(en.blocks[0], _block("table", short, 6))),
            "missing ac at row 3 column 1",
        ))
        empty = deepcopy(table)
        empty[2][0] = "** **"
        malformed.append((
            replace(en, blocks=(en.blocks[0], _block("table", empty, 7))),
            "dc_usb slot must start with one non-empty bold label",
        ))
        duplicate = deepcopy(table)
        duplicate[2][0] = duplicate[0][0]
        malformed.append((
            replace(en, blocks=(en.blocks[0], _block("table", duplicate, 8))),
            "control labels must be unique across roles",
        ))

        for overview, message in malformed:
            with self.subTest(message=message):
                candidate = replace(ir, pages=(overview,) + ir.pages[1:])
                with self.assertRaisesRegex(ValueError, message):
                    extract_overview_control_labels(
                        candidate,
                        ("en", "fr", "es"),
                    )

    def test_contract_rejects_language_role_and_base_drift(self) -> None:
        ir = _manual_ir()
        valid = _idml_contract()
        self.assertEqual(
            [],
            validate_app_control_label_contract(valid, ir, ["en", "fr", "es"]),
        )

        cases = []
        missing_language = deepcopy(valid)
        del missing_language["editable_components"]["app_add_device"][
            "control_labels"
        ]["fr"]
        cases.append((missing_language, "missing languages: fr"))

        extra_language = deepcopy(valid)
        extra_language["editable_components"]["app_add_device"][
            "control_labels"
        ]["de"] = deepcopy(extra_language["editable_components"][
            "app_add_device"
        ]["control_labels"]["en"])
        cases.append((extra_language, "unexpected languages: de"))

        missing_role = deepcopy(valid)
        del missing_role["editable_components"]["app_add_device"][
            "control_labels"
        ]["en"]["render_labels_by_role"]["ac"]
        cases.append((missing_role, "missing roles: ac"))

        base_drift = deepcopy(valid)
        base_drift["editable_components"]["app_add_device"][
            "control_labels"
        ]["es"]["base_labels_by_role"]["main_power"] = "wrong"
        cases.append((base_drift, "does not match the Product Overview source slot"))

        for contract, message in cases:
            with self.subTest(message=message):
                issues = validate_app_control_label_contract(
                    contract,
                    ir,
                    ["en", "fr", "es"],
                )
                self.assertTrue(any(message in issue for issue in issues), issues)

    def test_runtime_uses_render_variants_and_only_exact_base_set_deduplicates(self) -> None:
        page_plan = {"approved_contract": {"idml_contract": _idml_contract()}}
        base, render = approved_app_control_labels(page_plan, "en-US")

        self.assertEqual(BASE_LABELS["en"], base)
        self.assertEqual(RENDER_LABELS["en"], render)
        self.assertTrue(matches_base_label_block(
            "AC Power Button\nPOWER Button\nDC / USB Power Button",
            base,
        ))
        self.assertFalse(matches_base_label_block(
            "POWER Button\nDC / USB Power Button\nNot the AC label",
            base,
        ))
        self.assertFalse(matches_base_label_block(
            "2.3 Tras hacer clic en el icono del dispositivo buscado",
            BASE_LABELS["es"],
        ))


if __name__ == "__main__":
    unittest.main()
