from __future__ import annotations

import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from tools.rtd import deployment_receipt as receipt
from tools.rtd import private_build_verify as private_verify
from tools import verify_web_deployment_targets as verifier


BASE_URL = "https://ht-doc.readthedocs.io"
PAGE_ONE = "JE-1000F/US/en/md/manual_je1000f_us.html"
PAGE_TWO = "JE-2000E/EU/de/md/manual_je2000e_eu_de.html"


def fast_session(**kwargs) -> receipt.FetchSession:
    """Unpaced session: these tests exercise verdicts, not wall-clock politeness."""
    kwargs.setdefault("min_interval", 0)
    return receipt.FetchSession(**kwargs)


def _manifest_payload() -> dict:
    return {
        "schema_version": verifier.MANIFEST_SCHEMA,
        "built_at": "2026-09-18T00:00:00+00:00",
        "targets": [
            {
                "model": "JE-2000E",
                "region": "EU",
                "lang": "de",
                "route": "JE-2000E/EU/de/md",
                "manual": "manual_je2000e_eu_de.md",
            },
            {
                "model": "JE-1000F",
                "region": "US",
                "lang": "en",
                "route": "JE-1000F/US/en/md",
                "manual": "manual_je1000f_us.md",
            },
        ],
    }


def _injection_block(path: str, slug: str) -> bytes:
    return (
        b'<script async type="text/javascript" '
        b'src="/_/static/javascript/readthedocs-addons.js"></script>'
        b'<meta name="readthedocs-project-slug" content="' + slug.encode() + b'" />'
        b'<meta name="readthedocs-version-slug" content="latest" />'
        b'<meta name="readthedocs-resolver-filename" content="/' + path.encode() + b'" />'
        b'<meta name="readthedocs-http-status" content="200" />'
    )


class ManifestTargetsTests(unittest.TestCase):
    def test_extracts_sorted_canonical_pages(self) -> None:
        targets = verifier.manifest_targets(_manifest_payload())
        self.assertEqual([PAGE_ONE, PAGE_TWO], [target["page"] for target in targets])
        self.assertEqual(
            {"model": "JE-1000F", "region": "US", "lang": "en", "page": PAGE_ONE},
            targets[0],
        )

    def test_rejects_tampered_or_unsafe_catalog_entries(self) -> None:
        for mutate, message in (
            (lambda p: p.update(schema_version="other/v1"), "schema"),
            (lambda p: p.update(targets=[]), "no targets"),
            (lambda p: p["targets"][0].update(model="../evil"), "unsafe model"),
            (lambda p: p["targets"][0].update(manual="dir/manual.md"), "unsafe manual"),
            (lambda p: p["targets"][0].update(manual="manual.txt"), "unsafe manual"),
            (lambda p: p["targets"][0].update(route="JE-1000F/US/en/md"), "route does not match"),
            (lambda p: p["targets"][0].pop("lang"), "unsafe lang"),
        ):
            payload = _manifest_payload()
            mutate(payload)
            with self.subTest(message=message):
                with self.assertRaisesRegex(ValueError, message):
                    verifier.manifest_targets(payload)


class ExpectedProjectSlugTests(unittest.TestCase):
    def test_derives_from_rtd_base_url_and_accepts_override(self) -> None:
        self.assertEqual("ht-doc", verifier.expected_project_slug(BASE_URL))
        self.assertEqual("custom", verifier.expected_project_slug(BASE_URL, "custom"))

    def test_underivable_host_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "expected RTD project slug"):
            verifier.expected_project_slug("https://manuals.example.com")


class FetchManifestBytesTests(unittest.TestCase):
    def test_rejects_non_https_and_credentialed_urls(self) -> None:
        for url in ("http://example.org/manifest.json", "https://user:pw@example.org/m.json"):
            with self.subTest(url=url):
                with self.assertRaisesRegex(ValueError, "HTTPS"):
                    verifier.fetch_manifest_bytes(url)


class DeploymentVerificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.publish = root / "publish"
        self.web = self.publish / "web"
        self.web.mkdir(parents=True)
        (self.web / "index.md").write_text("frozen source")
        (self.publish / verifier.PUBLISH_MANIFEST).write_text(
            json.dumps(_manifest_payload()), encoding="utf-8"
        )
        self.output = root / "html"
        for page in (PAGE_ONE, PAGE_TWO):
            path = self.output / page
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(
                b"<html><head></head><body>" + page.encode() + b"</body></html>"
            )
        app = SimpleNamespace(
            srcdir=self.web, outdir=self.output, builder=SimpleNamespace(format="html")
        )
        receipt.write_deployment_receipt(app, None)
        self.slugs = {PAGE_ONE: "ht-doc", PAGE_TWO: "ht-doc"}
        self.targets = verifier.manifest_targets(_manifest_payload())

    def serve(self, url: str) -> bytes:
        path = url.removeprefix(BASE_URL + "/")
        data = (self.output / path).read_bytes()
        if path.endswith(".html"):
            data = data.replace(b"</head>", _injection_block(path, self.slugs[path]) + b"</head>")
        return data

    def test_full_verification_passes_every_target(self) -> None:
        with patch.object(receipt, "_fetch", side_effect=self.serve):
            results = verifier.verify_targets_against_source(
                self.web, base_url=BASE_URL, targets=self.targets, project_slug="ht-doc",
                session=fast_session()
            )
        self.assertEqual(["ok", "ok"], [entry["status"] for entry in results])
        self.assertEqual(["frozen-source", "frozen-source"], [entry["mode"] for entry in results])

    def test_full_verification_attributes_the_wrong_site_target(self) -> None:
        self.slugs[PAGE_TWO] = "impostor-project"
        with patch.object(receipt, "_fetch", side_effect=self.serve):
            results = verifier.verify_targets_against_source(
                self.web, base_url=BASE_URL, targets=self.targets, project_slug="ht-doc",
                session=fast_session()
            )
        by_page = {entry["page"]: entry for entry in results}
        self.assertEqual("ok", by_page[PAGE_ONE]["status"])
        self.assertEqual("failed", by_page[PAGE_TWO]["status"])
        self.assertIn("impostor-project", by_page[PAGE_TWO]["error"])

    def test_full_verification_attributes_drifted_bytes(self) -> None:
        (self.output / PAGE_ONE).write_bytes(
            b"<html><head></head><body>silently replaced</body></html>"
        )
        with patch.object(receipt, "_fetch", side_effect=self.serve):
            results = verifier.verify_targets_against_source(
                self.web, base_url=BASE_URL, targets=self.targets, project_slug="ht-doc",
                session=fast_session()
            )
        by_page = {entry["page"]: entry for entry in results}
        self.assertEqual("failed", by_page[PAGE_ONE]["status"])
        self.assertIn("bytes differ", by_page[PAGE_ONE]["error"])
        self.assertEqual("ok", by_page[PAGE_TWO]["status"])

    def test_live_slug_mode_detects_foreign_and_missing_slugs(self) -> None:
        self.slugs[PAGE_TWO] = "impostor-project"
        with patch.object(receipt, "_fetch", side_effect=self.serve):
            results = verifier.verify_targets_live_slug(
                base_url=BASE_URL, targets=self.targets, project_slug="ht-doc",
                session=fast_session(),
            )
        by_page = {entry["page"]: entry for entry in results}
        self.assertEqual("ok", by_page[PAGE_ONE]["status"])
        self.assertIn("impostor-project", by_page[PAGE_TWO]["error"])

        def serve_plain(url: str) -> bytes:
            return (self.output / url.removeprefix(BASE_URL + "/")).read_bytes()

        with patch.object(receipt, "_fetch", side_effect=serve_plain):
            results = verifier.verify_targets_live_slug(
                base_url=BASE_URL, targets=self.targets, project_slug="ht-doc",
                session=fast_session(),
            )
        self.assertEqual({"failed"}, {entry["status"] for entry in results})
        self.assertIn("never declared", results[0]["error"])

    def test_live_slug_mode_reports_unreachable_pages(self) -> None:
        def refuse(url: str) -> bytes:
            raise ValueError("Deployment response is not same-origin HTTP 200")

        with patch.object(receipt, "_fetch", side_effect=refuse):
            results = verifier.verify_targets_live_slug(
                base_url=BASE_URL, targets=self.targets, project_slug="ht-doc",
                session=fast_session(),
            )
        self.assertEqual({"failed"}, {entry["status"] for entry in results})
        self.assertIn("HTTP 200", results[0]["error"])

    def test_main_full_mode_json_and_limit(self) -> None:
        stdout = io.StringIO()
        with patch.object(receipt, "_fetch", side_effect=self.serve):
            with contextlib.redirect_stdout(stdout):
                code = verifier.main(
                    [
                        "--publish-root", str(self.publish),
                        "--base-url", BASE_URL,
                        "--limit", "1",
                        "--rps", "0",
                        "--json",
                    ]
                )
        self.assertEqual(0, code)
        report = json.loads(stdout.getvalue())
        self.assertEqual(verifier.REPORT_SCHEMA, report["schema"])
        self.assertEqual("verified", report["status"])
        self.assertEqual("live-html", report["verification_mode"])
        self.assertEqual(1, report["targets_checked"])
        self.assertEqual("ht-doc", report["expected_project_slug"])

    def test_main_exits_nonzero_on_any_failed_target(self) -> None:
        self.slugs[PAGE_TWO] = "impostor-project"
        stdout = io.StringIO()
        with patch.object(receipt, "_fetch", side_effect=self.serve):
            with contextlib.redirect_stdout(stdout):
                code = verifier.main(
                    ["--publish-root", str(self.publish), "--base-url", BASE_URL, "--rps", "0"]
                )
        self.assertEqual(1, code)
        text = stdout.getvalue()
        self.assertIn("MISMATCH JE-2000E/EU/de", text)
        self.assertIn("[wrong-site]", text)
        self.assertIn("TARGET MISMATCH: 1 target(s) disproved (wrong-site 1)", text)
        self.assertIn("OK JE-1000F/US/en", text)

    def test_report_with_no_results_is_not_verified(self) -> None:
        report = verifier.build_report(base_url=BASE_URL, project_slug="ht-doc", results=[])
        self.assertEqual("failed", report["status"])

    # --- rate-limit classification (Hello-Docs run 35432328072 regression) ---

    def throttling_serve(self, *pages: str):
        """Serve normally except for `pages`, which the host rate-limits."""
        blocked = set(pages)

        def serve(url: str) -> bytes:
            path = url.removeprefix(BASE_URL + "/")
            if path in blocked:
                raise receipt.DeploymentThrottled(
                    f"Deployment host rate-limited the request (HTTP 429): {url}",
                    retry_after=None,
                )
            return self.serve(url)

        return serve

    def test_rate_limited_target_is_throttled_not_mismatched(self) -> None:
        with patch.object(receipt, "sleep"):
            with patch.object(receipt, "_fetch", side_effect=self.throttling_serve(PAGE_TWO)):
                results = verifier.verify_targets_against_source(
                    self.web, base_url=BASE_URL, targets=self.targets,
                    project_slug="ht-doc", session=fast_session(),
                )
        by_page = {entry["page"]: entry for entry in results}
        self.assertEqual("ok", by_page[PAGE_ONE]["status"])
        self.assertEqual("throttled", by_page[PAGE_TWO]["status"])
        self.assertIn("DeploymentThrottled", by_page[PAGE_TWO]["error"])
        report = verifier.build_report(base_url=BASE_URL, project_slug="ht-doc", results=results)
        self.assertEqual("throttled", report["status"])
        self.assertEqual(0, report["targets_failed"])
        self.assertEqual(1, report["targets_throttled"])
        self.assertEqual(verifier.EXIT_THROTTLED, verifier.exit_code_for(report["status"]))

    def test_exhausted_budget_stops_requesting_and_marks_the_rest_throttled(self) -> None:
        attempts = []

        def refuse(url: str) -> bytes:
            attempts.append(url)
            raise receipt.DeploymentThrottled("rate limited", retry_after=None)

        with patch.object(receipt, "sleep"):
            with patch.object(receipt, "_fetch", side_effect=refuse):
                session = fast_session(retry_budget=0.0)
                results = verifier.verify_targets_against_source(
                    self.web, base_url=BASE_URL, targets=self.targets,
                    project_slug="ht-doc", session=session,
                )
        self.assertEqual({"throttled"}, {entry["status"] for entry in results})
        self.assertTrue(session.budget_exhausted)
        # Once the budget is gone the checker stops adding load: the batch's
        # single receipt attempt is all that reached the wire.
        self.assertEqual(1, len(attempts))

    def test_a_real_mismatch_outranks_throttling_in_the_verdict(self) -> None:
        (self.output / PAGE_ONE).write_bytes(
            b"<html><head></head><body>silently replaced</body></html>"
        )
        with patch.object(receipt, "sleep"):
            with patch.object(receipt, "_fetch", side_effect=self.throttling_serve(PAGE_TWO)):
                results = verifier.verify_targets_against_source(
                    self.web, base_url=BASE_URL, targets=self.targets,
                    project_slug="ht-doc", session=fast_session(),
                )
        by_page = {entry["page"]: entry for entry in results}
        self.assertEqual("failed", by_page[PAGE_ONE]["status"])
        self.assertEqual("throttled", by_page[PAGE_TWO]["status"])
        report = verifier.build_report(base_url=BASE_URL, project_slug="ht-doc", results=results)
        self.assertEqual("failed", report["status"])
        self.assertEqual(verifier.EXIT_FAILED, verifier.exit_code_for(report["status"]))

    def test_mismatch_is_not_retried_as_if_it_were_a_rate_limit(self) -> None:
        (self.output / PAGE_ONE).write_bytes(
            b"<html><head></head><body>silently replaced</body></html>"
        )
        slept = []
        with patch.object(receipt, "sleep", side_effect=slept.append):
            with patch.object(receipt, "_fetch", side_effect=self.serve):
                session = fast_session()
                results = verifier.verify_targets_against_source(
                    self.web, base_url=BASE_URL, targets=self.targets,
                    project_slug="ht-doc", session=session,
                )
        self.assertEqual("failed", results[0]["status"])
        self.assertEqual([], slept)
        self.assertEqual(0, session.throttle_waits)

    def test_attribution_replays_the_cache_instead_of_refetching_each_closure(self) -> None:
        """The storm's amplifier: per-target re-verification re-fetching everything."""
        (self.output / PAGE_ONE).write_bytes(
            b"<html><head></head><body>silently replaced</body></html>"
        )
        with patch.object(receipt, "_fetch", side_effect=self.serve):
            session = fast_session()
            verifier.verify_targets_against_source(
                self.web, base_url=BASE_URL, targets=self.targets,
                project_slug="ht-doc", session=session,
            )
        # receipt + both pages, each fetched exactly once across the failing
        # batch AND the two-target attribution pass that follows it.
        self.assertEqual(3, session.requests)
        self.assertGreaterEqual(session.cache_hits, 3)

    def test_live_slug_mode_classifies_rate_limits_as_throttled(self) -> None:
        with patch.object(receipt, "sleep"):
            with patch.object(receipt, "_fetch", side_effect=self.throttling_serve(PAGE_ONE)):
                results = verifier.verify_targets_live_slug(
                    base_url=BASE_URL, targets=self.targets,
                    project_slug="ht-doc", session=fast_session(),
                )
        by_page = {entry["page"]: entry for entry in results}
        self.assertEqual("throttled", by_page[PAGE_ONE]["status"])
        self.assertEqual("ok", by_page[PAGE_TWO]["status"])

    def test_main_exits_75_and_advises_a_rerun_when_only_throttled(self) -> None:
        stdout = io.StringIO()
        with patch.object(receipt, "sleep"):
            with patch.object(receipt, "_fetch", side_effect=self.throttling_serve(PAGE_TWO)):
                with contextlib.redirect_stdout(stdout):
                    code = verifier.main([
                        "--publish-root", str(self.publish),
                        "--base-url", BASE_URL, "--rps", "0",
                    ])
        self.assertEqual(75, code)
        text = stdout.getvalue()
        self.assertIn("THROTTLED JE-2000E/EU/de", text)
        self.assertIn("OK JE-1000F/US/en", text)
        self.assertIn("1 verified / 0 mismatched / 0 unverifiable / 1 throttled of 2", text)
        self.assertIn("no target was disproved", text)

    def test_report_json_file_carries_the_classification_counts(self) -> None:
        path = Path(self.temp.name) / "report.json"
        with patch.object(receipt, "sleep"):
            with patch.object(receipt, "_fetch", side_effect=self.throttling_serve(PAGE_TWO)):
                with contextlib.redirect_stdout(io.StringIO()):
                    code = verifier.main([
                        "--publish-root", str(self.publish),
                        "--base-url", BASE_URL, "--rps", "0",
                        "--report-json", str(path),
                    ])
        self.assertEqual(75, code)
        report = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual("throttled", report["status"])
        self.assertEqual(2, report["targets_checked"])
        self.assertEqual(0, report["targets_failed"])
        self.assertEqual(1, report["targets_throttled"])
        self.assertIn("requests", report["transport"])

    def test_markup_scope_skips_binary_assets_but_still_demands_they_exist(self) -> None:
        """The daily budget trim must not become a link-integrity hole."""
        asset = "_static/manual-assets/JE-1000F/US/en/md/diagram.png"
        (self.output / asset).parent.mkdir(parents=True, exist_ok=True)
        (self.output / asset).write_bytes(b"\x89PNG binary")
        (self.output / PAGE_ONE).write_bytes(
            b'<html><head></head><body><img src="/' + asset.encode() + b'"></body></html>'
        )
        app = SimpleNamespace(
            srcdir=self.web, outdir=self.output, builder=SimpleNamespace(format="html")
        )
        receipt.write_deployment_receipt(app, None)

        fetched = []

        def serve(url: str) -> bytes:
            fetched.append(url.removeprefix(BASE_URL + "/"))
            return self.serve(url)

        with patch.object(receipt, "_fetch", side_effect=serve):
            result = receipt.verify_deployment(
                self.web, BASE_URL, [PAGE_ONE], expected_project_slug="ht-doc",
                session=fast_session(), include_dependency=receipt.markup_dependency,
            )
        self.assertNotIn(asset, fetched)
        self.assertEqual(1, result["unfetched_dependencies"])

        # Full scope does download it...
        fetched.clear()
        with patch.object(receipt, "_fetch", side_effect=serve):
            result = receipt.verify_deployment(
                self.web, BASE_URL, [PAGE_ONE], expected_project_slug="ht-doc",
                session=fast_session(),
            )
        self.assertIn(asset, fetched)
        self.assertEqual(0, result["unfetched_dependencies"])

        # ...and markup scope still fails closed when the asset is missing
        # from the served receipt, so drift cannot hide behind the trim.
        (self.output / asset).unlink()
        receipt.write_deployment_receipt(app, None)
        with patch.object(receipt, "_fetch", side_effect=serve):
            with self.assertRaisesRegex(ValueError, "lacks a referenced resource"):
                receipt.verify_deployment(
                    self.web, BASE_URL, [PAGE_ONE], expected_project_slug="ht-doc",
                    session=fast_session(), include_dependency=receipt.markup_dependency,
                )

    def test_asset_scope_defaults_to_markup_and_is_recorded_in_the_report(self) -> None:
        path = Path(self.temp.name) / "scope.json"
        with patch.object(receipt, "_fetch", side_effect=self.serve):
            with contextlib.redirect_stdout(io.StringIO()):
                code = verifier.main([
                    "--publish-root", str(self.publish), "--base-url", BASE_URL,
                    "--rps", "0", "--report-json", str(path),
                ])
        self.assertEqual(0, code)
        self.assertEqual("markup", json.loads(path.read_text())["asset_scope"])
        self.assertEqual("markup", verifier.parse_args([]).asset_scope)
        self.assertEqual("full", verifier.parse_args(["--asset-scope", "full"]).asset_scope)

    # --- unverifiable vs. mismatched (Hello-Docs runs 47-80: sign-in redirect) ---

    LOGIN = "https://app.readthedocs.com/accounts/login/?next=/en/latest/manual-deployment.json"

    def redirecting_serve(self, *pages: str, to: str | None = None):
        """Serve normally except for `pages`, which redirect off-site (default: sign-in)."""
        blocked = set(pages)
        destination = to or self.LOGIN

        def serve(url: str) -> bytes:
            if url.removeprefix(BASE_URL + "/") in blocked:
                raise receipt.CrossOriginRedirect(destination)
            return self.serve(url)

        return serve

    def test_sign_in_redirect_is_unverifiable_and_asked_once(self) -> None:
        """The month-long red run: a login-gated receipt read as 49 mismatches + a 429 storm."""
        calls = []
        serve = self.redirecting_serve(receipt.RECEIPT)

        def counting(url: str) -> bytes:
            calls.append(url)
            return serve(url)

        stdout = io.StringIO()
        path = Path(self.temp.name) / "login.json"
        with patch.object(receipt, "_fetch", side_effect=counting):
            with contextlib.redirect_stdout(stdout):
                code = verifier.main([
                    "--publish-root", str(self.publish), "--base-url", BASE_URL,
                    "--rps", "0", "--report-json", str(path),
                ])
        self.assertEqual(verifier.EXIT_UNDECIDED, code)
        report = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual("unverifiable", report["status"])
        self.assertEqual(
            {"verified": 0, "mismatched": 0, "unverifiable": 2, "throttled": 0}, report["counts"]
        )
        self.assertEqual({"login-required": 2}, report["undecided_categories"])
        self.assertTrue(report["headline"].startswith("UNVERIFIABLE: the site redirected"))
        # Legacy readers compute verified = checked - failed - throttled; it must stay 0.
        self.assertEqual(0, report["targets_failed"])
        self.assertEqual(2, report["targets_throttled"])
        # The redirect is replayed from the session, not re-requested per target.
        self.assertEqual(1, len(calls))
        self.assertEqual(2, report["transport"]["failure_replays"])
        text = stdout.getvalue()
        self.assertIn("UNVERIFIABLE: the site redirected the anonymous verifier", text)
        self.assertIn("UNVERIFIABLE JE-1000F/US/en", text)
        self.assertIn("(to https://app.readthedocs.com/accounts/login/)", text)
        self.assertNotIn("next=", text)
        self.assertNotIn("MISMATCH", text)

    def test_a_real_mismatch_outranks_unverifiable_and_is_printed_first(self) -> None:
        (self.output / PAGE_ONE).write_bytes(
            b"<html><head></head><body>silently replaced</body></html>"
        )
        stdout = io.StringIO()
        with patch.object(receipt, "_fetch", side_effect=self.redirecting_serve(PAGE_TWO)):
            with contextlib.redirect_stdout(stdout):
                code = verifier.main([
                    "--publish-root", str(self.publish), "--base-url", BASE_URL, "--rps", "0",
                ])
        self.assertEqual(verifier.EXIT_FAILED, code)
        lines = stdout.getvalue().splitlines()
        self.assertIn("TARGET MISMATCH: 1 target(s) disproved (content-differs 1)", lines[0])
        self.assertIn("1 mismatched / 1 unverifiable", lines[1])
        verdicts = [line.split()[1] for line in lines if "/md/" in line]
        self.assertEqual(["MISMATCH", "UNVERIFIABLE"], verdicts)

    def test_failure_categories(self) -> None:
        cases = (
            (receipt.CrossOriginRedirect(self.LOGIN), ("unverifiable", "login-required")),
            (receipt.CrossOriginRedirect("https://evil.example/page.html"), ("failed", "redirect")),
            (HTTPError(BASE_URL, 404, "nf", {}, None), ("failed", "not-found")),
            (HTTPError(BASE_URL, 403, "no", {}, None), ("unverifiable", "access-denied")),
            (HTTPError(BASE_URL, 502, "bad", {}, None), ("unverifiable", "transport")),
            (URLError(ConnectionResetError()), ("unverifiable", "transport")),
            (TimeoutError("Deployment read exceeded its time budget"), ("unverifiable", "transport")),
            (receipt.DeploymentThrottled("429"), ("throttled", "rate-limited")),
            (ValueError("Live deployment does not match frozen source"),
             ("failed", "stale-deployment")),
            (ValueError("Live deployment bytes differ: x.html"), ("failed", "content-differs")),
            (ValueError("Live deployment declares RTD project a instead of b: x"),
             ("failed", "wrong-site")),
            (ValueError("Deployment receipt lacks selected routes"),
             ("failed", "missing-from-deployment")),
            (ValueError("something new"), ("failed", "other")),
        )
        for exc, expected in cases:
            with self.subTest(exc=repr(exc)):
                self.assertEqual(expected, verifier.classify_failure(exc))

    def test_shared_callers_keep_the_two_way_split_by_default(self) -> None:
        """The receipt-link lane gates a Bitable write on ok/failed/throttled; unchanged."""
        with patch.object(receipt, "_fetch", side_effect=self.redirecting_serve(receipt.RECEIPT)):
            results = verifier.verify_targets_against_source(
                self.web, base_url=BASE_URL, targets=self.targets,
                project_slug="ht-doc", session=fast_session(),
            )
        self.assertEqual({"failed"}, {entry["status"] for entry in results})
        self.assertEqual({"login-required"}, {entry["category"] for entry in results})

    def test_live_slug_mode_separates_unreadable_pages_when_asked(self) -> None:
        with patch.object(receipt, "_fetch", side_effect=self.redirecting_serve(PAGE_ONE)):
            results = verifier.verify_targets_live_slug(
                base_url=BASE_URL, targets=self.targets, project_slug="ht-doc",
                session=fast_session(), separate_unverifiable=True,
            )
        by_page = {entry["page"]: entry for entry in results}
        self.assertEqual("unverifiable", by_page[PAGE_ONE]["status"])
        self.assertEqual("ok", by_page[PAGE_TWO]["status"])

    def test_rps_flag_sets_the_shared_pace_and_rejects_negatives(self) -> None:
        session = verifier._session(verifier.parse_args(["--rps", "4"]))
        self.assertAlmostEqual(0.25, session.min_interval)
        self.assertEqual(0.0, verifier._session(verifier.parse_args(["--rps", "0"])).min_interval)
        default = verifier._session(verifier.parse_args([]))
        self.assertAlmostEqual(1.0 / verifier.DEFAULT_RPS, default.min_interval)
        with self.assertRaisesRegex(ValueError, "--rps"):
            verifier._session(verifier.parse_args(["--rps", "-1"]))


