"""The one lang_<code>_ override cascade behind every IDML component.

Before consolidation each component re-derived the cascade with its own gate
({"fr","es"} literals beside governed_languages()), so a language entering
layout tuning was honored by half the components and ignored by the rest —
and one positional lookup crashed outright on a fourth honored language.

Two distinct language sets drive the behavior:
- governed_languages(): approved, reference-bound flow behavior.
- layout_override_languages(): whose lang_<code>_ rows the cascade honors —
  governed plus lines in active layout tuning (ko).
"""
from __future__ import annotations

from pathlib import Path
import unittest

from tools.idml.params import (
    load_layout_params,
    localized_component_param_pt,
    localized_param_pt,
)
from tools.idml.components.base import RenderContext
from tools.idml.components.prose_table import TroubleshootingTableStyle
from tools.idml.reference_story_flow import storage_first_top_offset
from tools.lang_registry import governed_languages, layout_override_languages

ROOT = Path(__file__).resolve().parents[1]


def _params(**overrides: tuple[str, str]) -> dict[str, tuple[str, str]]:
    params = {"idml_gap": ("10.0", "pt")}
    params.update(overrides)
    return params


class LocalizedParamTests(unittest.TestCase):
    def test_ko_is_honored_by_the_cascade_but_not_governed(self) -> None:
        self.assertNotIn("ko", governed_languages())
        self.assertIn("ko", layout_override_languages())
        params = _params(lang_ko_idml_gap=("12.5", "pt"))
        self.assertEqual(
            12.5, localized_param_pt(params, "idml_gap", 0.0, language="ko"),
        )

    def test_honored_language_without_a_row_keeps_the_base_value(self) -> None:
        self.assertEqual(
            10.0, localized_param_pt(_params(), "idml_gap", 0.0, language="ko"),
        )

    def test_unhonored_language_rows_are_not_read(self) -> None:
        params = _params(lang_de_idml_gap=("12.5", "pt"))
        self.assertNotIn("de", layout_override_languages())
        self.assertEqual(
            10.0, localized_param_pt(params, "idml_gap", 0.0, language="de"),
        )

    def test_region_subtags_resolve_to_the_honored_base_language(self) -> None:
        params = _params(lang_fr_idml_gap=("11.0", "pt"))
        self.assertEqual(
            11.0, localized_param_pt(params, "idml_gap", 0.0, language="fr-CA"),
        )

    def test_component_base_token_keeps_caller_strictness(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing required layout token"):
            localized_component_param_pt(
                {}, "idml_gap", 0.0,
                language="ko", strict=True, owner="cascade test",
            )

    def test_contract_language_override_row_is_strict_required(self) -> None:
        with self.assertRaisesRegex(
            ValueError, "missing required layout token: lang_fr_idml_gap",
        ):
            localized_component_param_pt(
                _params(), "idml_gap", 0.0,
                language="fr", strict=True, owner="cascade test",
                contract_languages=frozenset({"fr"}),
            )

    def test_tuning_language_builds_before_its_rows_exist(self) -> None:
        value = localized_component_param_pt(
            _params(), "idml_gap", 0.0,
            language="ko", strict=True, owner="cascade test",
            contract_languages=frozenset({"fr"}),
        )
        self.assertEqual(10.0, value)


class GovernedCascadeConsumerTests(unittest.TestCase):
    def _style(self, params: dict[str, tuple[str, str]]) -> TroubleshootingTableStyle:
        ctx = RenderContext(
            params=params,
            page_w=368.79,
            m_l=28.35,
            m_r=28.35,
            root=ROOT,
            bundle_root=ROOT / "docs",
            language="ko",
        )
        return TroubleshootingTableStyle.from_context(ctx)

    def test_trouble_space_before_survives_a_fourth_honored_language(self) -> None:
        """governed.index() over a positional 3-tuple raised IndexError for ko."""
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        style = self._style(params)
        self.assertEqual(style.table_space_before("en"), style.table_space_before("ko"))
        for language in layout_override_languages():
            self.assertIsInstance(style.table_space_before(language), float)

    def test_trouble_space_before_honors_a_ko_tuning_row(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        params["lang_ko_idml_trouble_table_space_before"] = ("5.55", "pt")
        self.assertEqual(5.55, self._style(params).table_space_before("ko"))

    def test_trouble_row_minima_honor_a_ko_tuning_row(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        params["lang_ko_idml_trouble_row_minima"] = (
            ";".join(["19.5"] * 12), "text",
        )
        style = self._style(params)
        self.assertEqual((19.5,) * 12, style.row_minima)

    def test_storage_offset_is_reference_flow_behavior_not_tuning(self) -> None:
        """The approved continuation offset stays governed-gated: a tuning
        language keeps measured flow, so it gets no offset even with a row."""
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        self.assertEqual(16.87, storage_first_top_offset(params, "en"))
        self.assertEqual(0.0, storage_first_top_offset(params, "de"))
        self.assertEqual(0.0, storage_first_top_offset(params, "ko"))
        params["lang_ko_idml_storage_page_top_offset"] = ("9.9", "pt")
        self.assertEqual(0.0, storage_first_top_offset(params, "ko"))


if __name__ == "__main__":
    unittest.main()
