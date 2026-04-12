from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from typing import Any

from tools.document_link_actions import (
    best_effort_queue_workflow_action,
    workflow_action_label,
)
from tools.document_link_queue import (
    is_immediate_trigger_enabled,
    scalar_text,
)
from tools.phase2_support import (
    LarkCliSource,
    cli_bin,
    load_config,
    phase2_identity,
)
from tools.process_build_queue import (
    BUILD_FAMILY_FIELD,
    DOCUMENT_DIRECTORY_FIELD,
    DOCUMENT_ID_FIELD,
    DOCUMENT_KEY_FIELD,
    DOCUMENT_LINK_FIELD,
    GIT_REF_FIELD,
    IMMEDIATE_TRIGGER_FIELD,
    RESULT_FIELD,
    TRIGGER_FIELD,
    TRIGGER_VALUES,
    VERSION_FIELD,
    WORKFLOW_ACTION_FIELD,
    collect_queue_preflight_errors,
    resolve_document_link_binding,
)
from tools.process_review_start_queue import (
    INITIAL_RESULT_FIELD,
    LANG_FIELD,
    PR_URL_FIELD,
    REMARKS_FIELD,
    REVIEW_START_ACTION_LABEL,
    REVIEW_STATUS_FIELD,
    REVIEW_TRIGGER_FIELD,
    collect_review_start_preflight_errors,
    parse_review_start_records,
    resolve_review_init_binding,
)


@dataclass(frozen=True)
class QueueQueryRow:
    queue_scope: str
    record_id: str
    document_id: str
    document_key: str
    build_family: str
    lang: str
    version: str
    workflow_action: str
    normalized_workflow_action: str | None
    git_ref: str
    document_link: str
    document_directory: str
    result: str
    pr_url: str
    review_status: str
    review_trigger_enabled: bool | None
    build_trigger_requested: bool | None
    immediate_build: bool | None
    initial_result: str
    remarks: str


@dataclass(frozen=True)
class InferredQueueQuery:
    document_id: str = ""
    document_key: str = ""
    build_family: str = ""
    lang: str = ""
    document_version: str = ""
    query_workflow_action: str = ""
    result_contains: str = ""
    queue_scope: str = "all"


def _text(value: Any) -> str:
    return scalar_text(value).strip()


_VERSION_TOKEN_RE = re.compile(r"^\d+(?:\.\d+)+$")
_UNDERSCORE_TOKEN_RE = re.compile(r"[A-Za-z0-9.-]+(?:_[A-Za-z0-9.-]+)+")
_QUERY_TOKEN_RE = re.compile(r"[A-Za-z0-9_.-]+")
_MODEL_TOKEN_RE = re.compile(r"^(?=.*\d)[A-Za-z0-9]+(?:-[A-Za-z0-9]+)+$")
_REGION_TOKEN_RE = re.compile(r"^[A-Za-z]{2,3}$")
_BUILD_FAMILY_TOKEN_RE = re.compile(r"^[a-z]{2,}(?:-[a-z][a-z0-9]*)+$")
_LANG_CODES = {"en", "fr", "es", "ja", "jp", "zh", "cn", "de", "it", "pt", "ko"}


def _query_tokens(text: str) -> list[str]:
    return _QUERY_TOKEN_RE.findall(text)


def _is_probable_lang_token(token: str) -> bool:
    return token.strip().lower() in _LANG_CODES


def _infer_document_filters(text: str) -> tuple[str, str, str, str]:
    for token in _UNDERSCORE_TOKEN_RE.findall(text):
        parts = token.split("_")
        if len(parts) >= 3 and _VERSION_TOKEN_RE.match(parts[-1]):
            return token, "", "", ""
    for token in _UNDERSCORE_TOKEN_RE.findall(text):
        parts = token.split("_")
        if len(parts) == 2:
            return "", token, "", ""

    tokens = _query_tokens(text)
    for index, token in enumerate(tokens):
        if "_" in token or not _MODEL_TOKEN_RE.match(token):
            continue
        if index + 1 >= len(tokens):
            continue
        region_token = tokens[index + 1]
        if not _REGION_TOKEN_RE.match(region_token):
            continue
        region = region_token.upper()
        lang = ""
        version = ""
        if index + 2 < len(tokens):
            third = tokens[index + 2]
            if _VERSION_TOKEN_RE.match(third):
                version = third
            elif _is_probable_lang_token(third):
                lang = third.lower()
                if index + 3 < len(tokens) and _VERSION_TOKEN_RE.match(tokens[index + 3]):
                    version = tokens[index + 3]
        if version:
            if lang:
                return f"{token}_{region}_{lang}_{version}", "", "", ""
            return f"{token}_{region}_{version}", "", "", ""
        document_key = f"{token}_{region}"
        return "", document_key, lang, ""
    return "", "", "", ""


