"""Shared IDML constants + layout-parameter access (componentization P1).

The single read-path for data/layout_params.csv values: page geometry,
type sizes, and brand CMYK swatches all resolve through here so the IDML
side stays aligned with the PDF renderer's parameter source.
"""
from __future__ import annotations

from pathlib import Path

try:
    from tools.render_contract import load_layout_token_layers
except ModuleNotFoundError:  # direct tools/export_idml.py execution
    from render_contract import load_layout_token_layers  # type: ignore

MIMETYPE = "application/vnd.adobe.indesign-idml-package"
IDPKG = "http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging"

MM_TO_PT = 72.0 / 25.4


def load_layout_params(
    csv_path: Path,
    overlay_csvs: tuple[Path, ...] = (),
) -> dict[str, tuple[str, str]]:
    """key -> (value, unit)"""
    return {
        key: (token.value, token.unit)
        for key, token in load_layout_token_layers(csv_path, overlay_csvs).items()
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


def param_text(
    params: dict[str, tuple[str, str]],
    key: str,
    default: str,
) -> str:
    """Resolve one non-numeric IDML style token from the shared parameter map."""
    value, _unit = params.get(key, ("", ""))
    normalized = str(value).strip()
    return normalized or default


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


def localized_param_pt(
    params: dict[str, tuple[str, str]],
    key: str,
    default: float,
    *,
    language: str | None,
) -> float:
    """Language override of a pt token; the base value otherwise.

    The one implementation of the ``lang_<code>_<key>`` cascade the IDML
    components previously re-derived each for themselves, with gates that
    disagreed ({"fr","es"} literals beside ``governed_languages()`` — survey
    D3). The gate is ``layout_override_languages()``: governed languages plus
    lines in active layout tuning. Registering a language does not opt it in,
    and an honored language with no override row simply keeps the base value —
    override tokens are additive, never contract-required here.
    """
    from .language_contract import layout_override_languages

    base = param_pt(params, key, default)
    code = (language or "").split("-", 1)[0].strip().casefold()
    if code and code in layout_override_languages():
        return param_pt(params, f"lang_{code}_{key}", base)
    return base


def localized_component_param_pt(
    params: dict[str, tuple[str, str]],
    key: str,
    default: float,
    *,
    language: str | None,
    strict: bool,
    owner: str,
    contract_languages: frozenset[str] = frozenset(),
) -> float:
    """``localized_param_pt`` with component fail-closed semantics.

    The base token keeps the caller's strictness — an approved component's
    required token stays contract-checked. The override lookup is strict only
    for ``contract_languages``: the languages whose approved reference
    geometry *lives in* the ``lang_<code>_`` rows, so losing or corrupting one
    of those rows must fail the approved contract rather than silently render
    the base geometry. For every other honored language a missing override
    row means "no override yet", which is what lets a language in layout
    tuning build before its rows exist.
    """
    from .language_contract import layout_override_languages

    base = component_param_pt(params, key, default, strict=strict, owner=owner)
    code = (language or "").split("-", 1)[0].strip().casefold()
    if code and code in layout_override_languages():
        return component_param_pt(
            params,
            f"lang_{code}_{key}",
            base,
            strict=strict and code in contract_languages,
            owner=owner,
        )
    return base


def brand_cmyk(params: dict[str, tuple[str, str]], key: str, default: str) -> tuple[float, float, float, float]:
    value, unit = params.get(key, (default, "cmyk"))
    parts = [p.strip() for p in (value or default).split(",")]
    try:
        c, m, y, k = (float(p) for p in parts)
    except (ValueError, TypeError):
        c, m, y, k = 0.0, 0.0, 0.0, 1.0
    return c * 100, m * 100, y * 100, k * 100
