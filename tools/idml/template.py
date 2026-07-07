"""Template-shell support for flow IDML exports.

The flow exporter owns the generated story and threaded frames. A designer
template can still provide the document shell: resources, styles, fonts,
preferences, and master spreads. We copy only shell parts, never template
stories/spreads, so generated content stays deterministic.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import zipfile
import xml.etree.ElementTree as ET

from . import fontmap as _fontmap


RESOURCE_PARTS = (
    "Resources/Graphic.xml",
    "Resources/Fonts.xml",
    "Resources/Styles.xml",
    "Resources/Preferences.xml",
)

SYMBOL_FALLBACK_FAMILIES = {"Arial Unicode MS", "Apple Symbols"}


@dataclass(frozen=True)
class IdmlTemplate:
    path: Path
    resources: dict[str, str]
    master_spreads: dict[str, str]
    master_self: str | None
    page_w: float | None
    page_h: float | None
    margins: tuple[float, float, float, float] | None
    font_map: _fontmap.IdmlFontMap | None = None

    def resource(self, name: str) -> str | None:
        return self.resources.get(name)

    def fonts_xml(self, fallback_fonts_xml: str) -> str:
        fonts = self.resources.get("Resources/Fonts.xml")
        if not fonts:
            return fallback_fonts_xml
        for family in ("Arial Unicode MS", "Apple Symbols"):
            if f'Name="{family}"' not in fonts:
                fonts = _append_font_family(fonts, fallback_fonts_xml, family)
        return _fontmap.apply_fonts_font_map(
            fonts,
            self.font_map,
            preserve_families=SYMBOL_FALLBACK_FAMILIES,
        )


def load_idml_template(path: Path, lang: str = "en") -> IdmlTemplate:
    with zipfile.ZipFile(path) as zf:
        names = set(zf.namelist())
        resources = {
            name: zf.read(name).decode("utf-8")
            for name in RESOURCE_PARTS
            if name in names
        }
        master_spreads = {
            name: zf.read(name).decode("utf-8")
            for name in names
            if name.startswith("MasterSpreads/") and name.endswith(".xml")
        }
        page_w, page_h = _page_size(resources.get("Resources/Preferences.xml", ""))
        margins = _first_page_margins(zf, names)
    font_map = _fontmap.load_template_font_map(path, lang)
    if font_map and "Resources/Styles.xml" in resources:
        resources["Resources/Styles.xml"] = _fontmap.apply_styles_font_map(
            resources["Resources/Styles.xml"],
            font_map,
        )
    return IdmlTemplate(
        path=path,
        resources=resources,
        master_spreads=master_spreads,
        master_self=_first_master_self(master_spreads),
        page_w=page_w,
        page_h=page_h,
        margins=margins,
        font_map=font_map,
    )


def load_optional_idml_template(value: str | None, root: Path, lang: str = "en") -> IdmlTemplate | None:
    if not value:
        return None
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    if not path.exists():
        raise FileNotFoundError(path)
    return load_idml_template(path, lang=lang)


def _page_size(preferences_xml: str) -> tuple[float | None, float | None]:
    if not preferences_xml:
        return None, None
    try:
        root = ET.fromstring(preferences_xml)
    except ET.ParseError:
        return None, None
    for elem in root.iter("DocumentPreference"):
        try:
            return float(elem.attrib["PageWidth"]), float(elem.attrib["PageHeight"])
        except (KeyError, ValueError):
            return None, None
    return None, None


def _first_page_margins(zf: zipfile.ZipFile, names: set[str]) -> tuple[float, float, float, float] | None:
    for name in sorted(n for n in names if n.startswith("Spreads/") and n.endswith(".xml")):
        try:
            root = ET.fromstring(zf.read(name))
        except ET.ParseError:
            continue
        for page in root.iter("Page"):
            margin = page.find("MarginPreference")
            if margin is None:
                continue
            try:
                return (
                    float(margin.attrib["Top"]),
                    float(margin.attrib["Bottom"]),
                    float(margin.attrib["Left"]),
                    float(margin.attrib["Right"]),
                )
            except (KeyError, ValueError):
                continue
    return None


def _first_master_self(master_spreads: dict[str, str]) -> str | None:
    for xml in master_spreads.values():
        try:
            root = ET.fromstring(xml)
        except ET.ParseError:
            continue
        spread = root.find("MasterSpread")
        if spread is not None:
            return spread.attrib.get("Self")
    return None


def _append_font_family(fonts_xml: str, fallback_fonts_xml: str, family: str) -> str:
    pattern = re.compile(
        rf'\n?\s*<FontFamily\b[^>]*Name="{re.escape(family)}"[\s\S]*?</FontFamily>'
    )
    match = pattern.search(fallback_fonts_xml)
    if not match:
        return fonts_xml
    insert = "\n" + match.group(0).strip() + "\n"
    return fonts_xml.replace("</idPkg:Fonts>", insert + "</idPkg:Fonts>")
