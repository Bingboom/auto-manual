#!/usr/bin/env python3
"""Scheduled cross-check that published Web targets are served by the intended RTD project.

REV-08(b): the receipt lane (``web-publish-receipt.yml``, REV-07) verifies a
deployment once, at ``HTML_link`` registration time, so a later wrong-site
deployment or link drift is otherwise invisible. This checker reads the
published target catalog (``docs/publish/publish_manifest.json`` on Hello-Docs
``main``) and verifies every target's canonical nested page against the live
site:

- With ``--publish-root`` (a local frozen ``docs/publish`` checkout) it runs
  the full ``tools.rtd.deployment_receipt.verify_deployment`` check per target:
  live receipt against the frozen source fingerprint, byte identity for each
  page and its same-origin resources, and the RTD project-slug dimension.
- Without a local tree it fetches the manifest remotely (``--manifest-url``)
  and still fails closed on unreachable pages, cross-origin redirects, and
  pages served by a foreign RTD project (``readthedocs-project-slug`` meta).

Every request goes through one shared, paced, caching
``rtd_deployment_receipt.FetchSession``. Each target ends in one of four
verdicts, and only one of them is a finding about the deployment:

- **verified** — the live page matches its frozen source;
- **mismatched** — a real finding (bytes differ, not found, wrong site,
  stale deployment, redirect off-site, …), with a ``category``; exit 1;
- **unverifiable** — the live page could not be read at all: the site sent the
  anonymous reader to its sign-in page, refused access, or the transport kept
  failing. Nothing was learned about the deployment;
- **throttled** — the host rate-limited the run before the target was decided.

Unverifiable and throttled targets are *undecided*, never failures: a run with
no mismatch but some undecided targets exits 75 (``EX_TEMPFAIL``), a run with a
mismatch exits 1 whatever else happened, so the alert says which incident it is.

``--asset-scope`` bounds the daily request budget: the default ``markup`` scope
byte-verifies each target page and its HTML/CSS/JS closure and requires every
other referenced resource to exist in the served receipt, while ``full``
additionally re-downloads the ~2,200 per-model binary assets.

Read-only: no Base identity, no record IDs, no writeback path.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable
import json
import os
from pathlib import Path, PurePosixPath
import re
from typing import Any
from http.client import HTTPException
from ssl import SSLError
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root


ROOT = bootstrap_repo_root(__file__, parent_count=1)

from tools.rtd import deployment_receipt as receipt  # noqa: E402
from tools.manual_operations_online_health import publication_url  # noqa: E402
from tools.utils.path_utils import PathSegments  # noqa: E402
from tools.utils.log import get_logger

_ERR = get_logger("verify-web-deploy", stream="stderr")

REPORT_SCHEMA = "auto-manual-web-deployment-verification/v1"
MANIFEST_SCHEMA = "auto-manual-web-publish-branch/v2"
PUBLISH_MANIFEST = "publish_manifest.json"
# The business-plane catalog of everything published to production RTD.
DEFAULT_MANIFEST_URL = (
    "https://api.github.com/repos/Bingboom/Hello-Docs/contents/"
    "docs/publish/publish_manifest.json?ref=main"
)
MAX_MANIFEST_BYTES = 32 * 1024 * 1024
_SAFE_SEGMENT_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
# sysexits EX_TEMPFAIL: the catalog is undecided, not disproved. Re-run.
EXIT_OK = 0
EXIT_FAILED = 1
EXIT_THROTTLED = 75
EXIT_UNDECIDED = EXIT_THROTTLED
DEFAULT_RPS = 2.0

# Per-target verdicts. "failed" is the historical name of a mismatch and stays
# the value in reports and in the shared result rows other callers read.
STATUS_OK = "ok"
STATUS_MISMATCH = "failed"
STATUS_UNVERIFIABLE = "unverifiable"
STATUS_THROTTLED = "throttled"
# Undecided targets: nothing was learned about the deployment.
UNDECIDED_STATUSES = (STATUS_UNVERIFIABLE, STATUS_THROTTLED)
_HTTP_NOT_FOUND = {404, 410}
_HTTP_ACCESS_DENIED = {401, 403}
_TRANSPORT_ERRORS = (URLError, HTTPException, ConnectionError, TimeoutError, SSLError)
# Message fragment -> mismatch category, checked in order. The messages are the
# receipt module's own fail-closed errors.
_MISMATCH_CATEGORIES = (
    ("does not match frozen source", "stale-deployment"),
    ("bytes differ", "content-differs"),
    ("declares RTD project", "wrong-site"),
    ("never declared the expected RTD project", "wrong-site"),
    ("lacks selected routes", "missing-from-deployment"),
    ("lacks a referenced resource", "missing-from-deployment"),
    ("not same-origin HTTP 200", "unexpected-response"),
    ("Unexpected deployment probe query", "redirect"),
)


def fetch_manifest_bytes(url: str, *, token: str | None = None, timeout: float = 30) -> bytes:
    """Fetch the remote publish manifest over HTTPS with a bounded read."""
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Manifest URL must be HTTPS without credentials")
    headers = {
        "User-Agent": "auto-manual-web-deploy-verify/1",
        # GitHub contents API returns the raw file body with this media type;
        # plain raw.githubusercontent.com URLs simply ignore it.
        "Accept": "application/vnd.github.raw+json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers)
    with build_opener().open(request, timeout=timeout) as response:
        if response.status != 200:
            raise ValueError(f"Manifest fetch returned HTTP {response.status}")
        if urlsplit(response.geturl()).scheme != "https":
            raise ValueError("Manifest fetch was redirected off HTTPS")
        data = response.read(MAX_MANIFEST_BYTES + 1)
    if len(data) > MAX_MANIFEST_BYTES:
        raise ValueError("Manifest exceeds size limit")
    return data


def _target_identity(item: dict[str, Any]) -> dict[str, str]:
    identity: dict[str, str] = {}
    for field in ("model", "region", "lang"):
        value = item.get(field)
        if not isinstance(value, str) or not _SAFE_SEGMENT_RE.fullmatch(value):
            raise ValueError(f"Publish manifest target has an unsafe {field}: {value!r}")
        identity[field] = value
    return identity


def manifest_targets(payload: Any) -> list[dict[str, str]]:
    """Extract verified target identities and canonical page routes from the manifest.

    Manifest content is data, not trust: every segment is validated before it
    can become part of a URL, and each target's stored ``route`` must match its
    own identity so a tampered catalog cannot point verification elsewhere.
    """
    if not isinstance(payload, dict) or payload.get("schema_version") != MANIFEST_SCHEMA:
        raise ValueError("Unsupported publish manifest schema")
    raw = payload.get("targets")
    if not isinstance(raw, list) or not raw:
        raise ValueError("Publish manifest lists no targets")
    targets: list[dict[str, str]] = []
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("Publish manifest target must be an object")
        identity = _target_identity(item)
        manual = item.get("manual")
        if (
            not isinstance(manual, str)
            or PurePosixPath(manual).name != manual
            or PurePosixPath(manual).suffix != ".md"
            or not _SAFE_SEGMENT_RE.fullmatch(PurePosixPath(manual).stem)
        ):
            raise ValueError(f"Publish manifest target has an unsafe manual name: {manual!r}")
        expected_route = "/".join(
            (identity["model"], identity["region"], identity["lang"], PathSegments.MD)
        )
        if item.get("route") != expected_route:
            raise ValueError(
                "Publish manifest target route does not match its identity: "
                f"{item.get('route')!r} != {expected_route!r}"
            )
        targets.append(
            {
                **identity,
                "page": f"{expected_route}/{PurePosixPath(manual).stem}.html",
            }
        )
    targets.sort(key=lambda item: (item["model"], item["region"], item["lang"]))
    return targets


def expected_project_slug(base_url: str, explicit: str | None = None) -> str:
    if explicit:
        return explicit
    derived = receipt.rtd_project_slug_from_base_url(base_url)
    if derived is None:
        raise ValueError(
            f"Cannot derive the expected RTD project slug from base URL {base_url!r}; "
            "pass --expected-project-slug explicitly"
        )
    return derived


def _result(
    target: dict[str, str],
    *,
    mode: str,
    error: str | None = None,
    status: str | None = None,
    category: str | None = None,
) -> dict[str, str]:
    if status is None:
        status = STATUS_OK if error is None else STATUS_MISMATCH
    entry = {
        "model": target["model"],
        "region": target["region"],
        "lang": target["lang"],
        "page": target["page"],
        "mode": mode,
        "status": status,
    }
    if category is not None:
        entry["category"] = category
    if error is not None:
        entry["error"] = error
    return entry


def classify_failure(exc: Exception) -> tuple[str, str]:
    """(status, category) for one target's verification error.

    Only evidence about the deployment is a mismatch. A sign-in redirect, an
    access refusal or a failing transport says nothing about the served bytes,
    so those targets are unverifiable; a rate limit is throttled.
    """
    if isinstance(exc, receipt.DeploymentThrottled):
        return STATUS_THROTTLED, "rate-limited"
    if isinstance(exc, receipt.CrossOriginRedirect):
        if exc.login_required:
            return STATUS_UNVERIFIABLE, "login-required"
        return STATUS_MISMATCH, "redirect"
    if isinstance(exc, HTTPError):
        if exc.code in _HTTP_NOT_FOUND:
            return STATUS_MISMATCH, "not-found"
        if exc.code in _HTTP_ACCESS_DENIED:
            return STATUS_UNVERIFIABLE, "access-denied"
        if exc.code in receipt.TRANSIENT_STATUS or exc.code >= 500:
            return STATUS_UNVERIFIABLE, "transport"
        return STATUS_MISMATCH, f"http-{exc.code}"
    if isinstance(exc, _TRANSPORT_ERRORS):
        return STATUS_UNVERIFIABLE, "transport"
    message = str(exc)
    for fragment, category in _MISMATCH_CATEGORIES:
        if fragment in message:
            return STATUS_MISMATCH, category
    return STATUS_MISMATCH, "other"


def _error_text(exc: Exception) -> str:
    text = f"{type(exc).__name__}: {exc}"
    if isinstance(exc, receipt.CrossOriginRedirect):
        text += f" (to {exc.destination})"
    return text


def _failure(
    target: dict[str, str], *, mode: str, exc: Exception, separate_unverifiable: bool = False
) -> dict[str, str]:
    """Rate limiting leaves a target undecided; so does an unreadable page when asked to.

    Without ``separate_unverifiable`` the historical two-way split stands
    (throttled vs. failed) for callers that gate a write on it; the category is
    recorded either way.
    """
    status, category = classify_failure(exc)
    if status == STATUS_UNVERIFIABLE and not separate_unverifiable:
        status = STATUS_MISMATCH
    return _result(target, mode=mode, error=_error_text(exc), status=status, category=category)


def _budget_exhausted(target: dict[str, str], *, mode: str) -> dict[str, str]:
    return _result(
        target, mode=mode, status=STATUS_THROTTLED, category="rate-limited",
        error="DeploymentThrottled: rate-limit budget exhausted before this target was verified",
    )


def verify_targets_against_source(
    web_root: Path,
    *,
    base_url: str,
    targets: list[dict[str, str]],
    project_slug: str,
    session: receipt.FetchSession | None = None,
    include_dependency: Callable[[str], bool] | None = None,
    separate_unverifiable: bool = False,
) -> list[dict[str, str]]:
    """Full verification: frozen receipt + byte identity + project slug per target.

    One batch call verifies every route on the happy path (single source
    fingerprint, shared resource closure); only when the batch fails does the
    checker re-run per target to attribute each failure. The attribution pass
    shares the batch's session, so it replays cached bytes instead of
    re-fetching every target's whole closure — that amplification is what put
    ~570 requests on the wire for a 52-target catalog.
    """
    mode = "frozen-source"
    session = session or receipt.FetchSession()
    routes = [target["page"] for target in targets]
    try:
        receipt.verify_deployment(
            web_root, base_url, routes, expected_project_slug=project_slug, session=session,
            include_dependency=include_dependency,
        )
    except Exception:  # noqa: BLE001 - falls back to per-target verification
        results = []
        for target in targets:
            if session.budget_exhausted:
                # The host is still rate-limiting us; stop adding to its load.
                results.append(_budget_exhausted(target, mode=mode))
                continue
            try:
                receipt.verify_deployment(
                    web_root, base_url, [target["page"]],
                    expected_project_slug=project_slug, session=session,
                    include_dependency=include_dependency,
                )
            except Exception as exc:  # noqa: BLE001 - one target's failure is recorded
                results.append(_failure(
                    target, mode=mode, exc=exc, separate_unverifiable=separate_unverifiable))
            else:
                results.append(_result(target, mode=mode))
        return results
    return [_result(target, mode=mode) for target in targets]


def verify_targets_live_slug(
    *,
    base_url: str,
    targets: list[dict[str, str]],
    project_slug: str,
    session: receipt.FetchSession | None = None,
    separate_unverifiable: bool = False,
) -> list[dict[str, str]]:
    """Remote-only verification: page reachability plus the served RTD project slug.

    Reuses the receipt module's hardened fetch (HTTPS, same-origin redirects,
    HTTP 200, byte limits) and its slug-meta parser; module-private reuse is
    deliberate, mirroring rtd_deployment_receipt's own reuse of
    manual_operations_online_health internals.
    """
    mode = "live-slug"
    session = session or receipt.FetchSession()
    results = []
    for target in targets:
        page = target["page"]
        if session.budget_exhausted:
            results.append(_budget_exhausted(target, mode=mode))
            continue
        try:
            data = session.fetch(publication_url(base_url, page))
            served = receipt._served_project_slugs(page, data)
            foreign = sorted(served - {project_slug})
            if foreign:
                raise ValueError(
                    f"page declares RTD project {', '.join(foreign)} instead of {project_slug}"
                )
            if project_slug not in served:
                raise ValueError(
                    "page never declared the expected RTD project slug "
                    f"{project_slug}: no readthedocs-project-slug meta observed"
                )
        except Exception as exc:  # noqa: BLE001 - one target's failure is recorded
            results.append(_failure(
                target, mode=mode, exc=exc, separate_unverifiable=separate_unverifiable))
        else:
            results.append(_result(target, mode=mode))
    return results


def _category_counts(entries: list[dict[str, str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in entries:
        category = entry.get("category", "other")
        counts[category] = counts.get(category, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def build_report(
    *,
    base_url: str,
    project_slug: str,
    results: list[dict[str, str]],
    session: receipt.FetchSession | None = None,
) -> dict[str, Any]:
    """Mismatch outranks everything: a real verdict is never masked by a 429 or a sign-in page.

    ``counts`` is the authoritative tally. ``targets_failed`` (mismatched) and
    ``targets_throttled`` (every *undecided* target: unverifiable plus
    throttled) keep their historical meaning for readers that compute
    "verified = checked - failed - throttled".
    """
    verified = [entry for entry in results if entry["status"] == STATUS_OK]
    failed = [entry for entry in results if entry["status"] == STATUS_MISMATCH]
    unverifiable = [entry for entry in results if entry["status"] == STATUS_UNVERIFIABLE]
    throttled = [entry for entry in results if entry["status"] == STATUS_THROTTLED]
    if not results or failed:
        status = "failed"
    elif unverifiable:
        status = STATUS_UNVERIFIABLE
    elif throttled:
        status = STATUS_THROTTLED
    else:
        status = "verified"
    report = {
        "schema": REPORT_SCHEMA,
        "base_url": base_url,
        "expected_project_slug": project_slug,
        "targets_checked": len(results),
        "targets_failed": len(failed),
        "targets_throttled": len(unverifiable) + len(throttled),
        "counts": {
            "verified": len(verified),
            "mismatched": len(failed),
            "unverifiable": len(unverifiable),
            "throttled": len(throttled),
        },
        "mismatch_categories": _category_counts(failed),
        "undecided_categories": _category_counts(unverifiable + throttled),
        "status": status,
        "results": results,
    }
    if session is not None:
        report["transport"] = session.stats()
    return report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Verify every published Web target against the live RTD deployment: "
            "wrong-site deployments and link drift fail the run."
        )
    )
    parser.add_argument(
        "--publish-root",
        type=Path,
        default=None,
        help=(
            "Local frozen docs/publish tree (a Hello-Docs main checkout); "
            "enables the full receipt/byte verification. Without it the "
            "manifest is fetched from --manifest-url and only page "
            "reachability plus the served RTD project slug are checked."
        ),
    )
    parser.add_argument("--manifest-url", default=DEFAULT_MANIFEST_URL)
    parser.add_argument("--base-url", default=receipt.DEFAULT_RTD_BASE_URL)
    parser.add_argument(
        "--expected-project-slug",
        default=None,
        help="Override the slug derived from --base-url (required for custom domains)",
    )
    parser.add_argument("--limit", type=int, default=None, help="Verify only the first N targets")
    parser.add_argument("--json", action="store_true", help="Print the JSON report instead of text lines")
    parser.add_argument(
        "--rps",
        type=float,
        default=DEFAULT_RPS,
        help=(
            f"Global request rate ceiling, requests/second (default {DEFAULT_RPS}); "
            "0 disables pacing. Every request in the run shares this budget."
        ),
    )
    parser.add_argument(
        "--retry-budget",
        type=float,
        default=receipt.DEFAULT_RETRY_BUDGET_SECONDS,
        help=(
            "Total seconds the run may spend sleeping on rate-limit backoff "
            f"(default {receipt.DEFAULT_RETRY_BUDGET_SECONDS}); once spent, the "
            "remaining targets are reported throttled without further requests."
        ),
    )
    parser.add_argument(
        "--asset-scope",
        choices=("markup", "full"),
        default="markup",
        help=(
            "Which discovered resources to re-download and hash. 'markup' "
            "(default) fetches HTML/CSS/JS and requires every other referenced "
            "resource to be present in the served receipt; 'full' also "
            "re-downloads every binary asset (~2,200 across the catalog, so "
            "reserve it for on-demand deep runs)."
        ),
    )
    parser.add_argument(
        "--report-json",
        type=Path,
        default=None,
        help="Also write the JSON report to this path (for CI classification counts)",
    )
    return parser.parse_args(argv)


def _session(args: argparse.Namespace) -> receipt.FetchSession:
    rps = float(getattr(args, "rps", DEFAULT_RPS))
    if rps < 0:
        raise ValueError("--rps must not be negative")
    return receipt.FetchSession(
        min_interval=0.0 if rps == 0 else 1.0 / rps,
        retry_budget=float(getattr(args, "retry_budget", receipt.DEFAULT_RETRY_BUDGET_SECONDS)),
    )


def exit_code_for(status: str) -> int:
    """Undecided runs keep their own code so CI never reads them as a content mismatch."""
    return {
        "verified": EXIT_OK,
        STATUS_THROTTLED: EXIT_UNDECIDED,
        STATUS_UNVERIFIABLE: EXIT_UNDECIDED,
    }.get(status, EXIT_FAILED)


def headline(report: dict[str, Any]) -> str:
    """One sentence an operator can act on; mismatches always come first."""
    counts = report.get("counts", {})
    undecided = report.get("undecided_categories", {})
    status = report.get("status")
    if status == "verified":
        return "VERIFIED: every target matches its frozen publish source."
    if status == "failed":
        mismatched = counts.get("mismatched", 0)
        if not mismatched:
            return "FAILED: the catalog lists no target, so nothing was verified."
        kinds = ", ".join(f"{name} {n}" for name, n in report.get("mismatch_categories", {}).items())
        return (
            f"TARGET MISMATCH: {mismatched} target(s) disproved ({kinds}). "
            "These are real findings; investigate them first."
        )
    if status == STATUS_UNVERIFIABLE and undecided.get("login-required"):
        return (
            "UNVERIFIABLE: the site redirected the anonymous verifier to its sign-in page, "
            "so no page could be read. Nothing is known to be wrong, and a re-run will not "
            "help: the check needs an authenticated read path or a different proof."
        )
    if status == STATUS_UNVERIFIABLE:
        return (
            "UNVERIFIABLE: pages could not be read (access refused or transport errors). "
            "Nothing is known to be wrong; re-run, and check site access if it repeats."
        )
    return (
        "UNDECIDED: the host rate-limited the run. No target was disproved; "
        "re-run (optionally with a lower --rps) to decide them."
    )


def run(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    project_slug = expected_project_slug(str(args.base_url), args.expected_project_slug)
    session = _session(args)
    if args.publish_root is not None:
        publish_root = Path(args.publish_root)
        publish_root = publish_root if publish_root.is_absolute() else ROOT / publish_root
        payload = json.loads((publish_root / PUBLISH_MANIFEST).read_text(encoding="utf-8"))
    else:
        token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or None
        payload = json.loads(fetch_manifest_bytes(str(args.manifest_url), token=token))
    targets = manifest_targets(payload)
    if args.limit is not None:
        if args.limit < 1:
            raise ValueError("--limit must be a positive integer")
        targets = targets[: args.limit]
    scope = str(getattr(args, "asset_scope", "markup"))
    if args.publish_root is not None:
        results = verify_targets_against_source(
            publish_root / PathSegments.WEB,
            base_url=str(args.base_url),
            targets=targets,
            project_slug=project_slug,
            session=session,
            include_dependency=None if scope == "full" else receipt.markup_dependency,
            separate_unverifiable=True,
        )
    else:
        results = verify_targets_live_slug(
            base_url=str(args.base_url),
            targets=targets,
            project_slug=project_slug,
            session=session,
            separate_unverifiable=True,
        )
    report = build_report(
        base_url=str(args.base_url),
        project_slug=project_slug,
        results=results,
        session=session,
    )
    report["asset_scope"] = scope if args.publish_root is not None else "live-slug"
    report["headline"] = headline(report)
    return exit_code_for(str(report["status"])), report


_VERDICT = {
    STATUS_OK: "OK",
    STATUS_MISMATCH: "MISMATCH",
    STATUS_UNVERIFIABLE: "UNVERIFIABLE",
    STATUS_THROTTLED: "THROTTLED",
}
# Output order: findings first, then what stays undecided, then the passes.
_ORDER = {STATUS_MISMATCH: 0, STATUS_UNVERIFIABLE: 1, STATUS_THROTTLED: 2, STATUS_OK: 3}


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        exit_code, report = run(args)
    except Exception as exc:  # noqa: BLE001 - CLI boundary reports the error and exits non-zero
        _ERR.error(f"[verify-web-deploy] ERROR: {exc}")
        return EXIT_FAILED
    if args.report_json is not None:
        Path(args.report_json).write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return exit_code
    counts = report["counts"]
    tally = (
        f"{counts['verified']} verified / {counts['mismatched']} mismatched / "
        f"{counts['unverifiable']} unverifiable / {counts['throttled']} throttled "
        f"of {report['targets_checked']} target(s)"
    )
    print(f"[verify-web-deploy] {report['headline']}")
    print(f"[verify-web-deploy] counts: {tally}")
    if report["undecided_categories"]:
        reasons = ", ".join(f"{name} {n}" for name, n in report["undecided_categories"].items())
        print(f"[verify-web-deploy] undecided by reason: {reasons}")
    ordered = sorted(
        report["results"], key=lambda entry: _ORDER.get(entry["status"], len(_ORDER))
    )
    for entry in ordered:
        identity = "/".join((entry["model"], entry["region"], entry["lang"]))
        verdict = _VERDICT.get(entry["status"], entry["status"].upper())
        line = f"[verify-web-deploy] {verdict} {identity} {entry['page']} ({entry['mode']})"
        if entry["status"] != STATUS_OK:
            line = f"{line} [{entry.get('category', 'other')}]: {entry['error']}"
        print(line)
    print(
        f"[verify-web-deploy] {report['status']}: {tally} against {report['base_url']} "
        f"(expected project: {report['expected_project_slug']}, "
        f"asset scope: {report.get('asset_scope', 'markup')})"
    )
    if report["status"] in UNDECIDED_STATUSES:
        print(
            "[verify-web-deploy] no target was disproved; undecided targets are "
            "not failures and carry no finding about the deployment."
        )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
