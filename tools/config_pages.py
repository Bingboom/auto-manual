#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import re

from dataclasses import dataclass
from typing import Any, TypeAlias

SUPPORTED_PAGE_TYPES = {"cover_pdf", "csv_page", "generated_page", "pdf_insert", "rst_include"}


@dataclass(frozen=True)
class PageParseIssue:
    level: str  # "ERROR" | "WARN"
    msg: str


@dataclass(frozen=True)
class CoverPdfPage:
    page_type: str
    file: str
    # 能力条件页:装配期按 model_capabilities.csv 选配(None=无条件)
    capability: str | None = None
    # 骨架槽位 id(骨架库产线):非空时物化文件名 = f"{slot_id}.rst",
    # 与列表位置解耦;None=沿用 legacy 命名路径(既有 17 份 manifest 不变)
    slot_id: str | None = None


@dataclass(frozen=True)
class CsvPage:
    page_type: str
    page: str
    source: str
    langs: tuple[str, ...]
    include_dir: str | None
    # 能力条件页:装配期按 model_capabilities.csv 选配(None=无条件)
    capability: str | None = None
    # 骨架槽位 id(见 CoverPdfPage.slot_id);多语页型携带 slot_id 时 langs 必须单元素
    slot_id: str | None = None


@dataclass(frozen=True)
class GeneratedPage:
    page_type: str
    page: str
    engine: str
    recipe: str
    template: str
    langs: tuple[str, ...]
    include_dir: str | None
    # 能力条件页:装配期按 model_capabilities.csv 选配(None=无条件)
    capability: str | None = None
    # 骨架槽位 id(见 CoverPdfPage.slot_id);多语页型携带 slot_id 时 langs 必须单元素
    slot_id: str | None = None


@dataclass(frozen=True)
class PdfInsertPage:
    page_type: str
    file_map: dict[str, str]
    langs: tuple[str, ...]
    # 能力条件页:装配期按 model_capabilities.csv 选配(None=无条件)
    capability: str | None = None
    # 骨架槽位 id(见 CoverPdfPage.slot_id);多语页型携带 slot_id 时 langs 必须单元素
    slot_id: str | None = None


@dataclass(frozen=True)
class RstIncludePage:
    page_type: str
    file: str
    lang: str | None
    # 能力条件页:装配期按 model_capabilities.csv 选配(None=无条件)
    capability: str | None = None
    # 多语整页:模板内含多个语言块(前言页),装配期按 model_languages.csv
    # 解析出的语言集合裁掉块(False=整页按 lang 归属单一语言)
    lang_blocks: bool = False
    # 序数中立:该条目不消耗重名消歧序数(pNN_ 前缀编号)。用于向已定稿的
    # 清单中段插入印刷专用页(目录/封底)——后续重名页保持既有 pNN 名,
    # 评审分支文件名与版式契约钉住的 source_ref 才不会整体漂移。
    ordinal_neutral: bool = False
    # 骨架槽位 id(见 CoverPdfPage.slot_id)
    slot_id: str | None = None


ConfigPage: TypeAlias = CoverPdfPage | CsvPage | GeneratedPage | PdfInsertPage | RstIncludePage


def _slot_id_single_lang_issue(
    idx: int,
    page_type: str,
    slot_id: str | None,
    langs: tuple[str, ...],
) -> PageParseIssue | None:
    if slot_id is not None and len(langs) != 1:
        return PageParseIssue(
            "ERROR",
            f"pages[{idx}].slot_id requires a single-language langs list "
            f"on {page_type} (got {len(langs)})")
    return None


def _is_list_of_str(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(i, str) for i in value)


