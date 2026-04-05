#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_docs import build_root_for_target, render_build_template, resolve_output_path  # noqa: E402
from tools.data_snapshot import resolve_phase2_export_root  # noqa: E402
from tools.document_link_actions import (  # noqa: E402
    DRAFT_PACKAGE_ACTION_LABEL,
    PUBLISH_ACTION_LABEL,
    best_effort_queue_workflow_action as _best_effort_queue_workflow_action,
    legacy_doc_phase_value as _legacy_doc_phase_value,
    normalize_cli_queue_action as _normalize_cli_queue_action,
    normalize_doc_phase as _normalize_doc_phase,
    normalize_workflow_action as _normalize_workflow_action,
    resolve_workflow_action as _resolve_workflow_action,
    warn_legacy_cli_doc_phase as _warn_legacy_cli_doc_phase,
    warn_legacy_record_doc_phase as _warn_legacy_record_doc_phase,
    workflow_action_label as _workflow_action_label,
    workflow_action_source as _workflow_action_source,
    workflow_action_uses_legacy_doc_phase as _workflow_action_uses_legacy_doc_phase,
)
from tools.queue_config_resolution import (  # noqa: E402
    build_languages as _build_languages,
    queue_by_document_key as _queue_by_document_key,
    resolve_config_path_for_task as _resolve_config_path_for_task,
)
from tools.release_contract import (  # noqa: E402
    normalize_release_token,
    release_lang_for_config,
    release_latest_dir_for_target,
    release_root_for_target,
    release_version_dir_for_target,
)
from tools.sync_data import (  # noqa: E402
    LarkCliSource,
    _cli_bin,
    _cli_command_exists,
    _cli_command_parts,
    _env_value,
    _phase2_identity,
    _parse_json_payload,
    _provider_name,
    _resolved_cli_command_parts,
    _sync_phase2_cfg,
    load_config,
)
from tools.utils.targets import resolve_output_lang  # noqa: E402

TRIGGER_FIELD = "是否触发文档构建"
LEGACY_TRIGGER_FIELDS = ("是否构建文档？",)
RESULT_FIELD = "构建结果"
DOCUMENT_ID_FIELD = "Document_ID"
DOCUMENT_KEY_FIELD = "Document_Key"
VERSION_FIELD = "Version"
LANG_FIELD = "Lang"
BUILD_FAMILY_FIELD = "Build_family"
WORKFLOW_ACTION_FIELD = "Workflow_action"
DOC_PHASE_FIELD = "Doc_phase"
GIT_REF_FIELD = "Git_ref"
BUILD_STARTED_AT_FIELD = "开始构建时间"
DOCUMENT_DIRECTORY_FIELD = "Document directory"
DOCUMENT_LINK_FIELD = "Document link"
IMMEDIATE_TRIGGER_FIELD = "是否立即构建"

SUCCESS_PREFIX = "SUCCESS"
FAILED_PREFIX = "FAILED"
TRIGGER_VALUES = {"1", "true", "y", "yes"}
DONE_TRIGGER_VALUE = "已构建"


@dataclass(frozen=True)
class DocumentLinkBinding:
    base_token_env: str
    table_id_env: str
    view_id_env: str | None
    wiki_parent_token_env: str | None
    base_token: str
    table_id: str
    view_id: str | None
    wiki_parent_token: str | None


@dataclass(frozen=True)
class QueueRecord:
    record_id: str
    document_id: str
    document_key: str
    version: str
    lang: str
    workflow_action: str = ""
    doc_phase: str = ""
    git_ref: str = ""
    trigger_value: str = ""
    immediate_trigger_value: Any = None
    build_family: str = ""

    @property
    def label(self) -> str:
        return self.document_id or f"{self.document_key}_{self.lang}"


@dataclass(frozen=True)
class WikiDestination:
    space_id: str
    parent_wiki_token: str


def _document_link_cfg(cfg: dict[str, Any]) -> dict[str, Any]:
    phase2_cfg = _sync_phase2_cfg(cfg)
    raw = phase2_cfg.get("document_link", {})
    return raw if isinstance(raw, dict) else {}


def _document_link_env_names(cfg: dict[str, Any]) -> tuple[str, str, str | None]:
    phase2_cfg = _sync_phase2_cfg(cfg)
    document_link_cfg = _document_link_cfg(cfg)
    base_token_env = str(document_link_cfg.get("base_token_env") or phase2_cfg.get("base_token_env") or "").strip()
    table_id_env = str(document_link_cfg.get("table_id_env") or "").strip()
    view_id_env = str(document_link_cfg.get("view_id_env") or "").strip() or None
    return base_token_env, table_id_env, view_id_env


def _document_link_wiki_parent_token_env(cfg: dict[str, Any]) -> str | None:
    document_link_cfg = _document_link_cfg(cfg)
    value = str(document_link_cfg.get("wiki_parent_token_env") or "").strip()
    return value or None


