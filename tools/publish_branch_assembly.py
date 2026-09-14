#!/usr/bin/env python3
"""Assemble frozen Web Publish sources below ``docs/publish``.

The queue renderer writes one versioned, verified MyST bundle plus
``latest/web/publish_meta.json``. This module copies only that Web bundle into
the dedicated publish-branch tree and rebuilds the aggregate Sphinx source.
Print Publish artifacts are deliberately outside this contract.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import posixpath
import shutil
import tempfile
from typing import Any

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root


ROOT = bootstrap_repo_root(__file__, parent_count=1)

from tools.readthedocs_source import assemble_rtd_source, write_redirect_page  # noqa: E402
from tools.publish_locale_identity import (  # noqa: E402
    WebPublishTarget,
    assign_legacy_defaults,
    discover_web_publish_targets,
    ensure_unique_targets as _ensure_unique_targets,
    load_web_publish_target,
    migrate_legacy_targets,
    required_text as _required_text,
    safe_aliases,
    stage_web_target,
    stored_target_metadata,
    stored_targets,
)
from tools.safe_copy import assert_source_tree_no_symlinks  # noqa: E402
from tools.publication_withdrawal import reject_withdrawn_version, write_withdrawal_notices  # noqa: E402
from tools.utils.path_utils import PathSegments, Paths  # noqa: E402


SCHEMA_VERSION = "auto-manual-web-publish-branch/v2"
DEFAULT_MAX_FILE_SIZE_MB = 95
_WEB_ONLY_TOP_LEVEL_NAMES = frozenset(
    {
        "publish_manifest.json",
        "sources",
        "web",
    }
)
_FORBIDDEN_PRINT_ARTIFACT_SUFFIXES = frozenset(
    {
        ".7z",
        ".ai",
        ".aux",
        ".cls",
        ".doc",
        ".docx",
        ".eps",
        ".idml",
        ".indb",
        ".indd",
        ".ltx",
        ".pdf",
        ".psd",
        ".rtf",
        ".sty",
        ".tex",
        ".zip",
    }
)


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


def _paths_overlap(first: Path, second: Path) -> bool:
    return first == second or first.is_relative_to(second) or second.is_relative_to(first)


def _validate_publish_boundaries(*, repo_root: Path, releases_root: Path, output_dir: Path) -> None:
    if output_dir.is_symlink():
        raise RuntimeError(f"publish destination must not be a symbolic link: {output_dir}")
    resolved_repo = repo_root.resolve(strict=False)
    resolved_releases = releases_root.resolve(strict=False)
    resolved_output = output_dir.resolve(strict=False)
    if resolved_output.parent == resolved_output:
        raise RuntimeError("publish destination must not be the filesystem root")
    if resolved_output == resolved_repo or resolved_repo.is_relative_to(resolved_output):
        raise RuntimeError(f"publish destination must not contain the repository root: {output_dir}")
    if _paths_overlap(resolved_output, resolved_releases):
        raise RuntimeError(
            f"publish destination must not overlap releases root: {output_dir} and {releases_root}"
        )


def _replace_dir(path: Path) -> None:
    if path.exists():
        if path.is_symlink() or not path.is_dir():
            raise RuntimeError(f"publish destination must be a real directory: {path}")
        shutil.rmtree(path)
    path.mkdir(parents=True)


def _copy_markdown_source(target: WebPublishTarget, destination: Path) -> None:
    source_dir = target.markdown_path.parent
    assert_source_tree_no_symlinks(source_dir, label="Web Publish Markdown source")
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
    # Preserve generated Web sidecars included in sealed Markdown inventories.
    # They are optional for legacy releases; unknown files still fail evidence
    # verification instead of being silently added to the publication surface.
    for filename in (PathSegments.MANUAL_IR_JSON, "manual_bundle.html"):
        source = source_dir / filename
        if source.is_file():
            shutil.copy2(source, destination / filename)
    if target.language_projection_evidence_path is not None:
        evidence_destination = destination / PathSegments.EVIDENCE
        shutil.copytree(
            target.language_projection_evidence_path.parent,
            evidence_destination,
        )
    index_text = (destination / "index.md").read_text(encoding="utf-8")
    if target.markdown_path.stem not in index_text:
        raise RuntimeError(
            f"Web Publish index does not reference {target.markdown_path.stem}: {source_dir / 'index.md'}"
        )


def rebuild_web_source(*, output_dir: Path, title: str) -> None:
    stored_targets = assign_legacy_defaults(output_dir=output_dir)
    if not stored_targets:
        raise RuntimeError(f"publish tree has no stored Web targets: {output_dir}")
    routes: dict[str, Path] = {}
    with tempfile.TemporaryDirectory(prefix="auto-manual-web-publish-") as temp_dir:
        build_root = Path(temp_dir) / PathSegments.BUILD
        build_root.mkdir()
        for metadata_path, payload in stored_targets:
            route = _required_text(payload, "route", source=metadata_path)
            route_key = route.casefold()
            if route_key in routes:
                raise RuntimeError(
                    f"duplicate Web route {route}: {routes[route_key]} and {metadata_path}"
                )
            routes[route_key] = metadata_path
            destination = build_root / route
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(metadata_path.parent, destination)
            (destination / PathSegments.PUBLISH_META_JSON).unlink()
        assembled = build_root / "rtd"
        assemble_rtd_source(build_root=build_root, output_dir=assembled, title=title)
        _write_legacy_compatibility_routes(assembled=assembled, stored_targets=stored_targets)
        web_dir = output_dir / PathSegments.WEB
        _replace_dir(web_dir)
        shutil.copytree(assembled, web_dir, dirs_exist_ok=True)
        write_withdrawal_notices(output_dir)


def _write_legacy_compatibility_routes(
    *,
    assembled: Path,
    stored_targets: list[tuple[Path, dict[str, Any]]],
) -> None:
    root_aliases = {
        path.stem.casefold(): path
        for path in assembled.glob("*.md")
        if path.name != "index.md"
    }
    for metadata_path, payload in stored_targets:
        if payload.get("legacy_default") is not True:
            continue
        route = Path(_required_text(payload, "route", source=metadata_path))
        manual_stem = Path(_required_text(payload, "manual", source=metadata_path)).stem
        canonical_ref = (route / manual_stem).as_posix()
        legacy_route = Path(_required_text(payload, "legacy_route", source=metadata_path))
        label = f"{payload['model']} / {payload['region']} / {payload['lang']}"
        relative_target = posixpath.relpath(canonical_ref, start=legacy_route.as_posix())
        write_redirect_page(
            path=assembled / legacy_route / "index.md",
            label=label,
            target_ref=relative_target,
        )
        for alias in safe_aliases(payload, source=metadata_path):
            write_redirect_page(
                path=assembled / legacy_route / f"{alias}.md",
                label=label,
                target_ref=relative_target,
            )
            existing = root_aliases.get(alias.casefold())
            canonical_alias = alias == manual_stem
            if existing is not None and not canonical_alias:
                raise RuntimeError(
                    f"duplicate RTD short alias {alias}: {existing} and {metadata_path}"
                )
            if existing is None:
                root_alias = assembled / f"{alias}.md"
                write_redirect_page(
                    path=root_alias,
                    label=label,
                    target_ref=canonical_ref,
                )
                root_aliases[alias.casefold()] = root_alias


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
    targets = [payload for _path, payload in stored_targets(output_dir)]
    targets.sort(
        key=lambda item: tuple(
            str(item.get(field) or "").casefold() for field in ("model", "region", "lang")
        )
    )
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


def _enforce_web_only_tree(output_dir: Path) -> None:
    unexpected_top_level = sorted(
        path
        for path in output_dir.iterdir()
        if path.name not in _WEB_ONLY_TOP_LEVEL_NAMES
    )
    if unexpected_top_level:
        details = ", ".join(path.relative_to(output_dir).as_posix() for path in unexpected_top_level)
        raise RuntimeError(
            "docs/publish may contain only Web source, Web assets, and the publish manifest; "
            f"unexpected top-level paths: {details}"
        )

    forbidden = [
        path
        for path in sorted(output_dir.rglob("*"))
        if path.is_file()
        and any(
            path.name.casefold().endswith(suffix)
            for suffix in _FORBIDDEN_PRINT_ARTIFACT_SUFFIXES
        )
    ]
    if forbidden:
        details = ", ".join(path.relative_to(output_dir).as_posix() for path in forbidden)
        raise RuntimeError(
            "docs/publish cannot contain print/source artifacts such as IDML, LaTeX, PDF, "
            f"DOCX, or archives: {details}"
        )


def _promote_candidate(*, candidate: Path, output_dir: Path) -> None:
    backup_root = Path(
        tempfile.mkdtemp(
            prefix=f".{output_dir.name}-backup-",
            dir=output_dir.parent,
        )
    )
    backup = backup_root / output_dir.name
    try:
        if output_dir.exists():
            os.replace(output_dir, backup)
        try:
            os.replace(candidate, output_dir)
        except Exception as promotion_error:
            if backup.exists() and not output_dir.exists():
                try:
                    os.replace(backup, output_dir)
                except Exception as restore_error:
                    raise RuntimeError(
                        "failed to promote Web Publish candidate and restore the previous tree; "
                        f"previous bytes are preserved at {backup}"
                    ) from restore_error
            elif backup.exists():
                raise RuntimeError(
                    "failed to promote Web Publish candidate after the destination reappeared; "
                    f"previous bytes are preserved at {backup}"
                ) from promotion_error
            raise
    except Exception:
        if not backup.exists():
            shutil.rmtree(backup_root, ignore_errors=True)
        raise
    else:
        shutil.rmtree(backup_root)


def assemble_web_publish_branch(
    *,
    repo_root: Path,
    releases_root: Path,
    output_dir: Path,
    title: str,
    max_file_size_mb: int = DEFAULT_MAX_FILE_SIZE_MB,
) -> Path:
    _validate_publish_boundaries(
        repo_root=repo_root,
        releases_root=releases_root,
        output_dir=output_dir,
    )
    output_dir = output_dir.resolve(strict=False)
    targets = discover_web_publish_targets(
        repo_root=repo_root,
        releases_root=releases_root,
    )
    if output_dir.exists() and (output_dir.is_symlink() or not output_dir.is_dir()):
        raise RuntimeError(f"publish destination must be a real directory: {output_dir}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=f".{output_dir.name}-candidate-",
        dir=output_dir.parent,
    ) as temp_dir:
        temp_root = Path(temp_dir)
        candidate = temp_root / output_dir.name
        if output_dir.exists():
            assert_source_tree_no_symlinks(output_dir, label="existing Web Publish tree")
            shutil.copytree(output_dir, candidate)
        else:
            candidate.mkdir()
        migrate_legacy_targets(output_dir=candidate)
        previous_by_identity = {
            tuple(str(payload[field]).casefold() for field in ("model", "region", "lang")): payload
            for _path, payload in stored_targets(candidate)
        }
        for target in targets:
            reject_withdrawn_version(
                candidate, model=target.model, region=target.region,
                lang=target.lang, version=target.version,
            )
            stage_web_target(
                target=target,
                output_dir=candidate,
                copy_markdown_source=_copy_markdown_source,
                previous=previous_by_identity.get(target.identity),
            )
        rebuild_web_source(output_dir=candidate, title=title)
        _enforce_web_only_tree(candidate)
        _write_publish_manifest(candidate)
        _enforce_file_size_limit(candidate, max_file_size_mb=max_file_size_mb)
        _promote_candidate(candidate=candidate, output_dir=output_dir)
    return output_dir / "publish_manifest.json"


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
    print(f"[web-publish-branch] targets={len(stored_target_metadata(manifest_path.parent))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
