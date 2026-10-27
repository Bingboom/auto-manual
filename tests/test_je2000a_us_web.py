"""JE-2000A US en Git-only manual candidate: identity, verbatim copy, artwork and replay."""
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
PACKAGE = ROOT / "manual_sources/JE-2000A/US/en/git-20261027-a8ec2be7"
SOURCE_SHA = "a8ec2be735be6483d340f2f35c7bc13a9300bf7d9499f60099ed8d5ef5cf689f"
MARKDOWN = "manual_je2000a_us_en.md"
CALLOUT_LABELS = {"ops.tip.l", "ex.caution.l", "save.warn.l", "save.danger.l"}
CHAPTERS = ["TECHNICAL SPECIFICATIONS", "PACKAGE LIST", "GET TO KNOW YOUR GEAR", "LCD DISPLAY",
            "BASIC OPERATIONS", "CHARGING YOUR JACKERY EXPLORER 2000 PRO", "CHARGING IN THE CAR",
            "SAFETY PRECAUTIONS WHEN CHARGING", "SAFETY PRECAUTIONS WHEN USING",
            "INSTRUCTIONS PERTAINING TO RISK OF FIRE, ELECTRIC SHOCK, OR INJURY TO PERSONS",
            "FAQ", "TROUBLESHOOTING", "WARRANTY"]
SPEC_GROUPS = ["GENERAL INFO", "OUTPUT PORTS", "INPUT PORTS", "ENVIRONMENTAL OPERATING TEMPERATURE"]


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


def visible_text(value: str) -> str:
    soup = BeautifulSoup(value, "html.parser")
    for node in soup.find_all(["style", "script"]):
        node.decompose()
    return squash(soup.get_text(""))


def web_lines() -> list[dict]:
    pages = read(PACKAGE / "source/transcription.json")["pages"]
    return [line for page in pages if page["web"] for line in page["lines"]]


