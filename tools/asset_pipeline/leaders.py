"""Suppress callout leaders in a master page so the artwork beneath survives.

The master draws every callout leader twice — a wide white halo under a thin
dark line — and both sit *above* the device artwork. That halo is what erases
the vent grille and the panel divider wherever a leader crosses them, so
painting the leader out can never restore what the halo hid. The earlier recipes
tried anyway, with ``whiteout`` blocks up to 77x40pt, and punched visible holes
through the product drawing.

Removing the leader's own strokes instead lets the artwork underneath render
normally. The strokes are identified structurally, never by coordinates baked
into a recipe: a leader is an axis-aligned polyline stroked twice at the halo
and line widths, so the pair is the signature. Their paint operator is replaced
with ``n`` (end path, paint nothing), which leaves every byte of geometry and
every other object untouched.

Two traps worth keeping in mind here:

* a perfectly horizontal or vertical line has a zero-area bounding box, and
  ``fitz.Rect.intersects`` reports False for those — overlap has to be tested
  by hand or every single-segment leader goes undetected;
* the content stream stores local coordinates under ``cm`` transforms, so the
  walker has to track the CTM to compare geometry in page space.
"""
from __future__ import annotations

import re
from typing import Any

HALO_WIDTH = 1.821
LINE_WIDTH = 0.30
WIDTH_TOLERANCE = 0.03
GEOMETRY_TOLERANCE = 0.6

_NUMBER = re.compile(rb"^[-+]?(?:\d+\.?\d*|\.\d+)$")
_STROKE_OPS = (b"S", b"s")
_PATH_END_OPS = (b"f", b"F", b"f*", b"B", b"B*", b"b", b"b*", b"n")


def _tokens(data: bytes):
    for match in re.finditer(rb"\S+", data):
        yield match.group(0), match.start(), match.end()


def _overlaps(rect: Any, bbox: tuple[float, float, float, float], margin: float) -> bool:
    """Zero-area-safe overlap test (a straight line has an empty rect)."""
    return (
        rect.x1 >= bbox[0] - margin
        and rect.x0 <= bbox[2] + margin
        and rect.y1 >= bbox[1] - margin
        and rect.y0 <= bbox[3] + margin
    )


def find_leader_geometries(
    fitz: Any,
    page: Any,
    bbox: tuple[float, float, float, float],
    *,
    margin: float = 0.5,
    halo_width: float = HALO_WIDTH,
    line_width: float = LINE_WIDTH,
    width_tolerance: float = WIDTH_TOLERANCE,
) -> tuple[tuple[tuple[float, float, float, float], ...], ...]:
    """Axis-aligned polylines stroked at both the halo and the line width.

    The widths are per-master, not universal: the JE-1000F US master draws
    1.821pt halo + 0.30pt stroke (the module defaults), the HTP017 master draws
    2.00pt + 0.202pt. Hardcoding them meant the operator silently matched
    nothing on a second master, so they are parameters with the original values
    as defaults — existing recipes keep byte-identical behaviour.
    """
    groups: dict[tuple, list[float]] = {}
    for drawing in page.get_drawings():
        items = drawing["items"]
        if not items or any(item[0] != "l" for item in items):
            continue
        width = drawing.get("width")
        if width is None:
            continue
        if not _overlaps(drawing["rect"], bbox, margin):
            continue
        segments = tuple(
            (
                round(item[1].x, 2),
                round(item[1].y, 2),
                round(item[2].x, 2),
                round(item[2].y, 2),
            )
            for item in items
        )
        groups.setdefault(segments, []).append(width)

    leaders: list[tuple[tuple[float, float, float, float], ...]] = []
    for segments, widths in groups.items():
        has_halo = any(abs(w - halo_width) < width_tolerance for w in widths)
        has_line = any(abs(w - line_width) < width_tolerance for w in widths)
        if not (has_halo and has_line):
            continue
        if not all(
            abs(x0 - x1) < 0.05 or abs(y0 - y1) < 0.05 for x0, y0, x1, y1 in segments
        ):
            continue
        leaders.append(segments)
    return tuple(sorted(leaders))


def suppress_leader_strokes(
    fitz: Any,
    document: Any,
    page: Any,
    leaders: tuple[tuple[tuple[float, float, float, float], ...], ...],
) -> int:
    """Turn each leader's paint operator into a no-op. Returns strokes changed."""
    if not leaders:
        return 0
    height = page.rect.height
    suppressed = 0
    for xref in page.get_contents():
        data = document.xref_stream(xref)
        out = bytearray(data)
        changed = False
        ctm = fitz.Matrix(1, 0, 0, 1, 0, 0)
        stack: list[Any] = []
        operands: list[bytes] = []
        points: list[Any] = []
        segments: list[tuple[float, float, float, float]] = []

        for token, start, end in _tokens(data):
            if _NUMBER.match(token):
                operands.append(token)
                continue
            numbers = [float(value) for value in operands]
            if token == b"q":
                stack.append(fitz.Matrix(ctm))
            elif token == b"Q":
                if stack:
                    ctm = stack.pop()
            elif token == b"cm" and len(numbers) == 6:
                ctm = fitz.Matrix(*numbers) * ctm
            elif token == b"m" and len(numbers) == 2:
                points = [_map(fitz, numbers, ctm, height)]
                segments = []
            elif token == b"l" and len(numbers) == 2 and points:
                previous = points[-1]
                points.append(_map(fitz, numbers, ctm, height))
                segments.append(
                    (previous.x, previous.y, points[-1].x, points[-1].y)
                )
            elif token in _STROKE_OPS:
                if segments and _is_leader(segments, leaders):
                    out[start:end] = b"n" + b" " * (end - start - 1)
                    suppressed += 1
                    changed = True
                points, segments = [], []
            elif token in _PATH_END_OPS:
                points, segments = [], []
            operands = []

        if changed:
            document.update_stream(xref, bytes(out))
    return suppressed


def _map(fitz: Any, numbers: list[float], ctm: Any, height: float) -> Any:
    mapped = fitz.Point(numbers[0], numbers[1]) * ctm
    return fitz.Point(mapped.x, height - mapped.y)


def _is_leader(segments: list, leaders: tuple) -> bool:
    seen = [
        (round(a, 1), round(b, 1), round(c, 1), round(d, 1)) for a, b, c, d in segments
    ]
    return any(_same_polyline(seen, list(leader)) for leader in leaders)


def _same_polyline(seen: list, target: list) -> bool:
    if len(seen) != len(target):
        return False
    remaining = list(target)
    for a, b, c, d in seen:
        for index, (e, f, g, h) in enumerate(remaining):
            forward = (
                abs(a - e) <= GEOMETRY_TOLERANCE
                and abs(b - f) <= GEOMETRY_TOLERANCE
                and abs(c - g) <= GEOMETRY_TOLERANCE
                and abs(d - h) <= GEOMETRY_TOLERANCE
            )
            reverse = (
                abs(a - g) <= GEOMETRY_TOLERANCE
                and abs(b - h) <= GEOMETRY_TOLERANCE
                and abs(c - e) <= GEOMETRY_TOLERANCE
                and abs(d - f) <= GEOMETRY_TOLERANCE
            )
            if forward or reverse:
                remaining.pop(index)
                break
        else:
            return False
    return True
