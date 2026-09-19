from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools import rtd_deployment_receipt as receipt
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
        self.assertIn("FAIL JE-2000E/EU/de", text)
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
        self.assertIn("1 throttled (undecided)", text)
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

    def test_rps_flag_sets_the_shared_pace_and_rejects_negatives(self) -> None:
        session = verifier._session(verifier.parse_args(["--rps", "4"]))
        self.assertAlmostEqual(0.25, session.min_interval)
        self.assertEqual(0.0, verifier._session(verifier.parse_args(["--rps", "0"])).min_interval)
        default = verifier._session(verifier.parse_args([]))
        self.assertAlmostEqual(1.0 / verifier.DEFAULT_RPS, default.min_interval)
        with self.assertRaisesRegex(ValueError, "--rps"):
            verifier._session(verifier.parse_args(["--rps", "-1"]))


if __name__ == "__main__":
    unittest.main()