def _infer_build_family(text: str) -> str:
    for token in _query_tokens(text):
        lowered = token.lower()
        if not _BUILD_FAMILY_TOKEN_RE.match(lowered):
            continue
        if _MODEL_TOKEN_RE.match(token) or "_" in token:
            continue
        return lowered
    return ""


def _normalize_query_workflow_action(value: str | None) -> str | None:
    text = _text(value).lower()
    if not text:
        return None
    aliases = {
        "start-review": "start_review",
        "start_review": "start_review",
        "start review": "start_review",
        "review-init": "start_review",
        "review_init": "start_review",
        "build-draft": "draft",
        "build draft": "draft",
        "build-draft-package": "draft",
        "build draft package": "draft",
        "draft": "draft",
        "publish": "publish",
    }
    normalized = aliases.get(text)
    if normalized:
        return normalized
    raise RuntimeError(
        "--query-workflow-action must be one of: start-review, build-draft-package, publish"
    )


def infer_queue_query_from_text(raw_text: str | None) -> InferredQueueQuery:
    text = _text(raw_text).replace("\\_", "_")
    if not text:
        return InferredQueueQuery()

    normalized_text = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
    workflow_action = ""
    queue_scope = "all"
    result_contains = ""

    if any(needle in normalized_text for needle in ("build draft package", "build draft", "draft package")) or "草稿" in text:
        workflow_action = "build-draft-package"
        queue_scope = "document-link"
    elif "publish" in normalized_text or "发布" in text:
        workflow_action = "publish"
        queue_scope = "document-link"
    elif (
        any(needle in normalized_text for needle in ("start review", "review init"))
        or re.search(r"(开始|进入|拉进)\s*review", text, flags=re.IGNORECASE)
        or "进入review" in text
        or "拉进review" in text
    ):
        workflow_action = "start-review"
        queue_scope = "review-init"

    if any(needle in normalized_text for needle in ("document link", "latest link")) or "链接" in text:
        queue_scope = "document-link"
    if any(needle in normalized_text for needle in ("failed", "failure")) or "失败" in text:
        result_contains = "fail"
        queue_scope = "document-link"

    document_id, document_key, lang, document_version = _infer_document_filters(text)
    build_family = ""
    if not document_id and not document_key:
        build_family = _infer_build_family(text)

    return InferredQueueQuery(
        document_id=document_id,
        document_key=document_key,
        build_family=build_family,
        lang=lang,
        document_version=document_version,
        query_workflow_action=workflow_action,
        result_contains=result_contains,
        queue_scope=queue_scope,
    )


def apply_inferred_queue_query(args: argparse.Namespace) -> argparse.Namespace:
    inferred = infer_queue_query_from_text(getattr(args, "query_text", None))
    merged = argparse.Namespace(**vars(args))
    if not getattr(merged, "document_id", None) and inferred.document_id:
        merged.document_id = inferred.document_id
    if not getattr(merged, "document_key", None) and inferred.document_key:
        merged.document_key = inferred.document_key
    if not getattr(merged, "build_family", None) and inferred.build_family:
        merged.build_family = inferred.build_family
    if not getattr(merged, "lang", None) and inferred.lang:
        merged.lang = inferred.lang
    if not getattr(merged, "document_version", None) and inferred.document_version:
        merged.document_version = inferred.document_version
    if not getattr(merged, "query_workflow_action", None) and inferred.query_workflow_action:
        merged.query_workflow_action = inferred.query_workflow_action
    if not getattr(merged, "result_contains", None) and inferred.result_contains:
        merged.result_contains = inferred.result_contains
    if getattr(merged, "queue_scope", "all") == "all" and inferred.queue_scope != "all":
        merged.queue_scope = inferred.queue_scope
    return merged


def _match_exact(actual: str, expected: str | None) -> bool:
    if not expected:
        return True
    return actual.strip().lower() == expected.strip().lower()


