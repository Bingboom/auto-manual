"""Simple continuous-story IDML writer for flow handoff mode."""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape

from . import components as _components
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


@dataclass(frozen=True)
class _FlowBlock:
    """Lossless-enough block model used by the rendered flow story.

    ``manual.flow.md`` remains the human-readable handoff artifact.  The
    IDML must not parse that artifact as plain text, though: images, tables,
    and component JSON need to stay typed until they reach the IDML writer.
    """

    kind: str
    text: str = ""
    payload: object | None = None


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
    writer = _FlowIdmlWriter(
        params=params,
        style_map=style_map,
        root=root,
        bundle_root=bundle_root,
        data_root=data_root,
    )
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
    def __init__(self, *, params: dict[str, tuple[str, str]], style_map: dict[str, str],
                 root: Path, bundle_root: Path, data_root: Path) -> None:
        self.params = params
        self.style_map = style_map
        self.root = root
        self.bundle_root = bundle_root
        self.data_root = data_root
        self.page_w = _params.param_pt(params, "page_paperwidth", 368.79)
        self.page_h = _params.param_pt(params, "page_paperheight", 524.69)
        self.m_l = _params.param_pt(params, "page_margin_left", 28.35)
        self.m_r = _params.param_pt(params, "page_margin_right", 28.35)
        self.m_t = _params.param_pt(params, "page_margin_top", 14.17)
        self.m_b = _params.param_pt(params, "page_margin_bottom", 36.85)
        self.stories: list[tuple[str, str]] = []
        self.spreads: list[tuple[str, str]] = []

    def add_markdown_story(self, markdown: str) -> None:
        blocks = _parse_flow_markdown(markdown)
        parts: list[str] = []
        estimated_height = 0.0
        for index, block in enumerate(blocks):
            terminal = index == len(blocks) - 1
            part, height = self._render_block(
                block, terminal=terminal, block_index=index,
            )
            if part:
                parts.append(part)
                estimated_height += height
        if not parts:
            parts.append(self._psr("paragraph", "", terminal=True))
            estimated_height = self.frame_height() * 0.6
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
        pages = _package.pages_for_height(self, max(
            estimated_height, self.frame_height() * 0.6,
        ))
        _package.add_spread_chain(self, sid, pages, 0, columns=1)

    def _render_block(self, block: _FlowBlock, *, terminal: bool,
                      block_index: int) -> tuple[str, float]:
        tid = f"tbl_flow_{block_index}"
        if block.kind == "component":
            spec = block.payload if isinstance(block.payload, dict) else {}
            xml, height = _components.render(
                spec,
                self._render_context(),
                tid=f"flow_cmp_{block_index}",
                terminal=terminal,
                span_columns=True,
            )
            if xml:
                return _sanitize_fallback_font_attrs(xml), height
            # Unknown component kinds must not regress to JSON source text in
            # the rendered IDML. Keep the readable copy and mark it as an
            # ordinary paragraph instead.
            fallback = _component_fallback_text(spec)
            return self._text_part("paragraph", fallback, terminal), self._estimate_text(
                "paragraph", fallback)
        if block.kind == "image":
            xml, height = _components.render_image_block(
                block.text,
                self._render_context(),
                rect_id=f"flow_img_{block_index}",
                terminal=terminal,
            )
            return (xml or ""), height
        if block.kind == "table":
            rows = block.payload if isinstance(block.payload, list) else []
            if not rows:
                return "", 0.0
            if _table_has_images(rows, self._render_context()):
                return self._render_image_table(rows, tid=tid, terminal=terminal)
            xml, height = _components.render_table_block(
                rows,
                self._render_context(),
                tid=tid,
                terminal=terminal,
                span_columns=True,
            )
            return xml, height

        style_key = block.kind if block.kind in self.style_map else "paragraph"
        if block.kind in {"body", "paragraph"}:
            style_key = "paragraph"
        elif block.kind in {"sublist", "list"}:
            style_key = "list"
        text = block.text
        if block.kind in {"list", "sublist"} and not text.startswith("•"):
            text = ("◦ " if block.kind == "sublist" else "• ") + text
        return self._text_part(style_key, text, terminal), self._estimate_text(
            style_key, text,
        )

    def _render_context(self):
        return _components.RenderContext(
            params=self.params,
            page_w=self.page_w,
            m_l=self.m_l,
            m_r=self.m_r,
            root=self.root,
            bundle_root=self.bundle_root,
            data_root=self.data_root,
            add_story=self._add_story_parts,
        )

    def _text_part(self, style_key: str, text: str, terminal: bool) -> str:
        style = self.style_map.get(style_key, self.style_map["paragraph"])
        return _prim.psr(style, text, terminal=terminal)

    @staticmethod
    def _psr(style: str, text: str, *, terminal: bool = False) -> str:
        return _prim.psr(style, text, terminal=terminal)

    def _estimate_text(self, style_key: str, text: str) -> float:
        size, leading = _style_metrics(style_key)
        width = max(80.0, self.page_w - self.m_l - self.m_r)
        per_line = max(24, int(width / (0.52 * size)))
        return max(1, math.ceil(max(1, len(text)) / per_line)) * leading

    def _render_image_table(self, rows: list[list], *, tid: str,
                            terminal: bool) -> tuple[str, float]:
        n_cols = max(len(row) for row in rows)
        body_w = self.page_w - self.m_l - self.m_r
        if n_cols == 2:
            cols = [body_w * 0.22, body_w * 0.78]
        elif n_cols == 4:
            cols = [body_w * 0.08, body_w * 0.12,
                    body_w * 0.25, body_w * 0.55]
        else:
            cols = [body_w / n_cols] * n_cols
        ctx = self._render_context()
        cells: list[str] = []
        for ri, row in enumerate(rows):
            for ci in range(n_cols):
                value = row[ci] if ci < len(row) else ""
                image = _image_value(value, ctx)
                if image is not None:
                    content = _components.figure_paragraph(
                        _prim.image_cell_content(
                            f"{tid}img{ri}_{ci}", image, 20.0, 20.0,
                        ),
                        tail="<Content></Content>",
                    )
                else:
                    style = "HB Data Header" if ri == 0 else "HB Data Body"
                    content = _prim.psr(style, str(value), terminal=True)
                cells.append(self._cell(
                    f"{tid}c{ri}_{ci}", f"{ci}:{ri}", content,
                    top=2.0, bottom=2.0, left=3.0, right=3.0,
                    valign="CenterAlign",
                ))
        table = _prim.component_table(
            tid, cols, cells, n_rows=len(rows), role="data",
        )
        return _prim.wrap_table_paragraph(
            table, terminal, span_columns=True,
        ), 13.0 * max(1, len(rows))

    def _cell(self, cid: str, name: str, content: str, **kwargs) -> str:
        return _prim.cell(cid, name, content, **kwargs)

    def _add_story_parts(self, sid: str, title: str,
                         parts: list[str]) -> str:
        safe_parts = [_sanitize_fallback_font_attrs(part) for part in parts]
        xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            f'<idPkg:Story xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
            f'<Story Self="{sid}" AppliedTOCStyle="n" TrackChanges="false" '
            f'StoryTitle="{escape(title, _ATTR_ENTITIES)}">\n'
            '<StoryPreference OpticalMarginAlignment="false" FrameType="TextFrameType"/>\n'
            + "".join(safe_parts) + '</Story>\n</idPkg:Story>\n'
        )
        self.stories.append((sid, xml))
        return sid

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
        # Flow owns the semantic style names, while actual components use the
        # shared HB style family.  Keep both families in one Styles resource;
        # emitting only the flow family makes component references unresolved
        # after import into InDesign.
        base = _styles.styles_xml(self.params)
        extra = _flow_style_entries(self.style_map)
        return base.replace(
            "  </RootParagraphStyleGroup>",
            extra + "\n  </RootParagraphStyleGroup>",
            1,
        )

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


