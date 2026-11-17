from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path
from unittest import mock

from tools.data import sync_data
from tools.feishu_record_transport import (
    LarkRetryPolicy,
    SourceTableLarkTransport,
    TranslationMemoryLarkTransport,
)
from tools.translation_memory_sync import apply_translation_suggestions


class LarkCliSourceRetryTests(unittest.TestCase):
    def test_retries_nonzero_exit_429_and_succeeds(self) -> None:
        sleeps: list[float] = []
        calls = 0

        def fake_run(cmd: list[str], **_: object) -> mock.Mock:
            nonlocal calls
            calls += 1
            if calls == 1:
                raise subprocess.CalledProcessError(1, cmd, stderr="HTTP 429 Too Many Requests")
            if calls == 2:
                return mock.Mock(returncode=1, stdout="", stderr="rate limit exceeded")
            return mock.Mock(returncode=0, stdout=json.dumps({"code": 0, "data": {"ok": True}}), stderr="")

        source = sync_data.LarkCliSource(
            cli_bin="lark-cli",
            retry_policy=LarkRetryPolicy(max_retries=3, base_delay_seconds=1.5, max_delay_seconds=10.0),
            sleep=sleeps.append,
        )
        with mock.patch("tools.data.sync_data.subprocess.run", side_effect=fake_run):
            payload = source._run_base_command(args=["+record-get"])

        self.assertEqual({"code": 0, "data": {"ok": True}}, payload)
        self.assertEqual(3, calls)
        self.assertEqual([1.5, 3.0], sleeps)

    def test_retries_exit_zero_429_json_using_retry_after(self) -> None:
        sleeps: list[float] = []
        responses = [
            mock.Mock(returncode=0, stdout=json.dumps({"code": 429, "retry_after": 2}), stderr=""),
            mock.Mock(returncode=0, stdout=json.dumps({"code": 429}), stderr=""),
            mock.Mock(returncode=0, stdout=json.dumps({"code": 0, "data": {"ok": True}}), stderr=""),
        ]

        source = sync_data.LarkCliSource(
            cli_bin="lark-cli",
            retry_policy=LarkRetryPolicy(max_retries=3, base_delay_seconds=1.0, max_delay_seconds=10.0),
            sleep=sleeps.append,
        )
        with mock.patch("tools.data.sync_data.subprocess.run", side_effect=responses):
            payload = source._run_base_command(args=["+record-get"])

        self.assertEqual(0, payload["code"])
        self.assertEqual([2.0, 2.0], sleeps)

    def test_exhausted_429_retries_raise_runtime_error(self) -> None:
        sleeps: list[float] = []

        def fake_nonzero(cmd: list[str], **_: object) -> mock.Mock:
            raise subprocess.CalledProcessError(1, cmd, stderr="429 Too Many Requests")

        source = sync_data.LarkCliSource(
            cli_bin="lark-cli",
            retry_policy=LarkRetryPolicy(max_retries=2, base_delay_seconds=0.5, max_delay_seconds=5.0),
            sleep=sleeps.append,
        )
        with mock.patch("tools.data.sync_data.subprocess.run", side_effect=fake_nonzero):
            with self.assertRaisesRegex(RuntimeError, r"Lark CLI base command failed with exit code 1"):
                source._run_base_command(args=["+record-get"])
        self.assertEqual([0.5, 1.0], sleeps)

        sleeps.clear()
        rate_limited_json = [
            mock.Mock(returncode=0, stdout=json.dumps({"code": 429, "msg": "too many requests"}), stderr=""),
            mock.Mock(returncode=0, stdout=json.dumps({"code": 429, "msg": "too many requests"}), stderr=""),
            mock.Mock(returncode=0, stdout=json.dumps({"code": 429, "msg": "too many requests"}), stderr=""),
        ]
        with mock.patch("tools.data.sync_data.subprocess.run", side_effect=rate_limited_json):
            with self.assertRaisesRegex(RuntimeError, r"Lark CLI API request failed: too many requests"):
                source._run_base_command(args=["+record-get"])
        self.assertEqual([0.5, 1.0], sleeps)

    def test_non_429_error_does_not_retry(self) -> None:
        sleeps: list[float] = []

        def fake_fail(cmd: list[str], **_: object) -> mock.Mock:
            raise subprocess.CalledProcessError(2, cmd, stderr="invalid base token")

        source = sync_data.LarkCliSource(
            cli_bin="lark-cli",
            retry_policy=LarkRetryPolicy(max_retries=3, base_delay_seconds=1.0, max_delay_seconds=10.0),
            sleep=sleeps.append,
        )
        with mock.patch("tools.data.sync_data.subprocess.run", side_effect=fake_fail):
            with self.assertRaisesRegex(RuntimeError, r"exit code 2"):
                source._run_base_command(args=["+record-get"])
        self.assertEqual([], sleeps)


