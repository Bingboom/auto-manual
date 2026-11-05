"""JE-1500B JP Git-only manual candidate: source identity, verbatim copy, artwork and replay."""
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
from tests.historical_app_styles import pre_rowspan_divider_styles

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "manual_sources/JE-1500B/JP/ja/git-20261103-f61d0d68"
SOURCE_SHA = "f61d0d68f37c32ceb7441d0853da40ad1087e7241a4bf925089d86f8074b0a65"
MARKDOWN = "manual_je1500b_jp_ja.md"
# Printed run-in signal words become the shared callout label without the colon.
CALLOUT_LINES = {"solar.caution", "tj.note"}
# 「名称（[LCD]）：」 titles: the bracketed glyph is the HB-TABLE-LCD-ICON row icon.
LCD_TITLES = {"lcd.ring.t", "lcd.lowbat.t", "lcd.lpm.t", "lcd.fault.t", "chg.hot.t", "chg.cold.t"}
PENDING = {"symbols.h", "sym.unplug", "sym.mandatory", "sym.disassemble", "sym.wet", "sym.wethand", "sym.prohibit"}
CHAPTERS = ["1.主な仕様", "2.各部の名称", "3.液晶画面", "4.使用について", "5.充電方法", "6.安全上のご注意",
            "7.使用上のご注意", "8.同梱品", "9.免責事項"]


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


