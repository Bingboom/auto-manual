"""Source-local word selections and shared component constructors.

Selections use complete native words, never clipped textbox strings. Every
selection records its PDF page, rectangle, word IDs, raw text and normalization.
The coverage gate distinguishes live copy, embedded screenshot counters, and
printed folios. It refuses unclassified source words.
"""
from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path
import re
import unicodedata

import fitz
from bs4 import BeautifulSoup

from tools.component_specs.reference_figure import reference_figure_component_spec
from tools.component_specs.fcc import fcc_semantic_projection
from tools.component_specs.inbox_adapters import web_inbox_projection
from tools.component_specs.model import ComponentSpec
from tools.manual_ir.components import component_flow_node
from tools.manual_ir.flow import flow_nodes_to_html
from tools.web.composite_presentation import WebCompositeContext
from tools.web.reference_figure_component import _component_contract, _validate_carrier
from tools.component_specs.reference_figure_adapters import web_reference_figure_projection
from tools.web.presentation import _transform_reference_figure
from tools.web.frozen_ai_flow import cell, heading, node, paragraph, root, table, text

SOURCE = Path(__file__).resolve().parents[1]
PDF = SOURCE / "Jackery HomePower 3000 User Manual.pdf"
PDF_SHA = "cebe4aab0a65d5fb2c36bb1867cdb6497e2a6db5251c46c61a33a530b862cf27"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def normalize(raw):
    value = unicodedata.normalize("NFC", raw).replace("\x00", "").replace("\u00ad", "")
    for old, new in [("ﬁ", "fi"), ("ﬂ", "fl"), ("ﬀ", "ff"), ("ﬃ", "ffi"), ("ﬄ", "ffl")]:
        value = value.replace(old, new)
    # These are actual line-break splits, not spelling or source-copy corrections.
    value = re.sub(r"(?<=\w)-\n(?=\w)", "", value)
    return " ".join(value.split())


STATE = re.compile(
    r"\b(On|Off|Blink|on|off|Marche|Arrêt|Allumé|Éteint|Clignotant|"
    r"Encendido|Apagado|Parpadeo)(?=\s*[:/]|$)", re.I
)


def rich(value):
    value = STATE.sub(r"<strong>\1</strong>", html.escape(value))
    return re.sub(r"^(on|off|Marche|Arrêt|Encendido|Apagado)\b(?!</strong>)",
                  r"<strong>\1</strong>", value)


def pair(key, value):
    return {key + "_html": rich(value), key + "_text": value}


def attrs(value):
    return {"html": {"attributes": {"class": value}}}


def rich_nodes(value):
    parts = re.split(r"(<strong>.*?</strong>)", rich(value))
    return [node("strong", [text(html.unescape(part[8:-9]))])
            if part.startswith("<strong>") else text(html.unescape(part))
            for part in parts if part]


def label_children(value):
    return value["nodes"] if isinstance(value, dict) else rich_nodes(value)


def carrier(spec):
    """Bind slots to the shared renderer's independently checked rich carrier."""
    slot = lambda role: spec.slot(role).content
    if spec.component_id == "HB-SPECIAL-FCC":
        payload = fcc_semantic_projection(spec)
        result = [paragraph(v) for v in payload["opening_copy"]]
        for block in payload["left_blocks"] + payload["right_blocks"]:
            if block["kind"] == "list":
                result.append(node("list", [node("list_item", [text(v)])
                                            for v in block["items"]], ordered=False))
            else:
                result.append(paragraph(" ".join(filter(None, [block.get("label"), block["text"]]))))
        return result
    if spec.component_id == "HB-SPECIAL-INBOX":
        return [table([[node("table_cell", [node("image", source=c["image_ref"], alt=c["alt"]),
                                            paragraph(c["label"])], header=False)
                        for c in web_inbox_projection(spec)["cards"]]]),
                table([[cell(slot("tip_label")), cell(slot("tip_body"))]])]
    if spec.component_id == "HB-TABLE-SPEC":
        title = node("heading", [node("inline_group", [text(slot("section_title"))],
                                     presentation=attrs("hb-spec-section-text"))], level=2,
                     presentation=attrs("hb-spec-section hb-spec-group"))
        rows = [[cell(r["label"] if i == 0 else "", header=True), cell(v["text"])]
                for r in slot("rows") for i, v in enumerate(r["values"])]
        return [title, table(rows)]
    if spec.component_id == "HB-SPECIAL-APP":
        return [node("image", source=spec.assets[0].asset_ref, alt="App download"),
                *[paragraph(c["text"]) for c in slot("columns")]]
    return None


