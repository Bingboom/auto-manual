"""Bind the JE-2000E JP safety symbols to shared catalog variants.

Run from the repository root:

    python manual_sources/JE-2000E/JP/ja/git-20261019-6a70e879-jp-native/derive_symbols.py

``source/symbol_recipe.json`` is the reviewed recipe. Each printed symbol is
compared with the authoritative PDF's own vector paths (``native_symbol_svg``)
under the fixed 2% admission; beyond it, the canonical of an operator-confirmed
group is released for a row whose source caption that group lists (the same
rule ``require_symbol_asset_admission`` enforces). The package copy is
byte-identical to the bound shared catalog variant. This script never writes the shared catalog: a missing
variant stops the run. It rewrites ``source_manifest.json:symbol_asset_admission``.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import fitz

PACKAGE = Path(__file__).resolve().parent
ROOT = next(parent for parent in PACKAGE.parents if (parent / "build.py").is_file())
sys.path.insert(0, str(ROOT))

from tools.asset_pipeline.native_svg import native_symbol_svg  # noqa: E402
from tools.web.shared_symbol_assets import canonical_groups  # noqa: E402
from tools.web.symbol_asset_admission import SCHEMA, _canonical_release, compare_symbol  # noqa: E402

SHARED_SYMBOLS = ROOT / "docs/renderers/web/assets/shared/symbols"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def caption_text(page: fitz.Page, bbox: list[float]) -> str:
    return "".join(page.get_text("text", clip=fitz.Rect(bbox)).split())


def derive() -> dict:
    recipe = read(PACKAGE / "source/symbol_recipe.json")
    manifest = read(PACKAGE / "source_manifest.json")
    pdf = PACKAGE / manifest["original_source"]["filename"]
    if sha256(pdf.read_bytes()) != recipe["source_sha256"]:
        raise ValueError("authoritative PDF identity changed")
    catalog = {row["key"]: row for row in read(SHARED_SYMBOLS / "manifest.json")["assets"]}
    rows = []
    groups = canonical_groups()
    with fitz.open(pdf) as doc:
        for symbol in recipe["symbols"]:
            page = doc[symbol["physical_page"] - 1]
            box = fitz.Rect(symbol["glyph_bbox"])
            indices = [i for i, d in enumerate(page.get_drawings()) if box.contains(d["rect"])]
            native = native_symbol_svg(page, indices, symbol["glyph_bbox"])
            entry = catalog.get(symbol["shared_symbol_key"])
            if entry is None:
                raise ValueError("shared symbol variant missing from the catalog: " + symbol["shared_symbol_key"])
            data = (SHARED_SYMBOLS / entry["path"]).read_bytes()
            suffix = Path(entry["path"]).suffix
            meaning = caption_text(page, symbol["caption_bbox"])
            try:
                check = compare_symbol(data, suffix, native)
            except ValueError as exc:
                # The gate's own rule: an operator-confirmed group's canonical
                # is released for a row whose source caption that group lists.
                check = _canonical_release(groups, {"shared_symbol_key": symbol["shared_symbol_key"]},
                                           meaning, "ja", data, suffix, native)
                if check is None:
                    raise ValueError(f"{symbol['path']}: {exc}") from exc
            (PACKAGE / symbol["path"]).write_bytes(data)
            glyph, caption = fitz.Rect(symbol["glyph_bbox"]), fitz.Rect(symbol["caption_bbox"])
            band = glyph | caption
            pixels = page.get_pixmap(matrix=fitz.Matrix(4, 4), clip=caption, alpha=False)
            rows.append({
                "asset_ref": symbol["path"].removeprefix("web/ja/"), "asset_sha256": sha256(data),
                "physical_page": symbol["physical_page"], "drawing_indices": indices,
                "glyph_bbox": symbol["glyph_bbox"], "caption_bbox": symbol["caption_bbox"],
                "row_bbox": [band.x0 - 1, band.y0 - 1, band.x1 + 1, band.y1 + 1],
                "caption_text": caption_text(page, symbol["caption_bbox"]),
                "caption_sha256": sha256(pixels.tobytes("png")),
                "shared_symbol_key": symbol["shared_symbol_key"], **check,
            })
    return {"schema_version": SCHEMA, "locales": {"ja": rows}}


def main() -> None:
    admission = derive()
    path = PACKAGE / "source_manifest.json"
    manifest = read(path)
    manifest["symbol_asset_admission"] = admission
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps([{k: r[k] for k in ("asset_ref", "shared_symbol_key", "max_mean_channel_error")}
                      for r in admission["locales"]["ja"]], ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
