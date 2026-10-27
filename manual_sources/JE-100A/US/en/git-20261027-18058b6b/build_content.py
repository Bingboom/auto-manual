"""Bind the reviewed JE-100A US English transcription to shared Web components.

Run from the repository root:

    python manual_sources/JE-100C/US/en/git-20261027-18058b6b/build_content.py

Every Web string comes from ``source/transcription.json`` by line id; this
module only decides which shared component carries each printed block, in
printed order. It writes ``source/en/content.json``, the frozen input that
``rebuild.py`` replays. ``source_manifest.json:component_map`` lists the map
and ``source/differences.md`` every deliberate layout difference.
"""
from __future__ import annotations

from html import escape
import json
from pathlib import Path
import sys

from bs4 import BeautifulSoup

PACKAGE = Path(__file__).resolve().parent
ROOT = next(parent for parent in PACKAGE.parents if (parent / "build.py").is_file())
sys.path.insert(0, str(ROOT))

from tools.component_specs.fcc import fcc_component_spec, fcc_semantic_projection  # noqa: E402
from tools.component_specs.inbox import inbox_component_spec  # noqa: E402
from tools.component_specs.manual_tables import lcd_icon_component_spec  # noqa: E402
from tools.component_specs.reference_figure import reference_figure_component_spec  # noqa: E402
from tools.component_specs.spec_table import spec_table_component_spec  # noqa: E402
from tools.component_specs.warranty import warranty_section_component_spec  # noqa: E402
from tools.manual_ir.components import component_flow_node  # noqa: E402
from tools.web.composite_hashing import reference_source_fragment_sha256  # noqa: E402
from tools.web.frozen_ai_flow import node, root, table, text  # noqa: E402

LANGUAGE = "en"
SOURCE_SHA256 = "18058b6bb7e83041fce1798f3baf98a018d079fa5caa6fd8dceec934df02c0b5"
MARKS = {"strong": "strong", "sub": "subscript", "sup": "superscript"}


class Lines:
    """Line lookup that records every id used, so coverage can be checked."""

    def __init__(self) -> None:
        source = json.loads((PACKAGE / "source/transcription.json").read_text(encoding="utf-8"))
        self.rows = {line["id"]: line for page in source["pages"] if page["web"] for line in page["lines"]}
        self.used: list[str] = []

    def __call__(self, key: str) -> str:
        if key in self.used:
            raise ValueError("transcription line bound twice: " + key)
        self.used.append(key)
        return self.rows[key]["text"]

    def spans(self, key: str) -> list[tuple[str, str | None]]:
        """(text, mark) runs: printed bold, subscript and superscript spans in order."""
        row = self.rows[key]
        marks = [(span, kind) for kind in MARKS for span in row.get(kind, [])]
        runs: list[tuple[str, str | None]] = [(self(key), None)]
        for span, kind in marks:
            for index, (value, mark) in enumerate(runs):
                if mark is None and span in value:
                    before, after = value.split(span, 1)
                    runs[index:index + 1] = [r for r in ((before, None), (span, kind), (after, None)) if r[0]]
                    break
            else:
                raise ValueError(f"{key}: printed span not found: {span}")
        return runs

    def inline(self, key: str) -> list[dict]:
        return [text(value) if mark is None else node(MARKS[mark], [text(value)]) for value, mark in self.spans(key)]

    def html(self, key: str) -> str:
        tags = {"strong": "strong", "sub": "sub", "sup": "sup"}
        return "".join(escape(value) if mark is None else f"<{tags[mark]}>{escape(value)}</{tags[mark]}>"
                       for value, mark in self.spans(key))


T = Lines()


def para(key: str) -> dict:
    return root(node("paragraph", T.inline(key)))


def strong_para(key: str) -> dict:
    return root(node("paragraph", [node("strong", [text(T(key))])]))


def heading(key: str, level: int = 3, anchor: str | None = None) -> dict:
    return root(node("heading", [text(T(key))], level=level, **({"anchor": anchor} if anchor else {})))


def chapter(key: str, anchor: str) -> dict:
    return heading(key, level=2, anchor=anchor)


def bullets(keys: list[str]) -> dict:
    return root(node("list", [node("list_item", [node("paragraph", T.inline(k))]) for k in keys], ordered=False))


def group(children: list[dict], css: str) -> dict:
    return root(node("group", children, role="container", presentation={"html": {"attributes": {"class": css}}}))