def reference_flow(spec, flow):
    payload = web_reference_figure_projection(spec)
    count = len(payload["captions"])
    payload.update(capture_following_lines=count, captions_origin="carrier", composite_locale="")
    soup = BeautifulSoup(flow_nodes_to_html([root(v) for v in flow]), "html.parser")
    image = _validate_carrier(payload, soup)
    _transform_reference_figure(soup, image=image, spec=_component_contract(payload),
                               source_path=Path(spec.source_ref),
                               composites=WebCompositeContext(None, "JHP-3000D", "US", spec.language, ValueError))
    spec_data = spec.to_dict()
    spec_data["metadata"].update(capture_following_lines=count,
                                source_fragment_sha256=soup.figure["data-source-fragment-sha256"])
    return component_flow_node(ComponentSpec.from_dict(spec_data), carrier_flow=flow, root=True)


def prose(raw):
    """Preserve bullets and their subordinate source lines."""
    raw = unicodedata.normalize("NFC", raw)
    chunks = re.split(r"(?:^|\n)\s*[•·]\s*", raw)
    result = [paragraph(normalize(chunks[0]))] if normalize(chunks[0]) else []
    if len(chunks) > 1:
        items = []
        for chunk in chunks[1:]:
            parts = re.split(r"\n\s*-(?=[A-Za-zÀ-ÿ])", chunk)
            children = [text(normalize(parts[0]))]
            if len(parts) > 1:
                children.append(node("list", [
                    node("list_item", [text(normalize(part))]) for part in parts[1:]
                ], ordered=False))
            items.append(node("list_item", children))
        result.append(node("list", items, ordered=False))
    return result


