"""Tests for tools.web.package_build and tools.web.package_inventory."""
from __future__ import annotations

from contextlib import redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest

from tools.utils.path_utils import PathSegments
from tools.web.package_build import (
    DEFAULT_REPO_ROOT,
    audit_styles,
    build_declarative_package,
    main,
    verify_pins,
)
from tools.web.package_inventory import collect_inventory
from tools.web.prepared_style_audit import PREPARED_SOURCE, load_baseline
from tools.web.presentation import PRESENTATION_PROFILE_ENV


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _run_cli(argv: list[str]) -> tuple[int, str]:
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = main(argv)
    return code, buf.getvalue()


class VerifyPinsTests(unittest.TestCase):
    def test_verify_pins_passes_and_supports_crlf_normalization(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pkg = root / "manual_sources" / "TEST-1" / "US" / "en"
            pkg.mkdir(parents=True)

            lf_bytes = b"line one\nline two\n"
            crlf_bytes = b"line one\r\nline two\r\n"
            (pkg / "README.md").write_bytes(crlf_bytes)

            shared_file = root / "docs" / "shared.txt"
            shared_file.parent.mkdir(parents=True)
            shared_bytes = b"shared-content\n"
            shared_file.write_bytes(shared_bytes)

            _write_json(
                pkg / "source_manifest.json",
                {
                    "inputs": [{"path": "README.md", "sha256": _sha256_bytes(lf_bytes)}],
                    "repo_inputs": [
                        {"path": "docs/shared.txt", "sha256": _sha256_bytes(shared_bytes)}
                    ],
                },
            )

            report = verify_pins(pkg, repo_root=root)
            self.assertTrue(report["ok"])
            self.assertEqual(report["checked_inputs"], 1)
            self.assertEqual(report["checked_repo_inputs"], 1)
            self.assertEqual(report["mismatches"], [])
            self.assertEqual(report["missing"], [])
            self.assertEqual(report["traversal_errors"], [])

            code, out = _run_cli(
                ["verify-pins", str(pkg), "--repo-root", str(root), "--json"]
            )
            self.assertEqual(code, 0)
            self.assertTrue(json.loads(out)["ok"])

    def test_verify_pins_fails_on_sha256_mismatch_missing_and_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outside = root / "secret.txt"
            outside.write_text("secret", encoding="utf-8")

            pkg = root / "manual_sources" / "TEST-2" / "US" / "en"
            pkg.mkdir(parents=True)
            (pkg / "changed.txt").write_text("actual", encoding="utf-8")

            _write_json(
                pkg / "source_manifest.json",
                {
                    "inputs": [
                        {"path": "changed.txt", "sha256": "0" * 64},
                        {"path": "absent.txt", "sha256": "1" * 64},
                        {"path": "../../../secret.txt", "sha256": _sha256_bytes(b"secret")},
                    ],
                    "repo_inputs": [
                        {"path": "../outside_repo.txt", "sha256": "2" * 64},
                    ],
                },
            )

            report = verify_pins(pkg, repo_root=root)
            self.assertFalse(report["ok"])
            self.assertEqual(len(report["mismatches"]), 1)
            self.assertEqual(report["mismatches"][0]["path"], "changed.txt")
            self.assertEqual(len(report["missing"]), 1)
            self.assertEqual(report["missing"][0]["path"], "absent.txt")
            self.assertEqual(len(report["traversal_errors"]), 2)

            code, _ = _run_cli(["verify-pins", str(pkg), "--repo-root", str(root)])
            self.assertEqual(code, 1)


class AuditStylesTests(unittest.TestCase):
    def _write_sealed_package(
        self,
        pkg: Path,
        *,
        css_text: str,
        content_sha: str = "abc123",
    ) -> None:
        _write_json(
            pkg / "source_manifest.json",
            {"target": {"model": "TEST-M", "region": "US", "languages": ["en"]}},
        )
        web_en = pkg / "web" / "en"
        (web_en / "_static").mkdir(parents=True)
        (web_en / "_static" / "source.css").write_text(css_text, encoding="utf-8")
        _write_json(
            web_en / PathSegments.MANUAL_IR_JSON,
            {
                "source": PREPARED_SOURCE,
                "model": "TEST-M",
                "region": "US",
                "language": "en",
                "content_sha256": content_sha,
                "metadata": {
                    "source_stylesheet": {"path": "_static/source.css"},
                },
                "pages": [
                    {
                        "page_id": "00_preface_en.rst",
                        "blocks": [
                            {
                                "block_id": "b0",
                                "payload": {
                                    "kind": "paragraph",
                                    "children": [{"kind": "text", "text": "Hello"}],
                                },
                            }
                        ],
                    }
                ],
            },
        )

    def test_audit_styles_catches_paint_css_and_passes_geometry_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad_pkg = root / "bad_pkg"
            self._write_sealed_package(
                bad_pkg,
                css_text=".manual-wrap { color: #111; background: #fff; max-width: 720px; }\n",
            )
            bad_report = audit_styles(bad_pkg)
            self.assertFalse(bad_report["ok"])
            issues = bad_report["locales"][0]["issues"]
            self.assertTrue(any("color" in item for item in issues))
            self.assertTrue(any("background" in item for item in issues))

            code_bad, _ = _run_cli(["audit-styles", str(bad_pkg), "--lang", "en"])
            self.assertEqual(code_bad, 1)

            good_pkg = root / "good_pkg"
            self._write_sealed_package(
                good_pkg,
                css_text=".manual-wrap { margin: 0 auto; padding: 12px; max-width: 720px; }\n",
            )
            code_good, out_good = _run_cli(
                ["audit-styles", str(good_pkg), "--lang", "en", "--json"]
            )
            self.assertEqual(code_good, 0)
            payload = json.loads(out_good)
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["locales"][0]["issues"], [])

    def test_audit_styles_respects_baseline_when_requested(self) -> None:
        baseline_sha = str(load_baseline()["entries"][0]["ir_content_sha256"])
        with tempfile.TemporaryDirectory() as tmp:
            pkg = Path(tmp) / "legacy_pkg"
            self._write_sealed_package(
                pkg,
                css_text=".manual-wrap { color: red; }\n",
                content_sha=baseline_sha,
            )
            strict = audit_styles(pkg, respect_baseline=False)
            self.assertFalse(strict["ok"])

            exempt = audit_styles(pkg, respect_baseline=True)
            self.assertTrue(exempt["ok"])
            self.assertTrue(exempt["locales"][0]["baseline"])


