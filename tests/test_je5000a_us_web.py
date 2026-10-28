"""JE-5000A US Git-only manual candidate: source identity, verbatim copy, artwork and replay."""
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
PACKAGE = ROOT / "manual_sources/JE-5000A/US/en/git-20261028-804ebe78"
SOURCE_SHA = "804ebe784c84a698800b2c1cc0f4d28ec692057b1600c48fcc3604e27c86f013"
MARKDOWN = "manual_je5000a_us_en.md"
PRINT_ONLY = {"imp.badge"}
SPEC = ["GENERAL INFO", "INPUT PORTS", "OUTPUT PORTS", "ENVIRONMENTAL OPERATING TEMPERATURE"]
CHAPTERS = ["IMPORTANT", "IMPORTANT SAFETY INFORMATION", "WHAT'S IN THE BOX", "PRODUCT OVERVIEW", "LCD DISPLAY",
            "OPERATIONS", "TROUBLESHOOTING", "UNINTERRUPTIBLE POWER SUPPLY (UPS)", "CONNECTIONS", "CHARGING",
            "WARRANTY", "APP SETUP", "SPECIFICATIONS", *SPEC, "SMART HOME BACKUP SYSTEM (AC ESS) INSTALLATION GUIDE",
            "Jackery Explorer 5000 Plus", *SPEC, "Jackery Battery Pack 5000 Plus", "GENERAL INFO",
            "INPUT/OUTPUT PORTS", "ENVIRONMENTAL OPERATING TEMPERATURE", "Jackery Smart Transfer Switch",
            "GENERAL INFO"]


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
    return [line for page in pages if page["web"] for line in page["lines"] if line["id"] not in PRINT_ONLY]


