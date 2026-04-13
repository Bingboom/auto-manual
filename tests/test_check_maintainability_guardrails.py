from __future__ import annotations

import unittest

from tests.test_helpers import temp_test_root, write_lines
from tools import check_maintainability_guardrails as guardrails


class TestCheckMaintainabilityGuardrails(unittest.TestCase):
    def test_collect_hotspot_failures_returns_empty_within_threshold(self) -> None:
        with temp_test_root() as root:
            write_lines(root / "build.py", ["print('ok')"])

            failures = guardrails.collect_hotspot_failures(
                root,
                thresholds={"build.py": 5},
            )

        self.assertEqual([], failures)

    def test_collect_hotspot_failures_reports_threshold_regression(self) -> None:
        with temp_test_root() as root:
            write_lines(root / "tools" / "build_docs.py", ["line 1", "line 2", "line 3"])

            failures = guardrails.collect_hotspot_failures(
                root,
                thresholds={"tools/build_docs.py": 2},
            )

        self.assertEqual(1, len(failures))
        self.assertEqual("tools/build_docs.py", failures[0].path)
        self.assertEqual(3, failures[0].actual_lines)
        self.assertEqual(2, failures[0].max_lines)

    def test_collect_hotspot_failures_requires_expected_file(self) -> None:
        with temp_test_root() as root:
            with self.assertRaisesRegex(RuntimeError, "Guardrail target does not exist"):
                guardrails.collect_hotspot_failures(
                    root,
                    thresholds={"tools/process_build_queue.py": 10},
                )


if __name__ == "__main__":
    unittest.main()
