import re
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

from tools import check_docs_runtime
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


class RuntimePageLanguageTests(unittest.TestCase):
    """The orchestrator must give page-classifying collectors a language for authored pages."""

    def _seen_langs(self, *, family_langs, target_lang):
        seen = {}

        def capture(name):
            def collector(**kwargs):
                seen[name] = kwargs["lang"]
                return []

            return collector

        def nothing(*args, **kwargs):
            return []

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            check_docs_runtime.collect_check_issues(
                cfg_path=root / "config.yaml",
                model="JE-1000F",
                region="JP",
                lang=None,
                all_targets=False,
                data_root=None,
                docs_build_dir=None,
                issue_cls=_Issue,
                repo_root=root,
                load_config=lambda path: {},
                resolve_docs_dir=lambda cfg: root,
                build_langs=lambda cfg: list(family_langs),
                resolve_page_manifest_path=lambda cfg, **kwargs: None,
                resolve_build_targets=lambda cfg, **kwargs: [
                    SimpleNamespace(model="JE-1000F", region="JP", lang=target_lang)
                ],
                bundle_dir_for_target=lambda **kwargs: root / "bundle",
                collect_target_identity_issues=nothing,
                collect_page_contract_issues=nothing,
                collect_generated_page_issues=nothing,
                collect_bundle_issues=nothing,
                collect_identity_drift_issues=nothing,
                collect_duplicate_render_text_issues=nothing,
                collect_fcc_renderer_contract_issues=capture("fcc"),
                collect_terminology_issues=capture("terminology"),
            )
        return seen

    def test_single_language_family_without_target_lang_uses_that_language(self):
        # config.ja.yaml declares languages: [ja] and no per-target lang;
        # without this the gate skipped every unsuffixed JP page.
        seen = self._seen_langs(family_langs=["ja"], target_lang=None)
        self.assertEqual(seen, {"fcc": "ja", "terminology": "ja"})

    def test_multi_language_family_leaves_the_page_language_open(self):
        seen = self._seen_langs(family_langs=["en", "fr", "es"], target_lang=None)
        self.assertEqual(seen, {"fcc": None, "terminology": None})

    def test_explicit_target_lang_wins(self):
        seen = self._seen_langs(family_langs=["ko"], target_lang="ko")
        self.assertEqual(seen, {"fcc": "ko", "terminology": "ko"})


_REPO_DATA = Path(__file__).resolve().parents[1] / "data"

# U+FF5E and U+301C render alike in most fonts; spell them by code point.
FULLWIDTH_TILDE = chr(0xFF5E)
WAVE_DASH = chr(0x301C)


class RepoRulesTests(unittest.TestCase):
    """The shipped rule table, not a fixture: a bad pattern here breaks every check run."""

    def setUp(self):
        self.rules = {rule["rule_id"]: rule for rule in load_rules(_REPO_DATA)}

    def test_every_rule_compiles(self):
        for rule in self.rules.values():
            with self.subTest(rule=rule["rule_id"]):
                re.compile(rule["deprecated_regex"])
                if rule["allow_regex"]:
                    re.compile(rule["allow_regex"])

    def test_japanese_rules_use_the_ja_page_language(self):
        # JP bundles name their pages spec_ja.rst / *_ja.rst and the JP config
        # declares languages: [ja], so unsuffixed pages resolve to "ja" too.
        # A rule keyed "jp" would only ever see cover_jp.rst.
        japanese = [rule for rule in self.rules.values() if rule["rule_id"].startswith("JA-")]
        self.assertTrue(japanese)
        for rule in japanese:
            self.assertEqual(rule["lang"], "ja", rule["rule_id"])

    def test_japanese_rules_hit_retired_forms_and_spare_the_rest(self):
        cases = {
            "JA-CAR-CABLE": (["車載充電ケーブルは別売りです"], ["シガーソケット充電ケーブル", "車載充電器"]),
            "JA-HALFWIDTH-KANA": (["ｼｶﾞｰｿｹｯﾄ ：11V"], ["シガーソケット"]),
            "JA-LED-BUTTON": (["LEDスイッチを長押し", "主電源ボタン + ライトボタン"], ["LEDライトボタン"]),
            "JA-DISPLAY": (["ディスプレーに"], ["ディスプレイ"]),
            "JA-COMPANY": (["弊社では責任を負いかねます"], ["当社は"]),
            "JA-HONKI": (["本機の仕様"], ["本機能は", "本機種", "本製品"]),
            "JA-USER-MANUAL": (["Jackeryアプリ ユーザーマニュアル"], ["取扱説明書", "User Manual"]),
            # Python treats kana as word characters, so a word-boundary pattern
            # cannot see the end of APP in "APPの".
            "JA-APP": (["2.1 APPの右上", "「Jackery App」で"], ["Jackeryアプリ", "App Store", "HAPPY"]),
            "JA-RANGE-TILDE": (
                ["3" + FULLWIDTH_TILDE + "7倍"],
                ["3" + WAVE_DASH + "7倍", "100V~ 50Hz"],
            ),
            "JA-SLASH": (["AC出力のオン/オフ"], ["オン／オフ", "DC/USB"]),
            "JA-CALLOUT-LABEL": (
                ["   * - ご注意\n", "   * - **備考**\n"],
                ["安全上のご注意\n", "   * - 注意\n"],
            ),
            "JA-BYPASS": (["バイパスモード"], ["パススルー"]),
        }
        self.assertEqual(set(cases), {rule_id for rule_id in self.rules if rule_id.startswith("JA-")})
        for rule_id, (retired, clean) in cases.items():
            rule = self.rules[rule_id]
            for text in retired:
                with self.subTest(rule=rule_id, text=text):
                    self.assertTrue(scan_text(text, rule))
            for text in clean:
                with self.subTest(rule=rule_id, text=text):
                    self.assertEqual(scan_text(text, rule), [])


if __name__ == "__main__":
    unittest.main()
