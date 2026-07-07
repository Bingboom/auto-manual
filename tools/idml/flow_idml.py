"""Simple continuous-story IDML writer for flow handoff mode."""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape

from . import flow_md
from . import package as _package
from . import params as _params
from . import primitives as _prim
from . import styles as _styles
from .params import IDPKG
from .primitives import _ATTR_ENTITIES


DEFAULT_STYLE_MAP = {
    "h1": "Manual H1",
    "h2": "Manual H2",
    "h3": "Manual H3",
    "paragraph": "Body",
    "list": "Bullet List",
    "table": "Simple Table",
    "warning": "Warning Paragraph",
    "caution": "Caution Paragraph",
    "note": "Note Paragraph",
    "tip": "Tip Paragraph",
    "caption": "Figure Caption",
}


@dataclass(frozen=True)
class FlowOutputs:
    markdown: Path
    source_trace: Path
    asset_manifest: Path
    conversion_notes: Path
    idml: Path
    style_map: Path


@dataclass(frozen=True)
class _FlowParagraph:
    style_key: str
    text: str


def write_flow_outputs(*, root: Path, model: str, region: str, lang: str,
                       data_root: Path, bundle_root: Path,
                       build_command: list[str] | None = None) -> FlowOutputs:
    artifacts = flow_md.write_flow_artifacts(
        root=root,
        model=model,
        region=region,
        lang=lang,
        data_root=data_root,
        bundle_root=bundle_root,
        build_command=build_command or [],
    )
    out_dir = artifacts.markdown.parent
    style_map = load_style_map(root)
    style_map_path = out_dir / "flow_style_map.json"
    style_map_path.write_text(
        json.dumps(style_map, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    idml_path = out_dir / "manual.flow.idml"
    params = _params.load_layout_params(root / "data" / "layout_params.csv")
    writer = _FlowIdmlWriter(params=params, style_map=style_map)
    writer.add_markdown_story(artifacts.markdown.read_text(encoding="utf-8"))
    writer.write(idml_path)
    _update_trace(artifacts.source_trace, root, idml_path, style_map_path)
    return FlowOutputs(
        markdown=artifacts.markdown,
        source_trace=artifacts.source_trace,
        asset_manifest=artifacts.asset_manifest,
        conversion_notes=artifacts.conversion_notes,
        idml=idml_path,
        style_map=style_map_path,
    )


def load_style_map(root: Path) -> dict[str, str]:
    path = root / "docs" / "templates" / "idml_template" / "style_mapping" / "flow_style_map.json"
    if not path.is_file():
        return dict(DEFAULT_STYLE_MAP)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return dict(DEFAULT_STYLE_MAP)
    merged = dict(DEFAULT_STYLE_MAP)
    merged.update({str(k): str(v) for k, v in raw.items() if str(v).strip()})
    return merged


class _FlowIdmlWriter:
    def __init__(self, *, params: dict[str, tuple[str, str]], style_map: dict[str, str]) -> None:
        self.params = params
        self.style_map = style_map
        self.page_w = _params.param_pt(params, "page_paperwidth", 368.79)
        self.page_h = _params.param_pt(params, "page_paperheight", 524.69)
        self.m_l = _params.param_pt(params, "page_margin_left", 28.35)
        self.m_r = _params.param_pt(params, "page_margin_right", 28.35)
        self.m_t = _params.param_pt(params, "page_margin_top", 14.17)
        self.m_b = _params.param_pt(params, "page_margin_bottom", 36.85)
        self.stories: list[tuple[str, str]] = []
        self.spreads: list[tuple[str, str]] = []

    def add_markdown_story(self, markdown: str) -> None:
        paragraphs = _parse_flow_markdown(markdown)
        parts = [
            _prim.psr(
                self.style_map.get(p.style_key, self.style_map["paragraph"]),
                p.text,
                terminal=i == len(paragraphs) - 1,
            )
            for i, p in enumerate(paragraphs)
        ]
        sid = "st_flow_main"
        xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            f'<idPkg:Story xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
            f'<Story Self="{sid}" AppliedTOCStyle="n" TrackChanges="false" '
            'StoryTitle="FLOW MAIN">\n'
            '<StoryPreference OpticalMarginAlignment="false" FrameType="TextFrameType"/>\n'
            + "".join(parts) +
            '</Story>\n'
            '</idPkg:Story>\n'
        )
        self.stories.append((sid, xml))
        pages = _package.pages_for_height(self, self._estimate_height(paragraphs))
        _package.add_spread_chain(self, sid, pages, 0, columns=1)

    def _estimate_height(self, paragraphs: list[_FlowParagraph]) -> float:
        width = max(80.0, self.page_w - self.m_l - self.m_r)
        total = 0.0
        for para in paragraphs:
            size, leading = _style_metrics(para.style_key)
            chars_per_line = max(24, int(width / (0.52 * size)))
            lines = max(1, math.ceil(max(1, len(para.text)) / chars_per_line))
            total += lines * leading
        return max(_package.frame_height(self) * 0.6, total)

    def frame_height(self) -> float:
        return _package.frame_height(self)

    def write(self, out_path: Path) -> None:
        _package.write(self, out_path)

    def designmap_xml(self) -> str:
        return _package.designmap_xml(self)

    def graphic_xml(self) -> str:
        return _styles.graphic_xml(self.params)

    def fonts_xml(self) -> str:
        return _styles.fonts_xml()

    def styles_xml(self) -> str:
        return _flow_styles_xml(self.style_map)

    def preferences_xml(self) -> str:
        return _styles.preferences_xml(
            page_w=self.page_w,
            page_h=self.page_h,
            m_t=self.m_t,
            m_b=self.m_b,
            m_l=self.m_l,
            m_r=self.m_r,
        )

    def _path_geometry(self, x1: float, y1: float, x2: float, y2: float) -> str:
        return _prim.path_geometry(x1, y1, x2, y2)


def _parse_flow_markdown(markdown: str) -> list[_FlowParagraph]:
    paragraphs: list[_FlowParagraph] = []
    in_front_matter = False
    in_code = False
    fence_style: str | None = None
    for line_no, raw in enumerate(markdown.splitlines()):
        line = raw.strip()
        if line_no == 0 and line == "---":
            in_front_matter = True
            continue
        if in_front_matter:
            if line == "---":
                in_front_matter = False
            continue
        if not line or line.startswith("<!-- source_ref:") or line.startswith("<!-- asset_id:"):
            continue
        if line.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            paragraphs.append(_FlowParagraph("paragraph", line))
            continue
        if line.startswith(":::"):
            fence_style = _fence_style(line, fence_style)
            if fence_style in {"fcc", "inbox", "lcdmode"}:
                paragraphs.append(_FlowParagraph("h3", fence_style.upper()))
            continue
        if line.startswith("# "):
            paragraphs.append(_FlowParagraph("h1", line[2:].strip()))
        elif line.startswith("## "):
            paragraphs.append(_FlowParagraph("h2", line[3:].strip()))
        elif line.startswith("### "):
            paragraphs.append(_FlowParagraph("h3", line[4:].strip()))
        elif line.startswith("!["):
            paragraphs.append(_FlowParagraph("caption", _image_placeholder(line)))
        elif line.startswith("|") and "|" in line[1:]:
            table_line = _table_text(line)
            if table_line:
                paragraphs.append(_FlowParagraph("table", table_line))
        elif line.startswith("- "):
            style = fence_style if fence_style in {"warning", "caution", "note", "tip"} else "list"
            paragraphs.append(_FlowParagraph(style, line[2:].strip()))
        elif line.startswith("**") and line.endswith("**") and fence_style:
            style = fence_style if fence_style in {"warning", "caution", "note", "tip"} else "h3"
            paragraphs.append(_FlowParagraph(style, line.strip("*").strip()))
        else:
            style = fence_style if fence_style in {"warning", "caution", "note", "tip"} else "paragraph"
            paragraphs.append(_FlowParagraph(style, line))
    return paragraphs or [_FlowParagraph("paragraph", "")]


def _fence_style(line: str, current: str | None) -> str | None:
    if line == ":::":
        return None
    token = line[3:].strip().split(None, 1)[0].lower()
    aliases = {"warn": "warning", "danger": "warning", "important": "warning"}
    return aliases.get(token, token or current)


def _image_placeholder(line: str) -> str:
    match = re.match(r"!\[(?P<alt>[^\]]*)\]\((?P<ref>[^)]+)\)", line)
    if not match:
        return line
    ref = match.group("ref").strip()
    alt = match.group("alt").strip()
    asset_id = Path(ref).stem or ref
    suffix = f" {alt}" if alt else ""
    return f"[FIGURE: {asset_id}]{suffix} ({ref})"


def _table_text(line: str) -> str:
    cells = [cell.strip() for cell in line.strip("|").split("|")]
    compact = "".join(cells).replace("-", "").replace(":", "").strip()
    if not compact:
        return ""
    return "\t".join(cells)


def _style_metrics(style_key: str) -> tuple[float, float]:
    return {
        "h1": (14.0, 20.0),
        "h2": (11.0, 16.0),
        "h3": (9.0, 13.0),
        "list": (8.0, 11.0),
        "table": (7.5, 10.0),
        "caption": (7.5, 10.0),
        "warning": (8.0, 11.5),
        "caution": (8.0, 11.5),
        "note": (8.0, 11.5),
        "tip": (8.0, 11.5),
    }.get(style_key, (8.2, 11.0))


def _flow_styles_xml(style_map: dict[str, str]) -> str:
    styles = []
    seen: set[str] = set()
    for key, name in style_map.items():
        if name in seen:
            continue
        seen.add(name)
        size, leading = _style_metrics(key)
        weight = "Bold" if key in {"h1", "h2", "h3", "warning", "caution", "note", "tip"} else "Regular"
        fill = "Color/HB Brand Dark"
        self_id = "ParagraphStyle/" + escape(name, _ATTR_ENTITIES)
        name_attr = escape(name, _ATTR_ENTITIES)
        styles.append(
            f'    <ParagraphStyle Self="{self_id}" Name="{name_attr}" '
            f'PointSize="{size:g}" FillColor="{fill}" Justification="LeftAlign">\n'
            '      <Properties>\n'
            '        <AppliedFont type="string">Gilroy</AppliedFont>\n'
            f'        <FontStyle type="string">{weight}</FontStyle>\n'
            f'        <Leading type="unit">{leading:g}</Leading>\n'
            '      </Properties>\n'
            '    </ParagraphStyle>'
        )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<idPkg:Styles xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
        '  <RootCharacterStyleGroup Self="rcsg">\n'
        '    <CharacterStyle Self="CharacterStyle/$ID/[No character style]" '
        'Name="$ID/[No character style]"/>\n'
        '  </RootCharacterStyleGroup>\n'
        '  <RootParagraphStyleGroup Self="rpsg">\n'
        '    <ParagraphStyle Self="ParagraphStyle/$ID/[No paragraph style]" '
        'Name="$ID/[No paragraph style]"/>\n'
        '    <ParagraphStyle Self="ParagraphStyle/$ID/NormalParagraphStyle" '
        'Name="$ID/NormalParagraphStyle"/>\n'
        + "\n".join(styles) + "\n"
        '  </RootParagraphStyleGroup>\n'
        '  <RootCellStyleGroup Self="rcellsg">\n'
        '    <CellStyle Self="CellStyle/$ID/[None]" Name="$ID/[None]"/>\n'
        '  </RootCellStyleGroup>\n'
        '  <RootTableStyleGroup Self="rtsg">\n'
        '    <TableStyle Self="TableStyle/$ID/[Basic Table]" Name="$ID/[Basic Table]"/>\n'
        '  </RootTableStyleGroup>\n'
        '  <RootObjectStyleGroup Self="rosg">\n'
        '    <ObjectStyle Self="ObjectStyle/$ID/[None]" Name="$ID/[None]"/>\n'
        '    <ObjectStyle Self="ObjectStyle/$ID/[Normal Text Frame]" '
        'Name="$ID/[Normal Text Frame]"/>\n'
        '  </RootObjectStyleGroup>\n'
        '</idPkg:Styles>\n'
    )


def _update_trace(trace_path: Path, root: Path, idml_path: Path, style_map_path: Path) -> None:
    try:
        trace = json.loads(trace_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    trace.update({
        "flow_idml": _display_path(root, idml_path),
        "style_map": _display_path(root, style_map_path),
        "trace_granularity": "page",
    })
    trace_path.write_text(json.dumps(trace, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _display_path(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()
