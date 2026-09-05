"""Structural validation of a built .idml package (componentization P1)."""
from __future__ import annotations

import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from .font_family import CJK_FONT_FAMILY_TOKEN, JAPANESE_FONT_FAMILY_TOKEN
from .inline_text import fallback_font_for_character
from .params import MIMETYPE


def _paragraph_fonts(styles: ET.Element) -> dict[str, str]:
    fonts: dict[str, str] = {}
    for style in styles.iter("ParagraphStyle"):
        properties = style.find("Properties")
        applied = properties.find("AppliedFont") if properties is not None else None
        if applied is not None and applied.text:
            fonts[str(style.get("Self") or "")] = applied.text
    return fonts


def _fallback_run_issues(
    part_name: str,
    root: ET.Element,
    paragraph_fonts: dict[str, str],
    declared_font_families: set[str],
) -> list[str]:
    issues: list[str] = []

    def walk(element: ET.Element, paragraph_font: str | None = None) -> None:
        if element.tag == "ParagraphStyleRange":
            paragraph_font = paragraph_fonts.get(
                str(element.get("AppliedParagraphStyle") or ""),
                paragraph_font,
            )
        applied_font = paragraph_font
        if element.tag == "CharacterStyleRange":
            properties = element.find("Properties")
            explicit = (
                properties.find("AppliedFont")
                if properties is not None else None
            )
            if explicit is not None and explicit.text:
                applied_font = explicit.text
            for content in element.findall("Content"):
                for character in content.text or "":
                    required = fallback_font_for_character(character)
                    localized_cjk = (
                        required == CJK_FONT_FAMILY_TOKEN.name
                        and JAPANESE_FONT_FAMILY_TOKEN.name
                        in declared_font_families
                        and applied_font == JAPANESE_FONT_FAMILY_TOKEN.name
                    )
                    if required is None or applied_font == required or localized_cjk:
                        continue
                    issues.append(
                        f"{part_name}: character U+{ord(character):04X} "
                        f"requires {required} but uses "
                        f"{applied_font or 'no declared font'}"
                    )
        for child in element:
            walk(child, applied_font)

    walk(root)
    return issues


def check_idml(path: Path) -> list[str]:
    issues: list[str] = []
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        duplicates = sorted({name for name in names if names.count(name) > 1})
        for name in duplicates:
            issues.append(f"duplicate package part: {name}")
        if names[0] != "mimetype":
            issues.append("mimetype is not the first zip entry")
        info = zf.getinfo("mimetype")
        if info.compress_type != zipfile.ZIP_STORED:
            issues.append("mimetype entry is compressed (must be STORED)")
        if zf.read("mimetype").decode() != MIMETYPE:
            issues.append("mimetype content mismatch")
        xml_roots: dict[str, ET.Element] = {}
        for name in names:
            if name.endswith(".xml"):
                try:
                    xml_roots[name] = ET.fromstring(zf.read(name))
                except ET.ParseError as exc:
                    issues.append(f"{name}: XML parse error: {exc}")
        styles = xml_roots.get("Resources/Styles.xml")
        fonts = xml_roots.get("Resources/Fonts.xml")
        declared_font_families = (
            {
                str(family.get("Name") or "")
                for family in fonts.iter("FontFamily")
            }
            if fonts is not None
            else set()
        )
        if styles is not None:
            paragraph_fonts = _paragraph_fonts(styles)
            for name, root in xml_roots.items():
                if name.startswith("Stories/"):
                    issues.extend(_fallback_run_issues(
                        name, root, paragraph_fonts, declared_font_families,
                    ))
        # designmap references must resolve
        dm = zf.read("designmap.xml").decode("utf-8")
        root = ET.fromstring(dm)
        for el in root.iter():
            src = el.attrib.get("src")
            if src and src not in names:
                issues.append(f"designmap references missing part: {src}")
        # spline items must carry PathGeometry — a GeometricBounds
        # attribute is silently ignored by InDesign and yields invisible
        # frames ("opens fine but blank pages")
        for name in names:
            if not name.startswith("Spreads/"):
                continue
            spread = ET.fromstring(zf.read(name))
            for element_name in ("Spread", "Page", "TextFrame", "Rectangle"):
                for element in spread.iter(element_name):
                    expected = f"hb:self={element.get('Self')}"
                    if element.get("Label") != expected:
                        issues.append(f"{name}: {element_name} {element.get('Self')} "
                                      "has no stable hb label")
            for frame in spread.iter("TextFrame"):
                if "GeometricBounds" in frame.attrib:
                    issues.append(f"{name}: TextFrame {frame.get('Self')} uses "
                                  "GeometricBounds (ignored by InDesign; use PathGeometry)")
                if frame.find("./Properties/PathGeometry") is None:
                    issues.append(f"{name}: TextFrame {frame.get('Self')} has no PathGeometry")
    return issues


def run_check_cli(path: str) -> int:
    """--check CLI: validate an existing .idml, print results, return exit code."""
    issues = check_idml(Path(path))
    for i in issues:
        print(f"[idml-check] FAIL {i}")
    print(f"[idml-check] {'OK' if not issues else f'{len(issues)} issue(s)'}: {path}")
    return 1 if issues else 0
