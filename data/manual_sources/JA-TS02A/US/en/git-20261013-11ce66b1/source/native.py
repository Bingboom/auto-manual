"""Source-local selections from the archived JA-TS02A PDF and shared flow constructors.

Every selection records its PDF page, rectangle, word IDs and purpose. The
coverage gate refuses any English body word that no selection classified.
Prose keeps the print's own structure: a line the print ended early, while the
next word would still have fitted, is a print line break; every other line end
is a wrap. Bold and semibold print runs stay strong.
"""
from __future__ import annotations

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
MODEL, REGION, LANGUAGE = "JA-TS02A", "US", "en"
PAGES = range(3, 25)  # English body: PDF pages 3-24, printed 01-22.
LIST_MARK = re.compile(r"^(?:(?P<number>\d+)\.\s?|(?P<bullet>•)\s*)")
# Print line ends where a word is split without a hyphen glyph, or with one.
SPLIT_WORDS = {("approxi", "mately"), ("consump-", "tion")}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def attrs(value):
    return {"html": {"attributes": {"class": value}}}


def normalize(raw):
    value = unicodedata.normalize("NFC", raw).replace("\x00", "").replace("­", "")
    for old, new in [("ﬁ", "fi"), ("ﬂ", "fl"), ("ﬀ", "ff"), ("ﬃ", "ffi"), ("ﬄ", "ffl")]:
        value = value.replace(old, new)
    return value


