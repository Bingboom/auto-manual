#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Component registry contract (componentization P2).

The registry is the extension point for new manual components: every kind
the extractor can emit must have a renderer, every renderer must produce
render output for a minimal spec, and the writer façade must dispatch
through the registry (no forked logic).
"""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MINIMAL_SPECS: dict[str, dict] = {
    "inbox": {"kind": "inbox", "items": [{"img": "", "label": "Unit"}]},
    "safetywarning": {"kind": "safetywarning", "texts": ["Risk text."]},
    "warninglead": {"kind": "warninglead", "label": "WARNING", "texts": ["Lead."]},
    "tailwarnbox": {"kind": "tailwarnbox", "label": "WARNING", "texts": ["Tail."]},
    "warnbox": {"kind": "warnbox", "label": "DANGER", "texts": ["Boxed."]},
    "notice": {"kind": "notice", "label": "NOTE", "texts": ["Note text."]},
    "fcc": {"kind": "fcc", "texts": ["Left copy.", "Right copy."]},
    "lcdmode": {"kind": "lcdmode", "img": "",
                "groups": [{"state": "On", "actions": [["Press", "Wakes"]]}]},
    "oppanel": {"kind": "oppanel", "image": "", "prereq": "Prerequisite: powered on.",
                "rows": [["On", "Press once"], ["Off", "Press once"]]},
    "langtag": {"kind": "langtag", "lang": "EN", "texts": ["IMPORTANT"]},
    "warrantyyears": {"kind": "warrantyyears", "items": [
        {"number": "3", "unit": "YEARS", "label": "Standard", "text": "Copy."}]},
}


def _ctx():
    from tools.idml.components import RenderContext

    return RenderContext(params={}, page_w=368.79, m_l=28.35, m_r=28.35,
                         root=ROOT, bundle_root=ROOT / "does-not-exist")


class ComponentRegistryTests(unittest.TestCase):
    def test_every_extractor_kind_has_a_renderer(self) -> None:
        from tools.idml.components import REGISTRY
        from tools.idml_rst_extract import EMITTED_COMPONENT_KINDS

        missing = sorted(set(EMITTED_COMPONENT_KINDS) - set(REGISTRY))
        self.assertEqual(missing, [], f"extractor kinds without a renderer: {missing}")

    def test_minimal_specs_cover_the_whole_registry(self) -> None:
        from tools.idml.components import REGISTRY

        self.assertEqual(sorted(MINIMAL_SPECS), sorted(REGISTRY))

    def test_every_registered_kind_renders(self) -> None:
        from tools.idml.components import render

        ctx = _ctx()
        for kind, spec in MINIMAL_SPECS.items():
            with self.subTest(kind=kind):
                xml, est = render(spec, ctx, tid=f"t_{kind}", terminal=True)
                self.assertTrue(xml, f"{kind} rendered empty")
                self.assertGreater(est, 0.0)
                self.assertIn("<Table ", xml)

    def test_unknown_kind_renders_nothing(self) -> None:
        from tools.idml.components import render

        self.assertEqual(render({"kind": "hologram"}, _ctx(), tid="t", terminal=True),
                         ("", 0.0))

    def test_writer_dispatches_through_the_registry(self) -> None:
        from tools.export_idml import IdmlWriter, load_layout_params
        from tools.idml.components import RenderContext, render

        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        w = IdmlWriter(params)
        ctx = RenderContext(params=params, page_w=w.page_w, m_l=w.m_l, m_r=w.m_r,
                            root=ROOT, bundle_root=ROOT / "does-not-exist")
        for kind, spec in MINIMAL_SPECS.items():
            with self.subTest(kind=kind):
                via_writer = w._render_component(
                    "st_x", 3, spec, ROOT / "does-not-exist", True)
                via_registry = render(spec, ctx, tid="st_x_cmp3", terminal=True)
                self.assertEqual(via_writer, via_registry)


if __name__ == "__main__":
    unittest.main()


class FccEdgeCaseTests(unittest.TestCase):
    def test_empty_texts_render_instead_of_crashing(self) -> None:
        # `\HBFccBlock{}{}` arrives as texts=[]; this used to IndexError and
        # abort the whole export.
        from tools.idml.components import render

        xml, est = render({"kind": "fcc", "texts": []}, _ctx(), tid="t_fcc0", terminal=True)
        self.assertIn("<Table ", xml)
        self.assertGreater(est, 0.0)

    def test_single_text_fills_left_panel_only(self) -> None:
        from tools.idml.components import render

        xml, _ = render({"kind": "fcc", "texts": ["Only left."]}, _ctx(),
                        tid="t_fcc1", terminal=True)
        self.assertIn("Only left.", xml)
        left, right = xml.split('Name="1:0"', 1)
        self.assertIn("Only left.", left)
        self.assertNotIn("Only left.", right)
