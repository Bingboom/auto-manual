#!/usr/bin/env python3
"""Extract Word tracked changes (insertions/deletions) from a reviewer-revised manual .docx.

A reviewer typically opens a *built* manual in Word, turns on Track Changes, and edits.
This script reads ``word/document.xml`` in document order, reconstructs each paragraph's
OLD text (kept + deleted) and NEW text (kept + inserted), and emits every changed
paragraph with a running heading breadcrumb so each change can be mapped back to a
manual section. It does NOT decide what to do with the changes — it just surfaces them
so a human + Claude can categorize and route them (see ../references/source-map.md).

Usage:
    python3 extract_docx_changes.py REVISED.docx [MORE.docx ...] [--out DIR] [--limit N]

For each input it prints a summary and, when --out is given, writes a per-file report
``changes_<stem>.txt`` (document outline + every OLD→NEW paragraph).
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def _para_style(p):
    ppr = p.find(f"{W}pPr")
    if ppr is None:
        return ""
    pstyle = ppr.find(f"{W}pStyle")
    return pstyle.get(f"{W}val") if pstyle is not None else ""


def _walk(elem, mode, old, new):
    """Recursively collect text into old/new lists according to ins/del mode."""
    tag = elem.tag
    if tag == f"{W}ins":
        mode = "ins"
    elif tag == f"{W}del":
        mode = "del"
    for child in elem:
        ctag = child.tag
        if ctag == f"{W}t":
            txt = child.text or ""
            if mode in ("keep", "ins"):
                new.append(txt)
            if mode == "keep":
                old.append(txt)
        elif ctag == f"{W}delText":
            if mode == "del":
                old.append(child.text or "")
        elif ctag in (f"{W}tab",):
            if mode in ("keep", "ins"):
                new.append("\t")
            if mode in ("keep", "del"):
                old.append("\t")
        elif ctag in (f"{W}br", f"{W}cr"):
            if mode in ("keep", "ins"):
                new.append(" ")
            if mode in ("keep", "del"):
                old.append(" ")
        else:
            _walk(child, mode, old, new)


def _para(p):
    old, new = [], []
    _walk(p, "keep", old, new)
    changed = (p.find(f".//{W}ins") is not None) or (p.find(f".//{W}del") is not None)
    return "".join(old).strip(), "".join(new).strip(), changed


def _norm(s, limit=400):
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= limit else s[:limit] + " …"


def process(path, limit):
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("word/document.xml"))
    body = root.find(f"{W}body")
    heading, outline, changes = "", [], []
    for p in body.iter(f"{W}p"):
        style = _para_style(p)
        old_t, new_t, changed = _para(p)
        is_heading = bool(re.search(r"(?i)heading|title|toc", style)) or style.lower().startswith("heading") or re.fullmatch(r"\d+", style or "")
        if is_heading and new_t:
            heading = new_t
            outline.append(f"[{style}] {_norm(new_t, 120)}")
        if changed and old_t != new_t:
            changes.append((heading, style, _norm(old_t, limit), _norm(new_t, limit)))
    return outline, changes


def render(stem, outline, changes):
    out = [f"===== {stem}: {len(changes)} changed paragraphs, {len(outline)} headings =====", "", "---- OUTLINE ----"]
    out += outline
    out += ["", "---- CHANGES (old -> new) ----", ""]
    for i, (h, style, old_t, new_t) in enumerate(changes, 1):
        out += [f"#{i}  «{_norm(h, 80)}»  [{style}]", f"  OLD: {old_t}", f"  NEW: {new_t}", ""]
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Extract Word tracked changes from revised manual .docx files.")
    ap.add_argument("docx", nargs="+", help="One or more revised .docx files (with tracked changes)")
    ap.add_argument("--out", default=None, help="Directory to write per-file changes_<stem>.txt reports")
    ap.add_argument("--limit", type=int, default=400, help="Truncate OLD/NEW text to this many chars")
    args = ap.parse_args(argv)
    if args.out:
        os.makedirs(args.out, exist_ok=True)
    for path in args.docx:
        stem = os.path.splitext(os.path.basename(path))[0]
        try:
            outline, changes = process(path, args.limit)
        except Exception as exc:  # noqa: BLE001
            print(f"[{stem}] ERROR: {exc}", file=sys.stderr)
            continue
        report = render(stem, outline, changes)
        if args.out:
            with open(os.path.join(args.out, f"changes_{stem}.txt"), "w", encoding="utf-8") as fh:
                fh.write(report)
            print(f"[{stem}] {len(changes)} changed paragraphs -> {args.out}/changes_{stem}.txt")
        else:
            print(report)


if __name__ == "__main__":
    main()
