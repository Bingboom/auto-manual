"""Materialize the reviewed artwork decisions into assets/ and pin their hashes.

Run from the repository root after editing source/figures.json, source/symbols.json
or source/glyphs.json: ``python3 <package>/source/extract_assets.py``. Reused files
are copied byte-for-byte and must match their origin; extracted crops are rendered
from the archived PDF at 4x (the scale of the reused JBP-3600A EU Web artwork).
A French or Spanish panel whose crop matches the English panel pixel for pixel
(within antialiasing) shares the English file; any other panel is cut per language.
Symbol rows record the native drawings, caption pixels and the fixed glyph
comparison that the shared symbol admission re-checks at release.
"""
from __future__ import annotations

import hashlib
from io import BytesIO
import json
from pathlib import Path
import shutil
import sys

import fitz
from PIL import Image, ImageChops

REPO = next(p for p in Path(__file__).resolve().parents if (p / "build.py").is_file())
sys.path.insert(0, str(REPO))

from tools.asset_pipeline.native_svg import native_symbol_svg  # noqa: E402
from tools.web.symbol_asset_admission import compare_symbol  # noqa: E402

SOURCE = Path(__file__).resolve().parents[1]
SCALE = 4
# A panel counts as identical when no more than 0.1% of its pixels differ by more than 60/255.
SHARE_LIMIT = 0.001


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def drawings_in(page, box, *, cell=True):
    """Glyph paths inside a reviewed box; table rules and cell fills span the box and are not glyph."""
    area = fitz.Rect(box)
    found = [i for i, g in enumerate(page.get_drawings())
             if area.contains(g["rect"]) and (not cell or (g["rect"].width < area.width * 0.9
                                                   and g["rect"].height < area.height * 0.9))]
    bounds = fitz.Rect()
    for i in found:
        bounds |= page.get_drawings()[i]["rect"]
    return found, list(bounds)


def differing_share(a: bytes, b: bytes) -> float:
    left, right = Image.open(BytesIO(a)).convert("L"), Image.open(BytesIO(b)).convert("L")
    if left.size != right.size:
        return 1.0
    histogram = ImageChops.difference(left, right).histogram()
    return sum(histogram[61:]) / max(1, sum(histogram))


def copy_shared(record):
    source = REPO / record["shared_path"]
    target = SOURCE / record["local_path"]
    shutil.copy2(source, target)
    if sha(target) != sha(source):
        raise ValueError("shared bytes changed while copying " + record["local_path"])
    record["sha256"] = sha(target)


def figures(doc, pdf_sha):
    records = json.loads((SOURCE / "source/figures.json").read_text())
    english = {}
    for g in records:
        page = doc[g["physical_page"] - 1]
        crop = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), clip=fitz.Rect(g["bbox"]), alpha=False).tobytes("png")
        if g["language"] == "en":
            target = SOURCE / g["local_path"]
            if g["decision"].startswith("reuse"):
                shutil.copy2(REPO / g["source"], target)
                if sha(target) != sha(REPO / g["source"]):
                    raise ValueError("reused bytes changed: " + g["slot"])
            else:
                target.write_bytes(crop)
                g["render_scale"] = SCALE
            english[g["slot"]] = g
        else:
            base = english[g["slot"]]
            share = differing_share(crop, (SOURCE / base["local_path"]).read_bytes())
            g["differing_pixel_share"] = round(share, 5)
            if share <= SHARE_LIMIT:
                g["decision"] = "share the English panel (identical art)"
                stale = SOURCE / "assets" / f"{g['language']}-{g['slot']}.png"
                stale.unlink(missing_ok=True)
                g["local_path"] = base["local_path"]
            else:
                g["decision"] = "extract complete source illustration (labels or art differ from the English panel)"
                g["local_path"] = f"assets/{g['language']}-{g['slot']}.png"
                g["render_scale"] = SCALE
                (SOURCE / g["local_path"]).write_bytes(crop)
            g["caption"] = g.get("caption") or base["caption"]
        g["sha256"] = sha(SOURCE / g["local_path"])
        g["source_sha256"] = pdf_sha
    dump(SOURCE / "source/figures.json", records)
    return records


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


def icon_pixels(doc, g):
    box = fitz.Rect(g["glyph_bbox"])
    pixmap = doc[g["physical_page"] - 1].get_pixmap(matrix=fitz.Matrix(12, 12), clip=box, alpha=False)
    image = Image.open(BytesIO(pixmap.tobytes("png"))).convert("L").resize((180, 112))
    out = BytesIO()
    image.save(out, "PNG")
    return out.getvalue()


def glyphs(doc):
    rows = json.loads((SOURCE / "source/glyphs.json").read_text())
    english = {}
    for g in rows:
        page = doc[g["physical_page"] - 1]
        indices, bounds = drawings_in(page, g["search_box"], cell=False)
        reference = native_symbol_svg(page, indices, bounds)
        g.update(drawing_indices=indices, glyph_bbox=bounds)
        if "shared_path" in g:
            copy_shared(g)
            local = SOURCE / g["local_path"]
            g["glyph_comparison"] = compare_symbol(local.read_bytes(), local.suffix, reference)
            continue
        if g["language"] == "en":
            target = SOURCE / g["local_path"]
            target.write_bytes(reference if isinstance(reference, bytes) else reference.encode())
            english[g["slot"]] = g
        else:
            # The same printed icon on the FR/ES page shares the English vector when the printed
            # pixels match (MuPDF cannot render this glyph's clip paths for compare_symbol).
            base = english[g["slot"]]
            share = differing_share(icon_pixels(doc, g), icon_pixels(doc, base))
            if share > SHARE_LIMIT * 20:
                raise ValueError(f"{g['language']} {g['slot']} differs from the English glyph")
            g["printed_pixel_comparison"] = {"differing_pixel_share": round(share, 5)}
            if g["local_path"] != base["local_path"]:
                (SOURCE / g["local_path"]).unlink(missing_ok=True)
            g["decision"] = "share the English native glyph (fixed glyph comparison)"
            g["local_path"] = base["local_path"]
        g["sha256"] = sha(SOURCE / g["local_path"])
    dump(SOURCE / "source/glyphs.json", rows)
    return rows


def main() -> None:
    manifest = json.loads((SOURCE / "source_manifest.json").read_text())
    pdf = SOURCE / manifest["original_source"]["filename"]
    if sha(pdf) != manifest["original_source"]["sha256"]:
        raise ValueError("archived source PDF identity changed")
    doc = fitz.open(pdf)
    (SOURCE / "assets").mkdir(exist_ok=True)
    counts = {"figures": len(figures(doc, manifest["original_source"]["sha256"])),
              "symbols": len(symbols(doc)), "glyphs": len(glyphs(doc))}
    print(json.dumps(counts))


if __name__ == "__main__":
    main()
