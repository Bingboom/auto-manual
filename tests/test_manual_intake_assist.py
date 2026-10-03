"""Assistance must expose missing work, not bless stale or incomplete copy."""
from copy import deepcopy
from hashlib import sha256
import csv
import json
from pathlib import Path
import tempfile
import unittest

import fitz

from tools.asset_registry import REQUIRED_COLUMNS
from tools.component_specs.fcc import fcc_component_spec
from tools.manual_intake_assist import main
from tools.manual_intake_assist.packet import check_packet, copy_items, make_packet, native_copy_map
from tools.manual_intake_assist.art_review import apply_review_annotations, category, inventory, write_review


class IntakePacketTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source.pdf"
        doc = fitz.open()
        doc.new_page().insert_text((40, 40), "Source native text")
        doc.save(self.source)
        doc.close()
        self.ir = self.root / "manual.ir.json"
        self.raw = {"model": "TEST", "region": "EU", "language": "en", "pages": [
            {"page_id": "safety", "blocks": [{"component_spec": {"component_id": "HB-NOTICE",
                "slots": [{"content": {"text": "Warning", "body_html": "<b>Warning</b><!-- hidden --><style>x</style>"}}]},
                "metadata": {"text": "not copy"}, "source_path": "/do/not/translate"}]}],
            "metadata": {"asset_sha256": {"assets/x.png": "a" * 64}}}
        self.ir.write_text(json.dumps(self.raw))
        self.expected = make_packet(self.ir, self.source, model="TEST", region="EU", language="fr", pages=[1])

    def complete(self):
        packet = deepcopy(self.expected)
        for item in packet["items"]:
            item.update(native="Attention", decision="native-copy", physical_page=1, evidence="page 1, block 0; visually checked")
        return packet

    def test_visible_copy_grouped_with_occurrences(self):
        items = self.expected["items"]
        self.assertEqual([i["reference"] for i in items], ["Warning"])
        self.assertEqual(len(items[0]["occurrences"]), 2)
        self.assertEqual(items[0]["occurrences"][0]["component"], "HB-NOTICE")

    def test_component_enums_are_not_translation_tasks(self):
        raw = deepcopy(self.raw)
        slots = raw["pages"][0]["blocks"][0]["component_spec"]["slots"]
        slots.extend([{"role": "caption_mode", "content": "live"},
                      {"role": "reference_id", "content": "locking"},
                      {"role": "body", "content": "<p>Native copy</p>"}])
        texts = [item["reference"] for item in copy_items(raw)]
        self.assertNotIn("live", texts)
        self.assertNotIn("locking", texts)
        self.assertIn("Native copy", texts)
        self.assertNotIn("<p>Native copy</p>", texts)

    def test_complete_is_not_publication_or_baseline_approval(self):
        result = check_packet(self.complete(), self.expected)
        self.assertEqual(result["status"], "copy-mapping-complete")
        self.assertFalse(result["publication_eligible"])
        mapped = native_copy_map(self.complete(), self.expected)
        self.assertEqual(mapped["copy_by_page"], {"safety": {"Warning": "Attention"}})
        self.assertIn("not-approved", mapped["status"])

    def test_mutations_fail(self):
        for name in ("delete", "duplicate", "extra", "slot", "source", "asset", "approval", "page", "empty", "evidence", "pending", "identical"):
            with self.subTest(name=name):
                p = self.complete()
                if name == "delete": p["items"].clear()
                elif name == "duplicate": p["items"].append(deepcopy(p["items"][0]))
                elif name == "extra": p["items"].append({"id": "unknown"})
                elif name == "slot": p["items"][0]["occurrences"] = []
                elif name == "source": p["source_sha256"] = "b" * 64
                elif name == "asset": p["asset_refs"] = {}
                elif name == "approval": p["status"] = "approved"
                elif name == "page": p["items"][0]["physical_page"] = 2
                elif name == "empty": p["items"][0]["native"] = ""
                elif name == "evidence": p["items"][0]["evidence"] = ""
                elif name == "pending": p["items"][0]["decision"] = "pending"
                elif name == "identical": p["items"][0]["decision"] = "source-identical"
                self.assertTrue(check_packet(p, self.expected)["errors"])
                with self.assertRaises(ValueError): native_copy_map(p, self.expected)

    def test_fcc_native_list_copy_cannot_be_omitted(self):
        bullets = ["Reorient or relocate the receiving antenna.",
                   "Increase the separation between the equipment and receiver."]
        spec = fcc_component_spec(
            accessibility_label="FCC notice", opening_copy=["Compliance notice"],
            left_blocks=[{"kind": "list", "items": bullets}], right_blocks=[],
            source_ref="fcc#body", language="en")
        raw = json.loads(json.dumps({"pages": [{"page_id": "fcc", "component_spec": spec.to_dict()}]}))
        expected = deepcopy(self.expected)
        expected["items"] = copy_items(raw)
        self.assertTrue(set(bullets).issubset({i["reference"] for i in expected["items"]}))
        packet = deepcopy(expected)
        for item in packet["items"]:
            item.update(native=item["reference"], decision="source-identical",
                        physical_page=1, evidence="source page 1")
        self.assertFalse(check_packet(packet, expected)["errors"])
        packet["items"] = [i for i in packet["items"] if i["reference"] not in bullets]
        self.assertEqual(sum(e["code"] == "missing_item" for e in check_packet(packet, expected)["errors"]), 2)

    def test_explicit_identical_source_and_long_copy(self):
        p = self.complete()
        p["items"][0].update(native="Warning", decision="source-identical")
        self.assertFalse(check_packet(p, self.expected)["errors"])
        p["items"][0].update(native="Texte long\n" * 50, decision="native-copy")
        self.assertFalse(check_packet(p, self.expected)["errors"])

    def test_invalid_pages_and_reference(self):
        for pages in ([0], [2], [1, 1], []):
            with self.assertRaises(ValueError):
                make_packet(self.ir, self.source, model="TEST", region="EU", language="fr", pages=pages)
        self.raw["pages"].append(deepcopy(self.raw["pages"][0]))
        with self.assertRaises(ValueError): copy_items(self.raw)

    def test_cli_creates_missing_work_and_refuses_overwrite(self):
        output = self.root / "packet.json"
        args = ["packet", "--reference-ir", str(self.ir), "--source", str(self.source),
                "--model", "TEST", "--region", "EU", "--language", "fr", "--pages", "1", "--output", str(output)]
        self.assertEqual(main(args), 0)
        with self.assertRaises(FileExistsError): main(args)
        report = self.root / "check.json"
        args[0] = "check-copy"
        args[-1] = str(report)
        self.assertEqual(main(args + ["--packet", str(output)]), 1)
        self.assertTrue(json.loads(report.read_text())["errors"])


