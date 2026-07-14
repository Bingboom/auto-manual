from __future__ import annotations

import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

from tools.check_docs_lang_parity import collect_lang_parity_issues


@dataclass
class _Issue:
    code: str
    message: str
    model: str
    region: str
    path: Path


def _collect(bundle: Path, langs: list[str]) -> list[_Issue]:
    return collect_lang_parity_issues(
        bundle_dir=bundle, langs=langs, model="JE-1000F", region="XX", issue_cls=_Issue
    )


def _write(bundle: Path, name: str, text: str) -> None:
    page_dir = bundle / "page"
    page_dir.mkdir(parents=True, exist_ok=True)
    (page_dir / name).write_text(text, encoding="utf-8")


_ENGLISH_PROSE = (
    "Congratulations on your new product. Please read this manual carefully "
    "before using the product, particularly the relevant precautions to "
    "ensure proper use. Keep this manual in an accessible place for future "
    "reference and visit the support site for the latest version.\n"
) * 3

_KOREAN_PROSE = (
    "제품을 사용하기 전에 본 설명서를 주의 깊게 읽어 주세요. 특히 관련 주의 "
    "사항을 확인하여 올바르게 사용하십시오. 본 설명서는 나중에 참조할 수 "
    "있도록 접근 가능한 장소에 보관하세요. USB-C 및 AC/DC 단자 지원.\n"
) * 3


class TestForeignShell(unittest.TestCase):
    """R1 — the KR English-shell incident class."""

    def test_english_shell_page_in_ko_family_is_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp)
            _write(bundle, "05_operation_guide.rst", _ENGLISH_PROSE)
            issues = _collect(bundle, ["ko"])
        self.assertEqual([i.code for i in issues], ["LANG_PARITY_FOREIGN_SHELL"])

    def test_translated_ko_page_passes_despite_latin_terms(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp)
            _write(bundle, "05_operation_guide.rst", _KOREAN_PROSE + "AC DC USB " * 40)
            issues = _collect(bundle, ["ko"])
        self.assertEqual(issues, [])

    def test_short_pages_are_not_judged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp)
            _write(bundle, "cover.rst", "Cover title only\n")
            issues = _collect(bundle, ["ko"])
        self.assertEqual(issues, [])

    def test_latin_language_families_are_out_of_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp)
            _write(bundle, "05_operation_guide.rst", _ENGLISH_PROSE)
            issues = _collect(bundle, ["fr"])
        self.assertEqual(issues, [])

    def test_jp_alias_maps_to_ja_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp)
            _write(bundle, "05_operation_guide.rst", _ENGLISH_PROSE)
            issues = _collect(bundle, ["jp"])
        self.assertEqual([i.code for i in issues], ["LANG_PARITY_FOREIGN_SHELL"])


class TestForeignLangBlocks(unittest.TestCase):
    """R2 — the AU leftover FR/ES preface incident class."""

    _AU_PREFACE = (
        "English\n\n**IMPORTANT**\n\n| Congratulations...\n\n"
        "**FR IMPORTANT**\n\n| Félicitations...\n\n"
        "**ES IMPORTANTE**\n\n| Felicitaciones...\n"
    )

    def test_foreign_tagged_blocks_in_single_lang_family_are_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp)
            _write(bundle, "00_preface.rst", self._AU_PREFACE)
            issues = _collect(bundle, ["en"])
        self.assertEqual([i.code for i in issues], ["LANG_PARITY_FOREIGN_LANG_BLOCK"])
        self.assertIn("FR", issues[0].message)
        self.assertIn("ES", issues[0].message)

    def test_same_blocks_are_legitimate_in_trilingual_family(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp)
            _write(bundle, "00_preface.rst", self._AU_PREFACE)
            issues = _collect(bundle, ["en", "fr", "es"])
        self.assertEqual(issues, [])

    def test_apply_lang_outside_family_is_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp)
            _write(bundle, "00_preface.rst", ".. raw:: latex\n\n   \\HBApplyLang{fr}\n")
            issues = _collect(bundle, ["en"])
        self.assertEqual([i.code for i in issues], ["LANG_PARITY_FOREIGN_LANG_BLOCK"])


