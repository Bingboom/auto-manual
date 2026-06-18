#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for family-scope R-vs-T classification (Milestone F, PR F3)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.cloud_doc_backport import _classify_route, diff_blocks, parse_blocks  # noqa: E402
from tools.family_scope import build_family_index, classify_family_scope  # noqa: E402


def _sibling(tmp: str, name: str, text: str) -> Path:
    path = Path(tmp) / name
    path.write_text(text, encoding="utf-8")
    return path


class BuildFamilyIndexTests(unittest.TestCase):
    def test_indexes_lines_to_labels(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fr = _sibling(tmp, "fr.rst", "Shared safety note\nUnique fr line\n")
            de = _sibling(tmp, "de.rst", "Shared safety note\nUnique de line\n")
            index = build_family_index({"fr": fr, "de": de})
            self.assertEqual(index["Shared safety note"], ["de", "fr"])
            self.assertEqual(index["Unique fr line"], ["fr"])

    def test_list_input_uses_path_as_label(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fr = _sibling(tmp, "fr.rst", "Shared line\n")
            index = build_family_index([fr])
            self.assertEqual(index["Shared line"], [str(fr)])

    def test_missing_file_skipped(self) -> None:
        index = build_family_index([Path("/no/such/file.rst")])
        self.assertEqual(index, {})


class ClassifyFamilyScopeTests(unittest.TestCase):
    def test_shared_and_whitespace_normalized(self) -> None:
        index = {"Shared safety note": ["de", "fr"]}
        scope = classify_family_scope("  Shared   safety  note ", index)
        self.assertEqual(scope, {"shared": True, "targets": ["de", "fr"]})

    def test_not_shared_returns_none(self) -> None:
        self.assertIsNone(classify_family_scope("Target only line", {"X": ["fr"]}))
        self.assertIsNone(classify_family_scope("anything", None))


class ClassifyRouteFamilyTests(unittest.TestCase):
    def test_shared_review_span_needs_human_mapping(self) -> None:
        scope = {"shared": True, "targets": ["de", "fr"]}
        route, _, reason = _classify_route("review", None, None, None, scope)
        self.assertEqual(route, "needs_human_mapping")
        self.assertIn("2 family target", reason)

    def test_not_shared_stays_review_text(self) -> None:
        route, _, _ = _classify_route("review", None, None, None, None)
        self.assertEqual(route, "repo_review_text")

    def test_data_origin_takes_precedence_over_family(self) -> None:
        # data_origin set -> Class D regardless of family_scope.
        route, _, _ = _classify_route("review", None, None, {"table": "Spec_Master"}, {"shared": True})
        self.assertEqual(route, "source_table_suggestion")


class DiffBlocksFamilyTests(unittest.TestCase):
    def _deltas(self, family_index):
        baseline = parse_blocks("Shared safety note\n")
        fetched = parse_blocks("Changed safety note\n")
        return diff_blocks(
            baseline, fetched, doc_type="review", run_id="t", family_index=family_index
        )

    def test_shared_span_flagged_with_blast_radius(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fr = _sibling(tmp, "fr.rst", "Shared safety note\n")
            de = _sibling(tmp, "de.rst", "Shared safety note\n")
            index = build_family_index({"fr": fr, "de": de})
            deltas = self._deltas(index)
            shared = [d for d in deltas if d["route_class"] == "needs_human_mapping"]
            self.assertTrue(shared, "expected a shared (needs_decision) delta")
            self.assertEqual(shared[0]["family_scope"], {"shared": True, "targets": ["de", "fr"]})

    def test_without_family_index_stays_review_text(self) -> None:
        deltas = self._deltas(None)
        self.assertTrue(deltas)
        self.assertTrue(any(d["route_class"] == "repo_review_text" for d in deltas))
        self.assertFalse(any(d["route_class"] == "needs_human_mapping" for d in deltas))


if __name__ == "__main__":
    unittest.main()