def _parse_flow_markdown(markdown: str) -> list[_FlowBlock]:
    """Parse flow Markdown without converting renderable blocks to text.

    The old parser intentionally flattened every non-paragraph construct.
    That made the IDML look like a source dump: image syntax became a label,
    table rows became tab-delimited paragraphs, and unsupported component JSON
    was emitted literally.  This parser keeps those constructs typed until
    ``_FlowIdmlWriter`` renders them.
    """
    blocks: list[_FlowBlock] = []
    lines = markdown.splitlines()
    i = 0
    in_front_matter = False
    while i < len(lines):
        line = lines[i].strip()
        if i == 0 and line == "---":
            in_front_matter = True
            i += 1
            continue
        if in_front_matter:
            if line == "---":
                in_front_matter = False
            i += 1
            continue
        if not line or line.startswith("<!-- source_ref:") or line.startswith("<!-- asset_id:"):
            i += 1
            continue

        if line.startswith("```"):
            fence = line[3:].strip().lower()
            code: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            if i < len(lines):
                i += 1
            if fence == "json":
                try:
                    payload = json.loads("\n".join(code))
                except json.JSONDecodeError:
                    payload = None
                if isinstance(payload, dict):
                    blocks.append(_FlowBlock("component", payload=payload))
                else:
                    blocks.extend(_FlowBlock("paragraph", text=item.strip())
                                  for item in code if item.strip())
            else:
                blocks.extend(_FlowBlock("paragraph", text=item.strip())
                              for item in code if item.strip())
            continue

        if line.startswith(":::"):
            token = line[3:].strip().split(None, 1)[0].lower() if line[3:].strip() else ""
            body: list[str] = []
            i += 1
            while i < len(lines) and lines[i].strip() != ":::":
                body.append(lines[i].strip())
                i += 1
            if i < len(lines):
                i += 1
            block = _parse_flow_fence(token, body)
            if block is not None:
                blocks.append(block)
            continue

        if line.startswith("# "):
            blocks.append(_FlowBlock("h1", text=line[2:].strip()))
            i += 1
            continue
        if line.startswith("## "):
            blocks.append(_FlowBlock("h2", text=line[3:].strip()))
            i += 1
            continue
        if line.startswith("### "):
            blocks.append(_FlowBlock("h3", text=line[4:].strip()))
            i += 1
            continue
        if line.startswith("!["):
            match = re.match(r"!\[[^\]]*\]\(([^)]+)\)", line)
            if match:
                blocks.append(_FlowBlock("image", text=match.group(1).strip()))
            else:
                blocks.append(_FlowBlock("paragraph", text=line))
            i += 1
            continue
        if line.startswith("|") and "|" in line[1:]:
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            rows = _parse_markdown_table(table_lines)
            if rows:
                blocks.append(_FlowBlock("table", payload=rows))
            continue
        if line.startswith("- "):
            blocks.append(_FlowBlock("list", text=line[2:].strip()))
            i += 1
            continue
        blocks.append(_FlowBlock("paragraph", text=line))
        i += 1
    return blocks or [_FlowBlock("paragraph", text="")]


