from __future__ import annotations

import unittest
from pathlib import Path

from tools.new_line_scaffold import build_plan


ROOT = Path(__file__).resolve().parents[1]


class TestNewLineScaffold(unittest.TestCase):
    def test_kr_replay_has_no_unexpected_scaffold_diff(self) -> None:
        plan = build_plan(ROOT / "configs/config.kr.yaml", root=ROOT)

        self.assertEqual("KR", plan.target["region"])
        self.assertEqual(["ko"], plan.target["languages"])
        self.assertEqual([], list(plan.whitelist_diff))
        self.assertEqual("passed", plan.validation["status"])
        self.assertEqual("blocked", plan.write_policy["source_table_write"])

    def test_au_replay_has_no_unexpected_scaffold_diff(self) -> None:
        plan = build_plan(ROOT / "configs/config.au-en.yaml", root=ROOT)

        self.assertEqual("AU", plan.target["region"])
        self.assertEqual(["en"], plan.target["languages"])
        self.assertEqual([], list(plan.whitelist_diff))
        self.assertEqual("passed", plan.validation["status"])

    def test_replay_plan_includes_source_table_boundaries(self) -> None:
        plan = build_plan(ROOT / "configs/config.kr.yaml", root=ROOT)

        self.assertIn("source-table", {reference.role for reference in plan.references})
        self.assertIn(
            {"role": "source-table", "path": "data/phase2", "operation": "F6-gated"},
            plan.write_surface,
        )


if __name__ == "__main__":
    unittest.main()
