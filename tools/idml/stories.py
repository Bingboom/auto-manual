"""Story builders for the IDML exporter (componentization P3).

Each function takes the writer (geometry/params/primitives via its thin
delegates + the stories/spreads sinks) and appends the built story. The
per-section ``parts`` are assembled in ``idml.section_parts`` (shared with the
single-flow book path); these wrappers add the Story envelope. The golden
byte-comparison pins equivalence.
"""
from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

from . import section_parts as _sp
from .params import IDPKG
from .primitives import _ATTR_ENTITIES

# Re-exported for callers that import the part-builders from idml.stories.
prose_blocks_to_parts = _sp.prose_blocks_to_parts
spec_parts = _sp.spec_parts
lcd_parts = _sp.lcd_parts
symbols_parts = _sp.symbols_parts
trouble_parts = _sp.trouble_parts


def add_prose_story(writer, sid: str, title: str, blocks: list[tuple[str, str]],
                    bundle_root: Path) -> tuple[str, float]:
    """Story from extracted prose blocks; returns (sid, est_height_pt)."""
    parts, est = _sp.prose_blocks_to_parts(writer, sid, blocks, bundle_root)
    xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<idPkg:Story xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
        f'<Story Self="{sid}" AppliedTOCStyle="n" TrackChanges="false" StoryTitle="{escape(title, _ATTR_ENTITIES)}">\n'
        '<StoryPreference OpticalMarginAlignment="false" FrameType="TextFrameType"/>\n'
        + "".join(parts) + '</Story>\n</idPkg:Story>\n'
    )
    writer.stories.append((sid, xml))
    return sid, est


def add_lcd_story(writer, rows: list[dict], data_root: Path) -> str:
    """LCD icon table: circled-no / icon image / name / description."""
    return writer._add_story_parts("st_lcd", "LCD DISPLAY", _sp.lcd_parts(writer, rows))


def add_symbols_story(writer, signals: list[tuple[str, str]],
                      icons: list[dict], data_root: Path, lang: str = "en") -> str:
    return writer._add_story_parts(
        "st_symbols", "MEANING OF SYMBOLS", _sp.symbols_parts(writer, signals, icons, lang))


def add_trouble_story(writer, rows: list[tuple[str, str]]) -> str:
    sid = "st_trouble"
    parts = _sp.trouble_parts(writer, rows)
    xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<idPkg:Story xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
        f'<Story Self="{sid}" AppliedTOCStyle="n" TrackChanges="false" StoryTitle="TROUBLESHOOTING">\n'
        '<StoryPreference OpticalMarginAlignment="false" FrameType="TextFrameType"/>\n'
        + "".join(parts) + '</Story>\n</idPkg:Story>\n'
    )
    writer.stories.append((sid, xml))
    return sid


def add_spec_story(writer, sections: list[dict],
                   annotations: list[str] | None = None) -> str:
    sid = "st_spec"
    parts = _sp.spec_parts(writer, sections, annotations)
    xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<idPkg:Story xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
        f'<Story Self="{sid}" AppliedTOCStyle="n" TrackChanges="false" StoryTitle="SPECIFICATIONS">\n'
        '<StoryPreference OpticalMarginAlignment="false" FrameType="TextFrameType"/>\n'
        + "".join(parts) +
        '</Story>\n'
        '</idPkg:Story>\n'
    )
    writer.stories.append((sid, xml))
    return sid


def add_text_story(writer, sid: str, title: str, blocks: list[tuple[str, str]]) -> str:
    parts = [
        writer._psr(style, text, terminal=(i == len(blocks) - 1))
        for i, (style, text) in enumerate(blocks)
    ]
    return writer._add_story_parts(sid, title, parts)


def _add_story_parts(writer, sid: str, title: str, parts: list[str]) -> str:
    xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<idPkg:Story xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
        f'<Story Self="{sid}" AppliedTOCStyle="n" TrackChanges="false" StoryTitle="{escape(title, _ATTR_ENTITIES)}">\n'
        '<StoryPreference OpticalMarginAlignment="false" FrameType="TextFrameType"/>\n'
        + "".join(parts) +
        '</Story>\n'
        '</idPkg:Story>\n'
    )
    writer.stories.append((sid, xml))
    return sid
