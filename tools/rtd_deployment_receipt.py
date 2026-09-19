"""Bind a successful frozen Sphinx deployment to source and served bytes."""
from __future__ import annotations

import hashlib
from http.client import IncompleteRead, RemoteDisconnected
from html.parser import HTMLParser
import json
from pathlib import Path, PurePosixPath
import re
from ssl import SSLEOFError
from time import monotonic
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from uuid import uuid4

from tools.manual_operations_online_health import _https_url, _origin, publication_url
from tools.utils.path_utils import PathSegments

RECEIPT = "manual-deployment.json"
SCHEMA = "manual-rtd-deployment/v1"
# Single source of truth for the production RTD base URL; CLI defaults and
# expected-project derivation reference this constant instead of restating it.
DEFAULT_RTD_BASE_URL = "https://ht-doc.readthedocs.io"
_PROJECT_SLUG = r"[A-Za-z0-9_.-]+"
_PROJECT_SLUG_META = re.compile(
    rb'<meta name="readthedocs-project-slug" content="(' + _PROJECT_SLUG.encode("ascii") + rb')" />')
MAX_FILES = 10000
MAX_FILE_BYTES = 32 * 1024 * 1024
MAX_TOTAL_BYTES = 512 * 1024 * 1024
MAX_FETCH_ATTEMPTS = 3
FETCH_BUDGET_SECONDS = 45
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


def _canonical_probe_url(url: str) -> str:
    """Accept only our internal cache nonce while retaining strict URL checks."""
    parsed = urlsplit(url)
    if parsed.query and re.fullmatch(r"receipt_probe=[0-9a-f]{32}", parsed.query) is None:
        raise ValueError("Unexpected deployment probe query")
    return _https_url(parsed._replace(query="").geturl())


def _probe_url(url: str) -> str:
    return _https_url(url) + "?receipt_probe=" + uuid4().hex


class _Redirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target = _canonical_probe_url(newurl)
        if _origin(_canonical_probe_url(req.full_url)) != _origin(target):
            raise ValueError("Cross-origin deployment redirect refused")
        return super().redirect_request(req, fp, code, msg, headers, _probe_url(target))


def _read_complete(response, deadline: float) -> bytes:
    length = response.headers.get("Content-Length")
    if length is not None:
        if re.fullmatch(r"[0-9]+", length) is None or int(length) > MAX_FILE_BYTES:
            raise ValueError("Invalid deployment Content-Length or size limit")
        length = int(length)
    if response.headers.get("Content-Encoding", "identity").lower() != "identity":
        raise ValueError("Deployment response changed requested identity encoding")
    data = bytearray()
    while True:
        if monotonic() >= deadline:
            raise TimeoutError("Deployment read exceeded its time budget")
        chunk = response.read(min(65536, MAX_FILE_BYTES + 1 - len(data)))
        if monotonic() >= deadline:
            raise TimeoutError("Deployment read exceeded its time budget")
        if not chunk:
            break
        data.extend(chunk)
        if len(data) > MAX_FILE_BYTES:
            raise ValueError("Deployment response exceeds size limit")
    if length is not None and len(data) != length:
        raise IncompleteRead(bytes(data), max(0, length - len(data)))
    return bytes(data)


def _fetch(url: str) -> bytes:
    _https_url(url)
    deadline = monotonic() + FETCH_BUDGET_SECONDS
    transient = (IncompleteRead, RemoteDisconnected, ConnectionError, TimeoutError, SSLEOFError)
    for attempt in range(MAX_FETCH_ATTEMPTS):
        if monotonic() >= deadline:
            raise TimeoutError("Deployment read exceeded its time budget")
        request = Request(_probe_url(url), headers={
            "User-Agent": "auto-manual-deployment/1", "Accept-Encoding": "identity",
            "Cache-Control": "no-cache, no-transform", "Pragma": "no-cache",
        })
        try:
            with build_opener(_Redirect()).open(request, timeout=min(15, deadline - monotonic())) as response:
                final_url = _canonical_probe_url(response.geturl())
                if response.status != 200 or _origin(final_url) != _origin(url):
                    raise ValueError("Deployment response is not same-origin HTTP 200")
                return _read_complete(response, deadline)
        except HTTPError as exc:
            exc.close()
            if exc.code not in {408, 429, 500, 502, 503, 504} or attempt + 1 == MAX_FETCH_ATTEMPTS:
                raise
        except URLError as exc:
            if not isinstance(exc.reason, transient) or attempt + 1 == MAX_FETCH_ATTEMPTS:
                raise
        except transient:
            if attempt + 1 == MAX_FETCH_ATTEMPTS:
                raise
    raise RuntimeError("Deployment fetch attempts exhausted")  # pragma: no cover


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


