"""JE-1000D US en Git-only manual: source identity, verbatim copy, artwork and replay."""
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
PACKAGE = ROOT / "manual_sources/JE-1000D/US/en/git-20261027-10d15090"
SOURCE_SHA = "10d15090f944d3a0a1518e495dca4cf5cad15252220990c1b0e324564519316f"
MARKDOWN = "manual_je1000d_us_en.md"
# Printed signal-word lines: the shared callout strip shows the label without its trailing colon.
LABEL_LINES = {"ops.caut.label", "chg.caut.label", "opi.warn", "opi.danger",
               "appm.note1", "appm.note2", "appm.note3"}
CHAPTERS = ["TECHNICAL SPECIFICATIONS", "PACKAGE LIST", "GET TO KNOW YOUR GEAR", "LCD DISPLAY",
            "BASIC OPERATIONS", "APP CONNECTION", "CHARGING YOUR JACKERY EXPLORER 1000",
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


class Je1000dUsWebTests(unittest.TestCase):
    def test_identity_and_candidate_status(self):
        manifest = read(PACKAGE / "source_manifest.json")
        self.assertEqual(manifest["target"]["model"], "JE-1000D")
        self.assertEqual((manifest["target"]["region"], manifest["target"]["languages"]), ("US", ["en"]))
        self.assertEqual(manifest["target"]["technical_version"], PACKAGE.name)
        self.assertEqual(manifest["target"]["printed_manual_version"], "V2")
        self.assertEqual(manifest["original_source"]["sha256"], SOURCE_SHA)
        self.assertEqual(file_sha256(PACKAGE / manifest["original_source"]["filename"]), SOURCE_SHA)
        self.assertEqual(manifest["feishu_record"]["record_id"], "reczz28SPRx9pE14")
        self.assertEqual(manifest["feishu_record"]["物料号文本"], "38-0001-000612")
        self.assertEqual(len(manifest["feishu_record"]["sku"]), 10)
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
                           "1-888-502-2236"):
            self.assertNotIn(print_only, markdown)

    def test_model_facts_come_from_this_source(self):
        markdown = (PACKAGE / "web/en" / MARKDOWN).read_text(encoding="utf-8")
        for fact in ("JE-1000D", "30.4Ah/35.2V DC (1070Wh)", "1500W Rated, 3000W Surge peak", "within 20ms",
                     "Jackery Explorer 1000 is 36 months", "two DC8020 input ports", "12V⎓10A"):
            self.assertIn(fact, markdown)
        for foreign in ("JE-1500D", "JE-1000F", "1536Wh", "Explorer 1500", "ポータブル電源", "10ms", "within 10"):
            self.assertNotIn(foreign, markdown)

    def test_assets_reuse_and_no_symbol_table(self):
        recipe = read(PACKAGE / "source/asset_recipe.json")
        manifest = read(PACKAGE / "source_manifest.json")
        for item in recipe["reused"]:
            self.assertEqual(file_sha256(PACKAGE / item["path"]), item["sha256"])
            self.assertEqual(file_sha256(ROOT / item["from"]), item["sha256"])
        reuse = manifest["artwork_reuse_comparison"]
        self.assertEqual(sorted({r["asset_ref"] for r in reuse}), sorted(i["path"] for i in recipe["reused"]))
        self.assertTrue(all(r["max_mean_channel_error"] <= 0.02 for r in reuse))
        self.assertEqual(recipe["symbols"], [])
        self.assertEqual(manifest["symbol_asset_admission"]["locales"], {"en": []})
        markdown = (PACKAGE / "web/en" / MARKDOWN).read_text(encoding="utf-8")
        refs = {img["src"] for img in BeautifulSoup(markdown, "html.parser").find_all("img")}
        for ref in refs:
            self.assertTrue((PACKAGE / "web/en" / ref).is_file(), ref)
            self.assertEqual(file_sha256(PACKAGE / "web/en" / ref), file_sha256(PACKAGE / ref), ref)
        expected = {p["path"] for p in recipe["panels"]} | {i["path"] for i in recipe["native_icons"]}
        expected |= {i["path"] for i in recipe["reused"]}
        self.assertEqual(refs, expected)

    def test_cold_replay_matches_stored_candidate(self):
        try:
            subprocess.run([resolve_pandoc_binary(None), "--version"], check=True, capture_output=True)
        except (OSError, RuntimeError, subprocess.CalledProcessError):
            self.skipTest("Pandoc unavailable")
        rebuild = load("je1000d_us_rebuild", PACKAGE / "rebuild.py")
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "replay"
            rebuild.rebuild(output)
            for name in (MARKDOWN, "manual.ir.json", "_static/source_geometry.css"):
                self.assertEqual((output / name).read_bytes(), (PACKAGE / "web/en" / name).read_bytes(), name)

    def test_content_is_rebuilt_from_transcription(self):
        builder = load("je1000d_us_build_content", PACKAGE / "build_content.py")
        built = json.loads(json.dumps(builder.build(), ensure_ascii=False))
        self.assertEqual(built, read(PACKAGE / "source/en/content.json"))

    def test_changed_source_input_is_rejected(self):
        module = load("je1000d_us_rebuild_copy", PACKAGE / "rebuild.py")
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "source"
            shutil.copytree(PACKAGE, source, ignore=shutil.ignore_patterns("web", "evidence", "__pycache__"))
            path = source / "source/en/content.json"
            path.write_text(path.read_text(encoding="utf-8").replace("1070Wh", "1071Wh"), encoding="utf-8")
            module.SOURCE_ROOT = source
            with self.assertRaisesRegex(ValueError, "input missing or changed"):
                module.rebuild(Path(temp) / "out")


if __name__ == "__main__":
    unittest.main()
