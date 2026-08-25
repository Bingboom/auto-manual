from __future__ import annotations

import hashlib
import inspect
import json
import unittest
from dataclasses import asdict
from pathlib import Path

from tools.export_idml import IdmlWriter, load_layout_params
from tools.idml import page03, shared_page, symbols_page
from tools.idml.components.symbols_panel import SymbolsPanel, SymbolsPanelData
from tools.idml.loaders import load_symbols_rows
from tools.idml.params import param_pt
from tools.idml.symbols_page import SafetySymbolsPageStyle


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "tests" / "fixtures" / "phase2"
GOLDEN = ROOT / "tests" / "fixtures" / "idml_symbols_panel_golden.json"

TITLES = {
    "en": "MEANING OF SYMBOLS",
    "fr": "SIGNIFICATION DES SYMBOLES",
    "es": "SIGNIFICADO DE LOS SÍMBOLOS",
}
HEADERS = {
    "en": ("Symbol", "Meaning"),
    "fr": ("Symbole", "Signification"),
    "es": ("Símbolo", "Significados"),
}


def _story_digest(xml: str) -> str:
    normalized = xml.replace(ROOT.resolve().as_uri(), "file://SYMBOLS-PANEL-ROOT")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _snapshot(density: str, language: str) -> dict[str, object]:
    overlays = (
        (ROOT / "data" / "layout_params.idml-compact.csv",)
        if density == "compact"
        else ()
    )
    params = load_layout_params(ROOT / "data" / "layout_params.csv", overlays)
    writer = IdmlWriter(params)
    signals, icons = load_symbols_rows(DATA_ROOT, language)
    data = SymbolsPanelData(
        title=TITLES[language],
        signal_headers=HEADERS[language],
        icon_headers=HEADERS[language],
        signals=tuple(signals),
        icons=tuple(icons),
    )
    x = writer.m_l
    width = writer.page_w - writer.m_l - writer.m_r
    if density == "compact":
        y = param_pt(
            params,
            f"lang_{language}_idml_compact_safety_symbols_title_top",
            param_pt(params, "idml_compact_safety_symbols_title_top", 163.2),
        )
        available_height = writer.page_h - y
        sid = f"st_symbols_shared_{language}"
    else:
        style = SafetySymbolsPageStyle.from_writer(writer, language)
        y = (
            style.page_top
            + style.first_tail_height
            + style.first_tail_gap
            + style.second_tail_height
            + style.second_tail_gap
            + style.subbar_height
            + style.maintenance_title_gap
            + style.maintenance_body_height
            + style.maintenance_body_gap
        )
        available_height = writer.page_h - style.page_bottom_allowance - y
        sid = f"st_symbols_standard_{language}"
    rendered = SymbolsPanel(
        writer,
        sid=sid,
        data=data,
        bundle_root=ROOT,
        language=language,
        density=density,
    ).render(
        x=x,
        y=y,
        width=width,
        available_height=available_height,
    )
    stories = dict(writer.stories)
    return {
        "contract": asdict(rendered.contract),
        "height": rendered.height,
        "overflow": {
            "left": len(rendered.overflow.left),
            "right": len(rendered.overflow.right),
        },
        "story_sha256": {
            story_id: _story_digest(stories[story_id])
            for story_id in rendered.story_ids
        },
    }


class SymbolsPanelTests(unittest.TestCase):
    def test_three_language_visual_contract_matches_golden(self) -> None:
        expected = json.loads(GOLDEN.read_text(encoding="utf-8"))
        actual = json.loads(json.dumps({
            density: {
                language: _snapshot(density, language)
                for language in ("en", "fr", "es")
            }
            for density in ("standard", "compact")
        }))

        self.assertEqual(expected, actual)

    def test_compact_panel_owns_fixed_rows_and_continuous_k05_fill(self) -> None:
        params = load_layout_params(
            ROOT / "data" / "layout_params.csv",
            (ROOT / "data" / "layout_params.idml-compact.csv",),
        )
        writer = IdmlWriter(params)
        signals, icons = load_symbols_rows(DATA_ROOT, "en")
        rendered = SymbolsPanel(
            writer,
            sid="st_symbols_contract",
            data=SymbolsPanelData(
                title=TITLES["en"],
                signal_headers=HEADERS["en"],
                icon_headers=HEADERS["en"],
                signals=tuple(signals),
                icons=tuple(icons),
            ),
            bundle_root=ROOT,
            language="en",
            density="compact",
        ).render(x=writer.m_l, y=163.2, width=312.09, available_height=361.0)

        self.assertTrue(rendered.contract.fill_all_cells)
        self.assertFalse(rendered.contract.auto_grow_rows)
        self.assertTrue(rendered.contract.disable_hyphenation)
        for story_id in rendered.story_ids[1:]:
            xml = dict(writer.stories)[story_id]
            self.assertIn('FillColor="Color/HB Bg K05"', xml)
            self.assertIn('AutoGrow="false"', xml)
            self.assertNotIn('AutoGrow="true"', xml)

    def test_page_assemblers_only_assign_symbols_panel_rectangles(self) -> None:
        forbidden = (
            "_symbols_signal_table",
            "_symbols_icon_table",
            "idml_compact_symbols_signal_row_height",
            "idml_compact_symbols_icon_row_height",
        )
        sources = (
            inspect.getsource(shared_page.add_safety_symbols_page),
            inspect.getsource(symbols_page.add_safety_symbols_page),
            inspect.getsource(page03._symbol_continuation_objects),
        )
        for source in sources:
            for token in forbidden:
                self.assertNotIn(token, source)
        self.assertIn('density="compact"', sources[0])
        self.assertIn('density="standard"', sources[1])
        self.assertIn("render_continuation", sources[2])


if __name__ == "__main__":
    unittest.main()
