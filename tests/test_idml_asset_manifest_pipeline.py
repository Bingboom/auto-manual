from __future__ import annotations

import hashlib
import html
import json
import re
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image

from tools.bundle_asset_finalize import finalize_materialized_bundle
from tools.bundle_asset_manifest import BundleAssetManifestError, resolve_manifest_asset
from tools.gen_index_bundle_models import MaterializedBundle
from tools.idml.asset_contracts import (
    APP_PAIRING_PANEL_ASSET_URI,
    is_je1000f_us_en_app_reference_page,
    requirements_for_page,
)
from tools.idml.components.base import RenderContext
from tools.idml.components.reference_figure import render_referencefigure
from tools.idml.delivery import build_delivery_package
from tools.idml.params import MIMETYPE


ROOT = Path(__file__).resolve().parents[1]
_IDPKG = "http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging"
_REGISTRY_HEADER = (
    "asset_key,override_for,类别,语言维度,状态,待无字化,适用机型,适用区域,"
    "导出物路径,语言变体,内容哈希,备注\n"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_usage_manifest_rows(
    bundle: Path,
    rows: list[dict[str, object]],
    *,
    schema_version: int = 2,
    target: dict[str, object] | None = None,
) -> None:
    (bundle / "asset_usage_manifest.json").write_text(
        json.dumps(
            {
                "assets": rows,
                "registry_snapshot": {},
                "rewrites": [],
                "schema_version": schema_version,
                "target": target
                or {"language": "en", "model": "JE-1000F", "region": "US"},
            }
        ),
        encoding="utf-8",
    )


def _write_usage_manifest(bundle: Path, row: dict[str, object]) -> None:
    _write_usage_manifest_rows(bundle, [row])


def _manifest_row(asset: Path, bundle: Path) -> dict[str, object]:
    return {
        "asset_key": "controls/je1000f_us/network_pairing_panel",
        "consumer": "idml-renderer",
        "format": "pdf",
        "reference_kind": "idml-component-contract",
        "sha256": _sha256(asset),
        "staged_path": asset.relative_to(bundle).as_posix(),
    }


def _write_idml(path: Path, uris: list[str]) -> None:
    rectangles = "".join(
        f'<Rectangle Self="r{index}"><Image Self="r{index}_img">'
        f'<Link Self="r{index}_lnk" '
        f'LinkResourceURI="{escape(uri, {chr(34): "&quot;"})}"/>'
        "</Image></Rectangle>"
        for index, uri in enumerate(uris)
    )
    story = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<idPkg:Story xmlns:idPkg="{_IDPKG}"><Story Self="s1">'
        f"{rectangles}</Story></idPkg:Story>\n"
    )
    designmap = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<Document xmlns:idPkg="{_IDPKG}" Self="doc">'
        '<idPkg:Story src="Stories/Story_s1.xml"/></Document>\n'
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            zipfile.ZipInfo("mimetype"),
            MIMETYPE,
            compress_type=zipfile.ZIP_STORED,
        )
        archive.writestr("designmap.xml", designmap)
        archive.writestr("Stories/Story_s1.xml", story)


