from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass, replace
from typing import Any

from tools.document_link_actions import (
    best_effort_queue_workflow_action,
    workflow_action_label,
)
from tools.document_link_queue import (
    is_immediate_trigger_enabled,
    scalar_text,
)
from tools.language_aliases import normalize_language
from tools.phase2_support import (
    LarkCliSource,
    cli_bin,
    load_config,
    phase2_identity,
)
from tools.process_build_queue import (
    BUILD_FAMILY_FIELD,
    BUILD_STARTED_AT_FIELD,
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
from tools.queue_freshness import (
    compute_freshness,
    isoformat_timestamp,
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
    normalize_review_start_action,
    parse_review_start_records,
    resolve_review_init_binding,
)

TASK_ID_FIELD = "Task_id"
MARKET_GROUP_FIELD = "Market_Group"
MARKET_FIELD = "Market"
_TASK_ACTION_LABELS = {
    "start-review": "Start Review",
    "start_review": "Start Review",
    "start review": "Start Review",
    "build-draft": "Build Draft Package",
    "build_draft": "Build Draft Package",
    "build draft": "Build Draft Package",
    "build-draft-package": "Build Draft Package",
    "build draft package": "Build Draft Package",
    "draft": "Build Draft Package",
    "publish": "Publish",
}
_ACTION_LABEL_TO_QUERY = {
    "start review": "start-review",
    "build draft package": "build-draft-package",
    "publish": "publish",
}


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
    task_id: str = ""
    market_group: str = ""
    build_started_at: str = ""
    result_built_at: str = ""
    result_is_fresh: bool | None = None
    freshness_status: str = "not_requested"


@dataclass(frozen=True)
class InferredQueueQuery:
    record_id: str = ""
    task_id: str = ""
    task_id_prefix: str = ""
    document_id: str = ""
    document_key: str = ""
    document_keys: tuple[str, ...] = ()
    build_family: str = ""
    lang: str = ""
    langs: tuple[str, ...] = ()
    document_version: str = ""
    query_workflow_action: str = ""
    result_contains: str = ""
    latest_per_document_key: bool = False
    queue_scope: str = "all"
    market_group: str = ""
    allow_multiple: bool = False
    recommended_limit: int = 0


@dataclass(frozen=True)
class QueueQueryResult:
    rows: list[QueueQueryRow]
    matched_count: int
    returned_count: int
    limit: int
    truncated: bool


def _text(value: Any) -> str:
    return scalar_text(value).strip()


_VERSION_TOKEN_RE = re.compile(r"^\d+(?:\.\d+)+$")
_RECORD_ID_RE = re.compile(r"\b(rec[A-Za-z0-9_]+)\b")
_TASK_DOCUMENT_ID_RE = r"(?P<document_id>[A-Za-z0-9.-]+_[A-Za-z]{2,3}(?:_[A-Za-z]{2})?_\d+(?:\.\d+)*)"
_UNDERSCORE_TOKEN_RE = re.compile(r"[A-Za-z0-9.-]+(?:_[A-Za-z0-9.-]+)+")
_QUERY_TOKEN_RE = re.compile(r"[A-Za-z0-9_.-]+")
_MODEL_TOKEN_RE = re.compile(r"^(?=.*\d)[A-Za-z0-9]+(?:-[A-Za-z0-9]+)+$")
_REGION_TOKEN_RE = re.compile(r"^[A-Za-z]{2,3}$")
_BUILD_FAMILY_TOKEN_RE = re.compile(r"^[a-z]{2,}(?:-[a-z][a-z0-9]*)+$")
_LANG_CODES = {"en", "fr", "es", "ja", "jp", "zh", "cn", "de", "it", "pt", "br", "pt-br", "ko", "uk"}
_LANG_ALIASES = {
    "英语": "en",
    "英文": "en",
    "english": "en",
    "法语": "fr",
    "法文": "fr",
    "french": "fr",
    "西语": "es",
    "西班牙语": "es",
    "spanish": "es",
    "德语": "de",
    "德文": "de",
    "german": "de",
    "意语": "it",
    "意大利语": "it",
    "italian": "it",
    "日语": "ja",
    "日文": "ja",
    "japanese": "ja",
    "中文": "zh",
    "汉语": "zh",
    "chinese": "zh",
    "葡语": "pt",
    "葡萄牙语": "pt",
    "portuguese": "pt-BR",
    "brazilian portuguese": "pt-BR",
    "pt-br": "pt-BR",
    "pt_br": "pt-BR",
    "br": "pt-BR",
    "韩语": "ko",
    "韩文": "ko",
    "korean": "ko",
    "乌克兰语": "uk",
    "乌语": "uk",
    "ukrainian": "uk",
}
_LANG_NAME_PATTERN = re.compile("|".join(re.escape(name) for name in sorted(_LANG_ALIASES, key=len, reverse=True)), re.IGNORECASE)
_MARKET_ALIASES = {
    "欧规": "EU",
    "欧洲": "EU",
    "欧盟": "EU",
    "美规": "US",
    "美国": "US",
    "日规": "JP",
    "日本": "JP",
    "中规": "CN",
    "中国": "CN",
}
_LATIN_MARKET_ALIASES = {
    "eu": "EU",
    "us": "US",
    "jp": "JP",
    "ja": "JP",
    "cn": "CN",
}
_BATCH_KEYWORDS = (
    "所有",
    "全部",
    "全量",
    "整包",
    "整套",
    "全语种",
    "多语言",
    "每个",
    "各个",
    "所有语言",
    "全部语言",
    "all",
    "every",
    "each",
)
_BUILD_DRAFT_INTENT_KEYWORDS = (
    "输出",
    "生成",
    "构建",
    "创建",
    "制作",
    "发起",
    "触发",
    "重跑",
    "重新构建",
    "重新跑",
    "补跑",
    "补构建",
    "补触发",
    "重试",
)
_CONFIG_BATCH_CONTENT_KEYWORDS = (
    "说明书文案",
    "说明书",
    "文案",
    "文档",
    "手册",
    "整包",
    "整套",
    "语种",
    "配置",
    "构建要求",
    "manual copy",
    "manual",
    "copy",
)
_DEFAULT_QUEUE_QUERY_LIMIT = 10
_BUILT_LINK_INVENTORY_LIMIT = 200


def _query_tokens(text: str) -> list[str]:
    return _QUERY_TOKEN_RE.findall(text)


def _normalize_langs(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (list, tuple, set)):
        raw_parts = [str(item or "") for item in value]
    else:
        raw_parts = re.split(r"[,，/、\s]+", str(value or ""))
    langs: list[str] = []
    for raw_part in raw_parts:
        part = raw_part.strip().lower()
        if not part:
            continue
        normalized = _LANG_ALIASES.get(part, part)
        if normalized == "jp":
            normalized = "ja"
        if normalized == "cn":
            normalized = "zh"
        if normalized in {"pt", "br", "pt-br"}:
            normalized = "pt-BR"
        if (normalized in _LANG_CODES or normalized == "pt-BR") and normalized not in langs:
            langs.append(normalized)
    return tuple(langs)


def _infer_langs(text: str) -> tuple[str, ...]:
    langs: list[str] = []
    for match in _LANG_NAME_PATTERN.finditer(text):
        lang = _LANG_ALIASES.get(match.group(0).lower())
        if lang and lang not in langs:
            langs.append(lang)
    tokens = {token.lower() for token in _query_tokens(text)}
    for token in tokens:
        if token in _LANG_CODES:
            normalized = "ja" if token == "jp" else "zh" if token == "cn" else token
            if normalized in {"pt", "br", "pt-br"}:
                normalized = "pt-BR"
            if normalized not in langs:
                langs.append(normalized)
    return tuple(langs)


def _normalize_task_id(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", " ", _text(value).lower()).strip()


def _match_task_id_prefix(actual: str, prefix: str | None) -> bool:
    normalized_prefix = _normalize_task_id(prefix)
    if not normalized_prefix:
        return True
    return _normalize_task_id(actual).startswith(normalized_prefix)


def _action_label_pattern(label: str) -> str:
    return r"[\s_-]+".join(re.escape(part) for part in label.split())


def _canonical_query_action_label(value: str | None) -> str:
    return _TASK_ACTION_LABELS.get(_text(value).lower(), "")


def _workflow_action_for_task_label(label: str) -> str:
    return _ACTION_LABEL_TO_QUERY.get(_normalize_task_id(label), "")


def _infer_task_id_filters(text: str) -> tuple[str, str, str]:
    for action_label in ("Build Draft Package", "Start Review", "Publish"):
        pattern = re.compile(
            _TASK_DOCUMENT_ID_RE + r"[\s_:-]+" + _action_label_pattern(action_label),
            flags=re.IGNORECASE,
        )
        match = pattern.search(text)
        if match:
            document_id = match.group("document_id")
            return f"{document_id}_{action_label}", document_id, _workflow_action_for_task_label(action_label)
    return "", "", ""


def _action_label_for_row(row: QueueQueryRow) -> str:
    mapping = {
        "start_review": "Start Review",
        "draft": "Build Draft Package",
        "publish": "Publish",
    }
    if row.normalized_workflow_action in mapping:
        return mapping[row.normalized_workflow_action]
    if row.workflow_action:
        return workflow_action_label(row.workflow_action) or row.workflow_action
    return ""


def _row_task_id(row: QueueQueryRow) -> str:
    if row.task_id:
        return row.task_id
    action_label = _action_label_for_row(row)
    if row.document_id and action_label:
        return f"{row.document_id}_{action_label}"
    if row.document_key and action_label and row.normalized_workflow_action == "start_review":
        return f"{row.document_key}_{action_label}"
    return ""


def _is_probable_lang_token(token: str) -> bool:
    return token.strip().lower() in _LANG_CODES


def _version_sort_key(version: str) -> tuple[int, tuple[int, ...], str]:
    text = version.strip()
    if not text:
        return (0, (), "")
    normalized = text[1:] if text[:1].lower() == "v" else text
    if re.fullmatch(r"\d+(?:\.\d+)*", normalized):
        return (1, tuple(int(part) for part in normalized.split(".")), normalized)
    return (0, (), normalized.lower())


def _row_version(row: QueueQueryRow) -> str:
    if row.version:
        return row.version
    parts = row.document_id.split("_")
    if parts and _VERSION_TOKEN_RE.match(parts[-1]):
        return parts[-1]
    return ""


def _row_latest_group_key(row: QueueQueryRow) -> str:
    if row.document_key:
        return row.document_key
    parts = row.document_id.split("_")
    if len(parts) >= 3 and _VERSION_TOKEN_RE.match(parts[-1]):
        return "_".join(parts[:-1])
    return row.document_id or row.record_id


def _prefer_row_for_latest(candidate: QueueQueryRow, current: QueueQueryRow) -> bool:
    candidate_version = _version_sort_key(_row_version(candidate))
    current_version = _version_sort_key(_row_version(current))
    if candidate_version != current_version:
        return candidate_version > current_version
    if bool(candidate.document_link) != bool(current.document_link):
        return bool(candidate.document_link)
    if ("success" in candidate.result.lower()) != ("success" in current.result.lower()):
        return "success" in candidate.result.lower()
    return False


def _latest_per_document_key(rows: list[QueueQueryRow]) -> list[QueueQueryRow]:
    selected: dict[str, QueueQueryRow] = {}
    order: list[str] = []
    for row in rows:
        key = _row_latest_group_key(row)
        if key not in selected:
            selected[key] = row
            order.append(key)
            continue
        if _prefer_row_for_latest(row, selected[key]):
            selected[key] = row
    return [selected[key] for key in order]


def _should_apply_latest_per_document_key(args: argparse.Namespace, normalized_action: str | None) -> bool:
    if not getattr(args, "latest_per_document_key", False):
        return False
    if getattr(args, "allow_multiple", False) and normalized_action in {"draft", "publish"}:
        return False
    return True


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


def _looks_like_document_key_token(token: str) -> bool:
    parts = token.split("_")
    return len(parts) == 2 and _MODEL_TOKEN_RE.match(parts[0]) is not None and _REGION_TOKEN_RE.match(parts[1]) is not None


def _infer_document_key_tokens(text: str) -> tuple[str, ...]:
    keys: list[str] = []
    for token in _UNDERSCORE_TOKEN_RE.findall(text):
        if not _looks_like_document_key_token(token):
            continue
        model, region = token.split("_", 1)
        key = f"{model}_{region.upper()}"
        if key not in keys:
            keys.append(key)
    return tuple(keys)


def _infer_model_token(text: str) -> str:
    for token in _query_tokens(text):
        if "_" in token:
            continue
        if _MODEL_TOKEN_RE.match(token):
            return token
    return ""


def _infer_market_group(text: str) -> str:
    for alias, market in _MARKET_ALIASES.items():
        if alias in text:
            return market
    tokens = {token.lower() for token in _query_tokens(text)}
    for alias, market in _LATIN_MARKET_ALIASES.items():
        if alias in tokens:
            return market
    return ""


def _infer_build_family(text: str) -> str:
    for token in _query_tokens(text):
        lowered = token.lower()
        if not _BUILD_FAMILY_TOKEN_RE.match(lowered):
            continue
        if _MODEL_TOKEN_RE.match(token) or "_" in token:
            continue
        return lowered
    return ""


def _infer_allow_multiple(text: str) -> bool:
    normalized_text = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
    if any(keyword in text or keyword in normalized_text for keyword in _BATCH_KEYWORDS):
        return True
    return _has_config_batch_draft_intent(text, normalized_text)


def _has_config_batch_draft_intent(text: str, normalized_text: str) -> bool:
    document_id, document_key, _lang, _version = _infer_document_filters(text)
    has_region_version_target = bool(_split_region_version_document_id(document_id)[0])
    has_model_market_target = bool(_infer_model_token(text) and _infer_market_group(text))
    has_model_target = bool(_infer_model_token(text))
    if not (has_model_market_target or has_model_target or document_key or has_region_version_target):
        return False
    if not any(keyword in text or keyword in normalized_text for keyword in _BUILD_DRAFT_INTENT_KEYWORDS):
        return False
    return any(keyword in text or keyword in normalized_text for keyword in _CONFIG_BATCH_CONTENT_KEYWORDS)


def _has_successful_document_link_query_intent(text: str, normalized_text: str) -> bool:
    has_link_or_document = any(
        needle in text or needle in normalized_text
        for needle in (
            "链接",
            "文档",
            "说明书",
            "document link",
            "doc link",
            "document",
            "manual",
        )
    )
    has_successful_build = any(
        needle in text or needle in normalized_text
        for needle in (
            "已构建",
            "构建好",
            "构建成功",
            "构建完成",
            "成功构建",
            "built document",
            "build completed",
            "successfully built",
        )
    )
    return has_link_or_document and has_successful_build


def _has_inventory_query_intent(text: str, normalized_text: str) -> bool:
    inventory_keywords = (
        "当前所有",
        "现在所有",
        "所有",
        "全部",
        "全量",
        "完整",
        "清单",
        "列表",
        "多少",
        "数量",
        "库里",
        "all",
        "every",
        "inventory",
        "list",
        "count",
        "how many",
    )
    return any(keyword in text or keyword in normalized_text for keyword in inventory_keywords)


def _split_region_version_document_id(value: str) -> tuple[str, str, str]:
    parts = value.split("_")
    if len(parts) != 3 or not _VERSION_TOKEN_RE.match(parts[-1]):
        return "", "", ""
    model, region, version = parts
    if not _MODEL_TOKEN_RE.match(model) or not _REGION_TOKEN_RE.match(region):
        return "", "", ""
    return model, region.upper(), version


def _has_start_review_intent(text: str, normalized_text: str) -> bool:
    if any(needle in normalized_text for needle in ("start review", "review init")):
        return True
    if re.search(r"(开始|进入|拉进)\s*review", text, flags=re.IGNORECASE):
        return True
    if any(needle in text for needle in ("进入review", "拉进review")):
        return True
    return bool(re.search(r"\breview\b", normalized_text))


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

    inferred_langs = _infer_langs(text)
    task_id, task_document_id, task_workflow_action = _infer_task_id_filters(text)
    record_id = next(
        (
            match.group(1)
            for match in _RECORD_ID_RE.finditer(text)
            if match.group(1).lower() not in {"record", "records", "record_id", "recordid"}
        ),
        "",
    )
    normalized_text = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
    workflow_action = ""
    queue_scope = "all"
    result_contains = ""
    latest_per_document_key = False
    recommended_limit = 0
    successful_link_query = _has_successful_document_link_query_intent(text, normalized_text)
    inventory_link_query = successful_link_query and _has_inventory_query_intent(text, normalized_text)

    if task_workflow_action:
        workflow_action = task_workflow_action
        queue_scope = "review-init" if task_workflow_action == "start-review" else "document-link"
    elif any(needle in normalized_text for needle in ("build draft package", "build draft", "draft package")) or "草稿" in text:
        workflow_action = "build-draft-package"
        queue_scope = "document-link"
    elif not successful_link_query and (
        any(token in text for token in _BUILD_DRAFT_INTENT_KEYWORDS) or "manual copy" in normalized_text
    ):
        workflow_action = "build-draft-package"
        queue_scope = "document-link"
    elif "publish" in normalized_text or "发布" in text:
        workflow_action = "publish"
        queue_scope = "document-link"
    elif _has_start_review_intent(text, normalized_text):
        workflow_action = "start-review"
        queue_scope = "review-init"

    if any(needle in normalized_text for needle in ("document link", "latest link")) or "链接" in text:
        queue_scope = "document-link"
    if successful_link_query:
        queue_scope = "document-link"
        result_contains = "success"
        latest_per_document_key = not inventory_link_query
        if inventory_link_query:
            recommended_limit = _BUILT_LINK_INVENTORY_LIMIT
    if queue_scope == "document-link" and ("最新" in text or "latest" in normalized_text):
        latest_per_document_key = True
    if any(needle in normalized_text for needle in ("failed", "failure")) or "失败" in text:
        result_contains = "fail"
        queue_scope = "document-link"

    document_id, document_key, lang, document_version = _infer_document_filters(text)
    if not lang and len(inferred_langs) == 1:
        lang = inferred_langs[0]
    market_group = _infer_market_group(text)
    task_id_prefix = ""
    allow_multiple = _infer_allow_multiple(text)
    document_keys: tuple[str, ...] = ()
    if workflow_action == "start-review":
        inferred_document_keys = _infer_document_key_tokens(text)
        if len(inferred_document_keys) > 1:
            document_keys = inferred_document_keys
            document_id = ""
            document_key = ""
            lang = ""
            document_version = ""
            task_id = ""
            task_document_id = ""
            allow_multiple = True
    if workflow_action == "build-draft-package" and allow_multiple:
        if document_id:
            model_token, region, version = _split_region_version_document_id(document_id)
            if model_token and region:
                task_id_prefix = f"{model_token}_{region}_"
                document_version = document_version or version
                document_id = ""
        if not document_id and document_key:
            key_parts = document_key.split("_")
            if len(key_parts) == 2:
                task_id_prefix = f"{document_key}_"
                document_key = ""
    if not document_id and not document_key and not task_id_prefix:
        model_token = _infer_model_token(text)
        if model_token and market_group and allow_multiple:
            task_id_prefix = f"{model_token}_{market_group}_"
        elif model_token and workflow_action == "build-draft-package" and allow_multiple:
            task_id_prefix = f"{model_token}_"
        elif model_token and market_group:
            document_key = f"{model_token}_{market_group}"
    if not document_id and task_document_id:
        document_id = task_document_id
    build_family = ""
    if not document_id and not document_key:
        build_family = _infer_build_family(text)
    if not task_id and workflow_action:
        action_label = _canonical_query_action_label(workflow_action)
        if document_id and action_label:
            task_id = f"{document_id}_{action_label}"
        elif document_key and workflow_action == "start-review" and action_label:
            task_id = f"{document_key}_{action_label}"

    return InferredQueueQuery(
        record_id=record_id,
        task_id=task_id,
        task_id_prefix=task_id_prefix,
        document_id=document_id,
        document_key=document_key,
        document_keys=document_keys,
        build_family=build_family,
        lang=lang,
        langs=inferred_langs,
        document_version=document_version,
        query_workflow_action=workflow_action,
        result_contains=result_contains,
        latest_per_document_key=latest_per_document_key,
        queue_scope=queue_scope,
        market_group=market_group,
        allow_multiple=allow_multiple,
        recommended_limit=recommended_limit,
    )


def apply_inferred_queue_query(args: argparse.Namespace) -> argparse.Namespace:
    inferred = infer_queue_query_from_text(getattr(args, "query_text", None))
    merged = argparse.Namespace(**vars(args))
    if not getattr(merged, "record_id", None) and inferred.record_id:
        merged.record_id = inferred.record_id
    if not getattr(merged, "task_id", None) and inferred.task_id:
        merged.task_id = inferred.task_id
    if not getattr(merged, "task_id_prefix", None) and inferred.task_id_prefix:
        merged.task_id_prefix = inferred.task_id_prefix
    if not getattr(merged, "document_id", None) and inferred.document_id:
        merged.document_id = inferred.document_id
    if (
        not getattr(merged, "document_key", None)
        and inferred.document_key
        and not (inferred.task_id and inferred.query_workflow_action == "start-review")
    ):
        merged.document_key = inferred.document_key
    if not getattr(merged, "document_keys", None) and inferred.document_keys:
        merged.document_keys = ",".join(inferred.document_keys)
    if not getattr(merged, "build_family", None) and inferred.build_family:
        merged.build_family = inferred.build_family
    if not getattr(merged, "lang", None) and inferred.lang:
        merged.lang = inferred.lang
    if not getattr(merged, "langs", None) and inferred.langs:
        merged.langs = ",".join(inferred.langs)
    if not getattr(merged, "document_version", None) and inferred.document_version:
        merged.document_version = inferred.document_version
    if (
        not getattr(merged, "market_group", None)
        and inferred.market_group
        and not inferred.task_id_prefix
        and not inferred.document_id
        and not inferred.document_key
        and not inferred.build_family
    ):
        merged.market_group = inferred.market_group
    if not getattr(merged, "query_workflow_action", None) and inferred.query_workflow_action:
        merged.query_workflow_action = inferred.query_workflow_action
    if not getattr(merged, "result_contains", None) and inferred.result_contains:
        merged.result_contains = inferred.result_contains
    if not getattr(merged, "latest_per_document_key", False) and inferred.latest_per_document_key:
        merged.latest_per_document_key = inferred.latest_per_document_key
    if getattr(merged, "queue_scope", "all") == "all" and inferred.queue_scope != "all":
        merged.queue_scope = inferred.queue_scope
    if not getattr(merged, "allow_multiple", False) and inferred.allow_multiple:
        merged.allow_multiple = inferred.allow_multiple
    if inferred.recommended_limit and int(getattr(merged, "limit", _DEFAULT_QUEUE_QUERY_LIMIT) or 0) == _DEFAULT_QUEUE_QUERY_LIMIT:
        merged.limit = inferred.recommended_limit
    return merged


def _match_exact(actual: str, expected: str | None) -> bool:
    if not expected:
        return True
    return actual.strip().lower() == expected.strip().lower()


def _match_contains(actual: str, expected: str | None) -> bool:
    if not expected:
        return True
    return expected.strip().lower() in actual.strip().lower()


def _normalize_document_key_filters(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (list, tuple, set)):
        raw_parts = [str(item or "") for item in value]
    else:
        raw_parts = re.split(r"[,，/、\s]+", str(value or ""))
    keys: list[str] = []
    for raw_part in raw_parts:
        part = raw_part.strip()
        if not part:
            continue
        normalized = part.upper()
        if normalized not in keys:
            keys.append(normalized)
    return tuple(keys)


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
        market_group = _text(fields.get(MARKET_GROUP_FIELD) or fields.get(MARKET_FIELD)).upper()
        rows.append(
            QueueQueryRow(
                queue_scope="document-link",
                record_id=_text(raw_record.get("record_id")),
                document_id=_text(fields.get(DOCUMENT_ID_FIELD)),
                document_key=_text(fields.get(DOCUMENT_KEY_FIELD)),
                build_family=_text(fields.get(BUILD_FAMILY_FIELD)).lower(),
                lang=normalize_language(_text(fields.get(LANG_FIELD))),
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
                task_id=_text(fields.get(TASK_ID_FIELD)),
                market_group=market_group,
                build_started_at=_text(fields.get(BUILD_STARTED_AT_FIELD)),
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
        workflow_action = _text(fields.get(WORKFLOW_ACTION_FIELD)) or REVIEW_START_ACTION_LABEL
        try:
            normalize_review_start_action(workflow_action)
        except RuntimeError:
            continue
        rows.append(
            QueueQueryRow(
                queue_scope="review-init",
                record_id=parsed.record_id,
                document_id=parsed.document_id,
                document_key=parsed.document_key,
                build_family=parsed.build_family,
                lang=parsed.lang,
                version=parsed.version,
                workflow_action=workflow_action,
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
                task_id=_text(fields.get(TASK_ID_FIELD)),
                market_group=_text(fields.get(MARKET_GROUP_FIELD) or fields.get(MARKET_FIELD)).upper(),
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


def _effective_queue_query_limit(args: argparse.Namespace, normalized_action: str | None) -> int:
    limit = max(int(getattr(args, "limit", _DEFAULT_QUEUE_QUERY_LIMIT) or _DEFAULT_QUEUE_QUERY_LIMIT), 1)
    if (
        getattr(args, "allow_multiple", False)
        and normalized_action in {"draft", "publish", "start_review"}
        and limit == _DEFAULT_QUEUE_QUERY_LIMIT
    ):
        return 1000
    return limit


def _matches_queue_query_row(
    args: argparse.Namespace,
    row: QueueQueryRow,
    *,
    normalized_action: str | None,
    lang_filters: tuple[str, ...],
) -> bool:
    document_keys = _normalize_document_key_filters(getattr(args, "document_keys", None))
    if getattr(args, "record_id", None) and row.record_id != args.record_id:
        return False
    if getattr(args, "task_id", None) and _normalize_task_id(_row_task_id(row)) != _normalize_task_id(args.task_id):
        return False
    if not _match_task_id_prefix(_row_task_id(row), getattr(args, "task_id_prefix", None)):
        return False
    if not _match_exact(row.document_id, getattr(args, "document_id", None)):
        return False
    if not _match_exact(row.document_key, getattr(args, "document_key", None)):
        return False
    if document_keys and row.document_key.strip().upper() not in document_keys:
        return False
    if not _match_exact(row.build_family, getattr(args, "build_family", None)):
        return False
    requested_lang = normalize_language(getattr(args, "lang", None))
    if requested_lang and row.lang.casefold() != requested_lang.casefold():
        return False
    if lang_filters and row.lang not in lang_filters:
        return False
    if not _match_exact(row.version, getattr(args, "document_version", None)):
        return False
    if not _match_exact(row.market_group, getattr(args, "market_group", None)):
        return False
    if normalized_action and row.normalized_workflow_action != normalized_action:
        return False
    if (
        getattr(args, "allow_multiple", False)
        and normalized_action in {"draft", "publish"}
        and row.build_trigger_requested is not True
    ):
        return False
    if not _match_contains(row.git_ref, getattr(args, "git_ref_contains", None)):
        return False
    return _match_contains(row.result, getattr(args, "result_contains", None))


def query_queue_rows(args: argparse.Namespace, rows: list[QueueQueryRow]) -> QueueQueryResult:
    normalized_action = _normalize_query_workflow_action(getattr(args, "query_workflow_action", None))
    lang_filters = _normalize_langs(getattr(args, "langs", None))
    filtered = [
        row
        for row in rows
        if _matches_queue_query_row(
            args,
            row,
            normalized_action=normalized_action,
            lang_filters=lang_filters,
        )
    ]
    if _should_apply_latest_per_document_key(args, normalized_action):
        filtered = _latest_per_document_key(filtered)
    limit = _effective_queue_query_limit(args, normalized_action)
    limited_rows = apply_freshness_to_rows(args, filtered[:limit])
    return QueueQueryResult(
        rows=limited_rows,
        matched_count=len(filtered),
        returned_count=len(limited_rows),
        limit=limit,
        truncated=len(filtered) > len(limited_rows),
    )


def filter_queue_query_rows(args: argparse.Namespace, rows: list[QueueQueryRow]) -> list[QueueQueryRow]:
    return query_queue_rows(args, rows).rows


def apply_freshness_to_rows(args: argparse.Namespace, rows: list[QueueQueryRow]) -> list[QueueQueryRow]:
    fresh_since = getattr(args, "fresh_since", None)
    enriched: list[QueueQueryRow] = []
    for row in rows:
        freshness = compute_freshness(
            result=row.result,
            build_started_at=row.build_started_at,
            fresh_since=fresh_since,
        )
        enriched.append(
            replace(
                row,
                build_started_at=isoformat_timestamp(freshness.build_started_at),
                result_built_at=isoformat_timestamp(freshness.result_built_at),
                result_is_fresh=freshness.result_is_fresh,
                freshness_status=freshness.freshness_status,
            )
        )
    return enriched


def _row_title(row: QueueQueryRow) -> str:
    action = workflow_action_label(row.workflow_action) if row.queue_scope == "document-link" else REVIEW_START_ACTION_LABEL
    action_text = action or row.workflow_action or row.normalized_workflow_action or ""
    return f"{row.queue_scope} {row.record_id} {row.document_id or row.document_key}".strip() + (
        f" [{action_text}]" if action_text else ""
    )


def render_queue_query_rows(
    rows: list[QueueQueryRow],
    *,
    as_json: bool,
    query_result: QueueQueryResult | None = None,
) -> str:
    matched_count = query_result.matched_count if query_result else len(rows)
    returned_count = query_result.returned_count if query_result else len(rows)
    limit = query_result.limit if query_result else len(rows)
    truncated = query_result.truncated if query_result else False
    if as_json:
        return json.dumps(
            {
                "count": returned_count,
                "returned_count": returned_count,
                "matched_count": matched_count,
                "limit": limit,
                "truncated": truncated,
                "rows": [asdict(row) for row in rows],
            },
            ensure_ascii=False,
            indent=2,
        )
    if not rows:
        return "No matching queue rows."
    blocks: list[str] = []
    if truncated:
        blocks.append(
            f"Showing {returned_count} of {matched_count} matching queue rows (limit={limit}). "
            "Increase --limit or narrow filters for a complete result."
        )
    for row in rows:
        lines = [
            _row_title(row),
            f"record_id: {row.record_id}",
        ]
        task_id = _row_task_id(row)
        if task_id:
            lines.append(f"task_id: {task_id}")
        if row.document_id:
            lines.append(f"document_id: {row.document_id}")
        if row.document_key:
            lines.append(f"document_key: {row.document_key}")
        if row.build_family:
            lines.append(f"build_family: {row.build_family}")
        if row.market_group:
            lines.append(f"market_group: {row.market_group}")
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
        if row.build_started_at:
            lines.append(f"build_started_at: {row.build_started_at}")
        if row.result_built_at:
            lines.append(f"result_built_at: {row.result_built_at}")
        if row.freshness_status and row.freshness_status != "not_requested":
            lines.append(f"freshness_status: {row.freshness_status}")
            if row.result_is_fresh is not None:
                lines.append(f"result_is_fresh: {str(row.result_is_fresh).lower()}")
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
    query_result = query_queue_rows(resolved_args, rows)
    print(render_queue_query_rows(query_result.rows, as_json=resolved_args.json, query_result=query_result))


if __name__ == "__main__":
    raise SystemExit("Use `python build.py queue-query ...`.")
