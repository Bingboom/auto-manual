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

from hb_latex_callouts import (  # noqa: E402
    HBCallout,
    HBCalloutItem,
    replace_notice_tables,
    visit_callout_item_latex,
)


class LatexCalloutTests(unittest.TestCase):
    def _transform(self, source: str, *, output_format: str = "latex") -> nodes.document:
        doctree = publish_doctree(source)
        app = SimpleNamespace(builder=SimpleNamespace(format=output_format))
        replace_notice_tables(app, doctree, "test")
        return doctree

    def test_replaces_all_four_notice_variants_and_localized_labels(self) -> None:
        for label, variant in (
            ("WARNING", "warning"),
            ("CAUTION", "caution"),
            ("NOTE", "note"),
            ("TIP", "tip"),
            ("AVERTISSEMENT", "warning"),
            ("ATTENTION", "caution"),
            ("REMARQUE", "note"),
            ("CONSEJOS", "tip"),
            ("PRECAUCIÓN", "caution"),
            ("NOTA", "note"),
        ):
            doctree = self._transform(
                f""".. list-table::
   :header-rows: 0
   :widths: 12 88

   * - **{label}**
     - Keep the product safe.
"""
            )
            callouts = list(doctree.findall(HBCallout))
            self.assertEqual(1, len(callouts), label)
            self.assertEqual(variant, callouts[0]["variant"])
            self.assertEqual(label, callouts[0]["label"])

    def test_flattens_nested_notice_lists_into_callout_items(self) -> None:
        doctree = self._transform(
            """.. list-table::
   :header-rows: 0
   :widths: 12 88

   * - **CAUTION**
     - - First item.
       - Second item.

         - Nested detail.
"""
        )

        self.assertEqual(3, len(list(doctree.findall(HBCalloutItem))))

    def test_keeps_regular_tables_and_non_latex_builders_unchanged(self) -> None:
        regular = self._transform(
            """.. list-table::

   * - Name
     - Value
"""
        )
        html_notice = self._transform(
            """.. list-table::

   * - **NOTE**
     - Body
""",
            output_format="html",
        )

        self.assertEqual(1, len(list(regular.findall(nodes.table))))
        self.assertEqual(1, len(list(html_notice.findall(nodes.table))))

    def test_callout_item_opener_keeps_tex_content_off_comment_line(self) -> None:
        translator = SimpleNamespace(body=[])

        visit_callout_item_latex(translator, HBCalloutItem())

        self.assertEqual(["\\HBCalloutBullet{%\n"], translator.body)

    def test_callout_geometry_keeps_border_and_list_alignment_parameterized(self) -> None:
        params = (ROOT / "data" / "layout_params.csv").read_text(encoding="utf-8")
        component = (ROOT / "docs" / "renderers" / "latex" / "components_base.tex").read_text(
            encoding="utf-8"
        )

        self.assertIn("comp_callout_rule,1.2,pt", params)
        self.assertIn("comp_callout_label_inset,1.2,mm", params)
        self.assertIn("colback=BgK05,\n    colframe=BgK05", component)
        self.assertIn("HBcomp_callout_body_inset", component)
        self.assertIn("HBcomp_callout_bullet_indent", component)
        self.assertIn("HBcomp_callout_bullet_width", component)


if __name__ == "__main__":
    unittest.main()
