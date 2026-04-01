from __future__ import annotations

import unittest

from tools import listen_build_queue


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
