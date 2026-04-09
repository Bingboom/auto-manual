from __future__ import annotations

import json
import os
import unittest
from unittest import mock

from tools.dingtalk import auth


class _FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


class TestDingTalkAuth(unittest.TestCase):
    def test_get_app_only_token_should_read_env_and_return_token(self) -> None:
        with (
            mock.patch.dict(
                os.environ,
                {
                    "DINGTALK_CLIENT_ID": "client-id",
                    "DINGTALK_CLIENT_SECRET": "secret-value",
                    "DINGTALK_CORP_ID": "ding-corp",
                },
                clear=False,
            ),
            mock.patch.object(auth, "_curl_binary", return_value=None),
            mock.patch.object(
                auth.request,
                "urlopen",
                return_value=_FakeResponse({"access_token": "token-123", "expires_in": 7200}),
            ) as mocked_urlopen,
        ):
            token = auth.get_app_only_token(
                client_id_env="DINGTALK_CLIENT_ID",
                client_secret_env="DINGTALK_CLIENT_SECRET",
                corp_id_env="DINGTALK_CORP_ID",
            )

        self.assertEqual("token-123", token.access_token)
        self.assertEqual(7200, token.expires_in_seconds)
        request_arg = mocked_urlopen.call_args.args[0]
        self.assertEqual("https://api.dingtalk.com/v1.0/oauth2/ding-corp/token", request_arg.full_url)

    def test_get_app_only_token_should_raise_for_missing_env(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "Required DingTalk environment variable is not set: DINGTALK_CLIENT_ID"):
                auth.get_app_only_token(
                    client_id_env="DINGTALK_CLIENT_ID",
                    client_secret_env="DINGTALK_CLIENT_SECRET",
                    corp_id_env="DINGTALK_CORP_ID",
                )

    def test_get_app_only_token_should_raise_for_missing_access_token(self) -> None:
        with (
            mock.patch.dict(
                os.environ,
                {
                    "DINGTALK_CLIENT_ID": "client-id",
                    "DINGTALK_CLIENT_SECRET": "secret-value",
                    "DINGTALK_CORP_ID": "ding-corp",
                },
                clear=False,
            ),
            mock.patch.object(auth, "_curl_binary", return_value=None),
            mock.patch.object(
                auth.request,
                "urlopen",
                return_value=_FakeResponse({"expires_in": 7200}),
            ),
        ):
            with self.assertRaisesRegex(RuntimeError, "missing access_token"):
                auth.get_app_only_token(
                    client_id_env="DINGTALK_CLIENT_ID",
                    client_secret_env="DINGTALK_CLIENT_SECRET",
                    corp_id_env="DINGTALK_CORP_ID",
                )

    def test_request_app_only_token_response_should_use_curl_for_default_endpoint(self) -> None:
        with mock.patch.object(auth, "_curl_json_request", return_value={"access_token": "token-123", "expires_in": 7200}) as mocked_curl:
            response = auth.request_app_only_token_response(
                client_id="client-id",
                client_secret="secret-value",
                corp_id="ding-corp",
            )

        self.assertEqual("token-123", response["access_token"])
        mocked_curl.assert_called_once()
