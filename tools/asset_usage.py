"""Resolve, stage, and account for every image consumed by a bundle.

The registry and each resolved export are frozen as bytes before a bundle is
assembled.  This keeps the manifest, registry snapshot, and staged files on
one immutable view of the inputs instead of trusting paths that can change
between resolution and copying.
"""

from __future__ import annotations

import hashlib
import json
import os
import posixpath
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, overload

from tools.asset_registry import (
    REGISTRY_RELATIVE_PATH,
    AssetRecord,
    AssetRegistryError,
    AssetResolution,
    NoMatchingAssetExportError,
    load_registry_bytes,
    resolve_asset,
)
from tools.safe_copy import prepare_file_destination_no_symlinks
from tools.utils.path_utils import PathSegments

ASSET_URI_PREFIX = "asset:"
ASSET_USAGE_MANIFEST_FILENAME = "asset_usage_manifest.json"
ASSET_REGISTRY_SNAPSHOT_FILENAME = "asset_registry_snapshot.csv"
SAFE_BUNDLE_FORMATS = ("png", "jpg", "jpeg", "svg", "pdf")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _rendered_relative(*, staged_relative: str, reference_relative: str) -> str:
    reference_parent = posixpath.dirname(reference_relative) or "."
    return posixpath.relpath(staged_relative, start=reference_parent)


def parse_asset_uri(value: str) -> str | None:
    """Return the key in ``asset:<key>`` or ``None`` for a legacy path."""

    token = value.strip()
    if not token.lower().startswith(ASSET_URI_PREFIX):
        return None
    asset_key = token[len(ASSET_URI_PREFIX) :].strip()
    if not asset_key:
        raise AssetRegistryError("asset URI is missing an asset key")
    key_path = Path(asset_key)
    if key_path.is_absolute() or ".." in key_path.parts:
        raise AssetRegistryError(f"asset URI has an unsafe key: {asset_key!r}")
    return asset_key


@dataclass(frozen=True)
class AssetTarget:
    """The exact product target whose bundle is being assembled."""

    model: str
    region: str
    language: str | None = None

    def __post_init__(self) -> None:
        model = self.model.strip()
        region = self.region.strip()
        language = self.language.strip() if self.language is not None else None
        if not model:
            raise AssetRegistryError("asset target model must be non-empty")
        if not region:
            raise AssetRegistryError("asset target region must be non-empty")
        if self.language is not None and not language:
            raise AssetRegistryError("asset target language must be non-empty when provided")
        object.__setattr__(self, "model", model)
        object.__setattr__(self, "region", region)
        object.__setattr__(self, "language", language)


@dataclass(frozen=True)
class FrozenAssetReference:
    """A registry resolution coupled to the exact bytes that were verified."""

    source_path: Path
    resolution: AssetResolution
    content: bytes = field(repr=False)
    source_relative: str

    @property
    def sha256(self) -> str:
        return _sha256(self.content)

    # Preserve the two-item tuple behaviour used by the original PR draft.
    def __iter__(self) -> Iterator[Path | AssetResolution]:
        yield self.source_path
        yield self.resolution

    @overload
    def __getitem__(self, index: int) -> Path | AssetResolution: ...

    @overload
    def __getitem__(self, index: slice) -> tuple[Path | AssetResolution, ...]: ...

    def __getitem__(
        self, index: int | slice
    ) -> Path | AssetResolution | tuple[Path | AssetResolution, ...]:
        return (self.source_path, self.resolution)[index]

    def __len__(self) -> int:
        return 2


@dataclass(frozen=True)
class _FrozenLegacySource:
    source_path: Path
    content: bytes = field(repr=False)
    source_relative: str

    @property
    def sha256(self) -> str:
        return _sha256(self.content)


@dataclass(frozen=True)
class _FrozenOverride:
    source_path: Path
    content: bytes = field(repr=False)
    source_relative: str

    @property
    def sha256(self) -> str:
        return _sha256(self.content)