class Native:
    def __init__(self, language):
        if sha(PDF) != PDF_SHA:
            raise ValueError("source PDF identity changed")
        self.doc = fitz.open(PDF)
        self.language = language
        self.offset = {"en": 0, "fr": 18, "es": 36}[language]
        self.words = {p + 1: page.get_text("words") for p, page in enumerate(self.doc)}
        self.used = {}
        self.selections = []
        self.chapters = []
        self.current = None
        self.serial = 0
        self.figures = {f["id"]: f for f in json.loads((SOURCE / "source/figures.json").read_text())}

    def page(self, english_page):
        return english_page + self.offset

    def take(self, p, box, *, purpose="live-copy", unused=False, reading_order="native"):
        indices = [
            i for i, w in enumerate(self.words[p])
            if box[0] <= (w[0] + w[2]) / 2 < box[2]
            and box[1] <= (w[1] + w[3]) / 2 < box[3]
            and (not unused or (p, i) not in self.used)
        ]
        lines = {}
        for i in indices:
            w = self.words[p][i]
            self.used.setdefault((p, i), []).append(purpose)
            lines.setdefault((w[5], w[6]), []).append(w)
        ordered_lines = list(lines.values())
        if reading_order == "vertical":
            ordered_lines.sort(key=lambda ws: (min(w[1] for w in ws), min(w[0] for w in ws)))
        elif reading_order != "native":
            raise ValueError("unknown native reading order")
        raw = "\n".join(
            " ".join(w[4] for w in sorted(ws, key=lambda w: w[7]))
            for ws in ordered_lines
        )
        value = normalize(raw)
        self.selections.append({
            "page": p, "bbox": box, "purpose": purpose,
            "word_ids": indices, "raw": raw, "normalized": value,
        })
        bbox = [
            min((self.words[p][i][0] for i in indices), default=box[0]),
            min((self.words[p][i][1] for i in indices), default=box[1]),
            max((self.words[p][i][2] for i in indices), default=box[2]),
            max((self.words[p][i][3] for i in indices), default=box[3]),
        ]
        return value, raw, bbox

    def t(self, p, box, **kwargs):
        return self.take(p, box, **kwargs)[0]

    def b(self, p, index, purpose="live-copy"):
        block = self.doc[p - 1].get_text("blocks")[index]
        return self.take(p, [block[0] - .1, block[1] - .1, block[2] + .1, block[3] + .1],
                         purpose=purpose)[0]

    def add(self, *nodes):
        def descendants(item):
            for child in item.get("children", []):
                child.pop("schema_version", None)
                descendants(child)
        for item in nodes:
            descendants(item)
            self.current["nodes"].append(item if "schema_version" in item else root(item))

    def chapter(self, identity, title):
        self.current = {"id": identity, "title": title, "nodes": []}
        self.chapters.append(self.current)
        self.add(heading(title, level=2, anchor="native-" + identity))

    def h(self, p, box, level=3):
        candidates = [s["bbox"] for b in self.doc[p - 1].get_text("dict")["blocks"]
                      for line in b.get("lines", []) for s in line["spans"]
                      if "Bold" in s["font"] and s["size"] >= 7
                      and fitz.Rect(box).contains(fitz.Point(
                          (s["bbox"][0] + s["bbox"][2]) / 2,
                          (s["bbox"][1] + s["bbox"][3]) / 2))]
        if candidates:
            box = [min(b[0] for b in candidates) - .1, min(b[1] for b in candidates) - .1,
                   max(b[2] for b in candidates) + .1, max(b[3] for b in candidates) + .1]
        self.add(heading(self.t(p, box), level=level))

    def paras(self, p, box):
        self.add(*prose(self.take(p, box)[1]))

    def comp(self, factory, **kwargs):
        self.serial += 1
        spec = factory(
            source_ref=f"native-pdf/{self.current['id']}/{self.serial}",
            language=self.language, **kwargs,
        )
        return component_flow_node(spec, carrier_flow=carrier(spec), root=True)

    def figure(self, identity, labels=(), *, width="regular", panel="#ffffff"):
        g = self.figures[identity]
        path = SOURCE / "assets" / (identity + ".svg")
        art_hash = sha(path)
        captions, geometry = [], []
        for i, item in enumerate(labels):
            value, rect, *fill = item
            source_rect = identity == "overview" or (identity == "power" and i < 2)
            if source_rect and isinstance(value, dict):
                b, frame = value["bbox"], g["bbox"]
                rect = [(b[0] - frame[0]) / (frame[2] - frame[0]) * 100,
                        (b[1] - frame[1]) / (frame[3] - frame[1]) * 100,
                        (b[2] - b[0] + 1) / (frame[2] - frame[0]) * 100,
                        (b[3] - b[1]) / (frame[3] - frame[1]) * 100]
                if identity == "power":
                    rect[2] = max(rect[2], item[1][2])
            markup = flow_nodes_to_html([root(node("inline_group", label_children(value)))])
            captions.append({"text": BeautifulSoup(markup, "html.parser").get_text(" ", strip=True),
                             "html": markup})
            geometry.append({"line": i, "rect": rect, **({"fill": fill[0]} if fill else {})})
        metadata = {}
        if labels:
            metadata = {
                "presentation_mode": "base-art-live-copy",
                "base_art_layout": {
                    "art_sha256": art_hash, "panel_top": 0,
                    "panel_fill": panel, "preserve_frame": True,
                    "mobile_labels": "overlay", "labels": geometry,
                },
            }
        spec = reference_figure_component_spec(
            reference_id=identity, accessibility_label=identity,
            caption_mode="live" if labels else "none", captions=captions,
            adjacent_copy=None, source_art_ref="assets/" + path.name,
            source_art_locale_policy="shared", source_fragment_sha256=art_hash,
            source_ref=f"native-pdf/page-{g['page']}/{identity}",
            language=self.language, image_key=identity, metadata=metadata,
        )
        flow = [node("image", source="assets/" + path.name, alt=identity)]
        if labels:
            flow.append(node("group", [node("group", [node("inline_group", label_children(v[0]))], role="container",
                                           presentation=attrs("line")) for v in labels],
                             role="container", presentation=attrs("line-block")))
        return node("group", [reference_flow(spec, flow)], role="container",
                    presentation={"html": {"attributes": {
                        "class": f"native-figure native-{identity} native-{width}",
                    }}})

    def labels(self, p, regions, geometry):
        return [(self.caption(p, box), rect, *fill)
                for box, (rect, *fill) in zip(regions, geometry, strict=True)]

    def caption(self, p, box):
        """Keep native label line order and bold typography as editable nodes."""
        _, _, bbox = self.take(p, box)
        words = [self.words[p][i] for i in self.selections[-1]["word_ids"]]
        lines = {}
        for word in words:
            lines.setdefault((word[5], word[6]), []).append(word)
        spans = [s for b in self.doc[p - 1].get_text("dict")["blocks"]
                 for line in b.get("lines", []) for s in line["spans"]]
        children = []
        for line in sorted(lines.values(), key=lambda ws: (min(w[1] for w in ws), min(w[0] for w in ws))):
            if children:
                children.append(node("line_break"))
            for i, word in enumerate(sorted(line, key=lambda w: w[0])):
                if i:
                    children.append(text(" "))
                value = normalize(word[4])
                bold = any("Bold" in s["font"] and fitz.Rect(s["bbox"]).contains(
                    fitz.Point((word[0] + word[2]) / 2, (word[1] + word[3]) / 2)) for s in spans)
                children.extend([node("strong", [text(value)])] if bold else rich_nodes(value))
        return {"nodes": children, "bbox": bbox}

    def finish(self):
        pages = [2, *range(4 + self.offset, 22 + self.offset), 58]
        for p in pages[1:-1]:
            self.take(p, [0, 500, 369, 525], purpose="printed-folio")
        missing = [
            {"page": p, "word_id": i, "word": w[4], "bbox": list(w[:4])}
            for p in pages[1:-1] for i, w in enumerate(self.words[p])
            if (p, i) not in self.used
        ]
        locale = SOURCE / "source" / self.language
        dump(locale / "coverage.json", {
            "schema": "native-word-coverage/v1", "language": self.language,
            "pages": pages, "classified_word_count": len(self.used),
            "unmapped": missing, "selections": self.selections,
        })
        dump(locale / "content.json", {
            "title": "Jackery HomePower 3000 · JHP-3000D",
            "model": "JHP-3000D", "region": "US", "language": self.language,
            "source_sha256": PDF_SHA, "chapters": self.chapters,
        })
        return missing
