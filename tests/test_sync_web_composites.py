from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from tools.sync_web_composites import (
    build_web_composite_entries,
    sync_web_composites,
)
from tools.web_composite_manifest import WebCompositeManifestError


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class _Source:
    def __init__(
        self,
        *,
        records_by_table: dict[str, list[dict[str, object]]] | None = None,
        downloads: dict[str, bytes] | None = None,
    ) -> None:
        self.records_by_table = records_by_table or {}
        self.download_bytes = downloads or {}
        self.fetches: list[tuple[str, str, str | None]] = []
        self.downloads: list[tuple[str, Path, bool]] = []

    def fetch_records_with_ids(
        self,
        *,
        base_token: str,
        table_id: str,
        view_id: str | None,
    ) -> list[dict[str, object]]:
        self.fetches.append((base_token, table_id, view_id))
        return list(self.records_by_table[table_id])

    def fetch_records(
        self,
        *,
        base_token: str,
        table_id: str,
        view_id: str | None,
    ) -> list[dict[str, object]]:
        return self.fetch_records_with_ids(
            base_token=base_token,
            table_id=table_id,
            view_id=view_id,
        )

    def download_drive_file(
        self,
        *,
        file_token: str,
        output_path: Path,
        overwrite: bool = False,
    ) -> None:
        self.downloads.append((file_token, output_path, overwrite))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(self.download_bytes[file_token])


def _definition(
    *,
    asset_key: str = "web-composite/demo",
    web_replace_key: str = "demo.panel",
    language_dimension: str = "按语言",
    language_variants: str = "en,fr,es",
) -> dict[str, object]:
    return {
        "record_id": "rec-definition",
        "fields": {
            "asset_key": asset_key,
            "build_eligible": True,
            "gate_status": "approved",
            "language_dimension": language_dimension,
            "language_variants": language_variants,
            "model_scope": "JE-1000F",
            "region_scope": "US",
            "visual_review_required": False,
            "web_replace_key": web_replace_key,
        },
    }


def _export(
    *,
    locale: str = "en",
    use_web_locale: bool = False,
    content: bytes = b"panel",
    export_key: str | None = None,
    file_token: str | None = None,
    source_fragment_sha256: str = "a" * 64,
    build_eligible: bool = True,
    gate_status: str = "approved",
) -> dict[str, object]:
    token = file_token or f"file-{locale}"
    locale_fields = {"web_locale" if use_web_locale else "locale": locale}
    return {
        "record_id": f"rec-export-{locale}",
        "fields": {
            "artifact_kind": "web-composite",
            "asset_key": "web-composite/demo",
            "build_eligible": build_eligible,
            "content_sha256": _sha256(content),
            "export_file": [{"file_token": token, "name": f"panel-{locale}.png"}],
            "export_key": export_key or f"web-composite/demo/{locale}",
            "format": "png",
            "gate_status": gate_status,
            **locale_fields,
            "source_fragment_sha256": source_fragment_sha256,
            "source_page": 8,
            "visual_review_required": False,
        },
    }


