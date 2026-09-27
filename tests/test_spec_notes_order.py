"""Spec trailer order: the default template and its footnotes-first variant.

The approved prints disagree on what comes first under the specification
tables: the footnotes, or notes such as the ※ USB-IF trademark note. The
HTML order (Web, and the Word bundle that takes its order from the HTML)
follows the template the target's page_registry.csv ``spec`` row names. The
LaTeX branch, which feeds the PDF and the IDML, is the same in both.
"""

from __future__ import annotations

import csv
import re
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from tools.csv_pages import BuildPaths, BuildSelector, CsvPageBuilder, renderers


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "docs" / "templates"
DEFAULT_TEMPLATE = "spec_template.rst"
FOOTNOTES_FIRST_TEMPLATE = "spec_template_footnotes_first.rst"
HTML_BRANCH = ".. only:: html"
TRAILER_KIND_RE = re.compile(r'data-spec-trailer-kind="(note|footnote)"')

# Frozen sources whose print sets the footnotes above the ※ note, with a
# language whose spec page renders both kinds. JE-1000F: the FR/ES/DE/IT
# blocks do; its EN block prints the ※ note first but builds review-asis.
FOOTNOTES_FIRST_SOURCES = {
    "manual_sources/JE-1000H/EU/en/2.0": ("JE-1000H", "en"),
    "manual_sources/JE-2000F/EU/en/2.0": ("JE-2000F", "en"),
    "manual_sources/JE-3000C/EU/en/2.0": ("JE-3000C", "en"),
    "manual_sources/JE-1000F/EU/en-fr/2.0": ("JE-1000F", "fr"),
}
# Frozen sources whose print sets the ※ note first keep the default.
NOTES_FIRST_SOURCES = {
    "manual_sources/JE-2000E/EU/en/2.0": ("JE-2000E", "en"),
    "manual_sources/JE-3600A/EU/en/2026-05-25": ("JE-3600A", "en"),
}
REGISTRY_ROOTS = ("manual_sources", "data", "tests/fixtures")


def _template_text(name: str) -> str:
    return (TEMPLATES / name).read_bytes().decode("utf-8")


def _registry_rows(registry: Path) -> list[dict[str, str]]:
    with registry.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _spec_template_of(registry: Path) -> str | None:
    rows = [row for row in _registry_rows(registry) if row["page_id"] == "spec"]
    return rows[0]["template"] if rows else None


def _trailer_order(fragment: str) -> list[str]:
    order: list[str] = []
    for kind in TRAILER_KIND_RE.findall(fragment):
        if not order or order[-1] != kind:
            order.append(kind)
    return order


def _build_spec_page(source: str, model: str, lang: str, output_dir: Path) -> str:
    data_root = ROOT / source / "phase2"
    paths = replace(
        BuildPaths.from_root(ROOT),
        page_registry=data_root / "page_registry.csv",
        page_blocks_dir=data_root,
        output_dir=output_dir,
        spec_master_csv=data_root / "Spec_Master.csv",
        spec_footnotes_csv=data_root / "Spec_Footnotes.csv",
        spec_notes_csv=data_root / "Spec_Notes.csv",
        spec_titles_csv=data_root / "spec_titles.csv",
        localized_copy_csv=data_root / "Localized_Copy.csv",
    )
    result = CsvPageBuilder(paths).build(
        BuildSelector.from_args(models=model, regions="EU", pages="spec", langs=lang)
    )
    (written,) = result.written_files
    return written.read_text(encoding="utf-8")


class SpecTemplateParityTests(unittest.TestCase):
    def test_variant_differs_from_default_only_in_html_trailer_order(self) -> None:
        default = _template_text(DEFAULT_TEMPLATE)
        variant = _template_text(FOOTNOTES_FIRST_TEMPLATE)
        notes, footnotes = renderers.PH_SPEC_NOTES_HTML, renderers.PH_SPEC_FOOTNOTES_HTML
        for text in (default, variant):
            self.assertEqual(1, text.count(HTML_BRANCH))
            self.assertEqual(1, text.count(notes))
            self.assertEqual(1, text.count(footnotes))
        self.assertLess(default.index(notes), default.index(footnotes))
        self.assertLess(variant.index(footnotes), variant.index(notes))
        self.assertEqual(default.split(HTML_BRANCH)[0], variant.split(HTML_BRANCH)[0])
        # Swapping the two HTML placeholders back gives the default byte for
        # byte, so an edit to either template has to be mirrored in the other.
        swapped = variant.replace(notes, "\0").replace(footnotes, notes).replace("\0", footnotes)
        self.assertEqual(default, swapped)


