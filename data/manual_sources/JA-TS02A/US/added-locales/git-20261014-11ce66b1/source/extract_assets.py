"""Materialize the reviewed French and Spanish artwork decisions into assets/ and pin their hashes.

Run from the repository root after editing source/figures.json, source/inline-controls.json
or source/symbols.json: ``python3 <package>/source/extract_assets.py``.

Inventory first (Web artwork reuse order): every FR/ES panel is compared with the accepted
English panel at the matched print offset. A panel whose crop matches the English panel
within antialiasing (at most 0.1% of pixels differ by more than 60/255) shares the English
file byte for byte; any other panel is cut from its own page as a complete panel, at the
English scale (3x). Inline App controls share the English files when their vector paths
are identical; symbols are the English assets, checked against each language's own
printed drawings with the fixed shared glyph comparison.
"""
from __future__ import annotations

import hashlib
from io import BytesIO
import json
from pathlib import Path
import shutil
import sys

import fitz
from PIL import Image, ImageChops, ImageDraw, ImageStat

REPO = next(p for p in Path(__file__).resolve().parents if (p / "build.py").is_file())
sys.path.insert(0, str(REPO))

from tools.asset_pipeline.native_svg import native_symbol_svg  # noqa: E402
from tools.web.symbol_asset_admission import _normalized, _render, compare_symbol  # noqa: E402

SOURCE = Path(__file__).resolve().parents[1]
SCALE = 3  # the accepted English crops are 3x renders of their PDF boxes
SHARE_LIMIT = 0.001
VECTOR_LIMIT = 0.001  # points; inline controls are the same drawing when every path point agrees


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def english_package(manifest):
    return REPO / manifest["english_baseline"]


def archived_pdf(manifest):
    original = manifest["original_source"]
    data = b"".join((REPO / part["path"]).read_bytes() for part in original["archive_parts"])
    if hashlib.sha256(data).hexdigest() != original["sha256"]:
        raise ValueError("archived source PDF identity changed")
    return fitz.open(stream=data, filetype="pdf")


def crop(doc, page, bbox, exclude=()):
    """A complete panel at the English scale; excluded print areas (a folio, a heading) stay blank."""
    pixmap = doc[page - 1].get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), clip=fitz.Rect(bbox), alpha=False)
    if not exclude:
        return pixmap.tobytes("png")
    image = Image.open(BytesIO(pixmap.tobytes("png"))).convert("RGB")
    draw = ImageDraw.Draw(image)
    for x0, y0, x1, y1 in exclude:
        draw.rectangle([(x0 - bbox[0]) * SCALE, (y0 - bbox[1]) * SCALE,
                        (x1 - bbox[0]) * SCALE - 1, (y1 - bbox[1]) * SCALE - 1], fill=(255, 255, 255))
    out = BytesIO()
    image.save(out, "PNG", optimize=True)
    return out.getvalue()


def match_crop(doc, page, bbox, size):
    """The English-sized pixel box at a (sub-point) print offset, cut from a 3x render of the page."""
    pixmap = doc[page - 1].get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=False)
    image = Image.open(BytesIO(pixmap.tobytes("png")))
    x, y = round(bbox[0] * SCALE), round(bbox[1] * SCALE)
    out = BytesIO()
    image.crop((x, y, x + size[0], y + size[1])).save(out, "PNG")
    return out.getvalue()


def differing_share(a: bytes, b: bytes) -> float:
    left, right = Image.open(BytesIO(a)).convert("L"), Image.open(BytesIO(b)).convert("L")
    if left.size != right.size:
        return 1.0
    histogram = ImageChops.difference(left, right).histogram()
    return sum(histogram[61:]) / max(1, sum(histogram))


def copy_english(english: Path, name: str, expected_sha: str) -> None:
    source = english / "assets" / name
    if sha(source) != expected_sha:
        raise ValueError("English asset changed: " + name)
    shutil.copy2(source, SOURCE / "assets" / name)
    if sha(SOURCE / "assets" / name) != expected_sha:
        raise ValueError("shared bytes changed while copying " + name)


def figures(doc, english, pdf_sha):
    records = json.loads((SOURCE / "source/figures.json").read_text())
    base = {f["slot"]: f for f in json.loads((english / "source/figures.json").read_text())}
    for g in records:
        en = base[g["slot"]]
        # The English-sized box at the offset where this page prints the same panel.
        english_art = (english / en["local_path"]).read_bytes()
        match = match_crop(doc, g["physical_page"], g["english_match_bbox"], Image.open(BytesIO(english_art)).size)
        share = differing_share(match, english_art)
        g["english_differing_pixel_share"] = round(share, 5)
        stale = SOURCE / "assets" / f"{g['language']}-{g['slot']}.png"
        if share <= SHARE_LIMIT:
            if g["bbox"] != g["english_match_bbox"] or g.get("exclude"):
                raise ValueError(f"{g['language']} {g['slot']}: a shared panel uses the matched English box")
            g["decision"] = "share the English panel (identical art)"
            g["reason"] = "The crop matches the accepted English panel within antialiasing."
            g["local_path"] = en["local_path"]
            g.pop("render_scale", None)
            stale.unlink(missing_ok=True)
            copy_english(english, Path(en["local_path"]).name, en["sha256"])
        else:
            g["decision"] = "extract complete source illustration (labels or art differ from the English panel)"
            g["reason"] = ("Printed labels are translated, or the art sits at a sub-point offset; "
                           "the English file would show other wording or other pixels.")
            g["local_path"] = f"assets/{g['language']}-{g['slot']}.png"
            g["render_scale"] = SCALE
            stale.write_bytes(crop(doc, g["physical_page"], g["bbox"], g.get("exclude", ())))
        g["sha256"] = sha(SOURCE / g["local_path"])
        g["source_sha256"] = pdf_sha
    dump(SOURCE / "source/figures.json", records)
    return records


