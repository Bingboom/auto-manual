"""Single source of truth for governed IDML font-family contracts."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IdmlFontFace:
    resource_id: str
    name: str
    postscript_name: str
    style_name: str
    font_type: str


@dataclass(frozen=True)
class IdmlFontFamilyToken:
    resource_id: str
    name: str
    faces: tuple[IdmlFontFace, ...]
    delivery_postscript_names: str
    delivery_license: str

    @property
    def delivery_row(self) -> tuple[str, str, str]:
        return self.name, self.delivery_postscript_names, self.delivery_license


PRIMARY_FONT_FAMILY_TOKEN = IdmlFontFamilyToken(
    resource_id="ff_gilroy",
    name="Gilroy",
    faces=(
        IdmlFontFace(
            resource_id="ff_gilroy_r",
            name="Gilroy Regular",
            postscript_name="Gilroy-Regular",
            style_name="Regular",
            font_type="OpenTypeCFF",
        ),
        IdmlFontFace(
            resource_id="ff_gilroy_m",
            name="Gilroy Medium",
            postscript_name="Gilroy-Medium",
            style_name="Medium",
            font_type="OpenTypeCFF",
        ),
        IdmlFontFace(
            resource_id="ff_gilroy_sb",
            name="Gilroy Semibold",
            postscript_name="Gilroy-SemiBold",
            style_name="Semibold",
            font_type="OpenTypeCFF",
        ),
        IdmlFontFace(
            resource_id="ff_gilroy_b",
            name="Gilroy Bold",
            postscript_name="Gilroy-Bold",
            style_name="Bold",
            font_type="OpenTypeCFF",
        ),
        IdmlFontFace(
            resource_id="ff_gilroy_h",
            name="Gilroy Heavy",
            postscript_name="Gilroy-Heavy",
            style_name="Heavy",
            font_type="OpenTypeCFF",
        ),
    ),
    delivery_postscript_names=(
        "Gilroy-Regular / Gilroy-Medium / Gilroy-SemiBold / Gilroy-Bold"
    ),
    delivery_license="commercial (Radomir Tinkov)",
)


# ``idml_font_family_cjk`` is a renderer token, not a layout-geometry
# parameter.  Keep it out of layout_params.csv so enabling explicit CJK runs
# does not invalidate an otherwise unchanged approved reference-layout plan.
# Arial Unicode MS is already part of the historical IDML resource and
# delivery contract; centralizing it here therefore keeps non-CJK package
# bytes unchanged.
CJK_FONT_FAMILY_TOKEN = IdmlFontFamilyToken(
    resource_id="ff_arial_unicode_ms",
    name="Arial Unicode MS",
    faces=(
        IdmlFontFace(
            resource_id="ff_arial_unicode_ms_r",
            name="Arial Unicode MS Regular",
            postscript_name="ArialUnicodeMS",
            style_name="Regular",
            font_type="OpenTypeTT",
        ),
    ),
    delivery_postscript_names="ArialUnicodeMS",
    delivery_license="system font (symbol fallback)",
)


# Latin-market IDML must not depend on macOS-only symbol faces. Segoe UI
# Symbol is present on supported Windows hosts and covers the editable DC,
# bullet, reference-mark, ordinal, and subscript glyphs emitted by the
# renderer.
SYMBOL_FONT_FAMILY_TOKEN = IdmlFontFamilyToken(
    resource_id="ff_segoe_ui_symbol",
    name="Segoe UI Symbol",
    faces=(
        IdmlFontFace(
            resource_id="ff_segoe_ui_symbol_r",
            name="Segoe UI Symbol",
            postscript_name="SegoeUISymbol",
            style_name="Regular",
            font_type="OpenTypeTT",
        ),
    ),
    delivery_postscript_names="SegoeUISymbol",
    delivery_license="Windows system font (symbol fallback)",
)


# Segoe UI Symbol stops at circled 20. Yu Gothic is the Windows-native face
# used for the complete editable circled-number set through 27, including the
# LCD table row labels.
CIRCLED_NUMBER_FONT_FAMILY_TOKEN = IdmlFontFamilyToken(
    resource_id="ff_yu_gothic",
    name="Yu Gothic",
    faces=(
        IdmlFontFace(
            resource_id="ff_yu_gothic_r",
            name="Yu Gothic Regular",
            postscript_name="YuGothic-Regular",
            style_name="Regular",
            font_type="OpenTypeTT",
        ),
    ),
    delivery_postscript_names="YuGothic-Regular",
    delivery_license="Windows system font (circled-number fallback)",
)


# Korean body text is a typographic choice, not coverage fallback: Hangul
# runs route here instead of degrading to the Arial Unicode MS symbol face.
# Noto Sans KR is the print-industry default for Korean (SIL OFL 1.1 — free
# to install and to embed in print PDFs). The family is declared only inside
# Korean packages so every non-Korean package keeps byte-identical
# resources; swapping the Korean face later means editing this one token.
KOREAN_FONT_FAMILY_TOKEN = IdmlFontFamilyToken(
    resource_id="ff_noto_sans_kr",
    name="Noto Sans KR",
    faces=(
        IdmlFontFace(
            resource_id="ff_noto_sans_kr_r",
            name="Noto Sans KR Regular",
            postscript_name="NotoSansKR-Regular",
            style_name="Regular",
            font_type="OpenTypeCFF",
        ),
    ),
    delivery_postscript_names="NotoSansKR-Regular",
    delivery_license="SIL OFL 1.1 (Korean text; Google Noto)",
)


IDML_FONT_FAMILY_TOKENS = (
    PRIMARY_FONT_FAMILY_TOKEN,
    CJK_FONT_FAMILY_TOKEN,
    SYMBOL_FONT_FAMILY_TOKEN,
    CIRCLED_NUMBER_FONT_FAMILY_TOKEN,
)

# One manifest serves every delivery, so operators installing fonts see the
# Korean family listed even though it ships only inside Korean packages.
DELIVERY_FONT_FAMILY_TOKENS = IDML_FONT_FAMILY_TOKENS + (
    KOREAN_FONT_FAMILY_TOKEN,
)


def font_family_tokens(
    language: str | None = None,
) -> tuple[IdmlFontFamilyToken, ...]:
    """Return the font families a package for ``language`` must declare."""
    code = (language or "").split("-", 1)[0].strip().casefold()
    if code == "ko":
        return IDML_FONT_FAMILY_TOKENS + (KOREAN_FONT_FAMILY_TOKEN,)
    return IDML_FONT_FAMILY_TOKENS
