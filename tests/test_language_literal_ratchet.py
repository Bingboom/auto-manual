from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools import check_language_literal_ratchet as ratchet


class LanguageLiteralRatchetTest(unittest.TestCase):
    def _repo(self) -> tuple[tempfile.TemporaryDirectory[str], Path, Path]:
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        (root / "tools").mkdir()
        (root / "tools" / "lang_registry.py").write_text("SUPPORTED = ('en', 'fr')\n", encoding="utf-8")
        source = root / "tools" / "example.py"
        source.write_text("LANGS = {'en': 'English', 'fr': 'French'}\n", encoding="utf-8")
        return tmp, root, source

    def test_findings_are_line_independent_and_registry_is_excluded(self) -> None:
        tmp, root, source = self._repo()
        self.addCleanup(tmp.cleanup)
        before = ratchet.collect_findings(root)
        source.write_text("\n\nLANGS = {'en': 'English', 'fr': 'French'}\n", encoding="utf-8")
        after = ratchet.collect_findings(root)
        self.assertEqual(before[0].key, after[0].key)
        self.assertEqual(1, len(after))

    def test_new_findings_fail_and_removed_findings_are_stale_only(self) -> None:
        tmp, root, source = self._repo()
        self.addCleanup(tmp.cleanup)
        baseline = root / "baseline.txt"
        findings = ratchet.collect_findings(root)
        ratchet.write_baseline(baseline, findings)

        source.write_text(
            "LANGS = {'en': 'English', 'fr': 'French'}\n"
            "MORE = ('en', 'de')\n",
            encoding="utf-8",
        )
        result = ratchet.check_repository(root, baseline_path=baseline, printer=lambda _: None)
        self.assertEqual(1, result.exit_code)
        self.assertEqual(1, len(result.new))

        source.write_text("ONLY = {'en': 'English'}\n", encoding="utf-8")
        result = ratchet.check_repository(root, baseline_path=baseline, printer=lambda _: None)
        self.assertEqual(0, result.exit_code)
        self.assertEqual(1, len(result.stale))

    def test_missing_baseline_is_a_distinct_failure(self) -> None:
        tmp, root, _ = self._repo()
        self.addCleanup(tmp.cleanup)
        result = ratchet.check_repository(
            root, baseline_path=root / "missing.txt", printer=lambda _: None
        )
        self.assertEqual(2, result.exit_code)
        self.assertTrue(result.baseline_missing)


if __name__ == "__main__":
    unittest.main()
