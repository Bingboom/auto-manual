"""Package assembly for the IDML exporter (componentization P4).

The zip contract (mimetype first + STORED), designmap wiring, the linked
spread chain, and the deliberately-coarse height estimation used to size
it. Moved verbatim from IdmlWriter — golden byte-comparison pins it.
"""
from __future__ import annotations

import zipfile
from pathlib import Path

from .params import IDPKG, MIMETYPE
from .stable_ids import apply_stable_labels
from .story_frames import add_lcd_story_frames, add_story_frames


def frame_height(writer) -> float:
    return writer.page_h - writer.m_t - writer.m_b

def estimate_spec_height(sections: list[dict]) -> float:
    """Rough content height in pt for page-count estimation.

    Deliberately coarse: if it underestimates, InDesign shows the
    standard overset indicator and the designer drags the chain one
    frame longer — a trailing blank page is worse than that.
    """
    h = 16.0  # H1
    for sec in sections:
        h += 14.0  # section title
        for _, value in sec["rows"]:
            h += 11.0 * max(1, value.count("\n") + 1)
    return h

def pages_for_height(writer, height_pt: float) -> int:
    import math
    return max(1, math.ceil(height_pt / writer.frame_height()))

def add_spread_chain(writer, story_id: str, n_pages: int, start_index: int,
                     columns: int = 1, bottom_extra: float = 0.0,
                     first_top_offset: float = 0.0) -> None:
    """One spread per page, each holding one frame of a linked chain.

    Spread coordinates: origin at the spread center; the page's
    top-left corner sits at (-w/2, -h/2), so the type area is that
    corner offset by the page margins.
    """
    x1 = -writer.page_w / 2 + writer.m_l
    x2 = writer.page_w / 2 - writer.m_r
    y2 = writer.page_h / 2 - writer.m_b + bottom_extra
    for i in range(n_pages):
        first_offset = first_top_offset if i == 0 else 0.0
        y1 = -writer.page_h / 2 + writer.m_t + first_offset
        frame_y2 = y2 + first_offset
        spread_id = f"sp_{start_index + i}"
        frame_id = f"tf_{story_id}_{i}"
        prev = f'PreviousTextFrame="tf_{story_id}_{i-1}"' if i > 0 else 'PreviousTextFrame="n"'
        nxt = f'NextTextFrame="tf_{story_id}_{i+1}"' if i < n_pages - 1 else 'NextTextFrame="n"'
        xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            f'<idPkg:Spread xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
            f'<Spread Self="{spread_id}" PageCount="1" BindingLocation="0" ShowMasterItems="true">\n'
            f'  <Page Self="{spread_id}_pg" Name="{start_index + i + 1}" '
            'AppliedMaster="n" OverrideList="" TabOrder="" GridStartingPoint="TopOutside" '
            f'GeometricBounds="0 0 {writer.page_h:g} {writer.page_w:g}" '
            f'ItemTransform="1 0 0 1 {-writer.page_w / 2:g} {-writer.page_h / 2:g}">\n'
            '    <MarginPreference ColumnCount="1" ColumnGutter="12" '
            f'Top="{writer.m_t:g}" Bottom="{writer.m_b:g}" Left="{writer.m_l:g}" Right="{writer.m_r:g}"/>\n'
            '  </Page>\n'
            f'  <TextFrame Self="{frame_id}" ParentStory="{story_id}" {prev} {nxt} '
            'ContentType="TextType" AppliedObjectStyle="ObjectStyle/$ID/[Normal Text Frame]" '
            'ItemTransform="1 0 0 1 0 0">\n'
            + writer._path_geometry(x1, y1, x2, frame_y2) +
            f'    <TextFramePreference TextColumnCount="{columns}" TextColumnGutter="11" AutoSizingType="Off"/>\n'
            '  </TextFrame>\n'
            '</Spread>\n'
            '</idPkg:Spread>\n'
        )
        writer.spreads.append((spread_id, xml))


def designmap_xml(writer) -> str:
    spread_refs = "\n".join(
        f'  <idPkg:Spread src="Spreads/Spread_{sid}.xml"/>' for sid, _ in writer.spreads
    )
    # InDesign binds an anchored frame's ParentStory only when the sub-story
    # is declared AFTER its host story (forward reference); declared before,
    # it imports as an orphan and the frame comes up empty.
    plain = [s for s in writer.stories if not s[0].startswith("st_anchor_")]
    # Within the anchored block, reversed creation order keeps the
    # forward-reference contract even for nesting: a nested chip story is
    # created while its host panel's parts are assembled (earlier), so
    # reversing declares the host first and the chip after it.
    anchored = [s for s in writer.stories if s[0].startswith("st_anchor_")]
    ordered = plain + anchored[::-1]
    story_refs = "\n".join(
        f'  <idPkg:Story src="Stories/Story_{sid}.xml"/>' for sid, _ in ordered
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<?aid style="50" type="document" readerVersion="15.0" featureSet="257" product="15.0(100)"?>\n'
        f'<Document xmlns:idPkg="{IDPKG}" DOMVersion="15.0" Self="doc" '
        'StoryList="' + " ".join(sid for sid, _ in ordered) + '" Name="manual">\n'
        '  <Language Self="Language/$ID/English%3a USA" Name="$ID/English: USA" '
        'SingleQuotes="&#8216;&#8217;" DoubleQuotes="&#8220;&#8221;"/>\n'
        f'  <idPkg:Graphic src="Resources/Graphic.xml"/>\n'
        f'  <idPkg:Fonts src="Resources/Fonts.xml"/>\n'
        f'  <idPkg:Styles src="Resources/Styles.xml"/>\n'
        f'  <idPkg:Preferences src="Resources/Preferences.xml"/>\n'
        f'{spread_refs}\n'
        f'{story_refs}\n'
        '</Document>\n'
    )

def write(writer, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w") as zf:
        # mimetype must be first and stored uncompressed
        zf.writestr(zipfile.ZipInfo("mimetype"), MIMETYPE, compress_type=zipfile.ZIP_STORED)
        def add(name: str, data: str) -> None:
            zf.writestr(name, data, compress_type=zipfile.ZIP_DEFLATED)
        add("designmap.xml", writer.designmap_xml())
        add("META-INF/container.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">\n'
            '  <rootfiles><rootfile full-path="designmap.xml" media-type="text/xml"/></rootfiles>\n'
            '</container>\n')
        add("Resources/Graphic.xml", writer.graphic_xml())
        add("Resources/Fonts.xml", writer.fonts_xml())
        add("Resources/Styles.xml", writer.styles_xml())
        add("Resources/Preferences.xml", writer.preferences_xml())
        for sid, xml in writer.spreads:
            add(f"Spreads/Spread_{sid}.xml", apply_stable_labels(xml))
        for sid, xml in writer.stories:
            add(f"Stories/Story_{sid}.xml", apply_stable_labels(xml))