class Je2000aUsWebTests(unittest.TestCase):
    def test_identity_and_candidate_status(self):
        manifest = read(PACKAGE / "source_manifest.json")
        self.assertEqual(manifest["target"]["model"], "JE-2000A")
        self.assertEqual((manifest["target"]["region"], manifest["target"]["languages"]), ("US", ["en"]))
        self.assertEqual(manifest["target"]["technical_version"], PACKAGE.name)
        self.assertEqual(manifest["target"]["printed_manual_version"], "Version: JAK-UM-V1.0")
        self.assertEqual(manifest["original_source"]["sha256"], SOURCE_SHA)
        self.assertEqual(file_sha256(PACKAGE / manifest["original_source"]["filename"]), SOURCE_SHA)
        self.assertEqual(manifest["feishu_record"]["record_id"], "reczz28SPLqH8cvK")
        self.assertEqual(manifest["feishu_record"]["物料号文本"], "38-0001-000200")
        self.assertFalse(manifest["original_artwork"]["committed"])
        ir = read(PACKAGE / "web/en/manual.ir.json")
        if manifest["publication_status"] == "operator-authorized-git-only-release":
            self.assertTrue(ir["metadata"]["publication_eligible"])
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

    def test_every_web_line_is_selectable_text_or_alt(self):
        page_markdown = markdown()
        page = visible_text(page_markdown)
        soup = BeautifulSoup(page_markdown, "html.parser")
        alts = squash(" ".join(img.get("alt", "") for img in soup.find_all("img")))
        missing = []
        for line in web_lines():
            text = squash(line["text"]).replace("[ICON]", "")
            if line["id"] in CALLOUT_LABELS:
                # The shared callout label slot carries the word without its colon.
                text = text[:-1]
            if text not in page and text not in alts:
                missing.append(line["id"])
        self.assertEqual(missing, [])
        for line in web_lines():
            if line["id"].startswith("fig."):
                self.assertIn(squash(line["text"]), alts, line["id"])

    def test_source_typos_are_kept_verbatim(self):
        page = visible_text(markdown())
        for printed in ("Technologles,Inc.", "MOVINANDSTORAGEINSTRUCTIONS", "“OUPUT”", "applicablewarranty",
                        "turnoff，while", "1~2seconds", "SolarSaga200×3"):
            self.assertIn(squash(printed), page + squash(" ".join(
                img.get("alt", "") for img in BeautifulSoup(markdown(), "html.parser").find_all("img"))), printed)

    def test_chapters_and_print_only_pages_excluded(self):
        headings = [squash(BeautifulSoup(line, "html.parser").get_text()).lstrip("#")
                    for line in markdown().splitlines() if line.startswith("## ")]
        # Each specification group title is a shared HB-TABLE-SPEC section heading.
        expected = [CHAPTERS[0], *SPEC_GROUPS, *CHAPTERS[1:]]
        self.assertEqual(headings, [squash(c) for c in expected])
        for print_only in ("USER MANUAL", "JAK-UM-V1.0", "Contact us:", "5310 Bunche Dr", "JACKERY INC."):
            self.assertNotIn(print_only, markdown())

    def test_model_facts_come_from_this_source(self):
        page = markdown()
        for fact in ("JE-2000A", "Lithium-ion 50Ah / 43.2V (2160Wh)", "2200W Rated output, 4400W Surge peak",
                     "Double to 24A/1400W Max", "36 months", "J2000P-UM-001"):
            self.assertIn(fact, page)
        for foreign in ("JE-1500B", "JE-1500D", "JE-1000D", "1500 Pro", "1000 Pro", "1512Wh", "LiFePO"):
            self.assertNotIn(foreign, page)

    def test_assets_reuse_and_symbol_admission(self):
        recipe = read(PACKAGE / "source/asset_recipe.json")
        manifest = read(PACKAGE / "source_manifest.json")
        catalog = read(ROOT / "docs/renderers/web/assets/shared/symbols/manifest.json")
        keys = {row["key"]: row for row in catalog["assets"]}
        for symbol in recipe["symbols"]:
            if symbol.get("reuse"):
                self.assertEqual(file_sha256(PACKAGE / symbol["path"]), keys[symbol["shared_symbol_key"]]["sha256"])
        for item in recipe["reused"]:
            self.assertEqual(file_sha256(PACKAGE / item["path"]), item["sha256"])
            self.assertEqual(file_sha256(ROOT / item["from"]), item["sha256"])
        decisions = {row.get("final_path"): row["sha256"] for row in read(PACKAGE / "source/asset_decisions.json")
                     if row.get("final_path")}
        for path in (PACKAGE / "assets").rglob("*.png"):
            relative = path.relative_to(PACKAGE).as_posix()
            self.assertEqual(decisions.get(relative), file_sha256(path), relative)
        for icon in recipe["native_icons"]:
            from PIL import Image
            with Image.open(PACKAGE / icon["path"]) as image:
                self.assertEqual(image.mode, "RGBA", icon["path"])
                self.assertEqual(image.getchannel("A").getextrema()[0], 0, icon["path"])
        refs = {img["src"] for img in BeautifulSoup(markdown(), "html.parser").find_all("img")}
        for ref in refs:
            self.assertTrue((PACKAGE / "web/en" / ref).is_file(), ref)
        self.assertEqual(manifest["symbol_asset_admission"]["locales"]["en"], [])
        tables = {row["page_id"] for row in manifest["shared_component_exceptions"]}
        self.assertEqual(tables, {"lcd_display", "troubleshooting"})

    def test_no_feishu_tokens_recorded(self):
        for path in [PACKAGE / "README.md", PACKAGE / "source_manifest.json", *(PACKAGE / "source").rglob("*.md")]:
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("obj_token", text, path)
            self.assertNotIn("file_token", text, path)

    def test_cold_replay_matches_stored_candidate(self):
        try:
            subprocess.run([resolve_pandoc_binary(None), "--version"], check=True, capture_output=True)
        except (OSError, RuntimeError, subprocess.CalledProcessError):
            self.skipTest("Pandoc unavailable")
        rebuild = load("je2000a_us_rebuild", PACKAGE / "rebuild.py")
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "replay"
            rebuild.rebuild(output)
            for name in (MARKDOWN, "manual.ir.json", "_static/source_geometry.css"):
                self.assertEqual((output / name).read_bytes(), (PACKAGE / "web/en" / name).read_bytes(), name)

    def test_content_is_rebuilt_from_transcription(self):
        builder = load("je2000a_us_build_content", PACKAGE / "build_content.py")
        built = json.loads(json.dumps(builder.build(), ensure_ascii=False))
        self.assertEqual(built, read(PACKAGE / "source/en/content.json"))

    def test_changed_source_input_is_rejected(self):
        module = load("je2000a_us_rebuild_copy", PACKAGE / "rebuild.py")
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "source"
            shutil.copytree(PACKAGE, source, ignore=shutil.ignore_patterns("web", "evidence", "__pycache__"))
            path = source / "source/en/content.json"
            path.write_text(path.read_text(encoding="utf-8").replace("2160Wh", "2161Wh"), encoding="utf-8")
            module.SOURCE_ROOT = source
            with self.assertRaisesRegex(ValueError, "input missing or changed"):
                module.rebuild(Path(temp) / "out")


if __name__ == "__main__":
    unittest.main()
