from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tests import test_rtd_feedback
from tools.readthedocs_source import RtdManual, _write_short_aliases
from tools.rtd_alias_entry import alias_head_markup, alias_targets, delayed_forward_body

_BASE = "https://ht-doc.readthedocs.io"
_TARGET = "JE-TEST/EU/fr/md/manual.html"


class RtdAliasEntryTests(unittest.TestCase):
    def test_alias_targets_map_stems_to_nested_urls(self) -> None:
        products = [{"publications": [{"url": _TARGET}, {"url": "JE-TEST/EU/md/manual_legacy.html"}]}]
        self.assertEqual(
            {"manual": _TARGET, "manual_legacy": "JE-TEST/EU/md/manual_legacy.html"},
            alias_targets(products),
        )

    def test_alias_head_markup_is_noindex_with_optional_canonical(self) -> None:
        markup = alias_head_markup(target_url=_TARGET, site_base_url=_BASE)
        self.assertIn('content="noindex"', markup)
        self.assertIn(f'<link rel="canonical" href="{_BASE}/{_TARGET}" />', markup)
        bare = alias_head_markup(target_url=_TARGET, site_base_url="")
        self.assertIn('content="noindex"', bare)
        self.assertNotIn("canonical", bare)

    def test_delayed_forward_requires_both_generated_markers(self) -> None:
        meta = f'<meta http-equiv="refresh" content="0; url={_TARGET}">'
        script = f"<script>window.location.replace({json.dumps(_TARGET)});</script>"
        body = f"<h1>x</h1>{meta}{script}<a href='{_TARGET}'>go</a>"
        changed = delayed_forward_body(body, target_url=_TARGET)
        self.assertIn('content="4; url=', changed)
        self.assertIn('window.addEventListener("load"', changed)
        self.assertNotIn('content="0; url=', changed)
        for partial in (meta, script, "<h1>only</h1>"):
            self.assertEqual(partial, delayed_forward_body(partial, target_url=_TARGET))

    def test_sphinx_alias_gets_attribution_delay_canonical_and_noindex(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            source, assets = test_rtd_feedback.RtdFeedbackTests._fixture(root, channels=None)
            self._write_alias(source)
            self._set(assets, base=_BASE, beacon="0123456789abcdef" * 2)
            output = test_rtd_feedback.RtdFeedbackTests._build(source, root / "out")
            alias = (output / "manual.html").read_text(encoding="utf-8")
            self.assertIn('<meta name="robots" content="noindex" />', alias)
            self.assertIn(f'<link rel="canonical" href="{_BASE}/{_TARGET}" />', alias)
            self.assertIn(f'content="4; url={_TARGET}"', alias)
            self.assertIn('window.addEventListener("load"', alias)
            self.assertNotIn('content="0; url=', alias)
            self.assertIn("cloudflareinsights", alias)
            nested = (output / _TARGET).read_text(encoding="utf-8")
            self.assertNotIn("noindex", nested)

    def test_sphinx_alias_without_beacon_keeps_instant_forward(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            source, assets = test_rtd_feedback.RtdFeedbackTests._fixture(root, channels=None)
            self._write_alias(source)
            self._set(assets, base=_BASE, beacon="")
            output = test_rtd_feedback.RtdFeedbackTests._build(source, root / "out")
            alias = (output / "manual.html").read_text(encoding="utf-8")
            self.assertIn(f'content="0; url={_TARGET}"', alias)
            self.assertNotIn('window.addEventListener("load"', alias)
            self.assertIn('content="noindex"', alias)

    @staticmethod
    def _write_alias(source: Path) -> None:
        _write_short_aliases(output_dir=source, manuals=[RtdManual(
            source_dir=source / "JE-TEST/EU/fr/md",
            destination_dir=source / "JE-TEST/EU/fr/md",
            label="Jackery French User Manual",
            toctree_ref="JE-TEST/EU/fr/md/manual",
            short_alias="manual",
        )])

    @staticmethod
    def _set(assets: Path, *, base: str, beacon: str) -> None:
        settings_path = assets / "settings.json"
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        settings["site_base_url"] = base
        settings["analytics_beacon_token"] = beacon
        settings_path.write_text(json.dumps(settings), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
