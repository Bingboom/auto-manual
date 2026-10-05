from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.rtd.web_baseline import SCHEMA, apply_baselines, baseline_markup, read_baselines, source_digest


class WebBaselineTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "publish" / "web"
        self.route = "JE-TEST/EU/en/md"
        self.manual = self.root / self.route / "manual_test.md"
        self.manual.parent.mkdir(parents=True)
        self.manual.write_text("# Manual\n\nRated output: 200 W.\n")
        self.package = self.root.parent / "sources" / "web" / self.route
        self.package.mkdir(parents=True)
        (self.package / "manual_test.md").write_bytes(self.manual.read_bytes())
        self.art = self.package / "panel.png"
        self.art.write_bytes(b"approved artwork")
        self.record = {"url": self.route + "/manual_test.html", "version": "2.7",
                       "language_scope": "single"}
        self.sealed = {"route": self.route, "manual": self.manual.name,
                       "model": "JE-TEST", "region": "EU", "lang": "en",
                       "original_version": "2.7", "language_scope": "single",
                       "source_sha256": source_digest(self.package),
                       "markdown_sha256": hashlib.sha256(self.manual.read_bytes()).hexdigest(), "web_assets": {}}
        self.baseline = {"schema": SCHEMA, "version": "V1.0", "snapshot_commit": "a" * 40,
                         "publish_manifest_sha256": "b" * 64, "publications": [self.sealed]}
        self.path = self.root.parent / "sources" / "baselines" / "V1.0.json"

    def seal(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.baseline))

    def test_absent_baseline_preserves_existing_publication(self):
        original = dict(self.record)
        apply_baselines(self.root, [self.record])
        self.assertEqual(self.record, original)

    def test_matching_baseline_preserves_original_version(self):
        self.seal()
        apply_baselines(self.root, [self.record])
        self.assertEqual(self.record["version"], "2.7")
        self.assertEqual(self.record["web_baselines"], ["V1.0"])
        markup = baseline_markup(self.record, lambda url: "../../" + url + ".html")
        self.assertIn("../../releases/web/V1.0.html", markup)
        self.assertIn("Original publication version: 2.7", markup)

    def test_baseline_notice_is_not_manual_answer_evidence(self):
        from tools.manual_knowledge.html import extract_sections

        sections, _ = extract_sections(
            '<main><p class="web-release-baseline">Web release baseline: V1.0</p>'
            '<h1>Specifications</h1><p>Rated output: 200 W.</p></main>', url="manual.html")
        text = json.dumps(sections)
        self.assertNotIn("Web release baseline", text)
        self.assertIn("Rated output: 200 W.", text)

    def test_changed_web_content_does_not_inherit_baseline(self):
        self.seal()
        self.manual.write_text("# Changed output\n250 W\n")
        apply_baselines(self.root, [self.record])
        self.assertNotIn("web_baselines", self.record)

    def test_changed_source_artwork_does_not_inherit_baseline(self):
        self.seal()
        self.art.write_bytes(b"different region artwork")
        apply_baselines(self.root, [self.record])
        self.assertNotIn("web_baselines", self.record)

    def test_changed_assembled_artwork_does_not_inherit_baseline(self):
        asset = self.root / "_static" / "panel.png"
        asset.parent.mkdir()
        asset.write_bytes(b"approved artwork")
        self.sealed["web_assets"] = {"_static/panel.png": hashlib.sha256(asset.read_bytes()).hexdigest()}
        self.seal()
        asset.write_bytes(b"wrong artwork")
        apply_baselines(self.root, [self.record])
        self.assertNotIn("web_baselines", self.record)

    def test_new_version_and_withdrawal_do_not_inherit_baseline(self):
        self.seal()
        self.record["version"] = "2.8"
        apply_baselines(self.root, [self.record])
        self.assertNotIn("web_baselines", self.record)
        apply_baselines(self.root, [])

    def test_legacy_scope_is_preserved(self):
        self.sealed["language_scope"] = self.record["language_scope"] = "legacy_unspecified"
        self.seal()
        apply_baselines(self.root, [self.record])
        self.assertEqual(self.record["language_scope"], "legacy_unspecified")
        self.assertEqual(self.record["web_baselines"], ["V1.0"])

    def test_duplicate_or_escaping_routes_fail(self):
        self.baseline["publications"].append(dict(self.sealed))
        self.seal()
        with self.assertRaises(ValueError):
            read_baselines(self.root)
        self.baseline["publications"] = [dict(self.sealed, route="../escape")]
        self.seal()
        with self.assertRaises(ValueError):
            read_baselines(self.root)

    def test_symlink_record_fails(self):
        self.seal()
        raw = self.path.read_bytes()
        self.path.unlink()
        other = self.path.parent / "record.txt"
        other.write_bytes(raw)
        self.path.symlink_to(other)
        with self.assertRaises(ValueError):
            read_baselines(self.root)
