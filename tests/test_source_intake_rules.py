#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the spec-sheet intake rule engine (region-aware transforms)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.source_intake_rules import (  # noqa: E402
    DIRECT, EXCLUDED, NEEDS_REVIEW, TRANSFORMED,
    FieldRule, apply_op, display_width, extract_candidates, find_field_value,
)


class ApplyOpTests(unittest.TestCase):
    def test_capacity_format(self):
        v, s = apply_op("capacity", "Nominal: 2048Wh，Battery Cell：DFD 51.2V/40Ah (16S2P)", "", "JP")
        self.assertEqual(v, "2048 Wh (40 Ah / 51.2 V DC)")
        self.assertEqual(s, TRANSFORMED)

    def test_weight_region_aware(self):
        self.assertEqual(apply_op("weight", "About 18.8Kg", "", "US")[0], "About 41.45 lbs/18.8 kg")
        self.assertEqual(apply_op("weight", "About 18.8Kg", "", "JP")[0], "About 18.8 kg")

    def test_dimensions_region_aware(self):
        us, _ = apply_op("dims_mm_to_cm", "长 366mm x 宽 255mm x 高 272mm", "", "US")
        self.assertEqual(us, "14.4 × 10.0 × 10.7 in / 36.6 × 25.5 × 27.2 cm")
        jp, _ = apply_op("dims_mm_to_cm", "长 366mm x 宽 255mm x 高 272mm", "", "JP")
        self.assertEqual(jp, "36.6 × 25.5 × 27.2 cm")

    def test_temp_region_aware_needs_review(self):
        us, s = apply_op("temp", "-10~45℃", "", "US")
        self.assertEqual(us, "14 °F to 113 °F / -10 °C to 45 °C")
        self.assertEqual(s, NEEDS_REVIEW)   # charge/discharge split stays human
        self.assertEqual(apply_op("temp", "-10~45℃", "", "JP")[0], "-10 °C to 45 °C")

    def test_cycle_life_and_dc12(self):
        self.assertEqual(apply_op("cycle_life", "6000 Cycles（90%DOD）", "", "JP")[0], "6000 cycles to 70%+ capacity")
        self.assertEqual(apply_op("dc12", "12V, 10A Max", "", "JP")[0], "12 V⎓10 A max.")

    def test_default_and_passthrough(self):
        self.assertEqual(apply_op("default", "", "LiFePO₄", "JP"), ("LiFePO₄", DIRECT))
        self.assertEqual(apply_op("passthrough", "JHP-2000A HTE…", "", "US", parts=["JHP-2000A", "HTE…"]),
                         ("JHP-2000A", DIRECT))

    def test_manual_and_exclude_and_missing(self):
        self.assertEqual(apply_op("manual", "AC 100V", "", "JP"), ("AC 100V", NEEDS_REVIEW))
        self.assertEqual(apply_op("exclude", "IP20", "", "JP"), (None, EXCLUDED))
        self.assertEqual(apply_op("capacity", "", "", "JP"), (None, NEEDS_REVIEW))   # no raw, no default

    def test_transform_no_match_abstains(self):
        # op recognised but raw not the expected shape -> needs_review, never a wrong guess
        v, s = apply_op("capacity", "garbage no numbers", "", "JP")
        self.assertEqual(s, NEEDS_REVIEW)


class DisplayWidthTests(unittest.TestCase):
    def test_cjk_counts_double(self):
        self.assertEqual(display_width("ABC"), 3)
        self.assertEqual(display_width("充電方法"), 8)
        self.assertEqual(display_width("4 ご確認Wi-Fi・Bluetoothの設定"), 30)


class FindAndExtractTests(unittest.TestCase):
    SHEET = "\n".join([
        "额定容量 (Wh)", "", "Nominal: 2048Wh，Battery Cell：DFD", "51.2V/40Ah (Note:16S2P)", "",
        "型号:", "产品重量 (Kg)", "", "About 18.8Kg", "",
        "客户型号", "", "制造商型号", "", "JHP-2000A", "", "HTE1522000A-US-JAK",
    ])

    def test_find_field_value_block(self):
        headers = {"额定容量(Wh)", "型号", "产品重量(Kg)", "客户型号", "制造商型号"}
        raw, parts = find_field_value(self.SHEET.splitlines(), "额定容量(Wh)", headers=headers)
        self.assertIn("2048Wh", raw)
        self.assertEqual(len(parts), 2)

    def test_find_field_value_skips_paired_header(self):
        # 客户型号 / 制造商型号 are a 2-col header pair; the value (JHP-2000A) follows
        # both headers. The first captured part is this field's value (a passthrough
        # op uses parts[0]); the manufacturer code may leak as a 2nd part.
        headers = {"客户型号", "制造商型号"}
        _, parts = find_field_value(self.SHEET.splitlines(), "客户型号", headers=headers)
        self.assertEqual(parts[0], "JHP-2000A")

    def test_extract_candidates_applies_rules(self):
        rules = [
            FieldRule("capacity", "GENERAL INFO", "Capacity", "额定容量(Wh)", "capacity"),
            FieldRule("weight", "GENERAL INFO", "Weight", "产品重量(Kg)", "weight"),
            FieldRule("cell_chemistry", "GENERAL INFO", "Cell", "(默认)", "default", default="LiFePO₄"),
            FieldRule("ip", "-", "-", "防护等级", "exclude", manual_facing=False),
        ]
        rows = extract_candidates(self.SHEET, rules, region="US", document_key="JHP-2000A_US")
        by = {r["Row_key"]: r for r in rows}
        self.assertEqual(by["capacity"]["value"], "2048 Wh (40 Ah / 51.2 V DC)")
        self.assertEqual(by["weight"]["value"], "About 41.45 lbs/18.8 kg")    # US dual unit
        self.assertEqual(by["cell_chemistry"]["value"], "LiFePO₄")
        self.assertNotIn("ip", by)   # exclude + non-manual-facing dropped
        self.assertTrue(all(r["document_key"] == "JHP-2000A_US" for r in rows))


class FieldRuleTests(unittest.TestCase):
    def test_from_dict_bilingual_keys(self):
        r = FieldRule.from_dict({"Row_key": "weight", "章节": "GENERAL INFO", "行标签": "Weight",
                                 "规格书字段": "产品重量(Kg)", "取值规则": "weight", "Line_order": "1"})
        self.assertEqual((r.row_key, r.op, r.section), ("weight", "weight", "GENERAL INFO"))
        self.assertEqual(r.line_order, 1)


if __name__ == "__main__":
    unittest.main()
