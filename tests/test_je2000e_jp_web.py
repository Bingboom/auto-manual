"""JE-2000E JP V2 Git-only manual candidate: source identity, verbatim copy, symbols and replay."""
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
from unittest import mock
from tools.web import stylesheets
from tests.historical_app_styles import pre_rowspan_divider_styles

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "manual_sources/JE-2000E/JP/ja/git-20261019-6a70e879-jp-native"
SOURCE_SHA = "f1829cd35ffe05079fe4b04f6c62fef3ca6adfd64270c47d64f7b2203af9780a"
MASTER_SHA = "6a70e879d65c14741462d0107e45c22f3ce1507b8835a4de1b5647cc4087c661"
MARKDOWN = "manual_je2000e_jp_ja.md"


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
    return (PACKAGE / "web/ja" / MARKDOWN).read_text(encoding="utf-8")


class Je2000eJpWebTests(unittest.TestCase):
    def test_identity_and_candidate_status(self):
        manifest = read(PACKAGE / "source_manifest.json")
        self.assertEqual(manifest["target"]["model"], "JE-2000E")
        self.assertEqual((manifest["target"]["region"], manifest["target"]["languages"]), ("JP", ["ja"]))
        self.assertEqual(manifest["target"]["technical_version"], PACKAGE.name)
        self.assertEqual(manifest["original_source"]["sha256"], SOURCE_SHA)
        self.assertEqual(file_sha256(PACKAGE / manifest["original_source"]["filename"]), SOURCE_SHA)
        self.assertEqual(read(PACKAGE / "source/document.json")["source_sha256"], SOURCE_SHA)
        record = manifest["source_record"]
        self.assertEqual((record["record_id"], record["子物料编码"], record["项目号"], record["sku"]),
                         ("reczz28SfbsHbvLy", "16-0102-000389", "HTE152", "21-0001-000403"))
        self.assertEqual(record["single_language_manual"]["sha256"], SOURCE_SHA)
        self.assertEqual(record["print_master"]["sha256"], MASTER_SHA)
        self.assertEqual(manifest["route"], "JE-2000E/JP/ja/md")
        self.assertNotIn("token", json.dumps(manifest).lower())
        ir = read(PACKAGE / "web/ja/manual.ir.json")
        self.assertEqual(ir["metadata"]["original_source_sha256"], SOURCE_SHA)
        if manifest["publication_status"] == "operator-authorized-git-only-release":
            self.assertTrue(ir["metadata"]["publication_eligible"])
        else:
            self.assertEqual(manifest["publication_status"], "candidate-pending-operator-review")
            self.assertFalse(ir["metadata"]["publication_eligible"])
            self.assertFalse((PACKAGE / "source/approval.json").exists())

    def test_inputs_are_pinned(self):
        manifest = read(PACKAGE / "source_manifest.json")
        listed = {row["path"] for row in manifest["inputs"]}
        for row in manifest["inputs"]:
            self.assertEqual(file_sha256(PACKAGE / row["path"]), row["sha256"], row["path"])
        for path in PACKAGE.rglob("*"):
            if path.is_file() and path.name != "source_manifest.json" and "__pycache__" not in path.parts:
                self.assertIn(path.relative_to(PACKAGE).as_posix(), listed)

    def test_source_copy_is_verbatim(self):
        text = squash(BeautifulSoup(markdown(), "html.parser").get_text(""))
        # Printed spellings stay as printed (source_concerns), never normalized.
        for printed in ("出カポート", "ｼｶﾞｰｿｹｯﾄ", "次のようなような機器", "大きいな設備", "行って下さい",
                        "再度短く押すとでライト", "主電源ボタン/オフ"):
            self.assertIn(printed, text)
        concerns = {c["text"] for c in read(PACKAGE / "source_manifest.json")["source_concerns"]}
        self.assertIn("出カポート", concerns)
        normalizations = " ".join(read(PACKAGE / "source_manifest.json")["normalizations"])
        self.assertNotIn("出力ポート", normalizations)

    def test_print_only_cover_and_toc_excluded(self):
        page = markdown()
        for print_only in ("取扱説明書｜JE-2000E｜日本語", "国内専用/For use only in Japan", "お買い上げありがとうございます",
                           "目次"):
            self.assertNotIn(print_only, page)
        pages = [p["physical_pages"] for p in read(PACKAGE / "source/document.json")["pages"]]
        self.assertEqual(min(min(p) for p in pages), 3)

    def test_native_lines_are_selectable_or_reviewed(self):
        page = squash(BeautifulSoup(markdown(), "html.parser").get_text("")).replace("+", "")
        soup = BeautifulSoup(markdown(), "html.parser")
        alts = squash(" ".join(img.get("alt", "") for img in soup.find_all("img")))
        review = read(PACKAGE / "source/text_coverage_review.json")
        reviewed = {(row["physical_page"], block) for row in review["reviewed_exceptions"]
                    for block in row.get("blocks", [row.get("block")])}
        missing = []
        for line in read(PACKAGE / "source/text_bindings.json"):
            value = squash(line["text"]).lstrip("•◦")
            if len(value) < 12 or (line["physical_page"], line["block"]) in reviewed:
                continue
            # PDF stream order puts a callout's label (ご注意/備考) after its body and,
            # in one warning, the consequence before its heading; every sentence
            # must still appear verbatim in the page.
            for label in ("ご注意", "備考"):
                value = value.removesuffix(label)
            fragments = [part for part in value.split("。") if part]
            if not all(part in page or part in alts for part in fragments):
                missing.append((line["physical_page"], line["text"]))
        self.assertEqual(missing, [])

    def test_symbols_follow_the_operator_canonicals(self):
        recipe = read(PACKAGE / "source/symbol_recipe.json")["symbols"]
        admission = read(PACKAGE / "source_manifest.json")["symbol_asset_admission"]["locales"]["ja"]
        self.assertEqual([row["asset_ref"] for row in admission],
                         [s["path"].removeprefix("web/ja/") for s in recipe])
        groups = {g["id"]: g for g in
                  read(ROOT / "docs/renderers/web/assets/shared/symbols/manifest.json")["canonical_groups"]}
        for symbol, row in zip(recipe, admission, strict=True):
            group = groups[symbol["group"]]
            self.assertEqual(symbol["binding"], "canonical")
            self.assertEqual(row["shared_symbol_key"], symbol["shared_symbol_key"])
            self.assertEqual(symbol["shared_symbol_key"], group["canonical"])
            if row["max_mean_channel_error"] > 0.02:
                # Released on the operator-confirmed group's listed caption.
                self.assertEqual(group["status"], "operator-confirmed")
                self.assertEqual(row["canonical_group"], group["id"])
        catalog = {row["key"]: row for row in
                   read(ROOT / "docs/renderers/web/assets/shared/symbols/manifest.json")["assets"]}
        for symbol in recipe:
            self.assertEqual(file_sha256(PACKAGE / symbol["path"]), catalog[symbol["shared_symbol_key"]]["sha256"])

    @pre_rowspan_divider_styles
    def test_cold_replay_matches_stored_candidate(self):
        try:
            subprocess.run([resolve_pandoc_binary(None), "--version"], check=True, capture_output=True)
        except (OSError, RuntimeError, subprocess.CalledProcessError):
            self.skipTest("Pandoc unavailable")
        rebuild = load("je2000e_jp_rebuild", PACKAGE / "rebuild.py")
        # The package pins web_manual.css by hash; verify the historical copy the decorator supplies.
        historical = stylesheets.get_paths().renderer_contracts_dir / "web_manual.css"
        live = (ROOT / "docs/renderers/contracts/web_manual.css").resolve()
        pinned_sha256 = rebuild.file_sha256
        with tempfile.TemporaryDirectory() as temp, mock.patch.object(
                rebuild, "file_sha256",
                lambda path: pinned_sha256(historical if Path(path).resolve() == live else path)):
            output = Path(temp) / "replay"
            rebuild.assemble(output)
            for name in (MARKDOWN, "manual.ir.json", "_static/source_geometry.css"):
                self.assertEqual((output / name).read_bytes(), (PACKAGE / "web/ja" / name).read_bytes(), name)

    def test_changed_source_input_is_rejected(self):
        module = load("je2000e_jp_rebuild_copy", PACKAGE / "rebuild.py")
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "source"
            shutil.copytree(PACKAGE, source, ignore=shutil.ignore_patterns("__pycache__"))
            path = source / "source/document.json"
            path.write_text(path.read_text(encoding="utf-8").replace("2048Wh", "2049Wh"), encoding="utf-8")
            module.PACKAGE = source
            with self.assertRaisesRegex(ValueError, "frozen input changed"):
                module.assemble(Path(temp) / "out")


if __name__ == "__main__":
    unittest.main()
