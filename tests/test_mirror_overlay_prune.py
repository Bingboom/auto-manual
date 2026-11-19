"""Unit tests for tools.web.mirror_overlay_prune."""

from __future__ import annotations

import hashlib
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.web import external_source_store as store
from tools.web import mirror_overlay_prune as prune


def _write_pointer(
    path: Path,
    *,
    file_name: str,
    content: bytes = b"externalized-source-bytes",
    role: str = "asset_sources",
) -> str:
    sha = hashlib.sha256(content).hexdigest()
    payload = {
        "schema_version": store.POINTER_SCHEMA_VERSION,
        "storage_role": role,
        "file_name": file_name,
        "sha256": sha,
        "size_bytes": len(content),
        "feishu": {
            "table_id": store.ASSET_SOURCES_TABLE_ID,
            "record_id": "recAbcDef123456",
            "field_name": "source_file",
            "file_token": "boxcnTokenAbc123456789",
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return sha


class MirrorOverlayPruneTests(unittest.TestCase):
    def test_prunes_direct_pdf_ai_and_bin_when_pointer_exists_and_raw_is_absent(self) -> None:
        with TemporaryDirectory() as tmp:
            source = Path(tmp)
            _write_pointer(
                source / "manual_sources" / "MOD-1" / "US" / "manual.pdf.source-pointer.json",
                file_name="manual.pdf",
            )
            _write_pointer(
                source / "manual_sources" / "MOD-1" / "EU" / "设计稿 修正.ai.source-pointer.json",
                file_name="设计稿 修正.ai",
            )
            _write_pointer(
                source / "data" / "manual_sources" / "MOD-1" / "JP" / "chunk.bin.source-pointer.json",
                file_name="chunk.bin",
            )

            mirror_only = [
                "manual_sources/MOD-1/US/manual.pdf",
                "manual_sources/MOD-1/EU/设计稿 修正.ai",
                "data/manual_sources/MOD-1/JP/chunk.bin",
                "manual_sources/MOD-1/US/untracked-downstream.pdf",
                "reports/downstream-only.json",
            ]
            plan = prune.plan_prune(
                source,
                mirror_only,
                overlay_paths=("manual_sources", "data/manual_sources", "reports"),
            )
            self.assertEqual(
                plan.pruned_paths,
                (
                    "data/manual_sources/MOD-1/JP/chunk.bin",
                    "manual_sources/MOD-1/EU/设计稿 修正.ai",
                    "manual_sources/MOD-1/US/manual.pdf",
                ),
            )
            self.assertEqual(
                plan.kept_paths,
                (
                    "manual_sources/MOD-1/US/untracked-downstream.pdf",
                    "reports/downstream-only.json",
                ),
            )

    def test_prunes_multipart_bin_archive_via_manifest_and_pdf_identity(self) -> None:
        with TemporaryDirectory() as tmp:
            source = Path(tmp)
            # Case A: manifest.json holds original_source.archive_parts alongside .pdf.source-pointer.json.
            pkg_a = source / "data" / "manual_sources" / "MOD-A" / "US" / "en" / "v1"
            sha_a = _write_pointer(
                pkg_a / "source" / "pdf-archive" / "MOD-A_US.pdf.source-pointer.json",
                file_name="MOD-A_US.pdf",
                content=b"full-pdf-a",
            )
            (pkg_a / "manifest.json").write_text(
                json.dumps(
                    {
                        "original_source": {
                            "filename": "MOD-A_US.pdf",
                            "sha256": sha_a,
                            "archive_parts": [
                                {"path": "source/pdf-archive/part-001.bin", "size": 5},
                                {"path": "source/pdf-archive/part-002.bin", "size": 5},
                            ],
                        }
                    }
                ),
                encoding="utf-8",
            )

            # Case B: source_manifest.json holds original_source.source_pointer while
            # source/pdf-identity.json holds archive_parts (plus a non-externalized .gitattributes).
            pkg_b = source / "data" / "manual_sources" / "MOD-B" / "JP" / "ja" / "v2"
            sha_b = _write_pointer(
                pkg_b / "source" / "MOD-B_JP.pdf.source-pointer.json",
                file_name="MOD-B_JP.pdf",
                content=b"full-pdf-b",
            )
            (pkg_b / "source_manifest.json").write_text(
                json.dumps(
                    {
                        "original_source": {
                            "filename": "MOD-B_JP.pdf",
                            "sha256": sha_b,
                            "source_pointer": "source/MOD-B_JP.pdf.source-pointer.json",
                        }
                    }
                ),
                encoding="utf-8",
            )
            (pkg_b / "source" / "pdf-identity.json").write_text(
                json.dumps(
                    {
                        "filename": "MOD-B_JP.pdf",
                        "sha256": sha_b,
                        "archive_parts": [
                            {"path": "source/pdf-archive/part-0001.bin", "size": 4},
                            {"path": "source/pdf-archive/part-0002.bin", "size": 6},
                        ],
                    }
                ),
                encoding="utf-8",
            )

            # Case C: archive_parts in manifest.json WITHOUT any matching upstream pointer -> MUST NOT prune.
            pkg_c = source / "data" / "manual_sources" / "MOD-C" / "EU" / "en" / "v1"
            pkg_c.mkdir(parents=True)
            (pkg_c / "manifest.json").write_text(
                json.dumps(
                    {
                        "original_source": {
                            "filename": "MOD-C_EU.pdf",
                            "sha256": "a" * 64,
                            "archive_parts": [
                                {"path": "source/pdf-archive/part-001.bin", "size": 10},
                            ],
                        }
                    }
                ),
                encoding="utf-8",
            )

            mirror_only = [
                "data/manual_sources/MOD-A/US/en/v1/source/pdf-archive/part-001.bin",
                "data/manual_sources/MOD-A/US/en/v1/source/pdf-archive/part-002.bin",
                "data/manual_sources/MOD-B/JP/ja/v2/source/pdf-archive/.gitattributes",
                "data/manual_sources/MOD-B/JP/ja/v2/source/pdf-archive/part-0001.bin",
                "data/manual_sources/MOD-B/JP/ja/v2/source/pdf-archive/part-0002.bin",
                "data/manual_sources/MOD-C/EU/en/v1/source/pdf-archive/part-001.bin",
            ]
            plan = prune.plan_prune(
                source,
                mirror_only,
                overlay_paths=("manual_sources", "data/manual_sources"),
            )
            self.assertEqual(
                plan.pruned_paths,
                (
                    "data/manual_sources/MOD-A/US/en/v1/source/pdf-archive/part-001.bin",
                    "data/manual_sources/MOD-A/US/en/v1/source/pdf-archive/part-002.bin",
                    "data/manual_sources/MOD-B/JP/ja/v2/source/pdf-archive/part-0001.bin",
                    "data/manual_sources/MOD-B/JP/ja/v2/source/pdf-archive/part-0002.bin",
                ),
            )
            self.assertEqual(
                plan.kept_paths,
                (
                    "data/manual_sources/MOD-B/JP/ja/v2/source/pdf-archive/.gitattributes",
                    "data/manual_sources/MOD-C/EU/en/v1/source/pdf-archive/part-001.bin",
                ),
            )

    def test_never_prunes_files_still_present_upstream_or_with_invalid_pointer(self) -> None:
        with TemporaryDirectory() as tmp:
            source = Path(tmp)
            raw = source / "manual_sources" / "MOD-1" / "US" / "still-tracked.pdf"
            raw.parent.mkdir(parents=True)
            raw.write_bytes(b"%PDF-1.7")
            _write_pointer(
                source / "manual_sources" / "MOD-1" / "US" / "still-tracked.pdf.source-pointer.json",
                file_name="still-tracked.pdf",
                content=b"%PDF-1.7",
            )

            # Invalid pointer JSON (missing required fields / wrong schema_version) must NOT prune.
            bad_ptr = source / "manual_sources" / "MOD-1" / "US" / "bad.pdf.source-pointer.json"
            bad_ptr.write_text('{"schema_version": "broken"}', encoding="utf-8")

            ls_tree_input = (
                b"100644 blob " + b"0" * 40 + b"\tmanual_sources/MOD-1/US/still-tracked.pdf\0"
                b"100644 blob " + b"1" * 40 + b"\tmanual_sources/MOD-1/US/bad.pdf\0"
            )
            superseded = prune.collect_superseded_overlay_paths(source, ("manual_sources",))
            filtered, kept_count, pruned_count = prune.filter_nul_ls_tree(
                ls_tree_input, source, superseded
            )
            self.assertEqual(kept_count, 2)
            self.assertEqual(pruned_count, 0)
            self.assertEqual(filtered, ls_tree_input)

    def test_cli_filter_and_dry_run_json(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            _write_pointer(
                source / "manual_sources" / "MOD-1" / "US" / "manual.pdf.source-pointer.json",
                file_name="manual.pdf",
            )
            ls_tree_in = root / "in.lstree"
            ls_tree_out = root / "out.lstree"
            stats_file = root / "stats.txt"
            ls_tree_in.write_bytes(
                b"100644 blob " + b"a" * 40 + b"\tmanual_sources/MOD-1/US/manual.pdf\0"
                b"100644 blob " + b"b" * 40 + b"\tmanual_sources/MOD-1/US/notes.txt\0"
            )
            rc = prune.main(
                [
                    "filter-ls-tree",
                    "--source-root",
                    str(source),
                    "--overlay-paths",
                    "manual_sources data/manual_sources",
                    "--input",
                    str(ls_tree_in),
                    "--output",
                    str(ls_tree_out),
                    "--stats-file",
                    str(stats_file),
                ]
            )
            self.assertEqual(rc, 0)
            self.assertEqual(stats_file.read_text(encoding="utf-8"), "1 1\n")
            self.assertEqual(
                ls_tree_out.read_bytes(),
                b"100644 blob " + b"b" * 40 + b"\tmanual_sources/MOD-1/US/notes.txt\0",
            )

            tree_json = root / "mirror.json"
            tree_json.write_text(
                json.dumps(
                    {
                        "manual_sources": [
                            {"type": "blob", "path": "MOD-1/US/manual.pdf", "size": 1048576},
                            {"type": "blob", "path": "MOD-1/US/notes.txt", "size": 42},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = prune.main(
                    [
                        "dry-run",
                        "--source-root",
                        str(source),
                        "--overlay-paths",
                        "manual_sources",
                        "--mirror-tree-json",
                        str(tree_json),
                        "--json",
                    ]
                )
            self.assertEqual(rc, 0)
            summary = json.loads(buf.getvalue())
            self.assertEqual(summary["pruned_count"], 1)
            self.assertEqual(summary["pruned_bytes"], 1048576)
            self.assertEqual(summary["kept_paths"], ["manual_sources/MOD-1/US/notes.txt"])


if __name__ == "__main__":
    unittest.main()
