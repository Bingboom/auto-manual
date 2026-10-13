"""Derive the JE-3600A CN and JP Web-layout editions from the reviewed packages.

The same file lives in both editions; it derives the one it sits in (CN/zh or
JP/ja). Run from the repository root:

    python data/manual_sources/JE-3600A/JP/git-20261013-fd06cd04-web-layout/derive_web_layout.py
    python data/manual_sources/JE-3600A/CN/git-20261013-caa5370a-web-layout/derive_web_layout.py

The reviewed package next to this edition stays immutable. Every derived file is
regenerated from it on each run, so a second run leaves the tree unchanged:

* ``source/<language>/content.json``: the reviewed flow with the print layout
  restored; every edit is listed in ``source/<language>/web_layout.json``;
* ``assets/`` and ``assets_manifest.json``: the reviewed art pool plus the assets
  the passes add (a shared copy, native PDF vectors and art without a crop sliver),
  each recorded after the reviewed records;
* byte copies of the PDF and the reviewed source records (text ledger, native
  pages, normalizations, art recipes, layout review).

Hand-written files are never touched: README.md, rebuild.py, source/differences.md,
source/presentation.css, source/refresh_manifest.py and source/approval.json.

Wording rule: visible copy keeps the reviewed strings. The only copy edits restore
the authoritative PDF where the reviewed intake disagreed with it; each one is
listed in web_layout.json under "copy_restorations". Spaces the intake inserted
at print line wraps between CJK characters are removed as one class of
restoration (each instance logged); every other change is structure, weight,
line breaks or art.
"""
from __future__ import annotations

import copy
import functools
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import unicodedata

HERE = Path(__file__).resolve().parent
REPO = next(p for p in HERE.parents if (p / "build.py").is_file())
sys.path.insert(0, str(REPO))

import fitz  # noqa: E402
from bs4 import BeautifulSoup  # noqa: E402

from tools.asset_pipeline.native_svg import native_symbol_svg  # noqa: E402
from tools.component_specs.model import ComponentSpec  # noqa: E402
from tools.component_specs.reference_figure_adapters import web_reference_figure_projection  # noqa: E402
from tools.manual_ir.components import component_flow_node  # noqa: E402
from tools.manual_ir.flow import flow_nodes_to_html, html_to_flow_nodes  # noqa: E402
from tools.web.callout_ir import render_callout_component  # noqa: E402
from tools.web.composite_presentation import WebCompositeContext  # noqa: E402
from tools.web.embedded_components import _carrier_html  # noqa: E402
from tools.web.presentation import _transform_reference_figure  # noqa: E402
from tools.web.reference_figure_component import _component_contract, _validate_carrier  # noqa: E402
from tools.web.warranty_component import render_warranty_component  # noqa: E402

TARGETS = {
    "CN": {"approved": "git-20261012-caa5370a-reviewed", "language": "zh",
           "pdf": "电小二户外电源 3600 Plus.pdf"},
    "JP": {"approved": "git-20261012-fd06cd04-reviewed", "language": "ja",
           "pdf": "Jackery ポータブル電源 3600 Plus 取扱説明書.pdf"},
}
REGION = HERE.parent.name
TARGET = TARGETS[REGION]
APPROVED = HERE.parent / TARGET["approved"]
LANGUAGE = TARGET["language"]
FLOW = "manual-flow/v2"
COPIED = ("source/artwork-recipes.json", "source/layout-artwork-recipes.json",
          "source/layout-review.json", "source/native-pages.json", "source/text-ledger.json",
          "source/unicode-normalizations.json")

INLINE = {"text", "strong", "emphasis", "inline_group", "link", "superscript", "subscript",
          "small_text", "code", "abbreviation", "line_break", "image", "comment"}
WS = re.compile(r"\s+")
LIST_MARKER = re.compile(r"^\s*(?:[•・●◦▪]\s*|\d+\.(?:\s+|(?=[^\d\s])))")
# A print line ending one of these, with room left on the line, ends its print line on purpose.
FINAL = "。．！？：:；;）)」』"
MEDIUM = "ht-print-medium"
SOURCE_LINE = "ht-source-line"

# LCD table glyphs reused from JHP-3600A that differ from this print: (page, name, reviewed asset).
LCD_NATIVE = {
    "JP": [(10, "バッテリー節約モード", "lcd-battery-saving.png"), (10, "自家発電モード", "lcd-self-powered.png"),
           (11, "AC入力電力表示", "lcd-ac-wall-charging.png"), (11, "シガーソケット入力電", "lcd-car-charging.png"),
           (11, "ソーラー(グリーンエネ", "lcd-solar-charging.png"), (11, "バッテリーパックインジ", "lcd-connected-batteries.png"),
           (11, "高温インジケーター", "lcd-high-temperature.png"), (11, "低温インジケーター", "lcd-low-temperature.png")],
    "CN": [(5, "节省电池模式", "lcd-battery-saving.png"), (5, "自发自用模式", "lcd-self-powered.png"),
           (6, "市电充电接入", "lcd-ac-wall-charging.png"), (6, "车充充电接入", "lcd-car-charging.png"),
           (6, "太阳能（绿色", "lcd-solar-charging.png"), (7, "加电包接入", "lcd-connected-batteries.png"),
           (7, "高温警告", "lcd-high-temperature.png"), (7, "低温警告", "lcd-low-temperature.png")],
}
LCD_ICON_COLUMN = {"JP": (48.0, 84.0), "CN": (45.0, 80.0)}   # x range of the print's icon column (pt)
SPEC_CHAPTER = {"JP": "page-25", "CN": "page-19"}
LCD_CHAPTERS = {"JP": ["page-10", "page-11"], "CN": ["page-5", "page-6", "page-7"]}
# The open warning triangle of CN p15, copied byte for byte from the shared symbol set.
SHARED_TRIANGLE_SOURCE = "docs/renderers/web/assets/shared/symbols/native-v1/symbol_warning_triangle.svg"
# JP p14: the in-text 12H glyph (drawings 526-537) and both in-text copies in the art (page pt).
ENERGY_GLYPH = [303.6, 89.2, 318.5, 100.5]
ENERGY_ART_HOLES = [[303.6, 89.2, 318.5, 100.5], [293.5, 238.3, 309.5, 250.5]]
ENERGY_ART_ORIGIN = (28.482098388671876, 45.785595703125)   # the reviewed art's crop origin
# Reviewed art whose crop reaches 1-2 pt into the note box next to it: (chapter, asset,
# page rectangle of that box, the art's page origin, what the box is).
CROP_SLIVERS = {
    "CN": [("page-20", "app-controls-p20.svg", [[28.0, 380.0, 341.0, 400.5]], (28.0, 398.0), "备注 box above")],
    "JP": [("page-28", "app-phones-native-p28.svg", [[27.0, 369.0, 341.0, 402.0]], (0.0, 0.0), "備考 box below")],
}


# ---- flow helpers -------------------------------------------------------------
def node(kind: str, children=(), **fields) -> dict:
    if kind in {"image", "line_break", "thematic_break", "column"}:
        return {"kind": kind, **fields}
    return {"kind": kind, **fields, "children": list(children)}


def text(value: str) -> dict:
    return {"kind": "text", "text": value}


def attrs(value: str) -> dict:
    return {"html": {"attributes": {"class": value}}}


def css_class(item) -> str:
    if not isinstance(item, dict):
        return ""
    value = (((item.get("presentation") or {}).get("html") or {}).get("attributes") or {}).get("class", "")
    return " ".join(value) if isinstance(value, list) else str(value or "")


def has_class(item, name: str) -> bool:
    return name in css_class(item).split()


def add_class(item: dict, name: str) -> None:
    present = item.setdefault("presentation", {}).setdefault("html", {}).setdefault("attributes", {})
    value = present.get("class", "")
    names = value if isinstance(value, list) else str(value or "").split()
    if name not in names:
        present["class"] = " ".join([*names, name]) if not isinstance(value, list) else [*names, name]


def flow_root(item: dict) -> dict:
    return {"schema_version": FLOW, **{k: v for k, v in item.items() if k != "schema_version"}}


def bare(item: dict) -> dict:
    return {k: v for k, v in item.items() if k != "schema_version"}


def markup(fragment: str) -> list[dict]:
    return [bare(item) for item in html_to_flow_nodes(fragment)]


