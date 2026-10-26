"""Derive this package's Web artwork from the archived connection-guide PDF.

Run from the repository root (PyMuPDF 1.28.0 / MuPDF 1.29.0, ``requirements.lock``)::

    python manual_sources/JS-CONNECTION-GUIDE/JP/ja/git-20261026-bc35fd65-connection-guide/derive_assets.py

The PDF is a single production artboard whose type is fully outlined (no text
layer). Only the Japanese face is on the Web. Its two connection figures are
clips of their print table cells in source-page points; the Japanese labels
the Web page sets live (the two speech bubbles and the two port captions) are
painted out with the paper colour, found by drawing index, before the clip is
trimmed to its drawn content and the label rectangles. Connector tags
(DC7909 / DC8020), the numbered markers and 「または」 between the two
alternatives stay in the art. The three DC入力 port icons are rebuilt
from their placed rasters (with the soft mask where the PDF has one) and the
orange dimension marks of the two DC ports; their labels are table text. The
recipe, the resulting hashes and the live-label rectangles are written to
``source/asset_decisions.json``; a second run leaves the tree unchanged.
"""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path

import fitz
from PIL import Image

PACKAGE = Path(__file__).resolve().parent
PDF = PACKAGE / "source" / "original.pdf"
ASSETS = PACKAGE / "assets"
DECISIONS = PACKAGE / "source" / "asset_decisions.json"
PDF_SHA256 = "bc35fd6518769bd26c88fee088cc3a748c0ef680f4419682bede0f62738f8821"
PYMUPDF = ("1.28.0", "1.29.0")
ZOOM = 4.0
WHITE = (255, 255, 255)
CONTENT_THRESHOLD = 250
TRIM_PAD_PX = 8
GLYPH_PAD = 0.6
TEXT_GREY = (0.244, 0.234, 0.235)

# Japanese face, right-hand column of the print table: one cell per connector
# row, bounded by drawing 857 (table top), 856 (row divider) and the frame 30.
CELL_INSET = 2.0
# The table's rounded outer frame (drawing 30) bends into the last cell's
# bottom-right corner; its stroke band is painted out with the paper colour.
TABLE_FRAME = 30
FRAME_BAND = 3.0
FIGURES = {
    "connection-dc7909.png": {
        "cell": (1413.7, 455.8, 1858.4, 651.1),
        "bubble": 839,
        "labels": [
            ("黒のプラスチック", "bubble", None),
            ("DC7909（メスコネクタ）", "glyphs", (1465.0, 617.0, 1550.0, 632.0)),
        ],
        "role": "DC7909 connection figure (black plastic tip); Japanese labels set live",
    },
    "connection-dc8020.png": {
        "cell": (1413.7, 651.1, 1858.4, 837.8),
        "bubble": 767,
        "labels": [
            ("ロック溝", "bubble", None),
            ("DC8020（メスコネクタ）", "glyphs", (1465.0, 806.0, 1550.0, 821.0)),
        ],
        "role": "DC8020 connection figure (locking groove); Japanese labels set live",
    },
}

# DC入力 port icons: placed raster xref, its placement on the Japanese face,
# and the drawing indices of the orange dimension marks drawn over it.
PORTS = {
    "port-usb-c.png": (346, (1357.3, 495.5, 1400.4, 538.5), []),
    "port-dc7909.png": (348, (1357.4, 594.6, 1400.5, 637.8), list(range(3517, 3525))),
    "port-dc8020.png": (347, (1357.9, 700.5, 1399.4, 742.0), list(range(3504, 3512))),
}
PORT_MARK_COLOUR = (0.878, 0.337, 0.18)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def check_source() -> fitz.Page:
    if (fitz.VersionBind, fitz.VersionFitz) != PYMUPDF:
        raise SystemExit(f"PyMuPDF {PYMUPDF} required, found {fitz.VersionBind}/{fitz.VersionFitz}")
    if sha256_bytes(PDF.read_bytes()) != PDF_SHA256:
        raise SystemExit("source/original.pdf is not the archived connection guide")
    document = fitz.open(PDF)
    if document.page_count != 1:
        raise SystemExit("the connection guide artboard must be a single page")
    return document[0]


def png(image: Image.Image) -> bytes:
    stream = io.BytesIO()
    image.save(stream, format="PNG", optimize=True)
    return stream.getvalue()


