"""Source-local selections from the archived JBP-3600A JP production sheet.

The supplied PDF is one 3715 x 2605 pt production drawing. Twelve 130 x 185 mm
manual panels sit in a 6 x 2 grid inside its frame; each panel is read as one
page in panel-local PDF points. Panel 1 is the printed cover, panel 2 the
contents, panels 3-12 the printed pages 01-10. Words outside the panels (frame
grid, title block, revision table, production notes) are page 0.

Every selection records its panel, rectangle, word IDs and purpose. The
coverage gate refuses any word on the sheet that no selection classified.
Prose keeps the print's own structure. At a junction between Japanese
characters a wrapped line joins without a space. A line the print ended early
is a print line break: at least one em short after closing punctuation, or
three ems short anywhere. Latin junctions keep the English rule (the next word
would still have fitted). Bold print runs stay strong.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import unicodedata

import fitz
from bs4 import BeautifulSoup

from tools.component_specs.model import ComponentSpec
from tools.component_specs.reference_figure import reference_figure_component_spec
from tools.component_specs.reference_figure_adapters import web_reference_figure_projection
from tools.manual_ir.components import component_flow_node
from tools.manual_ir.flow import flow_nodes_to_html
from tools.web.composite_presentation import WebCompositeContext
from tools.web.frozen_ai_flow import heading, node, root, text
from tools.web.presentation import _transform_reference_figure
from tools.web.reference_figure_component import _component_contract, _validate_carrier

SOURCE = Path(__file__).resolve().parents[1]
MODEL, REGION, LANGUAGE = "JBP-3600A", "JP", "ja"
# Panel top-left corners on the sheet (the drawn 368.5 x 524.4 pt panel frames), reading order.
PANEL_ORIGINS = [(x, y) for y in (598.989, 1172.879)
                 for x in (729.003, 1097.507, 1466.011, 1834.515, 2203.019, 2571.523)]
PANEL_SIZE = (368.504, 524.409)
PANELS = range(1, 13)
BODY = range(3, 13)  # printed pages 01-10
SHEET = 0            # production metadata outside the panels
LIST_MARK = re.compile(r"^(?:(?P<number>\d+)\.(?!\d)\s*|(?P<bullet>[・•])\s*)")
FINAL = "。．！？」』）):：!?."


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def attrs(value):
    return {"html": {"attributes": {"class": value}}}


def normalize(raw):
    return unicodedata.normalize("NFC", raw).replace("\x00", "").replace("­", "")


def is_cjk(ch):
    if not ch:
        return False
    name = unicodedata.name(ch, "")
    return (any(t in name for t in ("CJK", "HIRAGANA", "KATAKANA", "FULLWIDTH", "IDEOGRAPHIC"))
            or ch in "。、「」『』（）・：；！？～ー〜※■●…")


def archived_pdf():
    """Reassemble the archived original and refuse any byte change."""
    manifest = json.loads((SOURCE / "source_manifest.json").read_text())
    original = manifest["original_source"]
    data = b"".join((SOURCE / part["path"]).read_bytes() for part in original["archive_parts"])
    if hashlib.sha256(data).hexdigest() != original["sha256"]:
        raise ValueError("archived source PDF identity changed")
    return original, fitz.open(stream=data, filetype="pdf")


def panel_of(bbox):
    cx, cy = (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2
    for index, (x, y) in enumerate(PANEL_ORIGINS, 1):
        if x <= cx < x + PANEL_SIZE[0] and y <= cy < y + PANEL_SIZE[1]:
            return index, x, y
    return SHEET, 0.0, 0.0


def label_spans(page, panel, box, labels):
    """The printed label lines a text-free figure carries as live copy, in source order.

    Each listed label must match a whole native line inside the panel-local box,
    exactly as many times as it is listed. Returns sheet-coordinate line rects.
    """
    x, y = PANEL_ORIGINS[panel - 1]
    crop = fitz.Rect(box[0] + x, box[1] + y, box[2] + x, box[3] + y)
    found = []
    for block in page.get_text("dict", clip=crop)["blocks"]:
        for line in block.get("lines", []):
            spans = [span for span in line["spans"] if span["text"].strip()]
            if not spans:
                continue
            rect = fitz.Rect(line["bbox"])
            if crop.contains((rect.tl + rect.br) / 2):
                found.append({"text": normalize("".join(span["text"] for span in line["spans"])).strip(),
                              "rect": rect, "size": max(span["size"] for span in spans),
                              "origin": spans[0]["origin"], "bold": all("Bold" in span["font"] for span in spans)})
    found.sort(key=lambda s: (round(s["origin"][1], 0), s["rect"].x0))
    wanted = [label["text"] for label in labels]
    chosen = [s for s in found if s["text"] in wanted]
    if sorted(s["text"] for s in chosen) != sorted(wanted):
        raise ValueError(f"label spans differ in panel {panel} {box}: {[s['text'] for s in chosen]}")
    return chosen


class Line:
    """One print line: geometry, size and weight runs."""

    def __init__(self, bbox, size, runs, first_word_width, recovered=False):
        self.x0, self.y0, self.x1, self.y1 = bbox
        self.size = size
        self.runs = runs
        self.first_word_width = first_word_width
        self.recovered = recovered

    @property
    def text(self):
        return "".join(value for value, _ in self.runs)


class Native:
    def __init__(self):
        self.original, self.doc = archived_pdf()
        self.pdf_sha = self.original["sha256"]
        page = self.doc[0]
        self.words = {p: [] for p in [SHEET, *PANELS]}
        for w in page.get_text("words"):
            p, x, y = panel_of(w[:4])
            self.words[p].append((w[0] - x, w[1] - y, w[2] - x, w[3] - y, w[4]))
        self.spans = {p: [] for p in [SHEET, *PANELS]}  # one list of spans per native line
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                p, x, y = panel_of(line["bbox"])
                spans = []
                for s in line["spans"]:
                    b = s["bbox"]
                    spans.append({**s, "bbox": (b[0] - x, b[1] - y, b[2] - x, b[3] - y)})
                self.spans[p].append(spans)
        self.used = {}
        self.selections = []
        self.chapters = []
        self.current = None
        self.serial = 0
        self.breaks = []
        self.figures = {f["slot"]: f for f in json.loads((SOURCE / "source/figures.json").read_text())}
        self.recoveries = json.loads((SOURCE / "source/text-recovery.json").read_text())
        self.recovered_used = set()

    # --- selection and coverage -------------------------------------------------
    def take(self, p, box, *, purpose="live-copy"):
        indices = [i for i, w in enumerate(self.words[p])
                   if box[0] <= (w[0] + w[2]) / 2 < box[2] and box[1] <= (w[1] + w[3]) / 2 < box[3]]
        for i in indices:
            self.used.setdefault((p, i), []).append(purpose)
        raw = " ".join(self.words[p][i][4] for i in indices)
        self.selections.append({"panel": p, "bbox": list(box), "purpose": purpose,
                                "word_ids": indices, "raw": raw})
        return " ".join(normalize(raw).split())

    def t(self, p, box):
        value = self.take(p, box)
        if not value:
            raise ValueError(f"empty native selection panel {p} {box}")
        return value

    def recovered(self, p, box):
        """A visible print word drawn as outlines (absent from the text layer)."""
        for r in self.recoveries:
            b = r["bbox"]
            if r["panel"] == p and box[0] <= b[0] < box[2] and box[1] <= (b[1] + b[3]) / 2 < box[3]:
                self.recovered_used.add((p, r["text"]))
                return r["text"]
        raise ValueError(f"no text recovery in panel {p} {box}")

    def lines(self, p, box, *, purpose="live-copy"):
        """Native lines inside box, with weight runs and the first word's width."""
        self.take(p, box, purpose=purpose)
        found = []
        for line in self.spans[p]:
            spans = [s for s in line if s["text"]
                     and box[0] <= (s["bbox"][0] + s["bbox"][2]) / 2 < box[2]
                     and box[1] <= (s["bbox"][1] + s["bbox"][3]) / 2 < box[3]]
            if "".join(s["text"] for s in spans).strip():
                found.append(spans)
        merged = []
        for spans in sorted(found, key=lambda ss: (round(ss[0]["bbox"][1]), ss[0]["bbox"][0])):
            if merged and abs(merged[-1][0]["bbox"][1] - spans[0]["bbox"][1]) < 1.5:
                merged[-1].extend(spans)
            else:
                merged.append(list(spans))
        result = []
        for spans in merged:
            spans.sort(key=lambda s: s["bbox"][0])
            runs = []
            for s in spans:
                strong = "Bold" in s["font"]
                value = normalize(s["text"])
                if runs and runs[-1][1] == strong:
                    runs[-1] = (runs[-1][0] + value, strong)
                else:
                    runs.append((value, strong))
            bbox = [min(s["bbox"][0] for s in spans), min(s["bbox"][1] for s in spans),
                    max(s["bbox"][2] for s in spans if s["text"].strip()), max(s["bbox"][3] for s in spans)]
            first = [w for w in self.words[p] if abs(w[1] - bbox[1]) < 2.5 and abs(w[0] - bbox[0]) < 3.5]
            width = (first[0][2] - first[0][0]) if first else 0.0
            size = max(s["size"] for s in spans if s["text"].strip())
            result.append(Line(bbox, size, runs, width))
        result.sort(key=lambda ln: (round(ln.y0, 0), ln.x0))
        return result

    # --- flow assembly ------------------------------------------------------------
    def add(self, *nodes):
        def descendants(item):
            for child in item.get("children", []):
                child.pop("schema_version", None)
                descendants(child)
        for item in nodes:
            descendants(item)
            self.current["nodes"].append(item if "schema_version" in item else root(item))

    def chapter(self, identity, p, box):
        title = self.t(p, box)
        self.current = {"id": identity, "title": title, "nodes": []}
        self.chapters.append(self.current)
        self.add(heading(title, level=2, anchor="native-" + identity))

    def h(self, p, box, level=3):
        self.add(heading(self.t(p, box), level=level))

    def prose(self, p, box, *, right, lists="all", every_line=False):
        """Paragraphs and lists from native lines, keeping print line breaks.

        lists: "all" (numbered and bullet marks start items), "bullets" (numbered
        lines stay printed paragraphs) or "none". every_line marks a reviewed
        region whose printed lines are separate statements.
        """
        return build_flow(self, p, self.lines(p, box), right=right, lists=lists, every_line=every_line)

    def comp(self, factory, carrier, **kwargs):
        self.serial += 1
        spec = factory(source_ref=f"native-pdf/{self.current['id']}/{self.serial}", language=LANGUAGE, **kwargs)
        return component_flow_node(spec, carrier_flow=carrier(spec), root=True)

    def embedded(self, slot):
        """Words printed inside reviewed artwork stay in the art (not live copy)."""
        figure = self.figures[slot]
        return self.take(figure["panel"], figure["bbox"], purpose="embedded-art/" + slot)

    def figure(self, slot, *, width="regular"):
        g = self.figures[slot]
        if g.get("live_labels"):
            return self.live_figure(slot, width=width)
        printed = self.embedded(slot)
        path = SOURCE / g["local_path"]
        mode = "embedded" if printed else "none"
        alt = g["caption"]
        spec = reference_figure_component_spec(
            reference_id=slot, accessibility_label=alt, caption_mode=mode, captions=[],
            adjacent_copy=None, source_art_ref=g["local_path"], source_art_locale_policy="exact",
            source_fragment_sha256=sha(path), source_ref=f"native-pdf/panel-{g['panel']}/{slot}",
            language=LANGUAGE, image_key=slot,
        )
        flow = [node("image", source=g["local_path"], alt=alt)]
        return node("group", [reference_flow(spec, flow)], role="container",
                    presentation=attrs(f"native-figure native-{slot} native-{width}"))

    def live_figure(self, slot, *, width="regular"):
        """Text-free art with its printed label lines as live copy on their print positions.

        The shared base-art reference places each line on a rectangle given in percent of
        the art; on phones the shared style stacks the lines under the art, in print order.
        """
        g = self.figures[slot]
        p, box = g["panel"], g["bbox"]
        x, y = PANEL_ORIGINS[p - 1]
        # Reading order: the left label column top to bottom, then the right one.
        middle = x + (box[0] + box[2]) / 2
        spans = sorted(label_spans(self.doc[0], p, box, g["live_labels"]),
                       key=lambda s: ((s["rect"].x0 + s["rect"].x1) / 2 >= middle, s["origin"][1], s["rect"].x0))
        width_pt, height_pt = box[2] - box[0], box[3] - box[1]
        label_ids = set()
        captions, lines, rects = [], [], []
        for index, span in enumerate(spans):
            r = span["rect"]
            ids = [i for i, w in enumerate(self.words[p])
                   if r.x0 - x <= (w[0] + w[2]) / 2 < r.x1 - x and abs(w[1] - (r.y0 - y)) < 1.0]  # same line
            label_ids.update(ids)
            for i in ids:
                self.used.setdefault((p, i), []).append("live-copy")
            self.selections.append({"panel": p, "bbox": [round(r.x0 - x, 2), round(r.y0 - y, 2),
                                                         round(r.x1 - x, 2), round(r.y1 - y, 2)],
                                    "purpose": "live-copy", "word_ids": ids, "raw": span["text"]})
            value = text(span["text"])
            inline = node("strong", [value]) if span["bold"] else value
            captions.append({"text": span["text"], "html": flow_nodes_to_html([root(deepcopy(inline))])})
            lines.append(node("group", [inline], role="container", presentation=attrs("line")))
            badge = "color" in g["live_labels"][[label["text"] for label in g["live_labels"]].index(span["text"])]
            # Glyph box from the baseline: an em above it, a quarter below; room to grow rightwards.
            top = span["origin"][1] - span["size"] * 0.95 - y
            left = r.x0 - x
            pct = [(left - box[0]) / width_pt * 100, (top - box[1]) / height_pt * 100,
                   (r.x1 - r.x0) * (2.2 if badge else 1.3) / width_pt * 100, span["size"] * 1.25 / height_pt * 100]
            pct[2] = min(pct[2], 100 - pct[0])
            rect = {"line": index, "rect": [round(v, 3) for v in pct]}
            if badge:  # the print's dark tag: a dark pill with white text, readable when stacked too
                rect["color"] = g["live_labels"][0]["color"]
                rect["fill"] = "#404042"
            rects.append(rect)
        rest = [i for i, w in enumerate(self.words[p]) if i not in label_ids
                and box[0] <= (w[0] + w[2]) / 2 < box[2] and box[1] <= (w[1] + w[3]) / 2 < box[3]]
        for i in rest:
            self.used.setdefault((p, i), []).append("embedded-art/" + slot)
        self.selections.append({"panel": p, "bbox": list(box), "purpose": "embedded-art/" + slot,
                                "word_ids": rest, "raw": " ".join(self.words[p][i][4] for i in rest)})
        path = SOURCE / g["local_path"]
        layout = {"art_sha256": sha(path), "panel_top": 0, "panel_fill": g["panel_fill"],
                  "preserve_frame": True, "labels": rects}
        if g.get("mobile_labels"):  # short marks stay on the art at every width
            layout["mobile_labels"] = g["mobile_labels"]
        spec = reference_figure_component_spec(
            reference_id=slot, accessibility_label=g["caption"], caption_mode="live", captions=captions,
            adjacent_copy=None, source_art_ref=g["local_path"], source_art_locale_policy="exact",
            source_fragment_sha256=sha(path), source_ref=f"native-pdf/panel-{p}/{slot}",
            language=LANGUAGE, image_key=g["local_path"], web_replace_key="reference." + slot,
            metadata={"presentation_mode": "base-art-live-copy", "base_art_layout": layout},
        )
        flow = [node("image", source=g["local_path"], alt=g["caption"]),
                node("group", lines, role="container", presentation=attrs("line-block"))]
        return node("group", [reference_flow(spec, flow)], role="container",
                    presentation=attrs(f"native-figure native-{slot} native-{width}"))

    def glyph(self, slot, *, css="native-inline-glyph"):
        g = self.figures[slot]
        self.embedded(slot)
        return node("image", source=g["local_path"], alt=g["caption"], presentation=attrs(css))

    def finish(self, classify_sheet):
        classify_sheet(self)
        for p in BODY:
            self.take(p, [170, 495, 200, 520], purpose="printed-folio")
        missing = [{"panel": p, "word_id": i, "word": w[4], "bbox": [round(v, 1) for v in w[:4]]}
                   for p in self.words for i, w in enumerate(self.words[p]) if (p, i) not in self.used]
        double = [{"panel": p, "word_id": i, "purposes": purposes} for (p, i), purposes in self.used.items()
                  if len([x for x in purposes if x == "live-copy"]) > 1]
        unused_recoveries = [r["text"] for r in self.recoveries
                             if (r["panel"], r["text"]) not in self.recovered_used]
        locale = SOURCE / "source" / LANGUAGE
        dump(locale / "coverage.json", {
            "schema": "native-word-coverage/v1", "language": LANGUAGE,
            "panels": list(PANELS), "body_panels": list(BODY), "sheet_page": SHEET,
            "classified_word_count": len(self.used),
            "sheet_word_count": sum(len(v) for v in self.words.values()),
            "unmapped": missing, "duplicate_live_copy": double,
            "unused_recoveries": unused_recoveries,
            "print_line_breaks": self.breaks,
            "selections": self.selections,
        })
        dump(locale / "content.json", {
            "title": "Jackery Battery Pack 3600 取扱説明書 · JBP-3600A",
            "model": MODEL, "region": REGION, "language": LANGUAGE,
            "source_sha256": self.pdf_sha, "chapters": self.chapters,
        })
        return missing + double + unused_recoveries