def to_html(nodes: list[dict]) -> str:
    return flow_nodes_to_html([flow_root(copy.deepcopy(n)) for n in nodes])


def component_id(item) -> str | None:
    return item.get("component_spec", {}).get("component_id") if isinstance(item, dict) and item.get("kind") == "component" else None


def slot(spec: dict, role: str) -> dict:
    return next(s for s in spec["slots"] if s["role"] == role)


def walk(items, carriers: bool = True):
    """Yield (owner list, index, node) for every flow node below ``items``."""
    for index, item in enumerate(items):
        yield items, index, item
        if isinstance(item, dict):
            yield from walk(item.get("children", []), carriers)
            if carriers and item.get("kind") == "component" and item.get("carrier_flow"):
                yield from walk(item["carrier_flow"], carriers)


def text_of(item) -> str:
    if isinstance(item, list):
        return "".join(text_of(child) for child in item)
    if not isinstance(item, dict):
        return ""
    if item.get("kind") == "text":
        return item.get("text", "")
    if item.get("kind") == "line_break":
        return "\n"
    return "".join(text_of(child) for child in item.get("children", []))


def is_container(item) -> bool:
    """A node that directly holds inline content (paragraph, cell, list item, caption line...)."""
    if not isinstance(item, dict) or item.get("kind") in INLINE or item.get("kind") == "component":
        return False
    return any(isinstance(c, dict) and c.get("kind") in INLINE - {"image", "line_break"}
               for c in item.get("children", []))


def is_cjk(ch: str) -> bool:
    if not ch:
        return False
    name = unicodedata.name(ch, "")
    return (any(t in name for t in ("CJK", "HIRAGANA", "KATAKANA", "FULLWIDTH", "IDEOGRAPHIC", "CIRCLED"))
            or ch in "。、「」『』（）・：；！？～ー〜※■●◦…“”‘’—")


def _points(d: str):
    """Every end and control point of an absolute M/L/C/H/V/Z path (enough for its bounds)."""
    number = r"-?\d*\.?\d+(?:e-?\d+)?"
    x = y = 0.0
    for command, args in re.findall(r"([MLCHVZ])([^MLCHVZ]*)", d):
        values = [float(v) for v in re.findall(number, args)]
        if command in "MLC":
            for i in range(0, len(values) - 1, 2):
                x, y = values[i], values[i + 1]
                yield x, y
        elif command == "H":
            for x in values:
                yield x, y
        elif command == "V":
            for y in values:
                yield x, y


def svg_without(data: bytes, holes: list[list[float]], origin: tuple[float, float]) -> tuple[bytes, int]:
    """Drop the art paths lying wholly inside the given page rectangles (the rest stays byte-faithful)."""
    import xml.etree.ElementTree as ET
    namespace = "http://www.w3.org/2000/svg"
    root = ET.fromstring(data)
    rects = [fitz.Rect(h[0] - origin[0], h[1] - origin[1], h[2] - origin[0], h[3] - origin[1]) for h in holes]
    removed = 0

    def matrix_of(element, parent):
        raw = element.get("transform", "")
        if not raw:
            return parent
        values = [float(v) for v in re.split(r"[\s,]+", re.fullmatch(r"matrix\(([^)]+)\)", raw).group(1).strip())]
        return fitz.Matrix(*values) * parent

    def visit(element, matrix):
        nonlocal removed
        for child in list(element):
            tag = child.tag.rsplit("}", 1)[-1]
            if tag in ("defs", "clipPath"):
                continue
            local = matrix_of(child, matrix)
            if tag == "path" and child.get("d"):
                points = [fitz.Point(x, y) * local for x, y in _points(child.get("d"))]
                if points:
                    box = fitz.Rect(min(p.x for p in points), min(p.y for p in points),
                                    max(p.x for p in points), max(p.y for p in points))
                    if any(rect.contains(box) for rect in rects):
                        element.remove(child)
                        removed += 1
                        continue
            visit(child, local)

    if root.tag != "{%s}svg" % namespace:
        raise ValueError("expected an SVG document")
    visit(root, fitz.Matrix(1, 0, 0, 1, 0, 0))
    # Serialize SVG as the default namespace, as native_svg does; without this the prefix
    # depended on whether native_svg had already registered it in this process.
    ET.register_namespace("", namespace)
    return ET.tostring(root, encoding="unicode").encode(), removed


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---- print lines ----------------------------------------------------------------
class Print:
    """The reviewed text ledger with native span fonts: print lines, their geometry and weight."""

    def __init__(self, document: fitz.Document):
        self.document = document
        self._panels: dict[int, list] = {}
        self.ledger = json.loads((APPROVED / "source/text-ledger.json").read_text())
        native = json.loads((APPROVED / "source/native-pages.json").read_text())
        mapping = json.loads((APPROVED / "source/unicode-normalizations.json").read_text())["mapping"]
        self.mapping = {chr(int(k, 16)): v for k, v in mapping.items()}
        self.native = {line["id"]: line for page in native for line in page["lines"]}
        self.by_page: dict[int, list[dict]] = {}
        for row in self.ledger:
            if row.get("web_role", "").startswith("paper-footer") or not self.key(row["text"]):
                continue
            self.by_page.setdefault(row["physical_page"], []).append(row)
        self.used: set[str] = set()

    def norm(self, value: str) -> str:
        return "".join(self.mapping.get(ch, ch) for ch in value)

    def key(self, value: str) -> str:
        return WS.sub("", self.norm(value))

    def size(self, row: dict) -> float:
        return float(self.native.get(row["id"], {}).get("size") or 7)

    def variants(self, row: dict) -> set[str]:
        return {v for v in (self.key(row["text"]), self.key(LIST_MARKER.sub("", self.norm(row["text"]))))
                if len(v) >= 2}

    def weights(self, row: dict) -> list[str | None]:
        """Print weight per non-space character of the line: B(old), M(edium), R(egular), None."""
        out: list[str | None] = []
        for span in self.native.get(row["id"], {}).get("spans", []):
            font = span.get("font", "")
            lower = font.lower()
            if not (lower.startswith(("notosansjp", "notosanscjk", "kozgo")) or lower.startswith("fzlt")):
                weight = None   # Latin display faces and symbol fonts keep the reviewed weight
            elif any(t in lower for t in ("bold", "black", "heavy", "fzltchjw", "fzltdhk")):
                weight = "B"
            elif any(t in lower for t in ("medium", "fzltzhjw", "fzlthk")):
                # 兰亭黑 (FZLTHK) sits between the 细黑 body and 中黑: it reads as a light emphasis.
                weight = "M"
            else:
                weight = "R"
            out.extend(weight for ch in self.norm(span.get("text", "")) if not ch.isspace())
        return out

    def follows(self, prev: dict | None, row: dict) -> bool:
        if prev is None or prev["physical_page"] != row["physical_page"]:
            return False
        size = self.size(prev)
        dy = row["bbox"][1] - prev["bbox"][1]
        if abs(dy) < size * .4:
            return -2 * size < row["bbox"][0] - prev["bbox"][2] < 3 * size
        return size * .3 < dy < size * 2.8 and row["bbox"][0] < prev["bbox"][2] + size

    def tiles(self, K: str, pages: list[int]) -> list[tuple[int, int, dict, str]]:
        """Cover K with whole print lines: most characters, then most line-to-line continuity."""
        candidates = [row for page in pages for row in self.by_page.get(page, [])]
        occ: dict[int, list[tuple[int, dict, str]]] = {}
        for row in candidates:
            for variant in self.variants(row):
                for match in re.finditer(re.escape(variant), K):
                    occ.setdefault(match.start(), []).append((match.end(), row, variant))
        by_id = {row["id"]: row for row in candidates}

        @functools.lru_cache(maxsize=None)
        def best(pos: int, prev_id: str | None):
            if pos >= len(K):
                return (0, 0, 0), ()
            score, path = best(pos + 1, None)
            choice = (score, path)
            prev = by_id.get(prev_id) if prev_id else None
            for end, row, variant in occ.get(pos, []):
                # a short line (a title, a label) only counts as a whole container or in sequence
                if len(variant) < 6 and pos and end != len(K) and not self.follows(prev, row):
                    continue
                sub, rest = best(end, row["id"])
                total = (sub[0] + end - pos, sub[1] + (1 if self.follows(prev, row) else 0),
                         sub[2] + (0 if row["id"] in self.used else 1))
                if total > choice[0]:
                    choice = (total, ((pos, end, row["id"], variant),) + rest)
            return choice

        _, path = best(0, None)
        self.used.update(rid for _, _, rid, _ in path)
        return [(s, e, by_id[rid], v) for s, e, rid, v in path]

    def right_edge(self, page: int, a: dict, b: dict) -> float:
        """The right edge of a's column: the widest nearby line starting within 2.5 em of a or b,
        or the inner edge of the smallest drawn panel holding a, whichever reaches further."""
        size = self.size(a)
        lefts = (a["bbox"][0], b["bbox"][0])
        near = [r["bbox"][2] for r in self.by_page.get(page, [])
                if min(abs(r["bbox"][0] - x) for x in lefts) < 2.5 * size
                and abs(r["bbox"][1] - a["bbox"][1]) < 60 and r["bbox"][2] > a["bbox"][0]]
        edges = [*near, a["bbox"][2]]
        panel = self.panel(a)
        if panel is not None:
            edges.append(panel.x1 - (a["bbox"][0] - panel.x0))
        if a.get("web_role") == "body":
            # body text: the document's own column on pages of the same side
            peers = sorted(r["bbox"][2] for rows in self.by_page.values() for r in rows
                           if r.get("web_role") == "body" and abs(r["bbox"][0] - a["bbox"][0]) < 2.0
                           and r["physical_page"] % 2 == a["physical_page"] % 2)
            if len(peers) >= 5:
                edges.append(peers[int(len(peers) * .95) - 1])
        return max(edges)

    def panel(self, row: dict):
        """The smallest drawn rectangle (panel, card or cell) around a print line, if any."""
        page = row["physical_page"]
        if page not in self._panels:
            source = self.document[page - 1]
            self._panels[page] = [fitz.Rect(d["rect"]) for d in source.get_drawings()
                                  if d["rect"].width < source.rect.width * .9
                                  and d["rect"].height > 6 and d["rect"].width > 20]
        box = fitz.Rect(row["bbox"])
        inside = [r for r in self._panels[page] if r.x0 - 1 <= box.x0 and r.x1 + 1 >= box.x1
                  and r.y0 - 1 <= box.y0 and r.y1 + 1 >= box.y1]
        return min(inside, key=lambda r: r.width * r.height) if inside else None


