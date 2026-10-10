"""Derive the JHP-5000C/US Web-layout edition from the approved package.

Run from the repository root:

    python data/manual_sources/JHP-5000C/US/git-20261010-051169dd-web-layout/derive_web_layout.py

The approved package ``../git-20261009-051169dd`` stays immutable. Every derived
file here is regenerated from it on each run, so a second run leaves the tree
unchanged:

* ``source/<language>/content.json``: rebuilt with the shared flow and
  ComponentSpec builders; each edit is listed in ``source/<language>/web_layout.json``;
* ``source/figures.json`` and ``source/asset_decisions.json``: the approved records
  plus the art decisions below;
* ``assets/``: the approved art plus two shared warning triangles (byte copies),
  native ingestion-hazard and contact glyphs, the three overview views with their
  full frames, and the FR/ES print panels whose geometry differs from English.

Hand-written files are never touched: README.md, rebuild.py, the validators,
source/differences.md, source/approval.json, source/presentation.css and
source/refresh_manifest.py. The other source/ records (coverage, LCD and symbol
provenance) are the approved intake's, copied unchanged.

Wording rule: visible copy keeps the approved strings. The only copy edits restore
the authoritative PDF where the approved intake disagreed with it; each one is
listed in web_layout.json under "copy_restorations". Where the PDF itself prints
another language's text (ES p52/p62/p65/p74-75, FR p28) the Web keeps the print.
"""
from __future__ import annotations

import copy
import hashlib
import html
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

from tools.asset_pipeline.native_svg import native_art_svg, native_symbol_svg  # noqa: E402
from tools.component_specs.lcd_mode import lcd_mode_component_spec  # noqa: E402
from tools.component_specs.manual_tables import symbol_signal_component_spec  # noqa: E402
from tools.component_specs.model import ComponentSpec  # noqa: E402
from tools.component_specs.spec_table import spec_table_component_spec  # noqa: E402
from tools.component_specs.reference_figure_adapters import web_reference_figure_projection  # noqa: E402
from tools.manual_ir.components import component_flow_node  # noqa: E402
from tools.manual_ir.flow import flow_nodes_to_html  # noqa: E402
from tools.web.composite_presentation import WebCompositeContext  # noqa: E402
from tools.web.presentation import _transform_reference_figure  # noqa: E402
from tools.web.reference_figure_component import _component_contract, _validate_carrier  # noqa: E402
from tools.web.frozen_ai_flow import callout, cell, node, paragraph, table, text  # noqa: E402

APPROVED = HERE.parent / "git-20261009-051169dd"
LANGUAGES = ("en", "fr", "es")
PDF_NAME = "Jackery HomePower 5000 Plus.pdf"
FIRST_PAGE = {"en": 4, "fr": 28, "es": 52}
FLOW = "manual-flow/v2"

# Print TOC (physical p3): these semantic chapters are sections of a printed chapter.
NESTED_UNDER = {
    "maintenance": "safety", "symbols": "safety", "fcc": "safety",
    "ess-host": "ess", "ess-battery": "ess", "ess-sts": "ess", "ess-package": "ess",
}
# Physical p2 prints the English block with a "US" badge; French/Spanish match their codes.
PREFACE_BADGE = {"en": "US", "fr": "FR", "es": "ES"}
LIGATURES = {"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl"}
BOLD_FONTS = ("Bold", "SemiBold", "Heavy")
BULLETS = "·•"
INGESTION = re.compile(r"^(INGESTION HAZARD|RISQUE D.INGESTION|RIESGO DE INGESTA)\b")
MODEL_LABEL = re.compile(r"^(?:Model|Modèle|Modelo)\s*:\s*(\S+)$")

# Shared art reused byte-identically (searched before any extraction, per the Web
# artwork reuse order); the triangle glyphs carry the print's two warning lockups.
SHARED_ART = {
    "warning_triangle_dark.svg": "docs/templates/word_template/common_assets/symbols/warning_triangle_dark.svg",
    "warning_triangle_white.svg": "docs/templates/word_template/common_assets/symbols/warning_triangle_white.svg",
}
# Back cover (p76) contact glyphs and QR code: native vectors, shared by all locales.
CONTACT_ART = {
    "contact-phone.svg": ([2, 3], [36.0, 469.0, 54.0, 487.2], "Telephone glyph left of the phone number."),
    "contact-mail.svg": ([4, 5], [208.8, 469.7, 218.1, 476.1], "Envelope glyph left of the e-mail address."),
    "contact-web.svg": ([6, 7, 8], [208.3, 479.0, 219.1, 487.8], "Globe glyph left of the website."),
    "contact-qr.svg": (list(range(10, 33)), [309.2, 463.7, 337.9, 492.5], "QR code at the right of the contact panel."),
}
INGESTION_ART = "symbol_ingestion_hazard.svg"
INGESTION_GLYPH = {"page": 23, "drawings": [1, 2, 3, 4, 5], "bbox": [30.0, 452.5, 47.5, 473.6]}
# The approved overview views stop short of their own paths: the right view cuts
# the print's handle-button inset at the top and all three cut wheels or panel
# edges at the bottom. Only each SVG frame grows; the drawing set is the approved
# one. Values are (approved top, approved bottom, new top, new bottom) in points.
FRAMES = {
    "overview-front": (266.0, 490.0, 266.0, 495.0),
    "overview-left": (39.0, 248.0, 39.0, 253.0),
    "overview-right": (275.0, 492.0, 238.0, 504.0),
}

# FR/ES print these panels with their own geometry (device scale, zoom circles, bracket,
# localized phone screens), so the shared English art cannot carry their labels; car-fr/es
# are re-acquired because the approved variants dropped the plug's cable.
# Figures listed here were measured: their locale panel shifts the drawing 1.3-17 pt inside
# its frame, adds or drops drawings, or localizes screens; every other locale panel is the
# English drawing translated as a whole (< 1 pt) and keeps the shared art.
LOCALE_ART = {"ac-output": ("fr", "es"), "usb-output": ("fr", "es"), "dc-output": ("fr", "es"),
              "sts-charge": ("fr", "es"), "car": ("fr", "es"), "low-pv-500": ("fr", "es"),
              "low-pv-200": ("fr", "es"), "ac-charge": ("fr", "es"), "high-pv": ("fr", "es"),
              "high-pv-lock": ("fr", "es"), "dual-pv": ("fr", "es"), "ess": ("fr", "es"),
              "battery-packs": ("fr", "es"), "package-sts": ("fr",),
              # Same drawing list as English, but leader lines moved for longer copy
              # (FR/ES left view NEMA 14-50: 6.6 pt; FR front view: 2.9 pt).
              "overview-left": ("fr", "es"), "overview-front": ("fr",), "app-control": ("fr", "es")}
LOCALE_OFFSET = {"en": 0, "fr": 24, "es": 48}


def locale_variant(document: fitz.Document, figure: dict, language: str,
                   frame: list[float] | None = None) -> tuple[bytes, list[int], int]:
    """The figure's own panel on the locale page, selected exactly as the English one was.

    English art keeps every drawing that touches its frame except the panel stroke and
    caption plates (verified to reproduce the approved English indices). The locale
    plates are the drawings with the same paint nearest the English plates' scaled spots.
    """
    english = document[figure["page"] - 1].get_drawings()
    number = figure["page"] + LOCALE_OFFSET[language]
    drawings = document[number - 1].get_drawings()
    if not figure.get("locale_boxes") and len(drawings) == len(english):
        # The locale page repeats the English drawing list one for one (only some
        # positions differ), so the approved English selection names the same paths.
        crop = frame or figure["bbox"]
        return (native_art_svg(document[number - 1], figure["drawing_indices"], list(crop)),
                list(figure["removed_drawing_indices"]), number)
    box_value = figure.get("locale_boxes", {}).get(language, figure["bbox"])
    en_box, box = fitz.Rect(figure["bbox"]), fitz.Rect(box_value)

    def touches(d, frame):
        return frame.intersects(d["rect"]) or frame.contains(d["rect"])

    def overlap(a, b):
        inter = fitz.Rect(a) & fitz.Rect(b)
        return 0 if inter.is_empty else inter.get_area() / max(1e-6, (fitz.Rect(a) | fitz.Rect(b)).get_area())

    removed = []
    for index in figure["removed_drawing_indices"]:
        source = english[index]
        r = source["rect"]
        predicted = fitz.Rect(box.x0 + (r.x0 - en_box.x0) / en_box.width * box.width,
                              box.y0 + (r.y0 - en_box.y0) / en_box.height * box.height,
                              box.x0 + (r.x1 - en_box.x0) / en_box.width * box.width,
                              box.y0 + (r.y1 - en_box.y0) / en_box.height * box.height)
        paint = (source["type"], source.get("fill"), source.get("color"))
        # Plates grow with translated copy, so match the anchored corner and height, not area.
        scored = [(abs(d["rect"].x0 - predicted.x0) + abs(d["rect"].y0 - predicted.y0)
                   + abs(d["rect"].height - predicted.height), i)
                  for i, d in enumerate(drawings)
                  if (d["type"], d.get("fill"), d.get("color")) == paint and touches(d, box)
                  and 0.6 <= d["rect"].height / max(1e-6, predicted.height) <= 1.6]
        best = min(scored, default=(float("inf"), None))
        if best[0] > 20 and overlap(drawings[best[1]]["rect"] if best[1] is not None else predicted, predicted) < 0.3:
            raise SystemExit(f"{figure['id']}/{language}: caption plate {index} has no locale match")
        removed.append(best[1])
    indices = sorted({i for i, d in enumerate(drawings) if touches(d, box)} - set(removed))
    return native_art_svg(document[number - 1], indices, list(box)), sorted(removed), number


def page_of(language: str, english_page: int) -> int:
    """Physical PDF page of a locale for the equivalent English page number."""
    return english_page - 4 + FIRST_PAGE[language]


def squash(value: str) -> str:
    for old, new in LIGATURES.items():
        value = value.replace(old, new)
    return " ".join(value.split())


def key(value: str) -> str:
    value = unicodedata.normalize("NFC", squash(value)).casefold()
    return re.sub(r"\W", "", value)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def text_of(item) -> str:
    if isinstance(item, list):
        return "".join(text_of(child) for child in item)
    if not isinstance(item, dict):
        return ""
    if item.get("kind") == "text":
        return item.get("text", "")
    if item.get("kind") == "line_break":
        return " "
    return "".join(text_of(child) for child in item.get("children", []))


def css_class(item) -> str:
    value = (((item.get("presentation") or {}).get("html") or {}).get("attributes") or {}).get("class", "")
    return " ".join(value) if isinstance(value, list) else value


def attrs(value: str) -> dict:
    return {"html": {"attributes": {"class": value}}}


