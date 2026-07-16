from __future__ import annotations

import os
import re
import shutil
from pathlib import Path, PureWindowsPath
from typing import Callable

from tools.asset_registry import AssetRegistryError
from tools.asset_usage import BundleAssetUsage, parse_asset_uri
from tools.utils.path_utils import PathSegments, latex_renderer_of

_RST_ASSET_DIRECTIVE_RE = re.compile(
    r"^(\s*(?:[-*]\s+)?(?:-\s+)?\.\.\s+(?:\|[^|]+\|\s+)?(?:image|figure)::\s+)(\S+)(\s*)$",
    re.MULTILINE,
)
_HTML_SRC_RE = re.compile(r"(\bsrc\s*=\s*)(['\"])(.*?)\2", re.IGNORECASE)
_LATEX_INCLUDEPDF_RE = re.compile(
    r"(\\includepdf(?:\[[^\]]*\])?\{)([^{}]+)(\})",
    re.IGNORECASE,
)
_EMPTY_TOP_LEVEL_LINE_BLOCK_RE = re.compile(r"(?m)^\|[ \t]*(\r?\n|$)")
_BUNDLE_SOURCE_PREFIX = "bundle-source:"


def is_external_path(value: str) -> bool:
    token = value.strip()
    if not token:
        return True
    lowered = token.lower()
    return lowered.startswith(("http://", "https://", "data:", "mailto:", "#", "//"))


def _is_local_absolute_path(value: str) -> bool:
    return Path(value).is_absolute() or PureWindowsPath(value).is_absolute()


def _deferred_source_value(
    path: Path,
    *,
    bundle_dir: Path,
    docs_dir: Path,
    repo_root: Path,
) -> str:
    canonical = path.resolve(strict=True)
    for label, root in (
        ("bundle", bundle_dir),
        ("docs", docs_dir),
        ("repo", repo_root),
    ):
        trusted_root = root.resolve(strict=True)
        try:
            relative = canonical.relative_to(trusted_root)
        except ValueError:
            continue
        return f"{_BUNDLE_SOURCE_PREFIX}{label}/{relative.as_posix()}"
    raise AssetRegistryError(f"asset source is outside trusted roots: {path}")


def _resolve_deferred_source(
    token: str,
    *,
    bundle_dir: Path | None,
    docs_dir: Path,
    repo_root: Path,
) -> Path | None:
    if not token.startswith(_BUNDLE_SOURCE_PREFIX):
        return None
    scope_and_path = token[len(_BUNDLE_SOURCE_PREFIX) :]
    scope, separator, raw_relative = scope_and_path.partition("/")
    relative = Path(raw_relative)
    if (
        not separator
        or not raw_relative
        or relative.is_absolute()
        or ".." in relative.parts
    ):
        raise AssetRegistryError(f"deferred asset source is unsafe: {token!r}")
    roots: dict[str, Path | None] = {
        "bundle": bundle_dir,
        "docs": docs_dir,
        "repo": repo_root,
    }
    root = roots.get(scope)
    if root is None:
        raise AssetRegistryError(f"deferred asset source has unknown scope: {token!r}")
    trusted_root = root.resolve(strict=True)
    candidate = (trusted_root / relative).resolve(strict=True)
    try:
        candidate.relative_to(trusted_root)
    except ValueError as exc:
        raise AssetRegistryError(f"deferred asset source escapes trusted root: {token!r}") from exc
    if not candidate.is_file():
        raise AssetRegistryError(f"deferred asset source is not a file: {token!r}")
    return candidate


