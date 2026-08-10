from __future__ import annotations

import ast
import inspect
import json
import tempfile
import unittest
from pathlib import Path

from tools.export_idml import IdmlWriter, load_layout_params
from tools.idml import (
    app_inline,
    data_components,
    data_stories,
    ir_projection,
    page_placed,
    page_toc,
)
from tools.idml.components.reference_figure import _fallback as reference_figure_fallback
from tools.idml.flow_idml import _component_fallback_text
from tools.idml.oppanel import _duration_label
from tools.idml_rst_extract import extract_page
from tools.manual_ir import build_manual_ir


ROOT = Path(__file__).resolve().parents[1]
IDML_PYTHON = (
    *sorted((ROOT / "tools" / "idml").rglob("*.py")),
    ROOT / "tools" / "idml_rst_extract.py",
    ROOT / "tools" / "idml_rst_tables.py",
    ROOT / "tools" / "export_idml.py",
)


class _MissingAssetContext:
    def resolve_bundle_image(self, *_args, **_kwargs):
        return None


class _MissingAssetWriter:
    strict_component_assets = False
    params: dict[str, tuple[str, str]] = {}

    def _render_context(self, *_args, **_kwargs):
        return _MissingAssetContext()


class IdmlVisibleCopyBehaviorTests(unittest.TestCase):
    def test_unknown_component_does_not_publish_internal_kind(self) -> None:
        self.assertEqual("", _component_fallback_text({"kind": "internal_widget"}))
        self.assertEqual("", _component_fallback_text({}))
        self.assertEqual(
            "Source label\nSource body",
            _component_fallback_text({
                "kind": "internal_widget",
                "label": "Source label",
                "texts": ["Source body"],
            }),
        )

    def test_reference_figure_has_no_renderer_placeholder_copy(self) -> None:
        xml, height = reference_figure_fallback({}, tid="missing_copy", terminal=True)
        self.assertEqual("", xml)
        self.assertEqual(0.0, height)

    def test_duration_is_only_derived_from_source_action(self) -> None:
        self.assertEqual("3s", _duration_label("Press and hold for 3 seconds."))
        self.assertEqual("", _duration_label("Press and hold both buttons."))

    def test_toc_parser_does_not_invent_a_missing_title(self) -> None:
        payload = data_components.parse_data_component(
            r"\HBTocPageBegin\HBTocLanguageBlock{EN}{English}{01--01}{}{}"
        )
        self.assertIsNotNone(payload)
        assert payload is not None
        self.assertEqual("", payload["title"])

    def test_fcc_extractor_does_not_synthesize_a_visible_heading(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            page = Path(td) / "fcc.rst"
            page.write_text(
                ".. raw:: latex\n\n"
                "   \\HBFccBlock{Source paragraph.}{First clause.}"
                "{Second clause.}\n",
                encoding="utf-8",
            )
            result = extract_page(page, {"latex"})

        self.assertNotIn(("h1", "FCC"), result.blocks)
        self.assertEqual("component", result.blocks[0][0])
        self.assertEqual("fcc", json.loads(result.blocks[0][1])["kind"])

    def test_safety_warning_label_is_not_inferred_from_macro_kind(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            page = Path(td) / "safety.rst"
            page.write_text(
                ".. raw:: latex\n\n"
                "   \\safetywarning{Source warning body.}\n",
                encoding="utf-8",
            )
            result = extract_page(page, {"latex"})

        payload = json.loads(result.blocks[0][1])
        self.assertEqual("safetywarning", payload["kind"])
        self.assertNotIn("label", payload)

    def test_approved_back_cover_keeps_region_fallback(self) -> None:
        writer = IdmlWriter(load_layout_params(ROOT / "data" / "layout_params.csv"))
        self.assertTrue(page_placed.add_back_cover_page(writer, "US", 0, None))
        stories = "".join(xml for _, xml in writer.stories)
        self.assertIn("JACKERY INC.", stories)
        self.assertIn("hello@jackery.com", stories)

    def test_approved_toc_keeps_historical_fallback_assembly(self) -> None:
        collector = page_toc.TocCollector(entries=[
            ("en", "Source section", 3),
        ])
        title, segments = page_toc._display_segments(collector, None)
        self.assertEqual("TABLE OF CONTENTS", title)
        self.assertEqual("EN  English", segments[0][0])
        self.assertEqual("02-02", segments[0][1])
        self.assertEqual([("Source section", 2)], segments[0][2])

    def test_app_icon_rewrite_preserves_source_sentence_when_asset_is_missing(self) -> None:
        source = "Click the **Add device** button to continue."
        text, replacements = app_inline.prepare_app_body_inline(
            _MissingAssetWriter(),
            semantic_kind="body_app_primary",
            text=source,
            bundle_root=ROOT,
            page_language="en",
            story_id="app",
            block_index=0,
        )
        self.assertEqual(source, text)
        self.assertIsNone(replacements)

    def test_missing_data_page_heading_fails_instead_of_defaulting_to_english(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            bundle = Path(td) / "rst"
            page_dir = bundle / "page"
            page_dir.mkdir(parents=True)
            (bundle / "index.rst").write_text(
                ".. include:: page/lcd_icons_en.rst\n", encoding="utf-8"
            )
            (page_dir / "lcd_icons_en.rst").write_text(
                ".. raw:: latex\n\n"
                "   \\begin{HBLcdIconTable}\n"
                "   \\HBLcdIconRow{1}{}{Source name}{Source description.}\n"
                "   \\end{HBLcdIconTable}\n",
                encoding="utf-8",
            )
            ir = build_manual_ir(
                root=ROOT,
                bundle_root=bundle,
                model="JE-1000F",
                region="US",
                lang="en",
                source="test",
                data_root=ROOT / "tests" / "fixtures" / "phase2",
            )
            with self.assertRaisesRegex(ValueError, "LCD page title"):
                ir_projection.lcd_page_data(
                    ir,
                    "en",
                    root=ROOT,
                    data_root=ROOT / "tests" / "fixtures" / "phase2",
                )

    def test_data_story_apis_require_source_titles(self) -> None:
        self.assertIs(inspect._empty, inspect.signature(data_stories.add_lcd_story)
                      .parameters["title"].default)
        self.assertIs(inspect._empty, inspect.signature(data_stories.add_spec_story)
                      .parameters["title"].default)
        self.assertIn("title", inspect.signature(data_stories.add_trouble_story).parameters)
        self.assertIn("title", inspect.signature(data_stories.add_symbols_story).parameters)


class IdmlVisibleCopyStaticGateTests(unittest.TestCase):
    _VISIBLE_TEXT_ARGUMENT = {
        "_psr": 1,
        "psr": 1,
        "_sized_psr": 1,
        "sized_psr": 1,
        "heading_text": 1,
        "h1_pill_paragraph": 1,
    }
    _ALLOWED_VISIBLE_LITERALS = {"+", ""}

    def test_renderer_visible_text_sinks_have_no_business_copy_literals(self) -> None:
        violations: list[str] = []
        for path in IDML_PYTHON:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                function = node.func
                name = (
                    function.attr if isinstance(function, ast.Attribute)
                    else function.id if isinstance(function, ast.Name)
                    else ""
                )
                index = self._VISIBLE_TEXT_ARGUMENT.get(name)
                if index is None or len(node.args) <= index:
                    continue
                value = node.args[index]
                if (
                    isinstance(value, ast.Constant)
                    and isinstance(value.value, str)
                    and value.value not in self._ALLOWED_VISIBLE_LITERALS
                ):
                    violations.append(
                        f"{path.relative_to(ROOT)}:{node.lineno}: {value.value!r}"
                    )
        self.assertEqual([], violations)

    def test_known_renderer_copy_fallbacks_are_absent(self) -> None:
        joined = "\n".join(path.read_text(encoding="utf-8") for path in IDML_PYTHON)
        forbidden = (
            "Editable reference figure",
            'or str(spec.get("kind") or "component")',
            'match else "3s"',
            'or "On/Off"',
            'or "3s"',
            'label or token.upper()',
            'or "figure"',
            '), "USER MAINTENANCE INSTRUCTIONS")',
            '), "OPERATING INSTRUCTIONS")',
            "SYMBOL_COPY =",
        )
        present = [value for value in forbidden if value in joined]
        self.assertEqual([], present)

    def test_toc_language_registry_is_scoped_to_approved_page_three(self) -> None:
        consumers = []
        for path in IDML_PYTHON:
            if path.name == "language_contract.py":
                continue
            text = path.read_text(encoding="utf-8")
            if "IDML_LANGUAGE_PACKS" in text or "LANGUAGE_REGISTRY" in text:
                consumers.append(str(path.relative_to(ROOT)))
        self.assertEqual(["tools/idml/page_toc.py"], consumers)


if __name__ == "__main__":
    unittest.main()
