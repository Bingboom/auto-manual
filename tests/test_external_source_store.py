"""Unit tests for tools.web.external_source_store and inventory integration."""

from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools.web import external_source_store as store
from tools.web.package_inventory import collect_inventory, format_inventory_text


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _valid_pointer_dict(
    *,
    role: str = "asset_sources",
    table_id: str = store.ASSET_SOURCES_TABLE_ID,
    file_name: str = "master_art.ai",
    content: bytes = b"illustrator-bytes",
    file_token: str = "boxcnTokenAbc123456789",
) -> dict[str, object]:
    return {
        "schema_version": store.POINTER_SCHEMA_VERSION,
        "storage_role": role,
        "file_name": file_name,
        "sha256": _sha256_bytes(content),
        "size_bytes": len(content),
        "feishu": {
            "table_id": table_id,
            "record_id": "recAbcDef123456",
            "field_name": "source_file",
            "file_token": file_token,
        },
    }


def _run_cli(argv: list[str]) -> tuple[int, str, str]:
    out_buf = io.StringIO()
    err_buf = io.StringIO()
    with redirect_stdout(out_buf), redirect_stderr(err_buf):
        code = store.main(argv)
    return code, out_buf.getvalue(), err_buf.getvalue()


class PointerValidationTests(unittest.TestCase):
    def test_valid_asset_sources_and_published_docs_pointers_roundtrip(self) -> None:
        raw_asset = _valid_pointer_dict(role="asset_sources")
        raw_asset["local_relpath"] = "source/master_art.ai"
        raw_asset["source_key"] = "source/demo_master"
        raw_asset["notes"] = "Round-trip verified"
        ptr = store.validate_pointer_payload(raw_asset)
        self.assertEqual(ptr.storage_role, "asset_sources")
        self.assertEqual(ptr.feishu.table_id, store.ASSET_SOURCES_TABLE_ID)
        self.assertEqual(ptr.local_relpath, "source/master_art.ai")

        with tempfile.TemporaryDirectory() as tmp:
            pointer_file = Path(tmp) / f"master_art.ai{store.POINTER_SUFFIX}"
            store.write_pointer_file(pointer_file, ptr)
            text = pointer_file.read_text(encoding="utf-8")
            # Ensure file_token sits on its own standalone line for secret-scan compatibility.
            token_lines = [line.strip() for line in text.splitlines() if "file_token" in line]
            self.assertEqual(token_lines, ['"file_token": "boxcnTokenAbc123456789"'])
            reloaded = store.load_pointer_file(pointer_file)
            self.assertEqual(reloaded, ptr)

        raw_pub = _valid_pointer_dict(
            role="published_docs",
            table_id="tblPubDocs987654",
            file_name="shipped_manual.pdf",
        )
        pub_ptr = store.validate_pointer_payload(raw_pub)
        self.assertEqual(pub_ptr.storage_role, "published_docs")
        self.assertEqual(pub_ptr.feishu.table_id, "tblPubDocs987654")

    def test_asset_sources_enforces_canonical_table_id(self) -> None:
        bad = _valid_pointer_dict(role="asset_sources", table_id="tblWrongTable123")
        with self.assertRaisesRegex(ValueError, store.ASSET_SOURCES_TABLE_ID):
            store.validate_pointer_payload(bad)

    def test_rejects_embedded_credentials_and_base_tokens(self) -> None:
        for secret_key in ("base_token", "app_secret", "access_token", "webhook_secret"):
            top_bad = _valid_pointer_dict()
            top_bad[secret_key] = "leaked"
            with self.assertRaisesRegex(ValueError, "forbidden credential/base key"):
                store.validate_pointer_payload(top_bad)

            nested_bad = _valid_pointer_dict()
            assert isinstance(nested_bad["feishu"], dict)
            nested_bad["feishu"][secret_key] = "leaked"
            with self.assertRaisesRegex(ValueError, "forbidden credential/base key"):
                store.validate_pointer_payload(nested_bad)

    def test_rejects_traversal_bad_hash_and_invalid_sizes(self) -> None:
        for bad_name in ("../evil.ai", "sub/file.ai", "..", ""):
            payload = _valid_pointer_dict(file_name=bad_name)
            with self.assertRaises(ValueError):
                store.validate_pointer_payload(payload)

        bad_rel = _valid_pointer_dict()
        bad_rel["local_relpath"] = "../escape.ai"
        with self.assertRaisesRegex(ValueError, "local_relpath"):
            store.validate_pointer_payload(bad_rel)

        bad_sha = _valid_pointer_dict()
        bad_sha["sha256"] = "ABCDEF" + ("0" * 58)
        with self.assertRaisesRegex(ValueError, "sha256"):
            store.validate_pointer_payload(bad_sha)

        for bad_size in (0, -5, True):
            bad_sz = _valid_pointer_dict()
            bad_sz["size_bytes"] = bad_size
            with self.assertRaisesRegex(ValueError, "size_bytes"):
                store.validate_pointer_payload(bad_sz)


