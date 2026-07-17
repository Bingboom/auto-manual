from __future__ import annotations

import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.asset_registry import AssetRegistryError, NoMatchingAssetExportError
from tools.asset_usage import (
    ASSET_REGISTRY_SNAPSHOT_FILENAME,
    ASSET_USAGE_MANIFEST_FILENAME,
    AssetTarget,
    BundleAssetUsage,
)


class TestBundleAssetUsageCore(unittest.TestCase):
    _HEADER = (
        "asset_key",
        "override_for",
        "类别",
        "语言维度",
        "状态",
        "待无字化",
        "适用机型",
        "适用区域",
        "导出物路径",
        "语言变体",
        "内容哈希",
        "备注",
    )

    def _write_registry(self, root: Path, rows: list[dict[str, str]]) -> Path:
        registry = root / "data" / "asset_registry.csv"
        registry.parent.mkdir(parents=True, exist_ok=True)
        with registry.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=self._HEADER)
            writer.writeheader()
            for row in rows:
                writer.writerow(
                    {
                        "类别": "插图",
                        "语言维度": "中立",
                        "状态": "✅成品",
                        "待无字化": "FALSE",
                        "适用机型": "ALL",
                        "适用区域": "ALL",
                        "导出物路径": "docs/assets",
                        "语言变体": "",
                        "备注": "test fixture",
                        **row,
                    }
                )
        return registry

    def _add_export(
        self,
        root: Path,
        *,
        filename: str,
        content: bytes,
    ) -> str:
        export = root / "docs" / "assets" / filename
        export.parent.mkdir(parents=True, exist_ok=True)
        export.write_bytes(content)
        return hashlib.sha256(content).hexdigest()

    def _usage(
        self,
        root: Path,
        *,
        model: str = "M1",
        region: str = "US",
        language: str | None = "en",
    ) -> BundleAssetUsage:
        return BundleAssetUsage(
            target=AssetTarget(model=model, region=region, language=language),
            repo_root=root,
        )

    def _output_paths(self, bundle: Path) -> tuple[Path, Path]:
        return (
            bundle / ASSET_USAGE_MANIFEST_FILENAME,
            bundle / ASSET_REGISTRY_SNAPSHOT_FILENAME,
        )

    def test_target_and_registry_scope_are_fail_closed(self) -> None:
        with self.assertRaisesRegex(AssetRegistryError, "model must be non-empty"):
            AssetTarget(model=" ", region="US")
        with self.assertRaisesRegex(AssetRegistryError, "region must be non-empty"):
            AssetTarget(model="M1", region=" ")
        with self.assertRaisesRegex(AssetRegistryError, "language must be non-empty"):
            AssetTarget(model="M1", region="US", language=" ")

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            content = b"localized"
            digest = self._add_export(
                root,
                filename="localized-en.png",
                content=content,
            )
            self._write_registry(
                root,
                [
                    {
                        "asset_key": "demo/localized",
                        "语言维度": "按语言",
                        "适用机型": "M1",
                        "适用区域": "US",
                        "语言变体": "en",
                        "内容哈希": f"localized-en.png:{digest}",
                    }
                ],
            )

            usage = self._usage(root, language="EN")
            resolved = usage.resolve_reference(
                "asset:demo/localized",
                model="m1",
                region="us",
                language="en",
            )
            self.assertIsNotNone(resolved)
            self.assertEqual("en", resolved.resolution.language)

            with self.assertRaisesRegex(AssetRegistryError, "conflicts with bound target"):
                usage.resolve_reference("asset:demo/localized", model="M2")
            with self.assertRaisesRegex(AssetRegistryError, "not registered for region EU"):
                self._usage(root, region="EU").resolve_reference("asset:demo/localized")
            with self.assertRaisesRegex(AssetRegistryError, "requires an explicit language"):
                self._usage(root, language=None).resolve_reference("asset:demo/localized")

    def test_safe_format_selection_never_falls_back_to_ai(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            digest = self._add_export(root, filename="sourceonly.ai", content=b"private ai")
            self._write_registry(
                root,
                [
                    {
                        "asset_key": "demo/sourceonly",
                        "内容哈希": f"ai:{digest}",
                    }
                ],
            )

            usage = self._usage(root)
            with self.assertRaisesRegex(NoMatchingAssetExportError, "bundle-safe export"):
                usage.resolve_reference("asset:demo/sourceonly")
            with self.assertRaisesRegex(AssetRegistryError, "unsafe bundle format"):
                usage.stage(
                    root / "docs" / "assets" / "sourceonly.ai",
                    bundle_dir=root / "bundle",
                    docs_dir=root / "docs",
                )

    def test_registry_snapshot_uses_constructor_bytes_after_source_changes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            digest = self._add_export(root, filename="one.png", content=b"one")
            registry = self._write_registry(
                root,
                [{"asset_key": "demo/one", "内容哈希": f"png:{digest}"}],
            )
            original = registry.read_bytes()
            usage = self._usage(root)
            registry.write_text("changed after construction\n", encoding="utf-8")
            bundle = root / "bundle"
            bundle.mkdir()
            manifest, snapshot = self._output_paths(bundle)

            usage.write(
                usage_manifest_path=manifest,
                registry_snapshot_path=snapshot,
                bundle_dir=bundle,
            )

            self.assertEqual(original, snapshot.read_bytes())
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(hashlib.sha256(original).hexdigest(), payload["registry_snapshot"]["sha256"])

    def test_write_rejects_symlinked_snapshot_without_overwriting_bundle_file(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._write_registry(root, [])
            usage = self._usage(root)
            bundle = root / "bundle"
            bundle.mkdir()
            victim = bundle / "index.rst"
            victim.write_bytes(b"must remain an index")
            manifest, snapshot = self._output_paths(bundle)
            snapshot.symlink_to(victim)

            with self.assertRaisesRegex(RuntimeError, "snapshot destination.*symbolic link"):
                usage.write(
                    usage_manifest_path=manifest,
                    registry_snapshot_path=snapshot,
                    bundle_dir=bundle,
                )

            self.assertEqual(b"must remain an index", victim.read_bytes())
            self.assertFalse(manifest.exists())

    def test_write_rejects_symlinked_output_parent_inside_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._write_registry(root, [])
            usage = self._usage(root)
            bundle = root / "bundle"
            real_parent = bundle / "real"
            real_parent.mkdir(parents=True)
            alias_parent = bundle / "alias"
            alias_parent.symlink_to(real_parent, target_is_directory=True)

            with self.assertRaisesRegex(RuntimeError, "manifest destination.*symbolic link"):
                usage.write(
                    usage_manifest_path=alias_parent / ASSET_USAGE_MANIFEST_FILENAME,
                    registry_snapshot_path=bundle / ASSET_REGISTRY_SNAPSHOT_FILENAME,
                    bundle_dir=bundle,
                )

            self.assertFalse((real_parent / ASSET_USAGE_MANIFEST_FILENAME).exists())
            self.assertFalse((bundle / ASSET_REGISTRY_SNAPSHOT_FILENAME).exists())

    def test_registry_and_stage_reject_symlink_escape(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "repo"
            outside = Path(td) / "outside"
            (root / "docs" / "assets").mkdir(parents=True)
            outside.mkdir()
            content = b"outside"
            outside_export = outside / "escaped.png"
            outside_export.write_bytes(content)
            (root / "docs" / "assets" / "escaped.png").symlink_to(outside_export)
            digest = hashlib.sha256(content).hexdigest()
            self._write_registry(
                root,
                [{"asset_key": "demo/escaped", "内容哈希": f"png:{digest}"}],
            )

            with self.assertRaisesRegex(AssetRegistryError, "escapes its trusted root"):
                self._usage(root).resolve_reference("asset:demo/escaped")

            safe_digest = self._add_export(root, filename="safe.png", content=b"safe")
            self._write_registry(
                root,
                [{"asset_key": "demo/safe", "内容哈希": f"png:{safe_digest}"}],
            )
            usage = self._usage(root)
            frozen = usage.resolve_reference("asset:demo/safe")
            self.assertIsNotNone(frozen)
            bundle = root / "bundle"
            bundle.mkdir()
            (bundle / "_assets").symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(AssetRegistryError, "escapes its trusted root"):
                usage.stage(frozen, bundle_dir=bundle, docs_dir=root / "docs")

    def test_stage_uses_frozen_bytes_and_detects_collision(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            original = b"verified bytes"
            digest = self._add_export(root, filename="frozen.png", content=original)
            self._write_registry(
                root,
                [{"asset_key": "demo/frozen", "内容哈希": f"png:{digest}"}],
            )
            usage = self._usage(root)
            frozen = usage.resolve_reference("asset:demo/frozen")
            self.assertIsNotNone(frozen)
            frozen.source_path.write_bytes(b"changed on disk")
            bundle = root / "bundle"
            target = bundle / "_assets" / "assets" / "frozen.png"
            target.parent.mkdir(parents=True)
            target.write_bytes(b"collision")

            with self.assertRaisesRegex(AssetRegistryError, "collision"):
                usage.stage(frozen, bundle_dir=bundle, docs_dir=root / "docs")

            target.write_bytes(original)
            # Passing the tuple-compatible source path still reuses the
            # registry-frozen bytes instead of re-reading the changed file.
            staged = usage.stage(frozen.source_path, bundle_dir=bundle, docs_dir=root / "docs")
            self.assertEqual(target.resolve(), staged.resolve())
            self.assertEqual(original, staged.read_bytes())

    def test_write_rejects_staged_asset_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            digest = self._add_export(root, filename="tamper.png", content=b"original")
            self._write_registry(
                root,
                [{"asset_key": "demo/tamper", "内容哈希": f"png:{digest}"}],
            )
            usage = self._usage(root)
            frozen = usage.resolve_reference("asset:demo/tamper")
            self.assertIsNotNone(frozen)
            bundle = root / "bundle"
            staged = usage.stage(frozen, bundle_dir=bundle, docs_dir=root / "docs")
            usage.record(
                frozen,
                staged_path=staged,
                reference_path=bundle / "page" / "manual.rst",
                bundle_dir=bundle,
            )
            staged.write_bytes(b"tampered")
            manifest, snapshot = self._output_paths(bundle)

            with self.assertRaisesRegex(AssetRegistryError, "hash changed"):
                usage.write(
                    usage_manifest_path=manifest,
                    registry_snapshot_path=snapshot,
                    bundle_dir=bundle,
                )

    def test_manifest_records_registry_and_legacy_assets_in_stable_order(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rows: list[dict[str, str]] = []
            for key, content in (("demo/zeta", b"z"), ("demo/alpha", b"a")):
                basename = key.rsplit("/", 1)[-1]
                digest = self._add_export(root, filename=f"{basename}.png", content=content)
                rows.append({"asset_key": key, "内容哈希": f"png:{digest}"})
            self._write_registry(root, rows)
            legacy = root / "docs" / "legacy" / "old.jpg"
            legacy.parent.mkdir(parents=True)
            legacy.write_bytes(b"legacy")

            usage = self._usage(root)
            bundle = root / "bundle"
            for key in ("demo/zeta", "demo/alpha"):
                frozen = usage.resolve_reference(f"asset:{key}")
                self.assertIsNotNone(frozen)
                staged = usage.stage(frozen, bundle_dir=bundle, docs_dir=root / "docs")
                usage.record(
                    frozen,
                    staged_path=staged,
                    reference_path=bundle / "page" / "b.rst",
                    bundle_dir=bundle,
                )
            legacy_staged = usage.stage(legacy, bundle_dir=bundle, docs_dir=root / "docs")
            usage.record_legacy(
                source_path=legacy,
                staged_path=legacy_staged,
                reference_path=bundle / "page" / "a.rst",
                bundle_dir=bundle,
                docs_dir=root / "docs",
            )
            zeta = usage.resolve_reference("asset:demo/zeta")
            self.assertIsNotNone(zeta)
            usage.record(
                zeta,
                staged_path=bundle / "_assets" / "assets" / "zeta.png",
                reference_path=bundle / "page" / "a.rst",
                bundle_dir=bundle,
            )
            manifest, snapshot = self._output_paths(bundle)
            usage.write(
                usage_manifest_path=manifest,
                registry_snapshot_path=snapshot,
                bundle_dir=bundle,
            )
            first_bytes = manifest.read_bytes()
            usage.write(
                usage_manifest_path=manifest,
                registry_snapshot_path=snapshot,
                bundle_dir=bundle,
            )

            self.assertEqual(first_bytes, manifest.read_bytes())
            payload = json.loads(first_bytes)
            self.assertEqual(
                [
                    ("legacy-path", None),
                    ("registry-uri", "demo/alpha"),
                    ("registry-uri", "demo/zeta"),
                ],
                [(row["reference_kind"], row["asset_key"]) for row in payload["assets"]],
            )
            self.assertEqual(["page/a.rst", "page/b.rst"], payload["assets"][2]["references"])
            self.assertEqual(
                {"model": "M1", "region": "US", "language": "en"},
                payload["target"],
            )
            self.assertEqual(4, len(payload["rewrites"]))
            self.assertTrue(
                all(not Path(row["rendered_value"]).is_absolute() for row in payload["rewrites"])
            )
            self.assertNotIn(str(root), first_bytes.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
