#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Release asset lineage and the publish gate that reads it."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.release_asset_lineage import (  # noqa: E402
    collect_asset_lineage,
    csv_columns,
    publish_blockers,
    run_publish_asset_gate,
)


def _bundle(tmp: str, *, assets, bundle_sha="abc123", snapshot=True) -> Path:
    bundle_dir = Path(tmp)
    usage = {
        "schema_version": 2,
        "assets": assets,
        "target": {"model": "JE-1000F", "region": "US", "language": None},
        "rewrites": [],
    }
    if snapshot:
        usage["registry_snapshot"] = {
            "path": "asset_registry_snapshot.csv",
            "sha256": "5fa9e6cf",
            "source_path": "data/asset_registry.csv",
        }
    (bundle_dir / "asset_usage_manifest.json").write_text(
        json.dumps(usage), encoding="utf-8")
    (bundle_dir / "bundle_manifest.json").write_text(
        json.dumps({"bundle_sha256": bundle_sha}), encoding="utf-8")
    return bundle_dir


def _approved(asset_key="hero/lcd_display", **over):
    row = {
        "asset_key": asset_key,
        "format": "pdf",
        "sha256": "f" * 64,
        "status": "✅成品",
        "source": "registry-export",
        "staged_path": f"renderers/latex/assets/{asset_key.split('/')[-1]}.pdf",
        "reference_kind": "registry-uri",
    }
    row.update(over)
    return row


def _legacy():
    return {
        "asset_key": None,
        "format": "png",
        "sha256": "e" * 64,
        "status": "legacy-unmanaged",
        "source": "legacy-path",
        "reference_kind": "legacy-path",
    }


class CollectLineageTest(unittest.TestCase):
    def test_separates_registry_assets_from_legacy_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            lineage = collect_asset_lineage(
                bundle_dir=_bundle(tmp, assets=[_approved(), _legacy(), _legacy()]))
        self.assertEqual(lineage["registry_asset_count"], 1)
        self.assertEqual(lineage["legacy_path_count"], 2)
        self.assertEqual(lineage["bundle_sha256"], "abc123")
        self.assertEqual(lineage["registry_snapshot"]["source_path"],
                         "data/asset_registry.csv")

    def test_assets_are_sorted_for_a_stable_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            lineage = collect_asset_lineage(bundle_dir=_bundle(
                tmp, assets=[_approved("z/last"), _approved("a/first")]))
        self.assertEqual([row["asset_key"] for row in lineage["assets"]],
                         ["a/first", "z/last"])

    def test_missing_usage_manifest_yields_no_lineage(self):
        """A target that predates asset finalization still gets a manifest."""
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(collect_asset_lineage(bundle_dir=Path(tmp)))

    def test_unreadable_usage_manifest_is_treated_as_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "asset_usage_manifest.json").write_text("{not json",
                                                                 encoding="utf-8")
            self.assertIsNone(collect_asset_lineage(bundle_dir=Path(tmp)))


class PublishBlockerTest(unittest.TestCase):
    def test_approved_assets_do_not_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            lineage = collect_asset_lineage(
                bundle_dir=_bundle(tmp, assets=[_approved(), _legacy()]))
        self.assertEqual(publish_blockers(lineage), ())

    def test_every_non_approved_status_blocks(self):
        for status in ("🔧临时替代", "❌缺失", "⛔隔离"):
            with self.subTest(status=status):
                with tempfile.TemporaryDirectory() as tmp:
                    lineage = collect_asset_lineage(bundle_dir=_bundle(
                        tmp, assets=[_approved(status=status)]))
                blockers = publish_blockers(lineage)
                self.assertEqual(len(blockers), 1)
                self.assertIn(status, blockers[0])

    def test_legacy_paths_alone_never_block(self):
        """Blocking on them would stop every publish instead of showing debt."""
        with tempfile.TemporaryDirectory() as tmp:
            lineage = collect_asset_lineage(
                bundle_dir=_bundle(tmp, assets=[_legacy()] * 50))
        self.assertEqual(publish_blockers(lineage), ())
        self.assertEqual(lineage["legacy_path_count"], 50)

    def test_absent_lineage_blocks_publish(self):
        self.assertEqual(len(publish_blockers(None)), 1)


class GateTest(unittest.TestCase):
    def test_gate_passes_and_reports(self):
        lines: list[str] = []
        with tempfile.TemporaryDirectory() as tmp:
            run_publish_asset_gate(
                bundle_dir=_bundle(tmp, assets=[_approved(), _legacy()]),
                printer=lines.append)
        self.assertTrue(lines[0].startswith("[publish-assets] OK"))
        self.assertIn("1 registry asset(s)", lines[0])

    def test_gate_raises_before_anything_is_released(self):
        lines: list[str] = []
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(RuntimeError):
                run_publish_asset_gate(
                    bundle_dir=_bundle(tmp, assets=[_approved(status="⛔隔离")]),
                    printer=lines.append)
        self.assertTrue(any("BLOCKED" in line for line in lines))


class CsvColumnTest(unittest.TestCase):
    def test_columns_are_scalars_for_the_release_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            lineage = collect_asset_lineage(
                bundle_dir=_bundle(tmp, assets=[_approved(), _legacy()]))
        self.assertEqual(csv_columns(lineage), {
            "assets_registry_count": "1",
            "assets_legacy_path_count": "1",
            "assets_bundle_sha256": "abc123",
            "assets_registry_snapshot_sha256": "5fa9e6cf",
        })

    def test_absent_lineage_still_yields_every_column(self):
        self.assertEqual(sorted(csv_columns(None)), [
            "assets_bundle_sha256",
            "assets_legacy_path_count",
            "assets_registry_count",
            "assets_registry_snapshot_sha256",
        ])


if __name__ == "__main__":
    unittest.main()
