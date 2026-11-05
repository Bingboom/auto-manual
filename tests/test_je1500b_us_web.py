"""JE-1500B US Git-only manual candidate: source identity, verbatim copy, artwork and replay."""
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
PACKAGE = ROOT / "manual_sources/JE-1500B/US/en/git-20261027-bb5a455b"
SOURCE_SHA = "bb5a455b5c3e03b70ee95d6d6ceb74a9c98b671addc1d30d9637f9bb974a7dbb"
MARKDOWN = "manual_je1500b_us_en.md"
# Printed run-in signal words become the shared callout label without the colon.
CALLOUT_LINES = {"ops.lcd.tip", "solar.caution", "solar.g2.tip"}
CHAPTERS = ["TECHNICAL SPECIFICATIONS", "GENERAL INFO", "OUTPUT PORTS", "INPUT PORTS",
            "ENVIRONMENTAL OPERATING TEMPERATURE", "PACKAGE LIST", "GET TO KNOW YOUR GEAR", "LCD DISPLAY",
            "BASIC OPERATIONS", "CHARGING YOUR JACKERY EXPLORER 1500 PRO", "CHARGING FROM THE WALL",
            "SOLAR ENERGY CHARGING", "CHARGING IN THE CAR", "SAFETY PRECAUTIONS WHEN USING", "WARRANTY"]


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


class Je1500bUsWebTests(unittest.TestCase):
    def test_identity_and_candidate_status(self):
        manifest = read(PACKAGE / "source_manifest.json")
        self.assertEqual(manifest["target"]["model"], "JE-1500B")
        self.assertEqual((manifest["target"]["region"], manifest["target"]["languages"]), ("US", ["en"]))
        self.assertEqual(manifest["target"]["technical_version"], PACKAGE.name)
        self.assertEqual(manifest["target"]["printed_manual_version"], "Version: JAK-UM-V1.0")
        self.assertEqual(manifest["original_source"]["sha256"], SOURCE_SHA)
        self.assertEqual(file_sha256(PACKAGE / manifest["original_source"]["filename"]), SOURCE_SHA)
        self.assertEqual(manifest["feishu_record"]["record_id"], "reczz28SPLqH7mCa")
        self.assertEqual(manifest["feishu_record"]["物料号文本"], "38-0001-000307")
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
            value = squash(line["text"])
            if line["id"] in CALLOUT_LINES:
                value = value.replace(":", "", 1)
            if value not in page and value not in alts:
                missing.append(line["id"])
            if "marker" in line:
                self.assertIn(line["marker"], page, line["id"])
        self.assertEqual(missing, [])
        for line in web_lines():
            if line["id"].startswith(("fig.", "names.")):
                self.assertIn(squash(line["text"]), alts, line["id"])

    def test_chapters_and_print_only_pages_excluded(self):
        markdown = (PACKAGE / "web/en" / MARKDOWN).read_text(encoding="utf-8")
        headings = [squash(BeautifulSoup(line, "html.parser").get_text()).lstrip("#")
                    for line in markdown.splitlines() if line.startswith("## ")]
        self.assertEqual(headings, [squash(c) for c in CHAPTERS])
        for print_only in ("JAK-UM-V1.0", "Contact us:", "5310 Bunche Dr", "JACKERY INC."):
            self.assertNotIn(print_only, markdown)

    def test_model_facts_come_from_this_source(self):
        markdown = (PACKAGE / "web/en" / MARKDOWN).read_text(encoding="utf-8")
        for fact in ("JE-1500B", "Jackery Explorer 1500 Pro", "Lithium-ion 35Ah/43.2V DC (1512Wh)",
                     "1800W Rated, 3600W Surge peak", "double to 24A/1400W max", "36 months"):
            self.assertIn(fact, markdown)
        for foreign in ("JE-2000A", "JE-1500D", "JE-1000D", "2000 Pro", "2160Wh", "1070Wh", "1536Wh"):
            self.assertNotIn(foreign, markdown)

    def test_assets_and_symbol_admission(self):
        recipe = read(PACKAGE / "source/asset_recipe.json")
        for item in recipe["reused"]:
            self.assertEqual(file_sha256(PACKAGE / item["path"]), item["sha256"])
            self.assertEqual(file_sha256(ROOT / item["from"]), item["sha256"])
        decisions = {row["final_path"]: row["sha256"] for row in read(PACKAGE / "source/asset_decisions.json")}
        for path in (PACKAGE / "assets").rglob("*"):
            if path.is_file():
                self.assertEqual(decisions[path.relative_to(PACKAGE).as_posix()], file_sha256(path))
        markdown = (PACKAGE / "web/en" / MARKDOWN).read_text(encoding="utf-8")
        refs = {img["src"] for img in BeautifulSoup(markdown, "html.parser").find_all("img")}
        for ref in refs:
            self.assertTrue((PACKAGE / "web/en" / ref).is_file(), ref)
        self.assertEqual(recipe["symbols"], [])
        admission = read(PACKAGE / "source_manifest.json")["symbol_asset_admission"]
        self.assertEqual(admission["locales"], {"en": []})
        self.assertNotIn("HB-TABLE-SYMBOL-ICON", markdown)

    def test_cold_replay_matches_stored_candidate(self):
        try:
            subprocess.run([resolve_pandoc_binary(None), "--version"], check=True, capture_output=True)
        except (OSError, RuntimeError, subprocess.CalledProcessError):
            self.skipTest("Pandoc unavailable")
        rebuild = load("je1500b_us_rebuild", PACKAGE / "rebuild.py")
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "replay"
            rebuild.rebuild(output)
            for name in (MARKDOWN, "manual.ir.json", "_static/source_geometry.css"):
                self.assertEqual((output / name).read_bytes(), (PACKAGE / "web/en" / name).read_bytes(), name)

    def test_content_is_rebuilt_from_transcription(self):
        builder = load("je1500b_us_build_content", PACKAGE / "build_content.py")
        built = json.loads(json.dumps(builder.build(), ensure_ascii=False))
        self.assertEqual(built, read(PACKAGE / "source/en/content.json"))

    def test_changed_source_input_is_rejected(self):
        module = load("je1500b_us_rebuild_copy", PACKAGE / "rebuild.py")
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "source"
            shutil.copytree(PACKAGE, source, ignore=shutil.ignore_patterns("web", "evidence", "__pycache__"))
            path = source / "source/en/content.json"
            path.write_text(path.read_text(encoding="utf-8").replace("1512Wh", "1513Wh"), encoding="utf-8")
            module.SOURCE_ROOT = source
            with self.assertRaisesRegex(ValueError, "input missing or changed"):
                module.rebuild(Path(temp) / "out")


if __name__ == "__main__":
    unittest.main()
