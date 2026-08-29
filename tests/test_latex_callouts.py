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

    def test_plural_notice_labels_are_recognised_so_the_box_survives(self) -> None:
        """An unrecognised label does not warn — it silently loses the box.

        replace_notice_tables converts a notice table only when
        variant_for_label returns a variant; otherwise it leaves the table
        alone and LaTeX emits \\sphinxstylestrong{LABEL} while Word emits
        loose paragraphs. Nothing appears in any log. The shipped books print
        the plural for a multi-item notes block, and `tip` already carried
        TIPS / CONSEILS / CONSEJOS while `note` did not — so every plural
        notes callout in the corpus was flattened.
        """
        from tools.component_specs.callout import variant_for_label

        for label, expected in (
            ("NOTE", "note"), ("NOTES", "note"),
            ("REMARQUE", "note"), ("REMARQUES", "note"),
            ("NOTA", "note"), ("NOTAS", "note"),
            ("TIP", "tip"), ("TIPS", "tip"),
            ("CONSEIL", "tip"), ("CONSEILS", "tip"),
            ("CONSEJO", "tip"), ("CONSEJOS", "tip"),
        ):
            with self.subTest(label=label):
                self.assertEqual(expected, variant_for_label(label))

    def test_every_registered_language_signal_word_resolves(self) -> None:
        """The reverse index closes what the en/fr/es-only map used to drop.

        These are the exact labels the corpus survey measured losing their box
        in every renderer except Word — 78 of 156 authored callouts, with
        de/ko/uk/zh at 100% loss. The data plane (Localized_Copy +
        symbols_blocks through tools.signal_words, fixture fallback in CI)
        supplies them; the zh 提示 collision (note vs tips both print it)
        resolves to note, matching the Word pipeline's setdefault behaviour.
        """
        from tools.component_specs.callout import variant_for_label

        for label, expected in (
            ("VORSICHT", "caution"), ("HINWEIS", "note"),     # de
            ("주의", "caution"), ("참고", "note"),              # ko
            ("경고", "warning"), ("위험", "danger"),            # ko
            ("УВАГА", "caution"), ("ПРИМІТКА", "note"),        # uk
            ("注意", "caution"), ("提示", "note"),              # zh (collision -> note)
            ("备注", "note"), ("说明", "note"),                 # zh synonyms (static)
            ("警告", "warning"), ("ご注意", "caution"),          # ja / zh
            ("備考", "note"),                                   # ja
            ("ATTENZIONE", "caution"), ("AVVERTENZA", "warning"),  # it
            ("CUIDADO", "caution"), ("AVISO", "warning"),      # pt-BR
            ("GEFAHR", "danger"), ("PERICOLO", "danger"),      # de / it
        ):
            with self.subTest(label=label):
                self.assertEqual(expected, variant_for_label(label))

    def test_an_unrecognised_label_leaves_the_table_unconverted(self) -> None:
        """Pin the degradation itself, so the cost of a missing label is visible.

        Every registered language now resolves through the data index, so the
        control must be a label no language registers. The MECHANISM this pins
        is unchanged: an unknown label means replace_notice_tables declines,
        LaTeX emits \\sphinxstylestrong{LABEL}, Word emits loose paragraphs,
        and nothing appears in any log.
        """
        from tools.component_specs.callout import variant_for_label

        self.assertIsNone(variant_for_label("NOT A SIGNAL WORD"))

        source = (
            ".. list-table::\n"
            "   :header-rows: 0\n"
            "   :widths: 12 88\n"
            "\n"
            "   * - **NOT A SIGNAL WORD**\n"
            "     - Something worth boxing.\n"
        )
        doctree = self._transform(source)

        self.assertEqual([], list(doctree.findall(HBCallout)))
        self.assertEqual(1, len(list(doctree.findall(nodes.table))))

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