class InventoryTests(unittest.TestCase):
    def test_inventory_classifies_synthetic_roots_collisions_and_binaries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # 1. manual_sources: declarative + approved + sealed + large pdf
            pkg_a = root / "manual_sources" / "MOD-A" / "US" / "en"
            (pkg_a / "source" / "en").mkdir(parents=True)
            (pkg_a / "source" / "en" / "index.rst").write_text(
                ".. toctree::\n\n   00_preface_en\n", encoding="utf-8"
            )
            (pkg_a / "source" / "en" / "00_preface_en.rst").write_text(
                "Hello\n", encoding="utf-8"
            )
            _write_json(pkg_a / "source" / "approval.json", {"approved": True})
            _write_json(pkg_a / "web" / "en" / PathSegments.MANUAL_IR_JSON, {"pages": []})
            _write_json(
                pkg_a / "source_manifest.json",
                {"target": {"model": "MOD-A", "region": "US"}},
            )
            large_pdf = pkg_a / "source" / "original.pdf"
            large_pdf.write_bytes(b"0" * (1024 * 1024 + 50))
            small_pdf = pkg_a / "source" / "small.pdf"
            small_pdf.write_bytes(b"0" * 512)

            # 2. data/manual_sources: collides with MOD-A/US, custom script, unapproved
            pkg_b = root / "data" / "manual_sources" / "MOD-A" / "US" / "v1"
            (pkg_b / "source").mkdir(parents=True)
            (pkg_b / "rebuild.py").write_text("# custom\n", encoding="utf-8")
            _write_json(
                pkg_b / "source_manifest.json",
                {"target": {"model": "MOD-A", "region": "US"}},
            )
            large_ai = pkg_b / "source" / "art.ai"
            large_ai.write_bytes(b"1" * (1024 * 1024 + 100))

            # 3. data/manual_sources: separate model with declarative_build.pages
            pkg_c = root / "data" / "manual_sources" / "MOD-B" / "JP" / "ja"
            (pkg_c / "source" / "ja").mkdir(parents=True)
            (pkg_c / "source" / "ja" / "00_preface_ja.rst").write_text(
                "Intro\n", encoding="utf-8"
            )
            _write_json(pkg_c / "source" / "release_approval.json", {"ok": True})
            _write_json(
                pkg_c / "source_manifest.json",
                {
                    "target": {"model": "MOD-B", "region": "JP"},
                    "declarative_build": {"pages": ["00_preface_ja.rst"]},
                },
            )

            report = collect_inventory(root)
            self.assertEqual(report["total_packages"], 3)
            self.assertEqual(
                report["by_root"], {"manual_sources": 1, "data/manual_sources": 2}
            )
            self.assertEqual(report["custom_script_count"], 1)
            self.assertEqual(report["declarative_ready_count"], 2)
            self.assertEqual(report["approved_count"], 2)
            self.assertEqual(report["sealed_package_count"], 1)
            self.assertEqual(report["large_binary_count"], 2)
            self.assertEqual(
                report["large_binary_bytes"],
                (1024 * 1024 + 50) + (1024 * 1024 + 100),
            )
            self.assertEqual(len(report["dual_root_collisions"]), 1)
            collision = report["dual_root_collisions"][0]
            self.assertEqual((collision["model"], collision["region"]), ("MOD-A", "US"))

            by_path = {item["path"]: item for item in report["packages"]}
            self.assertEqual(by_path["manual_sources/MOD-A/US/en"]["sealed_locales"], ["en"])
            self.assertTrue(by_path["manual_sources/MOD-A/US/en"]["declarative_ready"])
            self.assertFalse(by_path["data/manual_sources/MOD-A/US/v1"]["declarative_ready"])
            self.assertTrue(by_path["data/manual_sources/MOD-A/US/v1"]["has_custom_script"])

    def test_inventory_real_repo_smoke(self) -> None:
        code, out = _run_cli(
            ["inventory", "--repo-root", str(DEFAULT_REPO_ROOT), "--json"]
        )
        self.assertEqual(code, 0)
        report = json.loads(out)
        self.assertGreaterEqual(report["total_packages"], 200)
        self.assertGreater(report["by_root"]["manual_sources"], 0)
        self.assertGreater(report["by_root"]["data/manual_sources"], 0)
        self.assertEqual(report["large_binary_bytes"], 0)
        self.assertEqual(report["large_binary_count"], 0)
        self.assertEqual(report["unpackaged_large_binary_bytes"], 0)
        self.assertEqual(report["total_root_large_binary_bytes"], 0)
        self.assertGreaterEqual(report["external_source_pointer_count"], 189)
        self.assertIsInstance(report["dual_root_collisions"], list)


