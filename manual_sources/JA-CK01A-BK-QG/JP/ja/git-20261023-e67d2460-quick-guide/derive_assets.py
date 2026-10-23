"""Derive this package's Web artwork from the archived quick-guide PDF.

Run from the repository root (PyMuPDF 1.28.0 / MuPDF 1.29.0, ``requirements.lock``)::

    python manual_sources/JA-CK01A-BK-QG/JP/ja/git-20261023-e67d2460-quick-guide/derive_assets.py

The PDF is a single print artboard whose type is fully outlined (no text
layer). Every figure is a clip of that artboard in source-page points. Live
copy that the Web page sets as text (step headings, the step 4 warning box,
App step captions) is painted out with the surrounding paper colour before
the clip is trimmed to its drawn content; nothing else in the art is altered.
The warning triangle is rebuilt from its original vector paths. The recipe
and the resulting hashes are written to ``source/asset_decisions.json``; a
second run leaves the tree unchanged.
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
PDF_SHA256 = "e67d2460eff018f0f8cae0be53e404604d1d3bff620d3c69c8cd8396ccce3d7a"
PYMUPDF = ("1.28.0", "1.29.0")
ZOOM = 3.0
WHITE = (255, 255, 255)
CONTENT_THRESHOLD = 250
TRIM_PAD_PX = 6
UNTRIMMED = {"app-download-qr.png", "app-store-badges.png", "app-settings-1.png", "app-settings-2.png",
             "step2-backup.png"}
# Art allowed to touch its clip: the room perspective of the site panel is
# drawn up to its frame, and the 2-① wiring's dashed pointer runs on into the
# switching detail beside it.
REACHES_FRAME = {"site-space.png", "step2-port-a.png", "step2-port-a-switch.png"}

# Figure panels are the dashed print frames, found by drawing index and
# clipped PANEL_INSET pt inside the dotted stroke; whatever lies outside the
# frame's own rounded outline (the grey page at its corners) is painted out.
# Packing-list items are explicit clips.
PANEL_INSET = 2.0
FRAME_BAND = 6.0
PANELS = {
    "site": 62, "1-1": 57, "1-2": 58, "1-3": 59, "2-1": 55, "2-2": 54,
    "3-1": 65, "3-2": 60, "3-3": 30, "4": 18463,
}
# Step headings are set live: their outlined glyphs (the heading grey and the
# white counters of the step numeral) are painted out up to this x, within
# the top HEADING_BAND pt of the panel.
HEADING_FILLS = {(0.252, 0.25, 0.256), (1.0, 1.0, 1.0)}
HEADING_BAND = 48.0
HEADINGS = {
    "1-1": 512.0, "1-2": 552.0, "1-3": 513.0, "2-1": 1066.0, "2-2": 1027.0,
    "3-1": 1636.0, "3-2": 1713.0, "3-3": 2120.0,
}

# (asset, panel key or explicit clip rect, painted-out rects, role). Rects are
# source-page points, origin top-left; painted-out rects only ever cover copy
# the Web page sets live or a print-only page-turn marker.
CROPS: list[tuple[str, object, list[tuple[float, ...]], str]] = [
    ("site-space.png", "site", [
        (903.0, 678.5, 928.5, 687.6), (1016.3, 679.2, 1120.6, 688.5),
        (917.6, 966.7, 948.5, 975.2), (1155.3, 966.7, 1186.1, 975.2),
    ], "サイトスペース要件 complete panel; four labels set live"),
    ("pack-panel.png", (1376, 646, 1470, 717), [], "パッキングリスト1 item"),
    ("pack-handle.png", (1498, 646, 1526, 717), [], "パッキングリスト1 item"),
    ("pack-install-manual.png", (1566, 652, 1612, 717), [], "パッキングリスト1 item"),
    ("pack-label-sheet.png", (1650, 652, 1702, 717), [], "パッキングリスト1 item"),
    ("pack-screw.png", (1730, 652, 1760, 717), [], "パッキングリスト1 item"),
    ("pack-inlet-box.png", (1390, 772, 1434, 833), [], "パッキングリスト2 item"),
    ("pack-charge-cable.png", (1462, 772, 1518, 833), [], "パッキングリスト2 item"),
    ("pack-cable-hanger.png", (1538, 762, 1572, 833), [], "パッキングリスト2 item"),
    ("pack-user-manual.png", (1602, 772, 1648, 833), [], "パッキングリスト2 item"),
    ("pack-quick-guide.png", (1666, 772, 1712, 833), [], "パッキングリスト2 item"),
    ("pack-anchor-bolt.png", (1742, 772, 1772, 833), [], "パッキングリスト2 item"),
    ("need-conduit.png", (1378, 912, 1480, 977), [], "必要品 item"),
    ("need-outlet.png", (1497, 912, 1558, 977), [], "必要品 item"),
    ("need-wire.png", (1597, 912, 1643, 977), [], "必要品 item"),
    ("need-breaker.png", (1700, 908, 1772, 977), [], "必要品 item"),
    ("step1-open.png", "1-1", [], "1-① panel"),
    ("step1-front-panel.png", "1-2", [], "1-② panel"),
    ("step1-wall.png", "1-3", [], "1-③ panel"),
    ("step2-port-a-legend.png", (803, 1215, 877.5, 1296), [], "2-① wire legend"),
    ("step2-port-a.png", (877.5, 1150, 1260, 1307.0), [], "2-① wiring; dashed pointer runs on into the detail"),
    ("step2-port-a-switch.png", (1260, 1126, 1386, 1307.0), [], "2-① switching detail with its printed notes"),
    ("step2-backup-legend.png", (801, 1462, 858, 1510), [], "2-② wire legend"),
    ("step2-backup.png", (858, 1366, 1384, 1518.0), [
        (1216.9, 1370.1, 1336.5, 1390.5), (1288.0, 1390.5, 1299.0, 1399.0),
        (1043.3, 1503.7, 1088.8, 1517.2),
    ], "2-② wiring; note box, its pointer and the circuit pill set live"),
    ("step3-inlet.png", "3-1", [], "3-① panel"),
    ("step3-port-b.png", "3-2", [(1760, 1476, 1800, 1523)], "3-② panel; page-turn marker removed"),
    ("step3-battery.png", "3-3", [], "3-③ panel"),
    ("step4-charge.png", "4", [(2673.6, 815.4, 2863.1, 856.8)], "4 panel; warning box set live"),
    ("app-store-badges.png", (2001.89, 1262.6, 2081.14, 1321.71), [], "5-① store badges; clip is the placed raster (xref 4201)"),
    ("app-download-qr.png", (1996.57, 1322.6, 2154.64, 1480.68), [], "5-① QR raster (xref 4202) with 10 pt of its printed white margin"),
    ("app-settings-1.png", (2232, 1186, 2752, 1495), [
        (2263.6, 1200.1, 2330.8, 1216.3), (2424.1, 1200.1, 2549.0, 1216.3),
        (2625.4, 1200.1, 2729.0, 1216.3),
    ], "5-② screens 1–3; step-caption pills set live"),
    ("app-settings-2.png", (2786, 1186, 3305, 1495), [
        (2793.1, 1190.3, 2947.4, 1222.5), (3026.6, 1200.1, 3101.4, 1216.3),
        (3222.0, 1200.1, 3270.8, 1216.3),
    ], "5-② screens 4–6; step-caption pills set live"),
]

# The step 4 and step 5 boxes print the same glyph at two sizes.
TRIANGLE_SVG = "warning-triangle-yellow.svg"
TRIANGLE_PATHS = {
    39232: (0.9259632229804993, 0.9135729074478149, 0.3044785261154175),
    39233: (0.13669031858444214, 0.12195010483264923, 0.1252918243408203),
    39234: (0.2518501579761505, 0.24951553344726562, 0.2560158669948578),
    39236: (0.2518501579761505, 0.24951553344726562, 0.2560158669948578),
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def check_source() -> fitz.Page:
    if (fitz.VersionBind, fitz.VersionFitz) != PYMUPDF:
        raise SystemExit(f"PyMuPDF {PYMUPDF} required, found {fitz.VersionBind}/{fitz.VersionFitz}")
    if sha256_bytes(PDF.read_bytes()) != PDF_SHA256:
        raise SystemExit("source/original.pdf is not the archived quick guide")
    document = fitz.open(PDF)
    if document.page_count != 1:
        raise SystemExit("the quick guide artboard must be a single page")
    return document[0]


def trimmed(image: Image.Image, reaches_frame: bool = False) -> tuple[Image.Image, list[int]]:
    gray = image.convert("L").point(lambda value: 255 if value < CONTENT_THRESHOLD else 0)
    box = gray.getbbox()
    if box is None:
        raise SystemExit("clip holds no drawn content")
    left, top, right, bottom = box
    if not reaches_frame and (left == 0 or top == 0 or right == image.width or bottom == image.height):
        raise SystemExit(f"drawn content reaches the clip edge {box}: the clip would cut the art")
    box = [max(0, left - TRIM_PAD_PX), max(0, top - TRIM_PAD_PX),
           min(image.width, right + TRIM_PAD_PX), min(image.height, bottom + TRIM_PAD_PX)]
    return image.crop(box), box


def clip_rect(drawings: list[dict], where: object) -> fitz.Rect:
    if isinstance(where, str):
        frame = drawings[PANELS[where]]
        if frame.get("type") != "fs" or tuple(frame.get("fill") or ()) != (1.0, 1.0, 1.0):
            raise SystemExit(f"drawing {PANELS[where]} is not the dashed {where} panel")
        return fitz.Rect(frame["rect"]) + (PANEL_INSET, PANEL_INSET, -PANEL_INSET, -PANEL_INSET)
    return fitz.Rect(where)


def outside_frame(page: fitz.Page, frame: dict, clip: fitz.Rect) -> Image.Image:
    """Mask (L mode, 255 = outside) of the frame's rounded outline over the clip."""
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
    # The dotted stroke straddles the outline; its band is masked with the outside.
    shape.finish(fill=(0, 0, 0), color=(1, 1, 1), width=FRAME_BAND, closePath=True)
    shape.commit()
    pixmap = sheet.get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM), clip=clip, alpha=False,
                              colorspace=fitz.csGRAY)
    return Image.frombytes("L", (pixmap.width, pixmap.height), pixmap.samples).point(
        lambda value: 255 if value > 127 else 0)