def _parse_flow_fence(token: str, lines: list[str]) -> _FlowBlock | None:
    if token in {"warning", "caution", "note", "tip", "danger", "important"}:
        label = ""
        text: list[str] = []
        list_like = False
        for line in lines:
            if line.startswith("**") and line.endswith("**"):
                label = line.strip("*").strip()
            elif line.startswith("- "):
                list_like = True
                text.append(line[2:].strip())
            elif line:
                text.append(line)
        aliases = {"danger": "warning", "important": "warning"}
        return _FlowBlock(
            "component",
            payload={
                "kind": "notice",
                "variant": aliases.get(token, token),
                "label": label or token.upper(),
                "texts": text,
                "list": list_like,
            },
        )
    if token == "fcc":
        return _FlowBlock(
            "component",
            payload={"kind": "fcc", "texts": [line for line in lines if line]},
        )
    if token == "inbox":
        rows = _parse_markdown_table(lines)
        items = []
        for row in rows[1:]:
            if len(row) >= 3:
                items.append({"img": row[1], "label": row[2]})
        return _FlowBlock("component", payload={"kind": "inbox", "items": items})
    if token == "lcdmode":
        image_ref = ""
        table_lines: list[str] = []
        for line in lines:
            match = re.match(r"!\[[^\]]*\]\(([^)]+)\)", line)
            if match:
                image_ref = match.group(1).strip()
            elif line.startswith("|"):
                table_lines.append(line)
        rows = _parse_markdown_table(table_lines)
        groups: list[dict[str, object]] = []
        for row in rows[1:]:
            if len(row) < 3:
                continue
            state, action, description = row[:3]
            group = next((item for item in groups if item["state"] == state), None)
            if group is None:
                group = {"state": state, "actions": []}
                groups.append(group)
            group["actions"].append((action, description))  # type: ignore[index]
        return _FlowBlock(
            "component",
            payload={"kind": "lcdmode", "img": image_ref, "groups": groups},
        )
    return None