def _fake_pandoc_for_test(cmd: list[str], **_kwargs: object) -> object:
    from bs4 import BeautifulSoup
    from types import SimpleNamespace

    source_html = Path(cmd[1]).read_text(encoding="utf-8")
    soup = BeautifulSoup(source_html, "html.parser")
    lines = [el.get_text(" ", strip=True) for el in soup.find_all(["h1", "h2", "h3", "p", "li"])]
    target = Path(cmd[cmd.index("-o") + 1])
    target.write_text("\n\n".join(line for line in lines if line) + "\n", encoding="utf-8")
    return SimpleNamespace(stdout="")


class DeclarativeBuildTests(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        import shutil
        from unittest import mock
        from tools import markdown_bundle

        if shutil.which("pandoc") is None:
            for patcher in (
                mock.patch.object(markdown_bundle, "resolve_pandoc_binary", return_value="pandoc"),
                mock.patch.object(markdown_bundle, "resolve_markdown_writer", return_value="myst"),
                mock.patch.object(markdown_bundle.subprocess, "run", side_effect=_fake_pandoc_for_test),
            ):
                patcher.start()
                self.addCleanup(patcher.stop)
    def _create_declarative_package(self, pkg: Path) -> None:
        source_en = pkg / "source" / "en"
        source_en.mkdir(parents=True)
        preface = source_en / "00_preface_en.rst"
        guide = source_en / "guide_en.rst"
        index_rst = source_en / "index.rst"
        preface.write_text(
            "**Thank you for purchasing this product.**\n\n"
            "- Read this manual before use.\n",
            encoding="utf-8",
        )
        guide.write_text(
            "Operating Guide\n===============\n\n"
            "Press the power button to begin.\n",
            encoding="utf-8",
        )
        index_rst.write_text(
            "Manual\n======\n\n.. toctree::\n   :maxdepth: 2\n\n"
            "   00_preface_en\n   guide_en\n",
            encoding="utf-8",
        )
        sheet = pkg / "source" / "geometry.css"
        sheet.write_text(".manual-doc { max-width: 720px; }\n", encoding="utf-8")

        inputs = []
        for rel in (
            "source/en/00_preface_en.rst",
            "source/en/guide_en.rst",
            "source/en/index.rst",
            "source/geometry.css",
        ):
            inputs.append(
                {"path": rel, "sha256": _sha256_bytes((pkg / rel).read_bytes())}
            )

        _write_json(
            pkg / "source_manifest.json",
            {
                "schema_version": "auto-manual-frozen-web-source/v1",
                "target": {"model": "TEST-DEC", "region": "US", "languages": ["en"]},
                "declarative_build": {
                    "title": "Test Declarative Manual",
                    "stylesheet": "source/geometry.css",
                },
                "inputs": inputs,
                "repo_inputs": [],
            },
        )

    def test_declarative_build_end_to_end_and_env_restore(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pkg = root / "pkg"
            out_dir = root / "built_web"
            self._create_declarative_package(pkg)

            previous_env = os.environ.get(PRESENTATION_PROFILE_ENV)
            os.environ[PRESENTATION_PROFILE_ENV] = "document"
            try:
                code, out = _run_cli(
                    [
                        "build",
                        str(pkg),
                        "--lang",
                        "en",
                        "--out",
                        str(out_dir),
                        "--repo-root",
                        str(DEFAULT_REPO_ROOT),
                        "--json",
                    ]
                )
                self.assertEqual(os.environ.get(PRESENTATION_PROFILE_ENV), "document")
            finally:
                if previous_env is None:
                    os.environ.pop(PRESENTATION_PROFILE_ENV, None)
                else:
                    os.environ[PRESENTATION_PROFILE_ENV] = previous_env

            self.assertEqual(code, 0, out)
            result = json.loads(out)
            self.assertTrue(result["ok"])
            self.assertEqual(
                result["pages"],
                ["source/en/00_preface_en.rst", "source/en/guide_en.rst"],
            )
            markdown_path = Path(result["markdown_path"])
            ir_path = Path(result["manual_ir_path"])
            self.assertTrue(markdown_path.is_file())
            self.assertTrue(ir_path.is_file())
            self.assertTrue((out_dir / "conf.py").is_file())
            self.assertTrue((out_dir / "_static" / "web_manual.css").is_file())
            self.assertTrue((out_dir / "_static" / "geometry.css").is_file())
            ir_data = json.loads(ir_path.read_text(encoding="utf-8"))
            self.assertEqual(ir_data["model"], "TEST-DEC")
            self.assertEqual(ir_data["region"], "US")
            self.assertEqual(ir_data["language"], "en")
            self.assertEqual(len(ir_data["pages"]), 2)

            # Reject existing output directory
            code_exists, err_out = _run_cli(
                [
                    "build",
                    str(pkg),
                    "--lang",
                    "en",
                    "--out",
                    str(out_dir),
                    "--repo-root",
                    str(DEFAULT_REPO_ROOT),
                    "--json",
                ]
            )
            self.assertEqual(code_exists, 1)
            self.assertIn("already exists", err_out)

    def test_build_pin_check_and_skip_pin_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pkg = root / "pkg"
            self._create_declarative_package(pkg)
            # Drift a pinned file after manifest generation
            (pkg / "source" / "en" / "guide_en.rst").write_text(
                "Operating Guide\n===============\n\nUpdated copy.\n",
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                build_declarative_package(
                    pkg,
                    lang="en",
                    output_dir=root / "out_fail",
                    repo_root=DEFAULT_REPO_ROOT,
                    skip_pin_check=False,
                )
            self.assertFalse((root / "out_fail").exists())

            res = build_declarative_package(
                pkg,
                lang="en",
                output_dir=root / "out_skip",
                repo_root=DEFAULT_REPO_ROOT,
                skip_pin_check=True,
            )
            self.assertTrue(res["ok"])
            self.assertIn("Updated copy.", Path(res["markdown_path"]).read_text(encoding="utf-8"))

    def test_build_respect_baseline_admits_baselined_pkg_and_rejects_growth(self) -> None:
        from unittest import mock
        from tools.web import prepared_style_audit

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pkg = root / "pkg"
            self._create_declarative_package(pkg)
            (pkg / "source" / "geometry.css").write_text(
                ".manual-doc { max-width: 720px; color: #111; }\n",
                encoding="utf-8",
            )
            sealed_dir = pkg / "web" / "en"
            sealed_dir.mkdir(parents=True)
            (sealed_dir / PathSegments.MANUAL_IR_JSON).write_text(
                json.dumps({"content_sha256": "deadbeef" * 8, "language": "en"}),
                encoding="utf-8",
            )
            fake_baseline = {
                "schema_version": prepared_style_audit.BASELINE_SCHEMA,
                "entries": [
                    {
                        "web_root": "pkg/web/en",
                        "ir_content_sha256": "deadbeef" * 8,
                        "issues": 1,
                    }
                ],
            }
            with mock.patch.object(prepared_style_audit, "load_baseline", return_value=fake_baseline):
                with self.assertRaisesRegex(RuntimeError, "shared style admission failed"):
                    build_declarative_package(
                        pkg,
                        lang="en",
                        output_dir=root / "out_strict",
                        repo_root=DEFAULT_REPO_ROOT,
                        skip_pin_check=True,
                        respect_baseline=False,
                    )

                code, out = _run_cli(
                    [
                        "build",
                        str(pkg),
                        "--lang",
                        "en",
                        "--out",
                        str(root / "out_baseline"),
                        "--repo-root",
                        str(DEFAULT_REPO_ROOT),
                        "--skip-pin-check",
                        "--respect-baseline",
                        "--json",
                    ]
                )
                self.assertEqual(code, 0, out)
                payload = json.loads(out)
                self.assertTrue(payload["ok"])
                self.assertTrue(payload["admission"]["baseline"])
                self.assertEqual(payload["admission"]["baseline_source"], "sealed-ir")

                # Adding a second paint issue above baseline ceiling (1) must fail closed
                (pkg / "source" / "geometry.css").write_text(
                    ".manual-doc { max-width: 720px; color: #111; background: #fff; }\n",
                    encoding="utf-8",
                )
                with self.assertRaisesRegex(RuntimeError, "shared style admission failed"):
                    build_declarative_package(
                        pkg,
                        lang="en",
                        output_dir=root / "out_grown",
                        repo_root=DEFAULT_REPO_ROOT,
                        skip_pin_check=True,
                        respect_baseline=True,
                    )


if __name__ == "__main__":
    unittest.main()
