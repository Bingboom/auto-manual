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

Read-only: no Base identity, no record IDs, no writeback path.
"""

from __future__ import annotations

import argparse
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


def _result(target: dict[str, str], *, mode: str, error: str | None = None) -> dict[str, str]:
    entry = {
        "model": target["model"],
        "region": target["region"],
        "lang": target["lang"],
        "page": target["page"],
        "mode": mode,
        "status": "ok" if error is None else "failed",
    }
    if error is not None:
        entry["error"] = error
    return entry


def verify_targets_against_source(
    web_root: Path,
    *,
    base_url: str,
    targets: list[dict[str, str]],
    project_slug: str,
) -> list[dict[str, str]]:
    """Full verification: frozen receipt + byte identity + project slug per target.

    One batch call verifies every route on the happy path (single source
    fingerprint, shared resource closure); only when the batch fails does the
    checker re-run per target to attribute each failure.
    """
    mode = "frozen-source"
    routes = [target["page"] for target in targets]
    try:
        receipt.verify_deployment(web_root, base_url, routes, expected_project_slug=project_slug)
    except Exception:
        results = []
        for target in targets:
            try:
                receipt.verify_deployment(
                    web_root, base_url, [target["page"]], expected_project_slug=project_slug
                )
            except Exception as exc:
                results.append(_result(target, mode=mode, error=f"{type(exc).__name__}: {exc}"))
            else:
                results.append(_result(target, mode=mode))
        return results
    return [_result(target, mode=mode) for target in targets]


def verify_targets_live_slug(
    *,
    base_url: str,
    targets: list[dict[str, str]],
    project_slug: str,
) -> list[dict[str, str]]:
    """Remote-only verification: page reachability plus the served RTD project slug.

    Reuses the receipt module's hardened fetch (HTTPS, same-origin redirects,
    HTTP 200, byte limits) and its slug-meta parser; module-private reuse is
    deliberate, mirroring rtd_deployment_receipt's own reuse of
    manual_operations_online_health internals.
    """
    mode = "live-slug"
    results = []
    for target in targets:
        page = target["page"]
        try:
            data = receipt._fetch(publication_url(base_url, page))
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
            results.append(_result(target, mode=mode, error=f"{type(exc).__name__}: {exc}"))
        else:
            results.append(_result(target, mode=mode))
    return results


def build_report(
    *,
    base_url: str,
    project_slug: str,
    results: list[dict[str, str]],
) -> dict[str, Any]:
    failed = [entry for entry in results if entry["status"] != "ok"]
    return {
        "schema": REPORT_SCHEMA,
        "base_url": base_url,
        "expected_project_slug": project_slug,
        "targets_checked": len(results),
        "targets_failed": len(failed),
        "status": "verified" if results and not failed else "failed",
        "results": results,
    }


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
    return parser.parse_args(argv)


def run(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    project_slug = expected_project_slug(str(args.base_url), args.expected_project_slug)
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
    if args.publish_root is not None:
        results = verify_targets_against_source(
            publish_root / PathSegments.WEB,
            base_url=str(args.base_url),
            targets=targets,
            project_slug=project_slug,
        )
    else:
        results = verify_targets_live_slug(
            base_url=str(args.base_url),
            targets=targets,
            project_slug=project_slug,
        )
    report = build_report(base_url=str(args.base_url), project_slug=project_slug, results=results)
    return (0 if report["status"] == "verified" else 1), report


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        exit_code, report = run(args)
    except Exception as exc:
        print(f"[verify-web-deploy] ERROR: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return exit_code
    for entry in report["results"]:
        identity = "/".join((entry["model"], entry["region"], entry["lang"]))
        if entry["status"] == "ok":
            print(f"[verify-web-deploy] OK {identity} {entry['page']} ({entry['mode']})")
        else:
            print(f"[verify-web-deploy] FAIL {identity} {entry['page']} ({entry['mode']}): {entry['error']}")
    print(
        f"[verify-web-deploy] {report['status']}: "
        f"{report['targets_checked'] - report['targets_failed']}/{report['targets_checked']} "
        f"target(s) verified against {report['base_url']} "
        f"(expected project: {report['expected_project_slug']})"
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