def with_class(item: dict, value: str) -> dict:
    item = dict(item)
    item["presentation"] = attrs(value)
    return item


def flow_root(item: dict) -> dict:
    return {"schema_version": FLOW, **{k: v for k, v in item.items() if k != "schema_version"}}


def strong(value: str) -> dict:
    return node("strong", [text(value)])


def span(value, css: str) -> dict:
    children = value if isinstance(value, list) else [text(value)]
    return node("inline_group", children, presentation=attrs(css))


def group(children: list[dict], css: str, **fields) -> dict:
    return node("group", children, role="container", presentation=attrs(css), **fields)


def is_plain(item: dict, kind: str = "paragraph") -> bool:
    return item.get("kind") == kind and bool(item.get("children")) and all(
        child.get("kind") == "text" for child in item["children"])


def component_id(item: dict) -> str | None:
    return item["component_spec"]["component_id"] if item.get("kind") == "component" else None


def walk(items):
    """Yield (container list, index, node) for every flow node below ``items``."""
    for index, item in enumerate(items):
        yield items, index, item
        if isinstance(item, dict):
            yield from walk(item.get("children", []))


class PdfLines:
    """Styled text lines of the authoritative PDF, used to read print layout."""

    def __init__(self, document: fitz.Document):
        self.document = document
        self.cache: dict[int, list[dict]] = {}

    def lines(self, page: int) -> list[dict]:
        if page not in self.cache:
            rows = []
            for block in self.document[page - 1].get_text("dict")["blocks"]:
                for line in block.get("lines", []):
                    spans = [s for s in line["spans"] if s["text"].strip()]
                    if not spans:
                        continue
                    value = squash("".join(s["text"] for s in line["spans"]))
                    words = [s for s in spans if s["text"].strip(BULLETS + " ")]
                    rows.append({
                        "text": value,
                        "bullet": value[:1] in BULLETS,
                        "bold": bool(words) and all(any(f in s["font"] for f in BOLD_FONTS) for s in words),
                        "white": all(s["color"] == 0xFFFFFF for s in spans),
                        "bbox": line["bbox"],
                        "size": spans[0]["size"],
                    })
            self.cache[page] = rows
        return self.cache[page]

    def drawn_bullet(self, page: int, line: dict) -> bool:
        """A small filled dot drawn just left of the line (print sub-head bullets)."""
        x0, y0, _, y1 = line["bbox"]
        for drawing in self.document[page - 1].get_drawings():
            r = drawing["rect"]
            if (drawing.get("fill") and r.width < 4 and r.height < 4
                    and x0 - 11 <= r.x1 <= x0 and y0 <= (r.y0 + r.y1) / 2 <= y1):
                return True
        return False

    def styled(self, pages, value: str) -> dict | None:
        wanted = key(value)
        for page in pages:
            for line in self.lines(page):
                if key(line["text"]) == wanted:
                    return line
        return None

    def run(self, pages, value: str, keep=None) -> tuple[int, list[dict]] | None:
        """Consecutive print lines of one column whose text is exactly ``value``."""
        wanted = key(value)
        if not wanted:
            return None
        for page in pages:
            lines = [line for line in self.lines(page) if keep is None or keep(line)]
            for start in lines:
                joined = key(start["text"])
                if not joined or not wanted.startswith(joined):
                    continue
                run, current, x0 = [start], start, start["bbox"][0]
                while joined != wanted:
                    below = [line for line in lines if line["bbox"][1] > current["bbox"][1] + 1
                             and x0 - 8 <= line["bbox"][0] <= x0 + 14 and key(line["text"])]
                    if not below:
                        break
                    nearest = min(below, key=lambda line: line["bbox"][1])
                    if not wanted.startswith(joined + key(nearest["text"])):
                        break
                    run.append(nearest)
                    joined += key(nearest["text"])
                    current = nearest
                if joined == wanted:
                    return page, run
        return None


def words_by_line(value: str, run: list[dict]) -> list[list[str]] | None:
    """Assign the approved words to their print lines; None when a word spans two lines."""
    words = squash(value).split()
    out, cursor = [], 0
    for line in run:
        target, taken, chunk = key(line["text"]), "", []
        while cursor < len(words) and len(taken) < len(target):
            taken += key(words[cursor])
            chunk.append(words[cursor])
            cursor += 1
        if taken != target:
            return None
        # Bare punctuation (FR "à :") stays on the line that prints it.
        while (cursor < len(words) and not key(words[cursor])
               and squash(line["text"]).endswith(" ".join([*chunk[-1:], words[cursor]]))):
            chunk.append(words[cursor])
            cursor += 1
        out.append(chunk)
    return out if cursor == len(words) else None


def hard_break(line: dict, following: dict, right: float) -> bool:
    """A print line ends early when the next line's first word would have fitted."""
    width = line["bbox"][2] - line["bbox"][0]
    average = width / max(1, len(line["text"]))
    first = (following["text"].lstrip(BULLETS + " ").split() or [""])[0]
    return right - line["bbox"][2] > (len(first) + 1.5) * average


STATE_WORD = re.compile(
    r"^(On|Off|Blink|Marche|Arrêt|Allumé|Éteint|Clignotant|Encendido|Apagado|Parpadeo|"
    r"Activé|Désactivé|Activado|Desactivado|Parpadeando)$", re.I)


class PdfText:
    """The locale's print as one key stream with a weight flag per key character.

    Matching on keys (case-folded word characters) is independent of how the
    print splits spans, punctuation or full-width characters into words.
    """

    def __init__(self, document: fitz.Document, pages):
        chars, flags = [], []
        for page in pages:
            for block in document[page - 1].get_text("dict")["blocks"]:
                for line in block.get("lines", []):
                    for span_ in line["spans"]:
                        value = key(span_["text"])
                        chars.append(value)
                        flags.extend([any(f in span_["font"] for f in BOLD_FONTS)] * len(value))
        self.stream = "".join(chars)
        self.flags = flags

    def find(self, value: str) -> list[bool] | None:
        """Weight of each key character of ``value``; None unless every occurrence agrees."""
        wanted = key(value)
        if not wanted:
            return None
        found, start = set(), 0
        while (index := self.stream.find(wanted, start)) >= 0:
            found.add(tuple(self.flags[index:index + len(wanted)]))
            start = index + 1
        return list(found.pop()) if len(found) == 1 else None

def tokens(value: str) -> list[str]:
    return [t for t in re.split(r"[\s/:]+", squash(value)) if key(t)]


def spec_carrier(spec: ComponentSpec) -> list[dict]:
    """The approved intake's spec carrier: one titled table, one row per value."""
    slot = lambda role: spec.slot(role).content  # noqa: E731
    title = node("heading", [node("inline_group", [text(slot("section_title"))],
                                  presentation=attrs("hb-spec-section-text"))], level=2,
                 presentation=attrs("hb-spec-section hb-spec-group"))
    rows = [[cell(r["label"] if i == 0 else "", header=True), cell(v["text"])]
            for r in slot("rows") for i, v in enumerate(r["values"])]
    return [title, table(rows)]