# ---- inline containers ------------------------------------------------------------
class Inline:
    """The visible characters of one container, mapped back to their text nodes."""

    def __init__(self, item: dict, printed: Print):
        self.item = item
        self.slots: list[tuple[list | None, dict | None, int]] = []   # (owner, node, offset)
        self.chars: list[str] = []
        self.weight: list[str] = []
        self._collect(item.get("children", []), "R")
        self.T = "".join(self.chars)
        norm = printed.norm(self.T)
        self.k_map = [i for i, ch in enumerate(norm) if not ch.isspace() and ch != "￼"]
        self.K = "".join(norm[i] for i in self.k_map)

    def _collect(self, children: list, weight: str) -> None:
        for child in children:
            if not isinstance(child, dict):
                continue
            kind = child.get("kind")
            if kind == "text":
                for offset, ch in enumerate(child.get("text", "")):
                    self.slots.append((children, child, offset))
                    self.chars.append(ch)
                    self.weight.append(weight)
            elif kind == "line_break":
                self.slots.append((children, child, -1))
                self.chars.append("\n")
                self.weight.append(weight)
            elif kind == "image":
                self.slots.append((children, child, -1))
                self.chars.append("￼")
                self.weight.append(weight)
            elif kind == "strong":
                self._collect(child.get("children", []), "B")
            elif kind == "inline_group" and has_class(child, MEDIUM):
                self._collect(child.get("children", []), "M")
            elif kind in INLINE:
                self._collect(child.get("children", []), weight)

    def owner_class(self, t: int) -> str:
        """Class of the source-line span holding character t, if any."""
        owner, _, _ = self.slots[t]
        for _, _, n in walk(self.item.get("children", []), carriers=False):
            if isinstance(n, dict) and n.get("children") is owner:
                return css_class(n)
        return ""

    def delete(self, start: int, end: int) -> None:
        by_node: dict[int, tuple[dict, list[int]]] = {}
        for t in range(start, end):
            _, n, offset = self.slots[t]
            if n is not None and n.get("kind") == "text":
                by_node.setdefault(id(n), (n, []))[1].append(offset)
        for n, offsets in by_node.values():
            value = n["text"]
            n["text"] = "".join(ch for i, ch in enumerate(value) if i not in set(offsets))
            if not n["text"].strip() and value.strip() == "":
                n["text"] = ""

    def insert_break(self, t: int) -> None:
        owner, n, offset = self.slots[t]
        position = next(i for i, child in enumerate(owner) if child is n)
        if n.get("kind") == "text" and offset > 0:
            right = text(n["text"][offset:])
            n["text"] = n["text"][:offset]
            owner[position + 1:position + 1] = [{"kind": "line_break"}, right]
        else:
            owner.insert(position, {"kind": "line_break"})


def regroup(children: list, desired: list[str | None], counter: list[int], weight: str = "R") -> list:
    """Rebuild inline children so each character carries its print weight (strong / medium span)."""
    atoms: list = []

    def flatten(items: list, current: str) -> list:
        out = []
        for child in items:
            kind = child.get("kind")
            if kind == "text":
                for ch in child.get("text", ""):
                    want = desired[counter[0]]
                    counter[0] += 1
                    out.append(("ch", ch, want or current))
            elif kind in ("line_break", "image"):
                counter[0] += 1
                out.append(("node", child))
            elif kind == "comment":
                out.append(("node", child))
            elif kind == "strong":
                out.extend(flatten(child.get("children", []), "B"))
            elif kind == "inline_group" and has_class(child, MEDIUM):
                out.extend(flatten(child.get("children", []), "M"))
            elif kind in INLINE:
                out.append(("wrap", child, flatten(child.get("children", []), current)))
            else:
                out.append(("node", child))
        return out

    def build(items: list) -> list:
        out: list = []
        run: list[str] = []
        state = {"w": None}

        def flush():
            if run:
                value = text("".join(run))
                if state["w"] == "B":
                    value = node("strong", [value])
                elif state["w"] == "M":
                    value = node("inline_group", [value], presentation=attrs(MEDIUM))
                out.append(value)
                run.clear()

        for atom in items:
            if atom[0] == "ch":
                _, ch, w = atom
                if ch.isspace() and run:
                    w = state["w"]
                if w != state["w"]:
                    flush()
                    state["w"] = w
                run.append(ch)
            elif atom[0] == "wrap":
                flush()
                wrapper = {k: v for k, v in atom[1].items() if k != "children"}
                wrapper["children"] = build(atom[2])
                out.append(wrapper)
                state["w"] = None
            else:
                flush()
                out.append(atom[1])
                state["w"] = None
        flush()
        return out

    atoms = flatten(children, weight)
    return build(atoms)


