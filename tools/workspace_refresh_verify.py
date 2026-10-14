#!/usr/bin/env python3
"""Verify a frozen workspace release independently from production or export."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.rtd.deployment_receipt import (
    DEFAULT_RTD_BASE_URL, FetchSession, _without_rtd_proxy_injection, rtd_project_slug_from_base_url,
)
from tools.workspace_freshness import inventory
from tools.workspace_refresh_publish import command
from tools.workspace_snapshot import atomic_json

BASE_URL = DEFAULT_RTD_BASE_URL.rstrip("/") + "/"
ROUTE = "workspace/deliverables/index.html"
# Read the Docs for Business answers its builds API only with a token; Community answers anonymously.
API_TOKEN_ENV = "READTHEDOCS_API_TOKEN"


def builds_api(base_url: str) -> tuple[str, str, bool] | None:
    """Builds API URL, dashboard build prefix and whether a token is required; None off Read the Docs."""
    slug = rtd_project_slug_from_base_url(base_url)
    if slug is None:
        return None
    business = (urlsplit(base_url).hostname or "").lower().endswith(".readthedocs-hosted.com")
    domain = "readthedocs.com" if business else "readthedocs.org"
    return (f"https://{domain}/api/v3/projects/{slug}/builds/",
            f"https://app.{domain}/projects/{slug}/builds/", business)


def fetch_builds(url: str, token: str) -> bytes:
    if not token:
        return FetchSession().fetch(url)
    request = Request(url, headers={"Authorization": f"Token {token}", "User-Agent": "auto-manual-deployment/1"})
    with urlopen(request, timeout=30) as response:
        return response.read()


def verify_once(root: Path, revision: str, *, fetch=None) -> dict:
    fetch = fetch or FetchSession().fetch
    # A local candidate is not a mainline version; verify ancestry at the checkout boundary.
    command(["git", "merge-base", "--is-ancestor", revision, "origin/main"], cwd=root)
    payload = json.loads(fetch(BASE_URL + "manual-deployment.json"))
    if payload.get("workspace_revision") != revision:
        raise ValueError("online-version-mismatch")
    expected = inventory(root)
    if payload.get("workspace_sources") != expected:
        raise ValueError("online-snapshot-mismatch")
    html = fetch(BASE_URL + ROUTE)
    normalized = _without_rtd_proxy_injection(ROUTE, html)
    if hashlib.sha256(normalized).hexdigest() != payload.get("files", {}).get(ROUTE):
        raise ValueError("online-page-bytes-mismatch")
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    for kind, value in expected.items():
        tag = soup.select_one(f'[data-workspace-source="{kind}"]')
        if tag is None or tag.get("data-snapshot-sha256") != (value["snapshot_sha256"] or ""):
            raise ValueError("online-page-source-mismatch")
    return {"stage": "online-verified", "status": "verified", "revision": revision,
            "sources": expected, "url": BASE_URL + ROUTE,
            "checked_at": dt.datetime.now(dt.timezone.utc).isoformat()}


def builds_lookup(report: dict) -> tuple[tuple[str, str, bool] | None, str]:
    """The builds API to poll and its token, or None when the build state cannot be read."""
    api = builds_api(BASE_URL)
    token = os.environ.get(API_TOKEN_ENV, "").strip()
    # Without the token a Business build state is unreadable; the receipt check alone then decides,
    # and it still needs this revision, so an old receipt cannot pass for a finished build.
    if api is None or (api[2] and not token):
        report["rtd_build"] = f"Not checked (no {API_TOKEN_ENV})" if api else "Not checked"
        return None, ""
    # The token goes only to the Business API that needs it, never to the public Community API.
    return api, token if api[2] else ""


def verify_attempt(root: Path, revision: str, api: tuple[str, str, bool] | None, token: str,
                   report: dict, *, last: bool) -> bool:
    """One bounded attempt; True once the online page matches this revision."""
    if api is not None:
        # RTD success is checked separately; an old receipt cannot stand in for a finished build.
        report["stage"] = "rtd-build"
        builds = json.loads(fetch_builds(api[0], token))
        previous = next((item for item in builds["results"] if item.get("success")), None)
        report["last_success"] = (previous or {}).get("finished") or "Unavailable"
        target = next((item for item in builds["results"] if item.get("commit") == revision), None)
        if not target or target.get("state", {}).get("code") != "finished":
            return False
        report["rtd_build"] = target.get("id")
        report["rtd_url"] = f"{api[1]}{target.get('id')}/"
        if not target.get("success"):
            raise ValueError("RTD target build failed")
    report["stage"] = "online-verification"
    try:
        report.update(verify_once(root, revision))
    except (ValueError, OSError):
        if last:
            raise
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--revision", required=True)
    parser.add_argument("--attempts", type=int, default=1)
    parser.add_argument("--output", type=Path, default=Path(".tmp/workspace-refresh/verification.json"))
    args = parser.parse_args()
    if not 1 <= args.attempts <= 20:
        parser.error("attempts must be 1..20")
    report = {"status": "failed", "stage": "mainline", "revision": args.revision,
              "resume": f"python tools/workspace_refresh_verify.py --revision {args.revision}"}
    try:
        if command(["git", "rev-parse", "HEAD"], cwd=args.root) != args.revision:
            raise ValueError("checkout does not match target revision")
        command(["git", "merge-base", "--is-ancestor", args.revision, "origin/main"], cwd=args.root)
        report["mainline_verified"] = True
        api, token = builds_lookup(report)
        for attempt in range(args.attempts):
            if verify_attempt(args.root, args.revision, api, token, report, last=attempt + 1 == args.attempts):
                break
            if attempt + 1 < args.attempts:
                time.sleep(30)
        if report.get("status") != "verified":
            raise ValueError("target RTD build not confirmed within bounded wait")
    except Exception as exc:  # noqa: BLE001 - stage and retry path survive every failure
        report.update(status="failed", error_type=type(exc).__name__)
    atomic_json(args.output, report)
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report["status"] == "verified" else 1


if __name__ == "__main__":
    raise SystemExit(main())