class Derivation:
    def __init__(self, language: str, document: fitz.Document, art: dict[str, str]):
        self.language = language
        self.art = art
        self.pdf = PdfLines(document)
        first = FIRST_PAGE[language]
        self.locale_pages = [2, *range(first, first + 24), 76]
        self.print_text = PdfText(document, self.locale_pages)
        self.content = json.loads((APPROVED / f"source/{language}/content.json").read_text())
        self.chapters = {chapter["id"]: chapter for chapter in self.content["chapters"]}
        self.log: list[dict] = []
        self.restorations: list[dict] = []
        self._page_text: dict[int, PdfText] = {}

    def note(self, chapter: str, action: str, **detail) -> None:
        self.log.append({"chapter": chapter, "action": action, **detail})

    def nodes(self, chapter: str) -> list[dict]:
        return self.chapters[chapter]["nodes"]

    def pages(self, *english_pages: int) -> list[int]:
        return [page_of(self.language, p) for p in english_pages]

    def callouts(self, chapter: str):
        for index, item in enumerate(self.nodes(chapter)):
            if component_id(item) == "HB-CALLOUT-STRIP":
                yield index, item

    # ---- structure -------------------------------------------------------
    def nest_chapters(self) -> None:
        for chapter, parent in NESTED_UNDER.items():
            for item in self.nodes(chapter):
                if item.get("kind") == "heading":
                    item["level"] += 1
            self.note(chapter, "nested-under-print-chapter", parent=parent)

    def preface_badge(self) -> None:
        heading = self.nodes("preface")[0]
        badge = heading["children"][0]
        old = text_of(badge)
        new = PREFACE_BADGE[self.language]
        if old != new:
            badge["children"] = [text(new)]
            self.restorations.append({"chapter": "preface", "kind": "print-badge", "approved": old, "pdf": new})

    def fcc_heading(self) -> None:
        """Print p5 has no FCC title, only the FC mark; keep the chapter anchor on the panel."""
        items = self.nodes("fcc")
        heading = items[0]
        if heading.get("kind") != "heading" or heading.get("anchor") != "native-fcc":
            raise ValueError(f"{self.language}: unexpected FCC chapter head")
        panel = items[1]
        items[:2] = [flow_root(group([{k: v for k, v in panel.items() if k != "schema_version"}],
                                     "native-fcc-panel", anchor="native-fcc"))]
        self.note("fcc", "unprinted-title-removed", title=text_of(heading))
        self.restorations.append({"chapter": "fcc", "kind": "unprinted-title", "approved": text_of(heading), "pdf": None})

    # ---- copy restorations against the PDF --------------------------------
    def signal_words(self) -> None:
        """Rebuild the signal-word rows from the print table (p5 equivalent).

        The print detects as one merged table row, so badges and meanings are paired
        by their vertical position: each meaning line belongs to the badge whose
        band contains its centre. Badge text and order are the print's own.
        """
        items = self.nodes("symbols")
        index = next(i for i, item in enumerate(items)
                     if component_id(item) == "HB-TABLE-SYMBOL-SIGNAL")
        spec = items[index]["component_spec"]
        slots = {slot["role"]: slot["content"] for slot in spec["slots"]}
        page = self.pdf.document[page_of(self.language, 5) - 1]
        found = page.find_tables().tables[0]
        split = found.rows[0].cells[0][2]
        words = [w for w in page.get_text("words") if found.bbox[1] - 2 < w[1] < found.bbox[3] + 2]

        def lines(column):
            grouped: dict[tuple, list] = {}
            for w in column:
                grouped.setdefault((w[5], w[6]), []).append(w)
            out = [(min(w[1] for w in ws), max(w[3] for w in ws), " ".join(w[4] for w in ws))
                   for ws in grouped.values()]
            return sorted(out)[1:]  # the first line of each column is its header

        badges = lines([w for w in words if w[0] < split])
        meanings = lines([w for w in words if w[0] >= split])
        if len(badges) != 3:
            raise ValueError(f"{self.language}: expected three print signal badges, found {badges}")
        centres = [(top + bottom) / 2 for top, bottom, _ in badges]
        edges = [(a + b) / 2 for a, b in zip(centres, centres[1:], strict=False)]
        rows = []
        for i, (_, _, label) in enumerate(badges):
            low = edges[i - 1] if i else float("-inf")
            high = edges[i] if i < len(edges) else float("inf")
            meaning = squash(" ".join(t for top, bottom, t in meanings if low <= (top + bottom) / 2 < high))
            if not meaning:
                raise ValueError(f"{self.language}: print signal badge {label!r} has no meaning")
            rows.append({"label": squash(label), "show_icon": i < 2,
                         "meaning_html": html.escape(meaning, quote=False), "meaning_text": meaning})
        approved = [(r["label"], r["meaning_text"]) for r in slots["rows"]]
        restored = [(r["label"], r["meaning_text"]) for r in rows]
        if approved != restored:
            self.restorations.append({"chapter": "symbols", "kind": "signal-word-meanings",
                                      "approved": approved, "pdf": restored})
        new = symbol_signal_component_spec(
            accessibility_label=slots["accessibility_label"], headers=slots["headers"], rows=rows,
            source_ref=spec["source_ref"], language=self.language,
        )
        items[index] = component_flow_node(new, root=True)

    def page_text(self, page: int | None) -> "PdfText":
        """Print text of one physical page (a figure's own labels), else the whole locale."""
        if page is None:
            return self.print_text
        if page not in self._page_text:
            self._page_text[page] = PdfText(self.pdf.document, [page])
        return self._page_text[page]

    def _print_weight(self, context: str, start: int, end: int, page: int | None = None) -> bool | None:
        """Weight of context[start:end] in print, from the widest context the print contains."""
        words = list(re.finditer(r"\S+", context))
        first = next((i for i, w in enumerate(words) if w.end() > start), 0)
        last = next((i for i, w in enumerate(words) if w.end() >= end), len(words) - 1)
        windows = [(0, len(context))] + [
            (words[max(0, first - n)].start(), words[min(len(words) - 1, last + n)].end()) for n in (3, 2, 1)]
        source = self.page_text(page)
        for low, high in windows:
            flags = source.find(context[low:high])
            if flags is None:
                continue
            offset = len(key(context[low:start]))
            width = len(key(context[start:end]))
            return all(flags[offset:offset + width])
        # A state word glued to a hyphen ("Marking-off") is part of a regular noun.
        if start and context[start - 1] == "-":
            return False
        return None

    def regular_state_words(self) -> None:
        """Drop bold the intake gave state words (on/off, marche/arrêt…) that print sets regular."""
        removed = []

        def fix_flow(item, chapter: str, page: int | None = None) -> None:
            """Rebuild each child list; a strong's context is its parent's text."""
            if isinstance(item, list):
                for child in item:
                    fix_flow(child, chapter, page)
                return
            if not isinstance(item, dict):
                return
            if item.get("kind") == "component":
                # Figure labels repeat across pages (overview vs App diagram): read the
                # weight on the component's own print page when its source names one.
                found = re.search(r"page-(\d+)/", item["component_spec"]["source_ref"])
                own = int(found.group(1)) if found else None
                fix_flow(item.get("carrier_flow", []), chapter, own)
                for slot in item["component_spec"]["slots"]:
                    walk_spec(slot, chapter, own)
                return
            children = item.get("children")
            if not children:
                return
            plain = text_of(item)
            out, cursor = [], 0
            for child in children:
                value = text_of(child)
                if (child.get("kind") == "strong" and STATE_WORD.match(value.strip())
                        and self._print_weight(plain, cursor, cursor + len(value), page) is False):
                    out.append(text(value))
                    removed.append({"chapter": chapter, "word": value, "context": squash(plain)[:120]})
                else:
                    fix_flow(child, chapter, page)
                    out.append(child)
                cursor += len(value)
            item["children"] = merge_text(out)

        def fix_html(value: str, chapter: str, page: int | None = None) -> str:
            plain = BeautifulSoup(value, "html.parser").get_text()
            out, cursor = [], 0
            for part in re.split(r"(<strong>[^<]*</strong>)", value):
                inner = part[8:-9] if part.startswith("<strong>") else None
                visible = BeautifulSoup(inner if inner is not None else part, "html.parser").get_text()
                if (inner is not None and STATE_WORD.match(visible.strip())
                        and self._print_weight(plain, cursor, cursor + len(visible), page) is False):
                    out.append(inner)
                    removed.append({"chapter": chapter, "word": visible, "context": squash(plain)[:120]})
                else:
                    out.append(part)
                cursor += len(visible)
            return "".join(out)

        def walk_spec(value, chapter: str, page: int | None = None):
            if isinstance(value, dict):
                for field, inner in value.items():
                    if field.endswith("html") and isinstance(inner, str) and "<strong>" in inner:
                        value[field] = fix_html(inner, chapter, page)
                    else:
                        walk_spec(inner, chapter, page)
            elif isinstance(value, list):
                for inner in value:
                    walk_spec(inner, chapter, page)

        for chapter in self.content["chapters"]:
            fix_flow(chapter["nodes"], chapter["id"])
        self.note("*", "regular-state-words", removed=removed)

    # ---- callouts ------------------------------------------------------------
    def _callout_parts(self, item: dict) -> tuple[str, str, str, str]:
        spec = item["component_spec"]
        slots = {slot["role"]: slot["content"] for slot in spec["slots"]}
        return slots["label"], slots["body"], spec["variant"], spec["source_ref"]

    def _rebuild_callout(self, label: str, body: list[dict], variant: str, source_ref: str) -> dict:
        return flow_root(callout(label, body, variant=variant, language=self.language, source_ref=source_ref))

    def _print_bold(self, value: str) -> bool:
        flags = self.print_text.find(value)
        return bool(flags) and all(flags)

    def _lockup(self, item: dict, icon: str, css: str) -> dict:
        """Print draws these signals as icon + word lockups; the label text stays the slot."""
        label = self._callout_parts(item)[0]
        carrier = copy.deepcopy(item["carrier_flow"])
        found = 0
        for _, _, inner in walk(carrier):
            if inner.get("kind") == "table":
                inner["presentation"] = attrs(css_class(inner) + " hb-source-warning-lockup " + css)
            if inner.get("kind") == "table_cell" and "manual-callout-label" in css_class(inner):
                inner["children"] = [span([node("image", source="assets/" + icon, alt=""), text(label)],
                                          "hb-warning-lockup")]
                found += 1
        if found != 1:
            raise ValueError(f"{self.language}: callout label cell not found")
        spec = ComponentSpec.from_dict(item["component_spec"])
        return component_flow_node(spec, carrier_flow=carrier, root=True)

    def safety_lockups(self) -> None:
        """WARNING (inverse) and DANGER (outlined) carry the print's triangle and bold body."""
        items = self.nodes("safety")
        for index, item in self.callouts("safety"):
            label, body, variant, ref = self._callout_parts(item)
            if variant == "warning":
                bold = self._print_bold(body)
                if bold:
                    item = self._rebuild_callout(label, [node("paragraph", [strong(squash(body))])], variant, ref)
                items[index] = self._lockup(item, "warning_triangle_white.svg", "native-lockup-inverse")
                self.note("safety", "warning-lockup", label=label, bold_body=bold)
            elif variant == "danger":
                items[index] = self._lockup(item, "warning_triangle_dark.svg", "native-lockup-outlined")
                self.note("safety", "danger-lockup", label=label)

    def danger_callout(self) -> None:
        """Drop the label the intake repeated at the end; '※' starts its own print line."""
        items = self.nodes("safety")
        for index, item in self.callouts("safety"):
            label, body, variant, ref = self._callout_parts(item)
            if variant != "danger":
                continue
            value = squash(body)
            if value.endswith(" " + label):
                value = value[: -len(label) - 1]
                self.restorations.append({"chapter": "safety", "kind": "duplicated-callout-label",
                                          "approved": squash(body), "pdf": value})
            head, mark, tail = value.partition("※")
            parts = [head.strip()] + ([(mark + tail).strip()] if mark else [])
            bold = self._print_bold(value)
            runs = [strong(part) if bold else text(part) for part in parts]
            children = runs[:1] + ([node("line_break"), runs[1]] if len(runs) > 1 else [])
            items[index] = self._rebuild_callout(label, [node("paragraph", children)], variant, ref)
            self.note("safety", "danger-callout-lines", bold_body=bold)

    def solar_caution(self) -> None:
        """Item 2 of the low-PV caution was nested inside the second example bullet."""
        items = self.nodes("charging")
        for index, item in self.callouts("charging"):
            label, body, variant, ref = self._callout_parts(item)
            lines = body.split("\n")
            if len(lines) != 3 or not re.match(r"1\.\s", lines[0]):
                continue
            pieces = re.split(r"\s2\.\s", lines[2], maxsplit=1)
            if len(pieces) != 2:
                continue
            first = re.sub(r"^1\.\s+", "", lines[0])
            body_blocks = [
                node("list", [node("list_item", [text(first)])], ordered=True),
                node("list", [node("list_item", [text(lines[1])]), node("list_item", [text(pieces[0])])],
                     ordered=False),
                node("list", [node("list_item", [text(pieces[1])])], ordered=True, start=2),
            ]
            items[index] = self._rebuild_callout(label, body_blocks, variant, ref)
            self.note("charging", "caution-item-2-unnested", label=label)

    @staticmethod
    def numbered(value: str) -> list[str] | None:
        """Split '1. … 2. … 3. …' into its items when the numbers run 1..n."""
        parts = re.split(r"(?:^|(?<=\s))(\d{1,2})\.\s+", squash(value))
        if len(parts) < 5 or parts[0].strip():
            return None
        numbers, items = parts[1::2], [p.strip() for p in parts[2::2]]
        if numbers != [str(i) for i in range(1, len(numbers) + 1)] or not all(items):
            return None
        return items

    def numbered_callouts(self) -> None:
        for chapter in self.content["chapters"]:
            items = chapter["nodes"]
            for index, item in enumerate(items):
                if component_id(item) != "HB-CALLOUT-STRIP":
                    continue
                label, body, variant, ref = self._callout_parts(item)
                if "\n" in body:
                    continue  # already structured (handled separately when wrong)
                parts = self.numbered(body)
                if not parts:
                    continue
                items[index] = self._rebuild_callout(
                    label, [node("list", [node("list_item", [text(p)]) for p in parts], ordered=True)],
                    variant, ref)
                self.note(chapter["id"], "callout-numbered-items", label=label, items=len(parts))

    def numbered_paragraphs(self) -> None:
        """Steps printed one per line ('1. … 2. …') become an ordered list."""
        for chapter in self.content["chapters"]:
            items = chapter["nodes"]
            for index, item in enumerate(items):
                if not is_plain(item):
                    continue
                parts = self.numbered(text_of(item))
                if parts:
                    items[index] = flow_root(node("list", [node("list_item", [text(p)]) for p in parts], ordered=True))
                    self.note(chapter["id"], "paragraph-numbered-steps", items=len(parts))

    def print_items(self, english_pages, value: str) -> list[str]:
        """Split ``value`` where print ends an item: a line that stops short of its column."""
        found = self.pdf.run(self.pages(*english_pages), value)
        words = words_by_line(value, found[1]) if found else None
        if not words:
            raise ValueError(f"{self.language}: print lines not found for {value[:60]!r}")
        run = found[1]
        right = max(line["bbox"][2] for line in run)
        items, current = [], []
        for index, (line, chunk) in enumerate(zip(run, words, strict=True)):
            current.extend(chunk)
            if line["bbox"][2] < right - 15 or index == len(run) - 1:
                items.append(" ".join(current))
                current = []
        return items

    def line_item_callouts(self, chapter: str, english_page: int) -> None:
        """Unnumbered callout lines (one requirement per print line) stay separate lines."""
        items = self.nodes(chapter)
        for index, item in self.callouts(chapter):
            label, body, variant, ref = self._callout_parts(item)
            if "\n" in body or self.numbered(body):
                continue
            parts = self.print_items([english_page], body)
            if len(parts) > 1:
                items[index] = self._rebuild_callout(label, [paragraph(p) for p in parts], variant, ref)
                self.note(chapter, "callout-print-lines", label=label, lines=len(parts))

    def bullet_callouts(self) -> None:
        """Callout bodies printed as '·' bullets become bullet lists."""
        for chapter in self.content["chapters"]:
            items = chapter["nodes"]
            for index, item in enumerate(items):
                if component_id(item) != "HB-CALLOUT-STRIP":
                    continue
                label, body, variant, ref = self._callout_parts(item)
                if any(block.get("kind") == "list" for block in self._carrier_body(item)):
                    continue
                body = squash(body)
                page = int(re.search(r"page-(\d+)", ref).group(1)) if "page-" in ref else None
                found = self.pdf.run([page] if page else self.locale_pages, body)
                if not found or not any(line["bullet"] for line in found[1]):
                    continue
                words = words_by_line(body, found[1])
                if not words or not found[1][0]["bullet"]:
                    continue
                parts: list[list[str]] = []
                for line, chunk in zip(found[1], words, strict=True):
                    if line["bullet"] or not parts:
                        parts.append([])
                    parts[-1].extend(chunk)
                entries = [node("list_item", [text(" ".join(p))]) for p in parts]
                items[index] = self._rebuild_callout(label, [node("list", entries, ordered=False)], variant, ref)
                self.note(chapter["id"], "callout-print-bullets", label=label, items=len(entries))

    @staticmethod
    def _carrier_body(item: dict) -> list[dict]:
        for _, _, inner in walk(item.get("carrier_flow", [])):
            if inner.get("kind") == "table_cell" and "manual-callout-body" in css_class(inner):
                return inner.get("children", [])
        return []

    def inline_callout_labels(self) -> None:
        """A callout label the intake read into the middle of its body ('… is Caution within …').

        The body without the label must be contiguous print text, the approved string must
        not be, and the label must be a bold print line: then the print set it as a callout.
        """
        labels: dict[str, str] = {}
        for chapter in self.content["chapters"]:
            for _, item in self.callouts(chapter["id"]):
                label, _, variant, _ = self._callout_parts(item)
                labels.setdefault(label, variant)
        for chapter in self.content["chapters"]:
            items = chapter["nodes"]
            for index, item in enumerate(items):
                if not is_plain(item):
                    continue
                value = squash(text_of(item))
                for label, variant in labels.items():
                    marker = f" {label} "
                    if marker not in value or value.startswith(label):
                        continue
                    body = value.replace(marker, " ", 1)
                    line = self.pdf.styled(self.locale_pages, label)
                    if (line is None or not line["bold"] or self.print_text.find(value)
                            or not self.print_text.find(body)):
                        continue
                    items[index] = self._rebuild_callout(label, [paragraph(body)], variant,
                                                         f"native-pdf/{chapter['id']}/inline-label-{index}")
                    self.restorations.append({"chapter": chapter["id"], "kind": "misplaced-callout-label",
                                              "approved": value, "pdf": f"{label} | {body}"})
                    self.note(chapter["id"], "inline-label-callout", label=label)
                    break

    def label_paragraph_callouts(self) -> None:
        """A note whose label was read as its own block (or glued to its body) is one callout."""
        for chapter in self.content["chapters"]:
            items = chapter["nodes"]
            labels = {}
            for _, item in self.callouts(chapter["id"]):
                label, _, variant, _ = self._callout_parts(item)
                labels.setdefault(label, variant)
            index = 0
            while index < len(items):
                item = items[index]
                if is_plain(item):
                    value = squash(text_of(item))
                    # 'Remarks Please select …' (EN 2.4): label glued to its body.
                    label = next((lb for lb in labels if value.startswith(lb + " ")
                                  and value[len(lb) + 1:][:1].isupper()), None)
                    if label and self.pdf.styled(self.locale_pages, label):
                        body = value[len(label) + 1:]
                        items[index] = self._rebuild_callout(
                            label, [paragraph(body)], labels[label],
                            f"native-pdf/{chapter['id']}/label-{index}")
                        self.note(chapter["id"], "glued-label-callout", label=label)
                    # '<body>' followed by a separate '<label>' paragraph/heading (FR/ES STS note).
                    elif index + 1 < len(items):
                        following = items[index + 1]
                        name = squash(text_of(following))
                        if following.get("kind") in ("paragraph", "heading") and name in labels:
                            items[index] = self._rebuild_callout(
                                name, [paragraph(value)], labels[name],
                                f"native-pdf/{chapter['id']}/label-{index}")
                            del items[index + 1]
                            self.note(chapter["id"], "split-label-callout", label=name)
                index += 1

    # ---- LCD -----------------------------------------------------------------
    def lcd_screen(self) -> None:
        """The print's LCD SCREEN panel: device art beside two states × three actions.

        The approved intake kept these cells as loose (and, in Spanish, fragmented)
        paragraphs. Cells are rebuilt from the print table geometry; their words must
        be exactly the approved words, so no copy is added, dropped or respelled.
        """
        items = self.nodes("operations")
        start = next(i for i, item in enumerate(items) if "native-lcd-button" in css_class(item))
        heading = items[start - 1]
        end = start + 1
        while end < len(items) and is_plain(items[end]):
            end += 1
        paragraphs = items[start + 1:end]
        if heading.get("kind") != "heading" or len(paragraphs) < 14:
            raise ValueError(f"{self.language}: LCD SCREEN copy not found after its artwork")
        approved_words = sorted(key(w) for item in paragraphs for w in squash(text_of(item)).split())
        page = page_of(self.language, 11)
        document_page = self.pdf.document[page - 1]
        lines = [line for line in self.pdf.lines(page)
                 if line["bbox"][0] > 170 and 365 < line["bbox"][1] < 495]
        drawings = document_page.get_drawings()
        rules = sorted({round(d["rect"].y0, 1) for d in drawings
                        if d["rect"].x0 > 170 and 365 < d["rect"].y0 < 495
                        and d["rect"].height < 1.5 and d["rect"].width > 20})
        bold = [line for line in lines if line["bold"]]
        state_x = min(line["bbox"][0] for line in bold)
        action_x = min(line["bbox"][0] for line in bold if line["bbox"][0] > state_x + 15)
        divider = [d["rect"] for d in drawings
                   if 170 < d["rect"].x0 < action_x - 10
                   and 365 < d["rect"].y0 < 495 and d["rect"].height < 1.5 and d["rect"].width > 60]
        if len(rules) != 5 or len(divider) != 1:
            raise ValueError(f"{self.language}: LCD SCREEN rules not found: {rules}")
        edges = [float("-inf"), *rules, float("inf")]

        def cell_text(column, low, high):
            chosen = [line for line in column if low <= (line["bbox"][1] + line["bbox"][3]) / 2 < high]
            value = squash(" ".join(line["text"] for line in sorted(chosen, key=lambda l: l["bbox"][1])))
            if not value:
                raise ValueError(f"{self.language}: empty LCD SCREEN cell")
            return value

        states = [line for line in bold if line["bbox"][0] < action_x - 5]
        actions = [line for line in bold if line["bbox"][0] >= action_x - 5]
        copy_lines = [line for line in lines if not line["bold"]]
        groups, cells = [], []
        for g, (low, high) in enumerate(((edges[0], divider[0].y0), (divider[0].y0, edges[-1]))):
            rows = []
            for r in range(3):
                top, bottom = edges[g * 3 + r], edges[g * 3 + r + 1]
                action, description = cell_text(actions, top, bottom), cell_text(copy_lines, top, bottom)
                cells += [action, description]
                rows.append({"action_html": html.escape(action, quote=False), "action_text": action,
                             "description_html": html.escape(description, quote=False),
                             "description_text": description})
            state = cell_text(states, low, high)
            cells.append(state)
            groups.append({"state_html": html.escape(state, quote=False), "state_text": state, "actions": rows})
        if sorted(key(w) for value in cells for w in value.split()) != approved_words:
            raise ValueError(f"{self.language}: LCD SCREEN cells do not reuse exactly the approved words")
        spec = lcd_mode_component_spec(
            accessibility_label=squash(text_of(heading)), groups=groups,
            artwork_ref="assets/lcd-button.svg", source_ref=f"native-pdf/page-{page}/lcd-screen",
            language=self.language, artwork_locale_policy="shared",
        )
        items[start:end] = [flow_root(group([component_flow_node(spec)], "native-lcd-panel"))]
        self.note("operations", "lcd-screen-table", states=[g["state_text"] for g in groups],
                  approved_paragraphs=len(paragraphs))

    def lcd_icons(self) -> None:
        """Circled numbers, one number cell per printed entry, one line per state."""
        items = self.nodes("lcd")
        index = next(i for i, item in enumerate(items) if component_id(item) == "HB-TABLE-LCD-ICON")
        spec = copy.deepcopy(items[index]["component_spec"])
        rows = next(slot for slot in spec["slots"] if slot["role"] == "rows")["content"]
        broken = 0
        for row in rows:
            row["number_html"] = f'<span class="native-lcd-number">{row["number_text"]}</span>'
            value = row["description_html"]
            # Each later state label (Blink:, Off:, On/Off: …) starts a print line.
            value, count = re.subn(r"(?<=[^\s>])\s*(<strong>[^<]+</strong>\s*:)", r"<br>\1", value)
            row["description_html"] = value
            broken += count
        self._lcd_name_boundaries(rows)
        spec["metadata"] = {**spec.get("metadata", {}), "number_cell_layout": "span-adjacent-equal"}
        items[index] = component_flow_node(ComponentSpec.from_dict(spec), root=True)
        self.note("lcd", "lcd-icon-print-structure", state_lines=broken)

    def _lcd_name_boundaries(self, rows: list[dict]) -> None:
        """Words the intake moved across a row boundary (FR p33 'élevée', ES p57 'Indicador de')."""
        def split(row):
            head, *rest = row["name_html"].split("<br>", 1)
            return html.unescape(head), ("<br>" + rest[0]) if rest else ""
        for row, following in zip(rows, rows[1:], strict=False):
            (a, a_tail), (b, b_tail) = split(row), split(following)
            # Only a visibly broken pair: a name that starts lower-case or ends on a
            # preposition/article. The print text then decides where the words belong.
            broken = b[:1].islower() or re.search(
                r"\b(de|du|des|del|la|le|el|of|the|and|y|et|à|a|en|para|pour|for|to)$", a, re.I)
            if "<" in a + b or not broken:
                continue
            a_words, b_words = a.split(), b.split()
            options = [(" ".join(a_words + b_words[:k]), " ".join(b_words[k:])) for k in (1, 2, 3)]
            options += [(" ".join(a_words[:-k]), " ".join(a_words[-k:] + b_words)) for k in (1, 2, 3)]
            for new_a, new_b in options:
                if new_a and new_b and self.print_text.find(new_a) and self.print_text.find(new_b):
                    self.restorations.append({"chapter": "lcd", "kind": "lcd-name-word-boundary",
                                              "approved": [a, b], "pdf": [new_a, new_b]})
                    for target, old, new, tail in ((row, a, new_a, a_tail), (following, b, new_b, b_tail)):
                        target["name_html"] = html.escape(new, quote=False) + tail
                        target["name_text"] = new + target["name_text"][len(old):]
                        if target["icon_alt"].startswith(old):
                            target["icon_alt"] = new + target["icon_alt"][len(old):]
                    break

    # ---- warranty -------------------------------------------------------------
    def warranty(self) -> None:
        """Card paragraphs follow the print; FR 5-year title/body boundary restored."""
        for index, item in enumerate(self.nodes("warranty")):
            identity = component_id(item)
            if identity not in ("HB-WARRANTY-SECTION", "HB-WARRANTY-YEARS"):
                continue
            spec = copy.deepcopy(item["component_spec"])
            changed = False
            for slot in spec["slots"]:
                if slot["role"] == "blocks":
                    blocks = []
                    for block in slot["content"]:
                        parts = self._print_paragraphs(block["text"]) if block["kind"] == "paragraph" else [block["text"]]
                        if len(parts) > 1:
                            # The card appends block fragments as-is; only <p> keeps them apart.
                            changed = True
                            blocks.extend({"kind": "paragraph", "html": f"<p>{html.escape(p)}</p>", "text": p}
                                          for p in parts)
                        else:
                            blocks.append(block)
                    slot["content"] = blocks
                if slot["role"] == "periods":
                    for period in slot["content"]:
                        label, body = period["label"], period["body_text"]
                        if self.print_text.find(label) is not None:
                            continue
                        words = label.split()
                        for cut in range(1, len(words)):
                            head, tail = " ".join(words[:cut]), " ".join(words[cut:])
                            title = self.pdf.styled(self.pages(22), tail)
                            if title and title["bold"] and self.print_text.find(head + " " + body[:40]):
                                self.restorations.append({"chapter": "warranty", "kind": "warranty-title-body-boundary",
                                                          "approved": [label, body[:60]], "pdf": [tail, (head + " " + body)[:60]]})
                                period["label"] = tail
                                period["body_text"] = head + " " + body
                                period["body_html"] = html.escape(head) + " " + period["body_html"]
                                changed = True
                                break
            if changed:
                self.nodes("warranty")[index] = component_flow_node(ComponentSpec.from_dict(spec), root=True)
                self.note("warranty", "warranty-print-paragraphs", component=identity)

    def _print_paragraphs(self, value: str) -> list[str]:
        found = self.pdf.run(self.locale_pages, value)
        words = words_by_line(value, found[1]) if found and len(found[1]) > 1 else None
        if not words:
            return [value]
        run = found[1]
        right = max(line["bbox"][2] for line in run)
        parts, current = [], []
        for i, (line, chunk) in enumerate(zip(run, words, strict=True)):
            current.extend(chunk)
            if i == len(run) - 1 or (re.search(r"[.!?:;。]$", line["text"]) and run[i + 1]["text"][:1].isupper()
                                     and hard_break(line, run[i + 1], right)):
                parts.append(" ".join(current))
                current = []
        return parts

    # ---- troubleshooting ----------------------------------------------------
    def troubleshooting(self) -> None:
        """Codes and names are bold in print; each cause starts its own description line."""
        wrapper = self.nodes("troubleshooting")[1]
        body = next(inner for _, _, inner in walk([wrapper]) if inner.get("kind") == "table_body")
        page = page_of(self.language, 12)

        def described(line: dict) -> bool:  # the description column; FR F3's name repeats its text
            return line["bbox"][0] > 150 and not line["bold"]

        right = max(line["bbox"][2] for line in self.pdf.lines(page) if described(line))
        breaks = 0
        for row in body["children"]:
            code, name, description = row["children"]
            code["children"] = [strong(squash(text_of(code)))]
            name["children"] = [strong(squash(text_of(name)))]
            value = squash(text_of(description))
            found = self.pdf.run([page], value, keep=described)
            words = words_by_line(value, found[1]) if found else None
            if not words:
                continue
            run = found[1]
            parts, current = [], []
            for i, (line, chunk) in enumerate(zip(run, words, strict=True)):
                current.extend(chunk)
                last = i == len(run) - 1
                # A cause ends at ';' or where print stops a line early before a capitalized
                # word; lower-case or acronym continuations (FA, ES F2 'BMS') flow on.
                following = "" if last else run[i + 1]["text"].strip()
                if (last or line["text"].endswith(";")
                        or (hard_break(line, run[i + 1], right) and following[:1].isupper()
                            and following[1:2].islower())):
                    parts.append(" ".join(current))
                    current = []
            children = []
            for part in parts:
                if children:
                    children.append(node("line_break"))
                children.append(text(part))
            description["children"] = children
            breaks += len(parts) - 1
        self.note("troubleshooting", "codes-names-bold-cause-lines", line_breaks=breaks)

    def chapter_title_tail(self) -> None:
        """ES p61: '(UPS)' ended the title line in print but became a stray heading."""
        for chapter in self.content["chapters"]:
            items = chapter["nodes"]
            last, head = items[-1], items[0]
            tail = squash(text_of(last))
            if last.get("kind") != "heading" or not re.fullmatch(r"\(.+\)", tail):
                continue
            title = squash(text_of(head)) + " " + tail
            if not self.pdf.styled(self.locale_pages, title):
                continue
            head["children"] = [text(title)]
            chapter["title"] = title
            del items[-1]
            self.restorations.append({"chapter": chapter["id"], "kind": "title-tail",
                                      "approved": [squash(text_of(head)), tail], "pdf": title})
            self.note(chapter["id"], "title-tail-restored", title=title)

    def folio_continuations(self) -> None:
        """A last body line printed down by the folio was classified as the folio (ES p69)."""
        for chapter in self.content["chapters"]:
            for _, _, item in list(walk(chapter["nodes"])):
                if item.get("kind") not in ("paragraph", "list_item") or not is_plain(item, item["kind"]):
                    continue
                value = squash(text_of(item))
                found = self.pdf.run(self.locale_pages, value)
                if not found:
                    continue
                page, run = found
                last = run[-1]
                below = [line for line in self.pdf.lines(page)
                         if line["bbox"][1] >= 495 and 0 < line["bbox"][1] - last["bbox"][1] < 12
                         and abs(line["bbox"][0] - last["bbox"][0]) < 15 and not line["text"].isdigit()]
                if len(below) != 1:
                    continue
                combined = value + " " + below[0]["text"]
                if not self.pdf.run([page], combined):
                    continue
                item["children"] = [text(combined)]
                self.restorations.append({"chapter": chapter["id"], "kind": "folio-swallowed-line",
                                          "approved": value[-60:], "pdf": combined[-60:]})
                self.note(chapter["id"], "folio-line-restored", text=below[0]["text"])

    def hidden_glyphs(self) -> None:
        """ES p54: the inbox note label's '*' is painted over by the note box in print."""
        items = self.nodes("inbox")
        index = next(i for i, item in enumerate(items) if component_id(item) == "HB-SPECIAL-INBOX")
        data = copy.deepcopy(items[index]["component_spec"])
        slot = next(s for s in data["slots"] if s["role"] == "tip_label")
        if not slot["content"].startswith("* "):
            return
        page = self.pdf.document[page_of(self.language, 6) - 1]
        star = next(t for t in page.get_texttrace()
                    if "".join(chr(c[0]) for c in t["chars"]).strip() == "*")
        centre = fitz.Point((star["bbox"][0] + star["bbox"][2]) / 2, (star["bbox"][1] + star["bbox"][3]) / 2)
        if not any(d["seqno"] > star["seqno"] and d.get("fill") and d["rect"].contains(centre)
                   for d in page.get_drawings()):
            return
        old = slot["content"]
        slot["content"] = old[2:]
        carrier = copy.deepcopy(items[index]["carrier_flow"])
        for _, _, inner in walk(carrier):
            if inner.get("kind") == "text" and inner.get("text") == old:
                inner["text"] = slot["content"]
        items[index] = component_flow_node(ComponentSpec.from_dict(data), carrier_flow=carrier, root=True)
        self.restorations.append({"chapter": "inbox", "kind": "hidden-print-glyph", "approved": old,
                                  "pdf": slot["content"]})
        self.note("inbox", "hidden-asterisk-removed")

    # ---- headings, badges and bands ----------------------------------------
    def sold_separately(self) -> None:
        """'SOLD SEPARATELY' is a capsule beside its print title, not a paragraph."""
        for chapter in self.content["chapters"]:
            items = chapter["nodes"]
            index = 0
            while index < len(items) - 1:
                heading, badge = items[index], items[index + 1]
                if heading.get("kind") == "heading" and is_plain(heading, "heading") and is_plain(badge):
                    label = squash(text_of(badge))
                    line = self.pdf.styled(self.locale_pages, label)
                    if line and line["white"] and len(label) < 30:
                        title = squash(text_of(heading))
                        heading["children"] = [span(title, "hb-heading-title"), text(" "),
                                               span(label, "hb-sold-separately")]
                        del items[index + 1]
                        self.note(chapter["id"], "sold-separately-capsule", title=title)
                index += 1

    def safety_bands(self) -> None:
        """Safety sub-titles: white-on-dark pills, except the outlined risk banner."""
        for chapter in ("safety", "maintenance", "symbols"):
            items = self.nodes(chapter)
            for index, item in enumerate(items):
                if item.get("kind") != "heading" or item["level"] != 3 or not is_plain(item, "heading"):
                    continue
                title = squash(text_of(item))
                line = self.pdf.styled(self.pages(4, 5), title)
                if line and line["white"]:
                    item["children"] = [span(title, "native-band")]
                    self.note(chapter, "print-pill-title", title=title)
                elif chapter == "safety" and index == 1:
                    items[index] = flow_root(group([
                        node("image", source="assets/warning_triangle_dark.svg", alt=""),
                        node("paragraph", [strong(title)]),
                    ], "hb-source-safety-heading"))
                    self.note(chapter, "risk-banner", title=title)

    def model_bands(self) -> None:
        """Model identities sit at the right of their print bands, not as headings below."""
        models: dict[str, str] = {}
        for chapter in ("ess-host", "ess-battery", "ess-sts"):
            items = self.nodes(chapter)
            for index in reversed(range(len(items))):
                item = items[index]
                match = MODEL_LABEL.match(squash(text_of(item))) if item.get("kind") == "heading" else None
                if match:
                    models[match.group(1)] = (chapter, squash(text_of(item)))
                    del items[index]
        for chapter in ("ess-host", "ess-battery", "ess-sts"):
            specs = [item["component_spec"] for item in self.nodes(chapter) if component_id(item) == "HB-TABLE-SPEC"]
            values = {v["text"] for spec in specs for slot in spec["slots"] if slot["role"] == "rows"
                      for row in slot["content"] for v in row["values"]}
            owned = [m for m in models if m in values]
            if len(owned) != 1:
                raise ValueError(f"{self.language}: {chapter} model label not found: {models}")
            source, label = models[owned[0]]
            heading = self.nodes(chapter)[0]
            title = squash(text_of(heading))
            heading["children"] = [span(title, "hb-heading-title"), text(" "), span(label, "hb-heading-model")]
            if source != chapter:
                self.restorations.append({"chapter": chapter, "kind": "model-label-placement",
                                          "approved": f"{source}: {label}", "pdf": f"{chapter} band: {label}"})
            self.note(chapter, "model-in-band", model=label)
        # The installation guide band carries 'System Model' / its identifier on two lines.
        items = self.nodes("ess")
        tail = [item for item in items[-2:] if is_plain(item)]
        value = squash(" ".join(text_of(item) for item in tail))
        match = re.match(r"^(.*?)\s*(HB\S+)$", value)
        if not match or not match.group(1):
            raise ValueError(f"{self.language}: system model not found at the end of ess: {value!r}")
        del items[len(items) - len(tail):]
        heading = items[0]
        title = squash(text_of(heading))
        heading["children"] = [span(title, "hb-heading-title"), text(" "),
                               span([strong(match.group(1)), node("line_break"), text(match.group(2))],
                                    "hb-heading-model")]
        self.note("ess", "system-model-in-band", model=value)

    def plain_titles(self) -> None:
        """Product chapters print 'SPECIFICATIONS' as a plain bold title (no bullet)."""
        for chapter in ("ess-host",):
            for item in self.nodes(chapter):
                if item.get("kind") == "heading" and is_plain(item, "heading") and item["level"] == 4:
                    title = squash(text_of(item))
                    item["children"] = [span(title, "native-plain-title")]
                    self.note(chapter, "plain-title", title=title)

    def prose_pills(self) -> None:
        """Standalone white-on-dark print lines ('Fully charge …') are prose capsules."""
        for chapter in self.content["chapters"]:
            for index, item in enumerate(chapter["nodes"]):
                if not is_plain(item):
                    continue
                value = squash(text_of(item))
                found = self.pdf.run(self.locale_pages, value)
                if found and all(line["white"] for line in found[1]):
                    chapter["nodes"][index] = flow_root(with_class(node("paragraph", [strong(value)]),
                                                                   "hb-prose-pill"))
                    self.note(chapter["id"], "prose-pill", text=value[:60])

    def bulleted_subheads(self) -> None:
        """'• Connect to …' lines are bold bullet subheads in print."""
        for chapter in self.content["chapters"]:
            for index, item in enumerate(chapter["nodes"]):
                if not is_plain(item):
                    continue
                value = squash(text_of(item))
                found = self.pdf.run(self.locale_pages, value)
                if (found and len(found[1]) == 1 and found[1][0]["bold"]
                        and (found[1][0]["bullet"] or self.pdf.drawn_bullet(found[0], found[1][0]))):
                    chapter["nodes"][index] = flow_root(node("list", [node("list_item", [strong(value)])],
                                                             ordered=False))
                    self.note(chapter["id"], "bullet-subhead", text=value)

    # ---- specifications -----------------------------------------------------
    def spec_values(self) -> None:
        """A value printed on several lines of its cell is several values of one label."""
        for chapter in self.content["chapters"]:
            items = chapter["nodes"]
            for index, item in enumerate(items):
                if component_id(item) != "HB-TABLE-SPEC":
                    continue
                spec = ComponentSpec.from_dict(item["component_spec"])
                title = spec.slot("section_title").content
                rows, split = [], []
                for row in spec.slot("rows").content:
                    values = []
                    for value in row["values"]:
                        parts = self._value_lines(value["text"])
                        if len(parts) > 1:
                            split.append(value["text"])
                        values.extend(parts)
                    rows.extend([row["label"] if i == 0 else "", v] for i, v in enumerate(values))
                if not split:
                    continue
                new = spec_table_component_spec(section_title=title, rows=rows, source_ref=spec.source_ref,
                                                language=self.language, metadata=dict(spec.metadata))
                items[index] = component_flow_node(new, carrier_flow=spec_carrier(new), root=True)
                self.note(chapter["id"], "spec-value-print-lines", table=title, values=split)

    def _value_lines(self, value: str) -> list[str]:
        """Print spec cells never wrap here: each print line is one value (all locales checked)."""
        found = self.pdf.run(self.locale_pages, value)
        if not found or len(found[1]) < 2:
            return [value]
        words = words_by_line(value, found[1])
        return [" ".join(chunk) for chunk in words] if words else [value]

    def spec_hazard_rows(self) -> None:
        """FR/ES intake fused the hazard note into the last temperature row; print sets it below."""
        for chapter in self.content["chapters"]:
            items = chapter["nodes"]
            for index, item in enumerate(items):
                if component_id(item) != "HB-TABLE-SPEC":
                    continue
                spec = ComponentSpec.from_dict(item["component_spec"])
                rows = copy.deepcopy(spec.slot("rows").content)
                fused = [row for row in rows if INGESTION.match(row["label"])]
                if not fused:
                    continue
                row = fused[0]
                hazard_line = next((line["text"] for page in self.locale_pages for line in self.pdf.lines(page)
                                    if INGESTION.match(line["text"])), None)
                if hazard_line is None:
                    raise ValueError(f"{self.language}: print hazard note not found")
                wanted = [key(w) for w in hazard_line.split() if key(w)]
                taken, label_words, value_words = [], row["label"].split(), row["values"][0]["text"].split()
                for words in (label_words, value_words):
                    while words and wanted and (not key(words[0]) or key(words[0]) == wanted[0]):
                        word = words.pop(0)
                        taken.append(word)
                        if key(word):
                            wanted.pop(0)
                if wanted:
                    raise ValueError(f"{self.language}: hazard words not all found in the fused row")
                hazard = " ".join(taken)
                approved = (row["label"], row["values"][0]["text"])
                row["label"] = " ".join(label_words)
                row["values"][0]["text"] = " ".join(value_words)
                flat = [[r["label"] if i == 0 else "", v["text"]] for r in rows for i, v in enumerate(r["values"])]
                new = spec_table_component_spec(section_title=spec.slot("section_title").content, rows=flat,
                                                source_ref=spec.source_ref, language=self.language,
                                                metadata=dict(spec.metadata))
                items[index:index + 1] = [component_flow_node(new, carrier_flow=spec_carrier(new), root=True),
                                          flow_root(paragraph(hazard))]
                self.restorations.append({"chapter": chapter["id"], "kind": "hazard-note-out-of-spec-row",
                                          "approved": approved, "pdf": [row["label"], hazard]})
                self.note(chapter["id"], "hazard-note-below-table")
                break

    def trademark_notes(self) -> None:
        """Restore the detached '®' marks to their print positions and split the hazard note."""
        for chapter in self.content["chapters"]:
            items = chapter["nodes"]
            index = 0
            while index < len(items):
                item = items[index]
                if not is_plain(item) or "※" not in text_of(item):
                    index += 1
                    continue
                value = squash(text_of(item))
                head, mark, tail = value.partition("※")
                hazard = head.replace("®", "").strip()
                approved_note = mark + tail
                note_line = self._trademark_line(approved_note)
                children, pieces = [], re.split(r"(®)", note_line)
                for piece in pieces:
                    if piece == "®":
                        children.append(node("superscript", [text("®")]))
                    elif piece:
                        children.append(text(piece))
                replacement = ([flow_root(paragraph(hazard))] if hazard else []) + [
                    flow_root(with_class(node("paragraph", children), "native-trademark"))]
                items[index:index + 1] = replacement
                if note_line.replace("®", "") != approved_note.replace("®", "") or "®" in head:
                    self.restorations.append({"chapter": chapter["id"], "kind": "registered-mark-position",
                                              "approved": value, "pdf": " | ".join(filter(None, [hazard, note_line]))})
                self.note(chapter["id"], "trademark-note", split_hazard=bool(hazard))
                index += len(replacement)

    def _trademark_line(self, approved: str) -> str:
        """Print text of the trademark note with each '®' after the word it follows."""
        wanted = key(approved)
        for page in self.locale_pages:
            document_page = self.pdf.document[page - 1]
            for block in document_page.get_text("rawdict")["blocks"]:
                for line in block.get("lines", []):
                    chars = [c for s in line["spans"] for c in s["chars"]]
                    value = "".join(c["c"] for c in chars)
                    if "※" not in value or key(value) != wanted.replace("®", ""):
                        continue
                    marks = [c for b in document_page.get_text("rawdict")["blocks"]
                             for ln in b.get("lines", []) for s in ln["spans"] for c in s["chars"]
                             if c["c"] == "®" and abs(c["bbox"][3] - line["bbox"][3]) < 6]
                    out = []
                    for c in chars:
                        out.append(c["c"])
                        if any(abs(m["bbox"][0] - c["bbox"][2]) < 1.2 for m in marks) and c["c"].strip():
                            out.append("®")
                    restored = squash("".join(out))
                    if restored.count("®") == 2:
                        return restored
        if approved.count("®") == 2:
            return approved
        raise ValueError(f"{self.language}: trademark note not found in print: {approved!r}")

    def ingestion_notes(self) -> None:
        """Hazard note: print glyph, bold label, and its print place before the trademark note."""
        for chapter in self.content["chapters"]:
            items = chapter["nodes"]
            for index, item in enumerate(items):
                if not is_plain(item):
                    continue
                value = squash(text_of(item))
                match = INGESTION.match(value)
                if not match:
                    continue
                label, rest = value.split(":", 1) if ":" in value else (value, "")
                label = label.strip() + ":" if value[len(label.strip()):].lstrip().startswith(":") else label
                head = value[:value.index(":") + 1]
                items[index] = flow_root(with_class(node("paragraph", [
                    node("image", source="assets/" + INGESTION_ART, alt=""),
                    strong(head), text(value[len(head):]),
                ]), "native-ingestion"))
                self.note(chapter["id"], "ingestion-note")
            # Print order: hazard note, then the trademark note.
            for index in range(len(items) - 1):
                if "native-trademark" in css_class(items[index]) and "native-ingestion" in css_class(items[index + 1]):
                    items[index], items[index + 1] = items[index + 1], items[index]
                    self.note(chapter["id"], "ingestion-before-trademark")

    # ---- paragraphs ----------------------------------------------------------
    def merge_soft_wraps(self) -> None:
        """Join paragraphs the intake split at print line wraps (no sentence end, lowercase next)."""
        for chapter in self.content["chapters"]:
            if chapter["id"] == "contact":
                continue
            items = chapter["nodes"]
            index = 0
            while index < len(items) - 1:
                first, second = items[index], items[index + 1]
                if is_plain(first) and is_plain(second):
                    a, b = squash(text_of(first)), squash(text_of(second))
                    if a and b and not re.search(r"[.!?:;)。：]$", a) and re.match(r"[a-zà-ÿ0-9(]", b):
                        items[index] = flow_root(paragraph(a + " " + b))
                        del items[index + 1]
                        self.note(chapter["id"], "soft-wrap-joined", text=(a + " " + b)[:80])
                        continue
                index += 1

    def print_paragraph_breaks(self) -> None:
        """A sentence that ends a print line early, followed by a new sentence, is a new paragraph."""
        for chapter in self.content["chapters"]:
            items = chapter["nodes"]
            index = 0
            while index < len(items):
                item = items[index]
                parts = self._print_paragraphs(squash(text_of(item))) if is_plain(item) else []
                if len(parts) > 1:
                    items[index:index + 1] = [flow_root(paragraph(p)) for p in parts]
                    self.note(chapter["id"], "print-paragraph-break", paragraphs=len(parts))
                    index += len(parts)
                else:
                    index += 1

    def print_emphasis(self) -> None:
        """Bold runs of the print (sub-heads, lead-ins) inside plain paragraphs and list items."""
        changed = []
        for chapter in self.content["chapters"]:
            for container, index, item in list(walk(chapter["nodes"])):
                if item.get("kind") not in ("paragraph", "list_item") or not is_plain(item, item["kind"]):
                    continue
                value = squash(text_of(item))
                flags = self.print_text.find(value)
                if not flags or not any(flags):
                    continue
                words, bold, cursor, previous = value.split(), [], 0, False
                for word in words:
                    width = len(key(word))
                    if width:
                        previous = all(flags[cursor:cursor + width])
                        cursor += width
                    bold.append(previous)
                runs: list[tuple[bool, list[str]]] = []
                for word, flag in zip(words, bold, strict=True):
                    if runs and runs[-1][0] == flag:
                        runs[-1][1].append(word)
                    else:
                        runs.append((flag, [word]))
                out = []
                for i, (flag, run_words) in enumerate(runs):
                    value_ = " ".join(run_words)
                    if flag:
                        out.append(strong(value_))
                    else:
                        out.append(text((" " if i else "") + value_ + (" " if i < len(runs) - 1 else "")))
                item["children"] = out
                changed.append({"chapter": chapter["id"], "text": value[:70],
                                "bold": [" ".join(w) for f, w in runs if f][:3]})
        self.note("*", "print-emphasis", items=changed)

    def merge_adjacent_lists(self) -> None:
        for chapter in self.content["chapters"]:
            items = chapter["nodes"]
            index = 0
            while index < len(items) - 1:
                a, b = items[index], items[index + 1]
                if (a.get("kind") == b.get("kind") == "list" and a.get("ordered") == b.get("ordered")
                        and "start" not in b and not css_class(a) and not css_class(b)):
                    a["children"].extend(b["children"])
                    del items[index + 1]
                    self.note(chapter["id"], "adjacent-lists-merged")
                    continue
                index += 1

    def contact_card(self) -> None:
        """Back cover (p76): company, address and one contact panel; no invented title."""
        items = self.nodes("contact")
        heading, company, address, lines = items
        if heading.get("anchor") != "native-contact" or company.get("kind") != "heading":
            raise ValueError(f"{self.language}: unexpected contact chapter")
        value = squash(text_of(lines))
        email = re.search(r"\S+@\S+", value).group(0)
        web = re.search(r"www\.\S+", value).group(0)
        phone = re.search(r"([\d-]{10,})\s*(\([A-Z]{2}\))?", value)
        if squash(" ".join(filter(None, [email, phone.group(0), web]))) != value:
            raise ValueError(f"{self.language}: contact line has unexpected copy: {value!r}")
        def glyph(name):
            return node("image", source="assets/" + name, alt="", presentation=attrs("native-contact-glyph"))
        panel = group([
            node("paragraph", [glyph("contact-phone.svg"), strong(phone.group(1))]
                 + ([text(" "), span(phone.group(2), "native-contact-region")] if phone.group(2) else []),
                 presentation=attrs("native-contact-phone")),
            group([node("paragraph", [glyph("contact-mail.svg"), text(email)], presentation=attrs("native-contact-email")),
                   node("paragraph", [glyph("contact-web.svg"), text(web)], presentation=attrs("native-contact-web"))],
                  "native-contact-links"),
        ], "native-contact-panel")
        # Print sets the QR code in its own small frame beside the contact panel.
        panel = group([panel, group([node("image", source="assets/contact-qr.svg", alt="")], "native-contact-qr")],
                      "native-contact-row")
        items[:] = [flow_root(group([
            node("paragraph", [strong(squash(text_of(company)))], presentation=attrs("native-contact-company")),
            node("paragraph", [text(squash(text_of(address)))], presentation=attrs("native-contact-address")),
            panel,
        ], "native-contact-card", anchor="native-contact"))]
        self.note("contact", "back-cover-card", removed_title=squash(text_of(heading)))
        # The p76 back cover prints no title above JACKERY INC.
        self.restorations.append({"chapter": "contact", "kind": "unprinted-title",
                                  "approved": squash(text_of(heading)), "pdf": None})

    # ---- art -----------------------------------------------------------------
    def overview_frames(self) -> None:
        """Labels keep their print positions inside the regrown overview frames."""
        for item in self.nodes("overview"):
            figure = next((f for f in FRAMES if f"native-{f} " in css_class(item) + " "), None)
            if figure is None:
                continue
            old_top, old_bottom, new_top, new_bottom = FRAMES[figure]
            old_height, new_height = old_bottom - old_top, new_bottom - new_top
            component = item["children"][0]
            spec = copy.deepcopy(component["component_spec"])
            layout = spec["metadata"]["base_art_layout"]
            for label in layout["labels"]:
                x, y, w, h = label["rect"]
                label["rect"] = [x, (y / 100 * old_height + old_top - new_top) / new_height * 100,
                                 w, h * old_height / new_height]
            # The art bytes are bound here; source_fragment_sha256 hashes the semantic
            # carrier and captions, which are unchanged.
            layout["art_sha256"] = self.art[figure + ".svg"]
            carrier = copy.deepcopy(component["carrier_flow"])
            # Print right-aligns the label column at the frame's right edge; Web glyphs run a
            # few pixels wider, so those lines grow leftwards instead of past the frame.
            block = next(n for _, _, n in walk(carrier) if "line-block" in css_class(n))
            edge = [label["line"] for label in layout["labels"] if label["rect"][0] + label["rect"][2] >= 98]
            for line in edge:
                inner = block["children"][line]["children"][0]
                inner["presentation"] = attrs("native-edge-right")
            item["children"][0] = component_flow_node(ComponentSpec.from_dict(spec), carrier_flow=carrier)
            self.note("overview", "full-frame", figure=figure, top=new_top, bottom=new_bottom,
                      right_aligned_lines=edge)

    def locale_art(self) -> None:
        """FR/ES figures use their own print panel; label rects are already in that frame."""
        for chapter in self.content["chapters"]:
            for _, _, item in list(walk(chapter["nodes"])):
                identity = next((f for f in LOCALE_ART if f"native-{f} " in css_class(item) + " "), None)
                if identity is None or self.language not in LOCALE_ART[identity]:
                    continue
                component = item["children"][0]
                spec = copy.deepcopy(component["component_spec"])
                name = f"assets/{identity}-{self.language}.svg"
                old = spec["assets"][0]["asset_ref"]
                spec["assets"][0].update(asset_ref=name, locale_policy="exact")
                if spec["metadata"].get("base_art_layout"):
                    spec["metadata"]["base_art_layout"]["art_sha256"] = self.art[f"{identity}-{self.language}.svg"]
                carrier = copy.deepcopy(component["carrier_flow"])
                for _, _, inner in walk(carrier):
                    if inner.get("kind") == "image" and inner.get("source") == old:
                        inner["source"] = name
                item["children"][0] = component_flow_node(ComponentSpec.from_dict(spec), carrier_flow=carrier)
                self.note(chapter["id"], "locale-art", figure=identity, art=name, replaced=old)

    def refresh_reference_figures(self) -> None:
        """Re-derive caption slots from the edited carrier lines and re-bind the fragment hash.

        The hash is the shared renderer's own (semantic carrier + caption text), computed
        exactly as the approved intake did; figures whose captions did not change keep it.
        """
        changed = []
        for chapter in self.content["chapters"]:
            for container, index, item in list(walk(chapter["nodes"])):
                if component_id(item) != "HB-SPECIAL-REFERENCE-FIGURE":
                    continue
                data = copy.deepcopy(item["component_spec"])
                carrier = item["carrier_flow"]
                block = next((n for _, _, n in walk(carrier) if "line-block" in css_class(n)), None)
                if block is not None:
                    captions = next(slot for slot in data["slots"] if slot["role"] == "captions")
                    lines = block["children"]
                    if len(lines) != len(captions["content"]):
                        raise ValueError(f"{self.language}: caption lines disagree for {data['source_ref']}")
                    for caption, line in zip(captions["content"], lines, strict=True):
                        markup = flow_nodes_to_html([flow_root(copy.deepcopy(line["children"][0]))])
                        caption["html"] = markup
                        caption["text"] = BeautifulSoup(markup, "html.parser").get_text(" ", strip=True)
                spec = ComponentSpec.from_dict(data)
                payload = web_reference_figure_projection(spec)
                payload.update(capture_following_lines=int(spec.metadata.get("capture_following_lines") or 0),
                               captions_origin=str(spec.metadata.get("captions_origin") or "carrier"),
                               composite_locale=str(spec.metadata.get("composite_locale") or ""))
                soup = BeautifulSoup(flow_nodes_to_html([flow_root(copy.deepcopy(n)) for n in carrier]), "html.parser")
                image = _validate_carrier(payload, soup)
                _transform_reference_figure(soup, image=image, spec=_component_contract(payload),
                                            source_path=Path(spec.source_ref),
                                            composites=WebCompositeContext(None, "JHP-5000C", "US",
                                                                           spec.language, ValueError))
                digest = soup.figure["data-source-fragment-sha256"]
                if digest != data["metadata"].get("source_fragment_sha256"):
                    changed.append(data["source_ref"])
                data["metadata"]["source_fragment_sha256"] = digest
                fresh = component_flow_node(ComponentSpec.from_dict(data), carrier_flow=carrier)
                if "schema_version" in item:
                    fresh = flow_root(fresh)
                container[index] = fresh
        self.note("*", "reference-captions-rebound", figures=changed)

    # ---- writing -----------------------------------------------------------
    def write(self) -> None:
        target = HERE / f"source/{self.language}"
        target.mkdir(parents=True, exist_ok=True)
        (target / "content.json").write_text(json.dumps(self.content, ensure_ascii=False, indent=2) + "\n")
        (target / "web_layout.json").write_text(json.dumps(
            {"schema_version": "jhp5000c-web-layout-changes/v1", "language": self.language,
             "approved_source": f"../git-20261009-051169dd/source/{self.language}/content.json",
             "changes": self.log, "copy_restorations": self.restorations},
            ensure_ascii=False, indent=1) + "\n")


