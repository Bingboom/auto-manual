"""Whole-book acceptance against immutable, previously shipped four-language copy."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import re
import shutil
import tempfile
import unicodedata
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from bs4 import BeautifulSoup
from markdown_it import MarkdownIt

from tools.web.frozen_ai_web import build_book, replay_package
from tools.manual_ir import validate_manual_ir
from tools.manual_ir.document import validate_document
from tools.manual_ir.hashing import file_sha256
from tools.web.document_ir import render_document_fragments


SOURCE = Path(__file__).resolve().parents[1] / "manual_sources/JE-1000F/EU/nine-language/git-20260927-c38415f5/four-language"
LANGUAGES = ("uk", "pt", "nl", "pl")


def _soup(path):
    markdown = re.sub(r"^\([a-z_]+\)=$", "", path.read_text(encoding="utf-8"), flags=re.M)
    soup = BeautifulSoup(MarkdownIt("commonmark", {"html": True}).render(markdown), "html.parser")
    for item in soup.select(".hb-reference-semantic"):
        item.decompose()
    return soup


def _words(text):
    # Ignore typographic ligatures, punctuation and superscript wrappers;
    # retain every word and number, including source repetitions.
    return Counter(re.findall(r"[^\W\d_]+|\d+", unicodedata.normalize("NFKC", text)))


class FrozenHeadingReplayTests(unittest.TestCase):
    def test_styled_document_heading_enters_myst_navigation(self):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory)
            (package / "_static").mkdir()
            css = package / "_static/web_manual.css"
            css.write_text("")
            ir = SimpleNamespace(metadata={
                "frozen_stylesheet_sha256": file_sha256(css),
                "markdown_filename": "manual.md",
            })
            fragments = ('<h1 class="hb-h1-pill" id="specifications">SPÉCIFICATIONS</h1>'
                         '<figure><h2 class="component-title">Keep inside component</h2></figure>'
                         '<h2 hidden>Do not promote</h2>',)
            with patch("tools.frozen_ai_web.read_manual_ir", return_value=ir), \
                 patch("tools.frozen_ai_web.render_document_fragments", return_value=fragments):
                replay_package(package)
            output = (package / "manual.md").read_text()
            self.assertIn('<span id="specifications"></span>\n\n# SPÉCIFICATIONS', output)
            self.assertIn('<figure><h2 class="component-title">', output)
            self.assertNotIn("## Keep inside component", output)
            self.assertNotIn("## Do not promote", output)


class FrozenAIWebTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.output = Path(cls.temp.name)
        cls.ir = {language: build_book(SOURCE, cls.output / language, language) for language in LANGUAGES}

    def test_complete_shipped_copy_images_errata_and_registered_components(self):
        operation = json.loads((SOURCE / "source/operation_tables.json").read_text())["locales"]
        sections = json.loads((SOURCE / "source/section_index.json").read_text())["section_ids"]
        for language, ir in self.ir.items():
            with self.subTest(language=language):
                path = self.output / language
                filename = ir.metadata["markdown_filename"]
                new = _soup(path / filename)
                old_root = SOURCE / "web/JE-1000F/EU" / language / "md"
                old = _soup(old_root / filename)
                missing = _words(old.get_text(" ", strip=True)) - _words(new.get_text(" ", strip=True))
                # Shared LCD mode groups use rowspan=3 instead of repeating
                # the same state in each of three rows. No copy is omitted.
                duplicate_states = Counter()
                for mode in operation[language]["lcd_mode"]["modes"]:
                    state = mode["text"].replace("continuame nte", "continuamente")
                    duplicate_states.update(_words(state))
                    duplicate_states.update(_words(state))
                self.assertEqual(Counter(), missing - duplicate_states)
                self.assertEqual(sections, [p.page_id for p in ir.pages[1:-1]])
                for section in sections:
                    self.assertIsNotNone(new.find(id=section), section)
                legend = new.select_one("table.manual-table")
                self.assertEqual(26, len(legend.select("tr")))
                self.assertNotIn("lcd-text-only", legend.get("class", []))
                self.assertIn("table-wrapper", legend.parent.get("class", []))
                self.assertEqual(4, len(new.select("figure.hb-spec-table-composition")))
                self.assertEqual(28, len(ir.metadata["asset_sha256"]))
                old_hashes = {file_sha256(old_root / image["src"]) for image in old.find_all("img")}
                new_hashes = {file_sha256(path / image["src"]) for image in new.find_all("img")}
                self.assertEqual(old_hashes, new_hashes)
                self.assertEqual(old_hashes, set(ir.metadata["asset_sha256"].values()))
                self.assertEqual(21, ir.metadata["rendered_source_figure_count"])
                inventory = ir.metadata["component_inventory"]
                self.assertEqual(20, inventory["HB-SPECIAL-REFERENCE-FIGURE"])
                self.assertEqual(4, inventory["HB-TABLE-SPEC"])
                # Polish source has both Uwaga and UWAGA; both are notices.
                self.assertEqual(13, inventory["HB-CALLOUT-STRIP"])
                self.assertEqual(1, inventory["HB-WARRANTY-YEARS"])
                content = new.get_text(" ", strip=True)
                for erratum in ir.metadata["source_errata"]["entries"]:
                    if erratum["locale"] == language:
                        self.assertIn(erratum["corrected_text"], content)
                        if language == "uk":
                            self.assertNotIn(erratum["source_text"], content)
                if language == "nl":
                    self.assertNotRegex(content, r"Aan/uit-knop voor DC(?!/USB)")
                    self.assertIn("Aan/uit-knop voor DC/USB", content)

    def test_cold_replay_is_identical_after_move_without_source_or_live_contracts(self):
        for language, ir in self.ir.items():
            with self.subTest(language=language):
                original = self.output / language
                moved = self.output / f"moved-{language}"
                shutil.copytree(original, moved)
                expected = (original / ir.metadata["markdown_filename"]).read_bytes()
                with patch("tools.web.frozen_ai_web.FrozenBook", side_effect=AssertionError("source reopened")), \
                     patch("tools.web.frozen_ai_web.load_web_manual_contract", side_effect=AssertionError("contract reopened")), \
                     patch("tools.component_specs.registry.default_registry_path", side_effect=AssertionError("registry reopened")), \
                     patch("tools.component_specs.theme.default_theme_path", side_effect=AssertionError("theme reopened")):
                    replay_package(moved)
                self.assertEqual(expected, (moved / ir.metadata["markdown_filename"]).read_bytes())

    def test_asset_and_stylesheet_tampering_are_rejected(self):
        ir = self.ir["nl"]
        moved = self.output / "tampered"
        shutil.copytree(self.output / "nl", moved)
        asset = moved / next(iter(ir.metadata["asset_sha256"]))
        original = asset.read_bytes()
        asset.write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "asset missing or changed"):
            replay_package(moved)
        asset.write_bytes(original)
        (moved / "_static/web_manual.css").write_text("changed")
        with self.assertRaisesRegex(ValueError, "stylesheet changed"):
            replay_package(moved)

    def test_manifest_and_locale_identity_do_not_bypass_language_policy(self):
        ir = self.ir["nl"]
        mutations = [replace(ir, language="de"), replace(ir, region="US"),
                     replace(ir, pages=(replace(ir.pages[0], language="de"), *ir.pages[1:]))]
        for field, value in (("frozen_source_manifest", None), ("declared_languages", ["de"])):
            mutations.append(replace(ir, metadata={**ir.metadata, field: value}))
        manifest = deepcopy(ir.metadata["frozen_source_manifest"])
        manifest["target"]["languages"].append("de")
        mutations.append(replace(ir, metadata={**ir.metadata, "frozen_source_manifest": manifest}))
        for candidate in mutations:
            with self.subTest(candidate=candidate.language):
                with self.assertRaisesRegex(ValueError, "frozen source language"):
                    render_document_fragments(candidate, package_root=self.output / "nl")
        ordinary = replace(ir, source="prepared-document", language="zz")
        self.assertTrue(validate_manual_ir(ordinary, require_known_languages=True))
        validate_document(ir)

    def test_original_frozen_input_hashes_still_match_and_existing_output_is_protected(self):
        for entry in self.ir["nl"].metadata["frozen_source_manifest"]["inputs"]:
            self.assertEqual(entry["sha256"], file_sha256(SOURCE / entry["path"]))
        with self.assertRaisesRegex(ValueError, "output already exists"):
            build_book(SOURCE, self.output / "nl", "nl")
        with self.assertRaisesRegex(ValueError, "historical source"):
            build_book(SOURCE, SOURCE / "must-not-create", "nl")


if __name__ == "__main__":
    unittest.main()
