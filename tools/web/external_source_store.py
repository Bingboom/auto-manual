"""External source pointer contract, Feishu attachment fetcher, and raw binary ratchet.

Large source originals no longer enter bare Git objects:

- editable Illustrator / print design masters (``.ai``, ``.indd``, ``.idml``,
  ``.psd``) and editable master PDFs belong in the dedicated ``04_资产源文件``
  table (``tblsXlZx61Ff5pQC``) under ``storage_role="asset_sources"``;
- shipped manual PDFs belong in the ``发布文档管理`` Base under
  ``storage_role="published_docs"``;
- repository packages commit small ``*.source-pointer.json`` files (or
  ``external_sources`` entries in ``source_manifest.json``) validated against
  ``external-source-pointer/v1`` and verified by exact byte size + SHA-256 on
  every local check or ``lark-cli base +record-download-attachment`` fetch.

Existing historical raw binaries are frozen in
``data/raw_binary_ratchet_baseline.tsv`` so zero files are deleted and zero Git
history is rewritten in Phase 3A, while any new or grown raw design master,
split ``.bin`` archive chunk, or ``>1 MiB`` PDF fails maintainability guardrails::

    python -m tools.web.external_source_store check
    python -m tools.web.external_source_store update-ratchet [--allow PATH=REASON]
    python -m tools.web.external_source_store create-pointer FILE --storage-role asset_sources ...
    python -m tools.web.external_source_store verify-local POINTER_JSON [--file FILE]
    python -m tools.web.external_source_store fetch POINTER_JSON [--output FILE]
"""

from __future__ import annotations

import argparse
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any

from tools.utils.path_utils import PathSegments
from tools.web.frozen_package_registry import (
    SOURCE_MANIFEST_JSON,
    frozen_source_roots_of,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
POINTER_SCHEMA_VERSION = "external-source-pointer/v1"
POINTER_SUFFIX = ".source-pointer.json"
STORAGE_ROLE_ASSET_SOURCES = "asset_sources"
STORAGE_ROLE_PUBLISHED_DOCS = "published_docs"
STORAGE_ROLES = frozenset({STORAGE_ROLE_ASSET_SOURCES, STORAGE_ROLE_PUBLISHED_DOCS})
ASSET_SOURCES_TABLE_ID = "tblsXlZx61Ff5pQC"
ASSET_BASE_BINDINGS_JSON = "asset_base_bindings.json"
PHASE2_BASE_TOKEN_ENV = "FEISHU_PHASE2_BASE_TOKEN"
PUBLISHED_DOCS_BASE_TOKEN_ENV = "FEISHU_PUBLISHED_DOCS_BASE_TOKEN"

RAW_DESIGN_SUFFIXES = frozenset({".ai", ".indd", ".idml", ".psd"})
RAW_PDF_MAX_BYTES = 1024 * 1024
RATCHET_BASELINE_TSV = "raw_binary_ratchet_baseline.tsv"
PREFIX = "[raw-binary-ratchet]"

_HEX_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_TABLE_ID_RE = re.compile(r"^tbl[A-Za-z0-9]{6,32}$")
_RECORD_ID_RE = re.compile(r"^rec[A-Za-z0-9]{6,32}$")
_FILE_TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]{8,64}$")
_FORBIDDEN_CREDENTIAL_KEYS = frozenset(
    {
        "base_token",
        "app_id",
        "app_secret",
        "access_token",
        "tenant_access_token",
        "user_access_token",
        "authorization",
    }
)
_ALLOWED_TOP_LEVEL_KEYS = frozenset(
    {
        "schema_version",
        "storage_role",
        "file_name",
        "sha256",
        "size_bytes",
        "feishu",
        "local_relpath",
        "source_key",
        "notes",
    }
)
_ALLOWED_FEISHU_KEYS = frozenset(
    {
        "table_id",
        "record_id",
        "field_name",
        "file_token",
    }
)
_SKIP_SCAN_PREFIXES = (
    "docs/_build/",
    "docs/publish/",
    "docs/knowledge/",
    "docs/review-drafts/",
)


