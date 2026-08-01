from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.web_composite_manifest import (
    WEB_COMPOSITE_MANIFEST_SCHEMA,
    WebCompositeEntry,
    WebCompositeManifest,
    WebCompositeManifestError,
    load_web_composite_manifest,
    manifest_json_text,
    stage_web_composite_snapshot,
)

ROOT = Path(__file__).resolve().parents[1]
COMMITTED_FIXTURE_ROOT = ROOT / "tests" / "fixtures" / "phase2"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _entry(
    *,
    locale: str = "en",
    content_sha256: str | None = None,
    path: str = "_attachments/web_composites/panel.png",
    model_scope: str = "JE-1000F",
    region_scope: str = "US",
) -> WebCompositeEntry:
    return WebCompositeEntry(
        asset_key="web-composite/demo",
        web_replace_key="demo.panel",
        model_scope=model_scope,
        region_scope=region_scope,
        locale=locale,
        source_page=8,
        content_sha256=content_sha256 or _sha256(b"panel"),
        path=path,
        format="png",
        source_fragment_sha256="a" * 64,
        definition_record_id="rec-definition",
        export_record_id=f"rec-{locale}",
    )


class WebCompositeManifestTests(unittest.TestCase):
    def test_committed_rtd_fixture_is_frozen_and_hash_complete(self) -> None:
        manifest = load_web_composite_manifest(
            COMMITTED_FIXTURE_ROOT / "web_composite_manifest.json"
        )

        self.assertEqual(25, len(manifest.entries))
        for entry in manifest.entries:
            with self.subTest(key=entry.web_replace_key, locale=entry.locale):
                self.assertTrue(entry.path.startswith("_attachments/web_composites/"))
                self.assertNotIn("repo://", entry.path)
                attachment = COMMITTED_FIXTURE_ROOT / entry.path
                self.assertTrue(attachment.is_file())
                self.assertEqual(entry.content_sha256, _sha256(attachment.read_bytes()))

    def test_manifest_round_trip_and_exact_locale_precedes_shared(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "web_composite_manifest.json"
            path.write_text(
                manifest_json_text((_entry(locale="shared"), _entry(locale="fr"))),
                encoding="utf-8",
            )

            manifest = load_web_composite_manifest(path)

            exact = manifest.resolve(
                web_replace_key="demo.panel",
                locale="fr",
                model="JE-1000F",
                region="US",
            )
            fallback = manifest.resolve(
                web_replace_key="demo.panel",
                locale="es",
                model="JE-1000F",
                region="US",
            )
            self.assertEqual("fr", exact.locale if exact else None)
            self.assertEqual("shared", fallback.locale if fallback else None)
            self.assertEqual(WEB_COMPOSITE_MANIFEST_SCHEMA, json.loads(path.read_text())["schema_version"])

    def test_resolver_rejects_ambiguous_approved_matches(self) -> None:
        manifest = WebCompositeManifest(
            entries=(_entry(locale="en"), _entry(locale="en")),
            source=Path("fixture.json"),
        )

        with self.assertRaisesRegex(WebCompositeManifestError, "multiple approved"):
            manifest.resolve(
                web_replace_key="demo.panel",
                locale="en",
                model="JE-1000F",
                region="US",
            )

    def test_target_scope_is_fail_closed_without_a_match(self) -> None:
        manifest = WebCompositeManifest(
            entries=(_entry(model_scope="JE-1000F", region_scope="US"),),
            source=Path("fixture.json"),
        )

        self.assertIsNone(
            manifest.resolve(
                web_replace_key="demo.panel",
                locale="en",
                model="JE-2000F",
                region="US",
            )
        )

    def test_staging_freezes_bytes_and_rewrites_manifest_path(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            snapshot = root / "snapshot"
            source = snapshot / "_attachments" / "web_composites" / "panel.png"
            source.parent.mkdir(parents=True)
            source.write_bytes(b"panel")
            source_manifest = snapshot / "web_composite_manifest.json"
            source_manifest.write_text(manifest_json_text((_entry(),)), encoding="utf-8")
            bundle = root / "bundle"

            staged_manifest = stage_web_composite_snapshot(
                source_manifest_path=source_manifest,
                snapshot_root=snapshot,
                bundle_root=bundle,
                model="JE-1000F",
                region="US",
            )

            self.assertEqual(bundle / "web_composite_manifest.json", staged_manifest)
            staged = load_web_composite_manifest(staged_manifest)
            self.assertEqual(1, len(staged.entries))
            staged_asset = bundle / staged.entries[0].path
            self.assertEqual(b"panel", staged_asset.read_bytes())
            self.assertTrue(staged.entries[0].path.startswith("_assets/web_composites/"))

    def test_staging_rejects_attachment_hash_drift(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            snapshot = root / "snapshot"
            source = snapshot / "_attachments" / "web_composites" / "panel.png"
            source.parent.mkdir(parents=True)
            source.write_bytes(b"changed")
            source_manifest = snapshot / "web_composite_manifest.json"
            source_manifest.write_text(manifest_json_text((_entry(),)), encoding="utf-8")

            with self.assertRaisesRegex(WebCompositeManifestError, "SHA-256 mismatch"):
                stage_web_composite_snapshot(
                    source_manifest_path=source_manifest,
                    snapshot_root=snapshot,
                    bundle_root=root / "bundle",
                    model="JE-1000F",
                    region="US",
                )

    def test_loader_rejects_invalid_source_fragment_hash(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "web_composite_manifest.json"
            payload = json.loads(manifest_json_text((_entry(),)))
            payload["entries"][0]["source_fragment_sha256"] = "not-a-hash"
            path.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(WebCompositeManifestError, "source_fragment_sha256"):
                load_web_composite_manifest(path)

    def test_loader_requires_source_fragment_hash(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "web_composite_manifest.json"
            payload = json.loads(manifest_json_text((_entry(),)))
            del payload["entries"][0]["source_fragment_sha256"]
            path.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(WebCompositeManifestError, "source_fragment_sha256"):
                load_web_composite_manifest(path)

    def test_staging_rejects_repo_static_asset_escape_hatch(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            snapshot = root / "snapshot"
            snapshot.mkdir()
            source_manifest = snapshot / "web_composite_manifest.json"
            source_manifest.write_text(
                manifest_json_text((_entry(path="repo://docs/static.png"),)),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(WebCompositeManifestError, "escapes or is missing"):
                stage_web_composite_snapshot(
                    source_manifest_path=source_manifest,
                    snapshot_root=snapshot,
                    bundle_root=root / "bundle",
                    model="JE-1000F",
                    region="US",
                )


if __name__ == "__main__":
    unittest.main()