def _match_contains(actual: str, expected: str | None) -> bool:
    if not expected:
        return True
    return expected.strip().lower() in actual.strip().lower()


def _build_document_link_rows(cfg: dict[str, Any]) -> list[QueueQueryRow]:
    errors = collect_queue_preflight_errors(cfg)
    if errors:
        raise RuntimeError("queue-query preflight failed:\n- " + "\n- ".join(errors))
    binding = resolve_document_link_binding(cfg)
    source = LarkCliSource(cli_bin=cli_bin(cfg), identity=phase2_identity())
    raw_records = source.fetch_records_with_ids(
        base_token=binding.base_token,
        table_id=binding.table_id,
        view_id=binding.view_id,
    )
    rows: list[QueueQueryRow] = []
    for raw_record in raw_records:
        fields_raw = raw_record.get("fields", {})
        fields = fields_raw if isinstance(fields_raw, dict) else {}
        workflow_action = _text(fields.get(WORKFLOW_ACTION_FIELD))
        rows.append(
            QueueQueryRow(
                queue_scope="document-link",
                record_id=_text(raw_record.get("record_id")),
                document_id=_text(fields.get(DOCUMENT_ID_FIELD)),
                document_key=_text(fields.get(DOCUMENT_KEY_FIELD)),
                build_family=_text(fields.get(BUILD_FAMILY_FIELD)).lower(),
                lang=_text(fields.get(LANG_FIELD)).lower(),
                version=_text(fields.get(VERSION_FIELD)),
                workflow_action=workflow_action,
                normalized_workflow_action=best_effort_queue_workflow_action(
                    workflow_action=workflow_action,
                    doc_phase="",
                    record_id=_text(raw_record.get("record_id")),
                ),
                git_ref=_text(fields.get(GIT_REF_FIELD)),
                document_link=_text(fields.get(DOCUMENT_LINK_FIELD)),
                document_directory=_text(fields.get(DOCUMENT_DIRECTORY_FIELD)),
                result=_text(fields.get(RESULT_FIELD)),
                pr_url="",
                review_status="",
                review_trigger_enabled=None,
                build_trigger_requested=_text(fields.get(TRIGGER_FIELD)).lower() in TRIGGER_VALUES,
                immediate_build=is_immediate_trigger_enabled(fields.get(IMMEDIATE_TRIGGER_FIELD)),
                initial_result="",
                remarks="",
            )
        )
    return rows


def _build_review_init_rows(cfg: dict[str, Any]) -> list[QueueQueryRow]:
    errors = collect_review_start_preflight_errors(cfg, require_github=False)
    if errors:
        raise RuntimeError("queue-query preflight failed:\n- " + "\n- ".join(errors))
    binding = resolve_review_init_binding(cfg)
    source = LarkCliSource(cli_bin=cli_bin(cfg), identity=phase2_identity())
    raw_records = source.fetch_records_with_ids(
        base_token=binding.base_token,
        table_id=binding.table_id,
        view_id=binding.view_id,
    )
    rows: list[QueueQueryRow] = []
    for raw_record in raw_records:
        fields_raw = raw_record.get("fields", {})
        fields = fields_raw if isinstance(fields_raw, dict) else {}
        parsed_records = parse_review_start_records([raw_record])
        parsed = parsed_records[0]
        rows.append(
            QueueQueryRow(
                queue_scope="review-init",
                record_id=parsed.record_id,
                document_id=parsed.document_id,
                document_key=parsed.document_key,
                build_family=parsed.build_family,
                lang=parsed.lang,
                version=parsed.version,
                workflow_action=_text(fields.get(WORKFLOW_ACTION_FIELD)) or REVIEW_START_ACTION_LABEL,
                normalized_workflow_action="start_review",
                git_ref=parsed.git_ref,
                document_link="",
                document_directory="",
                result="",
                pr_url=parsed.pr_url,
                review_status=parsed.review_status,
                review_trigger_enabled=is_immediate_trigger_enabled(parsed.review_trigger_value),
                build_trigger_requested=None,
                immediate_build=None,
                initial_result=_text(fields.get(INITIAL_RESULT_FIELD)),
                remarks=_text(fields.get(REMARKS_FIELD)),
            )
        )
    return rows


