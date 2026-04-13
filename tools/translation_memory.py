from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tools.build_paths import load_config
from tools.data_snapshot import resolve_data_snapshot_paths, resolve_phase2_export_root

LANGUAGE_ALIASES = {
    "cn": "zh",
    "de": "de",
    "en": "en",
    "english": "en",
    "es": "es",
    "french": "fr",
    "fr": "fr",
    "german": "de",
    "italian": "it",
    "it": "it",
    "ja": "ja",
    "jp": "ja",
    "spanish": "es",
    "uk": "uk",
    "ukrainian": "uk",
    "zh": "zh",
}

TABLE_ALIASES = {
    "footnotes": "spec-footnotes",
    "notes": "spec-notes",
    "spec-footnotes": "spec-footnotes",
    "spec-notes": "spec-notes",
    "spec-titles": "spec-titles",
    "spec_master": "spec-master",
    "spec_footnotes": "spec-footnotes",
    "spec_notes": "spec-notes",
    "spec_titles": "spec-titles",
    "spec-master": "spec-master",
    "symbols": "symbols-blocks",
    "symbols-blocks": "symbols-blocks",
    "symbols_blocks": "symbols-blocks",
    "titles": "spec-titles",
}

TOKEN_RE = re.compile(r"[A-Za-z0-9_./-]+|[\u3040-\u30ff]+|[\u3400-\u9fff]+")
SENTENCE_SPLIT_RE = re.compile(r"(?:\r?\n)+|(?<=[.!?。！？])\s+")
TRUE_VALUES = {"1", "true", "yes", "y", "on"}
FALSE_VALUES = {"0", "false", "no", "n", "off", "disabled"}


@dataclass(slots=True)
class TranslationMemoryEntry:
    table: str
    entry_type: str
    source_lang: str
    source_text: str
    translations: dict[str, str]
    model: str | None = None
    region: str | None = None
    page: str | None = None
    section: str | None = None
    row_key: str | None = None
    slot_key: str | None = None
    line_order: str | None = None
    note_id: str | None = None
    footnote_id: str | None = None
    symbol_key: str | None = None
    aliases: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "table": self.table,
            "entry_type": self.entry_type,
            "source_lang": self.source_lang,
            "source_text": self.source_text,
            "translations": dict(sorted(self.translations.items())),
        }
        optional_fields = {
            "model": self.model,
            "region": self.region,
            "page": self.page,
            "section": self.section,
            "row_key": self.row_key,
            "slot_key": self.slot_key,
            "line_order": self.line_order,
            "note_id": self.note_id,
            "footnote_id": self.footnote_id,
            "symbol_key": self.symbol_key,
        }
        for key, value in optional_fields.items():
            if value:
                payload[key] = value
        if self.aliases:
            payload["aliases"] = list(self.aliases)
        return payload


def normalize_language(raw: str | None) -> str | None:
    value = _clean(raw)
    if not value:
        return None
    return LANGUAGE_ALIASES.get(value.lower(), value.lower())


def normalize_tables(raw_tables: list[str] | tuple[str, ...]) -> set[str]:
    normalized: set[str] = set()
    for raw in raw_tables:
        value = _clean(raw)
        if not value:
            continue
        normalized.add(TABLE_ALIASES.get(value.lower(), value.lower()))
    return normalized


