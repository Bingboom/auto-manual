"""JS-100I (SolarSaga 100 Air) JP Git-only manual: identity, verbatim copy, artwork reuse and replay."""
from __future__ import annotations

import hashlib
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
PACKAGE = ROOT / "manual_sources/JS-100I/JP/ja/git-20261026-cc8b3421"
SOURCE_SHA = "cc8b3421221bf11b03f2ddd0ce86519605189fbe0721a7d8a536520d75513e6f"
MARKDOWN = "manual_js100i_jp_ja.md"
# The printed chapter strips; the cover has no Web chapter.
CHAPTERS = ["使用ガイド（ご使用前の注意事項）", "同梱品", "使い方", "主な仕様", "保証について"]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


render_module = load("js100i_jp_render", PACKAGE / "render.py")


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def visible_text(markdown: str) -> str:
    soup = BeautifulSoup(markdown, "html.parser")
    for node in soup.find_all(["style", "script"]):
        node.decompose()
    # The shared Inbox draws its card numbers; the print badges are not copy.
    for badge in soup.select(".hb-inbox-number, .hb-inbox-index"):
        badge.decompose()
    return "".join(soup.get_text("").replace("#", "").split())


def expected_text() -> str:
    lines = [line["text"] for page in read(PACKAGE / "source/transcription.json")["pages"]
             for line in page["lines"] if line["web"]]
    return "".join("".join(lines).split())


class Js100iJpWebTests(unittest.TestCase):
    def test_identity_and_candidate_status(self):
        manifest = read(PACKAGE / "source_manifest.json")
        self.assertEqual(manifest["target"], {"model": "JS-100I", "region": "JP", "languages": ["ja"],
                                              "technical_version": PACKAGE.name})
        self.assertEqual(manifest["original_source"]["sha256"], SOURCE_SHA)
        self.assertEqual(file_sha256(PACKAGE / "source/original.pdf"), SOURCE_SHA)
        self.assertIsNone(manifest["printed_manual_version"])
        if manifest["publication_status"] == render_module.CANDIDATE:
            self.assertFalse(manifest["publication_eligible"])
            self.assertFalse((PACKAGE / "source/approval.json").exists())
        else:
            self.assertEqual(manifest["publication_status"], render_module.APPROVED)
            self.assertTrue(manifest["publication_eligible"])

    def test_stored_copy_equals_transcription_in_order(self):
        markdown = (PACKAGE / "web/ja" / MARKDOWN).read_text(encoding="utf-8")
        self.assertEqual(visible_text(markdown), expected_text())
        headings = [line[2:].strip() for line in markdown.splitlines() if line.startswith("# ")]
        self.assertEqual(headings, CHAPTERS)
        for cover_only in ("型番: JS-100I", "写真はイメージです"):
            self.assertNotIn(cover_only, markdown)

    def test_reused_eu_artwork_is_byte_identical(self):
        decisions = read(PACKAGE / "source/asset_decisions.json")["assets"]
        reused = [d for d in decisions if d["decision"] == "reuse"]
        self.assertEqual(len(reused), 11)
        for decision in reused:
            source = ROOT / decision["source_path"]
            self.assertEqual(file_sha256(source), decision["sha256"], decision["asset"])
            self.assertEqual((PACKAGE / decision["asset"]).read_bytes(), source.read_bytes(), decision["asset"])
        listed = {d["asset"] for d in decisions}
        present = {p.relative_to(PACKAGE).as_posix() for p in (PACKAGE / "assets").iterdir()}
        self.assertEqual(listed, present)
        for decision in decisions:
            if decision["decision"] == "extract":
                self.assertTrue(decision["reason"])
                self.assertEqual(file_sha256(PACKAGE / decision["asset"]), decision["sha256"])

    def test_figure_labels_bind_outlined_glyphs_and_art(self):
        labels = read(PACKAGE / "source/figure_labels.json")["figures"]
        pages = "".join((PACKAGE / "source/page" / name).read_text(encoding="utf-8")
                        for name in read(PACKAGE / "source_manifest.json")["page_order"])
        soup = BeautifulSoup(pages, "html.parser")
        references = {json.loads(img["data-reference"])["id"]: img for img in soup.select("img.hb-source-reference")}
        labelled = {name: figure for name, figure in labels.items() if figure["lines"]}
        self.assertEqual(set(references), {name.replace("_", "-") for name in labelled})
        for name, figure in labelled.items():
            self.assertTrue(all(line["glyph_indices"] for line in figure["lines"]), name)
            img = references[name.replace("_", "-")]
            layout = json.loads(img["data-reference"])["base_art_layout"]
            art = PACKAGE / "assets" / f"{name}.png"
            self.assertEqual(layout["art_sha256"], hashlib.sha256(art.read_bytes()).hexdigest(), name)
            lines = img.find_next_sibling("div", class_="line-block").find_all("div", class_="line")
            self.assertEqual([line.decode_contents() for line in lines],
                             [line["text"] for line in figure["lines"]], name)
        recipe = read(PACKAGE / "source/asset_recipe.json")
        for asset in recipe["assets"]:
            self.assertTrue((PACKAGE / asset["outputs"][0]["path"]).is_file())
            self.assertEqual({t["op"] for t in asset["transforms"]} - {"crop", "whiteout", "copy_pdf_region"}, set())

    def test_cold_replay_matches_stored_candidate(self):
        # The prepared RST pipeline converts through Pandoc; the CI unit runner has none.
        try:
            subprocess.run([resolve_pandoc_binary(None), "--version"], check=True, capture_output=True)
        except (OSError, RuntimeError, subprocess.CalledProcessError):
            self.skipTest("Pandoc unavailable")
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "replay"
            render_module.render(PACKAGE, output)
            for name in (MARKDOWN, "manual.ir.json", "_static/source.css"):
                self.assertEqual((output / name).read_bytes(), (PACKAGE / "web/ja" / name).read_bytes(), name)
            stored = sorted(p.relative_to(PACKAGE / "web/ja").as_posix()
                            for p in (PACKAGE / "web/ja/assets").rglob("*") if p.is_file())
            fresh = sorted(p.relative_to(output).as_posix() for p in (output / "assets").rglob("*") if p.is_file())
            self.assertEqual(fresh, stored)

    def test_changed_source_copy_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "source"
            shutil.copytree(PACKAGE, source, ignore=shutil.ignore_patterns("web", "evidence", "__pycache__"))
            page = source / "source/page/spec_ja.rst"
            page.write_text(page.read_text(encoding="utf-8").replace("100W±5%", "110W±5%"), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "frozen source input changed"):
                render_module.render(source, Path(temp) / "out")


if __name__ == "__main__":
    unittest.main()
