"""Bind the reviewed JE-100C US English transcription to shared Web components.

Run from the repository root:

    python manual_sources/JE-100C/US/en/git-20261027-39c58bca/build_content.py

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
from tools.component_specs.manual_tables import (  # noqa: E402
    lcd_icon_component_spec, symbol_icon_component_spec, symbol_signal_component_spec,
)
from tools.component_specs.reference_figure import reference_figure_component_spec  # noqa: E402
from tools.component_specs.reference_table import reference_table_component_spec  # noqa: E402
from tools.component_specs.spec_table import spec_table_component_spec  # noqa: E402
from tools.component_specs.warranty import warranty_section_component_spec  # noqa: E402
from tools.manual_ir.components import component_flow_node  # noqa: E402
from tools.web.composite_hashing import reference_source_fragment_sha256  # noqa: E402
from tools.web.frozen_ai_flow import callout, node, root, table, text  # noqa: E402

LANGUAGE = "en"
SOURCE_SHA256 = "39c58bca661f635fc9d500bc9362317b62b5da6f007589fbf8e4ebfcc8e0bad0"
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


def sold_separately(key: str) -> dict:
    """Printed cart pill: shared ``hb-source-purchase`` strip, cart mark reused from the EU edition."""
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
    alt = label or " / ".join(labels)
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


def lcd_table(rows: list[tuple[str, list[str], str]], ref: str, numbered: bool, label: str) -> dict:
    """Printed LCD rows: icon, bold name, description lines (print breaks kept as <br/>)."""
    values, refs = [], []
    for index, (name_key, body_keys, asset) in enumerate(rows):
        name = T(name_key)
        html_lines, text_lines, items = [], [], []
        for key in body_keys:
            if key.endswith((".l1", ".l2", ".l3")) and key.startswith("lcd.h1."):
                items.append(T.html(key))
                text_lines.append(T.rows[key]["text"])
            else:
                html_lines.append(T.html(key))
                text_lines.append(T.rows[key]["text"])
        description_html = "<br/>".join(html_lines)
        if items:
            description_html += "<ul>" + "".join(f"<li>{item}</li>" for item in items) + "</ul>"
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

def safety() -> list[dict]:
    return [chapter("safety.h", "native-safety"),
            heading("safety.risk"),
            callout_text("safety.warn.l", ["safety.warn.b"], "warning", "native-pdf/page-3/warning"),
            bullets([f"safety.l{i}" for i in range(1, 13)]),
            heading("safety.save"),
            callout_text("safety.caution.l", ["safety.caution.b"], "caution", "native-pdf/page-3/caution"),
            para("safety.d1"), para("safety.d2"), para("safety.d3"),
            heading("maint.h"), para("maint.p")]


SYMBOLS = [("sym.warning", "assets/symbol-01.svg"), ("sym.manual", "assets/symbol-02.svg"),
           (("sym.weee1", "sym.weee2"), "assets/symbol-03.png"), ("sym.dismantle", "assets/symbol-04.svg"),
           ("sym.fire", "assets/symbol-05.svg"), ("sym.children", "assets/symbol-06.svg"),
           ("sym.liion", "assets/symbol-07.svg")]


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
        source_ref="native-pdf/page-4/signal", language=LANGUAGE)
    headers4 = [pair(T(k), "content") for k in ("symbols.th1", "symbols.th2", "symbols.th3", "symbols.th4")]
    meanings = []
    for keys, _ in SYMBOLS:
        keys = (keys,) if isinstance(keys, str) else keys
        values = [T(k) for k in keys]
        meanings.append({"meaning_html": "<br/>".join(escape(v) for v in values), "meaning_text": " ".join(values),
                         "icon_alt": " ".join(values)})
    icons = symbol_icon_component_spec(
        accessibility_label=T.rows["sym.h"]["text"], headers=headers4,
        panels=[[{"asset_index": i, **meanings[i]} for i in rows] for rows in ((0, 1, 2), (3, 4, 5, 6))],
        icon_refs=[ref for _, ref in SYMBOLS], source_ref="native-pdf/page-4/symbols", language=LANGUAGE)
    note_label, note_body = T("fcc.note").split(" ", 1)
    mod_label, mod_body = T("fcc.mod").split(" ", 1)
    fcc = fcc_component_spec(
        accessibility_label="FCC", opening_copy=[T("fcc.p1")], mark_asset_ref="assets/fcc-mark.svg",
        left_blocks=[{"kind": "paragraph", "label": note_label, "text": note_body}],
        right_blocks=[{"kind": "paragraph", "label": "", "text": T("fcc.p3")},
                      {"kind": "list", "items": [T(f"fcc.l{i}") for i in range(1, 5)]},
                      {"kind": "paragraph", "label": mod_label, "text": mod_body}],
        source_ref="native-pdf/page-4/fcc", language=LANGUAGE)
    return [chapter("sym.h", "native-symbols"),
            component_flow_node(signal, root=True), component_flow_node(icons, root=True),
            group([component_flow_node(fcc, carrier_flow=fcc_carrier(fcc))], "hb-fcc-statement")]


def in_the_box() -> list[dict]:
    cards = [{"image_ref": ref, "label": T(key), "alt": T.rows[key]["text"]}
             for key, ref in (("box.c1", "assets/inbox_unit.png"), ("box.c2", "assets/inbox_cable.png"),
                              ("box.c3", "assets/inbox_manual.png"))]
    title = T.rows["box.h"]["text"]
    spec = inbox_component_spec(accessibility_label=title, cards=cards, tip_label="", tip_body="",
                                source_ref="native-pdf/page-5/inbox", language=LANGUAGE, require_tip=False,
                                variant="responsive-card-grid")
    carrier = table([[node("table_cell", [node("image", source=c["image_ref"], alt=c["alt"]),
                                          node("paragraph", [text(c["label"])])], header=False) for c in cards]])
    return [chapter("box.h", "native-in-the-box"), component_flow_node(spec, carrier_flow=(carrier,), root=True)]


def overview() -> list[dict]:
    keys = ["names.handle", "names.lcd", "names.usbc", "names.usbc.in", "names.usbc.out", "names.usba",
            "names.usba.v", "names.display", "names.usbc2", "names.usbc2.v"]
    return [chapter("ov.h", "native-product-overview"), heading("ov.front"),
            figure("assets/overview.png", "overview", 5, keys), sold_separately("ov.straps")]


def lcd() -> list[dict]:
    a = "assets/shared-lcd/"
    interface1 = [("lcd.i1.n", ["lcd.i1.d"], a + "lcd_input.png"),
                  ("lcd.i2.n", ["lcd.i2.d"], a + "lcd_charge_time.png"),
                  ("lcd.i3.n", ["lcd.i3.d1", "lcd.i3.d2"], a + "lcd_steady.png"),
                  ("lcd.i4.n", ["lcd.i4.d1", "lcd.i4.d2"], a + "lcd_thermal.png"),
                  ("lcd.i5.n", ["lcd.i5.d1", "lcd.i5.d2"], a + "lcd_energy.png"),
                  ("lcd.i6.n", ["lcd.i6.d"], a + "lcd_ring.png"),
                  ("lcd.i7.n", ["lcd.i7.d1", "lcd.i7.d2", "lcd.i7.d3"], a + "lcd_low_battery.png"),
                  ("lcd.i8.n", ["lcd.i8.d"], a + "lcd_percentage.png"),
                  ("lcd.i9.n", ["lcd.i9.d"], a + "lcd_discharge_time.png"),
                  ("lcd.i10.n", ["lcd.i10.d"], a + "lcd_output.png")]
    states = [("lcd.f.n", ["lcd.f.d"], a + "lcd_fault.png"),
              ("lcd.ht.n", ["lcd.ht.d"], a + "lcd_high_temperature.png"),
              ("lcd.lt.n", ["lcd.lt.d"], a + "lcd_low_temperature.png")]
    interface2 = [("lcd.p1.n", ["lcd.p1.d"], a + "lcd_discharging.png"),
                  ("lcd.p2.n", ["lcd.p2.d"], a + "lcd_charging.png"),
                  ("lcd.p3.n", ["lcd.p3.d"], a + "lcd_watts.png")]
    interface3 = [("lcd.h1.n", ["lcd.h1.d", "lcd.h1.l1", "lcd.h1.l2", "lcd.h1.l3"], a + "lcd_health.png"),
                  ("lcd.h2.n", ["lcd.h2.d"], a + "lcd_temperature.png")]
    if1, if2, if3 = (T.rows[k]["text"] for k in ("lcd.if1", "lcd.if2", "lcd.if3"))
    return [chapter("lcd.h", "native-lcd-display"),
            heading("lcd.if1"), figure("assets/lcd_interface_1.png", "lcd-interface-1", 6, [], label=if1),
            lcd_table(interface1, "native-pdf/page-6/interface-1", True, if1),
            lcd_table(states, "native-pdf/page-7/interface-1-states", False, if1),
            heading("lcd.if2"), figure("assets/lcd_interface_2.png", "lcd-interface-2", 7, [], label=if2),
            lcd_table(interface2, "native-pdf/page-7/interface-2", True, if2),
            heading("lcd.if3"), figure("assets/lcd_interface_3.png", "lcd-interface-3", 7, [], label=if3),
            lcd_table(interface3, "native-pdf/page-8/interface-3", True, if3)]


def operations() -> list[dict]:
    headers = [{"html": escape(T(k)), "text": T.rows[k]["text"]} for k in ("op.lcd.th1", "op.lcd.th2")]
    rows = [[{"html": escape(T(f"op.lcd.r{i}.f")), "text": T.rows[f"op.lcd.r{i}.f"]["text"]},
             {"html": escape(T(f"op.lcd.r{i}.d")), "text": T.rows[f"op.lcd.r{i}.d"]["text"]}] for i in range(1, 6)]
    screen = reference_table_component_spec(variant="lcd-actions-compact", label=T.rows["op.lcd.h"]["text"],
                                            headers=headers, rows=rows, source_ref="native-pdf/page-9/lcd-screen",
                                            language=LANGUAGE)
    return [chapter("op.h", "native-operations"),
            heading("op.out.h"), bullets(["op.out.l1"]),
            figure("assets/operation-output.png", "operation-output", 8, [], label=T.rows["op.out.h"]["text"]),
            callout_items("op.caution.l", ["op.caution.i1", "op.caution.i2", "op.caution.i3"], "caution",
                          "native-pdf/page-8/caution"),
            heading("op.eco.h"), para("op.eco.p1"), para("op.eco.p2"), para("op.eco.p3"),
            figure("assets/operation-energy.png", "operation-energy", 9, ["fig.eco.press"]),
            callout_text("op.eco.note.l", ["op.eco.note.b"], "note", "native-pdf/page-9/note"),
            heading("op.lcd.h"),
            figure("assets/operation-lcd.png", "operation-lcd", 9, [], label=T.rows["op.lcd.h"]["text"]),
            component_flow_node(screen, root=True)]


def charging() -> list[dict]:
    return [chapter("chg.h", "native-charging"), para("chg.first"),
            callout_items("chg.caution.l", ["chg.caution.i1", "chg.caution.i2"], "caution", "native-pdf/page-10/caution"),
            heading("chg.usbc.h"),
            figure("assets/charging_ac.png", "charging-usbc", 10, [], label=T.rows["chg.usbc.h"]["text"]),
            sold_separately("chg.usbc.sold"),
            heading("chg.solar.h"), para("chg.solar.p"), para("chg.solar.by"),
            figure("assets/charging_solar.png", "charging-solar", 10, ["fig.solar.panel"]),
            sold_separately("chg.solar.sold"), para("chg.solar.rec"),
            heading("chg.car.h"), para("chg.car.p"),
            figure("assets/charging_car.png", "charging-car", 11, ["fig.car.vehicle"]),
            sold_separately("chg.car.sold"),
            callout_items("chg.car.caution.l", ["chg.car.caution.i1", "chg.car.caution.i2"], "caution",
                          "native-pdf/page-11/caution")]


def storage() -> list[dict]:
    return [chapter("sto.h", "native-storage"), para("sto.p1"), bullets(["sto.l1", "sto.l2"]), para("sto.p2")]


def specifications() -> list[dict]:
    g = "spec.gen.r"
    return [chapter("spec.h", "native-specifications"),
            spec_block("spec.gen.h", [(f"{g}{i}.l", [f"{g}{i}.v"]) for i in range(1, 6)]
                       + [(f"{g}6.l", [f"{g}6.v1", f"{g}6.v2"]), (f"{g}7.l", [f"{g}7.v"])], "native-pdf/page-13/general"),
            spec_block("spec.in.h", [("spec.in.r1.l", ["spec.in.r1.v1", "spec.in.r1.v2", "spec.in.r1.v3"])],
                       "native-pdf/page-13/input"),
            spec_block("spec.out.h", [(f"spec.out.r{i}.l", [f"spec.out.r{i}.v"]) for i in (1, 2)],
                       "native-pdf/page-13/output"),
            spec_block("spec.tot.h", [(f"spec.tot.r{i}.l", [f"spec.tot.r{i}.v"]) for i in (1, 2, 3)],
                       "native-pdf/page-13/total"),
            spec_block("spec.env.h", [(f"spec.env.r{i}.l", [f"spec.env.r{i}.v"]) for i in (1, 2)],
                       "native-pdf/page-13/environment"),
            para("spec.tm")]


def warranty() -> list[dict]:
    def section(index: int, title_key: str, keys: list[str]) -> list[dict]:
        # The shared card draws the body; its printed title pill is the heading before it.
        title = heading(title_key)
        blocks = [{"kind": "paragraph", "html": f"<p>{T.html(k)}</p>", "text": T.rows[k]["text"]} for k in keys]
        spec = warranty_section_component_spec(title=T.rows[title_key]["text"], section_index=index, blocks=blocks,
                                               source_ref=f"native-pdf/page-14/warranty-{index}", language=LANGUAGE)
        return [title, component_flow_node(spec, root=True)]

    contact = group([node("paragraph", [node("strong", [text(T("back.company"))])]),
                     *(node("paragraph", [text(T(k))]) for k in ("back.address", "back.tel", "back.mail", "back.web"))],
                    "hb-text-panel")
    return [chapter("war.h", "native-warranty"),
            *section(1, "war.contact.h", ["war.contact.p"]),
            *section(2, "war.service.h", ["war.service.l1", "war.service.l2", "war.service.l3"]),
            contact]


CHAPTERS = (
    ("safety", "IMPORTANT SAFETY INFORMATION", safety), ("symbols", "MEANING OF SYMBOLS", symbols),
    ("in_the_box", "WHAT'S IN THE BOX", in_the_box), ("product_overview", "PRODUCT OVERVIEW", overview),
    ("lcd_display", "LCD DISPLAY", lcd), ("operations", "OPERATIONS", operations),
    ("charging", "CHARGING", charging), ("storage", "STORAGE", storage),
    ("specifications", "SPECIFICATIONS", specifications), ("warranty", "WARRANTY", warranty),
)


def build() -> dict:
    chapters = [{"id": cid, "title": title, "nodes": make()} for cid, title, make in CHAPTERS]
    missing = [k for k in T.rows if k not in T.used]
    if missing:
        raise ValueError("Web transcription lines not bound: " + ", ".join(missing))
    return {"model": "JE-100C", "region": "US", "language": LANGUAGE,
            "title": "Jackery Explorer 100D User Manual", "source_sha256": SOURCE_SHA256, "chapters": chapters}


def main() -> None:
    content = build()
    path = PACKAGE / "source/en/content.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(content, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"chapters": [c["id"] for c in content["chapters"]], "lines": len(T.used)}))


if __name__ == "__main__":
    main()
