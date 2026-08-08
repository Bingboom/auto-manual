from __future__ import annotations

from pathlib import Path
import re
import subprocess
import sys
from types import SimpleNamespace
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
    visit_callout_latex,
    visit_callout_item_latex,
)
from tools import lang_registry  # noqa: E402


class LatexCalloutTests(unittest.TestCase):
    def test_extension_imports_from_sphinx_console_path(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "-I",
                "-c",
                (
                    "import sys; "
                    f"sys.path.insert(0, {str(LATEX_RENDERER)!r}); "
                    "import hb_latex_callouts"
                ),
            ],
            cwd=Path("/tmp"),
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)

    def test_hb_apply_lang_has_a_warning_label_for_every_registered_language(self) -> None:
        source = (LATEX_RENDERER / "components_safety.tex").read_text(encoding="utf-8")
        for spec in lang_registry.LANGUAGE_REGISTRY:
            with self.subTest(language=spec.code):
                pack = lang_registry.idml_language_pack(spec.code)
                self.assertIsNotNone(pack)
                assert pack is not None
                label = pack.symbol_copy[3]
                if spec.code == "en":
                    self.assertIn(
                        r"\renewcommand{\HBLocalizedWarningLabel}{WARNING}",
                        source,
                    )
                    continue
                self.assertRegex(
                    source,
                    re.compile(
                        rf"\\ifstrequal\{{#1\}}\{{{re.escape(spec.code)}\}}"
                        rf"\{{\\renewcommand\{{\\HBLocalizedWarningLabel\}}"
                        rf"\{{{re.escape(label)}\}}\}}\{{\}}%"
                    ),
                )

    def _transform(self, source: str, *, output_format: str = "latex") -> nodes.document:
        doctree = publish_doctree(source)
        app = SimpleNamespace(builder=SimpleNamespace(format=output_format))
        replace_notice_tables(app, doctree, "test")
        return doctree

    def test_replaces_all_five_notice_variants_and_localized_labels(self) -> None:
        for label, variant in (
            ("WARNING", "warning"),
            ("DANGER", "danger"),
            ("CAUTION", "caution"),
            ("NOTE", "note"),
            ("TIP", "tip"),
            ("AVERTISSEMENT", "warning"),
            ("ATTENTION", "caution"),
            ("REMARQUE", "note"),
            ("CONSEJOS", "tip"),
            ("PELIGRO", "danger"),
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

    def test_all_five_variants_dispatch_through_component_adapter(self) -> None:
        expected = {
            "WARNING": "HBWarningBlock",
            "DANGER": "HBWarningBlock",
            "CAUTION": "HBCautionBlock",
            "NOTE": "HBNoteBlock",
            "TIP": "HBTipBlock",
        }
        for label, macro in expected.items():
            with self.subTest(label=label):
                doctree = self._transform(
                    f""".. list-table::
   :header-rows: 0

   * - **{label}**
     - Keep the product safe.
"""
                )
                callout = next(iter(doctree.findall(HBCallout)))
                translator = SimpleNamespace(body=[], encode=lambda value: value)
                visit_callout_latex(translator, callout)
                self.assertEqual(
                    [f"\n\\{macro}{{{label}}}{{%\n"],
                    translator.body,
                )

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
        self.assertIn("comp_callout_label_inset,0.44,mm", params)
        self.assertIn("comp_tip_pad_lr,1.15,mm", params)
        self.assertIn("comp_tip_label_baseline_shift,-0.57,pt", params)
        self.assertIn("type_tip_body_horizontal_scale,1.069,ratio", params)
        self.assertIn("colback=BgK05,\n    colframe=BgK05", component)
        self.assertIn("HBcomp_callout_body_inset", component)
        self.assertIn("HBcomp_callout_bullet_indent", component)
        self.assertIn("HBcomp_callout_bullet_width", component)
        self.assertIn(
            "height from={#4} to {\\textheight}",
            component,
        )
        self.assertIn(
            "\\HBCalloutBlock{#1}{#2}{\\csname HBcomp_caution_label_width\\endcsname}{0pt}",
            component,
        )
        self.assertIn(
            "{\\csname HBcomp_tip_height\\endcsname}",
            component,
        )
        self.assertIn("\\begin{minipage}[c]{\\linewidth}", component)
        self.assertIn("\\setlength{\\parskip}{0pt}", component)
        self.assertIn("sidebyside align=center", component)
        self.assertIn(
            "sidebyside gap=\\csname HBcomp_callout_body_inset\\endcsname",
            component,
        )
        self.assertIn("valign lower=center", component)
        self.assertIn("\\node[anchor=base,inner sep=0pt]", component)
        self.assertIn(
            "xshift=\\dimexpr(#3+\\csname HBcomp_callout_label_inset",
            component,
        )
        self.assertIn("yshift=\\csname HBcomp_tip_label_baseline_shift", component)
        self.assertIn("\\HBFontBold", component)
        self.assertIn("\\HBFontMedium", component)
        self.assertIn("FakeStretch=\\csname HBtype_tip_body_horizontal_scale", component)
        self.assertIn("lefthand width=#3", component)


if __name__ == "__main__":
    unittest.main()
