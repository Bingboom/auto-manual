from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.asset_registry import (
    APPROVED_STATUS,
    QUARANTINED_STATUS,
    AssetRecord,
    AssetRegistryError,
    NoMatchingAssetExportError,
    check_registry,
    load_registry,
    load_registry_bytes,
    resolve_asset,
)


ROOT = Path(__file__).resolve().parents[1]


class TestAssetRegistry(unittest.TestCase):
    def setUp(self) -> None:
        self.records = load_registry(ROOT / "data" / "asset_registry.csv")

    def test_real_registry_exports_have_matching_hashes(self) -> None:
        report = check_registry(self.records, repo_root=ROOT)

        self.assertEqual(70, report.records)
        self.assertEqual((), report.errors)
        self.assertEqual(63, report.status_counts[APPROVED_STATUS])
        self.assertEqual(1, report.status_counts[QUARANTINED_STATUS])

    def test_real_registry_has_explicit_region_scopes(self) -> None:
        by_key = {record.asset_key: record for record in self.records}

        self.assertTrue(all(record.region_scope for record in self.records))
        for asset_key in ("page/cover", "page/product_overview", "page/back_cover", "mark/fcc"):
            self.assertEqual(("US",), by_key[asset_key].region_scope)
        self.assertEqual(("JP",), by_key["mark/jp_certifications"].region_scope)
        self.assertEqual(("KR",), by_key["kr/image_placeholders"].region_scope)
        self.assertEqual(("ALL",), by_key["operation/ac_output"].region_scope)

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
        self.assertIsNone(resolution.language)

    def test_neutral_asset_does_not_claim_requested_language(self) -> None:
        resolution = resolve_asset(
            self.records,
            repo_root=ROOT,
            asset_key="operation/ac_output",
            format_name="png",
            language="en",
        )

        self.assertIsNone(resolution.language)

    def test_model_and_region_scopes_are_strict_when_provided(self) -> None:
        for kwargs, message in (
            ({"model": "JE-2000F", "region": "US"}, "model JE-2000F"),
            ({"model": "JE-1000F", "region": "EU"}, "region EU"),
        ):
            with self.subTest(**kwargs):
                with self.assertRaisesRegex(AssetRegistryError, message):
                    resolve_asset(
                        self.records,
                        repo_root=ROOT,
                        asset_key="mark/fcc",
                        format_name="png",
                        **kwargs,
                    )
        with self.assertRaisesRegex(AssetRegistryError, "model "):
            resolve_asset(
                self.records,
                repo_root=ROOT,
                asset_key="operation/ac_output",
                format_name="png",
                model="",
            )

    def test_restricted_scope_requires_explicit_target(self) -> None:
        with self.assertRaisesRegex(AssetRegistryError, "model None"):
            resolve_asset(
                self.records,
                repo_root=ROOT,
                asset_key="mark/fcc",
                format_name="png",
            )
        with self.assertRaisesRegex(AssetRegistryError, "region None"):
            resolve_asset(
                self.records,
                repo_root=ROOT,
                asset_key="mark/fcc",
                format_name="png",
                model="JE-1000F",
            )

    def test_language_scoped_asset_requires_a_declared_variant(self) -> None:
        with self.assertRaisesRegex(AssetRegistryError, "requires an explicit language"):
            resolve_asset(
                self.records,
                repo_root=ROOT,
                asset_key="page/product_overview",
                model="JE-1000F",
                region="US",
            )
        with self.assertRaisesRegex(AssetRegistryError, "no language variant 'de'"):
            resolve_asset(
                self.records,
                repo_root=ROOT,
                asset_key="page/product_overview",
                language="de",
                model="JE-1000F",
                region="US",
            )

        resolution = resolve_asset(
            self.records,
            repo_root=ROOT,
            asset_key="page/product_overview",
            format_name="pdf",
            language="EN",
            model="JE-1000F",
            region="us",
        )
        self.assertEqual("en", resolution.language)

    def test_quarantined_asset_cannot_resolve_or_publish(self) -> None:
        with self.assertRaisesRegex(AssetRegistryError, QUARANTINED_STATUS):
            resolve_asset(
                self.records,
                repo_root=ROOT,
                asset_key="page/back_cover",
                format_name="pdf",
                language="en",
                model="JE-1000F",
                region="US",
                allow_temporary=True,
            )

        report = check_registry(
            self.records,
            repo_root=ROOT,
            asset_keys=("page/back_cover",),
            publish=True,
        )
        self.assertEqual(("non_approved_status",), tuple(issue.code for issue in report.errors))

    def test_resolve_fails_closed_when_export_hash_does_not_match(self) -> None:
        record = AssetRecord(
            asset_key="demo/example",
            category="插图",
            language_dimension="中立",
            status=APPROVED_STATUS,
            textless_pending=False,
            model_scope=("ALL",),
            region_scope=("ALL",),
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

    def test_no_materialized_export_uses_typed_error(self) -> None:
        record = AssetRecord(
            asset_key="demo/missing_export",
            category="插图",
            language_dimension="中立",
            status=APPROVED_STATUS,
            textless_pending=False,
            model_scope=("ALL",),
            region_scope=("ALL",),
            export_root=Path("docs"),
            language_variants=(),
            hashes=(("png", "deadbeef"),),
            notes="",
        )
        with TemporaryDirectory() as tmp:
            Path(tmp, "docs").mkdir()
            with self.assertRaises(NoMatchingAssetExportError):
                resolve_asset((record,), repo_root=Path(tmp), asset_key=record.asset_key)

    def test_load_registry_bytes_parses_one_snapshot(self) -> None:
        data = (
            "asset_key,类别,语言维度,状态,待无字化,适用机型,适用区域,"
            "导出物路径,语言变体,内容哈希,备注\n"
            "demo/source,插图,中立,❌缺失,FALSE,ALL,US,,,,待补\n"
        ).encode("utf-8")

        records = load_registry_bytes(data, source="fixture.csv")

        self.assertEqual(1, len(records))
        self.assertEqual(("US",), records[0].region_scope)

    def test_load_registry_rejects_unknown_language_dimension(self) -> None:
        data = (
            "asset_key,类别,语言维度,状态,待无字化,适用机型,适用区域,"
            "导出物路径,语言变体,内容哈希,备注\n"
            "demo/source,插图,按语种,✅成品,FALSE,ALL,US,docs/assets,en,png:deadbeef,错误维度\n"
        ).encode("utf-8")

        with self.assertRaisesRegex(AssetRegistryError, "unknown language dimension"):
            load_registry_bytes(data, source="fixture.csv")

    def test_load_registry_reads_source_bytes_once(self) -> None:
        data = (ROOT / "data" / "asset_registry.csv").read_bytes()

        class ReadOnceSource:
            def __init__(self, snapshot: bytes) -> None:
                self.snapshot = snapshot
                self.calls = 0

            def read_bytes(self) -> bytes:
                self.calls += 1
                if self.calls > 1:
                    raise AssertionError("registry source was read more than once")
                return self.snapshot

            def __str__(self) -> str:
                return "read-once.csv"

        source = ReadOnceSource(data)
        records = load_registry(source)  # type: ignore[arg-type]

        self.assertEqual(1, source.calls)
        self.assertEqual(70, len(records))

    def test_temporary_asset_is_not_importable_by_default(self) -> None:
        with self.assertRaisesRegex(AssetRegistryError, "only ✅成品"):
            resolve_asset(
                self.records,
                repo_root=ROOT,
                asset_key="mark/warning_lockup",
                format_name="jpg",
                model="JE-1000F",
                region="US",
            )

    def test_temporary_asset_can_be_resolved_for_draft(self) -> None:
        resolution = resolve_asset(
            self.records,
            repo_root=ROOT,
            asset_key="mark/warning_lockup",
            format_name="jpg",
            model="JE-1000F",
            region="US",
            allow_temporary=True,
        )

        self.assertEqual("docs/renderers/latex/assets/warning_lockup.jpg", resolution.path)


if __name__ == "__main__":
    unittest.main()
