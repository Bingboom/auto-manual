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


# Portable symbol faces are committed unchanged under SIL OFL 1.1 and copied
# beside every designer-facing IDML. Do not replace them with a platform
# system font: Resources/Fonts.xml cannot prove that the opening host has it.
SYMBOL_FONT_FAMILY_TOKEN = IdmlFontFamilyToken(
    resource_id="ff_noto_sans_symbols",
    name="Noto Sans Symbols",
    faces=(
        IdmlFontFace(
            resource_id="ff_noto_sans_symbols_r",
            name="Noto Sans Symbols Regular",
            postscript_name="NotoSansSymbols-Regular",
            style_name="Regular",
            font_type="OpenTypeTT",
        ),
    ),
    delivery_postscript_names="NotoSansSymbols-Regular",
    delivery_license="SIL OFL 1.1 (bundled portable symbol fallback)",
)


TEXT_SYMBOL_FONT_FAMILY_TOKEN = IdmlFontFamilyToken(
    resource_id="ff_noto_sans",
    name="Noto Sans",
    faces=(
        IdmlFontFace(
            resource_id="ff_noto_sans_r",
            name="Noto Sans Regular",
            postscript_name="NotoSans-Regular",
            style_name="Regular",
            font_type="OpenTypeTT",
        ),
    ),
    delivery_postscript_names="NotoSans-Regular",
    delivery_license="SIL OFL 1.1 (bundled portable text-symbol fallback)",
)


BULLET_FONT_FAMILY_TOKEN = IdmlFontFamilyToken(
    resource_id="ff_noto_sans_symbols2",
    name="Noto Sans Symbols2",
    faces=(
        IdmlFontFace(
            resource_id="ff_noto_sans_symbols2_r",
            name="Noto Sans Symbols2 Regular",
            postscript_name="NotoSansSymbols2-Regular",
            style_name="Regular",
            font_type="OpenTypeTT",
        ),
    ),
    delivery_postscript_names="NotoSansSymbols2-Regular",
    delivery_license="SIL OFL 1.1 (bundled portable filled-circle fallback)",
)


# Compatibility export: circled numbers 1-20 share Noto Sans Symbols.
CIRCLED_NUMBER_FONT_FAMILY_TOKEN = SYMBOL_FONT_FAMILY_TOKEN


# Korean prose uses a real sans family whose unchanged SIL-OFL binary is
# shipped beside Korean IDML packages. This is typography, not a symbol
# fallback; Western punctuation continues to inherit the primary paragraph.
KOREAN_FONT_FAMILY_TOKEN = IdmlFontFamilyToken(
    resource_id="ff_nanum_gothic",
    name="NanumGothic",
    faces=(
        IdmlFontFace(
            resource_id="ff_nanum_gothic_r",
            name="NanumGothic Regular",
            postscript_name="NanumGothic",
            style_name="Regular",
            font_type="OpenTypeTT",
        ),
    ),
    delivery_postscript_names="NanumGothic",
    delivery_license="SIL OFL 1.1 (bundled Korean text; NHN Nanum)",
)


IDML_FONT_FAMILY_TOKENS = (
    PRIMARY_FONT_FAMILY_TOKEN,
    CJK_FONT_FAMILY_TOKEN,
    TEXT_SYMBOL_FONT_FAMILY_TOKEN,
    SYMBOL_FONT_FAMILY_TOKEN,
    BULLET_FONT_FAMILY_TOKEN,
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
