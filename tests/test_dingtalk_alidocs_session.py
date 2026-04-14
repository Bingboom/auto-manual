from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.dingtalk import alidocs_session


class TestAliDocsSession(unittest.TestCase):
    def test_load_session_config_for_operator_union_id_should_read_registry_file(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            session_path = Path(td) / "union_123.json"
            session_path.write_text(
                json.dumps(
                    {
                        "a_token": "token_123",
                        "xsrf_token": "xsrf_123",
                        "cookie": "cookie_123",
                        "bx_version": "9.9.9",
                    }
                ),
                encoding="utf-8",
            )

            session = alidocs_session.load_session_config_for_operator_union_id(
                operator_union_id="union_123",
                environ={"AUTO_MANUAL_DINGTALK_SESSION_ROOT": td},
            )

        self.assertEqual("token_123", session.a_token)
        self.assertEqual("xsrf_123", session.xsrf_token)
        self.assertEqual("cookie_123", session.cookie)
        self.assertEqual("9.9.9", session.bx_version)

    def test_load_session_config_for_operator_union_id_should_fallback_to_env(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            session = alidocs_session.load_session_config_for_operator_union_id(
                operator_union_id="union_missing",
                environ={
                    "AUTO_MANUAL_DINGTALK_SESSION_ROOT": td,
                    "DINGTALK_DOCS_A_TOKEN": "env_token",
                    "DINGTALK_DOCS_XSRF_TOKEN": "env_xsrf",
                    "DINGTALK_DOCS_COOKIE": "env_cookie",
                    "DINGTALK_DOCS_BX_V": "3.3.3",
                },
            )

        self.assertEqual("env_token", session.a_token)
        self.assertEqual("env_xsrf", session.xsrf_token)
        self.assertEqual("env_cookie", session.cookie)
        self.assertEqual("3.3.3", session.bx_version)


if __name__ == "__main__":
    unittest.main()
