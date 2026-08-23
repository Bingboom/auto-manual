from __future__ import annotations

import re
import unittest
from pathlib import Path

from tools.export_idml import IdmlWriter, load_layout_params
from tools.idml import page_toc


ROOT = Path(__file__).resolve().parents[1]


class IdmlPageTocTests(unittest.TestCase):
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
        writer = IdmlWriter(load_layout_params(
            ROOT / "data" / "layout_params.csv",
            (ROOT / "data" / "layout_params.idml-compact.csv",),
        ))
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
