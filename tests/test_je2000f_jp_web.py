"""JE-2000F JP Git-only candidate: source identity, verbatim copy, artwork and replay."""
from __future__ import annotations

from collections import Counter
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from tests.historical_web_inputs import historical_shared_inputs

from bs4 import BeautifulSoup
import fitz

from tools.manual_ir.hashing import file_sha256
from tools.word.bundle_docx_pandoc import resolve_pandoc_binary
from tests.historical_app_styles import pre_rowspan_divider_styles

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "manual_sources/JE-2000F/JP/ja/git-20261103-63cdf705"
SOURCE_SHA = "63cdf705e41a1680ca974cc69e5f233cd0e5e4d278d5cc5302dcb3389b361393"
MARKDOWN = "manual_je2000f_jp_ja.md"
CHAPTERS = ["安全上のご注意", "使用上のご注意", "免責事項", "同梱品", "各部の名称", "液晶画面", "使い方", "UPS 機能",
            "充電方法", "トラブルシューティング", "主な仕様", "基本情報", "入力ポート", "出カポート", "温度範囲",
            "保証について", "Jackeryアプリ ユーザーマニュアル"]
LIST_MARKERS = ("• ", "◦ ")


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


def transcription() -> dict:
    return read(PACKAGE / "source/transcription.json")


def web_lines() -> list[dict]:
    return [line for page in transcription()["pages"] if page["web"] for line in page["lines"]]


