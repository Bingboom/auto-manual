"""Reference-parity contracts specific to the multilingual preface."""
from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import Mock

from tools.export_idml import IdmlWriter
from tools.idml.reference_story_flow import ReferenceStoryEmitter
from tools.idml.stories import add_prose_story
from tools.idml.styles import styles_xml


ROOT = Path(__file__).resolve().parents[1]


class PrefaceParityTests(unittest.TestCase):
    def test_explicit_preface_uses_compact_top_override(self) -> None:
        writer = Mock()
        writer.params = {
            "idml_preface_margin_top": ("52.986", "pt"),
            "idml_compact_preface_margin_top": ("32.986", "pt"),
        }
        writer.m_l = 12.0
        writer.m_r = 12.0
        writer.m_t = 12.0
        writer.m_b = 12.0
        writer.page_h = 480.0
        writer.add_prose_story.return_value = ("st_preface", 120.0)
        emitter = ReferenceStoryEmitter(
            writer=writer,
            toc=Mock(),
            bundle_root=ROOT,
            page_plan={
                "plan_source": "target-assembly",
                "pages": [{
                    "source_path": "page/00_preface.rst",
                    "composition_id": "preface",
                    "composition_type": "preface",
                }],
            },
        )

        next_page = emitter.emit(
            "st_preface",
            "00_preface",
            [("body", "Preface copy.")],
            1,
        )

        self.assertEqual(2, next_page)
        self.assertEqual(
            ("st_preface", [(1, 32.986, 468.0)]),
            writer.add_story_frames.call_args.args,
        )

    def test_target_assembly_preface_honors_its_planned_page_count(self) -> None:
        writer = Mock()
        writer.params = {}
        writer.m_l = 12.0
        writer.m_r = 12.0
        writer.m_t = 12.0
        writer.m_b = 12.0
        writer.page_h = 480.0
        writer.add_prose_story.return_value = ("st_preface", 120.0)
        emitter = ReferenceStoryEmitter(
            writer=writer,
            toc=Mock(),
            bundle_root=ROOT,
            page_plan={
                "plan_source": "target-assembly",
                "physical_page_count": 54,
                "pages": [{
                    "source_path": "page/preface_important.rst",
                    "composition_id": "preface",
                    "composition_type": "preface",
                    "latex_start_page": 2,
                    "planned_page_count": 2,
                }],
            },
        )

        next_page = emitter.emit(
            "st_preface",
            "preface_important",
            [("body", "Six-language preface copy.")],
            1,
        )

        self.assertEqual(3, next_page)
        self.assertEqual(
            (
                "st_preface",
                [(1, 12.0, 468.0), (2, 12.0, 468.0)],
            ),
            writer.add_story_frames.call_args.args,
        )

    def test_semantic_preface_alias_uses_preface_typography(self) -> None:
        writer = IdmlWriter({
            "idml_preface_body_font_size": ("7", "pt"),
            "idml_preface_body_font_leading": ("10", "pt"),
        })
        writer.add_prose_story(
            "st_preface_alias",
            "preface_important",
            [("body", "Semantic preface copy.")],
            ROOT,
            semantic_page_role="preface",
        )
        story = dict(writer.stories)["st_preface_alias"]
        self.assertIn(
            'AppliedParagraphStyle="ParagraphStyle/HB Preface Body"',
            story,
        )

    def test_preface_body_disables_hyphenation(self) -> None:
        writer = IdmlWriter({
            "idml_preface_paragraph_space_after": ("2", "pt"),
        })
        self.assertIn(
            'Name="HB Preface Body" PointSize="7.2" '
            'FillColor="Color/HB Brand Dark" SpaceAfter="2" '
            'Hyphenation="false" Composer="HL Single"',
            styles_xml(writer.params),
        )

    def test_preface_uses_greedy_single_line_composition_only(self) -> None:
        xml = styles_xml(IdmlWriter({}).params)
        preface = xml.split('Name="HB Preface Body"', 1)[1].split(">", 1)[0]
        self.assertIn('Composer="HL Single"', preface)
        self.assertEqual(1, xml.count('Composer="HL Single"'))

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
