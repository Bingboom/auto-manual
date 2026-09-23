from __future__ import annotations

from pathlib import Path
import unittest

from bs4 import BeautifulSoup

from tools.web_base_art_operation import arrange_base_art_operation


SOURCE = Path("page/05_operation_guide_placeholder.rst")


def _figure(layout: str, stage_html: str) -> tuple[BeautifulSoup, object, object]:
    soup = BeautifulSoup(
        f'<figure class="hb-operation-figure hb-operation-layout-{layout} '
        f'hb-base-art-live-copy"><div class="hb-operation-stage">{stage_html}'
        "</div></figure>",
        "html.parser",
    )
    figure = soup.find("figure")
    stage = soup.select_one(".hb-operation-stage")
    return soup, figure, stage


def _step(step_id: str, *lines: tuple[str, str]) -> str:
    body = "".join(
        f'<div class="line" data-step-id="{step_id}" data-step-part="{part}">{html}</div>'
        for part, html in lines
    )
    return f'<div class="hb-operation-step" data-step-id="{step_id}">{body}</div>'


def _text(tag: object) -> str:
    return " ".join(tag.get_text(" ", strip=True).split())  # type: ignore[attr-defined]


class BaseArtOperationTests(unittest.TestCase):
    def test_summary_steps_sit_on_their_anchors_beside_one_duration(self) -> None:
        soup, figure, stage = _figure(
            "status-right",
            '<img class="hb-operation-art" alt="Power on/off operation placeholder." src="a.png">'
            '<div class="line-block hb-operation-steps" style="--hb-x:74.5%">'
            + _step("on", ("summary", "On: Press once."))
            + _step("off", ("summary", "Off: Press and hold for 3s."))
            + "</div>"
            '<div class="hb-operation-supporting-copy"><div class="line">Standby.</div></div>',
        )
        spec = {
            "id": "main-power",
            "layout": "status-right",
            "base_art_layout": {
                "art_sha256": "a" * 64,
                "step_anchors": [[76.5, 15.42], [76.5, 34.17]],
                "step_width": 22.5,
                "duration_anchor": [81.4, 48.1],
            },
        }

        arrange_base_art_operation(
            soup, figure=figure, stage=stage, spec=spec, source_path=SOURCE,
            error_type=ValueError,
        )

        children = [child for child in stage.children if getattr(child, "name", None)]
        self.assertEqual(
            ["hb-operation-canvas", "hb-operation-supporting-copy"],
            [child["class"][0] for child in children],
        )
        canvas = children[0]
        canvas_children = [
            child["class"][0] for child in canvas.children if getattr(child, "name", None)
        ]
        # Steps sit beside the art box, so stacking them never stretches the box
        # that art-anchored copy resolves against.
        self.assertEqual(["hb-operation-art-box", "line-block"], canvas_children)
        art = canvas.select_one(".hb-operation-art-box > img.hb-operation-art")
        self.assertEqual("", art["alt"])
        steps = canvas.select_one(".hb-operation-steps")
        self.assertFalse(steps.has_attr("style"))
        placed = canvas.select(".hb-operation-step")
        self.assertEqual(
            [
                "--hb-step-x:76.5%;--hb-step-y:15.42%;--hb-step-width:22.5%",
                "--hb-step-x:76.5%;--hb-step-y:34.17%;--hb-step-width:22.5%",
            ],
            [step["style"] for step in placed],
        )
        self.assertEqual(
            [("On", "Press once."), ("Off", "Press and hold for 3s.")],
            [
                (
                    _text(step.select_one(".hb-operation-step-label")),
                    _text(step.select_one(".hb-operation-step-instruction")),
                )
                for step in placed
            ],
        )
        duration = canvas.select_one(".hb-operation-art-box > .hb-operation-duration")
        self.assertEqual("3s", _text(duration))
        self.assertEqual("true", duration["aria-hidden"])
        self.assertEqual("--hb-x:81.4%;--hb-y:48.1%", duration["style"])

    def test_label_pairs_and_prerequisite_use_the_art_pill(self) -> None:
        soup, figure, stage = _figure(
            "status-right",
            '<img class="hb-operation-art" alt="" src="ac.png">'
            '<div class="hb-operation-prerequisite"><p><strong>Prerequisite</strong>: '
            "The product is powered on.</p></div>"
            '<div class="line-block hb-operation-steps">'
            + _step("on", ("label", "<strong>On</strong>"), ("instruction", "Press once"))
            + _step("off", ("label", "<strong>Off</strong>"), ("instruction", "Press once"))
            + "</div>",
        )
        spec = {
            "id": "ac-output",
            "layout": "status-right",
            "capture_prerequisite": True,
            "base_art_layout": {
                "art_sha256": "b" * 64,
                "step_anchors": [[84.0, 26.51], [84.0, 36.98]],
                "step_width": 15.5,
                "prerequisite_rect": [1.14, 1.98, 42.83, 6.05],
                "prerequisite_max_width": 55.0,
                "prerequisite_fill": "#f8f8f8",
            },
        }

        arrange_base_art_operation(
            soup, figure=figure, stage=stage, spec=spec, source_path=SOURCE,
            error_type=ValueError,
        )

        prerequisite = stage.select_one(
            ".hb-operation-canvas > .hb-operation-art-box > .hb-operation-prerequisite"
        )
        self.assertEqual(
            "--hb-x:1.14%;--hb-y:1.98%;--hb-width:42.83%;--hb-height:6.05%;"
            "--hb-max-width:55%;--hb-fill:#f8f8f8",
            prerequisite["style"],
        )
        self.assertEqual("Prerequisite : The product is powered on.", _text(prerequisite))
        labels = stage.select(".hb-operation-step-label")
        instructions = stage.select(".hb-operation-step-instruction")
        self.assertEqual(["On", "Off"], [_text(tag) for tag in labels])
        self.assertEqual(["Press once", "Press once"], [_text(tag) for tag in instructions])
        self.assertIsNone(stage.select_one(".hb-operation-duration"))

    def test_prerequisite_needs_the_measured_pill_tone(self) -> None:
        for fill in (None, "grey", "#F8F8F8"):
            with self.subTest(fill=fill):
                soup, figure, stage = _figure(
                    "status-right",
                    '<img class="hb-operation-art" src="ac.png">'
                    '<div class="hb-operation-prerequisite"><p>Prerequisite: On.</p></div>'
                    '<div class="line-block hb-operation-steps">'
                    + _step("on", ("summary", "On: Press once."))
                    + "</div>",
                )
                layout = {
                    "art_sha256": "b" * 64,
                    "step_anchors": [[84.0, 26.51]],
                    "step_width": 15.5,
                    "prerequisite_rect": [1.14, 1.98, 42.83, 6.05],
                }
                if fill is not None:
                    layout["prerequisite_fill"] = fill
                with self.assertRaisesRegex(ValueError, "prerequisite_fill"):
                    arrange_base_art_operation(
                        soup, figure=figure, stage=stage,
                        spec={"id": "ac-output", "layout": "status-right",
                              "base_art_layout": layout},
                        source_path=SOURCE, error_type=ValueError,
                    )

    def test_footer_carries_mode_label_duration_and_action(self) -> None:
        soup, figure, stage = _figure(
            "footer-overlay",
            '<img class="hb-operation-art" alt="x" src="energy.png">'
            '<div class="line-block hb-operation-steps">'
            + _step("toggle", ("summary", "Press and hold both buttons for more than 3 seconds."))
            + "</div>",
        )
        spec = {
            "id": "energy-saving",
            "layout": "footer-overlay",
            "mode_label": "On/Off",
            "base_art_layout": {"art_sha256": "c" * 64, "footer_x": 72.0},
        }

        arrange_base_art_operation(
            soup, figure=figure, stage=stage, spec=spec, source_path=SOURCE,
            error_type=ValueError,
        )

        footer = stage.select_one(".hb-operation-canvas + .hb-operation-footer")
        self.assertIsNotNone(footer)
        self.assertEqual("--hb-footer-x:72%", footer["style"])
        self.assertEqual("3s", _text(footer.select_one(".hb-operation-duration")))
        self.assertEqual("On/Off", _text(footer.select_one(".hb-operation-mode-label")))
        self.assertEqual(
            "Press and hold both buttons for more than 3 seconds.",
            _text(footer.select_one(".hb-operation-step-instruction")),
        )
        self.assertIsNone(footer.select_one(".hb-operation-step-label"))

    def test_summary_split_never_drops_copy(self) -> None:
        for summary, expected in (
            ("Press once.", ("", "Press once.")),
            (": Press once.", ("", ": Press once.")),
            ("On:", ("", "On:")),
            ("<strong>On</strong>: Press once.", ("On", "Press once.")),
        ):
            with self.subTest(summary=summary):
                soup, figure, stage = _figure(
                    "status-right",
                    '<img class="hb-operation-art" src="a.png">'
                    '<div class="line-block hb-operation-steps">'
                    + _step("on", ("summary", summary))
                    + "</div>",
                )
                arrange_base_art_operation(
                    soup,
                    figure=figure,
                    stage=stage,
                    spec={
                        "id": "x",
                        "layout": "status-right",
                        "base_art_layout": {
                            "art_sha256": "a" * 64,
                            "step_anchors": [[70, 20]],
                            "step_width": 20,
                        },
                    },
                    source_path=SOURCE,
                    error_type=ValueError,
                )
                label = stage.select_one(".hb-operation-step-label")
                instruction = stage.select_one(".hb-operation-step-instruction")
                self.assertEqual(
                    expected,
                    (_text(label) if label else "", _text(instruction) if instruction else ""),
                )

    def test_unrecognised_stage_content_is_kept(self) -> None:
        soup, figure, stage = _figure(
            "status-right",
            '<img class="hb-operation-art" src="a.png">'
            '<div class="line-block hb-operation-steps">'
            + _step("on", ("summary", "On: Press once."))
            + "</div>"
            '<div class="hb-future-note">Keep me.</div>',
        )
        arrange_base_art_operation(
            soup,
            figure=figure,
            stage=stage,
            spec={
                "id": "x",
                "layout": "status-right",
                "base_art_layout": {
                    "art_sha256": "a" * 64,
                    "step_anchors": [[70, 20]],
                    "step_width": 20,
                },
            },
            source_path=SOURCE,
            error_type=ValueError,
        )
        note = stage.select_one(":scope > .hb-future-note")
        self.assertEqual("Keep me.", _text(note) if note else None)

    def test_layouts_that_cannot_position_the_copy_fail_closed(self) -> None:
        base_stage = (
            '<img class="hb-operation-art" src="a.png">'
            '<div class="line-block hb-operation-steps">'
            + _step("on", ("summary", "On: Press once."))
            + _step("off", ("summary", "Off: Press once."))
            + "</div>"
        )
        layout = {
            "art_sha256": "a" * 64,
            "step_anchors": [[76.5, 15.4], [76.5, 34.2]],
            "step_width": 22.5,
        }
        cases = (
            ({"id": "x", "layout": "status-right"}, "no base_art_layout"),
            (
                {"id": "x", "layout": "status-right",
                 "base_art_layout": {**layout, "step_anchors": [[76.5, 15.4]]}},
                "one anchor per step",
            ),
            (
                {"id": "x", "layout": "status-right",
                 "base_art_layout": {**layout, "duration_anchor": [81.4, 48.1]}},
                "steps state no duration",
            ),
            (
                {"id": "x", "layout": "footer-panel", "base_art_layout": layout},
                "unsupported layout",
            ),
        )
        for spec, message in cases:
            with self.subTest(message=message):
                soup, figure, stage = _figure(str(spec["layout"]), base_stage)
                with self.assertRaisesRegex(ValueError, message):
                    arrange_base_art_operation(
                        soup, figure=figure, stage=stage, spec=spec,
                        source_path=SOURCE, error_type=ValueError,
                    )


