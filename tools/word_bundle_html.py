#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import html
from html.parser import HTMLParser
import re
import shutil
import struct
from pathlib import Path
from urllib.parse import unquote
from xml.etree import ElementTree as ET

from tools.gen_index_bundle import MaterializedBundle, materialize_bundle
from tools.phase1.renderers import rst_escape
from tools.word_bundle_common import paths


@dataclass(frozen=True)
class WordBundlePageMeta:
    source_path: Path
    anchor_text: str


def _render_cover_html(title: str) -> str:
    title_html = html.escape(rst_escape(title))
    return "".join(
        [
            '<section class="manual-cover">',
            f'<div class="cover-title">{title_html}</div>',
            "</section>",
        ]
    )


class _AnchorTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._texts: list[str] = []

    def handle_data(self, data: str) -> None:
        text = " ".join(data.split()).strip()
        if text:
            self._texts.append(text)

    @property
    def first_text(self) -> str:
        return self._texts[0] if self._texts else ""


def _extract_word_anchor_text(fragment: str) -> str:
    parser = _AnchorTextParser()
    parser.feed(fragment)
    return parser.first_text


def _render_page_break_html() -> str:
    return '<div class="manual-page-break"></div>'


def _render_safety_item_html(text: str) -> str:
    raw = rst_escape(text)
    parts = [part.strip() for part in raw.split("\\n") if part.strip()]
    if not parts:
        return ""

    head = html.escape(parts[0])
    extra_lines: list[str] = []
    sub_items: list[str] = []
    for part in parts[1:]:
        if part.startswith("- "):
            sub_items.append(f"<li>{html.escape(part[2:].strip())}</li>")
        else:
            extra_lines.append(html.escape(part))

    body = head
    if extra_lines:
        body += "<br/>" + "<br/>".join(extra_lines)
    if sub_items:
        body += '<ul>' + "".join(sub_items) + "</ul>"
    return f"<li>{body}</li>"


def render_safety_word_html(data: dict[str, object]) -> str:
    top_items = [str(item) for item in data["top_items"]]
    bottom_items = [str(item) for item in data["bottom_items"]]
    return "".join(
        [
            '<section class="manual-section safety-section">',
            f"<h1>{html.escape(rst_escape(str(data['title_main'])))}</h1>",
            f"<p><strong>{html.escape(rst_escape(str(data['warning_title'])))}</strong></p>",
            f"<p>{html.escape(rst_escape(str(data['lead_top'])))}</p>",
            "<ul>",
            "".join(_render_safety_item_html(item) for item in top_items),
            "</ul>",
            f"<h2>{html.escape(rst_escape(str(data['title_operating'])))}</h2>",
            f"<p><strong>{html.escape(rst_escape(str(data['save_title'])))}</strong></p>",
            "<ul>",
            "".join(_render_safety_item_html(item) for item in bottom_items),
            "</ul>",
            "</section>",
        ]
    )


def _render_table_cell_html(text: str) -> str:
    lines = [html.escape(rst_escape(x)) for x in rst_escape(text).replace("\\n", "\n").splitlines()]
    lines = [line for line in lines if line]
    if not lines:
        return ""
    return "<br/>".join(lines)


def render_spec_word_html(data: dict[str, object]) -> str:
    parts = [
        '<section class="manual-section spec-section">',
        f"<h1>{html.escape(rst_escape(str(data['title_main'])))}</h1>",
    ]

    for section in data["sections"]:
        title = html.escape(rst_escape(str(section["title"])))
        parts.append(f"<h2>{title}</h2>")
        parts.append('<table class="manual-table">')
        parts.append("<tbody>")
        for left, right in section["rows"]:
            parts.append("<tr>")
            parts.append(f"<td>{_render_table_cell_html(str(left))}</td>")
            parts.append(f"<td>{_render_table_cell_html(str(right))}</td>")
            parts.append("</tr>")
        parts.append("</tbody>")
        parts.append("</table>")

    for note in data["notes"]:
        parts.append(f"<p>{_render_table_cell_html(str(note))}</p>")
    for footnote in data["footnotes"]:
        parts.append(f"<p>{_render_table_cell_html(str(footnote))}</p>")

    parts.append("</section>")
    return "".join(parts)


