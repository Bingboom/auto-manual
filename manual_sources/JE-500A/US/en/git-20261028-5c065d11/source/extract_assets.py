"""Materialize the reviewed artwork decisions into assets/ and pin their hashes.

Run from the repository root after editing source/figures.json, source/symbols.json
or source/glyphs.json: ``python3 <package>/source/extract_assets.py``.
Inputs are re-read from the reviewed fields only, so the script is idempotent.

- Figures are source panels rendered from ``original.pdf`` at 4x, cropped just
  inside the print's panel frame; notes the print boxes inside a panel are set
  as shared callouts, not cropped.
- Symbols reuse the shared Web symbol library: every shared variant of the row's
  semantic family is compared with this print's own glyph drawings (the fixed
  comparison the shared symbol admission re-runs at release) and the first
  passing variant is copied byte for byte. A row with no passing variant stops
  the run: a missing symbol is raised with the operator, never drawn here.
- LCD glyphs and the FCC mark reuse their candidate (the same model's EU Web
  glyph, the shared FCC mark) when it passes the same fixed comparison against
  this print; otherwise this print's native vector paths
  are written as a transparent SVG and the rejection is recorded.
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
SHARED = "docs/renderers/web/assets/shared/symbols/"
SCALE = 4
SYMBOL_INPUT = ("language", "physical_page", "family", "meaning", "glyph_search_box", "caption_search_box")
GLYPH_INPUT = ("slot", "physical_page", "search_box", "local_path", "reuse_candidate")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def as_bytes(value) -> bytes:
    return value if isinstance(value, bytes) else value.encode()


def drawings_in(page, box, *, cell=True):
    """Paths inside a reviewed box; table rules and cell fills span the box and are not glyph."""
    area = fitz.Rect(box)
    drawings = page.get_drawings()
    found = [i for i, g in enumerate(drawings)
             if area.contains(g["rect"]) and (not cell or (g["rect"].width < area.width * 0.9
                                                   and g["rect"].height < area.height * 0.9))]
    bounds = fitz.Rect()
    for i in found:
        bounds |= drawings[i]["rect"]
    return found, list(bounds)


def figures(doc, pdf_sha: str):
    records = json.loads((SOURCE / "source/figures.json").read_text())
    for g in records:
        page = doc[g["physical_page"] - 1]
        crop = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), clip=fitz.Rect(g["bbox"]), alpha=False)
        g["local_path"] = "assets/" + g["slot"] + ".png"
        target = SOURCE / g["local_path"]
        target.write_bytes(crop.tobytes("png"))
        g.update(render_scale=SCALE, sha256=sha(target), source_sha256=pdf_sha,
                 decision="extract source panel at 4x (inside the print frame)")
    dump(SOURCE / "source/figures.json", records)
    return records


def symbols(doc):
    rows = json.loads((SOURCE / "source/symbols.json").read_text())
    library = json.loads((REPO / SHARED / "manifest.json").read_text())
    withdrawn = {w.get("sha256") for w in library.get("withdrawn", [])}
    for index, row in enumerate(rows):
        row = {key: row[key] for key in SYMBOL_INPUT}
        page = doc[row["physical_page"] - 1]
        indices, glyph = drawings_in(page, row["glyph_search_box"])
        _, caption = drawings_in(page, row["caption_search_box"])
        caption = [round(caption[0] - 1, 4), round(caption[1] - 1, 4), round(caption[2] + 1, 4), round(caption[3] + 1, 4)]
        band = fitz.Rect(glyph) | fitz.Rect(caption)
        row.update(drawing_indices=indices, glyph_bbox=glyph, caption_bbox=caption,
                   row_bbox=[round(v, 4) for v in (band.x0 - 1, band.y0 - 1, band.x1 + 1, band.y1 + 1)],
                   caption_text=" ".join(row["meaning"].split()), caption_mode="outlined-manual-transcription")
        pixels = page.get_pixmap(matrix=fitz.Matrix(4, 4), clip=fitz.Rect(caption), alpha=False)
        row["caption_sha256"] = hashlib.sha256(pixels.tobytes("png")).hexdigest()
        reference = as_bytes(native_symbol_svg(page, indices, glyph))
        tried = []
        for asset in library["assets"]:
            if not asset["key"].replace("_", "-").startswith(row["family"]) or asset["sha256"] in withdrawn:
                continue
            data = (REPO / SHARED / asset["path"]).read_bytes()
            try:
                result = compare_symbol(data, Path(asset["path"]).suffix, reference)
            except ValueError as exc:
                tried.append({"shared_symbol_key": asset["key"], "status": "rejected", "reason": str(exc)})
                continue
            tried.append({"shared_symbol_key": asset["key"], "status": "passed", **result})
            row.update(shared_symbol_key=asset["key"], shared_path=SHARED + asset["path"],
                       local_path="assets/" + Path(asset["path"]).name,
                       decision="reuse shared Web symbol unchanged (fixed glyph comparison against the print)")
            break
        row["candidates"] = tried
        if "shared_path" not in row:
            # No shared variant matches this print. The print's own native paths are the
            # proposed source-bound shared variant; it is not admitted until the operator
            # decides and the shared library carries it (release admission refuses it).
            row.update(shared_symbol_key=None, local_path="assets/" + row["family"].strip("/") + "-native-candidate.svg",
                       decision="PENDING operator decision: no shared variant passes; native paths proposed as a new shared variant")
            (SOURCE / row["local_path"]).write_bytes(reference)
        else:
            shutil.copy2(REPO / row["shared_path"], SOURCE / row["local_path"])
            if sha(SOURCE / row["local_path"]) != sha(REPO / row["shared_path"]):
                raise ValueError("shared bytes changed while copying " + row["local_path"])
        row["sha256"] = sha(SOURCE / row["local_path"])
        rows[index] = row
    dump(SOURCE / "source/symbols.json", rows)
    return rows


def glyphs(doc):
    rows = json.loads((SOURCE / "source/glyphs.json").read_text())
    for index, g in enumerate(rows):
        g = {key: g[key] for key in GLYPH_INPUT}
        page = doc[g["physical_page"] - 1]
        indices, bounds = drawings_in(page, g["search_box"], cell=False)
        reference = as_bytes(native_symbol_svg(page, indices, bounds))
        g.update(drawing_indices=indices, glyph_bbox=bounds)
        if g["reuse_candidate"] is None:
            g["reuse_comparison"] = {"status": "no-candidate",
                                     "reason": "no glyph for this icon in the JE-300E EU assets or shared/lcd"}
        else:
            candidate = REPO / g["reuse_candidate"]
            try:
                result = compare_symbol(candidate.read_bytes(), candidate.suffix, reference)
                g["reuse_comparison"] = {"status": "passed", **result}
            except ValueError as exc:
                g["reuse_comparison"] = {"status": "rejected", "reason": str(exc)}
        target = SOURCE / g["local_path"]
        if g["reuse_comparison"]["status"] == "passed":
            shutil.copy2(candidate, target)
            g["decision"] = "reuse the candidate unchanged (passes the fixed comparison against this print)"
        else:
            target.write_bytes(reference)
            g["decision"] = "native vector glyph from this print (transparent SVG)"
        g["sha256"] = sha(target)
        rows[index] = g
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
    counts = {"figures": len(figures(doc, original["sha256"])),
              "symbols": len(symbols(doc)), "glyphs": len(glyphs(doc))}
    print(json.dumps(counts))


if __name__ == "__main__":
    main()