def merge_text(children: list[dict]) -> list[dict]:
    out: list[dict] = []
    for child in children:
        if child.get("kind") == "text" and out and out[-1].get("kind") == "text" and set(out[-1]) == {"kind", "text"}:
            out[-1] = text(out[-1]["text"] + child["text"])
        else:
            out.append(child)
    return out


def derive(language: str, document: fitz.Document, art: dict[str, str]) -> Derivation:
    work = Derivation(language, document, art)
    work.nest_chapters()
    work.preface_badge()
    work.signal_words()
    work.regular_state_words()
    work.fcc_heading()
    work.safety_bands()
    work.danger_callout()
    work.safety_lockups()
    work.solar_caution()
    work.numbered_callouts()
    work.numbered_paragraphs()
    work.line_item_callouts("ess", 24)
    work.bullet_callouts()
    work.inline_callout_labels()
    work.chapter_title_tail()
    work.hidden_glyphs()
    work.label_paragraph_callouts()
    work.lcd_screen()
    work.lcd_icons()
    work.troubleshooting()
    work.warranty()
    work.sold_separately()
    work.model_bands()
    work.plain_titles()
    work.spec_hazard_rows()
    work.spec_values()
    work.trademark_notes()
    work.merge_soft_wraps()
    work.folio_continuations()
    work.print_paragraph_breaks()
    work.bulleted_subheads()
    work.prose_pills()
    work.ingestion_notes()
    work.print_emphasis()
    work.merge_adjacent_lists()
    work.contact_card()
    work.overview_frames()
    work.locale_art()
    work.refresh_reference_figures()
    return work

