from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError
from urllib.request import Request

from tools import manual_operations_online_health as health


class OnlineHealthTests(unittest.TestCase):
    def record(self, *, scope="single", url="JE-TEST/EU/en/md/manual.html"):
        return {"model": "JE-TEST", "region": "EU", "lang": "en", "language_scope": scope,
                "version": "1.0", "url": url}

    def report(self, records, *, probe=None, **kwargs):
        with patch.object(health, "catalog", return_value=[{"publications": records}]):
            return health.build_online_health_report(
                Path("."), base_url="https://docs.example.test/en/latest/",
                probe=probe or (lambda _: {"status": "ok", "http_status": 200}), **kwargs,
            )

    def test_http_success_never_becomes_deployment_or_translation_proof(self):
        result = self.report([self.record()])
        self.assertEqual(result["status"], "ok")
        for field in ("deployment_identity", "translation_coverage", "visitor_metrics", "operations_owner"):
            self.assertEqual(result[field]["status"], "no_data")
        self.assertEqual(result["entries"][0]["language"], "en")

    def test_legacy_language_slot_is_not_counted_as_a_translation(self):
        result = self.report([self.record(scope="legacy_unspecified")])
        self.assertIsNone(result["entries"][0]["language"])
        self.assertEqual(result["entries"][0]["language_scope"], "legacy_unspecified")

    def test_empty_inventory_is_no_data_and_does_not_probe(self):
        probe = Mock()
        result = self.report([], probe=probe)
        self.assertEqual(result["status"], "no_data")
        self.assertIsNone(result["summary"]["http_failures"])
        probe.assert_not_called()

    def test_request_cap_and_invalid_routes_fail_before_network(self):
        probe = Mock()
        with self.assertRaisesRegex(ValueError, "request limit"):
            self.report([self.record(), self.record(url="other.html")], probe=probe, max_publications=1)
        for route in ("../private", "//other.example.test/x", "https://other.example.test/x", "/x", "x?token=secret", "x#fragment", "x\\y"):
            with self.subTest(route=route), self.assertRaises(ValueError):
                self.report([self.record(), self.record(url=route)], probe=probe)
        probe.assert_not_called()

    def test_duplicate_urls_fail_before_network(self):
        probe = Mock()
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            self.report([self.record(), self.record()], probe=probe)
        probe.assert_not_called()

    def test_url_encoding_preserves_base_path_without_query_or_fragment(self):
        self.assertEqual(health.publication_url("https://docs.example.test/en/latest", "manual name.html"),
                         "https://docs.example.test/en/latest/manual%20name.html")
        for base in ("http://docs.example.test", "https://user:secret@docs.example.test",
                     "https://docs.example.test?token=secret", "https://docs.example.test/#fragment",
                     "https://docs.example.test/\n", "https://%65xample.test/", "https://docs.example.test\\other"):
            with self.subTest(base=base), self.assertRaises(ValueError):
                health.publication_url(base, "manual.html")

    def test_redirect_keeps_head_and_rejects_cross_origin_or_credentials(self):
        handler = health._SameOriginRedirect()
        req = Request("https://docs.example.test/old.html", method="HEAD")
        redirected = handler.redirect_request(req, None, 302, "Found", {}, "https://docs.example.test/new.html")
        self.assertEqual(redirected.get_method(), "HEAD")
        for target in ("https://other.example.test/manual", "http://docs.example.test/manual",
                       "https://user:secret@docs.example.test/manual", "https://docs.example.test/manual?token=secret"):
            with self.subTest(target=target), self.assertRaises(ValueError):
                handler.redirect_request(req, None, 302, "Found", {}, target)

    def test_http_and_network_errors_are_failures_without_body_or_secret_output(self):
        for error, expected_code in (
            (HTTPError("https://docs.example.test/x", 404, "secret error", {}, None), 404),
            (URLError("secret network detail"), None),
            (ValueError("secret redirect detail"), None),
        ):
            opener = Mock()
            opener.open.side_effect = error
            with patch.object(health, "build_opener", return_value=opener):
                result = health.probe_url("https://docs.example.test/x", timeout=2)
            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["http_status"], expected_code)
            self.assertNotIn("secret", json.dumps(result))
            self.assertEqual(opener.open.call_args.args[0].get_method(), "HEAD")
            self.assertEqual(opener.open.call_args.kwargs["timeout"], 2)

    def test_http_success_and_report_failure_count(self):
        response = Mock(status=200)
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=None)
        opener = Mock()
        opener.open.return_value = response
        with patch.object(health, "build_opener", return_value=opener):
            self.assertEqual(health.probe_url("https://docs.example.test/x")["http_status"], 200)
        result = self.report([self.record()], probe=lambda _: {"status": "failed", "http_status": 404})
        self.assertEqual(result["summary"]["http_failures"], 1)
        self.assertEqual(result["status"], "failed")

    def test_real_frozen_legacy_catalog_and_cli_remain_read_only(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            web = root / "web"
            source = web / "JE-TEST/EU/md/manual.md"
            source.parent.mkdir(parents=True)
            source.write_text("# Manual\n")
            (web / "index.md").write_text("- [Jackery Test User Manual](JE-TEST/EU/md/manual.md)\n")
            before = {p: p.read_bytes() for p in web.rglob("*") if p.is_file()}
            result = health.build_online_health_report(web, base_url="https://docs.example.test/",
                probe=lambda _: {"status": "ok", "http_status": 200})
            self.assertEqual(result["summary"]["indexed_publications"], 1)
            self.assertIsNone(result["entries"][0]["language"])
            self.assertEqual(before, {p: p.read_bytes() for p in before})
            with patch.object(health, "build_online_health_report", return_value=result):
                code = health.main(["--web-root", str(web), "--base-url", "https://docs.example.test/",
                                    "--output", str(root / "report.json")])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads((root / "report.json").read_text())["status"], "ok")
