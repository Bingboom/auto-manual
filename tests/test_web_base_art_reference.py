from __future__ import annotations

from pathlib import Path
import unittest

from bs4 import BeautifulSoup

from tools.web_base_art_reference import arrange_base_art_reference


SOURCE = Path("page/08_charging_methods.rst")
VEHICLE = {"line": 0, "rect": [64.0, 30.6, 18.0, 8.96]}
NOTE = {"line": 1, "rect": [55.0, 3.73, 42.12, 11.19], "fill": "#ffffff"}


def _spec(**layout: object) -> dict[str, object]:
    return {
        "id": "charging-car",
        "base_art_layout": {
            "art_sha256": "a" * 64,
            "panel_top": 6.15,
            "panel_fill": "#f2f3f3",
            "labels": [VEHICLE, NOTE],
            **layout,
        },
    }


def _semantic(*lines: str) -> tuple[BeautifulSoup, object, object, object]:
    body = "".join(f'<div class="line">{line}</div>' for line in lines)
    soup = BeautifulSoup(
        '<div class="hb-reference-semantic">'
        '<img class="hb-reference-art hb-composite-art" alt="Car charging" src="car.png">'
        f'<div class="line-block hb-reference-labels">{body}</div>'
        "</div>",
        "html.parser",
    )
    semantic = soup.select_one(".hb-reference-semantic")
    image = soup.select_one("img")
    label_block = soup.select_one(".hb-reference-labels")
    return soup, semantic, image, label_block


def _text(tag: object) -> str:
    return " ".join(tag.get_text().split())  # type: ignore[attr-defined]


class BaseArtReferenceTests(unittest.TestCase):
    def test_source_lines_sit_on_their_declared_rects_over_the_art(self) -> None:
        soup, semantic, image, label_block = _semantic(
            "Vehicle", "*The car charging cable is <em>sold separately</em>."
        )

        arrange_base_art_reference(
            soup, semantic=semantic, image=image, label_block=label_block,
            spec=_spec(), source_path=SOURCE, error_type=ValueError,
        )

        children = [child for child in semantic.children if getattr(child, "name", None)]
        self.assertEqual(["hb-reference-art-panel"], [child["class"][0] for child in children])
        panel = children[0]
        self.assertEqual("--hb-panel-top:6.15%;--hb-panel-fill:#f2f3f3", panel["style"])
        # The art stays the one image; it is decorative once its copy is live.
        self.assertIs(image, panel.find("img"))
        self.assertEqual("", image["alt"])
        labels = panel.select(":scope > span.hb-reference-live-label")
        self.assertEqual(["0", "1"], [label["data-source-line"] for label in labels])
        self.assertEqual(
            [
                "--hb-x:64%;--hb-y:30.6%;--hb-width:18%;--hb-height:8.96%",
                "--hb-x:55%;--hb-y:3.73%;--hb-width:42.12%;--hb-height:11.19%;"
                "--hb-fill:#ffffff",
            ],
            [label["style"] for label in labels],
        )
        self.assertEqual(
            [["hb-reference-live-label"], ["hb-reference-live-label", "hb-reference-live-pill"]],
            [label["class"] for label in labels],
        )
        self.assertEqual(
            ["Vehicle", "*The car charging cable is sold separately."],
            [_text(label) for label in labels],
        )
        # Inline markup moves with the line instead of being flattened.
        self.assertIsNotNone(labels[1].find("em"))
        # Every governed line now lives on the panel; nothing is shown twice.
        self.assertIsNone(semantic.select_one(".hb-reference-labels"))
        self.assertEqual(1, _text(semantic).count("Vehicle"))

    def test_lines_keep_source_order_whatever_order_the_layout_declares(self) -> None:
        soup, semantic, image, label_block = _semantic("Véhicule", "※Le câble est vendu séparément.")

        arrange_base_art_reference(
            soup, semantic=semantic, image=image, label_block=label_block,
            spec=_spec(labels=[NOTE, VEHICLE]), source_path=SOURCE, error_type=ValueError,
        )

        self.assertEqual(
            [("0", "Véhicule"), ("1", "※Le câble est vendu séparément.")],
            [
                (label["data-source-line"], _text(label))
                for label in semantic.select(".hb-reference-live-label")
            ],
        )

    def test_fails_closed_unless_every_captured_line_is_placed_once(self) -> None:
        rejected = (
            ("no layout", {"id": "charging-car"}, "has no base_art_layout"),
            ("a line left unplaced", _spec(labels=[VEHICLE]), "exactly once"),
            ("a line placed twice", _spec(labels=[VEHICLE, {**NOTE, "line": 0}]), "exactly once"),
            ("a line that was not captured", _spec(labels=[VEHICLE, {**NOTE, "line": 2}]), "exactly once"),
            ("a boolean line index", _spec(labels=[VEHICLE, {**NOTE, "line": True}]), "exactly once"),
            ("rect outside the panel", _spec(labels=[VEHICLE, {**NOTE, "rect": [55, 3, 42, 111]}]), "rect must be 4"),
            ("rect without its height", _spec(labels=[VEHICLE, {**NOTE, "rect": [55, 3, 42]}]), "rect must be 4"),
            ("band outside the panel", _spec(panel_top=-1), "panel_top"),
            ("panel tone that is not #rrggbb", _spec(panel_fill="#F2F3F3"), "panel_fill"),
            ("pill tone that is not #rrggbb", _spec(labels=[VEHICLE, {**NOTE, "fill": "white"}]), "fill"),
        )
        for label, spec, message in rejected:
            with self.subTest(label):
                soup, semantic, image, label_block = _semantic("Vehicle", "*Sold separately.")
                with self.assertRaisesRegex(ValueError, message):
                    arrange_base_art_reference(
                        soup, semantic=semantic, image=image, label_block=label_block,
                        spec=spec, source_path=SOURCE, error_type=ValueError,
                    )

        soup, semantic, image, _ = _semantic("Vehicle", "*Sold separately.")
        with self.assertRaisesRegex(ValueError, "no captured source lines"):
            arrange_base_art_reference(
                soup, semantic=semantic, image=image, label_block=None,
                spec=_spec(), source_path=SOURCE, error_type=ValueError,
            )


if __name__ == "__main__":
    unittest.main()
