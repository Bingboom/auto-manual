"""Read immutable Web release baselines without changing manual versions."""
from __future__ import annotations

import hashlib
import json
import re
from html import escape
from pathlib import Path

from tools.utils.path_utils import PathSegments

SCHEMA = "auto-manual-web-baseline/v1"
_VERSION = re.compile(r"V[0-9]+\.[0-9]+")
_SHA = re.compile(r"[0-9a-f]{64}")


def web_assets(root: Path, source: Path) -> dict[str, str]:
    """Use the deployment resource walker to bind the assembled image copies too."""
    from tools.rtd.deployment_receipt import _dependencies

    relative = source.relative_to(root).with_suffix(".html").as_posix()
    text = source.read_text(encoding="utf-8")
    images = re.findall(r"!\[[^\]]*\]\(([^\s)]+)\)", text)
    text += "".join(f'<img src="{escape(url, quote=True)}"/>' for url in images)
    result = {}
    pending = _dependencies(relative, text.encode(), "https://baseline.invalid")
    while pending:
        relative = pending.pop()
        path = (root / relative).resolve()
        if path.is_symlink() or not path.is_relative_to(root.resolve()) or not path.is_file():
            raise ValueError(f"Missing or unsafe baseline resource: {relative}")
        data = path.read_bytes()
        result[relative] = hashlib.sha256(data).hexdigest()
        pending.update(_dependencies(relative, data, "https://baseline.invalid") - result.keys())
    return result


def _assets_match(root: Path, assets: dict) -> bool:
    for relative, digest in assets.items():
        path = (root / relative).resolve()
        if (not path.is_relative_to(root.resolve()) or not path.is_file()
                or hashlib.sha256(path.read_bytes()).hexdigest() != digest):
            return False
    return True


def source_digest(directory: Path) -> str:
    """Bind the entire retained source package, including artwork and metadata."""
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError("Baseline source must be a real directory")
    files = {}
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            raise ValueError("Baseline source cannot contain symlinks")
        if path.is_file():
            files[path.relative_to(directory).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    if not files:
        raise ValueError("Baseline source package is empty")
    return hashlib.sha256(json.dumps(files, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _validate_record(data: dict, path: Path) -> None:
    if (not isinstance(data, dict) or data.get("schema") != SCHEMA
            or not isinstance(data.get("version"), str)
            or not _VERSION.fullmatch(data["version"]) or path.stem != data["version"]
            or not re.fullmatch(r"[0-9a-f]{40}", str(data.get("snapshot_commit", "")))
            or not _SHA.fullmatch(str(data.get("publish_manifest_sha256", "")))
            or not isinstance(data.get("publications"), list) or not data["publications"]):
        raise ValueError(f"Invalid Web baseline: {path.name}")


def _validate_publication(item: dict, seen: set) -> None:
    if not isinstance(item, dict):
        raise ValueError("Invalid baseline publication")
    route, manual = item.get("route"), item.get("manual")
    valid_fields = all(isinstance(item.get(k), str) and item[k]
                       for k in ("model", "region", "lang", "original_version"))
    if (not isinstance(route, str) or not isinstance(manual, str) or not valid_fields
            or not re.fullmatch(r"[A-Za-z0-9_/-]+", route)
            or not re.fullmatch(r"[A-Za-z0-9_-]+\.md", manual)
            or route in seen or route.split("/") != [item["model"], item["region"], item["lang"], "md"]
            or item.get("language_scope") not in ("single", "legacy_unspecified")
            or not _SHA.fullmatch(str(item.get("source_sha256", "")))
            or not _SHA.fullmatch(str(item.get("markdown_sha256", "")))):
        raise ValueError("Invalid or duplicate baseline publication")
    seen.add(route)
    _validate_assets(item.get("web_assets"))


def _validate_assets(assets: dict) -> None:
    if not isinstance(assets, dict):
        raise ValueError("Baseline needs an assembled resource inventory")
    for relative, digest in assets.items():
        if (not isinstance(relative, str) or not isinstance(digest, str)
                or not _SHA.fullmatch(digest) or relative.startswith("/")
                or any(p in ("", ".", "..") for p in relative.split("/"))):
            raise ValueError("Unsafe baseline resource inventory")


def read_baselines(root: Path) -> list[dict]:
    """Read business-owned records; absent baselines keep existing behavior."""
    directory = root.parent / "sources" / "baselines"
    if directory.is_symlink():
        raise ValueError("Baseline directory cannot be a symlink")
    result = []
    for path in sorted(directory.glob("*.json")):
        if path.is_symlink():
            raise ValueError("Baseline record cannot be a symlink")
        data = json.loads(path.read_text(encoding="utf-8"))
        _validate_record(data, path)
        seen = set()
        for item in data["publications"]:
            _validate_publication(item, seen)
        result.append(data)
    return result


def prepend_baseline(products: list[dict], pagename: str, context: dict) -> None:
    publication = next((p for product in products for p in product["publications"]
                        if p["url"] == f"{pagename}.html"), None)
    if publication is not None and publication.get("web_baselines"):
        context["body"] = baseline_markup(publication, context["pathto"]) + context.get("body", "")


def apply_baselines(root: Path, records: list[dict]) -> None:
    """Label matching retained packages only; later content is never relabelled."""
    by_url = {item["url"]: item for item in records}
    for baseline in read_baselines(root):
        for sealed in baseline["publications"]:
            url = f"{sealed['route']}/{Path(sealed['manual']).with_suffix('.html')}"
            current = by_url.get(url)
            if current is None or (current.get("version"), current.get("language_scope")) != (
                    sealed["original_version"], sealed["language_scope"]):
                continue
            source = root / sealed["route"] / sealed["manual"]
            package = root.parent / "sources" / PathSegments.WEB / sealed["route"]
            if (not source.is_file() or source.is_symlink()
                    or hashlib.sha256(source.read_bytes()).hexdigest() != sealed["markdown_sha256"]
                    or source_digest(package) != sealed["source_sha256"]
                    or not _assets_match(root, sealed["web_assets"])):
                continue
            current.setdefault("web_baselines", []).append(baseline["version"])


def baseline_markup(publication: dict, pathto) -> str:
    labels = publication.get("web_baselines", [])
    if not labels:
        return ""
    links = ", ".join(
        f'<a href="{escape(pathto(f"releases/web/{version}"), quote=True)}">{escape(version)}</a>'
        for version in labels
    )
    original = escape(str(publication.get("version") or ""))
    return (f'<p class="web-release-baseline">Web release baseline: {links}'
            f' · Original publication version: {original}</p>')


def collect_baseline_pages(app):
    from tools.rtd.portal import portal_data

    _, products = portal_data(app)
    current = {p["url"]: p for product in products for p in product["publications"]}
    for baseline in read_baselines(Path(app.srcdir)):
        rows = []
        for sealed in baseline["publications"]:
            url = f"{sealed['route']}/{Path(sealed['manual']).with_suffix('.html')}"
            rows.append({**sealed, "url": url,
                         "current_matches": baseline["version"] in current.get(url, {}).get("web_baselines", [])})
        yield f"releases/web/{baseline['version']}", {"baseline": baseline, "baseline_rows": rows, "title": f"网页发布基线 {baseline['version']}"}, \
            "web_baseline.html"