def derive_art(document: fitz.Document) -> tuple[dict[str, str], list[dict]]:
    """Regenerate the art this edition adds or reframes, and record each decision."""
    assets = HERE / "assets"
    shutil.rmtree(assets)
    shutil.copytree(APPROVED / "assets", assets)
    digests, decisions = {}, []
    for name, source in SHARED_ART.items():
        data = (REPO / source).read_bytes()
        (assets / name).write_bytes(data)
        digests[name] = sha256(data)
        decisions.append({
            "slot": name, "searched": ["docs/renderers/web/assets/shared/symbols", "docs/templates/word_template/common_assets/symbols"],
            "candidate": source, "decision": "reuse byte-identical", "new_extraction_reason": None,
            "identity_check": ("Filled dark triangle with white exclamation: print p4 risk banner and DANGER lockup."
                               if "dark" in name else
                               "White triangle with dark exclamation: print p4 WARNING lockup on its dark panel."),
            "final_path": "assets/" + name, "sha256": digests[name], "background_policy": "preserve SVG transparency",
        })
    glyph = native_symbol_svg(document[INGESTION_GLYPH["page"] - 1], INGESTION_GLYPH["drawings"], INGESTION_GLYPH["bbox"])
    (assets / INGESTION_ART).write_bytes(glyph)
    digests[INGESTION_ART] = sha256(glyph)
    decisions.append({
        "slot": INGESTION_ART, "searched": ["docs/renderers/web/assets/shared/symbols", "docs/templates/word_template/common_assets/symbols",
                                            "data/manual_sources/JHP-3600C", "data/manual_sources/JHP-3000D"],
        "candidate": None, "decision": "native-source-glyph",
        "new_extraction_reason": "No coin-battery ingestion hazard glyph exists in the shared libraries.",
        "identity_check": "Warning triangle above a button cell, left of the INGESTION HAZARD note (print p23/p25/p26; same drawing in FR/ES).",
        "final_path": "assets/" + INGESTION_ART, "source_page": INGESTION_GLYPH["page"],
        "drawing_indices": INGESTION_GLYPH["drawings"], "bbox": INGESTION_GLYPH["bbox"],
        "sha256": digests[INGESTION_ART], "background_policy": "standalone-transparent",
    })
    for name, (indices, bbox, identity) in CONTACT_ART.items():
        glyph = native_symbol_svg(document[75], indices, bbox)
        (assets / name).write_bytes(glyph)
        digests[name] = sha256(glyph)
        decisions.append({
            "slot": name, "searched": ["docs/renderers/web/assets/shared/symbols",
                                       "docs/templates/word_template/common_assets/symbols"],
            "candidate": None, "decision": "native-source-glyph",
            "new_extraction_reason": "No matching contact glyph or this manual's QR code exists in the shared libraries.",
            "identity_check": identity, "final_path": "assets/" + name, "source_page": 76,
            "drawing_indices": indices, "bbox": bbox, "sha256": digests[name],
            "background_policy": "standalone-transparent",
        })
    figures = {f["id"]: f for f in json.loads((APPROVED / "source/figures.json").read_text())}
    for identity, languages in LOCALE_ART.items():
        for language in languages:
            frame = None
            if identity in FRAMES:
                frame = [figures[identity]["bbox"][0], FRAMES[identity][2],
                         figures[identity]["bbox"][2], FRAMES[identity][3]]
            data, removed, number = locale_variant(document, figures[identity], language, frame)
            name = f"{identity}-{language}.svg"
            (assets / name).write_bytes(data)
            digests[name] = sha256(data)
            decisions.append({
                "slot": f"{identity}-{language}", "searched": [f"assets/{identity}.svg"],
                "candidate": None, "decision": "acquire native locale variant after artwork comparison",
                "identity_check": ("Locale print geometry differs from English (device scale, zoom circles, "
                                   "bracket and caption plate positions"
                                   + (", localized App screens" if identity == "sts-charge" else "")
                                   + (", plug cable restored" if identity == "car" else "") + ")."),
                "new_extraction_reason": "The shared English panel cannot carry the locale's print label geometry.",
                "source_page": number,
                "source_bbox": figures[identity].get("locale_boxes", {}).get(language, figures[identity]["bbox"]),
                "removed_caption_indices": removed, "final_path": "assets/" + name, "sha256": digests[name],
                "background_policy": "complete panel; caption plates and panel stroke drawn by CSS",
            })
    for figure, (old_top, old_bottom, new_top, new_bottom) in FRAMES.items():
        path = assets / (figure + ".svg")
        data = path.read_text()
        old = f'height="{old_bottom - old_top:.1f}" viewBox="27.0 {old_top:.1f} 317.0 {old_bottom - old_top:.1f}"'
        new = f'height="{new_bottom - new_top:.1f}" viewBox="27.0 {new_top:.1f} 317.0 {new_bottom - new_top:.1f}"'
        if data.count(old) != 1:
            raise SystemExit(f"approved {figure} frame changed")
        path.write_text(data.replace(old, new))
        digests[figure + ".svg"] = sha256(path.read_bytes())
    return digests, decisions


