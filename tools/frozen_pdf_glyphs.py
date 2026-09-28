"""Recover missing PDF glyphs from the hash-verified, same-position AI original.

The fresh PDF remains the text authority. AI may supply only a glyph where the
PDF extraction has U+FFFD or U+001F; every other character must agree.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import re
from typing import Any, Mapping

import fitz

from tools.manual_ir.hashing import file_sha256


_PDF_MISSING = ("\ufffd", "\x1f")
_AI_GLYPH = "⎓"


def _normalize(value: str) -> str:
    return " ".join(value.split())


def _glyph_equivalent(value: str) -> str:
    """Compare line-wrapped blocks while retaining each missing-glyph position."""
    normalized = _normalize(value.replace("\x1f", _AI_GLYPH).replace("\ufffd", _AI_GLYPH))
    return re.sub(r"\s*⎓\s*", _AI_GLYPH, normalized)


def _ai_lines_at(page: fitz.Page, bbox: list[float]) -> str:
    """Use majority-overlapping source lines, not neighboring textbox spans."""
    rectangle = fitz.Rect(bbox)
    blocks = page.get_text(
        "dict", flags=fitz.TEXTFLAGS_DICT & ~fitz.TEXT_PRESERVE_IMAGES,
    )["blocks"]
    lines = [line for block in blocks for line in block.get("lines", [])]
    selected = [
        line for line in lines
        if (rectangle & fitz.Rect(line["bbox"])).get_area()
        > fitz.Rect(line["bbox"]).get_area() * .5
    ]
    selected.sort(key=lambda line: (line["bbox"][1], line["bbox"][0]))
    return "\n".join(
        "".join(span["text"] for span in line["spans"]) for line in selected
    )


def _checked_replacement(before: str, candidate: str, *, field: str, block: bool) -> str:
    missing = sum(before.count(character) for character in _PDF_MISSING)
    if not missing or candidate.count(_AI_GLYPH) != missing or any(
        character in candidate for character in _PDF_MISSING
    ):
        raise ValueError(f"{field}: AI glyph count disagrees with PDF")
    if block:
        agrees = _glyph_equivalent(candidate) == _glyph_equivalent(before)
        after = candidate + ("\n" if before.endswith("\n") else "")
    else:
        after = _normalize(candidate)
        agrees = after.replace(_AI_GLYPH, "\ufffd") == before
    if not agrees:
        raise ValueError(f"{field}: AI differs from PDF beyond missing glyphs")
    return after


def recover_pdf_glyphs(book_data: Mapping[str, Any], ai_path: Path) -> dict[str, Any]:
    """Return a copy with precisely supported PDF glyph gaps restored.

    Specification fields use their recorded rectangles. Page text blocks use
    majority-overlapping AI lines at the PDF block rectangle. No historical
    JSON, OCR, or unpositioned replacement participates in recovery.
    """
    book = deepcopy(dict(book_data))
    provenance = book["provenance"]
    ai_identity = provenance["ai"]
    ai_path = Path(ai_path).resolve()
    ai_sha256 = file_sha256(ai_path)
    if ai_sha256 != ai_identity["sha256"]:
        raise ValueError("AI SHA-256 disagrees with PDF provenance")
    if ai_path.name != ai_identity["filename"]:
        raise ValueError("AI filename disagrees with PDF provenance")

    corrections: list[dict[str, Any]] = []
    originals: list[dict[str, Any]] = []
    seen_fields: set[str] = set()
    with fitz.open(ai_path) as document:
        if len(document) != ai_identity["physical_page_count"]:
            raise ValueError("AI page count disagrees with PDF provenance")
        for unresolved in provenance["unresolved_text"]:
            field = unresolved["field"]
            parts = field.split("/")
            if len(parts) != 4 or parts[0] != "specifications" or field in seen_fields:
                raise ValueError(f"unsupported or duplicate unresolved PDF field: {field}")
            seen_fields.add(field)
            _, group, index, key = parts
            try:
                record = book["source"]["tables"]["specifications"]["groups"][group][int(index)]
                before = record[key]
            except (KeyError, IndexError, TypeError, ValueError) as exc:
                raise ValueError(f"{field}: unresolved field has no PDF value") from exc
            if not isinstance(before, str) or before.count("\ufffd") != unresolved["replacement_character_count"]:
                raise ValueError(f"{field}: unresolved count disagrees with PDF field")
            page_number = unresolved["physical_page"]
            if page_number != book["source"]["tables"]["specifications"]["physical_page"]:
                raise ValueError(f"{field}: PDF field page changed")
            bbox = unresolved["bbox"]
            candidate = document[page_number - 1].get_textbox(fitz.Rect(bbox))
            after = _checked_replacement(before, candidate, field=field, block=False)
            record[key] = after
            detail = {"field": field, "physical_page": page_number, "bbox": list(bbox),
                      "before": before, "after": after, "reason": "PDF U+FFFD glyph recovered from same-bbox AI text",
                      "ai_sha256": ai_sha256}
            corrections.append(detail)
            originals.append({key: detail[key] for key in ("field", "physical_page", "bbox", "before")})

        for page in book["source"]["pages"]:
            page_number = page["physical_page"]
            for index, block in enumerate(page["blocks_visual_order"]):
                before = block["text"]
                if not any(character in before for character in _PDF_MISSING):
                    continue
                field = f"pages/{page_number}/blocks_visual_order/{index}/text"
                bbox = block["bbox"]
                candidate = _ai_lines_at(document[page_number - 1], bbox)
                after = _checked_replacement(before, candidate, field=field, block=True)
                block["text"] = after
                detail = {"field": field, "physical_page": page_number, "bbox": list(bbox),
                          "before": before, "after": after, "reason": "PDF missing glyph recovered from same-bbox AI lines",
                          "ai_sha256": ai_sha256}
                corrections.append(detail)
                originals.append({key: detail[key] for key in ("field", "physical_page", "bbox", "before")})

    provenance["original_pdf_text"] = originals
    provenance["corrections_applied"].extend(corrections)
    provenance["glyph_recovery"] = {"ai_sha256": ai_sha256,
                                    "field_count": len(corrections)}
    return book


__all__ = ["recover_pdf_glyphs"]