def archived_pdf():
    """Reassemble the archived original and refuse any byte change."""
    manifest = json.loads((SOURCE / "source_manifest.json").read_text())
    original = manifest["original_source"]
    data = b"".join((SOURCE / part["path"]).read_bytes() for part in original["archive_parts"])
    if hashlib.sha256(data).hexdigest() != original["sha256"]:
        raise ValueError("archived source PDF identity changed")
    return original, fitz.open(stream=data, filetype="pdf")


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
        self.words = {p: self.doc[p - 1].get_text("words") for p in range(1, len(self.doc) + 1)}
        self.dicts = {}
        self.used = {}
        self.selections = []
        self.chapters = []
        self.current = None
        self.serial = 0
        self.joins = []
        self.breaks = []
        self.figures = {f["slot"]: f for f in json.loads((SOURCE / "source/figures.json").read_text())
                        if "physical_page" in f}
        self.controls = {c["slot"]: c for c in json.loads((SOURCE / "source/inline-controls.json").read_text())}
        self.recoveries = json.loads((SOURCE / "source/text-recovery.json").read_text())
        self.recovered_used = set()

    # --- selection and coverage -------------------------------------------------
    def take(self, p, box, *, purpose="live-copy"):
        indices = [i for i, w in enumerate(self.words[p])
                   if box[0] <= (w[0] + w[2]) / 2 < box[2] and box[1] <= (w[1] + w[3]) / 2 < box[3]]
        for i in indices:
            self.used.setdefault((p, i), []).append(purpose)
        raw = " ".join(self.words[p][i][4] for i in indices)
        self.selections.append({"page": p, "bbox": list(box), "purpose": purpose,
                                "word_ids": indices, "raw": raw})
        return " ".join(normalize(raw).split())

    def t(self, p, box):
        value = self.take(p, box)
        if not value:
            raise ValueError(f"empty native selection p{p} {box}")
        return value

    def page_dict(self, p):
        if p not in self.dicts:
            self.dicts[p] = self.doc[p - 1].get_text("dict")
        return self.dicts[p]

    def lines(self, p, box, *, purpose="live-copy"):
        """Native lines inside box, with weight runs and the first word's width."""
        self.take(p, box, purpose=purpose)
        found = []
        for block in self.page_dict(p)["blocks"]:
            for line in block.get("lines", []):
                spans = [s for s in line["spans"] if s["text"]
                         and box[0] <= (s["bbox"][0] + s["bbox"][2]) / 2 < box[2]
                         and box[1] <= (s["bbox"][1] + s["bbox"][3]) / 2 < box[3]]
                if not "".join(s["text"] for s in spans).strip():
                    continue
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
                strong = "Bold" in s["font"]  # also SemiBold
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
        for r in self.recoveries:
            box_r = r["bbox"]
            if r["physical_page"] == p and box[0] <= box_r[0] < box[2] and box[1] <= (box_r[1] + box_r[3]) / 2 < box[3]:
                self.recovered_used.add((p, r["text"]))
                size = result[0].size if result else 6.36
                width = fitz.get_text_length(r["text"], fontname="helv", fontsize=size)
                first = fitz.get_text_length(r["text"].split()[0], fontname="helv", fontsize=size)
                bbox = [box_r[0], box_r[1], box_r[0] + width, box_r[3]]
                result.append(Line(bbox, size, [(r["text"], False)], first, True))
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

    def prose(self, p, box, *, right, extra=(), keep_marks=False, every_line=False):
        """Paragraphs and lists from native lines, keeping print line breaks.

        every_line marks a reviewed region whose printed lines are separate statements
        the geometry cannot prove (each line already fills its narrow panel).
        """
        lines = self.lines(p, box)
        for page, page_box in extra:
            lines += self.lines(page, page_box)
        return build_flow(self, p, lines, right=right, keep_marks=keep_marks, every_line=every_line)

    def comp(self, factory, carrier, **kwargs):
        self.serial += 1
        spec = factory(source_ref=f"native-pdf/{self.current['id']}/{self.serial}", language=LANGUAGE, **kwargs)
        return component_flow_node(spec, carrier_flow=carrier(spec), root=True)

    def embedded(self, slot):
        """Words printed inside reviewed artwork stay in the art (not live copy)."""
        figure = self.figures[slot]
        self.take(figure["physical_page"], figure["bbox"], purpose="embedded-art/" + slot)

    def figure(self, slot, *, width="regular"):
        g = self.figures[slot]
        self.embedded(slot)
        path = SOURCE / g["local_path"]
        art = sha(path)
        words = [w for w in self.words[g["physical_page"]]
                 if g["bbox"][0] <= (w[0] + w[2]) / 2 < g["bbox"][2] and g["bbox"][1] <= (w[1] + w[3]) / 2 < g["bbox"][3]]
        mode = "embedded" if words else "none"
        # Note sentences printed in the art (grey warning strips) are read out in the alt text, verbatim.
        printed = normalize(" ".join(w[4] for w in words))
        for note in g.get("printed_notes", []):
            if note not in printed:
                raise ValueError(f"{slot}: printed note not in the art: {note!r}")
        alt = " ".join([g["caption"] + ".", *g.get("printed_notes", [])]) if g.get("printed_notes") else g["caption"]
        spec = reference_figure_component_spec(
            reference_id=slot, accessibility_label=alt, caption_mode=mode, captions=[],
            adjacent_copy=None, source_art_ref=g["local_path"], source_art_locale_policy="exact",
            source_fragment_sha256=art, source_ref=f"native-pdf/page-{g['physical_page']}/{slot}",
            language=LANGUAGE, image_key=slot,
        )
        flow = [node("image", source=g["local_path"], alt=alt)]
        return node("group", [reference_flow(spec, flow)], role="container",
                    presentation=attrs(f"native-figure native-{slot} native-{width}"))

    def control(self, slot):
        c = self.controls[slot]
        return node("image", source=c["local_path"], alt=c["meaning"],
                    presentation=attrs("native-inline-control"))

    def finish(self):
        for p in PAGES:
            self.take(p, [0, 0, 369, 22], purpose="printed-badge")
            self.take(p, [0, 500, 369, 525], purpose="printed-folio")
        missing = [{"page": p, "word_id": i, "word": w[4], "bbox": [round(v, 1) for v in w[:4]]}
                   for p in PAGES for i, w in enumerate(self.words[p]) if (p, i) not in self.used]
        double = [{"page": p, "word_id": i, "purposes": purposes} for (p, i), purposes in self.used.items()
                  if len([x for x in purposes if x == "live-copy"]) > 1]
        unused_recoveries = [r["text"] for r in self.recoveries
                             if (r["physical_page"], r["text"]) not in self.recovered_used]
        unused_joins = sorted(set(SPLIT_WORDS) - {tuple(j[:2]) for j in self.joins})
        locale = SOURCE / "source" / LANGUAGE
        dump(locale / "coverage.json", {
            "schema": "native-word-coverage/v1", "language": LANGUAGE, "pages": list(PAGES),
            "classified_word_count": len([k for k in self.used if k[0] in PAGES]),
            "unmapped": missing, "duplicate_live_copy": double,
            "unused_recoveries": unused_recoveries, "unused_split_words": unused_joins,
            "word_joins": self.joins, "print_line_breaks": self.breaks,
            "selections": self.selections,
        })
        dump(locale / "content.json", {
            "title": "Jackery Smart Transfer Switch · JA-TS02A",
            "model": MODEL, "region": REGION, "language": LANGUAGE,
            "source_sha256": self.pdf_sha, "chapters": self.chapters,
        })
        return missing + double + unused_recoveries + unused_joins


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
def junction(native, p, line, nxt, right, pitch):
    """'wrap', 'join' (split word), 'break' (print line break) or 'gap' (paragraph)."""
    tail, head = line.text.rstrip(), nxt.text.lstrip()
    for left, rest in SPLIT_WORDS:
        if tail.endswith(left) and head.startswith(rest):
            native.joins.append([left, rest, p, round(line.y0, 1)])
            return "join"
    if nxt.y0 - line.y0 > pitch * 1.3 or nxt.y0 < line.y0:
        return "gap"
    width = nxt.first_word_width or len(head.split()[0]) * line.size * 0.5 if head else 0.0
    slack = (right - line.x1) - (width + line.size * 0.27)
    ends = bool(re.search(r"[.:!?)]$", tail))
    starts = bool(re.match(r"[A-Z0-9\"'“(•*-]", head))
    if slack >= 0 and starts and (ends or slack >= 60):
        return "break"
    return "wrap"


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
            elif kind == "join" and children:
                last = children[-1] if children[-1]["kind"] == "text" else children[-1]["children"][-1]
                last["text"] = last["text"].rstrip()
                if last["text"].endswith("-"):
                    last["text"] = last["text"][:-1]
                runs[0] = (runs[0][0].lstrip(), runs[0][1])
        for value, strong in runs:
            push(value, strong)
    # Collapse print spacing inside runs and trim the ends.
    for child in children:
        target = child if child["kind"] == "text" else (child["children"][0] if child["kind"] == "strong" else None)
        if target is not None:
            target["text"] = re.sub(r"\s+", " ", target["text"])
    if children and children[0]["kind"] in {"text", "strong"}:
        first = children[0] if children[0]["kind"] == "text" else children[0]["children"][0]
        first["text"] = first["text"].lstrip()
    if children and children[-1]["kind"] in {"text", "strong"}:
        last = children[-1] if children[-1]["kind"] == "text" else children[-1]["children"][0]
        last["text"] = last["text"].rstrip()
    for i, child in enumerate(children):
        if child["kind"] == "line_break":
            for j, side in ((i - 1, "r"), (i + 1, "l")):
                if 0 <= j < len(children) and children[j]["kind"] in {"text", "strong"}:
                    t = children[j] if children[j]["kind"] == "text" else children[j]["children"][0]
                    t["text"] = t["text"].rstrip() if side == "r" else t["text"].lstrip()
    return [c for c in children if c["kind"] == "line_break"
            or (c["text"] if c["kind"] == "text" else c["children"][0]["text"])]


