from __future__ import annotations

import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from tools.export_idml import IdmlWriter, load_layout_params


ROOT = Path(__file__).resolve().parents[1]


class MeasuredSpecPanelTests(unittest.TestCase):
    def test_celsius_uses_bundled_font_without_rewriting_the_unit(self):
        writer = IdmlWriter(load_layout_params(ROOT / "data" / "layout_params.csv"))
        paragraph = ET.fromstring(writer._psr("HB Spec Value", "0℃ ~ 45℃", terminal=True))
        self.assertEqual("0℃ ~ 45℃", "".join(
            node.text or "" for node in paragraph.iter("Content")
        ))
        units = [run for run in paragraph.findall("CharacterStyleRange")
                 if run.findtext("Content") == "℃"]
        self.assertEqual(2, len(units))
        self.assertTrue(all(run.findtext("Properties/AppliedFont") == "Noto Sans"
                            for run in units))

    def render(self, rows, *, fit_content=False, language="jp"):
        writer = IdmlWriter(load_layout_params(ROOT / "data" / "layout_params.csv"))
        sections = [
            {"title": title, "rows": [("Label", "Value")]}
            for title in ("General", "Input", "Output")
        ] + [{"title": "Temperature", "rows": rows}]
        sid = writer.add_spec_story(
            sections, lang=language, title="Specifications", fit_content=fit_content,
        )
        stories = dict(writer.stories)
        root = ET.fromstring(stories[sid])
        frame = next(
            item for item in root.iter("TextFrame")
            if item.get("ParentStory") == f"st_anchor_spec_{language}3"
        )
        ys = [
            float(point.get("Anchor").split()[1])
            for point in frame.findall("./Properties/PathGeometry//PathPointType")
        ]
        return max(ys) - min(ys), stories[f"st_anchor_spec_{language}3"]

    def test_three_row_shell_covers_reproduced_native_height(self):
        rows = [
            ("充電温度", "0℃ ~ 45℃"),
            ("動作温度", "-10℃ ~ 45℃"),
            ("保存温度", "1ヶ月 -20℃~45℃ 3ヶ月 0℃~45℃ 1年間 0℃~25℃"),
        ]
        old_height, old_content = self.render(rows)
        height, content = self.render(rows, fit_content=True)
        self.assertEqual(27.11, old_height)
        # InDesign 21.0.1.6 composes these three rows to 41.0901 pt.
        self.assertGreater(height, 41.0901)
        self.assertEqual(old_content, content)

    def test_wrapped_and_explicit_lines_expand_without_changing_cells(self):
        for language in ("jp", "en"):
            for value in ("長期保存温度の条件を確認してください。" * 8, "A\nB\nC\nD"):
                with self.subTest(language=language, value=value):
                    short, _ = self.render([("Storage", "20℃")], fit_content=True,
                                           language=language)
                    _, original = self.render([("Storage", value)], language=language)
                    height, content = self.render([("Storage", value)], fit_content=True,
                                                  language=language)
                    self.assertGreater(height, short)
                    self.assertEqual(original, content)


if __name__ == "__main__":
    unittest.main()