# ---- derivation -------------------------------------------------------------------
class Derivation:
    def __init__(self, document: fitz.Document):
        self.document = document
        self.content = json.loads((APPROVED / f"source/{LANGUAGE}/content.json").read_text())
        self.print = Print(document)
        self.log: list[dict] = []
        self.restorations: list[dict] = []
        self.new_assets: list[dict] = []

    def note(self, chapter: str, action: str, **detail) -> None:
        self.log.append({"chapter": chapter, "action": action, **detail})

    def restore(self, chapter: str, kind: str, approved: str, pdf: str, **detail) -> None:
        self.restorations.append({"chapter": chapter, "kind": kind, "approved": approved, "pdf": pdf, **detail})

    def chapter(self, chapter_id: str) -> dict:
        return next(c for c in self.content["chapters"] if c["id"] == chapter_id)

    @staticmethod
    def page_of(chapter_id: str) -> int:
        match = re.match(r"page-(\d+)$", chapter_id)
        return int(match.group(1)) if match else 1

    def print_pages(self, chapter_id: str) -> list[int]:
        """Print pages a chapter's lines may come from: its page and the next one. The LCD
        glossary chapter holds the rows of every glossary page (lcd_tables merges them)."""
        page = self.page_of(chapter_id)
        if chapter_id == LCD_CHAPTERS[REGION][0]:
            return sorted({page, page + 1} | {self.page_of(c) for c in LCD_CHAPTERS[REGION]})
        return [page, page + 1]

    def containers(self):
        """Yield (chapter, container, ancestors) for every inline container, components included."""
        def visit(chapter, items, ancestors):
            for item in items:
                if not isinstance(item, dict):
                    continue
                if is_container(item):
                    yield chapter, item, ancestors
                yield from visit(chapter, item.get("children", []), ancestors + (item,))
                if item.get("kind") == "component" and item.get("carrier_flow"):
                    yield from visit(chapter, item["carrier_flow"], ancestors + (item,))

        for chapter in self.content["chapters"]:
            yield from visit(chapter, chapter["nodes"], ())

    # ---- print line seams --------------------------------------------------------
    @staticmethod
    def _prose(item: dict, ancestors: tuple) -> bool:
        """Containers whose print line ends are meaningful (not labels, headings or captions)."""
        if item.get("kind") == "heading" or item.get("kind") == "table_cell" and item.get("header"):
            return False
        if has_class(item, "manual-callout-label") or any(has_class(a, "manual-callout-label") for a in ancestors):
            return False
        if item.get("kind") == "group" and has_class(item, "line"):
            return False
        return item.get("kind") in {"paragraph", "list_item", "table_cell", "group", "caption"}

    def print_lines(self) -> None:
        """Remove spaces the intake added at print line wraps; break lines where the print does."""
        printed = self.print
        removed, breaks, kept = [], [], 0
        for chapter, item, ancestors in self.containers():
            line = Inline(item, printed)
            if len(line.K) < 2:
                continue
            tiles = printed.tiles(line.K, self.print_pages(chapter["id"]))
            starts = {s: (e, r, v) for s, e, r, v in tiles}
            ends = {e: (s, r, v) for s, e, r, v in tiles}
            edits = []
            for p in sorted(set(starts) & set(ends)):
                _, a, va = ends[p]
                _, b, vb = starts[p]
                t_end, t_start = line.k_map[p - 1] + 1, line.k_map[p]
                gap = line.T[t_end:t_start]
                if "￼" in gap or "\n" in gap or a["physical_page"] != b["physical_page"]:
                    continue
                size = printed.size(a)
                cjk = is_cjk(va[-1]) or is_cjk(vb[0])
                same_line = abs(b["bbox"][1] - a["bbox"][1]) < size * .4
                if same_line:
                    if gap and cjk and (b["bbox"][0] - a["bbox"][2]) / size < .25:
                        edits.append(("delete", t_end, t_start, a, b, va, vb))
                    continue
                if b["bbox"][1] <= a["bbox"][1]:
                    continue
                short = (printed.right_edge(a["physical_page"], a, b) - a["bbox"][2]) / size
                token = re.match(r"[A-Za-z0-9°~.,%/+\-−–]+", vb)
                overflow = token is not None and short < .55 * len(token.group(0)) + .5
                forced = self._prose(item, ancestors) and (
                    va[-1] in FINAL and short >= 1.0 or short >= 3.0 and not overflow)
                if forced and line.owner_class(t_start).find(SOURCE_LINE) < 0:
                    edits.append(("break", t_end, t_start, a, b, va, vb))
                elif gap and cjk:
                    edits.append(("delete", t_end, t_start, a, b, va, vb))
                else:
                    kept += 1
            for action, t_end, t_start, a, b, va, vb in sorted(edits, key=lambda e: -e[1]):
                context = va[-12:] + "|" + vb[:12]
                if t_start > t_end:
                    line.delete(t_end, t_start)
                    removed.append({"chapter": chapter["id"], "lines": [a["id"], b["id"]], "at": context})
                if action == "break":
                    line.insert_break(t_end)
                    breaks.append({"chapter": chapter["id"], "lines": [a["id"], b["id"]], "at": context})
        for row in removed:
            self.restore(row["chapter"], "print-wrap-space", row["at"].replace("|", " "), row["at"].replace("|", ""),
                         lines=row["lines"])
        self.note("*", "print-line-breaks", count=len(breaks), breaks=breaks)
        self.note("*", "print-wrap-spaces", count=len(removed), soft_latin_wraps_kept=kept)

    # ---- print weights --------------------------------------------------------------
    @staticmethod
    def _weighted(item: dict, ancestors: tuple) -> bool:
        if item.get("kind") == "heading" or item.get("kind") == "table_cell" and item.get("header"):
            return False
        if any(a.get("kind") == "heading" for a in ancestors):
            return False
        return not (has_class(item, "manual-callout-label") or any(has_class(a, "manual-callout-label") for a in ancestors))

    def print_weights(self) -> None:
        """Every character takes its print weight: bold faces strong, medium faces a 500 span."""
        printed = self.print
        printed.used = set()
        changed = []
        for chapter, item, ancestors in self.containers():
            if not self._weighted(item, ancestors):
                continue
            line = Inline(item, printed)
            if len(line.K) < 2:
                continue
            desired_k: list[str | None] = [None] * len(line.K)
            for s, e, row, variant in printed.tiles(line.K, self.print_pages(chapter["id"])):
                weights = printed.weights(row)
                key = printed.key(row["text"])
                shift = key.find(variant)
                if shift < 0 or len(weights) != len(key):
                    continue
                for i in range(s, e):
                    desired_k[i] = weights[shift + i - s]
            desired_t: list[str | None] = [None] * len(line.T)
            for k, t in enumerate(line.k_map):
                desired_t[t] = desired_k[k]
            diff = [line.K[k] for k, t in enumerate(line.k_map)
                    if desired_k[k] is not None and desired_k[k] != line.weight[t]]
            if not diff:
                continue
            # one desired weight per slot in collection order (text characters, breaks and images)
            item["children"] = regroup(item["children"], desired_t, [0])
            changed.append({"chapter": chapter["id"], "text": "".join(diff)[:40]})
        self.note("*", "print-weights", count=len(changed), containers=changed)

    # ---- shared structure ------------------------------------------------------------
    def find(self, chapter_id: str, predicate, *, count: int = 1, carriers: bool = True) -> list:
        """(owner, index, node) matches in a chapter; the expected count is asserted."""
        found = [(o, i, n) for o, i, n in walk(self.chapter(chapter_id)["nodes"], carriers)
                 if isinstance(n, dict) and predicate(n)]
        if count is not None and len(found) != count:
            raise ValueError(f"{chapter_id}: expected {count} match(es), found {len(found)}")
        return found

    def find_text(self, chapter_id: str, kind: str, value: str, **options) -> list:
        return self.find(chapter_id, lambda n: n.get("kind") == kind and WS.sub("", text_of(n)) == WS.sub("", value),
                         **options)

    def warranty_open(self) -> None:
        """Expose each warranty card's block HTML as flow, so the print passes see its lines."""
        for chapter in self.content["chapters"]:
            for _, _, item in walk(chapter["nodes"], carriers=False):
                if component_id(item) == "HB-WARRANTY-SECTION":
                    blocks = slot(item["component_spec"], "blocks")["content"]
                    item["carrier_flow"] = [node("group", markup(b["html"]), role="container") for b in blocks]

    def warranty_close(self) -> None:
        for chapter in self.content["chapters"]:
            for _, _, item in walk(chapter["nodes"], carriers=False):
                if component_id(item) != "HB-WARRANTY-SECTION":
                    continue
                blocks = slot(item["component_spec"], "blocks")["content"]
                for block, holder in zip(blocks, item.pop("carrier_flow"), strict=True):
                    block["html"] = to_html(holder["children"])
                    soup = BeautifulSoup(block["html"], "html.parser")
                    if block["kind"] == "paragraph":
                        block["text"] = soup.get_text(" ", strip=True)
                    else:
                        block["items"] = [li.get_text(" ", strip=True) for li in soup.find_all("li")]

    def remove_hidden_label(self, chapter_id: str, value: str) -> None:
        """A live label the print paints over (white device fill drawn after the text)."""
        (owner, index, figure), = self.find(chapter_id, lambda n: component_id(n) == "HB-SPECIAL-REFERENCE-FIGURE"
                                            and value in json.dumps(n, ensure_ascii=False))
        spec = figure["component_spec"]
        block = next(n for _, _, n in walk(figure["carrier_flow"]) if has_class(n, "line-block"))
        position = next(i for i, line in enumerate(block["children"]) if text_of(line).strip() == value)
        del block["children"][position]
        captions = slot(spec, "captions")["content"]
        if captions[position]["text"] != value:
            raise ValueError(f"{chapter_id}: caption slot order differs at {value!r}")
        del captions[position]
        layout = spec["metadata"]["base_art_layout"]["labels"]
        layout[:] = [dict(label, line=label["line"] - (label["line"] > position))
                     for label in layout if label["line"] != position]
        spec["metadata"]["capture_following_lines"] = len(captions)
        self.note(chapter_id, "hidden-print-label-removed", figure=spec["source_ref"], label=value)
        self.restore(chapter_id, "hidden-print-text", value, "",
                     reason="painted over by the device drawing in print; not visible")

    # ---- art ---------------------------------------------------------------------------
    def add_asset(self, name: str, data: bytes, **record) -> str:
        self.new_assets.append({"asset": name, **record, "sha256": sha256(data), "_bytes": data})
        return "assets/" + name

    def native_glyph(self, page: int, box: list[float]) -> tuple[bytes, list[int], list[float]]:
        """The print's own vector glyph: every drawing inside the box, nothing else."""
        drawings = self.document[page - 1].get_drawings()
        inside = [i for i, d in enumerate(drawings) if fitz.Rect(box).contains(d["rect"])]
        if not inside:
            raise ValueError(f"p{page}: no glyph drawings inside {box}")
        bounds = fitz.Rect(drawings[inside[0]]["rect"])
        for i in inside[1:]:
            bounds |= drawings[i]["rect"]
        glyph = [round(bounds.x0 - .2, 2), round(bounds.y0 - .2, 2), round(bounds.x1 + .2, 2), round(bounds.y1 + .2, 2)]
        indices = [i for i, d in enumerate(drawings) if fitz.Rect(glyph).contains(d["rect"])]
        return native_symbol_svg(self.document[page - 1], indices, glyph), indices, glyph

    def strip_figure_art(self, chapter_id: str, asset: str, holes: list[list[float]],
                         origin: tuple[float, float], **record) -> tuple[dict, str, int]:
        """Point a reference figure at a copy of its reviewed art without the paths inside holes."""
        old = "assets/" + asset
        (_, _, figure), = self.find(chapter_id, lambda n: component_id(n) == "HB-SPECIAL-REFERENCE-FIGURE"
                                    and n["component_spec"]["assets"][0]["asset_ref"] == old)
        spec = figure["component_spec"]
        art, removed = svg_without((APPROVED / old).read_bytes(), holes, origin)
        if not removed:
            raise ValueError(f"{chapter_id}: no {asset} paths inside {holes}")
        new = self.add_asset(asset.replace(".svg", "-web.svg"), art, candidate=old, removed_paths=removed,
                             removed_bounds=holes, **record)
        spec["assets"][0]["asset_ref"] = new
        spec["metadata"]["base_art_layout"]["art_sha256"] = sha256(art)
        for _, _, n in walk(figure["carrier_flow"]):
            if isinstance(n, dict) and n.get("kind") == "image" and n.get("source") == old:
                n["source"] = new
        return figure, new, removed

    def crop_slivers(self) -> None:
        """App art whose crop reaches into the note box beside it showed a stray line (CN p20 above
        the button panel, JP p28 under the phones). The art drops that box; the live callout keeps it."""
        for chapter_id, asset, holes, origin, where in CROP_SLIVERS[REGION]:
            _, new, removed = self.strip_figure_art(
                chapter_id, asset, holes, origin,
                decision="reviewed art minus the note box clipped into its crop",
                reason=f"The {where} prints as a live callout; every other path is the reviewed art's.")
            self.note(chapter_id, "art-crop-sliver-removed", art=new, removed_paths=removed, box=where)

    def lcd_icons(self) -> None:
        """LCD table glyphs the reviewed edition reused from another model, replaced by this print's own.

        The reused JHP-3600A glyphs lack this display's round and triangular frames, and the
        battery-pack glyph counts x8 where this product prints x5.
        """
        column = LCD_ICON_COLUMN[REGION]
        for page, name, old in LCD_NATIVE[REGION]:
            row = next(r for r in self.print.by_page[page] if WS.sub("", r["text"]).startswith(WS.sub("", name)))
            centre = (row["bbox"][1] + row["bbox"][3]) / 2
            drawings = self.document[page - 1].get_drawings()
            small = [d["rect"] for d in drawings if d["rect"].width < 30 and d["rect"].height < 30
                     and d["rect"].x0 >= column[0] and d["rect"].x1 <= column[1]]
            clusters: list[fitz.Rect] = []
            for rect in sorted(small, key=lambda r: r.y0):
                if clusters and rect.y0 <= clusters[-1].y1 + 3:
                    clusters[-1] |= rect
                else:
                    clusters.append(fitz.Rect(rect))
            box = min(clusters, key=lambda c: abs((c.y0 + c.y1) / 2 - centre))
            if abs((box.y0 + box.y1) / 2 - centre) > 25:
                raise ValueError(f"p{page}: no LCD glyph beside {name!r}")
            data, indices, glyph = self.native_glyph(page, [box.x0 - .5, box.y0 - .5, box.x1 + .5, box.y1 + .5])
            new = old.rsplit(".", 1)[0] + "-native.svg"
            ref = self.add_asset(new, data, decision="native extraction", physical_page=page,
                                 glyph_bbox=glyph, drawing_indices=indices, replaces=old,
                                 reason="The reused JHP-3600A glyph differs from this print (frame or count); "
                                        "native_symbol_svg keeps every source path inside the glyph bounds.")
            # SVG glyphs have no pixel size: show them at their print height relative to the 7 pt table
            # text. A glyph inside a sentence (CN p7 descriptions) keeps the text-height cap instead.
            style = f"height:{(glyph[3] - glyph[1]) / 7:.2f}em;width:auto"
            replaced = 0
            for chapter in self.content["chapters"]:
                for owner, _, item in walk(chapter["nodes"]):
                    if isinstance(item, dict) and item.get("kind") == "image" and item.get("source") == "assets/" + old:
                        item["source"] = ref
                        if not any(isinstance(x, dict) and x.get("kind") == "text" and x.get("text", "").strip()
                                   for x in owner):
                            present = item.setdefault("presentation", {}).setdefault("html", {})
                            present.setdefault("attributes", {})["style"] = style
                        replaced += 1
            if not replaced:
                raise ValueError(f"{old} is not referenced")
            self.note(f"page-{page}", "native-lcd-glyph", entry=name, art=ref, replaced=old, references=replaced)

    def inline_icon_spaces(self) -> None:
        """Spaces that held an inline glyph's place in a print line go once the glyph sits in the text."""
        removed = 0
        for chapter, item, _ in list(self.containers()):
            kids = item.get("children", [])
            for index, child in enumerate(kids[:-1]):
                after = kids[index + 1]
                if (child.get("kind") == "image" and after.get("kind") == "text"
                        and re.match(r"^ {3,}", after.get("text", ""))):
                    approved = after["text"]
                    after["text"] = approved.lstrip(" ")
                    removed += 1
                    self.restore(chapter["id"], "inline-glyph-placeholder", approved[:12], after["text"][:12],
                                 glyph=child.get("source"))
        self.note("*", "inline-glyph-placeholders", count=removed)

    def spec_tables(self) -> None:
        """Specifications: footnote marks and ® print as superscripts; one label width for all grids."""
        chapter_id = SPEC_CHAPTER[REGION]
        marks = tables = 0
        for owner, index, item in list(walk(self.chapter(chapter_id)["nodes"])):
            if not isinstance(item, dict):
                continue
            if item.get("kind") == "table" and has_class(item, "ht-native-table"):
                add_class(item, "ht-spec-grid")
                tables += 1
                for row in item["children"][0]["children"]:
                    if len(row["children"]) >= 2:
                        add_class(row["children"][0], "ht-spec-label")
            elif item.get("kind") == "text" and item.get("text", "").strip() in ("①", "②", "③", "®"):
                owner[index] = node("superscript", [text(item["text"].strip())])
                marks += 1
        self.note(chapter_id, "print-superscripts", marks=marks)
        self.note(chapter_id, "spec-label-column", tables=tables)

    # ---- CN passes ------------------------------------------------------------------
    def cn_titles(self) -> None:
        """p12: the battery-pack title prints without the section dot; p15: the first-use
        warning prints as a bold line behind the print's open warning triangle, not as a section."""
        (_, _, title), = self.find_text("page-12", "heading", "与加电包连接（单独售卖）")
        title["children"] = [node("inline_group", title["children"], presentation=attrs("native-plain-title"))]
        self.note("page-12", "plain-title", title=text_of(title))
        (owner, index, warning), = self.find_text("page-15", "heading", "首次使用前请先将本设备充满电！")
        triangle = self.add_asset("shared-symbol_warning_triangle.svg", (REPO / SHARED_TRIANGLE_SOURCE).read_bytes(),
                                  decision="byte-identical shared reuse",
                                  candidate=SHARED_TRIANGLE_SOURCE,
                                  reason="Print p15 sets the first-use warning behind an open warning triangle.")
        owner[index] = node("paragraph", [node("image", source=triangle, alt=""), node("strong", warning["children"])],
                            presentation=attrs("ht-print-warning-line"))
        self.note("page-15", "print-warning-line", text=text_of(warning), heading_removed=True)

    def cn_voc(self) -> None:
        """p16: Voc prints with a subscript oc, as the reviewed troubleshooting table already sets it."""
        (owner, index, run), = self.find("page-16", lambda n: n.get("kind") == "text" and n.get("text") == "oc")
        owner[index] = node("subscript", [text("oc")])
        self.note("page-16", "print-subscript", text="Voc")

    # ---- JP passes ------------------------------------------------------------------
    def jp_energy_icons(self) -> None:
        """p14: the 12H energy-saving glyph sits in the text, not in the art behind it.

        The print draws the glyph into its line; live Web text cannot hit that spot, so the
        glyph overlapped or drifted from its words. The art drops the two in-text glyphs
        (paths inside their bounds) and the labels carry the print's own vector glyph.
        """
        data, indices, glyph = self.native_glyph(14, ENERGY_GLYPH)
        ref = self.add_asset("native-energy-saving-12h-p14.svg", data, decision="native extraction",
                             physical_page=14, glyph_bbox=glyph, drawing_indices=indices,
                             candidate="docs/templates/word_template/common_assets/operation/energy_saving_12h.svg",
                             reason="The shared 12H icon draws an open circle; the print's glyph is a pill "
                                    "with segment digits. native_symbol_svg keeps every source path.")

        def icon() -> dict:
            return node("image", source=ref, alt="", presentation=attrs("ht-inline-symbol"))

        figure, new, removed = self.strip_figure_art(
            "page-14", "energy-saving-p14.svg", ENERGY_ART_HOLES, ENERGY_ART_ORIGIN,
            decision="reviewed art minus in-text glyphs",
            reason="The 12H glyphs move into the live text; every other path is the reviewed art's.")
        placed = 0
        for _, _, span in walk(figure["carrier_flow"]):
            if not (isinstance(span, dict) and has_class(span, SOURCE_LINE)):
                continue
            value = text_of(span)
            for pattern in (r"^(.*省エネアイコン) {5,}$", r"^(.*画面上の) {5,}(アイ)$"):
                match = re.match(pattern, value)
                if match:
                    children = [text(match.group(1)), icon()] + ([text(match.group(2))] if match.lastindex == 2 else [])
                    span["children"] = children
                    placed += 1
                    self.restore("page-14", "inline-glyph-placeholder", value[-16:], text_of(children)[-8:],
                                 glyph=ref)
        if placed != 2:
            raise ValueError(f"page-14: expected two in-text 12H glyphs, placed {placed}")
        (_, _, heading), = self.find_text("page-14", "heading", "省エネモード")
        heading["children"].append(icon())
        self.note("page-14", "in-text-glyph", glyph=ref, art=new, removed_paths=removed, heading=True)

    def jp_cover(self) -> None:
        """The printed cover (p1) is not part of the Web edition; the TOC (p2) never was."""
        cover = self.chapter("preface")
        self.content["chapters"].remove(cover)
        self.note("preface", "printed-cover-removed", headings=[text_of(n) for n in cover["nodes"]
                                                                 if n.get("kind") == "heading"])

    def jp_safety(self) -> None:
        # p3: the two sub-titles print white on a full-width dark band.
        for title in ("絵表示について", "絵表示の説明"):
            (_, _, heading), = self.find_text("page-3", "heading", title)
            heading["children"] = [node("inline_group", [text(title)], presentation=attrs("native-band"))]
            self.note("page-3", "print-pill-title", title=title)
        # p3: every signal label (警告, 注意, 説明, ヒント) sits in the grey label column.
        for label in ("説明", "ヒント"):
            (owner, index, cell), = self.find("page-3", lambda n, v=label: n.get("kind") == "table_cell"
                                              and text_of(n) == v)
            cell["presentation"] = attrs("ht-cell")
            self.note("page-3", "signal-label-column", label=label)
        # p5: the five symptoms print in a three-column grid, read row by row.
        (_, _, listing), = self.find("page-5", lambda n: n.get("kind") == "list"
                                     and "異音がする" in text_of(n))
        rows = [r for r in self.print.by_page[5]
                if any(WS.sub("", r["text"]).endswith(v) for v in ("異臭がする", "破損したとき", "異音がする",
                                                                   "入ったとき", "傷んだとき"))]
        printed = sorted(rows, key=lambda r: (round(r["bbox"][1]), r["bbox"][0]))
        before = [WS.sub("", text_of(item)) for item in listing["children"]]
        order = []
        for row in printed:
            key = WS.sub("", row["text"]).lstrip("・")
            order.append(next(i for i, value in enumerate(before) if value == key))
        if sorted(order) != list(range(len(before))):
            raise ValueError("page-5: symptom list does not match the print grid")
        listing["children"] = [listing["children"][i] for i in order]
        add_class(listing, "ht-print-grid-3")
        if order != list(range(len(before))):
            self.restore("page-5", "print-order", " / ".join(before),
                         " / ".join(before[i] for i in order))
        self.note("page-5", "print-grid", columns=3, items=len(order))

    def jp_caution_lockup(self) -> None:
        """p6: the outlined ご注意 panel prints the dark warning triangle beside a large label."""
        (_, _, callout), = self.find("page-6", lambda n: component_id(n) == "HB-CALLOUT-STRIP")
        table = callout["carrier_flow"][0]
        add_class(table, "hb-source-warning-lockup")
        label = next(n for _, _, n in walk(table["children"]) if has_class(n, "manual-callout-label"))
        value = text_of(label).strip()
        label["children"] = [node("inline_group", [
            node("image", source="assets/shared-h1-jp-warning_triangle.svg", alt=""), text(value)],
            presentation=attrs("hb-warning-lockup"))]
        self.note("page-6", "signal-lockup", label=value)

    def jp_package(self) -> None:
        # p8: the closing remark prints with its square bullet, bold.
        (_, _, para), = self.find_text("page-8", "paragraph", "本機の仕様および外観は、改善のため予告なく変更することがあります。")
        row = next(r for r in self.print.by_page[8] if "本機の仕様" in r["text"])
        if not row["text"].lstrip().startswith("■"):
            # the square is a drawn glyph in print, not text: render it as a list marker
            add_class(para, "ht-square-note")
        self.note("page-8", "print-square-note")
        # p8: the three notes print in a white panel with a grey outline (stroke only, no fill).
        (_, _, panel), = self.find("page-8", lambda n: n.get("kind") == "group" and has_class(n, "ht-native-note-panel"))
        panel["presentation"] = attrs("ht-print-outline-panel")
        self.note("page-8", "print-outline-panel")

    def lcd_tables(self) -> None:
        """LCD glossary: one table (print splits it at page breaks), cells tagged by role.

        Names print bold (one or two lines); in JP an App note follows in small type.
        """
        groups = []
        for chapter_id in LCD_CHAPTERS[REGION]:
            found = [(chapter_id, i, n) for i, n in enumerate(self.chapter(chapter_id)["nodes"])
                     if n.get("kind") == "group" and any(c.get("kind") == "table" for c in n.get("children", []))]
            if len(found) != 1:
                raise ValueError(f"{chapter_id}: expected one LCD glossary table, found {len(found)}")
            groups.extend(found)
        first = next(c for c in groups[0][2]["children"] if c.get("kind") == "table")
        add_class(first, "ht-lcd-icons")
        rows = first["children"][0]["children"]
        for chapter_id, index, wrapper in groups[1:]:
            table = next(c for c in wrapper["children"] if c.get("kind") == "table")
            rows.extend(table["children"][0]["children"])
            chapter = self.chapter(chapter_id)
            chapter["nodes"].remove(wrapper)
            if not chapter["nodes"]:
                # the print page held only a part of the table
                self.content["chapters"].remove(chapter)
        self.note(LCD_CHAPTERS[REGION][0], "one-glossary-table", rows=len(rows), print_parts=len(groups))
        notes = 0
        for row in rows:
            cells = row["children"]
            roles = ["number", "icon", "name", "desc"][-len(cells):]
            for cell, role in zip(cells, roles, strict=True):
                add_class(cell, "ht-lcd-" + role)
            name = cells[-2]
            for paragraph_node in list(name["children"]):
                kids = paragraph_node.get("children", [])
                if paragraph_node.get("kind") != "paragraph":
                    continue
                lead = 0
                while lead < len(kids) and (kids[lead].get("kind") == "strong" or not text_of(kids[lead]).strip()):
                    lead += 1
                rest = kids[lead:]
                if not lead or not text_of(rest).strip():
                    continue
                position = name["children"].index(paragraph_node)
                paragraph_node["children"] = kids[:lead]
                name["children"].insert(position + 1, node("paragraph", rest, presentation=attrs("ht-lcd-note")))
                notes += 1
        self.note(LCD_CHAPTERS[REGION][0], "lcd-name-note-lines", notes=notes)
        # Display modes: mode and action cells keep one line each, as printed.
        for chapter in self.content["chapters"]:
            for _, _, table in walk(chapter["nodes"]):
                if isinstance(table, dict) and table.get("kind") == "table" and has_class(table, "ht-lcd-modes"):
                    for row in table["children"][0]["children"]:
                        cells = row["children"]
                        if len(cells) == 3:
                            add_class(cells[0], "ht-lcd-mode")
                        add_class(cells[-2], "ht-lcd-action")
                    self.note(chapter["id"], "lcd-mode-columns")

    def lcd_glyph_heights(self) -> None:
        """Every glossary glyph shows at its print height, as the native glyphs already do.

        The reviewed glyphs are tightly cropped bitmaps shown at their pixel size under the
        2.5rem image cap: from about half (the readouts) to 1.4 times print size, so they
        matched neither each other nor the native glyphs. The print sets all of them to one scale.
        """
        column = LCD_ICON_COLUMN[REGION]
        pages = [int(chapter_id.split("-")[1]) for chapter_id in LCD_CHAPTERS[REGION]]
        clusters: dict[int, list[fitz.Rect]] = {}
        for page in pages:
            pdf_page = self.document[page - 1]
            parts = [d["rect"] for d in pdf_page.get_drawings() if d["rect"].width < 34 and d["rect"].height < 30
                     and d["rect"].x0 >= column[0] and d["rect"].x1 <= column[1]]
            parts += [fitz.Rect(span["bbox"]) for block in pdf_page.get_text("dict")["blocks"]
                      for line in block.get("lines", []) for span in line["spans"]
                      if span["text"].strip() and column[0] - 1 <= span["bbox"][0] and span["bbox"][2] <= column[1] + 1]
            found: list[fitz.Rect] = []
            for rect in sorted(parts, key=lambda r: r.y0):
                if found and rect.y0 <= found[-1].y1 + 3:
                    found[-1] |= rect
                else:
                    found.append(fitz.Rect(rect))
            clusters[page] = found
        (_, _, table), = self.find(LCD_CHAPTERS[REGION][0],
                                   lambda n: n.get("kind") == "table" and has_class(n, "ht-lcd-icons"))
        sized = native = 0
        for row in table["children"][0]["children"]:
            icon = next(c for c in row["children"] if has_class(c, "ht-lcd-icon"))
            name = self.print.key(text_of(next(c for c in row["children"] if has_class(c, "ht-lcd-name"))))
            lines = [line for page in pages for line in self.print.by_page.get(page, [])
                     # names start just right of the glyphs (CN p5 sets its table 13 pt further left)
                     if column[1] - 8 < line["bbox"][0] < column[1] + 15 and self.print.key(line["text"])
                     and name.startswith(self.print.key(line["text"]))]
            if not lines:
                raise ValueError(f"LCD glossary: no print name line for {name!r}")
            line = max(lines, key=lambda r: len(self.print.key(r["text"])))
            centre = (line["bbox"][1] + line["bbox"][3]) / 2
            box = min(clusters[line["physical_page"]], key=lambda c: abs((c.y0 + c.y1) / 2 - centre))
            if abs((box.y0 + box.y1) / 2 - centre) > 12:
                raise ValueError(f"LCD glossary: no print glyph beside {name!r}")
            for _, _, image in walk(icon["children"]):
                if not (isinstance(image, dict) and image.get("kind") == "image"):
                    continue
                present = image.setdefault("presentation", {}).setdefault("html", {}).setdefault("attributes", {})
                if "style" in present:
                    native += 1     # native glyphs carry their print height already
                    continue
                present["style"] = f"height:{box.height / 7:.2f}em;width:auto"
                sized += 1
        self.note(LCD_CHAPTERS[REGION][0], "lcd-glyph-print-height", sized=sized, native=native)

    def jp_ups(self) -> None:
        """p16: the body under the UPS figure prints inside a grey panel."""
        found = [n for n in self.chapter("page-16")["nodes"] if n.get("kind") == "group" and has_class(n, "ht-prose")]
        if len(found) != 1:
            raise ValueError("page-16: expected one prose group")
        add_class(found[0], "ht-native-note-panel")
        self.note("page-16", "print-grey-panel")

    def jp_parallel(self) -> None:
        """p18: the parallel icon closes the first check line; ご使用前の確認 prints two bullets."""
        (_, _, listing), = self.find("page-18", lambda n: n.get("kind") == "list" and "並列アイコン" in text_of(n))
        first, second = listing["children"]
        icon = second["children"][0]["children"].pop(0)
        if icon.get("kind") != "image" or "parallel" not in icon.get("source", ""):
            raise ValueError("page-18: parallel icon not found at the start of the second check line")
        first["children"][0]["children"].append(icon)
        self.restore("page-18", "print-icon-position", "icon before 設定に失敗した場合は",
                     "icon after 並列アイコンが点灯表示されます。")
        self.note("page-18", "inline-icon-position", icon=icon["source"])
        (_, _, callout), = self.find("page-18", lambda n: component_id(n) == "HB-CALLOUT-STRIP"
                                     and text_of(n.get("carrier_flow", [])).find("ご使用前の確認") >= 0)
        body = next(n for _, _, n in walk(callout["carrier_flow"]) if has_class(n, "manual-callout-body"))
        paragraph_node, = body["children"]
        runs = paragraph_node["children"]
        split = next(i for i, run in enumerate(runs) if text_of(run).startswith("AC出力がオンの状態"))
        items = [node("list_item", [node("paragraph", [r for r in runs[:split] if text_of(r).strip()])]),
                 node("list_item", [node("paragraph", runs[split:])])]
        body["children"] = [node("list", items, ordered=False)]
        add_class(callout["carrier_flow"][0], "ht-native-item-list")
        callout["component_spec"]["slots"].append({"role": "items", "content_kind": "list_items", "content": []})
        self.note("page-18", "print-bullets", callout="ご使用前の確認", items=2)

    def jp_solar(self) -> None:
        # p21: the accessory notes print in one grey panel; the ※ line closes the panel, not the list.
        chapter = self.chapter("page-21")
        prose = chapter["nodes"][0]
        kids = prose["children"]
        index = next(i for i, n in enumerate(kids) if n.get("kind") == "heading" and "必要なアクセサリー" in text_of(n))
        heading, listing = kids[index], kids[index + 1]
        second = listing["children"][1]["children"][0]
        split = next(i for i, run in enumerate(second["children"]) if text_of(run).startswith("※"))
        note_runs = second["children"][split:]
        second["children"] = second["children"][:split]
        panel = node("group", [node("paragraph", heading["children"]), listing, node("paragraph", note_runs)],
                     role="container", presentation=attrs("ht-native-note-panel"))
        kids[index:index + 2] = [panel]
        self.note("page-21", "print-grey-panel", title=text_of(heading).strip(), heading_removed=True)
        # p22: one bullet with two sub-bullets (◦), as printed.
        prose = self.chapter("page-22")["nodes"][0]
        lead, sub = prose["children"][0], prose["children"][1]
        if lead.get("kind") != "paragraph" or sub.get("kind") != "list":
            raise ValueError("page-22: SolarSaga adapter list changed")
        prose["children"][0:2] = [node("list", [node("list_item", [lead, sub])], ordered=False)]
        self.note("page-22", "print-nested-list", items=len(sub["children"]))
        # p22: Voc prints with a subscript OC (the reviewed edition set it as bold full-size text).
        (owner, index, voc), = self.find("page-22", lambda n: n.get("kind") == "strong" and text_of(n) == "OC")
        owner[index] = node("subscript", voc["children"])
        self.note("page-22", "print-subscript", text="V" + text_of(voc))

    def jp_warranty(self) -> None:
        """p26-27: the ※ / * notes print in light grey capsules."""
        marked = 0
        for chapter_id in ("page-26", "page-27"):
            for _, _, item in self.find(chapter_id, lambda n: n.get("kind") == "paragraph"
                                        and re.match(r"^(※\s*Jackery 公式|※\s+ご提示|\*無償修理)", text_of(n).strip()),
                                        count=None):
                add_class(item, "ht-print-note-pill")
                marked += 1
        if marked != 4:
            raise ValueError(f"warranty: expected 4 printed note capsules, found {marked}")
        self.note("page-26", "print-note-capsules", count=marked)

    def jp_app(self) -> None:
        """p29: 4.1 prints its two cases as bullets under the lead line."""
        (owner, index, para), = self.find("page-29", lambda n: n.get("kind") == "paragraph"
                                          and text_of(n).startswith("4.1"))
        runs = para["children"]
        lead_end = next(i for i, run in enumerate(runs) if text_of(run).rstrip().endswith("：")) + 1
        rest = runs[lead_end:]
        split = next(i for i, run in enumerate(rest) if text_of(run).startswith("上記アイコンが点灯しない"))
        items = [node("list_item", [node("paragraph", [r for r in rest[:split] if text_of(r).strip()])]),
                 node("list_item", [node("paragraph", rest[split:])])]
        owner[index:index + 1] = [node("paragraph", runs[:lead_end]), node("list", items, ordered=False)]
        self.note("page-29", "print-bullets", lead="4.1", items=2)

    # ---- components ---------------------------------------------------------------
    def refresh_callouts(self) -> None:
        """Callout slots read the carrier: label, body text runs (one per line) and list items."""
        for chapter in self.content["chapters"]:
            for _, _, item in walk(chapter["nodes"], carriers=False):
                if component_id(item) != "HB-CALLOUT-STRIP":
                    continue
                carrier = BeautifulSoup(_carrier_html(item), "html.parser")
                cells = carrier.find("tr").find_all(["th", "td"], recursive=False)
                spec = item["component_spec"]
                slot(spec, "label")["content"] = cells[0].get_text(" ", strip=True)
                slot(spec, "body")["content"] = cells[1].get_text("\n", strip=True)
                if any(s["role"] == "items" for s in spec["slots"]):
                    slot(spec, "items")["content"] = [li.get_text(" ", strip=True) for li in cells[1].select("li")]
                render_callout_component(ComponentSpec.from_dict(spec), _carrier_html(item))

    def refresh_warranty(self) -> None:
        for chapter in self.content["chapters"]:
            for _, _, item in walk(chapter["nodes"], carriers=False):
                if component_id(item) == "HB-WARRANTY-SECTION":
                    render_warranty_component(ComponentSpec.from_dict(item["component_spec"]))

    def refresh_reference_figures(self) -> None:
        """Re-derive caption slots from the edited carrier lines and re-bind the fragment hash."""
        changed = []
        for chapter in self.content["chapters"]:
            for owner, index, item in list(walk(chapter["nodes"], carriers=False)):
                if component_id(item) != "HB-SPECIAL-REFERENCE-FIGURE":
                    continue
                data = copy.deepcopy(item["component_spec"])
                carrier = item["carrier_flow"]
                block = next((n for _, _, n in walk(carrier) if has_class(n, "line-block")), None)
                if block is not None:
                    captions = slot(data, "captions")
                    lines = block["children"]
                    if len(lines) != len(captions["content"]):
                        raise ValueError(f"caption lines disagree for {data['source_ref']}")
                    for caption, line in zip(captions["content"], lines, strict=True):
                        # a caption may hold several positioned print lines (one span each)
                        value = to_html(line["children"])
                        caption["html"] = value
                        caption["text"] = BeautifulSoup(value, "html.parser").get_text(" ", strip=True)
                spec = ComponentSpec.from_dict(data)
                payload = web_reference_figure_projection(spec)
                payload.update(capture_following_lines=int(spec.metadata.get("capture_following_lines") or 0),
                               captions_origin=str(spec.metadata.get("captions_origin") or "carrier"),
                               composite_locale=str(spec.metadata.get("composite_locale") or ""))
                soup = BeautifulSoup(flow_nodes_to_html([flow_root(copy.deepcopy(n)) for n in carrier]), "html.parser")
                image = _validate_carrier(payload, soup)
                _transform_reference_figure(soup, image=image, spec=_component_contract(payload),
                                            source_path=Path(spec.source_ref),
                                            composites=WebCompositeContext(None, "JE-3600A", REGION,
                                                                           spec.language, ValueError))
                digest = soup.figure["data-source-fragment-sha256"]
                if digest == data["metadata"].get("source_fragment_sha256") and data == item["component_spec"]:
                    continue
                changed.append(data["source_ref"])
                data["metadata"]["source_fragment_sha256"] = digest
                fresh = component_flow_node(ComponentSpec.from_dict(data), carrier_flow=carrier)
                if "schema_version" in item:
                    fresh = flow_root(fresh)
                owner[index] = fresh
        self.note("*", "reference-figures-rebound", figures=changed)

    # ---- writing ----------------------------------------------------------------------
    def write(self) -> None:
        target = HERE / f"source/{LANGUAGE}"
        target.mkdir(parents=True, exist_ok=True)
        (target / "content.json").write_text(json.dumps(self.content, ensure_ascii=False, indent=2) + "\n")
        (target / "web_layout.json").write_text(json.dumps(
            {"schema_version": "je3600a-web-layout-changes/v1", "region": REGION, "language": LANGUAGE,
             "approved_source": f"../{TARGET['approved']}/source/{LANGUAGE}/content.json",
             "changes": self.log, "copy_restorations": self.restorations},
            ensure_ascii=False, indent=1) + "\n")


