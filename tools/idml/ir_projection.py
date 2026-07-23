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

from tools.attachment_identity import resolve_semantic_attachment
from tools.manual_ir import ManualIR, ManualPage, build_manual_ir, validate_manual_ir
from tools.utils.path_utils import PathSegments

from .latex_page_plan import (
    build_page_plan,
    find_reference_pdf,
    planned_span,
    validate_page_plan,
    write_page_plan,
)
from .data_components import parse_data_component
from .lcd_reference_profile import apply_lcd_reference_profile
from .reference_layout_plan import load_approved_reference_plan


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
            twocol=any(kind == "layout" and value.startswith("twocol_")
                       for kind, value in blocks),
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


def _special_payload(ir: ManualIR, kind: str) -> dict[str, Any] | None:
    return next((payload for page in ir.pages for payload in _data_payloads(page)
                 if payload.get("kind") == kind), None)


def toc_page_data(ir: ManualIR, bundle_root: Path | None = None) -> dict[str, Any] | None:
    """Return the source-authored TOC title, language blocks, and folios."""
    payload = _special_payload(ir, "toc")
    if payload is not None or bundle_root is None:
        return payload
    template_toc = (
        Path(__file__).resolve().parents[2]
        / "docs" / "templates" / "page_shared" / "en" / "00_toc.rst"
    )
    for candidate in (
        bundle_root / "page" / "00_toc.rst",
        bundle_root / "00_toc.rst",
        template_toc,
    ):
        if not candidate.is_file():
            continue
        parsed = parse_data_component(candidate.read_text(encoding="utf-8"))
        if parsed and parsed.get("kind") == "toc":
            return parsed
    return None


def back_cover_data(ir: ManualIR) -> dict[str, Any] | None:
    """Return the source-authored back-cover company/contact copy."""
    return _special_payload(ir, "back_cover")


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
    attachment = resolve_semantic_attachment(
        data_root / "_attachments" / category,
        path.name,
    )
    if attachment is not None:
        return attachment.as_posix()
    return reference


def asset_resolution_issues(ir: ManualIR, *, root: Path, data_root: Path) -> list[str]:
    """Reject semantic rows whose projected artwork cannot be resolved."""
    issues: list[str] = []
    for lang in sorted({page.language for page in ir.pages}):
        lcd = lcd_page_data(ir, lang, root=root, data_root=data_root)
        if lcd is not None:
            for row in lcd.rows:
                figure = str(row.get("figure") or "")
                if figure and not Path(figure).is_file():
                    issues.append(f"{lang}: unresolved LCD asset: {figure}")
        symbols = symbol_page_data(ir, lang, root=root, data_root=data_root)
        if symbols is not None:
            for row in symbols.icons:
                figure = str(row.get("figure") or "")
                if figure and not Path(figure).is_file():
                    issues.append(f"{lang}: unresolved symbol asset: {figure}")
    return issues


def lcd_page_data(
    ir: ManualIR, lang: str, *, root: Path, data_root: Path,
    reference_plan: dict[str, Any] | None = None,
) -> LcdPageData | None:
    page = _matching_page(ir, "lcd_icons_", lang)
    payload = next((payload for payload in _data_payloads(page)
                    if payload.get("kind") == "lcd_icons"), None)
    if payload is None or not payload.get("rows"):
        return None
    rows = []
    for index, source in enumerate(payload["rows"], start=1):
        row = {key: str(source.get(key) or "") for key in ("no", "figure", "name", "desc")}
        source_number = row["no"].strip()
        row["source_no"] = source_number or str(index)
        row["no"] = source_number or str(index)
        row["figure"] = _asset_path(root, data_root, "lcd_icons", row["figure"])
        rows.append(row)

    profile = (
        ((reference_plan or {}).get("idml_contract") or {})
        .get("editable_components", {})
        .get("lcd_icon_table")
    )
    if profile is not None:
        rows = list(apply_lcd_reference_profile(rows, profile))

    for index, row in enumerate(rows, start=1):
        display_number = row["no"].strip()
        try:
            numeric_number = float(display_number)
            row["no"] = (
                _circled(int(numeric_number))
                if numeric_number.is_integer() and numeric_number > 0
                else display_number
            )
        except ValueError:
            row["no"] = display_number or _circled(index)
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
    source_names = {Path(page.source_path).name for page in ir.pages}
    toc = toc_page_data(ir)
    if "00_toc.rst" in source_names and (
        not toc or not toc.get("languages")
        or any(not language.get("entries") for language in toc["languages"])
    ):
        issues.append("TOC page has no complete semantic source payload")
    back = back_cover_data(ir)
    if "99_back_cover.rst" in source_names and (
        not back or any(not back.get(field) for field in ("company", "address", "phone"))
    ):
        issues.append("back cover has no complete semantic source payload")
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
    issues.extend(asset_resolution_issues(ir, root=root, data_root=data_root))
    if issues:
        raise ValueError("; ".join(issues))
    return ir


