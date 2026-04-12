from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest import mock

from tools.dingtalk import openapi_upload_cli


class TestDingTalkOpenAPIUploadCli(unittest.TestCase):
    def test_parse_args_should_require_file(self) -> None:
        with self.assertRaises(SystemExit):
            openapi_upload_cli.parse_args([])

    def test_main_should_return_error_for_missing_file(self) -> None:
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            exit_code = openapi_upload_cli.main(["--file", "missing.docx"])

        self.assertEqual(1, exit_code)
        self.assertIn("Upload file does not exist", stderr.getvalue())

    def test_main_dry_run_should_use_env_defaults_and_emit_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "sample.docx"
            file_path.write_bytes(b"fake-docx")
            stdout = io.StringIO()
            with (
                redirect_stdout(stdout),
                mock.patch.object(
                    openapi_upload_cli,
                    "get_app_only_token",
                    return_value=type("Token", (), {"access_token": "token-123"})(),
                ),
                mock.patch.object(
                    openapi_upload_cli,
                    "load_default_target_node_url",
                    return_value="https://alidocs.dingtalk.com/i/nodes/node-123",
                ),
                mock.patch.object(
                    openapi_upload_cli,
                    "load_operator_union_id",
                    return_value="union-123",
                ),
                mock.patch.object(
                    openapi_upload_cli,
                    "request_upload_info",
                    return_value=type(
                        "UploadInfo",
                        (),
                        {
                            "upload_key": "upload-key",
                            "upload_request": type("UploadRequest", (), {"method": "PUT", "url": "https://upload.example.com/object-a"})(),
                        },
                    )(),
                ),
            ):
                exit_code = openapi_upload_cli.main(["--file", str(file_path), "--dry-run", "--json"])

        self.assertEqual(0, exit_code)
        payload = json.loads(stdout.getvalue())
        self.assertEqual("dry-run", payload["mode"])
        self.assertEqual("union-123", payload["operator_union_id"])
        self.assertEqual("node-123", payload["parent_node_id"])
        self.assertEqual("upload-key", payload["upload_key"])

    def test_main_upload_should_print_committed_identifiers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "sample.docx"
            file_path.write_bytes(b"fake-docx")
            stdout = io.StringIO()
            with (
                redirect_stdout(stdout),
                mock.patch.object(
                    openapi_upload_cli,
                    "get_app_only_token",
                    return_value=type("Token", (), {"access_token": "token-123"})(),
                ),
                mock.patch.object(
                    openapi_upload_cli,
                    "request_upload_info",
                    return_value=type(
                        "UploadInfo",
                        (),
                        {
                            "upload_key": "upload-key",
                            "file_name": "sample.docx",
                            "file_size": file_path.stat().st_size,
                        },
                    )(),
                ),
                mock.patch.object(openapi_upload_cli, "upload_file_with_signed_url") as mocked_upload,
                mock.patch.object(
                    openapi_upload_cli,
                    "commit_uploaded_file",
                    return_value=type(
                        "Committed",
                        (),
                        {
                            "dentry_id": "file-id-123",
                            "dentry_uuid": "file-uuid-456",
                            "candidate_node_url": "https://alidocs.dingtalk.com/i/nodes/file-uuid-456",
                        },
                    )(),
                ),
            ):
                exit_code = openapi_upload_cli.main(
                    [
                        "--file",
                        str(file_path),
                        "--parent-node-url",
                        "https://alidocs.dingtalk.com/i/nodes/node-123",
                        "--operator-union-id",
                        "union-123",
                    ]
                )

        self.assertEqual(0, exit_code)
        self.assertIn("dentry_uuid: file-uuid-456", stdout.getvalue())
        self.assertIn("candidate_node_url: https://alidocs.dingtalk.com/i/nodes/file-uuid-456", stdout.getvalue())
        mocked_upload.assert_called_once()
