#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass

MANUAL_COPY_SOURCE_FILE = "Manual_Copy_Source.csv"
LOCALIZED_COPY_FILE = "Localized_Copy.csv"
STATUS_WORDS_FILE = "Status_Words.csv"
SPEC_TITLES_FILE = "spec_titles.csv"
MISSING_TRANSLATIONS_REPORT = "reports/content_audit/manual_copy_missing_translations.csv"

MANUAL_COPY_TAG_FIELD = "用途标签"
MANUAL_COPY_TAG = "manual_copy"
STATUS_WORD_MARKER_FIELD = "是否为 status word"

MANUAL_COPY_SOURCE_COLUMNS = (
    "copy_key",
    "page_id",
    "copy_type",
    "Market",
    "Model",
    "Source_lang",
    "Is_Latest",
    "Version",
    "source_text",
    "section_order",
    "notes",
)

LOCALIZED_COPY_COLUMNS = (
    "copy_key",
    "page_id",
    "copy_type",
    "Region",
    "Model",
    "Source_lang",
    "Is_Latest",
    "Version",
    "text_en",
    "text_zh",
    "text_ja",
    "text_fr",
    "text_es",
    "text_pt-BR",
    "text_de",
    "text_it",
    "text_uk",
    "text_ko",
    "notes",
)

TM_LANGUAGE_FIELDS = {
    "en": "en",
    "zh": "zh",
    "ja": "jp",
    "jp": "jp",
    "fr": "fr",
    "es": "es",
    "pt-br": "pt-BR",
    "pt_br": "pt-BR",
    "br": "pt-BR",
    "de": "de",
    "it": "it",
    "uk": "uk",
    "ukr": "uk",
    "ko": "ko",
}

LOCALIZED_COPY_TEXT_COLUMNS = {
    "text_en": "en",
    "text_zh": "zh",
    "text_ja": "jp",
    "text_fr": "fr",
    "text_es": "es",
    "text_pt-BR": "pt-BR",
    "text_de": "de",
    "text_it": "it",
    "text_uk": "uk",
    "text_ko": "ko",
}

STATUS_WORD_COLUMNS = ("en", "zh", "jp", "fr", "es", "pt-BR", "de", "it", "uk", "ko", STATUS_WORD_MARKER_FIELD)
TRANSLATION_MEMORY_COLUMNS = (*STATUS_WORD_COLUMNS[:-1], MANUAL_COPY_TAG_FIELD, STATUS_WORD_MARKER_FIELD)
SPEC_TITLE_COLUMNS = (
    "title_en",
    "section_order",
    "title_zh",
    "title_jp",
    "title_fr",
    "title_es",
    "title_de",
    "title_it",
    "title_uk",
    "title_ko",
)
SPEC_TITLE_TEXT_COLUMNS = {
    "title_en": "en",
    "title_zh": "zh",
    "title_jp": "jp",
    "title_fr": "fr",
    "title_es": "es",
    "title_de": "de",
    "title_it": "it",
    "title_uk": "uk",
    "title_ko": "ko",
}

_TRUE_VALUES = {"1", "true", "yes", "y"}
_FALSE_VALUES = {"0", "false", "no", "n"}


@dataclass(frozen=True)
class MissingManualCopyTranslation:
    copy_key: str
    source_lang: str
    target_lang: str
    source_text: str


class ManualCopyConflictError(RuntimeError):
    pass


def _normalize_space(value: str) -> str:
    return " ".join((value or "").replace("\r\n", "\n").replace("\r", "\n").split())


def _truthy(value: str, *, default: bool = False) -> bool:
    raw = (value or "").strip().casefold()
    if not raw:
        return default
    if raw in _TRUE_VALUES:
        return True
    if raw in _FALSE_VALUES:
        return False
    return default


def _split_tokens(value: str) -> list[str]:
    return [
        token.strip()
        for token in re.split(r"[,;|/\n\u3001\uff0c]+", value or "")
        if token.strip()
    ]


def _tm_field_for_lang(lang: str) -> str:
    normalized = (lang or "").strip().casefold().replace("_", "-")
    return TM_LANGUAGE_FIELDS.get(normalized, (lang or "").strip())


def _is_manual_copy_tm_row(row: dict[str, str]) -> bool:
    return any(token.casefold() == MANUAL_COPY_TAG for token in _split_tokens(row.get(MANUAL_COPY_TAG_FIELD, "")))


def _copy_source_key(source_lang: str, source_text: str) -> tuple[str, str]:
    return (_tm_field_for_lang(source_lang).casefold(), _normalize_space(source_text).casefold())


def _is_spec_title_row(row: dict[str, str]) -> bool:
    page_id = (row.get("page_id") or "").strip().casefold()
    copy_type = (row.get("copy_type") or "").strip().casefold()
    return page_id in {"spec", "specifications"} and copy_type in {
        "page_title",
        "section_title",
        "spec_page_title",
        "spec_section_title",
    }


def _numeric_sort_token(value: str) -> tuple[int, float | str]:
    raw = (value or "").strip()
    if not raw:
        return (1, "")
    try:
        return (0, float(raw))
    except ValueError:
        return (1, raw.casefold())