def collect_queue_preflight_errors(cfg: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    _provider_name(cfg)

    cli_bin = _cli_bin(cfg)
    try:
        command = _cli_command_parts(cli_bin)[0]
    except RuntimeError as exc:
        errors.append(str(exc))
        command = None
    if command and not _cli_command_exists(cli_bin):
        errors.append(f"sync.phase2.cli_bin executable is not available: {command}")

    base_token_env, table_id_env, view_id_env = _document_link_env_names(cfg)
    missing_env_names = [
        env_name
        for env_name in (base_token_env, table_id_env, view_id_env or "")
        if env_name and not str(os.environ.get(env_name, "")).strip()
    ]
    if not base_token_env:
        errors.append("sync.phase2.document_link.base_token_env is required, or provide sync.phase2.base_token_env")
    if not table_id_env:
        errors.append("sync.phase2.document_link.table_id_env is required")
    if missing_env_names:
        errors.append("Required environment variables are not set: " + ", ".join(missing_env_names))
    return errors


def resolve_document_link_binding(cfg: dict[str, Any]) -> DocumentLinkBinding:
    base_token_env, table_id_env, view_id_env = _document_link_env_names(cfg)
    wiki_parent_token_env = _document_link_wiki_parent_token_env(cfg)
    if not base_token_env:
        raise RuntimeError("sync.phase2.document_link.base_token_env is required, or provide sync.phase2.base_token_env")
    if not table_id_env:
        raise RuntimeError("sync.phase2.document_link.table_id_env is required")
    return DocumentLinkBinding(
        base_token_env=base_token_env,
        table_id_env=table_id_env,
        view_id_env=view_id_env,
        wiki_parent_token_env=wiki_parent_token_env,
        base_token=_env_value(base_token_env),
        table_id=_env_value(table_id_env),
        view_id=_env_value(view_id_env) if view_id_env else None,
        wiki_parent_token=_env_value(wiki_parent_token_env) if wiki_parent_token_env and str(os.environ.get(wiki_parent_token_env, "")).strip() else None,
    )


def _scalar_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        for item in value:
            text = _scalar_text(item)
            if text:
                return text
        return ""
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return format(value, "g")
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return str(value).strip()


def _field_value(fields: dict[str, Any], *field_names: str) -> Any:
    for field_name in field_names:
        if field_name in fields:
            return fields.get(field_name)
    return None


def _available_field_names(raw_records: list[dict[str, Any]]) -> set[str]:
    names: set[str] = set()
    for record in raw_records:
        fields_raw = record.get("fields", {})
        if not isinstance(fields_raw, dict):
            continue
        for key in fields_raw:
            if isinstance(key, str):
                names.add(key)
    return names


def parse_queue_records(raw_records: list[dict[str, Any]]) -> list[QueueRecord]:
    records: list[QueueRecord] = []
    for record in raw_records:
        record_id = str(record.get("record_id") or "").strip()
        if not record_id:
            raise RuntimeError("Document_link record list is missing record_id")
        fields_raw = record.get("fields", {})
        fields = fields_raw if isinstance(fields_raw, dict) else {}
        records.append(
            QueueRecord(
                record_id=record_id,
                document_id=_scalar_text(fields.get(DOCUMENT_ID_FIELD)),
                document_key=_scalar_text(fields.get(DOCUMENT_KEY_FIELD)),
                version=_scalar_text(fields.get(VERSION_FIELD)),
                lang=_scalar_text(fields.get(LANG_FIELD)).lower(),
                build_family=_scalar_text(fields.get(BUILD_FAMILY_FIELD)).lower(),
                workflow_action=_scalar_text(fields.get(WORKFLOW_ACTION_FIELD)),
                doc_phase=_scalar_text(fields.get(DOC_PHASE_FIELD)),
                git_ref=_scalar_text(fields.get(GIT_REF_FIELD)),
                trigger_value=_scalar_text(_field_value(fields, TRIGGER_FIELD, *LEGACY_TRIGGER_FIELDS)),
                immediate_trigger_value=fields.get(IMMEDIATE_TRIGGER_FIELD),
            )
        )
    return records


def _is_immediate_trigger_enabled(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = _scalar_text(value).strip().lower()
    return text in {"1", "true", "y", "yes", "checked"}


def _is_trigger_requested(value: Any) -> bool:
    return _scalar_text(value).strip().lower() in TRIGGER_VALUES


def normalize_workflow_action(value: Any) -> str | None:
    return _normalize_workflow_action(value)


def normalize_doc_phase(value: Any) -> str | None:
    return _normalize_doc_phase(value)


def queue_record_uses_legacy_doc_phase(record: QueueRecord) -> bool:
    return _workflow_action_uses_legacy_doc_phase(
        workflow_action=record.workflow_action,
        doc_phase=record.doc_phase,
    )


def queue_record_action_source(record: QueueRecord) -> str:
    return _workflow_action_source(
        workflow_action=record.workflow_action,
        doc_phase=record.doc_phase,
    )


def queue_record_legacy_doc_phase(record: QueueRecord) -> str | None:
    return _legacy_doc_phase_value(
        workflow_action=record.workflow_action,
        doc_phase=record.doc_phase,
    )


def resolve_queue_workflow_action(record: QueueRecord) -> str | None:
    return _resolve_workflow_action(
        workflow_action=record.workflow_action,
        doc_phase=record.doc_phase,
        record_id=record.record_id,
    )


def workflow_action_label(value: str | None) -> str | None:
    return _workflow_action_label(value)


def pending_queue_records(raw_records: list[dict[str, Any]]) -> list[QueueRecord]:
    return select_pending_queue_records(raw_records)


def pending_immediate_queue_records(raw_records: list[dict[str, Any]]) -> list[QueueRecord]:
    return select_pending_queue_records(raw_records, immediate_only=True)


def select_pending_queue_records(
    raw_records: list[dict[str, Any]],
    *,
    immediate_only: bool = False,
    workflow_action: str | None = None,
    doc_phase: str | None = None,
    record_id: str | None = None,
) -> list[QueueRecord]:
    normalized_filter_doc_phase = normalize_cli_queue_action(
        workflow_action=workflow_action,
        doc_phase=doc_phase,
    )
    selected: list[QueueRecord] = []
    for record in parse_queue_records(raw_records):
        if not _is_trigger_requested(record.trigger_value):
            continue
        if immediate_only and not _is_immediate_trigger_enabled(record.immediate_trigger_value):
            continue
        if record_id and record.record_id != record_id:
            continue
        if normalized_filter_doc_phase is not None:
            if resolve_queue_workflow_action(record) != normalized_filter_doc_phase:
                continue
        selected.append(record)
    return selected


def parse_document_key(document_key: str) -> tuple[str, str]:
    model, separator, region = document_key.strip().rpartition("_")
    if not separator or not model.strip() or not region.strip():
        raise RuntimeError(
            "Document_Key must use '<MODEL>_<REGION>' so the build target is unambiguous: "
            + document_key
        )
    return model.strip(), region.strip().upper()


def _document_key_from_document_id(*, document_id: str, lang: str, version: str) -> str:
    candidate = document_id.strip()
    version_text = version.strip()
    lang_text = lang.strip().lower()
    if version_text and candidate.endswith("_" + version_text):
        candidate = candidate[: -(len(version_text) + 1)]
    if lang_text and candidate.lower().endswith("_" + lang_text):
        candidate = candidate[: -(len(lang_text) + 1)]
    return candidate.strip()


def resolve_target_for_record(record: QueueRecord) -> tuple[str, str]:
    candidates: list[str] = []
    if record.document_key.strip():
        candidates.append(record.document_key.strip())
    fallback_key = _document_key_from_document_id(
        document_id=record.document_id,
        lang=record.lang,
        version=record.version,
    )
    if fallback_key and fallback_key not in candidates:
        candidates.append(fallback_key)

    errors: list[str] = []
    for candidate in candidates:
        try:
            return parse_document_key(candidate)
        except RuntimeError as exc:
            errors.append(str(exc))

    detail = (
        f"Document_ID={record.document_id!r}, Document_Key={record.document_key!r}, "
        f"Lang={record.lang!r}, Build_family={record.build_family!r}"
    )
    if errors:
        raise RuntimeError("Unable to resolve build target for queue record. " + detail + " | " + " | ".join(errors))
    raise RuntimeError("Unable to resolve build target for queue record. " + detail)


def queue_record_key(record: QueueRecord) -> str:
    if record.document_key.strip():
        return record.document_key.strip().upper()
    fallback_key = _document_key_from_document_id(
        document_id=record.document_id,
        lang=record.lang,
        version=record.version,
    )
    if fallback_key:
        return fallback_key.upper()
    return record.record_id


def queue_group_lang(records: list[QueueRecord]) -> str:
    for record in records:
        if record.lang.strip():
            return record.lang.strip().lower()
    return ""


def queue_group_build_family(records: list[QueueRecord]) -> str:
    for record in records:
        if record.build_family.strip():
            return record.build_family.strip().lower()
    return ""


def resolve_config_path_for_task(*, region: str, lang: str | None, build_family: str | None = None) -> Path:
    return _resolve_config_path_for_task(
        repo_root=ROOT,
        region=region,
        lang=lang,
        build_family=build_family,
        config_loader=load_config,
    )


def group_pending_queue_records(records: list[QueueRecord]) -> list[list[QueueRecord]]:
    grouped: list[list[QueueRecord]] = []
    index_by_key: dict[str, int] = {}
    for record in records:
        model, region = resolve_target_for_record(record)
        config_path = resolve_config_path_for_task(region=region, lang=record.lang, build_family=record.build_family)
        cfg = load_config(config_path)
        if _queue_by_document_key(cfg):
            key = queue_record_key(record)
        else:
            key = record.record_id
        existing_index = index_by_key.get(key)
        if existing_index is None:
            index_by_key[key] = len(grouped)
            grouped.append([record])
            continue
        grouped[existing_index].append(record)
    return grouped


def validate_queue_record_group(records: list[QueueRecord]) -> None:
    if not records:
        return
    if len(records) == 1:
        resolve_queue_workflow_action(records[0])
        return

    group_key = queue_record_key(records[0])
    doc_phases = {resolve_queue_workflow_action(record) or "" for record in records}
    versions = {record.version.strip() for record in records}
    git_refs = {record.git_ref.strip() for record in records}
    build_families = {record.build_family.strip().lower() for record in records if record.build_family.strip()}
    conflicts: list[str] = []
    if len(doc_phases) > 1:
        conflicts.append("Workflow_action/Doc_phase")
    if len(versions) > 1:
        conflicts.append("Version")
    if len(git_refs) > 1:
        conflicts.append("Git_ref")
    if len(build_families) > 1:
        conflicts.append("Build_family")
    if conflicts:
        raise RuntimeError(
            "Queue rows merged by Document_Key must agree on "
            + ", ".join(conflicts)
            + f": {group_key}"
        )


def _resolve_docs_dir_for_config(config_path: Path, cfg: dict[str, Any] | None = None) -> Path:
    resolved_config_path = config_path if config_path.is_absolute() else (ROOT / config_path)
    loaded_cfg = cfg if cfg is not None else load_config(resolved_config_path)
    paths_cfg_raw = loaded_cfg.get("paths", {})
    paths_cfg = paths_cfg_raw if isinstance(paths_cfg_raw, dict) else {}
    raw = paths_cfg.get("docs_dir")
    if isinstance(raw, str) and raw.strip():
        candidate = Path(raw.strip())
        return candidate if candidate.is_absolute() else (resolved_config_path.parent / candidate)
    return resolved_config_path.parent / "docs"


def resolve_word_output_path_for_target(*, config_path: Path, model: str, region: str) -> Path:
    cfg = load_config(config_path)
    build_cfg_raw = cfg.get("build", {})
    build_cfg = build_cfg_raw if isinstance(build_cfg_raw, dict) else {}
    docs_dir = _resolve_docs_dir_for_config(config_path, cfg)
    primary_lang = _build_languages(cfg)[0]
    output_lang = resolve_output_lang(cfg)
    build_root = build_root_for_target(
        model,
        region,
        lang=output_lang,
        docs_build_dir=docs_dir / "_build",
    )
    word_output_name = render_build_template(
        str(build_cfg.get("word_output", "manual_demo.docx")),
        model=model,
        region=region,
        lang=primary_lang,
    )
    return resolve_output_path(build_root / "word", word_output_name)


def resolve_html_output_dir_for_target(*, config_path: Path, model: str, region: str) -> Path:
    cfg = load_config(config_path)
    docs_dir = _resolve_docs_dir_for_config(config_path, cfg)
    output_lang = resolve_output_lang(cfg)
    build_root = build_root_for_target(
        model,
        region,
        lang=output_lang,
        docs_build_dir=docs_dir / "_build",
    )
    return build_root / "html"


def _normalize_version_for_filename(version: str) -> str:
    return normalize_release_token(version)


def _versioned_word_output_path(word_output_path: Path, *, version: str, doc_phase: str | None = None) -> Path:
    normalized_doc_phase = normalize_workflow_action(doc_phase)
    version_token = _normalize_version_for_filename(version)
    suffix_parts: list[str] = []
    if normalized_doc_phase == "publish":
        suffix_parts.append("publish")
    if version_token:
        suffix_parts.append(version_token)
    if not suffix_parts:
        return word_output_path
    return word_output_path.with_name(
        f"{word_output_path.stem}_{'_'.join(suffix_parts)}{word_output_path.suffix}"
    )


def _config_path_in_repo_root(config_path: Path, *, repo_root: Path) -> Path:
    return repo_root / config_path.name


def _repo_relative(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(ROOT.resolve(strict=False)).as_posix()
    except ValueError:
        return path.resolve(strict=False).as_posix()


def _publish_release_root_for_target(*, config_path: Path, model: str, region: str) -> Path:
    cfg = load_config(config_path)
    return release_root_for_target(
        repo_root=ROOT,
        config_path=config_path,
        model=model,
        region=region,
        cfg=cfg,
    )


def _publish_release_version_dir_for_target(*, config_path: Path, model: str, region: str, version: str) -> Path:
    cfg = load_config(config_path)
    return release_version_dir_for_target(
        repo_root=ROOT,
        config_path=config_path,
        model=model,
        region=region,
        version=version,
        cfg=cfg,
    )


def _publish_release_latest_dir_for_target(*, config_path: Path, model: str, region: str) -> Path:
    cfg = load_config(config_path)
    return release_latest_dir_for_target(
        repo_root=ROOT,
        config_path=config_path,
        model=model,
        region=region,
        cfg=cfg,
    )


def _slug_ref_token(value: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return text or "queue"


def _format_command(cmd: list[str]) -> str:
    return subprocess.list2cmdline([str(part) for part in cmd])


def _command_failure_message(cmd: list[str], stdout: str, stderr: str, returncode: int) -> str:
    for stream in (stderr, stdout):
        raw = stream.strip()
        if raw:
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = None
            if isinstance(payload, dict):
                error = payload.get("error")
                if isinstance(error, dict):
                    parts: list[str] = []
                    error_type = str(error.get("type") or "").strip()
                    error_code = str(error.get("code") or "").strip()
                    error_message = str(error.get("message") or "").strip()
                    if error_type:
                        parts.append(error_type)
                    if error_message:
                        parts.append(error_message)
                    if error_code and error_code not in error_message:
                        parts.append(f"code={error_code}")
                    detail = error.get("detail")
                    if isinstance(detail, dict):
                        violations = detail.get("permission_violations")
                        if isinstance(violations, list):
                            subjects = [
                                str(item.get("subject") or "").strip()
                                for item in violations
                                if isinstance(item, dict) and str(item.get("subject") or "").strip()
                            ]
                            if subjects:
                                parts.append("subjects=" + ",".join(subjects))
                    if parts:
                        return f"{' | '.join(parts)} (exit={returncode}, cmd={_format_command(cmd)})"
        lines = [line.strip() for line in stream.splitlines() if line.strip()]
        if lines:
            return f"{lines[-1]} (exit={returncode}, cmd={_format_command(cmd)})"
    return f"command failed with exit={returncode}: {_format_command(cmd)}"


def _run_command(cmd: list[str], *, cwd: Path = ROOT) -> None:
    print(f"[build-queue] {_format_command(cmd)}")
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    if proc.returncode:
        raise RuntimeError(_command_failure_message(cmd, proc.stdout or "", proc.stderr or "", proc.returncode))


def _run_git(args: list[str], *, cwd: Path = ROOT) -> None:
    _run_command(["git", *args], cwd=cwd)


def _worktree_dir_for_git_ref(git_ref: str) -> Path:
    return ROOT / ".tmp" / "process-build-queue-worktrees" / _slug_ref_token(git_ref)


def _remove_worktree(path: Path) -> None:
    if not path.exists():
        return
    proc = subprocess.run(
        ["git", "worktree", "remove", "--force", str(path)],
        cwd=str(ROOT),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if proc.returncode != 0 and path.exists():
        shutil.rmtree(path, ignore_errors=True)


def _prepare_git_ref_worktree(git_ref: str) -> Path:
    branch_name = git_ref.strip()
    if not branch_name:
        raise RuntimeError("Git_ref is required when preparing a queue build worktree")
    _run_git(["fetch", "origin", "--prune"])
    _run_git(["fetch", "origin", f"refs/heads/{branch_name}:refs/remotes/origin/{branch_name}"])
    source_ref = f"origin/{branch_name}"
    worktree = _worktree_dir_for_git_ref(branch_name)
    _remove_worktree(worktree)
    worktree.parent.mkdir(parents=True, exist_ok=True)
    _run_git(["worktree", "add", "--force", "--detach", str(worktree), source_ref])
    return worktree


def _run_lark_cli_json(*, cli_bin: str, args: list[str]) -> dict[str, Any]:
    cmd = [*_resolved_cli_command_parts(cli_bin), *args]
    print(f"[build-queue] {_format_command(cmd)}")
    proc = subprocess.run(
        cmd,
        cwd=str(ROOT),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if proc.returncode:
        raise RuntimeError(_command_failure_message(cmd, proc.stdout or "", proc.stderr or "", proc.returncode))
    payload = _parse_json_payload(proc.stdout or proc.stderr or "")
    code = payload.get("code")
    if code not in (None, 0):
        message = str(payload.get("msg") or payload.get("message") or "Lark CLI API request failed")
        raise RuntimeError(f"Lark CLI API request failed: {message}")
    return payload


def _cli_relative_file_arg(path: Path) -> str:
    resolved = path.resolve(strict=False)
    try:
        relative = resolved.relative_to(ROOT)
    except ValueError as exc:
        raise RuntimeError(f"Word output must stay under repo root for lark-cli upload: {resolved}") from exc
    if os.name == "nt":
        return ".\\" + str(relative).replace("/", "\\")
    return "./" + relative.as_posix()


def upload_word_to_drive(*, cli_bin: str, word_output_path: Path, identity: str) -> tuple[str, str]:
    if not word_output_path.exists():
        raise RuntimeError(f"Word output was not created: {word_output_path}")

    upload_payload = _run_lark_cli_json(
        cli_bin=cli_bin,
        args=[
            "drive",
            "+upload",
            "--as",
            identity,
            "--file",
            _cli_relative_file_arg(word_output_path),
            "--name",
            word_output_path.name,
        ],
    )
    upload_data = upload_payload.get("data")
    if not isinstance(upload_data, dict):
        raise RuntimeError("Drive upload response is missing data payload")
    file_token = str(upload_data.get("file_token") or "").strip()
    if not file_token:
        raise RuntimeError("Drive upload response is missing file_token")

    meta_payload = _run_lark_cli_json(
        cli_bin=cli_bin,
        args=[
            "drive",
            "metas",
            "batch_query",
            "--as",
            identity,
            "--data",
            json.dumps(
                {
                    "with_url": True,
                    "request_docs": [{"doc_token": file_token, "doc_type": "file"}],
                },
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        ],
    )
    meta_data = meta_payload.get("data")
    if not isinstance(meta_data, dict):
        raise RuntimeError("Drive metadata response is missing data payload")
    metas = meta_data.get("metas")
    if not isinstance(metas, list) or not metas or not isinstance(metas[0], dict):
        raise RuntimeError(f"Drive metadata response is missing file url for file_token={file_token}")
    drive_url = str(metas[0].get("url") or "").strip()
    if not drive_url:
        raise RuntimeError(f"Drive metadata response is missing file url for file_token={file_token}")
    return file_token, drive_url


def _wiki_node_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data")
    if not isinstance(data, dict):
        raise RuntimeError("Wiki node response is missing data payload")
    node = data.get("node")
    if not isinstance(node, dict):
        raise RuntimeError("Wiki node response is missing node payload")
    return node


def get_wiki_node(
    *,
    cli_bin: str,
    identity: str,
    token: str,
    obj_type: str | None = None,
) -> dict[str, Any]:
    params: dict[str, Any] = {"token": token}
    if obj_type:
        params["obj_type"] = obj_type
    payload = _run_lark_cli_json(
        cli_bin=cli_bin,
        args=[
            "wiki",
            "spaces",
            "get_node",
            "--as",
            identity,
            "--params",
            json.dumps(params, ensure_ascii=False, separators=(",", ":")),
        ],
    )
    return _wiki_node_from_payload(payload)


def resolve_wiki_destination(
    *,
    cli_bin: str,
    identity: str,
    binding: DocumentLinkBinding,
) -> WikiDestination:
    if binding.wiki_parent_token:
        node = get_wiki_node(
            cli_bin=cli_bin,
            identity=identity,
            token=binding.wiki_parent_token,
        )
        space_id = str(node.get("space_id") or "").strip()
        parent_wiki_token = binding.wiki_parent_token
    else:
        node = get_wiki_node(
            cli_bin=cli_bin,
            identity=identity,
            token=binding.base_token,
            obj_type="bitable",
        )
        space_id = str(node.get("space_id") or "").strip()
        parent_wiki_token = str(node.get("parent_node_token") or node.get("node_token") or "").strip()
    if not space_id:
        raise RuntimeError("Wiki destination lookup did not return a space_id")
    if not parent_wiki_token:
        raise RuntimeError("Wiki destination lookup did not return a usable parent_wiki_token")
    return WikiDestination(space_id=space_id, parent_wiki_token=parent_wiki_token)


def _host_root_from_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if not parsed.scheme or not parsed.netloc:
        raise RuntimeError(f"Could not determine tenant host from URL: {url}")
    return f"{parsed.scheme}://{parsed.netloc}"


def _wiki_url_from_host_root(host_root: str, wiki_token: str) -> str:
    return f"{host_root.rstrip('/')}/wiki/{wiki_token}"


def _move_result_entry_from_task_payload(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data")
    if not isinstance(data, dict):
        raise RuntimeError("Wiki task response is missing data payload")
    task = data.get("task")
    if not isinstance(task, dict):
        raise RuntimeError("Wiki task response is missing task payload")
    move_result = task.get("move_result")
    if not isinstance(move_result, list) or not move_result or not isinstance(move_result[0], dict):
        raise RuntimeError("Wiki task response is missing move_result payload")
    return move_result[0]


def wait_for_wiki_move_task(
    *,
    cli_bin: str,
    identity: str,
    task_id: str,
    host_root: str,
) -> str:
    for _ in range(20):
        payload = _run_lark_cli_json(
            cli_bin=cli_bin,
            args=[
                "api",
                "GET",
                f"/open-apis/wiki/v2/tasks/{task_id}",
                "--params",
                json.dumps({"task_type": "move"}, ensure_ascii=False, separators=(",", ":")),
                "--as",
                identity,
            ],
        )
        entry = _move_result_entry_from_task_payload(payload)
        status = entry.get("status")
        status_msg = str(entry.get("status_msg") or "").strip()
        if status == 1 or status_msg == "processing":
            time.sleep(3.0)
            continue
        if status == 0:
            node = entry.get("node")
            if not isinstance(node, dict):
                raise RuntimeError("Wiki task completed without node payload")
            wiki_token = str(node.get("node_token") or "").strip()
            if not wiki_token:
                raise RuntimeError("Wiki task completed without node_token")
            return _wiki_url_from_host_root(host_root, wiki_token)
        raise RuntimeError(f"Wiki move task failed: {status_msg or status}")
    raise RuntimeError(f"Wiki move task timed out: {task_id}")


def move_drive_file_to_wiki(
    *,
    cli_bin: str,
    identity: str,
    file_token: str,
    drive_url: str,
    destination: WikiDestination,
) -> str:
    host_root = _host_root_from_url(drive_url)
    payload = _run_lark_cli_json(
        cli_bin=cli_bin,
        args=[
            "api",
            "POST",
            f"/open-apis/wiki/v2/spaces/{destination.space_id}/nodes/move_docs_to_wiki",
            "--as",
            identity,
            "--data",
            json.dumps(
                {
                    "parent_wiki_token": destination.parent_wiki_token,
                    "obj_type": "file",
                    "obj_token": file_token,
                },
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        ],
    )
    data = payload.get("data")
    if not isinstance(data, dict):
        raise RuntimeError("Wiki move response is missing data payload")
    wiki_token = str(data.get("wiki_token") or "").strip()
    if wiki_token:
        return _wiki_url_from_host_root(host_root, wiki_token)
    task_id = str(data.get("task_id") or "").strip()
    if task_id:
        return wait_for_wiki_move_task(
            cli_bin=cli_bin,
            identity=identity,
            task_id=task_id,
            host_root=host_root,
        )
    if data.get("applied") is True:
        raise RuntimeError("Wiki move requires a permission approval flow before the file can be attached to the knowledge base")
    raise RuntimeError("Wiki move response did not include wiki_token or task_id")


def _build_py_target_command(
    *,
    repo_root: Path = ROOT,
    action: str,
    config_path: Path,
    model: str,
    region: str,
    data_root: str | None,
    source: str | None = None,
    no_clean: bool = False,
) -> list[str]:
    cmd = [
        sys.executable,
        str(repo_root / "build.py"),
        action,
        "--config",
        str(config_path),
        "--model",
        model,
        "--region",
        region,
    ]
    if source:
        cmd += ["--source", source]
    if no_clean:
        cmd.append("--no-clean")
    if data_root:
        cmd += ["--data-root", data_root]
    return cmd


def _build_py_sync_data_command(*, repo_root: Path = ROOT, config_path: Path, data_root: str | None) -> list[str]:
    cmd = [
        sys.executable,
        str(repo_root / "build.py"),
        "sync-data",
        "--config",
        str(config_path),
    ]
    if data_root:
        cmd += ["--data-root", data_root]
    return cmd


def sync_phase2_snapshot_before_queue(*, config_path: Path, data_root: str | None) -> None:
    _run_command(
        _build_py_sync_data_command(
            repo_root=ROOT,
            config_path=config_path,
            data_root=data_root,
        )
    )


def _copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def _stage_draft_word_output_to_host_repo(
    *,
    built_word_output_path: Path,
    host_config_path: Path,
    model: str,
    region: str,
    version: str,
    doc_phase: str | None,
) -> Path:
    host_output_path = resolve_word_output_path_for_target(
        config_path=host_config_path,
        model=model,
        region=region,
    )
    staged_output_path = _versioned_word_output_path(
        host_output_path,
        version=version,
        doc_phase=doc_phase,
    )
    staged_output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(built_word_output_path, staged_output_path)
    return staged_output_path


def _stage_publish_assets_to_host_repo(
    *,
    built_word_output_path: Path,
    built_html_dir: Path,
    host_config_path: Path,
    model: str,
    region: str,
    version: str,
) -> tuple[Path, Path]:
    version_dir = _publish_release_version_dir_for_target(
        config_path=host_config_path,
        model=model,
        region=region,
        version=version,
    )
    latest_dir = _publish_release_latest_dir_for_target(
        config_path=host_config_path,
        model=model,
        region=region,
    )
    version_dir.mkdir(parents=True, exist_ok=True)
    latest_dir.mkdir(parents=True, exist_ok=True)
    staged_word_output_path = version_dir / built_word_output_path.name
    shutil.copy2(built_word_output_path, staged_word_output_path)
    latest_html_dir = latest_dir / "html"
    _copy_tree(built_html_dir, latest_html_dir)
    return staged_word_output_path, latest_html_dir


def write_publish_release_metadata(
    *,
    config_path: Path,
    model: str,
    region: str,
    version: str,
    git_ref: str,
    built_at: datetime,
    word_output_path: Path,
    html_dir: Path,
    document_link_url: str,
) -> Path:
    version_dir = _publish_release_version_dir_for_target(
        config_path=config_path,
        model=model,
        region=region,
        version=version,
    )
    latest_dir = _publish_release_latest_dir_for_target(
        config_path=config_path,
        model=model,
        region=region,
    )
    payload = {
        "model": model,
        "region": region,
        "lang": release_lang_for_config(config_path),
        "version": version,
        "git_ref": git_ref.strip(),
        "doc_phase": "publish",
        "built_at": built_at.isoformat(timespec="seconds"),
        "word_output_path": _repo_relative(word_output_path),
        "html_dir": _repo_relative(html_dir),
        "html_index": _repo_relative(html_dir / "index.html"),
        "document_link_url": document_link_url.strip(),
    }
    version_dir.mkdir(parents=True, exist_ok=True)
    latest_dir.mkdir(parents=True, exist_ok=True)
    version_meta_path = version_dir / "publish_meta.json"
    latest_meta_path = latest_dir / "publish_meta.json"
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    version_meta_path.write_text(text, encoding="utf-8")
    latest_meta_path.write_text(text, encoding="utf-8")
    return latest_meta_path


def build_document_for_task(
    *,
    config_path: Path,
    model: str,
    region: str,
    data_root: str | None,
    doc_phase: str | None,
    version: str = "",
    git_ref: str = "",
) -> Path:
    normalized_doc_phase = normalize_workflow_action(doc_phase)
    repo_root = ROOT
    effective_config_path = config_path
    worktree: Path | None = None
    if git_ref.strip():
        worktree = _prepare_git_ref_worktree(git_ref.strip())
        repo_root = worktree
        effective_config_path = _config_path_in_repo_root(config_path, repo_root=worktree)

    try:
        if normalized_doc_phase == "draft":
            _run_command(
                _build_py_target_command(
                    repo_root=repo_root,
                    action="check",
                    config_path=effective_config_path,
                    model=model,
                    region=region,
                    data_root=data_root,
                    source="review",
                ),
                cwd=repo_root,
            )
            _run_command(
                _build_py_target_command(
                    repo_root=repo_root,
                    action="word",
                    config_path=effective_config_path,
                    model=model,
                    region=region,
                    data_root=data_root,
                    source="review",
                    no_clean=True,
                ),
                cwd=repo_root,
            )
        elif normalized_doc_phase == "publish":
            _run_command(
                _build_py_target_command(
                    repo_root=repo_root,
                    action="publish",
                    config_path=effective_config_path,
                    model=model,
                    region=region,
                    data_root=data_root,
                ),
                cwd=repo_root,
            )
            _run_command(
                _build_py_target_command(
                    repo_root=repo_root,
                    action="html",
                    config_path=effective_config_path,
                    model=model,
                    region=region,
                    data_root=data_root,
                    source="review",
                    no_clean=True,
                ),
                cwd=repo_root,
            )
        else:
            _run_command(
                _build_py_target_command(
                    repo_root=repo_root,
                    action="check",
                    config_path=effective_config_path,
                    model=model,
                    region=region,
                    data_root=data_root,
                ),
                cwd=repo_root,
            )
            _run_command(
                _build_py_target_command(
                    repo_root=repo_root,
                    action="word",
                    config_path=effective_config_path,
                    model=model,
                    region=region,
                    data_root=data_root,
                    no_clean=True,
                ),
                cwd=repo_root,
            )

        word_output_path = resolve_word_output_path_for_target(
            config_path=effective_config_path,
            model=model,
            region=region,
        )
        if not word_output_path.exists():
            raise RuntimeError(f"Word output was not created: {word_output_path}")
        versioned_path = _versioned_word_output_path(
            word_output_path,
            version=version,
            doc_phase=normalized_doc_phase,
        )
        if versioned_path != word_output_path:
            versioned_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(word_output_path, versioned_path)
            word_output_path = versioned_path
        if normalized_doc_phase == "publish":
            html_output_dir = resolve_html_output_dir_for_target(
                config_path=effective_config_path,
                model=model,
                region=region,
            )
            if not html_output_dir.exists():
                raise RuntimeError(f"HTML output was not created for publish: {html_output_dir}")
            host_config_path = _config_path_in_repo_root(config_path, repo_root=ROOT)
            staged_word_output_path, _latest_html_dir = _stage_publish_assets_to_host_repo(
                built_word_output_path=word_output_path,
                built_html_dir=html_output_dir,
                host_config_path=host_config_path,
                model=model,
                region=region,
                version=version,
            )
            return staged_word_output_path
        if repo_root != ROOT:
            return _stage_draft_word_output_to_host_repo(
                built_word_output_path=word_output_path,
                host_config_path=_config_path_in_repo_root(config_path, repo_root=ROOT),
                model=model,
                region=region,
                version=version,
                doc_phase=normalized_doc_phase,
            )
        return word_output_path
    finally:
        if worktree is not None:
            _remove_worktree(worktree)


def build_success_fields(
    *,
    version: str,
    word_output_path: Path,
    document_link_url: str,
    built_at: datetime,
    workflow_action: str | None = None,
    doc_phase: str | None = None,
) -> dict[str, Any]:
    normalized_workflow_action = normalize_workflow_action(workflow_action or doc_phase)
    action_label = workflow_action_label(workflow_action or doc_phase)
    normalized_doc_phase = normalize_doc_phase(doc_phase) if _scalar_text(doc_phase) else None
    return {
        RESULT_FIELD: " | ".join(
            part
            for part in (
                SUCCESS_PREFIX,
                f"version={version}" if version else "",
                f"workflow_action={action_label}" if action_label else "",
                (
                    f"legacy_doc_phase={normalized_doc_phase}"
                    if normalized_doc_phase and normalized_workflow_action == normalized_doc_phase and _scalar_text(doc_phase)
                    else ""
                ),
                f"built_at={built_at.isoformat(timespec='seconds')}",
            )
            if part
        ),
        DOCUMENT_DIRECTORY_FIELD: word_output_path.resolve(strict=False).as_posix(),
        DOCUMENT_LINK_FIELD: document_link_url.strip(),
        TRIGGER_FIELD: [DONE_TRIGGER_VALUE],
        IMMEDIATE_TRIGGER_FIELD: False,
    }


def build_started_fields(*, started_at: datetime) -> dict[str, Any]:
    return {
        BUILD_STARTED_AT_FIELD: int(started_at.timestamp() * 1000),
    }


def build_failure_fields(
    *,
    version: str,
    message: str,
    workflow_action: str | None = None,
    doc_phase: str | None = None,
) -> dict[str, Any]:
    normalized_workflow_action = normalize_workflow_action(workflow_action or doc_phase)
    action_label = workflow_action_label(workflow_action or doc_phase)
    normalized_doc_phase = normalize_doc_phase(doc_phase) if _scalar_text(doc_phase) else None
    return {
        RESULT_FIELD: " | ".join(
            part
            for part in (
                FAILED_PREFIX,
                f"version={version}" if version else "",
                f"workflow_action={action_label}" if action_label else "",
                (
                    f"legacy_doc_phase={normalized_doc_phase}"
                    if normalized_doc_phase and normalized_workflow_action == normalized_doc_phase and _scalar_text(doc_phase)
                    else ""
                ),
                message.strip(),
            )
            if part
        )
    }


def build_failure_writeback_fields(
    *,
    version: str,
    message: str,
    workflow_action: str | None = None,
    doc_phase: str | None = None,
    word_output_path: Path | None = None,
    document_link_url: str | None = None,
) -> dict[str, Any]:
    fields = build_failure_fields(
        version=version,
        message=message,
        workflow_action=workflow_action,
        doc_phase=doc_phase,
    )
    if word_output_path is not None:
        fields[DOCUMENT_DIRECTORY_FIELD] = word_output_path.resolve(strict=False).as_posix()
    if document_link_url:
        fields[DOCUMENT_LINK_FIELD] = document_link_url
        fields[RESULT_FIELD] += " | latest_drive_link_preserved"
    # Clear the immediate checkbox on failure so local startup catch-up does not loop
    # forever; users can re-check it after fixing the root cause.
    fields[IMMEDIATE_TRIGGER_FIELD] = False
    return fields


def normalize_cli_queue_action(*, workflow_action: str | None = None, doc_phase: str | None = None) -> str | None:
    return _normalize_cli_queue_action(workflow_action=workflow_action, doc_phase=doc_phase)


def warn_legacy_cli_doc_phase(doc_phase: str | None, workflow_action: str | None) -> None:
    _warn_legacy_cli_doc_phase(doc_phase, workflow_action)


def warn_legacy_record_doc_phase(record: QueueRecord) -> None:
    _warn_legacy_record_doc_phase(
        record_id=record.record_id,
        workflow_action=record.workflow_action,
        doc_phase=record.doc_phase,
    )


def best_effort_queue_workflow_action(record: QueueRecord) -> str | None:
    return _best_effort_queue_workflow_action(
        workflow_action=record.workflow_action,
        doc_phase=record.doc_phase,
        record_id=record.record_id,
    )


def process_build_queue(
    *,
    cfg: dict[str, Any],
    config_path: Path,
    data_root: str | None,
    dry_run: bool,
    immediate_only: bool = False,
    workflow_action: str | None = None,
    doc_phase: str | None = None,
    record_id: str | None = None,
) -> int:
    errors = collect_queue_preflight_errors(cfg)
    if errors:
        raise RuntimeError("process-build-queue preflight failed:\n- " + "\n- ".join(errors))

    binding = resolve_document_link_binding(cfg)
    cli_bin = _cli_bin(cfg)
    identity = _phase2_identity()
    source = LarkCliSource(cli_bin=cli_bin, identity=identity)
    raw_records = source.fetch_records_with_ids(
        base_token=binding.base_token,
        table_id=binding.table_id,
        view_id=binding.view_id,
    )
    normalized_cli_action = normalize_cli_queue_action(workflow_action=workflow_action, doc_phase=doc_phase)
    warn_legacy_cli_doc_phase(doc_phase, workflow_action)
    pending = select_pending_queue_records(
        raw_records,
        immediate_only=immediate_only,
        workflow_action=normalized_cli_action,
        record_id=record_id,
    )
    if not pending:
        if immediate_only:
            print("[build-queue] No pending immediate build tasks found.")
        else:
            print("[build-queue] No pending build tasks found.")
        return 0
    pending_groups = group_pending_queue_records(pending)
    available_fields = _available_field_names(raw_records)
    can_write_started_at = BUILD_STARTED_AT_FIELD in available_fields

    if dry_run:
        for group in pending_groups:
            record = group[0]
            warn_legacy_record_doc_phase(record)
            model, region = resolve_target_for_record(record)
            group_lang = queue_group_lang(group)
            group_build_family = queue_group_build_family(group)
            validate_queue_record_group(group)
            resolved_config_path = resolve_config_path_for_task(
                region=region,
                lang=group_lang,
                build_family=group_build_family,
            )
            print(
                "[build-queue] DRY-RUN "
                + json.dumps(
                    {
                        "record_ids": [item.record_id for item in group],
                        "record_id": record.record_id,
                        "label": record.label,
                        "document_key": queue_record_key(record),
                        "model": model,
                        "region": region,
                        "lang": group_lang,
                        "build_family": group_build_family,
                        "langs": [item.lang for item in group if item.lang.strip()],
                        "version": record.version,
                        "workflow_action": workflow_action_label(record.workflow_action or record.doc_phase) or "Legacy/Unspecified",
                        "workflow_action_source": queue_record_action_source(record),
                        "legacy_doc_phase": queue_record_legacy_doc_phase(record),
                        "git_ref": record.git_ref,
                        "config": str(resolved_config_path),
                        "data_root": data_root,
                    },
                    ensure_ascii=False,
                )
            )
        return 0

    print("[build-queue] Syncing latest phase2 snapshot before building queued documents.")
    sync_phase2_snapshot_before_queue(
        config_path=config_path,
        data_root=data_root,
    )
    raw_records = source.fetch_records_with_ids(
        base_token=binding.base_token,
        table_id=binding.table_id,
        view_id=binding.view_id,
    )
    pending = select_pending_queue_records(
        raw_records,
        immediate_only=immediate_only,
        workflow_action=normalized_cli_action,
        record_id=record_id,
    )
    if not pending:
        print("[build-queue] Queue changed during sync; no pending build tasks remain.")
        return 0
    pending_groups = group_pending_queue_records(pending)
    available_fields = _available_field_names(raw_records)
    can_write_started_at = BUILD_STARTED_AT_FIELD in available_fields

    wiki_destination = resolve_wiki_destination(
        cli_bin=cli_bin,
        identity=identity,
        binding=binding,
    )
    print(
        "[build-queue] Wiki destination "
        + json.dumps(
            {
                "space_id": wiki_destination.space_id,
                "parent_wiki_token": wiki_destination.parent_wiki_token,
            },
            ensure_ascii=False,
        )
    )

    failures: list[str] = []
    processed = 0
    for group in pending_groups:
        record = group[0]
        word_output_path: Path | None = None
        drive_url: str | None = None
        try:
            warn_legacy_record_doc_phase(record)
            validate_queue_record_group(group)
            model, region = resolve_target_for_record(record)
            group_lang = queue_group_lang(group)
            group_build_family = queue_group_build_family(group)
            resolved_config_path = resolve_config_path_for_task(
                region=region,
                lang=group_lang,
                build_family=group_build_family,
            )
            effective_doc_phase = resolve_queue_workflow_action(record)
            started_at = datetime.now().astimezone()
            if can_write_started_at:
                start_fields = build_started_fields(started_at=started_at)
                for group_record in group:
                    try:
                        source.upsert_record(
                            base_token=binding.base_token,
                            table_id=binding.table_id,
                            record_id=group_record.record_id,
                            record=start_fields,
                        )
                    except Exception as exc:
                        print(
                            f"[build-queue] WARNING start-time writeback failed for {group_record.label}: {exc}",
                            file=sys.stderr,
                        )
                print(
                    "[build-queue] Marked start time for "
                    f"{queue_record_key(record)} ({len(group)} row(s)): {started_at.isoformat(timespec='seconds')}"
                )
            word_output_path = build_document_for_task(
                config_path=resolved_config_path,
                model=model,
                region=region,
                data_root=data_root,
                doc_phase=effective_doc_phase,
                version=record.version,
                git_ref=record.git_ref,
            )
            file_token, drive_url = upload_word_to_drive(
                cli_bin=cli_bin,
                word_output_path=word_output_path,
                identity=identity,
            )
            document_link_url = move_drive_file_to_wiki(
                cli_bin=cli_bin,
                identity=identity,
                file_token=file_token,
                drive_url=drive_url,
                destination=wiki_destination,
            )
            built_at = datetime.now().astimezone()
            success_fields = build_success_fields(
                version=record.version,
                word_output_path=word_output_path,
                document_link_url=document_link_url,
                built_at=built_at,
                workflow_action=effective_doc_phase,
                doc_phase=queue_record_legacy_doc_phase(record),
            )
            for group_record in group:
                source.upsert_record(
                    base_token=binding.base_token,
                    table_id=binding.table_id,
                    record_id=group_record.record_id,
                    record=success_fields,
                )
            if effective_doc_phase == "publish":
                latest_html_dir = _publish_release_latest_dir_for_target(
                    config_path=resolved_config_path,
                    model=model,
                    region=region,
                ) / "html"
                write_publish_release_metadata(
                    config_path=resolved_config_path,
                    model=model,
                    region=region,
                    version=record.version,
                    git_ref=record.git_ref,
                    built_at=built_at,
                    word_output_path=word_output_path,
                    html_dir=latest_html_dir,
                    document_link_url=document_link_url,
                )
            processed += len(group)
            print(
                f"[build-queue] {workflow_action_label(effective_doc_phase) or 'Updated'} "
                f"{queue_record_key(record)} ({len(group)} row(s)): {word_output_path} -> {document_link_url}"
            )
        except Exception as exc:
            message = str(exc).strip()
            failures.append(
                f"{workflow_action_label(record.workflow_action or record.doc_phase) or 'Queue task'} "
                f"{queue_record_key(record)} ({len(group)} row(s)): {message}"
            )
            try:
                if drive_url:
                    print(
                        f"[build-queue] WARNING wiki attach failed for {queue_record_key(record)}; preserving latest Drive link {drive_url}",
                        file=sys.stderr,
                    )
                failure_fields = build_failure_writeback_fields(
                    version=record.version,
                    message=message,
                    workflow_action=best_effort_queue_workflow_action(record),
                    doc_phase=queue_record_legacy_doc_phase(record),
                    word_output_path=word_output_path,
                    document_link_url=drive_url,
                )
                for group_record in group:
                    source.upsert_record(
                        base_token=binding.base_token,
                        table_id=binding.table_id,
                        record_id=group_record.record_id,
                        record=failure_fields,
                    )
            except Exception as writeback_exc:
                failures[-1] += f" | writeback_failed={writeback_exc}"
                print(
                    f"[build-queue] ERROR writeback failed for {queue_record_key(record)}: {writeback_exc}",
                    file=sys.stderr,
                )

    print(f"[build-queue] Summary: processed={processed} failed={len(failures)}")
    for failure in failures:
        print(f"[build-queue] FAILURE {failure}", file=sys.stderr)
    return 1 if failures else 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Consume Document_link build tasks and write draft-package or publish results back to Feishu.")
    ap.add_argument("--config", required=True, help="Config YAML path")
    ap.add_argument("--data-root", default=None, help="Override structured content snapshot root")
    ap.add_argument("--dry-run", action="store_true", help="List pending tasks without building or writing back")
    ap.add_argument(
        "--workflow-action",
        choices=("build-draft-package", "draft", "publish"),
        default=None,
        help="Only consume queue rows for one normalized Workflow_action (Build Draft Package or Publish)",
    )
    ap.add_argument(
        "--doc-phase",
        choices=("draft", "publish"),
        default=None,
        help="Deprecated compatibility filter for legacy Doc_phase rows; prefer --workflow-action",
    )
    ap.add_argument("--record-id", default=None, help="Only consume one Document_link record_id")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = ROOT / config_path
    cfg = load_config(config_path)
    resolved_data_root = str(
        resolve_phase2_export_root(
            cfg,
            repo_root=ROOT,
            data_root=args.data_root,
        )
    )
    try:
        return process_build_queue(
            cfg=cfg,
            config_path=config_path,
            data_root=resolved_data_root,
            dry_run=bool(args.dry_run),
            workflow_action=args.workflow_action,
            doc_phase=args.doc_phase,
            record_id=(args.record_id or "").strip() or None,
        )
    except RuntimeError as exc:
        print(f"[build-queue] ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