def build_translation_memory_payload(
    *,
    config_path: Path,
    repo_root: Path,
    data_root: str | Path | None = None,
    model: str | None = None,
    region: str | None = None,
    query_text: str | None = None,
    preferred_lang: str | None = None,
    tables: list[str] | tuple[str, ...] = (),
    page: str | None = None,
    section: str | None = None,
    row_key: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    entries, snapshot_root = collect_translation_memory_entries(
        config_path=config_path,
        repo_root=repo_root,
        data_root=data_root,
        model=model,
        region=region,
    )
    matched = query_translation_memory_entries(
        entries,
        query_text=query_text,
        preferred_lang=preferred_lang,
        tables=tables,
        page=page,
        section=section,
        row_key=row_key,
        limit=limit,
    )
    return {
        "query_text": _clean(query_text),
        "preferred_lang": normalize_language(preferred_lang),
        "snapshot_root": _display_path(snapshot_root, repo_root=repo_root),
        "match_count": len(matched),
        "entries": [entry.to_dict() for entry in matched],
    }


def render_translation_memory_payload(payload: dict[str, Any]) -> str:
    query_text = _clean(payload.get("query_text"))
    preferred_lang = normalize_language(str(payload.get("preferred_lang") or ""))
    source_lang = normalize_language(str(payload.get("source_lang") or ""))
    returned_entries = int(payload.get("unique_entry_count") or payload.get("match_count", 0) or 0)
    lines = [
        "# Translation Memory Context",
        "",
        f"- query: `{query_text or '(empty)'}`",
        f"- source_lang: `{source_lang or 'auto'}`",
        f"- preferred_lang: `{preferred_lang or 'none'}`",
        f"- snapshot_root: `{payload.get('snapshot_root') or ''}`",
        f"- returned_entries: `{returned_entries}`",
    ]
    entries = payload.get("entries") or []
    if not entries:
        lines.extend(
            [
                "",
                "No matching translation-memory rows were found.",
                "If the snapshot may be stale, refresh it with `python build.py sync-data --config <config> --data-root data/phase2` first.",
            ]
        )
        return "\n".join(lines)
    for index, entry in enumerate(entries, start=1):
        lines.extend(_render_entry(entry, index=index, preferred_lang=preferred_lang))
    return "\n".join(lines)


def collect_translation_memory_entries(
    *,
    config_path: Path,
    repo_root: Path,
    data_root: str | Path | None = None,
    model: str | None = None,
    region: str | None = None,
) -> tuple[list[TranslationMemoryEntry], Path]:
    cfg = load_config(config_path)
    snapshot_paths = resolve_data_snapshot_paths(
        cfg,
        repo_root=repo_root,
        data_root=data_root,
        model=model,
        region=region,
    )
    phase2_root = resolve_phase2_export_root(
        cfg,
        repo_root=repo_root,
        data_root=data_root,
        model=model,
        region=region,
    )
    row_key_aliases = _load_row_key_aliases(snapshot_paths.row_key_mapping_csv)
    entries: list[TranslationMemoryEntry] = []
    entries.extend(
        _iter_spec_master_entries(
            snapshot_paths.spec_master_csv,
            model=model,
            region=region,
            row_key_aliases=row_key_aliases,
        )
    )
    entries.extend(_iter_spec_title_entries(snapshot_paths.spec_titles_csv))
    entries.extend(_iter_note_like_entries(snapshot_paths.spec_notes_csv, table="spec-notes", id_field="Note_id", model=model, region=region))
    entries.extend(
        _iter_note_like_entries(
            snapshot_paths.spec_footnotes_csv,
            table="spec-footnotes",
            id_field="Footnote_id",
            model=model,
            region=region,
        )
    )
    entries.extend(_iter_symbol_entries(phase2_root / "symbols_blocks.csv", model=model, region=region))
    if not entries:
        raise RuntimeError(
            f"No translation-memory entries were found under {phase2_root}. Run sync-data first or check the snapshot root."
        )
    entries.sort(key=_default_sort_key)
    return entries, phase2_root


def query_translation_memory_entries(
    entries: list[TranslationMemoryEntry],
    *,
    query_text: str | None = None,
    preferred_lang: str | None = None,
    source_lang: str | None = None,
    target_lang: str | None = None,
    tables: list[str] | tuple[str, ...] = (),
    page: str | None = None,
    section: str | None = None,
    row_key: str | None = None,
    limit: int = 10,
) -> list[TranslationMemoryEntry]:
    normalized_query = _normalize_text(query_text)
    preferred_lang_code = normalize_language(preferred_lang)
    source_lang_code = normalize_language(source_lang)
    target_lang_code = normalize_language(target_lang)
    table_filters = normalize_tables(tables)
    page_filter = _normalize_text(page)
    section_filter = _normalize_text(section)
    row_key_filter = _normalize_text(row_key)
    query_tokens = _tokenize(query_text)
    ranked: list[tuple[int, int, TranslationMemoryEntry]] = []

    for index, entry in enumerate(entries):
        if table_filters and entry.table not in table_filters:
            continue
        if page_filter and _normalize_text(entry.page) != page_filter:
            continue
        if section_filter and _normalize_text(entry.section) != section_filter:
            continue
        if row_key_filter and _normalize_text(entry.row_key) != row_key_filter:
            continue
        if source_lang_code and not entry.translations.get(source_lang_code):
            continue
        if target_lang_code and not entry.translations.get(target_lang_code):
            continue

        score = 0
        searchable_values = _entry_searchable_values(entry)
        search_blob = " ".join(searchable_values)
        source_blob = _normalize_text(entry.translations.get(source_lang_code)) if source_lang_code else ""
        target_blob = _normalize_text(entry.translations.get(target_lang_code)) if target_lang_code else ""
        source_token_hits = 0

        if normalized_query:
            if source_blob and normalized_query == source_blob:
                score += 180
            elif normalized_query == _normalize_text(entry.source_text):
                score += 120
            if normalized_query == _normalize_text(entry.row_key):
                score += 110
            if any(normalized_query == _normalize_text(value) for value in entry.translations.values()):
                score += 110
            if source_blob and normalized_query in source_blob:
                score += 60
            if normalized_query in search_blob:
                score += 40
            if source_blob:
                source_token_hits = sum(1 for token in query_tokens if token in source_blob)
                score += source_token_hits * 12
            token_hits = sum(1 for token in query_tokens if token in search_blob)
            if token_hits == 0:
                continue
            score += token_hits * 8
            if query_tokens and token_hits == len(query_tokens):
                score += 24
        if preferred_lang_code and entry.translations.get(preferred_lang_code):
            score += 12
        if target_lang_code and target_blob:
            score += 12
        if source_lang_code and source_token_hits:
            score += 10
        ranked.append((score, index, entry))

    ranked.sort(key=lambda item: (-item[0], item[1]))
    capped_limit = max(limit, 1)
    return [entry for _, _, entry in ranked[:capped_limit]]


def _iter_spec_master_entries(
    path: Path,
    *,
    model: str | None,
    region: str | None,
    row_key_aliases: dict[str, list[str]],
) -> list[TranslationMemoryEntry]:
    rows = _read_csv_rows(path)
    entries: list[TranslationMemoryEntry] = []
    for row in rows:
        if not _row_matches(row, model=model, region=region):
            continue
        if not _latest_enabled(row):
            continue
        source_lang = normalize_language(row.get("Source_lang")) or "en"
        aliases = row_key_aliases.get(_clean(row.get("Row_key")), [])
        metadata = {
            "model": _clean(row.get("Model")),
            "region": _clean(row.get("Region")),
            "page": _clean(row.get("Page")),
            "section": _clean(row.get("Section")),
            "row_key": _clean(row.get("Row_key")),
            "slot_key": _clean(row.get("Slot_key")),
            "line_order": _clean(row.get("Line_order")),
            "aliases": aliases,
        }
        entries.extend(
            _build_entry_set(
                table="spec-master",
                entry_specs=(
                    (
                        "row-label",
                        _translations_from_row(
                            row,
                            source_lang=source_lang,
                            source_key="Row_label_source",
                            explicit_keys={"fr": "Row_label_fr", "es": "Row_label_es"},
                        ),
                    ),
                    (
                        "param",
                        _translations_from_row(
                            row,
                            source_lang=source_lang,
                            source_key="Param_source",
                            explicit_keys={"fr": "Param_fr", "es": "Param_es"},
                        ),
                    ),
                    (
                        "value",
                        _translations_from_row(
                            row,
                            source_lang=source_lang,
                            source_key="Value_source",
                            explicit_keys={"fr": "Value_fr", "es": "Value_es"},
                        ),
                    ),
                ),
                source_lang=source_lang,
                metadata=metadata,
            )
        )
    return entries


def _iter_spec_title_entries(path: Path) -> list[TranslationMemoryEntry]:
    rows = _read_csv_rows(path)
    entries: list[TranslationMemoryEntry] = []
    for row in rows:
        translations = _explicit_language_map(
            row,
            {
                "en": "title_en",
                "zh": "title_zh",
                "ja": "title_jp",
                "fr": "title_fr",
                "es": "title_es",
            },
        )
        source_lang, source_text = _resolve_source_translation(translations, preferred_source="en")
        if not source_text:
            continue
        if source_lang not in translations:
            translations[source_lang] = source_text
        entries.append(
            TranslationMemoryEntry(
                table="spec-titles",
                entry_type="title",
                source_lang=source_lang,
                source_text=source_text,
                translations=translations,
                section=_clean(row.get("title_en")) or source_text,
                line_order=_clean(row.get("section_order")),
            )
        )
    return entries


def _iter_note_like_entries(
    path: Path,
    *,
    table: str,
    id_field: str,
    model: str | None,
    region: str | None,
) -> list[TranslationMemoryEntry]:
    rows = _read_csv_rows(path)
    entries: list[TranslationMemoryEntry] = []
    for row in rows:
        if not _row_matches(row, model=model, region=region):
            continue
        if not _latest_enabled(row):
            continue
        translations = _explicit_language_map(
            row,
            {
                "en": "Text_en",
                "fr": "Text_fr",
                "es": "Text_es",
                "ja": "Text_ja",
            },
        )
        preferred_source = normalize_language(row.get("Source_lang")) or "en"
        source_lang, source_text = _resolve_source_translation(translations, preferred_source=preferred_source)
        if not source_text:
            continue
        if source_lang not in translations:
            translations[source_lang] = source_text
        entry = TranslationMemoryEntry(
            table=table,
            entry_type=table.removeprefix("spec-").removesuffix("s"),
            source_lang=source_lang,
            source_text=source_text,
            translations=translations,
            model=_clean(row.get("Model")),
            region=_clean(row.get("Region")),
            page=_clean(row.get("Page")),
            line_order=_clean(row.get("Note_order")) or _clean(row.get("Footnote_order")),
        )
        identifier = _clean(row.get(id_field))
        if id_field == "Note_id":
            entry.note_id = identifier
        else:
            entry.footnote_id = identifier
        entries.append(entry)
    return entries


def _iter_symbol_entries(path: Path, *, model: str | None, region: str | None) -> list[TranslationMemoryEntry]:
    rows = _read_csv_rows(path)
    entries: list[TranslationMemoryEntry] = []
    for row in rows:
        if not _row_matches(row, model=model, region=region):
            continue
        if _clean(row.get("enabled")) and _clean(row.get("enabled")).lower() in FALSE_VALUES:
            continue
        translations = _explicit_language_map(
            row,
            {
                "en": "text_en",
                "fr": "text_fr",
                "es": "text_es",
            },
        )
        preferred_source = normalize_language(row.get("Source_lang")) or "en"
        source_lang, source_text = _resolve_source_translation(translations, preferred_source=preferred_source)
        if not source_text:
            continue
        if source_lang not in translations:
            translations[source_lang] = source_text
        entries.append(
            TranslationMemoryEntry(
                table="symbols-blocks",
                entry_type="symbol",
                source_lang=source_lang,
                source_text=source_text,
                translations=translations,
                model=_clean(row.get("Model")),
                region=_clean(row.get("Region")),
                page=_clean(row.get("page_id")),
                section=_clean(row.get("block_type")),
                line_order=_clean(row.get("order")),
                symbol_key=_clean(row.get("symbol_key")),
            )
        )
    return entries


def _build_entry_set(
    *,
    table: str,
    entry_specs: tuple[tuple[str, dict[str, str]], ...],
    source_lang: str,
    metadata: dict[str, Any],
) -> list[TranslationMemoryEntry]:
    entries: list[TranslationMemoryEntry] = []
    current_source_lang = source_lang
    for entry_type, translations in entry_specs:
        source_text = translations.get(current_source_lang) or ""
        entry_source_lang = current_source_lang
        if not source_text and translations:
            entry_source_lang, source_text = next(iter(translations.items()))
        if not source_text:
            continue
        entries.append(
            TranslationMemoryEntry(
                table=table,
                entry_type=entry_type,
                source_lang=entry_source_lang,
                source_text=source_text,
                translations=translations,
                model=metadata.get("model"),
                region=metadata.get("region"),
                page=metadata.get("page"),
                section=metadata.get("section"),
                row_key=metadata.get("row_key"),
                slot_key=metadata.get("slot_key"),
                line_order=metadata.get("line_order"),
                aliases=list(metadata.get("aliases") or []),
            )
        )
    return entries


def _translations_from_row(
    row: dict[str, str],
    *,
    source_lang: str,
    source_key: str,
    explicit_keys: dict[str, str],
) -> dict[str, str]:
    translations = _explicit_language_map(row, explicit_keys)
    source_text = _clean(row.get(source_key))
    if source_text:
        translations[source_lang] = source_text
    return translations


def _explicit_language_map(row: dict[str, str], mapping: dict[str, str]) -> dict[str, str]:
    translations: dict[str, str] = {}
    for lang, key in mapping.items():
        value = _clean(row.get(key))
        if value:
            translations[lang] = value
    return translations


def _resolve_source_translation(translations: dict[str, str], *, preferred_source: str) -> tuple[str, str]:
    source_lang = normalize_language(preferred_source) or "en"
    source_text = translations.get(source_lang) or ""
    if source_text:
        return source_lang, source_text
    for fallback_lang, fallback_text in translations.items():
        if fallback_text:
            return fallback_lang, fallback_text
    return source_lang, ""


def _load_row_key_aliases(path: Path) -> dict[str, list[str]]:
    aliases: dict[str, list[str]] = {}
    for row in _read_csv_rows(path):
        row_key = _clean(row.get("Row_key"))
        label = _clean(row.get("Row_label_source"))
        remark = _clean(row.get("Remark"))
        if not row_key:
            continue
        bucket = aliases.setdefault(row_key, [])
        for candidate in (label, remark):
            if candidate and candidate not in bucket:
                bucket.append(candidate)
    return aliases


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _row_matches(row: dict[str, str], *, model: str | None, region: str | None) -> bool:
    row_model = _clean(row.get("Model"))
    row_region = _clean(row.get("Region"))
    if model and row_model and row_model.lower() != model.lower():
        return False
    if region and row_region and row_region.lower() != region.lower():
        return False
    return True


def _latest_enabled(row: dict[str, str]) -> bool:
    is_latest = _clean(row.get("Is_Latest"))
    enabled = _clean(row.get("Enabled"))
    if is_latest and is_latest.lower() not in TRUE_VALUES:
        return False
    if enabled and enabled.lower() in FALSE_VALUES:
        return False
    return True


def _entry_searchable_values(entry: TranslationMemoryEntry) -> list[str]:
    values = [
        entry.table,
        entry.entry_type,
        entry.source_lang,
        entry.source_text,
        entry.model or "",
        entry.region or "",
        entry.page or "",
        entry.section or "",
        entry.row_key or "",
        entry.slot_key or "",
        entry.line_order or "",
        entry.note_id or "",
        entry.footnote_id or "",
        entry.symbol_key or "",
    ]
    values.extend(entry.aliases)
    values.extend(entry.translations.values())
    return [_normalize_text(value) for value in values if _normalize_text(value)]


def _default_sort_key(entry: TranslationMemoryEntry) -> tuple[str, str, str, str, str, str]:
    return (
        entry.table,
        entry.model or "",
        entry.region or "",
        entry.page or "",
        entry.section or "",
        entry.row_key or entry.note_id or entry.footnote_id or entry.symbol_key or "",
    )


def _render_entry(entry: dict[str, Any], *, index: int, preferred_lang: str | None) -> list[str]:
    heading = f"## {index}. {entry.get('table')} / {entry.get('entry_type')}"
    lines = ["", heading]
    lines.append(f"- source: `{entry.get('source_text')}` (`{entry.get('source_lang')}`)")
    translations = entry.get("translations") or {}
    ordered_languages: list[str] = []
    if preferred_lang and preferred_lang in translations:
        ordered_languages.append(preferred_lang)
    for lang in sorted(translations.keys()):
        if lang not in ordered_languages:
            ordered_languages.append(lang)
    translation_bits = [f"`{lang}={translations[lang]}`" for lang in ordered_languages]
    lines.append(f"- translations: {'; '.join(translation_bits) if translation_bits else 'none'}")
    locator_bits = []
    for key in ("model", "region", "page", "section", "row_key", "slot_key", "note_id", "footnote_id", "symbol_key", "line_order"):
        value = entry.get(key)
        if value:
            locator_bits.append(f"`{key}={value}`")
    if locator_bits:
        lines.append(f"- locator: {', '.join(locator_bits)}")
    aliases = entry.get("aliases") or []
    if aliases:
        lines.append(f"- aliases: {', '.join(f'`{alias}`' for alias in aliases)}")
    return lines


def _display_path(path: Path, *, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _clean(raw: Any) -> str:
    if raw is None:
        return ""
    return str(raw).strip()


def _normalize_text(raw: Any) -> str:
    return _clean(raw).lower()


def _tokenize(raw: str | None) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(_clean(raw))]


def payload_to_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)


