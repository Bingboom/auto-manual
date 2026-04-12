from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from unittest import mock

from tools import process_build_queue
from tools.dingtalk_control_config import (
    DingTalkControlConfig,
    read_dingtalk_control_config,
    run_dingtalk_control_config,
    update_dingtalk_control_config,
)


class _FakeSource:
    def __init__(self, raw_records: list[dict[str, object]]) -> None:
        self.raw_records = raw_records
        self.upserts: list[dict[str, object]] = []

    def fetch_records_with_ids(self, **_: object) -> list[dict[str, object]]:
        return self.raw_records

    def upsert_record(self, **kwargs: object) -> dict[str, object]:
        self.upserts.append(kwargs)
        return {"ok": True}


class TestDingTalkControlConfig(unittest.TestCase):
    def test_read_dingtalk_control_config_should_parse_single_visible_row(self) -> None:
        cfg = {
            "sync": {
                "phase2": {
                    "base_token_env": "BASE_TOKEN",
                    "dingtalk_control": {
                        "table_id_env": "DINGTALK_CONTROL_TABLE",
                        "view_id_env": "DINGTALK_CONTROL_VIEW",
                    },
                },
            },
        }
        source = _FakeSource(
            [
                {
                    "record_id": "rec_control_1",
                    "fields": {
                        "operator_union_id": "union-123",
                        "default_target_node_url": "https://alidocs.dingtalk.com/i/nodes/node-123?utm_scene=team_space",
                    },
                }
            ]
        )

        result = read_dingtalk_control_config(
            cfg=cfg,
            cli_bin_override="lark-cli",
            identity="user",
            environ={
                "BASE_TOKEN": "app_token",
                "DINGTALK_CONTROL_TABLE": "tbl_control",
                "DINGTALK_CONTROL_VIEW": "vew_control",
            },
            source=source,
        )

        self.assertEqual("rec_control_1", result.record_id)
        self.assertEqual("union-123", result.operator_union_id)
        self.assertEqual("node-123", result.default_target_node_id)

    def test_read_dingtalk_control_config_should_reject_ambiguous_rows_without_record_id(self) -> None:
        cfg = {
            "sync": {
                "phase2": {
                    "base_token_env": "BASE_TOKEN",
                    "dingtalk_control": {
                        "table_id_env": "DINGTALK_CONTROL_TABLE",
                    },
                },
            },
        }
        source = _FakeSource(
            [
                {"record_id": "rec_control_1", "fields": {}},
                {"record_id": "rec_control_2", "fields": {}},
            ]
        )

        with self.assertRaisesRegex(RuntimeError, "ambiguous"):
            read_dingtalk_control_config(
                cfg=cfg,
                cli_bin_override="lark-cli",
                identity="user",
                environ={
                    "BASE_TOKEN": "app_token",
                    "DINGTALK_CONTROL_TABLE": "tbl_control",
                },
                source=source,
            )

    def test_update_dingtalk_control_config_should_merge_existing_row_and_upsert(self) -> None:
        cfg = {
            "sync": {
                "phase2": {
                    "base_token_env": "BASE_TOKEN",
                    "dingtalk_control": {
                        "table_id_env": "DINGTALK_CONTROL_TABLE",
                    },
                },
            },
        }
        source = _FakeSource(
            [
                {
                    "record_id": "rec_control_1",
                    "fields": {
                        "operator_union_id": "union-old",
                        "default_target_node_url": "https://alidocs.dingtalk.com/i/nodes/node-old",
                    },
                }
            ]
        )

        result = update_dingtalk_control_config(
            cfg=cfg,
            operator_union_id="union-new",
            default_target_node_url=None,
            cli_bin_override="lark-cli",
            identity="user",
            environ={
                "BASE_TOKEN": "app_token",
                "DINGTALK_CONTROL_TABLE": "tbl_control",
            },
            source=source,
        )

        self.assertEqual("union-new", result.operator_union_id)
        self.assertEqual("https://alidocs.dingtalk.com/i/nodes/node-old", result.default_target_node_url)
        self.assertEqual(1, len(source.upserts))
        self.assertEqual("rec_control_1", source.upserts[0]["record_id"])
        self.assertEqual("union-new", source.upserts[0]["record"]["operator_union_id"])

    def test_run_dingtalk_control_config_should_emit_json_for_dry_run_update(self) -> None:
        stdout = io.StringIO()
        args = type(
            "Args",
            (),
            {
                "operator_union_id": "union-123",
                "target_node_url": "https://alidocs.dingtalk.com/i/nodes/node-123",
                "record_id": "rec_control_1",
                "dry_run": True,
                "json": True,
            },
        )()

        with (
            redirect_stdout(stdout),
            mock.patch(
                "tools.dingtalk_control_config.load_config",
                return_value={"sync": {"phase2": {"dingtalk_control": {}}}},
            ),
            mock.patch(
                "tools.dingtalk_control_config.update_dingtalk_control_config",
                return_value=DingTalkControlConfig(
                    record_id="rec_control_1",
                    operator_union_id="union-123",
                    default_target_node_url="https://alidocs.dingtalk.com/i/nodes/node-123",
                    default_target_node_id="node-123",
                ),
            ),
        ):
            run_dingtalk_control_config(args, config_path=process_build_queue.ROOT / "config.us.yaml")

        payload = json.loads(stdout.getvalue())
        self.assertEqual("dry-run-update", payload["mode"])
        self.assertEqual("node-123", payload["default_target_node_id"])

    def test_resolve_artifact_destination_should_prefer_feishu_control_config_for_dingtalk_openapi(self) -> None:
        cfg = {
            "queue": {
                "artifact_sink": {
                    "provider": "dingtalk_openapi",
                },
            },
        }
        binding = process_build_queue.DocumentLinkBinding(
            base_token_env="BASE_TOKEN",
            table_id_env="DOCUMENT_LINK_TABLE",
            view_id_env="DOCUMENT_LINK_VIEW",
            wiki_parent_token_env=None,
            base_token="app_token",
            table_id="tbl_document_link",
            view_id="vew_document_link",
            wiki_parent_token=None,
        )

        with (
            mock.patch.object(process_build_queue, "artifact_sink_provider", return_value="dingtalk_openapi"),
            mock.patch.object(
                process_build_queue,
                "read_dingtalk_control_config",
                return_value=DingTalkControlConfig(
                    record_id="rec_control_1",
                    operator_union_id="union-123",
                    default_target_node_url="https://alidocs.dingtalk.com/i/nodes/control-node",
                    default_target_node_id="control-node",
                ),
            ),
        ):
            destination = process_build_queue.resolve_artifact_destination(
                cfg=cfg,
                cli_bin="lark-cli",
                identity="user",
                binding=binding,
            )

        self.assertEqual("dingtalk_openapi", destination.provider)
        self.assertEqual("union-123", destination.details["operator_union_id"])
        self.assertEqual("https://alidocs.dingtalk.com/i/nodes/control-node", destination.details["target_node_url"])


if __name__ == "__main__":
    unittest.main()