def resolve_rst_asset_path(
    raw_value: str,
    *,
    source_path: Path,
    docs_dir: Path,
    repo_root: Path,
    bundle_dir: Path | None = None,
) -> Path | None:
    token = raw_value.strip()
    if not token or is_external_path(token):
        return None
    if token.lower().startswith("file://") or _is_local_absolute_path(token):
        raise AssetRegistryError(
            f"asset reference must not use an absolute local path: {raw_value!r}"
        )

    deferred = _resolve_deferred_source(
        token,
        bundle_dir=bundle_dir,
        docs_dir=docs_dir,
        repo_root=repo_root,
    )
    if deferred is not None:
        return deferred

    raw_path = Path(token)
    probe_paths = [source_path.parent / raw_path]
    if bundle_dir is not None:
        # Review RSTs already use bundle-root paths such as ``_assets/...``.
        # The finalizer scans those files only after the review overlay, so
        # bundle-root lookup must participate in the same trusted resolution.
        probe_paths.extend(
            (
                bundle_dir / raw_path,
                latex_renderer_of(bundle_dir) / PathSegments.ASSETS / raw_path,
            )
        )
    probe_paths.extend(
        (
            docs_dir / raw_path,
            latex_renderer_of(docs_dir) / PathSegments.ASSETS / raw_path,
            repo_root / "docs" / raw_path,
            latex_renderer_of(repo_root / PathSegments.DOCS)
            / PathSegments.ASSETS
            / raw_path,
            repo_root / raw_path,
        )
    )

    trusted_roots = [docs_dir.resolve(strict=False), repo_root.resolve(strict=False)]
    if bundle_dir is not None:
        trusted_roots.append(bundle_dir.resolve(strict=False))

    for probe in probe_paths:
        if probe.exists() and probe.is_file():
            resolved = probe.resolve(strict=True)
            if any(
                resolved == root or root in resolved.parents
                for root in trusted_roots
            ):
                return resolved
            raise AssetRegistryError(
                f"asset reference escapes trusted roots: {raw_value!r}"
            )
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
    docs_renderers_dir = (docs_dir / PathSegments.RENDERERS).resolve(strict=False)
    docs_root = docs_dir.resolve(strict=False)
    repo_docs_root = (repo_root / "docs").resolve(strict=False)
    repo_root_resolved = repo_root.resolve(strict=False)
    bundle_root = bundle_dir.resolve(strict=False)

    try:
        resolved_path.relative_to(bundle_root)
    except ValueError:
        pass
    else:
        return resolved_path

    try:
        rel = resolved_path.relative_to(docs_static_dir)
        return bundle_dir / "_static" / rel
    except ValueError:
        pass

    try:
        rel = resolved_path.relative_to(docs_renderers_dir)
        return bundle_dir / PathSegments.RENDERERS / rel
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

    raise AssetRegistryError(f"asset source is outside trusted roots: {resolved}")


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
    target_resolved = target.resolve(strict=False)
    bundle_resolved = bundle_dir.resolve(strict=False)
    try:
        target_resolved.relative_to(bundle_resolved)
    except ValueError as exc:
        raise AssetRegistryError(f"staged asset target escapes bundle: {target}") from exc
    if target_resolved == resolved.resolve(strict=True):
        return target_resolved
    if target.exists() or target.is_symlink():
        if target.is_symlink() or not target.is_file():
            raise AssetRegistryError(f"unsafe staged asset target: {target}")
        if target.read_bytes() != resolved.read_bytes():
            raise AssetRegistryError(
                f"staged asset collision: {target.relative_to(bundle_dir)}"
            )
        return target
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
    asset_usage: BundleAssetUsage | None = None,
    model: str | None = None,
    region: str | None = None,
    language: str | None = None,
    defer_staging: bool = False,
    preserve_basename: bool = False,
    required_format: str | None = None,
    render_base: Path | None = None,
) -> str:
    token = raw_value.strip()
    if not token:
        return raw_value

    frozen = None
    if parse_asset_uri(token) is not None:
        if asset_usage is None:
            return raw_value
        frozen = asset_usage.resolve_reference(
            token,
            model=model,
            region=region,
            language=language,
            format_name=required_format,
        )
        if frozen is None:  # pragma: no cover - guarded by parse_asset_uri
            return raw_value
        resolved = frozen.source_path
    else:
        if is_external_path(token):
            return raw_value
        # During the first materialization pass, support trees may already
        # have been copied into the bundle.  Prefer the original docs/repo
        # source so the finalizer can freeze and report its real provenance;
        # only fall back to a genuinely bundle-local source when no original
        # file exists.
        resolved = None
        if defer_staging:
            resolved = resolve_rst_asset_path(
                raw_value,
                source_path=source_path,
                docs_dir=docs_dir,
                repo_root=repo_root,
                bundle_dir=None,
            )
        if resolved is None:
            resolved = resolve_rst_asset_path(
                raw_value,
                source_path=source_path,
                docs_dir=docs_dir,
                repo_root=repo_root,
                bundle_dir=bundle_dir,
            )
    if resolved is None:
        if asset_usage is not None:
            raise AssetRegistryError(
                f"bundle asset reference not found: {token!r} in {source_path}"
            )
        return raw_value

    required_suffix = (
        f".{required_format.casefold().lstrip('.')}" if required_format is not None else None
    )
    if required_suffix is not None and resolved.suffix.casefold() != required_suffix:
        raise AssetRegistryError(
            f"asset reference requires {required_format.upper()} format: {token!r}"
        )

    if defer_staging:
        if asset_usage is not None:
            raise AssetRegistryError("deferred asset staging cannot record final usage")
        return _deferred_source_value(
            resolved,
            bundle_dir=bundle_dir,
            docs_dir=docs_dir,
            repo_root=repo_root,
        )

    if asset_usage is None:
        staged = stage_bundle_asset(
            resolved,
            bundle_dir=bundle_dir,
            docs_dir=docs_dir,
            repo_root=repo_root,
        )
    else:
        staged = asset_usage.stage(
            frozen or resolved,
            bundle_dir=bundle_dir,
            docs_dir=docs_dir,
        )
    rendered_value = (
        staged.name
        if preserve_basename
        else Path(
            os.path.relpath(
                staged,
                start=render_base or target_path.parent,
            )
        ).as_posix()
    )
    if asset_usage is not None:
        if frozen is not None:
            asset_usage.record(
                frozen,
                staged_path=staged,
                reference_path=target_path,
                bundle_dir=bundle_dir,
                model=model,
                region=region,
                original_value=token,
                rendered_value=rendered_value,
            )
        else:
            asset_usage.record_legacy(
                source_path=resolved,
                staged_path=staged,
                reference_path=target_path,
                bundle_dir=bundle_dir,
                docs_dir=docs_dir,
                original_value=token,
                rendered_value=rendered_value,
            )
    return rendered_value


