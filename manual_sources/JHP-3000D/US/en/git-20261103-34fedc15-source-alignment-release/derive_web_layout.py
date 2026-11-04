"""Derive the JHP-3000D/US Web-layout edition from the published package.

Run from the repository root:

    python data/manual_sources/JHP-3000D/US/git-20261013-cebe4aab-web-layout/derive_web_layout.py

The published package ``../git-20261009-cebe4aab`` stays immutable. Every derived
file here is regenerated from it on each run, so a second run leaves the tree
unchanged:

* ``source/<language>/content.json``: rebuilt with the shared flow and
  ComponentSpec builders; each edit is listed in ``source/<language>/web_layout.json``;
* ``source/figures.json`` and ``source/asset_decisions.json``: the published records
  plus the art decisions below;
* ``assets/``: the published art plus two shared warning triangles (byte copies),
  the print's own vertical-switch buttons, contact glyphs, contact QR code and
  App steps 2.3-2.5.

Hand-written files are never touched: README.md, rebuild.py, the validators,
source/differences.md, source/approval.json, source/presentation.css and
source/refresh_manifest.py. The other source/ records (coverage, LCD, native
blocks and exceptions) are the published intake's, copied unchanged.

Wording rule: visible copy keeps the published strings. The only copy edits restore
the authoritative PDF where the published intake disagreed with it; each one is
listed in web_layout.json under "copy_restorations". Print-source errors (text in
another language, typos) stay as printed.
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

from tools.asset_pipeline.native_svg import native_symbol_svg  # noqa: E402
from tools.component_specs.auto_resume import auto_resume_component_spec  # noqa: E402
from tools.component_specs.key_combinations import key_combinations_component_spec  # noqa: E402
from tools.component_specs.model import ComponentSpec  # noqa: E402
from tools.component_specs.spec_table import spec_table_component_spec  # noqa: E402
from tools.component_specs.reference_figure_adapters import web_reference_figure_projection  # noqa: E402
from tools.manual_ir.components import component_flow_node  # noqa: E402
from tools.manual_ir.flow import flow_nodes_to_html, html_to_flow_nodes  # noqa: E402
from tools.web.callout_ir import render_callout_component  # noqa: E402
from tools.web.composite_presentation import WebCompositeContext  # noqa: E402
from tools.web.embedded_components import _carrier_html  # noqa: E402
from tools.web.presentation import _transform_reference_figure  # noqa: E402
from tools.web.reference_figure_component import _component_contract, _validate_carrier  # noqa: E402
from tools.web.frozen_ai_flow import callout, cell, node, paragraph, table, text  # noqa: E402

APPROVED = HERE.parent / "git-20261009-cebe4aab"
LANGUAGES = ("en", "fr", "es")
PDF_NAME = "Jackery HomePower 3000 User Manual.pdf"
FIRST_PAGE = {"en": 4, "fr": 22, "es": 40}
PRINT_PAGES = 18
BACK_COVER = 58
FLOW = "manual-flow/v2"

LIGATURES = {"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl"}
BOLD_FONTS = ("Bold", "SemiBold", "Heavy")
BULLETS = "·•"
QUOTES = "\"“”«»"

# Shared art reused byte-identically (searched before any extraction, per the Web
# artwork reuse order); the triangle glyphs carry the print's warning lockups.
SHARED_ART = {
    "warning_triangle_dark.svg": "docs/templates/word_template/common_assets/symbols/warning_triangle_dark.svg",
    "warning_triangle_white.svg": "docs/templates/word_template/common_assets/symbols/warning_triangle_white.svg",
}
# Print p13 shortcut table (same drawing on FR p31 and ES p49): round button faces with
# a vertical switch and the marking below it. Every shared button SVG draws a
# horizontal switch, so none matches; values are (glyph bbox, marking, path count).
BUTTON_ART = {
    "button-power-p13.svg": ([49.8, 63.6, 73.4, 87.2], "POWER", 8),
    "button-ac-p13.svg": ([110.7, 63.6, 134.3, 87.2], "AC", 5),
    "button-dc-usb-p13.svg": ([110.7, 102.9, 134.3, 126.5], "DC/USB", 9),
}
# The published table referenced these names; assets/power.svg is the POWER ON/OFF panel.
BUTTON_FOR = {"assets/power.svg": "button-power-p13.svg", "assets/ac.svg": "button-ac-p13.svg",
              "assets/dc_usb.svg": "button-dc-usb-p13.svg"}
# Back cover (p58) contact glyphs: native vectors, shared by all locales.
CONTACT_ART = {
    "contact-phone.svg": ([2, 3], [36.1, 469.2, 53.9, 487.0], "Telephone glyph left of the phone number."),
    "contact-mail.svg": ([4, 5], [208.9, 469.8, 218.0, 476.0], "Envelope glyph left of the e-mail address."),
    "contact-web.svg": ([6, 7, 8], [208.4, 479.2, 219.0, 487.7], "Globe glyph left of the website."),
}
CONTACT_QR = "contact-qr.png"
# App steps 2.3-2.5 (EN p21; FR p39 and ES p57 print the same images): the published
# package reused JHP-3600C screens, which show an Explorer 1000 and a 1000 W input.
APP_STEPS = "app-steps-2-3-to-2-5.png"
APP_STEPS_ID = "app_connect_result_steps"


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


def bare(item: dict) -> dict:
    return {k: v for k, v in item.items() if k != "schema_version"}


def markup(fragment: str) -> list[dict]:
    """Flow nodes of a published HTML fragment, without root schema stamps."""
    return [bare(item) for item in html_to_flow_nodes(fragment)]


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


def merge_text(children: list[dict]) -> list[dict]:
    out: list[dict] = []
    for child in children:
        if child.get("kind") == "text" and out and out[-1].get("kind") == "text" and set(out[-1]) == {"kind", "text"}:
            out[-1] = text(out[-1]["text"] + child["text"])
        else:
            out.append(child)
    return out


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
    """Assign the published words to their print lines; None when a word spans two lines."""
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
        chars, flags, spans = [], [], []
        for page in pages:
            for block in document[page - 1].get_text("dict")["blocks"]:
                for line in block.get("lines", []):
                    for span_ in line["spans"]:
                        value = key(span_["text"])
                        bold = any(f in span_["font"] for f in BOLD_FONTS)
                        chars.append(value)
                        flags.extend([bold] * len(value))
                        if span_["text"].strip():
                            spans.append((squash(span_["text"]), bold))
        self.stream = "".join(chars)
        self.flags = flags
        self.spans = spans

    def regular_quote(self, quote: str, word: str, leading: bool) -> bool:
        """The print sets ``quote`` in a regular span against the bold ``word`` it encloses."""
        for (first, first_bold), (second, second_bold) in zip(self.spans, self.spans[1:], strict=False):
            if leading and not first_bold and second_bold and first.endswith(quote) and second.startswith(word):
                return True
            if not leading and first_bold and not second_bold and first.endswith(word) and second.startswith(quote):
                return True
        return False

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


def spec_carrier(spec: ComponentSpec) -> list[dict]:
    """The published intake's spec carrier: one titled table, one row per value."""
    slot = lambda role: spec.slot(role).content  # noqa: E731
    title = node("heading", [node("inline_group", [text(slot("section_title"))],
                                  presentation=attrs("hb-spec-section-text"))], level=2,
                 presentation=attrs("hb-spec-section hb-spec-group"))
    rows = [[cell(r["label"] if i == 0 else "", header=True), cell(v["text"])]
            for r in slot("rows") for i, v in enumerate(r["values"])]
    return [title, table(rows)]