@dataclass
class _UsageEntry:
    row: dict[str, object]
    staged_path: Path
    expected_sha256: str
    references: set[str] = field(default_factory=set)


def _resolved_path(path: Path, *, strict: bool, label: str) -> Path:
    try:
        return path.resolve(strict=strict)
    except (FileNotFoundError, OSError) as exc:
        raise AssetRegistryError(f"{label} is not a usable path") from exc


def _relative_to(path: Path, root: Path, *, label: str) -> Path:
    try:
        return path.relative_to(root)
    except ValueError as exc:
        raise AssetRegistryError(f"{label} escapes its trusted root") from exc


def _canonical_file_within(path: Path, root: Path, *, label: str) -> Path:
    canonical = _resolved_path(path, strict=True, label=label)
    _relative_to(canonical, root, label=label)
    if not canonical.is_file():
        raise AssetRegistryError(f"{label} is not a regular file")
    return canonical


def _canonical_target_within(path: Path, root: Path, *, label: str) -> Path:
    canonical = _resolved_path(path, strict=False, label=label)
    _relative_to(canonical, root, label=label)
    return canonical


class BundleAssetUsage:
    """Target-bound resolver, safe stager, and deterministic usage recorder."""

    def __init__(
        self,
        *,
        target: AssetTarget,
        repo_root: Path,
        registry_path: Path | None = None,
        override_root: Path | None = None,
    ) -> None:
        self.target = target
        self.repo_root = _resolved_path(repo_root, strict=True, label="repository root")
        if not self.repo_root.is_dir():
            raise AssetRegistryError("repository root is not a directory")

        selected_registry = registry_path or (self.repo_root / REGISTRY_RELATIVE_PATH)
        if not selected_registry.is_absolute():
            selected_registry = self.repo_root / selected_registry
        self.registry_path = _canonical_file_within(
            selected_registry,
            self.repo_root,
            label="asset registry",
        )
        self._registry_relative = self.registry_path.relative_to(self.repo_root).as_posix()
        # Deliberately read exactly once.  All parsing and snapshot output use
        # this frozen copy, even if the working-tree file changes later.
        self._registry_bytes = self.registry_path.read_bytes()
        self._registry_sha256 = _sha256(self._registry_bytes)
        self._records: tuple[AssetRecord, ...] = load_registry_bytes(
            self._registry_bytes,
            source=self._registry_relative,
        )
        self._resolved: dict[
            tuple[str, str | None, str | None], FrozenAssetReference
        ] = {}
        self._resolved_paths: dict[Path, FrozenAssetReference] = {}
        self._legacy_sources: dict[Path, _FrozenLegacySource] = {}
        self.override_root: Path | None = None
        if override_root is not None:
            resolved_override_root = _resolved_path(
                override_root,
                strict=True,
                label="asset override root",
            )
            if not resolved_override_root.is_dir():
                raise AssetRegistryError("asset override root is not a directory")
            self.override_root = resolved_override_root
        self._staged_overrides: dict[Path, _FrozenOverride] = {}
        self._entries: dict[tuple[str, ...], _UsageEntry] = {}
        self._rewrite_events: list[dict[str, object]] = []

    def _check_compat_scope(
        self,
        *,
        model: str | None,
        region: str | None,
        language: str | None,
    ) -> None:
        supplied = (("model", model, self.target.model), ("region", region, self.target.region))
        for label, value, expected in supplied:
            if value is not None and value.strip().casefold() != expected.casefold():
                raise AssetRegistryError(
                    f"asset {label} {value!r} conflicts with bound target {expected!r}"
                )
        if (
            language is not None
            and self.target.language is not None
            and language.strip().casefold() != self.target.language.casefold()
        ):
            raise AssetRegistryError(
                f"asset language {language!r} conflicts with bound target "
                f"{self.target.language!r}"
            )

    def resolve_reference(
        self,
        value: str,
        *,
        model: str | None = None,
        region: str | None = None,
        language: str | None = None,
        format_name: str | None = None,
    ) -> FrozenAssetReference | None:
        """Resolve and freeze an ``asset:`` reference using safe formats only."""

        asset_key = parse_asset_uri(value)
        if asset_key is None:
            return None
        self._check_compat_scope(model=model, region=region, language=language)
        effective_language = (
            language.strip() if language is not None else self.target.language
        )
        requested_format = (
            format_name.strip().lower().lstrip(".") if format_name is not None else None
        )
        if requested_format is not None and requested_format not in SAFE_BUNDLE_FORMATS:
            raise AssetRegistryError(
                f"asset {asset_key!r} requested unsafe format {format_name!r}"
            )
        cache_key = (
            asset_key,
            effective_language.casefold() if effective_language else None,
            requested_format,
        )
        cached = self._resolved.get(cache_key)
        if cached is not None:
            return cached

        resolution: AssetResolution | None = None
        candidate_formats = (
            (requested_format,) if requested_format is not None else SAFE_BUNDLE_FORMATS
        )
        for candidate_format in candidate_formats:
            try:
                resolution = resolve_asset(
                    self._records,
                    repo_root=self.repo_root,
                    asset_key=asset_key,
                    format_name=candidate_format,
                    language=effective_language,
                    model=self.target.model,
                    region=self.target.region,
                )
            except NoMatchingAssetExportError:
                continue
            break
        if resolution is None:
            formats = ", ".join(candidate_formats)
            raise NoMatchingAssetExportError(
                f"asset {asset_key!r} has no bundle-safe export ({formats})"
            )
        if resolution.format.casefold() not in SAFE_BUNDLE_FORMATS:
            raise AssetRegistryError(
                f"asset {asset_key!r} resolved to unsafe format {resolution.format!r}"
            )

        resolution_path = Path(resolution.path)
        if resolution_path.is_absolute() or ".." in resolution_path.parts:
            raise AssetRegistryError(f"asset {asset_key!r} resolved outside the repository")
        source_path = _canonical_file_within(
            self.repo_root / resolution_path,
            self.repo_root,
            label=f"asset {asset_key!r} export",
        )
        content = source_path.read_bytes()
        content_hash = _sha256(content)
        if content_hash != resolution.content_hash.lower():
            raise AssetRegistryError(
                f"asset {asset_key!r} changed while its export was being resolved"
            )
        declared_hash = resolution.declared_hash.lower()
        if not content_hash.startswith(declared_hash):
            raise AssetRegistryError(f"asset {asset_key!r} does not match its declared hash")

        frozen = FrozenAssetReference(
            source_path=source_path,
            resolution=resolution,
            content=content,
            source_relative=source_path.relative_to(self.repo_root).as_posix(),
        )
        self._resolved[cache_key] = frozen
        self._resolved_paths[source_path] = frozen
        return frozen

    def _trusted_roots(self, *, docs_dir: Path, bundle_dir: Path) -> tuple[Path, Path]:
        docs_root = _resolved_path(docs_dir, strict=True, label="docs root")
        if not docs_root.is_dir():
            raise AssetRegistryError("docs root is not a directory")
        bundle_root = _resolved_path(bundle_dir, strict=False, label="bundle root")
        return docs_root, bundle_root

    def _freeze_legacy(
        self,
        source_path: Path,
        *,
        docs_root: Path,
        bundle_root: Path,
    ) -> _FrozenLegacySource:
        source = _resolved_path(source_path, strict=True, label="legacy asset")
        cached = self._legacy_sources.get(source)
        if cached is not None:
            return cached

        source_relative: str
        try:
            source_relative = source.relative_to(self.repo_root).as_posix()
        except ValueError:
            try:
                docs_relative = source.relative_to(docs_root).as_posix()
            except ValueError:
                try:
                    bundle_relative = source.relative_to(bundle_root).as_posix()
                except ValueError as exc:
                    raise AssetRegistryError(
                        "legacy asset is outside the repository, docs, and bundle roots"
                    ) from exc
                source_relative = f"bundle/{bundle_relative}"
            else:
                source_relative = f"docs-root/{docs_relative}"
        if not source.is_file():
            raise AssetRegistryError("legacy asset is not a regular file")
        frozen = _FrozenLegacySource(
            source_path=source,
            content=source.read_bytes(),
            source_relative=source_relative,
        )
        self._legacy_sources[source] = frozen
        return frozen

    def _target_for_source(
        self,
        source: Path,
        *,
        docs_root: Path,
        bundle_root: Path,
    ) -> Path:
        try:
            source_relative = source.relative_to(bundle_root)
        except ValueError:
            pass
        else:
            return _canonical_target_within(
                bundle_root / source_relative,
                bundle_root,
                label="staged asset target",
            )
        roots_and_prefixes = (
            (docs_root / "_static", Path("_static")),
            (
                docs_root / PathSegments.RENDERERS,
                Path(PathSegments.RENDERERS),
            ),
            (docs_root, Path("_assets")),
            (self.repo_root / PathSegments.DOCS, Path("_assets")),
            (self.repo_root, Path("_repo_assets")),
        )
        for root, prefix in roots_and_prefixes:
            canonical_root = _resolved_path(root, strict=False, label="asset source root")
            try:
                relative = source.relative_to(canonical_root)
            except ValueError:
                continue
            return _canonical_target_within(
                bundle_root / prefix / relative,
                bundle_root,
                label="staged asset target",
            )
        raise AssetRegistryError("asset source is outside the repository and docs roots")

    def _explicit_override_for_target(
        self,
        target: Path,
        *,
        bundle_root: Path,
    ) -> _FrozenOverride | None:
        if self.override_root is None:
            return None
        relative = _relative_to(target, bundle_root, label="staged asset target")
        candidate = self.override_root / relative
        if not candidate.exists() and not candidate.is_symlink():
            return None
        source = _canonical_file_within(
            candidate,
            self.override_root,
            label="review asset override",
        )
        content = source.read_bytes()
        if target.read_bytes() != content:
            raise AssetRegistryError(
                f"review asset override was not staged at {relative.as_posix()}"
            )
        try:
            source_relative = source.relative_to(self.repo_root).as_posix()
        except ValueError:
            source_relative = f"override/{source.relative_to(self.override_root).as_posix()}"
        return _FrozenOverride(
            source_path=source,
            content=content,
            source_relative=source_relative,
        )

    def stage(
        self,
        asset: FrozenAssetReference | Path,
        *,
        bundle_dir: Path,
        docs_dir: Path,
        target_path: Path | None = None,
    ) -> Path:
        """Stage frozen bytes and reject path escapes or content collisions."""

        docs_root, bundle_root = self._trusted_roots(docs_dir=docs_dir, bundle_dir=bundle_dir)
        if isinstance(asset, FrozenAssetReference):
            source_path = asset.source_path
            content = asset.content
        else:
            canonical_source = _resolved_path(asset, strict=True, label="asset source")
            registry_asset = self._resolved_paths.get(canonical_source)
            if registry_asset is not None:
                source_path = registry_asset.source_path
                content = registry_asset.content
            else:
                legacy = self._freeze_legacy(
                    canonical_source,
                    docs_root=docs_root,
                    bundle_root=bundle_root,
                )
                source_path = legacy.source_path
                content = legacy.content

        format_name = source_path.suffix.lower().lstrip(".")
        if format_name not in SAFE_BUNDLE_FORMATS:
            raise AssetRegistryError(
                f"asset source uses unsafe bundle format {format_name or '<none>'!r}"
            )

        selected_target = target_path
        if selected_target is not None and not selected_target.is_absolute():
            selected_target = bundle_root / selected_target
        target = (
            _canonical_target_within(
                selected_target,
                bundle_root,
                label="staged asset target",
            )
            if selected_target is not None
            else self._target_for_source(
                source_path,
                docs_root=docs_root,
                bundle_root=bundle_root,
            )
        )
        if target.exists() or target.is_symlink():
            if target.is_symlink():
                raise AssetRegistryError("staged asset target must not be a symbolic link")
            if not target.is_file():
                raise AssetRegistryError("staged asset target is not a regular file")
            if isinstance(asset, FrozenAssetReference):
                explicit_override = self._explicit_override_for_target(
                    target,
                    bundle_root=bundle_root,
                )
                if explicit_override is not None:
                    self._staged_overrides[target] = explicit_override
                    return target
            if target.read_bytes() != content:
                raise AssetRegistryError(
                    f"staged asset collision at {target.relative_to(bundle_root).as_posix()}"
                )
            return target

        target.parent.mkdir(parents=True, exist_ok=True)
        # Creating parents may traverse a pre-existing symlink; resolve again
        # immediately before the exclusive create.
        target = _canonical_target_within(
            target,
            bundle_root,
            label="staged asset target",
        )
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            descriptor = os.open(target, flags, 0o644)
        except FileExistsError:
            if target.is_file() and not target.is_symlink() and target.read_bytes() == content:
                return target
            raise AssetRegistryError(
                f"staged asset collision at {target.relative_to(bundle_root).as_posix()}"
            ) from None
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(content)
        except BaseException:
            target.unlink(missing_ok=True)
            raise
        return target

    def _bundle_relative(self, path: Path, bundle_root: Path, *, label: str) -> str:
        canonical = _canonical_file_within(path, bundle_root, label=label)
        return canonical.relative_to(bundle_root).as_posix()

    def _reference_relative(self, path: Path, bundle_root: Path) -> str:
        canonical = _resolved_path(path, strict=False, label="asset reference")
        return _relative_to(canonical, bundle_root, label="asset reference").as_posix()

    def record(
        self,
        asset: FrozenAssetReference | AssetResolution,
        *,
        staged_path: Path,
        reference_path: Path,
        bundle_dir: Path,
        model: str | None = None,
        region: str | None = None,
        original_value: str | None = None,
        rendered_value: str | None = None,
        consumer: str = "bundle",
        reference_kind: str | None = None,
        emit_rewrite: bool = True,
    ) -> None:
        """Record one registry-backed consumer, retaining draft-call compatibility.

        Ordinary RST references use the default ``bundle`` / ``registry-uri``
        values and emit reversible rewrite provenance.  Native renderer
        contracts can name their real consumer/reference kind and suppress a
        rewrite event because no RST token was rewritten.
        """

        self._check_compat_scope(model=model, region=region, language=None)
        consumer = consumer.strip()
        if not consumer:
            raise AssetRegistryError("asset consumer must be non-empty")
        if reference_kind is not None:
            reference_kind = reference_kind.strip()
            if not reference_kind:
                raise AssetRegistryError("asset reference kind must be non-empty")
        frozen = asset if isinstance(asset, FrozenAssetReference) else next(
            (
                resolved
                for (asset_key, _language, _format), resolved in self._resolved.items()
                if asset_key == asset.asset_key and resolved.resolution == asset
            ),
            None,
        )
        if frozen is None:
            raise AssetRegistryError("registry asset must be resolved and frozen before recording")
        bundle_root = _resolved_path(bundle_dir, strict=False, label="bundle root")
        staged_relative = self._bundle_relative(
            staged_path,
            bundle_root,
            label="staged registry asset",
        )
        reference_relative = self._reference_relative(reference_path, bundle_root)
        canonical_staged = _canonical_file_within(
            staged_path,
            bundle_root,
            label="staged registry asset",
        )
        explicit_override = self._staged_overrides.get(canonical_staged)
        consumed_content = explicit_override.content if explicit_override is not None else frozen.content
        if canonical_staged.read_bytes() != consumed_content:
            raise AssetRegistryError(f"staged registry asset was modified: {staged_relative}")

        resolution = frozen.resolution
        if reference_kind is None:
            reference_kind = (
                "review-override" if explicit_override is not None else "registry-uri"
            )
        elif explicit_override is not None:
            reference_kind = f"{reference_kind}-review-override"
        consumed_sha256 = _sha256(consumed_content)
        # Preserve the historical manifest ordering by reference kind/key/path;
        # consumer distinguishes otherwise identical rows without reshuffling
        # legacy and registry entries.
        key = (reference_kind, resolution.asset_key, staged_relative, consumer)
        entry = self._entries.get(key)
        if entry is None:
            entry = _UsageEntry(
                row={
                    "asset_key": resolution.asset_key,
                    "consumer": consumer,
                    "declared_hash": (
                        None if explicit_override is not None else resolution.declared_hash
                    ),
                    "format": resolution.format,
                    "language": resolution.language,
                    "model": self.target.model,
                    "reference_kind": reference_kind,
                    "registry_declared_hash": resolution.declared_hash,
                    "registry_export_sha256": frozen.sha256,
                    "registry_status": resolution.status,
                    "region": self.target.region,
                    "sha256": consumed_sha256,
                    "source": (
                        "review-override" if explicit_override is not None else resolution.source
                    ),
                    "source_path": (
                        explicit_override.source_relative
                        if explicit_override is not None
                        else frozen.source_relative
                    ),
                    "staged_path": staged_relative,
                    "status": (
                        "review-override" if explicit_override is not None else resolution.status
                    ),
                },
                staged_path=canonical_staged,
                expected_sha256=consumed_sha256,
            )
            self._entries[key] = entry
        entry.references.add(reference_relative)
        if emit_rewrite:
            self._rewrite_events.append(
                {
                    "asset_key": resolution.asset_key,
                    "original_value": original_value or f"asset:{resolution.asset_key}",
                    "reference_kind": reference_kind,
                    "reference_path": reference_relative,
                    "rendered_value": _rendered_relative(
                        staged_relative=staged_relative,
                        reference_relative=reference_relative,
                    )
                    if rendered_value is None
                    else rendered_value,
                    "staged_path": staged_relative,
                }
            )

    def record_legacy(
        self,
        *,
        source_path: Path,
        staged_path: Path,
        reference_path: Path,
        bundle_dir: Path,
        docs_dir: Path,
        original_value: str | None = None,
        rendered_value: str | None = None,
    ) -> None:
        """Record a legacy path so unmanaged images remain visible in the manifest."""

        docs_root, bundle_root = self._trusted_roots(docs_dir=docs_dir, bundle_dir=bundle_dir)
        frozen = self._freeze_legacy(
            source_path,
            docs_root=docs_root,
            bundle_root=bundle_root,
        )
        staged_relative = self._bundle_relative(
            staged_path,
            bundle_root,
            label="staged legacy asset",
        )
        reference_relative = self._reference_relative(reference_path, bundle_root)
        if staged_path.read_bytes() != frozen.content:
            raise AssetRegistryError(f"staged legacy asset was modified: {staged_relative}")

        format_name = frozen.source_path.suffix.lower().lstrip(".") or None
        key = ("legacy-path", frozen.source_relative, staged_relative)
        entry = self._entries.get(key)
        if entry is None:
            entry = _UsageEntry(
                row={
                    "asset_key": None,
                    "consumer": "bundle",
                    "declared_hash": None,
                    "format": format_name,
                    "language": self.target.language,
                    "model": self.target.model,
                    "reference_kind": "legacy-path",
                    "region": self.target.region,
                    "sha256": frozen.sha256,
                    "source": "legacy-path",
                    "source_path": frozen.source_relative,
                    "staged_path": staged_relative,
                    "status": "legacy-unmanaged",
                },
                staged_path=staged_path,
                expected_sha256=frozen.sha256,
            )
            self._entries[key] = entry
        entry.references.add(reference_relative)
        self._rewrite_events.append(
            {
                "asset_key": None,
                "original_value": original_value,
                "reference_kind": "legacy-path",
                "reference_path": reference_relative,
                "rendered_value": _rendered_relative(
                    staged_relative=staged_relative,
                    reference_relative=reference_relative,
                )
                if rendered_value is None
                else rendered_value,
                "staged_path": staged_relative,
            }
        )

    def _asset_rows(self, *, bundle_root: Path) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for key in sorted(self._entries):
            entry = self._entries[key]
            staged = _canonical_file_within(
                entry.staged_path,
                bundle_root,
                label="manifest staged asset",
            )
            actual_hash = _sha256(staged.read_bytes())
            if actual_hash != entry.expected_sha256:
                relative = staged.relative_to(bundle_root).as_posix()
                raise AssetRegistryError(f"staged asset hash changed before manifest write: {relative}")
            row = dict(entry.row)
            row["references"] = sorted(entry.references)
            rows.append(row)
        return rows

    def write(
        self,
        *,
        usage_manifest_path: Path,
        registry_snapshot_path: Path,
        bundle_dir: Path | None = None,
    ) -> tuple[Path, Path]:
        """Write a stable manifest and the exact registry bytes parsed at startup."""

        selected_bundle_root = bundle_dir or usage_manifest_path.parent
        lexical_bundle_root = Path(os.path.abspath(selected_bundle_root))
        bundle_root = _resolved_path(
            selected_bundle_root,
            strict=False,
            label="bundle root",
        )
        if not usage_manifest_path.is_absolute():
            usage_manifest_path = lexical_bundle_root / usage_manifest_path
        if not registry_snapshot_path.is_absolute():
            registry_snapshot_path = lexical_bundle_root / registry_snapshot_path
        lexical_manifest_path = prepare_file_destination_no_symlinks(
            usage_manifest_path,
            destination_root=lexical_bundle_root,
            label="asset usage manifest",
        )
        lexical_snapshot_path = prepare_file_destination_no_symlinks(
            registry_snapshot_path,
            destination_root=lexical_bundle_root,
            label="asset registry snapshot",
        )
        manifest_path = _canonical_target_within(
            lexical_manifest_path,
            bundle_root,
            label="asset usage manifest",
        )
        snapshot_path = _canonical_target_within(
            lexical_snapshot_path,
            bundle_root,
            label="asset registry snapshot",
        )
        if manifest_path == snapshot_path:
            raise AssetRegistryError("asset manifest and registry snapshot paths must differ")

        self._atomic_write(snapshot_path, self._registry_bytes)
        if _sha256(snapshot_path.read_bytes()) != self._registry_sha256:
            raise AssetRegistryError("asset registry snapshot changed while being written")

        # This is intentionally the final input check before serializing the
        # manifest: every row must describe the bytes still present in bundle.
        asset_rows = self._asset_rows(bundle_root=bundle_root)
        payload = {
            "assets": asset_rows,
            "registry_snapshot": {
                "path": snapshot_path.relative_to(bundle_root).as_posix(),
                "sha256": self._registry_sha256,
                "source_path": self._registry_relative,
            },
            "schema_version": 2,
            "rewrites": [
                {**row, "ordinal": ordinal}
                for ordinal, row in enumerate(
                    sorted(
                        self._rewrite_events,
                        key=lambda row: str(row["reference_path"]),
                    ),
                    start=1,
                )
            ],
            "target": {
                "language": self.target.language,
                "model": self.target.model,
                "region": self.target.region,
            },
        }
        self._atomic_write(
            manifest_path,
            (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
                "utf-8"
            ),
        )
        return manifest_path, snapshot_path

    @staticmethod
    def _atomic_write(path: Path, data: bytes) -> None:
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


__all__ = [
    "ASSET_REGISTRY_SNAPSHOT_FILENAME",
    "ASSET_USAGE_MANIFEST_FILENAME",
    "SAFE_BUNDLE_FORMATS",
    "AssetTarget",
    "BundleAssetUsage",
    "FrozenAssetReference",
    "parse_asset_uri",
]