class Je1500bJpWebTests(unittest.TestCase):
    def test_identity_and_candidate_status(self):
        manifest = read(PACKAGE / "source_manifest.json")
        self.assertEqual(manifest["target"]["model"], "JE-1500B")
        self.assertEqual((manifest["target"]["region"], manifest["target"]["languages"]), ("JP", ["ja"]))
        self.assertEqual(manifest["target"]["technical_version"], PACKAGE.name)
        self.assertEqual(manifest["original_source"]["sha256"], SOURCE_SHA)
        self.assertEqual(manifest["original_source"]["operator_filename"], "【Jackery ポータブル電源 1500 Pro】说明书-JP.pdf")
        self.assertEqual(file_sha256(PACKAGE / manifest["original_source"]["filename"]), SOURCE_SHA)
        self.assertEqual(manifest["feishu_record"]["record_id"], "reczz28SfbsHeofK")
        self.assertEqual(manifest["feishu_record"]["子物料编码"], "38-0001-000276")
        self.assertEqual(manifest["original_artwork"]["operator_filename"],
                         "38-0001-000276 说明书 HTE0801500B-JP-JAK  RoHS REACH.ai")
        self.assertFalse(manifest["original_artwork"]["committed"])
        ir = read(PACKAGE / "web/ja/manual.ir.json")
        if manifest["publication_status"] == "operator-authorized-git-only-release":
            self.assertTrue(manifest["publication_eligible"])
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

    def test_every_web_line_is_selectable_text_in_the_page(self):
        markdown = (PACKAGE / "web/ja" / MARKDOWN).read_text(encoding="utf-8")
        page = visible_text(markdown)
        soup = BeautifulSoup(markdown, "html.parser")
        alts = squash(" ".join(img.get("alt", "") for img in soup.find_all("img")))
        missing = []
        for line in web_lines():
            if line["id"] in PENDING:
                continue
            value = squash(line["text"])
            if line["id"] in CALLOUT_LINES:
                value = value.replace("：", "", 1)
            if line["id"] in LCD_TITLES:
                value = value.split("（[LCD]）", 1)[0]
            if value not in page and value not in alts:
                missing.append(line["id"])
        self.assertEqual(missing, [])
        for line in web_lines():
            if line["id"].startswith(("fig.", "names.")) and line["id"] != "names.h":
                self.assertIn(squash(line["text"]), alts, line["id"])

    def test_pending_symbol_table_is_left_out(self):
        markdown = (PACKAGE / "web/ja" / MARKDOWN).read_text(encoding="utf-8")
        self.assertNotIn("HB-TABLE-SYMBOL-ICON", markdown)
        for line in web_lines():
            if line["id"] in PENDING:
                self.assertNotIn(squash(line["text"]), visible_text(markdown), line["id"])
        recipe = read(PACKAGE / "source/asset_recipe.json")
        self.assertEqual(recipe["symbols"], [])
        self.assertEqual({row["caption_id"] for row in recipe["pending_symbols"]}, PENDING - {"symbols.h"})

    def test_chapters_and_print_only_pages_excluded(self):
        markdown = (PACKAGE / "web/ja" / MARKDOWN).read_text(encoding="utf-8")
        headings = [squash(BeautifulSoup(line, "html.parser").get_text()).lstrip("#")
                    for line in markdown.splitlines() if line.startswith("## ")]
        # The specification table title is the shared HB-TABLE-SPEC section heading.
        expected = [CHAPTERS[0], "【Jackery ポータブル電源 1500 Pro】", *CHAPTERS[1:]]
        self.assertEqual(headings, [squash(c) for c in expected])
        for print_only in ("国内専用/For use only in Japan", "Jackery-UM-002", "お買い上げありがとうございます",
                           "jackery.jp@jackery.com"):
            self.assertNotIn(print_only, markdown)

    def test_model_facts_come_from_this_source(self):
        markdown = (PACKAGE / "web/ja" / MARKDOWN).read_text(encoding="utf-8")
        for fact in ("JE-1500B", "リチウムイオン電池35Ah/43.2V DC (1512Wh)", "3ポート合計1800W (瞬間最大3600W)",
                     "2ポート電流制限24A, 合計1400W", "高温（40°C以上）", "12時間後に自動的にシャットダウンします"):
            self.assertIn(fact, markdown)
        for foreign in ("JE-1000D", "JE-1500D", "1070Wh", "1536Wh", "LiFePO", "45°C以上", "Explorer 1500 Pro"):
            self.assertNotIn(foreign, markdown)

    def test_assets_and_symbol_admission(self):
        recipe = read(PACKAGE / "source/asset_recipe.json")
        for item in recipe["reused"]:
            self.assertEqual(file_sha256(PACKAGE / item["path"]), item["sha256"])
            self.assertEqual(file_sha256(ROOT / item["from"]), item["sha256"])
        decisions = {row["final_path"]: row["sha256"] for row in read(PACKAGE / "source/asset_decisions.json")
                     if row.get("final_path")}
        for path in (PACKAGE / "assets").rglob("*"):
            if path.is_file():
                self.assertEqual(decisions[path.relative_to(PACKAGE).as_posix()], file_sha256(path))
        markdown = (PACKAGE / "web/ja" / MARKDOWN).read_text(encoding="utf-8")
        refs = {img["src"] for img in BeautifulSoup(markdown, "html.parser").find_all("img")}
        for ref in refs:
            self.assertTrue((PACKAGE / "web/ja" / ref).is_file(), ref)
        admission = read(PACKAGE / "source_manifest.json")["symbol_asset_admission"]
        self.assertEqual(admission["locales"], {"ja": []})

    @pre_rowspan_divider_styles
    def test_cold_replay_matches_stored_candidate(self):
        try:
            subprocess.run([resolve_pandoc_binary(None), "--version"], check=True, capture_output=True)
        except (OSError, RuntimeError, subprocess.CalledProcessError):
            self.skipTest("Pandoc unavailable")
        rebuild = load("je1500b_jp_rebuild", PACKAGE / "rebuild.py")
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "replay"
            rebuild.rebuild(output)
            for name in (MARKDOWN, "manual.ir.json", "_static/source_geometry.css"):
                self.assertEqual((output / name).read_bytes(), (PACKAGE / "web/ja" / name).read_bytes(), name)

    def test_content_is_rebuilt_from_transcription(self):
        builder = load("je1500b_jp_build_content", PACKAGE / "build_content.py")
        built = json.loads(json.dumps(builder.build(), ensure_ascii=False))
        self.assertEqual(built, read(PACKAGE / "source/ja/content.json"))

    def test_changed_source_input_is_rejected(self):
        module = load("je1500b_jp_rebuild_copy", PACKAGE / "rebuild.py")
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "source"
            shutil.copytree(PACKAGE, source, ignore=shutil.ignore_patterns("web", "evidence", "__pycache__"))
            path = source / "source/ja/content.json"
            path.write_text(path.read_text(encoding="utf-8").replace("1512Wh", "1513Wh"), encoding="utf-8")
            module.SOURCE_ROOT = source
            with self.assertRaisesRegex(ValueError, "input missing or changed"):
                module.rebuild(Path(temp) / "out")


if __name__ == "__main__":
    unittest.main()
