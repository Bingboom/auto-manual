"""Bake exported content into the designer template package.

The placeable .icml route needs a manual InDesign File->Place; this module
removes that step. It takes our self-contained export package and swaps in the
template's style/color/font Resources so the result opens directly with the
designer's formatting — no placement.

Why it works: our story references paragraph/table styles by Self id
(``ParagraphStyle/<name>`` / ``TableStyle/<name>``), and the template uses the
same name-based Self ids. The template's Styles.xml is a superset of the style
ids our content uses, so wholesale-adopting the template Resources leaves every
reference resolved. The only additions needed are colour swatches our content
references that the template does not define (injected into its Graphic.xml).

We keep OUR designmap / Spreads / MasterSpreads / Stories / Preferences so the
page geometry and threaded flow are unchanged; only the look of each named
style is replaced by the template's definition.
"""
from __future__ import annotations

import re
import zipfile
from pathlib import Path

_RESOURCE_STYLES = "Resources/Styles.xml"
_RESOURCE_GRAPHIC = "Resources/Graphic.xml"
_RESOURCE_FONTS = "Resources/Fonts.xml"

# Cell attributes we KEEP when handing formatting to the template. Everything
# else on a <Cell> (FillColor, edge strokes, insets) is a local override that
# would mask the template table style's region cell styles, so it is dropped.
_CELL_KEEP = ("Self", "Name", "RowSpan", "ColumnSpan")


def _strip_cell_overrides(story_xml: str) -> str:
    """Drop per-cell fill/stroke/inset so the template TableStyle's region
    cell styles (header / left-column / body) paint the table instead."""
    def repl(m: "re.Match[str]") -> str:
        attrs = dict(re.findall(r'(\w+)="([^"]*)"', m.group(0)))
        kept = " ".join(f'{k}="{attrs[k]}"' for k in _CELL_KEEP if k in attrs)
        return f'<Cell {kept} AppliedCellStyle="CellStyle/$ID/[None]">'
    return re.sub(r'<Cell\b[^>]*?>', repl, story_xml)

_COLORISH = ("Color", "Swatch", "Gradient", "Tint", "MixedInk", "MixedInkGroup")
_CONTENT_DIRS = ("Stories/", "Spreads/", "MasterSpreads/", "XML/")


def _referenced_colors(members: dict[str, bytes]) -> set[str]:
    """Fill/stroke colour Self ids referenced anywhere in our content XML."""
    refs: set[str] = set()
    for name, data in members.items():
        if not name.startswith(_CONTENT_DIRS):
            continue
        text = data.decode("utf-8", "replace")
        refs.update(re.findall(
            r'(?:FillColor|StrokeColor|GradientFillColor|GradientStrokeColor|'
            r'ParagraphShadingColor|ParagraphBorderColor)="([^"]+)"', text))
    return {r for r in refs if r.startswith(("Color/", "Swatch/", "Gradient/"))}


def _defined_colors(graphic_xml: str) -> set[str]:
    pat = r'<(?:%s)\b[^>]*?\bSelf="([^"]*)"' % "|".join(_COLORISH)
    return set(re.findall(pat, graphic_xml))


def _color_element(graphic_xml: str, self_id: str) -> str | None:
    esc = re.escape(self_id)
    for tag in _COLORISH:
        m = re.search(
            r'<%s\b[^>]*?\bSelf="%s".*?(?:/>|</%s>)' % (tag, esc, tag),
            graphic_xml, re.S)
        if m:
            return m.group(0)
    return None


def _inject_colors(template_graphic: str, our_graphic: str,
                   missing: set[str]) -> tuple[str, list[str]]:
    """Insert missing colour elements after the <idPkg:Graphic> open tag."""
    injected: list[str] = []
    additions: list[str] = []
    for self_id in sorted(missing):
        el = _color_element(our_graphic, self_id)
        if el:
            additions.append(el)
            injected.append(self_id)
    if not additions:
        return template_graphic, injected
    open_tag = re.search(r'<idPkg:Graphic\b[^>]*>', template_graphic)
    end = open_tag.end()
    merged = (template_graphic[:end] + "\n" + "\n".join(additions)
              + template_graphic[end:])
    return merged, injected


def merge_into_template(ours_idml: Path, template_idml: Path,
                        out_idml: Path) -> dict:
    """Write out_idml = our content wearing the template's Resources.

    Returns a summary dict (injected colours, unresolved refs) for reporting.
    """
    with zipfile.ZipFile(ours_idml) as z:
        members = {n: z.read(n) for n in z.namelist()}
    with zipfile.ZipFile(template_idml) as t:
        tpl_styles = t.read(_RESOURCE_STYLES).decode("utf-8")
        tpl_graphic = t.read(_RESOURCE_GRAPHIC).decode("utf-8")
        tpl_fonts = t.read(_RESOURCE_FONTS).decode("utf-8")

    our_graphic = members[_RESOURCE_GRAPHIC].decode("utf-8")

    # let the template's table/cell styles paint every table: drop per-cell
    # fill/stroke/inset overrides BEFORE computing which colours are still
    # referenced, so we only inject swatches the final content actually uses.
    stripped_cells = 0
    for name, data in list(members.items()):
        if name.startswith("Stories/"):
            text = data.decode("utf-8")
            stripped_cells += len(re.findall(r'<Cell\b', text))
            members[name] = _strip_cell_overrides(text).encode("utf-8")

    missing = _referenced_colors(members) - _defined_colors(tpl_graphic)
    merged_graphic, injected = _inject_colors(tpl_graphic, our_graphic, missing)
    unresolved = sorted(missing - set(injected))

    members[_RESOURCE_STYLES] = tpl_styles.encode("utf-8")
    members[_RESOURCE_GRAPHIC] = merged_graphic.encode("utf-8")
    members[_RESOURCE_FONTS] = tpl_fonts.encode("utf-8")

    out_idml.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_idml, "w", zipfile.ZIP_DEFLATED) as z:
        # mimetype must be first and stored (IDML/OCF requirement)
        z.writestr("mimetype", members.pop("mimetype"),
                   compress_type=zipfile.ZIP_STORED)
        for name, data in members.items():
            z.writestr(name, data)

    return {"injected_colors": injected, "unresolved_colors": unresolved,
            "cells_style_driven": stripped_cells}