def heading_glyphs(drawings: list[dict], where: object) -> list[tuple[int, fitz.Rect]]:
    if where not in HEADINGS:
        return []
    frame = fitz.Rect(drawings[PANELS[where]]["rect"])
    band = fitz.Rect(frame.x0, frame.y0, HEADINGS[where], frame.y0 + HEADING_BAND)
    glyphs = []
    for index, drawing in enumerate(drawings):
        colour = tuple(round(value, 3) for value in (drawing.get("fill") or drawing.get("color") or ()))
        if index != PANELS[where] and colour in HEADING_FILLS and drawing["rect"] in band:
            glyphs.append((index, fitz.Rect(drawing["rect"]) + (-0.6, -0.6, 0.6, 0.6)))
    if not glyphs:
        raise SystemExit(f"no heading glyphs found in panel {where}")
    return glyphs


def render_crop(page: fitz.Page, clip: fitz.Rect, masks: list[fitz.Rect], trim: bool,
                outside: Image.Image | None = None, reaches_frame: bool = False) -> tuple[bytes, list[int]]:
    pixmap = page.get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM), clip=clip, alpha=False)
    image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
    if outside is not None:
        if outside.size != image.size:
            raise SystemExit("frame mask does not match the clip")
        image.paste(WHITE, (0, 0, image.width, image.height), outside)
    for mask in masks:
        x0, y0 = (mask.x0 - clip.x0) * ZOOM, (mask.y0 - clip.y0) * ZOOM
        x1, y1 = (mask.x1 - clip.x0) * ZOOM, (mask.y1 - clip.y0) * ZOOM
        image.paste(WHITE, (max(0, round(x0)), max(0, round(y0)), round(x1), round(y1)))
    box = [0, 0, image.width, image.height]
    if trim:
        image, box = trimmed(image, reaches_frame)
    stream = io.BytesIO()
    image.save(stream, format="PNG", optimize=True)
    return stream.getvalue(), box


