"""Materialize the reviewed artwork decisions into assets/ and pin their hashes.

Run from the repository root after editing source/figures.json, source/symbols.json
or source/glyphs.json: ``python3 <package>/source/extract_assets.py``.

- Figures are complete source panels rendered from the archived booklet at 4x.
  Words a record lifts out of its art (``lift_boxes``) are redacted from the crop
  as text only; every drawing stays.
- Symbols are shared Web symbols copied byte for byte; each row records the native
  drawings, caption pixels and the fixed glyph comparison the shared symbol
  admission re-checks at release.
- Glyphs (LCD icons, contact pictograms) are this print's native vector paths
  (transparent SVG). A row that names a shared candidate reuses it when the shared
  glyph passes the same fixed comparison; otherwise the result is recorded.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import sys

import fitz

REPO = next(p for p in Path(__file__).resolve().parents if (p / "build.py").is_file())
sys.path.insert(0, str(REPO))

from tools.asset_pipeline.native_svg import native_symbol_svg  # noqa: E402
from tools.web.symbol_asset_admission import compare_symbol  # noqa: E402

SOURCE = Path(__file__).resolve().parents[1]
SCALE = 4


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def drawings_in(page, box, *, cell=True):
    """Glyph paths inside a reviewed box; table rules and cell fills span the box and are not glyph."""
    area = fitz.Rect(box)
    drawings = page.get_drawings()
    found = [i for i, g in enumerate(drawings)
             if area.contains(g["rect"]) and (not cell or (g["rect"].width < area.width * 0.9
                                                   and g["rect"].height < area.height * 0.9))]
    bounds = fitz.Rect()
    for i in found:
        bounds |= drawings[i]["rect"]
    return found, list(bounds)


def as_bytes(value) -> bytes:
    return value if isinstance(value, bytes) else value.encode()


def figures(data: bytes, pdf_sha: str):
    records = json.loads((SOURCE / "source/figures.json").read_text())
    for g in records:
        doc = fitz.open(stream=data, filetype="pdf")
        page = doc[g["physical_page"] - 1]
        for box in g.get("lift_boxes", []):
            page.add_redact_annot(fitz.Rect(box), fill=False)
        if g.get("lift_boxes"):
            page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE, graphics=fitz.PDF_REDACT_LINE_ART_NONE,
                                  text=fitz.PDF_REDACT_TEXT_REMOVE)
        crop = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), clip=fitz.Rect(g["bbox"]), alpha=False)
        target = SOURCE / g["local_path"]
        target.write_bytes(crop.tobytes("png"))
        g.update(render_scale=SCALE, sha256=sha(target), source_sha256=pdf_sha)
    dump(SOURCE / "source/figures.json", records)
    return records


def copy_shared(record):
    source = REPO / record["shared_path"]
    target = SOURCE / record["local_path"]
    shutil.copy2(source, target)
    if sha(target) != sha(source):
        raise ValueError("shared bytes changed while copying " + record["local_path"])
    record["sha256"] = sha(target)


def symbols(doc):
    rows = json.loads((SOURCE / "source/symbols.json").read_text())
    for row in rows:
        page = doc[row["physical_page"] - 1]
        copy_shared(row)
        indices, glyph = drawings_in(page, row["glyph_search_box"])
        words = [w for w in page.get_text("words") if fitz.Rect(row["caption_search_box"]).contains(fitz.Rect(w[:4]))]
        caption = [round(min(w[0] for w in words) - 1, 4), round(min(w[1] for w in words) - 1, 4),
                   round(max(w[2] for w in words) + 1, 4), round(max(w[3] for w in words) + 1, 4)]
        band = fitz.Rect(glyph) | fitz.Rect(caption)
        row.update(drawing_indices=indices, glyph_bbox=glyph, caption_bbox=caption,
                   row_bbox=[round(v, 4) for v in (band.x0 - 1, band.y0 - 1, band.x1 + 1, band.y1 + 1)],
                   caption_text=" ".join(" ".join(w[4] for w in words).split()))
        pixels = page.get_pixmap(matrix=fitz.Matrix(4, 4), clip=fitz.Rect(caption), alpha=False)
        row["caption_sha256"] = hashlib.sha256(pixels.tobytes("png")).hexdigest()
        row["caption_mode"] = "native-extractable-text"
        reference = native_symbol_svg(page, indices, glyph)
        local = SOURCE / row["local_path"]
        row["glyph_comparison"] = compare_symbol(local.read_bytes(), local.suffix, reference)
    dump(SOURCE / "source/symbols.json", rows)
    return rows


def glyphs(doc):
    rows = json.loads((SOURCE / "source/glyphs.json").read_text())
    for g in rows:
        page = doc[g["physical_page"] - 1]
        indices, bounds = drawings_in(page, g["search_box"], cell=False)
        reference = as_bytes(native_symbol_svg(page, indices, bounds))
        g.update(drawing_indices=indices, glyph_bbox=bounds)
        candidate = g.get("shared_candidate")
        if candidate:
            shared = REPO / candidate
            try:
                result = compare_symbol(shared.read_bytes(), shared.suffix, reference)
                g["shared_comparison"] = {"status": "passed", **result}
            except ValueError as exc:
                g["shared_comparison"] = {"status": "rejected", "reason": str(exc)}
            if g["shared_comparison"]["status"] == "passed":
                g.update(decision="reuse shared Web LCD glyph unchanged", shared_path=candidate,
                         local_path="assets/" + shared.name)
                copy_shared(g)
                continue
        target = SOURCE / g["local_path"]
        target.write_bytes(reference)
        g["sha256"] = sha(target)
    dump(SOURCE / "source/glyphs.json", rows)
    return rows


def main() -> None:
    manifest = json.loads((SOURCE / "source_manifest.json").read_text())
    original = manifest["original_source"]
    data = (SOURCE / original["filename"]).read_bytes()
    if hashlib.sha256(data).hexdigest() != original["sha256"]:
        raise ValueError("archived source identity changed")
    assets = SOURCE / "assets"
    if assets.exists():
        shutil.rmtree(assets)
    assets.mkdir()
    doc = fitz.open(stream=data, filetype="pdf")
    counts = {"figures": len(figures(data, original["sha256"])),
              "symbols": len(symbols(doc)), "glyphs": len(glyphs(doc))}
    print(json.dumps(counts))


if __name__ == "__main__":
    main()
