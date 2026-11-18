from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.data import sync_data
from tools.data.sync_table_labels import (
    UNLABELLED_TABLE,
    LarkCliReadError,
    labelled_lark_failure,
    table_labels_from_cfg,
)
from tools.utils.redaction import REDACTED, redact_identifiers

# Synthetic, identifier-shaped values; none of them is a real binding.
BASE_TOKEN = "Zq7kP2mXw9LrT4vBn8YcD3sFh6J"
TM_TABLE_ID = "tblQw3Er5Ty7Ui9Op"
TM_VIEW_ID = "vewAs4Df6G"
ASSET_TABLE_ID = "tblZx1Cv3Bn5Mm7Kk"


def _cfg() -> dict:
    return {
        "sync": {
            "phase2": {
                "base_token_env": "T_BASE",
                "spec_master_sources": {"spec_rows_source_table_id_env": "T_SPEC_ROWS"},
                "tables": {
                    "spec_master": {},
                    "translation_memory": {
                        "base_token_env": "T_TM_BASE",
                        "table_id_env": "T_TM_TABLE",
                        "view_id_env": "T_TM_VIEW",
                    },
                },
                "model_capabilities": {"table_id_env": "T_CAPS"},
                "asset_registry": {"table_id_env": "T_UNSET"},
            }
        }
    }


def _repo_with_bindings(root: Path) -> Path:
    (root / "data").mkdir(parents=True)
    (root / "data" / "asset_base_bindings.json").write_text(
        json.dumps({"base": {"base_token": BASE_TOKEN}, "tables": {"asset_definitions": {"table_id": ASSET_TABLE_ID}}}),
        encoding="utf-8",
    )
    return root


class TestTableLabels(unittest.TestCase):
    def test_labels_come_from_config_paths_and_frozen_bindings(self) -> None:
        env = {"T_TM_TABLE": TM_TABLE_ID, "T_SPEC_ROWS": "tblSpecRows000001", "T_CAPS": "tblCaps0000000001"}
        with tempfile.TemporaryDirectory() as tmp:
            labels = table_labels_from_cfg(_cfg(), repo_root=_repo_with_bindings(Path(tmp)), environ=env)
        self.assertEqual("translation_memory", labels[TM_TABLE_ID])
        self.assertEqual("spec_master_sources.spec_rows_source", labels["tblSpecRows000001"])
        self.assertEqual("model_capabilities", labels["tblCaps0000000001"])
        self.assertEqual("asset_definitions", labels[ASSET_TABLE_ID])
        self.assertEqual(4, len(labels))  # unset env bindings are skipped

    def test_missing_bindings_file_is_not_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            labels = table_labels_from_cfg(_cfg(), repo_root=Path(tmp), environ={})
        self.assertEqual({}, labels)

    def test_labelled_failure_redacts_every_coordinate(self) -> None:
        args = ["+record-list", "--base-token", BASE_TOKEN, "--table-id", TM_TABLE_ID, "--view-id", TM_VIEW_ID]
        message = labelled_lark_failure(
            args,
            f"failed for {BASE_TOKEN}/{TM_TABLE_ID}?view={TM_VIEW_ID}",
            {TM_TABLE_ID: "translation_memory"},
        )
        self.assertTrue(message.startswith("[table: translation_memory] "))
        for value in (BASE_TOKEN, TM_TABLE_ID, TM_VIEW_ID):
            self.assertNotIn(value, message)

    def test_unknown_table_id_is_labelled_without_the_id(self) -> None:
        message = labelled_lark_failure(["--table-id", "tblUnknown12345"], "boom", {})
        self.assertEqual(f"[table: {UNLABELLED_TABLE}] boom", message)


class TestLarkCliSourceFailureLabel(unittest.TestCase):
    def _fail_with(self, stdout: str) -> str:
        source = sync_data.LarkCliSource(cli_bin="lark-cli", table_labels={TM_TABLE_ID: "translation_memory"})

        def fake_run(*_: object, **__: object) -> mock.Mock:
            raise subprocess.CalledProcessError(1, ["lark-cli"], output=stdout, stderr="")

        with mock.patch("tools.data.sync_data.subprocess.run", side_effect=fake_run):
            with self.assertRaises(LarkCliReadError) as ctx:
                source.fetch_records(base_token=BASE_TOKEN, table_id=TM_TABLE_ID, view_id=TM_VIEW_ID)
        self.assertIsInstance(ctx.exception, RuntimeError)
        self.assertIsNone(ctx.exception.__cause__)
        return str(ctx.exception)

    def test_permission_error_names_logical_table_and_no_ids(self) -> None:
        stdout = json.dumps(
            {
                "ok": False,
                "error": {
                    "code": 91403,
                    "message": "you don't have permission",
                    "detail": {"base_token": BASE_TOKEN, "table_id": TM_TABLE_ID, "view_id": TM_VIEW_ID},
                },
            },
            indent=2,
        )
        message = self._fail_with(stdout)
        self.assertTrue(message.startswith("[table: translation_memory] "))
        self.assertIn("91403", message)
        self.assertIn("you don't have permission", message)
        for value in (BASE_TOKEN, TM_TABLE_ID, TM_VIEW_ID):
            self.assertNotIn(value, message)

    def test_sync_data_main_prints_the_label(self) -> None:
        def failing_snapshot(**_: object) -> None:
            source = sync_data.LarkCliSource(cli_bin="lark-cli", table_labels={TM_TABLE_ID: "translation_memory"})
            with mock.patch(
                "tools.data.sync_data.subprocess.run",
                side_effect=subprocess.CalledProcessError(1, ["lark-cli"], output='{"code": 91403}', stderr=""),
            ):
                source.fetch_records(base_token=BASE_TOKEN, table_id=TM_TABLE_ID, view_id=None)

        with mock.patch.object(sync_data, "sync_phase2_snapshot", side_effect=failing_snapshot), mock.patch.object(
            sync_data, "load_config", return_value={}
        ), mock.patch("sys.stderr") as stderr:
            code = sync_data.main(["--config", "configs/config.us.yaml", "--dry-run"])
        printed = "".join(call.args[0] for call in stderr.write.call_args_list)
        self.assertEqual(1, code)
        self.assertIn("[table: translation_memory]", printed)
        self.assertNotIn(TM_TABLE_ID, printed)
        self.assertNotIn(BASE_TOKEN, printed)


class TestRedaction(unittest.TestCase):
    def test_redacts_urls_tokens_and_feishu_ids(self) -> None:
        text = (
            "see https://user:pw@open.feishu.cn/x?token=abc, access_token=sk-123 Bearer abc.def "
            f"rec7Hk2LmNp tblAbC123xyz {BASE_TOKEN} log_id 20261117164640ABCDEF0123456789"
        )
        result = redact_identifiers(text)
        for leaked in ("open.feishu.cn", "sk-123", "abc.def", "rec7Hk2LmNp", "tblAbC123xyz", BASE_TOKEN, "ABCDEF0123"):
            self.assertNotIn(leaked, result)
        self.assertIn(REDACTED, result)

    def test_keeps_ordinary_words(self) -> None:
        text = "you don't have permission to read records in this table view"
        self.assertEqual(text, redact_identifiers(text))


if __name__ == "__main__":
    unittest.main()
