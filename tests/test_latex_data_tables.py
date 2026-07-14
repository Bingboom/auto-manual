from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import sys
import unittest

from docutils import nodes
from docutils.core import publish_doctree


ROOT = Path(__file__).resolve().parents[1]
LATEX_RENDERER = ROOT / "docs" / "renderers" / "latex"
if str(LATEX_RENDERER) not in sys.path:
    sys.path.insert(0, str(LATEX_RENDERER))

from hb_latex_data_tables import (  # noqa: E402
    HBDataCell,
    HBDataHangingLine,
    HBDataRow,
    HBDataSectionGuard,
    HBDataTable,
    replace_data_tables,
)


DATA_TABLE_RST = r"""MANUAL
======

AC AND DC OUTPUT RESUME FUNCTION
--------------------------------

+----------------------+----------------------+
| Auto Resume          | Not Auto Resume      |
+======================+======================+
| First                | Right one            |
+----------------------+----------------------+
| Battery              | Right two            |
|                      +----------------------+
|                      | Right three          |
+----------------------+----------------------+
| Last                 | Right four           |
+----------------------+----------------------+

KEY COMBINATIONS
----------------

.. list-table::
   :header-rows: 1
   :widths: 40 25 35

   * - Buttons
     - Operation
     - Function
   * - Main POWER + AC
     - Hold 3s
     - Energy Saving Mode

TROUBLESHOOTING
---------------

.. list-table::
   :class: longtable
   :header-rows: 1
   :widths: 14 86

   * - Error Code
     - Corrective Measures
   * - F0
     - Restart the product.
   * - F6
     - | 1. First step.
       | 2. Check V\ :sub:`oc` now.
"""


class LatexDataTableTests(unittest.TestCase):
    def _transform(self, source: str, *, output_format: str = "latex") -> nodes.document:
        doctree = publish_doctree(source)
        app = SimpleNamespace(builder=SimpleNamespace(format=output_format))
        replace_data_tables(app, doctree, "test")
        return doctree

    def test_maps_all_body_table_families_to_shared_component_nodes(self) -> None:
        doctree = self._transform(DATA_TABLE_RST)

        tables = list(doctree.findall(HBDataTable))
        self.assertEqual(
            ["auto_resume", "key_combinations", "troubleshooting"],
            [table["kind"] for table in tables],
        )
        self.assertEqual(0, len(list(doctree.findall(nodes.table))))
        self.assertEqual(
            ["key_combinations", "troubleshooting"],
            [guard["kind"] for guard in doctree.findall(HBDataSectionGuard)],
        )

    def test_preserves_row_spans_and_hanging_numbered_measures(self) -> None:
        doctree = self._transform(DATA_TABLE_RST)

        spanning_cells = [
            cell for cell in doctree.findall(HBDataCell) if cell["rowspan"] > 1
        ]
        self.assertEqual(1, len(spanning_cells))
        self.assertEqual(2, spanning_cells[0]["rowspan"])

        hanging = list(doctree.findall(HBDataHangingLine))
        self.assertEqual(["1", "2"], [line["number"] for line in hanging])
        self.assertEqual(1, len(list(hanging[1].findall(nodes.subscript))))

        continuation_rows = [
            row for row in doctree.findall(HBDataRow) if row["continuations"]
        ]
        self.assertEqual([[0]], [row["continuations"] for row in continuation_rows])

    def test_keeps_non_latex_and_unrecognized_tables_unchanged(self) -> None:
        html_tree = self._transform(DATA_TABLE_RST, output_format="html")
        other_tree = self._transform(
            "MANUAL\n======\n\nOTHER\n-----\n\n"
            ".. list-table::\n\n   * - A\n     - B\n"
        )

        self.assertGreater(len(list(html_tree.findall(nodes.table))), 0)
        self.assertEqual(0, len(list(html_tree.findall(HBDataTable))))
        self.assertEqual(1, len(list(other_tree.findall(nodes.table))))

    def test_component_reuses_shared_rounded_table_frame(self) -> None:
        params = (ROOT / "data" / "layout_params.csv").read_text(encoding="utf-8")
        component = (
            ROOT / "docs" / "renderers" / "latex" / "components_data_tables.tex"
        ).read_text(encoding="utf-8")

        self.assertIn("comp_trouble_left_ratio,0.11,ratio", params)
        self.assertIn("comp_data_table_row_stretch,1.0,ratio", params)
        self.assertIn("comp_table_text_indent,5.2,pt", params)
        self.assertIn("begin{HBSharedDataTable}", component)
        self.assertIn("HBcomp_table_text_indent", component)
        self.assertIn("HBDataHangingLine", component)
        self.assertIn(r"\parbox[c][#1][c]", component)
        self.assertIn("HBDataNaturalCenteredCell", component)
        self.assertIn(r">{\centering\arraybackslash}m{", component)
        self.assertNotIn(r"\begin{tabularx}{\linewidth}{@{}p{", component)
        self.assertNotIn("newtcolorbox", component)


if __name__ == "__main__":
    unittest.main()
