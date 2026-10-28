"""Bind the reviewed JE-240B US English transcription to shared Web components.

Run from the repository root:

    python manual_sources/JE-240B/US/en/git-20261027-3dc1fbba/build_content.py

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

from tools.component_specs.callout import display_label  # noqa: E402
from tools.component_specs.fcc import fcc_component_spec, fcc_semantic_projection  # noqa: E402
from tools.component_specs.inbox import inbox_component_spec  # noqa: E402
from tools.component_specs.lcd_mode import lcd_mode_component_spec  # noqa: E402
from tools.component_specs.manual_tables import (  # noqa: E402
    lcd_icon_component_spec, symbol_icon_component_spec, symbol_signal_component_spec,
    troubleshooting_component_spec,
)
from tools.component_specs.reference_figure import reference_figure_component_spec  # noqa: E402
from tools.component_specs.spec_table import spec_table_component_spec  # noqa: E402
from tools.component_specs.warranty import (  # noqa: E402
    warranty_lead_component_spec, warranty_section_component_spec, warranty_years_component_spec,
)
from tools.manual_ir.components import component_flow_node  # noqa: E402
from tools.web.composite_hashing import reference_source_fragment_sha256  # noqa: E402
from tools.web.frozen_ai_flow import callout, node, root, table, text  # noqa: E402

LANGUAGE = "en"
SOURCE_SHA256 = "3dc1fbbaf28908f216955e32de05b88dc9b0477854e8c0b5df7926a542572521"
MARKS = {"strong": "strong", "sub": "subscript", "sup": "superscript"}


class Lines:
    """Line lookup that records every id used, so coverage can be checked."""

    def __init__(self) -> None:
        source = json.loads((PACKAGE / "source/transcription.json").read_text(encoding="utf-8"))
        self.rows = {line["id"]: line for page in source["pages"] if page["web"]
                     for line in page["lines"] if line.get("web", True)}
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


def list_item(key: str, children: list[str] = ()) -> dict:
    body = [node("paragraph", T.inline(key))]
    if children:
        body.append(node("list", [node("list_item", [node("paragraph", T.inline(k))]) for k in children],
                         ordered=False))
    return node("list_item", body)


def bullets(keys: list[str | tuple[str, list[str]]]) -> dict:
    items = [list_item(k) if isinstance(k, str) else list_item(*k) for k in keys]
    return root(node("list", items, ordered=False))


def group(children: list[dict], css: str) -> dict:
    return root(node("group", children, role="container", presentation={"html": {"attributes": {"class": css}}}))


def sold_separately(key: str) -> dict:
    """Printed cart pill: shared ``hb-source-purchase`` strip, cart mark reused from the JE-100C EU edition."""
    return group([node("image", source="assets/sold-separately.png", alt="Sold separately"),
                  node("paragraph", [node("strong", [text(T(key))])])], "hb-source-purchase")


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
    alt = " / ".join(labels) if not label else (f"{label}: {' / '.join(labels)}" if labels else label)
    spec = reference_figure_component_spec(
        reference_id=reference_id, accessibility_label=alt, caption_mode="embedded",
        captions=(), adjacent_copy=None, source_art_ref=ref, source_art_locale_policy="exact",
        source_fragment_sha256=fragment_sha256(ref, reference_id, alt),
        source_ref=f"native-pdf/page-{page}/{reference_id}", language=LANGUAGE, image_key=reference_id,
        metadata={"embedded_labels": labels, "physical_page": page},
    )
    return component_flow_node(spec, carrier_flow=(root(node("image", source=ref, alt=alt)),), root=True)


def callout_items(label_key: str, item_keys: list[str], variant: str, ref: str) -> dict:
    label = display_label(T(label_key))
    body = [node("list", [node("list_item", T.inline(k)) for k in item_keys], ordered=False)]
    return root(callout(label, body, variant=variant, language=LANGUAGE, source_ref=ref))


def callout_text(label_key: str, body_keys: list[str], variant: str, ref: str) -> dict:
    label = display_label(T(label_key))
    body = [node("paragraph", T.inline(k)) for k in body_keys]
    return root(callout(label, body, variant=variant, language=LANGUAGE, source_ref=ref))


def pair(value: str, key: str) -> dict:
    return {f"{key}_html": escape(value), f"{key}_text": value}


def html_pair(keys: list[str], key: str) -> dict:
    """Printed lines of one cell; print line breaks kept as <br/>."""
    html = "<br/>".join(T.html(k) for k in keys)
    return {f"{key}_html": html, f"{key}_text": " ".join(T.rows[k]["text"] for k in keys)}


def lcd_table(rows: list[tuple[str, str, list[str], str]], ref: str, label: str) -> dict:
    """Printed LCD rows: circled number, icon, bold name, description lines."""
    values, refs = [], []
    for index, (number, name_key, body_keys, asset) in enumerate(rows):
        name = T(name_key)
        values.append({**pair(number, "number"), **pair(name, "name"), **html_pair(body_keys, "description"),
                       "icon_alt": name, "asset_index": index})
        refs.append(asset)
    spec = lcd_icon_component_spec(accessibility_label=label, rows=values, icon_refs=refs, source_ref=ref,
                                   language=LANGUAGE, icon_locale_policy="exact", numbered=True)
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

def important() -> list[dict]:
    return [chapter("intro.h", "native-important"), para("intro.p1"), para("intro.p2"), para("intro.p3")]


def safety() -> list[dict]:
    return [chapter("safety.h", "native-safety"),
            heading("safety.risk"),
            callout_text("safety.warn.l", ["safety.warn.b"], "warning", "native-pdf/page-4/warning"),
            bullets([f"safety.l{i}" for i in range(1, 12)]),
            heading("opi.h"), strong_para("safety.save"),
            bullets(["opi.l1", ("opi.l2", ["opi.l2.s1", "opi.l2.s2"]), ("opi.l3", ["opi.l3.s1", "opi.l3.s2"]),
                     *(f"opi.l{i}" for i in range(4, 13))]),
            callout_text("danger.l", ["danger.b1", "danger.b2"], "danger", "native-pdf/page-4/danger"),
            heading("maint.h"), para("maint.p")]


SYMBOLS = [("sym.warning", "assets/symbol-01.svg"), ("sym.manual", "assets/symbol-02.svg"),
           (("sym.weee1", "sym.weee2"), "assets/symbol-03.png"), ("sym.shock", "assets/symbol-04.svg"),
           ("sym.dismantle", "assets/symbol-05.svg"), ("sym.fire", "assets/symbol-06.svg"),
           ("sym.children", "assets/symbol-07.svg"), ("sym.liion", "assets/symbol-08.svg"),
           ("sym.charging", "assets/symbol-09.svg"), ("sym.explosive", "assets/symbol-10.svg")]


def fcc_carrier(spec) -> list[dict]:
    payload = fcc_semantic_projection(spec)
    result = [node("paragraph", [text(v)]) for v in payload["opening_copy"]]
    for block in payload["left_blocks"] + payload["right_blocks"]:
        if block["kind"] == "list":
            result.append(node("list", [node("list_item", [text(v)]) for v in block["items"]], ordered=False))
        else:
            result.append(node("paragraph", [text(" ".join(filter(None, [block.get("label"), block["text"]])))]))
    return result


def symbols() -> list[dict]:
    headers2 = [pair(T(k), "content") for k in ("signal.th1", "signal.th2")]
    signal = symbol_signal_component_spec(
        accessibility_label=T.rows["sym.h"]["text"], headers=headers2,
        rows=[{"label": T(f"signal.{k}.l"), "show_icon": k in ("warn", "caut"), **pair(T(f"signal.{k}.m"), "meaning")}
              for k in ("warn", "caut", "note", "tip")],
        source_ref="native-pdf/page-5/signal", language=LANGUAGE)
    headers4 = [pair(T(k), "content") for k in ("symbols.th1", "symbols.th2", "symbols.th3", "symbols.th4")]
    meanings = []
    for keys, _ in SYMBOLS:
        keys = (keys,) if isinstance(keys, str) else keys
        values = [T(k) for k in keys]
        meanings.append({"meaning_html": "<br/>".join(escape(v) for v in values), "meaning_text": " ".join(values),
                         "icon_alt": " ".join(values)})
    icons = symbol_icon_component_spec(
        accessibility_label=T.rows["sym.h"]["text"], headers=headers4,
        panels=[[{"asset_index": i, **meanings[i]} for i in rows] for rows in ((0, 1, 2, 3), (4, 5, 6, 7, 8, 9))],
        icon_refs=[ref for _, ref in SYMBOLS], source_ref="native-pdf/page-5/symbols", language=LANGUAGE)
    note_label, note_body = T("fcc.note").split(" ", 1)
    mod_label, mod_body = T("fcc.mod").split(" ", 1)
    fcc = fcc_component_spec(
        accessibility_label="FCC", opening_copy=[T("fcc.p1")], mark_asset_ref="assets/fcc-mark.svg",
        left_blocks=[{"kind": "paragraph", "label": note_label, "text": note_body}],
        right_blocks=[{"kind": "paragraph", "label": "", "text": T("fcc.p3")},
                      {"kind": "list", "items": [T(f"fcc.l{i}") for i in range(1, 5)]},
                      {"kind": "paragraph", "label": mod_label, "text": mod_body}],
        source_ref="native-pdf/page-5/fcc", language=LANGUAGE)
    return [chapter("sym.h", "native-symbols"),
            component_flow_node(signal, root=True), component_flow_node(icons, root=True),
            group([component_flow_node(fcc, carrier_flow=fcc_carrier(fcc))], "hb-fcc-statement")]


def in_the_box() -> list[dict]:
    cards = [{"image_ref": ref, "label": T(key), "alt": T.rows[key]["text"]}
             for key, ref in (("box.c1", "assets/inbox-unit.png"), ("box.c2", "assets/inbox-cable.png"),
                              ("box.c3", "assets/inbox-manual.png"))]
    title = T.rows["box.h"]["text"]
    tip_label, tip_body = display_label(T("box.tip.l")), T("box.tip.b")
    spec = inbox_component_spec(accessibility_label=title, cards=cards, tip_label=tip_label, tip_body=tip_body,
                                source_ref="native-pdf/page-6/inbox", language=LANGUAGE, require_tip=True,
                                variant="responsive-card-grid")
    carrier = [table([[node("table_cell", [node("image", source=c["image_ref"], alt=c["alt"]),
                                           node("paragraph", [text(c["label"])])], header=False) for c in cards]]),
               table([[node("table_cell", [text(tip_label)], header=False),
                       node("table_cell", [text(tip_body)], header=False)]])]
    return [chapter("box.h", "native-in-the-box"), component_flow_node(spec, carrier_flow=carrier, root=True)]


def overview() -> list[dict]:
    keys = ["names.lcd", "names.power", "names.usba", "names.usba.v", "names.dc", "names.dc.v1", "names.dc.v2",
            "names.dc.v3", "names.usbc2", "names.usbc2.v", "names.usbc3", "names.usbc3.v", "names.handle",
            "names.usbc1", "names.usbc1.v"]
    straps = T.rows["ov.straps"]["text"]
    return [chapter("ov.h", "native-product-overview"), heading("ov.front"),
            figure("assets/overview.png", "overview", 6, keys), sold_separately("ov.straps"),
            figure("assets/strap.png", "strap", 7, [], label=straps)]


def lcd() -> list[dict]:
    rows = [("1", "lcd.i1.n", ["lcd.i1.d"], "assets/lcd-input-power.png"),
            ("2", "lcd.i2.n", ["lcd.i2.d"], "assets/lcd-usbc-charging.png"),
            ("3", "lcd.i3.n", ["lcd.i3.d"], "assets/lcd-car-charging.png"),
            ("4", "lcd.i4.n", ["lcd.i4.d"], "assets/lcd-solar-charging.png"),
            ("5", "lcd.i5.n", ["lcd.i5.d"], "assets/lcd-battery-ring.png"),
            ("6", "lcd.i6.n", ["lcd.i6.d"], "assets/lcd-battery-percentage.png"),
            ("7", "lcd.i7.n", ["lcd.i7.d1", "lcd.i7.d2"], "assets/lcd-energy-saving.png"),
            # Printed number 8 spans the high and low temperature rows.
            ("8", "lcd.ht.n", ["lcd.ht.d"], "assets/lcd-high-temperature.png"),
            ("8", "lcd.lt.n", ["lcd.lt.d"], "assets/lcd-low-temperature.png"),
            ("9", "lcd.f.n", ["lcd.f.d"], "assets/lcd-fault-code.png"),
            ("10", "lcd.i10.n", ["lcd.i10.d"], "assets/lcd-output-power.png")]
    title = T.rows["lcd.h"]["text"]
    return [chapter("lcd.h", "native-lcd-display"),
            figure("assets/lcd-map.png", "lcd-map", 7, [], label=title),
            lcd_table(rows, "native-pdf/page-7/lcd", title)]


def operations() -> list[dict]:
    groups = []
    for g in ("op.lcd.g1", "op.lcd.g2"):
        actions = [{**pair(T(f"{g}.a{i}"), "action"), **pair(T(f"{g}.d{i}"), "description")} for i in (1, 2, 3)]
        groups.append({**pair(T(g), "state"), "actions": actions})
    title = T.rows["op.lcd.h"]["text"]
    screen = lcd_mode_component_spec(accessibility_label=title, groups=groups, artwork_ref="assets/lcd-screen.png",
                                     source_ref="native-pdf/page-9/lcd-screen", language=LANGUAGE,
                                     artwork_locale_policy="exact")
    return [chapter("op.h", "native-operations"),
            heading("op.pwr.h"),
            figure("assets/power-on-off.png", "power-on-off", 8,
                   ["fig.pwr.on", "fig.pwr.on.d", "fig.pwr.off", "fig.pwr.off.d"], label=T.rows["op.pwr.h"]["text"]),
            heading("op.usb.h"), para("op.usb.p"),
            figure("assets/usb-output.png", "usb-output", 9,
                   ["fig.usb.on", "fig.usb.on.d", "fig.usb.off", "fig.usb.off.d"], label=T.rows["op.usb.h"]["text"]),
            para("op.usb.c1"), para("op.usb.c2"), para("op.usb.c3"),
            heading("op.eco.h", level=4), para("op.eco.p1"), para("op.eco.p2"),
            callout_items("op.eco.note.l", ["op.eco.note.i1", "op.eco.note.i2"], "note", "native-pdf/page-9/note"),
            heading("op.lcd.h"), component_flow_node(screen, root=True)]


def troubleshooting() -> list[dict]:
    headers = [pair(T(k), "content") for k in ("trbl.th1", "trbl.th2")]
    rows = []
    for code in range(10):
        key = f"trbl.f{code}"
        measures = [f"{key}.m1", f"{key}.m2", f"{key}.m3"] if code == 7 else [f"{key}.m"]
        rows.append({**pair(T(f"{key}.c"), "code"), **html_pair(measures, "measures")})
    spec = troubleshooting_component_spec(headers=headers, rows=rows, source_ref="native-pdf/page-10/troubleshooting",
                                          language=LANGUAGE)
    return [chapter("trbl.h", "native-troubleshooting"), para("trbl.p"), component_flow_node(spec, root=True)]


def charging() -> list[dict]:
    return [chapter("chg.h", "native-charging"), para("chg.green"), strong_para("chg.first"),
            callout_items("chg.note.l", ["chg.note.i1", "chg.note.i2"], "note", "native-pdf/page-10/note"),
            heading("chg.usbc.h"), para("chg.usbc.p"),
            figure("assets/charging-usbc.png", "charging-usbc", 11, ["fig.usbc.s1", "fig.usbc.s2"],
                   label=T.rows["chg.usbc.h"]["text"]),
            para("chg.usbc.after"),
            heading("chg.solar.h"), para("chg.solar.p"),
            figure("assets/charging-solar.png", "charging-solar", 11, ["fig.solar.panel"]),
            para("chg.solar.rec"),
            heading("chg.car.h"), para("chg.car.p"),
            figure("assets/charging-car.png", "charging-car", 12, ["fig.car.vehicle"]),
            para("chg.car.sold"),
            callout_items("chg.car.caution.l", ["chg.car.caution.i1", "chg.car.caution.i2", "chg.car.caution.i3"],
                          "caution", "native-pdf/page-12/caution")]


def storage() -> list[dict]:
    return [chapter("sto.h", "native-storage"), para("sto.p1"), bullets(["sto.l1", "sto.l2", "sto.l3"]),
            para("sto.p2")]


def specifications() -> list[dict]:
    g = "spec.gen.r"
    o = "spec.out.r"
    return [chapter("spec.h", "native-specifications"),
            spec_block("spec.gen.h", [(f"{g}{i}.l", [f"{g}{i}.v"]) for i in range(1, 8)], "native-pdf/page-13/general"),
            spec_block("spec.in.h", [("spec.in.r1.l", ["spec.in.r1.v"]),
                                     ("spec.in.r2.l", ["spec.in.r2.v1", "spec.in.r2.v2"])], "native-pdf/page-13/input"),
            spec_block("spec.out.h", [(f"{o}{i}.l", [f"{o}{i}.v"]) for i in range(1, 5)]
                       + [(f"{o}5.l", [f"{o}5.v{i}" for i in range(1, 7)]),
                          (f"{o}6.l", [f"{o}6.v{i}" for i in range(1, 5)]),
                          (f"{o}7.l", [f"{o}7.v"])], "native-pdf/page-13/output"),
            spec_block("spec.env.h", [(f"spec.env.r{i}.l", [f"spec.env.r{i}.v"]) for i in (1, 2)],
                       "native-pdf/page-13/environment"),
            para("spec.tm"), para("spec.thermal")]


def warranty() -> list[dict]:
    def p(*keys: str) -> dict:
        return {"kind": "paragraph", "html": "<p>" + "<br/>".join(T.html(k) for k in keys) + "</p>",
                "text": " ".join(T.rows[k]["text"] for k in keys)}

    def ul(*keys: str) -> dict:
        items = [T(k) for k in keys]
        return {"kind": "list", "items": items,
                "html": "<ul>" + "".join(f"<li>{escape(i)}</li>" for i in items) + "</ul>"}

    def section(index: int, title_key: str, blocks: list[dict]) -> list[dict]:
        # The shared card draws the body; its printed title pill is the heading before it.
        title = heading(title_key)
        spec = warranty_section_component_spec(title=T.rows[title_key]["text"], section_index=index, blocks=blocks,
                                               source_ref=f"native-pdf/page-14/warranty-{index}", language=LANGUAGE)
        return [title, component_flow_node(spec, root=True)]

    lead = warranty_lead_component_spec(accessibility_label=T.rows["war.h"]["text"],
                                        lead_html=T.html("war.lead"), local_note_html=T.html("war.local"),
                                        source_ref="native-pdf/page-14/lead", language=LANGUAGE)
    periods = [{"number": T(f"{y}.n"), "unit": T(f"{y}.unit"), "label": T(f"{y}.label"),
                "body_html": f"<p>{T.html(f'{y}.b')}</p>", "body_text": T.rows[f"{y}.b"]["text"]}
               for y in ("war.y1", "war.y2")]
    years = warranty_years_component_spec(title=T.rows["war.period.h"]["text"], periods=periods,
                                          source_ref="native-pdf/page-14/warranty-period", language=LANGUAGE)
    contact = group([node("paragraph", [node("strong", [text(T("back.company"))])]),
                     *(node("paragraph", [text(T(k))]) for k in ("back.address", "back.tel", "back.mail", "back.web"))],
                    "hb-text-panel")
    sections = [chapter("war.h", "native-warranty"), component_flow_node(lead, root=True)]
    sections += section(1, "war.lim.h", [p(k) for k in ("war.lim.p1", "war.lim.p2")])
    sections += [heading("war.period.h"), component_flow_node(years, root=True)]
    sections += section(3, "war.repair.h", [p("war.repair.p")])
    sections += section(4, "war.buyer.h", [p("war.buyer.p")])
    sections += section(5, "war.excl.h", [p("war.excl.lead"), ul(*(f"war.excl.l{i}" for i in range(1, 5)))])
    sections += section(6, "war.interp.h", [p("war.interp.p")])
    return [*sections, contact]


CHAPTERS = (
    ("important", "IMPORTANT:", important),
    ("safety", "IMPORTANT SAFETY INFORMATION", safety), ("symbols", "MEANING OF SYMBOLS", symbols),
    ("in_the_box", "WHAT'S IN THE BOX", in_the_box), ("product_overview", "PRODUCT OVERVIEW", overview),
    ("lcd_display", "LCD DISPLAY", lcd), ("operations", "OPERATIONS", operations),
    ("troubleshooting", "TROUBLESHOOTING", troubleshooting), ("charging", "CHARGING", charging),
    ("storage", "STORAGE", storage), ("specifications", "SPECIFICATIONS", specifications),
    ("warranty", "WARRANTY", warranty),
)


def build() -> dict:
    chapters = [{"id": cid, "title": title, "nodes": make()} for cid, title, make in CHAPTERS]
    missing = [k for k in T.rows if k not in T.used]
    if missing:
        raise ValueError("Web transcription lines not bound: " + ", ".join(missing))
    return {"model": "JE-240B", "region": "US", "language": LANGUAGE,
            "title": "Jackery Explorer 240D User Manual", "source_sha256": SOURCE_SHA256, "chapters": chapters}


def main() -> None:
    content = build()
    path = PACKAGE / "source/en/content.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(content, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"chapters": [c["id"] for c in content["chapters"]], "lines": len(T.used)}))


if __name__ == "__main__":
    main()
