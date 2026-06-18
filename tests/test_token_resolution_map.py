#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the token/copy resolution value index (Milestone F, PR F2)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.cloud_doc_backport import _classify_route, diff_blocks, parse_blocks  # noqa: E402
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


class ClassifyDataOriginTests(unittest.TestCase):
    def test_exact_match_and_whitespace_normalized(self) -> None:
        index = {"Operation Guide": {"table": "Localized_Copy", "copy_key": "x"}}
        self.assertIsNotNone(classify_data_origin("Operation Guide", index))
        self.assertIsNotNone(classify_data_origin("  Operation   Guide ", index))
        self.assertIsNone(classify_data_origin("Operation Manual", index))

    def test_no_index_returns_none(self) -> None:
        self.assertIsNone(classify_data_origin("anything", None))
        self.assertIsNone(classify_data_origin("anything", {}))


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
