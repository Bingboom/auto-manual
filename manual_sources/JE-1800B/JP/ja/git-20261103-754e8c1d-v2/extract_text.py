"""Freeze the JE-1800B JP V2 text layer as positioned source lines.

Run from the repository root (PyMuPDF from ``requirements.lock``):

    python manual_sources/JE-1800B/JP/ja/git-20261103-754e8c1d-v2/extract_text.py

The authoritative PDF carries a live text layer. Every PyMuPDF text line is
written to ``source/transcription.json`` with a stable ``p<page>-b<block>-l<line>``
id, its exact text, its rectangle and the spans set in a bold face. Nothing is
corrected, joined or reordered here: ``build_content.py`` binds these ids to
shared components in printed order and accounts for every Web-page line.
Some spans use a font Poppler cannot draw; MuPDF renders them, and the text
layer was checked against 300 dpi MuPDF renders of every Web page.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import fitz

PACKAGE = Path(__file__).resolve().parent
PDF = PACKAGE / "JE-1800B-JP-V2.pdf"
SOURCE_SHA256 = "754e8c1d076b7d5fd9d84ac76ce9447dccec4a9351c7b7d756a3225255b4da52"
# Physical 1 cover, 2 paper TOC and 27 back cover stay in the PDF only.
WEB_PAGES = range(3, 27)


def is_bold(span: dict) -> bool:
    font = span["font"].split("-")[-1]
    return font in {"Bold", "Black", "SemiBold"} or bool(span["flags"] & 16)


def extract() -> dict:
    data = PDF.read_bytes()
    if hashlib.sha256(data).hexdigest() != SOURCE_SHA256:
        raise ValueError("authoritative PDF identity changed")
    pages = []
    with fitz.open(PDF) as doc:
        for number, page in enumerate(doc, start=1):
            lines = []
            for block_index, block in enumerate(page.get_text("dict")["blocks"]):
                if block["type"] != 0:
                    continue
                for line_index, line in enumerate(block["lines"]):
                    spans = [s for s in line["spans"] if s["text"]]
                    value = "".join(s["text"] for s in spans)
                    if not value.strip():
                        continue
                    row = {"id": f"p{number}-b{block_index}-l{line_index}", "text": value,
                           "bbox": [round(v, 1) for v in line["bbox"]],
                           "size": round(spans[0]["size"], 1)}
                    bold = [s["text"] for s in spans if is_bold(s) and s["text"].strip()]
                    if bold and len(bold) == len([s for s in spans if s["text"].strip()]):
                        row["bold"] = True
                    elif bold:
                        row["strong"] = bold
                    lines.append(row)
            pages.append({"physical_page": number, "web": number in WEB_PAGES, "lines": lines})
    return {
        "schema_version": "je1800b-jp-transcription/v1",
        "source_sha256": SOURCE_SHA256,
        "method": ("PyMuPDF 1.28.0 text-layer lines, unmodified. bold marks a line set wholly in a bold "
                   "face; strong lists the bold spans of a mixed line. Whitespace-only lines are omitted."),
        "pages": pages,
    }


def main() -> None:
    result = extract()
    path = PACKAGE / "source/transcription.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"pages": len(result["pages"]),
                      "lines": sum(len(p["lines"]) for p in result["pages"])}))


if __name__ == "__main__":
    main()