_IMG_TAG_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
_IMG_SRC_RE = re.compile(r'(<img\b[^>]*\bsrc=")([^"]+)(")', re.IGNORECASE)
_STYLE_ATTR_RE = re.compile(r'style="([^"]*)"', re.IGNORECASE)
_WIDTH_ATTR_RE = re.compile(r"\bwidth\s*=", re.IGNORECASE)
_HEIGHT_ATTR_RE = re.compile(r"\bheight\s*=", re.IGNORECASE)
_STYLE_WIDTH_RE = re.compile(r"\bwidth\s*:\s*([^;]+)", re.IGNORECASE)
_STYLE_HEIGHT_RE = re.compile(r"\bheight\s*:\s*([^;]+)", re.IGNORECASE)
_RST_HEADING_CHARS = set("=-~^\"`:+*#")
_ALERT_LABELS = {"WARNING", "CAUTION", "DANGER", "NOTE", "TIP", "TIPS"}
_SIGNAL_WORD_BANNERS = {
    "WARNING": "templates/word_template/common_assets/symbols/warning_bar.png",
    "CAUTION": "templates/word_template/common_assets/symbols/caution_bar.png",
    "NOTE": "templates/word_template/common_assets/symbols/note_bar.png",
    "TIP": "templates/word_template/common_assets/symbols/tip_bar.png",
}
_SAFETY_SUBLIST_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "Do not charge the battery in extremely hot or cold environments",
        (
            "Charging temperature:",
            "Discharging temperature:",
        ),
    ),
    (
        "To ensure proper air circulation",
        (
            "Charging in damp or poorly ventilated spaces",
            "Water can cause short circuits",
        ),
    ),
)


def _normalize_css_size(value: str) -> str | None:
    token = value.strip()
    if not token:
        return None

    px_match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)px", token, re.IGNORECASE)
    if px_match:
        return str(int(round(float(px_match.group(1)))))

    pct_match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)%", token, re.IGNORECASE)
    if pct_match:
        number = float(pct_match.group(1))
        if number.is_integer():
            return f"{int(number)}%"
        return f"{number}%"

    return None


def _resolve_image_src_path(src: str) -> Path | None:
    candidate = src.strip()
    if not candidate:
        return None

    if candidate.lower().startswith("file://"):
        raw = unquote(candidate[7:])
        if raw.startswith("/") and len(raw) > 2 and raw[2] == ":":
            raw = raw[1:]
        path = Path(raw)
    else:
        path = Path(candidate)

    if path.exists() and path.is_file():
        return path.resolve()
    return None


def _read_png_dimensions(path: Path) -> tuple[int, int] | None:
    data = path.read_bytes()[:24]
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        return None
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def _read_gif_dimensions(path: Path) -> tuple[int, int] | None:
    data = path.read_bytes()[:10]
    if len(data) < 10 or data[:6] not in {b"GIF87a", b"GIF89a"}:
        return None
    width, height = struct.unpack("<HH", data[6:10])
    return width, height


def _read_bmp_dimensions(path: Path) -> tuple[int, int] | None:
    data = path.read_bytes()[:26]
    if len(data) < 26 or data[:2] != b"BM":
        return None
    width, height = struct.unpack("<ii", data[18:26])
    return width, abs(height)


def _read_jpeg_dimensions(path: Path) -> tuple[int, int] | None:
    with path.open("rb") as fh:
        if fh.read(2) != b"\xff\xd8":
            return None

        sof_markers = {
            0xC0,
            0xC1,
            0xC2,
            0xC3,
            0xC5,
            0xC6,
            0xC7,
            0xC9,
            0xCA,
            0xCB,
            0xCD,
            0xCE,
            0xCF,
        }

        while True:
            marker_start = fh.read(1)
            if not marker_start:
                return None
            if marker_start != b"\xff":
                continue

            marker = fh.read(1)
            while marker == b"\xff":
                marker = fh.read(1)
            if not marker:
                return None

            marker_code = marker[0]
            if marker_code in {0xD8, 0xD9}:
                continue

            length_bytes = fh.read(2)
            if len(length_bytes) != 2:
                return None
            segment_length = struct.unpack(">H", length_bytes)[0]
            if segment_length < 2:
                return None

            if marker_code in sof_markers:
                segment = fh.read(segment_length - 2)
                if len(segment) < 5:
                    return None
                height, width = struct.unpack(">HH", segment[1:5])
                return width, height

            fh.seek(segment_length - 2, 1)