def fragment_sha256(ref: str, reference_id: str, alt: str) -> str:
    """The shared renderer's source-fragment hash of a captionless semantic image."""
    soup = BeautifulSoup("", "html.parser")
    semantic = soup.new_tag("div", attrs={"class": "hb-reference-semantic",
                                          "data-reference-id": f"{reference_id}.semantic"})
    semantic.append(soup.new_tag("img", attrs={"alt": alt, "class": "hb-reference-art", "src": ref}))
    return reference_source_fragment_sha256(
        component={"id": reference_id, "image_key": reference_id, "captions_embedded": True},
        semantic=semantic, caption_labels=[], composite_locale=None)


def figure(ref: str, reference_id: str, page: int, label_keys: list[str], label: str | None = None) -> dict:
    """Complete source panel; printed labels stay in the art and the alt text."""
    labels = [T(key) for key in label_keys]
    alt = label or " / ".join(labels)
    spec = reference_figure_component_spec(
        reference_id=reference_id, accessibility_label=alt, caption_mode="embedded",
        captions=(), adjacent_copy=None, source_art_ref=ref, source_art_locale_policy="exact",
        source_fragment_sha256=fragment_sha256(ref, reference_id, alt),
        source_ref=f"native-pdf/page-{page}/{reference_id}", language=LANGUAGE, image_key=reference_id,
        metadata={"embedded_labels": labels, "physical_page": page},
    )
    return component_flow_node(spec, carrier_flow=(root(node("image", source=ref, alt=alt)),), root=True)






def pair(value: str, key: str) -> dict:
    return {f"{key}_html": escape(value), f"{key}_text": value}


def lcd_table(rows: list[tuple[str, list[str], str]], ref: str, numbered: bool, label: str) -> dict:
    """Printed LCD blocks: icon, bold title, description."""
    values, refs = [], []
    for index, (name_key, body_keys, asset) in enumerate(rows):
        name = T(name_key)
        html_lines, text_lines = [], []
        for key in body_keys:
            html_lines.append(T.html(key))
            text_lines.append(T.rows[key]["text"])
        description_html = "<br/>".join(html_lines)
        row = {**pair(name, "name"), "description_html": description_html,
               "description_text": " ".join(text_lines), "icon_alt": name, "asset_index": index}
        if numbered:
            row.update(pair(str(index + 1), "number"))
        values.append(row)
        refs.append(asset)
    spec = lcd_icon_component_spec(accessibility_label=label, rows=values, icon_refs=refs, source_ref=ref,
                                   language=LANGUAGE, icon_locale_policy="exact", numbered=numbered)
    return component_flow_node(spec, root=True)


def spec_carrier(spec) -> list[dict]:
    slot = lambda role: spec.slot(role).content  # noqa: E731
    title = node("heading", [node("inline_group", [text(slot("section_title"))],
                                  presentation={"html": {"attributes": {"class": "hb-spec-section-text"}}})],
                 level=2, presentation={"html": {"attributes": {"class": "hb-spec-section hb-spec-group"}}})
    rows = [[node("table_cell", [text(r["label"] if i == 0 else "")], header=True),
             node("table_cell", [text(v["text"])], header=False)]
            for r in slot("rows") for i, v in enumerate(r["values"])]
    return [title, table(rows)]


def spec_block(title_key: str, rows: list[tuple[str, list[str]]], ref: str) -> dict:
    """One printed ● spec table; a multi-line value continues under the same label."""
    title = T(title_key)
    flat = []
    for label_key, value_keys in rows:
        label = T(label_key)
        flat += [(label if i == 0 else "", T(k)) for i, k in enumerate(value_keys)]
    spec = spec_table_component_spec(section_title=title, rows=flat, source_ref=ref, language=LANGUAGE)
    return component_flow_node(spec, carrier_flow=spec_carrier(spec), root=True)


# --- chapters -------------------------------------------------------------

def introduction() -> list[dict]:
    # The dark print band carries 「US English」 and 「Model: JE-100A」 as one chapter strip.
    band = root(node("heading", [text(T("intro.lang")), text(" "), text(T("intro.model"))], level=2,
                     anchor="native-introduction"))
    specs = spec_block("spec.h", [(f"spec.r{i}.l", [f"spec.r{i}.v"]) for i in range(1, 19)],
                       "native-pdf/page-2/specifications")
    certifications = ["fig.cert.ul1", "fig.cert.csa", "fig.cert.ul2", "fig.cert.intertek"]
    return [band, para("intro.p1"), para("intro.p2"), para("intro.p3"), specs,
            heading("cert.h"), figure("assets/certifications.png", "certifications", 2, certifications),
            para("spec.tm")]


