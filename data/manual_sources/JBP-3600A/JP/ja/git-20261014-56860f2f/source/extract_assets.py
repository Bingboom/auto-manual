"""Acquire this package's artwork from the recorded decisions in source/figures.json.

Run from the repository root after any change to figures.json. Every record is
one of four reviewed acquisitions, and the result must equal the recorded
SHA-256 (``--check`` only verifies):

* ``reuse``: a byte copy of an existing repository file (shared symbol or the
  published JBP-3600A EU artwork) whose print matches;
* ``crop``: a complete print panel rendered from the archived sheet at 4x;
* ``textless-crop``: the same panel with its printed label lines removed (the shared
  pipeline's ``redact_text`` operator: text removed, line art and images kept),
  the labels become live copy on the figure;
* ``vector``: a small native glyph, its PDF paths written as a transparent SVG;
* ``embedded-image``: the sheet's embedded raster image as PNG, its pixels unresampled
  (CMYK converted to RGB).

Coordinates are panel-local PDF points (see native.PANEL_ORIGINS).
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

import fitz

SOURCE = Path(__file__).resolve().parents[1]
REPO = next(p for p in SOURCE.parents if (p / "build.py").is_file())
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from native import PANEL_ORIGINS, archived_pdf, label_spans  # noqa: E402

SCALE = 4.0  # 288 dpi: twice the 390 px phone column and the 1280 px desktop column.


def panel_rect(panel, box):
    x, y = PANEL_ORIGINS[panel - 1]
    return fitz.Rect(box[0] + x, box[1] + y, box[2] + x, box[3] + y)


def colour(value):
    return "#" + "".join(f"{round(c * 255):02x}" for c in value)


def vector_svg(page, panel, box, indices, clipped=()):
    """The listed filled PDF paths inside box, nothing else, on a transparent canvas.

    ``clipped`` names rectangle fills the PDF paints only through the preceding
    glyph path (used as its clip); the glyph path already carries that shape.
    """
    rect = panel_rect(panel, box)
    drawings = page.get_drawings()
    inside = [i for i, d in enumerate(drawings) if rect.contains(d["rect"])]
    if inside != sorted([*indices, *clipped]):
        raise ValueError(f"vector selection must be every drawing inside {box}: {inside}")
    paths = []
    for index in indices:
        d = drawings[index]
        if d["type"] not in {"f", "fs"}:
            raise ValueError("vector glyphs here are filled paths")
        parts = []
        for item in d["items"]:
            op, *points = item
            if op == "re":
                r = points[0]
                parts.append(f"M{r.x0 - rect.x0:.3f} {r.y0 - rect.y0:.3f}H{r.x1 - rect.x0:.3f}"
                             f"V{r.y1 - rect.y0:.3f}H{r.x0 - rect.x0:.3f}Z")
                continue
            if op == "qu":
                q = points[0]
                points = [q.ul, q.ur, q.lr, q.ll]
                op = "l"
            coords = [f"{p.x - rect.x0:.3f} {p.y - rect.y0:.3f}" for p in points]
            if not parts or not parts[-1].endswith(coords[0]):
                parts.append("M" + coords[0])
            parts.append(("L" if op == "l" else "C") + " ".join(coords[1:]))
        rule = "evenodd" if d.get("even_odd") else "nonzero"
        opacity = d.get("fill_opacity")
        extra = f' fill-opacity="{opacity:.3f}"' if opacity not in (None, 1, 1.0) else ""
        if d["type"] == "fs":
            extra += f' stroke="{colour(d["color"])}" stroke-width="{d["width"]:.3f}"'
        paths.append(f'<path d="{"".join(parts)}" fill="{colour(d["fill"])}" fill-rule="{rule}"{extra}/>')
    width, height = rect.width, rect.height
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.3f} {height:.3f}" '
            f'width="{width:.3f}" height="{height:.3f}">' + "".join(paths) + "</svg>\n").encode()


def textless(data, record):
    """Redact only the listed label spans on a fresh in-memory copy, then render the panel."""
    with fitz.open(stream=data, filetype="pdf") as doc:
        page = doc[0]
        for span in label_spans(page, record["panel"], record["bbox"], record["live_labels"]):
            page.add_redact_annot(span["rect"], fill=None, cross_out=False)
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE, graphics=fitz.PDF_REDACT_LINE_ART_NONE,
                              text=fitz.PDF_REDACT_TEXT_REMOVE)
        pix = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), clip=panel_rect(record["panel"], record["bbox"]))
        return pix.tobytes("png")


def acquire(record, doc, data):
    recipe = record["acquisition"]
    page = doc[0]
    if recipe["kind"] == "textless-crop":
        return textless(data, record)
    if recipe["kind"] == "reuse":
        return (REPO / recipe["from"]).read_bytes()
    if recipe["kind"] == "crop":
        pix = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), clip=panel_rect(record["panel"], record["bbox"]))
        return pix.tobytes("png")
    if recipe["kind"] == "vector":
        return vector_svg(page, record["panel"], record["bbox"], recipe["drawing_indices"],
                          recipe.get("clipped_fill_indices", ()))
    if recipe["kind"] == "embedded-image":
        pix = fitz.Pixmap(doc, recipe["xref"])
        if pix.colorspace.n != 3:  # the print stores it as CMYK; PNG needs RGB (same pixels, no resampling)
            pix = fitz.Pixmap(fitz.csRGB, pix)
        return pix.tobytes("png")
    raise ValueError("unknown acquisition " + recipe["kind"])


def main(check):
    original, doc = archived_pdf()
    data = b"".join((SOURCE / part["path"]).read_bytes() for part in original["archive_parts"])
    path = SOURCE / "source/figures.json"
    records = json.loads(path.read_text())
    failures = []
    for record in records:
        output = acquire(record, doc, data)
        digest = hashlib.sha256(output).hexdigest()
        target = SOURCE / record["local_path"]
        if check:
            if digest != record["sha256"] or not target.is_file() or target.read_bytes() != output:
                failures.append(record["slot"])
            continue
        if record["acquisition"]["kind"] == "reuse":
            shutil.copyfile(REPO / record["acquisition"]["from"], target)
        else:
            target.write_bytes(output)
        record["sha256"] = digest
    if not check:
        path.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"assets": len(records), "mismatched": failures}, ensure_ascii=False))
    return failures


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify only; write nothing")
    raise SystemExit(1 if main(parser.parse_args().check) else 0)
