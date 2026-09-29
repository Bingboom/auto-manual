from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools import check_doc_lifecycle as lifecycle


class StatusParsingTest(unittest.TestCase):
    def test_accepts_keywords_and_common_decorations(self) -> None:
        for header in (
            "Status: active · Owner: someone",
            "**Status:** done",
            "> Status: `archived`",
            "Status: superseded-by [plan](plan.md)",
            "status：Proposed",
        ):
            with self.subTest(header=header):
                self.assertTrue(lifecycle.is_compliant(f"# Title\n\n{header}\n"))

    def test_superseded_requires_exact_keyword_and_replacement_link(self) -> None:
        for header in (
            "Status: superseded", "Status: superseded-garbage",
            "Status: superseded-by", "Status: superseded-by later",
            "Status: superseded-by [empty]()",
        ):
            with self.subTest(header=header):
                self.assertFalse(lifecycle.is_compliant(header))
        self.assertTrue(lifecycle.is_compliant("Status: superseded-by [new](new.md)"))

    def test_rejects_missing_late_or_free_form_status(self) -> None:
        late = "# Title\n" + "\n" * lifecycle.HEADER_LINES + "Status: active\n"
        for text in ("# Title\n\nNo status here\n", late, "# Title\nStatus: complete\n"):
            with self.subTest(text=text[:30]):
                self.assertFalse(lifecycle.is_compliant(text))


class LifecycleRatchetTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.dev = self.root / "code-as-doc" / "dev"
        self.dev.mkdir(parents=True)
        (self.dev / "README.md").write_text("# Navigation, exempt\n", encoding="utf-8")
        (self.dev / "old_plan.md").write_text("# Old plan\n", encoding="utf-8")
        self.baseline = self.root / "baseline.txt"
        lifecycle.write_baseline(self.baseline, lifecycle.collect_noncompliant(self.root))

    def _check(self) -> lifecycle.LifecycleResult:
        return lifecycle.check_repository(self.root, baseline_path=self.baseline, printer=lambda _: None)

    def test_legacy_doc_is_exempt_and_navigation_files_are_skipped(self) -> None:
        self.assertEqual({"code-as-doc/dev/old_plan.md"}, lifecycle.load_baseline(self.baseline))
        self.assertEqual(0, self._check().exit_code)

    def test_new_doc_without_status_fails(self) -> None:
        (self.dev / "new_plan.md").write_text("# New plan\n", encoding="utf-8")
        result = self._check()
        self.assertEqual(1, result.exit_code)
        self.assertEqual(("code-as-doc/dev/new_plan.md",), result.new)

    def test_new_doc_with_status_passes_and_fixed_legacy_doc_is_stale(self) -> None:
        (self.dev / "new_plan.md").write_text("# New\n\nStatus: proposed\n", encoding="utf-8")
        (self.dev / "old_plan.md").write_text("# Old\n\nStatus: done\n", encoding="utf-8")
        result = self._check()
        self.assertEqual(0, result.exit_code)
        self.assertEqual(("code-as-doc/dev/old_plan.md",), result.stale)

    def test_missing_baseline_is_a_distinct_failure(self) -> None:
        result = lifecycle.check_repository(
            self.root, baseline_path=self.root / "missing.txt", printer=lambda _: None
        )
        self.assertEqual(2, result.exit_code)


if __name__ == "__main__":
    unittest.main()
