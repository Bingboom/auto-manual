"""Read a finalized bundle's governed asset resolutions safely."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ASSET_URI_PREFIX = "asset:"
ASSET_USAGE_MANIFEST_FILENAME = "asset_usage_manifest.json"
SUPPORTED_SCHEMA_VERSIONS = frozenset({2})


class BundleAssetManifestError(RuntimeError):
    """A finalized bundle asset cannot be resolved safely."""


def is_asset_uri(value: str) -> bool:
    """Return whether ``value`` names a semantic registry asset."""

    return value.strip().casefold().startswith(ASSET_URI_PREFIX)


def _parse_asset_uri(value: str) -> str:
    token = value.strip()
    if not token.casefold().startswith(ASSET_URI_PREFIX):
        raise BundleAssetManifestError(
            f"bundle manifest lookup requires an asset URI: {value!r}"
        )
    asset_key = token[len(ASSET_URI_PREFIX) :].strip()
    key_path = Path(asset_key)
    if not asset_key or key_path.is_absolute() or ".." in key_path.parts:
        raise BundleAssetManifestError(f"asset URI has an unsafe key: {asset_key!r}")
    return asset_key


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_bundle_file(bundle_root: Path, raw_relative: object, *, label: str) -> Path:
    value = str(raw_relative or "").strip()
    relative = Path(value)
    if not value or relative.is_absolute() or ".." in relative.parts:
        raise BundleAssetManifestError(f"{label} has unsafe bundle path: {value!r}")

    candidate = bundle_root
    for part in relative.parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise BundleAssetManifestError(
                f"{label} must not be a symbolic link: {value!r}"
            )
    try:
        canonical = candidate.resolve(strict=True)
        canonical.relative_to(bundle_root)
    except (FileNotFoundError, OSError, ValueError) as exc:
        raise BundleAssetManifestError(
            f"{label} escapes or is missing from bundle: {value!r}"
        ) from exc
    if not canonical.is_file():
        raise BundleAssetManifestError(f"{label} is not a file: {value!r}")
    return canonical


def resolve_manifest_asset(
    bundle_dir: Path,
    asset_uri: str,
    *,
    format_name: str | None = None,
    consumer: str | None = None,
    reference_kind: str | None = None,
    model: str | None = None,
    region: str | None = None,
    language: str | None = None,
) -> Path:
    """Resolve one semantic asset URI from the finalized usage manifest.

    The manifest is the renderer boundary: callers never guess a staged path.
    Both the manifest path and resolved asset stay inside the canonical bundle,
    and the bytes are re-hashed before they are handed to the renderer.
    """

    asset_key = _parse_asset_uri(asset_uri)
    required_format = (
        format_name.strip().casefold().lstrip(".") if format_name is not None else None
    )
    if format_name is not None and not required_format:
        raise BundleAssetManifestError("bundle manifest asset format must be non-empty")
    required_consumer = consumer.strip() if consumer is not None else None
    if consumer is not None and not required_consumer:
        raise BundleAssetManifestError(
            "bundle manifest asset consumer must be non-empty"
        )
    required_reference_kind = (
        reference_kind.strip() if reference_kind is not None else None
    )
    if reference_kind is not None and not required_reference_kind:
        raise BundleAssetManifestError(
            "bundle manifest asset reference kind must be non-empty"
        )
    expected_model = model.strip() if model is not None else None
    expected_region = region.strip() if region is not None else None
    expected_language = language.strip() if language is not None else None
    for label, supplied, normalized in (
        ("model", model, expected_model),
        ("region", region, expected_region),
        ("language", language, expected_language),
    ):
        if supplied is not None and not normalized:
            raise BundleAssetManifestError(
                f"bundle manifest expected {label} must be non-empty"
            )

    try:
        bundle_root = bundle_dir.resolve(strict=True)
    except (FileNotFoundError, OSError) as exc:
        raise BundleAssetManifestError("bundle asset root is not usable") from exc
    if not bundle_root.is_dir():
        raise BundleAssetManifestError("bundle asset root is not a directory")
    manifest_path = _safe_bundle_file(
        bundle_root,
        ASSET_USAGE_MANIFEST_FILENAME,
        label="asset usage manifest",
    )
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BundleAssetManifestError(
            f"asset usage manifest is invalid: {manifest_path}"
        ) from exc
    if not isinstance(payload, dict):
        raise BundleAssetManifestError(
            f"asset usage manifest root is invalid: {manifest_path}"
        )
    schema_version = payload.get("schema_version")
    if (
        type(schema_version) is not int
        or schema_version not in SUPPORTED_SCHEMA_VERSIONS
    ):
        raise BundleAssetManifestError(
            f"asset usage manifest has unsupported schema_version: {schema_version!r}"
        )
    raw_target = payload.get("target")
    if not isinstance(raw_target, dict):
        raise BundleAssetManifestError(
            f"asset usage manifest has invalid target: {manifest_path}"
        )
    manifest_model = raw_target.get("model")
    manifest_region = raw_target.get("region")
    manifest_language = raw_target.get("language")
    if not isinstance(manifest_model, str) or not manifest_model.strip():
        raise BundleAssetManifestError("asset usage manifest target model is invalid")
    if not isinstance(manifest_region, str) or not manifest_region.strip():
        raise BundleAssetManifestError("asset usage manifest target region is invalid")
    if manifest_language is not None and (
        not isinstance(manifest_language, str) or not manifest_language.strip()
    ):
        raise BundleAssetManifestError("asset usage manifest target language is invalid")
    target_pairs = (
        ("model", manifest_model, expected_model),
        ("region", manifest_region, expected_region),
    )
    for label, actual, expected in target_pairs:
        if expected is not None and actual.strip().casefold() != expected.casefold():
            raise BundleAssetManifestError(
                f"asset usage manifest target {label} does not match expected target"
            )
    if (
        expected_language is not None
        and manifest_language is not None
        and manifest_language.strip().casefold() != expected_language.casefold()
    ):
        raise BundleAssetManifestError(
            "asset usage manifest target language does not match expected target"
        )

    raw_assets = payload.get("assets")
    if not isinstance(raw_assets, list):
        raise BundleAssetManifestError(
            f"asset usage manifest has invalid assets: {manifest_path}"
        )

    candidates = [
        row
        for row in raw_assets
        if isinstance(row, dict)
        and row.get("asset_key") == asset_key
        and (
            required_format is None
            or str(row.get("format") or "").strip().casefold() == required_format
        )
    ]
    if not candidates:
        suffix = f" ({required_format})" if required_format is not None else ""
        raise BundleAssetManifestError(
            f"asset usage manifest has no resolved asset {asset_key!r}{suffix}"
        )
    selected = candidates
    if required_consumer is not None or required_reference_kind is not None:
        def reference_matches(row: dict[str, object]) -> bool:
            actual = str(row.get("reference_kind") or "").strip()
            return (
                required_reference_kind is None
                or actual == required_reference_kind
                or actual == f"{required_reference_kind}-review-override"
            )

        preferred = [
            row
            for row in candidates
            if (
                required_consumer is None
                or str(row.get("consumer") or "").strip() == required_consumer
            )
            and reference_matches(row)
        ]
        if preferred:
            selected = preferred
        elif len(candidates) == 1:
            row = candidates[0]
            actual_consumer = str(row.get("consumer") or "").strip()
            actual_reference_kind = str(row.get("reference_kind") or "").strip()
            consumer_compatible = (
                required_consumer is None
                or not actual_consumer
                or actual_consumer == required_consumer
            )
            reference_compatible = (
                required_reference_kind is None
                or not actual_reference_kind
                or reference_matches(row)
            )
            if consumer_compatible and reference_compatible:
                # Older manifests may omit consumer metadata.  One key/format
                # row remains deterministic and still passes all safety checks.
                selected = candidates
            else:
                raise BundleAssetManifestError(
                    f"asset usage manifest has no preferred resolved asset {asset_key!r}"
                )
        else:
            raise BundleAssetManifestError(
                f"asset usage manifest has no preferred resolved asset {asset_key!r}"
            )
    if len(selected) != 1:
        raise BundleAssetManifestError(
            f"asset usage manifest has ambiguous resolved asset {asset_key!r}"
        )

    row = selected[0]
    staged = _safe_bundle_file(
        bundle_root,
        row.get("staged_path"),
        label=f"staged asset {asset_key!r}",
    )
    declared_format = str(row.get("format") or "").strip().casefold().lstrip(".")
    staged_format = staged.suffix.casefold().lstrip(".")
    equivalent_formats = {declared_format, staged_format} <= {"jpg", "jpeg"}
    if not declared_format or (
        declared_format != staged_format and not equivalent_formats
    ):
        raise BundleAssetManifestError(
            f"staged asset suffix does not match declared format: {asset_key!r}"
        )
    expected_hash = str(row.get("sha256") or "").strip().casefold()
    if len(expected_hash) != 64 or any(ch not in "0123456789abcdef" for ch in expected_hash):
        raise BundleAssetManifestError(
            f"asset usage manifest has invalid sha256 for {asset_key!r}"
        )
    if _sha256(staged) != expected_hash:
        raise BundleAssetManifestError(
            f"staged asset hash does not match manifest: {asset_key!r}"
        )
    return staged


__all__ = (
    "BundleAssetManifestError",
    "is_asset_uri",
    "resolve_manifest_asset",
)
