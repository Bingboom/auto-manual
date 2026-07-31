from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from unittest import mock

from tools.feishu_record_transport import run_lark_cli_json
from tools.feishu_record_transport import LarkRetryPolicy, iter_lark_pages
from tools.queue_lark_ops import run_lark_cli_json as run_queue_lark_cli_json
from tools import bitable_schema, spec_master_rebuild


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

    def test_retries_rate_limit_with_bounded_exponential_backoff(self) -> None:
        processes = [
            self._run(stdout=json.dumps({"code": 429, "retry_after": 3})),
            self._run(stdout=json.dumps({"code": 429})),
            self._run(stdout=json.dumps({"code": 0, "data": {"ok": True}})),
        ]
        with mock.patch("tools.feishu_record_transport.subprocess.run", side_effect=processes), mock.patch(
            "tools.feishu_record_transport.time.sleep"
        ) as sleep:
            result = run_lark_cli_json(
                cli_bin="lark-cli",
                args=["base", "+record-list"],
                repo_root=Path("/repo"),
                resolved_cli_command_parts=lambda _: ["/bin/lark-cli"],
                parse_json_payload=json.loads,
                retry_policy=LarkRetryPolicy(max_retries=2, base_delay_seconds=1, max_delay_seconds=10),
                sleep=sleep,
            )

        self.assertEqual(0, result["code"])
        self.assertEqual([3, 2], [call.args[0] for call in sleep.call_args_list])

    def test_page_iterator_owns_offset_and_empty_page_policy(self) -> None:
        pages = {
            0: {"data": ["a"], "has_more": True},
            1: {"data": ["b"], "has_more": False},
        }
        seen: list[int] = []

        def fetch(offset: int, _limit: int) -> dict:
            seen.append(offset)
            return pages[offset]

        result = list(
            iter_lark_pages(
                fetch,
                items_from_payload=lambda payload: payload["data"],
                has_more_from_payload=lambda payload, _offset: payload["has_more"],
            )
        )

        self.assertEqual([0, 1], seen)
        self.assertEqual([["a"], ["b"]], [items for _payload, items in result])

        with self.assertRaisesRegex(RuntimeError, "returned no items"):
            list(
                iter_lark_pages(
                    lambda _offset, _limit: {"data": [], "has_more": True},
                    items_from_payload=lambda payload: payload["data"],
                    has_more_from_payload=lambda payload, _offset: payload["has_more"],
                )
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

    def test_bitable_schema_keeps_profile_and_identity_routing_at_wrapper(self) -> None:
        with mock.patch.object(bitable_schema, "_PROFILE", "prod"), mock.patch.object(
            bitable_schema, "_IDENTITY", "user"
        ), mock.patch(
            "tools.feishu_record_transport.run_lark_cli_json", return_value={"code": 0}
        ) as run:
            result = bitable_schema._lark(["base", "+table-list"], "lark-cli")

        self.assertEqual({"code": 0}, result)
        self.assertEqual(
            ["base", "+table-list", "--as", "user"],
            run.call_args.kwargs["args"],
        )
        self.assertEqual(
            ["lark-cli", "--profile", "prod"],
            run.call_args.kwargs["resolved_cli_command_parts"]("ignored"),
        )
        self.assertEqual(
            os.environ.get("LARK_CLI_NO_PROXY", "1"),
            run.call_args.kwargs["environment"]["LARK_CLI_NO_PROXY"],
        )

    def test_spec_master_rebuild_delegates_base_command_to_shared_transport(self) -> None:
        with mock.patch(
            "tools.feishu_record_transport.run_lark_cli_json", return_value={"code": 0}
        ) as run:
            result = spec_master_rebuild._run_lark_base(
                "lark-cli", ["+field-list", "--base-token", "secret"]
            )

        self.assertEqual({"code": 0}, result)
        self.assertEqual(
            ["base", "+field-list", "--base-token", "secret"],
            run.call_args.kwargs["args"],
        )


if __name__ == "__main__":
    unittest.main()