def rewrite_rst_asset_paths(
    text: str,
    *,
    source_path: Path,
    target_path: Path,
    bundle_dir: Path,
    docs_dir: Path,
    repo_root: Path,
    asset_usage: BundleAssetUsage | None = None,
    model: str | None = None,
    region: str | None = None,
    language: str | None = None,
    defer_staging: bool = False,
) -> str:
    def transform(
        raw_value: str,
        *,
        preserve_basename: bool = False,
        required_format: str | None = None,
        render_base: Path | None = None,
    ) -> str:
        return rewrite_single_asset_path(
            raw_value,
            source_path=source_path,
            target_path=target_path,
            bundle_dir=bundle_dir,
            docs_dir=docs_dir,
            repo_root=repo_root,
            asset_usage=asset_usage,
            model=model,
            region=region,
            language=language,
            defer_staging=defer_staging,
            preserve_basename=preserve_basename,
            required_format=required_format,
            render_base=render_base,
        )

    return map_rst_asset_paths(
        text,
        transform=lambda raw_value: transform(raw_value, render_base=bundle_dir),
        html_transform=lambda raw_value: transform(raw_value, render_base=bundle_dir),
        latex_transform=lambda raw_value: transform(
            raw_value,
            preserve_basename=not defer_staging,
            required_format="pdf",
        ),
    )


def map_rst_asset_paths(
    text: str,
    *,
    transform: Callable[[str], str],
    html_transform: Callable[[str], str] | None = None,
    latex_transform: Callable[[str], str] | None = None,
) -> str:
    """Transform RST directive and raw-HTML image path values only."""

    def replace_directive(match: re.Match[str]) -> str:
        prefix, raw_value, suffix = match.groups()
        return f"{prefix}{transform(raw_value)}{suffix}"

    def replace_html_src(match: re.Match[str]) -> str:
        prefix, quote, raw_value = match.groups()
        selected_transform = html_transform or transform
        return f"{prefix}{quote}{selected_transform(raw_value)}{quote}"

    def replace_latex_include(match: re.Match[str]) -> str:
        prefix, raw_value, suffix = match.groups()
        selected_transform = latex_transform or transform
        return f"{prefix}{selected_transform(raw_value)}{suffix}"

    out = _RST_ASSET_DIRECTIVE_RE.sub(replace_directive, text)
    out = _HTML_SRC_RE.sub(replace_html_src, out)
    return _LATEX_INCLUDEPDF_RE.sub(replace_latex_include, out)


def raw_html_asset_values(text: str) -> tuple[str, ...]:
    """Return every quoted raw-HTML ``src`` value in one RST document."""

    return tuple(match.group(3) for match in _HTML_SRC_RE.finditer(text))


def normalize_rst_empty_line_blocks(text: str) -> str:
    return _EMPTY_TOP_LEVEL_LINE_BLOCK_RE.sub(lambda match: match.group(1), text)