def _read_image_dimensions(path: Path) -> tuple[int, int] | None:
    suffix = path.suffix.lower()
    try:
        if suffix == ".png":
            return _read_png_dimensions(path)
        if suffix == ".gif":
            return _read_gif_dimensions(path)
        if suffix == ".bmp":
            return _read_bmp_dimensions(path)
        if suffix in {".jpg", ".jpeg"}:
            return _read_jpeg_dimensions(path)
    except (OSError, struct.error, ValueError):
        return None
    return None


def _derive_height_from_width(src: str, width_value: str | None) -> str | None:
    if not width_value or width_value.endswith("%"):
        return None

    try:
        target_width = int(width_value)
    except ValueError:
        return None
    if target_width <= 0:
        return None

    img_path = _resolve_image_src_path(src)
    if img_path is None:
        return None

    dims = _read_image_dimensions(img_path)
    if not dims:
        return None

    src_width, src_height = dims
    if src_width <= 0 or src_height <= 0:
        return None

    target_height = max(1, int(round(src_height * target_width / src_width)))
    return str(target_height)


def _inject_img_dimensions(html_doc: str) -> str:
    def replace_tag(match: re.Match[str]) -> str:
        tag = match.group(0)
        style_match = _STYLE_ATTR_RE.search(tag)
        additions: list[str] = []
        width_value: str | None = None
        height_value: str | None = None
        src_match = _IMG_SRC_RE.search(tag)
        src_value = src_match.group(2) if src_match else ""

        if style_match:
            style = style_match.group(1)
            width_match = _STYLE_WIDTH_RE.search(style)
            if width_match:
                width_value = _normalize_css_size(width_match.group(1))
            height_match = _STYLE_HEIGHT_RE.search(style)
            if height_match:
                height_value = _normalize_css_size(height_match.group(1))

        if width_value and not _WIDTH_ATTR_RE.search(tag):
            additions.append(f'width="{width_value}"')

        if not _HEIGHT_ATTR_RE.search(tag):
            if not height_value:
                height_value = _derive_height_from_width(src_value, width_value)
            if height_value:
                additions.append(f'height="{height_value}"')

        if not additions:
            return tag

        if tag.endswith("/>"):
            return tag[:-2] + " " + " ".join(additions) + " />"
        return tag[:-1] + " " + " ".join(additions) + ">"

    return _IMG_TAG_RE.sub(replace_tag, html_doc)


def _html_tag_name(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1].lower()


def _html_class_names(element: ET.Element) -> set[str]:
    return {
        token.strip()
        for token in (element.attrib.get("class") or "").split()
        if token.strip()
    }


def _normalize_inline_text(text: str) -> str:
    return " ".join((text or "").split()).strip()


def _match_safety_sublist_rule(text: str) -> tuple[str, ...] | None:
    normalized = _normalize_inline_text(text)
    for parent_prefix, child_prefixes in _SAFETY_SUBLIST_RULES:
        if normalized.startswith(parent_prefix):
            return child_prefixes
    return None


def _extract_alert_label(element: ET.Element) -> str | None:
    tag = _html_tag_name(element)
    text = _normalize_inline_text("".join(element.itertext())).rstrip(":").upper()
    if text not in _ALERT_LABELS:
        return None

    if tag in {"h1", "h2", "h3"}:
        return text

    if tag != "p":
        return None

    if _normalize_inline_text(element.text or ""):
        return None
    for child in element:
        if _html_tag_name(child) not in {"strong", "b"}:
            return None
        if _normalize_inline_text(child.tail or ""):
            return None
    return text


def _is_standalone_strong_paragraph(element: ET.Element) -> bool:
    if _html_tag_name(element) != "p":
        return False
    if _normalize_inline_text(element.text or ""):
        return False
    children = list(element)
    if not children:
        return False
    for child in children:
        if _html_tag_name(child) not in {"strong", "b"}:
            return False
        if _normalize_inline_text(child.tail or ""):
            return False
    return True


def _set_element_children(element: ET.Element, new_children: list[ET.Element]) -> ET.Element:
    for child in list(element):
        element.remove(child)
    for child in new_children:
        element.append(child)
    return element


