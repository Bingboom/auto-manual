"""Locale-safe identity and stored-source contracts for Web Publish assembly."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import json
from pathlib import Path
import re
import shutil
from typing import Any

from tools.release_contract import normalize_release_token
from tools.utils.path_utils import PathSegments
from tools.web_language_release_evidence import (
    RECEIPT_FILENAME,
    verify_release_evidence,
)


TARGET_SCHEMA_VERSION = "auto-manual-web-publish-target/v2"
LEGACY_TARGET_SCHEMA_VERSION = "auto-manual-web-publish-target/v1"
LANGUAGE_SCOPE_SINGLE = "single"
LANGUAGE_SCOPE_LEGACY_UNSPECIFIED = "legacy_unspecified"
_LANGUAGE_SCOPES = frozenset(
    {
        LANGUAGE_SCOPE_SINGLE,
        LANGUAGE_SCOPE_LEGACY_UNSPECIFIED,
    }
)
_SAFE_SEGMENT_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
# Feishu Bitable record ids ("recXXXX..."), carried from the queue run into the
# stored publish tree so the post-merge receipt lane can find its queue rows.
_QUEUE_RECORD_ID_RE = re.compile(r"rec[A-Za-z0-9_-]+")


@dataclass(frozen=True)
class WebPublishTarget:
    metadata_path: Path
    model: str
    region: str
    lang: str
    version: str
    built_at: str
    git_ref: str
    markdown_path: Path
    html_dir: Path
    legacy_default: bool | None
    language_scope: str
    language_projection_evidence_path: Path | None = None
    language_projection_evidence_sha256: str | None = None
    queue_record_ids: tuple[str, ...] = ()

    @property
    def route(self) -> Path:
        return Path(self.model) / self.region / self.lang / "md"

    @property
    def identity(self) -> tuple[str, str, str]:
        return tuple(value.casefold() for value in (self.model, self.region, self.lang))


def load_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cannot read JSON object: {path}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"JSON root must be an object: {path}")
    return payload


def required_text(payload: dict[str, Any], field: str, *, source: Path) -> str:
    raw = payload.get(field)
    if not isinstance(raw, str) or not raw.strip():
        raise RuntimeError(f"Web Publish metadata missing {field}: {source}")
    return raw.strip()


def _safe_segment(value: str, *, field: str, source: Path) -> str:
    if not _SAFE_SEGMENT_RE.fullmatch(value):
        raise RuntimeError(f"unsafe {field} in Web Publish metadata {source}: {value!r}")
    return value


def _optional_bool(payload: dict[str, Any], field: str, *, source: Path) -> bool | None:
    if field not in payload:
        return None
    value = payload[field]
    if not isinstance(value, bool):
        raise RuntimeError(f"Web Publish metadata {field} must be a boolean: {source}")
    return value


def safe_queue_record_ids(payload: dict[str, Any], *, source: Path) -> tuple[str, ...]:
    """Validate the optional queue-row ids carried through the publish tree.

    Metadata is data, not trust: a missing field means "no queue rows recorded"
    (the Git-only path), while a present field must be a list of well-formed
    Bitable record ids — anything else fails closed instead of flowing into a
    post-merge Bitable write.
    """
    if "queue_record_ids" not in payload:
        return ()
    raw = payload["queue_record_ids"]
    if not isinstance(raw, list):
        raise RuntimeError(f"Web Publish metadata queue_record_ids must be a list: {source}")
    cleaned: list[str] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, str):
            raise RuntimeError(
                f"Web Publish metadata queue_record_ids must contain strings: {source}"
            )
        value = item.strip()
        if not value:
            continue
        if not _QUEUE_RECORD_ID_RE.fullmatch(value):
            raise RuntimeError(
                f"unsafe queue record id in Web Publish metadata {source}: {value!r}"
            )
        if value in seen:
            continue
        seen.add(value)
        cleaned.append(value)
    return tuple(sorted(cleaned))


def _language_scope(payload: dict[str, Any], *, source: Path) -> str:
    if "language_scope" not in payload:
        return LANGUAGE_SCOPE_LEGACY_UNSPECIFIED
    value = payload["language_scope"]
    if not isinstance(value, str) or value not in _LANGUAGE_SCOPES:
        allowed = ", ".join(sorted(_LANGUAGE_SCOPES))
        raise RuntimeError(
            f"Web Publish metadata language_scope must be one of {allowed}: {source}"
        )
    return value


def _reject_symlink_path(path: Path, *, root: Path, label: str) -> None:
    lexical_root = Path(root.absolute())
    lexical_path = Path(path.absolute())
    if lexical_root.is_symlink():
        raise RuntimeError(f"{label} root must not be a symbolic link: {lexical_root}")
    try:
        relative = lexical_path.relative_to(lexical_root)
    except ValueError as exc:
        raise RuntimeError(f"{label} escapes releases root: {path}") from exc
    current = lexical_root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise RuntimeError(f"{label} must not use a symbolic link: {current}")


def _path_from_metadata(raw: str, *, repo_root: Path, releases_root: Path, source: Path) -> Path:
    path = Path(raw)
    lexical = path if path.is_absolute() else repo_root / path
    _reject_symlink_path(lexical, root=releases_root, label="Web Publish metadata path")
    resolved = lexical.resolve(strict=False)
    try:
        resolved.relative_to(releases_root.resolve(strict=False))
    except ValueError as exc:
        raise RuntimeError(f"Web Publish metadata path escapes releases root in {source}: {raw}") from exc
    if not resolved.exists():
        raise RuntimeError(f"Web Publish metadata path does not exist in {source}: {resolved}")
    return resolved


def load_web_publish_target(
    metadata_path: Path,
    *,
    repo_root: Path,
    releases_root: Path,
) -> WebPublishTarget:
    _reject_symlink_path(metadata_path, root=releases_root, label="Web Publish metadata")
    payload = load_json_object(metadata_path)
    if required_text(payload, "schema_version", source=metadata_path) != "auto-manual-web-publish/v1":
        raise RuntimeError(f"unsupported Web Publish metadata schema: {metadata_path}")
    identity_values = {
        field: _safe_segment(
            required_text(payload, field, source=metadata_path),
            field=field,
            source=metadata_path,
        )
        for field in ("model", "region", "lang")
    }
    version = required_text(payload, "version", source=metadata_path)
    version_token = normalize_release_token(version) or "unversioned"
    expected_metadata = releases_root.resolve(strict=False).joinpath(
        identity_values["model"],
        identity_values["region"],
        identity_values["lang"],
        PathSegments.LATEST,
        PathSegments.WEB,
        PathSegments.PUBLISH_META_JSON,
    )
    if metadata_path.resolve(strict=False) != expected_metadata:
        raise RuntimeError(
            "Web Publish metadata identity does not match path: "
            f"expected {expected_metadata}, got {metadata_path}"
        )
    markdown_path = _path_from_metadata(
        required_text(payload, "md_output_path", source=metadata_path),
        repo_root=repo_root,
        releases_root=releases_root,
        source=metadata_path,
    )
    html_dir = _path_from_metadata(
        required_text(payload, "html_dir", source=metadata_path),
        repo_root=repo_root,
        releases_root=releases_root,
        source=metadata_path,
    )
    if not markdown_path.is_file():
        raise RuntimeError(f"Web Publish Markdown output is not a file: {markdown_path}")
    if not html_dir.is_dir() or not (html_dir / "index.html").is_file():
        raise RuntimeError(f"Web Publish HTML verification output has no index.html: {html_dir}")
    expected_web_dir = releases_root.resolve(strict=False).joinpath(
        identity_values["model"],
        identity_values["region"],
        identity_values["lang"],
        PathSegments.VERSIONS,
        version_token,
        PathSegments.WEB,
    )
    if markdown_path.parent != expected_web_dir / "md" or html_dir != expected_web_dir / "html":
        raise RuntimeError(f"Web Publish artifact identity does not match metadata path: {metadata_path}")
    language_scope = _language_scope(payload, source=metadata_path)
    evidence_path: Path | None = None
    evidence_sha256: str | None = None
    evidence_fields_present = any(
        field in payload
        for field in (
            "language_projection_evidence_path",
            "language_projection_evidence_sha256",
        )
    )
    if language_scope == LANGUAGE_SCOPE_SINGLE:
        raw_evidence_path = required_text(
            payload, "language_projection_evidence_path", source=metadata_path
        )
        evidence_sha256 = required_text(
            payload, "language_projection_evidence_sha256", source=metadata_path
        )
        evidence_path = _path_from_metadata(
            raw_evidence_path,
            repo_root=repo_root,
            releases_root=releases_root,
            source=metadata_path,
        )
        expected_evidence_path = expected_web_dir / PathSegments.EVIDENCE / RECEIPT_FILENAME
        if evidence_path != expected_evidence_path:
            raise RuntimeError(
                "Web language release evidence identity does not match versioned Web path: "
                f"{evidence_path}"
            )
        verify_release_evidence(
            evidence_path,
            expected_sha256=evidence_sha256,
            model=identity_values["model"],
            region=identity_values["region"],
            language=identity_values["lang"],
            version=version,
            git_ref=required_text(payload, "git_ref", source=metadata_path),
            markdown_dir=markdown_path.parent,
            markdown_name=markdown_path.name,
            html_dir=html_dir,
        )
    elif evidence_fields_present:
        raise RuntimeError(
            f"legacy Web Publish metadata must not carry language projection evidence: {metadata_path}"
        )
    return WebPublishTarget(
        metadata_path=metadata_path,
        model=identity_values["model"],
        region=identity_values["region"],
        lang=identity_values["lang"],
        version=version,
        built_at=required_text(payload, "built_at", source=metadata_path),
        git_ref=required_text(payload, "git_ref", source=metadata_path),
        markdown_path=markdown_path,
        html_dir=html_dir,
        legacy_default=_optional_bool(payload, "legacy_default", source=metadata_path),
        language_scope=language_scope,
        language_projection_evidence_path=evidence_path,
        language_projection_evidence_sha256=evidence_sha256,
        queue_record_ids=safe_queue_record_ids(payload, source=metadata_path),
    )


def ensure_unique_targets(targets: list[WebPublishTarget]) -> None:
    identities: dict[tuple[str, str, str], Path] = {}
    for target in targets:
        previous = identities.get(target.identity)
        if previous is not None:
            raise RuntimeError(
                "duplicate Web Publish identity "
                f"{target.model}/{target.region}/{target.lang}: {previous} and {target.metadata_path}"
            )
        identities[target.identity] = target.metadata_path


def discover_web_publish_targets(*, repo_root: Path, releases_root: Path) -> list[WebPublishTarget]:
    metadata_paths = sorted(
        releases_root.glob(
            f"*/*/*/{PathSegments.LATEST}/{PathSegments.WEB}/{PathSegments.PUBLISH_META_JSON}"
        )
    )
    if not metadata_paths:
        raise RuntimeError(f"no latest Web Publish metadata found under {releases_root}")
    targets = [
        load_web_publish_target(path, repo_root=repo_root, releases_root=releases_root)
        for path in metadata_paths
    ]
    ensure_unique_targets(targets)
    return targets


def source_root(output_dir: Path) -> Path:
    return output_dir / "sources" / PathSegments.WEB


def stored_target_metadata(output_dir: Path) -> list[Path]:
    root = source_root(output_dir)
    return sorted(
        {
            *root.glob("*/*/md/publish_meta.json"),
            *root.glob("*/*/*/md/publish_meta.json"),
        }
    )


def _safe_manual_name(value: str, *, source: Path) -> str:
    path = Path(value)
    if path.name != value or path.suffix != ".md" or not _SAFE_SEGMENT_RE.fullmatch(path.stem):
        raise RuntimeError(f"unsafe manual name in stored Web metadata {source}: {value!r}")
    return value


def safe_aliases(payload: dict[str, Any], *, source: Path) -> list[str]:
    raw = payload.get("legacy_aliases", [])
    if not isinstance(raw, list):
        raise RuntimeError(f"stored Web metadata legacy_aliases must be a list: {source}")
    aliases = [str(item or "").strip() for item in raw]
    if any(not _SAFE_SEGMENT_RE.fullmatch(alias) for alias in aliases):
        raise RuntimeError(f"unsafe legacy alias in stored Web metadata: {source}")
    if len({alias.casefold() for alias in aliases}) != len(aliases):
        raise RuntimeError(f"duplicate legacy alias in stored Web metadata: {source}")
    return aliases


def stored_payload(metadata_path: Path, *, output_dir: Path) -> dict[str, Any]:
    payload = load_json_object(metadata_path)
    schema = required_text(payload, "schema_version", source=metadata_path)
    if schema not in {LEGACY_TARGET_SCHEMA_VERSION, TARGET_SCHEMA_VERSION}:
        raise RuntimeError(f"unsupported stored Web Publish metadata schema: {metadata_path}")
    values = {
        field: _safe_segment(required_text(payload, field, source=metadata_path), field=field, source=metadata_path)
        for field in ("model", "region", "lang")
    }
    manual = _safe_manual_name(required_text(payload, "manual", source=metadata_path), source=metadata_path)
    relative = metadata_path.parent.relative_to(source_root(output_dir))
    expected_legacy = Path(values["model"]) / values["region"] / "md"
    expected_locale = Path(values["model"]) / values["region"] / values["lang"] / "md"
    if relative not in {expected_legacy, expected_locale}:
        raise RuntimeError(f"stored Web metadata identity does not match path: {metadata_path}")
    if Path(required_text(payload, "route", source=metadata_path)) != relative:
        raise RuntimeError(f"stored Web metadata route does not match path: {metadata_path}")
    if not (metadata_path.parent / manual).is_file():
        raise RuntimeError(f"stored Web manual does not exist: {metadata_path.parent / manual}")
    _optional_bool(payload, "legacy_default", source=metadata_path)
    payload["language_scope"] = _language_scope(payload, source=metadata_path)
    evidence_fields_present = any(
        field in payload
        for field in (
            "language_projection_evidence_path",
            "language_projection_evidence_sha256",
        )
    )
    if payload["language_scope"] == LANGUAGE_SCOPE_SINGLE:
        evidence_relative = required_text(
            payload, "language_projection_evidence_path", source=metadata_path
        )
        expected_relative = (PathSegments.EVIDENCE + "/" + RECEIPT_FILENAME)
        if evidence_relative != expected_relative:
            raise RuntimeError(
                f"stored Web language evidence path must be {expected_relative}: {metadata_path}"
            )
        receipt_path = metadata_path.parent / evidence_relative
        verify_release_evidence(
            receipt_path,
            expected_sha256=required_text(
                payload, "language_projection_evidence_sha256", source=metadata_path
            ),
            model=values["model"],
            region=values["region"],
            language=values["lang"],
            version=required_text(payload, "version", source=metadata_path),
            git_ref=required_text(payload, "git_ref", source=metadata_path),
            markdown_dir=metadata_path.parent,
            markdown_name=manual,
            html_dir=None,
            stored=True,
        )
    elif evidence_fields_present:
        raise RuntimeError(
            f"stored legacy Web metadata must not carry language projection evidence: {metadata_path}"
        )
    safe_aliases(payload, source=metadata_path)
    safe_queue_record_ids(payload, source=metadata_path)
    return payload


def write_stored_payload(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def migrate_legacy_targets(*, output_dir: Path) -> None:
    root = source_root(output_dir)
    for metadata_path in sorted(root.glob("*/*/md/publish_meta.json")):
        payload = stored_payload(metadata_path, output_dir=output_dir)
        model, region, lang = (str(payload[field]) for field in ("model", "region", "lang"))
        destination = root / model / region / lang / "md"
        if destination.exists():
            raise RuntimeError(
                f"duplicate stored Web Publish identity {model}/{region}/{lang}: "
                f"{metadata_path.parent} and {destination}"
            )
        manual = str(payload["manual"])
        payload.update(
            schema_version=TARGET_SCHEMA_VERSION,
            route=(Path(model) / region / lang / "md").as_posix(),
            legacy_default=True,
            language_scope=LANGUAGE_SCOPE_LEGACY_UNSPECIFIED,
            legacy_route=(Path(model) / region / "md").as_posix(),
            legacy_aliases=[Path(manual).stem],
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(metadata_path.parent), str(destination))
        write_stored_payload(destination / PathSegments.PUBLISH_META_JSON, payload)


def stored_targets(output_dir: Path) -> list[tuple[Path, dict[str, Any]]]:
    records = [(path, stored_payload(path, output_dir=output_dir)) for path in stored_target_metadata(output_dir)]
    identities: dict[tuple[str, str, str], Path] = {}
    for path, payload in records:
        identity = tuple(str(payload[field]).casefold() for field in ("model", "region", "lang"))
        if identity in identities:
            raise RuntimeError(f"duplicate stored Web Publish identity {identity}: {identities[identity]} and {path}")
        identities[identity] = path
    return records


def stage_web_target(
    *,
    target: WebPublishTarget,
    output_dir: Path,
    copy_markdown_source: Callable[[WebPublishTarget, Path], None],
    previous: dict[str, Any] | None = None,
) -> Path:
    destination = source_root(output_dir) / target.route
    if destination.exists():
        if destination.is_symlink() or not destination.is_dir():
            raise RuntimeError(f"publish destination must be a real directory: {destination}")
        shutil.rmtree(destination)
    copy_markdown_source(target, destination)
    metadata_path = destination / PathSegments.PUBLISH_META_JSON
    inherited_default = bool(previous and previous.get("legacy_default"))
    if inherited_default and target.legacy_default is False:
        raise RuntimeError(
            f"cannot clear legacy default during locale staging: {target.model}/{target.region}/{target.lang}"
        )
    payload: dict[str, Any] = {
        "schema_version": TARGET_SCHEMA_VERSION,
        "model": target.model,
        "region": target.region,
        "lang": target.lang,
        "version": target.version,
        "built_at": target.built_at,
        "git_ref": target.git_ref,
        "route": target.route.as_posix(),
        "manual": target.markdown_path.name,
        "language_scope": target.language_scope,
    }
    if target.queue_record_ids:
        payload["queue_record_ids"] = list(target.queue_record_ids)
    if target.language_scope == LANGUAGE_SCOPE_SINGLE:
        if (
            target.language_projection_evidence_path is None
            or target.language_projection_evidence_sha256 is None
        ):
            raise RuntimeError(
                f"single-language Web target lacks verified evidence: {target.metadata_path}"
            )
        payload.update(
            language_projection_evidence_path=(
                PathSegments.EVIDENCE + "/" + RECEIPT_FILENAME
            ),
            language_projection_evidence_sha256=(
                target.language_projection_evidence_sha256
            ),
        )
    if target.legacy_default is not None or inherited_default:
        payload["legacy_default"] = inherited_default or target.legacy_default is True
    if inherited_default and previous is not None:
        payload["legacy_route"] = previous.get("legacy_route")
        payload["legacy_aliases"] = list(previous.get("legacy_aliases", []))
    write_stored_payload(metadata_path, payload)
    return metadata_path


def assign_legacy_defaults(*, output_dir: Path) -> list[tuple[Path, dict[str, Any]]]:
    records = stored_targets(output_dir)
    groups: dict[tuple[str, str], list[tuple[Path, dict[str, Any]]]] = {}
    for record in records:
        payload = record[1]
        key = (str(payload["model"]).casefold(), str(payload["region"]).casefold())
        groups.setdefault(key, []).append(record)
    for group in groups.values():
        defaults = [record for record in group if record[1].get("legacy_default") is True]
        if len(defaults) > 1:
            raise RuntimeError(f"multiple legacy defaults for Web publication: {defaults[0][0]} and {defaults[1][0]}")
        if not defaults:
            has_explicit_non_default = any(
                "legacy_default" in payload for _path, payload in group
            )
            if len(group) != 1 or has_explicit_non_default:
                paths = ", ".join(str(path) for path, _payload in group)
                raise RuntimeError(f"Web publication requires one explicit legacy_default: {paths}")
            defaults = group
            defaults[0][1]["legacy_default"] = True
        default_path, default = defaults[0]
        model, region = str(default["model"]), str(default["region"])
        expected_legacy_route = (Path(model) / region / "md").as_posix()
        legacy_route = str(default.get("legacy_route") or expected_legacy_route)
        if legacy_route != expected_legacy_route:
            raise RuntimeError(f"stored Web legacy route does not match identity: {default_path}")
        aliases = safe_aliases(default, source=default_path) or [Path(str(default["manual"])).stem]
        default.update(legacy_route=legacy_route, legacy_aliases=aliases)
        for path, payload in group:
            payload["legacy_default"] = payload.get("legacy_default") is True
            write_stored_payload(path, payload)
    return stored_targets(output_dir)