def _parse_markdown_table(lines: list[str]) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in lines:
        if not line.strip().startswith("|"):
            continue
        values: list[str] = []
        current: list[str] = []
        escaped = False
        for char in line.strip().strip("|"):
            if char == "|" and not escaped:
                values.append("".join(current).strip().replace("<br>", "\n"))
                current = []
                continue
            if char == "\\" and not escaped:
                escaped = True
                continue
            current.append(char)
            escaped = False
        values.append("".join(current).strip().replace("<br>", "\n"))
        if values and all(re.fullmatch(r":?-{3,}:?", value) for value in values):
            continue
        if values:
            rows.append(values)
    return rows


def _image_value(value: object, ctx) -> Path | None:
    if not isinstance(value, str):
        return None
    candidate = value.strip()
    if not candidate.lower().endswith((".png", ".jpg", ".jpeg", ".pdf", ".svg")):
        return None
    return ctx.resolve_bundle_image(candidate)


def _table_has_images(rows: list[list], ctx) -> bool:
    return any(_image_value(value, ctx) is not None for row in rows for value in row)


def _component_fallback_text(spec: dict) -> str:
    values: list[str] = []
    label = spec.get("label")
    if label:
        values.append(str(label))
    texts = spec.get("texts")
    if isinstance(texts, list):
        values.extend(str(item) for item in texts if str(item).strip())
    return "\n".join(values) or str(spec.get("kind") or "component")


def _sanitize_fallback_font_attrs(xml: str) -> str:
    """Remove a duplicate style attribute on Unicode fallback runs.

    Some component helpers add a semantic ``FontStyle`` to the character
    range and the primitive adds the fallback's ``Regular`` style when it
    sees an explicit ``AppliedFont``.  XML rejects two attributes with the
    same name; the fallback font already supplies the correct style, so the
    semantic attribute is the one to remove.
    """
    pattern = re.compile(
        r'<CharacterStyleRange (?P<attrs>[^>]*?)>'
        r'(?P<body><Properties><AppliedFont\b[^>]*>.*?</Properties>)',
        re.DOTALL,
    )

    def replace(match: re.Match[str]) -> str:
        attrs = re.sub(r'\sFontStyle="[^"]*"', "", match.group("attrs"))
        return f'<CharacterStyleRange {attrs}>{match.group("body")}'

    return pattern.sub(replace, xml)


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


def _flow_style_entries(style_map: dict[str, str]) -> str:
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
    return "\n".join(styles)


def _flow_styles_xml(style_map: dict[str, str]) -> str:
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
        + _flow_style_entries(style_map) + "\n"
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
