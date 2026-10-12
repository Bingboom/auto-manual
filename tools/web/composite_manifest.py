"""Frozen Web composite asset manifest and bundle staging.

The live Base is an intake/control plane. Rendering consumes only a snapshot
manifest plus content-addressed files, so local, CI, and ReadTheDocs builds are
reproducible and never require Feishu credentials.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Iterable

from tools.utils.path_utils import (
    PathSegments,
    bundle_web_composite_assets_of,
    web_composite_manifest_of,
)

WEB_COMPOSITE_MANIFEST_SCHEMA = "web-composite-manifest/v1"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_SCOPE_SPLIT_RE = re.compile(r"[,;\n]+")


class WebCompositeManifestError(RuntimeError):
    """The frozen Web composite snapshot is invalid or ambiguous."""


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _scope_matches(scope: str, value: str | None) -> bool:
    tokens = {
        token.strip().casefold()
        for token in _SCOPE_SPLIT_RE.split(scope or "")
        if token.strip()
    }
    if not tokens or "all" in tokens:
        return True
    candidate = (value or "").strip().casefold()
    return bool(candidate) and candidate in tokens


def _safe_part(value: str, *, fallback: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip()).strip("._-")
    return cleaned or fallback


@dataclass(frozen=True)
class WebCompositeEntry:
    asset_key: str
    web_replace_key: str
    model_scope: str
    region_scope: str
    locale: str
    source_page: int | None
    content_sha256: str
    path: str
    format: str
    source_fragment_sha256: str
    definition_record_id: str = ""
    export_record_id: str = ""

    @classmethod
    def from_payload(cls, payload: dict[str, Any], *, source: Path) -> "WebCompositeEntry":
        def required(name: str) -> str:
            value = str(payload.get(name) or "").strip()
            if not value:
                raise WebCompositeManifestError(f"{source}: manifest entry is missing {name}")
            return value

        content_sha256 = required("content_sha256").casefold()
        if not _SHA256_RE.fullmatch(content_sha256):
            raise WebCompositeManifestError(
                f"{source}: invalid content_sha256 for {payload.get('web_replace_key')!r}"
            )
        source_fragment_sha256 = required("source_fragment_sha256").casefold()
        if not _SHA256_RE.fullmatch(source_fragment_sha256):
            raise WebCompositeManifestError(
                f"{source}: invalid source_fragment_sha256 for {payload.get('web_replace_key')!r}"
            )
        raw_page = payload.get("source_page")
        source_page: int | None
        if raw_page in (None, ""):
            source_page = None
        else:
            try:
                source_page = int(raw_page)
            except (TypeError, ValueError) as exc:
                raise WebCompositeManifestError(
                    f"{source}: invalid source_page for {payload.get('web_replace_key')!r}"
                ) from exc
        return cls(
            asset_key=required("asset_key"),
            web_replace_key=required("web_replace_key"),
            model_scope=str(payload.get("model_scope") or "ALL").strip() or "ALL",
            region_scope=str(payload.get("region_scope") or "ALL").strip() or "ALL",
            locale=required("locale"),
            source_page=source_page,
            content_sha256=content_sha256,
            path=required("path"),
            format=required("format").casefold(),
            source_fragment_sha256=source_fragment_sha256,
            definition_record_id=str(payload.get("definition_record_id") or "").strip(),
            export_record_id=str(payload.get("export_record_id") or "").strip(),
        )

    def applies_to(self, *, model: str | None, region: str | None) -> bool:
        return _scope_matches(self.model_scope, model) and _scope_matches(
            self.region_scope, region
        )

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "asset_key": self.asset_key,
            "content_sha256": self.content_sha256,
            "format": self.format,
            "locale": self.locale,
            "model_scope": self.model_scope,
            "path": self.path,
            "region_scope": self.region_scope,
            "source_page": self.source_page,
            "web_replace_key": self.web_replace_key,
        }
        payload["source_fragment_sha256"] = self.source_fragment_sha256
        if self.definition_record_id:
            payload["definition_record_id"] = self.definition_record_id
        if self.export_record_id:
            payload["export_record_id"] = self.export_record_id
        return payload


@dataclass(frozen=True)
class WebCompositeManifest:
    entries: tuple[WebCompositeEntry, ...]
    source: Path
    generated_at: str = ""

    def entries_for_target(
        self,
        *,
        model: str | None,
        region: str | None,
    ) -> tuple[WebCompositeEntry, ...]:
        return tuple(
            entry
            for entry in self.entries
            if entry.applies_to(model=model, region=region)
        )

    def resolve(
        self,
        *,
        web_replace_key: str,
        locale: str,
        model: str | None,
        region: str | None,
    ) -> WebCompositeEntry | None:
        candidates = [
            entry
            for entry in self.entries_for_target(model=model, region=region)
            if entry.web_replace_key == web_replace_key
        ]
        requested = locale.strip().casefold()
        exact = [entry for entry in candidates if entry.locale.casefold() == requested]
        matches = exact or [entry for entry in candidates if entry.locale.casefold() == "shared"]
        if len(matches) > 1:
            record_ids = ", ".join(
                entry.export_record_id or entry.asset_key for entry in matches
            )
            raise WebCompositeManifestError(
                "multiple approved Web composites match "
                f"{web_replace_key!r} locale={locale!r} model={model!r} region={region!r}: "
                f"{record_ids}"
            )
        return matches[0] if matches else None


def manifest_json_text(
    entries: Iterable[WebCompositeEntry],
    *,
    generated_at: str = "",
    source_manifest_sha256: str = "",
) -> str:
    ordered = sorted(
        entries,
        key=lambda entry: (
            entry.web_replace_key.casefold(),
            entry.model_scope.casefold(),
            entry.region_scope.casefold(),
            entry.locale.casefold(),
            entry.asset_key.casefold(),
        ),
    )
    payload: dict[str, Any] = {
        "schema_version": WEB_COMPOSITE_MANIFEST_SCHEMA,
        "entries": [entry.to_payload() for entry in ordered],
    }
    if generated_at:
        payload["generated_at"] = generated_at
    if source_manifest_sha256:
        payload["source_manifest_sha256"] = source_manifest_sha256
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def load_web_composite_manifest(path: Path) -> WebCompositeManifest:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WebCompositeManifestError(f"cannot load Web composite manifest {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise WebCompositeManifestError(f"{path}: manifest root must be an object")
    if payload.get("schema_version") != WEB_COMPOSITE_MANIFEST_SCHEMA:
        raise WebCompositeManifestError(f"{path}: unsupported Web composite manifest schema")
    raw_entries = payload.get("entries")
    if not isinstance(raw_entries, list):
        raise WebCompositeManifestError(f"{path}: entries must be a list")
    entries: list[WebCompositeEntry] = []
    for raw in raw_entries:
        if not isinstance(raw, dict):
            raise WebCompositeManifestError(f"{path}: every manifest entry must be an object")
        entries.append(WebCompositeEntry.from_payload(raw, source=path))
    return WebCompositeManifest(
        entries=tuple(entries),
        source=path,
        generated_at=str(payload.get("generated_at") or "").strip(),
    )


def load_optional_web_composite_manifest(path: Path) -> WebCompositeManifest | None:
    if not path.is_file():
        return None
    return load_web_composite_manifest(path)


def _source_asset_path(
    entry: WebCompositeEntry,
    *,
    snapshot_root: Path,
) -> Path:
    relative = Path(entry.path.strip())
    if relative.is_absolute():
        raise WebCompositeManifestError(
            f"{entry.web_replace_key}: snapshot asset path must be relative"
        )
    candidate = snapshot_root / relative
    root = snapshot_root.resolve(strict=True)
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, ValueError) as exc:
        raise WebCompositeManifestError(
            f"{entry.web_replace_key}: asset path escapes or is missing: {entry.path}"
        ) from exc
    if not resolved.is_file():
        raise WebCompositeManifestError(
            f"{entry.web_replace_key}: asset path is not a file: {entry.path}"
        )
    return resolved


def stage_web_composite_snapshot(
    *,
    source_manifest_path: Path,
    snapshot_root: Path,
    bundle_root: Path,
    model: str | None,
    region: str | None,
) -> Path | None:
    """Freeze target-matching Web composites into one materialized bundle."""
    manifest = load_optional_web_composite_manifest(source_manifest_path)
    if manifest is None:
        return None
    target_entries = manifest.entries_for_target(model=model, region=region)
    target_dir = bundle_web_composite_assets_of(bundle_root)
    target_dir.mkdir(parents=True, exist_ok=True)
    staged_entries: list[WebCompositeEntry] = []
    for entry in target_entries:
        source_path = _source_asset_path(
            entry,
            snapshot_root=snapshot_root,
        )
        actual_sha256 = _file_sha256(source_path)
        if actual_sha256 != entry.content_sha256:
            raise WebCompositeManifestError(
                f"{entry.web_replace_key}: attachment SHA-256 mismatch; "
                f"expected {entry.content_sha256}, got {actual_sha256}"
            )
        suffix = source_path.suffix.casefold() or f".{entry.format}"
        target_name = (
            f"{_safe_part(entry.web_replace_key, fallback='component')}_"
            f"{_safe_part(entry.locale, fallback='shared')}_"
            f"{entry.content_sha256[:12]}{suffix}"
        )
        target_path = target_dir / target_name
        if target_path.exists():
            if _file_sha256(target_path) != entry.content_sha256:
                raise WebCompositeManifestError(
                    f"staged Web composite path contains unexpected bytes: {target_path}"
                )
        else:
            shutil.copy2(source_path, target_path)
        staged_entries.append(
            replace(
                entry,
                path=(
                    PathSegments.BUNDLE_ASSETS
                    + "/"
                    + PathSegments.WEB_COMPOSITES
                    + "/"
                    + target_name
                ),
            )
        )

    staged_manifest_path = web_composite_manifest_of(bundle_root)
    source_sha256 = _file_sha256(source_manifest_path)
    staged_manifest_path.write_text(
        manifest_json_text(
            staged_entries,
            generated_at=manifest.generated_at,
            source_manifest_sha256=source_sha256,
        ),
        encoding="utf-8",
    )
    return staged_manifest_path


__all__ = (
    "WEB_COMPOSITE_MANIFEST_SCHEMA",
    "WebCompositeEntry",
    "WebCompositeManifest",
    "WebCompositeManifestError",
    "load_optional_web_composite_manifest",
    "load_web_composite_manifest",
    "manifest_json_text",
    "stage_web_composite_snapshot",
)
