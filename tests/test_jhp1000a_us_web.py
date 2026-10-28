"""JHP-1000A US Git-only manual: source identity, verbatim copy, artwork and replay."""
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
PACKAGE = ROOT / "manual_sources/JHP-1000A/US/en/git-20261028-cb256e64"
SOURCE_SHA = "cb256e64ddf9a998f4717e3ec2b038b9ef7711572f7d9b752667f1d6e64077c1"
MARKDOWN = "manual_jhp1000a_us_en.md"
CHAPTERS = ["IMPORTANT", "IMPORTANT SAFETY INFORMATION", "MEANING OF SYMBOLS", "FCC", "WHAT'S IN THE BOX",
            "PRODUCT OVERVIEW", "LCD DISPLAY", "OPERATIONS", "UNINTERRUPTIBLE POWER SUPPLY (UPS)",
            "CHARGING", "STORAGE", "TROUBLESHOOTING",
            "SPECIFICATIONS", "GENERAL INFO", "INPUT PORTS", "OUTPUT PORTS", "ENVIRONMENTAL OPERATING TEMPERATURE",
            "WARRANTY", "APP SETUP"]


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


class Jhp1000aUsWebTests(unittest.TestCase):
    def test_identity_and_candidate_status(self):
        manifest = read(PACKAGE / "source_manifest.json")
        self.assertEqual(manifest["target"]["model"], "JHP-1000A")
        self.assertEqual((manifest["target"]["region"], manifest["target"]["languages"]), ("US", ["en"]))
        self.assertEqual(manifest["target"]["technical_version"], PACKAGE.name)
        self.assertEqual(manifest["route"], "JHP-1000A/US/en/md")
        self.assertIs(manifest["legacy_default"], True)
        self.assertEqual(manifest["base_record"]["record_id"], "reczz28SlRGJh40c")
        self.assertEqual(manifest["base_record"]["material_number"], "16-0102-000344")
        self.assertEqual(manifest["original_source"]["sha256"], SOURCE_SHA)
        self.assertEqual(file_sha256(PACKAGE / manifest["original_source"]["filename"]), SOURCE_SHA)
        self.assertFalse(manifest["design_original"]["stored_in_package"])
        ir = read(PACKAGE / "web/en/manual.ir.json")
        if manifest["publication_status"] == "operator-authorized-git-only-release":
            self.assertTrue(ir["metadata"]["publication_eligible"])
        else:
            self.assertEqual(manifest["publication_status"], "candidate-pending-operator-review")
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
            if line["id"] == "pre.badge":
                continue  # print-layout language badge (web_exclusions)
            text = squash(line["text"]).replace("[+]", "+")
            if text not in page and text not in alts:
                missing.append(line["id"])
        self.assertEqual(missing, [])

    def test_chapters_and_print_only_pages_excluded(self):
        markdown = (PACKAGE / "web/en" / MARKDOWN).read_text(encoding="utf-8")
        headings = [squash(BeautifulSoup(line, "html.parser").get_text())
                    for line in markdown.splitlines() if line.startswith("## ")]
        self.assertEqual([h.lstrip("#") for h in headings], [squash(c) for c in CHAPTERS])
        for print_only in ("TABLE OF CONTENTS", "5310 Bunche Dr", "CONTACT US"):
            self.assertNotIn(print_only, markdown)

    def test_model_facts_come_from_this_source(self):
        markdown = (PACKAGE / "web/en" / MARKDOWN).read_text(encoding="utf-8")
        for fact in ("JHP-1000A /JHP-1000A-WH", "1024 Wh (20Ah/51.2V DC)", "About 23.4 lbs/10.6 kg",
                     "HomePower 1000", "1500W Rated, 3000W Surge peak", "USB-C 100W"):
            self.assertIn(fact, markdown)
        for foreign in ("JHP-1000B", "HomePower 1000 Plus", "HomePower 2000 Plus", "1800W", "battery pack",
                        "American Red Cross", "140W"):
            self.assertNotIn(foreign, markdown)

    def test_pending_symbol_is_the_only_admission_gap(self):
        recipe = read(PACKAGE / "source/asset_recipe.json")
        pending = [s["path"] for s in recipe["symbols"] if s.get("pending_shared_variant")]
        self.assertEqual(pending, ["assets/symbol-07.svg"])
        admission = read(PACKAGE / "source_manifest.json")["symbol_asset_admission"]["locales"]["en"]
        for row in admission:
            if row["asset_ref"] in pending:
                self.assertIn("pending_shared_variant", row)
            else:
                self.assertLessEqual(row["max_mean_channel_error"], 0.02)

    def test_assets_and_shared_symbols(self):
        recipe = read(PACKAGE / "source/asset_recipe.json")
        catalog = read(ROOT / "docs/renderers/web/assets/shared/symbols/manifest.json")
        keys = {row["key"]: row for row in catalog["assets"]}
        for symbol in recipe["symbols"]:
            shared = keys[symbol["shared_symbol_key"]]
            self.assertEqual(shared["path"], symbol["shared_path"])
            self.assertEqual(file_sha256(PACKAGE / symbol["path"]), shared["sha256"])
        for item in recipe["reused"]:
            self.assertEqual(file_sha256(PACKAGE / item["path"]), item["sha256"])
            self.assertEqual(file_sha256(ROOT / item["from"]), item["sha256"])
        markdown = (PACKAGE / "web/en" / MARKDOWN).read_text(encoding="utf-8")
        refs = {img["src"] for img in BeautifulSoup(markdown, "html.parser").find_all("img")}
        for ref in refs:
            self.assertTrue((PACKAGE / "web/en" / ref).is_file(), ref)
        admission = read(PACKAGE / "source_manifest.json")["symbol_asset_admission"]["locales"]["en"]
        self.assertEqual([row["asset_ref"] for row in admission], [s["path"] for s in recipe["symbols"]])
        decisions = {row["slot"] for row in read(PACKAGE / "source/asset_decisions.json")["rows"]}
        actual = {p.relative_to(PACKAGE).as_posix() for p in (PACKAGE / "assets").iterdir()}
        self.assertEqual(decisions, actual)

    def test_cold_replay_matches_stored_candidate(self):
        try:
            subprocess.run([resolve_pandoc_binary(None), "--version"], check=True, capture_output=True)
        except (OSError, RuntimeError, subprocess.CalledProcessError):
            self.skipTest("Pandoc unavailable")
        rebuild = load("jhp1000a_us_rebuild", PACKAGE / "rebuild.py")
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "replay"
            if any(s.get("pending_shared_variant") for s in read(PACKAGE / "source/asset_recipe.json")["symbols"]):
                # The replay is written before symbol admission, which fails until the shared variant lands.
                with self.assertRaisesRegex(RuntimeError, "symbol asset admission failed"):
                    rebuild.rebuild(output)
            else:
                rebuild.rebuild(output)
            for name in (MARKDOWN, "manual.ir.json", "_static/source_geometry.css"):
                self.assertEqual((output / name).read_bytes(), (PACKAGE / "web/en" / name).read_bytes(), name)

    def test_content_is_rebuilt_from_transcription(self):
        builder = load("jhp1000a_us_build_content", PACKAGE / "build_content.py")
        built = json.loads(json.dumps(builder.build(), ensure_ascii=False))
        self.assertEqual(built, read(PACKAGE / "source/en/content.json"))

    def test_changed_source_input_is_rejected(self):
        module = load("jhp1000a_us_rebuild_copy", PACKAGE / "rebuild.py")
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "source"
            shutil.copytree(PACKAGE, source, ignore=shutil.ignore_patterns("web", "evidence", "__pycache__"))
            path = source / "source/en/content.json"
            path.write_text(path.read_text(encoding="utf-8").replace("1024 Wh", "1025 Wh"), encoding="utf-8")
            module.SOURCE_ROOT = source
            with self.assertRaisesRegex(ValueError, "input missing or changed"):
                module.rebuild(Path(temp) / "out")


if __name__ == "__main__":
    unittest.main()
