"""Tests for tools/idml/text_clean.py (P1 content parity)."""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from tools.idml.text_clean import VariableSubstituter, clean_cell, strip_rst_inline


class StripRstInlineTest(unittest.TestCase):
    def test_sub_and_sup_roles_render_as_plain_text(self) -> None:
        self.assertEqual(
            "the open-circuit voltage (Voc) of the panel",
            strip_rst_inline(r"the open-circuit voltage (V\ :sub:`oc`) of the panel"),
        )
        self.assertEqual("10 m2", strip_rst_inline(r"10 m\ :sup:`2`"))

    def test_line_block_pipes_are_removed(self) -> None:
        self.assertEqual(
            "1. Remove all DC inputs.\n2. Restart the product.",
            strip_rst_inline("| 1. Remove all DC inputs.\n| 2. Restart the product."),
        )


class VariableSubstituterTest(unittest.TestCase):
    def _data_root(self, root: Path) -> Path:
        (root / "Variable_Defaults.csv").write_text(
            "Variable_key,Model_key,Model,Value,is_default\n"
            'AC_POWER_BUTTON_LABEL,"JE-1000F","",AC,FALSE\n'
            "AC_POWER_BUTTON_LABEL,,,AC1/2,TRUE\n",
            encoding="utf-8",
        )
        fixture = Path(__file__).parent / "fixtures" / "phase2" / "Spec_Master.csv"
        shutil.copyfile(fixture, root / "Spec_Master.csv")
        return root

    def test_resolves_from_variable_tables_and_spec_master(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = self._data_root(Path(td))
            subst = VariableSubstituter(root, model="JE-1000F", lang="en", region="US")
            self.assertEqual(
                "Press the AC button on the Jackery Explorer 1000.",
                subst.apply("Press the {{AC_POWER_BUTTON_LABEL}} button on the {{PRODUCT_NAME}}."),
            )

    def test_unresolved_placeholder_is_left_intact(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = self._data_root(Path(td))
            subst = VariableSubstituter(root, model="JE-1000F", lang="en", region="US")
            self.assertEqual("{{NO_SUCH_KEY}}", subst.apply("{{NO_SUCH_KEY}}"))

    def test_clean_cell_combines_strip_and_substitution(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = self._data_root(Path(td))
            subst = VariableSubstituter(root, model="JE-1000F", lang="en", region="US")
            self.assertEqual(
                "Voc of the Jackery Explorer 1000",
                clean_cell(r"| V\ :sub:`oc` of the {{PRODUCT_NAME}}", subst),
            )


if __name__ == "__main__":
    unittest.main()
