from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import re
from types import SimpleNamespace
import unittest

from bs4 import BeautifulSoup

from tools.frozen_pdf_app import APP_ASSET_KEYS, app_section
from tools.manual_ir.components import component_specs_in_flow
from tools.manual_ir.flow import flow_nodes_to_html, validate_flow_node
from tools.web_embedded_components import render_embedded_web_component


PDF = Path("/private/tmp/je1000f-nine-language-intake/HTE153-nine-language-native-text-check.pdf")
ROOT = Path(__file__).resolve().parents[1]
RECIPE = ROOT / "manual_sources/JE-1000F/EU/nine-language/git-20260927-c38415f5/four-language"


def _fixture():
    copy = {
        "title": "APP INSTELLEN", "download_heading": "1. Download de app en log in",
        "download_store": 'Zoek naar \\\"Jackery\\\" in Google Play of de App Store.',
        "download_qr": "Of scan de QR-code om de app te installeren.",
        "add_heading": "2. Apparaat toevoegen", "step_2_1": "2.1 Klik op de      -knop om toe te voegen;",
        "step_2_2": "2.2 Druk op de aan/uit-knop en geef Bluetooth-machtigingen.",
        "step_2_3": "2.3 De app maakt verbinding via Bluetooth.",
        "bound_note_label": "OPMERKING", "bound_note_body": "Als het apparaat gebonden is:\n• Deel het apparaat.\n• Reset wifi en Bluetooth.",
        "step_2_4": "2.4 Voer het wifi-wachtwoord in.",
        "wifi_note_label": "OPMERKING", "wifi_note_body": "Selecteer 2,4 GHz; 5 GHz wordt niet ondersteund.",
        "step_2_5": "2.5 Het wifi-pictogram blijft aan.", "screenshots_note": "De schermafbeeldingen zijn alleen ter referentie.",
        "bluetooth_caution_label": "OPGELET", "bluetooth_caution_body": "Bluetooth kan één powerstation tegelijk verbinden.",
        "unbind": "3. Apparaat ontkoppelen\nOpen instellingen en tik op Ontkoppelen.",
        "notes_heading": "4. Opmerkingen", "enable": "4.1 Inschakelen:\n• Wifi wordt ingeschakeld.\n• Houd DC/USB en AC ingedrukt.",
        "disable": "4.2 Uitschakelen\n• Houd beide knoppen ingedrukt totdat de pictogrammen uitgaan.",
        "reset": "4.3 Resetten\n• Houd POWER en DC/USB 3 seconden ingedrukt.",
    }
    labels = [
        {"bbox": [51, 411, 90, 418], "text": "Aan/Uit-knop"},
        {"bbox": [59, 426, 113, 434], "text": "Aan/uit-knop voor"},
        {"bbox": [87, 435, 111, 443], "text": "DC/USB"},
        {"bbox": [278, 429, 318, 445], "text": "Aan/uit-knop\nvoor DC"},
        {"bbox": [128, 380, 234, 387], "text": "2.1\n2.2"},
    ]
    blocks = {
        key: {"raw_text": value, "text": " ".join(value.split()), "physical_page": 142}
        for key, value in copy.items()
    }
    for key in ("step_2_4", "step_2_5", "screenshots_note"):
        blocks[key]["physical_page"] = 143
    return SimpleNamespace(
        language="nl", records={"app_sections": {"blocks": blocks}},
        source={"pages": [
            {"physical_page": 142, "blocks_visual_order": labels},
            {"physical_page": 143, "blocks_visual_order": [
                {"bbox": [80, 281, 283, 288], "text": "2.5\n2.3\n2.4"},
            ]},
        ]},
        correct=lambda value: "Aan/uit-knop voor AC" if value == "Aan/uit-knop voor DC" else value,
    )


def _render(book, nodes):
    return BeautifulSoup(flow_nodes_to_html(nodes, component_renderer=lambda value:
        render_embedded_web_component(value, source_path=Path("app.rst"), model="JE-1000F",
                                      region="EU", language=book.language,
                                      composite_manifest=None, contract={})), "html.parser")