def _rewrite_known_safety_sublists(element: ET.Element) -> ET.Element:
    if _html_tag_name(element) != "ul" or "hb-list" not in _html_class_names(element):
        return element

    children = list(element)
    rewritten: list[ET.Element] = []
    index = 0
    while index < len(children):
        child = deepcopy(children[index])
        if _html_tag_name(child) != "li":
            rewritten.append(child)
            index += 1
            continue

        child_prefixes = _match_safety_sublist_rule("".join(child.itertext()))
        if not child_prefixes:
            rewritten.append(child)
            index += 1
            continue

        sub_items: list[ET.Element] = []
        next_index = index + 1
        while next_index < len(children):
            next_child = children[next_index]
            if _html_tag_name(next_child) != "li":
                break
            next_text = _normalize_inline_text("".join(next_child.itertext()))
            if not any(next_text.startswith(prefix) for prefix in child_prefixes):
                break
            sub_items.append(deepcopy(next_child))
            next_index += 1

        if sub_items:
            sublist = ET.Element("ul", {"class": "hb-sublist"})
            for sub_item in sub_items:
                sublist.append(sub_item)
            child.append(sublist)
            rewritten.append(child)
            index = next_index
            continue

        rewritten.append(child)
        index += 1

    return _set_element_children(element, rewritten)


def _rewrite_signal_word_banner_table(element: ET.Element) -> ET.Element:
    if _html_tag_name(element) != "table":
        return element

    head_row = element.find("./thead/tr")
    if head_row is None:
        return element

    head_cells = head_row.findall("./th")
    headers = [_normalize_inline_text("".join(cell.itertext())).lower() for cell in head_cells]
    if headers != ["symbol", "meaning"]:
        return element

    changed = False
    for row in element.findall("./tbody/tr"):
        cells = row.findall("./td")
        if len(cells) != 2:
            continue
        first_cell = cells[0]
        label = _normalize_inline_text("".join(first_cell.itertext())).upper()
        banner_src = _SIGNAL_WORD_BANNERS.get(label)
        if not banner_src:
            continue

        image = ET.Element(
            "img",
            {
                "alt": f"{label} banner placeholder.",
                "src": banner_src,
                "style": "width: 140px;",
            },
        )
        _set_element_children(first_cell, [image])
        first_cell.text = None
        changed = True

    return element if changed else element


def _build_alert_table(label: str, body_nodes: list[ET.Element]) -> ET.Element:
    table = ET.Element(
        "table",
        {
            "class": "manual-callout-table",
            "style": "width:100%; border-collapse:collapse; margin:0 0 16px 0;",
        },
    )
    tbody = ET.SubElement(table, "tbody")
    row = ET.SubElement(tbody, "tr")

    label_cell = ET.SubElement(
        row,
        "td",
        {
            "class": "manual-callout-label",
            "style": "width:16%; border:1px solid #888; padding:6px 8px; vertical-align:top; background:#f3c27b;",
        },
    )
    label_p = ET.SubElement(label_cell, "p")
    label_strong = ET.SubElement(label_p, "strong")
    label_strong.text = label

    body_cell = ET.SubElement(
        row,
        "td",
        {
            "class": "manual-callout-body",
            "style": "border:1px solid #888; padding:6px 8px; vertical-align:top;",
        },
    )
    if not body_nodes:
        ET.SubElement(body_cell, "p")
        return table

    for node in body_nodes:
        body_cell.append(deepcopy(node))
    return table


def _rewrite_word_friendly_children(children: list[ET.Element]) -> list[ET.Element]:
    normalized_children: list[ET.Element] = []
    for child in children:
        rewritten_child = deepcopy(child)
        if list(rewritten_child):
            _set_element_children(
                rewritten_child,
                _rewrite_word_friendly_children(list(rewritten_child)),
            )
        rewritten_child = _rewrite_known_safety_sublists(rewritten_child)
        rewritten_child = _rewrite_signal_word_banner_table(rewritten_child)
        normalized_children.append(rewritten_child)

    rewritten: list[ET.Element] = []
    index = 0
    while index < len(normalized_children):
        child = normalized_children[index]
        child_tag = _html_tag_name(child)
        child_classes = _html_class_names(child)

        if child_tag == "section" and "manual-cover" in child_classes:
            title = _normalize_inline_text("".join(child.itertext()))
            if title:
                heading = ET.Element("h1")
                heading.text = title
                rewritten.append(heading)
            index += 1
            continue

        if child_tag == "div" and "hb-warning-box" in child_classes:
            warning_text = ""
            for node in child.iter():
                if "hb-warning-text" in _html_class_names(node):
                    warning_text = _normalize_inline_text("".join(node.itertext()))
                    break
            body_nodes: list[ET.Element] = []
            if warning_text:
                para = ET.Element("p")
                para.text = warning_text
                body_nodes.append(para)
            rewritten.append(_build_alert_table("WARNING", body_nodes))
            index += 1
            continue

        alert_label = _extract_alert_label(child)
        if alert_label is not None:
            body_nodes: list[ET.Element] = []
            next_index = index + 1
            saw_terminal_block = False
            while next_index < len(normalized_children):
                next_child = normalized_children[next_index]
                next_tag = _html_tag_name(next_child)
                if next_tag == "div" and "manual-page-break" in _html_class_names(next_child):
                    break
                if _extract_alert_label(next_child) is not None:
                    break
                if next_tag in {"h1", "h2", "h3", "section"}:
                    break
                if _is_standalone_strong_paragraph(next_child):
                    break
                if saw_terminal_block:
                    break
                if next_tag in {"ul", "ol", "img", "table"}:
                    body_nodes.append(next_child)
                    saw_terminal_block = True
                    next_index += 1
                    continue
                if next_tag in {"p", "div"}:
                    body_nodes.append(next_child)
                    next_index += 1
                    continue
                break

            if body_nodes:
                rewritten.append(_build_alert_table(alert_label, body_nodes))
                index = next_index
                continue

        rewritten.append(child)
        index += 1

    return rewritten


