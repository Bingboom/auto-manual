from __future__ import annotations

import hashlib
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import build
from tools.manual_knowledge import ir_commands as manual_ir_commands
from tools.web import ir_commands, package_commands
from tools.web.prepared_style_audit import PREPARED_SOURCE, load_baseline


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_pinned_package(
    pkg_dir: Path,
    *,
    model: str = "MOD-1",
    region: str = "US",
    css_text: str | None = None,
    content_sha: str = "abc123",
    lang: str = "en",
) -> Path:
    src_file = pkg_dir / "source" / "input.txt"
    src_file.parent.mkdir(parents=True, exist_ok=True)
    src_bytes = b"source copy\n"
    src_file.write_bytes(src_bytes)
    manifest: dict[str, object] = {
        "model": model,
        "region": region,
        "target": {"model": model, "region": region, "languages": [lang]},
        "inputs": [{"path": "source/input.txt", "sha256": _sha256_bytes(src_bytes)}],
        "repo_inputs": [],
    }
    (pkg_dir / "source_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if css_text is not None:
        web_dir = pkg_dir / "web" / lang
        (web_dir / "_static").mkdir(parents=True, exist_ok=True)
        (web_dir / "_static" / "source.css").write_text(css_text, encoding="utf-8")
        (web_dir / "manual.ir.json").write_text(
            json.dumps(
                {
                    "schema_version": "manual-ir/v2",
                    "source": PREPARED_SOURCE,
                    "model": model,
                    "region": region,
                    "language": lang,
                    "content_sha256": content_sha,
                    "metadata": {"source_stylesheet": {"path": "_static/source.css"}},
                    "pages": [
                        {
                            "page_id": "00_preface",
                            "blocks": [
                                {
                                    "block_id": "b0",
                                    "kind": "flow",
                                    "payload": {
                                        "kind": "paragraph",
                                        "children": [{"kind": "text", "text": "Hello"}],
                                    },
                                }
                            ],
                        }
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    return pkg_dir


def _write_ir_bundle(
    ir_dir: Path,
    *,
    model: str = "MOD-1",
    region: str = "US",
    language: str = "en",
    text: str = "Press the power button.",
    include_warning_residue: bool = False,
    empty_heading: bool = False,
) -> Path:
    ir_dir.mkdir(parents=True, exist_ok=True)
    heading_text = "" if empty_heading else ("Safety" if language == "en" else "Sécurité")
    raw_blocks: list[dict[str, object]] = [
        {"kind": "heading", "level": 1, "children": [{"kind": "text", "text": heading_text}]},
        {"kind": "paragraph", "children": [{"kind": "text", "text": text}]},
    ]
    if include_warning_residue:
        raw_blocks.append(
            {"kind": "paragraph", "children": [{"kind": "text", "text": "Charge battery fully before use."}]}
        )
    page_id = f"01_safety_{language}"
    payload = {
        "schema_version": "manual-ir/v2",
        "model": model,
        "region": region,
        "language": language,
        "content_sha256": f"sha-{model}-{region}-{language}",
        "metadata": {
            "publication_eligible": True,
            "product_name": f"Jackery {model}",
            "revision": "1.0",
            "asset_sha256": {},
        },
        "pages": [
            {
                "page_id": page_id,
                "language": language,
                "source_path": f"{page_id}.rst",
                "source_ref": page_id,
                "source_sha256": "0" * 64,
                "blocks": [
                    {
                        "block_id": f"b{idx}",
                        "source_ref": f"{page_id}#{idx}",
                        "kind": "flow",
                        "payload": blk,
                    }
                    for idx, blk in enumerate(raw_blocks)
                ],
            }
        ],
    }
    ir_path = ir_dir / "manual.ir.json"
    ir_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return ir_path


class BuildWebIrCliTests(unittest.TestCase):
    def test_parse_args_supports_web_package_ir_qc_and_ir_export_flags(self) -> None:
        pkg_args = build.parse_args(
            [
                "web-package",
                "--package-command",
                "build",
                "--package-dir",
                "manual_sources/MOD/US/en",
                "--output-dir",
                ".tmp/out",
                "--lang",
                "en",
                "--respect-baseline",
                "--skip-pin-check",
                "--json",
            ]
        )
        self.assertEqual(pkg_args.action, "web-package")
        self.assertEqual(pkg_args.package_command, "build")
        self.assertEqual(pkg_args.package_dir, Path("manual_sources/MOD/US/en"))
        self.assertEqual(pkg_args.output_dir, Path(".tmp/out"))
        self.assertTrue(pkg_args.respect_baseline)
        self.assertTrue(pkg_args.skip_pin_check)
        self.assertTrue(pkg_args.json)

        qc_args = build.parse_args(
            [
                "ir-qc",
                "--ir-command",
                "audit",
                "--all-ir",
                "--no-verify-assets",
                "--strict",
                "--max-warnings",
                "5",
                "--output-path",
                ".tmp/qc.json",
                "--json",
            ]
        )
        self.assertEqual(qc_args.action, "ir-qc")
        self.assertEqual(qc_args.ir_command, "audit")
        self.assertTrue(qc_args.all_ir)
        self.assertTrue(qc_args.no_verify_assets)
        self.assertTrue(qc_args.strict)
        self.assertEqual(qc_args.max_warnings, 5)
        self.assertEqual(qc_args.output_path, Path(".tmp/qc.json"))

        exp_args = build.parse_args(
            [
                "ir-export",
                "--ir-root",
                "manual_sources",
                "--ir-root",
                "data/manual_sources",
                "--region",
                "EU",
                "--model",
                "MOD-1",
                "--publication-eligible-only",
                "--output-corpus",
                ".tmp/corpus.json",
                "--output-observations",
                ".tmp/obs.json",
                "--previous-observations",
                ".tmp/prev.json",
                "--json",
            ]
        )
        self.assertEqual(exp_args.action, "ir-export")
        self.assertEqual(exp_args.ir_roots, [Path("manual_sources"), Path("data/manual_sources")])
        self.assertEqual(exp_args.region, "EU")
        self.assertEqual(exp_args.model, "MOD-1")
        self.assertTrue(exp_args.publication_eligible_only)
        self.assertEqual(exp_args.output_corpus, Path(".tmp/corpus.json"))
        self.assertEqual(exp_args.output_observations, Path(".tmp/obs.json"))
        self.assertEqual(exp_args.previous_observations, Path(".tmp/prev.json"))

    def test_web_package_batch_verify_pins_and_audit_styles(self) -> None:
        baseline_sha = str(load_baseline()["entries"][0]["ir_content_sha256"])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pkg_a = _write_pinned_package(
                root / "manual_sources" / "MOD-A" / "US" / "en",
                model="MOD-A",
                region="US",
                css_text=".manual-wrap { margin: 0 auto; max-width: 720px; }\n",
            )
            pkg_b = _write_pinned_package(
                root / "data" / "manual_sources" / "MOD-B" / "EU" / "fr",
                model="MOD-B",
                region="EU",
                lang="fr",
                css_text=".manual-wrap { color: red; }\n",
                content_sha=baseline_sha,
            )
            self.assertTrue(pkg_a.is_dir() and pkg_b.is_dir())

            buf = io.StringIO()
            with redirect_stdout(buf):
                package_commands.run_web_package_command(
                    SimpleNamespace(package_command="inventory", json=True),
                    repo_root=root,
                )
            inv = json.loads(buf.getvalue())
            self.assertEqual(inv["total_packages"], 2)

            # Both packages pass verify-pins initially
            buf = io.StringIO()
            with redirect_stdout(buf):
                package_commands.run_web_package_command(
                    SimpleNamespace(
                        package_command="verify-pins",
                        package_dir=None,
                        all_packages=True,
                        json=True,
                    ),
                    repo_root=root,
                )
            pin_ok = json.loads(buf.getvalue())
            self.assertTrue(pin_ok["ok"])
            self.assertEqual(pin_ok["passed_packages"], 2)

            # Drift pkg_b input -> verify-pins --all-packages fails non-zero
            (pkg_b / "source" / "input.txt").write_text("drifted\n", encoding="utf-8")
            buf = io.StringIO()
            with redirect_stdout(buf), self.assertRaises(RuntimeError):
                package_commands.run_web_package_command(
                    SimpleNamespace(
                        package_command="verify-pins",
                        package_dir=None,
                        all_packages=True,
                        json=True,
                    ),
                    repo_root=root,
                )
            pin_fail = json.loads(buf.getvalue())
            self.assertFalse(pin_fail["ok"])
            self.assertEqual(pin_fail["failed_packages"], 1)

            # audit-styles --all-packages fails on paint CSS without baseline
            buf = io.StringIO()
            with redirect_stdout(buf), self.assertRaises(RuntimeError):
                package_commands.run_web_package_command(
                    SimpleNamespace(
                        package_command="audit-styles",
                        package_dir=None,
                        all_packages=True,
                        lang=None,
                        respect_baseline=False,
                        json=True,
                    ),
                    repo_root=root,
                )
            audit_fail = json.loads(buf.getvalue())
            self.assertFalse(audit_fail["ok"])
            self.assertEqual(audit_fail["sealed_packages"], 2)
            self.assertEqual(audit_fail["failed_packages"], 1)

            # With --respect-baseline, pkg_b passes using committed baseline entry
            buf = io.StringIO()
            with redirect_stdout(buf):
                package_commands.run_web_package_command(
                    SimpleNamespace(
                        package_command="audit-styles",
                        package_dir=None,
                        all_packages=True,
                        lang=None,
                        respect_baseline=True,
                        json=True,
                    ),
                    repo_root=root,
                )
            audit_ok = json.loads(buf.getvalue())
            self.assertTrue(audit_ok["ok"])
            self.assertEqual(audit_ok["passed_packages"], 2)

    def test_web_package_build_facade_routes_flags_and_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(RuntimeError):
                package_commands.run_web_package_command(
                    SimpleNamespace(package_command="build", all_packages=True, package_dir=None, lang="en", output_dir=None),
                    repo_root=root,
                )
            with mock.patch(
                "tools.web.package_build.build_declarative_package",
                return_value={"ok": True, "markdown_path": str(root / "out" / "manual.md"), "pages": ["a"]},
            ) as build_mock:
                buf = io.StringIO()
                with redirect_stdout(buf):
                    package_commands.run_web_package_command(
                        SimpleNamespace(
                            package_command="build",
                            all_packages=False,
                            package_dir=Path("manual_sources/MOD/US/en"),
                            lang="en",
                            output_dir=Path(".tmp/out"),
                            skip_pin_check=True,
                            respect_baseline=True,
                            json=True,
                        ),
                        repo_root=root,
                    )
                payload = json.loads(buf.getvalue())
                self.assertTrue(payload["ok"])
                build_mock.assert_called_once()
                self.assertTrue(build_mock.call_args.kwargs["skip_pin_check"])
                self.assertTrue(build_mock.call_args.kwargs["respect_baseline"])

    def test_ir_qc_all_ir_audit_max_warnings_strict_and_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_ir_bundle(
                root / "manual_sources" / "MOD-1" / "EU" / "v1" / "web" / "en",
                model="MOD-1",
                region="EU",
                language="en",
                text="Charge battery fully before use.",
            )
            _write_ir_bundle(
                root / "manual_sources" / "MOD-1" / "EU" / "v1" / "web" / "fr",
                model="MOD-1",
                region="EU",
                language="fr",
                text="Charge battery fully before use.",
                include_warning_residue=False,
            )

            out_report = root / "reports" / "qc.json"
            buf = io.StringIO()
            with redirect_stdout(buf):
                ir_commands.run_ir_qc_command(
                    SimpleNamespace(
                        ir_command="audit",
                        ir=None,
                        all_ir=True,
                        output_path=out_report,
                        max_warnings=5,
                        strict=False,
                        no_verify_assets=True,
                        json=True,
                    ),
                    repo_root=root,
                )
            report = json.loads(buf.getvalue())
            self.assertEqual(report["total_bundles"], 2)
            self.assertEqual(report["paired_targets"], 1)
            self.assertEqual(report["total_errors"], 0)
            self.assertGreaterEqual(report["total_warnings"], 1)
            self.assertIn("untranslated_english_residue", report["warning_types"])
            self.assertNotIn("unknown", report["warning_types"])
            self.assertTrue(out_report.is_file())

            # Exceeding --max-warnings=0 fails
            with redirect_stdout(io.StringIO()), self.assertRaises(RuntimeError):
                ir_commands.run_ir_qc_command(
                    SimpleNamespace(
                        ir_command="audit",
                        ir=None,
                        all_ir=True,
                        max_warnings=0,
                        strict=False,
                        no_verify_assets=True,
                        json=True,
                    ),
                    repo_root=root,
                )

            # --strict fails on warnings
            with redirect_stdout(io.StringIO()), self.assertRaises(RuntimeError):
                ir_commands.run_ir_qc_command(
                    SimpleNamespace(
                        ir_command="audit",
                        ir=None,
                        all_ir=True,
                        strict=True,
                        no_verify_assets=True,
                        json=False,
                    ),
                    repo_root=root,
                )

            # Error bundle fails even without strict
            bad_ir = _write_ir_bundle(
                root / "manual_sources" / "MOD-2" / "US" / "v1" / "web" / "en",
                model="MOD-2",
                region="US",
                language="en",
                empty_heading=True,
            )
            with redirect_stdout(io.StringIO()), self.assertRaises(RuntimeError):
                ir_commands.run_ir_qc_command(
                    SimpleNamespace(
                        ir_command="audit",
                        ir=bad_ir,
                        all_ir=False,
                        strict=False,
                        no_verify_assets=True,
                        json=True,
                    ),
                    repo_root=root,
                )

            # Provenance across --all-ir succeeds
            prov_out = root / "reports" / "prov.json"
            buf = io.StringIO()
            with redirect_stdout(buf):
                ir_commands.run_ir_qc_command(
                    SimpleNamespace(
                        ir_command="provenance",
                        ir=None,
                        all_ir=True,
                        output_path=prov_out,
                        json=True,
                    ),
                    repo_root=root,
                )
            prov_report = json.loads(buf.getvalue())
            self.assertEqual(prov_report["total_bundles"], 3)
            self.assertEqual(prov_report["ok_bundles"], 3)
            self.assertTrue(prov_out.is_file())

    def test_ir_export_command_and_build_main_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_ir_bundle(
                root / "manual_sources" / "MOD-1" / "EU" / "v1" / "web" / "en",
                model="MOD-1",
                region="EU",
                language="en",
                text="Do not disassemble the unit.",
            )
            out_corpus = root / "out" / "corpus.json"
            out_obs = root / "out" / "observations.json"
            buf = io.StringIO()
            with redirect_stdout(buf):
                manual_ir_commands.run_ir_export_command(
                    SimpleNamespace(
                        ir_roots=[Path("manual_sources")],
                        region="EU",
                        model="MOD-1",
                        publication_eligible_only=True,
                        output_corpus=out_corpus,
                        output_observations=out_obs,
                        previous_observations=None,
                        json=True,
                    ),
                    repo_root=root,
                )
            summary = json.loads(buf.getvalue())
            self.assertEqual(summary["status"], "ok")
            self.assertEqual(summary["counts"]["editions"], 1)
            self.assertTrue(out_corpus.is_file())
            self.assertTrue(out_obs.is_file())

            # Full build.main(...) round-trip on error case returns exit code 1 cleanly
            err_buf = io.StringIO()
            with redirect_stderr(err_buf):
                rc = build.main(["web-package", "--package-command", "verify-pins"])
            self.assertEqual(rc, 1)
            self.assertIn("requires --package-dir or --all-packages", err_buf.getvalue())

            # Full build.main(...) inventory round-trip returns 0
            out_buf = io.StringIO()
            with mock.patch("tools.build_main.load_local_env_file"), redirect_stdout(out_buf):
                rc_ok = build.main(["web-package", "--package-command", "inventory", "--json"])
            self.assertEqual(rc_ok, 0)
            self.assertIn('"total_packages"', out_buf.getvalue())


if __name__ == "__main__":
    unittest.main()
