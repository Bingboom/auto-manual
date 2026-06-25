#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the source_record_index sidecar (Milestone F, PR F1)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.source_record_index import (  # noqa: E402
    SIDECAR_FILENAME,
    SOURCE_RECORD_ID_KEY,
    _KEY_SEP,
    build_index,
    collect_index_rows,
    index_json_text,
    load_index,
    record_count,
    resolve,
    resolve_by_table,
    resolve_findings,
    resolve_row_record_ids,
)


def _lcd_row(icon: str, model: str, version: str) -> dict[str, str]:
    return {"icon_en": icon, "Model": model, "Version": version}


def _lcd_finding(icon: str, model: str, version: str) -> dict[str, object]:
    return {
        "rule": "status_word_consistency",
        "record_id": None,
        "resolution_status": "snapshot_only",
        "source_ref": {
            "kind": "lcd_icon",
            "table": "lcd_icons_blocks",
            "file": "lcd_icons_blocks.csv",
            "key": icon,
            "model": model,
            "version": version,
        },
    }


class BuildIndexTests(unittest.TestCase):
    def test_exact_keys_map_to_record_ids(self) -> None:
        rows = {
            "lcd_icons_blocks": [
                (_lcd_row("battery", "JE-1000F", "0.7"), "recAAA"),
                (_lcd_row("ac_out", "JE-1000F", "0.7"), "recBBB"),
            ]
        }
        index = build_index(rows)
        table = index["tables"]["lcd_icons_blocks"]
        self.assertEqual(table["key_fields"], ["icon_en", "Model", "Version"])
        self.assertEqual(record_count(index), 2)
        rid, status = resolve(
            index, kind="lcd_icon", source_ref={"key": "battery", "model": "JE-1000F", "version": "0.7"}
        )
        self.assertEqual((rid, status), ("recAAA", "resolved"))

    def test_duplicate_key_distinct_ids_is_ambiguous(self) -> None:
        rows = {
            "lcd_icons_blocks": [
                (_lcd_row("battery", "JE-1000F", "0.7"), "recAAA"),
                (_lcd_row("battery", "JE-1000F", "0.7"), "recDUP"),
            ]
        }
        index = build_index(rows)
        table = index["tables"]["lcd_icons_blocks"]
        self.assertNotIn("battery\x1fJE-1000F\x1f0.7", table["records"])
        self.assertIn("battery\x1fJE-1000F\x1f0.7", table["ambiguous"])
        rid, status = resolve(
            index, kind="lcd_icon", source_ref={"key": "battery", "model": "JE-1000F", "version": "0.7"}
        )
        self.assertEqual((rid, status), (None, "ambiguous"))

    def test_duplicate_key_same_id_is_not_ambiguous(self) -> None:
        rows = {
            "lcd_icons_blocks": [
                (_lcd_row("battery", "JE-1000F", "0.7"), "recAAA"),
                (_lcd_row("battery", "JE-1000F", "0.7"), "recAAA"),
            ]
        }
        index = build_index(rows)
        table = index["tables"]["lcd_icons_blocks"]
        self.assertEqual(table["ambiguous"], [])
        self.assertEqual(record_count(index), 1)

    def test_incomplete_rows_are_skipped(self) -> None:
        rows = {
            "lcd_icons_blocks": [
                (_lcd_row("battery", "JE-1000F", "0.7"), ""),  # no record id
                (_lcd_row("", "JE-1000F", "0.7"), "recCCC"),  # missing key field
            ]
        }
        index = build_index(rows)
        self.assertEqual(record_count(index), 0)


def _spec_row(doc: str, row_key: str, slot: str) -> dict:
    return {"document_key": doc, "Row_key": row_key, "Slot_key": slot}