def collect_queue_query_rows(cfg: dict[str, Any], *, queue_scope: str) -> list[QueueQueryRow]:
    if queue_scope == "document-link":
        return _build_document_link_rows(cfg)
    if queue_scope == "review-init":
        return _build_review_init_rows(cfg)
    if queue_scope == "all":
        return [*_build_review_init_rows(cfg), *_build_document_link_rows(cfg)]
    raise RuntimeError(f"Unsupported queue scope: {queue_scope}")


def filter_queue_query_rows(args: argparse.Namespace, rows: list[QueueQueryRow]) -> list[QueueQueryRow]:
    normalized_action = _normalize_query_workflow_action(getattr(args, "query_workflow_action", None))
    filtered: list[QueueQueryRow] = []
    for row in rows:
        if getattr(args, "record_id", None) and row.record_id != args.record_id:
            continue
        if not _match_exact(row.document_id, getattr(args, "document_id", None)):
            continue
        if not _match_exact(row.document_key, getattr(args, "document_key", None)):
            continue
        if not _match_exact(row.build_family, getattr(args, "build_family", None)):
            continue
        if not _match_exact(row.lang, getattr(args, "lang", None)):
            continue
        if not _match_exact(row.version, getattr(args, "document_version", None)):
            continue
        if normalized_action and row.normalized_workflow_action != normalized_action:
            continue
        if not _match_contains(row.git_ref, getattr(args, "git_ref_contains", None)):
            continue
        if not _match_contains(row.result, getattr(args, "result_contains", None)):
            continue
        filtered.append(row)
    return filtered[: max(int(getattr(args, "limit", 10) or 10), 1)]


def _row_title(row: QueueQueryRow) -> str:
    action = workflow_action_label(row.workflow_action) if row.queue_scope == "document-link" else REVIEW_START_ACTION_LABEL
    action_text = action or row.workflow_action or row.normalized_workflow_action or ""
    return f"{row.queue_scope} {row.record_id} {row.document_id or row.document_key}".strip() + (
        f" [{action_text}]" if action_text else ""
    )


def render_queue_query_rows(rows: list[QueueQueryRow], *, as_json: bool) -> str:
    if as_json:
        return json.dumps(
            {
                "count": len(rows),
                "rows": [asdict(row) for row in rows],
            },
            ensure_ascii=False,
            indent=2,
        )
    if not rows:
        return "No matching queue rows."
    blocks: list[str] = []
    for row in rows:
        lines = [
            _row_title(row),
            f"record_id: {row.record_id}",
        ]
        if row.document_id:
            lines.append(f"document_id: {row.document_id}")
        if row.document_key:
            lines.append(f"document_key: {row.document_key}")
        if row.build_family:
            lines.append(f"build_family: {row.build_family}")
        if row.lang:
            lines.append(f"lang: {row.lang}")
        if row.version:
            lines.append(f"version: {row.version}")
        if row.workflow_action:
            lines.append(f"workflow_action: {row.workflow_action}")
        if row.git_ref:
            lines.append(f"git_ref: {row.git_ref}")
        if row.pr_url:
            lines.append(f"pr_url: {row.pr_url}")
        if row.document_link:
            lines.append(f"document_link: {row.document_link}")
        if row.document_directory:
            lines.append(f"document_directory: {row.document_directory}")
        if row.result:
            lines.append(f"result: {row.result}")
        if row.review_status:
            lines.append(f"review_status: {row.review_status}")
        if row.review_trigger_enabled is not None:
            lines.append(f"review_trigger_enabled: {str(row.review_trigger_enabled).lower()}")
        if row.immediate_build is not None:
            lines.append(f"immediate_build: {str(row.immediate_build).lower()}")
        if row.build_trigger_requested is not None:
            lines.append(f"build_trigger_requested: {str(row.build_trigger_requested).lower()}")
        if row.initial_result:
            lines.append(f"initial_result: {row.initial_result}")
        if row.remarks:
            lines.append(f"remarks: {row.remarks}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def run_queue_query(args: argparse.Namespace, *, config_path) -> None:
    resolved_args = apply_inferred_queue_query(args)
    cfg = load_config(config_path)
    rows = collect_queue_query_rows(cfg, queue_scope=resolved_args.queue_scope)
    filtered = filter_queue_query_rows(resolved_args, rows)
    print(render_queue_query_rows(filtered, as_json=resolved_args.json))


if __name__ == "__main__":
    raise SystemExit("Use `python build.py queue-query ...`.")