def _svg_path(items: list[tuple]) -> str:
    parts: list[str] = []
    cursor = None

    def point(value: fitz.Point) -> str:
        return f"{value.x:.3f} {value.y:.3f}"

    for item in items:
        kind = item[0]
        if kind == "l":
            start, end = item[1], item[2]
            if cursor != start:
                parts.append(f"M{point(start)}")
            parts.append(f"L{point(end)}")
            cursor = end
        elif kind == "c":
            start, c1, c2, end = item[1:5]
            if cursor != start:
                parts.append(f"M{point(start)}")
            parts.append(f"C{point(c1)} {point(c2)} {point(end)}")
            cursor = end
        else:
            raise SystemExit(f"unexpected path operator {kind!r} in the warning triangle")
    return " ".join(parts) + " Z"


def triangle_svg(page: fitz.Page) -> bytes:
    drawings = page.get_drawings()
    paths = []
    bounds = fitz.Rect()
    for index, fill in TRIANGLE_PATHS.items():
        drawing = drawings[index]
        if drawing.get("type") != "f" or tuple(drawing.get("fill") or ()) != fill:
            raise SystemExit(f"drawing {index} is not the archived warning-triangle path")
        bounds |= drawing["rect"]
        rgb = "".join(f"{round(channel * 255):02x}" for channel in fill)
        rule = ' fill-rule="evenodd"' if drawing.get("even_odd") else ""
        paths.append(f'<path fill="#{rgb}"{rule} d="{_svg_path(drawing["items"])}"/>')
    view = f"{bounds.x0:.3f} {bounds.y0:.3f} {bounds.width:.3f} {bounds.height:.3f}"
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" '
        f'width="{bounds.width:.3f}" height="{bounds.height:.3f}" viewBox="{view}">\n'
        + "\n".join(paths)
        + "\n</svg>\n"
    )
    return svg.encode("utf-8")


