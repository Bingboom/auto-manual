import tempfile
import unittest
from pathlib import Path

from tools import build_docs
from tools.utils.korean_josa import (
    JOSA_PAIRS,
    has_batchim,
    josa_base_key,
    josa_substitutions,
    select_josa,
    with_josa_substitutions,
)
from tools.word_bundle_common import apply_rst_substitutions


class KoreanJosaSelectionTests(unittest.TestCase):
    def test_select_josa_should_follow_the_final_consonant(self) -> None:
        cases = [
            # 템 carries a final consonant -> 은 / 을; 리 does not -> 는 / 를.
            ("Jackery Explorer 2000 Plus 리튬이차전지시스템", "EUN", "은"),
            ("Jackery Explorer 2000 Plus 리튬이차전지시스템", "EUL", "을"),
            ("배터리", "EUN", "는"),
            ("배터리", "EUL", "를"),
            ("POWER 버튼", "EUL", "을"),
            ("DC/USB 전원 버튼", "EUL", "을"),
        ]
        for value, pair, expected in cases:
            with self.subTest(value=value, pair=pair):
                self.assertEqual(expected, select_josa(value, pair))

    def test_every_josa_pair_should_be_ordered_consonant_then_vowel(self) -> None:
        """Ground truth for every pair, so none can be registered backwards.

        ``JOSA_PAIRS`` stores ``(after a consonant, after a vowel)``. ``WA`` was
        stored the other way round and no test named it, so 시스템 resolved to
        와 and 배터리 to 과 — both wrong — until a template asked for it.
        """

        # 템 carries a final consonant; 리 does not.
        correct_forms = {
            "EUN": ("시스템은", "배터리는"),
            "EUL": ("시스템을", "배터리를"),
            "I": ("시스템이", "배터리가"),
            "WA": ("시스템과", "배터리와"),
        }
        self.assertEqual(
            set(JOSA_PAIRS),
            set(correct_forms),
            "a new josa pair needs its expected forms written down here",
        )
        for pair, (after_consonant, after_vowel) in correct_forms.items():
            with self.subTest(pair=pair):
                self.assertEqual(after_consonant, "시스템" + select_josa("시스템", pair))
                self.assertEqual(after_vowel, "배터리" + select_josa("배터리", pair))

    def test_select_josa_should_read_trailing_digits_as_sino_korean(self) -> None:
        # 2000 reads 이천 (final ㄴ) -> 은; 12 reads 십이 (no final) -> 는.
        self.assertEqual("은", select_josa("Battery Pack 2000", "EUN"))
        self.assertEqual("는", select_josa("USB-C 12", "EUN"))

    def test_select_josa_should_use_the_latin_reading_table(self) -> None:
        # Jackery reads 재키 -> vowel-final.
        self.assertEqual("는", select_josa("Jackery", "EUN"))
        self.assertEqual("가", select_josa("Jackery", "I"))

    def test_select_josa_should_abstain_on_an_unknown_latin_tail(self) -> None:
        # Guessing here would print a wrong particle in a shipped manual, so the
        # companion is simply not offered and the build fails on the unknown key.
        self.assertIsNone(select_josa("HomePower", "EUN"))
        self.assertIsNone(has_batchim("HomePower"))

    def test_select_josa_should_ignore_trailing_punctuation(self) -> None:
        self.assertEqual("은", select_josa("리튬이차전지시스템.", "EUN"))
        self.assertEqual("는", select_josa("(Jackery)", "EUN"))

    def test_unknown_pair_should_raise(self) -> None:
        with self.assertRaises(KeyError):
            select_josa("배터리", "EOPSEUL")


