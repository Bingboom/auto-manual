from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.manual_operations_health import build_health_report


def write_meta(root: Path, *, model: str = "M", region: str = "EU", lang: str = "en", version: str = "1", html_dir: str | None = None) -> Path:
    releases = root / "reports" / "releases"
    path = releases / model / region / lang / "latest" / "web" / "publish_meta.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"schema_version": "auto-manual-web-publish/v1", "model": model, "region": region, "lang": lang, "version": version,
                                "built_at": "2026-09-13T00:00:00Z", "git_ref": "abc123",
                                "html_dir": html_dir or f"reports/releases/{model}/{region}/{lang}/versions/{version}/web/html",
                                "html_index": f"reports/releases/{model}/{region}/{lang}/versions/{version}/web/html/index.html"}), encoding="utf-8")
    return path


class ManualOperationsHealthTests(unittest.TestCase):
    def test_encoded_and_external_references(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write_meta(root)
            html = root / "reports/releases/M/EU/en/versions/1/web/html"
            html.mkdir(parents=True)
            (html / "index.html").write_text('<img src="space%20name.png?x=1&amp;y=2"><a href="https://example.test/page">outside</a><img src=/root.png>')
            (html / "space name.png").write_bytes(b"asset")
            (html / "root.png").write_bytes(b"asset")
            report = build_health_report(root / "reports/releases", repo_root=root)
            self.assertEqual("ok", report["status"])

    def test_html_symlink_and_reference_escape_are_reported(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write_meta(root)
            html = root / "reports/releases/M/EU/en/versions/1/web/html"
            html.mkdir(parents=True)
            outside = root / "outside.html"
            outside.write_text("Outside root")
            (html / "linked.html").symlink_to(outside)
            (html / "index.html").write_text('<a href="linked.html">link</a>')
            report = build_health_report(root / "reports/releases", repo_root=root)
            self.assertEqual("failed", report["status"])
            self.assertEqual(2, report["summary"]["missing_assets"])
            self.assertIn("escapes artifact root", report["failures"][0])

    def test_release_scope_not_inferred_from_parent_of_arbitrary_root(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            releases = root / "custom"
            html = releases / "M/EU/en/versions/1/web/html"
            html.mkdir(parents=True)
            (html / "index.html").write_text("valid")
            meta = releases / "M/EU/en/latest/web/publish_meta.json"
            meta.parent.mkdir(parents=True)
            meta.write_text(json.dumps({"schema_version": "auto-manual-web-publish/v1", "model": "M", "region": "EU", "lang": "en", "version": "1", "html_dir": "custom/M/EU/en/versions/1/web/html"}))
            self.assertEqual("ok", build_health_report(releases, repo_root=root)["status"])

    def test_no_metadata_is_no_data_not_zero(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            report = build_health_report(Path(td) / "reports" / "releases")
        self.assertEqual("no_data", report["status"])
        self.assertIsNone(report["summary"]["failure_count"])
        self.assertIsNone(report["visitor_metrics"]["value"])

    def test_valid_corpus_reports_dimensions_and_all_html_files(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); write_meta(root, model="JE-X", lang="fr")
            html = root / "reports" / "releases" / "JE-X" / "EU" / "fr" / "versions" / "1" / "web" / "html"; html.mkdir(parents=True)
            (html / "index.html").write_text('<a href="article.html#top">ok</a>', encoding="utf-8")
            (html / "article.html").write_text('<img src="ok.png?v=1">', encoding="utf-8")
            (html / "ok.png").write_bytes(b"x")
            report = build_health_report(root / "reports" / "releases", repo_root=root)
        self.assertEqual("ok", report["status"])
        self.assertEqual(["JE-X"], report["dimensions"]["models"]["value"])
        self.assertEqual(2, report["entries"][0]["artifact_health"]["html_files"])

    def test_missing_query_fragment_reference_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); write_meta(root)
            html = root / "reports" / "releases" / "M" / "EU" / "en" / "versions" / "1" / "web" / "html"; html.mkdir(parents=True)
            (html / "index.html").write_text('<img src="missing.png?v=1"><a href="missing.html#x">x</a>', encoding="utf-8")
            report = build_health_report(root / "reports" / "releases", repo_root=root)
        self.assertEqual(2, report["summary"]["missing_assets"])
        self.assertEqual("failed", report["status"])

    def test_malformed_reference_is_reported_without_crashing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); write_meta(root)
            html = root / "reports" / "releases" / "M" / "EU" / "en" / "versions" / "1" / "web" / "html"; html.mkdir(parents=True)
            (html / "index.html").write_text('<a href="http://[bad">x</a>', encoding="utf-8")
            report = build_health_report(root / "reports" / "releases", repo_root=root)
        self.assertEqual("failed", report["status"])
        self.assertIn("malformed reference", report["failures"][0])

    def test_malformed_missing_html_and_outside_root_fail(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); path = write_meta(root, html_dir="/tmp/outside")
            path.write_text("[]", encoding="utf-8")
            report = build_health_report(root / "reports" / "releases", repo_root=root)
        self.assertEqual("failed", report["status"])
        self.assertEqual(1, report["summary"]["failure_count"])

    def test_outside_html_dir_is_rejected_and_invalid_dimensions_are_no_data(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); path = write_meta(root, html_dir="/tmp/outside")
            report = build_health_report(root / "reports" / "releases", repo_root=root)
            self.assertEqual("failed", report["status"])
            self.assertEqual(1, report["summary"]["failure_count"])
            path.write_text(json.dumps({"model": ["M"], "region": "EU", "lang": "en", "version": "1", "html_dir": "."}), encoding="utf-8")
            report = build_health_report(root / "reports" / "releases", repo_root=root)
        self.assertEqual("failed", report["status"])
        self.assertEqual("no_data", report["dimensions"]["models"]["status"])

    def test_wrong_web_publish_schema_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); path = write_meta(root)
            payload = json.loads(path.read_text())
            payload["schema_version"] = "other/v1"
            path.write_text(json.dumps(payload), encoding="utf-8")
            report = build_health_report(root / "reports" / "releases", repo_root=root)
        self.assertEqual("failed", report["status"])
        self.assertIn("unsupported Web Publish metadata schema", report["failures"][0])

    def test_missing_html_index_and_outside_path_are_failures(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); path = write_meta(root, html_dir="reports/releases/M/EU/en/latest/web/html")
            (root / "reports" / "releases" / "M" / "EU" / "en" / "latest" / "web" / "html").mkdir()
            report = build_health_report(root / "reports" / "releases", repo_root=root)
            self.assertEqual("failed", report["status"])
            path.write_text(json.dumps({"model": "M", "region": "EU", "lang": ["en"], "version": "1", "html_dir": "."}), encoding="utf-8")
            self.assertEqual("failed", build_health_report(root / "reports" / "releases", repo_root=root)["status"])

    def test_cli_writes_json_and_returns_failure_for_bad_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); write_meta(root)
            html = root / "reports" / "releases" / "M" / "EU" / "en" / "versions" / "1" / "web" / "html"; html.mkdir(parents=True)
            (html / "index.html").write_text('<img src="gone.png">', encoding="utf-8")
            output = root / "out.json"
            proc = subprocess.run([sys.executable, "-m", "tools.manual_operations_health", "--repo-root", str(root), "--releases-root", str(root / "reports" / "releases"), "--output", str(output)], capture_output=True, text=True)
            self.assertEqual(1, proc.returncode)
            self.assertIn('"failure_count": 1', proc.stdout)
            self.assertEqual("failed", json.loads(output.read_text())["status"])
