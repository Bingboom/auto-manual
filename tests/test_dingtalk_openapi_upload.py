from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.dingtalk import openapi_upload


class _FakeResponse:
    def __init__(self, payload: dict[str, object], *, status: int = 200, headers: dict[str, str] | None = None) -> None:
        self._payload = payload
        self.status = status
        self.headers = headers or {}

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


class _FakeRawResponse:
    def __init__(self, body: str = "", *, status: int = 200, headers: dict[str, str] | None = None) -> None:
        self._body = body
        self.status = status
        self.headers = headers or {}

    def read(self) -> bytes:
        return self._body.encode("utf-8")

    def __enter__(self) -> "_FakeRawResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


class TestDingTalkOpenAPIUpload(unittest.TestCase):
    def test_load_env_helpers_should_read_expected_values(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "DINGTALK_OPERATOR_UNION_ID": "union-123",
                "DINGTALK_DEFAULT_TARGET_NODE_URL": "https://alidocs.dingtalk.com/i/nodes/node-123",
            },
            clear=False,
        ):
            self.assertEqual("union-123", openapi_upload.load_operator_union_id())
            self.assertEqual(
                "https://alidocs.dingtalk.com/i/nodes/node-123",
                openapi_upload.load_default_target_node_url(),
            )

    def test_parse_upload_resource_should_support_string_urls(self) -> None:
        payload = {
            "headerSignatureInfo": {
                "resourceUrls": ["https://upload.example.com/object-a"],
                "headers": {"x-oss-object-acl": "private"},
            }
        }

        resource = openapi_upload.parse_upload_resource(payload)

        self.assertEqual("PUT", resource.method)
        self.assertEqual("https://upload.example.com/object-a", resource.url)
        self.assertEqual({"x-oss-object-acl": "private"}, resource.headers)

    def test_parse_upload_resource_should_prefer_internal_urls_when_requested(self) -> None:
        payload = {
            "headerSignatureInfo": {
                "resourceUrls": [{"url": "https://external.example.com/object-a", "method": "PUT"}],
                "internalResourceUrls": [{"url": "https://internal.example.com/object-a", "method": "PUT"}],
                "headers": {"x-meta-test": "true"},
            }
        }

        resource = openapi_upload.parse_upload_resource(payload, prefer_internal_url=True)

        self.assertEqual("https://internal.example.com/object-a", resource.url)
        self.assertEqual({"x-meta-test": "true"}, resource.headers)

    def test_request_upload_info_should_build_official_query_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "sample.docx"
            file_path.write_bytes(b"fake-docx")
            with mock.patch.object(
                openapi_upload.request,
                "urlopen",
                return_value=_FakeResponse(
                    {
                        "uploadKey": "upload-key-123",
                        "headerSignatureInfo": {
                            "resourceUrls": [{"url": "https://upload.example.com/object-a", "method": "PUT"}],
                            "headers": {"x-oss-object-acl": "private"},
                        },
                    }
                ),
            ) as mocked_urlopen:
                upload_info = openapi_upload.request_upload_info(
                    access_token="token-123",
                    parent_node_id="node-123",
                    operator_union_id="union-123",
                    file_path=file_path,
                    prefer_region="cn-hz",
                    prefer_intranet=True,
                )

        req = mocked_urlopen.call_args.args[0]
        self.assertIn("/v2.0/storage/spaces/files/node-123/uploadInfos/query", req.full_url)
        self.assertIn("unionId=union-123", req.full_url)
        body = json.loads(req.data.decode("utf-8"))
        self.assertEqual("HEADER_SIGNATURE", body["protocol"])
        self.assertTrue(body["option"]["preferIntranet"])
        self.assertEqual("cn-hz", body["option"]["preferRegion"])
        self.assertEqual("sample.docx", body["option"]["preCheckParam"]["name"])
        self.assertEqual("upload-key-123", upload_info.upload_key)
        self.assertEqual("https://upload.example.com/object-a", upload_info.upload_request.url)

    def test_upload_file_with_signed_url_should_issue_raw_put(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "sample.docx"
            file_path.write_bytes(b"fake-docx")
            upload_info = openapi_upload.OpenAPIUploadInfo(
                upload_key="upload-key",
                parent_dentry_uuid="node-123",
                operator_union_id="union-123",
                file_name="sample.docx",
                file_size=file_path.stat().st_size,
                upload_request=openapi_upload.OpenAPIUploadRequest(
                    method="PUT",
                    url="https://upload.example.com/object-a",
                    headers={"x-oss-object-acl": "private"},
                ),
                raw_payload={},
            )
            with mock.patch.object(
                openapi_upload.request,
                "urlopen",
                return_value=_FakeRawResponse(status=200),
            ) as mocked_urlopen:
                openapi_upload.upload_file_with_signed_url(upload_info=upload_info, file_path=file_path)

        req = mocked_urlopen.call_args.args[0]
        self.assertEqual("PUT", req.get_method())
        self.assertEqual("https://upload.example.com/object-a", req.full_url)
        self.assertEqual("private", req.headers["X-oss-object-acl"])
        self.assertEqual(b"fake-docx", req.data)

    def test_commit_uploaded_file_should_parse_dentry_and_candidate_url(self) -> None:
        with mock.patch.object(
            openapi_upload.request,
            "urlopen",
            return_value=_FakeResponse(
                {
                    "dentry": {
                        "id": "file-id-123",
                        "uuid": "file-uuid-456",
                        "name": "sample.docx",
                    }
                }
            ),
        ) as mocked_urlopen:
            committed = openapi_upload.commit_uploaded_file(
                access_token="token-123",
                parent_node_id="node-123",
                operator_union_id="union-123",
                upload_key="upload-key",
                file_name="sample.docx",
                file_size=42,
                convert_to_online_doc=True,
                conflict_strategy="AUTO_RENAME",
            )

        req = mocked_urlopen.call_args.args[0]
        self.assertIn("/v2.0/storage/spaces/files/node-123/commit", req.full_url)
        self.assertIn("unionId=union-123", req.full_url)
        body = json.loads(req.data.decode("utf-8"))
        self.assertEqual("upload-key", body["uploadKey"])
        self.assertTrue(body["option"]["convertToOnlineDoc"])
        self.assertEqual("AUTO_RENAME", body["option"]["conflictStrategy"])
        self.assertEqual("file-id-123", committed.dentry_id)
        self.assertEqual("file-uuid-456", committed.dentry_uuid)
        self.assertEqual("https://alidocs.dingtalk.com/i/nodes/file-uuid-456", committed.candidate_node_url)

    def test_upload_file_to_node_should_chain_query_upload_and_commit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "sample.docx"
            file_path.write_bytes(b"fake-docx")
            upload_info = openapi_upload.OpenAPIUploadInfo(
                upload_key="upload-key",
                parent_dentry_uuid="node-123",
                operator_union_id="union-123",
                file_name="sample.docx",
                file_size=file_path.stat().st_size,
                upload_request=openapi_upload.OpenAPIUploadRequest(
                    method="PUT",
                    url="https://upload.example.com/object-a",
                    headers={},
                ),
                raw_payload={},
            )
            committed = openapi_upload.OpenAPICommittedFile(
                dentry_id="file-id-123",
                dentry_uuid="file-uuid-456",
                name="sample.docx",
                raw_payload={},
            )
            with (
                mock.patch.object(openapi_upload, "request_upload_info", return_value=upload_info) as mocked_query,
                mock.patch.object(openapi_upload, "upload_file_with_signed_url") as mocked_upload,
                mock.patch.object(openapi_upload, "commit_uploaded_file", return_value=committed) as mocked_commit,
            ):
                result = openapi_upload.upload_file_to_node(
                    access_token="token-123",
                    operator_union_id="union-123",
                    file_path=file_path,
                    parent_node_url="https://alidocs.dingtalk.com/i/nodes/node-123",
                    convert_to_online_doc=True,
                )

        self.assertEqual(committed, result)
        mocked_query.assert_called_once()
        mocked_upload.assert_called_once()
        mocked_commit.assert_called_once()
