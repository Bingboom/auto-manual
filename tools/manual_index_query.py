from __future__ import annotations

import argparse
import json
import os
import re
import unicodedata
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from tools.document_link_queue import scalar_text
from tools.phase2_support import LarkCliSource, cli_bin, load_config, phase2_identity

DEFAULT_MANUAL_INDEX_SOURCE_URL = (
    "https://test-degwga5x6ex8.feishu.cn/wiki/AS02w8ZL2iDv44kDLHIcHCPqntd"
    "?table=tbl1ypQJJPbKostu&view=vewytqcvDc"
)
DEFAULT_MANUAL_INDEX_BASE_TOKEN = "ASabb6mXaafMtlsQYWScuqEYnAg"
DEFAULT_MANUAL_INDEX_TABLE_ID = "tbl1ypQJJPbKostu"
DEFAULT_MANUAL_INDEX_VIEW_ID = "vewytqcvDc"

MANUAL_INDEX_BASE_TOKEN_ENV = "FEISHU_MANUAL_INDEX_BASE_TOKEN"
MANUAL_INDEX_TABLE_ID_ENV = "FEISHU_MANUAL_INDEX_TABLE_ID"
MANUAL_INDEX_VIEW_ID_ENV = "FEISHU_MANUAL_INDEX_VIEW_ID"
MANUAL_INDEX_IDENTITY_ENV = "FEISHU_MANUAL_INDEX_IDENTITY"

FIELD_NO = "No."
FIELD_BUSINESS_ID = "业务号"
FIELD_MODELS = "产品型号"
FIELD_PROJECT = "项目"
FIELD_MANUAL_LINK = "说明书链接"
FIELD_MANUAL_NAME = "说明书名称"
FIELD_DOCUMENT_NAME = "文档名称"
FIELD_REGION = "区域"
FIELD_SOURCE_LANG = "源语言"
FIELD_REVISION_RECORD = "修订记录"
FIELD_COLOR = "颜色"
FIELD_ARCHIVED_AT = "归档日期"
FIELD_SHORT_NAME = "产品简称"
FIELD_NAME_EN = "产品名称_en"
FIELD_NAME_JP = "产品名称_jp"
FIELD_NAME_ZH = "产品名称_zh"
FIELD_NAME_KR_COPY = "产品名称_Kr 副本"
FIELD_NAME_KR = "产品名称_kr"
FIELD_DOC_TYPE = "文档类型"
FIELD_PRODUCT_STAGE = "产品阶段"
FIELD_VERSION = "版本"
FIELD_NOTES = "备注"
FIELD_CATEGORY = "分类"
FIELD_PRODUCT_MANAGER = "产品经理"
FIELD_PROJECT_MANAGER = "项目经理"
FIELD_SYSTEM_ENGINEER = "系统工程师"
FIELD_DESIGN = "设计"
FIELD_CERTIFICATION = "认证"
FIELD_DOC_DEVELOPER = "资料开发"
FIELD_VISIBLE = "是否显示"

_URL_RE = re.compile(r"https?://[^\s)>\]]+")
_MARKDOWN_LINK_RE = re.compile(r"\[([^\]]*)\]\((https?://[^)]+)\)")
_VERSION_RE = re.compile(r"\b[Vv]?\d+(?:\.\d+)+\b")
_ASCII_TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
_CJK_CHUNK_RE = re.compile(r"[\u3400-\u9fff]{2,}")

_READ_INTENT_KEYWORDS = (
    "查",
    "查询",
    "查看",
    "找",
    "获取",
    "给我",
    "发我",
    "链接",
    "列表",
    "清单",
    "总览",
    "概览",
    "统计",
    "多少",
    "有哪些",
    "show",
    "find",
    "search",
    "list",
    "overview",
    "summary",
    "count",
    "link",
)
_MANUAL_INDEX_KEYWORDS = (
    "说明书",
    "手册",
    "发布文档",
    "文档管理",
    "manual",
    "user manual",
    "manual index",
    "manual table",
)
_OVERVIEW_KEYWORDS = ("总览", "概览", "统计", "多少", "overview", "summary", "count")
_INVENTORY_KEYWORDS = ("所有", "全部", "全量", "各产品", "各个", "列表", "清单", "all", "every", "list", "inventory")
_EXECUTION_KEYWORDS = (
    "构建",
    "生成",
    "输出",
    "发起",
    "触发",
    "补跑",
    "补构建",
    "重跑",
    "重新构建",
    "开始",
    "build",
    "run",
    "trigger",
    "start",
    "publish",
    "发布",
    "review",
)
_QUEUE_COPY_KEYWORDS = ("文案", "manual copy", "copy")