class KoreanJosaSubstitutionTests(unittest.TestCase):
    def test_josa_substitutions_should_carry_value_and_particle(self) -> None:
        resolved = josa_substitutions({"PRODUCT_NAME": "리튬이차전지시스템"})

        self.assertEqual("리튬이차전지시스템은", resolved["PRODUCT_NAME_JOSA_EUN"])
        self.assertEqual("리튬이차전지시스템을", resolved["PRODUCT_NAME_JOSA_EUL"])

    def test_josa_substitutions_should_skip_empty_and_unreadable_values(self) -> None:
        resolved = josa_substitutions({"EMPTY": "  ", "LATIN": "HomePower"})

        self.assertEqual({}, resolved)

    def test_with_josa_substitutions_should_keep_the_original_keys(self) -> None:
        resolved = with_josa_substitutions({"PRODUCT_NAME": "배터리 팩"})

        self.assertEqual("배터리 팩", resolved["PRODUCT_NAME"])
        self.assertEqual("배터리 팩은", resolved["PRODUCT_NAME_JOSA_EUN"])

    def test_josa_base_key_should_recover_the_base_placeholder(self) -> None:
        self.assertEqual("PRODUCT_NAME", josa_base_key("PRODUCT_NAME_JOSA_EUN"))
        self.assertIsNone(josa_base_key("PRODUCT_NAME"))
        self.assertIsNone(josa_base_key("_JOSA_EUN"))


class KoreanJosaWiringTests(unittest.TestCase):
    def _spec_master(self, root: Path) -> Path:
        csv_path = root / "Spec_Master.csv"
        csv_path.write_text(
            "Section,Row_key,Slot_key,Line_order,Page,Model,Region,Is_Latest,enabled,Value_source\n"
            "GENERAL INFO,product_name,,1,specifications,JE-2000E,KR,1,1,"
            "Jackery Explorer 2000 Plus 리튬이차전지시스템\n"
            "GENERAL INFO,model_no,,1,specifications,JE-2000E,KR,1,1,JE-2000E\n",
            encoding="utf-8",
        )
        return csv_path

    def test_build_substitutions_should_add_josa_companions_for_ko(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            cfg = {"paths": {"spec_master_csv": str(self._spec_master(Path(td)))}}

            substitutions = build_docs.resolve_rst_substitutions_for_build(
                cfg, model="JE-2000E", region="KR", lang="ko"
            )

            self.assertEqual(
                "Jackery Explorer 2000 Plus 리튬이차전지시스템은",
                substitutions["PRODUCT_NAME_JOSA_EUN"],
            )

    def test_build_substitutions_should_not_add_josa_companions_for_other_langs(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            cfg = {"paths": {"spec_master_csv": str(self._spec_master(Path(td)))}}

            substitutions = build_docs.resolve_rst_substitutions_for_build(
                cfg, model="JE-2000E", region="KR", lang="en"
            )

            self.assertNotIn("PRODUCT_NAME_JOSA_EUN", substitutions)

    def test_word_path_should_resolve_josa_companions_for_ko(self) -> None:
        out = apply_rst_substitutions(
            "|PRODUCT_NAME_JOSA_EUN| 두 개의 포트를 갖추고 있습니다.",
            {"PRODUCT_NAME": "리튬이차전지시스템"},
            {"lang": "ko"},
        )

        self.assertEqual("리튬이차전지시스템은 두 개의 포트를 갖추고 있습니다.", out)

    def test_word_path_should_leave_josa_companions_alone_for_other_langs(self) -> None:
        out = apply_rst_substitutions(
            "|PRODUCT_NAME_JOSA_EUN| text",
            {"PRODUCT_NAME": "Explorer"},
            {"lang": "en"},
        )

        self.assertEqual("|PRODUCT_NAME_JOSA_EUN| text", out)


class KoreanTemplateJosaTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]
    DOUBLE_JOSA = ("은(는)", "을(를)", "이(가)", "와(과)")

    def test_ko_templates_should_not_print_a_double_josa(self) -> None:
        # Style Guide K11: the finished manual must never show 은(는). The ko
        # templates name a particle pair instead and the renderer resolves it.
        offenders: list[str] = []
        for directory in ("page_shared/ko", "page_eu-kr"):
            for path in sorted((self.ROOT / "docs" / "templates" / directory).glob("*.rst")):
                text = path.read_text(encoding="utf-8")
                if any(form in text for form in self.DOUBLE_JOSA):
                    offenders.append(str(path.relative_to(self.ROOT)))

        self.assertEqual([], offenders)


if __name__ == "__main__":
    unittest.main()