class TestPerLangPageSet(unittest.TestCase):
    """R3 — the missing per-language generated data page class."""

    def test_missing_family_language_page_is_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp)
            _write(bundle, "spec_en.rst", "spec table\n")
            _write(bundle, "spec_fr.rst", "table de spécifications\n")
            issues = _collect(bundle, ["en", "fr", "es"])
        self.assertEqual([i.code for i in issues], ["LANG_PARITY_MISSING_LANG_PAGE"])
        self.assertIn("'es'", issues[0].message)

    def test_complete_per_lang_set_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp)
            for lang in ("en", "fr", "es"):
                _write(bundle, f"spec_{lang}.rst", "spec\n")
            issues = _collect(bundle, ["en", "fr", "es"])
        self.assertEqual(issues, [])

    def test_foreign_lang_page_is_flagged_as_leftover(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp)
            _write(bundle, "spec_ko.rst", "사양\n")
            _write(bundle, "spec_ja.rst", "仕様\n")
            issues = _collect(bundle, ["ko"])
        self.assertEqual([i.code for i in issues], ["LANG_PARITY_FOREIGN_LANG_PAGE"])
        self.assertIn("spec_ja.rst", issues[0].message)

    def test_non_lang_suffix_stems_are_not_grouped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp)
            _write(bundle, "06_ups_mode.rst", "content\n")
            _write(bundle, "08_charging_methods.rst", "content\n")
            issues = _collect(bundle, ["en", "fr"])
        self.assertEqual(issues, [])

    def test_missing_page_dir_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            issues = _collect(Path(tmp), ["en"])
        self.assertEqual(issues, [])


class TestKnownExceptions(unittest.TestCase):
    """Registered debt stays green; anything else still fails."""

    _AU_PREFACE = TestForeignLangBlocks._AU_PREFACE

    def test_registered_exception_is_suppressed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp)
            _write(bundle, "00_preface.rst", self._AU_PREFACE)
            issues = collect_lang_parity_issues(
                bundle_dir=bundle, langs=["en"], model="JE-1000F", region="US",
                issue_cls=_Issue,
                exceptions={("JE-1000F", "US", "LANG_PARITY_FOREIGN_LANG_BLOCK", "00_preface.rst")},
            )
        self.assertEqual(issues, [])

    def test_exception_is_scoped_to_model_region_and_page(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp)
            _write(bundle, "00_preface.rst", self._AU_PREFACE)
            issues = collect_lang_parity_issues(
                bundle_dir=bundle, langs=["en"], model="JE-2000F", region="US",
                issue_cls=_Issue,
                exceptions={("JE-1000F", "US", "LANG_PARITY_FOREIGN_LANG_BLOCK", "00_preface.rst")},
            )
        self.assertEqual([i.code for i in issues], ["LANG_PARITY_FOREIGN_LANG_BLOCK"])

    def test_loader_reads_csv_rows(self) -> None:
        from tools.check_docs_lang_parity import load_known_exceptions

        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp)
            (data / "lang_parity_known_exceptions.csv").write_text(
                "model,region,code,page,note\n"
                "JE-1000F,US,LANG_PARITY_FOREIGN_LANG_BLOCK,00_preface.rst,pending trim\n",
                encoding="utf-8",
            )
            known = load_known_exceptions(data)
        self.assertEqual(
            known,
            {("JE-1000F", "US", "LANG_PARITY_FOREIGN_LANG_BLOCK", "00_preface.rst")},
        )

    def test_loader_missing_file_is_empty(self) -> None:
        from tools.check_docs_lang_parity import load_known_exceptions

        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(load_known_exceptions(Path(tmp)), set())


if __name__ == "__main__":
    unittest.main()