def _rewrite_word_friendly_fragment(fragment: str) -> str:
    wrapped = f"<root>{fragment}</root>"
    try:
        root = ET.fromstring(wrapped)
    except ET.ParseError:
        return fragment

    rewritten = _rewrite_word_friendly_children(list(root))
    return "".join(ET.tostring(node, encoding="unicode", method="html") for node in rewritten)


def _normalize_sphinx_only_blocks_for_docutils(rst_text: str) -> str:
    """
    Convert Sphinx-only blocks for docutils parsing:
    - keep `.. only:: html` content
    - drop non-html `.. only:: ...` content (e.g. latex)
    """
    lines = rst_text.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        if stripped.startswith(".. only::"):
            expr = stripped.split("::", 1)[1].strip().lower()
            i += 1
            block: list[str] = []
            while i < len(lines):
                cur = lines[i]
                cur_stripped = cur.lstrip()
                cur_indent = len(cur) - len(cur_stripped)
                if cur_stripped and cur_indent <= indent:
                    break
                block.append(cur)
                i += 1

            if expr == "html":
                base = indent + 3
                for b in block:
                    if not b.strip():
                        out.append("")
                    elif len(b) > base:
                        out.append(b[base:])
                    else:
                        out.append(b.lstrip())
            continue

        out.append(line)
        i += 1

    return "\n".join(out)


def _extract_rst_first_heading(text: str) -> tuple[str | None, str | None]:
    lines = text.splitlines()
    for idx in range(len(lines) - 1):
        title = lines[idx].strip()
        underline = lines[idx + 1].strip()
        if not title or title.startswith(".. "):
            continue
        if not underline:
            continue
        if len(set(underline)) != 1:
            continue
        ch = underline[0]
        if ch not in _RST_HEADING_CHARS:
            continue
        if len(underline) < len(title):
            continue
        return title, ch
    return None, None


def _resolve_fragment_asset_path(src: str, source_path: Path) -> Path | None:
    candidate = src.strip()
    if not candidate or candidate.startswith(("http://", "https://", "data:", "file:", "#")):
        return None

    raw_path = Path(candidate)
    probe_paths: list[Path] = []
    if raw_path.is_absolute():
        probe_paths.append(raw_path)
    else:
        probe_paths.extend(
            [
                source_path.parent / raw_path,
                source_path.parent.parent / raw_path,
                paths.docs_dir / raw_path,
                paths.root / raw_path,
            ]
        )

    for probe in probe_paths:
        if probe.exists() and probe.is_file():
            return probe.resolve()
    return None


def _stage_fragment_assets(fragment: str, source_path: Path, bundle_dir: Path) -> str:
    assets_dir = bundle_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    staged: dict[str, str] = {}

    def replace_src(match: re.Match[str]) -> str:
        prefix, src, suffix = match.groups()
        resolved = _resolve_fragment_asset_path(src, source_path)
        if resolved is None:
            return match.group(0)

        key = str(resolved)
        staged_name = staged.get(key)
        if staged_name is None:
            digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:10]
            staged_name = f"{resolved.stem}_{digest}{resolved.suffix}"
            shutil.copy2(resolved, assets_dir / staged_name)
            staged[key] = staged_name

        return f"{prefix}{(assets_dir / staged_name).resolve().as_uri()}{suffix}"

    return _IMG_SRC_RE.sub(replace_src, fragment)


