"""Shared IDML constants + layout-parameter access (componentization P1).

The single read-path for data/layout_params.csv values: page geometry,
type sizes, and brand CMYK swatches all resolve through here so the IDML
side stays aligned with the PDF renderer's parameter source.
"""
from __future__ import annotations

from pathlib import Path

try:
    from tools.render_contract import load_layout_tokens
except ModuleNotFoundError:  # direct tools/export_idml.py execution
    from render_contract import load_layout_tokens  # type: ignore

MIMETYPE = "application/vnd.adobe.indesign-idml-package"
IDPKG = "http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging"

MM_TO_PT = 72.0 / 25.4


def load_layout_params(csv_path: Path) -> dict[str, tuple[str, str]]:
    """key -> (value, unit)"""
    return {
        key: (token.value, token.unit)
        for key, token in load_layout_tokens(csv_path).items()
    }


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


def component_param_pt(
    params: dict[str, tuple[str, str]],
    key: str,
    default: float,
    *,
    strict: bool,
    owner: str,
) -> float:
    """Resolve one component token, failing closed for approved contracts."""
    if strict:
        raw = params.get(key)
        if raw is None or not str(raw[0]).strip():
            raise ValueError(
                f"approved {owner} style is missing required layout token: {key}"
            )
        try:
            float(raw[0])
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"approved {owner} style has a non-numeric layout token: {key}"
            ) from exc
    return param_pt(params, key, default)


def brand_cmyk(params: dict[str, tuple[str, str]], key: str, default: str) -> tuple[float, float, float, float]:
    value, unit = params.get(key, (default, "cmyk"))
    parts = [p.strip() for p in (value or default).split(",")]
    try:
        c, m, y, k = (float(p) for p in parts)
    except (ValueError, TypeError):
        c, m, y, k = 0.0, 0.0, 0.0, 1.0
    return c * 100, m * 100, y * 100, k * 100
