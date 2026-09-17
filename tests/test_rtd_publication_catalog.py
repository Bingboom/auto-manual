from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.rtd_portal import ASSETS, catalog
from tests.web_language_evidence_fixture import seal_language_evidence_fixture


class PublicationCatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "web"
        self.root.mkdir()
        self.settings = json.loads((ASSETS / "settings.json").read_text())
        self.links = []

    def publication(self, language="en", *, default=True, scope="single", model="JE-TEST"):
        route = f"{model}/EU/{language}/md"
        manual = f"manual_{language}.md"
        page = self.root / route / manual
        page.parent.mkdir(parents=True)
        page.write_text("# Test manual\n")
        self.links.append(f"- [Jackery Test User Manual]({route}/{manual})")
        (self.root / "index.md").write_text("\n".join(self.links))
        metadata = self.base / "sources/web" / route / "publish_meta.json"
        metadata.parent.mkdir(parents=True)
        (metadata.parent / manual).write_bytes(page.read_bytes())
        payload = {"schema_version": "auto-manual-web-publish-target/v2", "model": model,
                   "region": "EU", "lang": language, "route": route, "manual": manual,
                   "version": "1.0", "git_ref": f"review/{model}-EU", "legacy_default": default,
                   "language_scope": scope}
        if scope == "single":
            html = self.base / "verification-html" / model / language
            html.mkdir(parents=True)
            (html / "index.html").write_text("<html></html>\n", encoding="utf-8")
            receipt, receipt_sha256 = seal_language_evidence_fixture(
                markdown_dir=metadata.parent,
                markdown_name=manual,
                html_dir=html,
                evidence_dir=metadata.parent / "evidence",
                model=model,
                region="EU",
                language=language,
                version="1.0",
                git_ref=f"review/{model}-EU",
            )
            payload.update(
                language_projection_evidence_path="evidence/" + receipt.name,
                language_projection_evidence_sha256=receipt_sha256,
            )
        metadata.write_text(json.dumps(payload))
        return metadata

    def test_two_languages_one_product_and_only_published_options(self):
        self.publication()
        self.publication("fr", default=False)
        cards = catalog(self.root, self.settings)
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0]["edition"], "EUUK")
        available = [o["code"] for o in cards[0]["language_options"] if o["url"]]
        self.assertEqual(available, ["en", "fr"])
        self.assertEqual(len(cards[0]["language_options"]), 13)
        self.assertEqual(cards[0]["language_options"][-1]["unavailable_reason"], "Not yet published")

    def test_registered_japanese_language_resolves_to_its_label(self):
        """Reproduces the RTD portal side of production build 34602012: a
        single-language ``ja`` publication (JE-5000A/JP) must resolve through
        the same ``settings.json`` language table every other single-language
        publication uses, not raise ``Unknown portal publication language``."""
        self.publication("ja", model="JE-5000A")
        card = catalog(self.root, self.settings)[0]
        available = {o["code"]: o for o in card["language_options"] if o["url"]}
        self.assertIn("ja", available)
        self.assertEqual(available["ja"]["label"], self.settings["language_labels"]["ja"])
        self.assertEqual(available["ja"]["url"], card["publications"][0]["url"])

    def test_unregistered_language_code_still_raises(self):
        """Negative control for the ``ja`` fix above: ``ko`` is a real,
        registered doc language (``tools/lang_registry.py``) with no shipped
        RTD/Web publication yet, so it must NOT be in ``settings.json``'s
        ``language_labels`` -- and ``group_publications`` must still fail
        loudly on it instead of silently falling through. (An arbitrary
        made-up code like ``xx`` can't reach this check at all: the evidence
        sealing this fixture uses already rejects it earlier, at
        ``canonical_language``.)"""
        self.assertNotIn("ko", self.settings["language_labels"])
        self.publication("ko")
        with self.assertRaisesRegex(ValueError, "Unknown portal publication language: ko"):
            catalog(self.root, self.settings)

    def test_legacy_scope_does_not_count_as_english_only(self):
        self.publication(scope="legacy_unspecified")
        card = catalog(self.root, self.settings)[0]
        self.assertEqual([o["code"] for o in card["language_options"] if o["url"]], ["current"])
        self.assertEqual(card["language_options"][1]["unavailable_reason"], "Separate language page not verified")

    def test_legacy_alongside_single_does_not_assert_language_absence(self):
        self.publication(scope="legacy_unspecified")
        self.publication("fr", default=False)
        card = catalog(self.root, self.settings)[0]
        self.assertEqual([o["code"] for o in card["language_options"] if o["url"]], ["current", "fr"])
        self.assertTrue(all(o["unavailable_reason"] == "Separate language page not verified"
                            for o in card["language_options"] if not o["url"]))

    def test_missing_metadata_for_locale_route_fails(self):
        meta = self.publication()
        meta.unlink()
        with self.assertRaisesRegex(ValueError, "needs frozen"):
            catalog(self.root, self.settings)

    def test_identity_mismatch_fails(self):
        meta = self.publication()
        payload = json.loads(meta.read_text())
        payload["model"] = "OTHER"
        meta.write_text(json.dumps(payload))
        with self.assertRaisesRegex(ValueError, "identity"):
            catalog(self.root, self.settings)

    def test_unknown_single_language_fails_evidence_before_guessing_url(self):
        metadata = self.publication()
        payload = json.loads(metadata.read_text(encoding="utf-8"))
        payload["lang"] = "unknown"
        metadata.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "identity"):
            catalog(self.root, self.settings)

    def test_multiple_defaults_fail(self):
        self.publication()
        self.publication("fr")
        with self.assertRaisesRegex(ValueError, "Multiple default"):
            catalog(self.root, self.settings)

    def test_escaping_metadata_symlink_fails(self):
        meta = self.publication()
        external = self.base / "external.json"
        external.write_bytes(meta.read_bytes())
        meta.unlink()
        meta.symlink_to(external)
        with self.assertRaisesRegex(ValueError, "Unsafe publication"):
            catalog(self.root, self.settings)

    def test_sphinx_grouped_home_and_single_manual_dropdown(self):
        self.publication()
        self.publication("fr", default=False)
        (self.root / "conf.py").write_text("extensions=['myst_parser','tools.rtd_portal']\nhtml_theme='furo'\n")
        index = self.root / "index.md"
        index.write_text(index.read_text() + "\n\n```{toctree}\n\nJE-TEST/EU/en/md/manual_en\nJE-TEST/EU/fr/md/manual_fr\n```\n")
        before = {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        output = self.base / "html"
        proc = subprocess.run([sys.executable, "-m", "sphinx", "-q", "-b", "html", str(self.root), str(output)], capture_output=True, text=True)
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
        home = (output / "index.html").read_text()
        self.assertEqual(home.count('class="card"'), 1)
        page = (output / "JE-TEST/EU/en/md/manual_en.html").read_text()
        self.assertIn('id="manual-locale-select"', page)
        self.assertIn('../../fr/md/manual_fr.html', page)
        self.assertIn('value="manual_en.html" selected', page)
        self.assertIn('JE-TEST · EUUK', page)
        self.assertIn('manual-locales.js', page)
        french = (output / "JE-TEST/EU/fr/md/manual_fr.html").read_text()
        self.assertIn('lang="fr"', french)
        self.assertIn('<div lang="fr" dir="ltr">', french)
        self.assertEqual(before, {p: p.read_bytes() for p in before})

    def test_sphinx_real_build_succeeds_for_a_single_japanese_publication(self):
        """Minimal real reproduction of production build 34602012: a single
        ``ja`` publication (modeled on JE-5000A/JP) run through real Sphinx
        with ``tools.rtd_portal`` engaged, exactly as Read the Docs' ``-D
        extensions=myst_parser,tools.rtd_portal`` override does. Before the
        ``settings.json`` fix, ``page_context`` raises inside Sphinx's own
        write-doc phase and this fails with the same
        ``ExtensionError: ... Unknown portal publication language: ja``
        signature as the real RTD build; after the fix, it renders clean."""
        self.publication("ja", model="JE-5000A")
        (self.root / "conf.py").write_text("extensions=['myst_parser','tools.rtd_portal']\nhtml_theme='furo'\n")
        index = self.root / "index.md"
        index.write_text(index.read_text() + "\n\n```{toctree}\n\nJE-5000A/EU/ja/md/manual_ja\n```\n")
        output = self.base / "html"
        proc = subprocess.run([sys.executable, "-m", "sphinx", "-q", "-b", "html", str(self.root), str(output)], capture_output=True, text=True)
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
        home = (output / "index.html").read_text()
        self.assertEqual(home.count('class="card"'), 1)
        page = (output / "JE-5000A/EU/ja/md/manual_ja.html").read_text()
        self.assertIn('id="manual-locale-select"', page)
        self.assertIn('<div lang="ja" dir="ltr">', page)