class OptionalSlotKeyTests(unittest.TestCase):
    """Tier 1: Spec_Master Slot_key is an optional disambiguator.

    Rows without one (product_name, capacity…) — ~half of Spec_Master — must
    still index/resolve by (document_key, Row_key); collisions still abstain.
    """

    def test_unique_empty_slot_row_is_indexed_and_resolves(self) -> None:
        index = build_index({"Spec_Master": [(_spec_row("JE-1000F_US", "capacity", ""), "recCAP")]})
        records = index["tables"]["Spec_Master"]["records"]
        self.assertEqual(records[_KEY_SEP.join(["JE-1000F_US", "capacity", ""])], "recCAP")
        ref = {"table": "Spec_Master", "document_key": "JE-1000F_US", "row_key": "capacity", "slot_key": ""}
        self.assertEqual(resolve_by_table(index, ref), ("recCAP", "resolved"))

    def test_empty_slot_collision_still_abstains(self) -> None:
        # storage_temperature x3 (1/3/12 months) share an empty Slot_key; they are
        # disambiguated by Line_order, not Slot_key, so they remain ambiguous.
        index = build_index(
            {
                "Spec_Master": [
                    (_spec_row("JE-1000F_US", "storage_temperature", ""), "recST1"),
                    (_spec_row("JE-1000F_US", "storage_temperature", ""), "recST2"),
                ]
            }
        )
        table = index["tables"]["Spec_Master"]
        self.assertIn(_KEY_SEP.join(["JE-1000F_US", "storage_temperature", ""]), table["ambiguous"])
        ref = {"table": "Spec_Master", "document_key": "JE-1000F_US", "row_key": "storage_temperature", "slot_key": ""}
        self.assertEqual(resolve_by_table(index, ref), (None, "ambiguous"))

    def test_filled_and_empty_slot_keys_do_not_collide(self) -> None:
        index = build_index(
            {
                "Spec_Master": [
                    (_spec_row("JE-1000F_US", "usb_c", "30w"), "recUSB30"),
                    (_spec_row("JE-1000F_US", "usb_c", "100w"), "recUSB100"),
                    (_spec_row("JE-1000F_US", "capacity", ""), "recCAP"),
                ]
            }
        )
        base = {"table": "Spec_Master", "document_key": "JE-1000F_US"}
        self.assertEqual(resolve_by_table(index, {**base, "row_key": "usb_c", "slot_key": "30w"}), ("recUSB30", "resolved"))
        self.assertEqual(resolve_by_table(index, {**base, "row_key": "usb_c", "slot_key": "100w"}), ("recUSB100", "resolved"))
        self.assertEqual(resolve_by_table(index, {**base, "row_key": "capacity", "slot_key": ""}), ("recCAP", "resolved"))
        # A slotted Row_key queried with an empty slot has no such row -> no false match.
        self.assertEqual(resolve_by_table(index, {**base, "row_key": "usb_c", "slot_key": ""}), (None, "unresolved"))

    def test_missing_required_field_still_skipped(self) -> None:
        # An optional Slot_key may be empty, but a missing document_key (required) is not safe.
        index = build_index(
            {
                "Spec_Master": [
                    (_spec_row("", "capacity", ""), "recNoDoc"),
                    (_spec_row("JE-1000F_US", "", ""), "recNoRow"),
                ]
            }
        )
        self.assertEqual(record_count(index), 0)

    def test_page_placeholders_also_allow_empty_slot(self) -> None:
        index = build_index({"Page_Placeholders_Source": [(_spec_row("JE-2000F_EU", "power", ""), "recPP")]})
        ref = {"table": "Page_Placeholders_Source", "document_key": "JE-2000F_EU", "row_key": "power", "slot_key": ""}
        self.assertEqual(resolve_by_table(index, ref), ("recPP", "resolved"))


def _line_row(doc: str, row_key: str, slot: str, line_order: str) -> dict:
    return {"document_key": doc, "Row_key": row_key, "Slot_key": slot, "Line_order": line_order}


