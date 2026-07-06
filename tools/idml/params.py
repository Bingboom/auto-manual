"""Shared IDML constants + layout-parameter access (componentization P1).

The single read-path for data/layout_params.csv values: page geometry,
type sizes, and brand CMYK swatches all resolve through here so the IDML
side stays aligned with the PDF renderer's parameter source.
"""
from __future__ import annotations

import csv
from pathlib import Path

MIMETYPE = "application/vnd.adobe.indesign-idml-package"
IDPKG = "http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging"

MM_TO_PT = 72.0 / 25.4


def load_layout_params(csv_path: Path) -> dict[str, tuple[str, str]]:
    """key -> (value, unit)"""
    out: dict[str, tuple[str, str]] = {}
    with csv_path.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            key = (row.get("key") or "").strip()
            if not key:
                continue
            out[key] = ((row.get("value") or "").strip(), (row.get("unit") or "").strip())
    return out


def param_pt(params: dict[str, tuple[str, str]], key: str, default: float) -> float:
    value, unit = params.get(key, ("", ""))
    if not value:
        return default
    try:
        v = float(value)
    except ValueError:
        return default
    if unit == "mm":
        return v * MM_TO_PT
    return v  # pt / em treated as pt at this level


def brand_cmyk(params: dict[str, tuple[str, str]], key: str, default: str) -> tuple[float, float, float, float]:
    value, unit = params.get(key, (default, "cmyk"))
    parts = [p.strip() for p in (value or default).split(",")]
    try:
        c, m, y, k = (float(p) for p in parts)
    except (ValueError, TypeError):
        c, m, y, k = 0.0, 0.0, 0.0, 1.0
    return c * 100, m * 100, y * 100, k * 100
