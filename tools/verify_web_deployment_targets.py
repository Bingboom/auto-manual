#!/usr/bin/env python3
"""Scheduled cross-check that published Web targets are served by the intended RTD project.

REV-08(b): the queue writes ``Document_link.HTML_link`` deterministically
before the publish PR merges and before Read the Docs deploys, so a wrong-site
deployment or later link drift is otherwise invisible. This checker reads the
published target catalog (``docs/publish/publish_manifest.json`` on Hello-Docs
``main``) and verifies every target's canonical nested page against the live
site:

- With ``--publish-root`` (a local frozen ``docs/publish`` checkout) it runs
  the full ``tools.rtd_deployment_receipt.verify_deployment`` check per target:
  live receipt against the frozen source fingerprint, byte identity for each
  page and its same-origin resources, and the RTD project-slug dimension.
- Without a local tree it fetches the manifest remotely (``--manifest-url``)
  and still fails closed on unreachable pages, cross-origin redirects, and
  pages served by a foreign RTD project (``readthedocs-project-slug`` meta).

Every request goes through one shared, paced, caching
``rtd_deployment_receipt.FetchSession``, and a rate-limited target is reported
as **throttled** (undecided, exit 75) rather than as a mismatch (exit 1) — a
429 storm must never read as "the deployment is wrong", and must never be
silently swallowed as a pass either.

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
import sys
from typing import Any
from urllib.parse import urlsplit
from urllib.request import Request, build_opener

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root


ROOT = bootstrap_repo_root(__file__, parent_count=1)

from tools import rtd_deployment_receipt as receipt  # noqa: E402
from tools.manual_operations_online_health import publication_url  # noqa: E402
from tools.utils.path_utils import PathSegments  # noqa: E402

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
DEFAULT_RPS = 2.0


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
    target: dict[str, str], *, mode: str, error: str | None = None, status: str | None = None
) -> dict[str, str]:
    if status is None:
        status = "ok" if error is None else "failed"
    entry = {
        "model": target["model"],
        "region": target["region"],
        "lang": target["lang"],
        "page": target["page"],
        "mode": mode,
        "status": status,
    }
    if error is not None:
        entry["error"] = error
    return entry


def _failure(target: dict[str, str], *, mode: str, exc: Exception) -> dict[str, str]:
    """Rate limiting leaves a target undecided; everything else is a verdict."""
    status = "throttled" if isinstance(exc, receipt.DeploymentThrottled) else "failed"
    return _result(target, mode=mode, error=f"{type(exc).__name__}: {exc}", status=status)


def verify_targets_against_source(
    web_root: Path,
    *,
    base_url: str,
    targets: list[dict[str, str]],
    project_slug: str,
    session: receipt.FetchSession | None = None,
    include_dependency: Callable[[str], bool] | None = None,
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
    except Exception:
        results = []
        for target in targets:
            if session.budget_exhausted:
                # The host is still rate-limiting us; stop adding to its load.
                results.append(_result(
                    target, mode=mode, status="throttled",
                    error="DeploymentThrottled: rate-limit budget exhausted before "
                          "this target was verified"))
                continue
            try:
                receipt.verify_deployment(
                    web_root, base_url, [target["page"]],
                    expected_project_slug=project_slug, session=session,
                    include_dependency=include_dependency,
                )
            except Exception as exc:
                results.append(_failure(target, mode=mode, exc=exc))
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
            results.append(_result(
                target, mode=mode, status="throttled",
                error="DeploymentThrottled: rate-limit budget exhausted before "
                      "this target was verified"))
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
        except Exception as exc:
            results.append(_failure(target, mode=mode, exc=exc))
        else:
            results.append(_result(target, mode=mode))
    return results


def build_report(
    *,
    base_url: str,
    project_slug: str,
    results: list[dict[str, str]],
    session: receipt.FetchSession | None = None,
) -> dict[str, Any]:
    """Mismatch outranks throttling: a real verdict is never masked by a 429."""
    failed = [entry for entry in results if entry["status"] == "failed"]
    throttled = [entry for entry in results if entry["status"] == "throttled"]
    if not results or failed:
        status = "failed"
    elif throttled:
        status = "throttled"
    else:
        status = "verified"
    report = {
        "schema": REPORT_SCHEMA,
        "base_url": base_url,
        "expected_project_slug": project_slug,
        "targets_checked": len(results),
        "targets_failed": len(failed),
        "targets_throttled": len(throttled),
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
    """throttled keeps its own code so CI can say "undecided, re-run"."""
    return {"verified": EXIT_OK, "throttled": EXIT_THROTTLED}.get(status, EXIT_FAILED)


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
        )
    else:
        results = verify_targets_live_slug(
            base_url=str(args.base_url),
            targets=targets,
            project_slug=project_slug,
            session=session,
        )
    report = build_report(
        base_url=str(args.base_url),
        project_slug=project_slug,
        results=results,
        session=session,
    )
    report["asset_scope"] = scope if args.publish_root is not None else "live-slug"
    return exit_code_for(str(report["status"])), report


_VERDICT = {"ok": "OK", "failed": "FAIL", "throttled": "THROTTLED"}


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        exit_code, report = run(args)
    except Exception as exc:
        print(f"[verify-web-deploy] ERROR: {exc}", file=sys.stderr)
        return EXIT_FAILED
    if args.report_json is not None:
        Path(args.report_json).write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return exit_code
    for entry in report["results"]:
        identity = "/".join((entry["model"], entry["region"], entry["lang"]))
        verdict = _VERDICT.get(entry["status"], entry["status"].upper())
        line = f"[verify-web-deploy] {verdict} {identity} {entry['page']} ({entry['mode']})"
        print(line if entry["status"] == "ok" else f"{line}: {entry['error']}")
    verified = report["targets_checked"] - report["targets_failed"] - report["targets_throttled"]
    print(
        f"[verify-web-deploy] {report['status']}: "
        f"{verified}/{report['targets_checked']} target(s) verified, "
        f"{report['targets_failed']} mismatched, "
        f"{report['targets_throttled']} throttled (undecided) against {report['base_url']} "
        f"(expected project: {report['expected_project_slug']}, "
        f"asset scope: {report.get('asset_scope', 'markup')})"
    )
    if report["status"] == "throttled":
        print(
            "[verify-web-deploy] no target was disproved; the host rate-limited "
            "the run. Re-run (optionally with a lower --rps) to decide them."
        )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