STATE_LABEL = re.compile(r"^[A-ZÀ-Ý][^\s:]{0,13}\s?:")


def inline_chars(value: str) -> list[tuple[str, bool]]:
    """Characters of an inline HTML value (text and <strong> only) with their weight."""
    chars: list[tuple[str, bool]] = []
    bold = False
    for token in re.split(r"(</?strong>)", value):
        if token in ("<strong>", "</strong>"):
            bold = token == "<strong>"
            continue
        if "<" in token:
            raise ValueError(f"unexpected markup in {value!r}")
        chars.extend((c, bold) for c in html.unescape(token))
    return chars


def part_starts(plain: str, parts: list[str]) -> list[int]:
    """Character offsets in ``plain`` where each print part begins."""
    words = list(re.finditer(r"\S+", plain))
    if [w.group(0) for w in words] != " ".join(parts).split():
        raise ValueError(f"print parts disagree with {plain!r}")
    starts, count = [], 0
    for part in parts:
        starts.append(words[count].start())
        count += len(part.split())
    return starts


def html_with_breaks(chars: list[tuple[str, bool]], starts: set[int]) -> str:
    """Inline HTML of weighted characters with <br> before each offset in ``starts``."""
    out: list[str] = []
    bold = False
    for index, (c, flag) in enumerate(chars):
        if index in starts:
            while out and out[-1] == " ":
                out.pop()
            if bold:
                out.append("</strong>")
                bold = False
            out.append("<br>")
        if flag != bold:
            out.append("<strong>" if flag else "</strong>")
            bold = flag
        out.append(html.escape(c, quote=False))
    if bold:
        out.append("</strong>")
    return "".join(out)