@historical_shared_inputs
class Je2000fJpWebTests(unittest.TestCase):
    def test_identity_and_candidate_status(self):
        manifest = read(PACKAGE / "source_manifest.json")
        self.assertEqual(manifest["target"]["model"], "JE-2000F")
        self.assertEqual((manifest["target"]["region"], manifest["target"]["languages"]), ("JP", ["ja"]))
        self.assertEqual(manifest["target"]["technical_version"], PACKAGE.name)
        self.assertEqual(manifest["route"], "JE-2000F/JP/ja/md")
        self.assertEqual(manifest["feishu_source"]["customer_model"], "JE-2000F-WH")
        self.assertIn("voided", manifest["earlier_candidate"])
        self.assertEqual(manifest["original_source"]["sha256"], SOURCE_SHA)
        self.assertEqual(file_sha256(PACKAGE / manifest["original_source"]["filename"]), SOURCE_SHA)
        self.assertEqual(manifest["feishu_source"]["record_id"], "reczz28SfbsHbLFx")
        self.assertFalse(manifest["feishu_source"]["print_master"]["stored_in_package"])
        self.assertNotIn("supersedes_candidate", manifest)
        ir = read(PACKAGE / "web/ja/manual.ir.json")
        if manifest["publication_status"] == "operator-authorized-git-only-release":
            self.assertTrue(ir["metadata"]["publication_eligible"])
        else:
            self.assertEqual(manifest["publication_status"], "candidate-pending-operator-review")
            self.assertFalse(ir["metadata"]["publication_eligible"])
            self.assertFalse((PACKAGE / "source/approval.json").exists())

    def test_no_feishu_tokens_recorded(self):
        text = (PACKAGE / "source_manifest.json").read_text(encoding="utf-8")
        for marker in ("file_token", "obj_token", "attachment_token"):
            self.assertNotIn(marker, text)

    def test_inputs_are_pinned(self):
        manifest = read(PACKAGE / "source_manifest.json")
        for row in manifest["inputs"]:
            self.assertEqual(file_sha256(PACKAGE / row["path"]), row["sha256"], row["path"])
        listed = {row["path"] for row in manifest["inputs"]}
        for folder in ("source", "assets"):
            for path in (PACKAGE / folder).rglob("*"):
                if path.is_file():
                    self.assertIn(path.relative_to(PACKAGE).as_posix(), listed)

    def test_transcription_matches_the_pdf_text_layer(self):
        def bag(value: str) -> Counter:
            return Counter(c for c in value if not c.isspace() and c not in "•◦")
        with fitz.open(PACKAGE / "JE-2000F-JP-JA.pdf") as doc:
            for page in transcription()["pages"]:
                ours = Counter()
                for line in page["lines"]:
                    ours += bag(line["text"].replace("[88H]", "").replace("[+]", ""))
                for row in page["print_only"]:
                    if "outlined" not in row["text"]:
                        ours += bag(row["text"])
                source = bag(doc[page["physical_page"] - 1].get_text())
                if page["physical_page"] == 2:
                    source = Counter({k: v for k, v in source.items() if k != "."})
                self.assertEqual(ours, source, page["physical_page"])

    def test_every_web_line_is_selectable_text_in_the_page(self):
        markdown = (PACKAGE / "web/ja" / MARKDOWN).read_text(encoding="utf-8")
        page = visible_text(markdown)
        soup = BeautifulSoup(markdown, "html.parser")
        alts = squash(" ".join(img.get("alt", "") for img in soup.find_all("img")))
        missing = []
        for line in web_lines():
            value = line["text"]
            for marker in LIST_MARKERS:
                if value.startswith(marker):
                    value = value[len(marker):]
            value = squash(value).replace("[88H]", "88H").replace("[+]", "+")
            if value not in page and value.replace("88H", "") not in page and value not in alts:
                missing.append(line["id"])
        self.assertEqual(missing, [])
        for line in web_lines():
            if line["id"].startswith(("fig.", "ov.f.", "ov.r.")):
                self.assertIn(squash(line["text"]), alts, line["id"])

    def test_chapters_and_print_only_pages_excluded(self):
        markdown = (PACKAGE / "web/ja" / MARKDOWN).read_text(encoding="utf-8")
        headings = [squash(BeautifulSoup(line, "html.parser").get_text()).lstrip("#")
                    for line in markdown.splitlines() if line.startswith("## ")]
        self.assertEqual(headings, [squash(c) for c in CHAPTERS])
        for print_only in ("国内専用/For use only in Japan", "目次", "写真はイメージです",
                           "スマートコントロールに対応しています"):
            self.assertNotIn(print_only, markdown)

    def test_model_facts_come_from_this_source(self):
        markdown = (PACKAGE / "web/ja" / MARKDOWN).read_text(encoding="utf-8")
        for fact in ("JE-2000F / JE-2000F-SG / JE-2000F-WH", "2048Wh (40Ah/51.2V DC)", "約10 ミリ秒（0.010 秒）",
                     "瞬間最大4400W", "Jackery ポータブル電源 2000 New"):
            self.assertIn(fact, markdown)
        for foreign in ("Explorer 2000 Plus", "HomePower", "1070Wh", "JE-1000D", "JE-1500D", "1500 New"):
            self.assertNotIn(foreign, markdown)

    def test_assets_and_shared_symbols(self):
        recipe = read(PACKAGE / "source/asset_recipe.json")
        catalog = read(ROOT / "docs/renderers/web/assets/shared/symbols/manifest.json")
        keys = {row["key"]: row for row in catalog["assets"]}
        for symbol in recipe["symbols"]:
            shared = keys[symbol["shared_symbol_key"]]
            self.assertEqual(shared["path"], symbol["shared_path"])
            self.assertEqual(file_sha256(PACKAGE / symbol["path"]), shared["sha256"])
        for item in recipe["reused"] + recipe["compared_reuse"]:
            self.assertNotIn("d10ae5e0", item["from"])  # the voided earlier candidate is being removed
            self.assertEqual(file_sha256(PACKAGE / item["path"]), item["sha256"])
            self.assertEqual(file_sha256(ROOT / item["from"]), item["sha256"])
        markdown = (PACKAGE / "web/ja" / MARKDOWN).read_text(encoding="utf-8")
        refs = {img["src"] for img in BeautifulSoup(markdown, "html.parser").find_all("img")}
        for ref in refs:
            self.assertTrue((PACKAGE / "web/ja" / ref).is_file(), ref)
        manifest = read(PACKAGE / "source_manifest.json")
        admission = manifest["symbol_asset_admission"]["locales"]["ja"]
        self.assertEqual([row["asset_ref"] for row in admission], [s["path"] for s in recipe["symbols"]])
        reuse = manifest["operator_symbol_reuse"]
        self.assertEqual([row["asset_ref"] for row in reuse], ["assets/recycle-li-ion.svg"])
        self.assertEqual(file_sha256(PACKAGE / "assets/recycle-li-ion.svg"), reuse[0]["shared_sha256"])
        self.assertEqual(file_sha256(ROOT / reuse[0]["shared_path"]), reuse[0]["shared_sha256"])
        self.assertNotIn("pending_shared_symbols", manifest)

    @pre_rowspan_divider_styles
    def test_cold_replay_matches_stored_candidate(self):
        try:
            subprocess.run([resolve_pandoc_binary(None), "--version"], check=True, capture_output=True)
        except (OSError, RuntimeError, subprocess.CalledProcessError):
            self.skipTest("Pandoc unavailable")
        rebuild = load("je2000f_jp_rebuild", PACKAGE / "rebuild.py")
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "replay"
            rebuild.rebuild(output)
            for name in (MARKDOWN, "manual.ir.json", "_static/source_geometry.css"):
                self.assertEqual((output / name).read_bytes(), (PACKAGE / "web/ja" / name).read_bytes(), name)

    def test_content_is_rebuilt_from_transcription(self):
        builder = load("je2000f_jp_build_content", PACKAGE / "build_content.py")
        built = json.loads(json.dumps(builder.build(), ensure_ascii=False))
        self.assertEqual(built, read(PACKAGE / "source/ja/content.json"))

    def test_changed_source_input_is_rejected(self):
        module = load("je2000f_jp_rebuild_copy", PACKAGE / "rebuild.py")
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "source"
            shutil.copytree(PACKAGE, source, ignore=shutil.ignore_patterns("web", "evidence", "__pycache__"))
            path = source / "source/ja/content.json"
            path.write_text(path.read_text(encoding="utf-8").replace("2048Wh", "2049Wh"), encoding="utf-8")
            module.SOURCE_ROOT = source
            with self.assertRaisesRegex(ValueError, "input missing or changed"):
                module.rebuild(Path(temp) / "out")


if __name__ == "__main__":
    unittest.main()
