from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from typing import Any, Callable

from tools.document_link_queue import looks_like_explicit_document_key
from tools.review_branch_resolver import parse_document_id
from tools.language_aliases import normalize_language

DOCUMENT_ID_FIELD = "Document_ID"
DOCUMENT_KEY_FIELD = "Document_Key"
BUILD_FAMILY_FIELD = "Build_family"
VERSION_FIELD = "Version"
LANG_FIELD = "Lang"
WORKFLOW_ACTION_FIELD = "Workflow_action"
REVIEW_TRIGGER_FIELD = "是否进入Review"
REVIEW_STATUS_FIELD = "Review_status"
GIT_REF_FIELD = "Git_ref"
PR_URL_FIELD = "PR_url"
TASK_ID_FIELD = "Task_id"

REVIEW_STATUS_NOT_STARTED = "NotStarted"
REVIEW_STATUS_IN_REVIEW = "InReview"


@dataclass(frozen=True)
class ReviewStartRecord:
    record_id: str
    document_id: str
    document_key: str
    build_family: str
    version: str
    lang: str
    workflow_action: str = ""
    review_status: str = ""
    review_trigger_value: Any = None
    git_ref: str = ""
    pr_url: str = ""
    task_id: str = ""

    @property
    def label(self) -> str:
        if self.document_id:
            return self.document_id
        task_key = document_key_from_task_id(self.task_id)
        if task_key:
            return task_key
        if self.document_key and self.lang:
            return f"{self.document_key}_{self.lang}"
        return self.document_key or self.record_id


def scalar_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        for item in value:
            text = scalar_text(item)
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
        for key in ("text", "name", "label", "title", "value"):
            text = scalar_text(value.get(key))
            if text:
                return text
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return str(value).strip()


def normalized_build_family(value: Any) -> str:
    return scalar_text(value).strip().lower()