class IdmlAssetManifestPipelineTests(unittest.TestCase):
    def test_app_reference_page_predicate_fails_closed(self) -> None:
        page = Path("page/12_app_setup_placeholder.rst")
        for language in ("en", "en-US", "en_US", "fr", "es"):
            with self.subTest(language=language):
                self.assertTrue(is_je1000f_us_en_app_reference_page(
                    page,
                    model="JE-1000F",
                    region="US",
                    language=language,
                ))

        excluded = (
            (page, "JE-1000F", "EU", "en"),
            (page, "OTHER", "US", "en"),
            (Path("page/p34_12_app_setup_placeholder.rst"), "JE-1000F", "US", "de"),
            (page, None, "US", "en"),
        )
        for page_path, model, region, language in excluded:
            with self.subTest(
                page=page_path,
                model=model,
                region=region,
                language=language,
            ):
                self.assertFalse(is_je1000f_us_en_app_reference_page(
                    page_path,
                    model=model,
                    region=region,
                    language=language,
                ))

    def test_requirement_covers_the_three_approved_us_app_languages(self) -> None:
        for language in ("en", "en-US", "en_US", "fr", "es"):
            with self.subTest(language=language):
                page = Path(
                    "page/p34_12_app_setup_placeholder.rst"
                    if language == "fr" else
                    "page/p50_12_app_setup_placeholder.rst"
                    if language == "es" else
                    "page/12_app_setup_placeholder.rst"
                )
                matched = requirements_for_page(
                    page,
                    model="JE-1000F",
                    region="US",
                    language=language,
                )
                self.assertEqual(
                    (APP_PAIRING_PANEL_ASSET_URI,),
                    tuple(row.asset_uri for row in matched),
                )

        excluded = (
            (Path("page/p34_12_app_setup_placeholder.rst"), "JE-1000F", "US", "de"),
            (Path("page/12_app_setup_placeholder.rst"), "JE-1000F", "EU", "en"),
            (Path("page/12_app_setup_placeholder.rst"), "OTHER", "US", "en"),
        )
        for page, model, region, language in excluded:
            with self.subTest(page=page, model=model, region=region, language=language):
                self.assertEqual(
                    (),
                    requirements_for_page(
                        page,
                        model=model,
                        region=region,
                        language=language,
                    ),
                )

    def test_app_asset_and_prose_consumers_share_the_exact_target_gate(self) -> None:
        from tools.idml.prose_flow import promote_reference_figures

        page = Path("page/12_app_setup_placeholder.rst")
        blocks = [
            ("image", "_assets/app/add_device_je1000f_us.png"),
            ("body", "Power\nAC\nDC / USB"),
        ]
        cases = (
            ("JE-1000F", "US", "en", True),
            ("JE-1000F", "US", "en-US", True),
            ("JE-1000F", "US", "en_US", True),
            ("JE-1000F", "US", "fr", True),
            ("JE-1000F", "US", "es", True),
            ("JE-1000F", "EU", "en", False),
            ("OTHER", "US", "en", False),
        )
        for model, region, language, expected in cases:
            with self.subTest(model=model, region=region, language=language):
                role_labels = {
                    "main_power": "Power",
                    "ac": "AC",
                    "dc_usb": "DC / USB",
                }
                language_code = language.lower().replace("_", "-").split("-", 1)[0]
                requirements = requirements_for_page(
                    page,
                    model=model,
                    region=region,
                    language=language,
                )
                plan = {
                    "plan_source": "approved-reference",
                    "approved_contract": {
                        "target": {
                            "model": model,
                            "region": region,
                            "languages": [language],
                        },
                        "idml_contract": {
                            "editable_components": {
                                "app_add_device": {
                                    "control_labels": {
                                        language_code: {
                                            "base_labels_by_role": role_labels,
                                            "render_labels_by_role": role_labels,
                                        },
                                    },
                                },
                            },
                        },
                    },
                    "pages": [{
                        "source_path": page.as_posix(),
                        "language": language,
                    }],
                }
                promoted = promote_reference_figures(
                    blocks,
                    plan,
                    page.stem,
                )
                uses_pairing_panel = any(
                    kind == "component"
                    and json.loads(payload).get("control_image")
                    == APP_PAIRING_PANEL_ASSET_URI
                    for kind, payload in promoted
                )
                self.assertEqual(expected, bool(requirements))
                self.assertEqual(bool(requirements), uses_pairing_panel)

        incomplete_plans = (
            {"plan_source": "approved-reference", "pages": None},
            {
                "plan_source": "approved-reference",
                "pages": [{
                    "source_path": page.as_posix(),
                    "language": "en",
                }],
            },
            {
                "plan_source": "approved-reference",
                "approved_contract": {
                    "target": {"model": "JE-1000F", "region": "US"},
                },
                "pages": [{"source_path": page.as_posix()}],
            },
        )
        for plan in incomplete_plans:
            with self.subTest(plan=plan):
                self.assertEqual(
                    blocks,
                    promote_reference_figures(blocks, plan, page.stem),
                )

    def test_finalizer_stages_and_records_pairing_panel_without_fake_rewrite(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            repo = root / "repo"
            docs = repo / "docs"
            bundle = root / "bundle"
            page_dir = bundle / "page"
            page_dir.mkdir(parents=True)
            asset = docs / "renderers" / "latex" / "assets" / "app_control_panel.pdf"
            asset.parent.mkdir(parents=True)
            asset.write_bytes(b"%PDF-1.4\nIDML pairing panel\n")
            registry = repo / "data" / "asset_registry.csv"
            registry.parent.mkdir(parents=True)
            registry.write_text(
                _REGISTRY_HEADER
                + "controls/je1000f_us/network_pairing_panel,,插图,中立,✅成品,"
                + "FALSE,JE-1000F,US,docs/renderers/latex/assets,,"
                + f"app_control_panel.pdf:{_sha256(asset)},fixture\n",
                encoding="utf-8",
            )
            page = page_dir / "12_app_setup_placeholder.rst"
            page.write_text(
                ".. raw:: latex\n\n   \\HBApplyLang{en}\n\nAPP SETUP\n=========\n",
                encoding="utf-8",
            )
            index = bundle / "index.rst"
            index.write_text(
                ".. include:: page/12_app_setup_placeholder.rst\n",
                encoding="utf-8",
            )
            materialized = MaterializedBundle(
                bundle_dir=bundle,
                page_dir=page_dir,
                index_path=index,
                conf_path=bundle / "conf.py",
                conf_base_path=bundle / "conf_base.py",
                wrapper_index_path=docs / "index.rst",
                page_paths=(page,),
                title="fixture",
                reference_doc=None,
                model="JE-1000F",
                region="US",
                lang=None,
                manifest_path=bundle / "bundle_manifest.json",
            )

            finalized = finalize_materialized_bundle(
                materialized,
                cfg={"build": {"languages": ["en", "fr", "es"]}},
                docs_dir=docs,
                repo_root=repo,
            )

            staged = bundle / "renderers" / "latex" / "assets" / asset.name
            self.assertEqual(asset.read_bytes(), staged.read_bytes())
            usage = json.loads(
                finalized.asset_usage_manifest_path.read_text(encoding="utf-8")
            )
            self.assertEqual([], usage["rewrites"])
            self.assertEqual(1, len(usage["assets"]))
            row = usage["assets"][0]
            self.assertEqual(
                "controls/je1000f_us/network_pairing_panel",
                row["asset_key"],
            )
            self.assertEqual("idml-renderer", row["consumer"])
            self.assertEqual("idml-component-contract", row["reference_kind"])
            self.assertEqual("pdf", row["format"])
            self.assertEqual(
                "renderers/latex/assets/app_control_panel.pdf",
                row["staged_path"],
            )
            self.assertEqual(["page/12_app_setup_placeholder.rst"], row["references"])
            self.assertEqual(
                staged.resolve(),
                resolve_manifest_asset(
                    bundle,
                    APP_PAIRING_PANEL_ASSET_URI,
                    format_name="pdf",
                    consumer="idml-renderer",
                    reference_kind="idml-component-contract",
                    model="JE-1000F",
                    region="US",
                    language="en",
                ),
            )

    def test_manifest_lookup_prefers_idml_consumer_and_keeps_single_row_compatibility(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as td:
            bundle = Path(td)
            rst_asset = bundle / "rst-panel.pdf"
            idml_asset = bundle / "idml-panel.pdf"
            rst_asset.write_bytes(b"RST consumer")
            idml_asset.write_bytes(b"IDML consumer")
            idml_row = _manifest_row(idml_asset, bundle)
            rst_row = {
                **_manifest_row(rst_asset, bundle),
                "consumer": "bundle",
                "reference_kind": "registry-uri",
            }

            for rows in ([rst_row, idml_row], [idml_row, rst_row]):
                with self.subTest(order=tuple(row["consumer"] for row in rows)):
                    _write_usage_manifest_rows(bundle, rows)
                    self.assertEqual(
                        idml_asset.resolve(),
                        resolve_manifest_asset(
                            bundle,
                            APP_PAIRING_PANEL_ASSET_URI,
                            format_name="pdf",
                            consumer="idml-renderer",
                            reference_kind="idml-component-contract",
                            model="JE-1000F",
                            region="US",
                            language="en",
                        ),
                    )
                    with self.assertRaisesRegex(
                        BundleAssetManifestError,
                        "ambiguous resolved asset",
                    ):
                        resolve_manifest_asset(
                            bundle,
                            APP_PAIRING_PANEL_ASSET_URI,
                            format_name="pdf",
                        )

            legacy_row = dict(idml_row)
            legacy_row.pop("consumer")
            legacy_row.pop("reference_kind")
            _write_usage_manifest(bundle, legacy_row)
            self.assertEqual(
                idml_asset.resolve(),
                resolve_manifest_asset(
                    bundle,
                    APP_PAIRING_PANEL_ASSET_URI,
                    format_name="pdf",
                    consumer="idml-renderer",
                    reference_kind="idml-component-contract",
                    model="JE-1000F",
                    region="US",
                    language="en",
                ),
            )

    def test_idml_contract_rejects_wrong_schema_target_format_and_consumer(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            bundle = Path(td)
            asset = bundle / "panel.pdf"
            asset.write_bytes(b"governed panel")
            row = _manifest_row(asset, bundle)
            lookup = {
                "format_name": "pdf",
                "consumer": "idml-renderer",
                "reference_kind": "idml-component-contract",
                "model": "JE-1000F",
                "region": "US",
                "language": "en",
            }

            wrong_consumer = {**row, "consumer": "bundle"}
            _write_usage_manifest(bundle, wrong_consumer)
            with self.assertRaisesRegex(
                BundleAssetManifestError,
                "no preferred resolved asset",
            ):
                resolve_manifest_asset(bundle, APP_PAIRING_PANEL_ASSET_URI, **lookup)

            wrong_reference = {**row, "reference_kind": "registry-uri"}
            _write_usage_manifest(bundle, wrong_reference)
            with self.assertRaisesRegex(
                BundleAssetManifestError,
                "no preferred resolved asset",
            ):
                resolve_manifest_asset(bundle, APP_PAIRING_PANEL_ASSET_URI, **lookup)

            _write_usage_manifest_rows(bundle, [row], schema_version=99)
            with self.assertRaisesRegex(
                BundleAssetManifestError,
                "unsupported schema_version",
            ):
                resolve_manifest_asset(bundle, APP_PAIRING_PANEL_ASSET_URI, **lookup)

            wrong_targets = (
                ({"language": "en", "model": "OTHER", "region": "US"}, "model"),
                ({"language": "en", "model": "JE-1000F", "region": "EU"}, "region"),
                ({"language": "fr", "model": "JE-1000F", "region": "US"}, "language"),
            )
            for target, label in wrong_targets:
                with self.subTest(target=target):
                    _write_usage_manifest_rows(bundle, [row], target=target)
                    with self.assertRaisesRegex(
                        BundleAssetManifestError,
                        f"target {label} does not match",
                    ):
                        resolve_manifest_asset(
                            bundle,
                            APP_PAIRING_PANEL_ASSET_URI,
                            **lookup,
                        )

            png = bundle / "panel.png"
            png.write_bytes(b"not the declared PDF format")
            wrong_suffix = _manifest_row(png, bundle)
            _write_usage_manifest(bundle, wrong_suffix)
            with self.assertRaisesRegex(
                BundleAssetManifestError,
                "suffix does not match declared format",
            ):
                resolve_manifest_asset(bundle, APP_PAIRING_PANEL_ASSET_URI, **lookup)

    def test_manifest_lookup_rejects_escape_hash_mismatch_and_other_key(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle = root / "bundle"
            bundle.mkdir()
            asset = bundle / "app_control_panel.pdf"
            asset.write_bytes(b"panel")
            row = _manifest_row(asset, bundle)
            _write_usage_manifest(bundle, row)

            with self.assertRaisesRegex(BundleAssetManifestError, "no resolved asset"):
                resolve_manifest_asset(bundle, "asset:controls/not-this-panel")

            escaped = dict(row)
            escaped["staged_path"] = "../outside.pdf"
            _write_usage_manifest(bundle, escaped)
            with self.assertRaisesRegex(BundleAssetManifestError, "unsafe bundle path"):
                resolve_manifest_asset(bundle, APP_PAIRING_PANEL_ASSET_URI)

            _write_usage_manifest(bundle, row)
            asset.write_bytes(b"changed after manifest")
            with self.assertRaisesRegex(BundleAssetManifestError, "hash does not match"):
                resolve_manifest_asset(bundle, APP_PAIRING_PANEL_ASSET_URI)

            real_asset = bundle / "real-panel.pdf"
            linked_asset = bundle / "linked-panel.pdf"
            real_asset.write_bytes(b"real panel")
            linked_asset.symlink_to(real_asset)
            symlink_row = _manifest_row(real_asset, bundle)
            symlink_row["staged_path"] = linked_asset.name
            _write_usage_manifest(bundle, symlink_row)
            with self.assertRaisesRegex(BundleAssetManifestError, "symbolic link"):
                resolve_manifest_asset(bundle, APP_PAIRING_PANEL_ASSET_URI)

    def test_portable_delivery_contains_all_editable_app_composite_links(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle = root / "bundle"
            bundle.mkdir()
            download = bundle / "download.png"
            add_device = bundle / "add_device.png"
            connect_result = bundle / "connect_result.png"
            Image.new("RGB", (700, 160), "white").save(download)
            Image.new("RGB", (680, 601), "white").save(add_device)
            Image.new("RGB", (1046, 651), "white").save(connect_result)
            panel = bundle / "renderers" / "latex" / "assets" / "app_control_panel.pdf"
            panel.parent.mkdir(parents=True)
            panel.write_bytes(b"%PDF-1.4\npairing panel\n")
            rst_panel = bundle / "rst-consumer-panel.pdf"
            rst_panel.write_bytes(b"%PDF-1.4\nordinary RST consumer\n")
            rst_row = {
                **_manifest_row(rst_panel, bundle),
                "consumer": "bundle",
                "reference_kind": "registry-uri",
            }
            _write_usage_manifest_rows(
                bundle,
                [rst_row, _manifest_row(panel, bundle)],
            )

            stories: list[tuple[str, str]] = []

            def add_story(story_id: str, _title: str, parts: list[str]) -> str:
                stories.append((story_id, "".join(parts)))
                return story_id

            context = RenderContext(
                params={},
                page_w=368.79,
                m_l=28.35,
                m_r=28.35,
                root=ROOT,
                bundle_root=bundle,
                model="JE-1000F",
                region="US",
                language="en",
                add_story=add_story,
            )
            specs = (
                {
                    "kind": "referencefigure",
                    "layout": "app_download",
                    "image": download.name,
                    "copy": "Search in the store. Scan the QR code.",
                },
                {
                    "kind": "referencefigure",
                    "layout": "app_add_device",
                    "image": add_device.name,
                    "control_image": APP_PAIRING_PANEL_ASSET_URI,
                    "step_labels": ["2.1", "2.2"],
                    "labels": ["Power", "AC", "DC/USB"],
                },
                {
                    "kind": "referencefigure",
                    "layout": "app_connect_result",
                    "image": connect_result.name,
                    "step_labels": ["2.3", "2.4", "2.5"],
                    "reference_note": "Reference only.",
                },
            )
            rendered = "".join(
                render_referencefigure(
                    spec,
                    context,
                    tid=f"app_{index}",
                    terminal=True,
                )[0]
                for index, spec in enumerate(specs)
            )
            uris = [
                html.unescape(value)
                for value in re.findall(r'LinkResourceURI="([^"]+)"', rendered)
            ]
            expected_names = {
                "download_stores.png",
                "download_qr.png",
                "connect_result_screens.png",
                "app_control_panel.pdf",
            }
            self.assertTrue(expected_names.issubset({Path(uri).name for uri in uris}))

            production = root / "manual.idml"
            _write_idml(production, uris)
            handoff = root / "handoff"
            (handoff / "flow").mkdir(parents=True)
            delivery = build_delivery_package(
                production_idml=production,
                handoff_root=handoff,
                out_zip=root / "portable.zip",
            )

            self.assertEqual([], delivery.missing_links)
            with zipfile.ZipFile(delivery.zip_path) as archive:
                link_names = {
                    Path(name).name
                    for name in archive.namelist()
                    if name.startswith("Links/")
                }
            self.assertTrue(expected_names.issubset(link_names))
            self.assertNotIn(rst_panel.name, link_names)


if __name__ == "__main__":
    unittest.main()
