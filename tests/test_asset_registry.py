from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.asset_registry import (
    APPROVED_STATUS,
    AssetRecord,
    AssetRegistryError,
    check_registry,
    load_registry,
    resolve_asset,
)


ROOT = Path(__file__).resolve().parents[1]


class TestAssetRegistry(unittest.TestCase):
    def setUp(self) -> None:
        self.records = load_registry(ROOT / "data" / "asset_registry.csv")

    def test_real_registry_exports_have_matching_hashes(self) -> None:
        report = check_registry(self.records, repo_root=ROOT)

        self.assertEqual(71, report.records)
        self.assertEqual((), report.errors)
        self.assertEqual(64, report.status_counts[APPROVED_STATUS])

    def test_resolve_v2_vector_projection(self) -> None:
        resolution = resolve_asset(
            self.records,
            repo_root=ROOT,
            asset_key="operation/ac_output",
            format_name="png",
        )

        self.assertEqual("docs/renderers/latex/assets/op_ac_output.png", resolution.path)
        self.assertEqual("✅成品", resolution.status)
        self.assertEqual(64, len(resolution.content_hash))
        self.assertTrue(resolution.content_hash.startswith(resolution.declared_hash))

    def test_resolve_fails_closed_when_export_hash_does_not_match(self) -> None:
        record = AssetRecord(
            asset_key="demo/example",
            category="插图",
            language_dimension="中立",
            status=APPROVED_STATUS,
            textless_pending=False,
            model_scope=("ALL",),
            export_root=Path("docs"),
            language_variants=(),
            hashes=(("png", "deadbeef"),),
            notes="",
        )
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            root.joinpath("docs").mkdir()
            root.joinpath("docs", "example.png").write_bytes(b"not the registered bytes")

            with self.assertRaisesRegex(AssetRegistryError, "hash mismatch"):
                resolve_asset((record,), repo_root=root, asset_key=record.asset_key)

    def test_temporary_asset_is_not_importable_by_default(self) -> None:
        with self.assertRaisesRegex(AssetRegistryError, "only ✅成品"):
            resolve_asset(
                self.records,
                repo_root=ROOT,
                asset_key="mark/warning_lockup",
                format_name="jpg",
            )

    def test_temporary_asset_can_be_resolved_for_draft(self) -> None:
        resolution = resolve_asset(
            self.records,
            repo_root=ROOT,
            asset_key="mark/warning_lockup",
            format_name="jpg",
            allow_temporary=True,
        )

        self.assertEqual("docs/renderers/latex/assets/warning_lockup.jpg", resolution.path)


if __name__ == "__main__":
    unittest.main()
