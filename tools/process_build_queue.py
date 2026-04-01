#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_docs import build_root_for_target, render_build_template, resolve_output_path  # noqa: E402
from tools.data_snapshot import resolve_phase2_export_root  # noqa: E402
from tools.review_bundle import resolve_docs_dir  # noqa: E402
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
    base_token: str
    table_id: str
    view_id: str | None


@dataclass(frozen=True)
class QueueRecord:
    record_id: str
    document_id: str
    document_key: str
    version: str
    lang: str
    trigger_value: str
    immediate_trigger_value: Any

    @property
    def label(self) -> str:
        return self.document_id or f"{self.document_key}_{self.lang}"


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
    if not base_token_env:
        raise RuntimeError("sync.phase2.document_link.base_token_env is required, or provide sync.phase2.base_token_env")
    if not table_id_env:
        raise RuntimeError("sync.phase2.document_link.table_id_env is required")
    return DocumentLinkBinding(
        base_token_env=base_token_env,
        table_id_env=table_id_env,
        view_id_env=view_id_env,
        base_token=_env_value(base_token_env),
        table_id=_env_value(table_id_env),
        view_id=_env_value(view_id_env) if view_id_env else None,
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


def pending_queue_records(raw_records: list[dict[str, Any]]) -> list[QueueRecord]:
    return [
        record
        for record in parse_queue_records(raw_records)
        if _is_trigger_requested(record.trigger_value)
    ]


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

    detail = f"Document_ID={record.document_id!r}, Document_Key={record.document_key!r}, Lang={record.lang!r}"
    if errors:
        raise RuntimeError("Unable to resolve build target for queue record. " + detail + " | " + " | ".join(errors))
    raise RuntimeError("Unable to resolve build target for queue record. " + detail)


def _build_languages(cfg: dict[str, Any]) -> list[str]:
    build_cfg_raw = cfg.get("build", {})
    build_cfg = build_cfg_raw if isinstance(build_cfg_raw, dict) else {}
    langs = build_cfg.get("languages", ["en"])
    return [str(item).strip().lower() for item in langs if str(item).strip()] or ["en"]


def _config_match_score(*, config_path: Path, cfg: dict[str, Any], region: str, lang: str) -> int | None:
    build_cfg_raw = cfg.get("build", {})
    build_cfg = build_cfg_raw if isinstance(build_cfg_raw, dict) else {}
    default_region = str(build_cfg.get("default_region") or "").strip().upper()
    languages = _build_languages(cfg)
    primary_lang = languages[0] if languages else ""
    if default_region != region.upper() or primary_lang != lang.lower():
        return None

    score = 0
    file_name = config_path.name.lower()
    if region.lower() in file_name:
        score += 4
    if lang.lower() in file_name:
        score += 4
    if bool(build_cfg.get("include_lang_in_output_path")):
        score += 2
    if file_name != "config.yaml":
        score += 1
    return score


def resolve_config_path_for_task(*, region: str, lang: str) -> Path:
    candidates: list[tuple[int, Path]] = []
    for config_path in sorted(ROOT.glob("config*.yaml")):
        try:
            cfg = load_config(config_path)
        except RuntimeError:
            continue
        score = _config_match_score(config_path=config_path, cfg=cfg, region=region, lang=lang)
        if score is None:
            continue
        candidates.append((score, config_path))

    if not candidates:
        raise RuntimeError(f"No config family matches region='{region}' and lang='{lang}'")
    candidates.sort(key=lambda item: (-item[0], item[1].name))
    return candidates[0][1]


def resolve_word_output_path_for_target(*, config_path: Path, model: str, region: str) -> Path:
    cfg = load_config(config_path)
    build_cfg_raw = cfg.get("build", {})
    build_cfg = build_cfg_raw if isinstance(build_cfg_raw, dict) else {}
    docs_dir = resolve_docs_dir(cfg)
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


def _format_command(cmd: list[str]) -> str:
    return subprocess.list2cmdline([str(part) for part in cmd])


def _command_failure_message(cmd: list[str], stdout: str, stderr: str, returncode: int) -> str:
    for stream in (stderr, stdout):
        lines = [line.strip() for line in stream.splitlines() if line.strip()]
        if lines:
            return f"{lines[-1]} (exit={returncode}, cmd={_format_command(cmd)})"
    return f"command failed with exit={returncode}: {_format_command(cmd)}"


def _run_command(cmd: list[str]) -> None:
    print(f"[build-queue] {_format_command(cmd)}")
    proc = subprocess.run(
        cmd,
        cwd=str(ROOT),
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


def build_document_for_task(
    *,
    config_path: Path,
    model: str,
    region: str,
    data_root: str | None,
) -> Path:
    base_cmd = [
        sys.executable,
        str(ROOT / "build.py"),
        "check",
        "--config",
        str(config_path),
        "--model",
        model,
        "--region",
        region,
    ]
    if data_root:
        base_cmd += ["--data-root", data_root]
    _run_command(base_cmd)

    word_cmd = [
        sys.executable,
        str(ROOT / "build.py"),
        "word",
        "--config",
        str(config_path),
        "--model",
        model,
        "--region",
        region,
        "--no-clean",
    ]
    if data_root:
        word_cmd += ["--data-root", data_root]
    _run_command(word_cmd)

    word_output_path = resolve_word_output_path_for_target(
        config_path=config_path,
        model=model,
        region=region,
    )
    if not word_output_path.exists():
        raise RuntimeError(f"Word output was not created: {word_output_path}")
    return word_output_path


def build_success_fields(
    *,
    version: str,
    word_output_path: Path,
    drive_url: str,
    built_at: datetime,
) -> dict[str, Any]:
    return {
        RESULT_FIELD: " | ".join(
            part
            for part in (
                SUCCESS_PREFIX,
                f"version={version}" if version else "",
                f"built_at={built_at.isoformat(timespec='seconds')}",
            )
            if part
        ),
        DOCUMENT_DIRECTORY_FIELD: word_output_path.resolve(strict=False).as_posix(),
        DOCUMENT_LINK_FIELD: drive_url.strip(),
        TRIGGER_FIELD: [DONE_TRIGGER_VALUE],
        IMMEDIATE_TRIGGER_FIELD: False,
    }


def build_started_fields(*, started_at: datetime) -> dict[str, Any]:
    return {
        BUILD_STARTED_AT_FIELD: int(started_at.timestamp() * 1000),
    }


def build_failure_fields(*, version: str, message: str) -> dict[str, Any]:
    return {
        RESULT_FIELD: " | ".join(
            part
            for part in (
                FAILED_PREFIX,
                f"version={version}" if version else "",
                message.strip(),
            )
            if part
        )
    }


def process_build_queue(
    *,
    cfg: dict[str, Any],
    config_path: Path,
    data_root: str | None,
    dry_run: bool,
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
    pending = pending_queue_records(raw_records)
    if not pending:
        print("[build-queue] No pending build tasks found.")
        return 0
    available_fields = _available_field_names(raw_records)
    can_write_started_at = BUILD_STARTED_AT_FIELD in available_fields

    if dry_run:
        for record in pending:
            model, region = resolve_target_for_record(record)
            resolved_config_path = resolve_config_path_for_task(region=region, lang=record.lang)
            print(
                "[build-queue] DRY-RUN "
                + json.dumps(
                    {
                        "record_id": record.record_id,
                        "label": record.label,
                        "model": model,
                        "region": region,
                        "lang": record.lang,
                        "version": record.version,
                        "config": str(resolved_config_path),
                        "data_root": data_root,
                    },
                    ensure_ascii=False,
                )
            )
        return 0

    failures: list[str] = []
    processed = 0
    for record in pending:
        try:
            started_at = datetime.now().astimezone()
            if can_write_started_at:
                try:
                    source.upsert_record(
                        base_token=binding.base_token,
                        table_id=binding.table_id,
                        record_id=record.record_id,
                        record=build_started_fields(started_at=started_at),
                    )
                    print(f"[build-queue] Marked start time for {record.label}: {started_at.isoformat(timespec='seconds')}")
                except Exception as exc:
                    print(
                        f"[build-queue] WARNING start-time writeback failed for {record.label}: {exc}",
                        file=sys.stderr,
                    )
            model, region = resolve_target_for_record(record)
            resolved_config_path = resolve_config_path_for_task(region=region, lang=record.lang)
            word_output_path = build_document_for_task(
                config_path=resolved_config_path,
                model=model,
                region=region,
                data_root=data_root,
            )
            _, drive_url = upload_word_to_drive(
                cli_bin=cli_bin,
                word_output_path=word_output_path,
                identity=identity,
            )
            built_at = datetime.now().astimezone()
            source.upsert_record(
                base_token=binding.base_token,
                table_id=binding.table_id,
                record_id=record.record_id,
                record=build_success_fields(
                    version=record.version,
                    word_output_path=word_output_path,
                    drive_url=drive_url,
                    built_at=built_at,
                ),
            )
            processed += 1
            print(f"[build-queue] Updated {record.label}: {word_output_path} -> {drive_url}")
        except Exception as exc:
            message = str(exc).strip()
            failures.append(f"{record.label}: {message}")
            try:
                source.upsert_record(
                    base_token=binding.base_token,
                    table_id=binding.table_id,
                    record_id=record.record_id,
                    record=build_failure_fields(version=record.version, message=message),
                )
            except Exception as writeback_exc:
                failures[-1] += f" | writeback_failed={writeback_exc}"
                print(f"[build-queue] ERROR writeback failed for {record.label}: {writeback_exc}", file=sys.stderr)

    print(f"[build-queue] Summary: processed={processed} failed={len(failures)}")
    for failure in failures:
        print(f"[build-queue] FAILURE {failure}", file=sys.stderr)
    return 1 if failures else 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Consume Document_link build tasks and write results back to Feishu.")
    ap.add_argument("--config", required=True, help="Config YAML path")
    ap.add_argument("--data-root", default=None, help="Override structured content snapshot root")
    ap.add_argument("--dry-run", action="store_true", help="List pending tasks without building or writing back")
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
        )
    except RuntimeError as exc:
        print(f"[build-queue] ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
