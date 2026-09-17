"""Seal and verify evidence for explicit-language Web release inputs."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import shutil
from typing import Any, Iterable

from tools.lang_registry import canonical_language
from tools.safe_copy import assert_source_tree_no_symlinks
from tools.utils.path_utils import PathSegments


PROJECTION_SCHEMA_VERSION = "web-language-bundle/v1"
RECEIPT_SCHEMA_VERSION = "auto-manual-web-language-release-evidence/v1"
PROJECTION_MANIFEST_FILENAME = "projection_bundle_manifest.json"
RECEIPT_FILENAME = "language_projection_receipt.json"
_ACTIONS = ("check", "md", "html")
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_INCLUDE_RE = re.compile(
    r"^[ \t]*\.\.[ \t]+include::[ \t]+(.+?)[ \t]*$", re.MULTILINE
)


@dataclass(frozen=True)
class ProjectionCapture:
    action: str
    manifest_path: Path
    manifest_sha256: str
    source_files: tuple[dict[str, Any], ...]
    source_sha256: str
    model: str
    region: str
    language: str

    @property
    def fingerprint(self) -> str:
        return _projection_fingerprint(self.manifest_sha256, self.source_sha256)


@dataclass(frozen=True)
class VerifiedLanguageReleaseEvidence:
    path: Path
    sha256: str
    model: str
    region: str
    language: str
    projection_manifest_sha256: str


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_sha256(value: Any) -> str:
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _projection_fingerprint(manifest_sha256: str, source_sha256: str) -> str:
    return _json_sha256(
        {"manifest_sha256": manifest_sha256, "source_sha256": source_sha256}
    )


def _load_object(path: Path, *, label: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise RuntimeError(f"{label} must be a real file: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cannot read {label}: {path}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"{label} root must be an object: {path}")
    return payload


def _required_text(payload: dict[str, Any], field: str, *, source: Path) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(f"language evidence missing {field}: {source}")
    return value.strip()


def _required_sha(value: Any, *, field: str, source: Path) -> str:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise RuntimeError(f"language evidence has invalid {field}: {source}")
    return value


def _safe_relative(raw: Any, *, field: str, source: Path) -> Path:
    if not isinstance(raw, str) or not raw.strip():
        raise RuntimeError(f"language evidence has invalid {field}: {source}")
    path = Path(raw)
    if path.is_absolute() or ".." in path.parts or path.as_posix() != raw:
        raise RuntimeError(f"language evidence has unsafe {field}: {source}")
    return path


def _file_inventory(root: Path, *, excluded_roots: Iterable[Path] = ()) -> tuple[dict[str, Any], ...]:
    if root.is_symlink() or not root.is_dir():
        raise RuntimeError(f"language evidence inventory root must be a real directory: {root}")
    assert_source_tree_no_symlinks(root, label="Web language evidence input")
    excluded = {path.resolve(strict=False) for path in excluded_roots}
    records: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        if not path.is_file():
            continue
        resolved = path.resolve(strict=True)
        if any(resolved == item or resolved.is_relative_to(item) for item in excluded):
            continue
        records.append(
            {
                "path": path.relative_to(root).as_posix(),
                "size": path.stat().st_size,
                "sha256": _sha256(path),
            }
        )
    if not records:
        raise RuntimeError(f"language evidence inventory is empty: {root}")
    return tuple(records)


def _inventory_paths(root: Path, paths: Iterable[Path]) -> tuple[dict[str, Any], ...]:
    records = []
    for path in sorted(set(paths), key=lambda item: item.relative_to(root).as_posix()):
        records.append(
            {
                "path": path.relative_to(root).as_posix(),
                "size": path.stat().st_size,
                "sha256": _sha256(path),
            }
        )
    return tuple(records)


def _canonical_source_closure(
    bundle_root: Path, *, projection_payload: dict[str, Any]
) -> tuple[dict[str, Any], ...]:
    assert_source_tree_no_symlinks(bundle_root, label="Web language projection")
    index_path = bundle_root / "index.rst"
    try:
        index_includes = _INCLUDE_RE.findall(index_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError) as exc:
        raise RuntimeError(f"cannot read canonical Web language index: {index_path}") from exc
    expected_pages = [str(row["path"]) for row in projection_payload["pages"]]
    if index_includes != expected_pages:
        raise RuntimeError(
            "canonical Web language index does not match projection page order: "
            f"{index_path}"
        )
    seeds = [bundle_root / "index.rst"] + [
        bundle_root / str(row["path"]) for row in projection_payload["pages"]
    ]
    pending = list(seeds)
    seen: set[Path] = set()
    while pending:
        candidate = pending.pop()
        try:
            path = candidate.resolve(strict=True)
            path.relative_to(bundle_root.resolve(strict=True))
        except (FileNotFoundError, ValueError) as exc:
            raise RuntimeError(f"Web language projection include escapes or is missing: {candidate}") from exc
        if path in seen:
            continue
        if not path.is_file():
            raise RuntimeError(f"Web language projection include is not a file: {path}")
        seen.add(path)
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise RuntimeError(f"cannot read Web language projection include: {path}") from exc
        for raw in _INCLUDE_RE.findall(text):
            reference = Path(raw)
            if reference.is_absolute():
                raise RuntimeError(f"Web language projection include is unsafe: {raw}")
            pending.append(path.parent / reference)
    return _inventory_paths(bundle_root.resolve(strict=True), seen)


def _validated_inventory(raw: Any, *, field: str, source: Path) -> tuple[dict[str, Any], ...]:
    if not isinstance(raw, list) or not raw:
        raise RuntimeError(f"language evidence has invalid {field}: {source}")
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            raise RuntimeError(f"language evidence has invalid {field} row: {source}")
        relative = _safe_relative(item.get("path"), field=f"{field}.path", source=source)
        key = relative.as_posix()
        size = item.get("size")
        if key in seen or not isinstance(size, int) or isinstance(size, bool) or size < 0:
            raise RuntimeError(f"language evidence has invalid {field} row: {source}")
        seen.add(key)
        records.append(
            {
                "path": key,
                "size": size,
                "sha256": _required_sha(
                    item.get("sha256"), field=f"{field}.sha256", source=source
                ),
            }
        )
    if records != sorted(records, key=lambda item: item["path"]):
        raise RuntimeError(f"language evidence {field} must be path-sorted: {source}")
    return tuple(records)


def _validate_projection_payload(
    payload: dict[str, Any], *, source: Path, model: str, region: str, language: str
) -> None:
    if payload.get("schema_version") != PROJECTION_SCHEMA_VERSION:
        raise RuntimeError(f"unsupported Web language projection schema: {source}")
    expected = (model, region, canonical_language(language))
    actual = (
        _required_text(payload, "model", source=source),
        _required_text(payload, "region", source=source),
        canonical_language(_required_text(payload, "language", source=source)),
    )
    if not expected[2] or actual != expected:
        raise RuntimeError(
            f"Web language projection identity mismatch: expected {expected}, got {actual}"
        )
    _required_sha(payload.get("source_index_sha256"), field="source_index_sha256", source=source)
    for field in ("source_pages", "pages"):
        rows = payload.get(field)
        if not isinstance(rows, list) or not rows:
            raise RuntimeError(f"Web language projection has invalid {field}: {source}")
        seen: set[str] = set()
        for row in rows:
            if not isinstance(row, dict):
                raise RuntimeError(f"Web language projection has invalid {field} row: {source}")
            relative = _safe_relative(row.get("path"), field=f"{field}.path", source=source)
            key = relative.as_posix()
            if key in seen:
                raise RuntimeError(f"Web language projection has duplicate {field} path: {source}")
            seen.add(key)
            _required_sha(row.get("sha256"), field=f"{field}.sha256", source=source)


def capture_projection(
    manifest_path: Path,
    *,
    action: str,
    model: str,
    region: str,
    language: str,
) -> ProjectionCapture:
    if action not in _ACTIONS:
        raise RuntimeError(f"unsupported Web language evidence action: {action}")
    payload = _load_object(manifest_path, label="Web language projection manifest")
    _validate_projection_payload(
        payload, source=manifest_path, model=model, region=region, language=language
    )
    bundle_root = manifest_path.parent
    source_files = _canonical_source_closure(bundle_root, projection_payload=payload)
    if not source_files or not any(row["path"] == "index.rst" for row in source_files):
        raise RuntimeError(f"Web language projection has no canonical index.rst: {bundle_root}")
    by_path = {str(row["path"]): row for row in source_files}
    for row in payload["pages"]:
        relative = str(row["path"])
        actual = by_path.get(relative)
        if actual is None or actual["sha256"] != row["sha256"]:
            raise RuntimeError(f"Web language projection page hash mismatch: {relative}")
    canonical = canonical_language(language)
    assert canonical is not None
    return ProjectionCapture(
        action=action,
        manifest_path=manifest_path,
        manifest_sha256=_sha256(manifest_path),
        source_files=source_files,
        source_sha256=_json_sha256(source_files),
        model=model,
        region=region,
        language=canonical,
    )


def require_consistent_captures(
    captures: Iterable[ProjectionCapture],
) -> tuple[ProjectionCapture, ProjectionCapture, ProjectionCapture]:
    ordered = tuple(captures)
    if tuple(item.action for item in ordered) != _ACTIONS:
        raise RuntimeError("Web language evidence requires check, md, and html captures in order")
    first = ordered[0]
    if any(
        (item.model, item.region, item.language, item.fingerprint)
        != (first.model, first.region, first.language, first.fingerprint)
        for item in ordered[1:]
    ):
        raise RuntimeError("Web language projection changed across check, md, and html")
    return ordered  # type: ignore[return-value]


def seal_release_evidence(
    *,
    captures: Iterable[ProjectionCapture],
    markdown_dir: Path,
    markdown_name: str,
    html_dir: Path,
    evidence_dir: Path,
    version: str,
    git_ref: str,
) -> Path:
    if not version.strip() or not git_ref.strip():
        raise RuntimeError("Web language release evidence requires version and git_ref")
    checked = require_consistent_captures(captures)
    final = checked[-1]
    recaptured = capture_projection(
        final.manifest_path,
        action="html",
        model=final.model,
        region=final.region,
        language=final.language,
    )
    if recaptured.fingerprint != final.fingerprint:
        raise RuntimeError("Web language projection changed after html capture")
    final = recaptured
    if evidence_dir.exists():
        raise RuntimeError(f"Web language evidence candidate already exists: {evidence_dir}")
    evidence_dir.mkdir(parents=True)
    projection_copy = evidence_dir / PROJECTION_MANIFEST_FILENAME
    shutil.copy2(final.manifest_path, projection_copy)
    markdown_files = _file_inventory(markdown_dir)
    html_files = _file_inventory(html_dir)
    if markdown_name not in {str(item["path"]) for item in markdown_files}:
        raise RuntimeError(f"Web language evidence Markdown manual is missing: {markdown_name}")
    receipt = {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "model": final.model,
        "region": final.region,
        "language": final.language,
        "version": version.strip(),
        "git_ref": git_ref.strip(),
        "actions": {item.action: item.fingerprint for item in checked},
        "projection_manifest": {
            "path": PROJECTION_MANIFEST_FILENAME,
            "sha256": final.manifest_sha256,
        },
        "canonical_source": {
            "sha256": final.source_sha256,
            "files": list(final.source_files),
        },
        "markdown": {
            "manual": markdown_name,
            "sha256": _json_sha256(markdown_files),
            "files": list(markdown_files),
        },
        "html": {
            "sha256": _json_sha256(html_files),
            "files": list(html_files),
        },
    }
    receipt_path = evidence_dir / RECEIPT_FILENAME
    receipt_path.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return receipt_path


def verify_release_evidence(
    receipt_path: Path,
    *,
    expected_sha256: str | None,
    model: str,
    region: str,
    language: str,
    version: str,
    git_ref: str,
    markdown_dir: Path,
    markdown_name: str,
    html_dir: Path | None,
    stored: bool = False,
) -> VerifiedLanguageReleaseEvidence:
    if not stored and html_dir is None:
        raise RuntimeError("fresh Web language release evidence verification requires HTML")
    if receipt_path.name != RECEIPT_FILENAME:
        raise RuntimeError(
            f"Web language release evidence must use {RECEIPT_FILENAME}: {receipt_path}"
        )
    payload = _load_object(receipt_path, label="Web language release evidence")
    receipt_sha256 = _sha256(receipt_path)
    if expected_sha256 is not None and receipt_sha256 != _required_sha(
        expected_sha256, field="receipt_sha256", source=receipt_path
    ):
        raise RuntimeError(f"Web language release evidence SHA-256 mismatch: {receipt_path}")
    if payload.get("schema_version") != RECEIPT_SCHEMA_VERSION:
        raise RuntimeError(f"unsupported Web language release evidence schema: {receipt_path}")
    expected_identity = (model, region, canonical_language(language))
    actual_identity = (
        _required_text(payload, "model", source=receipt_path),
        _required_text(payload, "region", source=receipt_path),
        canonical_language(_required_text(payload, "language", source=receipt_path)),
    )
    if not expected_identity[2] or actual_identity != expected_identity:
        raise RuntimeError(
            f"Web language release evidence identity mismatch: expected {expected_identity}, got {actual_identity}"
        )
    expected_release = (version.strip(), git_ref.strip())
    actual_release = (
        _required_text(payload, "version", source=receipt_path),
        _required_text(payload, "git_ref", source=receipt_path),
    )
    if not all(expected_release) or actual_release != expected_release:
        raise RuntimeError(
            f"Web language release evidence release identity mismatch: "
            f"expected {expected_release}, got {actual_release}"
        )
    actions = payload.get("actions")
    if not isinstance(actions, dict) or set(actions) != set(_ACTIONS):
        raise RuntimeError(f"Web language release evidence has invalid actions: {receipt_path}")
    action_hashes = [
        _required_sha(actions[action], field=f"actions.{action}", source=receipt_path)
        for action in _ACTIONS
    ]
    if len(set(action_hashes)) != 1:
        raise RuntimeError(f"Web language release evidence action digests differ: {receipt_path}")
    projection = payload.get("projection_manifest")
    if not isinstance(projection, dict) or projection.get("path") != PROJECTION_MANIFEST_FILENAME:
        raise RuntimeError(f"Web language release evidence has invalid projection path: {receipt_path}")
    projection_sha256 = _required_sha(
        projection.get("sha256"), field="projection_manifest.sha256", source=receipt_path
    )
    projection_path = receipt_path.parent / PROJECTION_MANIFEST_FILENAME
    if _sha256(projection_path) != projection_sha256:
        raise RuntimeError(f"Web language release projection manifest SHA-256 mismatch: {projection_path}")
    evidence_files = _file_inventory(receipt_path.parent)
    if {item["path"] for item in evidence_files} != {
        RECEIPT_FILENAME,
        PROJECTION_MANIFEST_FILENAME,
    }:
        raise RuntimeError(
            f"Web language release evidence directory has unexpected files: {receipt_path.parent}"
        )
    projection_payload = _load_object(projection_path, label="Web language projection manifest")
    _validate_projection_payload(
        projection_payload,
        source=projection_path,
        model=model,
        region=region,
        language=language,
    )
    canonical = payload.get("canonical_source")
    if not isinstance(canonical, dict):
        raise RuntimeError(f"Web language release evidence has invalid canonical_source: {receipt_path}")
    canonical_files = _validated_inventory(
        canonical.get("files"), field="canonical_source.files", source=receipt_path
    )
    if _json_sha256(canonical_files) != _required_sha(
        canonical.get("sha256"), field="canonical_source.sha256", source=receipt_path
    ):
        raise RuntimeError(f"Web language release canonical RST digest mismatch: {receipt_path}")
    if not any(item["path"] == "index.rst" for item in canonical_files):
        raise RuntimeError(f"Web language release canonical RST lacks index.rst: {receipt_path}")
    canonical_by_path = {str(item["path"]): item for item in canonical_files}
    for page in projection_payload["pages"]:
        recorded = canonical_by_path.get(str(page["path"]))
        if recorded is None or recorded["sha256"] != page["sha256"]:
            raise RuntimeError(
                f"Web language release projection page is detached from canonical source: {receipt_path}"
            )
    expected_fingerprint = _projection_fingerprint(
        projection_sha256,
        _required_sha(
            canonical.get("sha256"), field="canonical_source.sha256", source=receipt_path
        ),
    )
    if any(value != expected_fingerprint for value in action_hashes):
        raise RuntimeError(
            f"Web language release action digest is detached from projection evidence: {receipt_path}"
        )
    markdown = payload.get("markdown")
    if not isinstance(markdown, dict) or markdown.get("manual") != markdown_name:
        raise RuntimeError(f"Web language release evidence Markdown identity mismatch: {receipt_path}")
    recorded_markdown = _validated_inventory(
        markdown.get("files"), field="markdown.files", source=receipt_path
    )
    if _json_sha256(recorded_markdown) != _required_sha(
        markdown.get("sha256"), field="markdown.sha256", source=receipt_path
    ):
        raise RuntimeError(f"Web language release Markdown digest mismatch: {receipt_path}")
    excluded = (
        (receipt_path.parent, markdown_dir / PathSegments.PUBLISH_META_JSON)
        if stored
        else ()
    )
    actual_markdown = _file_inventory(markdown_dir, excluded_roots=excluded)
    if actual_markdown != recorded_markdown:
        raise RuntimeError(f"Web language release Markdown files differ from evidence: {markdown_dir}")
    html = payload.get("html")
    if not isinstance(html, dict):
        raise RuntimeError(f"Web language release evidence has invalid html: {receipt_path}")
    recorded_html = _validated_inventory(html.get("files"), field="html.files", source=receipt_path)
    if _json_sha256(recorded_html) != _required_sha(
        html.get("sha256"), field="html.sha256", source=receipt_path
    ):
        raise RuntimeError(f"Web language release HTML digest mismatch: {receipt_path}")
    if html_dir is not None and _file_inventory(html_dir) != recorded_html:
        raise RuntimeError(f"Web language release HTML files differ from evidence: {html_dir}")
    return VerifiedLanguageReleaseEvidence(
        path=receipt_path,
        sha256=receipt_sha256,
        model=model,
        region=region,
        language=expected_identity[2],
        projection_manifest_sha256=projection_sha256,
    )
