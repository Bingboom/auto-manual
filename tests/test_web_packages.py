"""Regression boundaries for source projection and self-contained publication."""
from __future__ import annotations

import hashlib
import runpy
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from urllib.request import urlopen

from bs4 import BeautifulSoup

from tools.gen_index_bundle import MaterializedBundle
from tools.web_language_bundle import split_web_bundle
from tools.web_manual_package import archive_package, build_local_preview_bundle, build_package_site


class LanguageBundleTests(unittest.TestCase):
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


class PackageConsumerTests(unittest.TestCase):
    def test_local_preview_serves_sibling_languages_and_preserves_launcher_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            release = root / "release"
            for language in ("en", "fr"):
                (release / language).mkdir(parents=True)
                (release / language / "index.html").write_text(f"Manual {language}")
            preview = build_local_preview_bundle(release, destination=root / "preview", languages=("en", "fr"))
            namespace = runpy.run_path(str(preview / "open_manual.py"))

            def verify(url):
                self.assertTrue(url.startswith("http://127.0.0.1:"))
                for language in ("en", "fr"):
                    with urlopen(url + language + "/index.html", timeout=5) as response:
                        self.assertEqual(response.read().decode(), f"Manual {language}")
                return True

            with patch("webbrowser.open", side_effect=verify) as opened, patch("threading.Thread.join", side_effect=KeyboardInterrupt):
                namespace["main"]()
            opened.assert_called_once()
            archive_package(preview, root / "preview.zip")
            with zipfile.ZipFile(root / "preview.zip") as archive:
                launcher = archive.getinfo("preview/打开手册.command")
                self.assertEqual((launcher.external_attr >> 16) & 0o777, 0o755)

    def test_actual_sphinx_root_search_toolbar_and_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "md"
            source.mkdir()
            (source / "_static").mkdir()
            (source / "_static/web_manual.css").write_text("")
            markdown = source / "manual_example_fr.md"
            markdown.write_text("# Recharge\n\nBatterie française.\n\n## Entretien\n\nGardez le produit sec.\n", encoding="utf-8")
            # A neighboring source must never enter this package's search.
            (source / "foreign.md").write_text("# Fremdsprache\n\nOnlyForeignToken\n")
            package = root / "fr"
            html = build_package_site(
                markdown, title="Example User Manual", language="fr", languages=("en", "fr"),
                pdf_name="manual_example_fr.pdf", source_dir=root / "site-source", output_dir=package,
            )
            soup = BeautifulSoup(html.read_text(), "html.parser")
            self.assertEqual(soup.html["lang"], "fr")
            self.assertIn("Recharge", soup.select_one("article").get_text())
            self.assertNotIn("Auto Manual Library", str(soup))
            self.assertEqual(soup.select_one('[aria-current="page"]')["href"], "../fr/index.html")
            self.assertEqual(len(soup.select('.manual-package-toc a')), 2)
            search = (package / "searchindex.js").read_text()
            self.assertNotIn("OnlyForeignToken".lower(), search.lower())
            self.assertIn('"index"', search)
            first = root / "first.zip"
            second = root / "second.zip"
            archive_package(package, first)
            archive_package(package, second)
            self.assertEqual(hashlib.sha256(first.read_bytes()).hexdigest(), hashlib.sha256(second.read_bytes()).hexdigest())
            moved = root / "other-prefix"
            with zipfile.ZipFile(first) as zipped:
                zipped.extractall(moved)
            self.assertEqual((moved / "fr/index.html").read_bytes(), html.read_bytes())


if __name__ == "__main__":
    unittest.main()
