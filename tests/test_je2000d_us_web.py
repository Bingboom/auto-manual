"""JE-2000D US en Git-only manual: source identity, verbatim copy, artwork and replay."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from bs4 import BeautifulSoup

from tools.manual_ir.hashing import file_sha256
from tools.word.bundle_docx_pandoc import resolve_pandoc_binary

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "manual_sources/JE-2000D/US/en/git-20261028-3d50ef64"
SOURCE_SHA = "3d50ef6490217a0893119567ef0d276f40b23d45e52e51560e97f724b6ca8c77"
MARKDOWN = "manual_je2000d_us_en.md"
# Printed signal-word lines: the shared callout strip shows the label without its trailing colon.
LABEL_LINES = {"opi.warn", "opi.danger", "appm.note1", "appm.note2", "appm.note3"}
CHAPTERS = ["TECHNICAL SPECIFICATIONS", "PACKAGE LIST", "GET TO KNOW YOUR GEAR", "LCD DISPLAY",
            "BASIC OPERATIONS", "APP CONNECTION", "CHARGING YOUR JACKERY EXPLORER 2000",
            "INSTRUCTIONS PERTAINING TO RISK OF FIRE, ELECTRIC SHOCK, OR INJURY TO PERSONS",
            "WARRANTY", "User Manual for Jackery App"]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def squash(value: str) -> str:
    return "".join(value.split())


def visible_text(markdown: str) -> str:
    soup = BeautifulSoup(markdown, "html.parser")
    for node in soup.find_all(["style", "script"]):
        node.decompose()
    return squash(soup.get_text(""))


def web_lines() -> list[dict]:
    pages = read(PACKAGE / "source/transcription.json")["pages"]
    return [line for page in pages if page["web"] for line in page["lines"]]


class Je2000dUsWebTests(unittest.TestCase):
    def test_identity_and_candidate_status(self):
        manifest = read(PACKAGE / "source_manifest.json")
        self.assertEqual(manifest["target"]["model"], "JE-2000D")
        self.assertEqual((manifest["target"]["region"], manifest["target"]["languages"]), ("US", ["en"]))
        self.assertEqual(manifest["target"]["technical_version"], PACKAGE.name)
        self.assertEqual(manifest["target"]["printed_manual_version"], "V2")
        self.assertEqual(manifest["original_source"]["sha256"], SOURCE_SHA)
        self.assertEqual(file_sha256(PACKAGE / manifest["original_source"]["filename"]), SOURCE_SHA)
        self.assertEqual(manifest["base_record"]["record_id"], "reczz28SlRGJhr8p")
        self.assertEqual(manifest["base_record"]["material_number"], "16-0102-000055")
        self.assertEqual(manifest["base_record"]["project_number"], "HTE117")
        self.assertEqual(len(manifest["base_record"]["sku"]), 6)
        self.assertFalse(manifest["design_original"]["stored_in_package"])
        self.assertEqual(manifest["route"], "JE-2000D/US/en/md")
        self.assertTrue(manifest["legacy_default"])
        ir = read(PACKAGE / "web/en/manual.ir.json")
        if manifest["publication_status"] == "operator-authorized-git-only-release":
            self.assertTrue(manifest["publication_eligible"])
            self.assertTrue(ir["metadata"]["publication_eligible"])
            approval = read(PACKAGE / "source/approval.json")
            self.assertEqual(approval["source_sha256"], SOURCE_SHA)
            self.assertTrue(approval["operator_quote"])
        else:
            self.assertEqual(manifest["publication_status"], "candidate-pending-operator-review")
            self.assertFalse(manifest["publication_eligible"])
            self.assertFalse(ir["metadata"]["publication_eligible"])
            self.assertFalse((PACKAGE / "source/approval.json").exists())

    def test_inputs_are_pinned(self):
        manifest = read(PACKAGE / "source_manifest.json")
        for row in manifest["inputs"]:
            self.assertEqual(file_sha256(PACKAGE / row["path"]), row["sha256"], row["path"])
        listed = {row["path"] for row in manifest["inputs"]}
        for folder in ("source", "assets"):
            for path in (PACKAGE / folder).rglob("*"):
                if path.is_file():
                    self.assertIn(path.relative_to(PACKAGE).as_posix(), listed)

    def test_every_web_line_is_selectable_text_in_the_page(self):
        markdown = (PACKAGE / "web/en" / MARKDOWN).read_text(encoding="utf-8")
        page = visible_text(markdown)
        soup = BeautifulSoup(markdown, "html.parser")
        alts = squash(" ".join(img.get("alt", "") for img in soup.find_all("img")))
        missing = []
        for line in web_lines():
            value = squash(line["text"]).replace("[+]", "+")
            if line["id"] in LABEL_LINES:
                value = value.replace(":", "", 1)
            if value not in page and value not in alts:
                missing.append(line["id"])
        self.assertEqual(missing, [])
        for line in web_lines():
            if line["id"].startswith(("fig.", "names.f.", "names.r.")):
                self.assertIn(squash(line["text"]), alts, line["id"])

    def test_chapters_and_print_only_pages_excluded(self):
        markdown = (PACKAGE / "web/en" / MARKDOWN).read_text(encoding="utf-8")
        headings = [squash(BeautifulSoup(line, "html.parser").get_text())
                    for line in markdown.splitlines() if line.startswith("## ")]
        self.assertEqual([h.lstrip("#") for h in headings], [squash(c) for c in CHAPTERS])
        for print_only in ("JACKERY INC.", "5310 Bunche Dr", "Website:www.jackery.com", "Contact us:",
                           "1-888-502-2236", "CONTENTS"):
            self.assertNotIn(print_only, markdown)

    def test_model_facts_come_from_this_source(self):
        markdown = (PACKAGE / "web/en" / MARKDOWN).read_text(encoding="utf-8")
        for fact in ("JE-2000D", "45.6Ah/44.8V DC (2042Wh)", "2200W Rated, 4400W Surge peak", "within 20ms",
                     "Jackery Explorer 2000 is 36 months", "two DC8020 input ports", "12V⎓10A Max", "18.3A",
                     "100-120V ~ 60Hz, 12A Max", "16-60V⎓12A", "Around 39.5 lbs / 17.9 kg", "Interpretation Rights"):
            self.assertIn(fact, markdown)
        for foreign in ("JE-1000D", "JE-2000A", "1070Wh", "Explorer 1000", "Explorer 2000 Pro", "3000W Surge",
                        "ポータブル電源", "10ms", "within 10", "battery.battery"):
            self.assertNotIn(foreign, markdown)

    def test_assets_reuse_and_no_symbol_table(self):
        recipe = read(PACKAGE / "source/asset_recipe.json")
        manifest = read(PACKAGE / "source_manifest.json")
        for item in recipe["reused"]:
            self.assertEqual(file_sha256(PACKAGE / item["path"]), item["sha256"])
            self.assertEqual(file_sha256(ROOT / item["from"]), item["sha256"])
        for item in recipe["reused_panels"]:
            self.assertEqual(file_sha256(PACKAGE / item["path"]), item["sha256"])
            self.assertEqual(file_sha256(ROOT / item["from"]), item["sha256"])
        reuse = manifest["artwork_reuse_comparison"]
        self.assertEqual(sorted({r["asset_ref"] for r in reuse}),
                         sorted(i["path"] for i in recipe["reused"] + recipe["reused_panels"]))
        self.assertTrue(all(r["max_mean_channel_error"] <= 0.02 for r in reuse))
        decisions = {row["final_path"] for row in read(PACKAGE / "source/asset_decisions.json")}
        self.assertEqual(decisions, {p.relative_to(PACKAGE).as_posix() for p in (PACKAGE / "assets").rglob("*")
                                     if p.is_file()})
        self.assertEqual(recipe["symbols"], [])
        self.assertEqual(manifest["symbol_asset_admission"]["locales"], {"en": []})
        markdown = (PACKAGE / "web/en" / MARKDOWN).read_text(encoding="utf-8")
        refs = {img["src"] for img in BeautifulSoup(markdown, "html.parser").find_all("img")}
        for ref in refs:
            self.assertTrue((PACKAGE / "web/en" / ref).is_file(), ref)
            self.assertEqual(file_sha256(PACKAGE / "web/en" / ref), file_sha256(PACKAGE / ref), ref)
        expected = {p["path"] for p in recipe["panels"]} | {i["path"] for i in recipe["native_icons"]}
        expected |= {i["path"] for i in recipe["reused"] + recipe["reused_panels"]}
        self.assertEqual(refs, expected)

    def test_cold_replay_matches_stored_candidate(self):
        try:
            subprocess.run([resolve_pandoc_binary(None), "--version"], check=True, capture_output=True)
        except (OSError, RuntimeError, subprocess.CalledProcessError):
            self.skipTest("Pandoc unavailable")
        rebuild = load("je2000d_us_rebuild", PACKAGE / "rebuild.py")
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "replay"
            rebuild.rebuild(output)
            for name in (MARKDOWN, "manual.ir.json", "_static/source_geometry.css"):
                self.assertEqual((output / name).read_bytes(), (PACKAGE / "web/en" / name).read_bytes(), name)

    def test_content_is_rebuilt_from_transcription(self):
        builder = load("je2000d_us_build_content", PACKAGE / "build_content.py")
        built = json.loads(json.dumps(builder.build(), ensure_ascii=False))
        self.assertEqual(built, read(PACKAGE / "source/en/content.json"))

    def test_changed_source_input_is_rejected(self):
        module = load("je2000d_us_rebuild_copy", PACKAGE / "rebuild.py")
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "source"
            shutil.copytree(PACKAGE, source, ignore=shutil.ignore_patterns("web", "evidence", "__pycache__"))
            path = source / "source/en/content.json"
            path.write_text(path.read_text(encoding="utf-8").replace("2042Wh", "2043Wh"), encoding="utf-8")
            module.SOURCE_ROOT = source
            with self.assertRaisesRegex(ValueError, "input missing or changed"):
                module.rebuild(Path(temp) / "out")


if __name__ == "__main__":
    unittest.main()