def derive(document: fitz.Document) -> Derivation:
    work = Derivation(document)
    work.warranty_open()
    if REGION == "JP":
        work.jp_cover()
        work.jp_safety()
        work.jp_caution_lockup()
        work.jp_package()
        work.jp_ups()
        work.jp_parallel()
        work.jp_solar()
        work.jp_warranty()
        work.jp_app()
        work.remove_hidden_label("page-18", "Jackery Explorer 2000 Plus")
        work.jp_energy_icons()
    if REGION == "CN":
        work.cn_titles()
        work.cn_voc()
        work.remove_hidden_label("page-13", "Jackery Explorer 2000 Plus")
    work.crop_slivers()
    work.lcd_icons()
    work.lcd_tables()
    work.lcd_glyph_heights()
    work.spec_tables()
    work.inline_icon_spaces()
    work.print_lines()
    work.print_weights()
    work.warranty_close()
    work.refresh_callouts()
    work.refresh_warranty()
    work.refresh_reference_figures()
    return work


def copy_sources() -> None:
    shutil.copy2(APPROVED / TARGET["pdf"], HERE / TARGET["pdf"])
    for relative in COPIED:
        destination = HERE / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(APPROVED / relative, destination)


def write_assets(added: list[dict]) -> None:
    pool = HERE / "assets"
    if pool.exists():
        shutil.rmtree(pool)
    shutil.copytree(APPROVED / "assets", pool)
    records = json.loads((APPROVED / "assets_manifest.json").read_text())
    for record in added:
        (pool / record["asset"]).write_bytes(record.pop("_bytes"))
        records.append(record)
    (HERE / "assets_manifest.json").write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n")


def main() -> None:
    with fitz.open(APPROVED / TARGET["pdf"]) as document:
        work = derive(document)
    work.write()
    copy_sources()
    write_assets(work.new_assets)
    summary = {"region": REGION, "language": LANGUAGE, "changes": len(work.log),
               "copy_restorations": len(work.restorations)}
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
