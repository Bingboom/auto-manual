from __future__ import annotations

import json
import threading
import unittest
import uuid
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from integrations.product_voc.intake import BotWriter, Intake, IntakeError, validate
from integrations.product_voc.server import MAX_BODY, make_handler
from tests import test_rtd_feedback as feedback_fixture
from tools.rtd_product_voc import normalize_endpoint, page_markup, suggestion_markup


def payload(**updates):
    return {"request_id": str(uuid.uuid4()), "suggestion": "TEST: improve the handle.",
            "model": "JE-TEST", "use_case": "TEST only", "context": "Page: JE-TEST/EU/en/md/manual.html",
            "website": "", **updates}


class ProductVocTests(unittest.TestCase):
    def test_endpoint_is_opt_in_and_https_only(self):
        self.assertEqual("", normalize_endpoint(None))
        self.assertEqual("", normalize_endpoint(""))
        self.assertEqual("", suggestion_markup(endpoint=""))
        for value in (True, [], "mailto:a@example.com", "http://example.com", "https://example.com?key=x",
                      "https://a:b@example.com", "https://example.com#x", "https://example.com/\nx"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                normalize_endpoint(value)
        self.assertEqual("https://example.com/api/voc", normalize_endpoint("https://example.com/api/voc"))

    def test_markup_escapes_and_disables_submission_without_js(self):
        html = suggestion_markup(endpoint="https://example.com/api/voc", model='\"><script>', context="<private>")
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("&lt;private&gt;", html)
        self.assertIn("<fieldset disabled>", html)
        self.assertIn("No Feishu account", html)
        self.assertIn("stored in Feishu", html)
        self.assertNotIn("appSecret", html)

    def test_legacy_context_does_not_invent_language(self):
        html = page_markup(endpoint="https://example.com/api/voc", pagename="JE-TEST/EU/md/manual", root="index",
                           publications=[{"url": "JE-TEST/EU/md/manual.html", "model": "JE-TEST", "region": "EU"}])
        self.assertIn("Language: unverified", html)
        self.assertIn("Version: unverified", html)
        self.assertEqual("", page_markup(endpoint="https://example.com/api/voc", publications=[], pagename="search", root="index"))

    def test_real_sphinx_opt_in_on_home_single_and_legacy(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            source, assets = feedback_fixture.RtdFeedbackTests._fixture(root, channels=[], include_legacy=True)
            baseline = feedback_fixture.RtdFeedbackTests._build(source, root / "off")
            old = (baseline / "JE-TEST/EU/md/manual_legacy.html").read_bytes()
            settings = json.loads((assets / "settings.json").read_text())
            settings["product_voc_endpoint"] = "https://example.com/api/voc"
            (assets / "settings.json").write_text(json.dumps(settings))
            output = feedback_fixture.RtdFeedbackTests._build(source, root / "on")
            for name in ("index.html", "JE-TEST/EU/fr/md/manual.html", "JE-TEST/EU/md/manual_legacy.html"):
                html = (output / name).read_text()
                self.assertIn("data-product-voc", html)
                self.assertIn("product-voc.js", html)
                self.assertIn("product-voc.css", html)
                self.assertNotIn("manual-feedback", html)
            self.assertNotIn("product-voc", (output / "search.html").read_text())
            settings["product_voc_endpoint"] = ""
            (assets / "settings.json").write_text(json.dumps(settings))
            rollback = feedback_fixture.RtdFeedbackTests._build(source, root / "rollback")
            self.assertEqual(old, (rollback / "JE-TEST/EU/md/manual_legacy.html").read_bytes())

    def test_javascript_has_no_automatic_telemetry_or_credentials(self):
        script = (Path(__file__).parents[1] / "tools/rtd_portal_assets/_static/product-voc.js").read_text()
        self.assertIn('form.addEventListener("submit"', script)
        self.assertIn('credentials: "omit"', script)
        self.assertIn('referrerPolicy: "no-referrer"', script)
        self.assertIn("AbortController", script)
        for forbidden in ("localStorage", "document.cookie", "window.location", "innerHTML", "app_secret"):
            self.assertNotIn(forbidden, script)


class IntakeTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.writer = Mock()
        self.writer.create.return_value = "recTEST"
        self.intake = Intake(Path(self.temp.name) / "state.sqlite", self.writer)
        self.sleeper = patch("integrations.product_voc.intake.time.sleep")
        self.sleeper.start()

    def tearDown(self):
        self.intake.db.close()
        self.sleeper.stop()
        self.temp.cleanup()

    def test_schema_and_size_constraints(self):
        for invalid in ([], {}, payload(suggestion="a"), payload(suggestion="x" * 3001), payload(model=""),
                        payload(use_case=None), payload(context="\x00"), payload(website="spam"),
                        payload(table="tblEVIL"), payload(request_id="--bad")):
            with self.subTest(invalid=str(invalid)[:80]), self.assertRaises(IntakeError):
                validate(invalid)

    def test_literal_multilingual_text_is_preserved(self):
        request_id, fields = validate(payload(suggestion="优化提手\n日本語 تحسين المنتج $(whoami)"))
        self.assertIn("$(whoami)", fields["Your suggestion"])
        self.assertIn("Submission: " + request_id, fields["Manual context"])
        self.assertEqual(set(fields), {"Your suggestion", "Product model", "Use case", "Manual context"})

    def test_write_is_verified_and_retry_does_not_duplicate(self):
        body = payload()
        self.assertTrue(self.intake.submit(body, "peer")["ok"])
        self.assertTrue(self.intake.submit(body, "peer")["ok"])
        self.writer.create.assert_called_once()
        self.writer.verify.assert_called_once()

    def test_readback_failure_retries_only_verification(self):
        body = payload()
        self.writer.verify.side_effect = [RuntimeError("not visible"), None]
        with self.assertRaises(IntakeError) as caught:
            self.intake.submit(body, "peer")
        self.assertEqual(503, caught.exception.status)
        self.assertTrue(self.intake.submit(body, "peer")["ok"])
        self.writer.create.assert_called_once()
        self.assertEqual(2, self.writer.verify.call_count)

    def test_ambiguous_write_never_blindly_retries(self):
        body = payload()
        self.writer.create.side_effect = TimeoutError()
        for status in (503, 409):
            with self.assertRaises(IntakeError) as caught:
                self.intake.submit(body, "peer")
            self.assertEqual(status, caught.exception.status)
        self.writer.create.assert_called_once()

    def test_restart_keeps_idempotency(self):
        body = payload()
        self.intake.submit(body, "peer")
        self.intake.db.close()
        self.intake = Intake(Path(self.temp.name) / "state.sqlite", self.writer)
        self.intake.submit(body, "peer")
        self.writer.create.assert_called_once()

    def test_changed_payload_cannot_reuse_reference(self):
        body = payload()
        self.intake.submit(body, "peer")
        with self.assertRaises(IntakeError) as caught:
            self.intake.submit({**body, "model": "OTHER"}, "peer")
        self.assertEqual(409, caught.exception.status)

    def test_rate_limit_and_bounded_memory(self):
        for _ in range(5):
            self.intake.submit(payload(), "peer")
        with self.assertRaises(IntakeError) as caught:
            self.intake.submit(payload(), "peer")
        self.assertEqual(429, caught.exception.status)
        self.assertNotIn("peer", self.intake.attempts)
        self.intake.attempts["empty"] = []
        self.intake.submit(payload(), "another-peer")

    def test_cli_uses_fixed_argv_no_shell_and_readback(self):
        writer = BotWriter(base="BaseTEST", table="tblTEST")
        _, fields = validate(payload())
        responses = [
            {"record": {"id": "recTEST"}},
            {"record_id_list": ["recTEST"], "fields": list(fields), "data": [list(fields.values())]},
        ]
        with patch("integrations.product_voc.intake.subprocess.run") as run:
            run.side_effect = [Mock(returncode=0, stdout=json.dumps({"ok": True, "identity": "bot", "data": data})) for data in responses]
            record = writer.create(fields)
            writer.verify(record, fields)
            self.assertFalse(run.call_args.kwargs.get("shell", False))
            self.assertIn("--as", run.call_args.args[0])
            self.assertIn("tblTEST", run.call_args.args[0])


class HttpTests(unittest.TestCase):
    def setUp(self):
        self.intake = Mock()
        self.intake.submit.return_value = {"ok": True, "reference": "test"}
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(self.intake, {"https://ht-doc.readthedocs.io"}))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def request(self, method="POST", path="/api/voc", body=None, **headers):
        connection = HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        headers = {"Origin": "https://ht-doc.readthedocs.io", "Content-Type": "application/json", **headers}
        connection.request(method, path, body=json.dumps(body or payload()), headers=headers)
        response = connection.getresponse()
        result = response.status, dict(response.getheaders()), response.read()
        connection.close()
        return result

    def test_anonymous_json_post_and_exact_cors_origin(self):
        status, headers, body = self.request()
        self.assertEqual(200, status)
        self.assertEqual("https://ht-doc.readthedocs.io", headers["Access-Control-Allow-Origin"])
        self.assertNotIn("Access-Control-Allow-Credentials", headers)
        self.assertTrue(json.loads(body)["ok"])

    def test_bad_origins_paths_types_and_oversize_never_reach_writer(self):
        cases = [({"Origin": "https://evil.example"}, 403), ({"Content-Type": "text/plain"}, 400),
                 ({"Content-Length": str(MAX_BODY + 1)}, 413)]
        for headers, expected in cases:
            self.assertEqual(expected, self.request(**headers)[0])
        for path in ("/api/voc?command=x", "/", "/agent", "/records"):
            self.assertEqual(404, self.request(path=path)[0])
        self.intake.submit.assert_not_called()

    def test_preflight_get_and_no_public_record_access(self):
        self.assertEqual(204, self.request(method="OPTIONS", **{
            "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "content-type"})[0])
        self.assertEqual(404, self.request(method="GET")[0])
        self.assertEqual(404, self.request(method="GET", path="/preview")[0])
        self.assertEqual(200, self.request(method="GET", path="/healthz")[0])

    def test_proxy_address_is_not_trusted_by_default(self):
        self.request(**{"CF-Connecting-IP": "spoofed-client"})
        self.assertEqual("127.0.0.1", self.intake.submit.call_args.args[1])