def build_reference_page_plan(
    ir: ManualIR,
    *,
    root: Path,
    bundle_root: Path,
) -> dict[str, Any] | None:
    approved = load_approved_reference_plan(root=root, ir=ir)
    if approved is not None:
        issues = validate_page_plan(approved)
        if issues:
            raise ValueError(
                "approved reference page plan validation failed: " + "; ".join(issues)
            )
        return approved
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
    approved_contract = plan.get("approved_contract")
    if isinstance(approved_contract, dict):
        write_page_plan(
            approved_contract,
            out_dir / PathSegments.REFERENCE_LAYOUT_PLAN_JSON,
        )
    matchable = plan["source_page_count"] - plan.get("placed_source_pages", 0)
    print(
        f"[export-idml] PAGE PLAN OK ({plan.get('plan_source', 'latex-auto')}): {path} | "
        f"physical={plan['physical_page_count']} matched={plan['matched_source_pages']}/"
        f"{matchable} ({plan['match_rate']:.1%})"
        f" placed={plan.get('placed_source_pages', 0)}"
    )
    return path


def planned_story_pages(plan: dict[str, Any] | None, title: str, fallback: int) -> int:
    return planned_span(plan, title.split(" + "), fallback)


def reference_page_count_issues(
    plan: dict[str, Any] | None,
    emitted_page_count: int,
) -> list[str]:
    """Reject a package whose physical pages drift from its APPROVED plan.

    Exact physical-page parity is only meaningful under an approved reference
    plan, where a human mapped the IDML page-by-page to the frozen PDF. The
    measured LaTeX fallback compares two different composition engines:
    LaTeX packs preface+safety on one page and gives the TOC no standalone
    page, while the IDML writer anchors them discretely — equality there was
    a pre-#692 coincidence, not a contract (2026-07-21 live finding: writer
    63 vs LaTeX 61 with a 100% source match rate). Under the fallback the
    drift is reported as a note by the caller, not an error.
    """
    if plan is None:
        return []
    if plan.get("plan_source") != "approved-reference":
        return []
    expected = int(plan.get("physical_page_count") or 0)
    if emitted_page_count == expected:
        return []
    return [
        f"emitted {emitted_page_count} pages but the reference plan requires "
        f"{expected}"
    ]


def report_reference_page_count_issues(
    plan: dict[str, Any] | None,
    emitted_page_count: int,
) -> bool:
    """Print page-plan drift at the exporter boundary and report failure."""
    issues = reference_page_count_issues(plan, emitted_page_count)
    for issue in issues:
        print(f"[export-idml] PAGE PLAN FAIL: {issue}")
    if not issues and plan is not None and plan.get("plan_source") != "approved-reference":
        expected = int(plan.get("physical_page_count") or 0)
        if expected and emitted_page_count != expected:
            print(
                f"[export-idml] PAGE PLAN NOTE (fallback): emitted {emitted_page_count} pages, "
                f"measured LaTeX has {expected}; parity is enforced only under an approved reference plan"
            )
    return bool(issues)
