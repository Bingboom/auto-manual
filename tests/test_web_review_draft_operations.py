"""Operation panels read back from rendered markup replay through the shared renderer unchanged."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import unittest

from bs4 import BeautifulSoup

from tools.component_specs.operation import operation_component_spec
from tools.web.composite_presentation import WebCompositeContext
from tools.web.operation_component import render_operation_component
from tools.web.presentation import WebPresentationError
from tools.web.review_draft_blocks import DraftChapter
from tools.web.review_draft_operations import operations

PREFIX = "XX-1/US"
BASE_ART = "base-art-live-copy"


def _step(step_id: str, *parts: tuple[str, str]) -> dict[str, Any]:
    return {"id": step_id, "parts": [{"role": role, "html": html, "text": BeautifulSoup(html, "html.parser").get_text(" ", strip=True)}
                                     for role, html in parts]}


def _render(spec: Any, carrier: str, presentation: dict[str, Any]) -> str:
    context = WebCompositeContext(None, None, None, "en", WebPresentationError)
    return render_operation_component(spec, carrier, source_path=Path("page.html"), presentation=presentation,
                                      composites=context)


def _panel(operation_id: str, layout: str, steps: list[dict[str, Any]], layout_fields: dict[str, Any], *,
           support: tuple[str, ...] = (), lead: str = "", mode_label: str = "", sos_label: str = "",
           alt: str = "Power") -> tuple[str, dict[str, Any]]:
    """A panel as the shared renderer writes it, and the presentation it was written from."""
    presentation: dict[str, Any] = {
        "id": operation_id, "layout": layout, "step_ids": [step["id"] for step in steps],
        "image_key": f"{PREFIX}/{operation_id}", "capture_prerequisite": bool(lead),
        "capture_following_lines": len(support), **layout_fields,
    }
    mode = {"presentation_mode": BASE_ART} if "presentation_mode" in layout_fields else {}
    spec = operation_component_spec(
        operation_id=operation_id, accessibility_label=alt, layout=layout, steps=steps,
        prerequisite_html=lead, supporting_copy=list(support), artwork_ref="assets/panel.png",
        source_ref="page.html#operation", language="en", mode_label=mode_label, sos_label=sos_label,
        metadata={**mode, "web_presentation": presentation},
    )
    lines = "".join(f'<div class="line">{part["html"]}</div>' for step in steps for part in step["parts"])
    carrier = f'{lead}<img alt="{alt}" src="assets/panel.png"/><div class="line-block">{lines}</div>'
    return _render(spec, carrier, presentation), presentation


def _read(rendered: str) -> DraftChapter:
    root = BeautifulSoup(f'<section id="power"><h2>Power</h2>{rendered}</section>', "html.parser")
    chapter = DraftChapter(root=root, page_id="power", language="en", image_key_prefix=PREFIX)
    operations(chapter)
    return chapter


def _replay(chapter: DraftChapter) -> str:
    (claim,) = chapter.claims
    presentation = claim.spec.metadata["web_presentation"]
    return _render(claim.spec, "".join(str(node) for node in claim.owned_nodes), presentation)


PAIRS = [_step("on", ("label", "<strong>On</strong>"), ("instruction", "Press once")),
         _step("off", ("label", "<strong>Off</strong>"), ("instruction", "Press and hold for 3s"))]
SUMMARIES = [_step("on", ("summary", "On: Press once.")), _step("off", ("summary", "Off: Press and hold for 3s."))]


class RoundTripTests(unittest.TestCase):
    """Each layout the renderer writes is read back into the presentation it was written from."""

    def assert_round_trip(self, rendered: str, presentation: dict[str, Any]) -> DraftChapter:
        chapter = _read(rendered)
        (claim,) = chapter.claims
        self.assertEqual(claim.spec.metadata["web_presentation"], presentation)
        self.assertEqual(_replay(chapter), rendered)
        self.assertEqual(chapter.root.select("figure"), [])  # the panel left the flow for its carrier
        return chapter

    def test_status_right_anchors_duration_pill_and_supporting_panels(self):
        layout = {"presentation_mode": BASE_ART, "base_art_layout": {
            "step_anchors": [[76.5, 21.0], [76.5, 34.0]], "step_width": 22.5,
            "duration_anchor": [82.0, 43.0], "duration_icon": "clock",
            "prerequisite_rect": [4.0, 6.0, 30.0, 8.0], "prerequisite_fill": "#e8e8e8",
            "prerequisite_max_width": 40.0, "supporting_anchor": [43.0, 57.0, 52.0]}}
        rendered, presentation = _panel("main-power", "status-right", PAIRS, layout,
                                        support=("It turns off when idle.",),
                                        lead="<p>Connect the battery first.</p>")
        chapter = self.assert_round_trip(rendered, presentation)
        self.assertEqual(chapter.presentation_gaps, [])

    def test_summary_steps_are_joined_again_at_their_colon(self):
        layout = {"presentation_mode": BASE_ART, "base_art_layout": {
            "step_anchors": [[76.5, 15.0], [76.5, 34.0]], "step_width": 22.5, "duration_anchor": [81.0, 48.0]}}
        rendered, presentation = _panel("main-power", "status-right", SUMMARIES, layout)
        self.assertIn('class="hb-operation-step-label"', rendered)  # the renderer split each summary
        chapter = self.assert_round_trip(rendered, presentation)
        steps = chapter.claims[0].spec.slot("steps").content
        self.assertEqual([part["html"] for step in steps for part in step["parts"]],
                         ["On: Press once.", "Off: Press and hold for 3s."])

    def test_footer_overlay_keeps_its_offset_and_mode_label(self):
        steps = [_step("toggle", ("summary", "Press and hold both buttons for more than 3 seconds."))]
        layout = {"presentation_mode": BASE_ART, "base_art_layout": {"footer_x": 72.0}}
        rendered, presentation = _panel("energy-saving", "footer-overlay", steps, layout, mode_label="On/Off")
        chapter = self.assert_round_trip(rendered, presentation)
        self.assertEqual(chapter.claims[0].spec.slot("mode_label").content, "On/Off")

    def test_footer_panel_keeps_its_lead_art_width_and_markers(self):
        steps = [_step("light", ("summary", "Press once to turn on the light.")),
                 _step("sos", ("summary", "Press it again to switch to SOS Mode.")),
                 _step("off", ("summary", "Press it a third time to turn off the light."))]
        layout = {"presentation_mode": BASE_ART, "base_art_layout": {
            "art_width": 56.8, "step_markers": ["bulb-lit", "sos", "bulb-off"]}}
        rendered, presentation = _panel("led-light", "footer-panel", steps, layout, sos_label="SOS",
                                        lead="<p>The LED light has two modes: Light mode and SOS mode.</p>")
        chapter = self.assert_round_trip(rendered, presentation)
        self.assertEqual(chapter.claims[0].spec.slot("sos_label").content, "SOS")

    def test_plain_panel_replays_its_rectangles_but_stays_listed(self):
        layout = {"steps_rect": [77.0, 5.0, 20.0, 40.0], "prerequisite_rect": [5.0, 4.0, 40.0, 9.0]}
        rendered, presentation = _panel("power", "status-right", PAIRS, layout, support=("3s",),
                                        lead="<p>Connect the battery first.</p>", alt="On/Off")
        chapter = self.assert_round_trip(rendered, presentation)
        self.assertEqual([gap["component"] for gap in chapter.presentation_gaps], ["operation power"])
        self.assertIn("base art places it on the drawing", chapter.presentation_gaps[0]["missing"])
        self.assertEqual(chapter.claims[0].spec.slot("accessibility_label").content, "On/Off")


class FallbackTests(unittest.TestCase):
    """A presentation the renderer cannot replay leaves the plain artwork and lines, listed as a gap."""

    def base_art(self) -> str:
        layout = {"presentation_mode": BASE_ART, "base_art_layout": {
            "step_anchors": [[76.5, 21.0], [76.5, 34.0]], "step_width": 22.5, "duration_anchor": [82.0, 43.0]}}
        return _panel("main-power", "status-right", PAIRS, layout, support=("It turns off when idle.",))[0]

    def assert_fallback(self, rendered: str, reason: str) -> None:
        chapter = _read(rendered)
        (claim,) = chapter.claims
        self.assertNotIn("web_presentation", claim.spec.metadata)
        carrier = "".join(str(node) for node in claim.owned_nodes)
        self.assertEqual(BeautifulSoup(carrier, "html.parser").get_text("|", strip=True),
                         "On|Press once|Off|Press and hold for 3s|It turns off when idle.")
        (gap,) = chapter.presentation_gaps
        self.assertEqual(gap["component"], "operation main-power")
        self.assertRegex(gap["missing"], reason)

    def test_a_duration_the_steps_no_longer_state_is_refused_by_the_renderer(self):
        edited = self.base_art().replace("Press and hold for 3s", "Press and hold")
        chapter = _read(edited)
        self.assertRegex(chapter.presentation_gaps[0]["missing"], "its steps state no duration")
        self.assertNotIn("web_presentation", chapter.claims[0].spec.metadata)

    def test_steps_of_different_widths_are_not_guessed(self):
        edited = self.base_art().replace("--hb-step-width:22.5%", "--hb-step-width:30%", 1)
        self.assert_fallback(edited, "do not share one width")

    def test_a_missing_anchor_is_not_guessed(self):
        edited = self.base_art().replace("--hb-step-y:34%;", "", 1)
        self.assert_fallback(edited, "--hb-step-y is not a percentage")

    def test_label_lines_without_strong_copy_still_pair(self):
        edited = self.base_art().replace("<strong>On</strong>", "On")
        chapter = _read(edited)
        self.assertEqual(chapter.presentation_gaps, [])
        self.assertIn("<strong>On</strong>", _replay(chapter))


if __name__ == "__main__":
    unittest.main()
