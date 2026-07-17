from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from tools.asset_registry import AssetRegistryError
from tools.bundle_asset_finalize import finalize_materialized_bundle
from tools.gen_index_bundle_models import MaterializedBundle


class TestBundleAssetFinalize(unittest.TestCase):
    _REGISTRY_HEADER = (
        "asset_key,override_for,类别,语言维度,状态,待无字化,适用机型,适用区域,"
        "导出物路径,语言变体,内容哈希,备注\n"
    )

    def _workspace(self, root: Path) -> tuple[Path, Path, Path]:
        repo_root = root / "repo"
        docs_dir = repo_root / "docs"
        bundle_dir = root / "external-build" / "bundle"
        docs_dir.mkdir(parents=True)
        bundle_dir.mkdir(parents=True)
        registry = repo_root / "data" / "asset_registry.csv"
        registry.parent.mkdir(parents=True)
        registry.write_text(self._REGISTRY_HEADER, encoding="utf-8")
        return repo_root, docs_dir, bundle_dir

    def _materialized_bundle(
        self,
        *,
        docs_dir: Path,
        bundle_dir: Path,
        stale_page: Path,
        lang: str | None = "en",
    ) -> MaterializedBundle:
        return MaterializedBundle(
            bundle_dir=bundle_dir,
            page_dir=bundle_dir / "page",
            index_path=bundle_dir / "index.rst",
            conf_path=bundle_dir / "conf.py",
            conf_base_path=bundle_dir / "conf_base.py",
            wrapper_index_path=docs_dir / "index.rst",
            page_paths=(stale_page,),
            title="Asset finalizer fixture",
            reference_doc=None,
            model="M1",
            region="US",
            lang=lang,
            manifest_path=bundle_dir / "bundle_manifest.json",
        )

    def _add_registry_asset(
        self,
        *,
        repo_root: Path,
        asset_key: str = "demo/managed",
        content: bytes = b"registry bytes",
    ) -> Path:
        export = repo_root / "docs" / "assets" / "managed.png"
        export.parent.mkdir(parents=True, exist_ok=True)
        export.write_bytes(content)
        digest = hashlib.sha256(content).hexdigest()
        (repo_root / "data" / "asset_registry.csv").write_text(
            self._REGISTRY_HEADER
            + f"{asset_key},,插图,中立,✅成品,FALSE,M1,US,"
            f"docs/assets,,png:{digest},fixture\n",
            encoding="utf-8",
        )
        return export

    def _add_cover_asset(
        self,
        *,
        repo_root: Path,
        status: str = "✅成品",
    ) -> Path:
        content = b"localized cover pdf"
        export = repo_root / "docs" / "renderers" / "latex" / "assets" / "cover-en.pdf"
        export.parent.mkdir(parents=True, exist_ok=True)
        export.write_bytes(content)
        digest = hashlib.sha256(content).hexdigest()
        (repo_root / "data" / "asset_registry.csv").write_text(
            self._REGISTRY_HEADER
            + f"page/cover,,整页PDF,按语言,{status},FALSE,M1,US,"
            f"docs/renderers/latex/assets,en,cover-en.pdf:{digest},fixture\n",
            encoding="utf-8",
        )
        return export

    def _add_dual_format_cover_asset(self, *, repo_root: Path) -> Path:
        export_dir = repo_root / "docs" / "renderers" / "latex" / "assets"
        export_dir.mkdir(parents=True, exist_ok=True)
        png = export_dir / "cover-en.png"
        pdf = export_dir / "cover-en.pdf"
        png.write_bytes(b"localized cover png")
        pdf.write_bytes(b"localized cover pdf")
        png_digest = hashlib.sha256(png.read_bytes()).hexdigest()
        pdf_digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
        (repo_root / "data" / "asset_registry.csv").write_text(
            self._REGISTRY_HEADER
            + "page/cover,,整页PDF,按语言,✅成品,FALSE,M1,US,"
            + "docs/renderers/latex/assets,en,"
            + f'"cover-en.png:{png_digest},cover-en.pdf:{pdf_digest}",fixture\n',
            encoding="utf-8",
        )
        return pdf

    def _add_target_aware_lcd_assets(self, *, repo_root: Path) -> tuple[Path, Path]:
        generic_dir = repo_root / "docs" / "assets" / "generic"
        targeted_dir = repo_root / "docs" / "renderers" / "latex" / "assets"
        generic_dir.mkdir(parents=True, exist_ok=True)
        targeted_dir.mkdir(parents=True, exist_ok=True)

        generic_png = generic_dir / "lcd_mode.png"
        generic_pdf = generic_dir / "lcd_mode.pdf"
        targeted_png = targeted_dir / "op_lcd_mode.png"
        targeted_pdf = targeted_dir / "op_lcd_mode.pdf"
        generic_png.write_bytes(b"generic lcd png")
        generic_pdf.write_bytes(b"generic lcd pdf")
        targeted_png.write_bytes(b"JE-1000F US lcd png")
        targeted_pdf.write_bytes(b"JE-1000F US lcd pdf")

        def digest(path: Path) -> str:
            return hashlib.sha256(path.read_bytes()).hexdigest()

        (repo_root / "data" / "asset_registry.csv").write_text(
            self._REGISTRY_HEADER
            + "operation/lcd_mode,,插图,中立,✅成品,FALSE,ALL,ALL,docs/assets/generic,,"
            + f'"lcd_mode.pdf:{digest(generic_pdf)},lcd_mode.png:{digest(generic_png)}",fixture\n'
            + "operation/je1000f_us/lcd_mode,operation/lcd_mode,插图,中立,✅成品,"
            + "FALSE,JE-1000F,US,docs/renderers/latex/assets,,"
            + f'"op_lcd_mode.pdf:{digest(targeted_pdf)},'
            + f'op_lcd_mode.png:{digest(targeted_png)}",fixture\n',
            encoding="utf-8",
        )
        return generic_png, targeted_png

    def _finalize(
        self,
        *,
        repo_root: Path,
        docs_dir: Path,
        bundle_dir: Path,
        stale_page: Path,
    ) -> MaterializedBundle:
        return finalize_materialized_bundle(
            self._materialized_bundle(
                docs_dir=docs_dir,
                bundle_dir=bundle_dir,
                stale_page=stale_page,
            ),
            cfg={"build": {"languages": ["en"]}},
            docs_dir=docs_dir,
            repo_root=repo_root,
        )

    def test_finalizer_recomputes_direct_pages_from_final_index(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo_root, docs_dir, bundle_dir = self._workspace(Path(td))
            page_dir = bundle_dir / "page"
            page_dir.mkdir()
            stale = page_dir / "stale.rst"
            stale.write_text("Stale\n=====\n", encoding="utf-8")
            final = page_dir / "final.rst"
            final.write_text("Final\n=====\n", encoding="utf-8")
            (bundle_dir / "index.rst").write_text(
                "Manual\n======\n\n.. include:: page/final.rst\n",
                encoding="utf-8",
            )

            finalized = self._finalize(
                repo_root=repo_root,
                docs_dir=docs_dir,
                bundle_dir=bundle_dir,
                stale_page=stale,
            )

            self.assertEqual((final.resolve(),), finalized.page_paths)
            self.assertNotIn(stale.resolve(), finalized.page_paths)
            manifest_text = finalized.manifest_path.read_text(encoding="utf-8")
            usage_text = finalized.asset_usage_manifest_path.read_text(encoding="utf-8")
            self.assertNotIn(str(repo_root.resolve()), manifest_text + usage_text)
            self.assertNotIn(str(bundle_dir.resolve()), manifest_text + usage_text)
            manifest = json.loads(manifest_text)
            self.assertEqual(["bundle://page/final.rst"], manifest["page_files"])
            self.assertEqual(
                [{"path": "page/final.rst", "sha256": manifest["page_file_records"][0]["sha256"]}],
                manifest["page_file_records"],
            )

    def test_nested_include_accounts_for_all_legacy_reference_forms(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo_root, docs_dir, bundle_dir = self._workspace(Path(td))
            asset_dir = docs_dir / "assets"
            asset_dir.mkdir()
            assets = {
                "image.png": b"image",
                "figure.jpg": b"figure",
                "substitution.svg": b"<svg/>",
                "double.jpeg": b"double",
                "single.pdf": b"single",
            }
            for name, content in assets.items():
                (asset_dir / name).write_bytes(content)

            page_dir = bundle_dir / "page"
            fragment_dir = page_dir / "fragments"
            fragment_dir.mkdir(parents=True)
            stale = page_dir / "stale.rst"
            stale.write_text("Stale\n=====\n", encoding="utf-8")
            final = page_dir / "final.rst"
            final.write_text(
                "Final\n=====\n\n.. include:: fragments/assets.rst\n",
                encoding="utf-8",
            )
            fragment = fragment_dir / "assets.rst"

            def relative(name: str) -> str:
                return Path(
                    os.path.relpath((asset_dir / name).resolve(), start=fragment_dir.resolve())
                ).as_posix()

            fragment.write_text(
                "\n".join(
                    [
                        f".. image:: {relative('image.png')}",
                        "",
                        f".. figure:: {relative('figure.jpg')}",
                        "",
                        f".. |brand| image:: {relative('substitution.svg')}",
                        "",
                        ".. raw:: html",
                        "",
                        f'   <img src="{relative("double.jpeg")}">',
                        f"   <img src='{relative('single.pdf')}'>",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            (bundle_dir / "index.rst").write_text(
                "Manual\n======\n\n.. include:: page/final.rst\n",
                encoding="utf-8",
            )

            finalized = self._finalize(
                repo_root=repo_root,
                docs_dir=docs_dir,
                bundle_dir=bundle_dir,
                stale_page=stale,
            )

            self.assertEqual((final.resolve(),), finalized.page_paths)
            usage_text = finalized.asset_usage_manifest_path.read_text(encoding="utf-8")
            bundle_manifest_text = finalized.manifest_path.read_text(encoding="utf-8")
            usage = json.loads(usage_text)
            self.assertEqual(5, len(usage["assets"]))
            self.assertEqual(
                ["legacy-path"] * 5,
                [row["reference_kind"] for row in usage["assets"]],
            )
            self.assertEqual(
                {"page/fragments/assets.rst"},
                {reference for row in usage["assets"] for reference in row["references"]},
            )
            self.assertEqual(
                sorted(f"docs/assets/{name}" for name in assets),
                sorted(row["source_path"] for row in usage["assets"]),
            )
            self.assertNotIn(str(repo_root.resolve()), usage_text + bundle_manifest_text)
            self.assertNotIn(str(bundle_dir.resolve()), usage_text + bundle_manifest_text)

            rewritten = fragment.read_text(encoding="utf-8")
            directive_paths = re.findall(
                r"^\s*\.\.\s+(?:\|[^|]+\|\s+)?(?:image|figure)::\s+(\S+)",
                rewritten,
                flags=re.MULTILINE,
            )
            html_paths = re.findall(r"\bsrc\s*=\s*(['\"])(.*?)\1", rewritten)
            self.assertEqual(3, len(directive_paths))
            self.assertEqual(2, len(html_paths))
            for rewritten_path in directive_paths:
                self.assertFalse(Path(rewritten_path).is_absolute())
                self.assertTrue((bundle_dir / rewritten_path).resolve().is_file())
                self.assertFalse((fragment.parent / rewritten_path).resolve().is_file())
            for _quote, rewritten_path in html_paths:
                self.assertFalse(Path(rewritten_path).is_absolute())
                self.assertTrue((bundle_dir / rewritten_path).resolve().is_file())
                self.assertFalse((fragment.parent / rewritten_path).resolve().is_file())
            rewrite_values = {
                row["rendered_value"]
                for row in usage["rewrites"]
                if row["original_value"] in {relative("double.jpeg"), relative("single.pdf")}
            }
            self.assertEqual({value for _quote, value in html_paths}, rewrite_values)
            self.assertRegex(rewritten, r'\bsrc="[^"]+"')
            self.assertRegex(rewritten, r"\bsrc='[^']+'")

    def test_finalizer_rejects_manifest_path_outside_bundle_before_writing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo_root, docs_dir, bundle_dir = self._workspace(Path(td))
            page_dir = bundle_dir / "page"
            page_dir.mkdir()
            page = page_dir / "plain.rst"
            page.write_text("Plain\n=====\n", encoding="utf-8")
            (bundle_dir / "index.rst").write_text(
                ".. include:: page/plain.rst\n",
                encoding="utf-8",
            )
            outside_manifest = Path(td) / "outside.json"
            outside_manifest.write_bytes(b"do not replace")
            bundle = replace(
                self._materialized_bundle(
                    docs_dir=docs_dir,
                    bundle_dir=bundle_dir,
                    stale_page=page,
                ),
                manifest_path=outside_manifest,
            )

            with self.assertRaisesRegex(AssetRegistryError, "manifest.*escapes"):
                finalize_materialized_bundle(
                    bundle,
                    cfg={"build": {"languages": ["en"]}},
                    docs_dir=docs_dir,
                    repo_root=repo_root,
                )

            self.assertEqual(b"do not replace", outside_manifest.read_bytes())
            self.assertFalse((bundle_dir / "asset_usage_manifest.json").exists())

    def test_finalizer_rejects_manifest_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo_root, docs_dir, bundle_dir = self._workspace(Path(td))
            page_dir = bundle_dir / "page"
            page_dir.mkdir()
            page = page_dir / "plain.rst"
            page.write_text("Plain\n=====\n", encoding="utf-8")
            (bundle_dir / "index.rst").write_text(
                ".. include:: page/plain.rst\n",
                encoding="utf-8",
            )
            outside_manifest = Path(td) / "outside.json"
            outside_manifest.write_bytes(b"do not replace")
            manifest_link = bundle_dir / "bundle_manifest.json"
            manifest_link.symlink_to(outside_manifest)
            bundle = replace(
                self._materialized_bundle(
                    docs_dir=docs_dir,
                    bundle_dir=bundle_dir,
                    stale_page=page,
                ),
                manifest_path=manifest_link,
            )

            with self.assertRaisesRegex(AssetRegistryError, "manifest.*symbolic link"):
                finalize_materialized_bundle(
                    bundle,
                    cfg={"build": {"languages": ["en"]}},
                    docs_dir=docs_dir,
                    repo_root=repo_root,
                )

            self.assertEqual(b"do not replace", outside_manifest.read_bytes())

    @unittest.skipUnless(
        Path("/System/Volumes/Data/Users").exists(),
        "APFS Data-volume alias is only available on macOS",
    )
    def test_finalizer_accepts_equivalent_apfs_manifest_path(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.home()) as td:
            repo_root, docs_dir, bundle_dir = self._workspace(Path(td))
            page_dir = bundle_dir / "page"
            page_dir.mkdir()
            page = page_dir / "plain.rst"
            page.write_text("Plain\n=====\n", encoding="utf-8")
            (bundle_dir / "index.rst").write_text(
                ".. include:: page/plain.rst\n",
                encoding="utf-8",
            )
            data_alias = Path("/System/Volumes/Data") / bundle_dir.relative_to("/")
            try:
                equivalent = data_alias.samefile(bundle_dir)
            except OSError:
                equivalent = False
            if not equivalent:
                self.skipTest("workspace path has no equivalent APFS Data-volume alias")
            bundle = replace(
                self._materialized_bundle(
                    docs_dir=docs_dir,
                    bundle_dir=bundle_dir,
                    stale_page=page,
                ),
                manifest_path=data_alias / "bundle_manifest.json",
            )

            finalized = finalize_materialized_bundle(
                bundle,
                cfg={"build": {"languages": ["en"]}},
                docs_dir=docs_dir,
                repo_root=repo_root,
            )

            self.assertTrue(finalized.manifest_path.samefile(bundle_dir / "bundle_manifest.json"))

    def test_bundle_local_relative_asset_is_accounted_outside_repo(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo_root, docs_dir, bundle_dir = self._workspace(Path(td))
            page_dir = bundle_dir / "page"
            media_dir = bundle_dir / "media"
            page_dir.mkdir()
            media_dir.mkdir()
            local_asset = media_dir / "local.png"
            local_asset.write_bytes(b"review overlay asset")
            stale = page_dir / "stale.rst"
            stale.write_text("Stale\n=====\n", encoding="utf-8")
            final = page_dir / "final.rst"
            final.write_text(
                "Final\n=====\n\n.. image:: ../media/local.png\n",
                encoding="utf-8",
            )
            (bundle_dir / "index.rst").write_text(
                "Manual\n======\n\n.. include:: page/final.rst\n",
                encoding="utf-8",
            )

            finalized = self._finalize(
                repo_root=repo_root,
                docs_dir=docs_dir,
                bundle_dir=bundle_dir,
                stale_page=stale,
            )

            usage_text = finalized.asset_usage_manifest_path.read_text(encoding="utf-8")
            usage = json.loads(usage_text)
            self.assertEqual(1, len(usage["assets"]))
            row = usage["assets"][0]
            self.assertEqual("legacy-path", row["reference_kind"])
            self.assertEqual("bundle/media/local.png", row["source_path"])
            self.assertEqual("media/local.png", row["staged_path"])
            self.assertEqual(["page/final.rst"], row["references"])
            self.assertNotIn(str(bundle_dir.resolve()), usage_text)
            rewritten = final.read_text(encoding="utf-8")
            self.assertIn(".. image:: media/local.png", rewritten)
            self.assertTrue((bundle_dir / "media/local.png").resolve().is_file())

    def test_absolute_local_asset_reference_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo_root, docs_dir, bundle_dir = self._workspace(Path(td))
            local_asset = docs_dir / "assets" / "absolute.png"
            local_asset.parent.mkdir(parents=True)
            local_asset.write_bytes(b"must not bypass accounting")
            page_dir = bundle_dir / "page"
            page_dir.mkdir()
            page = page_dir / "absolute.rst"
            page.write_text(
                f"Absolute\n========\n\n.. image:: {local_asset.resolve()}\n",
                encoding="utf-8",
            )
            (bundle_dir / "index.rst").write_text(
                "Manual\n======\n\n.. include:: page/absolute.rst\n",
                encoding="utf-8",
            )
            stale = page_dir / "stale.rst"
            stale.write_text("Stale\n", encoding="utf-8")

            with self.assertRaisesRegex(AssetRegistryError, "absolute local path"):
                self._finalize(
                    repo_root=repo_root,
                    docs_dir=docs_dir,
                    bundle_dir=bundle_dir,
                    stale_page=stale,
                )

            self.assertFalse((bundle_dir / "asset_usage_manifest.json").exists())

    def test_latex_include_pdf_uses_registry_gate_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo_root, docs_dir, bundle_dir = self._workspace(Path(td))
            export = self._add_cover_asset(repo_root=repo_root)
            page_dir = bundle_dir / "page"
            page_dir.mkdir()
            page = page_dir / "cover-en.rst"
            page.write_text(
                ".. raw:: latex\n\n"
                "   \\includepdf[pages=1-]{asset:page/cover}\n",
                encoding="utf-8",
            )
            (bundle_dir / "index.rst").write_text(
                "Manual\n======\n\n.. include:: page/cover-en.rst\n",
                encoding="utf-8",
            )
            stale = page_dir / "stale.rst"
            stale.write_text("Stale\n", encoding="utf-8")

            finalized = self._finalize(
                repo_root=repo_root,
                docs_dir=docs_dir,
                bundle_dir=bundle_dir,
                stale_page=stale,
            )

            usage = json.loads(finalized.asset_usage_manifest_path.read_text(encoding="utf-8"))
            row = usage["assets"][0]
            self.assertEqual("page/cover", row["asset_key"])
            self.assertEqual("registry-uri", row["reference_kind"])
            self.assertEqual("renderers/latex/assets/cover-en.pdf", row["staged_path"])
            self.assertEqual(hashlib.sha256(export.read_bytes()).hexdigest(), row["sha256"])
            self.assertIn("{cover-en.pdf}", page.read_text(encoding="utf-8"))
            self.assertEqual("cover-en.pdf", usage["rewrites"][0]["rendered_value"])

    def test_latex_include_pdf_rejects_quarantined_registry_asset(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo_root, docs_dir, bundle_dir = self._workspace(Path(td))
            self._add_cover_asset(repo_root=repo_root, status="⛔隔离")
            page_dir = bundle_dir / "page"
            page_dir.mkdir()
            page = page_dir / "cover-en.rst"
            page.write_text(
                ".. raw:: latex\n\n   \\includepdf{asset:page/cover}\n",
                encoding="utf-8",
            )
            (bundle_dir / "index.rst").write_text(
                "Manual\n======\n\n.. include:: page/cover-en.rst\n",
                encoding="utf-8",
            )
            stale = page_dir / "stale.rst"
            stale.write_text("Stale\n", encoding="utf-8")

            with self.assertRaisesRegex(AssetRegistryError, "⛔隔离"):
                self._finalize(
                    repo_root=repo_root,
                    docs_dir=docs_dir,
                    bundle_dir=bundle_dir,
                    stale_page=stale,
                )

    def test_latex_include_pdf_requires_pdf_when_registry_has_png_first(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo_root, docs_dir, bundle_dir = self._workspace(Path(td))
            pdf = self._add_dual_format_cover_asset(repo_root=repo_root)
            page_dir = bundle_dir / "page"
            page_dir.mkdir()
            page = page_dir / "cover-en.rst"
            page.write_text(
                ".. raw:: latex\n\n   \\includepdf{asset:page/cover}\n",
                encoding="utf-8",
            )
            (bundle_dir / "index.rst").write_text(
                "Manual\n======\n\n.. include:: page/cover-en.rst\n",
                encoding="utf-8",
            )
            stale = page_dir / "stale.rst"
            stale.write_text("Stale\n", encoding="utf-8")

            finalized = self._finalize(
                repo_root=repo_root,
                docs_dir=docs_dir,
                bundle_dir=bundle_dir,
                stale_page=stale,
            )

            usage = json.loads(finalized.asset_usage_manifest_path.read_text(encoding="utf-8"))
            row = usage["assets"][0]
            self.assertEqual("pdf", row["format"])
            self.assertEqual("renderers/latex/assets/cover-en.pdf", row["staged_path"])
            self.assertEqual(hashlib.sha256(pdf.read_bytes()).hexdigest(), row["sha256"])
            self.assertIn("{cover-en.pdf}", page.read_text(encoding="utf-8"))
            self.assertFalse(
                (bundle_dir / "renderers" / "latex" / "assets" / "cover-en.png").exists()
            )

    def test_lcd_mode_table_uses_target_png_and_generic_region_fallback(self) -> None:
        cases = (
            (
                "US",
                "en",
                "operation/je1000f_us/lcd_mode",
                "op_lcd_mode.png",
                "renderers/latex/assets/op_lcd_mode.png",
            ),
            (
                "JP",
                "ja",
                "operation/lcd_mode",
                "lcd_mode.png",
                "_assets/assets/generic/lcd_mode.png",
            ),
            (
                "EU",
                "en",
                "operation/lcd_mode",
                "lcd_mode.png",
                "_assets/assets/generic/lcd_mode.png",
            ),
        )
        for region, language, expected_key, expected_name, staged_path in cases:
            with self.subTest(region=region), tempfile.TemporaryDirectory() as td:
                repo_root, docs_dir, bundle_dir = self._workspace(Path(td))
                generic_png, targeted_png = self._add_target_aware_lcd_assets(
                    repo_root=repo_root
                )
                page_dir = bundle_dir / "page"
                page_dir.mkdir()
                page = page_dir / f"lcd_{language}.rst"
                page.write_text(
                    ".. raw:: latex\n\n"
                    "   \\begin{HBLcdModeTable}{asset:operation/lcd_mode}\n"
                    "   \\end{HBLcdModeTable}\n",
                    encoding="utf-8",
                )
                legacy_draft = bundle_dir / "generated" / "draft" / "lcd.rst"
                legacy_draft.parent.mkdir(parents=True)
                legacy_draft.write_text(
                    ".. raw:: latex\n\n"
                    "   \\begin{HBLcdModeTable}{lcd_mode.png}\n"
                    "   \\end{HBLcdModeTable}\n",
                    encoding="utf-8",
                )
                (bundle_dir / "index.rst").write_text(
                    f".. include:: page/{page.name}\n",
                    encoding="utf-8",
                )
                stale = page_dir / "stale.rst"
                stale.write_text("Stale\n", encoding="utf-8")
                bundle = replace(
                    self._materialized_bundle(
                        docs_dir=docs_dir,
                        bundle_dir=bundle_dir,
                        stale_page=stale,
                        lang=language,
                    ),
                    model="JE-1000F",
                    region=region,
                )

                finalized = finalize_materialized_bundle(
                    bundle,
                    cfg={"build": {"languages": [language]}},
                    docs_dir=docs_dir,
                    repo_root=repo_root,
                )

                usage = json.loads(
                    finalized.asset_usage_manifest_path.read_text(encoding="utf-8")
                )
                row = usage["assets"][0]
                expected_source = targeted_png if region == "US" else generic_png
                self.assertEqual(expected_key, row["asset_key"])
                self.assertEqual("png", row["format"])
                self.assertEqual(staged_path, row["staged_path"])
                self.assertEqual(
                    hashlib.sha256(expected_source.read_bytes()).hexdigest(),
                    row["sha256"],
                )
                self.assertIn(
                    f"\\begin{{HBLcdModeTable}}{{{expected_name}}}",
                    page.read_text(encoding="utf-8"),
                )
                self.assertIn(
                    "\\begin{HBLcdModeTable}{lcd_mode.png}",
                    legacy_draft.read_text(encoding="utf-8"),
                )
                self.assertEqual(
                    "asset:operation/lcd_mode",
                    usage["rewrites"][0]["original_value"],
                )
                self.assertEqual(expected_name, usage["rewrites"][0]["rendered_value"])
                self.assertFalse((bundle_dir / Path(staged_path).with_suffix(".pdf")).exists())

                second = finalize_materialized_bundle(
                    finalized,
                    cfg={"build": {"languages": [language]}},
                    docs_dir=docs_dir,
                    repo_root=repo_root,
                )
                second_usage = json.loads(
                    second.asset_usage_manifest_path.read_text(encoding="utf-8")
                )
                self.assertEqual(usage, second_usage)

    def test_support_tree_rejects_symlink_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo_root, docs_dir, bundle_dir = self._workspace(Path(td))
            page_dir = bundle_dir / "page"
            page_dir.mkdir()
            page = page_dir / "plain.rst"
            page.write_text("Plain\n=====\n", encoding="utf-8")
            (bundle_dir / "index.rst").write_text(
                "Manual\n======\n\n.. include:: page/plain.rst\n",
                encoding="utf-8",
            )
            stale = page_dir / "stale.rst"
            stale.write_text("Stale\n", encoding="utf-8")
            outside = Path(td) / "outside.png"
            outside.write_bytes(b"outside")
            support = bundle_dir / "_static"
            support.mkdir()
            (support / "alias.png").symlink_to(outside)

            with self.assertRaisesRegex(AssetRegistryError, "symbolic links"):
                self._finalize(
                    repo_root=repo_root,
                    docs_dir=docs_dir,
                    bundle_dir=bundle_dir,
                    stale_page=stale,
                )

    def test_finalizer_is_idempotent_for_registry_uri_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo_root, docs_dir, bundle_dir = self._workspace(Path(td))
            self._add_registry_asset(repo_root=repo_root)
            page_dir = bundle_dir / "page"
            page_dir.mkdir()
            page = page_dir / "managed.rst"
            page.write_text("Managed\n=======\n\n.. image:: asset:demo/managed\n", encoding="utf-8")
            (bundle_dir / "index.rst").write_text(
                "Manual\n======\n\n.. include:: page/managed.rst\n",
                encoding="utf-8",
            )
            stale = page_dir / "stale.rst"
            stale.write_text("Stale\n", encoding="utf-8")

            first = self._finalize(
                repo_root=repo_root,
                docs_dir=docs_dir,
                bundle_dir=bundle_dir,
                stale_page=stale,
            )
            first_manifest = json.loads(first.asset_usage_manifest_path.read_text(encoding="utf-8"))
            first_bundle_hash = json.loads(first.manifest_path.read_text(encoding="utf-8"))[
                "bundle_sha256"
            ]
            second = finalize_materialized_bundle(
                first,
                cfg={"build": {"languages": ["en"]}},
                docs_dir=docs_dir,
                repo_root=repo_root,
            )
            second_manifest = json.loads(
                second.asset_usage_manifest_path.read_text(encoding="utf-8")
            )
            second_bundle_hash = json.loads(second.manifest_path.read_text(encoding="utf-8"))[
                "bundle_sha256"
            ]

            self.assertEqual("registry-uri", first_manifest["assets"][0]["reference_kind"])
            self.assertEqual(first_manifest, second_manifest)
            self.assertEqual(first_bundle_hash, second_bundle_hash)
            self.assertIn("_assets/assets/managed.png", page.read_text(encoding="utf-8"))

    def test_explicit_review_override_keeps_asset_key_and_override_hash(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo_root, docs_dir, bundle_dir = self._workspace(Path(td))
            registry_export = self._add_registry_asset(repo_root=repo_root)
            page_dir = bundle_dir / "page"
            page_dir.mkdir()
            page = page_dir / "managed.rst"
            page.write_text("Managed\n=======\n\n.. image:: asset:demo/managed\n", encoding="utf-8")
            (bundle_dir / "index.rst").write_text(
                "Manual\n======\n\n.. include:: page/managed.rst\n",
                encoding="utf-8",
            )
            stale = page_dir / "stale.rst"
            stale.write_text("Stale\n", encoding="utf-8")
            override_root = Path(td) / "review" / "overrides"
            override = override_root / "_assets" / "assets" / "managed.png"
            override.parent.mkdir(parents=True)
            override.write_bytes(b"review override")
            staged = bundle_dir / "_assets" / "assets" / "managed.png"
            staged.parent.mkdir(parents=True)
            staged.write_bytes(override.read_bytes())

            finalized = finalize_materialized_bundle(
                self._materialized_bundle(
                    docs_dir=docs_dir,
                    bundle_dir=bundle_dir,
                    stale_page=stale,
                ),
                cfg={"build": {"languages": ["en"]}},
                docs_dir=docs_dir,
                repo_root=repo_root,
                asset_override_root=override_root,
            )

            usage = json.loads(finalized.asset_usage_manifest_path.read_text(encoding="utf-8"))
            row = usage["assets"][0]
            self.assertEqual("demo/managed", row["asset_key"])
            self.assertEqual("review-override", row["reference_kind"])
            self.assertEqual(hashlib.sha256(override.read_bytes()).hexdigest(), row["sha256"])
            self.assertEqual(
                hashlib.sha256(registry_export.read_bytes()).hexdigest(),
                row["registry_export_sha256"],
            )
            self.assertEqual("review-override", row["status"])
            self.assertEqual("asset:demo/managed", usage["rewrites"][0]["original_value"])

    def test_bundle_hash_tracks_rst_closure_config_and_support_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo_root, docs_dir, bundle_dir = self._workspace(Path(td))
            page_dir = bundle_dir / "page"
            fragment_dir = page_dir / "fragments"
            fragment_dir.mkdir(parents=True)
            stale = page_dir / "stale.rst"
            stale.write_text("Stale\n", encoding="utf-8")
            final = page_dir / "final.rst"
            final.write_text("Final\n=====\n\n.. include:: fragments/detail.rst\n", encoding="utf-8")
            fragment = fragment_dir / "detail.rst"
            fragment.write_text("Detail one\n", encoding="utf-8")
            (bundle_dir / "index.rst").write_text(
                "Manual one\n==========\n\n.. include:: page/final.rst\n",
                encoding="utf-8",
            )
            (bundle_dir / "conf.py").write_text("project = 'one'\n", encoding="utf-8")
            (bundle_dir / "conf_base.py").write_text("extensions = []\n", encoding="utf-8")
            static = bundle_dir / "_static" / "style.css"
            static.parent.mkdir()
            static.write_text("body { color: black; }\n", encoding="utf-8")
            stale_generated = bundle_dir / "generated" / "stale.rst"
            stale_generated.parent.mkdir()
            stale_generated.write_text("not included\n", encoding="utf-8")

            bundle = self._materialized_bundle(
                docs_dir=docs_dir,
                bundle_dir=bundle_dir,
                stale_page=stale,
            )
            hashes: list[str] = []
            for mutate in (
                lambda: None,
                lambda: fragment.write_text("Detail two\n", encoding="utf-8"),
                lambda: (bundle_dir / "index.rst").write_text(
                    "Manual two\n==========\n\n.. include:: page/final.rst\n",
                    encoding="utf-8",
                ),
                lambda: static.write_text("body { color: orange; }\n", encoding="utf-8"),
                lambda: stale_generated.write_text("still not included\n", encoding="utf-8"),
            ):
                mutate()
                bundle = finalize_materialized_bundle(
                    bundle,
                    cfg={"build": {"languages": ["en"]}},
                    docs_dir=docs_dir,
                    repo_root=repo_root,
                )
                manifest = json.loads(bundle.manifest_path.read_text(encoding="utf-8"))
                hashes.append(manifest["bundle_sha256"])

            self.assertEqual(5, len(set(hashes)))
            manifest = json.loads(bundle.manifest_path.read_text(encoding="utf-8"))
            rst_paths = {row["path"] for row in manifest["rst_file_records"]}
            self.assertIn("index.rst", rst_paths)
            self.assertIn("page/fragments/detail.rst", rst_paths)
            self.assertNotIn("generated/stale.rst", rst_paths)
            self.assertEqual(
                ["generated/stale.rst"],
                [row["path"] for row in manifest["generated_file_records"]],
            )
            self.assertEqual(
                {"conf.py", "conf_base.py"},
                {row["path"] for row in manifest["config_file_records"]},
            )
            self.assertIn(
                "_static/style.css",
                {row["path"] for row in manifest["support_file_records"]},
            )

    def test_nested_include_inherits_language_and_rejects_conflicting_contexts(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo_root, docs_dir, bundle_dir = self._workspace(Path(td))
            export_dir = repo_root / "docs" / "assets"
            export_dir.mkdir(parents=True)
            hashes: list[str] = []
            for lang, content in (("en", b"english"), ("es", b"spanish")):
                path = export_dir / f"localized-{lang}.png"
                path.write_bytes(content)
                hashes.append(f"{path.name}:{hashlib.sha256(content).hexdigest()}")
            (repo_root / "data" / "asset_registry.csv").write_text(
                self._REGISTRY_HEADER
                + "demo/localized,,插图,按语言,✅成品,FALSE,M1,US,docs/assets,"
                + f'"en,es","{",".join(hashes)}",fixture\n',
                encoding="utf-8",
            )
            page_dir = bundle_dir / "page"
            fragment_dir = page_dir / "fragments"
            fragment_dir.mkdir(parents=True)
            stale = page_dir / "stale.rst"
            stale.write_text("Stale\n", encoding="utf-8")
            fragment = fragment_dir / "shared.rst"
            fragment.write_text(".. image:: asset:demo/localized\n", encoding="utf-8")
            page_en = page_dir / "manual_en.rst"
            page_en.write_text(".. include:: fragments/shared.rst\n", encoding="utf-8")
            (bundle_dir / "index.rst").write_text(
                ".. include:: page/manual_en.rst\n",
                encoding="utf-8",
            )
            bundle = self._materialized_bundle(
                docs_dir=docs_dir,
                bundle_dir=bundle_dir,
                stale_page=stale,
                lang=None,
            )

            finalized = finalize_materialized_bundle(
                bundle,
                cfg={"build": {"languages": ["en", "es"]}},
                docs_dir=docs_dir,
                repo_root=repo_root,
            )

            usage = json.loads(finalized.asset_usage_manifest_path.read_text(encoding="utf-8"))
            self.assertEqual("en", usage["assets"][0]["language"])
            self.assertIn(
                "_assets/assets/localized-en.png",
                fragment.read_text(encoding="utf-8"),
            )

            page_es = page_dir / "manual_es.rst"
            page_es.write_text(".. include:: fragments/shared.rst\n", encoding="utf-8")
            (bundle_dir / "index.rst").write_text(
                ".. include:: page/manual_en.rst\n\n.. include:: page/manual_es.rst\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(AssetRegistryError, "conflicting language contexts"):
                finalize_materialized_bundle(
                    finalized,
                    cfg={"build": {"languages": ["en", "es"]}},
                    docs_dir=docs_dir,
                    repo_root=repo_root,
                )


if __name__ == "__main__":
    unittest.main()
