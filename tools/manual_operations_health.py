"""Read-only health report for frozen Web publication artifacts."""
from __future__ import annotations

import argparse
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from typing import Any

from tools.utils.path_utils import PathSegments

SCHEMA = "manual-operations-health/v2"


class _References(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.references: list[str] = []

    def handle_starttag(self, tag, attrs):
        self.references.extend(value for key, value in attrs if key in {"src", "href"} and value)


def _ok(value: Any) -> dict[str, Any]:
    return {"status": "ok", "value": value}


def _no_data(reason: str) -> dict[str, Any]:
    return {"status": "no_data", "value": None, "reason": reason}


def _metadata_paths(releases_root: Path) -> list[Path]:
    return sorted(
        releases_root.glob(
            f"*/*/*/{PathSegments.LATEST}/{PathSegments.WEB}/{PathSegments.PUBLISH_META_JSON}"
        )
    )


def _resolve_html_dir(raw: str, *, trusted_root: Path) -> Path | None:
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = trusted_root / candidate
    try:
        resolved = candidate.resolve()
        return resolved if resolved.is_relative_to(trusted_root.resolve()) else None
    except (OSError, RuntimeError):
        return None


def _missing_refs(html_file: Path, *, html_root: Path) -> list[str]:
    missing: list[str] = []
    label = html_file.relative_to(html_root).as_posix()
    try:
        if not html_file.resolve().is_relative_to(html_root):
            return [f"{label}: HTML file escapes artifact root"]
        parser = _References()
        parser.feed(html_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        return [f"{label}: unreadable HTML ({exc})"]
    for raw in parser.references:
        try:
            parsed = urlsplit(raw)
        except ValueError:
            missing.append(f"{label}: malformed reference {raw}")
            continue
        if parsed.netloc.count("[") != parsed.netloc.count("]"):
            missing.append(f"{label}: malformed reference {raw}")
            continue
        if parsed.scheme or parsed.netloc:
            continue
        # Query/fragment do not change the local file identity, but must not
        # cause a reference to be skipped.
        if not parsed.path:
            continue
        decoded = unquote(parsed.path)
        candidate = html_root / decoded.lstrip("/") if decoded.startswith("/") else html_file.parent / decoded
        try:
            if not candidate.resolve().is_relative_to(html_root):
                missing.append(f"{label}: reference escapes artifact root: {raw}")
            elif not candidate.is_file():
                missing.append(f"{label}: {raw}")
        except (OSError, ValueError, RuntimeError):
            missing.append(f"{label}: invalid local reference: {raw}")
    return missing


def build_health_report(releases_root: Path, *, repo_root: Path | None = None) -> dict[str, Any]:
    """Inspect metadata and every HTML file without network access or writes."""
    releases_root = releases_root.resolve()
    # The release tree is the only trusted input scope.  Do not infer a
    # broader repository root from an arbitrary caller-supplied path.
    trusted_root = releases_root
    repo_root = (repo_root or Path.cwd()).resolve()
    metadata_paths = _metadata_paths(releases_root)
    if not metadata_paths:
        reason = f"no frozen web publish metadata under {releases_root}"
        return {
            "schema": SCHEMA, "source": releases_root.as_posix(), "status": "no_data",
            "summary": {"targets": 0, "failure_count": None, "missing_assets": None},
            "dimensions": {key: _no_data(reason) for key in ("models", "markets", "languages", "versions")},
            "entries": [], "failures": [],
            "deployment": _no_data("deployment is not probed by this local report"),
            "visitor_metrics": _no_data("visitor tracking is not collected"),
        }

    entries: list[dict[str, Any]] = []
    failures: list[str] = []
    for metadata_path in metadata_paths:
        try:
            if not metadata_path.resolve().is_relative_to(releases_root):
                raise ValueError("metadata escapes releases root")
            payload = json.loads(metadata_path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("metadata is not an object")
            required = ("schema_version", "model", "region", "lang", "version", "html_dir")
            if any(not isinstance(payload.get(field), str) or not payload[field].strip() for field in required):
                raise ValueError("metadata has missing or non-string required fields")
            if payload["schema_version"] != "auto-manual-web-publish/v1":
                raise ValueError("unsupported Web Publish metadata schema")
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            failures.append(f"{metadata_path}: invalid metadata ({exc})")
            entries.append({"metadata": metadata_path.as_posix(), "status": "invalid", "error": str(exc)})
            continue
        dimensions: dict[str, dict[str, Any]] = {}
        for field in ("model", "region", "lang", "version"):
            value = payload[field].strip()
            dimensions[field] = _ok(value) if value else _no_data(f"missing {field}")
        raw_dir = payload["html_dir"].strip()
        html_dir = _resolve_html_dir(raw_dir, trusted_root=repo_root)
        if html_dir is not None and not html_dir.is_relative_to(trusted_root):
            html_dir = None
        local_failure: list[str] = []
        if html_dir is None or not html_dir.is_dir():
            local_failure.append("HTML directory missing or outside trusted release root")
            html_files: list[Path] = []
        else:
            html_files = sorted(html_dir.rglob("*.html"))
            if not (html_dir / "index.html").is_file():
                local_failure.append("missing HTML index")
        missing_assets = [ref for html_file in html_files for ref in _missing_refs(html_file, html_root=html_dir)]
        if missing_assets:
            local_failure.append(f"{len(missing_assets)} missing local references: {', '.join(missing_assets)}")
        if local_failure:
            failures.append(f"{metadata_path}: " + "; ".join(local_failure))
        entries.append({
            "metadata": metadata_path.as_posix(),
            "model": dimensions["model"], "market": dimensions["region"],
            "language": dimensions["lang"], "version": dimensions["version"],
            "artifact_health": {"status": "failed" if local_failure else "ok",
                                 "missing_assets": missing_assets, "html_files": len(html_files)},
            "html_index": _ok((html_dir / "index.html").as_posix()) if html_dir and (html_dir / "index.html").is_file() else _no_data("HTML index unavailable"),
        })
    field_map = {"models": "model", "markets": "market", "languages": "language", "versions": "version"}
    values = {
        field: sorted({entry[key]["value"] for entry in entries if entry.get(key, {}).get("status") == "ok"})
        for field, key in field_map.items()
    }
    dimensions = {
        field: (_ok(value) if value else _no_data("no valid metadata values"))
        for field, value in values.items()
    }
    return {
        "schema": SCHEMA, "source": releases_root.as_posix(), "status": "failed" if failures else "ok",
        "summary": {"targets": len(entries), "failure_count": len(failures), "missing_assets": sum(len(e.get("artifact_health", {}).get("missing_assets", [])) for e in entries)},
        "dimensions": dimensions,
        "entries": entries, "failures": failures,
        "deployment": _no_data("deployment is not probed by this local report"),
        "visitor_metrics": _no_data("visitor tracking is not collected"),
        "coverage_notes": ["HTML src/href references are checked; CSS url() and srcset are not inspected"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a read-only Web publication health report")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--releases-root", type=Path, default=Path(PathSegments.REPORTS) / PathSegments.RELEASES)
    parser.add_argument("--output", type=Path, default=Path(PathSegments.REPORTS) / "manual_operations_health" / "health.json")
    args = parser.parse_args(argv)
    report = build_health_report(args.releases_root, repo_root=args.repo_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False, sort_keys=True))
    return 1 if report["status"] == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
