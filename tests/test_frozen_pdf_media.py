from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import unittest

from bs4 import BeautifulSoup

from tools.component_specs.overview_instance import resolve_overview_instance
from tools.frozen_pdf_media import (
    MEDIA_ASSET_KEYS, consumed_media_regions, media_section, operation_panels,
)
from tools.manual_ir.flow import validate_flow_node
from tools.web.embedded_components import render_embedded_web_component
from tools.web.presentation import load_web_manual_contract


PDF = Path("/private/tmp/je1000f-nine-language-intake/HTE153-nine-language-native-text-check.pdf")


def _block(x, y, value):
    return {"bbox": [x, y, x + 10, y + 10], "text": value}


def _fixture_book():
    inbox = [_block(35, 241, "WAT ZIT ER IN DE DOOS"), _block(60, 394, "Jackery\nExplorer 1000"),
             _block(162, 399, "AC-oplaadkabel"), _block(260, 399, "Gebruikershandleiding"),
             _block(48, 459, "TIPS\nKabel is apart verkrijgbaar.")]
    overview = [
        _block(34, 31, "PRODUCTOVERZICHT"), _block(40, 68, "VOORAANZICHT"),
        _block(40, 316, "RECHTERZIJAANZICHT"),
        _block(30, 105, "Aan/Uit-knop"), _block(326, 105, "LCD"),
        _block(30, 129, "DC 12 V-poort"), _block(30, 139, "12 V\x1f10 A Max"),
        _block(292, 128, "LED-lampknop"), _block(309, 157, "LED-lamp"),
        _block(30, 157, "USB-C 30W-uitgang"), _block(30, 167, "30 W Max, 20 V\x1f1,5 A"),
        _block(30, 183, "USB-C 100W-uitgang"), _block(30, 193, "100 W Max, 20 V\x1f5 A"),
        _block(268, 176, "Aan/uit-knop voor DC"),
        _block(30, 222, "USB-A 18W-uitgang"), _block(30, 232, "18 W Max, 9-12 V\x1f1,5 A"),
        _block(304, 204, "AC-uitgang"), _block(282, 215, "230 V~ 50 Hz, 6,5 A max., 1500 W Nominaal"),
        _block(30, 267, "Aan/uit-knop voor DC/USB"),
        _block(255, 259, "Totaal uitgangsvermogen"), _block(245, 270, "1500 W nominaal, 3000 W piekvermogen"),
        _block(33, 339, "Handvat"), _block(33, 355, "DC-ingang\n(2×DC8020-poorten)"),
        _block(34, 374, "PV: 16-60 V\x1f12A max, verdubbeld naar 21A / 400W max\nAuto: 11-16 V\x1f8A max, verdubbeld naar 16A max"),
        _block(303, 381, "AC-ingang"), _block(274, 390, "220-240 V~ 50 Hz, 10 A max."),
    ]
    operations = [
        _block(36, 57, "IN-/UITSCHAKELEN"),
        _block(262, 79, "Aan"), _block(262, 92, "Druk één keer"),
        _block(262, 105, "Uit"), _block(262, 117, "Houd 3 seconden ingedrukt."),
        _block(275, 129, "3s"),
        _block(152, 147, "Standaard stand-bymodustijd: 2 uur\nHet product wordt na 2 uur inactiviteit automatisch\nuitgeschakeld.\n*De stand-bymodustijd kan worden ingesteld in de Jackery-app."),
        _block(26, 209, "Outside main panel: retain all prose."),
        _block(36, 259, "AAN/UIT VOOR AC-UITGANG"),
        _block(34, 284, "Voorwaarde: Het product is ingeschakeld."),
        _block(285, 326, "Aan"), _block(285, 337, "Druk één keer"),
        _block(284, 349, "Uit"), _block(284, 361, "Druk één keer"),
    ]
    dc = [_block(45, 29, "DC/USB-UITGANG AAN/UIT"),
          _block(44, 53, "Voorwaarde: Het product is ingeschakeld."),
          _block(299, 77, "Aan"), _block(299, 86, "Druk één keer"),
          _block(299, 97, "Uit"), _block(299, 108, "Druk één keer"),
          _block(94, 247, "Outside DC panel: USB-C 100W safety warning."),
          _block(31, 401, "Outside energy panel: energy-saving explanation.")]
    led = [_block(287, 82, "AC"),
           _block(228, 116, "3s\nHoud beide knoppen langer\ndan 3 seconden ingedrukt.\nAan/Uit"),
           _block(44, 218, "De LED-lamp heeft twee modi: Lichtmodus en SOS-modus."),
           _block(44, 228, "Houd de knop ingedrukt om het licht uit te schakelen."),
           _block(216, 269, "1"), _block(253, 264, "Druk één keer om het licht in te schakelen."),
           _block(156, 287, "LAMP"), _block(216, 293, "2\nSOS"),
           _block(253, 290, "Druk nogmaals voor SOS."),
           _block(216, 318, "3"), _block(253, 315, "Druk een derde keer om het licht uit te schakelen."),
           _block(41, 354, "Outside panel: LCD table heading")]
    pages = [{"physical_page": number, "blocks_visual_order": blocks}
             for number, blocks in ((128, inbox), (129, overview), (132, operations), (133, dc), (134, led))]
    return _book("nl", 127, pages)