@dataclass(frozen=True)
class FeishuAttachmentRef:
    """Bitable attachment coordinates (without tenant/base secret tokens)."""

    table_id: str
    record_id: str
    field_name: str
    file_token: str


@dataclass(frozen=True)
class ExternalSourcePointer:
    """Validated ``external-source-pointer/v1`` record."""

    storage_role: str
    file_name: str
    sha256: str
    size_bytes: int
    feishu: FeishuAttachmentRef
    local_relpath: str | None = None
    source_key: str | None = None
    notes: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema_version": POINTER_SCHEMA_VERSION,
            "storage_role": self.storage_role,
            "file_name": self.file_name,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "feishu": {
                "table_id": self.feishu.table_id,
                "record_id": self.feishu.record_id,
                "field_name": self.feishu.field_name,
                "file_token": self.feishu.file_token,
            },
        }
        if self.local_relpath:
            payload["local_relpath"] = self.local_relpath
        if self.source_key:
            payload["source_key"] = self.source_key
        if self.notes:
            payload["notes"] = self.notes
        return payload


@dataclass(frozen=True)
class RawBinaryRecord:
    """One tracked raw design/archive/large-PDF file or baseline ceiling."""

    path: str
    size_bytes: int
    kind: str
    reason: str = ""


@dataclass(frozen=True)
class RatchetCheckResult:
    """Outcome of checking tracked raw binaries and committed pointers."""

    baselined_count: int = 0
    pointer_count: int = 0
    new_files: tuple[RawBinaryRecord, ...] = ()
    grown_files: tuple[ tuple[RawBinaryRecord, int], ... ] = ()
    stale_paths: tuple[str, ...] = ()
    invalid_pointers: tuple[str, ...] = ()
    baseline_missing: bool = False

    @property
    def exit_code(self) -> int:
        if self.baseline_missing:
            return 2
        failed = (
            self.new_files
            or self.grown_files
            or self.stale_paths
            or self.invalid_pointers
        )
        return 1 if failed else 0


def ratchet_baseline_of(repo_root: Path) -> Path:
    return repo_root / PathSegments.DATA / RATCHET_BASELINE_TSV


def asset_base_bindings_of(repo_root: Path) -> Path:
    return repo_root / PathSegments.DATA / ASSET_BASE_BINDINGS_JSON


def sha256_file(path: Path) -> tuple[int, str]:
    """Stream ``path`` and return ``(size_bytes, lowercase_sha256)``."""
    digest = hashlib.sha256()
    total = 0
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            digest.update(chunk)
    return total, digest.hexdigest()


def _validate_safe_basename(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label}: file_name must be a non-empty string")
    cleaned = value.strip()
    if (
        "/" in cleaned
        or "\\" in cleaned
        or cleaned in {".", ".."}
        or Path(cleaned).name != cleaned
    ):
        raise ValueError(f"{label}: file_name must be a bare filename without path segments")
    return cleaned


def _validate_safe_relpath(value: object, label: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label}: local_relpath must be a non-empty string when present")
    cleaned = value.strip().replace("\\", "/")
    parts = cleaned.split("/")
    if cleaned.startswith("/") or any(part in {"", ".", ".."} for part in parts):
        raise ValueError(f"{label}: local_relpath must stay relative without '..'")
    return cleaned


def _reject_credential_keys(mapping: Mapping[str, Any], label: str, allowed: frozenset[str]) -> None:
    for raw_key in mapping:
        key = str(raw_key)
        lowered = key.lower()
        if lowered in _FORBIDDEN_CREDENTIAL_KEYS or lowered.endswith("_secret"):
            raise ValueError(f"{label}: forbidden credential/base key {key!r} must not be stored in Git")
        if key not in allowed:
            raise ValueError(f"{label}: unsupported key {key!r}")


