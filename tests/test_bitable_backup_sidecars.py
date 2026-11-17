# -*- coding: utf-8 -*-
"""Fixture tests for tools.bitable_backup sidecar manifests and pass-2 link restore."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.test_helpers import temp_test_root

from tools import bitable_content_backup as bcb
from tools.bitable_backup import __main__ as bb_cli
from tools.bitable_backup import sidecars


def _fake_export_lark(
    *,
    symbols_att: list[list[dict]] | None = None,
    missing_live_token: bool = False,
):
    """Fake lark-cli covering attachment tables and cross-table links."""

    def fake(args: list[str], lark_cli: str = "lark-cli") -> dict:
        sub = args[1]
        if sub == "+table-list":
            return {
                "data": {
                    "items": [
                        {"name": "04_资产槽位", "table_id": "tblSLOT"},
                        {"name": "01_产品型号", "table_id": "tblMODEL"},
                        {"name": "03_内容源_Symbols", "table_id": "tblSYM"},
                    ]
                }
            }
        tid = args[args.index("--table-id") + 1]
        if sub == "+field-list":
            if tid == "tblSLOT":
                return {
                    "data": {
                        "items": [
                            {"field_id": "s1", "name": "Slot_key", "type": "text"},
                            {"field_id": "s2", "name": "preview", "type": "attachment"},
                        ]
                    }
                }
            if tid == "tblMODEL":
                return {
                    "data": {
                        "items": [
                            {"field_id": "m1", "name": "Model", "type": "text"},
                            {"field_id": "m2", "name": "Slots", "type": "two_way_link"},
                            {"field_id": "m3", "name": "ExternalRef", "type": "one_way_link"},
                        ]
                    }
                }
            if tid == "tblSYM":
                return {
                    "data": {
                        "items": [
                            {"field_id": "y1", "name": "Figure", "type": "attachment"},
                            {"field_id": "y2", "name": "Symbol_key", "type": "text"},
                        ]
                    }
                }
        if sub == "+record-list":
            if tid == "tblSLOT":
                att_cell = (
                    [{"token": "boxSlot1", "name": "hero.png", "size": 2048, "mime_type": "image/png", "tmp_url": "https://tmp/1"}]
                    if not missing_live_token
                    else [{"name": "hero.png", "size": 2048, "mime_type": "image/png"}]
                )
                return {
                    "data": {
                        "fields": ["Slot_key", "preview"],
                        "field_id_list": ["s1", "s2"],
                        "data": [
                            ["hero_main", att_cell],
                            ["port_detail", {"file_token": "boxSlot2", "name": "ports.svg", "size": "512", "type": "image/svg+xml"}],
                            ["empty_slot", None],
                        ],
                        "record_id_list": ["recS1", "recS2", "recS3"],
                        "has_more": False,
                    }
                }
            if tid == "tblMODEL":
                return {
                    "data": {
                        "fields": ["Model", "Slots", "ExternalRef"],
                        "field_id_list": ["m1", "m2", "m3"],
                        "data": [
                            [
                                "JE-1000F",
                                [{"record_ids": ["recS1", "recS2"], "text": "hero_main,port_detail"}],
                                {"link_record_ids": ["recOUTSIDE"]},
                            ],
                            [
                                "JE-2000F",
                                ["recS2"],
                                None,
                            ],
                        ],
                        "record_id_list": ["recM1", "recM2"],
                        "has_more": False,
                    }
                }
            if tid == "tblSYM":
                sym_rows = symbols_att if symbols_att is not None else [
                    [[{"file_token": "", "name": "broken.png", "size": 100, "type": "image/png"}], "warn_tri"],
                ]
                return {
                    "data": {
                        "fields": ["Figure", "Symbol_key"],
                        "field_id_list": ["y1", "y2"],
                        "data": sym_rows,
                        "record_id_list": [f"recY{i}" for i in range(len(sym_rows))],
                        "has_more": False,
                    }
                }
        raise AssertionError(f"unexpected lark call: {args[:3]}")

    return fake


MANIFEST = {
    "schema_version": 1,
    "tables": [
        {"name": "04_资产槽位", "fields": []},
        {"name": "01_产品型号", "fields": []},
        {"name": "03_内容源_Symbols", "fields": []},
    ],
}


class AttachmentSidecarTests(unittest.TestCase):
    def test_export_writes_attachments_manifest_and_flags_missing_tokens(self) -> None:
        with temp_test_root() as root, patch.object(bcb.bs, "_lark", _fake_export_lark()):
            report = bcb.export_content(MANIFEST, "basSRC", "business", Path(root), "lark-cli")
            dest = Path(root) / "business"
            self.assertEqual(report["attachments_manifest"], sidecars.ATTACHMENTS_MANIFEST)
            self.assertEqual(report["total_attachments"], 3)

            att_mf = json.loads((dest / sidecars.ATTACHMENTS_MANIFEST).read_text("utf-8"))
            self.assertEqual(att_mf["schema_version"], sidecars.ATTACHMENTS_SCHEMA_VERSION)
            self.assertEqual(att_mf["total_attachments"], 3)
            self.assertEqual(att_mf["missing_token_count"], 1)

            entries = att_mf["entries"]
            self.assertEqual(len(entries), 3)
            slot1, slot2, sym1 = entries
            self.assertEqual(slot1["primary_key_field"], "Slot_key")
            self.assertEqual(slot1["primary_key_value"], "hero_main")
            self.assertEqual(
                slot1["attachments"],
                [{"file_token": "boxSlot1", "name": "hero.png", "size": 2048, "type": "image/png"}],
            )
            self.assertEqual(slot2["attachments"][0]["size"], 512)
            # First column of 03_内容源_Symbols is attachment Figure, so PK skips to Symbol_key.
            self.assertEqual(sym1["primary_key_field"], "Symbol_key")
            self.assertEqual(sym1["primary_key_value"], "warn_tri")
            self.assertEqual(sym1["missing_token_count"], 1)

    def test_verify_legacy_backup_without_attachments_manifest_is_compatible(self) -> None:
        with temp_test_root() as root, patch.object(bcb.bs, "_lark", _fake_export_lark()):
            bcb.export_content(MANIFEST, "basSRC", "business", Path(root), "lark-cli")
            dest = Path(root) / "business"
            (dest / sidecars.ATTACHMENTS_MANIFEST).unlink()
            report = bcb.verify_content(dest, "basSRC", None, "lark-cli")
            self.assertTrue(report["in_sync"])
            self.assertNotIn("backup_attachments", report["tables"][0])

    def test_verify_detects_missing_live_file_token_and_lost_attachments(self) -> None:
        clean_sym = [
            [[{"file_token": "boxSym1", "name": "warn.png", "size": 100, "type": "image/png"}], "warn_tri"],
        ]
        with temp_test_root() as root:
            with patch.object(bcb.bs, "_lark", _fake_export_lark(symbols_att=clean_sym)):
                bcb.export_content(MANIFEST, "basSRC", "business", Path(root), "lark-cli")
            dest = Path(root) / "business"

            with patch.object(bcb.bs, "_lark", _fake_export_lark(symbols_att=clean_sym)):
                ok_report = bcb.verify_content(dest, "basSRC", None, "lark-cli")
                self.assertTrue(ok_report["in_sync"])

            with patch.object(bcb.bs, "_lark", _fake_export_lark(symbols_att=clean_sym, missing_live_token=True)):
                bad_token_report = bcb.verify_content(dest, "basSRC", None, "lark-cli")
                self.assertFalse(bad_token_report["in_sync"])
                slot_row = next(r for r in bad_token_report["tables"] if r["name"] == "04_资产槽位")
                self.assertFalse(slot_row["attachments_match"])
                self.assertEqual(slot_row["live_missing_tokens"], 1)

            with patch.object(bcb.bs, "_lark", _fake_export_lark(symbols_att=[[None, "warn_tri"]])):
                lost_att_report = bcb.verify_content(dest, "basSRC", None, "lark-cli")
                self.assertFalse(lost_att_report["in_sync"])
                sym_row = next(r for r in lost_att_report["tables"] if r["name"] == "03_内容源_Symbols")
                self.assertFalse(sym_row["attachments_match"])
                self.assertEqual(sym_row["backup_attachments"], 1)
                self.assertEqual(sym_row["live_attachments"], 0)


class LinkSidecarAndRestoreTests(unittest.TestCase):
    def _export_tm_fixture(self, root: Path) -> Path:
        tm_manifest = {
            "schema_version": 1,
            "tables": [
                {"name": "Terms", "fields": []},
                {"name": "Translation_Memory", "fields": []},
            ],
        }

        def fake_src(args: list[str], lark_cli: str = "lark-cli") -> dict:
            sub = args[1]
            if sub == "+table-list":
                return {
                    "data": {
                        "items": [
                            {"name": "Terms", "table_id": "tblTERMS"},
                            {"name": "Translation_Memory", "table_id": "tblTM"},
                        ]
                    }
                }
            tid = args[args.index("--table-id") + 1]
            if sub == "+field-list":
                if tid == "tblTERMS":
                    return {"data": {"items": [{"field_id": "t1", "name": "zh", "type": "text"}]}}
                return {
                    "data": {
                        "items": [
                            {"field_id": "m1", "name": "term_zh", "type": "lookup"},
                            {"field_id": "m2", "name": "Key", "type": "text"},
                            {"field_id": "m3", "name": "Glossary_term", "type": "link"},
                        ]
                    }
                }
            if sub == "+record-list":
                if tid == "tblTERMS":
                    return {
                        "data": {
                            "fields": ["zh"],
                            "field_id_list": ["t1"],
                            "data": [["额定功率"], ["电池容量"], ["重复词"]],
                            "record_id_list": ["srcTerm1", "srcTerm2", "srcTermDup"],
                            "has_more": False,
                        }
                    }
                return {
                    "data": {
                        "fields": ["term_zh", "Key", "Glossary_term"],
                        "field_id_list": ["m1", "m2", "m3"],
                        "data": [
                            ["额定功率", "tm_rated", [{"record_ids": ["srcTerm1"], "text": "额定功率"}]],
                            ["电池容量", "tm_cap", [{"record_id": "srcTerm2", "text": "电池容量"}]],
                            ["重复词", "tm_dup_tgt", ["srcTermDup"]],
                            ["缺失", "tm_missing_src", ["srcTerm1"]],
                            ["外部", "tm_unresolved", ["srcTermExternal"]],
                        ],
                        "record_id_list": ["srcTM1", "srcTM2", "srcTM3", "srcTM4", "srcTM5"],
                        "has_more": False,
                    }
                }
            raise AssertionError(f"unexpected: {args[:3]}")

        with patch.object(bcb.bs, "_lark", fake_src):
            report = bcb.export_content(tm_manifest, "basSRC", "tm", root, "lark-cli")
        self.assertEqual(report["links_manifest"], sidecars.LINKS_MANIFEST)
        return root / "tm"

    def _target_lark_factory(self, state: dict, *, silent_drop_for: set[str] | None = None):
        silent = silent_drop_for or set()

        def fake(args: list[str], lark_cli: str = "lark-cli") -> dict:
            state.setdefault("calls", []).append(args)
            sub = args[1]
            if sub == "+table-list":
                return {
                    "data": {
                        "items": [
                            {"name": "Terms", "table_id": "dstTERMS"},
                            {"name": "Translation_Memory", "table_id": "dstTM"},
                        ]
                    }
                }
            tid = args[args.index("--table-id") + 1]
            if sub == "+field-list":
                if tid == "dstTERMS":
                    return {"data": {"items": [{"field_id": "t1", "name": "zh", "type": "text"}]}}
                return {
                    "data": {
                        "items": [
                            {"field_id": "m1", "name": "term_zh", "type": "lookup"},
                            {"field_id": "m2", "name": "Key", "type": "text"},
                            {"field_id": "m3", "name": "Glossary_term", "type": "link"},
                        ]
                    }
                }
            if sub == "+record-list":
                if tid == "dstTERMS":
                    return {
                        "data": {
                            "fields": ["zh"],
                            "field_id_list": ["t1"],
                            "data": [["额定功率"], ["电池容量"], ["重复词"], ["重复词"]],
                            "record_id_list": ["dstTerm1", "dstTerm2", "dstTermDupA", "dstTermDupB"],
                            "has_more": False,
                        }
                    }
                links = state.setdefault(
                    "tm_links",
                    {
                        "dstTM1": [],
                        "dstTM2": [{"record_ids": ["dstTerm2"]}],  # already linked
                        "dstTM3": [],
                        "dstTM5": [],
                    },
                )
                return {
                    "data": {
                        "fields": ["term_zh", "Key", "Glossary_term"],
                        "field_id_list": ["m1", "m2", "m3"],
                        "data": [
                            ["", "tm_rated", links["dstTM1"]],
                            ["", "tm_cap", links["dstTM2"]],
                            ["", "tm_dup_tgt", links["dstTM3"]],
                            ["", "tm_unresolved", links["dstTM5"]],
                        ],
                        "record_id_list": ["dstTM1", "dstTM2", "dstTM3", "dstTM5"],
                        "has_more": False,
                    }
                }
            if sub == "+record-upsert":
                rid = args[args.index("--record-id") + 1]
                payload = json.loads(args[args.index("--json") + 1])
                state.setdefault("upserts", []).append((rid, payload))
                if rid not in silent:
                    state["tm_links"][rid] = payload["Glossary_term"]
                return {"ok": True, "code": 0}
            raise AssertionError(f"unexpected: {args[:3]}")

        return fake

    def test_export_resolves_cross_table_links_and_marks_unresolved(self) -> None:
        with temp_test_root() as root:
            backup_dir = self._export_tm_fixture(Path(root))
            lm = json.loads((backup_dir / sidecars.LINKS_MANIFEST).read_text("utf-8"))
            self.assertEqual(lm["schema_version"], sidecars.LINKS_SCHEMA_VERSION)
            self.assertEqual(lm["total_link_cells"], 5)
            self.assertEqual(lm["resolved_targets"], 4)
            self.assertEqual(lm["unresolved_targets"], 1)
            by_key = {e["primary_key_value"]: e for e in lm["entries"]}
            self.assertEqual(by_key["tm_rated"]["targets"][0]["target_table"], "Terms")
            self.assertEqual(by_key["tm_rated"]["targets"][0]["target_primary_value"], "额定功率")
            self.assertFalse(by_key["tm_unresolved"]["targets"][0]["resolved"])

    def test_dry_run_and_exact_or_abstain_and_write_readback_success(self) -> None:
        with temp_test_root() as root:
            backup_dir = self._export_tm_fixture(Path(root))
            state: dict = {}
            with patch.object(bcb.bs, "_lark", self._target_lark_factory(state)):
                dry = sidecars.plan_and_restore_links(backup_dir, "basDST", write=False)
                self.assertEqual(len(dry["planned"]), 1)
                self.assertEqual(dry["planned"][0]["source_record_id"], "dstTM1")
                self.assertEqual(dry["planned"][0]["target_record_ids"], ["dstTerm1"])
                self.assertEqual(len(dry["already_linked"]), 1)
                reasons = {a["primary_key_value"]: a["reason"] for a in dry["abstained"]}
                self.assertEqual(
                    reasons,
                    {
                        "tm_dup_tgt": "target_ambiguous",
                        "tm_missing_src": "source_not_found",
                        "tm_unresolved": "target_unresolved",
                    },
                )
                self.assertNotIn("upserts", state)

                applied = sidecars.plan_and_restore_links(backup_dir, "basDST", write=True)
                self.assertEqual(len(applied["written"]), 1)
                self.assertEqual(applied["verify_failed"], [])
                self.assertEqual(applied["errors"], [])
                self.assertEqual(state["upserts"], [("dstTM1", {"Glossary_term": ["dstTerm1"]})])

    def test_silent_non_persistence_is_flagged_as_verify_failed_and_cli_exits_nonzero(self) -> None:
        with temp_test_root() as root:
            backup_dir = self._export_tm_fixture(Path(root))
            state: dict = {}
            with patch.object(bcb.bs, "_lark", self._target_lark_factory(state, silent_drop_for={"dstTM1"})):
                rc = bb_cli.main(
                    [
                        "restore-links",
                        "--backup",
                        str(backup_dir),
                        "--base-token",
                        "basDST",
                        "--write",
                        "--yes",
                    ]
                )
                self.assertEqual(rc, 1)
                self.assertEqual(state["upserts"], [("dstTM1", {"Glossary_term": ["dstTerm1"]})])

    def test_cli_help_and_write_without_yes_stays_dry_run(self) -> None:
        with temp_test_root() as root:
            backup_dir = self._export_tm_fixture(Path(root))
            state: dict = {}
            with patch.object(bcb.bs, "_lark", self._target_lark_factory(state)):
                rc = bb_cli.main(
                    [
                        "restore-links",
                        "--backup",
                        str(backup_dir),
                        "--base-token",
                        "basDST",
                        "--write",
                    ]
                )
                self.assertEqual(rc, 0)
                self.assertNotIn("upserts", state)

        proc = subprocess.run(
            [sys.executable, "-m", "tools.bitable_backup", "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("restore-links", proc.stdout)


if __name__ == "__main__":
    unittest.main()
