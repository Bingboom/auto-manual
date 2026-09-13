from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from tools.gen_index_bundle import MaterializedBundle
from tools.web_language_bundle import split_web_bundle


class LanguageBundleTests(unittest.TestCase):
    def project(self, language="fr"):
        return split_web_bundle(self.bundle, language=language, destination=self.root / language)

    def test_missing_mixed_translation_fails_before_output(self):
        self.bundle = replace(self.bundle, languages=("en", "fr", "de"))
        with self.assertRaisesRegex(ValueError, "no declared block"):
            self.project("de")
        self.assertFalse((self.root / "de").exists())

    def test_unknown_language_rejected(self):
        with self.assertRaisesRegex(ValueError, "outside the frozen bundle"):
            self.project("unknown")

    def test_implicit_foreign_preface_is_not_relabeled_as_target_language(self):
        page = self.bundle.page_dir / "00_preface.rst"
        page.write_text("English preface.\n\n**FR IMPORTANT**\n\nPréface française.\n")
        result = self.project()
        preface = result.page_paths[0].read_text()
        self.assertIn("Préface française", preface)
        self.assertNotIn("English preface", preface)
        self.assertNotIn("projection boundary", preface)

    def test_existing_destination_is_untouched(self):
        target = self.root / "fr"
        target.mkdir()
        (target / "keep").write_text("unchanged")
        with self.assertRaisesRegex(ValueError, "must be new"):
            self.project()
        self.assertEqual((target / "keep").read_text(), "unchanged")

    def test_nested_source_destination_rejected(self):
        with self.assertRaisesRegex(ValueError, "outside the source"):
            split_web_bundle(self.bundle, language="fr", destination=self.source / "derived")

    def test_foreign_nested_include_rejected_before_output(self):
        page = self.bundle.page_dir / "p20_chapter.rst"
        page.write_text(page.read_text() + "\n.. include:: chapter.rst\n")
        with self.assertRaisesRegex(ValueError, "foreign or unknown"):
            self.project()
        self.assertFalse((self.root / "fr").exists())

    def test_escaping_nested_include_rejected_before_output(self):
        outside = self.root / "external.rst"
        outside.write_text("Not part of bundle")
        page = self.bundle.page_dir / "p20_chapter.rst"
        page.write_text(page.read_text() + "\n.. include:: ../../external.rst\n")
        with self.assertRaisesRegex(ValueError, "escapes"):
            self.project()
        self.assertFalse((self.root / "fr").exists())

    def test_neutral_fragment_and_frozen_asset_are_preserved(self):
        page = self.bundle.page_dir / "p20_chapter.rst"
        page.write_text(page.read_text() + "\n.. include:: neutral.rst\n")
        (page.parent / "neutral.rst").write_text("Shared structural fragment")
        (self.source / "asset.svg").write_text("<svg/>")
        result = self.project()
        self.assertTrue((result.page_dir / "neutral.rst").exists())
        self.assertEqual((result.bundle_dir / "asset.svg").read_bytes(), b"<svg/>")

    def test_index_outside_bundle_rejected(self):
        external = self.root / "external_index.rst"
        external.write_text(".. include:: source/page/chapter.rst\n")
        self.bundle = replace(self.bundle, index_path=external)
        with self.assertRaisesRegex(ValueError, "Index escapes"):
            self.project()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        page = self.source / "page"
        page.mkdir(parents=True)
        (page / "00_preface.rst").write_text(
            ".. raw:: latex\n\n   \\HBApplyLang{en}\n\n"
            "**EN IMPORTANT**\n\nEnglish preface.\n\n"
            "**FR IMPORTANT**\n\nPréface française.\n\n", encoding="utf-8")
        for name, lang in [("chapter.rst", "en"), ("p20_chapter.rst", "fr")]:
            (page / name).write_text(f".. raw:: latex\n\n   \\HBApplyLang{{{lang}}}\n\n{name}\n", encoding="utf-8")
        included = (page / "00_preface.rst", page / "p20_chapter.rst", page / "chapter.rst")
        index = self.source / "index.rst"
        index.write_text("\n".join(f".. include:: page/{p.name}\n" for p in included))
        self.bundle = MaterializedBundle(
            bundle_dir=self.source, page_dir=page, index_path=index,
            conf_path=self.source / "conf.py", conf_base_path=self.source / "conf_base.py",
            wrapper_index_path=self.source / "wrapper.rst", page_paths=included,
            title="Example manual", reference_doc=None, model="Example", region="US", lang=None,
            languages=("en", "fr"), lang_block_pages=(("00_preface.rst", "en"),),
        )

    def test_explicit_scope_preserves_order_and_original_bytes(self):
        original = {p: p.read_bytes() for p in self.source.rglob("*") if p.is_file()}
        result = split_web_bundle(self.bundle, language="fr", destination=self.root / "fr")
        self.assertEqual([p.name for p in result.page_paths], ["00_preface_fr.rst", "p20_chapter.rst"])
        self.assertEqual(result.languages, ("fr",))
        preface = result.page_paths[0].read_text()
        self.assertIn("Préface française", preface)
        self.assertNotIn("English preface", preface)
        self.assertIn(r"\HBApplyLang{fr}", preface)
        self.assertFalse((result.page_dir / "chapter.rst").exists())
        self.assertEqual(original, {p: p.read_bytes() for p in original})

    def test_undeclared_language_page_is_not_silently_retained(self):
        (self.bundle.page_dir / "chapter.rst").write_text("Undeclared copy")
        with self.assertRaisesRegex(ValueError, "explicit language"):
            split_web_bundle(self.bundle, language="en", destination=self.root / "en")
        self.assertFalse((self.root / "en").exists())

    def test_external_include_and_symlink_are_rejected(self):
        outside = self.root / "foreign.rst"
        outside.write_text("Foreign content")
        self.bundle.index_path.write_text(".. include:: ../foreign.rst\n")
        with self.assertRaisesRegex(ValueError, "escapes"):
            split_web_bundle(self.bundle, language="en", destination=self.root / "en")
        (self.source / "linked").symlink_to(outside)
        with self.assertRaises(Exception):
            split_web_bundle(self.bundle, language="en", destination=self.root / "en")