class Je5000aUsWebTests(unittest.TestCase):
    def test_identity_and_candidate_status(self):
        manifest = read(PACKAGE / "source_manifest.json")
        self.assertEqual(manifest["target"]["model"], "JE-5000A")
        self.assertEqual((manifest["target"]["region"], manifest["target"]["languages"]), ("US", ["en"]))
        self.assertEqual(manifest["target"]["technical_version"], PACKAGE.name)
        self.assertEqual(manifest["original_source"]["sha256"], SOURCE_SHA)
        self.assertEqual(file_sha256(PACKAGE / manifest["original_source"]["filename"]), SOURCE_SHA)
        self.assertEqual(manifest["base_record"]["record_id"], "reczz28SlRGJhXPM")
        self.assertEqual(manifest["base_record"]["material_number"], "16-0102-000447")
        self.assertEqual(manifest["route"], "JE-5000A/US/en/md")
        ir = read(PACKAGE / "web/en/manual.ir.json")
        if manifest["publication_status"] == "operator-authorized-git-only-release":
            self.assertTrue(ir["metadata"]["publication_eligible"])
            self.assertEqual(manifest.get("staged_shared_symbols"), [])
        else:
            self.assertEqual(manifest["publication_status"], "candidate-pending-operator-review")
            self.assertFalse(manifest["publication_eligible"])
            self.assertFalse(ir["metadata"]["publication_eligible"])
            self.assertFalse((PACKAGE / "source/approval.json").exists())

    def test_no_feishu_tokens_are_recorded(self):
        for path in PACKAGE.rglob("*"):
            if path.suffix in {".json", ".md", ".py"} and "web" not in path.relative_to(PACKAGE).parts:
                text = path.read_text(encoding="utf-8")
                for marker in ("obj_token", "file_token", "feishu.cn/file", "feishu.cn/wiki"):
                    self.assertNotIn(marker, text, path)

    def test_inputs_are_pinned(self):
        manifest = read(PACKAGE / "source_manifest.json")
        for row in manifest["inputs"]:
            self.assertEqual(file_sha256(PACKAGE / row["path"]), row["sha256"], row["path"])
        listed = {row["path"] for row in manifest["inputs"]}
        for folder in ("source", "assets"):
            for path in (PACKAGE / folder).rglob("*"):
                if path.is_file():
                    self.assertIn(path.relative_to(PACKAGE).as_posix(), listed)

    def test_every_web_line_is_text_or_alt_in_the_page(self):
        markdown = (PACKAGE / "web/en" / MARKDOWN).read_text(encoding="utf-8")
        page = visible_text(markdown)
        soup = BeautifulSoup(markdown, "html.parser")
        alts = squash(" ".join(img.get("alt", "") for img in soup.find_all("img")))
        missing = []
        for line in web_lines():
            text = squash(line["text"]).replace("[+]", "+")
            if text not in page and text not in alts:
                missing.append(line["id"])
        self.assertEqual(missing, [])
        for line in web_lines():
            if line["id"].startswith(("fig.", "names.f.", "names.l.", "names.r.")):
                self.assertIn(squash(line["text"]), alts, line["id"])

    def test_chapters_and_print_only_pages_excluded(self):
        markdown = (PACKAGE / "web/en" / MARKDOWN).read_text(encoding="utf-8")
        headings = [squash(BeautifulSoup(line, "html.parser").get_text())
                    for line in markdown.splitlines() if line.startswith("## ")]
        self.assertEqual([h.lstrip("#") for h in headings], [squash(c) for c in CHAPTERS])
        for print_only in ("TABLE OF CONTENTS", "5310 Bunche Dr.", "JACKERY INC.", "1-888-502-2236",
                           "CONTACT US:"):
            self.assertNotIn(print_only, markdown)

    def test_model_facts_come_from_this_source(self):
        markdown = (PACKAGE / "web/en" / MARKDOWN).read_text(encoding="utf-8")
        for fact in ("JE-5000A", "45Ah/112Vdc (5040Wh)", "4000 cycles to 70%+ capacity", "within 20 ms",
                     "is 60 months", "120V/240V~60Hz, 30A, 7200W Max", "JBP-5000A", "JA-TS02A", "HB5000A-TS02A",
                     "BMS or battery failuare"):
            self.assertIn(fact, markdown)
        for foreign in ("JE-1500D", "JE-1000D", "JHP-5000C", "HomePower 5000", "1536 Wh", "ポータブル電源"):
            self.assertNotIn(foreign, markdown)

    def test_assets_and_symbols(self):
        recipe = read(PACKAGE / "source/asset_recipe.json")
        manifest = read(PACKAGE / "source_manifest.json")
        catalog = read(ROOT / "docs/renderers/web/assets/shared/symbols/manifest.json")
        keys = {row["key"]: row for row in catalog["assets"]}
        staged = {row["key"]: row for row in manifest["staged_shared_symbols"]}
        for symbol in [*recipe["symbols"], recipe["fcc_mark"]]:
            key = symbol["shared_symbol_key"]
            row = keys.get(key) or staged[key]
            self.assertEqual(row["path"], symbol["shared_path"])
            self.assertEqual(file_sha256(PACKAGE / symbol["path"]), row["sha256"], symbol["path"])
            self.assertEqual(symbol.get("staged", False), key in staged)
        for key in staged:
            self.assertNotIn(key, keys, "approved staged symbols leave staged_shared_symbols")
        for item in recipe["reused"]:
            self.assertEqual(file_sha256(PACKAGE / item["path"]), file_sha256(ROOT / item["from"]))
        markdown = (PACKAGE / "web/en" / MARKDOWN).read_text(encoding="utf-8")
        refs = {img["src"] for img in BeautifulSoup(markdown, "html.parser").find_all("img")}
        for ref in refs:
            self.assertTrue((PACKAGE / "web/en" / ref).is_file(), ref)
        admission = manifest["symbol_asset_admission"]["locales"]["en"]
        self.assertEqual([row["asset_ref"] for row in admission], [s["path"] for s in recipe["symbols"]])
        self.assertTrue(all(row["max_mean_channel_error"] <= 0.02 for row in admission))

    def test_no_package_styles(self):
        css = (PACKAGE / "source/geometry.css").read_text(encoding="utf-8")
        for word in ("color", "background", "border", "fill", "stroke", "shadow", "outline"):
            self.assertNotIn(word, css)
        exceptions = read(PACKAGE / "source_manifest.json")["shared_component_exceptions"]
        self.assertEqual([(row["page_id"], row["kind"]) for row in exceptions], [("troubleshooting", "table")])

    def test_staged_symbols_are_package_only(self):
        manifest = read(PACKAGE / "source_manifest.json")
        recipe = read(PACKAGE / "source/asset_recipe.json")
        catalog = read(ROOT / "docs/renderers/web/assets/shared/symbols/manifest.json")
        keys = {row["key"] for row in catalog["assets"]}
        staged = {row["key"]: row for row in manifest["staged_shared_symbols"]}
        for glyph in recipe["inline_glyphs"]:
            self.assertEqual(file_sha256(PACKAGE / glyph["path"]), staged[glyph["shared_symbol_key"]]["sha256"])
        for key, row in staged.items():
            if key not in keys:
                self.assertFalse((ROOT / "docs/renderers/web/assets/shared/symbols" / row["path"]).exists(), key)
        for row in manifest["artwork_reuse_comparison"]:
            self.assertEqual(file_sha256(PACKAGE / row["asset_ref"]), row["sha256"])
            self.assertEqual(file_sha256(ROOT / row["from"]), row["sha256"])
            self.assertTrue(row.get("identical_path_data") or row.get("max_mean_channel_error", 1) <= 0.02)

    def test_cold_replay_matches_stored_candidate(self):
        try:
            subprocess.run([resolve_pandoc_binary(None), "--version"], check=True, capture_output=True)
        except (OSError, RuntimeError, subprocess.CalledProcessError):
            self.skipTest("Pandoc unavailable")
        rebuild = load("je5000a_us_rebuild", PACKAGE / "rebuild.py")
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "replay"
            rebuild.rebuild(output)
            for name in (MARKDOWN, "manual.ir.json", "_static/source_geometry.css", "conf.py"):
                self.assertEqual((output / name).read_bytes(), (PACKAGE / "web/en" / name).read_bytes(), name)

    def test_content_is_rebuilt_from_transcription(self):
        builder = load("je5000a_us_build_content", PACKAGE / "build_content.py")
        built = json.loads(json.dumps(builder.build(), ensure_ascii=False))
        self.assertEqual(built, read(PACKAGE / "source/en/content.json"))

    def test_changed_source_input_is_rejected(self):
        module = load("je5000a_us_rebuild_copy", PACKAGE / "rebuild.py")
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "source"
            shutil.copytree(PACKAGE, source, ignore=shutil.ignore_patterns("web", "evidence", "__pycache__"))
            path = source / "source/en/content.json"
            path.write_text(path.read_text(encoding="utf-8").replace("45Ah/112Vdc (5040Wh)", "45Ah/112Vdc (5041Wh)"), encoding="utf-8")
            module.SOURCE_ROOT = source
            with self.assertRaisesRegex(ValueError, "input missing or changed"):
                module.rebuild(Path(temp) / "out")


if __name__ == "__main__":
    unittest.main()
