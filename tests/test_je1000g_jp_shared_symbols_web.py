"""JE-1000G JP V3 shared-symbol follow-up: every symbol row binds its confirmed canonical, replay."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from tests.historical_web_inputs import historical_shared_inputs

from bs4 import BeautifulSoup

from tools.manual_ir.hashing import file_sha256
from tools.word.bundle_docx_pandoc import resolve_pandoc_binary
from tests.historical_app_styles import pre_rowspan_divider_styles

ROOT = Path(__file__).resolve().parents[1]
JP = ROOT / "manual_sources/JE-1000G/JP/ja"
PACKAGE = JP / "git-20261103-6cf12013-shared-symbols"
BASE = JP / "git-20261103-6cf12013"
SOURCE_SHA = "6cf120136d8366ad37f590610d739e09754ddc38d4c8cd3123d9dca0de132aad"
MARKDOWN = "manual_je1000g_jp_ja.md"
CHAPTERS = ["安全上のご注意", "使用上のご注意", "免責事項", "同梱品", "各部の名称", "液晶画面", "使い方", "UPS 機能",
            "充電方法", "トラブルシューティング", "主な仕様", "基本情報", "入力ポート", "出カポート", "温度範囲",
            "保証について", "Jackeryアプリ ユーザーマニュアル"]


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


@historical_shared_inputs
class Je1000gJpSharedSymbolsWebTests(unittest.TestCase):
    def test_identity_and_candidate_status(self):
        manifest = read(PACKAGE / "source_manifest.json")
        self.assertEqual(manifest["target"]["model"], "JE-1000G")
        self.assertEqual((manifest["target"]["region"], manifest["target"]["languages"]), ("JP", ["ja"]))
        self.assertEqual(manifest["target"]["technical_version"], PACKAGE.name)
        self.assertEqual(manifest["original_source"]["sha256"], SOURCE_SHA)
        self.assertEqual(file_sha256(PACKAGE / manifest["original_source"]["filename"]), SOURCE_SHA)
        self.assertEqual(manifest["base_record"]["record_id"], "reczz28SfbsHbQU5")
        self.assertFalse(manifest["design_original"]["stored_in_package"])
        ir = read(PACKAGE / "web/ja/manual.ir.json")
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
        markdown = (PACKAGE / "web/ja" / MARKDOWN).read_text(encoding="utf-8")
        page = visible_text(markdown)
        soup = BeautifulSoup(markdown, "html.parser")
        alts = squash(" ".join(img.get("alt", "") for img in soup.find_all("img")))
        missing = []
        for line in web_lines():
            value = squash(line["text"]).replace("[88H]", "").replace("[+]", "+")
            if value not in page and value not in alts:
                missing.append(line["id"])
        self.assertEqual(missing, [])
        for line in web_lines():
            if line["id"].startswith(("fig.", "ov.")):
                self.assertIn(squash(line["text"]), alts, line["id"])

    def test_chapters_and_print_only_pages_excluded(self):
        markdown = (PACKAGE / "web/ja" / MARKDOWN).read_text(encoding="utf-8")
        headings = [squash(BeautifulSoup(line, "html.parser").get_text())
                    for line in markdown.splitlines() if line.startswith("## ")]
        self.assertEqual([h.lstrip("#") for h in headings], [squash(c) for c in CHAPTERS])
        for print_only in ("国内専用/For use only in Japan", "目次", "写真はイメージです", "アプリケーションによるスマ"):
            self.assertNotIn(print_only, markdown)

    def test_model_facts_come_from_this_source(self):
        markdown = (PACKAGE / "web/ja" / MARKDOWN).read_text(encoding="utf-8")
        for fact in ("JE-1000G / JE-1000G-WH", "1024Wh (20Ah/51.2V DC)", "約10 ミリ秒（0.010 秒）以内",
                     "1500W，瞬間最大3000W", "050-3198-9007"):
            self.assertIn(fact, markdown)
        for foreign in ("JE-1000F", "JE-1000D", "1070Wh", "20ms", "JE-1000H", "1000 Plus"):
            self.assertNotIn(foreign, markdown)

    def test_assets_and_shared_symbols(self):
        recipe = read(PACKAGE / "source/asset_recipe.json")
        catalog = read(ROOT / "docs/renderers/web/assets/shared/symbols/manifest.json")
        keys = {row["key"]: row for row in catalog["assets"]}
        for symbol in recipe["symbols"]:
            shared = keys[symbol["shared_symbol_key"]]
            self.assertEqual(shared["path"], symbol["shared_path"])
            self.assertEqual(file_sha256(PACKAGE / symbol["path"]), shared["sha256"])
        for item in [*recipe["reused"], *recipe["compared_reuse"]]:
            self.assertEqual(file_sha256(PACKAGE / item["path"]), item["sha256"])
            self.assertEqual(file_sha256(ROOT / item["from"]), item["sha256"])
        markdown = (PACKAGE / "web/ja" / MARKDOWN).read_text(encoding="utf-8")
        refs = {img["src"] for img in BeautifulSoup(markdown, "html.parser").find_all("img")}
        for ref in refs:
            self.assertTrue((PACKAGE / "web/ja" / ref).is_file(), ref)
        admission = read(PACKAGE / "source_manifest.json")["symbol_asset_admission"]["locales"]["ja"]
        self.assertEqual([row["asset_ref"] for row in admission], [s["path"] for s in recipe["symbols"]])
        self.assertNotIn("pending_shared_symbols", read(PACKAGE / "source_manifest.json"))

    def test_every_symbol_row_binds_its_confirmed_canonical(self):
        catalog = read(ROOT / "docs/renderers/web/assets/shared/symbols/manifest.json")
        canonicals = {g["canonical"]: g for g in catalog["canonical_groups"] if g["status"] == "operator-confirmed"}
        rows = read(PACKAGE / "source_manifest.json")["symbol_asset_admission"]["locales"]["ja"]
        self.assertEqual(len(rows), 10)
        for row in rows:
            group = canonicals[row["shared_symbol_key"]]
            self.assertEqual(row["canonical_group"], group["id"])
            if row["max_mean_channel_error"] > 0.02:
                self.assertIn(row["caption_text"], group["captions"]["ja"])
        self.assertEqual(rows[2]["shared_symbol_key"], "no-open-flame/fire-match-prohibited")
        self.assertIn("本製品を火気の近くに置かないでください。",
                      visible_text((PACKAGE / "web/ja" / MARKDOWN).read_text(encoding="utf-8")))

    def test_same_source_and_transcription_as_released_version(self):
        self.assertEqual(file_sha256(PACKAGE / "JE-1000G-JP-JA.pdf"), file_sha256(BASE / "JE-1000G-JP-JA.pdf"))
        def texts(root: Path) -> list:
            return [(line["id"], line["text"]) for page in read(root / "source/transcription.json")["pages"]
                    for line in page["lines"]]
        self.assertEqual(texts(PACKAGE), texts(BASE))
        self.assertEqual(read(BASE / "source_manifest.json")["publication_status"], "operator-authorized-git-only-release")

    @pre_rowspan_divider_styles
    def test_cold_replay_matches_stored_candidate(self):
        try:
            subprocess.run([resolve_pandoc_binary(None), "--version"], check=True, capture_output=True)
        except (OSError, RuntimeError, subprocess.CalledProcessError):
            self.skipTest("Pandoc unavailable")
        rebuild = load("je1000g_jp_ss_rebuild", PACKAGE / "rebuild.py")
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "replay"
            rebuild.rebuild(output)
            for name in (MARKDOWN, "manual.ir.json", "_static/source_geometry.css"):
                self.assertEqual((output / name).read_bytes(), (PACKAGE / "web/ja" / name).read_bytes(), name)

    def test_content_is_rebuilt_from_transcription(self):
        builder = load("je1000g_jp_ss_build_content", PACKAGE / "build_content.py")
        built = json.loads(json.dumps(builder.build(), ensure_ascii=False))
        self.assertEqual(built, read(PACKAGE / "source/ja/content.json"))

    def test_changed_source_input_is_rejected(self):
        module = load("je1000g_jp_ss_rebuild_copy", PACKAGE / "rebuild.py")
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "source"
            shutil.copytree(PACKAGE, source, ignore=shutil.ignore_patterns("web", "evidence", "__pycache__"))
            path = source / "source/ja/content.json"
            path.write_text(path.read_text(encoding="utf-8").replace("1024Wh", "1025Wh"), encoding="utf-8")
            module.SOURCE_ROOT = source
            with self.assertRaisesRegex(ValueError, "input missing or changed"):
                module.rebuild(Path(temp) / "out")


if __name__ == "__main__":
    unittest.main()
