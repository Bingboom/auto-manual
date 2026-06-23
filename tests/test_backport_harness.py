#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CI guard for the backport integration harness (tools/backport_harness.py, L5).

Runs every harness fixture through the full pipeline in CI so the end-to-end
multi-edit coverage can only grow, and checks the harness self-detects a broken
fixture (so a green run actually means something).
"""
from __future__ import annotations

import sys
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.backport_harness import get_fixtures, main, run_fixture  # noqa: E402


class BackportHarnessTests(unittest.TestCase):
    def test_every_fixture_passes_full_pipeline(self) -> None:
        for fixture in get_fixtures():
            with self.subTest(fixture=fixture.name):
                result = run_fixture(fixture)
                self.assertTrue(
                    result["passed"],
                    f"{fixture.name}: {result['mismatches']} (observed={result['observed']})",
                )

    def test_main_check_exits_zero(self) -> None:
        self.assertEqual(main(["check"]), 0)
        self.assertEqual(main(["check", "--json"]), 0)
        self.assertEqual(main(["list"]), 0)

    def test_fixtures_span_languages_and_route_classes(self) -> None:
        fixtures = get_fixtures()
        langs = {fx.lang for fx in fixtures}
        self.assertGreaterEqual(len(langs), 3, "harness should span multiple languages")
        routes: set[str] = set()
        for fx in fixtures:
            routes.update(fx.expect_routes)
        for required in ("repo_review_text", "source_table_suggestion", "needs_human_mapping"):
            self.assertIn(required, routes, f"harness must exercise {required}")

    def test_harness_detects_a_broken_expectation(self) -> None:
        # Corrupt one fixture's expectation: the harness must report it as failed,
        # proving the assertions are live (a green run is meaningful).
        broken = replace(get_fixtures()[0], expect_routes={"repo_review_text": 99})
        result = run_fixture(broken)
        self.assertFalse(result["passed"])
        self.assertTrue(result["mismatches"])

    def test_missing_edit_target_is_rejected(self) -> None:
        # A fixture whose edit target is absent must raise, not silently no-op.
        broken = replace(get_fixtures()[0], edits=[("THIS TEXT IS NOT IN THE DOC", "x")])
        with self.assertRaises(ValueError):
            run_fixture(broken)


if __name__ == "__main__":
    unittest.main()
