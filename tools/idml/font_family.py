"""Single source of truth for the primary IDML font-family contract."""
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