def main() -> None:
    page = check_source()
    ASSETS.mkdir(exist_ok=True)
    drawings = page.get_drawings()
    records = []
    for name, where, extra, role in CROPS:
        clip = clip_rect(drawings, where)
        glyphs = heading_glyphs(drawings, where)
        masks = [rect for _index, rect in glyphs] + [fitz.Rect(rect) for rect in extra]
        outside = outside_frame(page, drawings[PANELS[where]], clip) if isinstance(where, str) else None
        try:
            data, box = render_crop(page, clip, masks, trim=name not in UNTRIMMED, outside=outside,
                                    reaches_frame=name in REACHES_FRAME)
        except SystemExit as error:
            raise SystemExit(f"{name}: {error}") from None
        (ASSETS / name).write_bytes(data)
        record = {
            "path": f"assets/{name}", "role": role, "decision": "new extraction",
            "source_page": 1, "clip_pt": [round(value, 3) for value in clip],
        }
        if isinstance(where, str):
            record["panel_drawing_index"] = PANELS[where]
        if glyphs:
            record["heading_glyph_drawing_indices"] = [index for index, _rect in glyphs]
        if extra:
            record["painted_out_pt"] = [list(rect) for rect in extra]
        record.update(zoom=ZOOM, trim_px=box, sha256=sha256_bytes(data))
        records.append(record)
    svg = triangle_svg(page)
    (ASSETS / TRIANGLE_SVG).write_bytes(svg)
    records.append({
        "path": f"assets/{TRIANGLE_SVG}", "role": "warning glyph of the step 4 and step 5 boxes",
        "decision": "new extraction (original vectors)", "source_page": 1,
        "drawing_indices": sorted(TRIANGLE_PATHS), "sha256": sha256_bytes(svg),
    })
    payload = json.loads(DECISIONS.read_text(encoding="utf-8")) if DECISIONS.exists() else {}
    payload["extractions"] = records
    DECISIONS.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(records)} assets written")


if __name__ == "__main__":
    main()
