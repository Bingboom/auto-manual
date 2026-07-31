"""Capability mirror sync: build-table records -> tracked CSV."""
from __future__ import annotations

import csv
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.sync_model_capabilities import (  # noqa: E402
    CAPABILITY_FIELDS,
    capabilities_csv_text,
    load_capability_fields,
    sync_capability_mirror,
)


def _record(key: str, project: str = "HTE153", **caps) -> dict:
    fields = {
        "Document_key": [{"text": key, "type": "text"}],
        "项目代码": [{"text": project, "type": "text"}],
    }
    fields.update(caps)
    return {"fields": fields}


class CapabilitiesCsvTests(unittest.TestCase):
    def test_capability_fields_follow_rules_csv(self) -> None:
        self.assertEqual(
            CAPABILITY_FIELDS,
            load_capability_fields(ROOT / "data"),
        )
        with (ROOT / "data" / "model_capabilities.csv").open(encoding="utf-8") as handle:
            self.assertEqual(tuple(next(csv.reader(handle))[2:]), CAPABILITY_FIELDS)

    def test_custom_capability_fields_drive_header_and_rows(self) -> None:
        text = capabilities_csv_text(
            [_record("JE-1000F_US", **{"新能力": True})],
            capability_fields=("新能力",),
        )
        self.assertEqual(text.splitlines()[0], "Document_key,Project,新能力")
        self.assertEqual(text.splitlines()[1], "JE-1000F_US,HTE153,TRUE")

    def test_booleans_and_sorting_are_deterministic(self) -> None:
        text = capabilities_csv_text([
            _record("JE-2000F_US", "HTE154", **{"UPS功能": True, "LED照明灯": False}),
            _record("JE-1000F_US", **{"UPS功能": True}),
        ])
        lines = text.strip().splitlines()
        self.assertEqual(lines[0].split(",")[:2], ["Document_key", "Project"])
        self.assertTrue(lines[1].startswith("JE-1000F_US,HTE153,"))
        self.assertTrue(lines[2].startswith("JE-2000F_US,HTE154,"))
        self.assertIn("TRUE", lines[1])

    def test_pending_model_and_uninventoried_rows_are_skipped(self) -> None:
        text = capabilities_csv_text([
            _record("_US", "HTE157", **{"UPS功能": True}),   # model link pending
            _record("JE-900B_JP", "HTE2610"),                # no capability data
            _record("JE-1000F_US", **{"UPS功能": True}),
        ])
        lines = text.strip().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertIn("JE-1000F_US", lines[1])

    def test_duplicate_document_keys_collapse_to_one_row(self) -> None:
        text = capabilities_csv_text([
            _record("JE-2000F_CN", "HTE154", **{"UPS功能": True}),
            _record("JE-2000F_CN", "HTE154", **{"UPS功能": True}),
        ])
        self.assertEqual(len(text.strip().splitlines()), 2)

    def test_all_capability_columns_present(self) -> None:
        text = capabilities_csv_text([_record("JE-1000F_US", **{"UPS功能": True})])
        header = text.splitlines()[0].split(",")
        for name in CAPABILITY_FIELDS:
            self.assertIn(name, header)


class _Result:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class SyncMirrorTests(unittest.TestCase):
    def test_absent_config_block_is_a_noop(self) -> None:
        result, written = sync_capability_mirror(
            {"sync": {"phase2": {}}}, source=None, repo_root=Path("/x"),
            sha256_text=lambda t: "h", sha256_file=lambda p: "h",
            result_cls=_Result)
        self.assertIsNone(result)
        self.assertIsNone(written)

    def test_configured_but_missing_env_fails_loudly(self) -> None:
        cfg = {"sync": {"phase2": {
            "base_token_env": "MC_TEST_ABSENT_BASE",
            "model_capabilities": {"table_id_env": "MC_TEST_ABSENT_TABLE"},
        }}}
        with self.assertRaises(RuntimeError):
            sync_capability_mirror(
                cfg, source=None, repo_root=Path("/x"),
                sha256_text=lambda t: "h", sha256_file=lambda p: "h",
                result_cls=_Result)

    def test_error_names_only_the_missing_variable(self) -> None:
        # Naming both variables when only one was unset cost 17 days of red
        # cred-health-check: the reader chased the base token while the
        # table id was the actual gap.
        import os
        os.environ["MC_TEST_PRESENT_BASE"] = "tok"
        os.environ.pop("MC_TEST_ABSENT_TABLE", None)
        cfg = {"sync": {"phase2": {
            "base_token_env": "MC_TEST_PRESENT_BASE",
            "model_capabilities": {"table_id_env": "MC_TEST_ABSENT_TABLE"},
        }}}
        with self.assertRaises(RuntimeError) as ctx:
            sync_capability_mirror(
                cfg, source=None, repo_root=Path("/x"),
                sha256_text=lambda t: "h", sha256_file=lambda p: "h",
                result_cls=_Result)
        message = str(ctx.exception)
        self.assertIn("MC_TEST_ABSENT_TABLE is not set", message)
        self.assertNotIn("MC_TEST_PRESENT_BASE", message)

    def test_fetch_and_result_shape(self) -> None:
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            rules = (
                "capability,scope,page_stem,match_regex,required_when_true,"
                "forbidden_when_false,notes\n"
                "UPS功能,page,06_ups_mode,,Y,Y,\n"
            )
            (repo_root / "data").mkdir()
            (repo_root / "data" / "capability_page_rules.csv").write_text(
                rules, encoding="utf-8"
            )
            self._run_fetch(repo_root)

    def _run_fetch(self, repo_root: Path) -> None:
        import os
        os.environ["MC_TEST_BASE"] = "base_tok"
        os.environ["MC_TEST_TABLE"] = "tbl_x"
        cfg = {"sync": {"phase2": {
            "base_token_env": "MC_TEST_BASE",
            "model_capabilities": {"table_id_env": "MC_TEST_TABLE"},
        }}}

        class _Source:
            def fetch_records(self, *, base_token, table_id, view_id):
                assert base_token == "base_tok" and table_id == "tbl_x"
                return [_record("JE-1000F_US", **{"UPS功能": True})]

        result, written = sync_capability_mirror(
            cfg, source=_Source(), repo_root=repo_root,
            sha256_text=lambda t: "new", sha256_file=lambda p: "old",
            result_cls=_Result)
        self.assertEqual(result.logical_name, "model_capabilities")
        self.assertEqual(result.row_count, 1)
        self.assertTrue(result.changed)
        self.assertEqual(written[0], repo_root / "data/model_capabilities.csv")
        self.assertIn("JE-1000F_US", written[1])


if __name__ == "__main__":
    unittest.main()
