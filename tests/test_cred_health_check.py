from __future__ import annotations

import json
import os
import unittest
from unittest import mock

from tools.cred_health_check import ProbeResult, _failure_detail, main, probe_github


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

    def test_json_error_without_keywords_reports_code_and_message(self) -> None:
        stderr = (
            "[sync-data] ERROR: [table: translation_memory] Lark CLI base command failed "
            "with exit code 1; stdout={\n"
            '  "ok": false,\n'
            '  "error": {\n'
            '    "code": 1254302,\n'
            '    "message": "RolePermNotAllow"\n'
            "  }\n"
            "}"
        )
        detail = _failure_detail(stderr, "", 1)
        self.assertEqual("code=1254302 message=RolePermNotAllow table=translation_memory", detail)

    def test_json_error_passes_through_no_identifiers(self) -> None:
        payload = {
            "ok": False,
            "error": {
                "code": 91403,
                "message": (
                    "no permission for Zq7kP2mXw9LrT4vBn8YcD3sFh6J table tblQw3Er5Ty7Ui9Op, "
                    "see https://user:pw@open.feishu.cn/doc?token=abc access_token=sk-1"
                ),
                "log_id": "20261117164640ABCDEF0123456789",
                "troubleshooter": "https://open.feishu.cn/search?log_id=20261117164640ABCDEF",
                "request_id": "req-7f3a9c1e2b4d5f6a7b8c9d0e",
            },
        }
        detail = _failure_detail(json.dumps(payload, indent=2), "", 1)
        self.assertTrue(detail.startswith("code=91403 message=no permission for "))
        for leaked in (
            "Zq7kP2mXw9LrT4vBn8YcD3sFh6J",
            "tblQw3Er5Ty7Ui9Op",
            "open.feishu.cn",
            "user:pw",
            "sk-1",
            "20261117164640",
            "req-7f3a",
            "log_id",
            "troubleshooter",
        ):
            self.assertNotIn(leaked, detail)
        self.assertNotIn("\n", detail)

    def test_long_message_is_bounded(self) -> None:
        payload = {"error": {"code": 1, "message": "word " * 200}}
        detail = _failure_detail(json.dumps(payload), "", 1)
        self.assertLessEqual(len(detail), len("code=1 message=") + 160)

    def test_truncated_json_still_reports_the_code(self) -> None:
        stderr = '{\n  "ok": false,\n  "error": {\n    "code": 91403,\n    "message": "you don\'t have'
        detail = _failure_detail(stderr, "", 1)
        self.assertEqual("code=91403 message=you don't have", detail)

    def test_malformed_json_without_code_falls_back_to_scrubbed_keyword_line(self) -> None:
        stderr = '{ "error": oops\nRuntimeError: failed for tblQw3Er5Ty7Ui9Op\n}'
        detail = _failure_detail(stderr, "", 1)
        self.assertIn("RuntimeError: failed for", detail)
        self.assertNotIn("tblQw3Er5Ty7Ui9Op", detail)

    def test_success_payload_is_not_mistaken_for_an_error(self) -> None:
        detail = _failure_detail('{"code": 0, "data": {}}\nTraceback: boom', "", 1)
        self.assertEqual("Traceback: boom", detail)


class TestGithubProbe(unittest.TestCase):
    def test_missing_github_token_is_skipped(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            result = probe_github()
        self.assertEqual("skipped", result.status)
        self.assertIn("GITHUB_TOKEN", result.detail)

    def test_missing_gh_cli_is_skipped(self) -> None:
        with mock.patch.dict(os.environ, {"GITHUB_TOKEN": "token"}, clear=True), mock.patch(
            "shutil.which", return_value=None
        ):
            result = probe_github()
        self.assertEqual("skipped", result.status)
        self.assertIn("gh CLI not installed", result.detail)

    def test_gh_auth_status_success_is_ok(self) -> None:
        with mock.patch.dict(os.environ, {"GITHUB_TOKEN": "token"}, clear=True), mock.patch(
            "shutil.which", return_value="/usr/bin/gh"
        ), mock.patch(
            "tools.cred_health_check._run", return_value=(0, "Logged in to github.com", "")
        ):
            result = probe_github()
        self.assertEqual("ok", result.status)

    def test_gh_auth_status_failure_is_failed(self) -> None:
        with mock.patch.dict(os.environ, {"GITHUB_TOKEN": "token"}, clear=True), mock.patch(
            "shutil.which", return_value="/usr/bin/gh"
        ), mock.patch(
            "tools.cred_health_check._run", return_value=(1, "", "authentication failed")
        ):
            result = probe_github()
        self.assertEqual("failed", result.status)


class TestMain(unittest.TestCase):
    def test_main_succeeds_when_all_probes_pass_or_skip(self) -> None:
        with mock.patch(
            "tools.cred_health_check.probe_feishu",
            return_value=ProbeResult("Feishu", "ok", "ok"),
        ), mock.patch(
            "tools.cred_health_check.probe_github",
            return_value=ProbeResult("GitHub", "skipped", "skipped"),
        ):
            code = main(["--config", "configs/config.us.yaml"])
        self.assertEqual(code, 0)

    def test_main_fails_when_probe_fails(self) -> None:
        with mock.patch(
            "tools.cred_health_check.probe_feishu",
            return_value=ProbeResult("Feishu", "failed", "token expired"),
        ), mock.patch(
            "tools.cred_health_check.probe_github",
            return_value=ProbeResult("GitHub", "ok", "ok"),
        ):
            code = main(["--config", "configs/config.us.yaml"])
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
