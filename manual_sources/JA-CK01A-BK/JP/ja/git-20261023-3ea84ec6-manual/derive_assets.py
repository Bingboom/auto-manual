"""Derive the Web artwork of this package from the frozen Japanese PDF.

Run from the repository root (requirements.lock, PyMuPDF 1.28.0 / MuPDF 1.29.0):

    python manual_sources/JA-CK01A-BK/JP/ja/git-20261023-3ea84ec6-manual/derive_assets.py

The PDF is one Illustrator artboard holding the four printed panels; every
letter is outlined, so the page has no text layer. Each figure is the native
PDF crop of one numbered step frame, produced by the shared asset pipeline.
Vector replay is not used: it drops this master's clipping paths and dashes.
The crop sits just inside the decorative step frame; ``whiteout`` clears the
frame's rounded corners and the outlined label glyphs, which stay native HTML.
The step-5 speech bubble is cleared with its copy and rebuilt as a live label.
The grey note capsules lie outside the crops and are native copy. The script
writes ``source/asset_recipe.json`` and ``source/figure_labels.json`` and
refreshes ``assets/``; a second run leaves the tree unchanged.
"""
from __future__ import annotations

import json
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
SOURCE_SHA256 = "3ea84ec63b20a4e65c4d2f5d34a45ce715133b6b6f29a424bd95393d131cd113"
SOURCE_KEY = "source/ja-ck01a-bk-jp-38-0001-000777"

# Printed panels on the artboard (pt, top-left origin): physical order of the
# folded sheet is cover, safety/specs/step 1, steps 2-4, step 5/QR.
PANELS = {
    "cover": (801.5, 413.0, 1170.0, 937.4),
    "panel-2": (1267.3, 413.2, 1635.8, 937.6),
    "panel-3": (1635.8, 413.2, 2004.3, 937.6),
    "panel-4": (433.0, 413.0, 801.5, 937.4),
}
# Step frames (rounded, r = 8.2 pt) and the step-5 speech bubble, by drawing index.
FRAMES = {"step1-cover": 1584, "step2-mark": 1585, "step3-drill": 1588, "step4-fix": 1587,
          "step5-wiring": 1586}
BUBBLE = 1590
CORNER = 8.5
INSET = 1.2
PAD = 0.6

# (asset name, crop bottom override in pt, label lines: (text, glyph search region in pt))
FIGURES = [
    ("step1-cover", None, []),
    ("step2-mark", None, []),
    ("step3-drill", 704.5, []),   # the note capsule starts at 706.7 pt
    ("step4-fix", None, []),
    ("step5-wiring", 663.0, [     # the note capsules start at 666.5 pt
        ("各ワイヤから3/5インチ（15 mm）の絶縁体を剥がし。", (471.0, 485.0, 590.0, 498.0)),
        ("Green", (485.0, 516.0, 515.0, 524.8)),
        ("White", (485.0, 524.8, 515.0, 533.3)),
        ("Black", (485.0, 533.3, 515.0, 541.8)),
        ("Red", (485.0, 541.8, 515.0, 551.0)),
        ("Groud Screw Terminal", (644.0, 500.0, 676.0, 513.0)),
        ("Green", (644.0, 521.0, 662.0, 527.5)),
        ("Black", (644.0, 529.0, 662.0, 536.0)),
        ("White", (644.0, 542.0, 662.0, 548.5)),
        ("Red", (644.0, 551.5, 662.0, 558.0)),
    ]),
]
QR = ("contact-qr", (732.0, 871.0, 772.0, 911.0))


def _is_glyph(drawing: dict, region: pymupdf.Rect) -> bool:
    fill = drawing.get("fill")
    rect = pymupdf.Rect(drawing["rect"])
    return (drawing["type"] == "f" and fill is not None and max(fill) < 0.4
            and rect.height < 7.5 and region.contains(rect))


def _round(values) -> list[float]:
    return [round(float(v), 2) for v in values]