class SyncWebCompositesTests(unittest.TestCase):
    def test_dedicated_web_locale_takes_precedence_over_legacy_locale(self) -> None:
        export = _export(locale="fr", use_web_locale=True)
        export["fields"]["locale"] = "en"

        entries = build_web_composite_entries(
            definition_records=[_definition()],
            export_records=[export],
            export_root=Path("unused"),
            source=_Source(),
            dry_run=True,
        )

        self.assertEqual("fr", entries[0].locale)

    def test_legacy_locale_remains_compatible(self) -> None:
        entries = build_web_composite_entries(
            definition_records=[_definition()],
            export_records=[_export(locale="es")],
            export_root=Path("unused"),
            source=_Source(),
            dry_run=True,
        )

        self.assertEqual("es", entries[0].locale)

    def test_approved_export_downloads_and_freezes_lineage(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            export_root = Path(td)
            source = _Source(downloads={"file-en": b"panel"})

            entries = build_web_composite_entries(
                definition_records=[_definition()],
                export_records=[_export()],
                export_root=export_root,
                source=source,
                dry_run=False,
            )

            self.assertEqual(1, len(entries))
            entry = entries[0]
            self.assertEqual("demo.panel", entry.web_replace_key)
            self.assertEqual("a" * 64, entry.source_fragment_sha256)
            self.assertEqual("rec-definition", entry.definition_record_id)
            self.assertEqual("rec-export-en", entry.export_record_id)
            self.assertEqual(b"panel", (export_root / entry.path).read_bytes())
            self.assertEqual("file-en", source.downloads[0][0])

    def test_unapproved_non_buildable_row_is_not_selected(self) -> None:
        entries = build_web_composite_entries(
            definition_records=[_definition()],
            export_records=[
                _export(build_eligible=False, gate_status="quarantine")
            ],
            export_root=Path("unused"),
            source=_Source(),
            dry_run=True,
        )

        self.assertEqual((), entries)

    def test_buildable_row_requires_approved_gate_and_one_attachment(self) -> None:
        with self.assertRaisesRegex(WebCompositeManifestError, "not approved"):
            build_web_composite_entries(
                definition_records=[_definition()],
                export_records=[_export(gate_status="quarantine")],
                export_root=Path("unused"),
                source=_Source(),
                dry_run=True,
            )

        missing = _export()
        missing["fields"]["export_file"] = []
        with self.assertRaisesRegex(WebCompositeManifestError, "exactly one"):
            build_web_composite_entries(
                definition_records=[_definition()],
                export_records=[missing],
                export_root=Path("unused"),
                source=_Source(),
                dry_run=True,
            )

    def test_duplicate_locale_and_invalid_source_hash_fail_closed(self) -> None:
        with self.assertRaisesRegex(WebCompositeManifestError, "multiple buildable"):
            build_web_composite_entries(
                definition_records=[_definition()],
                export_records=[_export(), _export(export_key="duplicate")],
                export_root=Path("unused"),
                source=_Source(),
                dry_run=True,
            )

        with self.assertRaisesRegex(WebCompositeManifestError, "source_fragment_sha256"):
            build_web_composite_entries(
                definition_records=[_definition()],
                export_records=[_export(source_fragment_sha256="")],
                export_root=Path("unused"),
                source=_Source(),
                dry_run=True,
            )

        with self.assertRaisesRegex(WebCompositeManifestError, "source_fragment_sha256"):
            build_web_composite_entries(
                definition_records=[_definition()],
                export_records=[_export(source_fragment_sha256="bad")],
                export_root=Path("unused"),
                source=_Source(),
                dry_run=True,
            )

    def test_download_hash_mismatch_does_not_publish_partial_file(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            export_root = Path(td)
            source = _Source(downloads={"file-en": b"changed"})

            with self.assertRaisesRegex(WebCompositeManifestError, "expected"):
                build_web_composite_entries(
                    definition_records=[_definition()],
                    export_records=[_export(content=b"panel")],
                    export_root=export_root,
                    source=source,
                    dry_run=False,
                )

            published = list(
                (export_root / "_attachments" / "web_composites").glob("*.png")
            )
            self.assertEqual([], published)

    def test_neutral_definition_requires_shared_locale(self) -> None:
        with self.assertRaisesRegex(WebCompositeManifestError, "locale=shared"):
            build_web_composite_entries(
                definition_records=[
                    _definition(
                        language_dimension="中立",
                        language_variants="shared",
                    )
                ],
                export_records=[_export(locale="en")],
                export_root=Path("unused"),
                source=_Source(),
                dry_run=True,
            )

    def test_sync_uses_frozen_table_bindings_and_returns_manifest_write(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bindings = root / "data" / "asset_base_bindings.json"
            bindings.parent.mkdir()
            bindings.write_text(
                json.dumps(
                    {
                        "tables": {
                            "asset_definitions": {
                                "table_id": "tbl-definitions",
                                "default_view_id": "view-definitions",
                            },
                            "asset_exports": {
                                "table_id": "tbl-exports",
                                "default_view_id": "view-exports",
                            },
                        }
                    }
                ),
                encoding="utf-8",
            )
            source = _Source(
                records_by_table={
                    "tbl-definitions": [_definition()],
                    "tbl-exports": [_export()],
                },
                downloads={"file-en": b"panel"},
            )
            cfg = {
                "sync": {
                    "phase2": {
                        "base_token_env": "TEST_PHASE2_TOKEN",
                        "web_composites": {},
                    }
                }
            }

            with mock.patch.dict("os.environ", {"TEST_PHASE2_TOKEN": "base-token"}):
                result, write = sync_web_composites(
                    cfg,
                    source=source,
                    repo_root=root,
                    export_root=root / "snapshot",
                    dry_run=False,
                    generated_at="2026-08-01T00:00:00+00:00",
                    sha256_text=lambda text: _sha256(text.encode("utf-8")),
                    sha256_file=lambda _path: None,
                    result_cls=SimpleNamespace,
                )

            self.assertEqual("web_composite_manifest", result.logical_name)
            self.assertEqual(1, result.row_count)
            self.assertEqual(root / "snapshot" / "web_composite_manifest.json", write[0])
            self.assertEqual(
                [
                    ("base-token", "tbl-definitions", "view-definitions"),
                    ("base-token", "tbl-exports", "view-exports"),
                ],
                source.fetches,
            )


if __name__ == "__main__":
    unittest.main()
