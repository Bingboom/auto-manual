"""JE-3000B US en Git-only manual candidate: source identity, verbatim copy, artwork and replay."""
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
PACKAGE = ROOT / "manual_sources/JE-3000B/US/en/git-20261028-bd8a8296"
SOURCE_SHA = "bd8a82962865ae64cd52e9c6ebf9a20d8495652773ba09806d1911cb0f360294"
MARKDOWN = "manual_je3000b_us_en.md"
PRINT_ONLY = {"pre.badge"}
# The shared callout label slot carries these printed run-in labels without their colon.
CALLOUT_LABELS = {"safety.warn.label", "ground.warn.label", "op.warn.label", "danger.label"}
CHAPTERS = ["IMPORTANT SAFETY INFORMATION", "WHAT'S IN THE BOX", "PRODUCT OVERVIEW", "LCD DISPLAY",
            "BASIC OPERATIONS", "TROUBLESHOOTING", "UPS", "CHARGING", "WARRANTY", "APP SETUP", "SPECIFICATIONS",
            "GENERAL INFO", "INPUT PORTS", "OUTPUT PORTS", "ENVIRONMENTAL OPERATING TEMPERATURE"]


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


def markdown() -> str:
    return (PACKAGE / "web/en" / MARKDOWN).read_text(encoding="utf-8")


def visible_text(source: str) -> str:
    soup = BeautifulSoup(source, "html.parser")
    for node in soup.find_all(["style", "script"]):
        node.decompose()
    return squash(soup.get_text(""))


def web_lines() -> list[dict]:
    pages = read(PACKAGE / "source/transcription.json")["pages"]
    return [line for page in pages if page["web"] for line in page["lines"] if line["id"] not in PRINT_ONLY]


