"""JE-1800B JP V2 Git-only manual: source identity, verbatim copy, artwork and replay."""
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
PACKAGE = ROOT / "manual_sources/JE-1800B/JP/ja/git-20261103-754e8c1d-v2"
SOURCE_SHA = "754e8c1d076b7d5fd9d84ac76ce9447dccec4a9351c7b7d756a3225255b4da52"
MASTER_SHA = "97a33a6da34bf1fc67f804b1405b3af11cc579f3a88837417234769269ff0099"
MARKDOWN = "manual_je1800b_jp_ja.md"
CHAPTERS = ["安全上のご注意", "使用上のご注意", "免責事項", "同梱品", "各部の名称", "液晶画面", "使い方",
            "UPS 機能", "充電方法", "トラブルシューティング", "主な仕様", "基本情報", "入力ポート", "出カポート",
            "温度範囲", "保証について", "Jackeryアプリ ユーザーマニュアル"]


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


def lines() -> dict[str, dict]:
    pages = read(PACKAGE / "source/transcription.json")["pages"]
    return {line["id"]: line for page in pages if page["web"] for line in page["lines"]}


class Je1800bJpWebTests(unittest.TestCase):
    def test_identity_and_candidate_status(self):
        manifest = read(PACKAGE / "source_manifest.json")
        self.assertEqual(manifest["target"]["model"], "JE-1800B")
        self.assertEqual((manifest["target"]["region"], manifest["target"]["languages"]), ("JP", ["ja"]))
        self.assertEqual(manifest["target"]["technical_version"], PACKAGE.name)
        self.assertEqual(manifest["original_source"]["sha256"], SOURCE_SHA)
        self.assertEqual(file_sha256(PACKAGE / manifest["original_source"]["filename"]), SOURCE_SHA)
        record = manifest["source_record"]
        self.assertEqual((record["record_id"], record["sub_material_code"], record["project_number"]),
                         ("reczz28SfbsHfHUZ", "16-0102-000418", "HTE2611"))
        self.assertEqual(record["print_master"]["sha256"], MASTER_SHA)
        self.assertNotIn("token", json.dumps(manifest).lower())
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

    def test_transcription_is_the_unmodified_text_layer(self):
        extractor = load("je1800b_jp_extract_text", PACKAGE / "extract_text.py")
        self.assertEqual(json.loads(json.dumps(extractor.extract(), ensure_ascii=False)),
                         read(PACKAGE / "source/transcription.json"))

    def test_every_web_line_has_one_disposition(self):
        dispositions = read(PACKAGE / "source/line_dispositions.json")["lines"]
        self.assertEqual(set(dispositions), set(lines()))
        kinds = {value.split(":")[0] for value in dispositions.values()}
        self.assertLessEqual(kinds, {"bound", "embedded", "component-number", "excluded"})

    def test_every_bound_line_is_selectable_text_in_the_page(self):
        markdown = (PACKAGE / "web/ja" / MARKDOWN).read_text(encoding="utf-8")
        page = visible_text(markdown).replace("+", "")
        soup = BeautifulSoup(markdown, "html.parser")
        alts = squash(" ".join(img.get("alt", "") for img in soup.find_all("img")))
        # Panel labels live in the art, its alt text and the IR (the LCD map's
        # numbers are IR labels under the map's heading alt).
        ir_labels = squash(" ".join(
            label for chapter in read(PACKAGE / "source/ja/content.json")["chapters"] for node in chapter["nodes"]
            for label in node.get("component_spec", {}).get("metadata", {}).get("embedded_labels", [])))
        dispositions = read(PACKAGE / "source/line_dispositions.json")["lines"]
        missing = []
        for key, line in lines().items():
            value = squash(line["text"])
            for marker in ("•", "◦", "■"):
                value = value.removeprefix(marker)
            if dispositions[key].startswith("bound:") and value.replace("®", "") not in page.replace("®", ""):
                missing.append(key)
            if dispositions[key].startswith("embedded:") and value not in alts and value not in ir_labels:
                missing.append(key)
        self.assertEqual(missing, [])

    def test_chapters_and_print_only_pages_excluded(self):
        markdown = (PACKAGE / "web/ja" / MARKDOWN).read_text(encoding="utf-8")
        headings = [squash(BeautifulSoup(line, "html.parser").get_text()).lstrip("#")
                    for line in markdown.splitlines() if line.startswith("## ")]
        self.assertEqual(headings, [squash(c) for c in CHAPTERS])
        for print_only in ("国内専用/For use only in Japan", "目次", "写真はイメージです"):
            self.assertNotIn(print_only, markdown)

    def test_model_facts_come_from_this_source(self):
        markdown = (PACKAGE / "web/ja" / MARKDOWN).read_text(encoding="utf-8")
        for fact in ("JE-1800B", "1920Wh (37.5Ah/51.2V DC)", "合計2200W，瞬間最大4400W", "約366×255×269 mm"):
            self.assertIn(fact, markdown)
        for foreign in ("JE-1500D", "1500 New", "1536Wh", "JE-1000D", "1070Wh"):
            self.assertNotIn(foreign, markdown)

    def test_assets_and_shared_symbols(self):
        recipe = read(PACKAGE / "source/asset_recipe.json")
        for item in recipe["reused"]:
            self.assertEqual(file_sha256(PACKAGE / item["path"]), item["sha256"])
            self.assertEqual(file_sha256(ROOT / item["from"]), item["sha256"])
        markdown = (PACKAGE / "web/ja" / MARKDOWN).read_text(encoding="utf-8")
        refs = {img["src"] for img in BeautifulSoup(markdown, "html.parser").find_all("img")}
        for ref in refs:
            self.assertTrue((PACKAGE / "web/ja" / ref).is_file(), ref)
        admission = read(PACKAGE / "source_manifest.json")["symbol_asset_admission"]["locales"]["ja"]
        self.assertEqual([row["asset_ref"] for row in admission], [s["path"] for s in recipe["symbols"]])
        catalog = read(ROOT / "docs/renderers/web/assets/shared/symbols/manifest.json")
        keys = {row["key"]: row for row in catalog["assets"]}
        for symbol in recipe["symbols"]:
            shared = keys[symbol["shared_symbol_key"]]
            self.assertEqual(shared["path"], symbol["shared_path"])
            self.assertEqual(file_sha256(PACKAGE / symbol["path"]), shared["sha256"])

    @pre_rowspan_divider_styles
    def test_cold_replay_matches_stored_candidate(self):
        try:
            subprocess.run([resolve_pandoc_binary(None), "--version"], check=True, capture_output=True)
        except (OSError, RuntimeError, subprocess.CalledProcessError):
            self.skipTest("Pandoc unavailable")
        rebuild = load("je1800b_jp_rebuild", PACKAGE / "rebuild.py")
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "replay"
            rebuild.rebuild(output)
            for name in (MARKDOWN, "manual.ir.json", "_static/source_geometry.css"):
                self.assertEqual((output / name).read_bytes(), (PACKAGE / "web/ja" / name).read_bytes(), name)

    def test_content_is_rebuilt_from_transcription(self):
        builder = load("je1800b_jp_build_content", PACKAGE / "build_content.py")
        built = json.loads(json.dumps(builder.build(), ensure_ascii=False))
        self.assertEqual(built, read(PACKAGE / "source/ja/content.json"))
        self.assertEqual(json.loads(json.dumps(builder.dispositions(), ensure_ascii=False)),
                         read(PACKAGE / "source/line_dispositions.json"))

    def test_changed_source_input_is_rejected(self):
        module = load("je1800b_jp_rebuild_copy", PACKAGE / "rebuild.py")
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "source"
            shutil.copytree(PACKAGE, source, ignore=shutil.ignore_patterns("web", "evidence", "__pycache__"))
            path = source / "source/ja/content.json"
            path.write_text(path.read_text(encoding="utf-8").replace("1920Wh", "1921Wh"), encoding="utf-8")
            module.SOURCE_ROOT = source
            with self.assertRaisesRegex(ValueError, "input missing or changed"):
                module.rebuild(Path(temp) / "out")


if __name__ == "__main__":
    unittest.main()
