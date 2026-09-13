"""Bounded HTTP accessibility checks; never deployment or translation proof."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from tools.rtd_portal import ASSETS, catalog


def _https_url(value: str) -> str:
    if not isinstance(value, str) or any(ord(c) < 33 or ord(c) == 127 for c in value) or "\\" in value:
        raise ValueError("HTTP probe URL must be a fixed HTTPS URL")
    try:
        parsed = urlsplit(value)
        host = parsed.hostname
        parsed.port
    except ValueError:
        raise ValueError("Invalid HTTP probe URL") from None
    if (parsed.scheme != "https" or not host or "%" in host or parsed.username is not None
            or parsed.password is not None or parsed.query or parsed.fragment):
        raise ValueError("HTTP probe URL must use HTTPS without credentials, query or fragment")
    return value


def _origin(value: str) -> tuple[str, str, int]:
    parsed = urlsplit(_https_url(value))
    return parsed.scheme, parsed.hostname, parsed.port or 443


def publication_url(base_url: str, relative: str) -> str:
    base_url = _https_url(base_url).rstrip("/") + "/"
    parsed = urlsplit(relative)
    if (not relative or parsed.scheme or parsed.netloc or parsed.query or parsed.fragment
            or relative.startswith("/") or "\\" in relative
            or any(ord(c) < 32 or ord(c) == 127 for c in relative)
            or ".." in PurePosixPath(relative).parts):
        raise ValueError("Unsafe frozen publication route")
    return base_url + quote(relative, safe="/")


class _SameOriginRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if _origin(req.full_url) != _origin(newurl):
            raise ValueError("Cross-origin HTTP probe redirect refused")
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is not None:
            redirected.method = "HEAD"
        return redirected


def probe_url(url: str, *, timeout: float = 10) -> dict:
    _https_url(url)
    if not 0 < timeout <= 60:
        raise ValueError("Probe timeout must be between 0 and 60 seconds")
    request = Request(url, method="HEAD", headers={"User-Agent": "auto-manual-health/1"})
    try:
        with build_opener(_SameOriginRedirect()).open(request, timeout=timeout) as response:
            code = response.status
            return {"status": "ok" if 200 <= code < 300 else "failed", "http_status": code}
    except HTTPError as exc:
        exc.close()
        return {"status": "failed", "http_status": exc.code, "reason": "HTTP error"}
    except (URLError, OSError, ValueError):
        return {"status": "failed", "http_status": None, "reason": "Network failure or unsafe redirect"}


def build_online_health_report(
    web_root: Path, *, base_url: str, max_publications: int = 100,
    probe: Callable[[str], dict] = probe_url,
) -> dict:
    """Use only explicitly indexed publications; do not guess missing routes."""
    _https_url(base_url)
    if not 1 <= max_publications <= 1000:
        raise ValueError("Publication limit must be between 1 and 1000")
    settings = json.loads((ASSETS / "settings.json").read_text(encoding="utf-8"))
    records = [p for card in catalog(web_root.resolve(), settings) for p in card["publications"]]
    if len(records) > max_publications:
        raise ValueError("Frozen publication inventory exceeds the explicit request limit")
    # Validate every route before the first network request.
    urls = [publication_url(base_url, p["url"]) for p in records]
    if len(set(urls)) != len(urls):
        raise ValueError("Duplicate frozen publication URLs")
    entries = []
    for record, url in zip(records, urls):
        entries.append({
            "model": record["model"], "market": record["region"],
            "language": record["lang"] if record["language_scope"] == "single" else None,
            "language_scope": record["language_scope"], "version": record["version"],
            "url": url, "http_accessibility": probe(url),
        })
    failures = sum(e["http_accessibility"]["status"] != "ok" for e in entries)
    return {
        "schema": "manual-operations-http-health/v1",
        "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": ("failed" if failures else "ok") if entries else "no_data",
        "summary": {"indexed_publications": len(entries), "http_failures": failures if entries else None},
        "entries": entries,
        "coverage_scope": "frozen index only; not the full approved intake or translation denominator",
        "deployment_identity": {"status": "no_data", "reason": "HTTP success does not verify a deployed version or receipt"},
        "translation_coverage": {"status": "no_data", "reason": "Approved target-language denominator not supplied"},
        "visitor_metrics": {"status": "no_data", "reason": "No visitor tracking is collected"},
        "operations_owner": {"status": "no_data", "reason": "Owner and response cadence require operator assignment"},
        "limitations": ["HEAD checks only; bodies, assets, fragments and soft-404s are not validated",
                        "No automatic retries, workflow dispatch, writeback or rollback"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--web-root", required=True, type=Path)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--max-publications", type=int, default=100)
    args = parser.parse_args(argv)
    report = build_online_health_report(args.web_root, base_url=args.base_url,
                                        max_publications=args.max_publications)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"]))
    return 1 if report["status"] == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