class LineOrderFallbackTests(unittest.TestCase):
    """Tier 2: an ambiguous empty-Slot_key key disambiguates by Line_order fallback."""

    def _multiline_index(self):
        return build_index(
            {
                "Spec_Master": [
                    (_line_row("D", "storage_temperature", "", "1"), "recST1"),
                    (_line_row("D", "storage_temperature", "", "2"), "recST2"),
                    (_line_row("D", "storage_temperature", "", "3"), "recST3"),
                    (_line_row("D", "capacity", "", ""), "recCAP"),  # unique base key
                    (_line_row("D", "usb_c", "30w", "1"), "recUSB30"),  # slotted base key
                ]
            }
        )

    def _ref(self, row_key, slot, line_order):
        return {
            "table": "Spec_Master",
            "document_key": "D",
            "row_key": row_key,
            "slot_key": slot,
            "line_order": line_order,
        }

    def test_multiline_resolves_by_line_order(self) -> None:
        index = self._multiline_index()
        sm = index["tables"]["Spec_Master"]
        self.assertIn(_KEY_SEP.join(["D", "storage_temperature", ""]), sm["ambiguous"])
        self.assertEqual(len(sm["records_by_fallback"]), 3)
        self.assertEqual(resolve_by_table(index, self._ref("storage_temperature", "", "2")), ("recST2", "resolved"))
        self.assertEqual(resolve_by_table(index, self._ref("storage_temperature", "", "3")), ("recST3", "resolved"))

    def test_base_key_path_is_unchanged(self) -> None:
        index = self._multiline_index()
        # Unique / slotted rows still resolve via the primary records map (no fallback).
        self.assertEqual(resolve_by_table(index, self._ref("capacity", "", "")), ("recCAP", "resolved"))
        self.assertEqual(resolve_by_table(index, self._ref("usb_c", "30w", "1")), ("recUSB30", "resolved"))

    def test_ambiguous_without_a_line_order_value_stays_ambiguous(self) -> None:
        index = self._multiline_index()
        self.assertEqual(resolve_by_table(index, self._ref("storage_temperature", "", "")), (None, "ambiguous"))

    def test_line_order_collision_still_abstains(self) -> None:
        # Two rows share Row_key AND Line_order (e.g. input vs output port, disambiguated
        # by Section, not Line_order) -> the fallback key is itself ambiguous -> abstain.
        index = build_index(
            {
                "Spec_Master": [
                    (_line_row("D", "battery_pack", "", "1"), "recIN"),
                    (_line_row("D", "battery_pack", "", "1"), "recOUT"),
                ]
            }
        )
        self.assertEqual(index["tables"]["Spec_Master"].get("records_by_fallback", {}), {})
        self.assertEqual(resolve_by_table(index, self._ref("battery_pack", "", "1")), (None, "ambiguous"))

    def test_old_sidecar_without_fallback_map_degrades_safely(self) -> None:
        # A sidecar built before Tier 2 has an ambiguous key but no records_by_fallback;
        # resolution must abstain, never crash.
        index = {
            "schema_version": "x",
            "tables": {
                "Spec_Master": {
                    "key_fields": ["document_key", "Row_key", "Slot_key"],
                    "records": {},
                    "ambiguous": [_KEY_SEP.join(["D", "storage_temperature", ""])],
                }
            },
        }
        self.assertEqual(resolve_by_table(index, self._ref("storage_temperature", "", "2")), (None, "ambiguous"))

    def test_section_fallback_resolves_same_line_order_ports(self) -> None:
        # Tier 3: two rows share (doc, Row_key, empty Slot_key, Line_order); only
        # Section differs (an input-vs-output port, e.g. dc_expansion_port). Line_order
        # alone can't split them; Section (the second fallback field) does.
        def port_row(section, rid):
            return (
                {"document_key": "D", "Row_key": "dc_expansion_port", "Slot_key": "", "Line_order": "1", "Section": section},
                rid,
            )
        index = build_index({"Spec_Master": [port_row("INPUT PORTS", "recIN"), port_row("OUTPUT PORTS", "recOUT")]})

        def ref(section):
            return {
                "table": "Spec_Master", "document_key": "D", "row_key": "dc_expansion_port",
                "slot_key": "", "line_order": "1", "section": section,
            }
        self.assertEqual(resolve_by_table(index, ref("INPUT PORTS")), ("recIN", "resolved"))
        self.assertEqual(resolve_by_table(index, ref("OUTPUT PORTS")), ("recOUT", "resolved"))
        # same Line_order AND no Section -> still ambiguous (exact-or-abstain)
        self.assertEqual(resolve_by_table(index, ref("")), (None, "ambiguous"))