def _validate_feishu_section(raw: object, storage_role: str, label: str) -> FeishuAttachmentRef:
    if not isinstance(raw, Mapping):
        raise ValueError(f"{label}: feishu must be a JSON object")
    _reject_credential_keys(raw, f"{label}.feishu", _ALLOWED_FEISHU_KEYS)
    table_id = str(raw.get("table_id") or "").strip()
    record_id = str(raw.get("record_id") or "").strip()
    field_name = str(raw.get("field_name") or "").strip()
    file_token = str(raw.get("file_token") or "").strip()
    if not _TABLE_ID_RE.match(table_id):
        raise ValueError(f"{label}: feishu.table_id must match tbl... (got {table_id!r})")
    if storage_role == STORAGE_ROLE_ASSET_SOURCES and table_id != ASSET_SOURCES_TABLE_ID:
        raise ValueError(
            f"{label}: asset_sources pointers must bind table_id={ASSET_SOURCES_TABLE_ID!r} "
            f"(got {table_id!r})"
        )
    if not _RECORD_ID_RE.match(record_id):
        raise ValueError(f"{label}: feishu.record_id must match rec... (got {record_id!r})")
    if not field_name:
        raise ValueError(f"{label}: feishu.field_name must be non-empty")
    if not _FILE_TOKEN_RE.match(file_token):
        raise ValueError(f"{label}: feishu.file_token must be an 8-64 char alphanumeric resource token")
    return FeishuAttachmentRef(
        table_id=table_id,
        record_id=record_id,
        field_name=field_name,
        file_token=file_token,
    )


def _optional_clean_str(mapping: Mapping[str, Any], key: str, label: str) -> str | None:
    value = mapping.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label}: {key} must be a non-empty string when present")
    return value.strip()


def validate_pointer_payload(payload: object, source_label: str = "<pointer>") -> ExternalSourcePointer:
    """Validate and parse an ``external-source-pointer/v1`` mapping."""
    if not isinstance(payload, Mapping):
        raise ValueError(f"{source_label}: pointer must be a JSON object")
    _reject_credential_keys(payload, source_label, _ALLOWED_TOP_LEVEL_KEYS)
    if payload.get("schema_version") != POINTER_SCHEMA_VERSION:
        raise ValueError(f"{source_label}: schema_version must be {POINTER_SCHEMA_VERSION!r}")
    role = str(payload.get("storage_role") or "").strip()
    if role not in STORAGE_ROLES:
        raise ValueError(
            f"{source_label}: storage_role must be one of {sorted(STORAGE_ROLES)} (got {role!r})"
        )
    file_name = _validate_safe_basename(payload.get("file_name"), source_label)
    sha256 = str(payload.get("sha256") or "").strip()
    if not _HEX_SHA256_RE.match(sha256):
        raise ValueError(f"{source_label}: sha256 must be 64 lowercase hex characters")
    size_bytes = payload.get("size_bytes")
    if isinstance(size_bytes, bool) or not isinstance(size_bytes, int) or size_bytes <= 0:
        raise ValueError(f"{source_label}: size_bytes must be a positive integer")
    feishu = _validate_feishu_section(payload.get("feishu"), role, source_label)
    return ExternalSourcePointer(
        storage_role=role,
        file_name=file_name,
        sha256=sha256,
        size_bytes=size_bytes,
        feishu=feishu,
        local_relpath=_validate_safe_relpath(payload.get("local_relpath"), source_label),
        source_key=_optional_clean_str(payload, "source_key", source_label),
        notes=_optional_clean_str(payload, "notes", source_label),
    )


def load_pointer_file(path: Path) -> ExternalSourcePointer:
    """Load and validate a ``*.source-pointer.json`` file from disk."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{path}: unreadable pointer JSON: {exc}") from exc
    return validate_pointer_payload(raw, str(path))


def write_pointer_file(path: Path, pointer: ExternalSourcePointer) -> Path:
    """Write ``pointer`` with canonical 2-space indentation so ``file_token`` stays on its own line."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(pointer.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def _scan_pointer_files(repo_root: Path) -> tuple[list[ExternalSourcePointer], list[str]]:
    pointers: list[ExternalSourcePointer] = []
    errors: list[str] = []
    scan_roots = (*frozen_source_roots_of(repo_root), repo_root / PathSegments.DOCS)
    for scan_root in scan_roots:
        if not scan_root.is_dir():
            continue
        for path in sorted(scan_root.rglob(f"*{POINTER_SUFFIX}")):
            rel = path.relative_to(repo_root).as_posix()
            if any(rel.startswith(prefix) for prefix in _SKIP_SCAN_PREFIXES):
                continue
            try:
                pointers.append(load_pointer_file(path))
            except ValueError as exc:
                errors.append(f"{rel}: {exc}")
    return pointers, errors


