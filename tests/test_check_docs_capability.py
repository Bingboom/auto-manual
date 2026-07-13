"""Capability -> chapter consistency check (data-driven quality gate)."""
from __future__ import annotations

import sys
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.check_docs_capability import collect_capability_issues  # noqa: E402


@dataclass(frozen=True)
class _Issue:
    code: str
    message: str
    model: str | None
    region: str | None
    path: Path | None = None
    lang: str | None = None


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class CapabilityCheckTests(unittest.TestCase):
    def _run(self, caps_row: str, rules: str, pages: dict[str, str],
             model: str = "JE-1000F", region: str = "US") -> list[_Issue]:
        td = Path(tempfile.mkdtemp())
        data = td / "data"
        _write(data / "model_capabilities.csv",
               "Document_key,Project,UPS功能,LED照明灯\n" + caps_row + "\n")
        _write(data / "capability_page_rules.csv",
               "capability,scope,page_stem,match_regex,required_when_true,forbidden_when_false,notes\n"
               + rules + "\n")
        bundle = td / "bundle"
        for name, text in pages.items():
            _write(bundle / "page" / name, text)
        (bundle / "page").mkdir(parents=True, exist_ok=True)
        return collect_capability_issues(
            bundle_dir=bundle, model=model, region=region,
            data_dir=data, issue_cls=_Issue)

    def test_required_page_missing_flags(self) -> None:
        issues = self._run(
            "JE-1000F_US,HTE153,TRUE,TRUE",
            "UPS功能,page,06_ups_mode,,Y,Y,",
            {"05_operation_guide.rst": "body"})
        self.assertEqual([i.code for i in issues], ["CAPABILITY_CONTENT_MISSING"])
        self.assertIn("UPS功能", issues[0].message)

    def test_required_page_present_passes(self) -> None:
        issues = self._run(
            "JE-1000F_US,HTE153,TRUE,TRUE",
            "UPS功能,page,06_ups_mode,,Y,Y,",
            {"06_ups_mode.rst": "UPS body"})
        self.assertEqual(issues, [])

    def test_forbidden_page_present_flags(self) -> None:
        issues = self._run(
            "JE-1000F_US,HTE153,FALSE,TRUE",
            "UPS功能,page,06_ups_mode,,Y,Y,",
            {"06_ups_mode.rst": "UPS body"})
        self.assertEqual([i.code for i in issues], ["CAPABILITY_CONTENT_UNEXPECTED"])

    def test_section_regex_and_lang_prefixed_stems(self) -> None:
        # p20_-prefixed FR copy still matches via substring stem matching
        issues = self._run(
            "JE-1000F_US,HTE153,TRUE,TRUE",
            "LED照明灯,section,05_operation_guide,LED LIGHT,Y,Y,",
            {"p20_05_operation_guide_placeholder.rst": "LED LIGHT ON/OFF"})
        self.assertEqual(issues, [])

    def test_section_regex_missing_flags(self) -> None:
        issues = self._run(
            "JE-1000F_US,HTE153,TRUE,TRUE",
            "LED照明灯,section,05_operation_guide,LED LIGHT,Y,Y,",
            {"05_operation_guide.rst": "no lamp here"})
        self.assertEqual([i.code for i in issues], ["CAPABILITY_CONTENT_MISSING"])

    def test_target_without_capability_row_is_skipped(self) -> None:
        issues = self._run(
            "JE-9999X_US,HTE000,TRUE,TRUE",
            "UPS功能,page,06_ups_mode,,Y,Y,",
            {})
        self.assertEqual(issues, [])

    def test_inert_rule_records_nothing(self) -> None:
        issues = self._run(
            "JE-1000F_US,HTE153,TRUE,TRUE",
            "UPS功能,page,06_ups_mode,,N,N,recorded only",
            {})
        self.assertEqual(issues, [])

    def test_overflowing_notes_column_does_not_crash(self) -> None:
        # an unquoted comma in notes shunts cells into DictReader's restkey
        issues = self._run(
            "JE-1000F_US,HTE153,TRUE,TRUE",
            "UPS功能,page,06_ups_mode,,Y,Y,note with, stray comma",
            {"06_ups_mode.rst": "UPS body"})
        self.assertEqual(issues, [])


if __name__ == "__main__":
    unittest.main()