def parse_config_pages(
    pages_raw: Any,
    *,
    default_languages: list[str] | None = None,
    model: str | None = None,
) -> tuple[list[ConfigPage], list[PageParseIssue]]:
    issues: list[PageParseIssue] = []
    parsed: list[ConfigPage] = []

    default_langs = tuple(default_languages or [])
    seen_slot_ids: set[str] = set()

    if not isinstance(pages_raw, list) or not pages_raw:
        issues.append(PageParseIssue("ERROR", "pages must be non-empty list"))
        return parsed, issues

    for idx, raw in enumerate(pages_raw, start=1):
        if not isinstance(raw, dict):
            issues.append(PageParseIssue("ERROR", f"pages[{idx}] must be mapping"))
            continue

        page_type = raw.get("type")
        if page_type not in SUPPORTED_PAGE_TYPES:
            issues.append(PageParseIssue("ERROR", f"pages[{idx}].type invalid: {page_type}"))
            continue

        capability_raw = raw.get("capability")
        if capability_raw is not None and (
                not isinstance(capability_raw, str) or not capability_raw.strip()):
            issues.append(PageParseIssue(
                "ERROR", f"pages[{idx}].capability must be a non-empty string"))
            continue
        capability = capability_raw.strip() if isinstance(capability_raw, str) else None

        slot_id_raw = raw.get("slot_id")
        if slot_id_raw is not None and (
                not isinstance(slot_id_raw, str) or not slot_id_raw.strip()):
            issues.append(PageParseIssue(
                "ERROR", f"pages[{idx}].slot_id must be a non-empty string"))
            continue
        slot_id = slot_id_raw.strip() if isinstance(slot_id_raw, str) else None
        if slot_id is not None:
            # Safe-basename guard: slot names become materialized file names
            # directly, so they must stay flat identifiers (the legacy path
            # guaranteed this via Path(...).name; slot naming must not regress
            # it, and must not be able to mint a pNN_-shaped name).
            if not re.fullmatch(r"[a-z][a-z0-9_-]*", slot_id) or re.match(r"p\d+_", slot_id):
                issues.append(PageParseIssue(
                    "ERROR",
                    f"pages[{idx}].slot_id must match [a-z][a-z0-9_-]* and must not "
                    f"look like a pNN_ prefix: {slot_id}"))
                continue
            if slot_id in seen_slot_ids:
                issues.append(PageParseIssue(
                    "ERROR", f"pages[{idx}].slot_id duplicated in manifest: {slot_id}"))
                continue
            seen_slot_ids.add(slot_id)

        lang_blocks_raw = raw.get("lang_blocks")
        if lang_blocks_raw is not None and not isinstance(lang_blocks_raw, bool):
            issues.append(PageParseIssue(
                "ERROR", f"pages[{idx}].lang_blocks must be a boolean"))
            continue
        # Reject the annotation on page types that cannot carry inline language
        # blocks, so a mis-annotated manifest fails instead of silently
        # trimming nothing.
        if lang_blocks_raw is not None and page_type != "rst_include":
            issues.append(PageParseIssue(
                "ERROR",
                f"pages[{idx}].lang_blocks is only supported on rst_include, "
                f"not {page_type}"))
            continue

        ordinal_neutral_raw = raw.get("ordinal_neutral")
        if ordinal_neutral_raw is not None and not isinstance(ordinal_neutral_raw, bool):
            issues.append(PageParseIssue(
                "ERROR", f"pages[{idx}].ordinal_neutral must be a boolean"))
            continue
        # Same containment rule as lang_blocks: a mis-annotated manifest must
        # fail loudly instead of silently destabilizing tail page numbering.
        if ordinal_neutral_raw is not None and page_type != "rst_include":
            issues.append(PageParseIssue(
                "ERROR",
                f"pages[{idx}].ordinal_neutral is only supported on rst_include, "
                f"not {page_type}"))
            continue

        if page_type == "cover_pdf":
            file_name = raw.get("file")
            if not isinstance(file_name, str) or not file_name.strip():
                issues.append(PageParseIssue("ERROR", f"pages[{idx}] cover_pdf requires file"))
                continue
            parsed.append(CoverPdfPage(page_type=page_type, file=file_name.strip(), capability=capability, slot_id=slot_id))
            continue

        if page_type == "csv_page":
            page_name = raw.get("page")
            if not isinstance(page_name, str) or not page_name.strip():
                issues.append(PageParseIssue("ERROR", f"pages[{idx}] csv_page requires page"))
                continue

            source = str(raw.get("source", "phase2")).strip().lower()
            if source != "phase2":
                issues.append(PageParseIssue("ERROR", f"pages[{idx}] csv_page.source invalid: {source}"))
                continue

            page_langs_raw = raw.get("langs", list(default_langs))
            if not _is_list_of_str(page_langs_raw):
                issues.append(PageParseIssue("ERROR", f"pages[{idx}] csv_page.langs invalid"))
                continue
            page_langs = tuple(page_langs_raw)

            include_dir = raw.get("include_dir")
            if include_dir is not None and not isinstance(include_dir, str):
                issues.append(PageParseIssue("ERROR", f"pages[{idx}] csv_page.include_dir must be string"))
                continue
            include_dir_text = include_dir.strip() if isinstance(include_dir, str) else None
            if include_dir_text == "":
                issues.append(PageParseIssue("ERROR", f"pages[{idx}] csv_page.include_dir must be non-empty string"))
                continue

            single_lang_issue = _slot_id_single_lang_issue(idx, "csv_page", slot_id, page_langs)
            if single_lang_issue is not None:
                issues.append(single_lang_issue)
                continue
            parsed.append(
                CsvPage(
                    page_type=page_type,
                    page=page_name.strip(),
                    source=source,
                    langs=page_langs,
                    include_dir=include_dir_text,
                    capability=capability,
                    slot_id=slot_id,
                )
            )
            continue

        if page_type == "generated_page":
            page_name = raw.get("page")
            if not isinstance(page_name, str) or not page_name.strip():
                issues.append(PageParseIssue("ERROR", f"pages[{idx}] generated_page requires page"))
                continue

            engine = str(raw.get("engine", "")).strip().lower()
            if engine != "draft_v1":
                issues.append(
                    PageParseIssue(
                        "ERROR",
                        f"pages[{idx}] generated_page.engine invalid: {engine}",
                    )
                )
                continue

            model_overrides_raw = raw.get("model_overrides", {})
            if not isinstance(model_overrides_raw, dict):
                issues.append(
                    PageParseIssue(
                        "ERROR",
                        f"pages[{idx}] generated_page.model_overrides must be a mapping",
                    )
                )
                continue
            invalid_override = False
            for override_model, override_raw in model_overrides_raw.items():
                if not isinstance(override_model, str) or not override_model.strip():
                    issues.append(
                        PageParseIssue(
                            "ERROR",
                            f"pages[{idx}] generated_page.model_overrides keys must be non-empty strings",
                        )
                    )
                    invalid_override = True
                    continue
                if not isinstance(override_raw, dict):
                    issues.append(
                        PageParseIssue(
                            "ERROR",
                            f"pages[{idx}] generated_page.model_overrides.{override_model} must be a mapping",
                        )
                    )
                    invalid_override = True
                    continue
                unknown_keys = sorted(set(override_raw) - {"recipe", "template"})
                if unknown_keys:
                    issues.append(
                        PageParseIssue(
                            "ERROR",
                            f"pages[{idx}] generated_page.model_overrides.{override_model} has unsupported fields: "
                            + ", ".join(unknown_keys),
                        )
                    )
                    invalid_override = True
                for field_name in ("recipe", "template"):
                    field_value = override_raw.get(field_name)
                    if field_value is not None and (
                        not isinstance(field_value, str) or not field_value.strip()
                    ):
                        issues.append(
                            PageParseIssue(
                                "ERROR",
                                f"pages[{idx}] generated_page.model_overrides.{override_model}."
                                f"{field_name} must be a non-empty string",
                            )
                        )
                        invalid_override = True
            if invalid_override:
                continue

            selected_override_raw = model_overrides_raw.get((model or "").strip(), {})
            selected_override = selected_override_raw if isinstance(selected_override_raw, dict) else {}

            recipe = selected_override.get("recipe", raw.get("recipe"))
            if not isinstance(recipe, str) or not recipe.strip():
                issues.append(PageParseIssue("ERROR", f"pages[{idx}] generated_page requires recipe"))
                continue

            template = selected_override.get("template", raw.get("template"))
            if not isinstance(template, str) or not template.strip():
                issues.append(PageParseIssue("ERROR", f"pages[{idx}] generated_page requires template"))
                continue

            page_langs_raw = raw.get("langs", list(default_langs))
            if not _is_list_of_str(page_langs_raw):
                issues.append(PageParseIssue("ERROR", f"pages[{idx}] generated_page.langs invalid"))
                continue
            page_langs = tuple(page_langs_raw)

            include_dir = raw.get("include_dir")
            if include_dir is not None and not isinstance(include_dir, str):
                issues.append(
                    PageParseIssue(
                        "ERROR",
                        f"pages[{idx}] generated_page.include_dir must be string",
                    )
                )
                continue
            include_dir_text = include_dir.strip() if isinstance(include_dir, str) else None
            if include_dir_text == "":
                issues.append(
                    PageParseIssue(
                        "ERROR",
                        f"pages[{idx}] generated_page.include_dir must be non-empty string",
                    )
                )
                continue

            single_lang_issue = _slot_id_single_lang_issue(idx, "generated_page", slot_id, page_langs)
            if single_lang_issue is not None:
                issues.append(single_lang_issue)
                continue
            parsed.append(
                GeneratedPage(
                    page_type=page_type,
                    page=page_name.strip(),
                    engine=engine,
                    recipe=recipe.strip(),
                    template=template.strip(),
                    langs=page_langs,
                    include_dir=include_dir_text,
                    capability=capability,
                    slot_id=slot_id,
                )
            )
            continue

        if page_type == "pdf_insert":
            file_map_raw = raw.get("file_map")
            if not isinstance(file_map_raw, dict):
                issues.append(PageParseIssue("ERROR", f"pages[{idx}] pdf_insert requires file_map"))
                continue

            file_map: dict[str, str] = {}
            bad_file_map = False
            for key, value in file_map_raw.items():
                if not isinstance(value, str) or not value.strip():
                    issues.append(
                        PageParseIssue(
                            "ERROR",
                            f"pages[{idx}] pdf_insert.file_map['{key}'] must be non-empty string",
                        )
                    )
                    bad_file_map = True
                    continue
                file_map[str(key)] = value.strip()
            if bad_file_map:
                continue

            page_langs_raw = raw.get("langs", list(default_langs))
            if not _is_list_of_str(page_langs_raw):
                issues.append(PageParseIssue("ERROR", f"pages[{idx}] pdf_insert.langs invalid"))
                continue

            single_lang_issue = _slot_id_single_lang_issue(
                idx, "pdf_insert", slot_id, tuple(page_langs_raw))
            if single_lang_issue is not None:
                issues.append(single_lang_issue)
                continue
            parsed.append(
                PdfInsertPage(
                    page_type=page_type,
                    file_map=file_map,
                    langs=tuple(page_langs_raw),
                    capability=capability,
                    slot_id=slot_id,
                )
            )
            continue

        if page_type == "rst_include":
            file_name = raw.get("file")
            if not isinstance(file_name, str) or not file_name.strip():
                issues.append(PageParseIssue("ERROR", f"pages[{idx}] rst_include requires non-empty file"))
                continue

            lang_raw = raw.get("lang")
            if lang_raw is not None and not isinstance(lang_raw, str):
                issues.append(PageParseIssue("ERROR", f"pages[{idx}] rst_include.lang must be string"))
                continue

            lang = lang_raw.strip() if isinstance(lang_raw, str) and lang_raw.strip() else None
            parsed.append(
                RstIncludePage(
                    page_type=page_type,
                    file=file_name.strip(),
                    lang=lang,
                    capability=capability,
                    lang_blocks=bool(lang_blocks_raw),
                    ordinal_neutral=bool(ordinal_neutral_raw),
                    slot_id=slot_id,
                )
            )
            continue

    # Slot naming is all-or-nothing per manifest: in a mixed manifest an
    # earlier slot page could silently steal the bare name a later legacy page
    # would have received (first-wins), flipping the legacy page to a pNN_
    # name — the exact rename class the slot mechanism exists to prevent.
    if parsed and seen_slot_ids:
        missing_slot = [p for p in parsed if getattr(p, "slot_id", None) is None]
        if missing_slot:
            issues.append(PageParseIssue(
                "ERROR",
                "manifest mixes slot_id and legacy entries "
                f"({len(missing_slot)} of {len(parsed)} pages lack slot_id); "
                "slot naming is all-or-nothing per manifest"))

    return parsed, issues


def parse_config_pages_or_raise(
    pages_raw: Any,
    *,
    default_languages: list[str] | None = None,
    model: str | None = None,
    error_prefix: str | None = None,
) -> list[ConfigPage]:
    pages, issues = parse_config_pages(
        pages_raw,
        default_languages=default_languages,
        model=model,
    )
    errors = [i for i in issues if i.level == "ERROR"]
    if not errors:
        return pages

    first = errors[0].msg
    if error_prefix:
        raise RuntimeError(f"{error_prefix}: {first}")
    raise RuntimeError(first)