def is_checkbox_enabled(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = scalar_text(value).strip().lower()
    return text in {"1", "true", "y", "yes", "checked"}


def normalize_review_status(value: Any) -> str | None:
    text = scalar_text(value).strip().lower()
    if not text:
        return None
    if text in {"notstarted", "not_started", "not started"}:
        return "notstarted"
    if text in {"inreview", "in_review", "in review"}:
        return "inreview"
    if text in {"readyforpublish", "ready_for_publish", "ready for publish"}:
        return "readyforpublish"
    return text


def normalize_review_start_action(value: Any) -> str | None:
    text = re.sub(r"[^a-z0-9]+", " ", scalar_text(value).strip().lower()).strip()
    if not text:
        return None
    if text in {"start review", "seed draft", "start review seed draft", "start_review", "seed_draft"}:
        return "start_review"
    raise RuntimeError("Workflow_action must map to Start Review for review-init rows")


def parse_review_start_records(raw_records: list[dict[str, Any]]) -> list[ReviewStartRecord]:
    records: list[ReviewStartRecord] = []
    for record in raw_records:
        record_id = str(record.get("record_id") or "").strip()
        if not record_id:
            raise RuntimeError("Review-init record list is missing record_id")
        fields_raw = record.get("fields", {})
        fields = fields_raw if isinstance(fields_raw, dict) else {}
        records.append(
            ReviewStartRecord(
                record_id=record_id,
                document_id=scalar_text(fields.get(DOCUMENT_ID_FIELD)),
                document_key=scalar_text(fields.get(DOCUMENT_KEY_FIELD)),
                build_family=normalized_build_family(fields.get(BUILD_FAMILY_FIELD)),
                version=scalar_text(fields.get(VERSION_FIELD)),
                lang=normalize_language(scalar_text(fields.get(LANG_FIELD))),
                workflow_action=scalar_text(fields.get(WORKFLOW_ACTION_FIELD)),
                review_status=scalar_text(fields.get(REVIEW_STATUS_FIELD)),
                review_trigger_value=fields.get(REVIEW_TRIGGER_FIELD),
                git_ref=scalar_text(fields.get(GIT_REF_FIELD)),
                pr_url=scalar_text(fields.get(PR_URL_FIELD)),
                task_id=scalar_text(fields.get(TASK_ID_FIELD)),
            )
        )
    return records


def select_pending_review_start_records(
    raw_records: list[dict[str, Any]],
    *,
    record_id: str | None = None,
) -> list[ReviewStartRecord]:
    selected: list[ReviewStartRecord] = []
    for record in parse_review_start_records(raw_records):
        if record_id and record.record_id != record_id:
            continue
        if not is_checkbox_enabled(record.review_trigger_value):
            continue
        if not record.document_key.strip():
            if record_id:
                raise RuntimeError(
                    f"Document_Key must be non-empty for review-start record {record.record_id}"
                )
            continue
        try:
            normalize_review_start_action(record.workflow_action)
        except RuntimeError as exc:
            if record_id:
                raise RuntimeError(
                    "Workflow_action must map to Start Review "
                    f"for review-start record {record.record_id}"
                ) from exc
            continue
        selected.append(record)
    return selected


def slug_branch_token(value: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return text or "review"


def generate_review_branch_name(record: ReviewStartRecord) -> str:
    # Review is versionless: one branch per (model, region) — the template target — named
    # review/<MODEL>-<REGION> (the _review tree is per model+region; git_branching_guide
    # §2). Derive the canonical name from the Document_ID's model+region.
    parsed = parse_document_id(record.document_id)
    existing = record.git_ref.strip()
    if parsed is not None:
        model, region, _version = parsed
        canonical = f"review/{model}-{region}"
        # Keep an existing CANONICAL ref (review/<MODEL>-<REGION>[-<topic>]) so an
        # in-flight review reuses its branch. A legacy/opaque ref (e.g.
        # review/id-<record_id>, codex/review-…) is RE-DERIVED to the canonical name, so
        # a re-seed self-heals the branch name instead of preserving the stale value.
        if existing and (existing == canonical or existing.startswith(f"{canonical}-")):
            return existing
        if existing:  # non-empty AND non-canonical -> self-heal
            print(
                f"[review-start] WARNING healing non-canonical branch name {existing!r} -> "
                f"{canonical!r}; the old branch's PR (if any) is NOT reused.",
                file=sys.stderr,
            )
        return canonical
    # Document_ID yields no model+region: keep an existing ref, else a sanitized slug.
    if existing:
        return existing
    source = record.document_key or record.document_id or f"{record.lang}_{record.version}"
    return f"review/{slug_branch_token(source)[:72]}"


def document_key_from_document_id(*, document_id: str, lang: str, version: str) -> str:
    candidate = document_id.strip()
    version_text = version.strip()
    lang_text = normalize_language(lang)
    if version_text and candidate.endswith("_" + version_text):
        candidate = candidate[: -(len(version_text) + 1)]
    lang_suffixes = {lang_text.casefold()}
    if lang_text.casefold() == "pt-br":
        lang_suffixes.add("br")
    for lang_suffix in sorted(lang_suffixes, key=len, reverse=True):
        if lang_suffix and candidate.casefold().endswith("_" + lang_suffix):
            candidate = candidate[: -(len(lang_suffix) + 1)]
            break
    return candidate.strip()


def document_key_from_task_id(task_id: str) -> str:
    text = scalar_text(task_id).strip()
    if not text:
        return ""
    candidate = re.sub(
        r"[\s_:-]+start[\s_-]+review$",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip(" _:-")
    if looks_like_explicit_document_key(candidate):
        return candidate
    return ""


def resolve_target_for_review_start(
    record: ReviewStartRecord,
    *,
    parse_document_key: Callable[[str], tuple[str, str]],
) -> tuple[str, str]:
    candidates: list[str] = []
    if looks_like_explicit_document_key(record.document_key):
        candidates.append(record.document_key.strip())
    fallback_key = document_key_from_document_id(
        document_id=record.document_id,
        lang=record.lang,
        version=record.version,
    )
    if fallback_key and fallback_key not in candidates:
        candidates.append(fallback_key)
    task_key = document_key_from_task_id(record.task_id)
    if task_key and task_key not in candidates:
        candidates.append(task_key)

    errors: list[str] = []
    for candidate in candidates:
        try:
            return parse_document_key(candidate)
        except RuntimeError as exc:
            errors.append(str(exc))

    detail = (
        f"Document_ID={record.document_id!r}, "
        f"Document_Key={record.document_key!r}, "
        f"Task_id={record.task_id!r}, "
        f"Build_family={record.build_family!r}, "
        f"Lang={record.lang!r}"
    )
    if errors:
        raise RuntimeError("Unable to resolve review-start target. " + detail + " | " + " | ".join(errors))
    raise RuntimeError("Unable to resolve review-start target. " + detail)


def review_start_record_key(record: ReviewStartRecord) -> str:
    if looks_like_explicit_document_key(record.document_key):
        return record.document_key.strip().upper()
    fallback_key = document_key_from_document_id(
        document_id=record.document_id,
        lang=record.lang,
        version=record.version,
    )
    if looks_like_explicit_document_key(fallback_key):
        return fallback_key.upper()
    task_key = document_key_from_task_id(record.task_id)
    if task_key:
        return task_key.upper()
    return record.record_id


def review_start_group_key(record: ReviewStartRecord) -> str:
    if looks_like_explicit_document_key(record.document_key):
        return record.document_key.strip().upper()
    return record.record_id


def group_review_start_records(
    records: list[ReviewStartRecord],
    *,
    resolve_target_for_review_start: Callable[[ReviewStartRecord], tuple[str, str]] | None = None,
    resolve_config_path_for_task: Callable[..., Any] | None = None,
    load_config: Callable[..., dict[str, Any]] | None = None,
) -> list[list[ReviewStartRecord]]:
    grouped: list[list[ReviewStartRecord]] = []
    index_by_key: dict[str, int] = {}
    for record in records:
        key = review_start_group_key(record)
        existing_index = index_by_key.get(key)
        if existing_index is None:
            index_by_key[key] = len(grouped)
            grouped.append([record])
            continue
        grouped[existing_index].append(record)
    return grouped


def review_start_group_build_family(records: list[ReviewStartRecord]) -> str:
    for record in records:
        build_family = normalized_build_family(record.build_family)
        if build_family:
            return build_family
    return ""


def review_start_group_lang(records: list[ReviewStartRecord]) -> str:
    for record in records:
        if record.lang.strip():
            return normalize_language(record.lang)
    return ""


def validate_review_start_group(records: list[ReviewStartRecord]) -> None:
    if not records:
        return
    if len(records) == 1:
        return

    group_key = review_start_record_key(records[0])
    versions = {record.version.strip() for record in records}
    git_refs = {record.git_ref.strip() for record in records}
    build_families = {review_start_group_build_family([record]) for record in records}
    build_families.discard("")
    conflicts: list[str] = []
    if len(versions) > 1:
        conflicts.append("Version")
    if len(git_refs) > 1:
        conflicts.append("Git_ref")
    if len(build_families) > 1:
        conflicts.append("Build_family")
    if conflicts:
        raise RuntimeError(
            "Review-start rows merged by Document_Key must agree on "
            + ", ".join(conflicts)
            + f": {group_key}"
        )
