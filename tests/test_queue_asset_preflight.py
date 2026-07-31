from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from tools.queue_asset_preflight import preflight_asset_lineage


REGISTRY_HEADER = (
    "asset_key,override_for,类别,语言维度,状态,待无字化,适用机型,适用区域,"
    "导出物路径,语言变体,内容哈希,备注\n"
)


def _registry_row(*, asset_key: str, digest: str) -> str:
    return (
        f"{asset_key},,插图,中立,✅成品,FALSE,ALL,ALL,"
        f"docs/templates/common_assets/foo,,png:{digest},\n"
    )


class TestQueueAssetPreflight(unittest.TestCase):
    def test_resolves_target_template_references(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            asset = root / "docs/templates/common_assets/foo/bar.png"
            asset.parent.mkdir(parents=True)
            asset.write_bytes(b"asset-bytes")
            digest = hashlib.sha256(asset.read_bytes()).hexdigest()
            registry = root / "data/asset_registry.csv"
            registry.parent.mkdir(parents=True)
            registry.write_text(
                REGISTRY_HEADER + _registry_row(asset_key="foo/bar", digest=digest),
                encoding="utf-8",
            )
            source = root / "docs/templates/page_us-en/page.rst"
            source.parent.mkdir(parents=True)
            source.write_text(".. image:: asset:foo/bar\n", encoding="utf-8")

            report = preflight_asset_lineage(
                repo_root=root,
                model="JE-1000F",
                region="US",
                language="en",
                build_family="us-merged",
            )

            self.assertEqual(("foo/bar",), report.references)
            self.assertEqual(("foo/bar",), report.resolved)
            self.assertEqual((), report.warnings)

    def test_unresolvable_reference_is_advisory_warning(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            registry = root / "data/asset_registry.csv"
            registry.parent.mkdir(parents=True)
            registry.write_text(REGISTRY_HEADER, encoding="utf-8")
            source = root / "docs/templates/page_us-en/page.rst"
            source.parent.mkdir(parents=True)
            source.write_text(".. image:: asset:missing/icon\n", encoding="utf-8")

            report = preflight_asset_lineage(
                repo_root=root,
                model="JE-1000F",
                region="US",
                language="en",
                build_family="us-en",
            )

            self.assertEqual(("missing/icon",), report.references)
            self.assertEqual((), report.resolved)
            self.assertEqual(("unresolvable_asset",), tuple(item.code for item in report.warnings))

    def test_missing_source_tree_is_advisory_warning(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            registry = root / "data/asset_registry.csv"
            registry.parent.mkdir(parents=True)
            registry.write_text(REGISTRY_HEADER, encoding="utf-8")

            report = preflight_asset_lineage(
                repo_root=root,
                model="JE-1000F",
                region="US",
                language="en",
                build_family="us-en",
            )

            self.assertEqual(("source_snapshot_unavailable",), tuple(item.code for item in report.warnings))


if __name__ == "__main__":
    unittest.main()
