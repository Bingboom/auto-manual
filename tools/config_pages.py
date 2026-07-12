#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

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


@dataclass(frozen=True)
class CsvPage:
    page_type: str
    page: str
    source: str
    langs: tuple[str, ...]
    include_dir: str | None
    # 能力条件页:装配期按 model_capabilities.csv 选配(None=无条件)
    capability: str | None = None


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


@dataclass(frozen=True)
class PdfInsertPage:
    page_type: str
    file_map: dict[str, str]
    langs: tuple[str, ...]
    # 能力条件页:装配期按 model_capabilities.csv 选配(None=无条件)
    capability: str | None = None


@dataclass(frozen=True)
class RstIncludePage:
    page_type: str
    file: str
    lang: str | None
    # 能力条件页:装配期按 model_capabilities.csv 选配(None=无条件)
    capability: str | None = None


ConfigPage: TypeAlias = CoverPdfPage | CsvPage | GeneratedPage | PdfInsertPage | RstIncludePage


def _is_list_of_str(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(i, str) for i in value)


def parse_config_pages(
    pages_raw: Any,
    *,
    default_languages: list[str] | None = None,
) -> tuple[list[ConfigPage], list[PageParseIssue]]:
    issues: list[PageParseIssue] = []
    parsed: list[ConfigPage] = []

    default_langs = tuple(default_languages or [])

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

        if page_type == "cover_pdf":
            file_name = raw.get("file")
            if not isinstance(file_name, str) or not file_name.strip():
                issues.append(PageParseIssue("ERROR", f"pages[{idx}] cover_pdf requires file"))
                continue
            parsed.append(CoverPdfPage(page_type=page_type, file=file_name.strip(), capability=capability))
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

            parsed.append(
                CsvPage(
                    page_type=page_type,
                    page=page_name.strip(),
                    source=source,
                    langs=page_langs,
                    include_dir=include_dir_text,
                    capability=capability,
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

            recipe = raw.get("recipe")
            if not isinstance(recipe, str) or not recipe.strip():
                issues.append(PageParseIssue("ERROR", f"pages[{idx}] generated_page requires recipe"))
                continue

            template = raw.get("template")
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

            parsed.append(
                PdfInsertPage(
                    page_type=page_type,
                    file_map=file_map,
                    langs=tuple(page_langs_raw),
                    capability=capability,
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
                )
            )
            continue

    return parsed, issues


def parse_config_pages_or_raise(
    pages_raw: Any,
    *,
    default_languages: list[str] | None = None,
    error_prefix: str | None = None,
) -> list[ConfigPage]:
    pages, issues = parse_config_pages(pages_raw, default_languages=default_languages)
    errors = [i for i in issues if i.level == "ERROR"]
    if not errors:
        return pages

    first = errors[0].msg
    if error_prefix:
        raise RuntimeError(f"{error_prefix}: {first}")
    raise RuntimeError(first)
