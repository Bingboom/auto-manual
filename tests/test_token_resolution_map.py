#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the token/copy resolution value index (Milestone F, PR F2)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.cloud_doc_backport import _classify_route, _looks_data_like, diff_blocks, parse_blocks  # noqa: E402
from tools.token_resolution_map import (  # noqa: E402
    build_value_index,
    classify_data_origin,
)

_SPEC_MASTER = (
    "document_key,Row_key,Slot_key,Value_uk,Param_uk,Row_label_uk,Value_en\n"
    "JE-1000F_EU,dc12_port,main,DC 12 В,,,DC 12 V\n"
)
_LOCALIZED_COPY = (
    "copy_key,text_uk,text_en\n"
    "op_guide.title,Посібник користувача,Operation Guide\n"
    "dup.a,,Shared Value\n"
    "dup.b,,Shared Value\n"
)


def _snapshot(tmp: str) -> Path:
    root = Path(tmp)
    (root / "Spec_Master.csv").write_text(_SPEC_MASTER, encoding="utf-8")
    (root / "Localized_Copy.csv").write_text(_LOCALIZED_COPY, encoding="utf-8")
    return root


class BuildValueIndexTests(unittest.TestCase):
    def test_indexes_spec_master_and_localized_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            index = build_value_index(_snapshot(tmp), "uk")
            spec = index["DC 12 В"]
            self.assertEqual(spec["table"], "Spec_Master")
            self.assertEqual(spec["row_key"], "dc12_port")
            self.assertEqual(spec["slot_key"], "main")
            copy = index["Посібник користувача"]
            self.assertEqual(copy["table"], "Localized_Copy")
            self.assertEqual(copy["copy_key"], "op_guide.title")

    def test_line_order_is_carried_for_fallback_disambiguation(self) -> None:
        # A multi-line spec row carries Line_order on its source_ref so the sidecar
        # can disambiguate an otherwise-ambiguous (doc, Row_key, empty Slot_key) key.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Spec_Master.csv").write_text(
                "document_key,Row_key,Slot_key,Line_order,Value_en\nD,storage_temperature,,2,32 F to 113 F\n",
                encoding="utf-8",
            )
            index = build_value_index(root, "en")
            self.assertEqual(index["32 F to 113 F"]["line_order"], "2")

    def test_lang_selects_value_column(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            index = build_value_index(_snapshot(tmp), "en")
            self.assertIn("Operation Guide", index)  # text_en
            self.assertIn("DC 12 V", index)  # Value_en
            self.assertNotIn("DC 12 В", index)  # uk column not selected for en

    def test_duplicate_value_marked_ambiguous(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            index = build_value_index(_snapshot(tmp), "en")
            self.assertTrue(index["Shared Value"].get("ambiguous"))

    def test_missing_csv_yields_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(build_value_index(Path(tmp), "uk"), {})

    def test_source_language_indexes_value_source_column(self) -> None:
        # Real Spec_Master carries Value_source + Source_lang (no Value_en); a
        # source-language review (US-en) must still index the source value as Class D.
        spec = (
            "document_key,Row_key,Slot_key,Source_lang,Value_source,Value_fr\n"
            "JE-1000F_US,ac_out,main,en,1500 W,1500 W FR\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "Spec_Master.csv").write_text(spec, encoding="utf-8")
            index = build_value_index(Path(tmp), "en")
            self.assertIn("1500 W", index)  # Value_source indexed for the en-source row
            self.assertEqual(index["1500 W"]["field"], "Value_source")
            self.assertEqual(index["1500 W"]["row_key"], "ac_out")

    def test_non_source_language_ignores_source_column(self) -> None:
        spec = (
            "document_key,Row_key,Slot_key,Source_lang,Value_source,Value_fr\n"
            "JE-1000F_US,ac_out,main,en,1500 W,1500 W FR\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "Spec_Master.csv").write_text(spec, encoding="utf-8")
            index = build_value_index(Path(tmp), "fr")
            self.assertIn("1500 W FR", index)  # the fr reviewer edits the localized value
            self.assertNotIn("1500 W", index)  # the en source value is NOT indexed under fr

    def test_non_spec_page_values_resolve_to_page_placeholders_source(self) -> None:
        spec = (
            "document_key,Page,Row_key,Slot_key,Value_fr\n"
            "JE-2000F_EU,Product overview,usb_a,front.label,USB-A 18 W Sortie\n"
            "JE-2000F_EU,specifications,capacity,value,2042 Wh\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "Spec_Master.csv").write_text(spec, encoding="utf-8")
            index = build_value_index(Path(tmp), "fr")
            self.assertEqual(index["USB-A 18 W Sortie"]["table"], "Page_Placeholders_Source")
            self.assertEqual(index["USB-A 18 W Sortie"]["field"], "Value_fr")
            self.assertEqual(index["2042 Wh"]["table"], "Spec_Master")


class ClassifyDataOriginTests(unittest.TestCase):
    def test_exact_match_and_whitespace_normalized(self) -> None:
        index = {"Operation Guide": {"table": "Localized_Copy", "copy_key": "x"}}
        self.assertIsNotNone(classify_data_origin("Operation Guide", index))
        self.assertIsNotNone(classify_data_origin("  Operation   Guide ", index))
        self.assertIsNone(classify_data_origin("Operation Manual", index))

    def test_no_index_returns_none(self) -> None:
        self.assertIsNone(classify_data_origin("anything", None))
        self.assertIsNone(classify_data_origin("anything", {}))

    def test_table_row_resolves_via_contained_cell_value(self) -> None:
        # A real cloud-doc delta arrives as a whole table ROW, not a bare cell — it must
        # still resolve to its source value via a cell / <br/>-joined sub-value match.
        index = {"12V⎓最大10A": {"table": "Spec_Master", "row_key": "dc12_port"}}
        hit = classify_data_origin("| 12V⎓最大10A <br/>12V⎓最大10A | LED 灯按键 |", index)
        self.assertIsNotNone(hit)
        self.assertEqual(hit["row_key"], "dc12_port")

    def test_paragraph_without_contained_value_is_none(self) -> None:
        # A prose paragraph that contains no source value does NOT resolve (so it routes
        # to review text, not a false Class D).
        index = {"12V⎓最大10A": {"table": "Spec_Master"}}
        self.assertIsNone(classify_data_origin("产品默认开启节能模式，屏幕将显示提示信息。", index))

    def test_whole_bare_value_still_matches(self) -> None:
        index = {"12V⎓最大10A": {"table": "Spec_Master"}}
        self.assertIsNotNone(classify_data_origin("12V⎓最大10A", index))

    def test_ambiguous_value_abstains(self) -> None:
        # A value in >1 source row (e.g. a port's front.label AND front.spec both "12V⎓最大10A")
        # is marked ambiguous by build_value_index — it can't pick a unique slot, so classify
        # abstains rather than resolving the arbitrary first one (which wrote the wrong slot).
        ambiguous = {"12V⎓最大10A": {"table": "Spec_Master", "slot_key": "front.spec", "ambiguous": True}}
        self.assertIsNone(classify_data_origin("12V⎓最大10A", ambiguous))
        self.assertIsNone(classify_data_origin("| 12V⎓最大10A <br/>12V⎓最大10A | LED 灯按键 |", ambiguous))
        # a unique (non-ambiguous) value still resolves
        unique = {"12V⎓最大10A": {"table": "Spec_Master", "slot_key": "front.spec"}}
        self.assertIsNotNone(classify_data_origin("12V⎓最大10A", unique))

    def test_build_value_index_marks_a_repeated_value_ambiguous(self) -> None:
        # two source rows (front.label + front.spec) sharing the same value -> ambiguous,
        # so the end-to-end classify abstains on it.
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "Spec_Master.csv").write_text(
                "document_key,Row_key,Slot_key,Source_lang,Value_source\n"
                "JE-1000F_CN,dc12_port,front.label,zh,12V⎓最大10A\n"
                "JE-1000F_CN,dc12_port,front.spec,zh,12V⎓最大10A\n",
                encoding="utf-8",
            )
            index = build_value_index(Path(tmp), "zh")
            self.assertTrue(index["12V⎓最大10A"].get("ambiguous"))
            self.assertIsNone(classify_data_origin("12V⎓最大10A", index))


class ClassifyRouteTests(unittest.TestCase):
    def test_data_origin_routes_review_to_source_table_suggestion(self) -> None:
        origin = {"table": "Spec_Master", "row_key": "dc12_port"}
        route, confidence, _ = _classify_route("review", None, None, origin)
        self.assertEqual(route, "source_table_suggestion")
        self.assertEqual(confidence, "high")

    def test_data_origin_routes_template_to_needs_human_mapping(self) -> None:
        origin = {"table": "Spec_Master"}
        route, _, _ = _classify_route("template", None, None, origin)
        self.assertEqual(route, "needs_human_mapping")

    def test_no_data_origin_preserves_existing_behavior(self) -> None:
        # Plain prose with no data origin -> repo_review_text (unchanged).
        route, _, _ = _classify_route("review", None, None, None)
        self.assertEqual(route, "repo_review_text")

    def _block(self, text: str, kind: str):
        for block in parse_blocks(text):
            if block.kind == kind:
                return block
        raise AssertionError(f"no {kind} block in {text!r}")

    def test_value_index_authoritative_suppresses_prose_heuristic(self) -> None:
        # A unit-bearing prose paragraph that matched no source value: with the value
        # index present it is authoritative -> review text (Class R), NOT the heuristic
        # Class D guess. This is the fix for the false-positive (e.g. the 节能模式 append).
        para = self._block("输出功率为 100W 的连续输出说明。", "paragraph")
        self.assertTrue(_looks_data_like(para))  # the heuristic WOULD have flagged it
        route, _, _ = _classify_route("review", para, para, None, None, value_index_present=True)
        self.assertEqual(route, "repo_review_text")

    def test_without_index_prose_unit_like_stays_heuristic_class_d(self) -> None:
        # Same paragraph, no index: the _looks_data_like heuristic still applies (prior behavior).
        para = self._block("输出功率为 100W 的连续输出说明。", "paragraph")
        route, _, _ = _classify_route("review", para, para, None, None, value_index_present=False)
        self.assertEqual(route, "source_table_suggestion")

    def test_table_row_without_match_stays_class_d(self) -> None:
        # A table row is structurally source-table content -> Class D even with no value
        # match and an index present (never write table markup to _review).
        row = self._block("| Port | Note |\n| --- | --- |\n| DC | LED |\n", "table_row")
        route, _, _ = _classify_route("review", row, row, None, None, value_index_present=True)
        self.assertEqual(route, "source_table_suggestion")


class DiffBlocksValueIndexTests(unittest.TestCase):
    def _deltas(self, value_index):
        baseline = parse_blocks("Operation Guide\n")
        fetched = parse_blocks("Operation Manual\n")
        return diff_blocks(
            baseline, fetched, doc_type="review", run_id="t", value_index=value_index
        )

    def test_plain_data_value_is_class_d_with_value_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            index = build_value_index(_snapshot(tmp), "en")
            deltas = self._deltas(index)
            self.assertTrue(deltas)
            data_deltas = [d for d in deltas if d["route_class"] == "source_table_suggestion"]
            self.assertTrue(data_deltas, "expected a data-origin (Class D) delta")
            self.assertEqual(data_deltas[0]["source_ref"]["copy_key"], "op_guide.title")

    def test_without_value_index_plain_text_is_review_text(self) -> None:
        # Same edit, no value index: the plain-text delta stays repo_review_text
        # (this is what F2 improves on -> deterministic Class D detection).
        deltas = self._deltas(None)
        self.assertTrue(deltas)
        self.assertTrue(any(d["route_class"] == "repo_review_text" for d in deltas))
        self.assertFalse(any(d["route_class"] == "source_table_suggestion" for d in deltas))


if __name__ == "__main__":
    unittest.main()
