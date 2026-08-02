"""Sync approved Base Web-composite exports into a frozen phase2 snapshot."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Protocol

from tools.utils.path_utils import (
    PathSegments,
    web_composite_attachments_of,
    web_composite_manifest_of,
)
from tools.web_composite_manifest import (
    WebCompositeEntry,
    WebCompositeManifestError,
    manifest_json_text,
)

_BINDINGS_FILE_NAME = "asset_base_bindings.json"
_DEFINITIONS_TABLE_KEY = "asset_definitions"
_EXPORTS_TABLE_KEY = "asset_exports"
_WEB_ARTIFACT_KIND = "web-composite"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class _RecordSource(Protocol):
    def fetch_records(
        self,
        *,
        base_token: str,
        table_id: str,
        view_id: str | None,
    ) -> list[dict[str, Any]]:
        ...


class _RecordSourceWithIds(_RecordSource, Protocol):
    def fetch_records_with_ids(
        self,
        *,
        base_token: str,
        table_id: str,
        view_id: str | None,
    ) -> list[dict[str, Any]]:
        ...


class _AttachmentDownloader(_RecordSource, Protocol):
    def download_drive_file(
        self,
        *,
        file_token: str,
        output_path: Path,
        overwrite: bool = False,
    ) -> None:
        ...


def _fields(record: dict[str, Any]) -> dict[str, Any]:
    raw = record.get("fields")
    return raw if isinstance(raw, dict) else record


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        if all(isinstance(item, dict) for item in value):
            parts = [
                str(item.get("text") or item.get("name") or item.get("value") or "").strip()
                for item in value
            ]
        else:
            parts = [str(item).strip() for item in value]
        return ",".join(part for part in parts if part)
    if isinstance(value, dict):
        return str(value.get("text") or value.get("name") or value.get("value") or "").strip()
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value).strip()


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _text(value).casefold() in {"1", "true", "yes", "y"}


def _attachment_items(value: Any) -> list[dict[str, Any]]:
    payload = value
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return []
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return []
    items = payload if isinstance(payload, list) else [payload]
    return [item for item in items if isinstance(item, dict)]


def _file_token(item: dict[str, Any]) -> str:
    return str(item.get("file_token") or item.get("token") or "").strip()


def _safe_part(value: str, *, fallback: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip()).strip("._-")
    return cleaned or fallback


def _attachment_suffix(item: dict[str, Any], format_name: str) -> str:
    name = str(item.get("name") or item.get("file_name") or "").strip()
    suffix = Path(name).suffix.casefold()
    if suffix:
        return suffix
    normalized = format_name.strip().casefold()
    return f".{normalized}" if normalized else ".png"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _bindings(repo_root: Path) -> dict[str, dict[str, Any]]:
    path = repo_root / PathSegments.DATA / _BINDINGS_FILE_NAME
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cannot load frozen asset Base bindings {path}: {exc}") from exc
    tables = payload.get("tables") if isinstance(payload, dict) else None
    if not isinstance(tables, dict):
        raise RuntimeError(f"{path} has no tables mapping")
    resolved: dict[str, dict[str, Any]] = {}
    for key in (_DEFINITIONS_TABLE_KEY, _EXPORTS_TABLE_KEY):
        table = tables.get(key)
        if not isinstance(table, dict) or not str(table.get("table_id") or "").strip():
            raise RuntimeError(f"{path} has no {key}.table_id")
        resolved[key] = table
    return resolved


def _fetch_records(
    source: _RecordSource,
    *,
    base_token: str,
    table: dict[str, Any],
) -> list[dict[str, Any]]:
    fetch_with_ids = getattr(source, "fetch_records_with_ids", None)
    fetch = fetch_with_ids if callable(fetch_with_ids) else source.fetch_records
    return fetch(
        base_token=base_token,
        table_id=str(table["table_id"]),
        view_id=str(table.get("default_view_id") or "").strip() or None,
    )


def _definition_map(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    definitions: dict[str, dict[str, Any]] = {}
    for record in records:
        fields = _fields(record)
        asset_key = _text(fields.get("asset_key"))
        if not asset_key:
            continue
        if asset_key in definitions:
            raise WebCompositeManifestError(
                f"04_资产定义 contains duplicate asset_key {asset_key!r}"
            )
        definitions[asset_key] = {
            "record_id": str(record.get("record_id") or "").strip(),
            **fields,
        }
    return definitions


def _language_variants(value: Any) -> set[str]:
    return {
        token.strip().casefold()
        for token in re.split(r"[,;\n]+", _text(value))
        if token.strip()
    }


def _require_approved_definition(asset_key: str, fields: dict[str, Any]) -> None:
    if not _bool(fields.get("build_eligible")):
        raise WebCompositeManifestError(
            f"approved Web export {asset_key!r} points to a non-buildable definition"
        )
    if _text(fields.get("gate_status")).casefold() != "approved":
        raise WebCompositeManifestError(
            f"approved Web export {asset_key!r} points to an unapproved definition"
        )
    if _bool(fields.get("visual_review_required")):
        raise WebCompositeManifestError(
            f"approved Web export {asset_key!r} still requires visual review"
        )


def _download_and_verify(
    *,
    source: _RecordSource,
    file_token: str,
    target_path: Path,
    expected_sha256: str,
) -> None:
    if target_path.exists():
        actual = _sha256(target_path)
        if actual != expected_sha256:
            raise WebCompositeManifestError(
                f"cached Web composite {target_path} has SHA-256 {actual}; "
                f"expected {expected_sha256}"
            )
        return
    downloader = getattr(source, "download_drive_file", None)
    if not callable(downloader):
        raise WebCompositeManifestError(
            "Web composite attachments require the sync source to support downloads"
        )
    target_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{target_path.name}.",
        suffix=".part",
        dir=target_path.parent,
    )
    os.close(fd)
    temporary_path = Path(temporary_name)
    temporary_path.unlink()
    try:
        downloader(
            file_token=file_token,
            output_path=temporary_path,
            overwrite=False,
        )
        if not temporary_path.is_file():
            raise WebCompositeManifestError(
                f"Web composite download did not create {temporary_path}"
            )
        actual = _sha256(temporary_path)
        if actual != expected_sha256:
            raise WebCompositeManifestError(
                f"downloaded Web composite {target_path} has SHA-256 {actual}; "
                f"expected {expected_sha256}"
            )
        temporary_path.replace(target_path)
    finally:
        temporary_path.unlink(missing_ok=True)


def build_web_composite_entries(
    *,
    definition_records: list[dict[str, Any]],
    export_records: list[dict[str, Any]],
    export_root: Path,
    source: _RecordSource,
    dry_run: bool,
) -> tuple[WebCompositeEntry, ...]:
    definitions = _definition_map(definition_records)
    attachments_root = web_composite_attachments_of(export_root)
    entries: list[WebCompositeEntry] = []
    identities: dict[tuple[str, str, str, str], str] = {}
    for record in export_records:
        fields = _fields(record)
        if _text(fields.get("artifact_kind")).casefold() != _WEB_ARTIFACT_KIND:
            continue
        if not _bool(fields.get("build_eligible")):
            continue
        export_record_id = str(record.get("record_id") or "").strip()
        export_key = _text(fields.get("export_key")) or export_record_id or "<unknown>"
        if _text(fields.get("gate_status")).casefold() != "approved":
            raise WebCompositeManifestError(
                f"buildable Web export {export_key!r} is not approved"
            )
        if _bool(fields.get("visual_review_required")):
            raise WebCompositeManifestError(
                f"buildable Web export {export_key!r} still requires visual review"
            )
        asset_key = _text(fields.get("asset_key"))
        definition = definitions.get(asset_key)
        if definition is None:
            raise WebCompositeManifestError(
                f"buildable Web export {export_key!r} references missing asset_key {asset_key!r}"
            )
        _require_approved_definition(asset_key, definition)
        web_replace_key = _text(definition.get("web_replace_key"))
        if not web_replace_key:
            raise WebCompositeManifestError(
                f"buildable Web asset definition {asset_key!r} has no web_replace_key"
            )
        # ``locale`` predates Web-composite assembly and is free text across the
        # existing export inventory.  New Web rows use the dedicated select so
        # operators can choose only en/fr/es/shared without migrating 142 legacy
        # records.  Keep the old field as a compatibility fallback for frozen
        # snapshots created before the dedicated field existed.
        locale = _text(fields.get("web_locale")) or _text(fields.get("locale"))
        if not locale:
            raise WebCompositeManifestError(
                f"buildable Web export {export_key!r} has no web_locale or locale"
            )
        language_dimension = _text(definition.get("language_dimension"))
        variants = _language_variants(definition.get("language_variants"))
        if language_dimension == "中立" and locale.casefold() != "shared":
            raise WebCompositeManifestError(
                f"neutral Web asset {asset_key!r} must use locale=shared"
            )
        if language_dimension == "按语言":
            if locale.casefold() == "shared":
                raise WebCompositeManifestError(
                    f"localized Web asset {asset_key!r} cannot use locale=shared"
                )
            if variants and locale.casefold() not in variants:
                raise WebCompositeManifestError(
                    f"locale {locale!r} is not declared by {asset_key!r}: {sorted(variants)}"
                )
        content_sha256 = _text(fields.get("content_sha256")).casefold()
        if not _SHA256_RE.fullmatch(content_sha256):
            raise WebCompositeManifestError(
                f"buildable Web export {export_key!r} has an invalid content_sha256"
            )
        items = _attachment_items(fields.get("export_file"))
        if len(items) != 1:
            raise WebCompositeManifestError(
                f"buildable Web export {export_key!r} must have exactly one export_file attachment"
            )
        file_token = _file_token(items[0])
        if not file_token:
            raise WebCompositeManifestError(
                f"buildable Web export {export_key!r} attachment has no file_token"
            )
        format_name = _text(fields.get("format")).casefold()
        if not format_name:
            raise WebCompositeManifestError(
                f"buildable Web export {export_key!r} has no format"
            )
        model_scope = _text(definition.get("model_scope")) or "ALL"
        region_scope = _text(definition.get("region_scope")) or "ALL"
        identity = (
            web_replace_key.casefold(),
            model_scope.casefold(),
            region_scope.casefold(),
            locale.casefold(),
        )
        prior = identities.get(identity)
        if prior is not None:
            raise WebCompositeManifestError(
                f"multiple buildable Web exports match {identity}: {prior}, {export_key}"
            )
        identities[identity] = export_key
        target_name = (
            f"{_safe_part(web_replace_key, fallback='component')}_"
            f"{_safe_part(locale, fallback='shared')}_"
            f"{content_sha256[:12]}{_attachment_suffix(items[0], format_name)}"
        )
        target_path = attachments_root / target_name
        if not dry_run:
            _download_and_verify(
                source=source,
                file_token=file_token,
                target_path=target_path,
                expected_sha256=content_sha256,
            )
        raw_page = fields.get("source_page")
        source_page = int(float(_text(raw_page))) if _text(raw_page) else None
        source_fragment_sha256 = _text(
            fields.get("source_fragment_sha256")
        ).casefold()
        if not _SHA256_RE.fullmatch(source_fragment_sha256):
            raise WebCompositeManifestError(
                f"buildable Web export {export_key!r} has a missing or invalid "
                "source_fragment_sha256"
            )
        entries.append(
            WebCompositeEntry(
                asset_key=asset_key,
                web_replace_key=web_replace_key,
                model_scope=model_scope,
                region_scope=region_scope,
                locale=locale,
                source_page=source_page,
                content_sha256=content_sha256,
                path=(
                    PathSegments.ATTACHMENTS
                    + "/"
                    + PathSegments.WEB_COMPOSITES
                    + "/"
                    + target_name
                ),
                format=format_name,
                source_fragment_sha256=source_fragment_sha256,
                definition_record_id=str(definition.get("record_id") or "").strip(),
                export_record_id=export_record_id,
            )
        )
    return tuple(entries)


def sync_web_composites(
    cfg: dict[str, Any],
    *,
    source: _RecordSource,
    repo_root: Path,
    export_root: Path,
    dry_run: bool,
    generated_at: str,
    sha256_text: Any,
    sha256_file: Any,
    result_cls: Any,
):
    phase2 = (cfg.get("sync") or {}).get("phase2") or {}
    web_cfg = phase2.get("web_composites")
    if web_cfg is None:
        return None, None
    if not isinstance(web_cfg, dict):
        raise RuntimeError("sync.phase2.web_composites must be a mapping")
    base_token_env = str(
        web_cfg.get("base_token_env") or phase2.get("base_token_env") or ""
    ).strip()
    base_token = os.environ.get(base_token_env, "").strip() if base_token_env else ""
    if not base_token:
        raise RuntimeError(
            "sync.phase2.web_composites is configured but "
            f"{base_token_env or 'base_token_env'} is not set in the environment"
        )
    tables = _bindings(repo_root)
    definition_records = _fetch_records(
        source,
        base_token=base_token,
        table=tables[_DEFINITIONS_TABLE_KEY],
    )
    export_records = _fetch_records(
        source,
        base_token=base_token,
        table=tables[_EXPORTS_TABLE_KEY],
    )
    entries = build_web_composite_entries(
        definition_records=definition_records,
        export_records=export_records,
        export_root=export_root,
        source=source,
        dry_run=dry_run,
    )
    text = manifest_json_text(entries, generated_at=generated_at)
    target_path = web_composite_manifest_of(export_root)
    digest = sha256_text(text)
    previous_digest = sha256_file(target_path)
    result = result_cls(
        logical_name="web_composite_manifest",
        file_name=target_path.name,
        target_path=target_path,
        row_count=len(entries),
        sha256=digest,
        previous_sha256=previous_digest,
        changed=digest != previous_digest,
    )
    return result, (target_path, text)


__all__ = (
    "build_web_composite_entries",
    "sync_web_composites",
)