def reference_flow(spec, flow):
    payload = web_reference_figure_projection(spec)
    count = len(payload["captions"])
    payload.update(capture_following_lines=count, captions_origin="carrier", composite_locale="")
    soup = BeautifulSoup(flow_nodes_to_html([root(v) for v in flow]), "html.parser")
    image = _validate_carrier(payload, soup)
    _transform_reference_figure(soup, image=image, spec=_component_contract(payload),
                                source_path=Path(spec.source_ref),
                                composites=WebCompositeContext(None, MODEL, REGION, spec.language, ValueError))
    spec_data = spec.to_dict()
    spec_data["metadata"].update(capture_following_lines=count,
                                 source_fragment_sha256=soup.figure["data-source-fragment-sha256"])
    return component_flow_node(ComponentSpec.from_dict(spec_data), carrier_flow=flow, root=True)


# --- prose ------------------------------------------------------------------------
def junction(line, nxt, right, pitch):
    """'wrap' (Latin space), 'join' (CJK, no space), 'break' (print line break) or 'gap'."""
    tail, head = line.text.rstrip(), nxt.text.lstrip()
    if nxt.y0 - line.y0 > pitch * 1.3 or nxt.y0 < line.y0:
        return "gap"
    if not tail or not head:
        return "break"
    short = (right - line.x1) / line.size
    if is_cjk(tail[-1]) or is_cjk(head[0]):
        if (tail[-1] in FINAL and short >= 1.0) or short >= 3.0:
            return "break"
        return "join"
    width = nxt.first_word_width or len(head.split()[0]) * line.size * 0.5
    slack = (right - line.x1) - (width + line.size * 0.27)
    ends = bool(re.search(r"[.:!?)]$", tail))
    if slack >= 0 and (ends or slack >= 60):
        return "break"
    return "wrap"


