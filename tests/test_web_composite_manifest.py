from __future__ import annotations

import csv
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

        self.assertEqual(80, len(manifest.entries))
        for entry in manifest.entries:
            with self.subTest(key=entry.web_replace_key, locale=entry.locale):
                if entry.region_scope == "US":
                    self.assertTrue(entry.definition_record_id)
                    self.assertTrue(entry.export_record_id)
                self.assertTrue(entry.path.startswith("_attachments/web_composites/"))
                self.assertNotIn("repo://", entry.path)
                attachment = COMMITTED_FIXTURE_ROOT / entry.path
                self.assertTrue(attachment.is_file())
                self.assertEqual(entry.content_sha256, _sha256(attachment.read_bytes()))

        required_slots = {
            "product-overview.front",
            "product-overview.right",
            "operation.main-power",
            "operation.ac-output",
            "operation.dc-usb-output",
            "operation.energy-saving",
            "operation.led-light",
            "reference.charging-ac-wall",
            "reference.charging-solar-direct",
            "reference.charging-solar-adapter",
            "reference.charging-car",
        }
        eu_entries = [
            entry for entry in manifest.entries if entry.region_scope == "EU"
        ]
        self.assertEqual(55, len(eu_entries))
        self.assertEqual(
            {
                (locale, slot)
                for locale in ("en", "fr", "es", "de", "it")
                for slot in required_slots
            },
            {(entry.locale, entry.web_replace_key) for entry in eu_entries},
        )
        self.assertTrue(
            all(
                entry.asset_key
                == f"web-composite/je1000f_eu/{entry.web_replace_key}"
                for entry in eu_entries
            )
        )

    def test_eu_recipe_manifest_registry_and_source_pins_agree(self) -> None:
        recipe = json.loads(
            (
                ROOT
                / "data"
                / "asset_recipes"
                / "manual_je1000f_eu_web_panels.json"
            ).read_text(encoding="utf-8")
        )
        manifest = load_web_composite_manifest(
            COMMITTED_FIXTURE_ROOT / "web_composite_manifest.json"
        )
        with (ROOT / "data" / "asset_registry.csv").open(encoding="utf-8") as handle:
            registry = {row["asset_key"]: row for row in csv.DictReader(handle)}
        with (ROOT / "data" / "asset_sources.csv").open(encoding="utf-8") as handle:
            sources = {row["source_key"]: row for row in csv.DictReader(handle)}

        source = sources[recipe["source"]["source_key"]]
        self.assertEqual(recipe["source"]["expected_sha256"], source["sha256"])
        self.assertEqual(str(recipe["source"]["expected_page_count"]), source["page_count"])
        self.assertEqual(55, len(recipe["assets"]))

        manifest_entries = {
            (entry.asset_key, entry.locale): entry
            for entry in manifest.entries
            if entry.region_scope == "EU"
        }
        registry_keys: set[str] = set()
        for asset in recipe["assets"]:
            self.assertEqual("localized-full-page", asset["text_policy"])
            self.assertEqual("approved", asset["gate"]["status"])
            self.assertEqual(["crop"], [item["op"] for item in asset["transforms"]])
            self.assertEqual(1, len(asset["outputs"]))
            output = asset["outputs"][0]
            locale = asset["scope"]["locales"][0]
            registry_key = f"web-composite/je1000f_eu/{asset['asset_key'].rsplit('/', 1)[-1]}"
            entry = manifest_entries[(registry_key, locale)]
            self.assertEqual(output["expected_sha256"], entry.content_sha256)
            self.assertEqual(Path(output["path"]).name, Path(entry.path).name)
            self.assertEqual(asset["page"], entry.source_page)

            row = registry[registry_key]
            registry_keys.add(registry_key)
            self.assertEqual("JE-1000F", row["适用机型"])
            self.assertEqual("EU", row["适用区域"])
            self.assertEqual("en,fr,es,de,it", row["语言变体"])
            self.assertIn(
                f"{Path(entry.path).name}:{entry.content_sha256[:12]}",
                row["内容哈希"],
            )

        self.assertEqual(11, len(registry_keys))

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
