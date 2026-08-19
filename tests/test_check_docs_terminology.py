import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

from tools.check_docs_terminology import (
    collect_terminology_issues,
    load_rules,
    page_language,
    scan_text,
)


@dataclass
class _Issue:
    code: str
    message: str
    model: str | None = None
    region: str | None = None
    lang: str | None = None
    path: Path | None = None


_RULES_CSV = (
    "rule_id,lang,deprecated_regex,preferred,allow_regex,note\n"
    "KO-POWER-BTN,ko,메인 전원 버튼,POWER 버튼,,main power button\n"
    "KO-GRID,ko,그리드 전력,전력망 전원,상용 전원\\(그리드 전력\\),grid wording\n"
    "DE-DEMO,de,Netzladeanzeige,Stromanzeige,,demo rule\n"
)


def _data_dir(tmp: Path) -> Path:
    data_dir = tmp / "data"
    data_dir.mkdir()
    (data_dir / "terminology_rules.csv").write_text(_RULES_CSV, encoding="utf-8")
    return data_dir


class LoadRulesTests(unittest.TestCase):
    def test_missing_file_disables_the_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(load_rules(Path(tmp)), [])

    def test_rows_without_id_or_pattern_are_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "data"
            data_dir.mkdir()
            (data_dir / "terminology_rules.csv").write_text(
                "rule_id,lang,deprecated_regex,preferred,allow_regex,note\n"
                ",ko,x,y,,no id\n"
                "R2,ko,,y,,no pattern\n"
                "R3,ko,z,y,,kept\n",
                encoding="utf-8",
            )
            rules = load_rules(data_dir)
            self.assertEqual([r["rule_id"] for r in rules], ["R3"])


class ScanTextTests(unittest.TestCase):
    def test_plain_match(self):
        rule = {"deprecated_regex": "메인 전원 버튼", "allow_regex": ""}
        self.assertEqual(len(scan_text("메인 전원 버튼을 누르십시오.", rule)), 1)

    def test_allow_regex_exempts_the_sanctioned_context(self):
        rule = {
            "deprecated_regex": "그리드 전력",
            "allow_regex": r"상용 전원\(그리드 전력\)",
        }
        text = "상용 전원(그리드 전력)이 중단될 때"
        self.assertEqual(scan_text(text, rule), [])

    def test_allow_regex_still_reports_other_occurrences(self):
        rule = {
            "deprecated_regex": "그리드 전력",
            "allow_regex": r"상용 전원\(그리드 전력\)",
        }
        text = "상용 전원(그리드 전력)이 중단될 때. 그리드 전력이 끊기면"
        self.assertEqual(len(scan_text(text, rule)), 1)


class PageLanguageTests(unittest.TestCase):
    def test_generated_page_suffix_wins(self):
        self.assertEqual(page_language(Path("lcd_icons_ko.rst"), default_lang="en"), "ko")
        self.assertEqual(page_language(Path("spec_pt-BR.rst"), default_lang="en"), "pt-BR")

    def test_authored_page_falls_back_to_target_language(self):
        self.assertEqual(page_language(Path("11_warranty.rst"), default_lang="ko"), "ko")

    def test_numeric_suffix_is_not_a_language(self):
        self.assertEqual(page_language(Path("p28_11_warranty.rst"), default_lang="de"), "de")


class CollectIssuesTests(unittest.TestCase):
    def _bundle(self, tmp: Path, files: dict[str, str]) -> Path:
        bundle = tmp / "bundle"
        (bundle / "page").mkdir(parents=True)
        for name, text in files.items():
            (bundle / "page" / name).write_text(text, encoding="utf-8")
        return bundle

    def test_reports_deprecated_term_for_the_page_language(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            bundle = self._bundle(tmp_path, {"05_operations.rst": "메인 전원 버튼을 누르십시오."})
            issues = collect_terminology_issues(
                bundle_dir=bundle,
                data_dir=_data_dir(tmp_path),
                model="JE-2000E",
                region="KR",
                lang="ko",
                issue_cls=_Issue,
            )
            self.assertEqual([i.code for i in issues], ["TERMINOLOGY_DEPRECATED"])
            self.assertIn("KO-POWER-BTN", issues[0].message)
            self.assertIn("POWER 버튼", issues[0].message)
            self.assertEqual(issues[0].lang, "ko")

    def test_rules_do_not_leak_across_languages(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            bundle = self._bundle(tmp_path, {"05_operations.rst": "메인 전원 버튼"})
            issues = collect_terminology_issues(
                bundle_dir=bundle,
                data_dir=_data_dir(tmp_path),
                model="JE-2000E",
                region="EU",
                lang="de",
                issue_cls=_Issue,
            )
            self.assertEqual(issues, [])

    def test_generated_page_suffix_selects_the_rule_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            bundle = tmp_path / "bundle"
            (bundle / "generated").mkdir(parents=True)
            (bundle / "generated" / "lcd_icons_de.rst").write_text(
                "AC-Netzladeanzeige", encoding="utf-8"
            )
            issues = collect_terminology_issues(
                bundle_dir=bundle,
                data_dir=_data_dir(tmp_path),
                model="JE-2000E",
                region="EU",
                lang="en",
                issue_cls=_Issue,
            )
            self.assertEqual(len(issues), 1)
            self.assertEqual(issues[0].lang, "de")
            self.assertIn("DE-DEMO", issues[0].message)

    def test_clean_bundle_reports_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            bundle = self._bundle(tmp_path, {"05_operations.rst": "POWER 버튼을 누르십시오."})
            issues = collect_terminology_issues(
                bundle_dir=bundle,
                data_dir=_data_dir(tmp_path),
                model="JE-2000E",
                region="KR",
                lang="ko",
                issue_cls=_Issue,
            )
            self.assertEqual(issues, [])


if __name__ == "__main__":
    unittest.main()
