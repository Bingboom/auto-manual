"""Reference-parity contracts specific to the multilingual preface."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from tools.export_idml import IdmlWriter
from tools.idml.stories import add_prose_story
from tools.idml.styles import styles_xml


ROOT = Path(__file__).resolve().parents[1]


class PrefaceParityTests(unittest.TestCase):
    def test_preface_body_disables_hyphenation(self) -> None:
        writer = IdmlWriter({
            "idml_preface_paragraph_space_after": ("2", "pt"),
        })
        self.assertIn(
            'Name="HB Preface Body" PointSize="7.2" '
            'FillColor="Color/HB Brand Dark" SpaceAfter="2" '
            'Hyphenation="false"',
            styles_xml(writer.params),
        )

    def test_preface_language_badge_uses_scoped_reference_gaps(self) -> None:
        writer = IdmlWriter({
            "idml_preface_paragraph_space_after": ("2", "pt"),
            "lang_fr_idml_preface_header_space_before": ("11.73", "pt"),
            "lang_fr_idml_preface_header_space_after": ("1.62", "pt"),
        })
        langtag = json.dumps({
            "kind": "langtag", "lang": "FR", "texts": ["IMPORTANT"],
        })
        _, estimated_height = add_prose_story(
            writer,
            "st_preface_test",
            "00_preface",
            [
                ("body", "First paragraph."),
                ("body", "Final English paragraph."),
                ("component", langtag),
                ("body", "French paragraph."),
            ],
            ROOT / "does-not-exist",
        )
        story = dict(writer.stories)["st_preface_test"]
        self.assertIn('SpaceBefore="11.73" SpaceAfter="1.62"', story)
        self.assertNotIn('SpaceAfter="13.74"', story)
        self.assertGreater(estimated_height, 0.0)


if __name__ == "__main__":
    unittest.main()