def _convert_rst_fragment_to_html(
    rst_text: str,
    source_path: Path,
    bundle_dir: Path,
) -> str:
    from docutils.core import publish_parts

    normalized_rst = _normalize_sphinx_only_blocks_for_docutils(rst_text)
    parts = publish_parts(
        source=normalized_rst,
        source_path=str(source_path),
        writer_name="html5",
        settings_overrides={
            "report_level": 5,
            "halt_level": 6,
            "file_insertion_enabled": False,
            "raw_enabled": True,
            "syntax_highlight": "none",
        },
    )
    fragment = parts.get("fragment") or parts.get("body") or parts.get("html_body")
    if not fragment:
        raise RuntimeError("docutils did not return an HTML fragment for the RST input")
    html_fragment = fragment.strip()

    title, adorn = _extract_rst_first_heading(normalized_rst)
    if title and adorn == "=":
        title_html = html.escape(rst_escape(title))
        html_fragment = f"<h1>{title_html}</h1>{html_fragment}"

    rewritten_fragment = _rewrite_word_friendly_fragment(html_fragment)
    return _stage_fragment_assets(rewritten_fragment, source_path, bundle_dir)


def build_word_bundle_html(
    cfg: dict,
    model: str | None,
    region: str | None,
    *,
    materialized_bundle: MaterializedBundle | None = None,
    output_dir: Path | None = None,
) -> tuple[Path, Path | None, tuple[WordBundlePageMeta, ...]]:
    materialized = materialized_bundle or materialize_bundle(cfg, model, region)
    title = materialized.title
    reference_doc = materialized.reference_doc

    bundle_output_dir = output_dir or (paths.docs_build_dir / "word")
    bundle_output_dir.mkdir(parents=True, exist_ok=True)
    bundle_html = bundle_output_dir / "manual_bundle.html"

    body_parts: list[str] = []
    page_metas: list[WordBundlePageMeta] = []
    previous_was_cover = False
    for idx, rst_path in enumerate(materialized.page_paths):
        if idx > 0 and not previous_was_cover:
            body_parts.append(_render_page_break_html())
        rst_text = rst_path.read_text(encoding="utf-8")
        html_fragment = _convert_rst_fragment_to_html(rst_text, rst_path, bundle_output_dir)
        body_parts.append(html_fragment or "<div></div>")
        page_metas.append(
            WordBundlePageMeta(
                source_path=rst_path,
                anchor_text=_extract_word_anchor_text(html_fragment),
            )
        )
        previous_was_cover = rst_path.name.startswith("cover")

    html_doc = "".join(
        [
            "<!DOCTYPE html>",
            '<html lang="en">',
            "<head>",
            '<meta charset="utf-8"/>',
            f"<title>{html.escape(title)}</title>",
            "<style>",
            "body { font-family: Calibri, Arial, sans-serif; line-height: 1.45; margin: 0; }",
            "h1, h2 { page-break-after: avoid; }",
            ".hb-h1-pill { margin: 10px 0 12px 0; font-size: 20pt; }",
            ".hb-subbar { margin: 10px 0 12px 0; font-size: 14pt; }",
            ".hb-spec-section { margin: 8px 0 6px 0; font-size: 12pt; }",
            ".manual-cover { min-height: 85vh; display: flex; align-items: center; justify-content: center; text-align: center; }",
            ".manual-cover .cover-title { font-size: 24pt; font-weight: 700; }",
            ".manual-page-break { page-break-after: always; }",
            ".manual-table { width: 100%; border-collapse: collapse; margin: 0 0 16px 0; }",
            ".manual-table td { border: 1px solid #888; padding: 6px 8px; vertical-align: top; }",
            ".manual-table td:first-child { width: 34%; }",
            ".manual-callout-table { width: 100%; border-collapse: collapse; margin: 0 0 16px 0; }",
            ".manual-callout-table td { border: 1px solid #888; padding: 6px 8px; vertical-align: top; }",
            ".manual-callout-table td:first-child { width: 16%; }",
            "p, li { font-size: 10.5pt; }",
            "</style>",
            "</head>",
            "<body>",
            "".join(body_parts),
            "</body>",
            "</html>",
        ]
    )
    bundle_html.write_text(_inject_img_dimensions(html_doc), encoding="utf-8")
    return bundle_html, reference_doc, tuple(page_metas)
