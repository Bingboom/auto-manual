"""Native-import-safe character metric overrides for IDML text runs."""
from __future__ import annotations

import re
import unicodedata

from .params import param_pt


def signal_label_metrics(
    params: dict[str, tuple[str, str]],
    lang: str,
    text: str,
    available_width: float,
) -> tuple[float, float, float]:
    """Return one-line signal-label size, leading, and horizontal scale."""
    language = (lang or "en").strip().casefold().replace("_", "-").split("-", 1)[0]
    base_signal_size = param_pt(params, "type_symbol_signal_font_size", 9.9)
    signal_size = base_signal_size
    body_size = param_pt(params, "type_symbol_body_font_size", 5.6)
    # The FR/ES reference artwork uses the compact symbol-body density for
    # signal words; long words receive a final width fit below.
    if language in {"fr", "es"}:
        signal_size = min(signal_size, body_size)
    signal_leading = param_pt(params, "type_symbol_signal_font_leading", 10.5)
    if signal_size != base_signal_size:
        signal_leading *= signal_size / max(0.01, base_signal_size)
    min_size = body_size

    def width_at(size: float) -> float:
        width = 0.0
        for char in str(text or ""):
            if char.isspace():
                ratio = 0.25
            elif char.isupper():
                ratio = 0.63
            elif char.islower():
                ratio = 0.56
            elif unicodedata.category(char).startswith("M"):
                ratio = 0.0
            elif char.isalpha():
                ratio = 0.60
            elif unicodedata.category(char).startswith("P"):
                ratio = 0.30
            else:
                ratio = 0.55
            width += ratio * size
        return width

    available = max(1.0, available_width)
    base_width = width_at(signal_size)
    fitted_size = signal_size
    if base_width > available:
        fitted_size = max(min_size, signal_size * available / base_width)
    fitted_width = width_at(fitted_size)
    horizontal_scale = min(100.0, 100.0 * available / max(1.0, fitted_width))
    fitted_leading = signal_leading * fitted_size / max(0.01, signal_size)
    return round(fitted_size, 3), round(fitted_leading, 3), round(horizontal_scale, 3)


def tail_label_metrics(
    params: dict[str, tuple[str, str]],
    lang: str,
    text: str,
    available_width: float,
) -> tuple[float, float, float]:
    """Fit a safety-tail warning label without borrowing signal-table sizing."""
    language = (lang or "en").strip().casefold().replace("_", "-").split("-", 1)[0]
    base_size = param_pt(params, "idml_safety_tail_label_font_size", 9.85)
    base_leading = param_pt(params, "idml_safety_tail_label_font_leading", 10.2)
    if language == "en":
        return base_size, base_leading, 100.0

    width = 0.0
    for char in str(text or ""):
        if char.isspace():
            ratio = 0.25
        elif char.isupper():
            ratio = 0.63
        elif char.islower():
            ratio = 0.56
        elif unicodedata.category(char).startswith("M"):
            ratio = 0.0
        elif char.isalpha():
            ratio = 0.60
        elif unicodedata.category(char).startswith("P"):
            ratio = 0.30
        else:
            ratio = 0.55
        width += ratio * base_size

    available = max(1.0, available_width)
    fitted_size = min(base_size, base_size * available / max(1.0, width))
    fitted_size = max(5.6, fitted_size)
    fitted_leading = base_leading * fitted_size / base_size
    return round(fitted_size, 3), round(fitted_leading, 3), 100.0