def strip_mark(line, mark):
    value, strong = line.runs[0]
    rest = value[len(mark):].lstrip() if value.startswith(mark) else re.sub(r"^\s*" + re.escape(mark.strip()) + r"\s*", "", value)
    runs = ([(rest, strong)] if rest else []) + line.runs[1:]
    if not runs and len(line.runs) > 1:
        runs = line.runs[1:]
    clone = Line([line.x0, line.y0, line.x1, line.y1], line.size, runs, line.first_word_width, line.recovered)
    while clone.runs and not clone.runs[0][0].strip():
        clone.runs = clone.runs[1:]
    if clone.runs:
        clone.runs[0] = (clone.runs[0][0].lstrip(), clone.runs[0][1])
    return clone


def build_flow(native, p, lines, *, right, keep_marks=False, every_line=False):
    """Group lines into paragraphs and lists; list markers start items.

    Each junction is classified once; a list item continues across wraps only.
    """
    steps = sorted(b.y0 - a.y0 for a, b in zip(lines[:-1], lines[1:], strict=True) if 0 < b.y0 - a.y0 < a.size * 2.4)
    pitch = steps[len(steps) // 2] if steps else 11.0
    kinds = [junction(native, p, a, b, right, pitch) for a, b in zip(lines[:-1], lines[1:], strict=True)]
    if every_line:
        kinds = ["break" if k in {"wrap", "break"} else k for k in kinds]
    blocks = []  # [kind, number, display lines, junction kinds]
    for index, line in enumerate(lines):
        match = None if keep_marks else LIST_MARK.match(line.text.lstrip())
        before = kinds[index - 1] if index else "gap"
        if match:
            kind = "ol" if match.group("number") else "ul"
            blocks.append([kind, int(match.group("number") or 0), [strip_mark(line, match.group(0).strip())], []])
        elif (blocks and before != "gap" and abs(line.x0 - lines[index - 1].x0) < 8
              and (blocks[-1][0] == "p" or before in {"wrap", "join"})):
            blocks[-1][2].append(line)
            blocks[-1][3].append(before)
            if before == "break":
                prev = lines[index - 1]
                native.breaks.append([p, round(prev.y0, 1), prev.text.rstrip()[-40:], line.text.lstrip()[:40]])
        else:
            blocks.append(["p", 0, [line], []])
    flow = []
    for kind, number, block_lines, block_kinds in blocks:
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