def _leaf(child):
    return child if child["kind"] == "text" else child["children"][-1]


def runs_to_children(lines, kinds):
    """Inline children for consecutive lines joined by the given junction kinds."""
    children = []

    def push(value, strong):
        if not value:
            return
        last = children[-1] if children else None
        if strong:
            if last and last["kind"] == "strong":
                last["children"][-1]["text"] += value
            else:
                children.append(node("strong", [text(value)]))
        elif last and last["kind"] == "text":
            last["text"] += value
        else:
            children.append(text(value))

    for index, line in enumerate(lines):
        runs = list(line.runs)
        if index:
            kind = kinds[index - 1]
            if kind == "break":
                children.append(node("line_break"))
            elif kind == "wrap":
                push(" ", runs[0][1] and children and children[-1]["kind"] == "strong")
            elif kind == "join" and children and children[-1]["kind"] != "line_break":
                last = _leaf(children[-1])
                last["text"] = last["text"].rstrip()
                runs[0] = (runs[0][0].lstrip(), runs[0][1])
        for value, strong in runs:
            push(value, strong)
    # Collapse print spacing inside runs and trim the ends.
    for child in children:
        if child["kind"] in {"text", "strong"}:
            target = _leaf(child)
            target["text"] = re.sub(r"\s+", " ", target["text"])
    if children and children[0]["kind"] in {"text", "strong"}:
        _leaf(children[0])["text"] = _leaf(children[0])["text"].lstrip()
    if children and children[-1]["kind"] in {"text", "strong"}:
        _leaf(children[-1])["text"] = _leaf(children[-1])["text"].rstrip()
    for i, child in enumerate(children):
        if child["kind"] == "line_break":
            for j, side in ((i - 1, "r"), (i + 1, "l")):
                if 0 <= j < len(children) and children[j]["kind"] in {"text", "strong"}:
                    t = _leaf(children[j])
                    t["text"] = t["text"].rstrip() if side == "r" else t["text"].lstrip()
    return [c for c in children if c["kind"] == "line_break" or _leaf(c)["text"]]


