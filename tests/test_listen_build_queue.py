from __future__ import annotations

import unittest

from tools import listen_build_queue
from tools import listen_build_queue_lark


class TestListenBuildQueue(unittest.TestCase):
    def test_build_event_subscribe_command_should_use_user_identity(self) -> None:
        with unittest.mock.patch.object(
            listen_build_queue,
            "_resolved_cli_command_parts",
            return_value=["lark-cli"],
        ):
            cmd = listen_build_queue.build_event_subscribe_command(cli_bin="lark-cli")

        self.assertEqual(["lark-cli", "event", "+subscribe"], cmd[:3])
        self.assertIn("--as", cmd)
        self.assertIn("user", cmd)
        self.assertIn(listen_build_queue.EVENT_TYPE, cmd)

    def test_fetch_field_id_map_should_use_user_identity(self) -> None:
        with unittest.mock.patch.object(
            listen_build_queue,
            "_fetch_field_id_map_impl",
            return_value={"是否立即构建": "fld_immediate"},
        ) as fetch_impl:
            resolved = listen_build_queue.fetch_field_id_map(
                cli_bin="lark-cli",
                base_token="base_123",
                table_id="tbl_123",
            )

        self.assertEqual({"是否立即构建": "fld_immediate"}, resolved)
        self.assertEqual("user", fetch_impl.call_args.kwargs["identity"])

    def test_fetch_field_id_map_should_page_until_html_link_is_found(self) -> None:
        payloads = [
            {
                "data": {
                    "total": 501,
                    "items": [{"field_id": "fld_doc", "field_name": "Document link"}],
                }
            },
            {
                "data": {
                    "total": 501,
                    "items": [{"field_id": "fld_html", "field_name": "HTML_link"}],
                }
            },
        ]

        def run_lark_cli_json(*, cli_bin: str, args: list[str]) -> dict[str, object]:
            self.assertEqual("lark-cli", cli_bin)
            index = int(args[args.index("--offset") + 1]) // 500
            return payloads[index]

        resolved = listen_build_queue_lark.fetch_field_id_map(
            cli_bin="lark-cli",
            base_token="base_123",
            table_id="tbl_123",
            identity="bot",
            run_lark_cli_json=run_lark_cli_json,
        )

        self.assertEqual(
            {
                "Document link": "fld_doc",
                "HTML_link": "fld_html",
            },
            resolved,
        )

    def test_event_field_value_truthy_should_accept_checkbox_shapes(self) -> None:
        self.assertTrue(listen_build_queue._event_field_value_truthy(True))
        self.assertTrue(listen_build_queue._event_field_value_truthy("true"))
        self.assertTrue(listen_build_queue._event_field_value_truthy("1"))
        self.assertFalse(listen_build_queue._event_field_value_truthy(False))
        self.assertFalse(listen_build_queue._event_field_value_truthy("false"))

    def test_event_requests_immediate_build_should_match_checkbox_edit(self) -> None:
        payload = {
            "header": {
                "event_id": "evt_1",
                "event_type": listen_build_queue.EVENT_TYPE,
            },
            "event": {
                "file_token": "app_token",
                "file_type": "bitable",
                "table_id": "tbl_document_link",
                "action_list": [
                    {
                        "action": "record_edited",
                        "record_id": "rec_1",
                        "after_value": [
                            {
                                "field_id": "fld_immediate",
                                "field_value": "true",
                            }
                        ],
                    }
                ],
            },
        }

        matched = listen_build_queue.event_requests_immediate_build(
            payload,
            base_token="app_token",
            table_id="tbl_document_link",
            immediate_field_id="fld_immediate",
        )

        self.assertTrue(matched)

    def test_event_requests_immediate_build_should_ignore_other_table(self) -> None:
        payload = {
            "header": {
                "event_id": "evt_2",
                "event_type": listen_build_queue.EVENT_TYPE,
            },
            "event": {
                "file_token": "app_token",
                "file_type": "bitable",
                "table_id": "tbl_other",
                "action_list": [
                    {
                        "action": "record_edited",
                        "record_id": "rec_1",
                        "after_value": [
                            {
                                "field_id": "fld_immediate",
                                "field_value": "true",
                            }
                        ],
                    }
                ],
            },
        }

        matched = listen_build_queue.event_requests_immediate_build(
            payload,
            base_token="app_token",
            table_id="tbl_document_link",
            immediate_field_id="fld_immediate",
        )

        self.assertFalse(matched)


if __name__ == "__main__":
    unittest.main()
