"""JE-1000H JP (1000 Plus) shared-symbol version: source identity, verbatim copy, artwork and replay."""
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
PACKAGE = ROOT / "manual_sources/JE-1000H/JP/ja/git-20261103-717c813d-shared-symbols"
SOURCE_SHA = "717c813db4c64d57f90072da6f40081162131979cc181a440c589e70d9947da4"
MARKDOWN = "manual_je1000h_jp_ja.md"
PENDING: set[str] = set()
CHAPTERS = ["安全上のご注意", "使用上のご注意", "免責事項", "同梱品", "各部の名称", "液晶画面", "使い方", "UPS 機能",
            "接続", "充電方法", "トラブルシューティング", "主な仕様", "基本情報", "入力ポート", "出カポート", "温度範囲",
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


class Je1000hJpSharedSymbolsWebTests(unittest.TestCase):
    def test_identity_and_candidate_status(self):
        manifest = read(PACKAGE / "source_manifest.json")
        self.assertEqual(manifest["target"]["model"], "JE-1000H")
        self.assertEqual((manifest["target"]["region"], manifest["target"]["languages"]), ("JP", ["ja"]))
        self.assertEqual(manifest["target"]["technical_version"], PACKAGE.name)
        self.assertEqual(manifest["original_source"]["sha256"], SOURCE_SHA)
        self.assertEqual(file_sha256(PACKAGE / manifest["original_source"]["filename"]), SOURCE_SHA)
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
            if line["id"] in PENDING:
                # Pending shared symbol variants: the row stays out of the Web table for now.
                self.assertNotIn(squash(line["text"]), page)
                continue
            text = squash(line["text"]).replace("[88H]", "").replace("[+]", "+")
            if text not in page and text not in alts:
                missing.append(line["id"])
        self.assertEqual(missing, [])
        figure_labels = [line for line in web_lines() if line["id"].startswith(("fig.", "names.f.", "names.r.", "names.l."))]
        for line in figure_labels:
            self.assertIn(squash(line["text"]), alts, line["id"])
        # The LCD map numbers stay in the art; the IR carries them as embedded labels.
        numbers = json.dumps([str(i) for i in range(1, 27)])
        ir = json.dumps(read(PACKAGE / "web/ja/manual.ir.json"), ensure_ascii=False)
        self.assertIn('"embedded_labels": ' + numbers, ir)

    def test_chapters_and_print_only_pages_excluded(self):
        markdown = (PACKAGE / "web/ja" / MARKDOWN).read_text(encoding="utf-8")
        headings = [squash(BeautifulSoup(line, "html.parser").get_text())
                    for line in markdown.splitlines() if line.startswith("## ")]
        # The four specification group titles are shared HB-TABLE-SPEC section headings.
        self.assertEqual([h.lstrip("#") for h in headings], [squash(c) for c in CHAPTERS])
        for print_only in ("国内専用/For use only in Japan", "目次", "写真はイメージです", "スマートコントロール"):
            self.assertNotIn(print_only, markdown)

    def test_model_facts_come_from_this_source(self):
        markdown = (PACKAGE / "web/ja" / MARKDOWN).read_text(encoding="utf-8")
        for fact in ("JE-1000H", "1024Wh (20Ah/51.2V DC)", "約10 ミリ秒（0.010 秒）", "定格出力1800W", "最大400W"):
            self.assertIn(fact, markdown)
        for foreign in ("JE-2000E", "2000 Plus", "JE-1000G", "1000 New", "2048Wh", "2400W"):
            self.assertNotIn(foreign, markdown)

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
        markdown = (PACKAGE / "web/ja" / MARKDOWN).read_text(encoding="utf-8")
        refs = {img["src"] for img in BeautifulSoup(markdown, "html.parser").find_all("img")}
        for ref in refs:
            self.assertTrue((PACKAGE / "web/ja" / ref).is_file(), ref)
        admission = read(PACKAGE / "source_manifest.json")["symbol_asset_admission"]["locales"]["ja"]
        self.assertEqual([row["asset_ref"] for row in admission], [s["path"] for s in recipe["symbols"]])

    def test_pending_symbols_are_bound_to_source(self):
        manifest = read(PACKAGE / "source_manifest.json")
        lines = {line["id"]: line["text"] for line in web_lines()}
        pending = manifest["pending_symbols"]
        self.assertEqual(sorted(k for row in pending for k in row["caption_ids"]), sorted(PENDING))
        for row in pending:
            self.assertEqual(row["caption_text"], "".join(lines[k] for k in row["caption_ids"]))
            self.assertGreater(row["closest_max_mean_channel_error"], 0.02)

    def test_every_symbol_row_binds_its_group_canonical(self):
        from tools.web.shared_symbol_assets import canonical_groups
        groups = canonical_groups()
        rows = read(PACKAGE / "source_manifest.json")["symbol_asset_admission"]["locales"]["ja"]
        self.assertEqual(len(rows), 12)
        for row in rows:
            group, role = groups[row["shared_symbol_key"]]
            # SCG-20261104 moved the battery-disposal canonical to the native SVG
            # after this package was sealed; its PNG row stays a legacy binding
            # admitted within the fixed tolerance (see the cold replay).
            expected = "legacy" if group["id"] == "battery-weee" else "canonical"
            self.assertEqual(role, expected, row["asset_ref"])
            self.assertEqual(row["canonical_group"], group["id"])
        keys = {row["asset_ref"]: row["shared_symbol_key"] for row in rows}
        self.assertEqual(keys["assets/symbol-read.svg"], "read-manual/book-information")
        self.assertEqual(keys["assets/symbol-wet.svg"], "native/je1000d-jp-00c43a89-05")

    @pre_rowspan_divider_styles
    def test_cold_replay_matches_stored_candidate(self):
        try:
            subprocess.run([resolve_pandoc_binary(None), "--version"], check=True, capture_output=True)
        except (OSError, RuntimeError, subprocess.CalledProcessError):
            self.skipTest("Pandoc unavailable")
        rebuild = load("je1000h_jp_ss_rebuild", PACKAGE / "rebuild.py")
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "replay"
            rebuild.rebuild(output)
            for name in (MARKDOWN, "manual.ir.json", "_static/source_geometry.css"):
                self.assertEqual((output / name).read_bytes(), (PACKAGE / "web/ja" / name).read_bytes(), name)

    def test_content_is_rebuilt_from_transcription(self):
        builder = load("je1000h_jp_ss_build_content", PACKAGE / "build_content.py")
        built = json.loads(json.dumps(builder.build(), ensure_ascii=False))
        self.assertEqual(built, read(PACKAGE / "source/ja/content.json"))

    def test_changed_source_input_is_rejected(self):
        module = load("je1000h_jp_ss_rebuild_copy", PACKAGE / "rebuild.py")
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