def glyphs(drawings: list[dict], box: tuple[float, ...]) -> list[tuple[int, fitz.Rect]]:
    """Outlined text glyphs (text grey, small) lying wholly inside ``box``."""
    found = []
    for index, drawing in enumerate(drawings):
        colour = tuple(round(value, 3) for value in (drawing.get("fill") or ()))
        rect = fitz.Rect(drawing["rect"])
        if drawing["type"] == "f" and colour == TEXT_GREY and rect in fitz.Rect(box) and rect.width < 20:
            found.append((index, rect))
    if not found:
        raise SystemExit(f"no label glyphs inside {box}")
    return found


def bubble(drawings: list[dict], index: int) -> fitz.Rect:
    drawing = drawings[index]
    if drawing.get("type") != "fs" or tuple(round(v, 3) for v in drawing.get("fill") or ()) != (0.886, 0.89, 0.895):
        raise SystemExit(f"drawing {index} is not a grey speech bubble")
    half = (drawing.get("width") or 0) / 2 + 0.2
    return fitz.Rect(drawing["rect"]) + (-half, -half, half, half)


def trimmed(image: Image.Image, keep: list[tuple[int, int, int, int]]) -> tuple[Image.Image, list[int]]:
    """Trim to the drawn content plus the ``keep`` boxes (where live labels are set)."""
    gray = image.convert("L").point(lambda value: 255 if value < CONTENT_THRESHOLD else 0)
    box = gray.getbbox()
    if box is None:
        raise SystemExit("clip holds no drawn content")
    left, top, right, bottom = box
    for x0, y0, x1, y1 in keep:
        left, top, right, bottom = min(left, x0), min(top, y0), max(right, x1), max(bottom, y1)
    if left == 0 or top == 0 or right == image.width or bottom == image.height:
        raise SystemExit(f"drawn content reaches the clip edge {box}: the clip would cut the art")
    box = [left - TRIM_PAD_PX, top - TRIM_PAD_PX, right + TRIM_PAD_PX, bottom + TRIM_PAD_PX]
    return image.crop(box), box


def frame_band(page: fitz.Page, frame: dict, clip: fitz.Rect) -> Image.Image:
    """Mask (L mode, 255 = stroke band) of the table frame over the clip."""
    scratch = fitz.open()
    sheet = scratch.new_page(width=page.rect.width, height=page.rect.height)
    shape = sheet.new_shape()
    for item in frame["items"]:
        if item[0] == "l":
            shape.draw_line(item[1], item[2])
        elif item[0] == "c":
            shape.draw_bezier(*item[1:5])
        else:
            raise SystemExit(f"unexpected frame path operator {item[0]!r}")
    shape.finish(color=(0, 0, 0), width=FRAME_BAND, closePath=True)
    shape.commit()
    pixmap = sheet.get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM), clip=clip, alpha=False, colorspace=fitz.csGRAY)
    return Image.frombytes("L", (pixmap.width, pixmap.height), pixmap.samples).point(
        lambda value: 255 if value < 128 else 0)


def figure(page: fitz.Page, drawings: list[dict], spec: dict) -> tuple[bytes, dict]:
    clip = fitz.Rect(spec["cell"]) + (CELL_INSET, CELL_INSET, -CELL_INSET, -CELL_INSET)
    pixmap = page.get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM), clip=clip, alpha=False)
    image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
    frame = drawings[TABLE_FRAME]
    if frame.get("type") != "s" or fitz.Rect(frame["rect"]) != fitz.Rect(1155.380615234375, 410.2059020996094,
                                                                         1858.392578125, 837.7619018554688):
        raise SystemExit(f"drawing {TABLE_FRAME} is not the table frame")
    band = frame_band(page, frame, clip)
    if band.size != image.size:
        raise SystemExit("frame mask does not match the clip")
    image.paste(WHITE, (0, 0, image.width, image.height), band)
    labels, painted = [], []
    for text, kind, box in spec["labels"]:
        if kind == "bubble":
            rects = [bubble(drawings, spec["bubble"])]
            indices = [spec["bubble"]]
            span = rects[0]
        else:
            found = glyphs(drawings, box)
            indices = [index for index, _rect in found]
            rects = [rect + (-GLYPH_PAD, -GLYPH_PAD, GLYPH_PAD, GLYPH_PAD) for _index, rect in found]
            span = fitz.Rect()
            for _index, rect in found:
                span |= rect
        for rect in rects:
            x0, y0 = (rect.x0 - clip.x0) * ZOOM, (rect.y0 - clip.y0) * ZOOM
            x1, y1 = (rect.x1 - clip.x0) * ZOOM, (rect.y1 - clip.y0) * ZOOM
            image.paste(WHITE, (max(0, round(x0)), max(0, round(y0)), round(x1), round(y1)))
        labels.append({"text": text, "kind": kind, "drawing_indices": indices, "span_pt": span})
        painted += [[round(value, 3) for value in rect] for rect in rects]
    keep = [(round((label["span_pt"].x0 - clip.x0) * ZOOM), round((label["span_pt"].y0 - clip.y0) * ZOOM),
             round((label["span_pt"].x1 - clip.x0) * ZOOM), round((label["span_pt"].y1 - clip.y0) * ZOOM))
            for label in labels]
    image, box = trimmed(image, keep)
    for label in labels:
        span = label.pop("span_pt")
        x = ((span.x0 - clip.x0) * ZOOM - box[0]) / image.width * 100
        y = ((span.y0 - clip.y0) * ZOOM - box[1]) / image.height * 100
        label["span_pct"] = [round(x, 2), round(y, 2), round(span.width * ZOOM / image.width * 100, 2),
                             round(span.height * ZOOM / image.height * 100, 2)]
    return png(image), {"clip_pt": [round(value, 3) for value in clip], "trim_px": box,
                        "size_px": list(image.size), "painted_out_pt": painted, "live_labels": labels}


