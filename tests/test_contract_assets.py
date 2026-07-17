from __future__ import annotations

import csv
import hashlib
import tempfile
import unittest
from pathlib import Path

from tools.asset_registry import AssetRegistryError
from tools.contract_assets import ContractAssetResolver, render_contract_asset_value


class TestContractAssets(unittest.TestCase):
    _REGISTRY_HEADER = (
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
            writer = csv.DictWriter(handle, fieldnames=self._REGISTRY_HEADER)
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
                        "内容哈希": "",
                        "备注": "contract resolver fixture",
                        **row,
                    }
                )
        return registry

    def _write_export(
        self,
        root: Path,
        *,
        filename: str,
        content: bytes,
    ) -> tuple[Path, str]:
        export = root / "docs" / "assets" / filename
        export.parent.mkdir(parents=True, exist_ok=True)
        export.write_bytes(content)
        return export, hashlib.sha256(content).hexdigest()

    def _resolver(
        self,
        root: Path,
        *,
        model: str | None = "M1",
        region: str | None = "US",
    ) -> ContractAssetResolver:
        return ContractAssetResolver(
            docs_dir=root / "docs",
            repo_root=root,
            model=model,
            region=region,
        )

    def test_legacy_path_and_registry_uri_share_one_resolver(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            legacy, _legacy_hash = self._write_export(
                root,
                filename="legacy.png",
                content=b"legacy",
            )
            approved, approved_hash = self._write_export(
                root,
                filename="approved.png",
                content=b"approved",
            )
            self._write_registry(
                root,
                [
                    {
                        "asset_key": "demo/approved",
                        "内容哈希": f"approved.png:{approved_hash}",
                    }
                ],
            )
            resolver = self._resolver(root)

            self.assertEqual(legacy, resolver.resolve("assets/legacy.png", lang="en"))
            self.assertEqual(approved.resolve(), resolver.resolve("asset:demo/approved", lang="en"))
            self.assertTrue(resolver.exists("assets/legacy.png", lang="en"))
            self.assertTrue(resolver.exists("asset:demo/approved", lang="en"))

    def test_registry_uri_scope_is_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            localized, digest = self._write_export(
                root,
                filename="localized-en.png",
                content=b"localized",
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

            self.assertEqual(
                localized.resolve(),
                self._resolver(root).resolve("asset:demo/localized", lang="en"),
            )
            for resolver, lang, message in (
                (self._resolver(root, model="M2"), "en", "model M2"),
                (self._resolver(root, region="EU"), "en", "region EU"),
                (self._resolver(root), "fr", "no language variant"),
                (self._resolver(root), None, "requires an explicit language"),
                (self._resolver(root, model=None), "en", "explicit model and region"),
                (self._resolver(root, region=None), "en", "explicit model and region"),
            ):
                with self.subTest(model=resolver.model, region=resolver.region, lang=lang):
                    self.assertFalse(resolver.exists("asset:demo/localized", lang=lang))
                    with self.assertRaisesRegex(AssetRegistryError, message):
                        resolver.resolve("asset:demo/localized", lang=lang)

    def test_contract_asset_tokens_use_build_slug_rules(self) -> None:
        rendered = render_contract_asset_value(
            "asset:demo/{model_slug}-{region_slug}-{lang_slug}",
            model="JE-1000F",
            region="US",
            lang="pt-BR",
        )

        self.assertEqual("asset:demo/je1000f-us-br", rendered)

    def test_contract_resolver_honors_injected_value_renderer(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            legacy, _digest = self._write_export(
                root,
                filename="legacy.png",
                content=b"legacy",
            )
            self._write_registry(root, [])
            resolver = ContractAssetResolver(
                docs_dir=root / "docs",
                repo_root=root,
                model="M1",
                region="US",
                value_renderer=lambda raw, **_kwargs: (
                    "assets/legacy.png" if raw == "custom:legacy" else raw
                ),
            )

            self.assertEqual(legacy, resolver.resolve("custom:legacy", lang="en"))

    def test_ai_only_temporary_and_quarantined_uris_do_not_exist(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rows: list[dict[str, str]] = []
            for asset_key, filename, status in (
                ("demo/ai_only", "ai_only.ai", "✅成品"),
                ("demo/temporary", "temporary.png", "🔧临时替代"),
                ("demo/quarantined", "quarantined.png", "⛔隔离"),
            ):
                _path, digest = self._write_export(
                    root,
                    filename=filename,
                    content=asset_key.encode("utf-8"),
                )
                rows.append(
                    {
                        "asset_key": asset_key,
                        "状态": status,
                        "内容哈希": f"{filename}:{digest}",
                    }
                )
            self._write_registry(root, rows)
            resolver = self._resolver(root)

            for asset_key in ("demo/ai_only", "demo/temporary", "demo/quarantined"):
                with self.subTest(asset_key=asset_key):
                    self.assertFalse(resolver.exists(f"asset:{asset_key}", lang="en"))

    def test_check_and_materialize_views_reuse_one_registry_byte_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            export, digest = self._write_export(
                root,
                filename="stable.png",
                content=b"stable",
            )
            registry = self._write_registry(
                root,
                [
                    {
                        "asset_key": "demo/stable",
                        "内容哈希": f"stable.png:{digest}",
                    }
                ],
            )
            initial_registry_bytes = registry.read_bytes()
            resolver = self._resolver(root)

            # ``exists`` is the check-side view and initializes the resolver's
            # immutable registry snapshot.
            self.assertTrue(resolver.exists("asset:demo/stable", lang="en"))
            self._write_registry(
                root,
                [
                    {
                        "asset_key": "demo/stable",
                        "状态": "⛔隔离",
                        "内容哈希": f"stable.png:{digest}",
                    }
                ],
            )
            self.assertNotEqual(initial_registry_bytes, registry.read_bytes())

            # ``resolve`` is the materialize-side view. The same resolver must
            # keep using the byte snapshot captured by the earlier check.
            self.assertEqual(export.resolve(), resolver.resolve("asset:demo/stable", lang="en"))
            self.assertFalse(
                self._resolver(root).exists("asset:demo/stable", lang="en"),
                "a new resolver should observe the quarantined registry row",
            )


if __name__ == "__main__":
    unittest.main()
