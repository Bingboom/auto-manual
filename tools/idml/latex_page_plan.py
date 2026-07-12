"""Derive a deterministic source-page plan from the LaTeX reference PDF."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import unicodedata
from pathlib import Path
from typing import Any

from tools.manual_ir import ManualIR, ManualPage


SCHEMA_VERSION = "latex-page-plan/v1"


def find_reference_pdf(bundle_root: Path) -> Path | None:
    candidates = sorted((bundle_root.parent / "pdf").glob("*.pdf"))
    return candidates[-1] if candidates else None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).casefold()
    text = text.replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-")
    return re.sub(r"[^\w%+./-]+", " ", text, flags=re.UNICODE).strip()


def extract_pdf_pages(pdf: Path) -> list[str]:
    result = subprocess.run(
        ["pdftotext", "-layout", str(pdf), "-"], check=True,
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    pages = result.stdout.split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    return pages


def _strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        preferred = [value.get(key) for key in ("title", "label", "name", "text", "desc")]
        out = [item for item in preferred if isinstance(item, str)]
        for key, child in value.items():
            if key not in {"title", "label", "name", "text", "desc", "asset", "figure", "img"}:
                out.extend(_strings(child))
        return out
    if isinstance(value, (list, tuple)):
        return [text for child in value for text in _strings(child)]
    return []


def _ranked_anchor_candidates(page: ManualPage) -> list[tuple[int, str]]:
    ranked: list[tuple[int, str]] = []
    for block in page.blocks:
        priority = {"h1": 0, "h2": 1, "body": 2, "list": 3}.get(block.kind, 4)
        for raw in _strings(block.payload):
            text = _normalize(raw)
            minimum = 6 if block.kind in {"h1", "h2"} else 12
            if len(text) >= minimum:
                ranked.append((priority, " ".join(text.split()[:12])))
    unique: dict[str, int] = {}
    for priority, text in sorted(ranked):
        unique.setdefault(text, priority)
    return [(priority, text) for text, priority in unique.items()][:8]


def anchor_candidates(page: ManualPage) -> list[str]:
    return [text for _, text in _ranked_anchor_candidates(page)]


def map_pages(ir: ManualIR, pdf_pages: list[str]) -> list[dict[str, Any]]:
    normalized_pages = [_normalize(page) for page in pdf_pages]
    toc_pages = {index for index, text in enumerate(normalized_pages)
                 if "table of contents" in text}
    cursor = 0
    entries: list[dict[str, Any]] = []
    for source_page in ir.pages:
        ranked_candidates = _ranked_anchor_candidates(source_page)
        candidates = [text for _, text in ranked_candidates]
        matches: list[tuple[int, int, int, str]] = []
        for rank, (priority, anchor) in enumerate(ranked_candidates):
            for index in range(cursor, len(normalized_pages)):
                if "toc" not in source_page.source_path and index in toc_pages:
                    continue
                if anchor in normalized_pages[index]:
                    matches.append((priority, index, rank, anchor))
                    break
        match_page = None
        matched_anchor = None
        if matches:
            _, index, _, matched_anchor = min(matches)
            match_page = index + 1
            cursor = index
        entries.append({
            "page_id": source_page.page_id,
            "source_ref": source_page.source_ref,
            "source_path": source_page.source_path,
            "language": source_page.language,
            "latex_start_page": match_page,
            "matched_anchor": matched_anchor,
            "candidate_count": len(candidates),
        })
    return entries


def build_page_plan(ir: ManualIR, pdf: Path) -> dict[str, Any]:
    pages = extract_pdf_pages(pdf)
    entries = map_pages(ir, pages)
    matched = sum(entry["latex_start_page"] is not None for entry in entries)
    return {
        "schema_version": SCHEMA_VERSION,
        "manual_content_sha256": ir.content_sha256,
        "style_contract_sha256": ir.style_contract_sha256,
        "reference_pdf": pdf.as_posix(),
        "reference_pdf_sha256": _sha256(pdf),
        "physical_page_count": len(pages),
        "source_page_count": len(entries),
        "matched_source_pages": matched,
        "unmatched_source_pages": len(entries) - matched,
        "match_rate": matched / len(entries) if entries else 0.0,
        "virtual_pages": [
            {"kind": "toc", "physical_page": index + 1}
            for index, text in enumerate(pages)
            if "table of contents" in _normalize(text)
        ],
        "pages": entries,
    }


def validate_page_plan(plan: dict[str, Any], *, minimum_match_rate: float = 0.65) -> list[str]:
    issues = []
    if plan.get("schema_version") != SCHEMA_VERSION:
        issues.append(f"schema_version must be {SCHEMA_VERSION}")
    if int(plan.get("physical_page_count") or 0) <= 0:
        issues.append("reference PDF has no pages")
    if float(plan.get("match_rate") or 0.0) < minimum_match_rate:
        issues.append(
            f"source-page match rate {float(plan.get('match_rate') or 0.0):.1%} "
            f"is below {minimum_match_rate:.0%}")
    starts = [entry["latex_start_page"] for entry in plan.get("pages", [])
              if entry.get("latex_start_page") is not None]
    if starts != sorted(starts):
        issues.append("source-page anchors are not monotonic")
    return issues


def planned_span(plan: dict[str, Any] | None, stems: list[str], fallback: int) -> int:
    """Return the LaTeX physical span for a consecutive source-story group."""
    if not plan or not stems:
        return fallback
    entries = plan.get("pages", [])
    by_stem = {Path(entry["source_path"]).stem: index for index, entry in enumerate(entries)}
    indices = [by_stem[stem] for stem in stems if stem in by_stem]
    if not indices:
        return fallback
    first_index, last_index = min(indices), max(indices)
    first_start = entries[first_index].get("latex_start_page")
    if first_start is None:
        return fallback
    for entry in entries[last_index + 1:]:
        next_start = entry.get("latex_start_page")
        if next_start is not None and next_start > first_start:
            return max(1, int(next_start) - int(first_start))
    return fallback


def write_page_plan(plan: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