def split_translation_units(raw: str | None) -> list[str]:
    text = _clean(raw)
    if not text:
        return []
    units: list[str] = []
    for candidate in SENTENCE_SPLIT_RE.split(text):
        normalized = " ".join(candidate.split())
        if normalized and normalized not in units:
            units.append(normalized)
    return units or [" ".join(text.split())]


def render_translation_prompt_context(
    *,
    query_text: str,
    source_lang: str | None,
    target_lang: str | None,
    memory_source: str,
    unit_matches: list[dict[str, Any]],
) -> str:
    lines = [
        "# OpenClaw Translation Prompt Context",
        "",
        "Use the matched translation memory below as the first-choice wording reference.",
        "If no candidate cleanly fits the sentence, stay faithful to the source text and keep terminology consistent.",
        "",
        f"Source language: `{normalize_language(source_lang) or 'auto'}`",
        f"Target language: `{normalize_language(target_lang) or 'auto'}`",
        f"Memory source: `{memory_source}`",
        "",
        "Source text:",
        query_text.strip(),
    ]
    for index, group in enumerate(unit_matches, start=1):
        lines.extend(
            [
                "",
                f"## Unit {index}",
                f"Source unit: `{group.get('source_unit', '')}`",
                f"Matched candidates: `{group.get('match_count', 0)}`",
            ]
        )
        for candidate_index, entry in enumerate(group.get("entries") or [], start=1):
            translations = entry.get("translations") or {}
            source_value = translations.get(normalize_language(source_lang) or "", entry.get("source_text", ""))
            target_value = translations.get(normalize_language(target_lang) or "", "")
            row_locator = entry.get("row_key") or entry.get("note_id") or entry.get("footnote_id") or entry.get("symbol_key") or ""
            lines.append(
                f"{candidate_index}. `{source_value}` -> `{target_value or '[missing target translation]'}`"
            )
            if row_locator:
                lines.append(f"   locator: `{row_locator}`")
    return "\n".join(lines)