def _build_manual_copy_tm_index(tm_rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    index: dict[tuple[str, str], dict[str, str]] = {}
    for row in tm_rows:
        if not _is_manual_copy_tm_row(row):
            continue
        for source_lang in dict.fromkeys(TM_LANGUAGE_FIELDS.values()):
            source_text = (row.get(source_lang) or "").strip()
            if not source_text:
                continue
            key = _copy_source_key(source_lang, source_text)
            existing = index.get(key)
            if existing is None:
                index[key] = dict(row)
                continue
            conflicts = []
            for lang in dict.fromkeys(LOCALIZED_COPY_TEXT_COLUMNS.values()):
                left = (existing.get(lang) or "").strip()
                right = (row.get(lang) or "").strip()
                if left and right and _normalize_space(left) != _normalize_space(right):
                    conflicts.append(f"{lang}: {left!r} != {right!r}")
                elif not left and right:
                    existing[lang] = right
            if conflicts:
                raise ManualCopyConflictError(
                    "Conflicting Translation_Memory manual_copy rows for "
                    f"{source_lang}:{source_text!r}: "
                    + "; ".join(conflicts)
                )
    return index


def build_localized_copy_rows(
    manual_rows: list[dict[str, str]],
    tm_rows: list[dict[str, str]],
) -> tuple[list[dict[str, str]], list[MissingManualCopyTranslation]]:
    tm_index = _build_manual_copy_tm_index(tm_rows)
    localized_rows: list[dict[str, str]] = []
    missing: list[MissingManualCopyTranslation] = []

    for row in manual_rows:
        if not _truthy(row.get("Is_Latest", ""), default=True):
            continue
        source_lang = (row.get("Source_lang") or "en").strip() or "en"
        source_text = (row.get("source_text") or "").strip()
        if not source_text:
            raise ValueError(f"manual copy source row has empty source_text: {row.get('copy_key', '')}")
        tm_row = tm_index.get(_copy_source_key(source_lang, source_text), {})
        output = {
            "copy_key": (row.get("copy_key") or "").strip(),
            "page_id": (row.get("page_id") or "").strip(),
            "copy_type": (row.get("copy_type") or "").strip(),
            "Region": (row.get("Market") or "ALL").strip() or "ALL",
            "Model": (row.get("Model") or "ALL").strip() or "ALL",
            "Source_lang": source_lang,
            "Is_Latest": (row.get("Is_Latest") or "TRUE").strip() or "TRUE",
            "Version": (row.get("Version") or "").strip(),
            "notes": (row.get("notes") or "").strip(),
        }
        source_tm_field = _tm_field_for_lang(source_lang)
        for text_column, tm_field in LOCALIZED_COPY_TEXT_COLUMNS.items():
            translated = (tm_row.get(tm_field) or "").strip()
            if tm_field == source_tm_field:
                translated = source_text
            if not translated:
                translated = source_text
                missing.append(
                    MissingManualCopyTranslation(
                        copy_key=output["copy_key"],
                        source_lang=source_lang,
                        target_lang=tm_field,
                        source_text=source_text,
                    )
                )
            output[text_column] = translated
        localized_rows.append(output)

    localized_rows.sort(
        key=lambda item: (
            item.get("page_id", "").casefold(),
            item.get("copy_key", "").casefold(),
            item.get("Region", "").casefold(),
            item.get("Model", "").casefold(),
        )
    )
    return localized_rows, missing


def build_status_word_rows(tm_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in tm_rows:
        if not _truthy(row.get(STATUS_WORD_MARKER_FIELD, ""), default=False):
            continue
        output = {column: (row.get(column) or "").strip() for column in STATUS_WORD_COLUMNS}
        output[STATUS_WORD_MARKER_FIELD] = "Y"
        rows.append(output)
    rows.sort(key=lambda item: item.get("en", "").casefold())
    return rows


def build_spec_title_rows(
    manual_rows: list[dict[str, str]],
    tm_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    tm_index = _build_manual_copy_tm_index(tm_rows)
    rows: list[dict[str, str]] = []
    for row in manual_rows:
        if not _truthy(row.get("Is_Latest", ""), default=True) or not _is_spec_title_row(row):
            continue
        source_lang = (row.get("Source_lang") or "en").strip() or "en"
        source_text = (row.get("source_text") or "").strip()
        if not source_text:
            raise ValueError(f"manual copy source row has empty source_text: {row.get('copy_key', '')}")
        tm_row = tm_index.get(_copy_source_key(source_lang, source_text), {})
        source_tm_field = _tm_field_for_lang(source_lang)
        output = {"section_order": (row.get("section_order") or "").strip()}
        for title_column, tm_field in SPEC_TITLE_TEXT_COLUMNS.items():
            translated = (tm_row.get(tm_field) or "").strip()
            if tm_field == source_tm_field:
                translated = source_text
            output[title_column] = translated or source_text
        rows.append(output)

    rows.sort(
        key=lambda item: (
            _numeric_sort_token(item.get("section_order", "")),
            item.get("title_en", "").casefold(),
        )
    )
    return rows


def csv_text(fieldnames: tuple[str, ...], rows: list[dict[str, str]]) -> str:
    handle = io.StringIO(newline="")
    writer = csv.DictWriter(handle, fieldnames=list(fieldnames), lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({column: row.get(column, "") for column in fieldnames})
    return handle.getvalue()


def missing_translations_csv_text(rows: list[MissingManualCopyTranslation]) -> str:
    handle = io.StringIO(newline="")
    fieldnames = ("copy_key", "source_lang", "target_lang", "source_text")
    writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {
                "copy_key": row.copy_key,
                "source_lang": row.source_lang,
                "target_lang": row.target_lang,
                "source_text": row.source_text,
            }
        )
    return handle.getvalue()
