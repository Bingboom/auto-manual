from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.rtd.portal import ASSETS, catalog
from tests.web_language_evidence_fixture import seal_language_evidence_fixture


from tests.web_language_evidence_fixture import isolate_shared_component_admission


class PublicationCatalogTests(unittest.TestCase):
    def setUp(self):
        isolate_shared_component_admission(self)
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "web"
        self.root.mkdir()
        self.settings = json.loads((ASSETS / "settings.json").read_text())
        self.links = []

    def publication(self, language="en", *, default=True, scope="single", model="JE-TEST", region="EU"):
        route = f"{model}/{region}/{language}/md"
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
                   "region": region, "lang": language, "route": route, "manual": manual,
                   "version": "1.0", "git_ref": f"review/{model}-{region}", "legacy_default": default,
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
                region=region,
                language=language,
                version="1.0",
                git_ref=f"review/{model}-{region}",
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
        options = cards[0]["language_options"]
        self.assertEqual([(o["code"], o["display"], o["label"]) for o in options],
                         [("en", "en-US", "English"), ("fr", "fr-FR", "Français")])
        self.assertTrue(all(o["url"] for o in options))
        self.assertTrue(all("unavailable_reason" not in o for o in options))

    def test_single_language_product_lists_only_itself(self):
        self.publication("ja", region="JP")
        options = catalog(self.root, self.settings)[0]["language_options"]
        self.assertEqual([(o["code"], o["display"]) for o in options], [("ja", "ja-JP")])

    def test_every_portal_language_has_a_display_code(self):
        expected = {"en": "en-US", "fr": "fr-FR", "es": "es-ES", "ja": "ja-JP", "de": "de-DE",
                    "zh": "zh-CN", "it": "it-IT", "zh-TW": "zh-TW", "nl": "nl-NL", "pl": "pl-PL",
                    "uk": "uk-UA", "pt": "pt-BR", "el": "el-GR", "he": "he-IL", "ar": "ar-SA", "ko": "ko-KR"}
        self.assertEqual(self.settings["language_display_codes"], expected)
        self.assertEqual(set(self.settings["language_labels"]), set(expected))

    def test_language_without_display_code_fails_closed(self):
        self.publication("fr")
        settings = dict(self.settings, language_display_codes={"en": "en-US"})
        with self.assertRaisesRegex(ValueError, "Unknown portal publication language: fr"):
            catalog(self.root, settings)

    def test_cn_and_jp_publications_keep_market_and_language_identity(self):
        self.publication("zh", region="CN")
        self.publication("ja", region="JP")
        self.publication("zh-TW", region="TW")
        cards = {card["region"]: card for card in catalog(self.root, self.settings)}
        self.assertEqual(set(cards), {"CN", "JP", "TW"})
        for region, language, label in (("CN", "zh", "简体中文"), ("JP", "ja", "日本語"), ("TW", "zh-TW", "繁體中文")):
            with self.subTest(region=region):
                available = [option for option in cards[region]["language_options"] if option["url"]]
                self.assertEqual([(option["code"], option["label"]) for option in available], [(language, label)])
                self.assertIn(f"/{region}/{language}/", available[0]["url"])

    def test_legacy_scope_does_not_count_as_english_only(self):
        self.publication(scope="legacy_unspecified")
        card = catalog(self.root, self.settings)[0]
        self.assertEqual([(o["code"], o["display"]) for o in card["language_options"]],
                         [("current", "Current publication")])

    def test_legacy_alongside_single_does_not_assert_language_absence(self):
        self.publication(scope="legacy_unspecified")
        self.publication("fr", default=False)
        card = catalog(self.root, self.settings)[0]
        self.assertEqual([(o["code"], o["display"]) for o in card["language_options"]],
                         [("current", "Current publication"), ("fr", "fr-FR")])
        self.assertTrue(all(o["url"] for o in card["language_options"]))

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
        (self.root / "conf.py").write_text("extensions=['myst_parser','tools.rtd.portal']\nhtml_theme='furo'\n")
        index = self.root / "index.md"
        index.write_text(index.read_text() + "\n\n```{toctree}\n\nJE-TEST/EU/en/md/manual_en\nJE-TEST/EU/fr/md/manual_fr\n```\n")
        before = {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        output = self.base / "html"
        proc = subprocess.run([sys.executable, "-m", "sphinx", "-q", "-b", "html", str(self.root), str(output)], capture_output=True, text=True, check=False)
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