def package_list() -> list[dict]:
    cards = [{"image_ref": ref, "label": T(key), "alt": T.rows[key]["text"]}
             for key, ref in (("box.c1", "assets/inbox-unit.png"), ("box.c2", "assets/inbox-cable.png"),
                              ("box.c3", "assets/inbox-manual.png"))]
    title = T.rows["box.h"]["text"]
    spec = inbox_component_spec(accessibility_label=title, cards=cards, tip_label="", tip_body="",
                                source_ref="native-pdf/page-3/inbox", language=LANGUAGE, require_tip=False,
                                variant="responsive-card-grid")
    carrier = table([[node("table_cell", [node("image", source=c["image_ref"], alt=c["alt"]),
                                          node("paragraph", [text(c["label"])])], header=False) for c in cards]])
    return [chapter("box.h", "native-package-list"), component_flow_node(spec, carrier_flow=(carrier,), root=True)]


def overview() -> list[dict]:
    keys = ["names.lcd", "names.display", "names.usba", "names.usbc1", "names.usbc2", "names.usbc"]
    return [chapter("ov.h", "native-get-to-know-your-gear"), heading("ov.sub"),
            figure("assets/overview.png", "overview", 3, keys)]


def lcd() -> list[dict]:
    map_labels = [f"fig.lcd.n{i}" for i in range(1, 10)]
    first = [("lcd.ring.t", ["lcd.ring.b"], "assets/lcd-battery-ring.png"),
             ("lcd.low.t", ["lcd.low.b"], "assets/lcd-low-battery.png"),
             ("lcd.aod.t", ["lcd.aod.b"], "assets/lcd-always-on.png"),
             ("lcd.eco.t", ["lcd.eco.b"], "assets/lcd-energy-saving.png")]
    second = [("lcd.fault.t", ["lcd.fault.b"], "assets/shared-lcd/25_Fault_code_LaTmb4IQYo3vwvxMqQNcC2RgnIf.png"),
              ("lcd.ht.t", ["lcd.ht.b"], "assets/lcd-high-temperature.png"),
              ("lcd.lt.t", ["lcd.lt.b"], "assets/lcd-low-temperature.png")]
    label = T.rows["lcd.h"]["text"]
    return [chapter("lcd.h", "native-lcd-display"),
            figure("assets/lcd-map.png", "lcd-map", 3, map_labels),
            lcd_table(first, "native-pdf/page-4/lcd-icons-1", False, label),
            heading("lcd.eco.on.h"), para("lcd.eco.on"), heading("lcd.eco.off.h"), para("lcd.eco.off"),
            lcd_table(second, "native-pdf/page-4/lcd-icons-2", False, label)]


def operations() -> list[dict]:
    return [chapter("ops.h", "native-basic-operations"), heading("ops.lcd.h"),
            para("ops.lcd.p1"), para("ops.lcd.p2"), para("ops.lcd.p3"), para("ops.lcd.tip")]


def charging() -> list[dict]:
    return [chapter("chg.h", "native-charging"),
            heading("chg.wall.h"), para("chg.wall.p"),
            figure("assets/charging-wall.png", "charging-wall", 5, ["fig.wall.cable", "fig.wall.unit"]),
            heading("chg.solar.h"), heading("chg.solar.g1.h", level=4), para("chg.solar.g1.p"),
            figure("assets/solar-100.png", "solar-100", 5,
                   ["fig.solar1.adaptor", "fig.solar1.male", "fig.solar1.port", "fig.solar1.panel", "fig.solar1.unit"]),
            heading("chg.solar.g2.h", level=4), para("chg.solar.g2.p80"),
            figure("assets/solar-80.png", "solar-80", 6,
                   ["fig.solar80.port", "fig.solar80.dc", "fig.solar80.panel", "fig.solar80.adaptor"]),
            para("chg.solar.g2.p40"),
            figure("assets/solar-40.png", "solar-40", 6,
                   ["fig.solar40.port", "fig.solar40.panel", "fig.solar40.dc", "fig.solar40.adaptor"]),
            heading("chg.car.h"), para("chg.car.p1"), para("chg.car.p2"),
            figure("assets/charging-car.png", "charging-car", 6, ["fig.car.unit", "fig.car.vehicle"])]


def charging_safety() -> list[dict]:
    return [chapter("chg.safe.h", "native-safety-charging"), para("chg.safe.l1"), para("chg.safe.l2")]


def fcc_carrier(spec) -> list[dict]:
    payload = fcc_semantic_projection(spec)
    result = [node("paragraph", [text(v)]) for v in payload["opening_copy"]]
    for block in payload["left_blocks"] + payload["right_blocks"]:
        if block["kind"] == "list":
            result.append(node("list", [node("list_item", [text(v)]) for v in block["items"]], ordered=False))
        else:
            result.append(node("paragraph", [text(" ".join(filter(None, [block.get("label"), block["text"]])))]))
    return result


