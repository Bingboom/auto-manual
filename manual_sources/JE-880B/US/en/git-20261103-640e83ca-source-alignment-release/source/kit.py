"""Shared flow constructors for an outlined (text-less) English booklet transcription.

The supplied PDF has no text layer: every glyph is outlined. The English copy in
``source/intake.py`` is a line-by-line transcription checked against 300 dpi renders
of ``original.pdf``; each chapter records the physical PDF pages it transcribes.
Nothing here edits the copy. Print markup is carried by a small inline syntax:

- ``**bold**``: a bold print run (``strong``);
- ``_{oc}``: a subscript run (V_{oc}, LiFePO_{4});
- ``\\n``: a print line break inside one paragraph or cell.

No node built here carries a package class or inline style: the prepared-document
shared-style gate admits only shared Web theme classes. Figure geometry lives in
``source/presentation.css`` and selects figures by their shared data attributes.
"""
from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path
import re

from bs4 import BeautifulSoup

from tools.component_specs.callout import display_label
from tools.component_specs.model import ComponentSpec
from tools.component_specs.reference_figure import reference_figure_component_spec
from tools.component_specs.reference_figure_adapters import web_reference_figure_projection
from tools.manual_ir.components import component_flow_node
from tools.manual_ir.flow import flow_nodes_to_html
from tools.web.composite_presentation import WebCompositeContext
from tools.web.frozen_ai_flow import callout as shared_callout
from tools.web.frozen_ai_flow import heading, node, root, table, text
from tools.web.presentation import _transform_reference_figure
from tools.web.reference_figure_component import _component_contract, _validate_carrier

INLINE = re.compile(r"\*\*(.+?)\*\*|_\{(.+?)\}|\n", re.S)