class Derivation:
    def __init__(self, language: str, document: fitz.Document, art: dict[str, str]):
        self.language = language
        self.art = art
        self.pdf = PdfLines(document)
        first = FIRST_PAGE[language]
        self.locale_pages = [2, *range(first, first + PRINT_PAGES), BACK_COVER]
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
        """Every callout of a chapter, nested ones included, as (container, index, node)."""
        for container, index, item in list(walk(self.nodes(chapter))):
            if component_id(item) == "HB-CALLOUT-STRIP":
                yield container, index, item

    # ---- structure -------------------------------------------------------
    def fcc_heading(self) -> None:
        """Print p6 has no FCC title, only the FC mark: the panel continues MEANING OF SYMBOLS."""
        items = self.nodes("fcc")
        heading = items[0]
        if heading.get("kind") != "heading" or heading.get("anchor") != "native-fcc" or len(items) != 2:
            raise ValueError(f"{self.language}: unexpected FCC chapter")
        items[:] = [flow_root(group([bare(items[1])], "native-fcc-panel", anchor="native-fcc"))]
        self.note("fcc", "unprinted-title-removed", title=text_of(heading), follows="symbols")
        self.restorations.append({"chapter": "fcc", "kind": "unprinted-title", "approved": text_of(heading), "pdf": None})

    def page_text(self, page: int | None) -> PdfText:
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
        if start and context[start - 1] == "-":
            return False
        return None

    def regular_state_words(self) -> None:
        """Drop bold the intake gave state words (on/off, encendido…) that print sets regular."""
        removed = []

        def fix_flow(item, chapter: str, page: int | None = None) -> None:
            if isinstance(item, list):
                for child in item:
                    fix_flow(child, chapter, page)
                return
            if not isinstance(item, dict):
                return
            if item.get("kind") == "component":
                # Figure labels repeat across pages (overview vs App diagram): read the weight
                # on the component's own print page. FR/ES figure refs keep the English page
                # number (<= 21); their callout refs already name the locale page.
                found = re.search(r"page-(\d+)/", item["component_spec"]["source_ref"])
                own = int(found.group(1)) if found else None
                if own is not None and own < FIRST_PAGE["en"] + PRINT_PAGES:
                    own = page_of(self.language, own)
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

    def _rebuild_callout(self, label: str, body: list[dict], variant: str, source_ref: str,
                         root: bool = True) -> dict:
        built = callout(label, body, variant=variant, language=self.language, source_ref=source_ref)
        return flow_root(built) if root else built

    @staticmethod
    def _carrier_body(item: dict) -> list[dict]:
        for _, _, inner in walk(item.get("carrier_flow", [])):
            if inner.get("kind") == "table_cell" and "manual-callout-body" in css_class(inner):
                return inner.get("children", [])
        return []

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

    def signal_lockups(self) -> None:
        """p5 WARNING and DANGER print as outlined triangle lockups with bold bodies; '※' starts a line."""
        items = self.nodes("safety")
        lead = next(index for _, index, _ in self.callouts("safety"))
        rebuilt = 0
        for container, index, item in list(self.callouts("safety")):
            if container is not items or index == lead:
                continue
            label, body, variant, ref = self._callout_parts(item)
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
            plain = self._rebuild_callout(label, [node("paragraph", children)], variant, ref)
            items[index] = self._lockup(plain, "warning_triangle_dark.svg", "native-lockup-outlined")
            self.note("safety", "signal-lockup", label=label, bold_body=bold, print_lines=len(parts))
            rebuilt += 1
        if rebuilt != 2:
            raise ValueError(f"{self.language}: expected the two p5 signal callouts, found {rebuilt}")

    def callout_labels(self) -> None:
        """A label the intake padded with words of the next paragraph ('The product can … CAUTION')."""
        labels = {self._callout_parts(item)[0] for chapter in self.content["chapters"]
                  for _, _, item in self.callouts(chapter["id"])}
        clean = {label for label in labels if len(label.split()) == 1}
        for chapter in self.content["chapters"]:
            for container, index, item in list(self.callouts(chapter["id"])):
                label, _, variant, ref = self._callout_parts(item)
                tail = next((c for c in clean if label != c and label.endswith(" " + c)), None)
                if tail is None:
                    continue
                stray = label[: -len(tail) - 1]
                neighbours = key(" ".join(text_of(other) for other in container if other is not item))
                if not all(key(word) in neighbours for word in stray.split() if key(word)):
                    raise ValueError(f"{self.language}: label words not found beside the callout: {stray!r}")
                if not self.pdf.styled(self.locale_pages, tail):
                    raise ValueError(f"{self.language}: callout label {tail!r} is not a print line")
                container[index] = self._rebuild_callout(tail, copy.deepcopy(self._carrier_body(item)), variant, ref,
                                                         root="schema_version" in item)
                self.restorations.append({"chapter": chapter["id"], "kind": "callout-label-stray-words",
                                          "approved": label, "pdf": tail})
                self.note(chapter["id"], "callout-label-restored", label=tail, removed=stray)

    # ---- LCD -----------------------------------------------------------------
    def lcd_icons(self) -> None:
        """Circled numbers, one number cell per printed entry, one description line per print line."""
        items = self.nodes("lcd")
        index = next(i for i, item in enumerate(items) if component_id(item) == "HB-TABLE-LCD-ICON")
        spec = copy.deepcopy(items[index]["component_spec"])
        rows = next(slot for slot in spec["slots"] if slot["role"] == "rows")["content"]
        pages = self.pages(8, 9)

        def described(line: dict) -> bool:  # the description column
            return line["bbox"][0] > 130

        right = max(line["bbox"][2] for page in pages for line in self.pdf.lines(page) if described(line))
        breaks, missing, weights = 0, [], []
        for row in rows:
            row["number_html"] = f'<span class="native-lcd-number">{row["number_text"]}</span>'
            value = squash(row["description_text"])
            found = self.pdf.run(pages, value, keep=described)
            words = words_by_line(value, found[1]) if found else None
            if not words:
                missing.append(row["number_text"])
                continue
            run = found[1]
            parts, current = [], []
            for i, (line, chunk) in enumerate(zip(run, words, strict=True)):
                current.extend(chunk)
                last = i == len(run) - 1
                following = "" if last else run[i + 1]["text"].strip()
                # A state or note label ('Off:', 'Éteint :') always starts its own print line.
                if last or (re.search(r"[.!?:;)]$", line["text"]) and following[:1].isupper()
                            and (STATE_LABEL.match(following) or hard_break(line, run[i + 1], right))):
                    parts.append(" ".join(current))
                    current = []
            chars = inline_chars(row["description_html"])
            plain = "".join(c for c, _ in chars)
            starts = part_starts(plain, parts)
            # Each line label takes the print weight (EN prints 'Note:' bold, FR/ES states regular).
            for start in starts:
                label = STATE_LABEL.match(plain[start:])
                if not label:
                    continue
                end = start + len(label.group(0).rstrip(": "))
                weight = self._print_weight(plain, start, end, found[0])
                if weight is not None and any(flag != weight for _, flag in chars[start:end]):
                    chars[start:end] = [(c, weight) for c, _ in chars[start:end]]
                    weights.append({"row": row["number_text"], "label": plain[start:end], "bold": weight})
            if len(parts) > 1 or weights and weights[-1]["row"] == row["number_text"]:
                row["description_html"] = html_with_breaks(chars, set(starts[1:]))
                breaks += len(parts) - 1
        if missing:
            raise ValueError(f"{self.language}: LCD descriptions not found in print: {missing}")
        if weights:
            self.note("lcd", "lcd-label-print-weight", labels=weights)
        spec["metadata"] = {**spec.get("metadata", {}), "number_cell_layout": "span-adjacent-equal"}
        items[index] = component_flow_node(ComponentSpec.from_dict(spec), root=True)
        self.note("lcd", "lcd-icon-print-structure", description_line_breaks=breaks,
                  shared_numbers=sorted({r["number_text"] for r in rows
                                         if sum(o["number_text"] == r["number_text"] for o in rows) > 1}))

    # ---- operation tables -----------------------------------------------------
    def _table_rows(self, item: dict) -> list[list[str]]:
        body = next(inner for _, _, inner in walk([item]) if inner.get("kind") == "table_body")
        return [[squash(text_of(c)) for c in row["children"]] for row in body["children"]]

    def auto_resume(self) -> None:
        """The resume table is the shared auto-resume component: its middle condition spans two rows.

        FR/ES intake split that condition's second print line into the next row; the
        print cell geometry decides which lines form one condition.
        """
        items = self.nodes("operations")
        index = next(i for i, item in enumerate(items)
                     if item.get("kind") == "group" and "table-wrapper" in css_class(item)
                     and len(self._table_rows(item)[0]) == 2)
        header, *rows = self._table_rows(items[index])
        if len(rows) != 4 or any(len(row) != 2 for row in rows):
            raise ValueError(f"{self.language}: unexpected resume table {rows}")
        page = page_of(self.language, 11)
        right = [row[1] for row in rows]
        approved = [row[0] for row in rows]
        # Full-width rules bound the three left cells; the middle right-column rule stops
        # at the column edge, so the second left condition spans two right rows.
        head = self.pdf.styled([page], header[0])
        if head is None:
            raise ValueError(f"{self.language}: resume table header not printed")
        rules = [d["rect"] for d in self.pdf.document[page - 1].get_drawings()
                 if d["rect"].height < 1.2 and d["rect"].width > 30
                 and head["bbox"][1] < d["rect"].y0 < head["bbox"][1] + 120]
        full = sorted({round(r.y0, 1) for r in rules if r.x0 < 40})
        column = min(r.x0 for r in rules if r.x0 >= 40)
        if len(full) != 3 or len(rules) != 4:
            raise ValueError(f"{self.language}: resume table rules changed: {rules}")
        edges = [*full, full[-1] + 16]
        left = []
        for top, bottom in zip(edges, edges[1:], strict=False):
            lines = sorted((line for line in self.pdf.lines(page)
                            if line["bbox"][0] < column - 5 and top < line["bbox"][1] < bottom),
                           key=lambda line: line["bbox"][1])
            left.append(squash(" ".join(line["text"] for line in lines)))
        if sorted(key(w) for w in " ".join(left).split()) != sorted(key(w) for w in " ".join(approved).split()):
            raise ValueError(f"{self.language}: print resume cells {left} do not reuse {approved}")
        for value in right:
            if not self.pdf.run([page], value):
                raise ValueError(f"{self.language}: resume condition is not one print cell: {value!r}")
        spec = auto_resume_component_spec(headers=header, conditions=[left, right],
                                          source_ref=f"native-pdf/page-{page}/auto-resume", language=self.language)
        items[index] = component_flow_node(spec, root=True)
        if len([value for value in approved if value]) != 3:
            self.restorations.append({"chapter": "operations", "kind": "table-row-boundary",
                                      "approved": approved, "pdf": [left[0], left[1], "", left[2]]})
        self.note("operations", "shared-auto-resume", page=page, conditions=[len(left), len(right)])

    def key_combinations(self) -> None:
        """The shortcut table is the shared key-combination component (as JHP-3600C/JHP-5000C).

        Print p13 sets two vertical-switch buttons with a '+' between them, each name
        under its button, and the hold time beside a clock. The published intake read
        the two names right-to-left in rows 2 and 3 and referenced the POWER ON/OFF
        panel as the POWER button.
        """
        items = self.nodes("operations")
        index = next(i for i, item in enumerate(items)
                     if item.get("kind") == "group" and any(
                         inner.get("kind") == "image" and "native-button-icon" in css_class(inner)
                         for _, _, inner in walk([item])))
        body = next(inner for _, _, inner in walk([items[index]]) if inner.get("kind") == "table_body")
        header, *rows = body["children"]
        headers = [squash(text_of(c)) for c in header["children"]]
        if len(rows) != 3 or len(headers) != 3:
            raise ValueError(f"{self.language}: unexpected shortcut table")
        page = page_of(self.language, 13)
        document_page = self.pdf.document[page - 1]
        drawings = document_page.get_drawings()
        rules = sorted({round(d["rect"].y0, 1) for d in drawings
                        if d["rect"].height < 1 and d["rect"].width > 250 and d["rect"].y0 < 220})
        faces = sorted((d["rect"] for d in drawings
                        if d["type"] == "fs" and 22 < d["rect"].width < 25 and 22 < d["rect"].height < 25
                        and d["rect"].y0 < 220), key=lambda r: (round(r.y0), r.x0))
        if len(rules) != 3 or len(faces) != 6:
            raise ValueError(f"{self.language}: shortcut table geometry changed: {rules} {len(faces)}")
        edges = [*rules, rules[-1] + (rules[-1] - rules[-2])]
        labels_by_row, out_rows, carrier_rows, reordered = [], [], [], []
        durations = []
        for r, row in enumerate(rows):
            top, bottom = edges[r], edges[r + 1]
            button_cell, operation_cell, function_cell = row["children"]
            images = [inner["source"] for _, _, inner in walk([button_cell]) if inner.get("kind") == "image"]
            centres = [(rect.x0 + rect.x1) / 2 for rect in faces if top < rect.y0 < bottom]
            if len(images) != 2 or len(centres) != 2:
                raise ValueError(f"{self.language}: shortcut row {r + 1} needs two buttons")
            names: list[list[str]] = [[], []]
            for line in sorted(self.pdf.lines(page), key=lambda line: line["bbox"][1]):
                x0, y0, x1, _ = line["bbox"]
                # Button names print at 4.5-5 pt under their buttons; operation copy is 6 pt.
                if not (top < y0 < bottom and x0 < 150 and line["size"] < 5.5):
                    continue
                middle = (x0 + x1) / 2
                names[min((0, 1), key=lambda k: abs(centres[k] - middle))].append(line["text"])
            pair = [squash(" ".join(lines)) for lines in names]
            approved = squash(text_of(button_cell))
            if sorted(key(w) for w in " ".join(pair).split()) != sorted(key(w) for w in approved.split()):
                raise ValueError(f"{self.language}: shortcut names {pair} do not reuse {approved!r}")
            if " ".join(pair) != approved:
                reordered.append({"row": r + 1, "approved": approved, "pdf": pair})
            operation, function = squash(text_of(operation_cell)), squash(text_of(function_cell))
            seconds = re.search(r"(\d+)\s*(?:s\b|sec|seg)", operation)
            if not seconds:
                raise ValueError(f"{self.language}: hold time not found in {operation!r}")
            duration = seconds.group(1) + "s"
            durations.append(duration)

            def button(source: str, label: str) -> dict:
                return group([node("image", source="assets/" + BUTTON_FOR[source], alt=""),
                              node("paragraph", [text(label)])], "hb-key-button")

            pair_node = group([button(images[0], pair[0]),
                               node("inline_group", [text(" + ")], presentation=attrs("hb-key-button-plus")),
                               button(images[1], pair[1])], "hb-key-button-pair")
            clock = node("inline_group", [text(duration)], presentation={
                "html": {"attributes": {"class": "hb-key-duration", "data-duration-icon": "clock"}}})
            carrier_rows.append(node("table_row", [
                node("table_cell", [pair_node], header=False),
                node("table_cell", [clock, paragraph(operation)], header=False),
                node("table_cell", [text(function)], header=False),
            ]))
            out_rows.append([f"{pair[0]} + {pair[1]}", f"{duration} {operation}", function])
            labels_by_row.append(pair)
        if durations != ["3s", "3s", "1s"]:
            raise ValueError(f"{self.language}: print hold times are 3s/3s/1s, read {durations}")
        carrier = [node("table", [
            node("table_head", [node("table_row", [node("table_cell", [text(h)], header=True) for h in headers])]),
            node("table_body", carrier_rows),
        ], presentation=attrs("hb-key-combination-table"))]
        spec = key_combinations_component_spec(headers=headers, rows=out_rows,
                                               source_ref=f"native-pdf/page-{page}/key-combinations",
                                               language=self.language)
        items[index] = component_flow_node(spec, carrier_flow=carrier, root=True)
        if reordered:
            self.restorations.append({"chapter": "operations", "kind": "button-name-order",
                                      "approved": [r["approved"] for r in reordered],
                                      "pdf": [" | ".join(r["pdf"]) for r in reordered]})
        self.restorations.append({"chapter": "operations", "kind": "print-hold-times",
                                  "approved": None, "pdf": durations})
        self.note("operations", "shared-key-combinations", page=page, names=labels_by_row,
                  reordered_rows=[r["row"] for r in reordered], hold_times=durations)

    # ---- troubleshooting ----------------------------------------------------
    def fault_codes(self) -> None:
        """F0-F3 print one code per row beside one shared measure."""
        items = self.nodes("troubleshooting")
        index = next(i for i, item in enumerate(items) if component_id(item) == "HB-TABLE-TROUBLESHOOTING")
        spec = copy.deepcopy(items[index]["component_spec"])
        rows = next(slot for slot in spec["slots"] if slot["role"] == "rows")["content"]
        page = page_of(self.language, 17)
        changed = []
        for row in rows:
            codes = [c.strip() for c in row["code_text"].split("/")]
            if len(codes) < 2:
                continue
            for code in codes:
                line = self.pdf.styled([page], code)
                if line is None or not line["bold"]:
                    raise ValueError(f"{self.language}: fault code {code} is not its own print line")
            changed.append(row["code_text"])
            row["code_html"] = "<br>".join(html.escape(c) for c in codes)
            row["code_text"] = " ".join(codes)
        if changed:
            items[index] = component_flow_node(ComponentSpec.from_dict(spec), root=True)
            self.restorations.append({"chapter": "troubleshooting", "kind": "fault-code-separators",
                                      "approved": changed, "pdf": [c.replace(" / ", " | ") for c in changed]})
            self.note("troubleshooting", "stacked-fault-codes", codes=changed)

    # ---- warranty -------------------------------------------------------------
    def warranty(self) -> None:
        """Card paragraphs follow the print."""
        for index, item in enumerate(self.nodes("warranty")):
            identity = component_id(item)
            if identity not in ("HB-WARRANTY-SECTION", "HB-WARRANTY-YEARS"):
                continue
            spec = copy.deepcopy(item["component_spec"])
            changed = False
            for slot in spec["slots"]:
                if slot["role"] != "blocks":
                    continue
                blocks = []
                for block in slot["content"]:
                    parts = self._print_paragraphs(block["text"]) if block["kind"] == "paragraph" else [block]
                    if len(parts) > 1:
                        # The card appends block fragments as-is; only <p> keeps them apart.
                        changed = True
                        blocks.extend({"kind": "paragraph", "html": f"<p>{html.escape(p)}</p>", "text": p}
                                      for p in parts)
                    else:
                        blocks.append(block)
                slot["content"] = blocks
            if changed:
                self.nodes("warranty")[index] = component_flow_node(ComponentSpec.from_dict(spec), root=True)
                self.note("warranty", "warranty-print-paragraphs", component=identity)

    def _print_paragraphs(self, value: str) -> list[str]:
        found = self.pdf.run(self.locale_pages, value)
        if not found or len(found[1]) < 2:
            return [value]
        run = found[1]
        right = max(line["bbox"][2] for line in run)
        # Paragraph ends, as offsets into the key stream. Matching keys rather than
        # words keeps a word hyphenated across two print lines (FR p31 "d'alimenta-")
        # from hiding the breaks around it.
        ends, offset = [], 0
        for i, line in enumerate(run[:-1]):
            offset += len(key(line["text"]))
            if (re.search(r"[.!?:;。]$", line["text"]) and run[i + 1]["text"][:1].isupper()
                    and hard_break(line, run[i + 1], right)):
                ends.append(offset)
        words = squash(value).split()
        parts, current, taken = [], [], 0
        for index, word in enumerate(words):
            current.append(word)
            taken += len(key(word))
            # Bare punctuation (FR "à :") stays with the line that prints it.
            if ends and taken == ends[0] and (index + 1 == len(words) or key(words[index + 1])):
                parts.append(" ".join(current))
                current = []
                ends.pop(0)
        if ends:
            return [value]
        return [*parts, " ".join(current)] if current else parts

    # ---- headings and bands --------------------------------------------------
    def safety_bands(self) -> None:
        """Safety sub-titles printed white on a dark band; a bulletless bold title stays plain.

        The first sub-title is the outlined risk banner, rebuilt by safety_two_columns.
        """
        items = self.nodes("safety")
        pages = self.pages(4, 5)
        for index, item in enumerate(items):
            if (index < 2 or item.get("kind") != "heading" or item["level"] != 3
                    or not is_plain(item, "heading")):
                continue
            title = squash(text_of(item))
            line = self.pdf.styled(pages, title)
            if line is None:
                raise ValueError(f"{self.language}: safety title not printed: {title!r}")
            page = next(page for page in pages if line in self.pdf.lines(page))
            if line["white"]:
                item["children"] = [span(title, "native-band")]
                self.note("safety", "print-pill-title", title=title)
            elif line["bold"] and not line["bullet"] and not self.pdf.drawn_bullet(page, line):
                item["children"] = [span(title, "native-plain-title")]
                self.note("safety", "plain-title", title=title)

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
                        parts = self._value_lines(value["text"], self.pages(18))
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

    def _value_lines(self, value: str, pages: list[int]) -> list[str]:
        """Print spec cells never wrap here: each print line is one value (all locales checked).

        Only the specification page is read: the overview labels (p7) wrap the same values.
        """
        found = self.pdf.run(pages, value)
        if not found or len(found[1]) < 2:
            return [value]
        words = words_by_line(value, found[1])
        return [" ".join(chunk) for chunk in words] if words else [value]

    def trademark_notes(self) -> None:
        """Superscript '®' at its print positions in the USB trademark note."""
        for chapter in self.content["chapters"]:
            items = chapter["nodes"]
            for index, item in enumerate(items):
                if not is_plain(item) or "※" not in text_of(item):
                    continue
                value = squash(text_of(item))
                if not value.startswith("※"):
                    continue
                note_line = self._trademark_line(value)
                children = [node("superscript", [text("®")]) if piece == "®" else text(piece)
                            for piece in re.split(r"(®)", note_line) if piece]
                items[index] = flow_root(with_class(node("paragraph", children), "native-trademark"))
                if note_line != value:
                    self.restorations.append({"chapter": chapter["id"], "kind": "registered-mark-position",
                                              "approved": value, "pdf": note_line})
                self.note(chapter["id"], "trademark-note")

    def _trademark_line(self, approved: str) -> str:
        """Print text of the trademark note with each '®' after the word it follows."""
        wanted = key(approved)
        for page in self.locale_pages:
            document_page = self.pdf.document[page - 1]
            blocks = document_page.get_text("rawdict")["blocks"]
            for block in blocks:
                for line in block.get("lines", []):
                    chars = [c for s in line["spans"] for c in s["chars"]]
                    value = "".join(c["c"] for c in chars)
                    if "※" not in value or key(value) != wanted.replace("®", ""):
                        continue
                    marks = [c for b in blocks for ln in b.get("lines", []) for s in ln["spans"] for c in s["chars"]
                             if c["c"] == "®" and abs(c["bbox"][3] - line["bbox"][3]) < 6]
                    out = []
                    for c in chars:
                        out.append(c["c"])
                        if any(abs(m["bbox"][0] - c["bbox"][2]) < 1.2 for m in marks) and c["c"].strip():
                            out.append("®")
                    restored = squash("".join(out))
                    if restored.count("®") == approved.count("®"):
                        return restored
        return approved

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
                    if (a and b and not re.search(r"[.!?:;)。：]$", a) and re.match(r"[a-zà-ÿ0-9(]", b)
                            and self.pdf.run(self.locale_pages, a + " " + b)):
                        items[index] = flow_root(paragraph(a + " " + b))
                        del items[index + 1]
                        self.note(chapter["id"], "soft-wrap-joined", text=(a + " " + b)[:80], joined=b[:40])
                        continue
                index += 1

    def print_paragraph_breaks(self) -> None:
        """A sentence that ends a print line early, followed by a new sentence, is a new paragraph."""
        for chapter in self.content["chapters"]:
            if chapter["id"] == "contact":
                continue
            items = chapter["nodes"]
            index = 0
            while index < len(items):
                item = items[index]
                parts = self._print_paragraphs(squash(text_of(item))) if is_plain(item) else []
                if len(parts) > 1:
                    items[index:index + 1] = [flow_root(paragraph(p)) for p in parts]
                    self.note(chapter["id"], "print-paragraph-break", starts=[part[:40] for part in parts])
                    index += len(parts)
                else:
                    index += 1

    def print_emphasis(self) -> None:
        """Bold runs of the print (lead-ins, button names) inside plain paragraphs and list items."""
        changed = []
        for chapter in self.content["chapters"]:
            holders = [(item, None) for _, _, item in walk(chapter["nodes"])]
            # Callout bodies render from their carrier (p21 NOTE: "the device has been bound").
            holders += [(inner, item) for item, _ in holders if component_id(item) == "HB-CALLOUT-STRIP"
                        for _, _, inner in walk(item.get("carrier_flow", []))]
            touched = []
            for item, owner in holders:
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
                    if not flag:
                        out.append(text((" " if i else "") + value_ + (" " if i < len(runs) - 1 else "")))
                        continue
                    # Quotes around a bold run print regular (p20 "Icon Flashed", p21 NOTE).
                    lead = value_[0] if value_[0] in QUOTES and self.print_text.regular_quote(
                        value_[0], value_[1:].split()[0], leading=True) else ""
                    tail = value_[-1] if value_[-1] in QUOTES and self.print_text.regular_quote(
                        value_[-1], value_[:-1].split()[-1], leading=False) else ""
                    out += [text(lead)] if lead else []
                    out.append(strong(value_[len(lead):len(value_) - len(tail)]))
                    out += [text(tail)] if tail else []
                item["children"] = merge_text(out)
                if owner is not None and owner not in touched:
                    touched.append(owner)
                changed.append({"chapter": chapter["id"], "text": value[:70],
                                "bold": [squash(text_of(c)) for c in item["children"] if c["kind"] == "strong"][:3]})
            for owner in touched:
                self._sync_callout_body(owner)
        self.note("*", "print-emphasis", items=changed)

    @staticmethod
    def _sync_callout_body(component: dict) -> None:
        """The shared callout renderer reads the body slot as the carrier's text runs, one per line.

        Same convention as the reviewed JHP-3600A US edition (p23 NOTE).
        """
        carrier = BeautifulSoup(_carrier_html(component), "html.parser")
        body = carrier.find("tr").find_all(["th", "td"], recursive=False)[1]
        for slot in component["component_spec"]["slots"]:
            if slot["role"] == "body":
                slot["content"] = body.get_text("\n", strip=True)
        render_callout_component(ComponentSpec.from_dict(component["component_spec"]), _carrier_html(component))

    # ---- safety page -------------------------------------------------------
    def safety_two_columns(self) -> None:
        """Print p4 sets both safety lists in two columns, the WARNING lead heading the left one.

        The markup is the two-column safety section the published template manuals use
        (JE-1000E-SIL, JHP-5000C): the hb-safety-instruction risk banner,
        manual-two-col-table rows and the hb-safety-lead panel, all styled by the shared
        web_safety_components.css. Each item stays in the print column it starts in.
        """
        items = self.nodes("safety")
        flow = [component_id(item) or item.get("kind") for item in items]
        if flow[:7] != ["heading", "heading", "HB-CALLOUT-STRIP", "list", "heading", "heading", "list"]:
            raise ValueError(f"{self.language}: unexpected safety flow {flow}")
        page = page_of(self.language, 4)
        title = squash(text_of(items[1]))
        label, body = self._callout_parts(items[2])[:2]
        banner = markup(
            '<figure class="hb-symbol-signal-composition hb-safety-instruction"><table class="hb-symbol-signal-table">'
            '<colgroup><col style="width:7%"/><col style="width:93%"/></colgroup><tbody><tr>'
            '<td><img alt="" src="assets/warning_triangle_dark.svg" style="width:30px;height:auto" width="30"/></td>'
            f'<td><p><strong>{html.escape(title)}</strong></p></td></tr></tbody></table></figure>')
        lead = markup(
            '<figure class="hb-symbol-signal-composition hb-safety-lead"><table class="hb-symbol-signal-table">'
            '<colgroup><col style="width:20%"/><col style="width:80%"/></colgroup><tbody><tr>'
            '<td class="hb-symbol-signal-label-cell"><span class="hb-signal-badge"><img alt="" '
            'src="assets/warning_triangle_white.svg" style="width:48px;height:auto" width="48"/></span></td>'
            f'<td class="hb-symbol-signal-meaning-cell"><p><strong>{html.escape(label)}</strong></p>'
            f'<p><strong>{html.escape(squash(body))}</strong></p></td></tr></tbody></table></figure>')
        save = node("paragraph", [strong(squash(text_of(items[5])))])
        warning, warning_split = self._two_column_table(page, lead, items[3])
        operating, operating_split = self._two_column_table(page, [save], items[6])
        items[:7] = [items[0], flow_root(banner[0]), warning, items[4], operating]
        self.note("safety", "shared-safety-two-columns", page=page, label=label,
                  items_left_right=[warning_split, operating_split],
                  left_column_head=squash(text_of(save)))

    def _two_column_table(self, page: int, head: list[dict], listing: dict) -> tuple[dict, list[int]]:
        """One manual-two-col-table row: head + the left-column items | the right-column items."""
        middle = self.pdf.document[page - 1].rect.width / 2
        lines = self.pdf.lines(page)
        sides = []
        for item in listing["children"]:
            # The item's first print line: a bullet line whose words begin the item.
            value = key(text_of(item))
            starts = [line for line in lines if line["text"].lstrip()[:1] in BULLETS
                      and len(key(line["text"])) >= 10 and value.startswith(key(line["text"]))]
            if len(starts) != 1:
                raise ValueError(f"{self.language}: p{page} item not found once: {text_of(item)[:40]!r}")
            sides.append(starts[0]["bbox"][0] < middle)
        split = sides.index(False)
        if not all(sides[:split]) or any(sides[split:]):
            raise ValueError(f"{self.language}: p{page} list does not read left column, then right")
        listing_ = bare(listing)
        table_ = markup(
            '<table class="manual-two-col-table" style="width:100%; border-collapse:separate; '
            'border-spacing:12px 0; margin:0 0 16px 0;"><colgroup><col style="width: 50%"/>'
            '<col style="width: 50%"/></colgroup><tbody><tr>'
            '<td style="width: 50%; border: none; padding: 0 8px 0 0; vertical-align: top"></td>'
            '<td style="width: 50%; border: none; padding: 0 0 0 8px; vertical-align: top"></td>'
            '</tr></tbody></table>')[0]
        left, right = [inner for _, _, inner in walk([table_]) if inner.get("kind") == "table_cell"]
        left["children"] = [*(bare(n) for n in head), {**listing_, "children": listing["children"][:split]}]
        right["children"] = [{**listing_, "children": listing["children"][split:]}]
        return flow_root(table_), [split, len(sides) - split]

    # ---- back cover -----------------------------------------------------------
    def contact_card(self) -> None:
        """Back cover (p58): company, address and one contact panel with its QR code."""
        items = self.nodes("contact")
        if len(items) != 3 or items[0].get("anchor") != "native-contact":
            raise ValueError(f"{self.language}: unexpected contact chapter")
        company, address, lines = items
        value = squash(text_of(lines))
        email = re.search(r"\S+@\S+", value).group(0)
        web = re.search(r"www\.\S+", value).group(0)
        phone = re.search(r"([\d-]{10,})\s*(\([A-Z]{2}\))?", value)
        if squash(" ".join(filter(None, [email, web, phone.group(0)]))) != value:
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
        row = group([panel, group([node("image", source="assets/" + CONTACT_QR, alt="")], "native-contact-qr")],
                    "native-contact-row")
        items[:] = [flow_root(group([
            node("paragraph", [strong(squash(text_of(company)))], presentation=attrs("native-contact-company")),
            node("paragraph", [text(squash(text_of(address)))], presentation=attrs("native-contact-address")),
            row,
        ], "native-contact-card", anchor="native-contact"))]
        self.note("contact", "back-cover-card", company=squash(text_of(company)))

    def standby_bubble(self) -> None:
        """The p10 standby bubble keeps its title and note lines; its sentence wraps on the Web.

        The print breaks the middle sentence where its bubble ran out of width; a forced
        break there leaves one word on its own Web line. Words and order are unchanged.
        """
        figure = next(item for _, _, item in walk(self.nodes("operations"))
                      if component_id(item) == "HB-SPECIAL-REFERENCE-FIGURE"
                      and next(s["content"] for s in item["component_spec"]["slots"] if s["role"] == "reference_id") == "power")
        block = next(n for _, _, n in walk(figure["carrier_flow"]) if "line-block" in css_class(n))
        line = block["children"][3]["children"][0]["children"]
        joined = []
        for index in range(len(line) - 2, 0, -1):
            before, item, after = line[index - 1], line[index], line[index + 1]
            if (item.get("kind") == "line_break" and before.get("kind") == "text" and after.get("kind") == "text"
                    and re.search(r"\w$", before["text"]) and re.match(r"[a-zà-ÿ]", after["text"])):
                line[index - 1:index + 2] = [text(before["text"] + " " + after["text"])]
                joined.append(after["text"].split()[0])
        if len(joined) != 1:
            raise ValueError(f"{self.language}: expected one wrapped sentence in the standby bubble, found {joined}")
        self.note("operations", "standby-bubble-sentence-wrap", joined_before=joined)

    # ---- art -----------------------------------------------------------------
    def app_steps_art(self) -> None:
        """Steps 2.3-2.5 show this product's own print screens."""
        found = 0
        for chapter in self.content["chapters"]:
            for _, _, item in walk(chapter["nodes"]):
                if component_id(item) != "HB-SPECIAL-REFERENCE-FIGURE":
                    continue
                spec = item["component_spec"]
                identity = next(s["content"] for s in spec["slots"] if s["role"] == "reference_id")
                if identity != APP_STEPS_ID:
                    continue
                old = spec["assets"][0]["asset_ref"]
                spec["assets"][0]["asset_ref"] = "assets/" + APP_STEPS
                for _, _, inner in walk(item["carrier_flow"]):
                    if inner.get("kind") == "image" and inner.get("source") == old:
                        inner["source"] = "assets/" + APP_STEPS
                found += 1
                self.note(chapter["id"], "native-app-screens", figure=identity, art="assets/" + APP_STEPS, replaced=old)
        if found != 1:
            raise ValueError(f"{self.language}: App steps 2.3-2.5 figure not found once")

    def refresh_reference_figures(self) -> None:
        """Re-derive caption slots from the edited carrier lines and re-bind the fragment hash.

        The hash is the shared renderer's own (semantic carrier + caption text), computed
        exactly as the published intake did; figures whose captions did not change keep it.
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
                        value = flow_nodes_to_html([flow_root(copy.deepcopy(line["children"][0]))])
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
                                            composites=WebCompositeContext(None, "JHP-3000D", "US",
                                                                           spec.language, ValueError))
                digest = soup.figure["data-source-fragment-sha256"]
                if digest == data["metadata"].get("source_fragment_sha256"):
                    continue
                changed.append(data["source_ref"])
                data["metadata"]["source_fragment_sha256"] = digest
                fresh = component_flow_node(ComponentSpec.from_dict(data), carrier_flow=carrier)
                if "schema_version" in item:
                    fresh = flow_root(fresh)
                container[index] = fresh
        self.note("*", "reference-figures-rebound", figures=changed)

    # ---- writing -----------------------------------------------------------
    def write(self) -> None:
        target = HERE / f"source/{self.language}"
        target.mkdir(parents=True, exist_ok=True)
        (target / "content.json").write_text(json.dumps(self.content, ensure_ascii=False, indent=2) + "\n")
        (target / "web_layout.json").write_text(json.dumps(
            {"schema_version": "jhp3000d-web-layout-changes/v1", "language": self.language,
             "approved_source": f"../git-20261009-cebe4aab/source/{self.language}/content.json",
             "changes": self.log, "copy_restorations": self.restorations},
            ensure_ascii=False, indent=1) + "\n")


def derive(language: str, document: fitz.Document, art: dict[str, str]) -> Derivation:
    work = Derivation(language, document, art)
    work.regular_state_words()
    work.fcc_heading()
    work.safety_bands()
    work.signal_lockups()
    work.callout_labels()
    work.lcd_icons()
    work.auto_resume()
    work.key_combinations()
    work.fault_codes()
    work.warranty()
    work.spec_values()
    work.trademark_notes()
    work.merge_soft_wraps()
    work.print_paragraph_breaks()
    work.prose_pills()
    work.safety_two_columns()
    work.print_emphasis()
    work.contact_card()
    work.standby_bubble()
    work.app_steps_art()
    work.refresh_reference_figures()
    return work


def derive_art(document: fitz.Document) -> tuple[dict[str, str], list[dict]]:
    """Regenerate the art this edition adds, and record each decision."""
    assets = HERE / "assets"
    shutil.rmtree(assets)
    shutil.copytree(APPROVED / "assets", assets)
    digests, decisions = {}, []
    symbol_roots = ["docs/renderers/web/assets/shared/symbols", "docs/templates/word_template/common_assets/symbols"]
    for name, source in SHARED_ART.items():
        data = (REPO / source).read_bytes()
        (assets / name).write_bytes(data)
        digests[name] = sha256(data)
        decisions.append({
            "slot": name, "searched": symbol_roots, "candidate": source,
            "decision": "reuse byte-identical", "new_extraction_reason": None,
            "identity_check": ("Filled dark triangle with white exclamation: print p4 risk banner and the p5 "
                               "WARNING/DANGER lockups." if "dark" in name else
                               "White triangle with dark exclamation: print p4 WARNING lead on its dark panel."),
            "final_path": "assets/" + name, "sha256": digests[name], "background_policy": "preserve SVG transparency",
        })
    page = document[12]
    drawings = page.get_drawings()
    for name, (bbox, marking, count) in BUTTON_ART.items():
        inside = [i for i, d in enumerate(drawings) if fitz.Rect(bbox).contains(d["rect"])]
        if len(inside) != count:
            raise SystemExit(f"{name}: expected {count} paths inside {bbox}, found {len(inside)}")
        data = native_symbol_svg(page, inside, bbox)
        (assets / name).write_bytes(data)
        digests[name] = sha256(data)
        decisions.append({
            "slot": name, "searched": ["docs/renderers/web/assets/shared/buttons"],
            "candidate": None, "decision": "native-source-glyph",
            "rejected_shared_variants": ["power.svg", "power-bottom.svg", "ac.svg", "ac-bottom.svg",
                                         "dc_usb.svg", "usb-bottom.svg"],
            "new_extraction_reason": ("Every shared button draws a horizontal switch; print p13 draws a vertical "
                                      "switch with the marking below it, so no shared variant matches."),
            "identity_check": f"Round {marking} button face of the print shortcut table (EN p13; same drawing on FR p31 and ES p49).",
            "final_path": "assets/" + name, "source_page": 13, "drawing_indices": inside, "bbox": bbox,
            "sha256": digests[name], "background_policy": "standalone-transparent",
        })
    back = document[BACK_COVER - 1]
    for name, (indices, bbox, identity) in CONTACT_ART.items():
        data = native_symbol_svg(back, indices, bbox)
        (assets / name).write_bytes(data)
        digests[name] = sha256(data)
        decisions.append({
            "slot": name, "searched": symbol_roots, "candidate": None, "decision": "native-source-glyph",
            "new_extraction_reason": "No matching contact glyph exists in the shared libraries.",
            "identity_check": identity, "final_path": "assets/" + name, "source_page": BACK_COVER,
            "drawing_indices": indices, "bbox": bbox, "sha256": digests[name],
            "background_policy": "standalone-transparent",
        })
    images = back.get_image_info(xrefs=True)
    if len(images) != 1:
        raise SystemExit("back cover: expected one QR image")
    xref = images[0]["xref"]
    pixmap = fitz.Pixmap(document, xref)
    if pixmap.colorspace is None or pixmap.colorspace.n != 3:
        pixmap = fitz.Pixmap(fitz.csRGB, pixmap)
    smask = document.extract_image(xref).get("smask")
    if smask:
        pixmap = fitz.Pixmap(pixmap, fitz.Pixmap(document, smask))
    data = pixmap.tobytes("png")
    (assets / CONTACT_QR).write_bytes(data)
    digests[CONTACT_QR] = sha256(data)
    decisions.append({
        "slot": CONTACT_QR, "searched": ["assets/app_download_qr.png"], "candidate": None,
        "decision": "native-source-image",
        "new_extraction_reason": "The back-cover QR code is this manual's own; the App download QR is a different code.",
        "identity_check": "QR code in its own frame right of the p58 contact panel; embedded image decoded at its native 300 x 300 pixels with its mask.",
        "final_path": "assets/" + CONTACT_QR, "source_page": BACK_COVER, "bbox": [round(v, 2) for v in images[0]["bbox"]],
        "sha256": digests[CONTACT_QR], "background_policy": "transparent outside the code",
    })
    page = document[page_of("en", 21) - 1]
    phones = [i["bbox"] for i in page.get_image_info() if i["width"] >= 700]
    lines = PdfLines(document).lines(page_of("en", 21))
    labels = [line["bbox"] for line in lines if re.fullmatch(r"2\.[345]", line["text"])]
    if len(labels) != 3 or len(phones) < 3:
        raise SystemExit("App steps 2.3-2.5: phones or step numbers not found")
    bottom = max(b[3] for b in labels)
    # Stop above the next print line ('The above screenshots are for reference only.').
    following = min(line["bbox"][1] for line in lines if line["bbox"][1] > bottom)
    clip = fitz.Rect(min(b[0] for b in phones) - 4, min(b[1] for b in phones) - 4,
                     max(b[2] for b in phones) + 4, min(bottom + 4, following - 0.5))
    data = page.get_pixmap(dpi=600, clip=clip, alpha=False).tobytes("png")
    (assets / APP_STEPS).write_bytes(data)
    digests[APP_STEPS] = sha256(data)
    decisions.append({
        "slot": APP_STEPS, "searched": ["assets/app_connect_result_steps.png (JHP-3600C)"], "candidate": None,
        "decision": "native print render after artwork comparison",
        "new_extraction_reason": ("The reused JHP-3600C screens show an Explorer 1000 with a 1000 W input; print p21 "
                                  "shows this product (3000) with an 1800 W input."),
        "identity_check": ("Complete phone frames 2.3, 2.4 and 2.5 with their step numbers, as printed; FR p39 and "
                           "ES p57 print the same embedded images (UI in English)."),
        "final_path": "assets/" + APP_STEPS, "source_page": page_of("en", 21),
        "clip": [round(v, 2) for v in clip], "dpi": 600, "sha256": digests[APP_STEPS],
        "background_policy": "complete-app-frames-and-ui",
    })
    return digests, decisions


def write_records(digests: dict[str, str], added: list[dict]) -> None:
    shutil.copy2(APPROVED / "source/figures.json", HERE / "source/figures.json")
    decisions = json.loads((APPROVED / "source/asset_decisions.json").read_text())
    superseded = {
        "power.svg": "assets/power.svg is the POWER ON/OFF panel; the shortcut table now uses button-power-p13.svg",
        "ac.svg": "horizontal switch; the shortcut table now uses the print's button-ac-p13.svg",
        "dc_usb.svg": "horizontal switch; the shortcut table now uses the print's button-dc-usb-p13.svg",
        "app_connect_result_steps.png": f"other product's screens; App steps 2.3-2.5 now use {APP_STEPS}",
    }
    for decision in decisions:
        if decision.get("slot") in superseded:
            decision["superseded_by_web_layout"] = superseded[decision["slot"]]
    (HERE / "source/asset_decisions.json").write_text(
        json.dumps(decisions + added, ensure_ascii=False, indent=2) + "\n")


def main() -> None:
    pdf = HERE / PDF_NAME
    if pdf.read_bytes() != (APPROVED / PDF_NAME).read_bytes():
        raise SystemExit("authoritative PDF differs from the published package")
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