_TOKEN_STOPWORDS = {
    "a",
    "an",
    "and",
    "all",
    "copy",
    "document",
    "documents",
    "find",
    "for",
    "index",
    "info",
    "link",
    "links",
    "list",
    "manual",
    "manuals",
    "overview",
    "please",
    "query",
    "search",
    "show",
    "summary",
    "table",
    "the",
    "user",
    "查看",
    "查询",
    "获取",
    "说明书",
    "手册",
    "产品",
    "文档",
    "链接",
    "总览",
    "概览",
    "信息",
    "所有",
    "全部",
    "各产品",
    "列表",
    "清单",
    "一下",
}

_REGION_ALIASES = {
    "美加规": "美加规",
    "美规": "美加规",
    "美国": "美加规",
    "加拿大": "美加规",
    "北美": "美加规",
    "us": "美加规",
    "usa": "美加规",
    "日规": "日规",
    "日本": "日规",
    "jp": "日规",
    "ja": "日规",
    "中规": "中规",
    "中国": "中规",
    "cn": "中规",
    "菲律宾规": "菲律宾规",
    "菲律宾": "菲律宾规",
    "ph": "菲律宾规",
    "欧英规": "欧英规",
    "欧规": "欧规",
    "欧洲": "欧规",
    "欧盟": "欧规",
    "eu": "欧规",
    "uk": "欧英规",
    "英国": "欧英规",
    "韩规": "韩规",
    "韩国": "韩规",
    "kr": "韩规",
    "澳规": "澳规",
    "澳洲": "澳规",
    "澳大利亚": "澳规",
    "au": "澳规",
}
_LANG_ALIASES = {
    "en": "EN",
    "english": "EN",
    "英文": "EN",
    "英语": "EN",
    "jp": "JP",
    "ja": "JP",
    "japanese": "JP",
    "日文": "JP",
    "日语": "JP",
    "cn": "CN",
    "zh": "CN",
    "chinese": "CN",
    "中文": "CN",
    "汉语": "CN",
    "kr": "KR",
    "ko": "KR",
    "korean": "KR",
    "韩文": "KR",
    "韩语": "KR",
}


@dataclass(frozen=True)
class ManualIndexSettings:
    base_token: str
    table_id: str
    view_id: str
    identity: str
    source_url: str = DEFAULT_MANUAL_INDEX_SOURCE_URL


@dataclass(frozen=True)
class ManualIndexIntent:
    matched: bool
    query_type: str
    reason: str = ""


@dataclass(frozen=True)
class ManualIndexFilters:
    regions: tuple[str, ...] = ()
    source_langs: tuple[str, ...] = ()
    versions: tuple[str, ...] = ()
    doc_types: tuple[str, ...] = ()


@dataclass(frozen=True)
class ManualIndexRow:
    record_id: str
    no: str
    business_id: str
    product_models: tuple[str, ...]
    project: tuple[str, ...]
    manual_link: str
    manual_link_text: str
    manual_name: str
    document_name: str
    region: tuple[str, ...]
    source_lang: tuple[str, ...]
    revision_record: str
    color: tuple[str, ...]
    archived_at: str
    product_short_names: tuple[str, ...]
    product_names_en: tuple[str, ...]
    product_names_jp: tuple[str, ...]
    product_names_zh: tuple[str, ...]
    product_names_kr: tuple[str, ...]
    doc_type: tuple[str, ...]
    product_stage: tuple[str, ...]
    version: tuple[str, ...]
    notes: str
    category: tuple[str, ...]
    product_manager: tuple[str, ...]
    project_manager: tuple[str, ...]
    system_engineer: tuple[str, ...]
    design: tuple[str, ...]
    certification: tuple[str, ...]
    doc_developer: tuple[str, ...]
    visible: str

    @property
    def primary_title(self) -> str:
        return self.manual_name or self.document_name or self.manual_link_text