def _without_rtd_proxy_injection(path: str, data: bytes) -> bytes:
    """Remove only the observed RTD-owned block immediately before head closure."""
    if not path.endswith(".html"):
        return data
    head, boundary, body = data.partition(b"</head>")
    if not boundary:
        return data
    pattern = (
        rb'<script async type="text/javascript" '
        rb'src="/_/static/javascript/readthedocs-addons\.js"></script>'
        rb'<meta name="readthedocs-project-slug" content="[A-Za-z0-9_.-]+" />'
        rb'<meta name="readthedocs-version-slug" content="[A-Za-z0-9_.-]+" />'
        rb'<meta name="readthedocs-resolver-filename" content="/'
        + re.escape(path.encode("utf-8")) + rb'" />'
        rb'<meta name="readthedocs-http-status" content="200" />$'
    )
    # Anything extra, moved into the body, or naming another route remains hashed.
    return re.sub(pattern, b"", head) + boundary + body


def rtd_project_slug_from_base_url(base_url: str) -> str | None:
    """Derive the expected project slug from a https://<slug>.readthedocs.io base URL.

    Returns None for any other host shape (custom domains, extra subdomains,
    lookalike registrable domains); callers then have no derivable expectation.
    """
    if not isinstance(base_url, str):
        return None
    try:
        host = urlsplit(base_url).hostname or ""
    except ValueError:
        return None
    match = re.fullmatch(r"([a-z0-9](?:[a-z0-9-]*[a-z0-9])?)\.readthedocs\.io", host.lower())
    return match.group(1) if match else None


def _served_project_slugs(path: str, data: bytes) -> set[str]:
    """Project slugs the served page declares via RTD-injected meta tags."""
    if not path.endswith(".html"):
        return set()
    return {match.group(1).decode("ascii") for match in _PROJECT_SLUG_META.finditer(data)}


def verify_deployment(web_root: Path, base_url: str, routes: list[str],
                      expected_project_slug: str | None = None) -> dict:
    """Fail closed before callers write links; never treat HTTP 200 as identity.

    With expected_project_slug given, every fetched HTML page's RTD-injected
    readthedocs-project-slug meta must name exactly that project, and at least
    one page must declare it — byte identity alone cannot prove the bytes were
    served by the intended RTD project. Without it, behavior is unchanged.
    """
    _https_url(base_url)
    if expected_project_slug is not None and (
            not isinstance(expected_project_slug, str)
            or re.fullmatch(_PROJECT_SLUG, expected_project_slug) is None):
        raise ValueError("Invalid expected RTD project slug")
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
    proxy_injections = []
    observed_slugs: set[str] = set()
    total = 0
    while selected - checked:
        path = min(selected - checked)
        if path not in files:
            raise ValueError(f"Deployment receipt lacks a referenced resource: {path}")
        data = _fetch(publication_url(base_url, path))
        total += len(data)
        if total > MAX_TOTAL_BYTES:
            raise ValueError("Deployment verification exceeds total byte limit")
        if expected_project_slug is not None:
            served = _served_project_slugs(path, data)
            observed_slugs.update(served)
            foreign = sorted(served - {expected_project_slug})
            if foreign:
                raise ValueError(
                    "Live deployment declares RTD project "
                    f"{', '.join(foreign)} instead of {expected_project_slug}: {path}")
        if hashlib.sha256(data).hexdigest() != files[path]:
            normalized = _without_rtd_proxy_injection(path, data)
            if normalized == data or hashlib.sha256(normalized).hexdigest() != files[path]:
                raise ValueError(f"Live deployment bytes differ: {path}")
            data = normalized
            proxy_injections.append(path)
        checked.add(path)
        selected.update(_dependencies(path, data, base_url))
        if len(selected) > MAX_FILES:
            raise ValueError("Deployment dependency count exceeds safety limit")
    result = {"schema": SCHEMA, "status": "verified", "source_sha256": fingerprint,
              "routes": routes, "verified_files": len(selected), "verified_bytes": total,
              "rtd_proxy_injections_removed": proxy_injections}
    if expected_project_slug is not None:
        if not observed_slugs:
            raise ValueError(
                "Live deployment never declared the expected RTD project slug "
                f"{expected_project_slug}: no readthedocs-project-slug meta observed")
        result["expected_project_slug"] = expected_project_slug
    return result
