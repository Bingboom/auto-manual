from __future__ import annotations

from pathlib import Path
from typing import Any, Callable


def base_file_name_for_plan(
    page: Any,
    *,
    lang: str | None,
    model: str | None,
    region: str | None,
    csv_page_cls: type[Any],
    generated_page_cls: type[Any],
    pdf_insert_page_cls: type[Any],
    rst_include_page_cls: type[Any],
    cover_pdf_page_cls: type[Any],
    format_tokenized: Callable[[str, str | None, str | None], str],
) -> str:
    if isinstance(page, cover_pdf_page_cls):
        pdf_path = format_tokenized(page.file, model, region)
        stem = Path(pdf_path).stem or "cover"
        return f"{stem}.rst"
    if isinstance(page, csv_page_cls):
        assert lang is not None
        return f"{page.page}_{lang}.rst"
    if isinstance(page, generated_page_cls):
        rst_path = format_tokenized(page.template, model, region)
        name = Path(rst_path).name
        return name if name.lower().endswith(".rst") else f"{name}.rst"
    if isinstance(page, pdf_insert_page_cls):
        assert lang is not None
        pdf_path = format_tokenized(page.file_map[lang], model, region)
        stem = Path(pdf_path).stem or "pdf_insert"
        return f"{stem}_{lang}.rst"
    if isinstance(page, rst_include_page_cls):
        rst_path = format_tokenized(page.file, model, region)
        name = Path(rst_path).name
        return name if name.lower().endswith(".rst") else f"{name}.rst"
    raise RuntimeError(f"Unsupported page type: {type(page).__name__}")


def ensure_unique_name(file_name: str, seen: set[str], ordinal: int) -> str:
    if file_name not in seen:
        seen.add(file_name)
        return file_name

    prefixed = f"p{ordinal:02d}_{file_name}"
    if prefixed not in seen:
        seen.add(prefixed)
        return prefixed

    seq = 2
    stem = Path(file_name).stem
    suffix = Path(file_name).suffix
    while True:
        candidate = f"p{ordinal:02d}_{stem}_{seq}{suffix}"
        if candidate not in seen:
            seen.add(candidate)
            return candidate
        seq += 1


def plan_materialized_pages(
    cfg: dict,
    model: str | None = None,
    region: str | None = None,
    *,
    langs: list[str] | None = None,
    root: Path,
    build_langs: Callable[[dict], list[str]],
    resolve_config_pages_or_raise: Callable[..., Any],
    planned_page_cls: type[Any],
    csv_page_cls: type[Any],
    generated_page_cls: type[Any],
    pdf_insert_page_cls: type[Any],
    rst_include_page_cls: type[Any],
    cover_pdf_page_cls: type[Any],
    format_tokenized: Callable[[str, str | None, str | None], str],
    base_file_name_for_plan: Callable[..., str],
    ensure_unique_name: Callable[[str, set[str], int], str],
) -> list[Any]:
    selected_langs = list(langs) if langs is not None else build_langs(cfg)
    pages = resolve_config_pages_or_raise(
        cfg,
        default_languages=selected_langs,
        root=root,
        model=model,
        region=region,
        error_prefix="config.pages",
    ).pages

    from tools.capability_pages import filter_pages_by_capability
    pages, dropped = filter_pages_by_capability(
        pages, model=model, region=region, data_dir=root / "data")
    for note in dropped:
        print(f"[bundle-plan] {note}")

    planned: list[Any] = []
    seen_names: set[str] = set()

    for ordinal, page in enumerate(pages, start=1):
        if isinstance(page, cover_pdf_page_cls):
            base_name = base_file_name_for_plan(page, lang=None, model=model, region=region)
            planned.append(
                planned_page_cls(
                    page=page,
                    lang=None,
                    file_name=ensure_unique_name(base_name, seen_names, ordinal),
                )
            )
            continue

        if isinstance(page, pdf_insert_page_cls):
            page_langs = [lang for lang in (list(page.langs) or selected_langs) if lang in selected_langs]
            for lang in page_langs:
                if lang not in page.file_map:
                    raise RuntimeError(f"pdf_insert.file_map missing lang '{lang}'")
                base_name = base_file_name_for_plan(page, lang=lang, model=model, region=region)
                planned.append(
                    planned_page_cls(
                        page=page,
                        lang=lang,
                        file_name=ensure_unique_name(base_name, seen_names, ordinal),
                    )
                )
            continue

        if isinstance(page, csv_page_cls):
            page_langs = [lang for lang in (list(page.langs) or selected_langs) if lang in selected_langs]
            if page.include_dir:
                format_tokenized(page.include_dir, model, region)
            for lang in page_langs:
                base_name = base_file_name_for_plan(page, lang=lang, model=model, region=region)
                planned.append(
                    planned_page_cls(
                        page=page,
                        lang=lang,
                        file_name=ensure_unique_name(base_name, seen_names, ordinal),
                    )
                )
            continue

        if isinstance(page, generated_page_cls):
            page_langs = [lang for lang in (list(page.langs) or selected_langs) if lang in selected_langs]
            format_tokenized(page.recipe, model, region)
            format_tokenized(page.template, model, region)
            if page.include_dir:
                format_tokenized(page.include_dir, model, region)
            for lang in page_langs:
                base_name = base_file_name_for_plan(page, lang=lang, model=model, region=region)
                planned.append(
                    planned_page_cls(
                        page=page,
                        lang=lang,
                        file_name=ensure_unique_name(base_name, seen_names, ordinal),
                    )
                )
            continue

        if isinstance(page, rst_include_page_cls):
            if page.lang is not None and page.lang not in selected_langs:
                continue
            base_name = base_file_name_for_plan(page, lang=page.lang, model=model, region=region)
            planned.append(
                planned_page_cls(
                    page=page,
                    lang=page.lang,
                    file_name=ensure_unique_name(base_name, seen_names, ordinal),
                )
            )
            continue

        raise RuntimeError(f"Unsupported page type: {type(page).__name__}")

    return planned


def build_index_from_pages(
    cfg: dict,
    model: str | None = None,
    region: str | None = None,
    *,
    langs: list[str] | None = None,
    root: Path,
    plan_materialized_pages: Callable[..., list[Any]],
) -> str:
    # Sphinx uses the first RST title style it sees to seed the whole
    # document hierarchy. Give LaTeX a hidden document title with a distinct
    # overline style so page-level "=" titles remain level 1 and page-local
    # "-" titles remain level 2, without asking templates to carry this rule.
    lines: list[str] = [
        ".. only:: latex",
        "",
        "   =============",
        "   Manual Bundle",
        "   =============",
        "",
    ]
    for planned in plan_materialized_pages(cfg, model=model, region=region, langs=langs, root=root):
        lines.extend([f".. include:: page/{planned.file_name}", ""])
    return "\n".join(lines) + "\n"


def build_wrapper_index_text(
    *,
    docs_dir: Path,
    bundle_dir: Path,
) -> str:
    bundle_rel = bundle_dir.relative_to(docs_dir).as_posix()
    return "\n".join(
        [
            ".. Auto-generated by tools/gen_index_bundle.py. Do not edit directly.",
            "",
            f".. include:: {bundle_rel}/index",
            "",
        ]
    )
