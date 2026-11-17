"""Deterministic structural block alignment and text extraction for manual-ir/v2."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from bs4 import BeautifulSoup

from tools import lang_registry
from tools.corpus.discover import IRPair

_DOC_EXT_RE = re.compile(r"\.(?:rst|md|html)$", re.IGNORECASE)
_URL_RE = re.compile(r"^(?:https?://|www\.)\S+$", re.IGNORECASE)
_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_MODEL_CODE_RE = re.compile(
    r"^(?:[A-Z]{1,5}-\d{2,5}[A-Z0-9-]*|(?:PTB|JSG)\d+[A-Z0-9-]*|[FE]\d+(?:-[FE]\d+)?|F0-FF)$"
)
_SPEC_UNIT_TOKEN_RE = re.compile(
    r"^(?:mm|cm|m|in|ft|kg|g|lb|lbs|wh|kwh|ah|mah|w|kw|v|mv|a|ma|hz|khz|mhz|ghz|db|rh|s|ms|min|h|hr|hrs|max|ac|dc|c|f|k|ip\d+)$",
    re.IGNORECASE,
)
_SPEC_STRIP_RE = re.compile(r"[\d\s.,:+*/×xX~\-±≤≥≈<>＜＞=°%()\[\]/]+")
_ADMONITION_CLASSES = frozenset({"admonition", "callout", "note", "warning", "caution", "tip", "important"})
_SKIP_LEAF_KINDS = frozenset({"comment", "image", "column", "line_break", "thematic_break"})
_CONTAINER_BLOCK_KINDS = frozenset({"heading", "paragraph", "list", "table", "component", "group", "section", "figure"})


@dataclass(frozen=True)
class ExtractedSegment:
    """A single plain-text segment with optional Translation_Memory content_attribute."""

    text: str
    content_attribute: str | None


@dataclass(frozen=True)
class ExtractedBlock:
    """Structural signature unit and its ordered text segments."""

    sig_token: str
    segments: tuple[ExtractedSegment, ...]


@dataclass(frozen=True)
class AlignedSegmentPair:
    """An aligned anchor-to-target text pair extracted from matching pages."""

    en_text: str
    target_text: str
    target_lang: str
    content_attribute: str | None
    page_stem: str
    model: str
    region: str
    anchor_ir_path: str
    target_ir_path: str
    anchor_ir_sha256: str
    target_ir_sha256: str


@dataclass(frozen=True)
class AbstainedPage:
    """Record explaining why a page pair was not aligned."""

    model: str
    region: str
    anchor_lang: str
    target_lang: str
    page_stem: str
    anchor_page_id: str | None
    target_page_id: str | None
    reason: str
    anchor_signature: tuple[str, ...]
    target_signature: tuple[str, ...]
    anchor_ir_path: str
    target_ir_path: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "region": self.region,
            "anchor_lang": self.anchor_lang,
            "target_lang": self.target_lang,
            "page_stem": self.page_stem,
            "anchor_page_id": self.anchor_page_id,
            "target_page_id": self.target_page_id,
            "reason": self.reason,
            "anchor_signature": list(self.anchor_signature),
            "target_signature": list(self.target_signature),
            "anchor_ir_path": self.anchor_ir_path,
            "target_ir_path": self.target_ir_path,
        }


def normalize_space(value: str) -> str:
    """Collapse internal whitespace and line breaks into single spaces."""

    return " ".join((value or "").replace("\r\n", "\n").replace("\r", "\n").split())


def _html_to_text(raw_html: str) -> str:
    return normalize_space(BeautifulSoup(raw_html, "html.parser").get_text(" ", strip=True))


def _known_lang_suffixes() -> tuple[str, ...]:
    tokens: set[str] = set()
    for alias in lang_registry.LANGUAGE_BY_ALIAS:
        folded = alias.casefold()
        tokens.add(folded)
        tokens.add(folded.replace("-", "_"))
    return tuple(sorted(tokens, key=len, reverse=True))


def normalize_page_stem(page_id: str) -> str:
    """Strip doc extension and trailing language code suffix from page_id."""

    stem = _DOC_EXT_RE.sub("", (page_id or "").strip())
    lower = stem.casefold()
    for suffix in _known_lang_suffixes():
        for sep in ("_", "-"):
            marker = f"{sep}{suffix}"
            if lower.endswith(marker) and len(stem) > len(marker):
                return stem[: len(stem) - len(marker)]
    return stem


def is_noise_segment(text: str) -> bool:
    """Return True when text is non-translatable spec/code/URL/marker noise."""

    norm = normalize_space(text)
    if len(norm) <= 1:
        return True
    if not any(ch.isalpha() for ch in norm):
        return True
    if _URL_RE.match(norm) or _EMAIL_RE.match(norm):
        return True
    if _MODEL_CODE_RE.match(norm):
        return True
    remainder = _SPEC_STRIP_RE.sub(" ", norm).strip()
    if not remainder:
        return True
    words = [tok for tok in remainder.split() if tok]
    if words and all(_SPEC_UNIT_TOKEN_RE.match(tok) for tok in words):
        return True
    return False


def _html_classes(node: dict[str, Any]) -> set[str]:
    attrs = ((node.get("presentation") or {}).get("html") or {}).get("attributes") or {}
    raw = attrs.get("class")
    if isinstance(raw, str):
        return {tok.strip().casefold() for tok in raw.split() if tok.strip()}
    if isinstance(raw, list):
        tokens: set[str] = set()
        for item in raw:
            for tok in str(item).split():
                if tok.strip():
                    tokens.add(tok.strip().casefold())
        return tokens
    return set()


def _extract_inline_parts(node: Any, parts: list[str]) -> None:
    if not isinstance(node, dict) or node.get("hidden") is True:
        return
    kind = node.get("kind")
    if kind == "text":
        parts.append(str(node.get("text") or ""))
        return
    if kind == "line_break":
        parts.append(" ")
        return
    if kind in _SKIP_LEAF_KINDS:
        return
    for child in node.get("children") or ():
        _extract_inline_parts(child, parts)


def _extract_inline_text(node: dict[str, Any]) -> str:
    parts: list[str] = []
    _extract_inline_parts(node, parts)
    return normalize_space("".join(parts))


def _extract_list_item_parts(node: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    text_parts: list[str] = []
    nested_lists: list[dict[str, Any]] = []
    for child in node.get("children") or ():
        if not isinstance(child, dict) or child.get("hidden") is True:
            continue
        if child.get("kind") == "list":
            nested_lists.append(child)
        else:
            txt = _extract_inline_text(child)
            if txt:
                text_parts.append(txt)
    return normalize_space(" ".join(text_parts)), nested_lists


def _extract_list_blocks(node: dict[str, Any]) -> list[ExtractedBlock]:
    items = [
        child
        for child in (node.get("children") or ())
        if isinstance(child, dict) and child.get("kind") == "list_item" and child.get("hidden") is not True
    ]
    if not items:
        return []
    segments: list[ExtractedSegment] = []
    nested: list[dict[str, Any]] = []
    for item in items:
        item_text, child_lists = _extract_list_item_parts(item)
        if item_text:
            segments.append(ExtractedSegment(text=item_text, content_attribute=None))
        nested.extend(child_lists)
    blocks: list[ExtractedBlock] = []
    if segments:
        blocks.append(ExtractedBlock(sig_token=f"list:{len(items)}", segments=tuple(segments)))
    for sub in nested:
        blocks.extend(_extract_list_blocks(sub))
    return blocks


def _iter_table_rows(table_node: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    head_rows: list[dict[str, Any]] = []
    body_rows: list[dict[str, Any]] = []
    for section in table_node.get("children") or ():
        if not isinstance(section, dict) or section.get("hidden") is True:
            continue
        sec_kind = section.get("kind")
        if sec_kind == "table_row":
            body_rows.append(section)
        elif sec_kind in ("table_head", "table_body", "table_foot"):
            for row in section.get("children") or ():
                if isinstance(row, dict) and row.get("kind") == "table_row" and row.get("hidden") is not True:
                    if sec_kind == "table_head":
                        head_rows.append(row)
                    else:
                        body_rows.append(row)
    return head_rows, body_rows


def _row_cells(row: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        cell
        for cell in (row.get("children") or ())
        if isinstance(cell, dict) and cell.get("kind") == "table_cell" and cell.get("hidden") is not True
    ]


def _extract_callout_table(body_rows: list[dict[str, Any]]) -> list[ExtractedBlock]:
    label_segs: list[ExtractedSegment] = []
    body_segs: list[ExtractedSegment] = []
    for row in body_rows:
        for cell in _row_cells(row):
            classes = _html_classes(cell)
            if "manual-callout-label" in classes:
                txt = _extract_inline_text(cell)
                if txt:
                    label_segs.append(ExtractedSegment(text=txt, content_attribute="panel_title"))
            elif "manual-callout-body" in classes:
                for blk in _extract_flow_node(cell):
                    body_segs.extend(blk.segments)
    all_segs = tuple((*label_segs, *body_segs))
    if not all_segs:
        return []
    return [ExtractedBlock(sig_token=f"callout:{len(label_segs)}:{len(body_segs)}", segments=all_segs)]


def _extract_table_blocks(node: dict[str, Any]) -> list[ExtractedBlock]:
    head_rows, body_rows = _iter_table_rows(node)
    all_cells = [_html_classes(cell) for row in (*head_rows, *body_rows) for cell in _row_cells(row)]
    if any("manual-callout-label" in cls or "manual-callout-body" in cls for cls in all_cells):
        return _extract_callout_table(body_rows)

    header_rows = list(head_rows)
    remaining_body: list[dict[str, Any]] = []
    for row in body_rows:
        cells = _row_cells(row)
        if cells and all(cell.get("header") is True for cell in cells):
            header_rows.append(row)
        else:
            remaining_body.append(row)

    header_segs: list[ExtractedSegment] = []
    for row in header_rows:
        for cell in _row_cells(row):
            txt = _extract_inline_text(cell)
            if txt:
                header_segs.append(ExtractedSegment(text=txt, content_attribute="table_header"))
    return [
        ExtractedBlock(
            sig_token=f"table:h{len(header_segs)}:b{len(remaining_body)}",
            segments=tuple(header_segs),
        )
    ]


def _slot_text(value: Any) -> str:
    if isinstance(value, str):
        return _html_to_text(value) if "<" in value and ">" in value else normalize_space(value)
    if isinstance(value, dict):
        if "content_text" in value:
            return normalize_space(str(value.get("content_text") or ""))
        if "text" in value:
            return normalize_space(str(value.get("text") or ""))
        if "html" in value:
            return _html_to_text(str(value.get("html") or ""))
    return ""


def _append_slot_items(
    items: Any,
    *,
    content_attribute: str | None,
    segments: list[ExtractedSegment],
) -> None:
    if not isinstance(items, list):
        return
    for item in items:
        txt = _slot_text(item)
        if txt:
            segments.append(ExtractedSegment(text=txt, content_attribute=content_attribute))


def _extract_slot_segments(slot: dict[str, Any], segments: list[ExtractedSegment]) -> None:
    role = str(slot.get("role") or "").strip()
    content = slot.get("content")
    if role == "headers":
        _append_slot_items(content, content_attribute="table_header", segments=segments)
    elif role in ("label", "tip_label"):
        txt = _slot_text(content)
        if txt:
            segments.append(ExtractedSegment(text=txt, content_attribute="panel_title"))
    elif role in ("body", "tip_body", "lead", "local_note"):
        txt = _slot_text(content)
        if txt:
            segments.append(ExtractedSegment(text=txt, content_attribute=None))
    elif role in ("items", "columns"):
        _append_slot_items(content, content_attribute=None, segments=segments)
    elif role == "blocks" and isinstance(content, list):
        _extract_warranty_slot_blocks(content, segments)
    elif role == "periods" and isinstance(content, list):
        for period in content:
            if isinstance(period, dict):
                txt = _slot_text(period.get("body_text") or period.get("body_html") or "")
                if txt:
                    segments.append(ExtractedSegment(text=txt, content_attribute=None))


def _extract_component_spec_blocks(component_id: str, spec: dict[str, Any]) -> list[ExtractedBlock]:
    slots = spec.get("slots")
    if not isinstance(slots, list):
        return []
    segments: list[ExtractedSegment] = []
    for slot in slots:
        if isinstance(slot, dict):
            _extract_slot_segments(slot, segments)
    if not segments:
        return []
    return [ExtractedBlock(sig_token=f"comp:{component_id}:spec:{len(segments)}", segments=tuple(segments))]


def _extract_warranty_slot_blocks(content: list[Any], segments: list[ExtractedSegment]) -> None:
    for item in content:
        if not isinstance(item, dict):
            continue
        if item.get("kind") == "list" and isinstance(item.get("items"), list):
            for li in item["items"]:
                txt = _slot_text(li)
                if txt:
                    segments.append(ExtractedSegment(text=txt, content_attribute=None))
        else:
            txt = _slot_text(item)
            if txt:
                segments.append(ExtractedSegment(text=txt, content_attribute=None))


def _extract_component_blocks(node: dict[str, Any]) -> list[ExtractedBlock]:
    spec = node.get("component_spec") or {}
    cid = str(spec.get("component_id") or "unknown")
    carrier_flow = node.get("carrier_flow")
    if isinstance(carrier_flow, list) and carrier_flow:
        inner: list[ExtractedBlock] = []
        for child in carrier_flow:
            inner.extend(_extract_flow_node(child))
        return [
            ExtractedBlock(sig_token=f"comp:{cid}:{blk.sig_token}", segments=blk.segments)
            for blk in inner
        ]
    return _extract_component_spec_blocks(cid, spec)


def _extract_admonition_group(node: dict[str, Any]) -> list[ExtractedBlock]:
    titles: list[ExtractedSegment] = []
    bodies: list[ExtractedSegment] = []
    for child in node.get("children") or ():
        if not isinstance(child, dict) or child.get("hidden") is True:
            continue
        classes = _html_classes(child)
        if "admonition-title" in classes or child.get("kind") == "heading":
            txt = _extract_inline_text(child)
            if txt:
                titles.append(ExtractedSegment(text=txt, content_attribute="panel_title"))
        else:
            for blk in _extract_flow_node(child):
                bodies.extend(blk.segments)
    all_segs = tuple((*titles, *bodies))
    if not all_segs:
        return []
    return [ExtractedBlock(sig_token=f"admonition:{len(titles)}:{len(bodies)}", segments=all_segs)]


def _extract_group_or_section(node: dict[str, Any]) -> list[ExtractedBlock]:
    classes = _html_classes(node)
    if node.get("kind") == "group" and (classes & _ADMONITION_CLASSES):
        return _extract_admonition_group(node)
    if node.get("kind") == "group" and "line" in classes:
        has_block_child = any(
            isinstance(ch, dict) and ch.get("kind") in _CONTAINER_BLOCK_KINDS
            for ch in (node.get("children") or ())
        )
        if not has_block_child:
            txt = _extract_inline_text(node)
            return [ExtractedBlock(sig_token="line", segments=(ExtractedSegment(text=txt, content_attribute=None),))] if txt else []
    blocks: list[ExtractedBlock] = []
    for child in node.get("children") or ():
        blocks.extend(_extract_flow_node(child))
    return blocks


def _extract_flow_node(node: Any) -> list[ExtractedBlock]:
    if isinstance(node, list):
        blocks: list[ExtractedBlock] = []
        for item in node:
            blocks.extend(_extract_flow_node(item))
        return blocks
    if not isinstance(node, dict) or node.get("hidden") is True:
        return []
    kind = node.get("kind")
    if kind in _SKIP_LEAF_KINDS or kind == "text":
        return []
    if kind == "heading":
        txt = _extract_inline_text(node)
        if not txt:
            return []
        return [
            ExtractedBlock(
                sig_token=f"heading:{node.get('level')}",
                segments=(ExtractedSegment(text=txt, content_attribute="section_title"),),
            )
        ]
    if kind == "paragraph":
        txt = _extract_inline_text(node)
        return [ExtractedBlock(sig_token="paragraph", segments=(ExtractedSegment(text=txt, content_attribute=None),))] if txt else []
    if kind == "list":
        return _extract_list_blocks(node)
    if kind == "table":
        return _extract_table_blocks(node)
    if kind == "component":
        return _extract_component_blocks(node)
    if kind in ("group", "section", "figure", "quote", "caption"):
        return _extract_group_or_section(node)
    return []


def extract_page_blocks(page: dict[str, Any]) -> tuple[ExtractedBlock, ...]:
    """Extract ordered structural blocks and text segments from a manual-ir/v2 page."""

    extracted: list[ExtractedBlock] = []
    for block in page.get("blocks") or ():
        if not isinstance(block, dict):
            continue
        extracted.extend(_extract_flow_node(block.get("payload")))
    return tuple(extracted)


def _index_pages_by_stem(pages: tuple[dict[str, Any], ...]) -> tuple[dict[str, dict[str, Any]], set[str]]:
    by_stem: dict[str, dict[str, Any]] = {}
    duplicates: set[str] = set()
    for page in pages:
        stem = normalize_page_stem(str(page.get("page_id") or ""))
        if not stem:
            continue
        if stem in by_stem:
            duplicates.add(stem)
        else:
            by_stem[stem] = page
    return by_stem, duplicates


def _blocks_align_exactly(
    anchor_blocks: tuple[ExtractedBlock, ...],
    target_blocks: tuple[ExtractedBlock, ...],
) -> tuple[bool, str]:
    anchor_sig = tuple(blk.sig_token for blk in anchor_blocks)
    target_sig = tuple(blk.sig_token for blk in target_blocks)
    if anchor_sig != target_sig:
        return False, "structural_signature_mismatch"
    for anchor_blk, target_blk in zip(anchor_blocks, target_blocks, strict=True):
        if len(anchor_blk.segments) != len(target_blk.segments):
            return False, "block_segment_count_mismatch"
        for anchor_seg, target_seg in zip(anchor_blk.segments, target_blk.segments, strict=True):
            if anchor_seg.content_attribute != target_seg.content_attribute:
                return False, "segment_attribute_mismatch"
    return True, ""


def align_ir_pair(pair: IRPair) -> tuple[list[AlignedSegmentPair], list[AbstainedPage], int]:
    """Align pages between anchor and target IRs using exact-structure-or-abstain."""

    anchor_pages, anchor_dups = _index_pages_by_stem(pair.anchor.pages)
    target_pages, target_dups = _index_pages_by_stem(pair.target.pages)

    aligned_pairs: list[AlignedSegmentPair] = []
    abstained: list[AbstainedPage] = []
    aligned_page_count = 0

    for stem, target_page in target_pages.items():
        target_pid = str(target_page.get("page_id") or "")
        if stem in anchor_dups or stem in target_dups:
            anchor_pid = str(anchor_pages[stem].get("page_id") or "") if stem in anchor_pages else None
            abstained.append(
                AbstainedPage(
                    model=pair.model,
                    region=pair.region,
                    anchor_lang=pair.anchor.language,
                    target_lang=pair.target.language,
                    page_stem=stem,
                    anchor_page_id=anchor_pid,
                    target_page_id=target_pid,
                    reason="duplicate_normalized_page_stem",
                    anchor_signature=(),
                    target_signature=(),
                    anchor_ir_path=pair.anchor.rel_path,
                    target_ir_path=pair.target.rel_path,
                )
            )
            continue

        anchor_page = anchor_pages.get(stem)
        if anchor_page is None:
            abstained.append(
                AbstainedPage(
                    model=pair.model,
                    region=pair.region,
                    anchor_lang=pair.anchor.language,
                    target_lang=pair.target.language,
                    page_stem=stem,
                    anchor_page_id=None,
                    target_page_id=target_pid,
                    reason="missing_anchor_page",
                    anchor_signature=(),
                    target_signature=(),
                    anchor_ir_path=pair.anchor.rel_path,
                    target_ir_path=pair.target.rel_path,
                )
            )
            continue

        anchor_pid = str(anchor_page.get("page_id") or "")
        anchor_blocks = extract_page_blocks(anchor_page)
        target_blocks = extract_page_blocks(target_page)
        ok, reason = _blocks_align_exactly(anchor_blocks, target_blocks)
        if not ok:
            abstained.append(
                AbstainedPage(
                    model=pair.model,
                    region=pair.region,
                    anchor_lang=pair.anchor.language,
                    target_lang=pair.target.language,
                    page_stem=stem,
                    anchor_page_id=anchor_pid,
                    target_page_id=target_pid,
                    reason=reason,
                    anchor_signature=tuple(b.sig_token for b in anchor_blocks),
                    target_signature=tuple(b.sig_token for b in target_blocks),
                    anchor_ir_path=pair.anchor.rel_path,
                    target_ir_path=pair.target.rel_path,
                )
            )
            continue

        if not anchor_blocks:
            continue
        aligned_page_count += 1
        for anchor_blk, target_blk in zip(anchor_blocks, target_blocks, strict=True):
            for anchor_seg, target_seg in zip(anchor_blk.segments, target_blk.segments, strict=True):
                if is_noise_segment(anchor_seg.text) or not normalize_space(target_seg.text):
                    continue
                aligned_pairs.append(
                    AlignedSegmentPair(
                        en_text=anchor_seg.text,
                        target_text=target_seg.text,
                        target_lang=pair.target.language,
                        content_attribute=anchor_seg.content_attribute,
                        page_stem=stem,
                        model=pair.model,
                        region=pair.region,
                        anchor_ir_path=pair.anchor.rel_path,
                        target_ir_path=pair.target.rel_path,
                        anchor_ir_sha256=pair.anchor.file_sha256,
                        target_ir_sha256=pair.target.file_sha256,
                    )
                )

    return aligned_pairs, abstained, aligned_page_count