class FrozenPDFAppTests(unittest.TestCase):
    def setUp(self):
        self.book = _fixture()
        self.assets = {key: f"assets/{key}.png" for key in APP_ASSET_KEYS}

    def test_three_public_app_variants_and_notices_render_once(self):
        original = deepcopy(self.book.records)
        nodes = app_section(self.book, self.assets)
        self.assertEqual(original, self.book.records)
        for value in nodes:
            self.assertEqual([], validate_flow_node(value))
        specs = component_specs_in_flow(nodes)
        self.assertEqual(["download", "inline-control", "add-device"],
                         [spec.variant for spec in specs if spec.component_id == "HB-SPECIAL-APP"])
        soup = _render(self.book, nodes)
        self.assertEqual(1, len(soup.select(".hb-app-download-composition")))
        self.assertEqual(1, len(soup.select(".hb-app-add-device-composition")))
        self.assertEqual(3, len(soup.select(".manual-callout-table")))
        self.assertEqual("+", soup.select_one(".hb-inline-add-device-icon").text)
        self.assertEqual("Aan/uit-knop voor AC", soup.select_one(".hb-app-add-device-live-label-ac-power").text)
        self.assertFalse(soup.find(["h1", "h2"]))
        self.assertEqual(4, len(soup.find_all("h3")))
        self.assertEqual(3, len(soup.find_all("h4")))
        self.assertEqual(self.assets["app.qr"], soup.select_one(".hb-app-download-art-qr")["src"])
        self.assertEqual(self.assets["app.store"], soup.select_one(".hb-app-download-art-store")["src"])
        self.assertEqual(self.assets["app.phone"], soup.select_one(".hb-app-add-device-phone-art")["src"])
        self.assertEqual(self.assets["app.control"], soup.select_one(".hb-app-add-device-control-art")["src"])
        self.assertEqual(1, len(soup.find_all("img", src=self.assets["app.result"])))
        self.assertEqual("live", soup.select_one(".hb-app-add-device-composition")["data-step-captions"])
        self.assertEqual(
            ["2.1", "2.2"],
            [span.text for span in soup.select(".hb-app-add-device-composition .hb-reference-caption")],
        )
        self.assertEqual(
            ["2.3", "2.4", "2.5"],
            [span.text for span in soup.select('[data-reference-id="app-connect-result"] .hb-reference-caption')],
        )
        result_figure = soup.select_one('[data-reference-id="app-connect-result"]')
        self.assertEqual("figcaption", result_figure.find_all(recursive=False)[-1].name)
        self.assertIsNotNone(result_figure.figcaption.find_previous_sibling().find("img"))
        visible = soup.get_text(" ", strip=True)
        self.assertNotIn('\\"', visible)
        for key, block in self.book.records["app_sections"]["blocks"].items():
            if key == "title" or key.endswith("_label"):
                continue
            raw = block["raw_text"]
            if key == "step_2_1":
                raw = re.sub(r"\s{5,}", " + ", raw)
            expected = re.sub(r'\\+"', '"', " ".join(raw.replace("•", " ").split()))
            self.assertEqual(1, visible.count(expected), key)

    def test_merged_native_control_columns_are_split_by_source_lines(self):
        self.book.source["pages"][0]["blocks_visual_order"] = [
            {"bbox": [42, 411, 90, 418], "text": "Przycisk zasilania"},
            {"bbox": [41, 428, 335, 437], "text": "Przycisk zasilania DC/USB\nPrzycisk zasilania AC\n"},
            {"bbox": [128, 380, 234, 387], "text": "2.1\n2.2"},
        ]
        soup = _render(self.book, app_section(self.book, self.assets))
        self.assertEqual("Przycisk zasilania DC/USB", soup.select_one(".hb-app-add-device-live-label-dc-usb").text)
        self.assertEqual("Przycisk zasilania AC", soup.select_one(".hb-app-add-device-live-label-ac-power").text)

    def test_four_native_app_controls_keep_distinct_roles_and_source_positions(self):
        labels = [
            ("main-power", "POWER", [40, 410, 90, 425]),
            ("dc-usb", "DC/USB", [90, 430, 145, 445]),
            ("ac-power-1", "AC1", [190, 430, 230, 445]),
            ("ac-power-2", "AC2", [260, 430, 300, 445]),
        ]
        self.book.records["app_control_labels"] = {"rows": [
            {"role": role, "text": label, "physical_page": 142, "bbox": bbox}
            for role, label, bbox in labels
        ]}
        self.book.assets = {"app.control": {"clip_points": [25, 400, 345, 455]}}
        nodes = app_section(self.book, self.assets)
        spec = next(spec for spec in component_specs_in_flow(nodes)
                    if spec.component_id == "HB-SPECIAL-APP" and spec.variant == "add-device")
        self.assertEqual([role for role, _, _ in labels],
                         [item["role"] for item in spec.slot("labels").content])
        positions = spec.metadata["control_label_positions"]
        self.assertEqual(set(positions), {role for role, _, _ in labels})
        self.assertLess(positions["ac-power-1"][1], positions["ac-power-2"][1])
        soup = _render(self.book, nodes)
        self.assertEqual([label for _, label, _ in labels],
                         [item.get_text(strip=True) for item in soup.select(".hb-app-add-device-live-label")])

    def test_missing_assets_or_ambiguous_source_fail_without_guessing(self):
        del self.assets["app.qr"]
        with self.assertRaises(KeyError):
            app_section(self.book, self.assets)
        self.assets["app.qr"] = "assets/qr.png"
        self.book.records["app_sections"]["blocks"]["step_2_1"]["raw_text"] = "No vector gap"
        with self.assertRaisesRegex(ValueError, "vector-control gap is ambiguous"):
            app_section(self.book, self.assets)

    def test_missing_native_step_numbers_fail_closed(self):
        self.book.source["pages"][1]["blocks_visual_order"] = []
        with self.assertRaisesRegex(ValueError, "expected one native number block"):
            app_section(self.book, self.assets)

    def test_explicit_caption_only_step_keeps_unnumbered_prose_and_requires_caption(self):
        record = self.book.records["app_sections"]["blocks"]["step_2_5"]
        record["raw_text"] = "Het wifi-pictogram blijft aan."
        with self.assertRaisesRegex(ValueError, "does not start with 2.5"):
            app_section(self.book, self.assets)
        self.book.target_layout = {"app": {"caption_only_steps": ["2.5"]}}
        soup = _render(self.book, app_section(self.book, self.assets))
        self.assertIn(record["raw_text"], soup.get_text())
        self.assertNotIn("2.5 Het wifi", soup.get_text())
        record["raw_text"] = "2.6 Conflicting source number."
        with self.assertRaisesRegex(ValueError, "does not start with 2.5"):
            app_section(self.book, self.assets)
        record["raw_text"] = "Het wifi-pictogram blijft aan."
        self.book.source["pages"][1]["blocks_visual_order"] = []
        with self.assertRaisesRegex(ValueError, "expected one native number block"):
            app_section(self.book, self.assets)

    @unittest.skipUnless(PDF.is_file(), "native intake PDF is not available")
    def test_complete_fresh_pdf_app_copy_survives_public_replay_in_four_languages(self):
        from tools.frozen_pdf_intake import load_pdf_book

        for language in ("uk", "pt", "nl", "pl"):
            with self.subTest(language=language):
                data = load_pdf_book(PDF, language, RECIPE)
                book = SimpleNamespace(**data, language=language)
                soup = _render(book, app_section(book, self.assets))
                visible = " ".join(soup.get_text(" ", strip=True).split())
                for key, block in book.records["app_sections"]["blocks"].items():
                    if key == "title" or key.endswith("_label"):
                        continue
                    raw = block["raw_text"]
                    if key == "step_2_1":
                        raw = re.sub(r"\s{5,}", " + ", raw)
                    expected = re.sub(r'\\+"', '"', " ".join(raw.replace("•", " ").split()))
                    self.assertEqual(1, visible.count(expected), key)
                self.assertEqual(3, len(soup.select(".hb-app-add-device-live-label")))
                self.assertEqual(
                    ["2.1", "2.2"],
                    [span.text for span in soup.select(".hb-app-add-device-composition .hb-reference-caption")],
                )
                self.assertEqual(
                    ["2.3", "2.4", "2.5"],
                    [span.text for span in soup.select('[data-reference-id="app-connect-result"] .hb-reference-caption')],
                )


if __name__ == "__main__":
    unittest.main()