def write_records(digests: dict[str, str], added: list[dict]) -> None:
    figures = json.loads((APPROVED / "source/figures.json").read_text())
    for figure in figures:
        if figure["id"] in FRAMES:
            figure["bbox"][1], figure["bbox"][3] = FRAMES[figure["id"]][2:]
        for language in LOCALE_ART.get(figure["id"], ()):
            figure.setdefault("locale_art", {})[language] = f"{figure['id']}-{language}.svg"
    (HERE / "source/figures.json").write_text(json.dumps(figures, ensure_ascii=False, indent=2) + "\n")
    decisions = json.loads((APPROVED / "source/asset_decisions.json").read_text())
    for decision in decisions:
        if decision.get("slot") in FRAMES:
            old_top, old_bottom, new_top, new_bottom = FRAMES[decision["slot"]]
            decision["bbox"][1], decision["bbox"][3] = new_top, new_bottom
            decision["sha256"] = digests[decision["slot"] + ".svg"]
            decision["web_layout_reframe"] = (
                f"Frame grown from y {old_top:g}-{old_bottom:g} to {new_top:g}-{new_bottom:g} so the "
                "approved paths are whole (handle-button inset, wheels, panel edge); only the SVG "
                "viewBox changed.")
    replaced = {d["slot"] for d in added}
    for decision in decisions:
        if decision.get("slot") in replaced:
            decision["superseded_by_web_layout"] = "re-acquired with the panel's full drawing set; see the later record"
    (HERE / "source/asset_decisions.json").write_text(
        json.dumps(decisions + added, ensure_ascii=False, indent=2) + "\n")

def main() -> None:
    pdf = HERE / PDF_NAME
    if pdf.read_bytes() != (APPROVED / PDF_NAME).read_bytes():
        raise SystemExit("authoritative PDF differs from the approved package")
    with fitz.open(pdf) as document:
        digests, added = derive_art(document)
        write_records(digests, added)
        for language in LANGUAGES:
            work = derive(language, document, digests)
            work.write()
            print(json.dumps({"language": language, "changes": len(work.log),
                              "copy_restorations": len(work.restorations)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
