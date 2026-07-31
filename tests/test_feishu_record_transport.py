from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest import mock

from tools.feishu_record_transport import run_lark_cli_json
from tools.queue_lark_ops import run_lark_cli_json as run_queue_lark_cli_json


class FeishuRecordTransportTests(unittest.TestCase):
    def _run(self, *, stdout: str, returncode: int = 0) -> mock.Mock:
        return mock.Mock(returncode=returncode, stdout=stdout, stderr="")

    def test_runs_and_validates_json_in_shared_transport(self) -> None:
        process = self._run(stdout=json.dumps({"code": 0, "data": {"ok": True}}))
        with mock.patch("tools.feishu_record_transport.subprocess.run", return_value=process) as run:
            payload = run_lark_cli_json(
                cli_bin="lark-cli",
                args=["base", "+record-list"],
                repo_root=Path("/repo"),
                resolved_cli_command_parts=lambda _: ["/bin/lark-cli"],
                parse_json_payload=json.loads,
                format_command=lambda cmd: " ".join(cmd),
            )

        self.assertEqual({"ok": True}, payload["data"])
        run.assert_called_once_with(
            ["/bin/lark-cli", "base", "+record-list"],
            cwd="/repo",
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def test_reports_command_failure_through_injected_formatter(self) -> None:
        process = self._run(stdout="out", returncode=2)
        failure = mock.Mock(return_value="translated failure")
        with mock.patch("tools.feishu_record_transport.subprocess.run", return_value=process):
            with self.assertRaisesRegex(RuntimeError, "translated failure"):
                run_lark_cli_json(
                    cli_bin="lark-cli",
                    args=["base", "+record-upsert"],
                    repo_root=Path("/repo"),
                    resolved_cli_command_parts=lambda _: ["/bin/lark-cli"],
                    parse_json_payload=json.loads,
                    command_failure_message=failure,
                )
        failure.assert_called_once_with(
            ["/bin/lark-cli", "base", "+record-upsert"], "out", "", 2
        )

    def test_queue_runner_delegates_to_shared_transport(self) -> None:
        with mock.patch(
            "tools.feishu_record_transport.run_lark_cli_json",
            return_value={"code": 0},
        ) as run:
            result = run_queue_lark_cli_json(
                cli_bin="lark-cli",
                args=["drive", "metas"],
                repo_root=Path("/repo"),
                resolved_cli_command_parts=lambda _: ["/bin/lark-cli"],
                parse_json_payload=json.loads,
                format_command=lambda cmd: " ".join(cmd),
                command_failure_message=lambda *_: "failure",
            )

        self.assertEqual({"code": 0}, result)
        self.assertEqual(
            {
                "cli_bin": "lark-cli",
                "args": ["drive", "metas"],
                "repo_root": Path("/repo"),
                "resolved_cli_command_parts": mock.ANY,
                "parse_json_payload": mock.ANY,
                "format_command": mock.ANY,
                "command_failure_message": mock.ANY,
            },
            run.call_args.kwargs,
        )


if __name__ == "__main__":
    unittest.main()
