"""Derive the Web artwork of this package: reuse the JS-100I EU art, extract only JP-specific figures.

Run from the repository root (requirements.lock, PyMuPDF 1.28.0 / MuPDF 1.29.0):

    python manual_sources/JS-100I/JP/ja/git-20261026-cc8b3421/derive_assets.py

Reuse comes first (web-artwork-reuse.md). Figures whose drawing matches the
published JS-100I EU Web art are copied byte for byte from
``docs/renderers/web/assets/`` and recorded with their source path and SHA-256
in ``source/asset_decisions.json``. Only figures whose drawing differs in the JP
master (Japanese power-station models, the JP manual cover, figures with JP
labels on art the EU edition does not hold label-free) are cropped from the
frozen PDF through the shared asset pipeline.

Every letter of the PDF is outlined, so it has no text layer. The labels printed
on an extracted figure become native text: on a white page ``whiteout`` clears
their outlined glyphs; on a grey figure panel ``copy_pdf_region`` repaints the
glyphs and the white note bubbles with a blank square of the same panel, copied
from the frozen source. Vector replay is not used: this master draws quadrilateral
paths the replay does not support, and relies on clipping paths. The script
writes ``source/asset_recipe.json``, ``source/figure_labels.json`` and
``source/asset_decisions.json`` and refreshes ``assets/``; a second run leaves the
tree unchanged.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import shutil
import sys
import tempfile

PACKAGE = Path(__file__).resolve().parent
ROOT = next(parent for parent in PACKAGE.parents if (parent / "build.py").is_file())
sys.path.insert(0, str(ROOT))

import pymupdf  # noqa: E402

from tools.asset_pipeline import load_recipe, run_intake  # noqa: E402
from tools.asset_pipeline.extract import sha256_file  # noqa: E402

PDF = PACKAGE / "source" / "original.pdf"
SOURCE_SHA256 = "cc8b3421221bf11b03f2ddd0ce86519605189fbe0721a7d8a536520d75513e6f"
SOURCE_KEY = "source/js-100i-jp-solarsaga-100-air-manual"
PAGES = 12
EU_SHARED = "docs/renderers/web/assets/js100i_eu_shared"
EU_EN = "docs/renderers/web/assets/js100i_eu_en"

# Byte-identical reuse of the published JS-100I EU Web art: (asset, source, JP page, reason).
REUSED = [
    ("inbox_panel.png", f"{EU_EN}/inbox_panel.png", 3, "同梱品① panel drawing identical to the JP card"),
    ("inbox_bag.png", f"{EU_EN}/inbox_bag.png", 3, "同梱品② storage bag drawing identical"),
    ("inbox_cable.png", f"{EU_EN}/inbox_cable.png", 3, "同梱品③ charging cable drawing identical"),
    ("unfold_1.png", f"{EU_SHARED}/unfold_1.png", 4, "展開 1: bag and panel drawing identical, both arrows"),
    ("unfold_2.png", f"{EU_SHARED}/unfold_2.png", 4, "展開 2: three unfolding stages identical"),
    ("unfold_3.png", f"{EU_SHARED}/unfold_3.png", 5, "展開 3: rear view with both stands identical"),
    ("fold_1.png", f"{EU_SHARED}/fold_1.png", 5, "収納 1: flat panel identical"),
    ("fold_2.png", f"{EU_SHARED}/fold_2.png", 5, "収納 2: two folding stages identical"),
    ("angle_choice_1.png", f"{EU_SHARED}/angle_choice_1.png", 8, "check mark and indicator drawing identical; caption is native text"),
    ("angle_choice_2.png", f"{EU_SHARED}/angle_choice_2.png", 8, "cross mark and indicator drawing identical; caption is native text"),
    ("dust.png", f"{EU_SHARED}/dust.png", 9, "rubber-plug close-up identical; the printed note is native text"),
]

CORNER = 8.5
INSET = 1.6
PAD = 0.7

# Extracted figures. ``panel`` figures sit on a grey print panel kept whole
# (rounded corners, grey ground); ``frame`` figures sit in a white step frame
# whose decorative outline stays outside the crop; ``page`` figures sit on the white
# page. ``origin`` (x, y, largest side in pt) anchors a blank square of the
# panel ground, measured as a single colour, that repaints glyphs and note bubbles. Labels are (text, glyph search regions in pt).
FIGURES = [
    {"name": "inbox_manual", "page": 3, "kind": "page", "crop": (58.5, 188.0, 100.5, 246.5),
     "reason": "JP card shows this manual's own cover; the EU card is a generic document icon", "labels": []},
    {"name": "front_view", "page": 3, "kind": "page", "crop": (72.0, 418.0, 338.0, 468.0),
     "reason": "EU product_views.png bakes English labels and pairs front/rear views; no label-free base exists",
     "labels": [("太陽角度インジケーター", [(266.0, 428.0, 336.0, 437.5)])]},
    {"name": "rear_view", "page": 4, "kind": "page", "crop": (26.0, 38.0, 346.0, 147.0),
     # 本体背面 sits beside the panel top; it is a native heading, not a figure label.
     "clears": [(26.0, 37.0, 58.0, 46.5)],
     "reason": "EU product_views.png bakes English labels; no label-free rear view exists",
     "labels": [
         ("ペグで固定するためのあらかじめ開けられた穴", [(270.0, 50.0, 340.0, 59.0), (270.0, 60.0, 340.0, 69.0)]),
         ("アダプターボックス", [(26.0, 68.0, 82.0, 77.0)]),
         ("スタンド", [(119.0, 108.0, 146.0, 117.5)]),
         ("穴の直径：10mm", [(294.0, 137.0, 346.0, 146.0)]),
     ]},
    {"name": "unfold_4", "page": 5, "kind": "frame", "frame": 84144, "top": 156.0,
     "reason": "JP step 4 shows a different power station from the EU unfold_4 art", "labels": []},
    {"name": "fold_3", "page": 6, "kind": "frame", "frame": 83999, "top": 46.4,
     "reason": "JP step 3 prints both bag arrows; the EU fold_3 art lost its lower arrow", "labels": []},
    {"name": "dc8020", "page": 6, "kind": "panel", "frame": 38736, "origin": (37.5, 165.9, 38.0),
     "bubbles": [38746, 38747],
     "reason": "JP DC8020 figure shows a different power station and port close-up",
     "labels": [
         ("DC8020", [(213.0, 162.0, 237.0, 170.0)]),
         ("※一般的に、以下のモデルが該当します：<br/>1500PTB / Proシリーズ / NEWシリーズ(240NEWを除く） /<br/>Plusシリーズ(300Plus/100Plusを除く)",
          [(163.0, 258.0, 327.0, 287.5)]),
     ]},
    {"name": "dc7909", "page": 6, "kind": "panel", "frame": 39337, "origin": (38.0, 348.6, 56.0),
     "bubbles": [39341, 39342],
     "reason": "JP DC7909 figure shows Explorer 1000 and a straight adapter; EU shows another model and an L adapter",
     "labels": [
         ("アダプターDC8020 - DC7909", [(164.0, 344.5, 243.0, 353.5)]),
         ("※旧モデルである以下の機種が該当します：<br/>240Wh / 400Wh / 700 / 708Wh / 1000Wh",
          [(196.0, 464.0, 326.0, 484.5)]),
     ]},
    {"name": "usbc", "page": 7, "kind": "panel", "frame": 41068, "origin": (37.5, 81.2, 60.0),
     "bubbles": [41086, 41087],
     "reason": "JP USB-C figure shows a different power station and panel layout",
     "labels": [
         ("アダプター DC8020 - USB-C", [(179.0, 84.5, 256.0, 94.0)]),
         ("※ 一般的に、以下のモデルが該当します：<br/>100Plus、240New、300Plusなど、入力端子が<br/>USB-C（in/out）のモデル。",
          [(180.0, 211.5, 316.0, 242.0)]),
     ]},
    {"name": "parallel", "page": 7, "kind": "panel", "frame": 90139, "origin": (39.0, 333.8, 38.0),
     "bubbles": [],
     "reason": "JP SolarSaga adapter figure shows a different power station and panel arrangement",
     "labels": [
         ("DC8020", [(203.0, 337.5, 227.5, 346.0)]),
         ("SolarSaga アダプター (Pro/Plus/New専用)", [(162.0, 449.5, 277.0, 459.5)]),
         ("別売り", [(210.0, 459.8, 231.0, 468.5)]),
     ]},
    {"name": "angle", "page": 8, "kind": "panel", "frame": 7331, "origin": (37.3, 157.0, 46.0),
     "bubbles": [],
     "reason": "JP indicator figure draws the panel, rays and close-up at another angle and scale than EU angle.png",
     "labels": [
         ("太陽角度インジケーター", [(200.0, 197.5, 272.0, 207.5)]),
         ("インジケーターポイント", [(252.0, 239.0, 322.0, 248.0)]),
         ("シャドウ", [(252.5, 250.0, 281.0, 259.0)]),
     ]},
    {"name": "device", "page": 9, "kind": "panel", "frame": 31632, "origin": (37.6, 56.3, 30.0),
     "bubbles": [31728],
     "reason": "JP device figure shows another power station and a closed adapter close-up",
     "labels": [
         ("多機能アダプター", [(192.0, 59.0, 241.0, 68.5)]),
         ("Jackery  SolarSaga 100 Air", [(47.0, 137.5, 123.5, 147.0)]),
         ("携帯電話", [(110.0, 180.0, 142.0, 189.5)]),
         ("電源グループ", [(145.0, 180.0, 184.5, 189.5)]),
         ("タブレット", [(189.5, 180.0, 219.0, 189.5)]),
         ("※ この多機能充電ケーブルは本製品にのみ対応しており、他のモデルのソーラーパネルには使用しないでください。",
          [(45.0, 207.0, 320.0, 225.5)]),
     ]},
]


def _round(values) -> list[float]:
    return [round(float(v), 2) for v in values]


def _is_glyph(drawing: dict, region: pymupdf.Rect) -> bool:
    fill = drawing.get("fill")
    rect = pymupdf.Rect(drawing["rect"])
    return (drawing["type"] == "f" and fill is not None and max(fill) < 0.4
            and rect.height < 9.0 and region.contains(rect))


def _tiles(dest: pymupdf.Rect, limit: float) -> list[pymupdf.Rect]:
    """Square tiles inside ``dest`` that cover it; the copied origin square is at most ``limit`` wide."""
    side = min(limit, dest.width, dest.height)
    columns = max(1, math.ceil(dest.width / side - 1e-9))
    rows = max(1, math.ceil(dest.height / side - 1e-9))
    xs = [dest.x0 + (dest.width - side) * (i / (columns - 1) if columns > 1 else 0) for i in range(columns)]
    ys = [dest.y0 + (dest.height - side) * (j / (rows - 1) if rows > 1 else 0) for j in range(rows)]
    return [pymupdf.Rect(x, y, x + side, y + side) for y in ys for x in xs]


def figure(drawings: list[dict], spec: dict) -> tuple[list[dict], dict]:
    kind = spec["kind"]
    if kind == "page":
        crop = pymupdf.Rect(spec["crop"])
    else:
        frame = pymupdf.Rect(drawings[spec["frame"]]["rect"])
        # A step frame's rounded corners stay outside the crop: the crop starts
        # below the step copy and keeps clear of the corner radius on both sides.
        crop = frame if kind == "panel" else pymupdf.Rect(
            frame.x0 + CORNER, spec["top"], frame.x1 - CORNER, frame.y1 - INSET)
    clears = [pymupdf.Rect(rect) & crop for rect in spec.get("clears", [])]
    for index in spec.get("bubbles", []):
        bubble = pymupdf.Rect(drawings[index]["rect"])
        clears.append(pymupdf.Rect(bubble.x0 - PAD, bubble.y0 - PAD, bubble.x1 + PAD, bubble.y1 + PAD) & crop)
    placed = []
    for line, (text, regions) in enumerate(spec["labels"]):
        members, box = [], None
        for region in regions:
            region = pymupdf.Rect(region)
            found = [i for i, d in enumerate(drawings) if _is_glyph(d, region)]
            if not found:
                raise ValueError(f"no outlined glyphs found for label {text!r} in {region}")
            members += found
            for index in found:
                rect = pymupdf.Rect(drawings[index]["rect"])
                box = rect if box is None else box | rect
            clears.append(pymupdf.Rect(region) & crop)
        placed.append({"line": line, "text": text, "glyph_indices": members,
                       "glyph_bbox_pt": _round(box), "cleared_pt": [_round(r) for r in regions],
                       "rect_pct": _round([(box.x0 - crop.x0) / crop.width * 100,
                                           (box.y0 - crop.y0) / crop.height * 100,
                                           box.width / crop.width * 100,
                                           box.height / crop.height * 100])})
    transforms = [{"op": "crop", "bbox_pt": _round(crop)}]
    if kind == "panel":
        ox, oy, limit = spec["origin"]
        for rect in clears:
            for tile in _tiles(rect, limit):
                dest = _round(tile)
                origin = _round((ox, oy, ox + dest[2] - dest[0], oy + dest[3] - dest[1]))
                transforms.append({"op": "copy_pdf_region", "bbox_pt": dest, "other_bbox_pt": origin})
    else:
        transforms += [{"op": "whiteout", "bbox_pt": _round(rect)} for rect in clears]
    return transforms, {"page": spec["page"], "kind": kind, "crop_pt": _round(crop),
                        "reason": spec["reason"], "lines": placed}


def asset(name: str, page: int, transforms: list) -> dict:
    return {
        "asset_key": f"web/js-100i/jp/ja/{name}", "page": page, "build_eligible": False,
        "scope": {"models": ["JS-100I"], "regions": ["JP"], "locales": ["ja"]},
        "text_policy": "fixed-product-markings", "visual_review_required": True,
        "transforms": transforms,
        "outputs": [{"format": "png", "path": f"assets/{name}.png", "scale": 4}],
        "gate": {"status": "quarantine", "reasons": ["Git-only JP candidate; no registry promotion"]},
        "risk_tags": ["region-locked-art"],
    }


def recipe(assets: list) -> dict:
    return {
        "schema_version": 1,
        "coordinate_contract": {"page_numbering": "pdf-1-based", "bbox_units": "pt",
                                "bbox_origin": "top-left", "bbox_space": "source-page"},
        "normalization": {
            "engine": "pymupdf", "validated_version": "1.28.0", "validated_mupdf_version": "1.29.0",
            "pdf_save": {"garbage": 4, "clean": True, "deflate": True, "no_new_id": True},
            "forbidden_pdf_markers": ["AIPrivateData", "PieceInfo", "AIMetaData"],
            "max_render_pixels": 40000000,
        },
        "source": {"source_key": SOURCE_KEY, "expected_sha256": SOURCE_SHA256, "expected_page_count": PAGES},
        "archive": {"pages": {"first": 1, "last": PAGES},
                    "pdf": {"path_pattern": "archive/pages/page-{page:04d}.pdf"},
                    "previews": {"path_pattern": "archive/previews/page-{page:04d}.png",
                                 "default_scale": 0.5, "page_scale": {}}},
        "page_catalog": [{"page": page, "page_key": f"jp-page-{page:02d}", "role": "manual_page", "locale": "ja",
                          "build_eligible": False,
                          "gate": {"status": "archive", "reasons": ["JP source provenance"]},
                          "risk_tags": []} for page in range(1, PAGES + 1)],
        "assets": assets,
    }


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if sha256_file(PDF) != SOURCE_SHA256:
        raise ValueError("original PDF identity changed")
    assets, labels = [], {}
    with pymupdf.open(PDF) as document:
        for spec in FIGURES:
            drawings = document[spec["page"] - 1].get_drawings()
            transforms, placed = figure(drawings, spec)
            assets.append(asset(spec["name"], spec["page"], transforms))
            labels[spec["name"]] = placed
    # Back-cover QR code with its rounded frame and quiet zone (p.12).
    assets.append(asset("contact_qr", 12, [{"op": "crop", "bbox_pt": [303.0, 453.0, 340.0, 490.0]}]))
    recipe_path = PACKAGE / "source" / "asset_recipe.json"
    recipe_path.write_text(json.dumps(recipe(assets), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (PACKAGE / "source" / "figure_labels.json").write_text(
        json.dumps({"schema_version": "js-100i-jp-figure-labels/v1", "figures": labels},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    target = PACKAGE / "assets"
    if target.exists():
        shutil.rmtree(target)
    target.mkdir()
    with tempfile.TemporaryDirectory() as scratch:
        output = Path(scratch) / "intake"
        run_intake(source_path=PDF, recipe=load_recipe(recipe_path), output_root=output)
        for item in assets:
            name = Path(item["outputs"][0]["path"]).name
            (produced,) = [p for p in output.rglob(name) if p.parent.name == "assets"]
            shutil.copyfile(produced, target / name)
    decisions = []
    for name, source, page, reason in REUSED:
        shutil.copyfile(ROOT / source, target / name)
        decisions.append({"asset": f"assets/{name}", "decision": "reuse", "jp_page": page,
                          "source_path": source, "sha256": sha256(ROOT / source), "evidence": reason})
    for spec in FIGURES:
        decisions.append({"asset": f"assets/{spec['name']}.png", "decision": "extract", "jp_page": spec["page"],
                          "reason": spec["reason"], "sha256": sha256(target / f"{spec['name']}.png")})
    decisions.append({"asset": "assets/contact_qr.png", "decision": "extract", "jp_page": 12,
                      "reason": "JP back-cover QR code; no shared asset encodes this target",
                      "sha256": sha256(target / "contact_qr.png")})
    (PACKAGE / "source" / "asset_decisions.json").write_text(
        json.dumps({"schema_version": "js-100i-jp-asset-decisions/v1", "assets": decisions},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps([d["asset"] for d in decisions], indent=2))


if __name__ == "__main__":
    main()