def _book(language, start, pages):
    return SimpleNamespace(
        language=language, source={"pages": pages, "sections": [
            {"id": key, "physical_pages": [start + offset]}
            for key, offset in (("in_the_box", 1), ("product_overview", 2), ("operations", 5))]},
        overview_instance=resolve_overview_instance(model="JE-1000F", region="EU"),
        contract=load_web_manual_contract(model="JE-1000F", region="EU"),
    )


def _render(book, node, *, region="EU"):
    return BeautifulSoup(render_embedded_web_component(
        node, source_path=Path(f"docs/_review/JE-1000F/{region}/page/05_operation_guide_placeholder.rst"),
        model="JE-1000F", region=region, language=book.language, composite_manifest=None,
        contract=book.contract, overview_instance=book.overview_instance,
    ), "html.parser")


class FrozenPDFMediaTests(unittest.TestCase):
    def setUp(self):
        self.book = _fixture_book()
        self.assets = {key: f"assets/{key}.png" for key in MEDIA_ASSET_KEYS}

    def test_inbox_is_three_live_cards_with_one_tip(self):
        node = media_section(self.book, "in_the_box", self.assets)[0]
        self.assertEqual([], validate_flow_node(node))
        soup = _render(self.book, node)
        self.assertEqual(3, len(soup.select(".hb-inbox-card")))
        self.assertEqual(1, len(soup.select(".hb-inbox-tip")))
        self.assertEqual([self.assets[f"inbox.{key}"] for key in ("main", "cable", "manual")],
                         [image["src"] for image in soup.select("img")])
        self.assertEqual("Jackery Explorer 1000 AC-oplaadkabel Gebruikershandleiding TIPS Kabel is apart verkrijgbaar.",
                         soup.get_text(" ", strip=True))
        self.assertFalse(soup.find("table"))

    def test_overview_retains_pdf_specs_and_approved_label_correction(self):
        self.book.correct = lambda value: value.replace("Aan/uit-knop voor DC", "Aan/uit-knop voor AC") if value == "Aan/uit-knop voor DC" else value
        original = deepcopy(self.book.source)
        node = media_section(self.book, "product_overview", self.assets)[0]
        self.assertEqual([], validate_flow_node(node))
        soup = _render(self.book, node)
        self.assertEqual(2, len(soup.select(".hb-annotated-figure")))
        self.assertEqual(15, len(soup.select(".hb-figure-callout")))
        self.assertEqual("Aan/uit-knop voor AC", soup.select_one('[data-callout-id="overview.front.ac_power"].hb-figure-callout').get_text(" ", strip=True))
        self.assertIn("21A / 400W max", soup.get_text())
        self.assertIn("verdubbeld naar 16A max", soup.get_text())
        self.assertIn("12 V⎓10 A Max", soup.get_text())
        self.assertEqual(original, self.book.source)
        self.assertFalse(soup.find("table"))

    def test_finished_panel_heading_visibility_is_per_view(self):
        for embedded in (False, True):
            with self.subTest(captions_embedded=embedded):
                self.book.overview_finished_panels = {
                    "front": {"captions_embedded": embedded},
                    "right": {"captions_embedded": not embedded},
                }
                payload = media_section(self.book, "product_overview", self.assets)[0]
                soup = _render(self.book, payload)
                headings = soup.select("h2")
                self.assertEqual(2, len(headings))
                self.assertEqual([embedded, not embedded],
                                 [h.has_attr("hidden") for h in headings])
                self.assertTrue(all(h.get_text(strip=True) for h in headings))
                self.assertEqual(15, len(soup.select(".hb-figure-callout")))

    def test_operations_replay_five_real_components_and_leave_body_regions(self):
        events = operation_panels(self.book, self.assets)
        self.assertEqual(5, len(events))
        for event in events:
            self.assertEqual([], validate_flow_node(event["node"]))
            soup = _render(self.book, event["node"])
            figure = soup.select_one(".hb-operation-figure")
            self.assertIsNotNone(figure)
            self.assertEqual("HB-SPECIAL-OPERATION", figure["data-component-id"])
        main = _render(self.book, events[0]["node"])
        self.assertEqual(3, len(main.select(".hb-operation-supporting-copy .line")))
        self.assertIn("2 uur", main.get_text())
        for page in self.book.source["pages"]:
            for block in page["blocks_visual_order"]:
                if block["text"].startswith("Outside"):
                    self.assertFalse(any(event["physical_page"] == page["physical_page"]
                        and event["consume_bbox"][0] <= block["bbox"][0] < event["consume_bbox"][2]
                        and event["consume_bbox"][1] <= block["bbox"][1] < event["consume_bbox"][3]
                        for event in events))
        self.assertEqual(7, len(consumed_media_regions(self.book)))

    def test_registered_base_art_layout_renders_source_mode_and_sos_labels(self):
        # Exercise the existing public base-art consumer with its declared US
        # geometry; choosing compatible production artwork remains the caller's job.
        self.book.contract = load_web_manual_contract(model="JE-1000F", region="US")
        events = operation_panels(self.book, self.assets)
        energy = _render(self.book, events[3]["node"], region="US")
        led = _render(self.book, events[4]["node"], region="US")
        self.assertEqual("Aan/Uit", energy.select_one(".hb-operation-mode-label").text)
        self.assertEqual("SOS", led.select_one(".hb-operation-marker-sos").text)
        self.assertEqual("AC", energy.select_one(".hb-operation-step-label").text)
        self.assertEqual("LAMP", led.select_one(".hb-operation-step-label").text)

    def test_missing_pdf_slot_or_asset_fails_closed(self):
        del self.assets["overview.front"]
        with self.assertRaises(KeyError):
            media_section(self.book, "product_overview", self.assets)
        self.book.source["pages"][0]["blocks_visual_order"] = []
        with self.assertRaisesRegex(ValueError, "has no text"):
            media_section(self.book, "in_the_box", self.assets)
        self.assertIsNone(media_section(self.book, "warranty", {}))

    @unittest.skipUnless(PDF.is_file(), "native intake PDF is not available")
    def test_four_languages_reextract_native_pdf_and_render_public_components(self):
        import fitz

        with fitz.open(PDF) as document:
            for language, start in (("uk", 93), ("pt", 110), ("nl", 127), ("pl", 144)):
                with self.subTest(language=language):
                    pages = [{"physical_page": number, "blocks_visual_order": [
                        {"bbox": list(block[:4]), "text": block[4]}
                        for block in document[number - 1].get_text("blocks", sort=True)]}
                        for number in (start + 1, start + 2, start + 5, start + 6, start + 7)]
                    book = _book(language, start, pages)
                    for section in ("in_the_box", "product_overview"):
                        soup = _render(book, media_section(book, section, self.assets)[0])
                        self.assertTrue(soup.find("figure"))
                    # The shared base-art consumer must expose source labels
                    # in every locale, including captions previously baked into art.
                    book.contract = load_web_manual_contract(model="JE-1000F", region="US")
                    events = operation_panels(book, self.assets)
                    for event in events:
                        soup = _render(book, event["node"], region="US")
                        self.assertIsNotNone(soup.select_one(".hb-operation-figure"))
                    energy = _render(book, events[3]["node"], region="US")
                    led = _render(book, events[4]["node"], region="US")
                    modes = {"uk": "Увімкнення/вимкнення", "pt": "Ligar/Desligar",
                             "nl": "Aan/Uit", "pl": "Wł./wył."}
                    ac = {"uk": "Змінний струм", "pt": "CA", "nl": "AC", "pl": "AC"}
                    light = {"uk": "СВІТЛО", "pt": "LUZ", "nl": "LAMP", "pl": "ŚWIATŁO"}
                    self.assertEqual(modes[language], energy.select_one(".hb-operation-mode-label").text)
                    self.assertEqual(ac[language], energy.select_one(".hb-operation-step-label").text)
                    self.assertEqual(light[language], led.select_one(".hb-operation-step-label").text)
                    self.assertEqual("SOS", led.select_one(".hb-operation-marker-sos").text)


if __name__ == "__main__":
    unittest.main()
