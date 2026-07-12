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

from hb_latex_warranty import (  # noqa: E402
    HBWarrantyLead,
    HBWarrantyPage,
    HBWarrantySection,
    HBWarrantyYearColumn,
    HBWarrantyYears,
    replace_warranty_page,
)


WARRANTY_RST = r"""WARRANTY
========

**Official-channel purchases only.**

\*Details may vary.

Limited Warranty
----------------

Jackery's warranty body.

Warranty Period
---------------

.. list-table::
   :header-rows: 0
   :widths: 50 50

   * - **3 YEARS**

       **Standard Warranty**

       Standard period body.

     - **2 YEARS**

       **Extended Warranty**

       Extended period body.

Exclusions
----------

- First exclusion.
"""


class LatexWarrantyTests(unittest.TestCase):
    def _transform(self, source: str, *, output_format: str = "latex") -> nodes.document:
        doctree = publish_doctree(source)
        app = SimpleNamespace(builder=SimpleNamespace(format=output_format))
        replace_warranty_page(app, doctree, "test")
        return doctree

    def test_builds_dedicated_page_lead_sections_and_year_columns(self) -> None:
        doctree = self._transform(WARRANTY_RST)

        self.assertEqual(1, len(list(doctree.findall(HBWarrantyPage))))
        self.assertEqual(1, len(list(doctree.findall(HBWarrantyLead))))
        self.assertEqual(3, len(list(doctree.findall(HBWarrantySection))))
        self.assertEqual(1, len(list(doctree.findall(HBWarrantyYears))))

        columns = list(doctree.findall(HBWarrantyYearColumn))
        self.assertEqual(["3", "2"], [column["number"] for column in columns])
        self.assertEqual(["YEARS", "YEARS"], [column["unit"] for column in columns])
        self.assertEqual(
            ["Standard Warranty", "Extended Warranty"],
            [column["subtitle"] for column in columns],
        )
        self.assertEqual(
            [1, 2, 3],
            [panel["index"] for panel in doctree.findall(HBWarrantySection)],
        )
        raw_latex = [node.astext() for node in doctree.findall(nodes.raw)]
        self.assertIn(r"\textquotesingle{}", raw_latex)

    def test_keeps_non_latex_and_non_warranty_sections_unchanged(self) -> None:
        html_tree = self._transform(WARRANTY_RST, output_format="html")
        other_tree = self._transform("APP SETUP\n=========\n\nBody.\n")

        self.assertEqual(0, len(list(html_tree.findall(HBWarrantyPage))))
        self.assertEqual(0, len(list(other_tree.findall(HBWarrantyPage))))
        self.assertGreater(len(list(html_tree.findall(nodes.section))), 0)
        self.assertGreater(len(list(other_tree.findall(nodes.title))), 0)

    def test_component_geometry_is_parameterized(self) -> None:
        params = (ROOT / "data" / "layout_params.csv").read_text(encoding="utf-8")
        component = (
            ROOT / "docs" / "renderers" / "latex" / "components_warranty.tex"
        ).read_text(encoding="utf-8")

        self.assertIn("comp_warranty_section_rule,0.9,pt", params)
        self.assertIn("comp_warranty_year_badge_size,8.4,mm", params)
        self.assertIn("attach boxed title to top left", component)
        self.assertIn("HBWarrantyYearBadge", component)
        self.assertIn("HBWarrantyPageEnd", component)


if __name__ == "__main__":
    unittest.main()