def port(document: fitz.Document, drawings: list[dict], xref: int, where: tuple[float, ...],
         marks: list[int]) -> bytes:
    """The placed port raster (soft mask applied) with its dimension marks, on transparency."""
    base = fitz.Pixmap(document, xref)
    smask = document.xref_get_key(xref, "SMask")
    if base.colorspace.n != 3:
        base = fitz.Pixmap(fitz.csRGB, base)
    if smask[0] == "xref":
        base = fitz.Pixmap(base, fitz.Pixmap(document, int(smask[1].split()[0])))
    rect = fitz.Rect(where)
    bounds = fitz.Rect(rect)
    for index in marks:
        drawing = drawings[index]
        if drawing.get("type") != "s" or tuple(round(v, 3) for v in drawing["color"]) != PORT_MARK_COLOUR:
            raise SystemExit(f"drawing {index} is not an orange dimension mark")
        bounds |= fitz.Rect(drawing["rect"]) + (-1, -1, 1, 1)
    scratch = fitz.open()
    sheet = scratch.new_page(width=document[0].rect.width, height=document[0].rect.height)
    sheet.insert_image(rect, pixmap=base)
    for index in marks:
        drawing = drawings[index]
        shape = sheet.new_shape()
        for item in drawing["items"]:
            if item[0] != "l":
                raise SystemExit(f"unexpected mark path operator {item[0]!r}")
            shape.draw_line(item[1], item[2])
        shape.finish(color=drawing["color"], width=drawing["width"], lineCap=drawing.get("lineCap", (0,))[0],
                     closePath=False)
        shape.commit()
    pixmap = sheet.get_pixmap(matrix=fitz.Matrix(ZOOM * 2, ZOOM * 2), clip=bounds, alpha=True)
    return png(Image.frombytes("RGBA", (pixmap.width, pixmap.height), pixmap.samples))


def main() -> None:
    page = check_source()
    document = page.parent
    drawings = page.get_drawings()
    ASSETS.mkdir(exist_ok=True)
    records = []
    for name, spec in FIGURES.items():
        data, detail = figure(page, drawings, spec)
        (ASSETS / name).write_bytes(data)
        records.append({"path": f"assets/{name}", "role": spec["role"], "decision": "new extraction",
                        "source_page": 1, "zoom": ZOOM, **detail, "sha256": sha256_bytes(data)})
    for name, (xref, where, marks) in PORTS.items():
        data = port(document, drawings, xref, where, marks)
        (ASSETS / name).write_bytes(data)
        records.append({"path": f"assets/{name}", "role": "DC入力 port icon; label set in the table",
                        "decision": "new extraction (placed raster" + (" + dimension-mark vectors)" if marks else ")"),
                        "source_page": 1, "raster_xref": xref, "placed_pt": list(where),
                        "dimension_mark_drawing_indices": marks, "zoom": ZOOM * 2, "sha256": sha256_bytes(data)})
    payload = json.loads(DECISIONS.read_text(encoding="utf-8")) if DECISIONS.exists() else {}
    payload["extractions"] = records
    DECISIONS.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(records)} assets written")


if __name__ == "__main__":
    main()