class LarkCliSourceFetchRecordByIdTests(unittest.TestCase):
    def test_rejects_empty_record_id(self) -> None:
        source = sync_data.LarkCliSource(cli_bin="lark-cli")
        with self.assertRaisesRegex(RuntimeError, "non-empty record id"):
            source.fetch_record_by_id(base_token="app1", table_id="tbl1", record_id="  ")

    def test_positional_array_with_field_id_mapping(self) -> None:
        source = sync_data.LarkCliSource(cli_bin="lark-cli", identity="bot")
        seen_commands: list[list[str]] = []
        responses = [
            mock.Mock(
                returncode=0,
                stdout=json.dumps(
                    {
                        "code": 0,
                        "data": {
                            "field_id_list": ["fld_long", "fld_short"],
                            "fields": ["Row_label_footnote_r...", "Value_en"],
                            "data": [["fn_1", "100 W"]],
                            "record_id_list": ["recABC"],
                        },
                    }
                ),
                stderr="",
            ),
            mock.Mock(
                returncode=0,
                stdout=json.dumps(
                    {
                        "code": 0,
                        "data": {
                            "items": [
                                {"field_id": "fld_long", "field_name": "Row_label_footnote_refs"},
                                {"field_id": "fld_short", "field_name": "Value_en"},
                            ],
                            "total": 2,
                        },
                    }
                ),
                stderr="",
            ),
        ]

        def fake_run(cmd: list[str], **_: object) -> mock.Mock:
            seen_commands.append(cmd)
            return responses.pop(0)

        with mock.patch("tools.data.sync_data.subprocess.run", side_effect=fake_run):
            record = source.fetch_record_by_id(base_token="app1", table_id="tbl1", record_id=" recABC ")

        self.assertEqual(
            {"record_id": "recABC", "fields": {"Row_label_footnote_refs": "fn_1", "Value_en": "100 W"}},
            record,
        )
        self.assertEqual("+record-get", seen_commands[0][2])
        self.assertIn("--record-id", seen_commands[0])
        self.assertEqual("recABC", seen_commands[0][seen_commands[0].index("--record-id") + 1])
        self.assertEqual("+field-list", seen_commands[1][2])

    def test_empty_data_rows_returns_none(self) -> None:
        source = sync_data.LarkCliSource(cli_bin="lark-cli")
        resp = mock.Mock(
            returncode=0,
            stdout=json.dumps({"code": 0, "data": {"fields": ["Value_en"], "data": []}}),
            stderr="",
        )
        with mock.patch("tools.data.sync_data.subprocess.run", return_value=resp):
            record = source.fetch_record_by_id(base_token="app1", table_id="tbl1", record_id="recMISSING")

        self.assertIsNone(record)

    def test_record_dict_envelope_fallback(self) -> None:
        source = sync_data.LarkCliSource(cli_bin="lark-cli")
        resp = mock.Mock(
            returncode=0,
            stdout=json.dumps(
                {
                    "code": 0,
                    "data": {"record": {"record_id": "recDICT", "fields": {"Value_en": "200 W"}}},
                }
            ),
            stderr="",
        )
        with mock.patch("tools.data.sync_data.subprocess.run", return_value=resp):
            record = source.fetch_record_by_id(base_token="app1", table_id="tbl1", record_id="recDICT")

        self.assertEqual({"record_id": "recDICT", "fields": {"Value_en": "200 W"}}, record)

    def test_retries_record_get_without_format_flag_for_old_cli(self) -> None:
        source = sync_data.LarkCliSource(cli_bin="lark-cli")
        seen_commands: list[list[str]] = []

        def fake_run(cmd: list[str], **_: object) -> mock.Mock:
            seen_commands.append(cmd)
            if "--format" in cmd:
                raise subprocess.CalledProcessError(1, cmd, stderr="Error: unknown flag: --format")
            return mock.Mock(
                returncode=0,
                stdout=json.dumps({"code": 0, "data": {"fields": ["Value_en"], "data": [["300 W"]]}}),
                stderr="",
            )

        with mock.patch("tools.data.sync_data.subprocess.run", side_effect=fake_run):
            record = source.fetch_record_by_id(base_token="app1", table_id="tbl1", record_id="recOLD")

        self.assertEqual({"record_id": "recOLD", "fields": {"Value_en": "300 W"}}, record)
        self.assertEqual(2, len(seen_commands))
        self.assertIn("--format", seen_commands[0])
        self.assertNotIn("--format", seen_commands[1])


