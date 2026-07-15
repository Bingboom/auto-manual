#!/usr/bin/env python3
"""Resolve and validate the repository's image-asset registry.

The registry is deliberately a small control plane.  Large editable sources
(.ai) stay in the Feishu attachment column; this module only resolves approved
exports that are safe for a renderer to import.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from tools.utils.path_utils import PathSegments

REGISTRY_RELATIVE_PATH = Path(PathSegments.DATA) / "asset_registry.csv"
APPROVED_STATUS = "✅成品"
TEMPORARY_STATUS = "🔧临时替代"
MISSING_STATUS = "❌缺失"
VALID_STATUSES = frozenset({APPROVED_STATUS, TEMPORARY_STATUS, MISSING_STATUS})
REQUIRED_COLUMNS = (
    "asset_key",
    "类别",
    "语言维度",
    "状态",
    "待无字化",
    "适用机型",
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


@dataclass(frozen=True)
class AssetRecord:
    asset_key: str
    category: str
    language_dimension: str
    status: str
    textless_pending: bool
    model_scope: tuple[str, ...]
    export_root: Path | None
    language_variants: tuple[str, ...]
    hashes: tuple[tuple[str, str], ...]
    notes: str

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
    return AssetRecord(
        asset_key=asset_key,
        category=(row.get("类别") or "").strip(),
        language_dimension=(row.get("语言维度") or "").strip(),
        status=status,
        textless_pending=(row.get("待无字化") or "").strip().upper() in {"TRUE", "YES", "Y", "1"},
        model_scope=_split_values(row.get("适用机型", "")),
        export_root=_parse_export_root(row.get("导出物路径", ""), asset_key=asset_key),
        language_variants=_split_values(row.get("语言变体", "")),
        hashes=_parse_hashes(row.get("内容哈希", ""), asset_key=asset_key),
        notes=(row.get("备注") or "").strip(),
    )


def load_registry(path: Path) -> tuple[AssetRecord, ...]:
    """Load the CSV registry and fail closed on schema or key errors."""

    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = tuple(reader.fieldnames or ())
        missing_columns = [column for column in REQUIRED_COLUMNS if column not in columns]
        if missing_columns:
            raise AssetRegistryError(
                f"asset registry {path} is missing columns: {', '.join(missing_columns)}"
            )
        records: list[AssetRecord] = []
        seen: set[str] = set()
        for row in reader:
            record = _record_from_row(row)
            if record.asset_key in seen:
                raise AssetRegistryError(f"duplicate asset_key: {record.asset_key}")
            seen.add(record.asset_key)
            records.append(record)
    return tuple(records)


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
        filename = _artifact_filename(record, label, language)
        if not filename:
            continue
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
        matches.append((path, actual_format or "", digest))
    return matches


def _model_matches(record: AssetRecord, model: str | None) -> bool:
    if not model or not record.model_scope:
        return True
    scope = {value.upper() for value in record.model_scope}
    return "ALL" in scope or model.upper() in scope


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

    del region  # Region-specificity is represented by model scope today.
    record = next((item for item in records if item.asset_key == asset_key), None)
    if record is None:
        raise AssetRegistryError(f"asset not registered: {asset_key}")
    if not _model_matches(record, model):
        raise AssetRegistryError(f"asset {asset_key} is not registered for model {model}")
    if record.status != APPROVED_STATUS and not (allow_temporary and record.status == TEMPORARY_STATUS):
        raise AssetRegistryError(
            f"asset {asset_key} is {record.status}; only {APPROVED_STATUS} assets are importable"
        )
    candidates = _matching_artifacts(
        record,
        repo_root=repo_root,
        format_name=format_name,
        language=language,
    )
    existing = [candidate for candidate in candidates if candidate[0].is_file()]
    if not existing:
        requested = format_name or "any format"
        raise AssetRegistryError(f"asset {asset_key} has no existing export for {requested}")
    path, actual_format, digest = existing[0]
    return AssetResolution(
        asset_key=asset_key,
        path=str(path.relative_to(repo_root)),
        format=actual_format,
        status=record.status,
        content_hash=digest,
        language=language,
        source="registry-export",
    )


def _hash_matches(path: Path, expected: str) -> bool:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest.startswith(expected.lower())


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
    selected_records = [record for record in records if not selected_keys or record.asset_key in selected_keys]
    known_keys = {record.asset_key for record in records}
    for key in sorted(selected_keys - known_keys):
        errors.append(AssetIssue("unknown_asset", key, "asset key is not registered"))

    for record in selected_records:
        status_counts[record.status] += 1
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


def run_asset_check(args: argparse.Namespace, *, repo_root: Path) -> None:
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
