#!/usr/bin/env python3
"""Resolve and validate the repository's image-asset registry.

The registry is deliberately a small build control plane. Large editable
sources (.ai) are tracked separately in ``data/asset_sources.csv`` and the
dedicated Feishu source table; this module only resolves approved exports that
are safe for a renderer to import.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from tools.app_ui_promotion import (
    PROMOTED_ASSET_KEYS,
    PROMOTION_ID,
    ReviewedPromotionError,
    validate_reviewed_promotion,
)
from tools.utils.path_utils import PathSegments

REGISTRY_RELATIVE_PATH = Path(PathSegments.DATA) / "asset_registry.csv"
APPROVED_STATUS = "✅成品"
TEMPORARY_STATUS = "🔧临时替代"
MISSING_STATUS = "❌缺失"
QUARANTINED_STATUS = "⛔隔离"
VALID_STATUSES = frozenset(
    {APPROVED_STATUS, TEMPORARY_STATUS, MISSING_STATUS, QUARANTINED_STATUS}
)
NEUTRAL_LANGUAGE_DIMENSION = "中立"
LOCALIZED_LANGUAGE_DIMENSION = "按语言"
VALID_LANGUAGE_DIMENSIONS = frozenset(
    {NEUTRAL_LANGUAGE_DIMENSION, LOCALIZED_LANGUAGE_DIMENSION}
)
REQUIRED_COLUMNS = (
    "asset_key",
    "override_for",
    "类别",
    "语言维度",
    "状态",
    "待无字化",
    "适用机型",
    "适用区域",
    "导出物路径",
    "语言变体",
    "内容哈希",
    "备注",
)
HASH_DIGEST_RE = re.compile(r"^[0-9a-fA-F]{8,64}$")
REPO_PATH_PREFIXES = ("docs/", "data/")
EXPORT_PREFIXES = {
    "button": "button_",
    "icon": "icon_",
    "operation": "op_",
}


class AssetRegistryError(RuntimeError):
    """Raised when a requested asset cannot be safely resolved."""


class NoMatchingAssetExportError(AssetRegistryError):
    """Raised when an asset has no materialized export matching a request."""


@dataclass(frozen=True)
class AssetRecord:
    asset_key: str
    category: str
    language_dimension: str
    status: str
    textless_pending: bool
    model_scope: tuple[str, ...]
    region_scope: tuple[str, ...]
    export_root: Path | None
    language_variants: tuple[str, ...]
    hashes: tuple[tuple[str, str], ...]
    notes: str
    override_for: str | None = None

    @property
    def hash_map(self) -> dict[str, str]:
        return dict(self.hashes)


@dataclass(frozen=True)
class AssetResolution:
    asset_key: str
    path: str
    format: str
    status: str
    content_hash: str
    declared_hash: str
    language: str | None
    source: str


@dataclass(frozen=True)
class AssetIssue:
    code: str
    asset_key: str | None
    message: str


@dataclass(frozen=True)
class AssetCheckReport:
    records: int
    status_counts: dict[str, int]
    errors: tuple[AssetIssue, ...]
    warnings: tuple[AssetIssue, ...]


@dataclass(frozen=True)
class AssetRefreshReport:
    """Machine-recomputed registry hash changes and safe skips."""

    records: int
    updated: tuple[str, ...]
    unchanged: tuple[str, ...]
    skipped: tuple[str, ...]
    errors: tuple[AssetIssue, ...]


def _registry_rows(data: str, *, source: str | Path) -> tuple[list[str], list[dict[str, str]]]:
    reader = csv.DictReader(io.StringIO(data, newline=""))
    fieldnames = list(reader.fieldnames or ())
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
    if missing_columns:
        raise AssetRegistryError(
            f"asset registry {source} is missing columns: {', '.join(missing_columns)}"
        )
    rows: list[dict[str, str]] = []
    for raw in reader:
        raw.pop(None, None)
        rows.append({name: (raw.get(name) or "") for name in fieldnames})
    return fieldnames, rows


def refresh_registry_csv(
    existing_text: str,
    *,
    repo_root: Path,
    source: str | Path = REGISTRY_RELATIVE_PATH,
    asset_keys: Iterable[str] | None = None,
) -> tuple[str, AssetRefreshReport]:
    """Recompute every materialized registry digest from the export bytes.

    The operation is deliberately separate from the Feishu mirror: the Base
    owns asset definitions, while the repository owns export bytes and their
    hashes.  This function is dry-run friendly and never changes statuses,
    scopes, paths, or notes.  Missing/unparseable artifacts are errors, so a
    caller can refuse to write a partial refresh.
    """

    records = load_registry_bytes(existing_text.encode("utf-8"), source=source)
    fieldnames, rows = _registry_rows(existing_text, source=source)
    by_key = {record.asset_key: record for record in records}
    selected = set(asset_keys or ())
    errors: list[AssetIssue] = []
    updated: list[str] = []
    unchanged: list[str] = []
    skipped: list[str] = []

    for key in sorted(selected - set(by_key)):
        errors.append(AssetIssue("unknown_asset", key, "asset key is not registered"))

    for row in rows:
        key = row["asset_key"].strip()
        if selected and key not in selected:
            continue
        record = by_key[key]
        if record.export_root is None or not record.hashes or record.status == MISSING_STATUS:
            skipped.append(key)
            continue

        raw_hash_tokens = [token.strip() for token in row["内容哈希"].split(",") if token.strip()]
        if any(
            ":" not in token
            or not HASH_DIGEST_RE.fullmatch(token.rsplit(":", 1)[1].strip())
            for token in raw_hash_tokens
        ):
            errors.append(
                AssetIssue(
                    "invalid_hash_declaration",
                    key,
                    "内容哈希 contains a token without a valid label:digest pair",
                )
            )

        artifacts = {
            label: (path, expected)
            for label, expected in record.hashes
            if (path := _artifact_path(record, label, repo_root=repo_root, language=None))
            is not None
        }
        refreshed_tokens: list[str] = []
        row_errors: list[AssetIssue] = []
        for label, _declared in record.hashes:
            artifact = artifacts.get(label)
            if artifact is None:
                row_errors.append(
                    AssetIssue(
                        "missing_export",
                        key,
                        f"no materialized export matches registry hash label {label!r}",
                    )
                )
                refreshed_tokens.append(f"{label}:{_declared}")
                continue
            path, _expected = artifact
            if not path.is_file():
                row_errors.append(
                    AssetIssue(
                        "missing_export",
                        key,
                        f"missing export: {path.relative_to(repo_root)}",
                    )
                )
                refreshed_tokens.append(f"{label}:{_declared}")
                continue
            refreshed_tokens.append(f"{label}:{_sha256_digest(path)}")

        errors.extend(row_errors)
        refreshed_hashes = ",".join(refreshed_tokens)
        if row["内容哈希"] == refreshed_hashes:
            unchanged.append(key)
        else:
            updated.append(key)
            row["内容哈希"] = refreshed_hashes

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    refreshed_text = output.getvalue()
    # Keep the resolver as the final schema/override gate for generated CSV.
    load_registry_bytes(refreshed_text.encode("utf-8"), source=source)
    return refreshed_text, AssetRefreshReport(
        records=len(rows),
        updated=tuple(updated),
        unchanged=tuple(unchanged),
        skipped=tuple(skipped),
        errors=tuple(errors),
    )


def _split_values(raw: str) -> tuple[str, ...]:
    return tuple(value.strip() for value in re.split(r"[,|;/]", raw or "") if value.strip())


def _parse_hashes(raw: str, *, asset_key: str) -> tuple[tuple[str, str], ...]:
    parsed: list[tuple[str, str]] = []
    for token in (raw or "").split(","):
        token = token.strip()
        if not token or ":" not in token:
            continue
        label, digest = token.rsplit(":", 1)
        label = label.strip()
        digest = digest.strip()
        if not label or not HASH_DIGEST_RE.fullmatch(digest):
            continue
        parsed.append((label, digest.lower()))
    return tuple(parsed)


def _parse_export_root(raw: str, *, asset_key: str) -> Path | None:
    value = (raw or "").strip().strip('"')
    if not value or not value.startswith(REPO_PATH_PREFIXES):
        return None
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise AssetRegistryError(f"asset {asset_key!r} has an unsafe export path: {value!r}")
    return path


def _record_from_row(row: dict[str, str]) -> AssetRecord:
    asset_key = (row.get("asset_key") or "").strip()
    if not asset_key or asset_key.startswith("/") or ".." in Path(asset_key).parts:
        raise AssetRegistryError(f"invalid asset_key: {asset_key!r}")
    status = (row.get("状态") or "").strip()
    if status not in VALID_STATUSES:
        raise AssetRegistryError(f"asset {asset_key!r} has unknown status: {status!r}")
    language_dimension = (row.get("语言维度") or "").strip()
    if language_dimension not in VALID_LANGUAGE_DIMENSIONS:
        raise AssetRegistryError(
            f"asset {asset_key!r} has unknown language dimension: {language_dimension!r}"
        )
    model_scope = _split_values(row.get("适用机型", ""))
    if not model_scope:
        raise AssetRegistryError(f"asset {asset_key!r} has no model scope")
    region_scope = _split_values(row.get("适用区域", ""))
    if not region_scope:
        raise AssetRegistryError(f"asset {asset_key!r} has no region scope")
    return AssetRecord(
        asset_key=asset_key,
        category=(row.get("类别") or "").strip(),
        language_dimension=language_dimension,
        status=status,
        textless_pending=(row.get("待无字化") or "").strip().upper() in {"TRUE", "YES", "Y", "1"},
        model_scope=model_scope,
        region_scope=region_scope,
        export_root=_parse_export_root(row.get("导出物路径", ""), asset_key=asset_key),
        language_variants=_split_values(row.get("语言变体", "")),
        hashes=_parse_hashes(row.get("内容哈希", ""), asset_key=asset_key),
        notes=(row.get("备注") or "").strip(),
        override_for=(row.get("override_for") or "").strip() or None,
    )


def load_registry_bytes(
    data: bytes,
    *,
    source: str | Path = "<memory>",
) -> tuple[AssetRecord, ...]:
    """Parse one immutable CSV byte snapshot and fail closed on bad data."""

    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise AssetRegistryError(f"asset registry {source} is not valid UTF-8") from exc
    reader = csv.DictReader(io.StringIO(text, newline=""))
    columns = tuple(reader.fieldnames or ())
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in columns]
    if missing_columns:
        raise AssetRegistryError(
            f"asset registry {source} is missing columns: {', '.join(missing_columns)}"
        )
    records: list[AssetRecord] = []
    seen: set[str] = set()
    for row in reader:
        record = _record_from_row(row)
        if record.asset_key in seen:
            raise AssetRegistryError(f"duplicate asset_key: {record.asset_key}")
        seen.add(record.asset_key)
        records.append(record)
    known_keys = {record.asset_key for record in records}
    override_keys = {record.asset_key for record in records if record.override_for}
    for record in records:
        if record.override_for is None:
            continue
        if record.override_for == record.asset_key:
            raise AssetRegistryError(f"asset {record.asset_key!r} cannot override itself")
        if record.override_for not in known_keys:
            raise AssetRegistryError(
                f"asset {record.asset_key!r} overrides unknown key {record.override_for!r}"
            )
        if record.override_for in override_keys:
            raise AssetRegistryError(
                f"nested asset override is not allowed: {record.asset_key!r} -> "
                f"{record.override_for!r}"
            )
    return tuple(records)


def load_registry(path: Path) -> tuple[AssetRecord, ...]:
    """Load the CSV registry from exactly one captured byte snapshot."""

    return load_registry_bytes(path.read_bytes(), source=path)


def _artifact_format(label: str) -> str | None:
    if "." in label:
        suffix = Path(label).suffix.lower().lstrip(".")
        return suffix or None
    return label.removeprefix("v2-").lower() or None


def _artifact_filename(record: AssetRecord, label: str, language: str | None) -> str | None:
    if "." in label:
        filename = Path(label).name
        if language and re.search(r"-[a-z]{2,3}(?=\.)", filename, flags=re.IGNORECASE):
            if f"-{language.lower()}." not in filename.lower():
                return None
        return filename

    format_name = _artifact_format(label)
    if not format_name:
        return None
    basename = record.asset_key.rsplit("/", 1)[-1]
    prefix = record.asset_key.split("/", 1)[0]
    # The PR's v2 vector pilot is projected into the LaTeX asset directory
    # with an ``op_`` filename.  The older common-assets exports keep the
    # plain basename, so only apply that prefix to v2 labels.
    filename_prefix = EXPORT_PREFIXES.get(prefix, "")
    if prefix == "operation" and not label.startswith("v2-"):
        filename_prefix = ""
    basename = f"{filename_prefix}{basename}"
    if prefix == "hero":
        basename = f"{basename}_hero"
        if label.startswith("v2-"):
            basename = f"{basename}_v2"
    if prefix == "page":
        effective_language = language
        if not effective_language and len(record.language_variants) == 1:
            effective_language = record.language_variants[0]
        if effective_language:
            basename = f"{basename}-{effective_language}"
    return f"{basename}.{format_name}"


def _matching_artifacts(
    record: AssetRecord,
    *,
    repo_root: Path,
    format_name: str | None,
    language: str | None,
) -> list[tuple[Path, str, str]]:
    if record.export_root is None:
        return []
    matches: list[tuple[Path, str, str]] = []
    for label, digest in record.hashes:
        actual_format = _artifact_format(label)
        if format_name and actual_format != format_name.lower().lstrip("."):
            continue
        path = _artifact_path(record, label, repo_root=repo_root, language=language)
        if path is None:
            continue
        matches.append((path, actual_format or "", digest))
    return matches


def _artifact_path(
    record: AssetRecord,
    label: str,
    *,
    repo_root: Path,
    language: str | None,
) -> Path | None:
    if record.export_root is None:
        return None
    filename = _artifact_filename(record, label, language)
    if not filename:
        return None
    path = repo_root / record.export_root / filename
    # PR #662 records the source row's historical common-assets directory
    # while its v2 vector projections live in docs/renderers/latex/assets.
    # Keep that migration detail in the resolver until the registry row is
    # updated to the final artifact root.
    if label.startswith("v2-") and not path.is_file():
        projected = (
            repo_root
            / PathSegments.DOCS
            / PathSegments.RENDERERS
            / PathSegments.LATEX
            / PathSegments.ASSETS
            / filename
        )
        path = projected if projected.is_file() else path
    return path


def _scope_matches(scope_values: tuple[str, ...], requested: str | None) -> bool:
    if requested is None:
        return "ALL" in {value.upper() for value in scope_values}
    normalized = requested.strip().upper()
    if not normalized:
        return False
    scope = {value.upper() for value in scope_values}
    return "ALL" in scope or normalized in scope


def _resolution_language(record: AssetRecord, language: str | None) -> str | None:
    if record.language_dimension == NEUTRAL_LANGUAGE_DIMENSION:
        return None
    if language is None or not language.strip():
        raise AssetRegistryError(f"asset {record.asset_key} requires an explicit language")
    variants = {variant.casefold(): variant for variant in record.language_variants}
    requested = language.strip().casefold()
    if requested not in variants:
        declared = ", ".join(record.language_variants) or "none"
        raise AssetRegistryError(
            f"asset {record.asset_key} has no language variant {language!r}; declared: {declared}"
        )
    return variants[requested]


def _select_asset_record(
    records: tuple[AssetRecord, ...],
    *,
    asset_key: str,
    model: str | None,
    region: str | None,
    language: str | None,
) -> AssetRecord | None:
    """Select one target-specific override before falling back to the base key."""

    direct = next((item for item in records if item.asset_key == asset_key), None)
    if direct is None:
        return None
    overrides = [
        item
        for item in records
        if item.override_for == asset_key
        and _scope_matches(item.model_scope, model)
        and _scope_matches(item.region_scope, region)
        and (
            item.language_dimension == NEUTRAL_LANGUAGE_DIMENSION
            or (
                language is not None
                and language.strip().casefold()
                in {variant.casefold() for variant in item.language_variants}
            )
        )
    ]
    if len(overrides) > 1:
        matches = ", ".join(sorted(item.asset_key for item in overrides))
        raise AssetRegistryError(
            f"asset {asset_key!r} has ambiguous target overrides: {matches}"
        )
    return overrides[0] if overrides else direct


def _sha256_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_asset(
    records: Iterable[AssetRecord],
    *,
    repo_root: Path,
    asset_key: str,
    format_name: str | None = None,
    language: str | None = None,
    model: str | None = None,
    region: str | None = None,
    allow_temporary: bool = False,
) -> AssetResolution:
    """Resolve one importable export; temporary assets are opt-in."""

    all_records = tuple(records)
    requested_asset_key = asset_key
    record = _select_asset_record(
        all_records,
        asset_key=requested_asset_key,
        model=model,
        region=region,
        language=language,
    )
    if record is None:
        raise AssetRegistryError(f"asset not registered: {requested_asset_key}")
    asset_key = record.asset_key
    if not _scope_matches(record.model_scope, model):
        raise AssetRegistryError(f"asset {asset_key} is not registered for model {model}")
    if not _scope_matches(record.region_scope, region):
        raise AssetRegistryError(f"asset {asset_key} is not registered for region {region}")
    if record.status != APPROVED_STATUS and not (allow_temporary and record.status == TEMPORARY_STATUS):
        raise AssetRegistryError(
            f"asset {asset_key} is {record.status}; only {APPROVED_STATUS} assets are importable"
        )
    resolved_language = _resolution_language(record, language)
    resolution_source = "registry-export"
    if asset_key in PROMOTED_ASSET_KEYS:
        try:
            validate_reviewed_promotion(
                repo_root,
                PROMOTION_ID,
                registry_record=record,
            )
        except ReviewedPromotionError as exc:
            raise AssetRegistryError(
                f"asset {asset_key} reviewed promotion is invalid: {exc}"
            ) from exc
        resolution_source = f"reviewed-promotion:{PROMOTION_ID}"
    candidates = _matching_artifacts(
        record,
        repo_root=repo_root,
        format_name=format_name,
        language=resolved_language,
    )
    existing = [candidate for candidate in candidates if candidate[0].is_file()]
    if not existing:
        requested = format_name or "any format"
        raise NoMatchingAssetExportError(
            f"asset {asset_key} has no existing export for {requested}"
        )
    path, actual_format, declared_hash = existing[0]
    actual_hash = _sha256_digest(path)
    if not actual_hash.startswith(declared_hash.lower()):
        raise AssetRegistryError(
            f"asset {asset_key} export hash mismatch: {path.relative_to(repo_root)} "
            f"(expected prefix {declared_hash})"
        )
    return AssetResolution(
        asset_key=asset_key,
        path=str(path.relative_to(repo_root)),
        format=actual_format,
        status=record.status,
        content_hash=actual_hash,
        declared_hash=declared_hash,
        language=resolved_language,
        source=resolution_source,
    )


def _hash_matches(path: Path, expected: str) -> bool:
    return _sha256_digest(path).startswith(expected.lower())


def check_registry(
    records: Iterable[AssetRecord],
    *,
    repo_root: Path,
    asset_keys: Iterable[str] | None = None,
    publish: bool = False,
) -> AssetCheckReport:
    selected_keys = set(asset_keys or ())
    errors: list[AssetIssue] = []
    warnings: list[AssetIssue] = []
    status_counts = {status: 0 for status in VALID_STATUSES}
    all_records = tuple(records)
    selected_records = [
        record
        for record in all_records
        if not selected_keys or record.asset_key in selected_keys
    ]
    known_keys = {record.asset_key for record in all_records}
    for key in sorted(selected_keys - known_keys):
        errors.append(AssetIssue("unknown_asset", key, "asset key is not registered"))
    if not selected_keys:
        for key in sorted(set(PROMOTED_ASSET_KEYS) - known_keys):
            errors.append(
                AssetIssue(
                    "reviewed_promotion_missing",
                    key,
                    "reviewed promotion output key is not registered",
                )
            )

    if not selected_keys:
        from tools.printed_url_inventory import crosscheck_qr_targets

        for code, key, message in crosscheck_qr_targets(all_records, repo_root=repo_root):
            errors.append(AssetIssue(code, key, message))

    for record in selected_records:
        status_counts[record.status] += 1
        if record.asset_key in PROMOTED_ASSET_KEYS:
            try:
                validate_reviewed_promotion(
                    repo_root,
                    PROMOTION_ID,
                    registry_record=record,
                )
            except ReviewedPromotionError as exc:
                errors.append(
                    AssetIssue(
                        "reviewed_promotion_invalid",
                        record.asset_key,
                        str(exc),
                    )
                )
        if publish and record.status != APPROVED_STATUS:
            errors.append(
                AssetIssue(
                    "non_approved_status",
                    record.asset_key,
                    f"publish requires {APPROVED_STATUS}; found {record.status}",
                )
            )
        if record.status == MISSING_STATUS:
            warnings.append(
                AssetIssue(
                    "registered_missing",
                    record.asset_key,
                    "asset is an explicit missing/debt item",
                )
            )
            continue
        if record.export_root is None or not record.hashes:
            warnings.append(
                AssetIssue(
                    "unmaterialized_export",
                    record.asset_key,
                    "registry row has no local export; it may be Feishu-materialized or source-only",
                )
            )
            continue
        for path, _format_name, expected_hash in _matching_artifacts(
            record, repo_root=repo_root, format_name=None, language=None
        ):
            if not path.is_file():
                errors.append(
                    AssetIssue(
                        "missing_export",
                        record.asset_key,
                        f"missing export: {path.relative_to(repo_root)}",
                    )
                )
            elif not _hash_matches(path, expected_hash):
                errors.append(
                    AssetIssue(
                        "hash_mismatch",
                        record.asset_key,
                        f"hash mismatch: {path.relative_to(repo_root)} (expected prefix {expected_hash})",
                    )
                )
    return AssetCheckReport(
        records=len(selected_records),
        status_counts=status_counts,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def _report_payload(report: AssetCheckReport) -> dict[str, object]:
    return {
        "records": report.records,
        "status_counts": report.status_counts,
        "errors": [asdict(issue) for issue in report.errors],
        "warnings": [asdict(issue) for issue in report.warnings],
    }


def _refresh_report_payload(report: AssetRefreshReport) -> dict[str, object]:
    return {
        "records": report.records,
        "updated": list(report.updated),
        "unchanged": list(report.unchanged),
        "skipped": list(report.skipped),
        "errors": [asdict(issue) for issue in report.errors],
    }


def _atomic_replace_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_name = handle.name
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
        temporary_name = None
    finally:
        if temporary_name is not None:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass


def run_asset_registry_refresh(args: argparse.Namespace, *, repo_root: Path) -> None:
    """Run the explicit ``asset-check --refresh`` registry maintenance pass."""

    if getattr(args, "publish", False):
        raise RuntimeError("asset registry refresh cannot combine with --publish")
    registry_path = repo_root / REGISTRY_RELATIVE_PATH
    existing_text = registry_path.read_text(encoding="utf-8")
    keys = tuple(getattr(args, "asset_key", None) or ())
    refreshed_text, report = refresh_registry_csv(
        existing_text,
        repo_root=repo_root,
        source=registry_path,
        asset_keys=keys,
    )
    if getattr(args, "write", False) and report.errors:
        raise AssetRegistryError(
            "asset registry refresh found errors; refusing to write: "
            + "; ".join(issue.message for issue in report.errors)
        )
    if getattr(args, "write", False) and refreshed_text != existing_text:
        _atomic_replace_text(registry_path, refreshed_text)

    payload = _refresh_report_payload(report)
    payload["mode"] = "write" if getattr(args, "write", False) else "dry-run"
    payload["changed"] = refreshed_text != existing_text
    payload["path"] = registry_path.relative_to(repo_root).as_posix()
    if getattr(args, "json", False):
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print(
        "asset registry refresh: "
        f"mode={payload['mode']} records={report.records} "
        f"updated={len(report.updated)} unchanged={len(report.unchanged)} "
        f"skipped={len(report.skipped)} errors={len(report.errors)}"
    )
    for issue in report.errors:
        print(f"[{issue.code}] {issue.asset_key or '-'}: {issue.message}")
    if getattr(args, "write", False):
        print(f"written={payload['changed']} path={payload['path']}")


def run_asset_check(args: argparse.Namespace, *, repo_root: Path) -> None:
    if getattr(args, "refresh", False):
        run_asset_registry_refresh(args, repo_root=repo_root)
        return
    registry_path = repo_root / REGISTRY_RELATIVE_PATH
    records = load_registry(registry_path)
    keys = tuple(getattr(args, "asset_key", None) or ())
    if getattr(args, "publish", False) and getattr(args, "allow_temporary", False):
        raise RuntimeError("asset-check cannot combine --publish and --allow-temporary")

    report = check_registry(records, repo_root=repo_root, asset_keys=keys, publish=args.publish)
    resolutions: list[dict[str, object]] = []
    if keys:
        for key in keys:
            try:
                resolution = resolve_asset(
                    records,
                    repo_root=repo_root,
                    asset_key=key,
                    format_name=getattr(args, "asset_format", None),
                    language=getattr(args, "lang", None),
                    model=getattr(args, "model", None),
                    region=getattr(args, "region", None),
                    allow_temporary=getattr(args, "allow_temporary", False),
                )
            except AssetRegistryError as exc:
                report = AssetCheckReport(
                    records=report.records,
                    status_counts=report.status_counts,
                    errors=(*report.errors, AssetIssue("unresolvable_asset", key, str(exc))),
                    warnings=report.warnings,
                )
            else:
                resolutions.append(asdict(resolution))

    payload = _report_payload(report)
    if resolutions:
        payload["resolutions"] = resolutions
    if getattr(args, "json", False):
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"asset registry: {report.records} rows; errors={len(report.errors)}; warnings={len(report.warnings)}")
        for issue in (*report.errors, *report.warnings):
            print(f"[{issue.code}] {issue.asset_key or '-'}: {issue.message}")
        for resolution in resolutions:
            print(f"[resolved] {resolution['asset_key']} -> {resolution['path']}")
    if report.errors:
        raise RuntimeError(f"asset registry check failed with {len(report.errors)} error(s)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("check", "resolve"))
    parser.add_argument("--asset-key", action="append", required=False)
    parser.add_argument("--format", dest="asset_format")
    parser.add_argument("--lang")
    parser.add_argument("--model")
    parser.add_argument("--region")
    parser.add_argument("--allow-temporary", action="store_true")
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.action == "resolve" and not args.asset_key:
        print("resolve requires --asset-key", file=sys.stderr)
        return 2
    try:
        run_asset_check(args, repo_root=Path(__file__).resolve().parents[1])
    except (AssetRegistryError, RuntimeError) as exc:
        print(f"[asset_registry] ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
