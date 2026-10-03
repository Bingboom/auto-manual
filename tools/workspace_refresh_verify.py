#!/usr/bin/env python3
"""Verify a frozen workspace release independently from production or export."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys
import time

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.rtd_deployment_receipt import FetchSession, _without_rtd_proxy_injection
from tools.workspace_freshness import inventory
from tools.workspace_refresh_publish import command
from tools.workspace_snapshot import atomic_json

BASE_URL = "https://ht-doc.readthedocs.io/"
ROUTE = "workspace/deliverables/index.html"


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
        for attempt in range(args.attempts):
            # RTD success is checked separately; an old receipt cannot stand in for a finished build.
            report["stage"] = "rtd-build"
            builds = json.loads(FetchSession().fetch("https://readthedocs.org/api/v3/projects/ht-doc/builds/?limit=20"))
            previous = next((item for item in builds["results"] if item.get("success")), None)
            report["last_success"] = (previous or {}).get("finished") or "Unavailable"
            target = next((item for item in builds["results"] if item.get("commit") == args.revision), None)
            if target and target.get("state", {}).get("code") == "finished":
                report["rtd_build"] = target.get("id")
                report["rtd_url"] = f"https://app.readthedocs.org/projects/ht-doc/builds/{target.get('id')}/"
                if not target.get("success"):
                    raise ValueError("RTD target build failed")
                report["stage"] = "online-verification"
                try:
                    report.update(verify_once(args.root, args.revision), rtd_build=target["id"])
                    break
                except (ValueError, OSError):
                    if attempt + 1 == args.attempts:
                        raise
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