def figure(drawings: list[dict], name: str, bottom: float | None, labels: list) -> tuple[dict, dict | None]:
    frame = pymupdf.Rect(drawings[FRAMES[name]]["rect"])
    crop = pymupdf.Rect(frame.x0 + INSET, frame.y0 + INSET, frame.x1 - INSET,
                        (bottom if bottom is not None else frame.y1 - INSET))
    whiteouts = [
        (crop.x0, crop.y0, crop.x0 + CORNER, crop.y0 + CORNER),
        (crop.x1 - CORNER, crop.y0, crop.x1, crop.y0 + CORNER),
    ]
    if bottom is None:
        whiteouts += [(crop.x0, crop.y1 - CORNER, crop.x0 + CORNER, crop.y1),
                      (crop.x1 - CORNER, crop.y1 - CORNER, crop.x1, crop.y1)]
    placed = []
    for line, (text, region) in enumerate(labels):
        region = pymupdf.Rect(region)
        members = [i for i, d in enumerate(drawings) if _is_glyph(d, region)]
        if not members:
            raise ValueError(f"no outlined glyphs found for label {text!r}")
        box = pymupdf.Rect(drawings[members[0]]["rect"])
        for index in members[1:]:
            box |= pymupdf.Rect(drawings[index]["rect"])
        if line == 0:
            cleared = pymupdf.Rect(drawings[BUBBLE]["rect"])
            cleared = pymupdf.Rect(cleared.x0 - 1, cleared.y0 - 1, cleared.x1 + 1, cleared.y1 + 1)
        else:
            cleared = pymupdf.Rect(box.x0 - PAD, box.y0 - PAD, box.x1 + PAD, box.y1 + PAD)
        whiteouts.append(tuple(cleared))
        placed.append({"line": line, "text": text, "glyph_indices": members,
                       "glyph_bbox_pt": _round(box), "whiteout_pt": _round(cleared)})
    transforms = [{"op": "crop", "bbox_pt": _round(crop)}]
    transforms += [{"op": "whiteout", "bbox_pt": _round(rect)} for rect in whiteouts]
    return transforms, ({"crop_pt": _round(crop), "lines": placed} if placed else None)


def asset(name: str, transforms: list) -> dict:
    return {
        "asset_key": f"web/ja-ck01a-bk/jp/ja/{name}", "page": 1, "build_eligible": False,
        "scope": {"models": ["JA-CK01A-BK"], "regions": ["JP"], "locales": ["ja"]},
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
        "source": {"source_key": SOURCE_KEY, "expected_sha256": SOURCE_SHA256, "expected_page_count": 1},
        "archive": {"pages": {"first": 1, "last": 1},
                    "pdf": {"path_pattern": "archive/pages/page-{page:04d}.pdf"},
                    "previews": {"path_pattern": "archive/previews/page-{page:04d}.png",
                                 "default_scale": 0.5, "page_scale": {}}},
        "page_catalog": [{"page": 1, "page_key": "jp-artboard", "role": "source_artboard", "locale": "ja",
                          "build_eligible": False,
                          "gate": {"status": "archive", "reasons": ["JP source provenance; four printed panels"]},
                          "risk_tags": []}],
        "assets": assets,
    }


def main() -> None:
    if sha256_file(PDF) != SOURCE_SHA256:
        raise ValueError("original PDF identity changed")
    with pymupdf.open(PDF) as document:
        drawings = document[0].get_drawings()
    assets, labels = [], {}
    for name, bottom, label_spec in FIGURES:
        transforms, placed = figure(drawings, name, bottom, label_spec)
        assets.append(asset(name, transforms))
        if placed:
            labels[name] = placed
    assets.append(asset(QR[0], [{"op": "crop", "bbox_pt": list(QR[1])}]))
    recipe_path = PACKAGE / "source" / "asset_recipe.json"
    recipe_path.write_text(json.dumps(recipe(assets), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (PACKAGE / "source" / "figure_labels.json").write_text(
        json.dumps({"schema_version": "ja-ck01a-bk-figure-labels/v1", "panels": PANELS,
                    "frames": FRAMES, "figures": labels}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    with tempfile.TemporaryDirectory() as scratch:
        output = Path(scratch) / "intake"
        run_intake(source_path=PDF, recipe=load_recipe(recipe_path), output_root=output)
        target = PACKAGE / "assets"
        if target.exists():
            shutil.rmtree(target)
        target.mkdir()
        for item in assets:
            name = Path(item["outputs"][0]["path"]).name
            (produced,) = [p for p in output.rglob(name) if p.parent.name == "assets"]
            shutil.copyfile(produced, target / name)
    print(json.dumps([item["outputs"][0]["path"] for item in assets], indent=2))


if __name__ == "__main__":
    main()