@dataclass(frozen=True)
class ManualIndexQueryResult:
    matched: bool
    query_type: str
    source: dict[str, str]
    overview: dict[str, Any]
    rows: list[ManualIndexRow]
    matched_count: int
    returned_count: int
    limit: int
    truncated: bool
    filters: dict[str, list[str]]
    tokens: list[str]
    summary: str
    next_step: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["rows"] = [asdict(row) for row in self.rows]
        return payload


def _normalize_text(value: Any) -> str:
    return unicodedata.normalize("NFKC", str(value or "")).strip()


def _search_normalize(value: Any) -> str:
    normalized = _normalize_text(value).casefold()
    normalized = re.sub(r"[^\w\u3400-\u9fff]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def _unique(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        text = _normalize_text(value)
        if not text or text in seen:
            continue
        seen.add(text)
        ordered.append(text)
    return tuple(ordered)


def _cell_texts(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (list, tuple, set)):
        texts: list[str] = []
        for item in value:
            texts.extend(_cell_texts(item))
        return _unique(texts)
    if isinstance(value, dict):
        texts: list[str] = []
        for key in ("text", "name", "label", "title", "value", "link"):
            if key in value:
                texts.extend(_cell_texts(value.get(key)))
        return _unique(texts)
    text = scalar_text(value)
    if not text:
        return ()
    return (text,)


def _field_texts(fields: dict[str, Any], *field_names: str) -> tuple[str, ...]:
    values: list[str] = []
    for field_name in field_names:
        if field_name in fields:
            values.extend(_cell_texts(fields.get(field_name)))
    return _unique(values)


def _first_field_text(fields: dict[str, Any], *field_names: str) -> str:
    texts = _field_texts(fields, *field_names)
    return texts[0] if texts else ""


def _extract_link(value: str) -> tuple[str, str]:
    text = _normalize_text(value)
    markdown = _MARKDOWN_LINK_RE.search(text)
    if markdown:
        label = _normalize_text(markdown.group(1))
        url = _normalize_text(markdown.group(2))
        return url, label or url
    url = _URL_RE.search(text)
    if url:
        return _normalize_text(url.group(0)), text
    return "", text


def manual_index_settings_from_env(cfg: dict[str, Any]) -> ManualIndexSettings:
    identity = (
        os.environ.get(MANUAL_INDEX_IDENTITY_ENV, "").strip().lower()
        or os.environ.get("FEISHU_PHASE2_IDENTITY", "").strip().lower()
        or phase2_identity()
    )
    if identity not in {"user", "bot"}:
        raise RuntimeError(f"{MANUAL_INDEX_IDENTITY_ENV} must be one of: bot, user")
    return ManualIndexSettings(
        base_token=os.environ.get(MANUAL_INDEX_BASE_TOKEN_ENV, "").strip() or DEFAULT_MANUAL_INDEX_BASE_TOKEN,
        table_id=os.environ.get(MANUAL_INDEX_TABLE_ID_ENV, "").strip() or DEFAULT_MANUAL_INDEX_TABLE_ID,
        view_id=os.environ.get(MANUAL_INDEX_VIEW_ID_ENV, "").strip() or DEFAULT_MANUAL_INDEX_VIEW_ID,
        identity=identity,
        source_url=DEFAULT_MANUAL_INDEX_SOURCE_URL,
    )


def infer_manual_index_intent(raw_text: str | None) -> ManualIndexIntent:
    text = _normalize_text(raw_text)
    if not text:
        return ManualIndexIntent(matched=False, query_type="", reason="empty_query")
    lowered = text.casefold()
    has_read_intent = any(keyword in lowered for keyword in _READ_INTENT_KEYWORDS)
    has_manual_keyword = any(keyword.casefold() in lowered for keyword in _MANUAL_INDEX_KEYWORDS)
    has_overview = any(keyword.casefold() in lowered for keyword in _OVERVIEW_KEYWORDS)
    has_inventory = any(keyword.casefold() in lowered for keyword in _INVENTORY_KEYWORDS)
    has_execution = any(keyword.casefold() in lowered for keyword in _EXECUTION_KEYWORDS)
    has_queue_copy = any(keyword.casefold() in lowered for keyword in _QUEUE_COPY_KEYWORDS)
    has_product_token = any(_looks_like_product_token(token) for token in _ASCII_TOKEN_RE.findall(text))

    if has_execution and has_queue_copy and not (has_overview or "链接" in text or "link" in lowered):
        return ManualIndexIntent(matched=False, query_type="", reason="queue_copy_execution")
    if has_overview and not (has_execution and not has_read_intent):
        return ManualIndexIntent(matched=True, query_type="overview", reason="overview_keyword")
    if has_manual_keyword and has_inventory and not (has_execution and not has_read_intent):
        return ManualIndexIntent(matched=True, query_type="inventory", reason="inventory_keyword")
    if has_manual_keyword and (has_read_intent or has_product_token) and not (has_execution and not has_read_intent):
        return ManualIndexIntent(matched=True, query_type="lookup", reason="manual_lookup")
    return ManualIndexIntent(matched=False, query_type="", reason="no_manual_index_intent")


def _looks_like_product_token(token: str) -> bool:
    text = token.strip()
    if not text:
        return False
    if re.fullmatch(r"doc-\d+", text, flags=re.IGNORECASE):
        return True
    if re.fullmatch(r"ht[a-z0-9]+", text, flags=re.IGNORECASE):
        return True
    if "-" in text and any(char.isdigit() for char in text):
        return True
    return bool(re.fullmatch(r"[A-Za-z]{1,8}\d[A-Za-z0-9._-]{1,}", text))


def _extract_filters(raw_text: str) -> ManualIndexFilters:
    lowered = _search_normalize(raw_text)
    regions = _unique(
        value
        for alias, value in _REGION_ALIASES.items()
        if re.search(rf"(?<![a-z0-9]){re.escape(alias.casefold())}(?![a-z0-9])", lowered)
        or alias in raw_text
    )
    source_langs = _unique(
        value
        for alias, value in _LANG_ALIASES.items()
        if re.search(rf"(?<![a-z0-9]){re.escape(alias.casefold())}(?![a-z0-9])", lowered)
        or alias in raw_text
    )
    versions = _unique(match.group(0).upper() for match in _VERSION_RE.finditer(raw_text))
    doc_types: list[str] = []
    if "user manual" in lowered:
        doc_types.append("User Manual")
    if "取扱説明書" in raw_text or "日文说明书" in raw_text or "日语说明书" in raw_text:
        doc_types.append("取扱説明書")
    if "사용자 매뉴얼" in raw_text or "韩文说明书" in raw_text or "韩语说明书" in raw_text:
        doc_types.append("사용자 매뉴얼")
    return ManualIndexFilters(
        regions=regions,
        source_langs=source_langs,
        versions=versions,
        doc_types=_unique(doc_types),
    )


def _extract_tokens(raw_text: str) -> tuple[str, ...]:
    text = _normalize_text(raw_text)
    tokens: list[str] = []
    for token in _ASCII_TOKEN_RE.findall(text):
        normalized = _search_normalize(token)
        if not normalized or normalized in _TOKEN_STOPWORDS:
            continue
        if len(normalized) < 2:
            continue
        if _looks_like_product_token(token) or any(char.isdigit() for char in token) or len(normalized) >= 4:
            tokens.append(token)
    for chunk in _CJK_CHUNK_RE.findall(text):
        compact = chunk
        for stopword in sorted(_TOKEN_STOPWORDS, key=len, reverse=True):
            compact = compact.replace(stopword, "")
        compact = compact.strip()
        if len(compact) >= 2:
            tokens.append(compact)
    return _unique(tokens)


def _row_values(row: ManualIndexRow) -> tuple[str, ...]:
    return (
        row.no,
        row.business_id,
        *row.product_models,
        *row.project,
        row.manual_link,
        row.manual_link_text,
        row.manual_name,
        row.document_name,
        *row.region,
        *row.source_lang,
        row.revision_record,
        *row.color,
        row.archived_at,
        *row.product_short_names,
        *row.product_names_en,
        *row.product_names_jp,
        *row.product_names_zh,
        *row.product_names_kr,
        *row.doc_type,
        *row.product_stage,
        *row.version,
        row.notes,
        *row.category,
        *row.product_manager,
        *row.project_manager,
        *row.system_engineer,
        *row.design,
        *row.certification,
        *row.doc_developer,
        row.visible,
    )


def _row_search_text(row: ManualIndexRow) -> str:
    return _search_normalize(" ".join(value for value in _row_values(row) if value))


def _row_matches_filters(row: ManualIndexRow, filters: ManualIndexFilters) -> bool:
    if filters.regions and not set(filters.regions).intersection(row.region):
        return False
    if filters.source_langs and not set(filters.source_langs).intersection(row.source_lang):
        return False
    if filters.versions and not set(filters.versions).intersection(version.upper() for version in row.version):
        return False
    if filters.doc_types and not set(filters.doc_types).intersection(row.doc_type):
        return False
    return True


def _token_score(row: ManualIndexRow, token: str, query_text: str) -> int:
    normalized_token = _search_normalize(token)
    if not normalized_token:
        return 0
    score = 0
    primary_fields = (
        row.business_id,
        *row.product_models,
        *row.product_short_names,
        *row.project,
    )
    for value in primary_fields:
        normalized_value = _search_normalize(value)
        if not normalized_value:
            continue
        if normalized_token == normalized_value:
            score += 90
        elif normalized_token in normalized_value or normalized_value in normalized_token:
            score += 60
    title_fields = (
        row.manual_name,
        row.document_name,
        row.manual_link_text,
        *row.product_names_en,
        *row.product_names_jp,
        *row.product_names_zh,
        *row.product_names_kr,
    )
    for value in title_fields:
        normalized_value = _search_normalize(value)
        if not normalized_value:
            continue
        if normalized_token == normalized_value:
            score += 60
        elif normalized_token in normalized_value:
            score += 30
        elif len(normalized_value) >= 4 and normalized_value in _search_normalize(query_text):
            score += 30
    if normalized_token in _row_search_text(row):
        score += 10
    return score


def _row_score(row: ManualIndexRow, tokens: tuple[str, ...], query_text: str) -> int:
    if not tokens:
        return 1
    return sum(_token_score(row, token, query_text) for token in tokens)


def manual_index_row_from_record(record: dict[str, Any]) -> ManualIndexRow:
    fields_raw = record.get("fields", {})
    fields = fields_raw if isinstance(fields_raw, dict) else {}
    manual_link, manual_link_text = _extract_link(_first_field_text(fields, FIELD_MANUAL_LINK))
    return ManualIndexRow(
        record_id=_normalize_text(record.get("record_id")),
        no=_first_field_text(fields, FIELD_NO),
        business_id=_first_field_text(fields, FIELD_BUSINESS_ID),
        product_models=_field_texts(fields, FIELD_MODELS),
        project=_field_texts(fields, FIELD_PROJECT),
        manual_link=manual_link,
        manual_link_text=manual_link_text,
        manual_name=_first_field_text(fields, FIELD_MANUAL_NAME),
        document_name=_first_field_text(fields, FIELD_DOCUMENT_NAME),
        region=_field_texts(fields, FIELD_REGION),
        source_lang=_field_texts(fields, FIELD_SOURCE_LANG),
        revision_record=_first_field_text(fields, FIELD_REVISION_RECORD),
        color=_field_texts(fields, FIELD_COLOR),
        archived_at=_first_field_text(fields, FIELD_ARCHIVED_AT),
        product_short_names=_field_texts(fields, FIELD_SHORT_NAME),
        product_names_en=_field_texts(fields, FIELD_NAME_EN),
        product_names_jp=_field_texts(fields, FIELD_NAME_JP),
        product_names_zh=_field_texts(fields, FIELD_NAME_ZH),
        product_names_kr=_field_texts(fields, FIELD_NAME_KR, FIELD_NAME_KR_COPY),
        doc_type=_field_texts(fields, FIELD_DOC_TYPE),
        product_stage=_field_texts(fields, FIELD_PRODUCT_STAGE),
        version=_field_texts(fields, FIELD_VERSION),
        notes=_first_field_text(fields, FIELD_NOTES),
        category=_field_texts(fields, FIELD_CATEGORY),
        product_manager=_field_texts(fields, FIELD_PRODUCT_MANAGER),
        project_manager=_field_texts(fields, FIELD_PROJECT_MANAGER),
        system_engineer=_field_texts(fields, FIELD_SYSTEM_ENGINEER),
        design=_field_texts(fields, FIELD_DESIGN),
        certification=_field_texts(fields, FIELD_CERTIFICATION),
        doc_developer=_field_texts(fields, FIELD_DOC_DEVELOPER),
        visible=_first_field_text(fields, FIELD_VISIBLE),
    )


def _counter_for(rows: list[ManualIndexRow], attr: str) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for row in rows:
        value = getattr(row, attr)
        values = value if isinstance(value, tuple) else (value,)
        for item in values:
            text = _normalize_text(item)
            if text:
                counter[text] += 1
    return dict(sorted(counter.items(), key=lambda item: (-item[1], item[0])))


def _split_product_models(rows: list[ManualIndexRow]) -> tuple[str, ...]:
    values: list[str] = []
    for row in rows:
        for value in row.product_models:
            values.extend(part.strip() for part in re.split(r"[,，/、]+", value) if part.strip())
    return _unique(values)


def build_manual_index_overview(rows: list[ManualIndexRow]) -> dict[str, Any]:
    archived_dates = sorted(row.archived_at for row in rows if row.archived_at)
    product_models = _split_product_models(rows)
    return {
        "total_manuals": len(rows),
        "distinct_product_model_count": len(product_models),
        "distinct_product_models": list(product_models),
        "by_region": _counter_for(rows, "region"),
        "by_source_lang": _counter_for(rows, "source_lang"),
        "by_doc_type": _counter_for(rows, "doc_type"),
        "by_category": _counter_for(rows, "category"),
        "by_product_stage": _counter_for(rows, "product_stage"),
        "latest_archive_date": archived_dates[-1] if archived_dates else "",
    }


def _result_source(settings: ManualIndexSettings) -> dict[str, str]:
    source = {
        "source_url": settings.source_url,
        "table_id": settings.table_id,
        "record_scope": "view_filtered_records" if settings.view_id else "all_table_records",
        "identity": settings.identity,
    }
    if settings.view_id:
        source["view_id"] = settings.view_id
    return source


def query_manual_index_records(
    raw_records: list[dict[str, Any]],
    *,
    query_text: str,
    settings: ManualIndexSettings,
    limit: int = 10,
) -> ManualIndexQueryResult:
    intent = infer_manual_index_intent(query_text)
    source = _result_source(settings)
    if not intent.matched:
        return ManualIndexQueryResult(
            matched=False,
            query_type="",
            source=source,
            overview={},
            rows=[],
            matched_count=0,
            returned_count=0,
            limit=max(limit, 1),
            truncated=False,
            filters={},
            tokens=[],
            summary="No manual-index intent detected.",
            next_step="Route this message through the normal queue resolver.",
        )
    all_rows = [manual_index_row_from_record(record) for record in raw_records]
    overview = build_manual_index_overview(all_rows)
    filters = _extract_filters(query_text)
    tokens = _extract_tokens(query_text)
    filtered = [row for row in all_rows if _row_matches_filters(row, filters)]
    scored: list[tuple[int, ManualIndexRow]] = []
    if intent.query_type in {"overview", "inventory"} and not tokens:
        scored = [(1, row) for row in filtered]
    else:
        for row in filtered:
            score = _row_score(row, tokens, query_text)
            if score > 0:
                scored.append((score, row))
        scored.sort(
            key=lambda item: (
                -item[0],
                item[1].business_id,
                item[1].primary_title,
                item[1].record_id,
            )
        )
    matched_rows = [row for _score, row in scored]
    effective_limit = max(limit, 1)
    returned_rows = [] if intent.query_type == "overview" and not tokens else matched_rows[:effective_limit]
    filters_payload = {
        "regions": list(filters.regions),
        "source_langs": list(filters.source_langs),
        "versions": list(filters.versions),
        "doc_types": list(filters.doc_types),
    }
    matched_count = len(matched_rows)
    is_overview_only = intent.query_type == "overview" and not tokens
    summary = _summary_for_result(intent.query_type, matched_count, len(all_rows), tokens, filters_payload)
    return ManualIndexQueryResult(
        matched=True,
        query_type=intent.query_type,
        source=source,
        overview=overview,
        rows=returned_rows,
        matched_count=matched_count,
        returned_count=len(returned_rows),
        limit=effective_limit,
        truncated=False if is_overview_only else matched_count > len(returned_rows),
        filters=filters_payload,
        tokens=list(tokens),
        summary=summary,
        next_step=(
            ""
            if is_overview_only or matched_count <= effective_limit
            else "Narrow by product model, region, source language, or version if the result is too broad."
        ),
    )


def _summary_for_result(
    query_type: str,
    matched_count: int,
    total_count: int,
    tokens: tuple[str, ...],
    filters: dict[str, list[str]],
) -> str:
    if query_type == "overview":
        return f"Manual index overview: {total_count} visible manual row(s)."
    narrowed_by = []
    if tokens:
        narrowed_by.append("tokens=" + ", ".join(tokens))
    for name, values in filters.items():
        if values:
            narrowed_by.append(f"{name}=" + ", ".join(values))
    suffix = f" ({'; '.join(narrowed_by)})" if narrowed_by else ""
    return f"Matched {matched_count} manual index row(s){suffix}."


def query_manual_index(
    *,
    cfg: dict[str, Any],
    query_text: str,
    limit: int,
    source: LarkCliSource | None = None,
) -> ManualIndexQueryResult:
    settings = manual_index_settings_from_env(cfg)
    intent = infer_manual_index_intent(query_text)
    if not intent.matched:
        return query_manual_index_records([], query_text=query_text, settings=settings, limit=limit)
    lark_source = source or LarkCliSource(cli_bin=cli_bin(cfg), identity=settings.identity)
    raw_records = lark_source.fetch_records_with_ids(
        base_token=settings.base_token,
        table_id=settings.table_id,
        view_id=settings.view_id or None,
    )
    return query_manual_index_records(raw_records, query_text=query_text, settings=settings, limit=limit)


def render_manual_index_result(result: ManualIndexQueryResult, *, as_json: bool) -> str:
    if as_json:
        return json.dumps(result.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)
    if not result.matched:
        return result.summary
    lines = [result.summary]
    overview = result.overview
    if result.query_type == "overview":
        lines.extend(_render_overview_lines(overview))
        return "\n".join(lines)
    if overview and result.query_type == "inventory":
        lines.extend(_render_overview_lines(overview)[:6])
    for row in result.rows:
        lines.append(_render_row_line(row))
    if result.truncated:
        lines.append(f"Showing {result.returned_count} of {result.matched_count}; increase --limit or narrow the query.")
    if result.next_step:
        lines.append(result.next_step)
    return "\n".join(line for line in lines if line)


def _render_overview_lines(overview: dict[str, Any]) -> list[str]:
    return [
        f"total_manuals: {overview.get('total_manuals', 0)}",
        f"distinct_product_model_count: {overview.get('distinct_product_model_count', 0)}",
        "by_region: " + _format_counts(overview.get("by_region", {})),
        "by_source_lang: " + _format_counts(overview.get("by_source_lang", {})),
        "by_doc_type: " + _format_counts(overview.get("by_doc_type", {})),
        "by_category: " + _format_counts(overview.get("by_category", {})),
        f"latest_archive_date: {overview.get('latest_archive_date', '')}",
    ]


def _format_counts(counts: Any) -> str:
    if not isinstance(counts, dict) or not counts:
        return "-"
    return "; ".join(f"{key}={value}" for key, value in counts.items())


def _render_row_line(row: ManualIndexRow) -> str:
    parts = [
        ", ".join(row.product_models) or row.business_id or row.record_id,
        row.primary_title,
        ", ".join(row.region),
        ", ".join(row.source_lang),
        ", ".join(row.version),
        row.archived_at,
        row.manual_link,
    ]
    return "- " + " | ".join(part for part in parts if part)


def run_manual_index_query(args: argparse.Namespace, *, config_path=None) -> None:
    cfg = load_config(config_path or Path(getattr(args, "config", "")))
    result = query_manual_index(
        cfg=cfg,
        query_text=str(getattr(args, "query_text", "") or ""),
        limit=int(getattr(args, "limit", 10) or 10),
    )
    print(render_manual_index_result(result, as_json=bool(getattr(args, "json", False))))