class CollectIndexRowsTests(unittest.TestCase):
    def test_pairs_normalized_rows_with_record_ids(self) -> None:
        normalized = {"lcd_icons": [_lcd_row("battery", "JE-1000F", "0.7")]}
        raws = {"lcd_icons": [{"fields": {"x": "y"}, "record_id": "recAAA"}]}
        rows = collect_index_rows(normalized, raws)
        self.assertIn("lcd_icons_blocks", rows)
        self.assertEqual(rows["lcd_icons_blocks"][0][1], "recAAA")
        index = build_index(rows)
        self.assertEqual(record_count(index), 1)

    def test_row_carried_record_id_wins_over_position(self) -> None:
        # The real bug: normalize_records SORTS, so the normalized list is in a different
        # order than the raw fetch — pairing positionally mapped each key to the WRONG
        # record. With the record_id carried on the row it stays correct regardless of order.
        normalized = {
            "spec_master": [
                {"document_key": "JE-1000F_CN", "Row_key": "dc12_port", "Slot_key": "front.spec",
                 SOURCE_RECORD_ID_KEY: "recCN"},
                {"document_key": "JE-1000F_US", "Row_key": "dc8020_ports", "Slot_key": "spec",
                 SOURCE_RECORD_ID_KEY: "recUS"},
            ],
        }
        # raws in the OPPOSITE order (the unsorted fetch) — must be ignored when the row carries its id
        raws = {"spec_master": [{"record_id": "recUS"}, {"record_id": "recCN"}]}
        records = build_index(collect_index_rows(normalized, raws))["tables"]["Spec_Master"]["records"]
        self.assertEqual(records[_KEY_SEP.join(["JE-1000F_CN", "dc12_port", "front.spec"])], "recCN")
        self.assertEqual(records[_KEY_SEP.join(["JE-1000F_US", "dc8020_ports", "spec"])], "recUS")

    def test_positional_fallback_when_row_lacks_carried_id(self) -> None:
        # A row without the carried key still pairs positionally with raw_records (legacy).
        normalized = {"lcd_icons": [_lcd_row("battery", "JE-1000F", "0.7")]}
        raws = {"lcd_icons": [{"record_id": "recAAA"}]}
        self.assertEqual(collect_index_rows(normalized, raws)["lcd_icons_blocks"][0][1], "recAAA")

    def test_missing_table_is_omitted(self) -> None:
        self.assertEqual(collect_index_rows({}, {}), {})

    def test_unindexed_logical_table_is_ignored(self) -> None:
        rows = collect_index_rows({"troubleshooting": [{"a": "b"}]}, {"troubleshooting": [{"record_id": "r"}]})
        self.assertEqual(rows, {})

    def test_spec_master_is_indexed_and_resolvable(self) -> None:
        normalized = {
            "spec_master": [
                {"document_key": "JE-1000F_EU", "Row_key": "dc12_port", "Slot_key": "main", "Value_uk": "DC 12 В"}
            ]
        }
        raws = {"spec_master": [{"fields": {}, "record_id": "recDC"}]}
        index = build_index(collect_index_rows(normalized, raws))
        self.assertIn("Spec_Master", index["tables"])
        self.assertEqual(record_count(index), 1)
        ref = {"table": "Spec_Master", "document_key": "JE-1000F_EU", "row_key": "dc12_port", "slot_key": "main"}
        self.assertEqual(resolve_by_table(index, ref), ("recDC", "resolved"))

    def test_page_placeholder_rows_are_indexed_separately_from_spec_master(self) -> None:
        normalized = {
            "spec_master": [
                {
                    "document_key": "JE-2000F_EU",
                    "Page": "Product overview",
                    "Row_key": "usb_a",
                    "Slot_key": "front.label",
                    SOURCE_RECORD_ID_KEY: "recPlaceholder",
                },
                {
                    "document_key": "JE-2000F_EU",
                    "Page": "specifications",
                    "Row_key": "capacity",
                    "Slot_key": "value",
                    SOURCE_RECORD_ID_KEY: "recSpec",
                },
            ]
        }
        index = build_index(collect_index_rows(normalized, {"spec_master": []}))
        placeholder_ref = {
            "table": "Page_Placeholders_Source",
            "document_key": "JE-2000F_EU",
            "row_key": "usb_a",
            "slot_key": "front.label",
        }
        spec_ref = {
            "table": "Spec_Master",
            "document_key": "JE-2000F_EU",
            "row_key": "capacity",
            "slot_key": "value",
        }
        self.assertEqual(resolve_by_table(index, placeholder_ref), ("recPlaceholder", "resolved"))
        self.assertEqual(resolve_by_table(index, spec_ref), ("recSpec", "resolved"))