def strip_mark(line, mark):
    value, strong = line.runs[0]
    rest = value.lstrip()[len(mark):].lstrip()
    runs = ([(rest, strong)] if rest else []) + line.runs[1:]
    clone = Line([line.x0, line.y0, line.x1, line.y1], line.size, runs, line.first_word_width, line.recovered)
    while clone.runs and not clone.runs[0][0].strip():
        clone.runs = clone.runs[1:]
    if clone.runs:
        clone.runs[0] = (clone.runs[0][0].lstrip(), clone.runs[0][1])
    return clone


def build_flow(native, p, lines, *, right, lists="all", every_line=False):
    """Group lines into paragraphs and lists; list markers start items.

    A list item continues across wraps, and across a print break onto a line the
    print indents (leading spaces or a hanging indent).
    """
    steps = sorted(b.y0 - a.y0 for a, b in zip(lines[:-1], lines[1:], strict=True) if 0 < b.y0 - a.y0 < a.size * 2.4)
    # Lower quartile: a region's paragraph gaps must not inflate its line pitch.
    pitch = steps[len(steps) // 4] if steps else 11.0
    kinds = [junction(a, b, right, pitch) for a, b in zip(lines[:-1], lines[1:], strict=True)]
    if every_line:
        kinds = ["break" if k in {"wrap", "join", "break"} else k for k in kinds]
    blocks = []  # [kind, number, display lines, junction kinds, first x0]
    for index, line in enumerate(lines):
        match = None if lists == "none" else LIST_MARK.match(line.text.lstrip())
        if match and lists == "bullets" and match.group("number"):
            match = None
        before = kinds[index - 1] if index else "gap"
        indented = bool(blocks) and (line.text[:1].isspace() or line.x0 > blocks[-1][4] + 3)
        if match:
            kind = "ol" if match.group("number") else "ul"
            blocks.append([kind, int(match.group("number") or 0), [strip_mark(line, match.group(0).strip())], [],
                           line.x0])
            continue
        continues = blocks and before != "gap" and (
            (blocks[-1][0] == "p" and abs(line.x0 - lines[index - 1].x0) < 8)
            or (blocks[-1][0] != "p" and (before in {"wrap", "join"} or indented)))
        if continues:
            blocks[-1][2].append(line)
            blocks[-1][3].append(before)
            if before == "break":
                prev = lines[index - 1]
                native.breaks.append([p, round(prev.y0, 1), prev.text.rstrip()[-24:], line.text.strip()[:24]])
        else:
            blocks.append(["p", 0, [line], [], line.x0])
    flow = []
    for kind, number, block_lines, block_kinds, _ in blocks:
        children = runs_to_children(block_lines, block_kinds)
        if kind == "p":
            flow.append(node("paragraph", children))
            continue
        item = node("list_item", children)
        if flow and flow[-1]["kind"] == "list" and flow[-1]["ordered"] == (kind == "ol"):
            flow[-1]["children"].append(item)
        else:
            fields = {"ordered": kind == "ol"}
            if kind == "ol" and number != 1:
                fields["start"] = number
            flow.append(node("list", [item], **fields,
                             presentation=attrs("native-steps" if kind == "ol" else "native-bullets")))
    return flow
