"""Chapter order, event ownership and precise PDF media consumption."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import unittest

from tools.frozen_ai_flow import flow_text, paragraph
from tools.frozen_ai_source import FrozenBook
from tools.frozen_pdf_document import _SECTIONS, _body_prose, _reference_nodes, ordered_pages
from tools.manual_ir.flow import validate_flow_node
from tools.web_composite_presentation import supports_figure_contract


def _block(text, y, x=30):
    return {"bbox": [x, y, x + 20, y + 8], "text": text}


def _book():
    numbers = {section: index * 10 + 1 for index, section in enumerate(_SECTIONS)}
    pages = [{"physical_page": numbers[section], "blocks_visual_order": [
        _block(f"Chapter {section}", 40), _block(f"Prose {section}", 55),
    ]} for section in _SECTIONS]
    for page in pages:
        if page["physical_page"] in {numbers["in_the_box"], numbers["product_overview"]}:
            page["blocks_visual_order"] += [_block("MEDIA_COPY_REPLACED", 90, 100), _block("Side copy retained", 90, 20)]
        if page["physical_page"] == numbers["operations"]:
            page["blocks_visual_order"] += [_block("PANEL_COPY_REPLACED", 70, 100), _block("Adjacent warning retained", 70, 20),
                                           _block("SOURCE_TABLE_REPLACED", 110, 100), _block("Same-height side copy retained", 110, 20)]
    source = {
        "source_sha256": "a" * 64, "pages": pages,
        "sections": [{"id": key, "physical_pages": [number]} for key, number in numbers.items()],
        "tables": {
            "specifications": {"physical_page": numbers["specifications"], "groups": {
                "general": [{"label": "Product", "value": "Live PDF product"}],
                "inputs": [{"label": "Input", "value": "10 V"}],
                "outputs": [{"label": "Output", "value": "12 V"}],
                "temperature": [{"label": "Temperature", "value": "20 C"}],
            }},
            "troubleshooting": {"physical_page": numbers["troubleshooting"],
                                "rows": [{"code": "F0", "action": "Fresh PDF fix"}]},
        },
    }
    book = SimpleNamespace(
        language="nl", target={"model": "JE-1000F", "region": "EU"}, source=source,
        locale={"label": "nl", "titles": [f"Chapter {s}" for s in _SECTIONS]},
        index={"section_ids": list(_SECTIONS)}, figures=[], icon_refs=["assets/a.png", "assets/b.png"],
        front_back={"locales": {"nl": {"preface": {"text": "NL\nFresh PDF preface"},
                                            "toc_shared_page": {"text": "PRINT CONTENTS NEVER IMPORT"}}},
                    "shared": {"eu_declaration": {"blocks_visual_order": [_block("Live declaration", 20)]}}},
        records={
            "symbols": {"physical_page": numbers["symbols"], "pictogram_page": numbers["in_the_box"],
                        "pictograms": [{"meaning": "First symbol", "meaning_bbox": [72, 44, 182, 75]},
                                       {"meaning": "Second symbol", "meaning_bbox": [225, 44, 340, 75]}]},
            "operation_tables": {part: {"physical_page": numbers["operations"], "source_region": [80, y, 160, y + 30]}
                                 for part, y in (("lcd_mode", 100), ("restore", 200), ("shortcuts", 300))},
        },
    )
    book.starts = lambda: [(numbers[s], 40, s) for s in _SECTIONS]
    book.special = lambda section: [paragraph(f"Complete {section}")] if section in {"symbols", "lcd_display", "app_setup", "warranty"} else []
    book.media_section = lambda section: [paragraph(f"Governed {section}")] if section in {"in_the_box", "product_overview"} else None
    book.consumed_media_regions = lambda: [{"section": section, "physical_page": numbers[section], "consume_bbox": [80, 80, 160, 120]}
                                           for section in ("in_the_box", "product_overview")]
    book.operation_panels = lambda: [{"physical_page": numbers["operations"], "y": 65,
                                     "consume_bbox": [80, 65, 160, 95], "node": paragraph("Governed operation panel")}]
    book.operation = lambda part: [paragraph(f"Structured {part}")]
    book.callouts = lambda blocks, page: ({}, set())
    book.correct = lambda value: value.replace("Prose safety", "Corrected safety")
    book.headers = lambda kind: ["General", "Inputs", "Outputs", "Temperature"] if kind == "specifications" else ["Label", "Meaning"]
    book.footnotes = lambda: [paragraph("Live specification note")]
    book.figure = lambda figure: paragraph(f"Textless reference {figure['slug']}")
    return book


class FrozenPDFDocumentTests(unittest.TestCase):
    def test_explicit_notice_regions_join_split_native_body_blocks(self):
        book = object.__new__(FrozenBook)
        book.language = "pl"
        book.correct = lambda value: value
        book.records = {"symbols": {"rows": [{"label": name} for name in
                                           ("OSTRZEŻENIE", "PRZESTROGA", "Uwaga", "WSKAZÓWKA")]}}
        book.target_layout = {"callout_regions": [{
            "physical_page": 173, "label_bbox": [25, 190, 100, 202],
            "body_bboxes": [[110, 170, 350, 181], [110, 181, 350, 225]],
        }]}
        blocks = [_block("First warning sentence.", 173, 120),
                  _block("Second warning sentence.", 182, 120),
                  _block("PRZESTROGA", 191, 30)]
        notices, consumed = book.callouts(blocks, 173)
        self.assertEqual({0, 1, 2}, consumed)
        self.assertEqual(1, len(notices))
        body = next(slot["content"] for slot in notices[0]["component_spec"]["slots"]
                    if slot["role"] == "body")
        self.assertEqual(1, body.count("First warning sentence."))
        self.assertEqual(1, body.count("Second warning sentence."))

    def test_reference_overview_uses_native_view_caption_before_figure(self):
        book = _book()
        book.target_layout = {"media": {"overview": {"presentation": "reference-figures"}}}
        book.records["media"] = {"overview": {"views": {"front": {"caption": "Widok z przodu"}}}}
        figure = {"section_id": "product_overview", "slug": "overview_front_view"}
        nodes = _reference_nodes(book, figure)
        self.assertEqual(["Widok z przodu", "Textless reference overview_front_view"],
                         [flow_text(value) for value in nodes])
        self.assertEqual("heading", nodes[0]["kind"])
        self.assertEqual(3, nodes[0]["level"])
        book.records["media"]["overview"]["views"]["front"]["caption"] = " "
        with self.assertRaisesRegex(ValueError, "native Overview view caption is empty"):
            _reference_nodes(book, figure)

    def test_native_heading_splits_only_recorded_merged_source_block(self):
        book = _book()
        charging_number = next(number for number, _, section in book.starts() if section == "charging")
        charging_page = next(page for page in book.source["pages"]
                             if page["physical_page"] == charging_number)
        merged = {"bbox": [28, 316, 338, 351],
                  "text": "CHARGING VIA CAR OUTLET\nConnect the cable to the car outlet."}
        charging_page["blocks_visual_order"].append(merged)
        book.records["native_body_headings"] = {"rows": [{
            "section_id": "charging", "physical_page": charging_number,
            "block_bbox": merged["bbox"], "heading": "CHARGING VIA CAR OUTLET", "level": 3,
        }]}
        _, pages = ordered_pages(book)
        charging = next(page for page in pages if page.page_id == "charging")
        texts = [flow_text(block) for _, block in charging.blocks]
        self.assertEqual(1, texts.count("CHARGING VIA CAR OUTLET"))
        self.assertEqual(1, texts.count("Connect the cable to the car outlet."))
        book.records["native_body_headings"]["rows"][0]["heading"] = "Changed heading"
        with self.assertRaisesRegex(ValueError, "native heading no longer starts"):
            ordered_pages(book)


    def test_emergency_charging_lead_is_bold_without_changing_body_copy(self):
        labels = {"uk": "Режим аварійного заряджання", "pt": "Modo de carregamento de emergência",
                  "nl": "Noodoplaadmodus", "pl": "Tryb ładowania awaryjnego"}
        for language, label in labels.items():
            for suffix in ("", " Native body & source caution."):
                with self.subTest(language=language, suffix=suffix):
                    nodes = _body_prose(label + suffix, "charging", language)
                    self.assertEqual("strong", nodes[0]["children"][0]["kind"])
                    self.assertEqual(label + suffix, " ".join(flow_text(n) for n in nodes))
                    self.assertEqual("text", _body_prose(label, "operations", language)[0]["children"][0]["kind"])

    def test_complete_order_no_contents_and_exact_media_consumption(self):
        book = _book()
        before = deepcopy(book.source)
        title, pages = ordered_pages(book)
        self.assertEqual("Live PDF product — nl", title)
        self.assertEqual(["introduction", *_SECTIONS, "eu-declaration"], [p.page_id for p in pages])
        text = " ".join(flow_text(block[1]) for page in pages for block in page.blocks)
        self.assertNotIn("Contents", text)
        self.assertNotIn("PRINT CONTENTS", text)
        self.assertNotIn("COPY_REPLACED", text)
        self.assertNotIn("SOURCE_TABLE_REPLACED", text)
        self.assertEqual(2, text.count("Side copy retained"))
        self.assertIn("Adjacent warning retained", text)
        self.assertIn("Same-height side copy retained", text)
        self.assertIn("Corrected safety", text)
        for part in ("lcd_mode", "restore", "shortcuts"):
            self.assertEqual(1, text.count(f"Structured {part}"))
        operation = next(page for page in pages if page.page_id == "operations")
        self.assertTrue(supports_figure_contract(Path(operation.source_path), {"figure_targets": [book.target]}))
        self.assertTrue(all(page.source_sha256 == "a" * 64 for page in pages))
        for page in pages:
            for _, block in page.blocks:
                self.assertEqual([], validate_flow_node(block))
        self.assertEqual(before, book.source)

    def test_events_without_following_blocks_and_variable_reference_inventory(self):
        book = _book()
        book.figures = [{"slug": "governed-solar", "physical_page": 71,
                         "section_id": "charging", "clip_points": [25, 450, 350, 490]}]
        # Correct physical page for the charging chapter, with no block at y450.
        book.figures[0]["physical_page"] = book.starts()[7][0]
        _, pages = ordered_pages(book)
        charging = next(p for p in pages if p.page_id == "charging")
        self.assertIn("Textless reference governed-solar", " ".join(flow_text(b[1]) for b in charging.blocks))

    def test_incomplete_or_wrong_chapter_events_fail_closed(self):
        book = _book()
        book.source["pages"][0]["blocks_visual_order"][0]["text"] = "Wrong source heading"
        with self.assertRaisesRegex(ValueError, "chapter heading coverage"):
            ordered_pages(book)
        book = _book()
        book.operation_panels = lambda: [{"physical_page": 1, "y": 70, "consume_bbox": [80, 65, 160, 95],
                                         "node": paragraph("Wrong chapter panel")}]
        with self.assertRaisesRegex(ValueError, "outside chapter"):
            ordered_pages(book)
        book = _book()
        del book.records["operation_tables"]["shortcuts"]
        with self.assertRaisesRegex(ValueError, "operation table recipe"):
            ordered_pages(book)
        book = _book()
        book.special = lambda section: []
        with self.assertRaisesRegex(ValueError, "no structured body"):
            ordered_pages(book)

    def test_printer_marks_before_first_heading_do_not_become_prose(self):
        book = _book()
        book.source["pages"][0]["blocks_visual_order"].insert(0, _block("86 +", 5))
        _, pages = ordered_pages(book)
        self.assertEqual(15, len(pages))


if __name__ == "__main__":
    unittest.main()
