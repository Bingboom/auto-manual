from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tests.test_rtd_feedback import RtdFeedbackTests
from tools.rtd_analytics import BEACON_SRC, beacon_attributes, beacon_markup, normalize_beacon_token

# Doubled halves keep this obviously fake value out of secret-scan shapes.
_FAKE_BEACON = "0123456789abcdef" * 2


class RtdAnalyticsTests(unittest.TestCase):
    def test_missing_or_blank_token_disables_analytics(self) -> None:
        self.assertEqual("", normalize_beacon_token(None))
        self.assertEqual("", normalize_beacon_token(""))
        self.assertEqual("", normalize_beacon_token("   "))

    def test_token_must_be_fixed_hex_shape(self) -> None:
        self.assertEqual(_FAKE_BEACON, normalize_beacon_token(f" {_FAKE_BEACON}\n"))
        for raw in (
            _FAKE_BEACON.upper(),
            _FAKE_BEACON[:-1],
            _FAKE_BEACON + "0",
            "not-a-token",
            f"{_FAKE_BEACON}?site=x",
            123,
            {"token": _FAKE_BEACON},
        ):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                normalize_beacon_token(raw)

    def test_beacon_attributes_carry_only_the_token(self) -> None:
        attributes = beacon_attributes(_FAKE_BEACON)
        self.assertEqual({"data-cf-beacon": json.dumps({"token": _FAKE_BEACON})}, attributes)

    def test_beacon_markup_is_empty_when_off_and_escaped_when_on(self) -> None:
        self.assertEqual("", beacon_markup(""))
        markup = beacon_markup(_FAKE_BEACON)
        self.assertIn(f'src="{BEACON_SRC}"', markup)
        self.assertIn("&quot;token&quot;", markup)
        self.assertNotIn('data-cf-beacon="{"', markup)

    def test_sphinx_default_and_explicit_empty_token_are_byte_identical(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            source, assets = RtdFeedbackTests._fixture(root / "default", channels=None)
            self._set_token(assets, None)
            first = self._build_page(source, root / "first")
            source, assets = RtdFeedbackTests._fixture(root / "explicit", channels=None)
            self._set_token(assets, "")
            second = self._build_page(source, root / "second")
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertNotIn("cloudflareinsights", first.read_text(encoding="utf-8"))

    def test_sphinx_enabled_beacon_appears_on_manual_and_root_pages(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            source, assets = RtdFeedbackTests._fixture(root, channels=None)
            self._set_token(assets, _FAKE_BEACON)
            page = self._build_page(source, root / "enabled")
            html = page.read_text(encoding="utf-8")
            self.assertIn(BEACON_SRC, html)
            self.assertIn(_FAKE_BEACON, html)
            index = page.parents[4] / "index.html"
            self.assertIn(BEACON_SRC, index.read_text(encoding="utf-8"))

    @staticmethod
    def _set_token(assets: Path, token: str | None) -> None:
        settings_path = assets / "settings.json"
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        if token is None:
            settings.pop("analytics_beacon_token", None)
        else:
            settings["analytics_beacon_token"] = token
        settings_path.write_text(json.dumps(settings), encoding="utf-8")

    @staticmethod
    def _build_page(source: Path, output: Path) -> Path:
        RtdFeedbackTests._build(source, output)
        return output / "JE-TEST/EU/fr/md/manual.html"


if __name__ == "__main__":
    unittest.main()
