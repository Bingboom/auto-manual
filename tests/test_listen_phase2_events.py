from __future__ import annotations

import unittest

from tools import listen_phase2_events


class TestListenPhase2Events(unittest.TestCase):
    def test_listen_phase2_events_uses_union_of_sync_and_queue_base_tokens(self) -> None:
        sync_tables_value = (
            type("Watched", (), {"logical_name": "spec_master", "base_token": "base_sync", "table_id": "tbl_sync"})(),
        )
        queue_binding = type(
            "Binding",
            (),
            {"base_token": "base_queue", "table_id": "tbl_queue"},
        )()
        subscribed: list[str] = []

        def fake_subscribe(*, cli_bin: str, base_token: str) -> None:
            self.assertEqual("lark-cli", cli_bin)
            subscribed.append(base_token)

        with unittest.mock.patch.object(
            listen_phase2_events,
            "collect_sync_preflight_errors",
            return_value=[],
        ), unittest.mock.patch.object(
            listen_phase2_events,
            "collect_queue_preflight_errors",
            return_value=[],
        ), unittest.mock.patch.object(
            listen_phase2_events,
            "_cli_bin",
            return_value="lark-cli",
        ), unittest.mock.patch.object(
            listen_phase2_events,
            "resolve_watched_tables",
            return_value=sync_tables_value,
        ), unittest.mock.patch.object(
            listen_phase2_events,
            "resolve_document_link_binding",
            return_value=queue_binding,
        ), unittest.mock.patch.object(
            listen_phase2_events,
            "fetch_field_id_map",
            return_value={listen_phase2_events.IMMEDIATE_TRIGGER_FIELD: "fld_immediate"},
        ), unittest.mock.patch.object(
            listen_phase2_events,
            "ensure_drive_event_subscription",
            side_effect=fake_subscribe,
        ), unittest.mock.patch.object(
            listen_phase2_events,
            "build_event_subscribe_command",
            return_value=["python", "-c", "pass"],
        ), unittest.mock.patch.object(
            listen_phase2_events.subprocess,
            "Popen",
        ) as popen_mock:
            process = unittest.mock.Mock()
            process.stdout = iter(())
            process.stderr = iter(())
            process.poll.return_value = 0
            process.returncode = 0
            popen_mock.return_value = process

            exit_code = listen_phase2_events.listen_phase2_events(
                cfg={},
                config_path=listen_phase2_events.ROOT / "config.yaml",
                data_root="data/phase2",
                table_names=["spec_master"],
            )

        self.assertEqual(0, exit_code)
        self.assertEqual({"base_sync", "base_queue"}, set(subscribed))


if __name__ == "__main__":
    unittest.main()