class Je3000bUsWebTests(unittest.TestCase):
    def test_identity_and_candidate_status(self):
        manifest = read(PACKAGE / "source_manifest.json")
        self.assertEqual(manifest["target"]["model"], "JE-3000B")
        self.assertEqual((manifest["target"]["region"], manifest["target"]["languages"]), ("US", ["en"]))
        self.assertEqual(manifest["target"]["technical_version"], PACKAGE.name)
        self.assertEqual(manifest["route"], "JE-3000B/US/en/md")
        self.assertEqual(manifest["original_source"]["sha256"], SOURCE_SHA)
        self.assertEqual(file_sha256(PACKAGE / manifest["original_source"]["filename"]), SOURCE_SHA)
        self.assertEqual(manifest["base_record"]["record_id"], "reczz28SlRGJim2Y")
        self.assertEqual(manifest["base_record"]["material_number"], "16-0102-000056")
        self.assertFalse(manifest["design_original"]["stored_in_package"])
        ir = read(PACKAGE / "web/en/manual.ir.json")
        if manifest["publication_status"] == "operator-authorized-git-only-release":
            self.assertTrue(ir["metadata"]["publication_eligible"])
        else:
            self.assertEqual(manifest["publication_status"], "candidate-pending-operator-review")
            self.assertFalse(manifest["publication_eligible"])
            self.assertFalse(ir["metadata"]["publication_eligible"])
            self.assertFalse((PACKAGE / "source/approval.json").exists())

    def test_no_feishu_tokens_are_recorded(self):
        for path in PACKAGE.rglob("*"):
            if path.suffix in {".json", ".md", ".py"} and "web" not in path.relative_to(PACKAGE).parts:
                text = path.read_text(encoding="utf-8")
                for marker in ("obj_token", "file_token", "attachmentToken", "feishu.cn/file", "feishu.cn/wiki"):
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
        page_markdown = markdown()
        page = visible_text(page_markdown)
        soup = BeautifulSoup(page_markdown, "html.parser")
        alts = squash(" ".join(img.get("alt", "") for img in soup.find_all("img")))
        missing = []
        for line in web_lines():
            text = squash(line["text"]).replace("[+]", "+")
            if line["id"] in CALLOUT_LABELS:
                text = text[:-1]
            if text not in page and text not in alts:
                missing.append(line["id"])
        self.assertEqual(missing, [])
        for line in web_lines():
            if line["id"].startswith(("fig.", "names.f.", "names.r.")):
                self.assertIn(squash(line["text"]), alts, line["id"])

    def test_chapters_and_print_only_pages_excluded(self):
        page_markdown = markdown()
        headings = [squash(BeautifulSoup(line, "html.parser").get_text())
                    for line in page_markdown.splitlines() if line.startswith("## ")]
        self.assertEqual([h.lstrip("#") for h in headings], [squash(c) for c in CHAPTERS])
        for print_only in ("TABLE OF CONTENTS", "5310 Bunche Dr.", "JACKERY INC.", "1-888-502-2236",
                           "CONTACT US:"):
            self.assertNotIn(print_only, page_markdown)

    def test_model_facts_come_from_this_source(self):
        page = visible_text(markdown())
        for fact in ("JE-3000B", "60Ah / 51.2Vdc (3072Wh)", "4000 cycles to 70%+ capacity", "About 59.52lbs / 27kg",
                     "120V~ 60Hz, 12A Max, 1440W", "3600W Max, 7200W surge peak", "within 20 ms",
                     "Jackery Explorer 3000 is 36 months", "BMS or battery failuare", "-15℃ to -10℃(5°F to 14°F)"):
            self.assertIn(squash(fact), page)
        for foreign in ("JE-1500D", "JE-3000C", "1536 Wh", "Explorer 1500", "within 10 ms", "ポータブル電源"):
            self.assertNotIn(squash(foreign), page)

    def test_assets_and_reuse(self):
        recipe = read(PACKAGE / "source/asset_recipe.json")
        manifest = read(PACKAGE / "source_manifest.json")
        catalog = read(ROOT / "docs/renderers/web/assets/shared/symbols/manifest.json")
        keys = {row["key"]: row for row in catalog["assets"]}
        mark = recipe["fcc_mark"]
        self.assertEqual(file_sha256(PACKAGE / mark["path"]), keys[mark["shared_symbol_key"]]["sha256"])
        for item in recipe["reused"]:
            self.assertEqual(file_sha256(PACKAGE / item["path"]), item["sha256"])
            self.assertEqual(file_sha256(ROOT / item["from"]), item["sha256"])
        rows = manifest["artwork_reuse_comparison"]
        self.assertEqual([r["asset_ref"] for r in rows], [i["path"] for i in recipe["reused"]] + [mark["path"]])
        self.assertTrue(all(r["max_mean_channel_error"] <= 0.02 for r in rows))
        self.assertEqual(recipe["symbols"], [])
        self.assertEqual(manifest["symbol_asset_admission"]["locales"]["en"], [])
        refs = {img["src"] for img in BeautifulSoup(markdown(), "html.parser").find_all("img")}
        for ref in refs:
            self.assertTrue((PACKAGE / "web/en" / ref).is_file(), ref)
        decisions = {row["final_path"] for row in read(PACKAGE / "source/asset_decisions.json")}
        stored = {p.relative_to(PACKAGE).as_posix() for p in (PACKAGE / "assets").rglob("*") if p.is_file()}
        self.assertEqual(decisions, stored)

    def test_no_package_styles(self):
        css = (PACKAGE / "source/geometry.css").read_text(encoding="utf-8")
        for word in ("color", "background", "border", "fill", "stroke", "shadow", "outline"):
            self.assertNotIn(word, css)
        exceptions = read(PACKAGE / "source_manifest.json")["shared_component_exceptions"]
        self.assertEqual([(e["page_id"], e["kind"]) for e in exceptions], [("troubleshooting", "table")])
        self.assertTrue(all(e["reason"] for e in exceptions))

    def test_cold_replay_matches_stored_candidate(self):
        try:
            subprocess.run([resolve_pandoc_binary(None), "--version"], check=True, capture_output=True)
        except (OSError, RuntimeError, subprocess.CalledProcessError):
            self.skipTest("Pandoc unavailable")
        rebuild = load("je3000b_us_rebuild", PACKAGE / "rebuild.py")
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "replay"
            rebuild.rebuild(output)
            for name in (MARKDOWN, "manual.ir.json", "_static/source_geometry.css", "conf.py"):
                self.assertEqual((output / name).read_bytes(), (PACKAGE / "web/en" / name).read_bytes(), name)

    def test_content_is_rebuilt_from_transcription(self):
        builder = load("je3000b_us_build_content", PACKAGE / "build_content.py")
        built = json.loads(json.dumps(builder.build(), ensure_ascii=False))
        self.assertEqual(built, read(PACKAGE / "source/en/content.json"))

    def test_changed_source_input_is_rejected(self):
        module = load("je3000b_us_rebuild_copy", PACKAGE / "rebuild.py")
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "source"
            shutil.copytree(PACKAGE, source, ignore=shutil.ignore_patterns("web", "evidence", "__pycache__"))
            path = source / "source/en/content.json"
            path.write_text(path.read_text(encoding="utf-8").replace("3072Wh", "3073Wh"), encoding="utf-8")
            module.SOURCE_ROOT = source
            with self.assertRaisesRegex(ValueError, "input missing or changed"):
                module.rebuild(Path(temp) / "out")


if __name__ == "__main__":
    unittest.main()
