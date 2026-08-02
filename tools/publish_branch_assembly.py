#!/usr/bin/env python3
"""Assemble frozen Web Publish sources below ``docs/publish``.

The queue renderer writes one versioned, verified MyST bundle plus
``latest/web/publish_meta.json``. This module copies only that Web bundle into
the dedicated publish-branch tree and rebuilds the aggregate Sphinx source.
Print Publish artifacts are deliberately outside this contract.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root


ROOT = bootstrap_repo_root(__file__, parent_count=1)

from tools.readthedocs_source import assemble_rtd_source  # noqa: E402
from tools.utils.path_utils import PathSegments, Paths  # noqa: E402


SCHEMA_VERSION = "auto-manual-web-publish-branch/v1"
TARGET_SCHEMA_VERSION = "auto-manual-web-publish-target/v1"
DEFAULT_MAX_FILE_SIZE_MB = 95
_SAFE_SEGMENT_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


@dataclass(frozen=True)
class WebPublishTarget:
    metadata_path: Path
    model: str
    region: str
    lang: str
    version: str
    built_at: str
    git_ref: str
    markdown_path: Path
    html_dir: Path

    @property
    def route(self) -> Path:
        return Path(self.model) / self.region / "md"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    paths = Paths(ROOT)
    parser = argparse.ArgumentParser(
        description="Assemble approved Web Publish outputs below docs/publish."
    )
    parser.add_argument("--releases-root", type=Path, default=paths.releases_dir)
    parser.add_argument("--output-dir", type=Path, default=paths.docs_publish_dir)
    parser.add_argument("--title", default="Auto Manual Library")
    parser.add_argument("--max-file-size-mb", type=int, default=DEFAULT_MAX_FILE_SIZE_MB)
    return parser.parse_args(argv)


def _resolved(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def _load_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cannot read JSON object: {path}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"JSON root must be an object: {path}")
    return payload


def _required_text(payload: dict[str, Any], field: str, *, source: Path) -> str:
    value = str(payload.get(field) or "").strip()
    if not value:
        raise RuntimeError(f"Web Publish metadata missing {field}: {source}")
    return value


def _safe_segment(value: str, *, field: str, source: Path) -> str:
    if not _SAFE_SEGMENT_RE.fullmatch(value):
        raise RuntimeError(f"unsafe {field} in Web Publish metadata {source}: {value!r}")
    return value


def _path_from_metadata(
    raw: str,
    *,
    repo_root: Path,
    releases_root: Path,
    source: Path,
) -> Path:
    path = Path(raw)
    resolved = path.resolve(strict=False) if path.is_absolute() else (repo_root / path).resolve(strict=False)
    try:
        resolved.relative_to(releases_root.resolve(strict=False))
    except ValueError as exc:
        raise RuntimeError(f"Web Publish metadata path escapes releases root in {source}: {raw}") from exc
    if not resolved.exists():
        raise RuntimeError(f"Web Publish metadata path does not exist in {source}: {resolved}")
    return resolved


def load_web_publish_target(
    metadata_path: Path,
    *,
    repo_root: Path,
    releases_root: Path,
) -> WebPublishTarget:
    payload = _load_json_object(metadata_path)
    if _required_text(payload, "schema_version", source=metadata_path) != "auto-manual-web-publish/v1":
        raise RuntimeError(f"unsupported Web Publish metadata schema: {metadata_path}")
    markdown_path = _path_from_metadata(
        _required_text(payload, "md_output_path", source=metadata_path),
        repo_root=repo_root,
        releases_root=releases_root,
        source=metadata_path,
    )
    html_dir = _path_from_metadata(
        _required_text(payload, "html_dir", source=metadata_path),
        repo_root=repo_root,
        releases_root=releases_root,
        source=metadata_path,
    )
    if not markdown_path.is_file():
        raise RuntimeError(f"Web Publish Markdown output is not a file: {markdown_path}")
    if not html_dir.is_dir() or not (html_dir / "index.html").is_file():
        raise RuntimeError(f"Web Publish HTML verification output has no index.html: {html_dir}")
    return WebPublishTarget(
        metadata_path=metadata_path,
        model=_safe_segment(
            _required_text(payload, "model", source=metadata_path),
            field="model",
            source=metadata_path,
        ),
        region=_safe_segment(
            _required_text(payload, "region", source=metadata_path),
            field="region",
            source=metadata_path,
        ),
        lang=_safe_segment(
            _required_text(payload, "lang", source=metadata_path),
            field="lang",
            source=metadata_path,
        ),
        version=_safe_segment(
            _required_text(payload, "version", source=metadata_path),
            field="version",
            source=metadata_path,
        ),
        built_at=_required_text(payload, "built_at", source=metadata_path),
        git_ref=_required_text(payload, "git_ref", source=metadata_path),
        markdown_path=markdown_path,
        html_dir=html_dir,
    )


def discover_web_publish_targets(
    *,
    repo_root: Path,
    releases_root: Path,
) -> list[WebPublishTarget]:
    metadata_paths = sorted(
        releases_root.glob(
            f"*/*/*/{PathSegments.LATEST}/{PathSegments.WEB}/{PathSegments.PUBLISH_META_JSON}"
        )
    )
    if not metadata_paths:
        raise RuntimeError(f"no latest Web Publish metadata found under {releases_root}")
    return [
        load_web_publish_target(path, repo_root=repo_root, releases_root=releases_root)
        for path in metadata_paths
    ]


def _replace_dir(path: Path) -> None:
    if path.exists():
        if path.is_symlink() or not path.is_dir():
            raise RuntimeError(f"publish destination must be a real directory: {path}")
        shutil.rmtree(path)
    path.mkdir(parents=True)


def _copy_markdown_source(target: WebPublishTarget, destination: Path) -> None:
    source_dir = target.markdown_path.parent
    destination.mkdir(parents=True, exist_ok=True)
    for directory_name in (PathSegments.ASSETS, PathSegments.STATIC):
        source = source_dir / directory_name
        if source.is_dir():
            shutil.copytree(source, destination / directory_name)
    for filename in ("conf.py", "index.md"):
        source = source_dir / filename
        if not source.is_file():
            raise RuntimeError(f"Web Publish source is missing {filename}: {source_dir}")
        shutil.copy2(source, destination / filename)
    shutil.copy2(target.markdown_path, destination / target.markdown_path.name)
    index_text = (destination / "index.md").read_text(encoding="utf-8")
    if target.markdown_path.stem not in index_text:
        raise RuntimeError(
            f"Web Publish index does not reference {target.markdown_path.stem}: {source_dir / 'index.md'}"
        )


def _source_root(output_dir: Path) -> Path:
    return output_dir / "sources" / PathSegments.WEB


def _stored_target_metadata(output_dir: Path) -> list[Path]:
    return sorted(_source_root(output_dir).glob("*/*/md/publish_meta.json"))


def stage_web_target(*, target: WebPublishTarget, output_dir: Path) -> Path:
    destination = _source_root(output_dir) / target.route
    _replace_dir(destination)
    _copy_markdown_source(target, destination)
    metadata_path = destination / PathSegments.PUBLISH_META_JSON
    metadata_path.write_text(
        json.dumps(
            {
                "schema_version": TARGET_SCHEMA_VERSION,
                "model": target.model,
                "region": target.region,
                "lang": target.lang,
                "version": target.version,
                "built_at": target.built_at,
                "git_ref": target.git_ref,
                "route": target.route.as_posix(),
                "manual": target.markdown_path.name,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return metadata_path


def rebuild_web_source(*, output_dir: Path, title: str) -> None:
    metadata_paths = _stored_target_metadata(output_dir)
    if not metadata_paths:
        raise RuntimeError(f"publish tree has no stored Web targets: {output_dir}")
    routes: dict[str, Path] = {}
    with tempfile.TemporaryDirectory(prefix="auto-manual-web-publish-") as temp_dir:
        build_root = Path(temp_dir) / PathSegments.BUILD
        build_root.mkdir()
        for metadata_path in metadata_paths:
            payload = _load_json_object(metadata_path)
            route = _required_text(payload, "route", source=metadata_path)
            if route in routes:
                raise RuntimeError(
                    f"duplicate Web route {route}: {routes[route]} and {metadata_path}"
                )
            routes[route] = metadata_path
            destination = build_root / route
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(metadata_path.parent, destination)
            (destination / PathSegments.PUBLISH_META_JSON).unlink()
        assembled = build_root / "rtd"
        assemble_rtd_source(build_root=build_root, output_dir=assembled, title=title)
        web_dir = output_dir / PathSegments.WEB
        _replace_dir(web_dir)
        shutil.copytree(assembled, web_dir, dirs_exist_ok=True)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _inventory(root: Path, *, base: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise RuntimeError(f"publish tree cannot contain symlinks: {path}")
        if path.is_file():
            records.append(
                {
                    "path": path.relative_to(base).as_posix(),
                    "size": path.stat().st_size,
                    "sha256": _sha256(path),
                }
            )
    return records


def _write_publish_manifest(output_dir: Path) -> Path:
    targets = [_load_json_object(path) for path in _stored_target_metadata(output_dir)]
    targets.sort(key=lambda item: (str(item.get("model") or ""), str(item.get("region") or "")))
    manifest_path = output_dir / "publish_manifest.json"
    manifest_path.unlink(missing_ok=True)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "built_at": max(str(item.get("built_at") or "") for item in targets),
        "targets": targets,
        "files": _inventory(output_dir, base=output_dir),
    }
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def _enforce_file_size_limit(output_dir: Path, *, max_file_size_mb: int) -> None:
    if max_file_size_mb <= 0:
        raise RuntimeError("max file size must be positive")
    limit = max_file_size_mb * 1024 * 1024
    oversized = [
        path
        for path in sorted(output_dir.rglob("*"))
        if path.is_file() and path.stat().st_size > limit
    ]
    if oversized:
        details = ", ".join(f"{path} ({path.stat().st_size} bytes)" for path in oversized)
        raise RuntimeError(
            f"publish branch file exceeds {max_file_size_mb} MiB safety limit: {details}"
        )


def assemble_web_publish_branch(
    *,
    repo_root: Path,
    releases_root: Path,
    output_dir: Path,
    title: str,
    max_file_size_mb: int = DEFAULT_MAX_FILE_SIZE_MB,
) -> Path:
    releases_root = releases_root.resolve(strict=False)
    output_dir = output_dir.resolve(strict=False)
    output_dir.mkdir(parents=True, exist_ok=True)
    for target in discover_web_publish_targets(
        repo_root=repo_root,
        releases_root=releases_root,
    ):
        stage_web_target(target=target, output_dir=output_dir)
    rebuild_web_source(output_dir=output_dir, title=title)
    manifest_path = _write_publish_manifest(output_dir)
    _enforce_file_size_limit(output_dir, max_file_size_mb=max_file_size_mb)
    return manifest_path


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        manifest_path = assemble_web_publish_branch(
            repo_root=ROOT,
            releases_root=_resolved(args.releases_root),
            output_dir=_resolved(args.output_dir),
            title=str(args.title),
            max_file_size_mb=int(args.max_file_size_mb),
        )
    except (OSError, RuntimeError) as exc:
        print(f"[web-publish-branch] ERROR: {exc}")
        return 1
    print(f"[web-publish-branch] manifest={manifest_path}")
    print(f"[web-publish-branch] targets={len(_stored_target_metadata(manifest_path.parent))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
