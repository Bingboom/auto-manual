"""Private Read the Docs Business verification via local publish integrity + Builds API."""
from __future__ import annotations

from collections.abc import Callable
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlsplit
from urllib.request import Request, urlopen

from tools.manual_operations_online_health import _https_url
from tools.rtd.deployment_receipt import (
    TRANSIENT_STATUS,
    DeploymentThrottled,
    FetchSession,
    _dependencies,
    retry_after_seconds,
    rtd_project_slug_from_base_url,
    source_fingerprint,
)
from tools.utils.path_utils import PathSegments

API_TOKEN_ENV = "READTHEDOCS_API_TOKEN"
VERIFICATION_MODE_LIVE = "live-html"
VERIFICATION_MODE_PRIVATE = "rtd-private-build"
_COMMIT_RE = re.compile(r"[0-9a-f]{40}")
_HTML_IMG_SRC_RE = re.compile(r"""<img\b[^>]*?\bsrc=(['"])([^'"]+)\1""", re.IGNORECASE)
_MD_IMG_SRC_RE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)")
_IN_PROGRESS_STATES = frozenset({"triggered", "cloning", "installing", "building"})


class RtdBuildError(RuntimeError):
    """Structured failure when checking a Read the Docs v3 build."""

    def __init__(
        self,
        message: str,
        *,
        category: str,
        build_info: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.category = category
        self.build_info = build_info


class LocalIntegrityError(ValueError):
    """Local frozen publish tree failed structural or manifest integrity checks."""

    def __init__(self, message: str, *, category: str = "local-integrity-failed") -> None:
        super().__init__(message)
        self.category = category


def rtd_builds_api(
    base_url: str,
    *,
    project_slug: str | None = None,
    business_hint: bool = False,
) -> tuple[str, str, bool] | None:
    """Builds API URL, dashboard build prefix, and whether Business auth is used."""
    slug = project_slug or rtd_project_slug_from_base_url(base_url)
    if slug is None:
        return None
    host = (urlsplit(base_url).hostname or "").lower()
    if host.endswith(".readthedocs-hosted.com"):
        business = True
    elif host.endswith(".readthedocs.io"):
        business = False
    else:
        business = business_hint
    domain = "readthedocs.com" if business else "readthedocs.org"
    return (
        f"https://{domain}/api/v3/projects/{slug}/builds/",
        f"https://app.{domain}/projects/{slug}/builds/",
        business,
    )


def rtd_version_slug_from_base_url(base_url: str) -> str:
    """Extract the RTD version slug from ``/lang/version`` base URLs (default ``latest``)."""
    segments = [seg for seg in urlsplit(base_url).path.split("/") if seg]
    if len(segments) >= 2:
        return segments[1]
    if len(segments) == 1:
        return segments[0]
    return "latest"


def fetch_rtd_builds_bytes(
    api_url: str,
    token: str,
    *,
    urlopen_fn: Callable[..., Any] | None = None,
    fetch_fn: Callable[[str], bytes] | None = None,
    timeout: float = 30.0,
) -> bytes:
    """Fetch raw JSON bytes from the RTD v3 Builds API without leaking tokens."""
    _https_url(api_url)
    if not token:
        if fetch_fn is not None:
            return fetch_fn(api_url)
        return FetchSession().fetch(api_url)
    headers = {
        "Authorization": f"Token {token}",
        "User-Agent": "auto-manual-deployment/1",
        "Accept": "application/json",
    }
    request = Request(api_url, headers=headers)
    open_fn = urlopen_fn or urlopen
    try:
        with open_fn(request, timeout=timeout) as response:
            return response.read()
    except HTTPError as exc:
        code = exc.code
        delay = retry_after_seconds(exc.headers)
        exc.close()
        if code in {401, 403}:
            raise RtdBuildError(
                f"RTD Builds API rejected {API_TOKEN_ENV} (HTTP {code})",
                category="rtd-auth-failed",
            ) from None
        if code in {429, 503}:
            raise DeploymentThrottled(
                f"RTD Builds API rate-limited the request (HTTP {code})",
                retry_after=delay,
            ) from None
        category = "transport" if code >= 500 or code in TRANSIENT_STATUS else "rtd-api-error"
        raise RtdBuildError(
            f"RTD Builds API returned HTTP {code}",
            category=category,
        ) from None
    except (URLError, TimeoutError, OSError) as exc:
        raise RtdBuildError(
            f"RTD Builds API request failed ({type(exc).__name__})",
            category="transport",
        ) from exc


def fetch_rtd_builds_payload(
    api_url: str,
    token: str,
    *,
    urlopen_fn: Callable[..., Any] | None = None,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Fetch and parse one RTD v3 Builds API response."""
    raw = fetch_rtd_builds_bytes(api_url, token, urlopen_fn=urlopen_fn, timeout=timeout)
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RtdBuildError(
            "RTD Builds API returned malformed JSON",
            category="rtd-api-error",
        ) from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
        raise RtdBuildError(
            "RTD Builds API response is missing a results list",
            category="rtd-api-error",
        )
    return payload


def _git_output(repo: Path, *args: str) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return proc.stdout.strip() if proc.returncode == 0 else None


def _make_is_ancestor(repo: Path | None) -> Callable[[str, str], bool]:
    def is_ancestor(ancestor: str, descendant: str) -> bool:
        anc = ancestor.lower()
        desc = descendant.lower()
        if not (_COMMIT_RE.fullmatch(anc) and _COMMIT_RE.fullmatch(desc)):
            return False
        if anc == desc:
            return True
        if repo is None:
            return False
        try:
            proc = subprocess.run(
                ["git", "-C", str(repo), "merge-base", "--is-ancestor", anc, desc],
                capture_output=True,
                text=True,
                check=False,
                timeout=15,
            )
        except (OSError, subprocess.SubprocessError):
            return False
        return proc.returncode == 0

    return is_ancestor


def resolve_git_commit_context(
    publish_root: Path,
    *,
    expected_commit: str | None = None,
) -> tuple[str, str, Callable[[str, str], bool]]:
    """Resolve ``(head_commit, publish_commit, is_ancestor)`` for ``publish_root``."""
    toplevel_raw = _git_output(publish_root, "rev-parse", "--show-toplevel")
    repo = Path(toplevel_raw) if toplevel_raw else None
    if expected_commit is not None:
        normalized = expected_commit.strip().lower()
        if not _COMMIT_RE.fullmatch(normalized):
            raise LocalIntegrityError(
                f"Expected git commit must be a 40-character hex SHA: {expected_commit!r}"
            )
        return normalized, normalized, _make_is_ancestor(repo)
    if repo is None:
        raise LocalIntegrityError(
            f"Cannot resolve git repository for {publish_root}; pass --expected-commit"
        )
    head = (_git_output(repo, "rev-parse", "HEAD") or "").lower()
    if not _COMMIT_RE.fullmatch(head):
        raise LocalIntegrityError(f"Cannot resolve HEAD commit for {repo}")
    publish_rel = publish_root.resolve().relative_to(repo.resolve()).as_posix()
    publish_commit = (_git_output(repo, "log", "-1", "--format=%H", "--", publish_rel) or "").lower()
    if not _COMMIT_RE.fullmatch(publish_commit):
        publish_commit = head
    return head, publish_commit, _make_is_ancestor(repo)


def _build_version_slug(build: dict[str, Any]) -> str | None:
    version = build.get("version")
    if isinstance(version, dict):
        slug = version.get("slug")
        return str(slug) if isinstance(slug, str) and slug else None
    if isinstance(version, str) and version:
        return version
    return None


def _build_is_finished(build: dict[str, Any]) -> bool:
    state = build.get("state")
    state_code = str(state.get("code") if isinstance(state, dict) else "").lower()
    if state_code in _IN_PROGRESS_STATES or state_code != "finished":
        return False
    if "finished" in build and build.get("finished") is None:
        return False
    return True


def _build_summary(
    build: dict[str, Any],
    *,
    dashboard_prefix: str,
    expected_version: str,
) -> dict[str, Any]:
    build_id = build.get("id")
    state = build.get("state")
    state_code = state.get("code") if isinstance(state, dict) else None
    return {
        "id": build_id,
        "url": f"{dashboard_prefix}{build_id}/" if build_id is not None else None,
        "commit": build.get("commit"),
        "state": state_code,
        "finished": build.get("finished"),
        "success": build.get("success"),
        "version": _build_version_slug(build) or expected_version,
    }


def _covering_builds(
    results: list[dict[str, Any]],
    *,
    head_norm: str,
    publish_norm: str,
    expected_version: str,
    is_ancestor: Callable[[str, str], bool],
) -> list[dict[str, Any]]:
    covering: list[dict[str, Any]] = []
    for item in results:
        if not isinstance(item, dict):
            continue
        version_slug = _build_version_slug(item)
        if version_slug is not None and version_slug != expected_version:
            continue
        commit = str(item.get("commit") or "").strip().lower()
        if not _COMMIT_RE.fullmatch(commit):
            continue
        if commit in {head_norm, publish_norm} or is_ancestor(publish_norm, commit):
            covering.append(item)
    return covering


def evaluate_rtd_builds(
    results: list[dict[str, Any]],
    *,
    head_commit: str,
    publish_commit: str,
    expected_version: str,
    dashboard_prefix: str,
    is_ancestor: Callable[[str, str], bool],
) -> dict[str, Any]:
    """Select the authoritative covering build for ``publish_commit`` or fail closed."""
    head_norm = head_commit.lower()
    publish_norm = publish_commit.lower()
    covering = _covering_builds(
        results,
        head_norm=head_norm,
        publish_norm=publish_norm,
        expected_version=expected_version,
        is_ancestor=is_ancestor,
    )
    if not covering:
        raise RtdBuildError(
            f"No RTD build for version {expected_version!r} covers publish commit "
            f"{publish_norm[:12]} (HEAD {head_norm[:12]})",
            category="stale-deployment",
        )

    latest = covering[0]
    info = _build_summary(
        latest,
        dashboard_prefix=dashboard_prefix,
        expected_version=expected_version,
    )
    if _build_is_finished(latest):
        if latest.get("success") is True:
            return {"status": "verified", "build": info}
        raise RtdBuildError(
            f"RTD build {info['id']} for commit {str(info['commit'])[:12]} failed "
            f"(success={latest.get('success')!r}, {info['url'] or 'no URL'})",
            category="rtd-build-failed",
            build_info=info,
        )

    latest_commit = str(latest.get("commit") or "").lower()
    if head_norm != publish_norm and latest_commit != publish_norm:
        for older in covering[1:]:
            if _build_is_finished(older) and older.get("success") is True:
                return {
                    "status": "verified",
                    "build": _build_summary(
                        older,
                        dashboard_prefix=dashboard_prefix,
                        expected_version=expected_version,
                    ),
                }

    raise RtdBuildError(
        f"RTD build {info['id']} for commit {str(info['commit'])[:12]} is still "
        f"{info['state'] or 'in-progress'} ({info['url'] or 'no URL'})",
        category="rtd-build-in-progress",
        build_info=info,
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_child_path(root: Path, relative: str) -> Path | None:
    if not relative or "%" in relative or "\\" in relative:
        return None
    parts = PurePosixPath(relative).parts
    if not parts or parts[0] in {"/", ""} or any(part in {".", ".."} for part in parts):
        return None
    candidate = root
    for part in parts:
        candidate = candidate / part
        if candidate.is_symlink():
            return None
    resolved_root = root.resolve(strict=False)
    resolved_candidate = candidate.resolve(strict=False)
    if not resolved_candidate.is_relative_to(resolved_root):
        return None
    return candidate


def _local_markdown_asset_refs(text: str) -> list[str]:
    refs: list[str] = []
    for match in _HTML_IMG_SRC_RE.finditer(text):
        refs.append(match.group(2))
    for match in _MD_IMG_SRC_RE.finditer(text):
        refs.append(match.group(1))
    return refs


def _check_markdown_assets(web_root: Path, md_path: Path) -> str | None:
    resolved_root = web_root.resolve(strict=False)
    try:
        text = md_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return f"cannot read {md_path.relative_to(web_root).as_posix()}: {exc}"
    for raw_ref in _local_markdown_asset_refs(text):
        ref = raw_ref.strip()
        if not ref or ref.startswith(("#", "data:", "http://", "https://", "mailto:")):
            continue
        clean_ref = unquote(ref.split("?", 1)[0].split("#", 1)[0])
        if not clean_ref:
            continue
        target_path = (
            web_root / clean_ref.lstrip("/")
            if clean_ref.startswith("/")
            else md_path.parent / clean_ref
        )
        resolved = target_path.resolve(strict=False)
        if not resolved.is_relative_to(resolved_root):
            return f"referenced asset escapes web root: {raw_ref}"
        if target_path.is_symlink() or not target_path.is_file() or target_path.stat().st_size == 0:
            return f"missing or empty local asset: {raw_ref}"
    return None


def _check_html_assets(web_root: Path, page: str, html_path: Path) -> str | None:
    resolved_root = web_root.resolve(strict=False)
    try:
        data = html_path.read_bytes()
        deps = _dependencies(page, data, "https://local.invalid")
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        return f"invalid local HTML {page}: {exc}"
    for dep in sorted(deps):
        dep_path = _safe_child_path(web_root, dep)
        if dep_path is None or not dep_path.resolve(strict=False).is_relative_to(resolved_root):
            return f"invalid local HTML asset reference: {dep}"
        if not dep_path.is_file() or dep_path.stat().st_size == 0:
            return f"missing or empty local HTML asset: {dep}"
    return None


def _validate_manifest_files(
    publish_root: Path,
    manifest_payload: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    raw_files = manifest_payload.get("files")
    if raw_files is None:
        return {}
    if not isinstance(raw_files, list) or not raw_files:
        raise LocalIntegrityError("Publish manifest files inventory is empty or invalid")
    by_path: dict[str, dict[str, Any]] = {}
    for entry in raw_files:
        if not isinstance(entry, dict):
            raise LocalIntegrityError("Publish manifest files entry must be an object")
        rel = entry.get("path")
        size = entry.get("size")
        sha256 = entry.get("sha256")
        if (
            not isinstance(rel, str)
            or not isinstance(size, int)
            or size < 0
            or not isinstance(sha256, str)
            or not re.fullmatch(r"[0-9a-f]{64}", sha256)
        ):
            raise LocalIntegrityError(f"Malformed publish manifest file entry: {entry!r}")
        disk_path = _safe_child_path(publish_root, rel)
        if disk_path is None or not disk_path.is_file():
            raise LocalIntegrityError(f"Publish tree is missing manifest file: {rel}")
        if disk_path.stat().st_size != size:
            raise LocalIntegrityError(f"Publish tree file size differs from manifest: {rel}")
        by_path[rel] = entry
    return by_path


def _check_local_html_target(
    *,
    web_root: Path,
    page: str,
    html_path: Path,
    manifest_files: dict[str, dict[str, Any]],
) -> str | None:
    manifest_key = f"{PathSegments.WEB}/{page}"
    if manifest_files and manifest_key in manifest_files:
        if _sha256_file(html_path) != manifest_files[manifest_key]["sha256"]:
            return f"local HTML sha256 differs from manifest: {page}"
    return _check_html_assets(web_root, page, html_path)


def _check_local_md_target(
    *,
    web_root: Path,
    route: str,
    stem: str,
    md_rel: str,
    md_path: Path,
    manifest_files: dict[str, dict[str, Any]],
) -> str | None:
    for root_file in ("conf.py", "index.md"):
        root_path = web_root / root_file
        if root_path.is_symlink() or not root_path.is_file() or root_path.stat().st_size == 0:
            return f"missing or empty publish/web/{root_file}"
    index_rel = f"{route}/index.md"
    index_path = _safe_child_path(web_root, index_rel)
    if index_path is None or not index_path.is_file() or index_path.stat().st_size == 0:
        return f"missing or empty target index: {index_rel}"
    if stem not in index_path.read_text(encoding="utf-8", errors="replace"):
        return f"target index {index_rel} does not reference {stem}"
    if manifest_files:
        for check_rel, disk in ((f"{PathSegments.WEB}/{md_rel}", md_path), (f"{PathSegments.WEB}/{index_rel}", index_path)):
            meta = manifest_files.get(check_rel)
            if meta is None:
                return f"publish_manifest.json files missing {check_rel}"
            if _sha256_file(disk) != meta["sha256"]:
                return f"local file sha256 differs from manifest: {check_rel}"
    return _check_markdown_assets(web_root, md_path)


def _check_single_local_target(
    *,
    web_root: Path,
    target: dict[str, str],
    manifest_entries: dict[tuple[str, str, str], dict[str, Any]],
    manifest_files: dict[str, dict[str, Any]],
) -> str | None:
    key = (target["model"], target["region"], target["lang"])
    manifest_entry = manifest_entries.get(key)
    if manifest_entry is None:
        return f"target {key[0]}/{key[1]}/{key[2]} missing from publish_manifest.json"
    page = target["page"]
    route = str(PurePosixPath(page).parent)
    stem = PurePosixPath(page).stem
    if manifest_entry.get("route") != route or Path(str(manifest_entry.get("manual", ""))).stem != stem:
        return f"target {key[0]}/{key[1]}/{key[2]} metadata does not match {page}"

    html_path = _safe_child_path(web_root, page)
    md_rel = f"{route}/{stem}.md"
    md_path = _safe_child_path(web_root, md_rel)
    has_html = html_path is not None and html_path.is_file() and html_path.stat().st_size > 0
    has_md = md_path is not None and md_path.is_file() and md_path.stat().st_size > 0
    if not has_html and not has_md:
        return f"missing or empty local page source/HTML for {page}"
    if has_html and html_path is not None:
        html_error = _check_local_html_target(
            web_root=web_root,
            page=page,
            html_path=html_path,
            manifest_files=manifest_files,
        )
        if html_error:
            return html_error
    if has_md and md_path is not None:
        return _check_local_md_target(
            web_root=web_root,
            route=route,
            stem=stem,
            md_rel=md_rel,
            md_path=md_path,
            manifest_files=manifest_files,
        )
    return None


def verify_local_publish_targets(
    web_root: Path,
    targets: list[dict[str, str]],
    *,
    manifest_payload: dict[str, Any] | None = None,
    session: FetchSession | None = None,
) -> tuple[str, dict[str, str]]:
    """Verify frozen ``docs/publish`` manifest, fingerprint, pages, and local assets."""
    fingerprint = (
        session.source_fingerprint(web_root)
        if session is not None
        else source_fingerprint(web_root)
    )
    publish_root = web_root.parent
    manifest_path = publish_root / "publish_manifest.json"
    if manifest_payload is None:
        try:
            manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise LocalIntegrityError(f"Cannot read publish manifest: {exc}") from exc
    if not isinstance(manifest_payload, dict) or not isinstance(manifest_payload.get("targets"), list):
        raise LocalIntegrityError("Invalid publish_manifest.json structure")
    manifest_files = _validate_manifest_files(publish_root, manifest_payload)
    manifest_entries = {
        (str(item.get("model")), str(item.get("region")), str(item.get("lang"))): item
        for item in manifest_payload["targets"]
        if isinstance(item, dict)
    }
    errors: dict[str, str] = {}
    for target in targets:
        err = _check_single_local_target(
            web_root=web_root,
            target=target,
            manifest_entries=manifest_entries,
            manifest_files=manifest_files,
        )
        if err:
            errors[target["page"]] = err
    return fingerprint, errors


def verify_private_rtd_deployment(
    web_root: Path,
    *,
    base_url: str,
    targets: list[dict[str, str]],
    project_slug: str,
    token: str,
    session: FetchSession | None = None,
    expected_commit: str | None = None,
    business_hint: bool = True,
    urlopen_fn: Callable[..., Any] | None = None,
) -> tuple[dict[str, str], dict[str, Any]]:
    """Run local integrity checks and RTD v3 Builds API verification."""
    if not token.strip():
        raise RtdBuildError(
            f"Private RTD site requires sign-in and {API_TOKEN_ENV} is not set",
            category="rtd-auth-failed",
        )
    api = rtd_builds_api(base_url, project_slug=project_slug, business_hint=business_hint)
    if api is None:
        raise RtdBuildError(
            f"Cannot derive RTD Builds API endpoint for {base_url!r}",
            category="rtd-api-error",
        )
    fingerprint, per_page_errors = verify_local_publish_targets(
        web_root,
        targets,
        session=session,
    )
    head_commit, publish_commit, is_ancestor = resolve_git_commit_context(
        web_root.parent,
        expected_commit=expected_commit,
    )
    expected_version = rtd_version_slug_from_base_url(base_url)
    payload = fetch_rtd_builds_payload(api[0], token, urlopen_fn=urlopen_fn)
    evaluation = evaluate_rtd_builds(
        payload["results"],
        head_commit=head_commit,
        publish_commit=publish_commit,
        expected_version=expected_version,
        dashboard_prefix=api[1],
        is_ancestor=is_ancestor,
    )
    return per_page_errors, {
        "verification_mode": VERIFICATION_MODE_PRIVATE,
        "source_sha256": fingerprint,
        "head_commit": head_commit,
        "publish_commit": publish_commit,
        "rtd_build": evaluation["build"],
    }