def sha(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def inline(value: str) -> list[dict]:
    """Inline children from the transcription markup (bold, subscript, line break)."""
    children, last = [], 0
    for match in INLINE.finditer(value):
        if match.start() > last:
            children.append(text(value[last:match.start()]))
        if match.group(1) is not None:
            children.append(node("strong", inline(match.group(1))))
        elif match.group(2) is not None:
            children.append(node("subscript", [text(match.group(2))]))
        else:
            children.append(node("line_break"))
        last = match.end()
    if last < len(value):
        children.append(text(value[last:]))
    return children


def plain(value: str) -> str:
    """Reading text of one markup string (line breaks become spaces)."""
    value = re.sub(r"\*\*(.+?)\*\*", r"\1", value, flags=re.S)
    value = re.sub(r"_\{(.+?)\}", r"\1", value)
    return " ".join(value.split())


def markup(value: str) -> str:
    """Shared-table HTML of one markup string."""
    out, last = [], 0
    for match in INLINE.finditer(value):
        out.append(html.escape(value[last:match.start()]))
        if match.group(1) is not None:
            out.append("<strong>" + markup(match.group(1)) + "</strong>")
        elif match.group(2) is not None:
            out.append("<sub>" + html.escape(match.group(2)) + "</sub>")
        else:
            out.append("<br>")
        last = match.end()
    out.append(html.escape(value[last:]))
    return "".join(out)


def P(value: str) -> dict:  # noqa: N802 - flow constructor
    return node("paragraph", inline(value))


def _items(values):
    items = []
    for value in values:
        if isinstance(value, tuple):
            body, nested = value
            items.append(node("list_item", [*inline(body), nested]))
        else:
            items.append(node("list_item", inline(value)))
    return items


def UL(*values) -> dict:  # noqa: N802 - flow constructor
    """A printed bullet list; an item given as (text, UL(...)) nests the hollow-bullet list."""
    return node("list", _items(values), ordered=False)


def OL(*values, start: int = 1) -> dict:  # noqa: N802 - flow constructor
    fields = {"ordered": True}
    if start != 1:
        fields["start"] = start
    return node("list", _items(values), **fields)


def pair(value: str, key: str) -> dict:
    return {key + "_html": markup(value), key + "_text": plain(value)}


def cell_pair(value: str) -> dict:
    return {"html": markup(value), "text": BeautifulSoup(markup(value), "html.parser").get_text("\n", strip=True)}


def blocks(*items) -> list[dict]:
    """Warranty section blocks: a str is a paragraph, a list of str a printed bullet list."""
    result = []
    for item in items:
        if isinstance(item, list):
            result.append({"kind": "list", "items": [plain(v) for v in item],
                           "html": "<ul>" + "".join("<li>" + markup(v) + "</li>" for v in item) + "</ul>"})
        else:
            result.append({"kind": "paragraph", "text": plain(item), "html": "<p>" + markup(item) + "</p>"})
    return result


class Book:
    """Chapters of shared flow; every chapter lists the PDF pages it transcribes."""

    def __init__(self, source: Path, model: str, region: str, language: str, title: str):
        self.source, self.model, self.region, self.language, self.title = source, model, region, language, title
        manifest = json.loads((source / "source_manifest.json").read_text())
        self.original = manifest["original_source"]
        if sha(source / self.original["filename"]) != self.original["sha256"]:
            raise ValueError("archived source identity changed")
        self.figures = {f["slot"]: f for f in json.loads((source / "source/figures.json").read_text())}
        self.used_figures = []
        self.chapters, self.current, self.serial = [], None, 0

    def chapter(self, identity: str, title: str, pages: list[int]):
        self.current = {"id": identity, "title": title, "pages": pages, "nodes": []}
        self.chapters.append(self.current)
        self.add(heading(title, level=2, anchor="native-" + identity))

    def add(self, *nodes):
        def descendants(item):
            for child in item.get("children", []):
                child.pop("schema_version", None)
                descendants(child)
        for item in nodes:
            descendants(item)
            self.current["nodes"].append(item if "schema_version" in item else root(item))

    def h(self, title: str, level: int = 3):
        self.add(heading(title, level=level))

    def callout(self, label: str, *body, variant: str):
        flow = [P(b) if isinstance(b, str) else b for b in body]
        self.serial += 1
        self.add(shared_callout(display_label(label), flow, variant=variant, language=self.language,
                                source_ref=f"transcribed-pdf/{self.current['id']}/{variant}-{self.serial}"))

    def comp(self, factory, carrier=lambda spec: None, **kwargs):
        self.serial += 1
        spec = factory(source_ref=f"transcribed-pdf/{self.current['id']}/{self.serial}",
                       language=self.language, **kwargs)
        self.add(component_flow_node(spec, carrier_flow=carrier(spec), root=True))

    def figure(self, slot: str):
        g = self.figures[slot]
        self.used_figures.append(slot)
        art = sha(self.source / g["local_path"])
        alt = " ".join([g["caption"] + ".", *g["printed_notes"]]) if g.get("printed_notes") else g["caption"]
        spec = reference_figure_component_spec(
            reference_id=slot, accessibility_label=alt, caption_mode="embedded" if g.get("embedded_words") else "none",
            captions=[], adjacent_copy=None, source_art_ref=g["local_path"], source_art_locale_policy="exact",
            source_fragment_sha256=art, source_ref=f"transcribed-pdf/page-{g['physical_page']}/{slot}",
            language=self.language, image_key=slot,
        )
        self.add(reference_flow(spec, [node("image", source=g["local_path"], alt=alt)], self))

    def finish(self, extra: dict | None = None) -> list[str]:
        unused = sorted(set(self.figures) - set(self.used_figures))
        twice = sorted({s for s in self.used_figures if self.used_figures.count(s) > 1})
        dump(self.source / "source" / self.language / "content.json", {
            "title": self.title, "model": self.model, "region": self.region, "language": self.language,
            "source_sha256": self.original["sha256"], "transcription": "outlined-pdf-manual-transcription",
            **(extra or {}), "chapters": self.chapters,
        })
        return [f"unused figure {s}" for s in unused] + [f"figure used twice {s}" for s in twice]


def reference_flow(spec, flow, book):
    payload = web_reference_figure_projection(spec)
    count = len(payload["captions"])
    payload.update(capture_following_lines=count, captions_origin="carrier", composite_locale="")
    soup = BeautifulSoup(flow_nodes_to_html([root(v) for v in flow]), "html.parser")
    image = _validate_carrier(payload, soup)
    _transform_reference_figure(soup, image=image, spec=_component_contract(payload),
                                source_path=Path(spec.source_ref),
                                composites=WebCompositeContext(None, book.model, book.region, spec.language, ValueError))
    spec_data = spec.to_dict()
    spec_data["metadata"].update(capture_following_lines=count,
                                 source_fragment_sha256=soup.figure["data-source-fragment-sha256"])
    return component_flow_node(ComponentSpec.from_dict(spec_data), carrier_flow=flow, root=True)


# --- shared component carriers ------------------------------------------------------
def inbox_carrier(spec):
    from tools.component_specs.inbox_adapters import web_inbox_projection
    cards = web_inbox_projection(spec)["cards"]
    return [table([[node("table_cell", [node("image", source=c["image_ref"], alt=c["alt"]),
                                        node("paragraph", [text(c["label"])])], header=False) for c in cards]])]


def spec_carrier(spec):
    slot = lambda role: spec.slot(role).content  # noqa: E731
    title = node("heading", [node("inline_group", [text(slot("section_title"))],
                                  presentation={"html": {"attributes": {"class": "hb-spec-section-text"}}})],
                 level=2, presentation={"html": {"attributes": {"class": "hb-spec-section hb-spec-group"}}})
    rows = [[node("table_cell", [text(r["label"] if i == 0 else "")], header=True),
             node("table_cell", [text(v["text"])], header=False)]
            for r in slot("rows") for i, v in enumerate(r["values"])]
    return [title, table(rows)]


def fcc_flow(spec, opening: str, paragraphs: list[str]) -> dict:
    """The shared FCC composition inside its balanced-flow group (JHP-3600C US form)."""
    carrier = [node("paragraph", [text(opening)]), *[node("paragraph", [text(p)]) for p in paragraphs]]
    return node("group", [component_flow_node(spec, carrier_flow=carrier)], role="container",
                presentation={"html": {"attributes": {"class": "hb-fcc-balanced-flow"}}})
