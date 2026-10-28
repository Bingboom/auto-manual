from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tests.test_rtd_feedback import RtdFeedbackTests
from tools.rtd.page_metadata import (
    head_markup, normalize_site_base_url, page_description, page_title, portal_head_markup,
)

_BASE = "https://ht-doc.readthedocs.io"


from tests.web_language_evidence_fixture import isolate_shared_component_admission


class RtdPageMetadataTests(unittest.TestCase):
    def setUp(self):
        isolate_shared_component_admission(self)

    def test_missing_or_blank_base_url_disables_absolute_tags(self) -> None:
        self.assertEqual("", normalize_site_base_url(None))
        self.assertEqual("", normalize_site_base_url("  "))
        markup = head_markup(title="T", description="D", page_url="a/b.html",
                             alternates=[("fr", "a/b.html")], site_base_url="")
        self.assertIn('name="description"', markup)
        self.assertNotIn("canonical", markup)
        self.assertNotIn("hreflang", markup)
        self.assertNotIn("og:url", markup)

    def test_base_url_is_an_https_origin_with_optional_prefix(self) -> None:
        self.assertEqual(_BASE, normalize_site_base_url(f" {_BASE}/ "))
        self.assertEqual(f"{_BASE}/en/latest", normalize_site_base_url(f"{_BASE}/en/latest/"))
        markup = portal_head_markup(site_base_url=normalize_site_base_url(f"{_BASE}/en/latest"))
        self.assertIn(f'<link rel="canonical" href="{_BASE}/en/latest/" />', markup)
        for raw in (
            "http://ht-doc.readthedocs.io",
            f"{_BASE}/en/../latest",
            f"{_BASE}/en//latest",
            f"{_BASE}?q=1",
            f"{_BASE}#f",
            "https://user:pw@ht-doc.readthedocs.io",
            123,
        ):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                normalize_site_base_url(raw)

    def test_title_and_description_derive_from_publication_identity(self) -> None:
        title = page_title(name="French", model="JE-TEST", region="EU", lang_label="Français")
        self.assertEqual("French JE-TEST User Manual (EU · Français) · Jackery", title)
        self.assertEqual("JE-TEST User Manual (EU · en) · Jackery",
                         page_title(name=" ", model="JE-TEST", region="EU", lang_label="en"))
        description = page_description(name="French", model="JE-TEST", region="EU",
                                       lang_label="Français", version="1.2")
        self.assertIn("French JE-TEST", description)
        self.assertIn("Version 1.2.", description)
        self.assertNotIn("Version", page_description(name="F", model="M", region="EU",
                                                     lang_label="fr", version=" "))

    def test_head_markup_escapes_values_and_includes_self_alternate(self) -> None:
        markup = head_markup(
            title='A "<T>"', description='D "<x>"', page_url="a/b.html",
            alternates=[("fr", "a/b.html"), ("en", "a/en.html")], site_base_url=_BASE,
        )
        self.assertIn("&lt;T&gt;", markup)
        self.assertIn("&lt;x&gt;", markup)
        self.assertIn(f'<link rel="canonical" href="{_BASE}/a/b.html" />', markup)
        self.assertIn(f'hreflang="fr" href="{_BASE}/a/b.html"', markup)
        self.assertIn(f'hreflang="en" href="{_BASE}/a/en.html"', markup)
        self.assertIn(f'<meta property="og:url" content="{_BASE}/a/b.html" />', markup)

    def test_sphinx_verified_page_gets_derived_head_and_legacy_is_untouched(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            source, assets = RtdFeedbackTests._fixture(root, channels=None, include_legacy=True)
            self._set_base(assets, _BASE)
            output = RtdFeedbackTests._build(source, root / "out")
            page = (output / "JE-TEST/EU/fr/md/manual.html").read_text(encoding="utf-8")
            self.assertIn("<title>French JE-TEST User Manual (EU · Français) · Jackery</title>", page)
            self.assertIn('<meta name="description"', page)
            self.assertIn(f'<link rel="canonical" href="{_BASE}/JE-TEST/EU/fr/md/manual.html" />', page)
            self.assertIn(f'<link rel="alternate" hreflang="fr" href="{_BASE}/JE-TEST/EU/fr/md/manual.html" />', page)
            self.assertIn('<select id="manual-locale-select"><option value="manual.html" selected>fr-FR</option></select>', page)
            self.assertNotIn("Not yet published", page)
            index = (output / "index.html").read_text(encoding="utf-8")
            self.assertIn(f'<link rel="canonical" href="{_BASE}/" />', index)
            self.assertIn('og:title" content="说明书资料库"', index)
            self.assertNotIn("Manual Center", index)
            self.assertIn('og:site_name" content="说明书资料库"', page)
            self.assertNotIn("Manual Center", page)
            legacy = (output / "JE-TEST/EU/md/manual_legacy.html").read_text(encoding="utf-8")
            self.assertNotIn("canonical", legacy)
            self.assertNotIn("· Jackery</title>", legacy)

    def test_sphinx_empty_base_url_keeps_relative_only_head(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            source, assets = RtdFeedbackTests._fixture(root, channels=None)
            self._set_base(assets, "")
            output = RtdFeedbackTests._build(source, root / "out")
            page = (output / "JE-TEST/EU/fr/md/manual.html").read_text(encoding="utf-8")
            self.assertIn("· Jackery</title>", page)
            self.assertIn('<meta name="description"', page)
            self.assertNotIn("canonical", page)
            self.assertNotIn("hreflang", page)

    def test_portal_head_markup_without_base_has_no_urls(self) -> None:
        markup = portal_head_markup(site_base_url="")
        self.assertIn('og:title" content="说明书资料库"', markup)
        self.assertNotIn("Manual Center", markup)
        self.assertNotIn("canonical", markup)

    @staticmethod
    def _set_base(assets: Path, base: str) -> None:
        settings_path = assets / "settings.json"
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        settings["site_base_url"] = base
        settings_path.write_text(json.dumps(settings), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
