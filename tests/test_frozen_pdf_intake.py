"""Fresh-PDF authority, geometry failures, and optional native-source acceptance."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import fitz

from tools.frozen_pdf_intake import (
    _PDFReader, _chapter_titles, _front_back, _lcd, _page_record, _preface_candidate,
    load_pdf_book, read_recipe_json,
)
from tools.manual_ir.hashing import file_sha256


ROOT = Path(__file__).resolve().parents[1]
RECIPE = ROOT / "manual_sources/JE-1000F/EU/nine-language/git-20260927-c38415f5/four-language"
PDF = Path("/private/tmp/je1000f-nine-language-intake/HTE153-nine-language-native-text-check.pdf")
PDF_SHA = "39f90f96c5825e835358a82329b8e36a40e6f9b59fccde9bb46f4ba81fe5b469"


class FreshPDFGeometryTests(unittest.TestCase):
    def test_lcd_majority_lines_exclude_adjacent_row_descenders(self):
        with fitz.open() as document:
            page = document.new_page(width=300, height=150)
            page.insert_text((30, 40), "Previous", fontsize=10)
            page.insert_text((30, 53), "Current", fontsize=10)
            page.insert_text((150, 53), "Description", fontsize=10)
            row = {"number": 2, "physical_page": 1, "label_bbox": [25, 41, 120, 57],
                   "meaning_bbox": [140, 41, 280, 57], "selection": "lines"}
            reader = _PDFReader(document)
            result = _lcd(reader, {"pages": [1], "rows": [row]})
            self.assertEqual("Current", result["rows"][0]["label"])
            self.assertEqual("pdf-line-majority-overlap", reader.spans[0]["selection"])

    def test_preface_approval_requires_matching_dated_operator_decision(self):
        approval = {"date": "2026-09-29", "instruction": "Use Jackery",
                    "scope": "JE-2000E EU NL preface"}
        candidate = {"heading": "IMPORTANT", "paragraphs": [
            {"text": "Approved copy.", "status": "operator-approved",
             "operator_decision": approval},
        ]}
        binding = {"path": "source/preface_candidates.json", "status": "operator-approved",
                   "approval": approval}
        with patch("tools.frozen_pdf_intake.read_recipe_json", return_value={"nl": candidate}):
            accepted = _preface_candidate(Path("unused"), {}, {"preface_candidate": binding}, "nl")
            self.assertEqual({"status": "operator-approved", "approval": approval,
                              "content": candidate}, accepted)
            for changed in ({"approval": None},
                            {"approval": {**approval, "scope": " "}},
                            {"approval": {**approval, "date": "undated"}}):
                with self.subTest(changed=changed), self.assertRaisesRegex(
                        ValueError, "dated operator decision"):
                    _preface_candidate(Path("unused"), {},
                                       {"preface_candidate": {**binding, **changed}}, "nl")
            with self.assertRaisesRegex(ValueError, "disagree with operator decision"):
                _preface_candidate(Path("unused"), {}, {"preface_candidate": {
                    **binding, "approval": {**approval, "scope": "Other target"}}}, "nl")

    def test_pending_preface_keeps_review_status_and_approved_preface_keeps_provenance(self):
        candidate = {"heading": "IMPORTANT", "paragraphs": [
            {"text": "Reused copy.", "status": "shared-copy-candidate"},
        ]}
        binding = {"path": "source/preface_candidates.json",
                   "status": "preview-only-pending-review"}
        with patch("tools.frozen_pdf_intake.read_recipe_json", return_value={"nl": candidate}):
            preview = _preface_candidate(Path("unused"), {}, {"preface_candidate": binding}, "nl")
        self.assertEqual("preview-only-pending-review", preview["status"])
        recipe = {"shared": {}, "locales": {"nl": {"preface": {
            "status": "missing-in-source", "physical_page": 1, "bbox": [1, 2, 3, 4]},
            "toc_page": 1}}}
        reader = type("Reader", (), {"document": [object()]})()
        with patch("tools.frozen_pdf_intake._page_record", return_value={}):
            pending = _front_back(reader, recipe, "nl", "a" * 64, preview)
            self.assertEqual("preview-only-pending-review",
                             pending["locales"]["nl"]["preface"]["status"])
            self.assertNotIn("approval", pending["locales"]["nl"]["preface"])
            approval = {"date": "2026-09-29", "instruction": "Use Jackery",
                        "scope": "JE-2000E EU NL preface"}
            approved = _front_back(reader, recipe, "nl", "a" * 64, {
                "status": "operator-approved", "content": candidate, "approval": approval})
        self.assertEqual(approval, approved["locales"]["nl"]["preface"]["approval"])
        self.assertEqual(candidate, approved["locales"]["nl"]["preface"]["candidate"])

    def test_recipe_reader_rejects_unpinned_or_changed_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "geometry.json"
            path.write_text('{"page": 1}')
            entry = {"path": path.name, "size": path.stat().st_size, "sha256": file_sha256(path)}
            manifest = {"inputs": [entry]}
            self.assertEqual({"page": 1}, read_recipe_json(root, path.name, manifest))
            path.write_text('{"page": 2}')  # Same size; only SHA catches this.
            with self.assertRaisesRegex(ValueError, "frozen recipe changed"):
                read_recipe_json(root, path.name, manifest)
            entry["sha256"] = file_sha256(path)
            entry["size"] += 1
            with self.assertRaisesRegex(ValueError, "frozen recipe changed"):
                read_recipe_json(root, path.name, manifest)
            with self.assertRaisesRegex(ValueError, "unregistered"):
                read_recipe_json(root, path.name, {"inputs": []})

    def test_positioned_fields_and_pages_come_from_saved_pdf(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "synthetic.pdf"
            with fitz.open() as document:
                page = document.new_page(width=400, height=500)
                page.insert_text((30, 50), "Fresh text & 42", fontsize=10)
                document.save(path)
            with fitz.open(path) as document:
                reader = _PDFReader(document)
                result = reader.positioned({
                    "physical_page": 1, "blocks": {"copy": {
                        "bbox": [25, 35, 200, 55], "text": "STALE", "raw_text": "STALE",
                    }},
                })
                self.assertEqual("Fresh text & 42", result["blocks"]["copy"]["text"])
                self.assertNotIn("STALE", json.dumps(result))
                self.assertIn("Fresh text & 42", _page_record(document[0])["text"])
                self.assertEqual("record/blocks/copy", reader.spans[0]["field"])

    def test_app_lines_do_not_import_adjacent_copy_and_sort_object_order(self):
        with fitz.open() as document:
            page = document.new_page(width=400, height=500)
            # Intentionally insert body before its heading in PDF object order.
            page.insert_text((30, 90), "Body belongs here.", fontsize=10)
            page.insert_text((30, 70), "4.1 Enable", fontsize=10)
            page.insert_text((30, 106), "4.2 Disable", fontsize=10)
            reader = _PDFReader(document)
            result = reader.positioned({"physical_page": 1, "bbox": [25, 55, 220, 98],
                                        "text": "OLD", "raw_text": "OLD"}, field="app_sections/enable")
            self.assertEqual("4.1 Enable Body belongs here.", result["text"])
            self.assertEqual("pdf-line-majority-overlap", reader.spans[0]["selection"])

    def test_missing_geometry_fails_instead_of_falling_back_to_old_text(self):
        with fitz.open() as document:
            document.new_page(width=400, height=500)
            reader = _PDFReader(document)
            with self.assertRaisesRegex(ValueError, "empty"):
                reader.positioned({"physical_page": 1, "bbox": [25, 30, 200, 50], "text": "old fallback"})
            with self.assertRaisesRegex(ValueError, "without source geometry"):
                reader.positioned({"physical_page": 1, "text": "old fallback"})
            with self.assertRaisesRegex(ValueError, "outside PDF"):
                reader.box(2, [25, 30, 200, 50], "missing")

    def test_chapter_titles_use_live_font_geometry_not_recipe_words(self):
        with fitz.open() as document:
            page = document.new_page(width=400, height=500)
            page.insert_text((30, 45), "FRESH CHAPTER", fontsize=12)
            page.insert_text((30, 100), "Small subtitle", fontsize=8)
            headings = _chapter_titles(document, [{"id": "safety", "physical_pages": [1]}])
            self.assertEqual("FRESH CHAPTER", headings[0]["text"])


@unittest.skipUnless(PDF.is_file(), "local exported source PDF is not present")
class NativePDFIntakeTests(unittest.TestCase):
    def test_four_locales_reimport_with_real_pdf_identity_and_no_image_extraction(self):
        with patch.object(fitz.Page, "get_pixmap", side_effect=AssertionError("image crop forbidden")):
            for language in ("uk", "pt", "nl", "pl"):
                with self.subTest(language=language):
                    book = load_pdf_book(PDF, language, RECIPE)
                    self.assertEqual(PDF_SHA, book["source"]["source_sha256"])
                    self.assertNotIn("icon_path", json.dumps(book["records"]["symbols"]))
                    self.assertNotIn("/tmp/", json.dumps(book))
                    self.assertEqual(PDF_SHA, book["front_back"]["source_sha256"])
                    self.assertTrue(all(r["source_sha256"] == PDF_SHA for r in book["records"].values()))
                    self.assertEqual(17, len(book["source"]["pages"]))
                    self.assertEqual(13, len(book["locale"]["titles"]))
                    self.assertEqual(26, len(book["records"]["lcd_indicators"]["rows"]))
                    self.assertEqual(11, len(book["source"]["tables"]["troubleshooting"]["rows"]))
                    self.assertEqual([3, 2], [book["records"]["warranty_columns"][f"{p}_years"] for p in ("standard", "extension")])
                    app = book["records"]["app_sections"]["blocks"]
                    for field, prefix in (("add_heading", "2."), ("enable", "4.1"), ("disable", "4.2"), ("reset", "4.3")):
                        self.assertTrue(app[field]["text"].startswith(prefix), field)
                    provenance = book["provenance"]
                    self.assertEqual(209, len(provenance["text_spans"]))
                    self.assertFalse(provenance["image_extraction_performed"])
                    self.assertEqual([], provenance["corrections_applied"])
                    # A missing exported font glyph must be reported, never
                    # substituted using an older JSON/AI text value.
                    self.assertEqual(5, len(provenance["unresolved_text"]))
                    self.assertEqual(16, sum(s["replacement_character_count"] for s in provenance["unresolved_text"]))

    def test_poisoned_legacy_copy_cannot_change_new_extraction(self):
        def poison(value):
            if isinstance(value, list):
                return [poison(item) for item in value]
            if isinstance(value, dict):
                return {key: "STALE COPY MUST NOT APPEAR" if key in {
                    "text", "raw_text", "label", "meaning", "raw_label", "action", "value", "titles",
                } and isinstance(item, (str, list)) else poison(item) for key, item in value.items()}
            return value

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "source").mkdir()
            manifest = json.loads((RECIPE / "source_manifest.json").read_text(encoding="utf-8"))
            names = ("nl_direct_source", "operation_tables", "warranty_columns", "app_sections",
                     "symbols", "lcd_indicators", "front_back_source")
            for name in names:
                data = json.loads((RECIPE / "source" / f"{name}.json").read_text(encoding="utf-8"))
                path = root / "source" / f"{name}.json"
                path.write_text(json.dumps(poison(data)), encoding="utf-8")
                entry = next(e for e in manifest["inputs"] if e["path"] == f"source/{name}.json")
                # Deliberately re-pin the modified test fixture. Production
                # recipes remain immutable; this tests text authority alone.
                entry.update(size=path.stat().st_size, sha256=file_sha256(path))
            (root / "source_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            book = load_pdf_book(PDF, "nl", root)
            self.assertNotIn("STALE COPY MUST NOT APPEAR", json.dumps(book))
            self.assertEqual("GARANTIE", book["records"]["warranty_columns"]["blocks"]["title"]["text"])


if __name__ == "__main__":
    unittest.main()
