from __future__ import annotations

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
