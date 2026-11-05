"""JE-3000A JP Git-only manual candidate: source identity, verbatim copy, artwork and replay."""
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
PACKAGE = ROOT / "manual_sources/JE-3000A/JP/ja/git-20261103-002fde5a"
SOURCE_SHA = "002fde5a36f8dfc4192a8534e8f43a98e249bfbc491027b7c1b0c819d75e2002"
MARKDOWN = "manual_je3000a_jp_ja.md"
CHAPTERS = ["1.主な仕様", "2.各部の名称", "3.液晶画面", "4.使用について", "5.充電方法",
            "6.安全上のご注意", "7.使用上のご注意", "8.同梱品", "9.免責事項"]


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


class Je3000aJpWebTests(unittest.TestCase):
    def test_identity_and_candidate_status(self):
        manifest = read(PACKAGE / "source_manifest.json")
        self.assertEqual(manifest["target"]["model"], "JE-3000A")
        self.assertEqual((manifest["target"]["region"], manifest["target"]["languages"]), ("JP", ["ja"]))
        self.assertEqual(manifest["target"]["technical_version"], PACKAGE.name)
        self.assertEqual((manifest["route"], manifest["legacy_default"]), ("JE-3000A/JP/ja/md", True))
        self.assertEqual(manifest["original_source"]["sha256"], SOURCE_SHA)
        self.assertEqual(file_sha256(PACKAGE / manifest["original_source"]["filename"]), SOURCE_SHA)
        feishu = manifest["feishu_source"]
        self.assertEqual((feishu["record_id"], feishu["single_language_pdf"]["sha256"]), ("reczz28SfbsHdQ1I", SOURCE_SHA))
        self.assertIn("recorded only", feishu["print_master"]["role"])
        self.assertNotIn("token", json.dumps(feishu).lower())
        eligible = read(PACKAGE / "web/ja/manual.ir.json")["metadata"]["publication_eligible"]
        if manifest["publication_status"] == "operator-authorized-git-only-release":
            self.assertTrue(eligible)
            approval = read(PACKAGE / "source/approval.json")
            self.assertEqual((approval["target"], approval["source_sha256"]), (manifest["target"], SOURCE_SHA))
        else:
            self.assertEqual(manifest["publication_status"], "candidate-pending-operator-review")
            self.assertFalse(eligible)
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
            text = squash(line["text"]).replace("[88H]", "").replace("[LT]", "")
            if text not in page and text not in alts:
                missing.append(line["id"])
        self.assertEqual(missing, [])
        for line in web_lines():
            if line["id"].startswith(("fig.", "names.f.", "names.r.")):
                self.assertIn(squash(line["text"]), alts, line["id"])

    def test_chapters_and_print_only_pages_excluded(self):
        markdown = (PACKAGE / "web/ja" / MARKDOWN).read_text(encoding="utf-8")
        headings = [squash(BeautifulSoup(line, "html.parser").get_text())
                    for line in markdown.splitlines() if line.startswith("## ")]
        # The specification table title is the shared HB-TABLE-SPEC section heading.
        expected = [CHAPTERS[0], "【Jackery ポータブル電源 3000 Pro】", *CHAPTERS[1:]]
        self.assertEqual([h.lstrip("#") for h in headings], [squash(c) for c in expected])
        for print_only in ("国内専用/For use only in Japan", "Jackery-UM-001", "お買い上げありがとうございます"):
            self.assertNotIn(print_only, markdown)

    def test_model_facts_come_from_this_source(self):
        markdown = (PACKAGE / "web/ja" / MARKDOWN).read_text(encoding="utf-8")
        for fact in ("JE-3000A", "70Ah/43.2V DC(3024Wh)", "5ポート合計3000W (瞬間最大6000W)", "20ms(0.020秒)",
                     "最大放電出力は800Wです", "Li-ion 20"):
            self.assertIn(fact, markdown)
        for foreign in ("JE-1000D", "JE-2000A", "JE-1500B", "1070Wh", "Li-ion 32", "ポータブル電源 1000"):
            self.assertNotIn(foreign, markdown)

    def test_assets_and_shared_symbols(self):
        recipe = read(PACKAGE / "source/asset_recipe.json")
        manifest = read(PACKAGE / "source_manifest.json")
        catalog = read(ROOT / "docs/renderers/web/assets/shared/symbols/manifest.json")
        keys = {row["key"]: row for row in catalog["assets"]}
        self.assertNotIn("symbol_admission_blocker", manifest)
        self.assertNotIn("je3000a", json.dumps(catalog).lower())
        for symbol in recipe["symbols"]:
            shared = keys[symbol["shared_symbol_key"]]
            self.assertEqual(shared["path"], symbol["shared_path"])
            self.assertEqual(file_sha256(PACKAGE / symbol["path"]), shared["sha256"])
        for item in recipe["reused"]:
            self.assertEqual(file_sha256(PACKAGE / item["path"]), item["sha256"])
            self.assertEqual(file_sha256(ROOT / item["from"]), item["sha256"])
        markdown = (PACKAGE / "web/ja" / MARKDOWN).read_text(encoding="utf-8")
        refs = {img["src"] for img in BeautifulSoup(markdown, "html.parser").find_all("img")}
        for ref in refs:
            self.assertTrue((PACKAGE / "web/ja" / ref).is_file(), ref)
        admission = manifest["symbol_asset_admission"]["locales"]["ja"]
        self.assertEqual([row["asset_ref"] for row in admission], [s["path"] for s in recipe["symbols"]])
        wet_hands = next(row for row in admission if row["asset_ref"] == "assets/symbol-03.svg")
        self.assertEqual(wet_hands["shared_symbol_key"], "native/je1000d-jp-00c43a89-03")
        for row in admission:
            self.assertTrue(row["max_mean_channel_error"] <= 0.02 or "canonical_group" in row, row["asset_ref"])

    @pre_rowspan_divider_styles
    def test_cold_replay_matches_stored_candidate(self):
        try:
            subprocess.run([resolve_pandoc_binary(None), "--version"], check=True, capture_output=True)
        except (OSError, RuntimeError, subprocess.CalledProcessError):
            self.skipTest("Pandoc unavailable")
        rebuild = load("je3000a_jp_rebuild", PACKAGE / "rebuild.py")
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "replay"
            result = rebuild.rebuild(output)
            self.assertEqual([row["asset_ref"] for row in result["symbol_admission"]],
                             [f"assets/symbol-0{i}.svg" for i in range(1, 7)])
            for name in (MARKDOWN, "manual.ir.json", "_static/source_geometry.css"):
                self.assertEqual((output / name).read_bytes(), (PACKAGE / "web/ja" / name).read_bytes(), name)

    def test_content_is_rebuilt_from_transcription(self):
        builder = load("je3000a_jp_build_content", PACKAGE / "build_content.py")
        built = json.loads(json.dumps(builder.build(), ensure_ascii=False))
        self.assertEqual(built, read(PACKAGE / "source/ja/content.json"))

    def test_changed_source_input_is_rejected(self):
        module = load("je3000a_jp_rebuild_copy", PACKAGE / "rebuild.py")
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "source"
            shutil.copytree(PACKAGE, source, ignore=shutil.ignore_patterns("web", "evidence", "__pycache__"))
            path = source / "source/ja/content.json"
            path.write_text(path.read_text(encoding="utf-8").replace("3024Wh", "3025Wh"), encoding="utf-8")
            module.SOURCE_ROOT = source
            with self.assertRaisesRegex(ValueError, "input missing or changed"):
                module.rebuild(Path(temp) / "out")


if __name__ == "__main__":
    unittest.main()
