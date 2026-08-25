from __future__ import annotations

import re
import unittest
from pathlib import Path

from tools.export_idml import IdmlWriter, load_layout_params
from tools.idml import page_toc


ROOT = Path(__file__).resolve().parents[1]


class IdmlPageTocTests(unittest.TestCase):
    def test_compact_tokens_control_language_block_rhythm(self) -> None:
        writer = IdmlWriter(load_layout_params(
            ROOT / "data" / "layout_params.csv",
            (ROOT / "data" / "layout_params.idml-compact.csv",),
        ))
        self.assertEqual(("1", "int"), writer.params["idml_toc_dynamic_leader_start"])
        self.assertEqual(("8.0", "pt"), writer.params["idml_toc_leader_text_gap"])
        writer.spreads = [
            (f"sp_{index}", f'<Spread Self="sp_{index}"/>')
            for index in range(4)
        ]
        source = {
            "title": "TABLE OF CONTENTS",
            "languages": [
                {
                    "code": code,
                    "label": label,
                    "page_range": page_range,
                    "entries": [{"title": "SAFETY", "folio": page_range[:2]}],
                }
                for code, label, page_range in (
                    ("EN", "English", "01-08"),
                    ("FR", "Français", "09-16"),
                    ("ES", "Español", "17-24"),
                )
            ],
        }
        self.assertTrue(page_toc.finalize(
            writer,
            page_toc.TocCollector(),
            writer._add_story_parts,
            writer._psr,
            source=source,
        ))
        xml = dict(writer.spreads)["sp_toc"]

        def bar_top(index: int) -> float:
            bar = xml.split(
                f'Self="bg_toc_bar_{index}"', 1,
            )[1].split("</Rectangle>", 1)[0]
            ys = [
                float(value)
                for value in re.findall(r'Anchor="[-.0-9]+ ([-.0-9]+)"', bar)
            ]
            return min(ys) + writer.page_h / 2.0

        tops = [bar_top(index) for index in range(3)]
        self.assertAlmostEqual(57.0, tops[0], places=2)
        self.assertAlmostEqual(119.5, tops[1] - tops[0], places=2)
        self.assertAlmostEqual(122.5, tops[2] - tops[1], places=2)

        def leader_y(segment_index: int) -> float:
            leader = xml.split(
                f'Self="gl_toc_leader_{segment_index}_0_0"', 1,
            )[1].split("</GraphicLine>", 1)[0]
            value = re.search(
                r'Anchor="[-.0-9]+ ([-.0-9]+)"', leader,
            )
            assert value is not None
            return float(value.group(1)) + writer.page_h / 2.0

        for index, (top, offset) in enumerate(zip(
            tops, (29.324, 26.492, 26.495), strict=True,
        )):
            self.assertAlmostEqual(top + offset, leader_y(index), places=2)

    def test_dynamic_leader_starts_follow_the_rendered_entry_width(self) -> None:
        cases = (
            ("CONNECTIONS", 0, 0),
            ("TROUBLESHOOTING", 0, 1),
            ("RESOLUCIÓN DE PROBLEMAS", 2, 1),
            ("ALMACENAMIENTO", 2, 4),
        )

        for title, segment_index, row_index in cases:
            with self.subTest(title=title):
                reference = page_toc._REFERENCE_LEADERS[segment_index][1][row_index]
                col_w = page_toc._RIGHT_ENTRY_WIDTH[segment_index]
                text_end = page_toc._entry_text_end_x(
                    title,
                    page_toc._RIGHT_ENTRY_X,
                    col_w,
                )
                adjusted = page_toc._leader_metric_for_entry(
                    title,
                    page_toc._RIGHT_ENTRY_X,
                    col_w,
                    reference,
                )

                self.assertGreater(adjusted[0], text_end)
                self.assertLess(adjusted[0], adjusted[2])
                self.assertAlmostEqual(
                    page_toc._LEADER_TEXT_GAP,
                    adjusted[0] - text_end,
                    places=6,
                )
                self.assertEqual(reference[1:], adjusted[1:])

    def test_finalize_uses_each_entry_title_for_its_leader_start(self) -> None:
        params = load_layout_params(ROOT / "data" / "layout_params.csv")
        params["idml_toc_dynamic_leader_start"] = ("1", "int")
        writer = IdmlWriter(params)
        writer.spreads = [
            (f"sp_{index}", f'<Spread Self="sp_{index}"/>')
            for index in range(4)
        ]
        titles = (
            "CONNECTIONS",
            "TROUBLESHOOTING",
            "RESOLUCIÓN DE PROBLEMAS",
            "ALMACENAMIENTO",
        )
        source = {
            "title": "TABLE OF CONTENTS",
            "languages": [{
                "code": "EN",
                "label": "English",
                "page_range": "01-04",
                "entries": [
                    {"title": title, "folio": index}
                    for index, title in enumerate(titles, start=1)
                ],
            }],
        }

        self.assertTrue(page_toc.finalize(
            writer,
            page_toc.TocCollector(),
            writer._add_story_parts,
            writer._psr,
            source=source,
        ))
        toc_xml = dict(writer.spreads)["sp_toc"]
        half = (len(titles) + 1) // 2
        for index, title in enumerate(titles):
            column_index, row_index = divmod(index, half)
            entry_x = (
                page_toc._LEFT_ENTRY_X[0]
                if column_index == 0
                else page_toc._RIGHT_ENTRY_X
            )
            entry_w = (
                page_toc._LEFT_ENTRY_WIDTH[0]
                if column_index == 0
                else page_toc._RIGHT_ENTRY_WIDTH[0]
            )
            leader_id = f"gl_toc_leader_0_{column_index}_{row_index}"
            leader_xml = toc_xml.split(f'Self="{leader_id}"', 1)[1].split(
                "</GraphicLine>", 1,
            )[0]
            relative_x = float(re.search(
                r'<PathPointType Anchor="([-.0-9]+) ',
                leader_xml,
            ).group(1))
            start_x = relative_x + writer.page_w / 2.0
            text_end = page_toc._entry_text_end_x(title, entry_x, entry_w)

            with self.subTest(title=title):
                self.assertGreater(start_x, text_end)
                self.assertAlmostEqual(
                    page_toc._LEADER_TEXT_GAP,
                    start_x - text_end,
                    places=4,
                )


if __name__ == "__main__":
    unittest.main()
