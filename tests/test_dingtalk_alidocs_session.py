from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.dingtalk import alidocs_session


class TestAliDocsSession(unittest.TestCase):
    def test_load_session_config_from_env_should_read_required_values(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "DINGTALK_DOCS_A_TOKEN": "a-token",
                "DINGTALK_DOCS_XSRF_TOKEN": "xsrf-token",
                "DINGTALK_DOCS_COOKIE": "cookie=value",
            },
            clear=False,
        ):
            config = alidocs_session.load_session_config_from_env()

        self.assertEqual("a-token", config.a_token)
        self.assertEqual("xsrf-token", config.xsrf_token)
        self.assertEqual("cookie=value", config.cookie)

    def test_load_session_config_should_support_custom_env_names(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "ALT_A_TOKEN": "a-token",
                "ALT_XSRF_TOKEN": "xsrf-token",
                "ALT_COOKIE": "cookie=value",
                "ALT_BX_VERSION": "9.9.9",
            },
            clear=False,
        ):
            config = alidocs_session.load_session_config(
                a_token_env="ALT_A_TOKEN",
                xsrf_token_env="ALT_XSRF_TOKEN",
                cookie_env="ALT_COOKIE",
                bx_version_env="ALT_BX_VERSION",
            )

        self.assertEqual("a-token", config.a_token)
        self.assertEqual("xsrf-token", config.xsrf_token)
        self.assertEqual("cookie=value", config.cookie)
        self.assertEqual("9.9.9", config.bx_version)

    def test_request_upload_ticket_should_parse_sts_payload(self) -> None:
        session = alidocs_session.AliDocsSessionConfig(a_token="a", xsrf_token="x", cookie="c")
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "sample.docx"
            file_path.write_bytes(b"fake-docx")
            with mock.patch.object(
                alidocs_session,
                "_json_request",
                return_value={
                    "status": 200,
                    "isSuccess": True,
                    "data": {
                        "uploadKey": "upload-key",
                        "stsSignatureInfo": {
                            "objectKey": "objects/sample.docx",
                            "bucket": "bucket-name",
                            "endPoint": "oss-accelerate.aliyuncs.com",
                            "accessKeyId": "ak",
                            "accessKeySecret": "sk",
                            "accessToken": "sts-token",
                        },
                    },
                },
            ):
                ticket = alidocs_session.request_upload_ticket(
                    session=session,
                    parent_dentry_uuid="node-123",
                    file_path=file_path,
                    referer_url="https://alidocs.dingtalk.com/i/nodes/node-123",
                )

        self.assertEqual("upload-key", ticket.upload_key)
        self.assertEqual("objects/sample.docx", ticket.object_key)
        self.assertEqual("bucket-name", ticket.bucket)

    def test_commit_uploaded_file_should_return_node_url(self) -> None:
        session = alidocs_session.AliDocsSessionConfig(a_token="a", xsrf_token="x", cookie="c")
        ticket = alidocs_session.AliDocsUploadTicket(
            parent_dentry_uuid="node-123",
            upload_key="upload-key",
            object_key="objects/sample.docx",
            bucket="bucket-name",
            endpoint="oss-accelerate.aliyuncs.com",
            access_key_id="ak",
            access_key_secret="sk",
            security_token="sts-token",
            file_name="sample.docx",
            file_size=42,
        )
        with mock.patch.object(
            alidocs_session,
            "_json_request",
            return_value={
                "status": 200,
                "isSuccess": True,
                "data": {
                    "dentryUuid": "file-node-456",
                    "dentryId": "file-id",
                    "name": "sample.docx",
                    "parentDentryUuid": "node-123",
                    "spaceId": "space-1",
                },
            },
        ):
            committed = alidocs_session.commit_uploaded_file(
                session=session,
                ticket=ticket,
                referer_url="https://alidocs.dingtalk.com/i/nodes/node-123",
            )

        self.assertEqual("file-node-456", committed.dentry_uuid)
        self.assertEqual("https://alidocs.dingtalk.com/i/nodes/file-node-456", committed.node_url)

    def test_upload_file_to_node_should_chain_ticket_upload_and_commit(self) -> None:
        session = alidocs_session.AliDocsSessionConfig(a_token="a", xsrf_token="x", cookie="c")
        ticket = alidocs_session.AliDocsUploadTicket(
            parent_dentry_uuid="node-123",
            upload_key="upload-key",
            object_key="objects/sample.docx",
            bucket="bucket-name",
            endpoint="oss-accelerate.aliyuncs.com",
            access_key_id="ak",
            access_key_secret="sk",
            security_token="sts-token",
            file_name="sample.docx",
            file_size=42,
        )
        committed = alidocs_session.AliDocsCommittedFile(
            dentry_uuid="file-node-456",
            dentry_id="file-id",
            name="sample.docx",
            parent_dentry_uuid="node-123",
            space_id="space-1",
            raw_payload={},
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "sample.docx"
            file_path.write_bytes(b"fake-docx")
            with (
                mock.patch.object(alidocs_session, "request_upload_ticket", return_value=ticket) as mocked_ticket,
                mock.patch.object(alidocs_session, "upload_file_to_oss") as mocked_upload,
                mock.patch.object(alidocs_session, "commit_uploaded_file", return_value=committed) as mocked_commit,
            ):
                result = alidocs_session.upload_file_to_node(
                    session=session,
                    file_path=file_path,
                    parent_node_url="https://alidocs.dingtalk.com/i/nodes/node-123",
                )

        self.assertEqual(committed, result)
        mocked_ticket.assert_called_once()
        mocked_upload.assert_called_once_with(ticket=ticket, file_path=file_path)
        mocked_commit.assert_called_once()
