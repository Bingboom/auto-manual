from __future__ import annotations

import os
import unittest
from unittest import mock

from tools.cred_health_check import _failure_detail, probe_dingtalk_docs_session


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


class TestDingTalkDocsSessionProbe(unittest.TestCase):
    def test_missing_session_secret_is_skipped_and_names_missing_values(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            result = probe_dingtalk_docs_session()

        self.assertEqual("skipped", result.status)
        self.assertIn("DINGTALK_DOCS_COOKIE", result.detail)
        self.assertIn("DINGTALK_DOCS_XSRF_TOKEN", result.detail)
        self.assertIn("DINGTALK_DOCS_A_TOKEN", result.detail)

    def test_configured_session_runs_authenticated_read_only_probe(self) -> None:
        values = {
            "DINGTALK_DOCS_COOKIE": "cookie",
            "DINGTALK_DOCS_XSRF_TOKEN": "xsrf",
            "DINGTALK_DOCS_A_TOKEN": "a-token",
        }
        with mock.patch.dict(os.environ, values, clear=True), mock.patch(
            "tools.dingtalk.alidocs_session.check_authenticated_session"
        ) as check:
            result = probe_dingtalk_docs_session()

        self.assertEqual("ok", result.status)
        check.assert_called_once()


if __name__ == "__main__":
    unittest.main()
