from __future__ import annotations

import os
import re
import shutil
from pathlib import Path

_RST_ASSET_DIRECTIVE_RE = re.compile(
    r"^(\s*(?:[-*]\s+)?(?:-\s+)?\.\.\s+(?:\|[^|]+\|\s+)?(?:image|figure)::\s+)(\S+)(\s*)$",
    re.MULTILINE,
)
_HTML_SRC_RE = re.compile(r'(\bsrc=")([^"]+)(")', re.IGNORECASE)
_EMPTY_TOP_LEVEL_LINE_BLOCK_RE = re.compile(r"(?m)^\|[ \t]*(\r?\n|$)")


def is_external_path(value: str) -> bool:
    token = value.strip()
    if not token:
        return True
    lowered = token.lower()
    return lowered.startswith(("http://", "https://", "data:", "file://", "mailto:", "#")) or Path(token).is_absolute()


def resolve_rst_asset_path(
    raw_value: str,
    *,
    source_path: Path,
    docs_dir: Path,
    repo_root: Path,
) -> Path | None:
    token = raw_value.strip()
    if not token or is_external_path(token):
        return None

    raw_path = Path(token)
    probe_paths = [
        source_path.parent / raw_path,
        docs_dir / raw_path,
        repo_root / "docs" / raw_path,
        repo_root / raw_path,
    ]

    for probe in probe_paths:
        if probe.exists() and probe.is_file():
            return probe.resolve()
    return None


def bundle_asset_target_path(
    resolved: Path,
    *,
    bundle_dir: Path,
    docs_dir: Path,
    repo_root: Path,
) -> Path:
    resolved_path = resolved.resolve(strict=False)
    docs_static_dir = (docs_dir / "_static").resolve(strict=False)
    docs_root = docs_dir.resolve(strict=False)
    repo_docs_root = (repo_root / "docs").resolve(strict=False)
    repo_root_resolved = repo_root.resolve(strict=False)

    try:
        rel = resolved_path.relative_to(docs_static_dir)
        return bundle_dir / "_static" / rel
    except ValueError:
        pass

    try:
        rel = resolved_path.relative_to(docs_root)
        return bundle_dir / "_assets" / rel
    except ValueError:
        pass

    try:
        rel = resolved_path.relative_to(repo_docs_root)
        return bundle_dir / "_assets" / rel
    except ValueError:
        pass

    try:
        rel = resolved_path.relative_to(repo_root_resolved)
        return bundle_dir / "_repo_assets" / rel
    except ValueError:
        pass

    return bundle_dir / "_external_assets" / resolved_path.name


def stage_bundle_asset(
    resolved: Path,
    *,
    bundle_dir: Path,
    docs_dir: Path,
    repo_root: Path,
) -> Path:
    target = bundle_asset_target_path(
        resolved,
        bundle_dir=bundle_dir,
        docs_dir=docs_dir,
        repo_root=repo_root,
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(resolved, target)
    return target


def rewrite_single_asset_path(
    raw_value: str,
    *,
    source_path: Path,
    target_path: Path,
    bundle_dir: Path,
    docs_dir: Path,
    repo_root: Path,
) -> str:
    _ = target_path
    token = raw_value.strip()
    if not token or is_external_path(token):
        return raw_value

    resolved = resolve_rst_asset_path(
        raw_value,
        source_path=source_path,
        docs_dir=docs_dir,
        repo_root=repo_root,
    )
    if resolved is None:
        return raw_value

    staged = stage_bundle_asset(
        resolved,
        bundle_dir=bundle_dir,
        docs_dir=docs_dir,
        repo_root=repo_root,
    )
    return Path(os.path.relpath(staged, start=bundle_dir)).as_posix()


def rewrite_rst_asset_paths(
    text: str,
    *,
    source_path: Path,
    target_path: Path,
    bundle_dir: Path,
    docs_dir: Path,
    repo_root: Path,
) -> str:
    def replace_directive(match: re.Match[str]) -> str:
        prefix, raw_value, suffix = match.groups()
        rewritten = rewrite_single_asset_path(
            raw_value,
            source_path=source_path,
            target_path=target_path,
            bundle_dir=bundle_dir,
            docs_dir=docs_dir,
            repo_root=repo_root,
        )
        return f"{prefix}{rewritten}{suffix}"

    def replace_html_src(match: re.Match[str]) -> str:
        prefix, raw_value, suffix = match.groups()
        rewritten = rewrite_single_asset_path(
            raw_value,
            source_path=source_path,
            target_path=target_path,
            bundle_dir=bundle_dir,
            docs_dir=docs_dir,
            repo_root=repo_root,
        )
        return f"{prefix}{rewritten}{suffix}"

    out = _RST_ASSET_DIRECTIVE_RE.sub(replace_directive, text)
    return _HTML_SRC_RE.sub(replace_html_src, out)


def normalize_rst_empty_line_blocks(text: str) -> str:
    return _EMPTY_TOP_LEVEL_LINE_BLOCK_RE.sub(lambda match: match.group(1), text)
