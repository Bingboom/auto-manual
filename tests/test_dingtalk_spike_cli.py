from __future__ import annotations

import io
import json
from contextlib import redirect_stdout, redirect_stderr
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.dingtalk import spike_cli


class TestDingTalkSpikeCli(unittest.TestCase):
    def test_render_template_object_should_render_nested_values(self) -> None:
        rendered = spike_cli.render_template_object(
            {
                "record_id": "{record_id}",
                "nested": ["{corp_id}", {"url": "https://api.example.com/{record_id}"}],
            },
            {"record_id": "rec-123", "corp_id": "ding-001"},
        )

        self.assertEqual(
            {
                "record_id": "rec-123",
                "nested": ["ding-001", {"url": "https://api.example.com/rec-123"}],
            },
            rendered,
        )

    def test_extract_json_path_should_support_lists(self) -> None:
        payload = {"items": [{"id": "recA"}, {"id": "recB"}]}

        self.assertEqual("recA", spike_cli.extract_json_path(payload, "items[0].id"))

    def test_extract_json_path_should_raise_readable_error_for_missing_key(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "JSON path 'items\\[0\\]\\.id' is missing object key 'items'"):
            spike_cli.extract_json_path({}, "items[0].id")

    def test_parse_update_set_should_decode_json_scalars(self) -> None:
        self.assertEqual(
            {"enabled": True, "count": 2, "label": "hello"},
            spike_cli.parse_update_set(["enabled=true", "count=2", "label=hello"]),
        )

    def test_multipart_body_should_include_file_name_and_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "sample.docx"
            file_path.write_bytes(b"fake-docx")

            body, content_type = spike_cli._multipart_body(
                file_field_name="file",
                file_path=file_path,
                extra_fields={"folder": "sandbox"},
                filename_field_name="fileName",
            )

        self.assertIn("multipart/form-data; boundary=", content_type)
        body_text = body.decode("utf-8", errors="replace")
        self.assertIn('name="folder"', body_text)
        self.assertIn("sandbox", body_text)
        self.assertIn('name="fileName"', body_text)
        self.assertIn("sample.docx", body_text)

    def test_build_update_body_should_support_convenience_fields(self) -> None:
        args = spike_cli.parse_args(
            [
                "update",
                "--client-id",
                "app",
                "--client-secret",
                "secret",
                "--corp-id",
                "dingcorp",
                "--update-set",
                "BuildStatus=\"OK\"",
            ]
        )

        body = spike_cli.build_update_body(
            args,
            record_id="rec-123",
            context={"record_id": "rec-123"},
        )

        self.assertEqual(
            {
                "record_id": "rec-123",
                "fields": {"BuildStatus": "OK"},
            },
            body,
        )

    def test_load_json_arg_should_support_file_reference(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            payload_path = Path(tmp_dir) / "payload.json"
            payload_path.write_text(json.dumps({"hello": "world"}), encoding="utf-8")

            payload = spike_cli.load_json_arg("@" + str(payload_path))

        self.assertEqual({"hello": "world"}, payload)

    def test_parse_args_help_should_exit_cleanly_and_show_actions(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        with self.assertRaises(SystemExit) as exc_info:
            with redirect_stdout(stdout), redirect_stderr(stderr):
                spike_cli.parse_args(["-h"])

        self.assertEqual(0, exc_info.exception.code)
        help_text = stdout.getvalue() + stderr.getvalue()
        self.assertIn("Manual DingTalk Phase 0 smoke CLI", help_text)
        self.assertIn("token", help_text)
        self.assertIn("all", help_text)

    def test_main_token_should_not_touch_followup_steps(self) -> None:
        with (
            mock.patch.object(spike_cli, "resolve_access_token", return_value=("token-123", {})),
            mock.patch.object(
                spike_cli,
                "run_list_step",
                side_effect=AssertionError("list step should not run for token"),
            ),
            mock.patch.object(
                spike_cli,
                "run_update_step",
                side_effect=AssertionError("update step should not run for token"),
            ),
            mock.patch.object(
                spike_cli,
                "run_upload_step",
                side_effect=AssertionError("upload step should not run for token"),
            ),
        ):
            exit_code = spike_cli.main(["token", "--client-id", "id", "--client-secret", "secret", "--corp-id", "corp"])

        self.assertEqual(0, exit_code)

    def test_main_all_should_require_explicit_record_id_by_default(self) -> None:
        with (
            mock.patch.object(spike_cli, "resolve_access_token", return_value=("token-123", {})),
            mock.patch.object(spike_cli, "run_list_step", return_value=({}, "rec-listed")),
            mock.patch.object(spike_cli, "run_update_step") as mocked_update,
            mock.patch.object(spike_cli, "run_upload_step") as mocked_upload,
        ):
            with self.assertRaisesRegex(RuntimeError, "'all' requires explicit --record-id by default"):
                spike_cli.main(
                    [
                        "all",
                        "--client-id",
                        "id",
                        "--client-secret",
                        "secret",
                        "--corp-id",
                        "corp",
                        "--list-url",
                        "https://example.com/list",
                        "--record-id-path",
                        "items[0].id",
                        "--update-url",
                        "https://example.com/update/{record_id}",
                        "--update-set",
                        "status=\"ok\"",
                        "--upload-url",
                        "https://example.com/upload",
                        "--upload-file",
                        __file__,
                    ]
                )

        mocked_update.assert_not_called()
        mocked_upload.assert_not_called()

    def test_run_upload_step_should_allow_json_mode_without_local_file(self) -> None:
        args = spike_cli.parse_args(
            [
                "upload",
                "--client-id",
                "id",
                "--client-secret",
                "secret",
                "--corp-id",
                "corp",
                "--upload-url",
                "https://example.com/upload",
                "--upload-body-json",
                "{\"name\":\"smoke\"}",
            ]
        )

        with mock.patch.object(
            spike_cli,
            "http_request",
            return_value=spike_cli.HttpResponse(
                status=200,
                url="https://example.com/upload",
                headers={},
                text="{\"ok\":true}",
                json_payload={"ok": True},
            ),
        ):
            payload = spike_cli.run_upload_step(args, access_token="token-123")

        self.assertEqual({"ok": True}, payload)