class SharedArtReviewTests(unittest.TestCase):
    def test_byte_dedup_keeps_different_art_and_dedicated_authority(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "data").mkdir()
            with (root / "data/asset_registry.csv").open("w") as f:
                csv.writer(f).writerow(REQUIRED_COLUMNS)
            a, b, c = (root / n for n in ("car.png", "copy.png", "car-other.png"))
            a.write_bytes(b"same"); b.write_bytes(b"same"); c.write_bytes(b"different")
            digest = sha256(b"same").hexdigest()
            for table in ("definitions", "exports", "lcd", "symbols"):
                rows = [{"record_id": "recLCD", "fields": {"icon_en": "Car charging"}, "download_sha256": digest}] if table == "lcd" else []
                (root / f"live-{table}.json").write_text(json.dumps(rows))
            report = inventory(root, [a, b, c], root)
            self.assertEqual(report["unique_bytes"], 2)
            lcd = next(i for i in report["items"] if i["sha256"] == digest)
            self.assertEqual(lcd["category"], "LCD icons 专表")
            self.assertEqual(len(lcd["paths"]), 2)
            self.assertFalse(report["publication_eligible"])
            output = root / "report"
            write_review(report, output, root)
            self.assertEqual((output / lcd["preview"]).read_bytes(), b"same")
            with self.assertRaises(FileExistsError): write_review(report, output, root)

    def test_category_is_a_hint_and_keeps_solar_out_of_lcd(self):
        self.assertEqual(category("lcd.icon.solar-charging.png"), "LCD icons 专表")
        self.assertEqual(category("solar_four.png"), "太阳能板与连接图")
        self.assertEqual(category("car_charge.png"), "车充与车充线")


class SharedArtAnnotationTests(unittest.TestCase):
    def report(self):
        return {"items": [{"id": "ART-a", "sha256": "a" * 64,
            "category": "Symbols 专表", "shared_eligible": True, "priority": True},
            {"id": "ART-op", "sha256": "b" * 64, "category": "操作与按键图",
             "shared_eligible": False, "priority": True}]}

    def test_selections_preserve_conditional_scope_and_exclude_operations(self):
        report = self.report()
        row = {"id": "ART-a", "decision": "limited", "note": "only when source symbol matches"}
        apply_review_annotations(report, {"items": [row]})
        self.assertEqual(report["items"][0]["operator_selection"], row)
        self.assertFalse(report["items"][1]["priority"])
        self.assertFalse(report["publication_eligible"])

    def test_identity_is_hash_bound_and_does_not_replace_original(self):
        report = self.report()
        row = {"id": "ART-a", "sha256": "a" * 64, "label": "Warning triangle",
               "canonical_id": "ART-a", "evidence": "operator selection + visible source"}
        apply_review_annotations(report, identities={"items": [row]})
        self.assertEqual(report["items"][0]["identity_review"], row)
        self.assertEqual(report["items"][0]["sha256"], "a" * 64)

    def test_invalid_annotations_fail_before_any_mutation(self):
        good = {"id": "ART-a", "decision": "limited"}
        for bad in ({"id": "unknown", "decision": "exclude"}, good,
                    {"id": "ART-op", "decision": "reuse"},
                    {"id": "ART-op", "decision": "approved"}):
            report = self.report()
            with self.assertRaises(ValueError):
                apply_review_annotations(report, {"items": [good, bad]})
            self.assertNotIn("operator_selection", report["items"][0])
        for field, value in (("sha256", "wrong"), ("label", ""), ("evidence", ""),
                             ("canonical_id", "unknown"), ("canonical_id", "ART-op")):
            row = {"id": "ART-a", "sha256": "a" * 64, "label": "Warning triangle",
                   "canonical_id": "ART-a", "evidence": "visual comparison"}
            row[field] = value
            with self.assertRaises(ValueError):
                apply_review_annotations(self.report(), identities={"items": [row]})
