import unittest

from tools.lang_asset_sweep import (
    JUNK_VALUE,
    lang_column_groups,
    minor_only,
    norm_key,
    norm_val,
    rst_headings,
    suggest,
    template_evidence_eligible,
)


class NormalizationTests(unittest.TestCase):
    def test_norm_key_strips_bullets_case_and_trailing_punct(self):
        self.assertEqual(norm_key("* Risk of Electric Shock."), "risk of electric shock")
        self.assertEqual(norm_key("OPERATIONS"), norm_key("Operations"))
        self.assertEqual(norm_key("보증 기간:"), norm_key("보증 기간"))

    def test_norm_val_collapses_whitespace(self):
        self.assertEqual(norm_val("a\n b\tc"), "a b c")

    def test_minor_only(self):
        self.assertTrue(minor_only("NOTA:", "NOTA"))
        self.assertTrue(minor_only("Fonction", "fonction"))
        self.assertFalse(minor_only("충전 계획", "충전 예약"))


class ColumnGroupTests(unittest.TestCase):
    def test_bare_and_prefixed_language_columns(self):
        groups = lang_column_groups(
            ["en", "ko", "zh-TW", "icon_en", "icon_ko", "icon_desc_en",
             "icon_desc_ko", "aliases_ko", "Model"]
        )
        self.assertEqual(groups[""]["en"], "en")
        self.assertEqual(groups[""]["ko"], "ko")
        self.assertEqual(groups[""]["zh-TW"], "zh-TW")
        self.assertEqual(groups["icon"]["ko"], "icon_ko")
        self.assertEqual(groups["icon_desc"]["ko"], "icon_desc_ko")
        self.assertNotIn("aliases", groups)


class HeadingTests(unittest.TestCase):
    def test_rst_headings_extracts_underlined_titles(self):
        text = "조작\n========\n\n본문\n\n전원 켜기/끄기\n------------------------\n"
        self.assertEqual(rst_headings(text), ["조작", "전원 켜기/끄기"])

    def test_rst_headings_ignores_directives_and_short_underlines(self):
        text = ".. image:: x\n=====\nab\n=\n"
        self.assertEqual(rst_headings(text), [])


class EvidenceAndSuggestionTests(unittest.TestCase):
    def test_junk_regex(self):
        self.assertTrue(JUNK_VALUE.fullmatch("test"))
        self.assertTrue(JUNK_VALUE.fullmatch("TBD"))
        self.assertFalse(JUNK_VALUE.fullmatch("테스트 모드"))

    def test_template_evidence_eligibility(self):
        self.assertFalse(template_evidence_eligible("test"))
        self.assertTrue(template_evidence_eligible("조작"))
        self.assertTrue(template_evidence_eligible("FONCTIONNEMENT"))

    def test_suggest_prefers_template_evidence_then_majority(self):
        variants = {
            "a": [("TM句对", "r1", "EN", "a")],
            "b": [("Terms", "r2", "EN", "b"), ("LCD_icons.icon", "r3", "EN", "b")],
        }
        self.assertEqual(suggest(variants, {"a": (1, []), "b": (0, [])}), "a")
        self.assertEqual(suggest(variants, {"a": (0, []), "b": (0, [])}), "b")
        tie = {
            "a": [("TM句对", "r1", "EN", "a")],
            "b": [("Terms", "r2", "EN", "b")],
        }
        self.assertEqual(suggest(tie, {"a": (0, []), "b": (0, [])}), "")


if __name__ == "__main__":
    unittest.main()
