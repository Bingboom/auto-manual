from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tests.test_rtd_feedback import RtdFeedbackTests
from tools.rtd_analytics import BEACON_SRC, beacon_attributes, beacon_markup, normalize_beacon_token

_TOKEN = "0123456789abcdef0123456789abcdef"


class RtdAnalyticsTests(unittest.TestCase):
    def test_missing_or_blank_token_disables_analytics(self) -> None:
        self.assertEqual("", normalize_beacon_token(None))
        self.assertEqual("", normalize_beacon_token(""))
        self.assertEqual("", normalize_beacon_token("   "))

    def test_token_must_be_fixed_hex_shape(self) -> None:
        self.assertEqual(_TOKEN, normalize_beacon_token(f" {_TOKEN}\n"))
        for raw in (
            _TOKEN.upper(),
            _TOKEN[:-1],
            _TOKEN + "0",
            "not-a-token",
            f"{_TOKEN}?site=x",
            123,
            {"token": _TOKEN},
        ):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                normalize_beacon_token(raw)

    def test_beacon_attributes_carry_only_the_token(self) -> None:
        attributes = beacon_attributes(_TOKEN)
        self.assertEqual({"data-cf-beacon": json.dumps({"token": _TOKEN})}, attributes)

    def test_beacon_markup_is_empty_when_off_and_escaped_when_on(self) -> None:
        self.assertEqual("", beacon_markup(""))
        markup = beacon_markup(_TOKEN)
        self.assertIn(f'src="{BEACON_SRC}"', markup)
        self.assertIn("&quot;token&quot;", markup)
        self.assertNotIn('data-cf-beacon="{"', markup)

    def test_sphinx_default_and_explicit_empty_token_are_byte_identical(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td)
            source, _ = RtdFeedbackTests._fixture(root / "default", channels=None)
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
            self._set_token(assets, _TOKEN)
            page = self._build_page(source, root / "enabled")
            html = page.read_text(encoding="utf-8")
            self.assertIn(BEACON_SRC, html)
            self.assertIn(_TOKEN, html)
            index = page.parents[4] / "index.html"
            self.assertIn(BEACON_SRC, index.read_text(encoding="utf-8"))

    @staticmethod
    def _set_token(assets: Path, token: str) -> None:
        settings_path = assets / "settings.json"
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        settings["analytics_beacon_token"] = token
        settings_path.write_text(json.dumps(settings), encoding="utf-8")

    @staticmethod
    def _build_page(source: Path, output: Path) -> Path:
        RtdFeedbackTests._build(source, output)
        return output / "JE-TEST/EU/fr/md/manual.html"


if __name__ == "__main__":
    unittest.main()