class OperationPanelCopySourceTests(unittest.TestCase):
    def test_only_active_panel_copy_reaches_the_page(self) -> None:
        from tools.web_document_source import _operation_panel_copy

        text = "\n".join(
            [
                "Energy",
                "======",
                "",
                ".. only:: lang_fr",
                "",
                "   .. raw:: manual-ir",
                "",
                '      {"kind":"operation_panel_copy","layout":"energy_saving","mode_label":"Marche/Arrêt"}',
                "",
                ".. only:: lang_en",
                "",
                "   .. raw:: manual-ir",
                "",
                '      {"kind":"operation_panel_copy","layout":"energy_saving","mode_label":"On/Off"}',
                "",
                ".. raw:: manual-ir",
                "",
                '   {"kind":"other","layout":"energy_saving"}',
                "",
                ".. raw:: manual-ir",
                "",
                "   {not json",
                "",
            ]
        )

        payloads = _operation_panel_copy(text, SOURCE, active_tags={"lang_en"})

        self.assertEqual(
            ({"kind": "operation_panel_copy", "layout": "energy_saving", "mode_label": "On/Off"},),
            payloads,
        )
        self.assertEqual((), _operation_panel_copy("No panel copy here.", SOURCE, active_tags=set()))


if __name__ == "__main__":
    unittest.main()