def fit_symbol_body_metrics(
    params: dict[str, tuple[str, str]],
    lang: str,
    text: str,
    available_width: float,
    available_height: float,
) -> tuple[float, float, float]:
    """Fit localized continuation-symbol copy inside its fixed row."""
    language = (lang or "en").strip().casefold().replace("_", "-").split("-", 1)[0]
    base_size = param_pt(params, "type_symbol_body_font_size", 5.6)
    base_leading = min(
        param_pt(params, "type_symbol_body_font_leading", 6.5),
        base_size * 1.1,
    )
    if language not in {"fr", "es"} or available_height <= 0:
        return round(base_size, 3), round(base_leading, 3), 100.0

    available = max(1.0, available_width)
    scale = 96.0

    def line_count(size: float) -> int:
        # Gilroy's localized lowercase/diacritic mix is wider than the
        # generic prose estimate; use a conservative body-cell measure so
        # InDesign's native shaping does not turn the final line into
        # overset content.
        per_line = max(1, int(available / (0.60 * size * scale / 100.0)))
        return sum(
            max(1, (len(part) + per_line - 1) // per_line)
            for part in str(text or "").split("\n")
        )

    # Keep the ordinary localized body size whenever it fits.  Otherwise
    # reduce it in deterministic steps; this keeps long WEEE copy editable
    # inside the approved continuation row instead of leaving it overset.
    size = base_size
    min_size = max(3.6, base_size * 0.7)
    while size >= min_size:
        leading = base_leading * size / max(0.01, base_size)
        required = line_count(size) * leading + 8.0
        if required <= available_height:
            return round(size, 3), round(leading, 3), scale
        size -= 0.1

    size = min_size
    leading = base_leading * size / max(0.01, base_size)
    return round(size, 3), round(leading, 3), scale


def fit_signal_label_xml(
    xml: str,
    params: dict[str, tuple[str, str]],
    lang: str,
    text: str,
    available_width: float,
) -> str:
    """Apply compact FR/ES signal metrics while preserving EN output."""
    language = (lang or "en").split("-", 1)[0].casefold()
    if language not in {"fr", "es"}:
        return xml
    size, leading, scale = signal_label_metrics(
        params, language, text, available_width,
    )
    return with_character_metrics(
        xml, point_size=size, leading=leading, horizontal_scale=scale,
    )


def fit_tail_label_xml(
    xml: str,
    params: dict[str, tuple[str, str]],
    lang: str,
    text: str,
    available_width: float,
) -> str:
    """Apply per-language warning-box sizing while preserving English XML."""
    language = (lang or "en").strip().casefold().replace("_", "-").split("-", 1)[0]
    if language == "en":
        return xml
    size, leading, scale = tail_label_metrics(
        params, language, text, available_width,
    )
    return with_character_metrics(
        xml, point_size=size, leading=leading, horizontal_scale=scale,
    )


def with_character_metrics(
    xml: str,
    *,
    point_size: float,
    leading: float,
    horizontal_scale: float | None = None,
) -> str:
    """Apply native-import-safe point size and leading to text runs.

    InDesign accepts ``PointSize`` on ``CharacterStyleRange`` but silently
    ignores a numeric ``Leading`` attribute there (and on the enclosing
    paragraph range).  Native round-tripping serializes leading as a unit
    property instead.  Rewrite every content-bearing run so symbol fallback
    runs receive the same compact metrics while paragraph-break-only runs stay
    untouched.
    """
    pattern = re.compile(
        r'<CharacterStyleRange (?P<attrs>[^>]*)>'
        r'(?P<body>.*?)</CharacterStyleRange>',
        re.S,
    )

    def rewrite(match: re.Match[str]) -> str:
        body = match.group("body")
        if "<Content>" not in body:
            return match.group(0)
        attrs = re.sub(r'\s+PointSize="[^"]*"', "", match.group("attrs"))
        attrs = re.sub(r'\s+Leading="[^"]*"', "", attrs)
        if horizontal_scale is not None:
            attrs = re.sub(r'\s+HorizontalScale="[^"]*"', "", attrs)
        leading_xml = f'<Leading type="unit">{leading:g}</Leading>'
        if "<Properties>" in body:
            body = body.replace("<Properties>", "<Properties>" + leading_xml, 1)
        else:
            body = f"<Properties>{leading_xml}</Properties>" + body
        scale_attr = (
            f' HorizontalScale="{horizontal_scale:g}"'
            if horizontal_scale is not None else ""
        )
        return (
            f'<CharacterStyleRange {attrs} PointSize="{point_size:g}"'
            f'{scale_attr}>'
            f"{body}</CharacterStyleRange>"
        )

    return pattern.sub(rewrite, xml)


def with_character_baseline_shift(xml: str, *, shift: float) -> str:
    """Apply one visual baseline shift to every content-bearing run.

    This keeps symbol-fallback runs and ordinary text together. It is also
    safe for an inline anchored group whose carrier range contains an empty
    ``Content`` node after the group object.
    """
    pattern = re.compile(
        r'<CharacterStyleRange (?P<attrs>[^>]*)>'
        r'(?P<body>.*?)</CharacterStyleRange>',
        re.S,
    )

    def rewrite(match: re.Match[str]) -> str:
        body = match.group("body")
        if "<Content>" not in body:
            return match.group(0)
        attrs = re.sub(r'\s+BaselineShift="[^"]*"', "", match.group("attrs"))
        return (
            f'<CharacterStyleRange {attrs} BaselineShift="{shift:g}">'
            f"{body}</CharacterStyleRange>"
        )

    return pattern.sub(rewrite, xml)
