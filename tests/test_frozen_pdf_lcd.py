"""Four-column LCD semantic binding and ordered native-row preservation."""
from copy import deepcopy
import unittest

from bs4 import BeautifulSoup

from tools.component_specs.model import ComponentSpec
from tools.frozen_pdf_lcd import LCD_ICON_ASSET_KEYS, lcd_icon_flow
from tools.web_manual_table_components import render_manual_table_component


def _record():
    numbers = [*range(1, 23), 22, 23, 24, 25]
    return {"rows": [{"number": number, "label": f"Name {index} <&>",
                      "meaning": f"Native description {index} with 230 V & 50 Hz.",
                      "physical_page": 96 if index < 7 else 97,
                      "label_bbox": [83, index * 10, 160, index * 10 + 5],
                      "meaning_bbox": [166, index * 10, 340, index * 10 + 5]}
                     for index, number in enumerate(numbers)]}


def _assets():
    return {key: {"asset_ref": f"assets/{key}.png"} for key in LCD_ICON_ASSET_KEYS}


def _flow(record=None, assets=None):
    return lcd_icon_flow(record or _record(), assets=assets or _assets(),
                         accessibility_label="Native LCD", language="uk", source_ref="uk/lcd#icons")


class FrozenPdfLcdTests(unittest.TestCase):
    def test_shared_component_renders_four_columns_without_rewriting_copy(self):
        record = _record()
        original = deepcopy(record)
        spec = ComponentSpec.from_dict(_flow(record)[0]["component_spec"])
        self.assertEqual("HB-TABLE-LCD-ICON", spec.component_id)
        soup = BeautifulSoup(render_manual_table_component(spec), "html.parser")
        rows = soup.select(".hb-lcd-icon-table tbody tr")
        self.assertEqual(26, len(rows))
        for index, (source, row) in enumerate(zip(record["rows"], rows, strict=True)):
            cells = row.find_all("td", recursive=False)
            self.assertEqual(4, len(cells))
            self.assertEqual(str(source["number"]), cells[0].get_text())
            self.assertEqual(_assets()[LCD_ICON_ASSET_KEYS[index]]["asset_ref"], cells[1].img["src"])
            self.assertEqual(source["label"], cells[2].get_text())
            self.assertEqual(source["meaning"], cells[3].get_text())
        self.assertEqual(original, record)
        self.assertIn("high-temperature", rows[21].img["src"])
        self.assertIn("low-temperature", rows[22].img["src"])
        self.assertEqual(["22", "22"], [rows[i].select_one('.hb-lcd-number').get_text() for i in (21, 22)])

    def test_missing_or_reordered_rows_do_not_silently_choose_different_icons(self):
        record = _record()
        record["rows"].pop()
        with self.assertRaisesRegex(ValueError, "cover 1-25"):
            _flow(record)
        record = _record()
        record["rows"][21], record["rows"][22] = record["rows"][22], record["rows"][21]
        with self.assertRaisesRegex(ValueError, "visual order"):
            _flow(record)

    def test_every_semantic_icon_is_required(self):
        assets = _assets()
        del assets['lcd.icon.low-temperature']
        with self.assertRaisesRegex(ValueError, "missing governed LCD icon: lcd.icon.low-temperature"):
            _flow(assets=assets)


if __name__ == "__main__":
    unittest.main()
