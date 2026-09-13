"""Bind a successful frozen Sphinx deployment to source and served bytes."""
from __future__ import annotations

import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path, PurePosixPath
import re
from urllib.parse import unquote, urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from tools.manual_operations_online_health import _https_url, _origin, publication_url
from tools.utils.path_utils import PathSegments

RECEIPT = "manual-deployment.json"
SCHEMA = "manual-rtd-deployment/v1"
MAX_FILES = 10000
MAX_FILE_BYTES = 32 * 1024 * 1024
MAX_TOTAL_BYTES = 512 * 1024 * 1024
_CACHE = {".doctrees", "__pycache__", ".git"}


def _route(value: str) -> str:
    if (not isinstance(value, str) or not value or "%" in value
            or any(part in {"", ".", ".."} for part in value.split("/"))):
        raise ValueError("Unsafe deployment path")
    publication_url("https://example.invalid", value)
    return value


def _inventory(root: Path) -> dict[str, str]:
    result = {}
    total = 0
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if path.is_symlink():
            raise ValueError("Deployment trees must not contain symlinks")
        if any(part in _CACHE for part in relative.parts) or not path.is_file():
            continue
        if relative.as_posix() == RECEIPT:
            continue
        size = path.stat().st_size
        total += size
        if size > MAX_FILE_BYTES or total > MAX_TOTAL_BYTES or len(result) >= MAX_FILES:
            raise ValueError("Deployment inventory exceeds safety limits")
        result[_route(relative.as_posix())] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def source_fingerprint(web_root: Path) -> str:
    web_root = Path(web_root)
    if (web_root.is_symlink() or web_root.name != PathSegments.WEB
            or web_root.parent.name != PathSegments.PUBLISH
            or not (web_root.parent / "publish_manifest.json").is_file()):
        raise ValueError("Expected a frozen publish/web source with publish manifest")
    inventory = _inventory(web_root.parent)
    if not inventory:
        raise ValueError("Empty frozen deployment source")
    return hashlib.sha256(json.dumps(inventory, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write_deployment_receipt(app, exception) -> None:
    """Sphinx build-finished callback; unrelated/non-HTML builds are untouched."""
    source = Path(app.srcdir)
    if (exception is not None or getattr(app.builder, "format", None) != "html"
            or source.name != PathSegments.WEB or source.parent.name != PathSegments.PUBLISH
            or not (source.parent / "publish_manifest.json").is_file()):
        return
    payload = {"schema": SCHEMA, "source_sha256": source_fingerprint(source),
               "files": _inventory(Path(app.outdir))}
    if not any(path.endswith(".html") for path in payload["files"]):
        raise ValueError("Successful deployment contains no HTML")
    (Path(app.outdir) / RECEIPT).write_text(
        json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")


class _Redirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if _origin(req.full_url) != _origin(newurl):
            raise ValueError("Cross-origin deployment redirect refused")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _fetch(url: str) -> bytes:
    _https_url(url)
    request = Request(url, headers={"User-Agent": "auto-manual-deployment/1"})
    with build_opener(_Redirect()).open(request, timeout=15) as response:
        if response.status != 200 or _origin(response.geturl()) != _origin(url):
            raise ValueError("Deployment response is not same-origin HTTP 200")
        data = response.read(MAX_FILE_BYTES + 1)
        if len(data) > MAX_FILE_BYTES:
            raise ValueError("Deployment response exceeds size limit")
        return data


class _Resources(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []
        self.in_style = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "base":
            raise ValueError("HTML base URL overrides are not permitted")
        self.urls.extend(_css_urls(attrs.get("style", "")))
        if tag == "style":
            self.in_style = True
        if tag == "object":
            self.urls.append(attrs.get("data", ""))
        if tag in {"img", "script", "source", "video", "audio", "iframe", "embed"}:
            self.urls.extend([attrs.get("src", ""), attrs.get("poster", "")])
            self.urls.extend(item.strip().split()[0] for item in attrs.get("srcset", "").split(",")
                             if item.strip())
        if tag == "link" and set(attrs.get("rel", "").split()) & {"stylesheet", "icon", "preload"}:
            self.urls.append(attrs.get("href", ""))

    def handle_endtag(self, tag):
        if tag == "style":
            self.in_style = False

    def handle_data(self, data):
        if self.in_style:
            self.urls.extend(_css_urls(data))


def _css_urls(text: str) -> list[str]:
    return (re.findall(r"url\(\s*['\"]?([^)'\"\s]+)", text)
            + re.findall(r"@import\s+['\"]([^'\"]+)", text))


def _dependencies(path: str, data: bytes, base_url: str) -> set[str]:
    urls = []
    if path.endswith(".html"):
        parser = _Resources()
        parser.feed(data.decode("utf-8"))
        urls = parser.urls
    elif path.endswith(".css"):
        urls = _css_urls(data.decode("utf-8"))
    prefix = urlsplit(base_url.rstrip("/") + "/").path
    result = set()
    for value in urls:
        if not value or value.startswith(("data:", "#")):
            continue
        absolute = urljoin(publication_url(base_url, path), value)
        if _origin(absolute.split("?", 1)[0].split("#", 1)[0]) != _origin(base_url):
            # External theme/CDN resources are not frozen publication assets.
            continue
        parsed = urlsplit(absolute)
        if not parsed.path.startswith(prefix):
            raise ValueError("Deployment dependency escapes the publication root")
        result.add(_route(unquote(parsed.path[len(prefix):])))
    return result


def verify_deployment(web_root: Path, base_url: str, routes: list[str]) -> dict:
    """Fail closed before callers write links; never treat HTTP 200 as identity."""
    _https_url(base_url)
    if not routes or len(routes) > MAX_FILES or len(set(routes)) != len(routes):
        raise ValueError("Select nonempty unique deployment routes")
    for route in routes:
        if not _route(route).endswith(".html"):
            raise ValueError("Deployment route must be HTML")
    fingerprint = source_fingerprint(web_root)
    payload = json.loads(_fetch(publication_url(base_url, RECEIPT)))
    if (not isinstance(payload, dict) or payload.get("schema") != SCHEMA
            or payload.get("source_sha256") != fingerprint):
        raise ValueError("Live deployment does not match frozen source")
    files = payload.get("files")
    if not isinstance(files, dict) or not files or len(files) > MAX_FILES:
        raise ValueError("Invalid deployment file inventory")
    for path, digest in files.items():
        _route(path)
        if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise ValueError("Invalid deployment file digest")
    if not set(routes).issubset(files):
        raise ValueError("Deployment receipt lacks selected routes")
    selected = set(routes)
    checked = set()
    total = 0
    while selected - checked:
        path = min(selected - checked)
        if path not in files:
            raise ValueError(f"Deployment receipt lacks a referenced resource: {path}")
        data = _fetch(publication_url(base_url, path))
        total += len(data)
        if total > MAX_TOTAL_BYTES:
            raise ValueError("Deployment verification exceeds total byte limit")
        if hashlib.sha256(data).hexdigest() != files[path]:
            raise ValueError(f"Live deployment bytes differ: {path}")
        checked.add(path)
        selected.update(_dependencies(path, data, base_url))
        if len(selected) > MAX_FILES:
            raise ValueError("Deployment dependency count exceeds safety limit")
    return {"schema": SCHEMA, "status": "verified", "source_sha256": fingerprint,
            "routes": routes, "verified_files": len(selected), "verified_bytes": total}