def _scan_manifest_pointers(repo_root: Path) -> tuple[list[ExternalSourcePointer], list[str]]:
    pointers: list[ExternalSourcePointer] = []
    errors: list[str] = []
    for root in frozen_source_roots_of(repo_root):
        if not root.is_dir():
            continue
        for manifest_path in sorted(root.rglob(SOURCE_MANIFEST_JSON)):
            rel = manifest_path.relative_to(repo_root).as_posix()
            try:
                data = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                continue
            if not isinstance(data, Mapping) or "external_sources" not in data:
                continue
            entries = data.get("external_sources")
            if not isinstance(entries, list):
                errors.append(f"{rel}: external_sources must be a list")
                continue
            for idx, item in enumerate(entries):
                try:
                    pointers.append(validate_pointer_payload(item, f"{rel}#external_sources[{idx}]"))
                except ValueError as exc:
                    errors.append(str(exc))
    return pointers, errors


def discover_pointers(repo_root: Path) -> tuple[tuple[ExternalSourcePointer, ...], tuple[str, ...]]:
    """Return ``(valid_pointers, error_messages)`` across the repository."""
    file_ptrs, file_errs = _scan_pointer_files(repo_root)
    manifest_ptrs, manifest_errs = _scan_manifest_pointers(repo_root)
    return tuple([*file_ptrs, *manifest_ptrs]), tuple([*file_errs, *manifest_errs])


def count_package_external_sources(
    package_dir: Path,
    manifest: Mapping[str, Any] | None = None,
) -> int:
    """Count standalone ``*.source-pointer.json`` files plus ``external_sources`` manifest entries."""
    file_count = sum(
        1
        for path in package_dir.rglob(f"*{POINTER_SUFFIX}")
        if path.is_file() and "__pycache__" not in path.parts
    )
    manifest_entries = manifest.get("external_sources") if isinstance(manifest, Mapping) else None
    inline_count = len(manifest_entries) if isinstance(manifest_entries, list) else 0
    return file_count + inline_count


def classify_raw_binary(rel_path: str, size_bytes: int) -> str | None:
    """Return the raw-binary class when ``rel_path`` is governed by the ratchet, else ``None``."""
    if any(rel_path.startswith(prefix) for prefix in _SKIP_SCAN_PREFIXES):
        return None
    suffix = Path(rel_path).suffix.lower()
    if suffix in RAW_DESIGN_SUFFIXES:
        return "design-master"
    if suffix == ".bin" and rel_path.startswith(("manual_sources/", "data/manual_sources/")):
        return "archive-chunk"
    if suffix == ".pdf" and size_bytes > RAW_PDF_MAX_BYTES:
        return "large-pdf"
    return None


def _iter_candidate_files(repo_root: Path) -> list[str]:
    if (repo_root / ".git").exists():
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "-c", "core.quotepath=false", "ls-files", "-z"],
            capture_output=True,
            check=True,
        )
        return sorted(
            raw.decode("utf-8")
            for raw in proc.stdout.split(b"\0")
            if raw
        )
    rels: list[str] = []
    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue
        if ".git" in path.parts or "__pycache__" in path.parts:
            continue
        rels.append(path.relative_to(repo_root).as_posix())
    return sorted(rels)


def collect_tracked_raw_binaries(repo_root: Path) -> dict[str, RawBinaryRecord]:
    """Collect governed raw binaries currently tracked in ``repo_root``."""
    found: dict[str, RawBinaryRecord] = {}
    for rel in _iter_candidate_files(repo_root):
        full = repo_root / rel
        if not full.is_file():
            continue
        size = full.stat().st_size
        kind = classify_raw_binary(rel, size)
        if kind is not None:
            found[rel] = RawBinaryRecord(path=rel, size_bytes=size, kind=kind)
    return found


