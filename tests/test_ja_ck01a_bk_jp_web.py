"""JA-CK01A-BK JP Git-only manual: source identity, verbatim copy, artwork and replay."""
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
PACKAGE = ROOT / "manual_sources/JA-CK01A-BK/JP/ja/git-20261023-3ea84ec6-manual"
SOURCE_SHA = "3ea84ec63b20a4e65c4d2f5d34a45ce715133b6b6f29a424bd95393d131cd113"
MARKDOWN = "manual_jack01abk_jp_ja.md"
# The printed chapter strips; the cover has no Web chapter.
CHAPTERS = ["安全上のご注意", "主な仕様", "インレットボックスの取り付け"]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


render_module = load("ja_ck01a_bk_jp_render", PACKAGE / "render.py")


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def visible_text(markdown: str) -> str:
    soup = BeautifulSoup(markdown, "html.parser")
    for node in soup.find_all(["style", "script"]):
        node.decompose()
    # Ordered-list numbers are printed copy; the browser draws them as markers.
    for ordered in soup.find_all("ol"):
        start = int(ordered.get("start", 1))
        for offset, item in enumerate(ordered.find_all("li", recursive=False)):
            item.insert(0, f"{start + offset}. ")
    return "".join(soup.get_text("").replace("#", "").split())


def expected_text() -> str:
    """Transcribed Web lines in Web order: the cover support line closes the page."""
    lines = [line for panel in read(PACKAGE / "source/transcription.json")["panels"]
             for line in panel["lines"] if line["web"]]
    body = [line["text"] for line in lines if line.get("web_page") != "contact_ja.rst"]
    tail = [line["text"] for line in lines if line.get("web_page") == "contact_ja.rst"]
    return "".join("".join(body + tail).split())


class JaCk01aBkJpWebTests(unittest.TestCase):
    def test_identity_and_candidate_status(self):
        manifest = read(PACKAGE / "source_manifest.json")
        self.assertEqual(manifest["target"], {"model": "JA-CK01A-BK", "region": "JP", "languages": ["ja"],
                                              "technical_version": PACKAGE.name})
        self.assertEqual(manifest["original_source"]["sha256"], SOURCE_SHA)
        self.assertEqual(file_sha256(PACKAGE / "source/original.pdf"), SOURCE_SHA)
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
        for cover_only in ("国内専用", "取扱説明書</", "型番:"):
            self.assertNotIn(cover_only, markdown)

    def test_figure_labels_bind_their_outlined_glyphs(self):
        labels = read(PACKAGE / "source/figure_labels.json")["figures"]["step5-wiring"]
        texts = [line["text"] for line in labels["lines"]]
        transcribed = [line["text"] for line in read(PACKAGE / "source/transcription.json")["panels"][3]["lines"]]
        self.assertEqual(texts, transcribed[2:3] + transcribed[4:13])
        self.assertTrue(all(line["glyph_indices"] for line in labels["lines"]))
        recipe = read(PACKAGE / "source/asset_recipe.json")
        for asset in recipe["assets"]:
            output = asset["outputs"][0]["path"]
            self.assertTrue((PACKAGE / output).is_file(), output)
            self.assertEqual({t["op"] for t in asset["transforms"]} - {"crop", "whiteout"}, set())

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
            page = source / "source/page/safety_ja.rst"
            page.write_text(page.read_text(encoding="utf-8").replace("資格のある", "資格ある"), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "frozen source input changed"):
                render_module.render(source, Path(temp) / "out")


if __name__ == "__main__":
    unittest.main()