class TransportGetO1Tests(unittest.TestCase):
    def test_source_table_transport_get_uses_fetch_record_by_id_without_full_scan(self) -> None:
        class _O1Source:
            def __init__(self) -> None:
                self.single_calls: list[tuple[str, str, str]] = []
                self.scan_calls = 0

            def upsert_record(self, *, base_token: str, table_id: str, record_id: str, record: dict) -> dict:
                return {"ok": True}

            def fetch_records_with_ids(self, *, base_token: str, table_id: str, view_id: str | None) -> list[dict]:
                self.scan_calls += 1
                return []

            def create_record(self, *, base_token: str, table_id: str, fields: dict) -> str:
                return "recNEW"

            def fetch_record_by_id(self, *, base_token: str, table_id: str, record_id: str) -> dict | None:
                self.single_calls.append((base_token, table_id, record_id))
                if record_id == "rec1":
                    return {"record_id": "rec1", "fields": {"Value_uk": "DC 12 B"}}
                return None

        source = _O1Source()
        transport = SourceTableLarkTransport(source=source, binding_for=lambda tbl: ("BASE", f"tbl_{tbl}"))

        self.assertEqual("DC 12 B", transport.get(table="Spec_Master", record_id="rec1", field="Value_uk"))
        self.assertIsNone(transport.get(table="Spec_Master", record_id="recMISSING", field="Value_uk"))
        self.assertEqual(0, source.scan_calls)
        self.assertEqual(
            [("BASE", "tbl_Spec_Master", "rec1"), ("BASE", "tbl_Spec_Master", "recMISSING")],
            source.single_calls,
        )

    def test_tm_transport_get_uses_fetch_record_by_id_and_falls_back_when_absent(self) -> None:
        class _O1Source:
            def __init__(self) -> None:
                self.single_calls: list[str] = []
                self.scan_calls = 0

            def upsert_record(self, *, base_token: str, table_id: str, record_id: str, record: dict) -> dict:
                return {"ok": True}

            def fetch_records_with_ids(self, *, base_token: str, table_id: str, view_id: str | None) -> list[dict]:
                self.scan_calls += 1
                return []

            def create_record(self, *, base_token: str, table_id: str, fields: dict) -> str:
                return "recNEW"

            def fetch_record_by_id(self, *, base_token: str, table_id: str, record_id: str) -> dict | None:
                self.single_calls.append(record_id)
                return {"record_id": record_id, "fields": {"it": "Nuovo"}}

        o1_source = _O1Source()
        o1_transport = TranslationMemoryLarkTransport(source=o1_source, base_token="BASE", table_id="tbl_tm")
        self.assertEqual("Nuovo", o1_transport.get(record_id="recTM1", field="it"))
        self.assertEqual(0, o1_source.scan_calls)
        self.assertEqual(["recTM1"], o1_source.single_calls)

        class _LegacySource:
            def __init__(self) -> None:
                self.scan_calls = 0

            def upsert_record(self, *, base_token: str, table_id: str, record_id: str, record: dict) -> dict:
                return {"ok": True}

            def fetch_records_with_ids(self, *, base_token: str, table_id: str, view_id: str | None) -> list[dict]:
                self.scan_calls += 1
                return [{"record_id": "recTM2", "fields": {"it": "Legacy"}}]

            def create_record(self, *, base_token: str, table_id: str, fields: dict) -> str:
                return "recNEW"

        legacy_source = _LegacySource()
        legacy_transport = TranslationMemoryLarkTransport(source=legacy_source, base_token="BASE", table_id="tbl_tm")
        self.assertEqual("Legacy", legacy_transport.get(record_id="recTM2", field="it"))
        self.assertEqual(1, legacy_source.scan_calls)

    def test_end_to_end_apply_translation_suggestions_uses_single_scan_plus_2k_gets(self) -> None:
        source = sync_data.LarkCliSource(cli_bin="lark-cli", identity="bot")
        transport = TranslationMemoryLarkTransport(source=source, base_token="BASE", table_id="tbl_tm")

        store = {
            "rec1": {"en": "Old 1", "it": "Vecchio 1"},
            "rec2": {"en": "Old 2", "it": "Vecchio 2"},
            "rec3": {"en": "Old 3", "it": "Vecchio 3"},
        }
        command_counts = {"+field-list": 0, "+record-list": 0, "+record-get": 0, "+record-upsert": 0}

        def fake_run(cmd: list[str], **_: object) -> mock.Mock:
            subcmd = cmd[2]
            command_counts[subcmd] += 1
            if subcmd == "+field-list":
                return mock.Mock(
                    returncode=0,
                    stdout=json.dumps(
                        {
                            "code": 0,
                            "data": {
                                "items": [
                                    {"field_id": "fld_en", "field_name": "en"},
                                    {"field_id": "fld_it", "field_name": "it"},
                                ],
                                "total": 2,
                            },
                        }
                    ),
                    stderr="",
                )
            if subcmd == "+record-list":
                rows = [[store[rid]["en"], store[rid]["it"]] for rid in ("rec1", "rec2", "rec3")]
                return mock.Mock(
                    returncode=0,
                    stdout=json.dumps(
                        {
                            "code": 0,
                            "data": {
                                "field_id_list": ["fld_en", "fld_it"],
                                "fields": ["en", "it"],
                                "data": rows,
                                "record_id_list": ["rec1", "rec2", "rec3"],
                                "has_more": False,
                            },
                        }
                    ),
                    stderr="",
                )
            if subcmd == "+record-get":
                rec_id = cmd[cmd.index("--record-id") + 1]
                row = store[rec_id]
                return mock.Mock(
                    returncode=0,
                    stdout=json.dumps(
                        {
                            "code": 0,
                            "data": {
                                "field_id_list": ["fld_en", "fld_it"],
                                "fields": ["en", "it"],
                                "data": [[row["en"], row["it"]]],
                                "record_id_list": [rec_id],
                            },
                        }
                    ),
                    stderr="",
                )
            if subcmd == "+record-upsert":
                rec_id = cmd[cmd.index("--record-id") + 1]
                payload_arg = cmd[cmd.index("--json") + 1]
                payload_path = Path(sync_data.ROOT / payload_arg[1:])
                patch_fields = json.loads(payload_path.read_text(encoding="utf-8"))
                store[rec_id].update(patch_fields)
                return mock.Mock(returncode=0, stdout=json.dumps({"code": 0, "ok": True}), stderr="")
            raise AssertionError(f"Unexpected command: {cmd}")

        suggestions = [
            {
                "delta_hash": f"h{idx}",
                "copy_key": f"k{idx}",
                "lang": "it",
                "source_lang": "en",
                "old_text": f"Vecchio {idx}",
                "new_text": f"Nuovo {idx}",
                "routing_hint": "translation_memory",
            }
            for idx in (1, 2, 3)
        ]

        with mock.patch("tools.data.sync_data.subprocess.run", side_effect=fake_run):
            report = apply_translation_suggestions(
                suggestions,
                approved_hashes={"h1", "h2", "h3"},
                transport=transport,
                write=True,
            )

        self.assertEqual(3, report["summary"]["written"])
        self.assertEqual(
            {
                "+field-list": 1,
                "+record-list": 1,
                "+record-get": 6,
                "+record-upsert": 3,
            },
            command_counts,
        )
        self.assertEqual("Nuovo 1", store["rec1"]["it"])
        self.assertEqual("Nuovo 2", store["rec2"]["it"])
        self.assertEqual("Nuovo 3", store["rec3"]["it"])


if __name__ == "__main__":
    unittest.main()
