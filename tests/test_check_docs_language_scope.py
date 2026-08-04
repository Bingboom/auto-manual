"""Language-scope check gate (verification side of per-model trimming)."""
from __future__ import annotations

import sys
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.check_docs_language_scope import (  # noqa: E402
    MAX_DROPPED_SCRIPT_CHARS,
    collect_language_scope_issues,
)

EU_FAMILY = ["en", "fr", "es", "de", "it", "uk"]
UKRAINIAN = "Вітаємо з придбанням нового виробу та бажаємо приємного користування ним"


@dataclass(frozen=True)
class Issue:
    code: str
    message: str
    model: str | None = None
    region: str | None = None
    path: Path | None = None
    lang: str | None = None


class LanguageScopeGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.data_dir = self.tmp / "data"
        self.data_dir.mkdir()
        self.page_dir = self.tmp / "bundle" / "page"
        self.page_dir.mkdir(parents=True)

    def _rows(self, rows: str) -> None:
        (self.data_dir / "model_languages.csv").write_text(
            "Document_key,Project,languages,notes\n" + rows, encoding="utf-8")

    def _page(self, name: str, text: str) -> None:
        (self.page_dir / name).write_text(text, encoding="utf-8")

    def _run(self, *, family=None, model="JE-1000F", region="EU"):
        return collect_language_scope_issues(
            bundle_dir=self.tmp / "bundle",
            family_langs=list(family if family is not None else EU_FAMILY),
            model=model,
            region=region,
            data_dir=self.data_dir,
            issue_cls=Issue,
        )

    def test_clean_trimmed_bundle_has_no_issues(self):
        self._rows("JE-1000F_EU,HTE153,en;fr;es;de;it,note\n")
        self._page("00_preface.rst", "IMPORTANT\n\nEnglish body only.\n")
        self.assertEqual([], self._run())

    def test_leaked_dropped_script_fails(self):
        self._rows("JE-1000F_EU,HTE153,en;fr;es;de;it,note\n")
        self._page("p78_01_user_maintenance.rst", UKRAINIAN)
        issues = self._run()
        self.assertEqual(["LANG_SCOPE_FOREIGN_SCRIPT"], [i.code for i in issues])
        self.assertEqual("uk", issues[0].lang)
        self.assertIn("p78_01_user_maintenance.rst", issues[0].message)

    def test_incidental_characters_stay_under_the_tolerance(self):
        self._rows("JE-1000F_EU,HTE153,en;fr;es;de;it,note\n")
        self._page("spec_en.rst", "Model Ж" + "\n" * 3)
        self.assertEqual([], self._run())
        self._page("spec_en.rst", "Ж" * (MAX_DROPPED_SCRIPT_CHARS + 1))
        self.assertEqual(
            ["LANG_SCOPE_FOREIGN_SCRIPT"], [i.code for i in self._run()])

    def test_target_that_ships_the_language_keeps_it(self):
        self._rows("JE-2000F_EU,HTE154,en;fr;es;de;it;uk,note\n")
        self._page("safety_uk.rst", UKRAINIAN)
        self.assertEqual([], self._run(model="JE-2000F"))

    def test_no_row_is_fail_open(self):
        self._rows("JE-9999X_EU,HTE999,en,note\n")
        self._page("safety_uk.rst", UKRAINIAN)
        self.assertEqual([], self._run())

    def test_disjoint_scope_reports_unshipped_language(self):
        self._rows("JE-1000F_EU,HTE153,en;fr;es;de;it,note\n")
        issues = self._run(family=["uk"])
        self.assertEqual(["LANG_SCOPE_UNSHIPPED_LANGUAGE"], [i.code for i in issues])
        self.assertIn("ships none of the languages", issues[0].message)

    def test_latin_dropped_language_is_not_script_detectable(self):
        """fr/es/de/it cannot be told from en by script; no false positives."""
        self._rows("JE-1000F_EU,HTE153,en;uk,note\n")
        self._page("00_preface.rst", "Felicitaciones por su nuevo producto.\n")
        self.assertEqual([], self._run())

    def test_missing_page_dir_still_reports_the_data_contradiction(self):
        self._rows("JE-1000F_EU,HTE153,en;fr;es;de;it,note\n")
        issues = collect_language_scope_issues(
            bundle_dir=self.tmp / "absent",
            family_langs=["uk"],
            model="JE-1000F", region="EU",
            data_dir=self.data_dir, issue_cls=Issue,
        )
        self.assertEqual(["LANG_SCOPE_UNSHIPPED_LANGUAGE"], [i.code for i in issues])


if __name__ == "__main__":
    unittest.main()