class SpecTemplateSelectionTests(unittest.TestCase):
    def test_declared_sources_name_the_footnotes_first_template(self) -> None:
        reference = _registry_rows(
            ROOT / next(iter(NOTES_FIRST_SOURCES)) / "phase2" / "page_registry.csv"
        )
        for source in FOOTNOTES_FIRST_SOURCES:
            with self.subTest(source=source):
                rows = _registry_rows(ROOT / source / "phase2" / "page_registry.csv")
                self.assertEqual(
                    FOOTNOTES_FIRST_TEMPLATE,
                    next(row for row in rows if row["page_id"] == "spec")["template"],
                )
                # The spec template cell is the registry's only difference.
                for row in rows:
                    if row["page_id"] == "spec":
                        row["template"] = DEFAULT_TEMPLATE
                self.assertEqual(reference, rows)

    def test_other_registries_keep_the_default_template(self) -> None:
        for source in NOTES_FIRST_SOURCES:
            with self.subTest(source=source):
                self.assertEqual(
                    DEFAULT_TEMPLATE,
                    _spec_template_of(ROOT / source / "phase2" / "page_registry.csv"),
                )
        declared = {
            ROOT / source / "phase2" / "page_registry.csv" for source in FOOTNOTES_FIRST_SOURCES
        }
        for base in REGISTRY_ROOTS:
            for registry in sorted((ROOT / base).rglob("page_registry.csv")):
                if registry in declared:
                    continue
                with self.subTest(registry=registry.relative_to(ROOT).as_posix()):
                    self.assertNotEqual(FOOTNOTES_FIRST_TEMPLATE, _spec_template_of(registry))


class SpecTrailerRenderOrderTests(unittest.TestCase):
    NOTE = "※ Demo trademark note."
    FOOTNOTE = "Demo footnote text."

    def _blocks(self) -> list[dict[str, str]]:
        def block(block_type: str, order: str, text: str) -> dict[str, str]:
            return {
                "block_type": block_type,
                "order": order,
                "sku_scope": "ALL",
                "enabled": "1",
                "meta_json": "{}",
                "text_en": text,
            }

        return [
            block("title_main", "100", "SPECIFICATIONS"),
            block("section_title", "110", "GENERAL INFO"),
            block("row_item", "111", "Model No. || DEMO-1000"),
            block("note_line", "150", self.NOTE),
            block("footnote", "160", self.FOOTNOTE),
        ]

    def _render(self, template_name: str) -> tuple[str, str]:
        out = renderers.render_spec_page(
            template=_template_text(template_name),
            blocks=self._blocks(),
            sku_id="",
            lang="en",
            vars_map={},
        )
        latex, html = out.split(HTML_BRANCH)
        return latex, html

    def test_variant_renders_footnotes_before_notes_in_html(self) -> None:
        _latex, default_html = self._render(DEFAULT_TEMPLATE)
        _latex, variant_html = self._render(FOOTNOTES_FIRST_TEMPLATE)
        self.assertLess(default_html.index(self.NOTE), default_html.index(self.FOOTNOTE))
        self.assertLess(variant_html.index(self.FOOTNOTE), variant_html.index(self.NOTE))
        self.assertEqual(["note", "footnote"], _trailer_order(default_html))
        self.assertEqual(["footnote", "note"], _trailer_order(variant_html))

    def test_both_templates_render_the_same_latex(self) -> None:
        default_latex, _html = self._render(DEFAULT_TEMPLATE)
        variant_latex, _html = self._render(FOOTNOTES_FIRST_TEMPLATE)
        self.assertEqual(default_latex, variant_latex)
        # \HBSpecPageEnd rides on the footnote block, which stays last in LaTeX.
        self.assertLess(default_latex.index(self.NOTE), default_latex.index(self.FOOTNOTE))
        self.assertGreater(default_latex.index(r"\HBSpecPageEnd"), default_latex.index(self.FOOTNOTE))

    def test_frozen_sources_render_their_printed_html_order(self) -> None:
        cases = [(source, *target, ["footnote", "note"]) for source, target in FOOTNOTES_FIRST_SOURCES.items()]
        cases += [(source, *target, ["note", "footnote"]) for source, target in NOTES_FIRST_SOURCES.items()]
        for source, model, lang, expected in cases:
            with self.subTest(model=model, lang=lang), tempfile.TemporaryDirectory() as tmp:
                page = _build_spec_page(source, model, lang, Path(tmp))
                latex, html = page.split(HTML_BRANCH)
                self.assertEqual(expected, _trailer_order(html))
                notes_at = latex.index(r"HBcomp_spec_notes_before")
                self.assertLess(notes_at, latex.index(r"HBcomp_spec_footnotes_before"))


if __name__ == "__main__":
    unittest.main()