def vector_points(page, box):
    area = fitz.Rect(box) + (-2, -2, 2, 2)
    drawings = [d for d in page.get_drawings() if area.contains(d["rect"])]
    origin = fitz.Rect()
    for d in drawings:
        origin |= d["rect"]
    points, style = [], []
    for d in drawings:
        style.append((d["type"], d.get("fill"), d.get("color"), d.get("width")))
        for item in d["items"]:
            for value in item[1:]:
                if isinstance(value, fitz.Point):
                    points.append((value.x - origin.x0, value.y - origin.y0))
    return style, points


def controls(doc, english):
    records = json.loads((SOURCE / "source/inline-controls.json").read_text())
    base = {c["slot"]: c for c in json.loads((english / "source/inline-controls.json").read_text())}
    for c in records:
        en = base[c["slot"]]
        style, points = vector_points(doc[c["physical_page"] - 1], c["bbox"])
        en_style, en_points = vector_points(doc[en["physical_page"] - 1], en["bbox"])
        if not points or style != en_style or len(points) != len(en_points):
            raise ValueError(f"{c['language']} {c['slot']}: not the English control drawing")
        delta = max(abs(a - b) for p, q in zip(points, en_points, strict=True) for a, b in zip(p, q, strict=True))
        if delta > VECTOR_LIMIT:
            raise ValueError(f"{c['language']} {c['slot']}: control paths differ by {delta}")
        copy_english(english, Path(en["local_path"]).name, en["sha256"])
        c.update(decision="share the English inline control (vector-identical source drawing)",
                 vector_max_delta_pt=float(f"{delta:.2e}"), local_path=en["local_path"], sha256=en["sha256"])
    dump(SOURCE / "source/inline-controls.json", records)
    return records


def drawings_in(page, box):
    """Glyph paths inside a reviewed box; table rules and cell fills span the box and are not glyph."""
    area = fitz.Rect(box)
    found = [i for i, g in enumerate(page.get_drawings())
             if area.contains(g["rect"]) and g["rect"].width < area.width * 0.9 and g["rect"].height < area.height * 0.9]
    bounds = fitz.Rect()
    for i in found:
        bounds |= page.get_drawings()[i]["rect"]
    return found, list(bounds)


def symbols(doc, english):
    """English symbol assets where they pass the fixed glyph gate against this page; else the print's own vectors."""
    rows = json.loads((SOURCE / "source/symbols.json").read_text())
    base = {r["local_path"]: r for r in json.loads((english / "source/figures.json").read_text())
            if r["slot"].startswith("symbol/")}
    written = {}
    for row in rows:
        en = base[row["english_asset"]]
        page = doc[row["physical_page"] - 1]
        indices, glyph = drawings_in(page, row["search_box"])
        reference = native_symbol_svg(page, indices, glyph)
        row.update(drawing_indices=indices, glyph_bbox=glyph)
        candidate = (english / row["english_asset"]).read_bytes()
        try:
            row["glyph_comparison"] = compare_symbol(candidate, Path(row["english_asset"]).suffix, reference)
        except ValueError:
            error = max(ImageStat.Stat(ImageChops.difference(
                _normalized(_render(candidate, Path(row["english_asset"]).suffix)),
                _normalized(_render(reference, ".svg")))).mean)
            row["english_asset_comparison"] = {"max_mean_channel_error": round(error / 255, 6), "passes_fixed_gate": False}
        else:
            copy_english(english, Path(row["english_asset"]).name, en["sha256"])
            row.update(decision="reuse the English asset (passes the fixed glyph gate against this page)",
                       local_path=row["english_asset"], sha256=en["sha256"])
            continue
        # The English (shared) asset draws another glyph than this print: keep the print's own vector paths.
        # French and Spanish share one print vector when it passes the same gate against both pages.
        name = f"assets/{Path(row['english_asset']).stem}-print.svg"
        if name in written:
            try:
                row["glyph_comparison"] = compare_symbol(written[name], ".svg", reference)
            except ValueError:
                name = f"assets/{row['language']}-{Path(name).name}"
        if name not in written:
            (SOURCE / name).write_bytes(reference)
            written[name] = reference
            row["glyph_comparison"] = compare_symbol(reference, ".svg", reference)
        row.update(decision="native-source-glyph (the English asset misses the fixed glyph gate against this print)",
                   local_path=name, sha256=sha(SOURCE / name))
    dump(SOURCE / "source/symbols.json", rows)
    return rows


def main() -> None:
    manifest = json.loads((SOURCE / "source_manifest.json").read_text())
    english = english_package(manifest)
    doc = archived_pdf(manifest)
    (SOURCE / "assets").mkdir(exist_ok=True)
    counts = {"figures": len(figures(doc, english, manifest["original_source"]["sha256"])),
              "controls": len(controls(doc, english)), "symbols": len(symbols(doc, english))}
    print(json.dumps(counts))


if __name__ == "__main__":
    main()
