#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Asset-registry mirror: the Base owns build facts, the repo owns files."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.sync_asset_registry import (  # noqa: E402
    definition_rows,
    merge_registry_csv,
    sync_asset_registry_mirror,
)

HEADER = (
    "asset_key,override_for,类别,语言维度,状态,待无字化,适用机型,适用区域,"
    "导出物路径,语言变体,内容哈希,备注\n"
)
EXISTING = HEADER + (
    "app/add_device,,插图,中立,✅成品,FALSE,ALL,ALL,"
    "docs/templates/word_template/common_assets/app,,png:474b6e863986,普查登记\n"
    "hero/lcd_display,,插图,中立,🔧临时替代,TRUE,ALL,ALL,"
    "docs/renderers/latex/assets,,v2-pdf:5004a9fe0afe,矢量正式版 v2 集成记录\n"
)


def _record(asset_key: str, **fields):
    """A Feishu record shaped like the 04_资产定义 table returns it."""
    payload = {
        "asset_key": [{"text": asset_key, "type": "text"}],
        "category": "插图",
        "language_dimension": ["中立"],
        "status": ["✅成品"],
        "textless_pending": False,
        "model_scope": "ALL",
        "region_scope": "ALL",
        "language_variants": None,
    }
    payload.update(fields)
    return {"fields": payload}


class DefinitionRowsTest(unittest.TestCase):
    def test_flattens_every_feishu_cell_shape(self):
        rows = definition_rows([
            _record(
                "hero/lcd_display",
                category="插图",
                status=["✅成品"],
                textless_pending=True,
                model_scope="JE-1000F",
                language_variants=["en", "ja"],
            )
        ])
        self.assertEqual(
            rows["hero/lcd_display"],
            {
                "类别": "插图",
                "语言维度": "中立",
                "状态": "✅成品",
                "待无字化": "TRUE",
                "适用机型": "JE-1000F",
                "适用区域": "ALL",
                "语言变体": "en,ja",
            },
        )

    def test_absent_checkbox_reads_as_false(self):
        rows = definition_rows([_record("icon/clock_3s", textless_pending=None)])
        self.assertEqual(rows["icon/clock_3s"]["待无字化"], "FALSE")

    def test_row_without_asset_key_is_skipped(self):
        self.assertEqual(definition_rows([_record("")]), {})


class MergeRegistryTest(unittest.TestCase):
    def test_overlays_owned_columns_and_keeps_repo_columns(self):
        text, stats = merge_registry_csv(EXISTING, [_record("hero/lcd_display")])
        rows = [line.split(",") for line in text.strip().split("\n")[1:]]
        hero = next(r for r in rows if r[0] == "hero/lcd_display")
        # Base-owned: status and textless debt now follow the table.
        self.assertEqual(hero[4], "✅成品")
        self.assertEqual(hero[5], "FALSE")
        # Repo-owned: export path, hashes and the maintenance note survive.
        self.assertEqual(hero[8], "docs/renderers/latex/assets")
        self.assertEqual(hero[10], "v2-pdf:5004a9fe0afe")
        self.assertEqual(hero[11], "矢量正式版 v2 集成记录")
        self.assertEqual(stats.updated, ("hero/lcd_display",))
        self.assertEqual(stats.appended, ())

    def test_unmanaged_rows_pass_through_untouched(self):
        text, _ = merge_registry_csv(EXISTING, [_record("hero/lcd_display")])
        self.assertIn(
            "app/add_device,,插图,中立,✅成品,FALSE,ALL,ALL,"
            "docs/templates/word_template/common_assets/app,,png:474b6e863986,普查登记",
            text,
        )

    def test_new_base_asset_is_appended_with_empty_repo_columns(self):
        text, stats = merge_registry_csv(EXISTING, [_record("button/power")])
        self.assertEqual(stats.appended, ("button/power",))
        self.assertIn("button/power,,插图,中立,✅成品,FALSE,ALL,ALL,,,,\n", text)

    def test_row_missing_from_base_is_never_deleted(self):
        """A vanished Base row must not drop an asset templates still use."""
        text, stats = merge_registry_csv(EXISTING, [])
        self.assertIn("app/add_device", text)
        self.assertIn("hero/lcd_display", text)
        self.assertEqual(stats.updated, ())

    def test_identical_base_data_produces_byte_identical_csv(self):
        first, _ = merge_registry_csv(EXISTING, [_record("hero/lcd_display")])
        second, stats = merge_registry_csv(first, [_record("hero/lcd_display")])
        self.assertEqual(first, second)
        self.assertEqual(stats.updated, ())

    def test_missing_column_fails_closed(self):
        with self.assertRaises(ValueError):
            merge_registry_csv("asset_key,状态\nfoo,✅成品\n", [])


class _Result:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class _Source:
    def __init__(self, records):
        self.records = records
        self.seen: dict = {}

    def fetch_records(self, *, base_token, table_id, view_id=None):
        self.seen = {
            "base_token": base_token, "table_id": table_id, "view_id": view_id}
        return self.records


class SyncMirrorTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(__file__).resolve().parents[1]

    def test_absent_config_block_is_a_no_op(self):
        result, written = sync_asset_registry_mirror(
            {}, source=_Source([]), repo_root=self.tmp,
            sha256_text=lambda t: "x", sha256_file=lambda p: "y",
            result_cls=_Result)
        self.assertIsNone(result)
        self.assertIsNone(written)

    def test_missing_base_token_fails_loudly(self):
        cfg = {"sync": {"phase2": {
            "base_token_env": "ABSENT_BASE_TOKEN", "asset_registry": {}}}}
        with mock.patch.dict("os.environ", {}, clear=False):
            with self.assertRaises(RuntimeError):
                sync_asset_registry_mirror(
                    cfg, source=_Source([]), repo_root=self.tmp,
                    sha256_text=lambda t: "x", sha256_file=lambda p: "y",
                    result_cls=_Result)

    def test_table_id_defaults_to_the_frozen_bindings(self):
        """No new GitHub secret: Phase B froze the coordinates in the repo."""
        cfg = {"sync": {"phase2": {
            "base_token_env": "AR_TEST_BASE_TOKEN", "asset_registry": {}}}}
        source = _Source([])
        with mock.patch.dict(
            "os.environ", {"AR_TEST_BASE_TOKEN": "basetok"}, clear=False
        ):
            result, written = sync_asset_registry_mirror(
                cfg, source=source, repo_root=ROOT,
                sha256_text=lambda t: "new", sha256_file=lambda p: "old",
                result_cls=_Result)
        self.assertEqual(source.seen["base_token"], "basetok")
        self.assertTrue(source.seen["table_id"].startswith("tbl"))
        self.assertEqual(result.logical_name, "asset_registry")
        self.assertTrue(result.changed)
        self.assertEqual(written[0], ROOT / "data" / "asset_registry.csv")

    def test_bad_base_row_fails_the_sync(self):
        """Validation runs through the resolver's own loader."""
        cfg = {"sync": {"phase2": {
            "base_token_env": "AR_TEST_BASE_TOKEN", "asset_registry": {}}}}
        bad = _record("hero/lcd_display", status=["not-a-status"])
        with mock.patch.dict(
            "os.environ", {"AR_TEST_BASE_TOKEN": "basetok"}, clear=False
        ):
            with self.assertRaises(Exception) as ctx:
                sync_asset_registry_mirror(
                    cfg, source=_Source([bad]), repo_root=ROOT,
                    sha256_text=lambda t: "new", sha256_file=lambda p: "old",
                    result_cls=_Result)
        self.assertIn("status", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
