"""Derive the JE-2000C JP transcription from the PDF text layer.

Run from the repository root:

    python manual_sources/JE-2000C/JP/ja/git-20261103-88b78332/build_transcription.py

The PDF carries a real text layer. Every native line gets a positional id
(``pNN.LLL``: page, then top-to-bottom/left-to-right order). ``source/line_map.json``
binds each Web line id to its native lines and lists every excluded native line
with a reason; this module fails if any native line is neither bound nor excluded,
or bound twice. Text is the native text with print indents/trailing spaces stripped
and wrapped lines joined; the only ops are the documented ones in ``line_map.json``.
Printed bold/medium runs inside a mixed-weight line are recorded as ``strong``.
It writes ``source/transcription.json``.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

import fitz

PACKAGE = Path(__file__).resolve().parent
PDF = PACKAGE / "JE-2000C-JP.pdf"
SOURCE_SHA256 = "88b78332342866ccd994cfa054a8a63a5fe30fa41131de5c7d53f16cd590690b"
HEAVY = ("NotoSansJP-Bold", "NotoSansJP-Medium")


def native_lines(doc: fitz.Document) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    for number, page in enumerate(doc, start=1):
        found = []
        for block in page.get_text("dict")["blocks"]:
            if block["type"] != 0:
                continue
            for line in block["lines"]:
                spans = [s for s in line["spans"] if s["text"]]
                value = "".join(s["text"] for s in spans)
                if not value.strip():
                    continue
                found.append({"bbox": [round(v, 2) for v in line["bbox"]], "text": value,
                              "spans": [(s["font"].split("+")[-1], s["text"]) for s in spans]})
        found.sort(key=lambda r: (round(r["bbox"][1] / 3), r["bbox"][0]))
        for index, row in enumerate(found, start=1):
            rows[f"p{number:02d}.{index:03d}"] = row
    return rows


def strong_runs(row: dict) -> list[str]:
    heavy = [name in HEAVY for name, _ in row["spans"]]
    if all(heavy) or not any(heavy):
        return []
    runs, current = [], ""
    for (_, value), bold in zip(row["spans"], heavy, strict=True):
        if bold:
            current += value
        elif current:
            runs.append(current.strip())
            current = ""
    if current:
        runs.append(current.strip())
    return [r for r in runs if r]


def apply(value: str, op: str) -> str:
    if op == "despace":
        return re.sub(r"(?<=[^\x00-\x7f]) +(?=[^\x00-\x7f])", "", value)
    if op == "strip_bullet":
        if not value.startswith("・"):
            raise ValueError("no printed bullet to strip: " + value)
        return value[1:]
    kind, _, token = op.partition(":")
    if kind == "marker":
        result, count = re.subn(r" {3,}", token, value, count=1)
        if count != 1:
            raise ValueError("no glyph gap for marker: " + value)
        return result
    if kind == "suffix":
        return value + token
    raise ValueError("unknown op " + op)


def build() -> dict:
    if hashlib.sha256(PDF.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise ValueError("authoritative PDF identity changed")
    mapping = json.loads((PACKAGE / "source/line_map.json").read_text(encoding="utf-8"))
    with fitz.open(PDF) as doc:
        native = native_lines(doc)
    seen: dict[str, str] = {}
    for group in mapping["excluded"]:
        for key in group["native"]:
            if key in seen or key not in native:
                raise ValueError("excluded native line unknown or repeated: " + key)
            seen[key] = "excluded"
    pages: dict[int, list[dict]] = {}
    ids: set[str] = set()
    for entry in mapping["lines"]:
        if entry["id"] in ids:
            raise ValueError("duplicate line id " + entry["id"])
        ids.add(entry["id"])
        parts, strong = [], []
        for key in entry["native"]:
            if key in seen or key not in native:
                raise ValueError("native line unknown or bound twice: " + key)
            seen[key] = entry["id"]
            parts.append(native[key]["text"].strip())
            strong += strong_runs(native[key])
        value = entry.get("sep", "").join(parts)
        for op in entry.get("ops", []):
            value = apply(value, op)
        line = {"id": entry["id"], "text": value,
                "native": [{"id": k, "bbox": native[k]["bbox"]} for k in entry["native"]]}
        if strong:
            line["strong"] = strong
        pages.setdefault(int(entry["native"][0][1:3]), []).append(line)
    missing = sorted(set(native) - set(seen))
    if missing:
        raise ValueError("native lines neither bound nor excluded: " + ", ".join(missing))
    return {
        "schema_version": "je2000c-jp-transcription/v1",
        "source_sha256": SOURCE_SHA256,
        "method": mapping["rules"],
        "native_line_count": len(native),
        "pages": [{"physical_page": n, "web": True, "lines": pages[n]} for n in sorted(pages)],
    }


def main() -> None:
    data = build()
    path = PACKAGE / "source/transcription.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"lines": sum(len(p["lines"]) for p in data["pages"]),
                      "native": data["native_line_count"]}))


if __name__ == "__main__":
    main()