class PrivateRtdDeploymentVerificationTests(unittest.TestCase):
    BUSINESS_BASE_URL = "https://ht-docs-ht-manuals.readthedocs-hosted.com/en/latest"
    CAS_LOGIN = "https://app.readthedocs.com/cas/login"

    def setUp(self) -> None:
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self._git("init")
        self._git("config", "user.email", "test@example.invalid")
        self._git("config", "user.name", "Test User")
        (self.repo / "README.md").write_text("init\n", encoding="utf-8")
        self._git("add", "README.md")
        self._git("commit", "-m", "chore: initial commit")
        self.pre_publish_sha = self._git("rev-parse", "HEAD")

        self.publish = self.repo / "docs" / "publish"
        self.web = self.publish / "web"
        self.web.mkdir(parents=True)
        (self.web / "conf.py").write_text('project = "Test"\n', encoding="utf-8")
        (self.web / "index.md").write_text("# Library\n", encoding="utf-8")
        asset = self.web / "_static" / "manual-assets" / "diagram.png"
        asset.parent.mkdir(parents=True, exist_ok=True)
        asset.write_bytes(b"\x89PNG\r\n\x1a\n")
        for page in (PAGE_ONE, PAGE_TWO):
            route = Path(page).parent
            stem = Path(page).stem
            target_dir = self.web / route
            target_dir.mkdir(parents=True, exist_ok=True)
            (target_dir / "index.md").write_text(
                f"# Manual\n\n```{{toctree}}\n{stem}\n```\n",
                encoding="utf-8",
            )
            (target_dir / f"{stem}.md").write_text(
                '<img src="../../../../_static/manual-assets/diagram.png"/>\n',
                encoding="utf-8",
            )
        (self.publish / verifier.PUBLISH_MANIFEST).write_text(
            json.dumps(_manifest_payload()), encoding="utf-8"
        )
        self._git("add", "docs/publish")
        self._git("commit", "-m", "feat(publish): publish web manuals")
        self.publish_sha = self._git("rev-parse", "HEAD")

        (self.repo / "knowledge.txt").write_text("update\n", encoding="utf-8")
        self._git("add", "knowledge.txt")
        self._git("commit", "-m", "chore(knowledge): non-publish update")
        self.head_sha = self._git("rev-parse", "HEAD")

    def _git(self, *args: str) -> str:
        return subprocess.check_output(
            ["git", "-C", str(self.repo), *args], text=True
        ).strip()

    def _cas_redirect(self, _url: str) -> bytes:
        raise receipt.CrossOriginRedirect(self.CAS_LOGIN)

    def _fake_builds_opener(self, builds_payload: dict):
        seen: list[tuple[str, str | None]] = []

        def opener(request, timeout=30):
            seen.append((request.full_url, request.get_header("Authorization")))
            return io.BytesIO(json.dumps(builds_payload).encode("utf-8"))

        return opener, seen

    def test_private_cas_login_without_token_fails_fast_unverifiable(self) -> None:
        calls: list[str] = []

        def probe(url: str) -> bytes:
            calls.append(url)
            raise receipt.CrossOriginRedirect(self.CAS_LOGIN)

        stdout = io.StringIO()
        with patch.dict(os.environ, {private_verify.API_TOKEN_ENV: ""}):
            with patch.object(receipt, "_fetch", side_effect=probe):
                with contextlib.redirect_stdout(stdout):
                    code = verifier.main([
                        "--publish-root", str(self.publish),
                        "--base-url", self.BUSINESS_BASE_URL,
                        "--rps", "0",
                        "--json",
                    ])
        self.assertEqual(verifier.EXIT_UNDECIDED, code)
        self.assertEqual(1, len(calls))
        report = json.loads(stdout.getvalue())
        self.assertEqual("unverifiable", report["status"])
        self.assertEqual({"login-required": 2}, report["undecided_categories"])
        self.assertIn(private_verify.API_TOKEN_ENV, report["headline"])

    def test_private_cas_login_with_token_and_valid_descendant_build_passes(self) -> None:
        builds_payload = {
            "results": [
                {
                    "id": 4762840,
                    "commit": self.head_sha,
                    "state": {"code": "finished"},
                    "finished": "2026-11-19T03:37:13Z",
                    "success": True,
                    "version": {"slug": "latest"},
                }
            ]
        }
        opener, seen = self._fake_builds_opener(builds_payload)
        stdout = io.StringIO()
        with patch.dict(os.environ, {private_verify.API_TOKEN_ENV: "super-secret-token"}):
            with patch.object(receipt, "_fetch", side_effect=self._cas_redirect):
                with patch.object(private_verify, "urlopen", side_effect=opener):
                    with contextlib.redirect_stdout(stdout):
                        code = verifier.main([
                            "--publish-root", str(self.publish),
                            "--base-url", self.BUSINESS_BASE_URL,
                            "--rps", "0",
                            "--json",
                        ])
        self.assertEqual(0, code)
        self.assertEqual(
            [("https://readthedocs.com/api/v3/projects/ht-docs-ht-manuals/builds/", "Token super-secret-token")],
            seen,
        )
        raw_out = stdout.getvalue()
        self.assertNotIn("super-secret-token", raw_out)
        report = json.loads(raw_out)
        self.assertEqual("verified", report["status"])
        self.assertEqual("rtd-private-build", report["verification_mode"])
        self.assertEqual(4762840, report["rtd_build"]["id"])
        self.assertEqual({"rtd-private-build"}, {entry["mode"] for entry in report["results"]})

    def test_private_accepts_build_covering_publish_commit_when_head_is_newer_non_publish(self) -> None:
        builds_payload = {
            "results": [
                {
                    "id": 4762800,
                    "commit": self.publish_sha,
                    "state": {"code": "finished"},
                    "finished": "2026-11-19T02:00:00Z",
                    "success": True,
                    "version": "latest",
                }
            ]
        }
        opener, _seen = self._fake_builds_opener(builds_payload)
        stdout = io.StringIO()
        with patch.dict(os.environ, {private_verify.API_TOKEN_ENV: "tok"}):
            with patch.object(receipt, "_fetch", side_effect=self._cas_redirect):
                with patch.object(private_verify, "urlopen", side_effect=opener):
                    with contextlib.redirect_stdout(stdout):
                        code = verifier.main([
                            "--publish-root", str(self.publish),
                            "--base-url", self.BUSINESS_BASE_URL,
                            "--rps", "0",
                            "--json",
                        ])
        self.assertEqual(0, code)
        report = json.loads(stdout.getvalue())
        self.assertEqual(4762800, report["rtd_build"]["id"])

    def test_private_rejects_stale_pre_publish_commit_or_wrong_version(self) -> None:
        for label, payload in (
            (
                "pre-publish-commit",
                {
                    "results": [
                        {
                            "id": 4760001,
                            "commit": self.pre_publish_sha,
                            "state": {"code": "finished"},
                            "finished": "2026-11-18T00:00:00Z",
                            "success": True,
                            "version": {"slug": "latest"},
                        }
                    ]
                },
            ),
            (
                "wrong-version",
                {
                    "results": [
                        {
                            "id": 4760002,
                            "commit": self.head_sha,
                            "state": {"code": "finished"},
                            "finished": "2026-11-19T03:00:00Z",
                            "success": True,
                            "version": {"slug": "v1.0"},
                        }
                    ]
                },
            ),
        ):
            with self.subTest(label=label):
                opener, _seen = self._fake_builds_opener(payload)
                stdout = io.StringIO()
                with patch.dict(os.environ, {private_verify.API_TOKEN_ENV: "tok"}):
                    with patch.object(receipt, "_fetch", side_effect=self._cas_redirect):
                        with patch.object(private_verify, "urlopen", side_effect=opener):
                            with contextlib.redirect_stdout(stdout):
                                code = verifier.main([
                                    "--publish-root", str(self.publish),
                                    "--base-url", self.BUSINESS_BASE_URL,
                                    "--rps", "0",
                                    "--json",
                                ])
                self.assertEqual(verifier.EXIT_FAILED, code)
                report = json.loads(stdout.getvalue())
                self.assertEqual("failed", report["status"])
                self.assertEqual({"stale-deployment": 2}, report["mismatch_categories"])

    def test_private_rtd_failed_build_fails_closed(self) -> None:
        builds_payload = {
            "results": [
                {
                    "id": 4762899,
                    "commit": self.head_sha,
                    "state": {"code": "finished"},
                    "finished": "2026-11-19T03:40:00Z",
                    "success": False,
                    "version": {"slug": "latest"},
                }
            ]
        }
        opener, _seen = self._fake_builds_opener(builds_payload)
        stdout = io.StringIO()
        with patch.dict(os.environ, {private_verify.API_TOKEN_ENV: "tok"}):
            with patch.object(receipt, "_fetch", side_effect=self._cas_redirect):
                with patch.object(private_verify, "urlopen", side_effect=opener):
                    with contextlib.redirect_stdout(stdout):
                        code = verifier.main([
                            "--publish-root", str(self.publish),
                            "--base-url", self.BUSINESS_BASE_URL,
                            "--rps", "0",
                            "--json",
                        ])
        self.assertEqual(verifier.EXIT_FAILED, code)
        report = json.loads(stdout.getvalue())
        self.assertEqual("failed", report["status"])
        self.assertEqual({"rtd-build-failed": 2}, report["mismatch_categories"])

    def test_private_rtd_in_progress_build_reports_unverifiable_75(self) -> None:
        builds_payload = {
            "results": [
                {
                    "id": 4762900,
                    "commit": self.publish_sha,
                    "state": {"code": "building"},
                    "finished": None,
                    "success": None,
                    "version": {"slug": "latest"},
                }
            ]
        }
        # Set HEAD == publish_sha so no earlier covering build exists
        self._git("reset", "--hard", self.publish_sha)
        opener, _seen = self._fake_builds_opener(builds_payload)
        stdout = io.StringIO()
        with patch.dict(os.environ, {private_verify.API_TOKEN_ENV: "tok"}):
            with patch.object(receipt, "_fetch", side_effect=self._cas_redirect):
                with patch.object(private_verify, "urlopen", side_effect=opener):
                    with contextlib.redirect_stdout(stdout):
                        code = verifier.main([
                            "--publish-root", str(self.publish),
                            "--base-url", self.BUSINESS_BASE_URL,
                            "--rps", "0",
                            "--json",
                        ])
        self.assertEqual(verifier.EXIT_UNDECIDED, code)
        report = json.loads(stdout.getvalue())
        self.assertEqual("unverifiable", report["status"])
        self.assertEqual({"rtd-build-in-progress": 2}, report["undecided_categories"])

    def test_private_missing_local_asset_fails_closed(self) -> None:
        (self.web / "_static" / "manual-assets" / "diagram.png").unlink()
        builds_payload = {
            "results": [
                {
                    "id": 4762840,
                    "commit": self.head_sha,
                    "state": {"code": "finished"},
                    "finished": "2026-11-19T03:37:13Z",
                    "success": True,
                    "version": {"slug": "latest"},
                }
            ]
        }
        opener, _seen = self._fake_builds_opener(builds_payload)
        stdout = io.StringIO()
        with patch.dict(os.environ, {private_verify.API_TOKEN_ENV: "tok"}):
            with patch.object(receipt, "_fetch", side_effect=self._cas_redirect):
                with patch.object(private_verify, "urlopen", side_effect=opener):
                    with contextlib.redirect_stdout(stdout):
                        code = verifier.main([
                            "--publish-root", str(self.publish),
                            "--base-url", self.BUSINESS_BASE_URL,
                            "--rps", "0",
                            "--json",
                        ])
        self.assertEqual(verifier.EXIT_FAILED, code)
        report = json.loads(stdout.getvalue())
        self.assertEqual("failed", report["status"])
        self.assertEqual({"local-integrity-failed": 2}, report["mismatch_categories"])


if __name__ == "__main__":
    unittest.main()
