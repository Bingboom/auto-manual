from __future__ import annotations

import unittest

from tools import listen_sync_data


class TestListenSyncData(unittest.TestCase):
    def test_resolve_watched_tables_should_follow_phase2_source_bindings(self) -> None:
        cfg = {"sync": {"phase2": {"tables": {}}}}

        def fake_binding(_: dict[str, object], logical_name: str) -> object:
            if logical_name == "spec_titles":
                return type(
                    "Binding",
                    (),
                    {"base_token": "app_token", "table_id": "tbl_spec_titles"},
                )()
            return type(
                "Binding",
                (),
                {"base_token": "app_token", "table_id": "tbl_spec_master"},
            )()

        with unittest.mock.patch.object(
            listen_sync_data,
            "resolve_table_binding",
            side_effect=fake_binding,
        ):
            watched = listen_sync_data.resolve_watched_tables(
                cfg,
                table_names=["spec_master", "spec_titles"],
            )

        self.assertEqual(
            (
                listen_sync_data.WatchedTable(
                    logical_name="spec_titles",
                    base_token="app_token",
                    table_id="tbl_spec_titles",
                ),
                listen_sync_data.WatchedTable(
                    logical_name="spec_master",
                    base_token="app_token",
                    table_id="tbl_spec_master",
                ),
            ),
            watched,
        )

    def test_event_requests_sync_should_match_source_table_edit(self) -> None:
        payload = {
            "header": {
                "event_id": "evt_1",
                "event_type": listen_sync_data.EVENT_TYPE,
            },
            "event": {
                "file_token": "app_token",
                "file_type": "bitable",
                "table_id": "tbl_spec_master",
                "action_list": [
                    {
                        "action": "record_edited",
                        "record_id": "rec_1",
                        "after_value": [],
                    }
                ],
            },
        }

        matched = listen_sync_data.event_requests_sync(
            payload,
            watched_tables_by_base={
                "app_token": {
                    "tbl_spec_master": "spec_master",
                    "tbl_spec_titles": "spec_titles",
                }
            },
        )

        self.assertEqual("spec_master", matched)

    def test_event_requests_sync_should_ignore_unwatched_table(self) -> None:
        payload = {
            "header": {
                "event_id": "evt_2",
                "event_type": listen_sync_data.EVENT_TYPE,
            },
            "event": {
                "file_token": "app_token",
                "file_type": "bitable",
                "table_id": "tbl_document_link",
                "action_list": [
                    {
                        "action": "record_edited",
                        "record_id": "rec_1",
                        "after_value": [],
                    }
                ],
            },
        }

        matched = listen_sync_data.event_requests_sync(
            payload,
            watched_tables_by_base={
                "app_token": {
                    "tbl_spec_master": "spec_master",
                }
            },
        )

        self.assertIsNone(matched)


if __name__ == "__main__":
    unittest.main()
