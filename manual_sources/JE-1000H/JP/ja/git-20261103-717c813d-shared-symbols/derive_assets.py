"""Derive the JE-1000H JP Web artwork from the frozen PDF and reused shared files.

Run from the repository root:

    python manual_sources/JE-1000H/JP/ja/git-20261103-717c813d-shared-symbols/derive_assets.py

``source/asset_recipe.json`` is the reviewed recipe. Panels are complete
3x renders of the source rectangle (panel backgrounds, leader lines, captions
and phone frames kept). The AC1 button keeps its original PDF vector paths
through the shared ``native_symbol_svg`` selector. The LIGHT button carries a
text-layer marking that the vector selector cannot keep, so it is a 6x render
of its own circle with everything outside the circle made transparent. LCD
icons and the POWER / DC/USB buttons are reused byte-identically after a hash
check. Every symbol row binds the canonical of its operator-confirmed shared
group (``canonical_groups`` of the shared catalog) byte for byte; a canonical
beyond the fixed 2% tolerance is released only when the row's source caption is
listed for that group, as ``require_symbol_asset_admission`` does. This script
never writes the shared catalog. The symbol
admission rows of ``source_manifest.json`` are written from the same recipe
and the reviewed transcription.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import sys

import fitz
from PIL import Image, ImageDraw

PACKAGE = Path(__file__).resolve().parent
ROOT = next(parent for parent in PACKAGE.parents if (parent / "build.py").is_file())
sys.path.insert(0, str(ROOT))

from tools.asset_pipeline.native_svg import native_symbol_svg  # noqa: E402
from tools.web.shared_symbol_assets import canonical_groups  # noqa: E402
from tools.web.symbol_asset_admission import SCHEMA, _symbol_error, _text, compare_symbol  # noqa: E402

SHARED_SYMBOLS = ROOT / "docs/renderers/web/assets/shared/symbols"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def native_svg(page: fitz.Page, bbox: list[float]) -> tuple[bytes, list[int]]:
    box = fitz.Rect(bbox)
    indices = [i for i, d in enumerate(page.get_drawings()) if box.contains(d["rect"])]
    return native_symbol_svg(page, indices, bbox), indices


def caption_pixels(page: fitz.Page, bbox: list[float]) -> str:
    pixels = page.get_pixmap(matrix=fitz.Matrix(4, 4), clip=fitz.Rect(bbox), alpha=False)
    return sha256(pixels.tobytes("png"))


def symbol_check(groups: dict, symbol: dict, caption: str, data: bytes, native: bytes) -> dict:
    """Fixed 2% comparison, or the confirmed group's caption-bound canonical release."""
    group, role = groups.get(symbol["shared_symbol_key"], (None, None))
    if group is not None and group["status"] == "operator-confirmed" and role != "canonical":
        raise ValueError("bind the canonical of group " + group["id"] + ": " + symbol["path"])
    suffix = Path(symbol["shared_path"]).suffix
    try:
        check = compare_symbol(data, suffix, native)
    except ValueError:
        if (group is None or group["status"] != "operator-confirmed"
                or _text(caption) not in {_text(c) for c in group["captions"].get("ja", [])}):
            raise
        check = {"max_mean_channel_error": round(_symbol_error(data, suffix, native), 6)}
    if group is not None:
        check.update({"canonical_group": group["id"], "canonical_status": group["status"]})
    return check


def circle_png(page: fitz.Page, bbox: list[float], scale: int, path: Path) -> None:
    """Render one round button and clear the cell backdrop outside its circle."""
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=fitz.Rect(bbox), alpha=False)
    image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples).convert("RGBA")
    over = 4  # supersampled mask for an antialiased edge
    mask = Image.new("L", (image.width * over, image.height * over), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, mask.width - 1, mask.height - 1), fill=255)
    image.putalpha(mask.resize(image.size, Image.Resampling.LANCZOS))
    image.save(path, optimize=True)


def derive() -> dict:
    recipe = read(PACKAGE / "source/asset_recipe.json")
    manifest = read(PACKAGE / "source_manifest.json")
    pdf = PACKAGE / manifest["original_source"]["filename"]
    if sha256(pdf.read_bytes()) != recipe["source_sha256"]:
        raise ValueError("authoritative PDF identity changed")
    lines = {line["id"]: line["text"] for page in read(PACKAGE / "source/transcription.json")["pages"]
             for line in page["lines"]}
    assets = PACKAGE / "assets"
    if assets.exists():
        shutil.rmtree(assets)
    (assets / "lcd").mkdir(parents=True)
    scale = fitz.Matrix(recipe["panel_scale"], recipe["panel_scale"])
    with fitz.open(pdf) as doc:
        for panel in recipe["panels"]:
            page = doc[panel["physical_page"] - 1]
            page.get_pixmap(matrix=scale, clip=fitz.Rect(panel["bbox"]), alpha=False).save(PACKAGE / panel["path"])
        for icon in recipe["native_icons"]:
            svg, indices = native_svg(doc[icon["physical_page"] - 1], icon["glyph_bbox"])
            if indices != icon["drawing_indices"]:
                raise ValueError("native icon drawing selection changed: " + icon["path"])
            (PACKAGE / icon["path"]).write_bytes(svg)
        for icon in recipe["circle_icons"]:
            circle_png(doc[icon["physical_page"] - 1], icon["circle_bbox"], icon["scale"], PACKAGE / icon["path"])
        rows = []
        groups = canonical_groups()
        for symbol in recipe["symbols"]:
            page = doc[symbol["physical_page"] - 1]
            native, indices = native_svg(page, symbol["glyph_bbox"])
            if indices != symbol["drawing_indices"]:
                raise ValueError("symbol drawing selection changed: " + symbol["path"])
            data = (SHARED_SYMBOLS / symbol["shared_path"]).read_bytes()
            caption_text = "".join(lines[key] for key in symbol["caption_ids"])
            check = symbol_check(groups, symbol, caption_text, data, native)
            (PACKAGE / symbol["path"]).write_bytes(data)
            glyph, caption = fitz.Rect(symbol["glyph_bbox"]), fitz.Rect(symbol["caption_bbox"])
            band = glyph | caption
            rows.append({
                "asset_ref": symbol["path"], "asset_sha256": sha256(data),
                "physical_page": symbol["physical_page"], "drawing_indices": indices,
                "glyph_bbox": symbol["glyph_bbox"], "caption_bbox": symbol["caption_bbox"],
                "row_bbox": [band.x0 - 1, band.y0 - 1, band.x1 + 1, band.y1 + 1],
                "caption_text": caption_text,
                "caption_sha256": caption_pixels(page, symbol["caption_bbox"]),
                "shared_symbol_key": symbol["shared_symbol_key"], **check,
            })
    for item in recipe["reused"]:
        data = (ROOT / item["from"]).read_bytes()
        if sha256(data) != item["sha256"]:
            raise ValueError("reused asset changed: " + item["from"])
        (PACKAGE / item["path"]).write_bytes(data)
    return {"schema_version": SCHEMA, "locales": {"ja": rows}}


def main() -> None:
    admission = derive()
    path = PACKAGE / "source_manifest.json"
    manifest = read(path)
    manifest["symbol_asset_admission"] = admission
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"assets": sorted(p.relative_to(PACKAGE).as_posix()
                                       for p in (PACKAGE / "assets").rglob("*") if p.is_file())}, indent=1))


if __name__ == "__main__":
    main()