def _mcs_row(copy_key: str, is_latest: str = "true") -> dict[str, str]:
    return {"copy_key": copy_key, "Is_Latest": is_latest}


def _copy_ref(copy_key: str) -> dict[str, str]:
    # The source_ref shape token_resolution_map emits for a Localized_Copy value.
    return {"table": "Localized_Copy", "field": "text_it", "copy_key": copy_key}


class ManualCopySourceIndexTests(unittest.TestCase):
    def test_localized_copy_origin_resolves_to_manual_copy_source(self) -> None:
        normalized = {"manual_copy_source": [_mcs_row("warning.intro")]}
        raws = {"manual_copy_source": [{"fields": {}, "record_id": "recMC1"}]}
        index = build_index(collect_index_rows(normalized, raws))
        self.assertIn("Manual_Copy_Source", index["tables"])
        self.assertEqual(record_count(index), 1)
        # A Localized_Copy-origin source_ref resolves to the authoring row.
        self.assertEqual(resolve_by_table(index, _copy_ref("warning.intro")), ("recMC1", "resolved"))

    def test_non_latest_rows_are_filtered_out(self) -> None:
        # The stale row shares copy_key but has a different record_id; without the
        # Is_Latest filter the key would be ambiguous. Only the latest is indexed.
        normalized = {
            "manual_copy_source": [
                _mcs_row("warning.intro", is_latest="false"),
                _mcs_row("warning.intro", is_latest="true"),
            ]
        }
        raws = {"manual_copy_source": [{"record_id": "recOLD"}, {"record_id": "recNEW"}]}
        index = build_index(collect_index_rows(normalized, raws))
        self.assertEqual(record_count(index), 1)
        self.assertEqual(resolve_by_table(index, _copy_ref("warning.intro")), ("recNEW", "resolved"))

    def test_blank_is_latest_is_kept(self) -> None:
        # A snapshot that does not populate Is_Latest must not silently empty the index.
        normalized = {"manual_copy_source": [_mcs_row("warning.intro", is_latest="")]}
        raws = {"manual_copy_source": [{"record_id": "recMC1"}]}
        index = build_index(collect_index_rows(normalized, raws))
        self.assertEqual(resolve_by_table(index, _copy_ref("warning.intro")), ("recMC1", "resolved"))

    def test_collision_among_latest_rows_abstains(self) -> None:
        normalized = {
            "manual_copy_source": [
                _mcs_row("dup.key", is_latest="true"),
                _mcs_row("dup.key", is_latest="true"),
            ]
        }
        raws = {"manual_copy_source": [{"record_id": "recA"}, {"record_id": "recB"}]}
        index = build_index(collect_index_rows(normalized, raws))
        self.assertEqual(resolve_by_table(index, _copy_ref("dup.key")), (None, "ambiguous"))


