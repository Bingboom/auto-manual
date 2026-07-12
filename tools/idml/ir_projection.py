"""Project ``manual-ir/v1`` into the production IDML writer inputs.

This is the only compatibility boundary between the renderer-neutral IR and
the established IDML page composers.  It deliberately has no phase2 loader
dependency: all editable copy and table rows come from the prepared bundle.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.manual_ir import ManualIR, ManualPage, build_manual_ir, validate_manual_ir
from tools.utils.path_utils import PathSegments

from .latex_page_plan import (
    build_page_plan,
    find_reference_pdf,
    planned_span,
    validate_page_plan,
    write_page_plan,
)


@dataclass(frozen=True)
class ProjectedPage:
    path: Path
    language: str
    blocks: tuple[tuple[str, str], ...]
    skipped_raw: int
    twocol: bool


@dataclass(frozen=True)
class SpecPageData:
    title: str
    sections: tuple[dict[str, Any], ...]
    annotations: tuple[str, ...]


@dataclass(frozen=True)
class LcdPageData:
    title: str
    rows: tuple[dict[str, str], ...]


@dataclass(frozen=True)
class SymbolPageData:
    title: str
    signals: tuple[tuple[str, str], ...]
    icons: tuple[dict[str, str], ...]


def _page_blocks(page: ManualPage) -> tuple[tuple[str, str], ...]:
    blocks: list[tuple[str, str]] = []
    for block in page.blocks:
        if block.kind == "data":
            continue
        if block.kind in {"component", "table"}:
            value = json.dumps(block.payload, ensure_ascii=False)
        else:
            value = str(block.payload)
        blocks.append((block.kind, value))
    return tuple(blocks)


def project_pages(ir: ManualIR, bundle_root: Path) -> tuple[ProjectedPage, ...]:
    pages = []
    for page in ir.pages:
        blocks = _page_blocks(page)
        pages.append(ProjectedPage(
            path=bundle_root / page.source_path,
            language=page.language,
            blocks=blocks,
            skipped_raw=page.skipped_raw,
            twocol=any(kind == "layout" for kind, _ in blocks),
        ))
    return tuple(pages)


def _matching_page(ir: ManualIR, prefix: str, lang: str) -> ManualPage | None:
    candidates = [
        page for page in ir.pages
        if Path(page.source_path).name.startswith(prefix) and page.language == lang
    ]
    return candidates[0] if candidates else None


def _data_payloads(page: ManualPage | None) -> list[dict[str, Any]]:
    if page is None:
        return []
    return [block.payload for block in page.blocks
            if block.kind == "data" and isinstance(block.payload, dict)]


def _heading(page: ManualPage | None, fallback: str) -> str:
    if page is not None:
        for block in page.blocks:
            if block.kind == "h1" and isinstance(block.payload, str):
                return block.payload
    return fallback


def spec_page_data(ir: ManualIR, lang: str) -> SpecPageData | None:
    page = _matching_page(ir, "spec_", lang)
    payloads = _data_payloads(page)
    sections = tuple(payload for payload in payloads if payload.get("kind") == "spec_section")
    if not sections:
        return None
    title = next((str(payload.get("title") or "") for payload in payloads
                  if payload.get("kind") == "spec_start"), "")
    annotations = tuple(
        str(text)
        for payload in payloads if payload.get("kind") == "spec_annotations"
        for text in payload.get("texts", []) if str(text)
    )
    return SpecPageData(title or _heading(page, "SPECIFICATIONS"), sections, annotations)


def _circled(index: int) -> str:
    if index <= 20:
        return chr(0x245F + index)
    return chr(0x323C + index)


def _asset_path(root: Path, data_root: Path, category: str, reference: str) -> str:
    path = Path(reference)
    if path.is_absolute() and path.exists():
        return path.as_posix()
    direct = root / path
    if direct.exists():
        return direct.as_posix()
    attachment = data_root / "_attachments" / category / path.name
    if attachment.exists():
        return attachment.as_posix()
    return reference


def lcd_page_data(
    ir: ManualIR, lang: str, *, root: Path, data_root: Path,
) -> LcdPageData | None:
    page = _matching_page(ir, "lcd_icons_", lang)
    payload = next((payload for payload in _data_payloads(page)
                    if payload.get("kind") == "lcd_icons"), None)
    if payload is None or not payload.get("rows"):
        return None
    rows = []
    for index, source in enumerate(payload["rows"], start=1):
        row = {key: str(source.get(key) or "") for key in ("no", "figure", "name", "desc")}
        row["no"] = _circled(index)
        row["figure"] = _asset_path(root, data_root, "lcd_icons", row["figure"])
        rows.append(row)
    return LcdPageData(_heading(page, "LCD DISPLAY"), tuple(rows))


def symbol_page_data(
    ir: ManualIR, lang: str, *, root: Path, data_root: Path,
) -> SymbolPageData | None:
    page = _matching_page(ir, "symbols_", lang)
    payloads = _data_payloads(page)
    signal_payload = next((payload for payload in payloads
                           if payload.get("kind") == "symbol_signals"), None)
    icon_payload = next((payload for payload in payloads
                         if payload.get("kind") == "symbol_icons"), None)
    signals = tuple(
        (str(row.get("label") or ""), str(row.get("text") or ""))
        for row in (signal_payload or {}).get("rows", [])
        if row.get("text")
    )
    icons = tuple(
        {
            "figure": _asset_path(root, data_root, "symbols", str(row.get("figure") or "")),
            "text": str(row.get("text") or ""),
        }
        for row in (icon_payload or {}).get("rows", [])
        if row.get("text")
    )
    if not (signals or icons):
        return None
    return SymbolPageData(_heading(page, "MEANING OF SYMBOLS"), signals, icons)


def trouble_rows(ir: ManualIR, lang: str) -> tuple[tuple[str, str], ...]:
    page = _matching_page(ir, "troubleshooting_", lang)
    if page is None:
        return ()
    payload = next((payload for payload in _data_payloads(page)
                    if payload.get("kind") == "trouble_rows"), None)
    if payload is not None:
        return tuple((str(row[0]), str(row[1]))
                     for row in payload.get("rows", []) if len(row) >= 2)
    for block in page.blocks:
        if block.kind != "table" or not isinstance(block.payload, list):
            continue
        rows = block.payload[1:] if block.payload else []
        return tuple((str(row[0]), str(row[1])) for row in rows if len(row) >= 2)
    return ()


def same_source_issues(ir: ManualIR) -> list[str]:
    """Completeness gate for data that production IDML must not re-query."""
    issues = []
    for lang in sorted({page.language for page in ir.pages}):
        if _matching_page(ir, "spec_", lang) and spec_page_data(ir, lang) is None:
            issues.append(f"{lang}: spec page has no semantic sections")
        if _matching_page(ir, "lcd_icons_", lang) and not any(
            payload.get("kind") == "lcd_icons"
            for payload in _data_payloads(_matching_page(ir, "lcd_icons_", lang))
        ):
            issues.append(f"{lang}: LCD page has no semantic rows")
        if _matching_page(ir, "symbols_", lang) and symbol_page_data(
            ir, lang, root=Path("."), data_root=Path(".")
        ) is None:
            issues.append(f"{lang}: symbols page has no semantic rows")
    return issues


def build_same_source_ir(
    *, root: Path, bundle_root: Path, model: str, region: str, lang: str,
    data_root: Path,
) -> ManualIR:
    """Build and enforce the production IDML same-source contract."""
    ir = build_manual_ir(
        root=root, bundle_root=bundle_root, model=model, region=region,
        lang=lang, source="prepared-bundle", data_root=data_root)
    issues = validate_manual_ir(ir, require_zero_skipped_raw=True)
    issues.extend(same_source_issues(ir))
    if issues:
        raise ValueError("; ".join(issues))
    return ir


def build_reference_page_plan(ir: ManualIR, *, bundle_root: Path) -> dict[str, Any] | None:
    reference_pdf = find_reference_pdf(bundle_root)
    if reference_pdf is None:
        return None
    plan = build_page_plan(ir, reference_pdf)
    issues = validate_page_plan(plan)
    if issues:
        raise ValueError("LaTeX page plan validation failed: " + "; ".join(issues))
    return plan


def emit_reference_page_plan(plan: dict[str, Any] | None, *, out_dir: Path) -> Path | None:
    """Write a validated LaTeX reference plan beside production IDML."""
    if plan is None:
        return None
    path = write_page_plan(plan, out_dir / PathSegments.LATEX_PAGE_PLAN_JSON)
    print(
        f"[export-idml] PAGE PLAN OK: {path} | "
        f"physical={plan['physical_page_count']} matched={plan['matched_source_pages']}/"
        f"{plan['source_page_count']} ({plan['match_rate']:.1%})"
    )
    return path


def planned_story_pages(plan: dict[str, Any] | None, title: str, fallback: int) -> int:
    return planned_span(plan, title.split(" + "), fallback)