def using_safety() -> list[dict]:
    note_label, note_body = T("fcc.p").split(" ", 1)
    mod_label, mod_body = T("fcc.mod").split(" ", 1)
    fcc = fcc_component_spec(
        accessibility_label="FCC", opening_copy=[], mark_asset_ref="assets/fcc-mark.svg",
        left_blocks=[{"kind": "paragraph", "label": note_label, "text": note_body}],
        right_blocks=[{"kind": "list", "items": [T(f"fcc.l{i}") for i in range(1, 5)]},
                      {"kind": "paragraph", "label": mod_label, "text": mod_body}],
        source_ref="native-pdf/page-7/fcc", language=LANGUAGE)
    items = ["use.a", "use.b", "use.c", "use.d", "use.e", "use.f", "use.g", "use.h2", "use.i", "use.j"]
    return [chapter("use.h", "native-safety-using"), para("use.lead"), *(para(k) for k in items),
            group([component_flow_node(fcc, carrier_flow=fcc_carrier(fcc))], "hb-fcc-statement")]


def instructions() -> list[dict]:
    items = ["ins.a", "ins.b", "ins.c", "ins.d", "ins.e", "ins.f", "ins.g", "ins.h2", "ins.i", "ins.j", "ins.k"]
    return [chapter("ins.h", "native-important-safety-instructions"), heading("ins.sub"), para("ins.warn"),
            *(para(k) for k in items), heading("ins.save"), para("ins.caution1"), para("ins.caution2"),
            heading("op.h"), bullets([f"op.l{i}" for i in range(1, 9)])]


def warranty() -> list[dict]:
    def section(index: int, title_key: str, keys: list[str]) -> list[dict]:
        # The shared card draws the body; the printed sub-heading is the heading before it.
        title = heading(title_key)
        blocks = [{"kind": "paragraph", "html": f"<p>{T.html(k)}</p>", "text": T.rows[k]["text"]} for k in keys]
        spec = warranty_section_component_spec(title=T.rows[title_key]["text"], section_index=index, blocks=blocks,
                                               source_ref=f"native-pdf/page-9/warranty-{index}", language=LANGUAGE)
        return [title, component_flow_node(spec, root=True)]

    def contact(title_key: str, keys: list[str]) -> dict:
        return group([node("paragraph", [node("strong", [text(T(title_key))])]),
                      *(node("paragraph", [text(T(k))]) for k in keys)], "hb-text-panel")

    return [chapter("war.h", "native-warranty"), para("war.lead1"), para("war.lead2"),
            *section(1, "war.limited.h", ["war.limited.p1", "war.limited.p2"]),
            *section(2, "war.period.h", ["war.period.p"]),
            *section(3, "war.exchange.h", ["war.exchange.p"]),
            *section(4, "war.buyer.h", ["war.buyer.p"]),
            *section(5, "war.excl.h", ["war.excl.lead", "war.excl.l1", "war.excl.l2", "war.excl.l3", "war.excl.l4"]),
            contact("contact.us.h", ["contact.us.addr", "contact.us.tel", "contact.us.mail", "contact.us.web"]),
            contact("contact.mx.h", ["contact.mx.addr"])]


CHAPTERS = (
    ("introduction", "US English Model: JE-100A", introduction), ("package_list", "PACKAGE LIST", package_list),
    ("product_overview", "GET TO KNOW YOUR GEAR", overview), ("lcd_display", "LCD DISPLAY", lcd),
    ("basic_operations", "BASIC OPERATIONS", operations),
    ("charging", "CHARGING YOUR JACKERY EXPLORER 100 PLUS", charging),
    ("safety_charging", "SAFETY PRECAUTIONS WHEN CHARGING", charging_safety),
    ("safety_using", "SAFETY PRECAUTIONS WHEN USING", using_safety),
    ("important_safety_instructions", "INSTRUCTIONS PERTAINING TO RISK OF FIRE, ELECTRIC SHOCK, OR INJURY TO PERSONS",
     instructions),
    ("warranty", "WARRANTY", warranty),
)


def build() -> dict:
    chapters = [{"id": cid, "title": title, "nodes": make()} for cid, title, make in CHAPTERS]
    missing = [k for k in T.rows if k not in T.used]
    if missing:
        raise ValueError("Web transcription lines not bound: " + ", ".join(missing))
    return {"model": "JE-100A", "region": "US", "language": LANGUAGE,
            "title": "Jackery Explorer 100 Plus User Manual", "source_sha256": SOURCE_SHA256, "chapters": chapters}


def main() -> None:
    content = build()
    path = PACKAGE / "source/en/content.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(content, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"chapters": [c["id"] for c in content["chapters"]], "lines": len(T.used)}))


if __name__ == "__main__":
    main()