class ResolveFindingsTests(unittest.TestCase):
    def _write_sidecar(self, root: Path, index: dict) -> None:
        (root / SIDECAR_FILENAME).write_text(index_json_text(index), encoding="utf-8")

    def test_resolves_against_sidecar(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index = build_index({"lcd_icons_blocks": [(_lcd_row("battery", "JE-1000F", "0.7"), "recAAA")]})
            self._write_sidecar(root, index)
            findings = resolve_findings([_lcd_finding("battery", "JE-1000F", "0.7")], root)
            self.assertEqual(findings[0]["record_id"], "recAAA")
            self.assertEqual(findings[0]["resolution_status"], "resolved")

    def test_unresolved_when_key_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index = build_index({"lcd_icons_blocks": [(_lcd_row("battery", "JE-1000F", "0.7"), "recAAA")]})
            self._write_sidecar(root, index)
            findings = resolve_findings([_lcd_finding("missing", "JE-1000F", "0.7")], root)
            self.assertIsNone(findings[0]["record_id"])
            self.assertEqual(findings[0]["resolution_status"], "unresolved")

    def test_no_sidecar_leaves_findings_snapshot_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertIsNone(load_index(root))
            findings = resolve_findings([_lcd_finding("battery", "JE-1000F", "0.7")], root)
            self.assertIsNone(findings[0]["record_id"])
            self.assertEqual(findings[0]["resolution_status"], "snapshot_only")

    def test_malformed_sidecar_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / SIDECAR_FILENAME).write_text("{not json", encoding="utf-8")
            self.assertIsNone(load_index(root))
            findings = resolve_findings([_lcd_finding("battery", "JE-1000F", "0.7")], root)
            self.assertEqual(findings[0]["resolution_status"], "snapshot_only")


class JsonTextTests(unittest.TestCase):
    def test_deterministic_and_parseable(self) -> None:
        index = build_index({"lcd_icons_blocks": [(_lcd_row("battery", "JE-1000F", "0.7"), "recAAA")]})
        text_a = index_json_text(index)
        text_b = index_json_text(build_index({"lcd_icons_blocks": [(_lcd_row("battery", "JE-1000F", "0.7"), "recAAA")]}))
        self.assertEqual(text_a, text_b)
        self.assertEqual(json.loads(text_a)["schema_version"], "source-record-index/v1")


def _spec_slot(document_key: str, row_key: str, slot_key: str) -> dict[str, str]:
    return {"document_key": document_key, "Row_key": row_key, "Slot_key": slot_key}


def _spec_row_finding(document_key: str, row_key: str) -> dict[str, object]:
    # content_lint's spec_overview_drift shape: row-level, uses `key` for Row_key.
    return {
        "rule": "spec_overview_drift",
        "resolution_status": "snapshot_only",
        "source_ref": {"kind": "spec_master_row", "table": "Spec_Master", "document_key": document_key, "key": row_key},
    }


class RowResolutionTests(unittest.TestCase):
    def _index(self):
        return build_index(
            {
                "Spec_Master": [
                    (_spec_slot("D", "ac_input", "label"), "recA"),
                    (_spec_slot("D", "ac_input", "spec"), "recB"),
                    (_spec_slot("D", "usb_a", "main"), "recC"),  # single slot
                    (_spec_slot("E", "ac_input", "label"), "recOther"),  # other document
                ]
            }
        )

    def test_row_resolves_to_all_slot_record_ids(self) -> None:
        ids, status = resolve_row_record_ids(
            self._index(), kind="spec_master_row", source_ref={"document_key": "D", "key": "ac_input"}
        )
        self.assertEqual(status, "resolved")
        self.assertEqual(sorted(ids), ["recA", "recB"])  # both slots, not the other document's

    def test_unknown_row_is_unresolved(self) -> None:
        ids, status = resolve_row_record_ids(
            self._index(), kind="spec_master_row", source_ref={"document_key": "D", "key": "missing"}
        )
        self.assertEqual((ids, status), ([], "unresolved"))

    def test_missing_key_field_abstains(self) -> None:
        ids, status = resolve_row_record_ids(
            self._index(), kind="spec_master_row", source_ref={"document_key": "D"}
        )
        self.assertEqual((ids, status), ([], "unresolved"))

    def test_resolve_findings_sets_record_ids_for_row_kind(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / SIDECAR_FILENAME).write_text(index_json_text(self._index()), encoding="utf-8")
            findings = resolve_findings([_spec_row_finding("D", "ac_input"), _spec_row_finding("D", "usb_a")], root)
            self.assertEqual(findings[0]["resolution_status"], "resolved")
            self.assertEqual(sorted(findings[0]["record_ids"]), ["recA", "recB"])
            self.assertNotIn("record_id", findings[0])  # multi-slot -> no single record_id
            # single-slot row exposes record_id too
            self.assertEqual(findings[1]["record_ids"], ["recC"])
            self.assertEqual(findings[1]["record_id"], "recC")


if __name__ == "__main__":
    unittest.main()