def load_ratchet_baseline(path: Path) -> dict[str, RawBinaryRecord] | None:
    """Load ``data/raw_binary_ratchet_baseline.tsv`` (``path\\tmax_bytes\\treason``)."""
    if not path.exists():
        return None
    records: dict[str, RawBinaryRecord] = {}
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = raw.split("\t")
        if len(parts) < 2:
            raise ValueError(f"{path}:{line_no}: expected 'path\\tmax_bytes[\\treason]'")
        rel = parts[0].strip()
        try:
            max_bytes = int(parts[1].strip())
        except ValueError as exc:
            raise ValueError(f"{path}:{line_no}: invalid integer max_bytes {parts[1]!r}") from exc
        reason = parts[2].strip() if len(parts) >= 3 else ""
        records[rel] = RawBinaryRecord(path=rel, size_bytes=max_bytes, kind="baselined", reason=reason)
    return records


def write_ratchet_baseline(path: Path, records: Mapping[str, RawBinaryRecord]) -> Path:
    header = (
        "# Tracked raw design masters (.ai/.indd/.idml/.psd), manual_sources .bin chunks,\n"
        "# and >1 MiB PDFs frozen at Phase 3A. This baseline may only shrink.\n"
        "# Store new originals in Feishu (04_资产源文件 or 发布文档管理) and commit a\n"
        "# *.source-pointer.json file instead.\n"
        "# Columns: path\tmax_bytes\treason\n"
    )
    rows = "".join(
        f"{rel}\t{records[rel].size_bytes}"
        + (f"\t{records[rel].reason}" if records[rel].reason else "")
        + "\n"
        for rel in sorted(records)
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(header + rows, encoding="utf-8")
    return path


def _print_ratchet_failures(result: RatchetCheckResult, printer: Callable[[str], None]) -> None:
    for item in result.new_files:
        printer(
            f"{PREFIX} NEW {item.path} ({item.kind}, {item.size_bytes} bytes): "
            "bare Git raw originals are closed; upload to Feishu (04_资产源文件 or 发布文档管理) "
            f"and commit a *{POINTER_SUFFIX} pointer instead"
        )
    for item, ceiling in result.grown_files:
        printer(
            f"{PREFIX} GROWN {item.path}: {item.size_bytes} bytes > baseline {ceiling} bytes"
        )
    for rel in result.stale_paths:
        printer(
            f"{PREFIX} STALE {rel}: file removed or shrunk; lock in the reduction with "
            "`python -m tools.web.external_source_store update-ratchet`"
        )
    for problem in result.invalid_pointers:
        printer(f"{PREFIX} INVALID POINTER {problem}")


def check_repository(
    repo_root: Path = REPO_ROOT,
    *,
    baseline_path: Path | None = None,
    printer: Callable[[str], None] = print,
) -> RatchetCheckResult:
    """Validate raw-binary ratchet baseline and all ``external-source-pointer/v1`` pointers."""
    path = baseline_path or ratchet_baseline_of(repo_root)
    baseline = load_ratchet_baseline(path)
    if baseline is None:
        printer(f"{PREFIX} ERROR missing baseline: {path}")
        return RatchetCheckResult(baseline_missing=True)

    current = collect_tracked_raw_binaries(repo_root)
    pointers, pointer_errors = discover_pointers(repo_root)

    new_files = tuple(current[rel] for rel in sorted(current) if rel not in baseline)
    grown_files = tuple(
        (current[rel], baseline[rel].size_bytes)
        for rel in sorted(current)
        if rel in baseline and current[rel].size_bytes > baseline[rel].size_bytes
    )
    stale_paths = tuple(
        sorted(
            rel
            for rel, base in baseline.items()
            if rel not in current or current[rel].size_bytes < base.size_bytes
        )
    )
    result = RatchetCheckResult(
        baselined_count=len(baseline),
        pointer_count=len(pointers),
        new_files=new_files,
        grown_files=grown_files,
        stale_paths=stale_paths,
        invalid_pointers=pointer_errors,
    )
    _print_ratchet_failures(result, printer)
    printer(
        f"{PREFIX} {len(result.new_files)} new, {len(result.grown_files)} grown, "
        f"{len(result.stale_paths)} stale, {result.baselined_count} baselined, "
        f"{result.pointer_count} pointer(s) valid"
    )
    return result


def parse_allow_specs(specs: Iterable[str]) -> dict[str, str]:
    allowed: dict[str, str] = {}
    for raw in specs:
        if "=" not in raw:
            raise ValueError(f"--allow expects PATH=REASON (got {raw!r})")
        rel, reason = raw.split("=", 1)
        rel_clean = rel.strip().replace("\\", "/")
        reason_clean = reason.strip()
        if not rel_clean or not reason_clean:
            raise ValueError(f"--allow requires both non-empty PATH and REASON (got {raw!r})")
        allowed[rel_clean] = reason_clean
    return allowed


def update_ratchet_baseline(
    repo_root: Path,
    *,
    baseline_path: Path | None = None,
    allow_reasons: Mapping[str, str] | None = None,
    seed_reason: str | None = None,
) -> Path:
    """Write shrunk/remaining entries back; new or grown files require explicit ``allow_reasons``."""
    path = baseline_path or ratchet_baseline_of(repo_root)
    existing = load_ratchet_baseline(path) or {}
    current = collect_tracked_raw_binaries(repo_root)
    allow = dict(allow_reasons or {})
    updated: dict[str, RawBinaryRecord] = {}

    for rel, record in sorted(current.items()):
        prev = existing.get(rel)
        if prev is None:
            reason = allow.get(rel) or (seed_reason.strip() if seed_reason else "")
            if not reason:
                raise ValueError(
                    f"{rel}: unbaselined raw binary cannot enter baseline without --allow {rel}=REASON"
                )
            updated[rel] = RawBinaryRecord(rel, record.size_bytes, record.kind, reason)
            continue
        if record.size_bytes > prev.size_bytes and rel not in allow:
            raise ValueError(
                f"{rel}: grew from {prev.size_bytes} to {record.size_bytes} bytes; growth is forbidden"
            )
        reason = allow.get(rel, prev.reason)
        updated[rel] = RawBinaryRecord(rel, record.size_bytes, record.kind, reason)

    return write_ratchet_baseline(path, updated)


def resolve_pointer_target_path(
    pointer_path: Path,
    pointer: ExternalSourcePointer,
    explicit_path: Path | None = None,
) -> Path:
    if explicit_path is not None:
        return explicit_path
    if pointer.local_relpath:
        return pointer_path.parent / pointer.local_relpath
    return pointer_path.parent / pointer.file_name


def verify_local_file(pointer: ExternalSourcePointer, file_path: Path) -> tuple[bool, str]:
    """Verify ``file_path`` exists and matches ``pointer.size_bytes`` + ``pointer.sha256``."""
    if not file_path.is_file():
        return False, f"missing local file: {file_path}"
    actual_size, actual_sha = sha256_file(file_path)
    if actual_size != pointer.size_bytes:
        return False, f"{file_path}: size mismatch (expected {pointer.size_bytes}, got {actual_size})"
    if actual_sha != pointer.sha256:
        return False, f"{file_path}: sha256 mismatch (expected {pointer.sha256}, got {actual_sha})"
    return True, f"verified {file_path} ({actual_size} bytes, sha256={actual_sha})"


def resolve_base_token(
    storage_role: str,
    repo_root: Path = REPO_ROOT,
    explicit_token: str | None = None,
    environ: Mapping[str, str] | None = None,
) -> str:
    """Resolve the Feishu ``base_token`` for ``storage_role`` without storing secrets in pointers."""
    if explicit_token and explicit_token.strip():
        return explicit_token.strip()
    env = environ if environ is not None else os.environ
    if storage_role == STORAGE_ROLE_ASSET_SOURCES:
        from_env = env.get(PHASE2_BASE_TOKEN_ENV, "").strip()
        if from_env:
            return from_env
        bindings_path = asset_base_bindings_of(repo_root)
        try:
            bindings = json.loads(bindings_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"cannot read {bindings_path} for asset_sources base_token: {exc}") from exc
        base = bindings.get("base") if isinstance(bindings, Mapping) else None
        token = str(base.get("base_token") or "").strip() if isinstance(base, Mapping) else ""
        if token:
            return token
        raise ValueError(
            f"missing base_token for asset_sources: set ${PHASE2_BASE_TOKEN_ENV} or pass --base-token"
        )
    if storage_role == STORAGE_ROLE_PUBLISHED_DOCS:
        from_env = env.get(PUBLISHED_DOCS_BASE_TOKEN_ENV, "").strip()
        if from_env:
            return from_env
        raise ValueError(
            f"missing base_token for published_docs: set ${PUBLISHED_DOCS_BASE_TOKEN_ENV} or pass --base-token"
        )
    raise ValueError(f"unsupported storage_role: {storage_role!r}")


def build_lark_download_command(
    pointer: ExternalSourcePointer,
    *,
    base_token: str,
    output_path: Path | str,
    lark_bin: str = "lark-cli",
    identity: str = "bot",
    profile: str | None = None,
) -> list[str]:
    cmd = [lark_bin]
    if profile:
        cmd.extend(["--profile", profile])
    cmd.extend(
        [
            "base",
            "+record-download-attachment",
            "--as",
            identity,
            "--base-token",
            base_token,
            "--table-id",
            pointer.feishu.table_id,
            "--record-id",
            pointer.feishu.record_id,
            "--file-token",
            pointer.feishu.file_token,
            "--output",
            str(output_path),
            "--overwrite",
        ]
    )
    return cmd


def fetch_pointer_attachment(
    pointer: ExternalSourcePointer,
    output_path: Path,
    *,
    base_token: str,
    lark_bin: str = "lark-cli",
    identity: str = "bot",
    profile: str | None = None,
    force: bool = False,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> Path:
    """Download ``pointer`` via ``lark-cli`` into a temp file, verify SHA-256, and atomically replace."""
    resolved_output = output_path.resolve()
    if resolved_output.is_file() and not force:
        ok, message = verify_local_file(pointer, resolved_output)
        if ok:
            return output_path
        raise RuntimeError(f"refusing to overwrite modified file without --force ({message})")

    resolved_output.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{resolved_output.name}.",
        suffix=".part",
        dir=str(resolved_output.parent),
    )
    os.close(fd)
    tmp_path = Path(tmp_name)
    try:
        # lark-cli 1.0.69 requires a cwd-relative --output path (rejects /var/folders/...).
        cmd = build_lark_download_command(
            pointer,
            base_token=base_token,
            output_path=f"./{tmp_path.name}",
            lark_bin=lark_bin,
            identity=identity,
            profile=profile,
        )
        proc = runner(
            cmd,
            cwd=str(resolved_output.parent),
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "").strip()
            raise RuntimeError(
                f"lark-cli attachment download failed (exit {proc.returncode}): {detail}"
            )
        ok, message = verify_local_file(pointer, tmp_path)
        if not ok:
            raise RuntimeError(f"downloaded attachment failed integrity check: {message}")
        os.replace(tmp_path, resolved_output)
    except (OSError, subprocess.SubprocessError, RuntimeError):
        tmp_path.unlink(missing_ok=True)
        raise
    return output_path


def create_pointer_from_file(
    local_file: Path,
    *,
    storage_role: str,
    record_id: str,
    field_name: str,
    file_token: str,
    table_id: str | None = None,
    local_relpath: str | None = None,
    source_key: str | None = None,
    notes: str | None = None,
) -> ExternalSourcePointer:
    """Hash ``local_file`` and construct a validated ``ExternalSourcePointer``."""
    if not local_file.is_file():
        raise ValueError(f"source file does not exist: {local_file}")
    resolved_table = table_id or (
        ASSET_SOURCES_TABLE_ID if storage_role == STORAGE_ROLE_ASSET_SOURCES else ""
    )
    size_bytes, digest = sha256_file(local_file)
    payload: dict[str, Any] = {
        "schema_version": POINTER_SCHEMA_VERSION,
        "storage_role": storage_role,
        "file_name": local_file.name,
        "sha256": digest,
        "size_bytes": size_bytes,
        "feishu": {
            "table_id": resolved_table,
            "record_id": record_id,
            "field_name": field_name,
            "file_token": file_token,
        },
    }
    if local_relpath:
        payload["local_relpath"] = local_relpath
    if source_key:
        payload["source_key"] = source_key
    if notes:
        payload["notes"] = notes
    return validate_pointer_payload(payload, str(local_file))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("check", help="check raw-binary ratchet and external source pointers")

    upd = sub.add_parser("update-ratchet", help="shrink raw-binary baseline or allow explicit exceptions")
    upd.add_argument("--allow", action="append", default=[], metavar="PATH=REASON")

    create = sub.add_parser("create-pointer", help="create a validated *.source-pointer.json from a local file")
    create.add_argument("local_file", type=Path)
    create.add_argument("--storage-role", required=True, choices=sorted(STORAGE_ROLES))
    create.add_argument("--table-id", help="Bitable table_id (defaults to tblsXlZx61Ff5pQC for asset_sources)")
    create.add_argument("--record-id", required=True)
    create.add_argument("--field-name", required=True)
    create.add_argument("--file-token", required=True)
    create.add_argument("--local-relpath")
    create.add_argument("--source-key")
    create.add_argument("--notes")
    create.add_argument("--output", type=Path, help=f"output pointer path (default: <file>{POINTER_SUFFIX})")

    verify = sub.add_parser("verify-local", help="verify a local file against its pointer JSON")
    verify.add_argument("pointer_json", type=Path)
    verify.add_argument("--file", type=Path, dest="target_file")

    fetch = sub.add_parser("fetch", help="download attachment from Feishu and verify SHA-256")
    fetch.add_argument("pointer_json", type=Path)
    fetch.add_argument("--output", type=Path)
    fetch.add_argument("--base-token")
    fetch.add_argument("--as", dest="identity", choices=("bot", "user"), default="bot")
    fetch.add_argument("--profile")
    fetch.add_argument("--lark-bin", default="lark-cli")
    fetch.add_argument("--force", action="store_true")
    return parser


def _run_create_pointer(args: argparse.Namespace) -> int:
    pointer = create_pointer_from_file(
        args.local_file,
        storage_role=args.storage_role,
        table_id=args.table_id,
        record_id=args.record_id,
        field_name=args.field_name,
        file_token=args.file_token,
        local_relpath=args.local_relpath,
        source_key=args.source_key,
        notes=args.notes,
    )
    out = args.output or Path(f"{args.local_file}{POINTER_SUFFIX}")
    write_pointer_file(out, pointer)
    print(f"{PREFIX} wrote pointer {out} ({pointer.size_bytes} bytes, sha256={pointer.sha256})")
    return 0


def _run_verify_local(args: argparse.Namespace) -> int:
    pointer = load_pointer_file(args.pointer_json)
    target = resolve_pointer_target_path(args.pointer_json, pointer, args.target_file)
    ok, message = verify_local_file(pointer, target)
    stream = sys.stdout if ok else sys.stderr
    print(f"{PREFIX} {message}", file=stream)
    return 0 if ok else 1


def _run_fetch(args: argparse.Namespace, repo_root: Path) -> int:
    pointer = load_pointer_file(args.pointer_json)
    target = resolve_pointer_target_path(args.pointer_json, pointer, args.output)
    token = resolve_base_token(pointer.storage_role, repo_root=repo_root, explicit_token=args.base_token)
    written = fetch_pointer_attachment(
        pointer,
        target,
        base_token=token,
        lark_bin=args.lark_bin,
        identity=args.identity,
        profile=args.profile,
        force=args.force,
    )
    print(f"{PREFIX} fetched and verified {written} ({pointer.size_bytes} bytes, sha256={pointer.sha256})")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    repo_root = args.repo_root.resolve()
    if args.command in (None, "check"):
        return check_repository(repo_root).exit_code
    try:
        if args.command == "update-ratchet":
            allow = parse_allow_specs(args.allow)
            path = update_ratchet_baseline(repo_root, allow_reasons=allow)
            print(f"{PREFIX} updated {path.relative_to(repo_root).as_posix()}")
            return 0
        if args.command == "create-pointer":
            return _run_create_pointer(args)
        if args.command == "verify-local":
            return _run_verify_local(args)
        return _run_fetch(args, repo_root)
    except ValueError as exc:
        print(f"{PREFIX} ERROR {exc}", file=sys.stderr)
        return 2
    except RuntimeError as exc:
        print(f"{PREFIX} ERROR {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
