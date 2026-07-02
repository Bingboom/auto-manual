from __future__ import annotations

import unittest

from tools.cred_health_check import _failure_detail


class TestFailureDetail(unittest.TestCase):
    def test_multiline_json_dump_yields_error_line_not_brace(self) -> None:
        stderr = (
            '{\n'
            '  "ok": false,\n'
            '  "error": {\n'
            '    "code": 91403,\n'
            '    "message": "you don\'t have permission"\n'
            '  }\n'
            '}'
        )
        detail = _failure_detail(stderr, "", 1)
        self.assertNotEqual(detail, "}")
        self.assertIn("permission", detail)

    def test_plain_error_line_is_surfaced(self) -> None:
        detail = _failure_detail("RuntimeError: FEISHU_PHASE2_BASE_TOKEN missing", "", 2)
        self.assertIn("FEISHU_PHASE2_BASE_TOKEN", detail)

    def test_no_error_keyword_falls_back_to_tail_lines(self) -> None:
        detail = _failure_detail("alpha\nbeta\ngamma", "", 1)
        self.assertEqual(detail, "alpha | beta | gamma")

    def test_empty_output_reports_exit_code(self) -> None:
        self.assertEqual(_failure_detail("", "", 7), "exit=7")

    def test_detail_is_capped(self) -> None:
        detail = _failure_detail("error: " + "x" * 1000, "", 1)
        self.assertLessEqual(len(detail), 300)


if __name__ == "__main__":
    unittest.main()
