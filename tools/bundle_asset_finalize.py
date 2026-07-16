"""Finalize one rendered bundle against a frozen asset-registry snapshot."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from collections import defaultdict
from dataclasses import replace
from pathlib import Path
from typing import Any, Iterable

from tools.asset_registry import AssetRegistryError
from tools.asset_rewrites import restore_registry_asset_uris
from tools.asset_usage import (
    ASSET_REGISTRY_SNAPSHOT_FILENAME,
    ASSET_USAGE_MANIFEST_FILENAME,
    AssetTarget,
    BundleAssetUsage,
)
from tools.gen_index_bundle_assets import rewrite_rst_asset_paths
from tools.gen_index_bundle_paths import read_included_page_paths

_INCLUDE_RE = re.compile(r"^\s*\.\.\s+include::\s+(\S+)\s*$", re.MULTILINE)
_LATEX_LANGUAGE_RE = re.compile(r"\\HBApplyLang\{([^{}]+)\}")
_LANGUAGE_SUFFIX_RE = re.compile(r"(?:^|[_-])([a-z]{2,3}(?:-[a-z]{2})?)$", re.IGNORECASE)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _within(path: Path, root: Path, *, label: str) -> Path:
    canonical = path.resolve(strict=True)
    try:
        canonical.relative_to(root.resolve(strict=True))
    except ValueError as exc:
        raise AssetRegistryError(f"{label} escapes the finalized bundle") from exc
    return canonical


def _manifest_target_within_bundle(path: Path | None, bundle_dir: Path) -> Path:
    lexical_root = Path(os.path.abspath(bundle_dir))
    bundle_root = lexical_root.resolve(strict=True)
    candidate = path or (lexical_root / "bundle_manifest.json")
    if not candidate.is_absolute():
        candidate = lexical_root / candidate
    candidate = Path(os.path.abspath(candidate))
    suffix = Path()
    probe = candidate
    symlink_ancestor: Path | None = None
    while True:
        if probe.is_symlink() and symlink_ancestor is None:
            symlink_ancestor = probe
        if probe.exists():
            try:
                if probe.samefile(bundle_root):
                    if symlink_ancestor is not None:
                        raise AssetRegistryError(
                            "bundle manifest must not be a symbolic link"
                        )
                    break
            except OSError:
                pass
        if probe.parent == probe:
            raise AssetRegistryError("bundle manifest escapes the finalized bundle")
        suffix = Path(probe.name) / suffix
        probe = probe.parent

    canonical = (bundle_root / suffix).resolve(strict=False)
    try:
        canonical.relative_to(bundle_root)
    except ValueError as exc:
        raise AssetRegistryError("bundle manifest escapes the finalized bundle") from exc
    if canonical.exists() and not canonical.is_file():
        raise AssetRegistryError("bundle manifest is not a regular file")
    return canonical


def _configured_languages(cfg: dict[str, Any]) -> tuple[str, ...]:
    build_raw = cfg.get("build", {})
    build = build_raw if isinstance(build_raw, dict) else {}
    languages_raw = build.get("languages", ())
    if not isinstance(languages_raw, (list, tuple)):
        return ()
    return tuple(str(value).strip() for value in languages_raw if str(value).strip())


def _language_for_rst(
    path: Path,
    text: str,
    *,
    bundle_language: str | None,
    configured_languages: tuple[str, ...],
    inherited_language: str | None = None,
) -> str | None:
    if (bundle_language or "").strip():
        return bundle_language.strip()
    marker = _LATEX_LANGUAGE_RE.search(text)
    if marker:
        return marker.group(1).strip()
    suffix = _LANGUAGE_SUFFIX_RE.search(path.stem)
    if suffix:
        candidate = suffix.group(1)
        for configured in configured_languages:
            if candidate.casefold() == configured.casefold():
                return configured
    if (inherited_language or "").strip():
        return inherited_language.strip()
    if len(configured_languages) == 1:
        return configured_languages[0]
    return None


def _rst_closure(
    index_path: Path,
    *,
    bundle_dir: Path,
    bundle_language: str | None,
    configured_languages: tuple[str, ...],
) -> tuple[tuple[Path, str | None], ...]:
    pending: list[tuple[Path, str | None]] = [(index_path, None)]
    seen_states: set[tuple[Path, str | None]] = set()
    contexts: dict[Path, set[str | None]] = defaultdict(set)
    ordered: list[Path] = []
    while pending:
        raw_current, inherited_language = pending.pop(0)
        current = _within(raw_current, bundle_dir, label="RST include")
        if not current.is_file():
            raise AssetRegistryError(f"RST include is not a file: {current}")
        text = current.read_text(encoding="utf-8")
        language = _language_for_rst(
            current,
            text,
            bundle_language=bundle_language,
            configured_languages=configured_languages,
            inherited_language=inherited_language,
        )
        normalized_language = language.casefold() if language is not None else None
        state = (current, normalized_language)
        if state in seen_states:
            continue
        seen_states.add(state)
        if current not in contexts:
            ordered.append(current)
        contexts[current].add(language)
        for raw_value in _INCLUDE_RE.findall(text):
            candidate = current.parent / raw_value
            if not candidate.exists():
                raise AssetRegistryError(
                    f"RST include target not found: {raw_value!r} in {current}"
                )
            pending.append((candidate, language))

    resolved: list[tuple[Path, str | None]] = []
    for path in ordered:
        languages = {
            language.casefold(): language
            for language in contexts[path]
            if language is not None
        }
        if len(languages) > 1:
            values = ", ".join(sorted(languages.values(), key=str.casefold))
            raise AssetRegistryError(
                f"RST include has conflicting language contexts ({values}): "
                f"{path.relative_to(bundle_dir).as_posix()}"
            )
        resolved.append((path, next(iter(languages.values()), None)))
    return tuple(resolved)


def _bundle_relative_records(paths: Iterable[Path], *, bundle_dir: Path) -> list[dict[str, str]]:
    root = bundle_dir.resolve(strict=True)
    records: list[dict[str, str]] = []
    for path in paths:
        canonical = _within(path, root, label="bundle manifest file")
        records.append(
            {
                "path": canonical.relative_to(root).as_posix(),
                "sha256": _sha256(canonical),
            }
        )
    return records


def _bundle_tree_files(bundle_dir: Path, *relative_roots: str) -> tuple[Path, ...]:
    files: list[Path] = []
    for relative_root in relative_roots:
        root = bundle_dir / relative_root
        if root.is_symlink():
            raise AssetRegistryError(
                f"bundle support root must not be a symbolic link: {relative_root}"
            )
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if path.is_symlink():
                raise AssetRegistryError(
                    "bundle support tree must not contain symbolic links: "
                    f"{path.relative_to(bundle_dir).as_posix()}"
                )
            if path.is_file():
                files.append(path)
    return tuple(files)


def _generated_rst_entries(
    bundle_dir: Path,
    *,
    bundle_language: str | None,
    configured_languages: tuple[str, ...],
) -> tuple[tuple[Path, str | None], ...]:
    generated_root = bundle_dir / "generated"
    if generated_root.is_symlink():
        raise AssetRegistryError("bundle generated root must not be a symbolic link")
    if not generated_root.is_dir():
        return ()

    entries: list[tuple[Path, str | None]] = []
    for path in sorted(generated_root.rglob("*")):
        if path.is_symlink():
            raise AssetRegistryError(
                "bundle generated tree must not contain symbolic links: "
                f"{path.relative_to(bundle_dir).as_posix()}"
            )
        if not path.is_file() or path.suffix.casefold() != ".rst":
            continue
        canonical = _within(path, bundle_dir, label="generated RST")
        text = canonical.read_text(encoding="utf-8")
        entries.append(
            (
                canonical,
                _language_for_rst(
                    canonical,
                    text,
                    bundle_language=bundle_language,
                    configured_languages=configured_languages,
                ),
            )
        )
    return tuple(entries)


def _display_path(path: Path, *, repo_root: Path, bundle_dir: Path) -> str:
    canonical = path.resolve(strict=True)
    try:
        return canonical.relative_to(repo_root.resolve(strict=True)).as_posix()
    except ValueError:
        return f"bundle://{canonical.relative_to(bundle_dir.resolve(strict=True)).as_posix()}"


def _atomic_json_write(path: Path, payload: dict[str, Any]) -> None:
    data = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def finalize_materialized_bundle(
    bundle: Any,
    *,
    cfg: dict[str, Any],
    docs_dir: Path,
    repo_root: Path,
    asset_override_root: Path | None = None,
) -> Any:
    """Rewrite final RST references and freeze the exact post-overlay bundle state."""

    if not (bundle.model or "").strip() or not (bundle.region or "").strip():
        raise AssetRegistryError("bundle asset finalization requires model and region")
    bundle_dir = bundle.bundle_dir.resolve(strict=True)
    index_path = _within(bundle.index_path, bundle_dir, label="bundle index")
    manifest_path = _manifest_target_within_bundle(
        bundle.manifest_path,
        bundle.bundle_dir,
    )
    restore_registry_asset_uris(
        source_bundle_dir=bundle_dir,
        target_bundle_dir=bundle_dir,
        strict=False,
    )
    configured_languages = _configured_languages(cfg)
    usage = BundleAssetUsage(
        target=AssetTarget(
            model=bundle.model,
            region=bundle.region,
            language=bundle.lang,
        ),
        repo_root=repo_root,
        override_root=asset_override_root,
    )

    rst_entries = _rst_closure(
        index_path,
        bundle_dir=bundle_dir,
        bundle_language=bundle.lang,
        configured_languages=configured_languages,
    )
    rst_paths = tuple(path for path, _language in rst_entries)
    generated_entries = _generated_rst_entries(
        bundle_dir,
        bundle_language=bundle.lang,
        configured_languages=configured_languages,
    )
    rewrite_entries = (*rst_entries, *(entry for entry in generated_entries if entry[0] not in rst_paths))
    for rst_path, rst_language in rewrite_entries:
        text = rst_path.read_text(encoding="utf-8")
        rewritten = rewrite_rst_asset_paths(
            text,
            source_path=rst_path,
            target_path=rst_path,
            bundle_dir=bundle_dir,
            docs_dir=docs_dir,
            repo_root=repo_root,
            asset_usage=usage,
            model=bundle.model,
            region=bundle.region,
            language=rst_language,
        )
        if rewritten != text:
            rst_path.write_text(rewritten, encoding="utf-8")

    page_paths = tuple(
        _within(path, bundle_dir, label="bundle page")
        for path in read_included_page_paths(index_path)
    )
    generated_paths = tuple(path for path, _language in generated_entries)
    config_paths = tuple(
        path
        for path in dict.fromkeys((bundle.conf_path, bundle.conf_base_path))
        if path.is_file()
    )
    support_paths = _bundle_tree_files(
        bundle_dir,
        "_assets",
        "_repo_assets",
        "_static",
        "renderers",
    )

    usage_manifest_path = bundle_dir / ASSET_USAGE_MANIFEST_FILENAME
    registry_snapshot_path = bundle_dir / ASSET_REGISTRY_SNAPSHOT_FILENAME
    usage.write(
        usage_manifest_path=usage_manifest_path,
        registry_snapshot_path=registry_snapshot_path,
        bundle_dir=bundle_dir,
    )

    if manifest_path.is_file():
        existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest = existing if isinstance(existing, dict) else {}
    else:
        manifest = {}
    page_records = _bundle_relative_records(page_paths, bundle_dir=bundle_dir)
    generated_records = _bundle_relative_records(generated_paths, bundle_dir=bundle_dir)
    rst_records = _bundle_relative_records(rst_paths, bundle_dir=bundle_dir)
    config_records = _bundle_relative_records(config_paths, bundle_dir=bundle_dir)
    support_records = _bundle_relative_records(support_paths, bundle_dir=bundle_dir)
    asset_usage_record = {
        "path": usage_manifest_path.relative_to(bundle_dir).as_posix(),
        "sha256": _sha256(usage_manifest_path),
    }
    registry_snapshot_record = {
        "path": registry_snapshot_path.relative_to(bundle_dir).as_posix(),
        "sha256": _sha256(registry_snapshot_path),
    }
    fingerprint_payload = {
        "asset_registry_snapshot": registry_snapshot_record,
        "asset_usage_manifest": asset_usage_record,
        "config_files": config_records,
        "generated_files": generated_records,
        "lang": bundle.lang,
        "model": bundle.model,
        "page_files": page_records,
        "region": bundle.region,
        "rst_files": rst_records,
        "support_files": support_records,
    }
    bundle_sha256 = hashlib.sha256(
        json.dumps(
            fingerprint_payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    manifest.update(
        {
            "asset_registry_snapshot": registry_snapshot_record,
            "asset_usage_manifest": asset_usage_record,
            "bundle_sha256": bundle_sha256,
            "config_file_records": config_records,
            "finalized": True,
            "generated_file_records": generated_records,
            "generated_files": [
                _display_path(path, repo_root=repo_root, bundle_dir=bundle_dir)
                for path in generated_paths
            ],
            "lang": bundle.lang,
            "model": bundle.model,
            "page_file_records": page_records,
            "page_files": [
                _display_path(path, repo_root=repo_root, bundle_dir=bundle_dir)
                for path in page_paths
            ],
            "region": bundle.region,
            "rst_file_records": rst_records,
            "schema_version": 2,
            "support_file_records": support_records,
        }
    )
    _atomic_json_write(manifest_path, manifest)

    return replace(
        bundle,
        page_paths=page_paths,
        manifest_path=manifest_path,
        asset_usage_manifest_path=usage_manifest_path,
        asset_registry_snapshot_path=registry_snapshot_path,
    )


__all__ = ("finalize_materialized_bundle",)