class RawBinaryRatchetTests(unittest.TestCase):
    def test_missing_baseline_exits_two(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            res = store.check_repository(Path(tmp), printer=lambda _: None)
            self.assertTrue(res.baseline_missing)
            self.assertEqual(res.exit_code, 2)

    def test_ratchet_blocks_new_ai_archive_bin_and_large_pdf_but_allows_small_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Small PDF <= 1 MiB is allowed without baseline entry.
            small_pdf = root / "docs" / "small_diagram.pdf"
            small_pdf.parent.mkdir(parents=True)
            small_pdf.write_bytes(b"%PDF-small" * 20)

            legacy_pdf = root / "manual_sources" / "MOD-1" / "US" / "source" / "legacy.pdf"
            legacy_pdf.parent.mkdir(parents=True)
            legacy_pdf.write_bytes(b"0" * (store.RAW_PDF_MAX_BYTES + 200))

            store.update_ratchet_baseline(root, seed_reason="legacy test baseline")
            ok = store.check_repository(root, printer=lambda _: None)
            self.assertEqual(ok.exit_code, 0)
            self.assertEqual(ok.baselined_count, 1)

            # 1. Tiny .ai is blocked regardless of size.
            tiny_ai = root / "docs" / "new_master.ai"
            tiny_ai.write_bytes(b"tiny-ai")
            # 2. Tiny .bin chunk under manual_sources/ is blocked regardless of size.
            chunk_bin = root / "manual_sources" / "MOD-1" / "US" / "source" / "part-001.bin"
            chunk_bin.write_bytes(b"chunk")
            # 3. >1 MiB PDF is blocked.
            big_pdf = root / "docs" / "huge.pdf"
            big_pdf.write_bytes(b"1" * (store.RAW_PDF_MAX_BYTES + 1))

            failed = store.check_repository(root, printer=lambda _: None)
            self.assertEqual(failed.exit_code, 1)
            self.assertEqual(
                [(item.path, item.kind) for item in failed.new_files],
                [
                    ("docs/huge.pdf", "large-pdf"),
                    ("docs/new_master.ai", "design-master"),
                    ("manual_sources/MOD-1/US/source/part-001.bin", "archive-chunk"),
                ],
            )

    def test_ratchet_catches_growth_shrinkage_deletion_and_allow_update(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tracked_ai = root / "manual_sources" / "MOD-2" / "JP" / "master.ai"
            tracked_ai.parent.mkdir(parents=True)
            tracked_ai.write_bytes(b"a" * 500)
            store.update_ratchet_baseline(root, seed_reason="initial")

            # Growth fails closed.
            tracked_ai.write_bytes(b"a" * 501)
            grown = store.check_repository(root, printer=lambda _: None)
            self.assertEqual(grown.exit_code, 1)
            self.assertEqual(len(grown.grown_files), 1)

            # Shrinkage flags stale until update-ratchet locks in the lower ceiling.
            tracked_ai.write_bytes(b"a" * 300)
            shrunk = store.check_repository(root, printer=lambda _: None)
            self.assertEqual(shrunk.exit_code, 1)
            self.assertEqual(shrunk.stale_paths, ("manual_sources/MOD-2/JP/master.ai",))

            code, _, _ = _run_cli(["--repo-root", str(root), "update-ratchet"])
            self.assertEqual(code, 0)
            self.assertEqual(store.check_repository(root, printer=lambda _: None).exit_code, 0)

            # Deletion also requires update-ratchet to shrink baseline to 0.
            tracked_ai.unlink()
            deleted = store.check_repository(root, printer=lambda _: None)
            self.assertEqual(deleted.exit_code, 1)
            self.assertEqual(deleted.stale_paths, ("manual_sources/MOD-2/JP/master.ai",))

            code_del, _, _ = _run_cli(["--repo-root", str(root), "update-ratchet"])
            self.assertEqual(code_del, 0)
            after_del = store.check_repository(root, printer=lambda _: None)
            self.assertEqual(after_del.exit_code, 0)
            self.assertEqual(after_del.baselined_count, 0)

            # Unbaselined file via CLI fails without --allow, succeeds with --allow.
            extra_ai = root / "docs" / "approved_exception.ai"
            extra_ai.parent.mkdir(parents=True)
            extra_ai.write_bytes(b"exception")
            code_no_allow, _, err_no_allow = _run_cli(["--repo-root", str(root), "update-ratchet"])
            self.assertEqual(code_no_allow, 2)
            self.assertIn("without --allow", err_no_allow)

            code_allow, _, _ = _run_cli(
                [
                    "--repo-root",
                    str(root),
                    "update-ratchet",
                    "--allow",
                    "docs/approved_exception.ai=MA-999 emergency test",
                ]
            )
            self.assertEqual(code_allow, 0)
            self.assertEqual(store.check_repository(root, printer=lambda _: None).exit_code, 0)

    def test_invalid_pointer_in_repo_fails_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store.write_ratchet_baseline(store.ratchet_baseline_of(root), {})
            bad_ptr = root / "manual_sources" / "MOD-3" / "US" / f"doc.pdf{store.POINTER_SUFFIX}"
            bad_ptr.parent.mkdir(parents=True)
            bad_ptr.write_text('{"schema_version": "wrong"}\n', encoding="utf-8")

            res = store.check_repository(root, printer=lambda _: None)
            self.assertEqual(res.exit_code, 1)
            self.assertEqual(len(res.invalid_pointers), 1)

    def test_real_repository_ratchet_passes(self) -> None:
        res = store.check_repository(store.REPO_ROOT, printer=lambda _: None)
        self.assertEqual(res.exit_code, 0)
        self.assertGreaterEqual(res.pointer_count, 20)
        baseline = store.load_ratchet_baseline(store.ratchet_baseline_of(store.REPO_ROOT))
        self.assertIsNotNone(baseline)
        assert baseline is not None
        self.assertEqual(
            [p for p in baseline if Path(p).suffix.lower() in {".ai", ".bin"}],
            [],
        )


class FetchAndCliWorkflowTests(unittest.TestCase):
    def test_create_pointer_and_verify_local_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            art = root / "master_panel.ai"
            payload_bytes = b"editable-vector-master-content"
            art.write_bytes(payload_bytes)

            code, _, err = _run_cli(
                [
                    "--repo-root",
                    str(root),
                    "create-pointer",
                    str(art),
                    "--storage-role",
                    "asset_sources",
                    "--record-id",
                    "recSourceRow001",
                    "--field-name",
                    "source_file",
                    "--file-token",
                    "boxcnValidToken987654",
                ]
            )
            self.assertEqual(code, 0, err)
            ptr_path = Path(f"{art}{store.POINTER_SUFFIX}")
            self.assertTrue(ptr_path.is_file())

            v_ok, _, _ = _run_cli(["verify-local", str(ptr_path)])
            self.assertEqual(v_ok, 0)

            art.write_bytes(b"tampered")
            v_bad, _, v_err = _run_cli(["verify-local", str(ptr_path)])
            self.assertEqual(v_bad, 1)
            self.assertIn("size mismatch", v_err)

    def test_resolve_base_token_by_role(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bindings = store.asset_base_bindings_of(root)
            bindings.parent.mkdir(parents=True)
            bindings.write_text(
                json.dumps({"base": {"base_token": "bascnFromBindings123"}}),
                encoding="utf-8",
            )
            self.assertEqual(
                store.resolve_base_token("asset_sources", repo_root=root, environ={}),
                "bascnFromBindings123",
            )
            self.assertEqual(
                store.resolve_base_token(
                    "asset_sources",
                    repo_root=root,
                    environ={store.PHASE2_BASE_TOKEN_ENV: "bascnFromEnv456"},
                ),
                "bascnFromEnv456",
            )
            with self.assertRaisesRegex(ValueError, store.PUBLISHED_DOCS_BASE_TOKEN_ENV):
                store.resolve_base_token("published_docs", repo_root=root, environ={})
            self.assertEqual(
                store.resolve_base_token(
                    "published_docs",
                    repo_root=root,
                    environ={store.PUBLISHED_DOCS_BASE_TOKEN_ENV: "bascnPubDocs789"},
                ),
                "bascnPubDocs789",
            )

    def test_fetch_verifies_sha256_atomically_and_cleans_up_on_corruption(self) -> None:
        expected = b"%PDF-1.7 verified attachment bytes"
        ptr = store.validate_pointer_payload(
            _valid_pointer_dict(
                role="published_docs",
                table_id="tblPubDocs987654",
                file_name="manual.pdf",
                content=expected,
            )
        )
        with tempfile.TemporaryDirectory() as tmp:
            out_file = Path(tmp) / "downloads" / "manual.pdf"
            calls: list[list[str]] = []

            def good_runner(
                cmd: list[str], **kwargs: object
            ) -> subprocess.CompletedProcess[str]:
                calls.append(cmd)
                out_arg = cmd[cmd.index("--output") + 1]
                self.assertTrue(out_arg.startswith("./"))
                cwd = Path(str(kwargs["cwd"]))
                (cwd / out_arg).write_bytes(expected)
                return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")

            written = store.fetch_pointer_attachment(
                ptr,
                out_file,
                base_token="bascnPubBase",
                profile="feishu_bot",
                runner=good_runner,
            )
            self.assertEqual(written, out_file)
            self.assertEqual(out_file.read_bytes(), expected)
            self.assertEqual(len(calls), 1)
            self.assertIn("+record-download-attachment", calls[0])
            self.assertEqual(calls[0][:3], ["lark-cli", "--profile", "feishu_bot"])

            # Idempotent re-fetch does not invoke lark-cli when local file already matches.
            store.fetch_pointer_attachment(
                ptr,
                out_file,
                base_token="bascnPubBase",
                runner=good_runner,
            )
            self.assertEqual(len(calls), 1)

            # Modified local file refuses overwrite unless --force is passed.
            out_file.write_bytes(b"local-dirty-edit")
            with self.assertRaisesRegex(RuntimeError, "without --force"):
                store.fetch_pointer_attachment(
                    ptr,
                    out_file,
                    base_token="bascnPubBase",
                    runner=good_runner,
                )

            # Corrupted remote payload cleans up temporary .part file and never writes target.
            corrupt_target = Path(tmp) / "downloads" / "corrupt.pdf"

            def corrupt_runner(
                cmd: list[str], **kwargs: object
            ) -> subprocess.CompletedProcess[str]:
                out_arg = cmd[cmd.index("--output") + 1]
                cwd = Path(str(kwargs["cwd"]))
                (cwd / out_arg).write_bytes(b"%PDF-1.7 wrong bytes same length!!")
                return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")

            with self.assertRaisesRegex(RuntimeError, "sha256 mismatch"):
                store.fetch_pointer_attachment(
                    ptr,
                    corrupt_target,
                    base_token="bascnPubBase",
                    runner=corrupt_runner,
                )
            self.assertFalse(corrupt_target.exists())
            leftover_parts = list((Path(tmp) / "downloads").glob("*.part"))
            self.assertEqual(leftover_parts, [])


class PackageInventoryPointerIntegrationTests(unittest.TestCase):
    def test_inventory_counts_pointer_files_and_manifest_external_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pkg = root / "manual_sources" / "MOD-EXT" / "EU" / "en"
            (pkg / "source").mkdir(parents=True)
            ptr = store.validate_pointer_payload(_valid_pointer_dict())
            store.write_pointer_file(pkg / "source" / f"master_art.ai{store.POINTER_SUFFIX}", ptr)

            manifest_payload = {
                "target": {"model": "MOD-EXT", "region": "EU"},
                "external_sources": [
                    _valid_pointer_dict(
                        role="published_docs",
                        table_id="tblPubDocs987654",
                        file_name="shipped.pdf",
                    )
                ],
            }
            (pkg / "source_manifest.json").write_text(
                json.dumps(manifest_payload, indent=2) + "\n",
                encoding="utf-8",
            )

            report = collect_inventory(root)
            self.assertEqual(report["external_source_pointer_count"], 2)
            self.assertEqual(report["external_source_package_count"], 1)
            self.assertEqual(report["packages"][0]["external_source_count"], 2)
            self.assertTrue(report["packages"][0]["has_external_source_pointers"])
            self.assertIn(
                "External source pointers: 2 across 1 packages",
                format_inventory_text(report),
            )


class PointerFallbackHelpersTests(unittest.TestCase):
    def test_resolve_source_identity_and_acceptance_parity(self) -> None:
        raw_bytes = b"part-one-" + b"part-two"
        raw_sha = hashlib.sha256(raw_bytes).hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            pkg = Path(tmp)
            ptr = store.validate_pointer_payload(
                _valid_pointer_dict(file_name="archive.pdf", content=raw_bytes)
            )
            ptr_rel = f"source/archive.pdf{store.POINTER_SUFFIX}"
            ptr_path = store.write_pointer_file(pkg / ptr_rel, ptr)
            self.assertEqual(
                store.resolve_source_identity(pkg / "source/archive.pdf"),
                (len(raw_bytes), raw_sha),
            )
            original = {
                "sha256": raw_sha,
                "archive_parts": [
                    {"path": "source/part-001.bin", "size": 9},
                    {"path": "source/part-002.bin", "size": 8},
                ],
            }
            self.assertEqual(
                store.resolve_archived_pdf_sha256(pkg, original, pointer_relpath=ptr_rel),
                raw_sha,
            )
            ptr_size, ptr_sha = store.sha256_file(ptr_path)
            approval_rows = [
                {"path": "README.md", "size": 5, "sha256": "a" * 64},
                {"path": "rebuild.py", "size": 10, "sha256": "b" * 64},
                {"path": "source/part-001.bin", "size": 9, "sha256": "c" * 64},
                {"path": "source/part-002.bin", "size": 8, "sha256": "d" * 64},
            ]
            manifest_rows = [
                {"path": "README.md", "size": 5, "sha256": "a" * 64},
                {"path": "rebuild.py", "size": 12, "sha256": "e" * 64},
                {"path": ptr_rel, "size": ptr_size, "sha256": ptr_sha},
            ]
            self.assertTrue(
                store.reviewed_inputs_match_with_pointers(
                    pkg,
                    approval_rows,
                    manifest_rows,
                    original_sha256=raw_sha,
                    raw_archive_paths=("source/part-001.bin", "source/part-002.bin"),
                    adapter_paths=("rebuild.py",),
                )
            )
            self.assertFalse(
                store.reviewed_inputs_match_with_pointers(
                    pkg,
                    approval_rows[1:],
                    manifest_rows,
                    original_sha256=raw_sha,
                    raw_archive_paths=("source/part-001.bin", "source/part-002.bin"),
                    adapter_paths=("rebuild.py",),
                )
            )


if __name__ == "__main__":
    unittest.main()
