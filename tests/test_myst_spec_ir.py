from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import tempfile
import subprocess
import sys
import unittest
from unittest.mock import patch

from bs4 import BeautifulSoup

from tools.manual_md_directives import SpecTableDirective, _inline_html
from tools.manual_ir import build_manual_ir_from_source, read_manual_ir, write_manual_ir
from tools.web_spec_component import render_specification_ir


def directive(rows, label="INPUT PORTS"):
    return SimpleNamespace(
        label=label,
        rows=lambda: rows,
        env=SimpleNamespace(config=SimpleNamespace(language="ja"), docname="manual"),
        lineno=7,
        aria=lambda: f' aria-label="{_inline_html(label)}"',
        error=lambda message: ValueError(message),
    )


class MystSpecIRTests(unittest.TestCase):
    def test_actual_directive_uses_public_ir_and_replays_serialized_input(self):
        observed = []

        def replay(ir):
            observed.append(ir)
            with tempfile.TemporaryDirectory() as tmp:
                return render_specification_ir(
                    read_manual_ir(write_manual_ir(ir, Path(tmp) / "ir.json"))
                )

        with (
            patch(
                "tools.web_spec_component.build_manual_ir_from_source",
                wraps=build_manual_ir_from_source,
            ) as assemble,
            patch(
                "tools.web_spec_component.render_specification_ir", side_effect=replay
            ),
        ):
            output = SpecTableDirective.run(
                directive(
                    [
                        ["AC", "12 A ^①^"],
                        ["", "100 V"],
                        ["DC", "V~oc~ **60 V**"],
                    ]
                )
            )[0].astext()
        assemble.assert_called_once()
        self.assertEqual("ja", observed[0].language)
        self.assertEqual("web-specifications", observed[0].metadata["projection"])
        self.assertIn("manual:7", observed[0].pages[0].source_ref)
        soup = BeautifulSoup(output, "html.parser")
        self.assertIsNone(soup.h2)
        self.assertEqual("INPUT PORTS", soup.figure["aria-label"])
        self.assertEqual("2", soup.th["rowspan"])
        self.assertEqual("①", soup.sup.text)
        self.assertIsNone(soup.select_one("sup sup"))
        self.assertEqual("oc", soup.sub.text)
        self.assertEqual("60 V", soup.strong.text)

    def test_plain_circled_notes_use_the_same_web_reference_style(self):
        html = SpecTableDirective.run(directive([["AC①", "12 A②"]]))[0].astext()
        soup = BeautifulSoup(html, "html.parser")
        self.assertEqual(
            ["①", "②"], [node.text for node in soup.select("sup.hb-spec-reference")]
        )
        self.assertEqual("AC①12 A②", "".join(soup.stripped_strings))

    def test_corrupt_ir_stops_directive_before_raw_html_return(self):
        def corrupt(source):
            return replace(build_manual_ir_from_source(source), content_sha256="0" * 64)

        with patch(
            "tools.web_spec_component.build_manual_ir_from_source", side_effect=corrupt
        ):
            with self.assertRaisesRegex(ValueError, "Manual IR"):
                SpecTableDirective.run(directive([["AC", "100 V"]]))

    def test_bad_rows_reject_instead_of_truncating(self):
        for rows, label in [
            ([["A", "B", "C"]], "Title"),
            ([["", "B"]], "Title"),
            ([], "Title"),
            ([["A", "B"]], ""),
        ]:
            with self.subTest(rows=rows, label=label), self.assertRaises(ValueError):
                SpecTableDirective.run(directive(rows, label))

    def test_isolated_sphinx_uses_staged_ir_and_rejects_corrupt_input(self):
        from tools.plain_markdown_site import stage_component_extension, write_conf_py

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            source.mkdir()
            (source / "_static").mkdir()
            self.assertTrue(stage_component_extension(source))
            conf = write_conf_py(source, title="Manual")
            with conf.open("a") as stream:
                stream.write("""
from tools import web_spec_component as spec_ir
from tools.manual_ir import write_manual_ir
from dataclasses import replace
original_assemble = spec_ir.build_manual_ir_from_source
def capture(source):
    ir = original_assemble(source)
    write_manual_ir(ir, Path(__file__).parent / 'captured.json')
    return ir
spec_ir.build_manual_ir_from_source = capture
""")
            (source / "index.md").write_text(
                "# Manual\n\n```{spec-table} 入力ポート\nAC | 100 V ^①^\n | **12 A**\nDC | V~oc~ 60 V\n```\n"
            )
            command = [
                sys.executable,
                "-I",
                "-m",
                "sphinx",
                "-E",
                "-W",
                "-b",
                "html",
                str(source),
                str(root / "html"),
            ]
            result = subprocess.run(command, cwd=root, text=True, capture_output=True)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            ir = read_manual_ir(source / "captured.json")
            self.assertEqual("web-specifications", ir.metadata["projection"])
            output = BeautifulSoup(
                (root / "html/index.html").read_text(), "html.parser"
            )
            figure = output.select_one("figure.hb-spec-table-composition")
            self.assertEqual("入力ポート", figure["aria-label"])
            self.assertEqual("2", figure.th["rowspan"])
            self.assertEqual("①", figure.sup.text)
            self.assertEqual("oc", figure.sub.text)
            self.assertEqual("12 A", figure.strong.text)
            with conf.open("a") as stream:
                stream.write(
                    "\nspec_ir.build_manual_ir_from_source = lambda source: replace(original_assemble(source), content_sha256='0' * 64)\n"
                )
            rejected = subprocess.run(command, cwd=root, text=True, capture_output=True)
            self.assertNotEqual(0, rejected.returncode)
            self.assertIn("Manual IR", rejected.stdout + rejected.stderr)


if __name__ == "__main__":
    unittest.main()
