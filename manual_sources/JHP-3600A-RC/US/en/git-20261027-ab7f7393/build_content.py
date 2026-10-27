"""Bind the reviewed JHP-3600A-RC US transcription to shared Web components.

Run from the repository root:

    python manual_sources/JHP-3600A-RC/US/en/git-20261027-ab7f7393/build_content.py

Every Web string comes from ``source/transcription.json`` by line id; this
module only decides which shared component carries each printed block, in
printed order. It writes ``source/en/content.json``, the frozen input that
``rebuild.py`` replays. Layout differences from print are listed in
``source/differences.md``.
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

from tools.component_specs.app import app_download_component_spec, app_inline_control_component_spec  # noqa: E402
from tools.component_specs.fcc import fcc_component_spec  # noqa: E402
from tools.component_specs.inbox import inbox_component_spec  # noqa: E402
from tools.component_specs.key_combinations import key_combinations_component_spec  # noqa: E402
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
from tools.web.frozen_ai_table_components import _spec_carrier  # noqa: E402

LANGUAGE = "en"


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

    def peek(self, key: str) -> str:
        return self.rows[key]["text"]

    def inline(self, key: str) -> list[dict]:
        """Text children with the printed bold spans as strong nodes."""
        value = self(key)
        children: list[dict] = []
        for span in self.rows[key].get("strong", []):
            before, value = value.split(span, 1)
            if before:
                children.append(text(before))
            children.append(node("strong", [text(span)]))
        if value:
            children.append(text(value))
        return children

    def html(self, key: str) -> str:
        value = escape(self.rows[key]["text"])
        for span in self.rows[key].get("strong", []):
            value = value.replace(escape(span), f"<strong>{escape(span)}</strong>", 1)
        self(key)
        return value


T = Lines()


def attrs(css: str) -> dict:
    return {"html": {"attributes": {"class": css}}}


def para(key: str) -> dict:
    return root(node("paragraph", T.inline(key)))


def strong_para(key: str) -> dict:
    return root(node("paragraph", [node("strong", [text(T(key))])]))


def heading(key: str, level: int = 3, anchor: str | None = None) -> dict:
    return root(node("heading", [text(T(key))], level=level, **({"anchor": anchor} if anchor else {})))


def sold_heading(key: str, label_key: str) -> dict:
    """Printed title capsule plus the separate SOLD SEPARATELY capsule (shared classes)."""
    return root(node("heading", [node("inline_group", [text(T(key))], presentation=attrs("hb-heading-title")),
                                 text(" "),
                                 node("inline_group", [text(T(label_key))], presentation=attrs("hb-sold-separately"))],
                     level=3, presentation=attrs("hb-heading-label-pair")))


def bullets(keys: list[str]) -> dict:
    return root(node("list", [node("list_item", [node("paragraph", T.inline(k))]) for k in keys], ordered=False))


def panel(children: list[dict]) -> dict:
    """Shared grey text panel (web_manual.css ``.hb-text-panel``)."""
    return root(node("group", children, role="container", presentation=attrs("hb-text-panel")))


def p(key: str) -> dict:
    return node("paragraph", T.inline(key))


def ul(keys: list[str]) -> dict:
    return node("list", [node("list_item", [node("paragraph", T.inline(k))]) for k in keys], ordered=False)


def fragment_sha256(ref: str, reference_id: str, alt: str) -> str:
    """The shared renderer's source-fragment hash of a captionless semantic image."""
    soup = BeautifulSoup("", "html.parser")
    semantic = soup.new_tag("div", attrs={"class": "hb-reference-semantic",
                                          "data-reference-id": f"{reference_id}.semantic"})
    semantic.append(soup.new_tag("img", attrs={"alt": alt, "class": "hb-reference-art", "src": ref}))
    return reference_source_fragment_sha256(
        component={"id": reference_id, "image_key": reference_id, "captions_embedded": True},
        semantic=semantic, caption_labels=[], composite_locale=None)


def figure(name: str, page: int, label_keys: list[str], label: str) -> dict:
    """Complete source panel; printed labels stay in the art, the alt text and the IR."""
    ref = f"assets/{name}.png"
    labels = [T(key) for key in label_keys]
    alt = " / ".join([label, *labels])
    spec = reference_figure_component_spec(
        reference_id=name, accessibility_label=alt, caption_mode="embedded",
        captions=(), adjacent_copy=None, source_art_ref=ref, source_art_locale_policy="exact",
        source_fragment_sha256=fragment_sha256(ref, name, alt),
        source_ref=f"native-pdf/page-{page}/{name}", language=LANGUAGE, image_key=name,
        metadata={"embedded_labels": labels, "physical_page": page},
    )
    return component_flow_node(spec, carrier_flow=(root(node("image", source=ref, alt=alt)),), root=True)


def flat(item: dict) -> dict:
    """Callout bodies carry plain text: the shared callout carrier checks its copy line by line."""
    if item.get("kind") in {"paragraph", "list_item"} and any(c.get("kind") == "strong" for c in item["children"]):
        value = "".join(c["text"] if c["kind"] == "text" else c["children"][0]["text"] for c in item["children"])
        return {**item, "children": [text(value)]}
    if item.get("children"):
        return {**item, "children": [flat(child) for child in item["children"]]}
    return item


def note_block(label_key: str, body: list[dict], variant: str, ref: str) -> dict:
    return root(callout(T(label_key), [flat(b) for b in body], variant=variant, language=LANGUAGE, source_ref=ref))


def plain_callout(label_key: str, keys: list[str], variant: str, ref: str) -> dict:
    return note_block(label_key, [p(k) for k in keys], variant, ref)


def list_callout(label_key: str, keys: list[str], variant: str, ref: str) -> dict:
    body = [node("list", [node("list_item", [text(T.peek(k))]) for k in keys], ordered=False)]
    for k in keys:
        T(k)
    return note_block(label_key, body, variant, ref)


# --- chapters -------------------------------------------------------------

def preface() -> list[dict]:
    return [heading("pre.h", 2, "native-important"), para("pre.p1"), para("pre.p2"), para("pre.p3"),
            para("pre.n1"), para("pre.n2")]


def safety() -> list[dict]:
    warn = root(callout(T("saf.warn.l"), [
        node("paragraph", [node("strong", [text(T("saf.warn.lead"))])]),
        ul([f"saf.w{i}" for i in range(1, 12)]),
    ], variant="warning", language=LANGUAGE, source_ref="native-pdf/page-4/warning"))
    items = [node("list_item", [p("op.l1")]),
             node("list_item", [p("op.l2"), p("op.l2.a"), p("op.l2.b")]),
             node("list_item", [p("op.l3"), p("op.l3.a"), p("op.l3.b")]),
             *(node("list_item", [p(f"op.l{i}")]) for i in range(4, 15))]
    danger = root(callout(T("danger.l"), [p("danger.p1"), p("danger.p2")], variant="danger",
                          language=LANGUAGE, source_ref="native-pdf/page-5/danger"))
    return [heading("saf.h", 2, "native-safety"), heading("saf.risk"), warn,
            heading("op.h"), heading("op.save", 4), root(node("list", items, ordered=False)),
            danger, heading("maint.h"), para("maint.p")]


SYMBOLS = ["alert", "manual", "shock", "charging", "explosive", "heavy",
           "dismantle", "fire", "children", "liion", "weee"]


def symbols() -> list[dict]:
    def pair(value: str, key: str) -> dict:
        return {f"{key}_html": escape(value), f"{key}_text": value}
    title = T("sym.h")
    signal = symbol_signal_component_spec(
        accessibility_label=title, headers=[pair(T("sig.th1"), "content"), pair(T("sig.th2"), "content")],
        rows=[{"label": T(f"sig.{k}.l"), "show_icon": True, **pair(T(f"sig.{k}.m"), "meaning")}
              for k in ("warn", "caut", "note", "tip")],
        source_ref="native-pdf/page-5/signal", language=LANGUAGE)
    manifest = json.loads((PACKAGE / "source/asset_recipe.json").read_text(encoding="utf-8"))
    refs = [row["path"] for row in manifest["symbols"]]
    meanings = [T("sym." + k) for k in SYMBOLS]
    icons = symbol_icon_component_spec(
        accessibility_label=title,
        headers=[pair(T(k), "content") for k in ("sym.th1", "sym.th2", "sym.th3", "sym.th4")],
        panels=[[{"asset_index": i, "icon_alt": meanings[i], **pair(meanings[i], "meaning")} for i in rows]
                for rows in (range(0, 6), range(6, 11))],
        icon_refs=refs, source_ref="native-pdf/page-5/symbols", language=LANGUAGE)
    return [root(node("heading", [text(title)], level=2, anchor="native-symbols")),
            component_flow_node(signal, root=True), component_flow_node(icons, root=True)]


def fcc() -> list[dict]:
    opening = [T("fcc.p1"), T("fcc.p1.a"), T("fcc.p1.b")]
    note = T("fcc.note")
    limits, cause = T("fcc.limits"), T("fcc.if")
    measures = [T(f"fcc.m{i}") for i in range(1, 5)]
    modification = T("fcc.mod")
    rf_label, rf = T("fcc.rf.h"), T("fcc.rf")
    left = [{"kind": "paragraph", "label": "NOTE:", "text": note.removeprefix("NOTE:").strip()},
            {"kind": "paragraph", "label": "", "text": limits},
            {"kind": "paragraph", "label": "", "text": cause}]
    right = [{"kind": "list", "items": measures},
             {"kind": "paragraph", "label": "MODIFICATION:",
              "text": modification.removeprefix("MODIFICATION:").strip()},
             {"kind": "paragraph", "label": rf_label, "text": rf}]
    spec = fcc_component_spec(accessibility_label="FCC", opening_copy=opening, left_blocks=left,
                              right_blocks=right, source_ref="native-pdf/page-6/fcc", language=LANGUAGE,
                              mark_asset_ref="assets/fcc-mark.svg", metadata={"source_page": 6})
    carrier = [node("paragraph", [text(value)]) for value in opening]
    for block in [*left, *right]:
        if block["kind"] == "list":
            carrier.append(node("list", [node("list_item", [node("paragraph", [text(v)])]) for v in block["items"]],
                                ordered=False))
        elif block["label"]:
            carrier.append(node("paragraph", [node("strong", [text(block["label"])]), text(" "),
                                              text(block["text"])]))
        else:
            carrier.append(node("paragraph", [text(block["text"])]))
    return [component_flow_node(spec, carrier_flow=carrier, root=True)]


def fcc_chapter() -> list[dict]:
    """The printed FCC panel has no title; the shared theme keeps this navigation H1 for assistive technology only."""
    return [root(node("heading", [text("FCC")], level=2, anchor="native-fcc")), *fcc(), canada()]


def canada() -> dict:
    return panel([node("paragraph", [node("strong", [text(T("ic.h"))])]), p("ic.p"), p("ic.l1"), p("ic.l2"),
                  p("ic.ices"), p("ic.can"), node("paragraph", [node("strong", [text(T("ic.rf.h"))])]),
                  p("ic.rf")])


def in_the_box() -> list[dict]:
    title = T("box.h")
    cards = [{"image_ref": f"assets/{ref}.png", "label": T(key), "alt": T.peek(key)}
             for key, ref in (("box.c1", "inbox-unit"), ("box.c2", "inbox-cable"), ("box.c3", "inbox-documents"))]
    tip_label, tip_body = T("box.tip.l"), T("box.tip")
    spec = inbox_component_spec(accessibility_label=title, cards=cards, tip_label=tip_label, tip_body=tip_body,
                                source_ref="native-pdf/page-6/inbox", language=LANGUAGE)
    card_table = table([[node("table_cell", [node("image", source=c["image_ref"], alt=c["alt"]),
                                             node("paragraph", [text(c["label"])])], header=False) for c in cards]])
    tip_table = table([[node("table_cell", [node("paragraph", [text(tip_label)])], header=False),
                        node("table_cell", [node("paragraph", [text(tip_body)])], header=False)]])
    return [root(node("heading", [text(title)], level=2, anchor="native-in-the-box")),
            component_flow_node(spec, carrier_flow=(card_table, tip_table), root=True)]


def overview() -> list[dict]:
    front = ["ov.f.lcd", "ov.f.acout30", "ov.f.power", "ov.f.usbc", "ov.f.acout", "ov.f.usba", "ov.f.usbbtn",
             "ov.f.acbtn"]
    side = ["ov.s.handle", "ov.s.acexp", "ov.s.reset", "ov.s.dcexp", "ov.s.dcin", "ov.s.acin", "ov.s.wheels"]
    return [heading("ov.h", 2, "native-product-overview"),
            heading("ov.front.h"), figure("overview-front", 7, front, T.peek("ov.front.h")),
            heading("ov.side.h"), figure("overview-side", 7, side, T.peek("ov.side.h"))]


LCD_ROWS = [  # (number, line prefix, asset)
    (1, "lcd.1", "wifi"), (2, "lcd.2", "bluetooth"), (3, "lcd.3", "quiet"), (4, "lcd.4a", "battery-saving"),
    (4, "lcd.4b", "self-powered"), (5, "lcd.5", "charging-plan"), (6, "lcd.6", "parallel"), (7, "lcd.7", "ac-power"),
    (8, "lcd.8", "output-vhz"), (9, "lcd.9", "input-power"), (10, "lcd.10", "charge-time"), (11, "lcd.11", "ac-wall"),
    (12, "lcd.12", "car"), (13, "lcd.13", "solar"), (14, "lcd.14", "battery-power"), (15, "lcd.15", "low-battery"),
    (16, "lcd.16", "percentage"), (17, "lcd.17", "battery-packs"), (18, "lcd.18", "fault-code"),
    (19, "lcd.19a", "high-temperature"), (19, "lcd.19b", "low-temperature"), (20, "lcd.20", "energy-saving"),
    (21, "lcd.21", "output-power"), (22, "lcd.22", "discharge-time"),
]


def lcd() -> list[dict]:
    rows, refs = [], []
    for index, (number, prefix, asset) in enumerate(LCD_ROWS):
        name = T(prefix + ".t")
        keys = [k for k in T.rows if k.startswith(prefix + ".b")]
        html = "<br/>".join(T.html(k) for k in keys)
        rows.append({"number_html": str(number), "number_text": str(number),
                     "name_html": escape(name), "name_text": name, "description_html": html,
                     "description_text": " ".join(T.peek(k) for k in keys), "icon_alt": name, "asset_index": index})
        refs.append(f"assets/lcd-{asset}.svg")
    title = T.peek("lcd.h")
    spec = lcd_icon_component_spec(accessibility_label=title, rows=rows, icon_refs=refs,
                                   source_ref="native-pdf/page-8/lcd-icons", language=LANGUAGE,
                                   icon_locale_policy="exact")
    return [heading("lcd.h", 2, "native-lcd-display"), figure("lcd-map", 8, [], title),
            component_flow_node(spec, root=True)]


def lcd_screen() -> dict:
    def pair(key: str, prefix: str) -> dict:
        return {f"{prefix}_html": escape(T.peek(key)), f"{prefix}_text": T(key)}
    groups = []
    for state, rows in (("scr.short", "s"), ("scr.steady", "t")):
        groups.append({**pair(state, "state"), "actions": [
            {**pair(f"scr.{rows}.{a}.l", "action"), **pair(f"scr.{rows}.{a}", "description")}
            for a in ("on", "off", "auto")]})
    T("fig.scr.btn")
    spec = lcd_mode_component_spec(accessibility_label=T.peek("scr.h"), groups=groups,
                                   artwork_ref="assets/lcd-screen.png", artwork_locale_policy="exact",
                                   source_ref="native-pdf/page-12/lcd-screen", language=LANGUAGE)
    carrier = [node("image", source="assets/lcd-screen.png", alt="POWER")]
    return component_flow_node(spec, carrier_flow=carrier, root=True)


def key_combinations() -> dict:
    headers = [T("key.th1"), T("key.th2"), T("key.th3")]
    buttons = {"Main power button": "assets/button-power.svg", "USB power button": "assets/button-usb.svg",
               "AC power button": "assets/button-ac.svg"}
    rows, carrier_rows = [], []
    for r in (1, 2, 3):
        b1, b2, dur, op, fn = (T(f"key.r{r}.{k}") for k in ("b1", "b2", "dur", "op", "fn"))
        rows.append([f"{b1} + {b2}", f"{dur} {op}", fn])

        def button(label: str) -> dict:
            return node("group", [node("image", source=buttons[label], alt=""),
                                  node("inline_group", [text(label)], presentation=attrs("ht-key-caption"))],
                        role="container", presentation=attrs("hb-key-button"))
        pair_cell = node("group", [button(b1), node("inline_group", [text("+")], hidden=True,
                                                    presentation=attrs("hb-key-button-plus")), button(b2)],
                         role="container", presentation=attrs("hb-key-button-pair"))
        duration = node("group", [text(dur)], role="container",
                        presentation={"html": {"attributes": {"class": "hb-key-duration", "data-duration-icon": "clock"}}})
        carrier_rows.append(node("table_row", [node("table_cell", [pair_cell], header=False),
                                               node("table_cell", [duration, node("paragraph", [text(op)])], header=False),
                                               node("table_cell", [node("paragraph", [text(fn)])], header=False)]))
    spec = key_combinations_component_spec(headers=headers, rows=rows, source_ref="native-pdf/page-12/key-combination",
                                           language=LANGUAGE)
    head = node("table_head", [node("table_row", [node("table_cell", [text(h)], header=True) for h in headers])])
    carrier = node("table", [head, node("table_body", carrier_rows)], presentation=attrs("hb-key-combination-table"))
    return component_flow_node(spec, carrier_flow=(carrier,), root=True)


def operations() -> list[dict]:
    return [heading("ops.h", 2, "native-operations"),
            heading("ops.pwr.h"),
            figure("power", 10, ["fig.pwr.btn", "fig.pwr.on", "fig.pwr.off", "fig.pwr.3s"], T.peek("ops.pwr.h")),
            panel([p("ops.pwr.standby"), p("ops.pwr.standby2"), p("ops.pwr.standby3")]),
            panel([p("ops.pwr.eco")]),
            heading("ops.ac.h"), para("ops.ac.pre"),
            figure("ac-output", 10, ["fig.ac.btn", "fig.ac.on", "fig.ac.off"], T.peek("ops.ac.h")),
            panel([node("paragraph", [node("strong", [text(T("ops.ac.reset.h"))])]), p("ops.ac.reset")]),
            heading("ops.usb.h"), para("ops.usb.pre"),
            figure("usb-output", 11, ["fig.usb.btn", "fig.usb.on", "fig.usb.off"], T.peek("ops.usb.h")),
            note_block("usb.caut.l", [ul(["usb.caut.i1", "usb.caut.i2", "usb.caut.i3"])], "caution",
                       "native-pdf/page-11/usb-caution"),
            heading("ops.eco.h"), panel([p("ops.eco.p1"), p("ops.eco.p2")]),
            figure("energy-saving", 11, ["fig.eco.power", "fig.eco.ac", "fig.eco.onoff"], T.peek("ops.eco.h")),
            plain_callout("ops.eco.note.l", ["ops.eco.note"], "note", "native-pdf/page-11/eco-note"),
            plain_callout("eco.warn.l", ["eco.warn"], "warning", "native-pdf/page-12/eco-warning"),
            heading("scr.h"), lcd_screen(), para("scr.app"),
            heading("key.h"), key_combinations()]


def ups() -> list[dict]:
    return [heading("ups.h", 2, "native-ups"), para("ups.lead"),
            figure("ups", 13, ["fig.ups.btn"], T.peek("ups.h")),
            para("ups.def"), para("ups.switch"), para("ups.peak"),
            list_callout("ups.caut.l", [f"ups.caut.i{i}" for i in range(1, 5)], "caution", "native-pdf/page-13/caution"),
            note_block("ups.warn.l", [p("ups.warn.p1"), p("ups.warn.p2"),
                                      ul(["ups.warn.l1", "ups.warn.l2", "ups.warn.l3"]), p("ups.warn.p3")],
                       "warning", "native-pdf/page-13/warning")]


def connections() -> list[dict]:
    steps = [para("par.s1"), para("par.s2"), para("par.s3"), para("par.s4"), bullets(["par.s4.a", "par.s4.b"])]
    return [heading("con.h", 2, "native-connections"),
            sold_heading("con.bp.h", "con.bp.sold"), para("con.bp.p"),
            figure("battery-stack", 14, ["fig.bp.gap1", "fig.bp.gap2"], T.peek("con.bp.h")),
            list_callout("con.bp.caut.l", ["con.bp.caut.i1", "con.bp.caut.i2"], "caution", "native-pdf/page-14/caution"),
            figure("battery-accessories", 14, ["con.bp.k1", "con.bp.k2", "con.bp.k3", "con.bp.k4"],
                   T.peek("con.bp.sold")),
            heading("par.h"),
            list_callout("par.note.l", ["par.note.i1", "par.note.i2"], "note", "native-pdf/page-15/note"),
            plain_callout("par.caut1.l", ["par.caut1"], "caution", "native-pdf/page-15/caution-1"),
            *steps,
            figure("parallel", 15, ["fig.par.port", "fig.par.conn"], T.peek("par.h")),
            list_callout("par.caut2.l", ["par.caut2.i1", "par.caut2.i2"], "caution", "native-pdf/page-15/caution-2"),
            para("par.fail1"), para("par.fail2"),
            figure("parallel-interrupted", 16, ["fig.fail.conn", "fig.fail.ac"], T.peek("par.h")),
            heading("exit.h"),
            figure("parallel-exit", 16, ["fig.exit.s1", "fig.exit.ac", "fig.exit.s2", "fig.exit.s3"],
                   T.peek("exit.h"))]


def charging() -> list[dict]:
    return [heading("chg.h", 2, "native-charging"), para("chg.green"), para("chg.prio"),
            root(node("paragraph", [node("strong", [text(T("chg.first"))])], presentation=attrs("hb-prose-pill"))),
            list_callout("chg.note.l", ["chg.note.i1", "chg.note.i2"], "note", "native-pdf/page-17/note"),
            heading("chg.ac.h"), figure("charging-ac", 17, [], T.peek("chg.ac.h")), para("chg.ac.p"),
            plain_callout("chg.ac.caut.l", ["chg.ac.caut"], "caution", "native-pdf/page-17/caution"),
            sold_heading("chg.sol.h", "chg.sol.sold"), para("chg.sol.p"),
            figure("charging-solar", 17, ["fig.sol.saga"], T.peek("chg.sol.h")),
            plain_callout("chg.sol.caut1.l", ["chg.sol.caut1"], "caution", "native-pdf/page-18/caution-1"),
            note_block("chg.sol.caut2.l", [p("chg.sol.caut2"), ul(["chg.sol.caut2.i1", "chg.sol.caut2.i2"])],
                       "caution", "native-pdf/page-18/caution-2"),
            para("chg.sol.rec"),
            sold_heading("chg.car.h", "chg.car.sold"), para("chg.car.p"),
            figure("charging-car", 18, ["fig.car.vehicle"], T.peek("chg.car.h")), para("chg.car.cable"),
            list_callout("chg.car.caut.l", ["chg.car.caut.i1", "chg.car.caut.i2", "chg.car.caut.i3"], "caution",
                         "native-pdf/page-18/caution-3")]


def storage() -> list[dict]:
    return [heading("sto.h", 2, "native-storage"),
            panel([p("sto.p"), ul(["sto.l1", "sto.l2", "sto.l3"]), p("sto.long")])]


def troubleshooting() -> list[dict]:
    def pair(value: str, key: str) -> dict:
        return {f"{key}_html": escape(value), f"{key}_text": value}
    rows = []
    for code in ("f0", "f4", "f5", "f6", "f7", "f8", "f9", "fa", "fc"):
        keys = [k for k in T.rows if k.startswith(f"ts.{code}.m")]
        measures = [T(k) for k in keys]
        rows.append({**pair(T(f"ts.{code}.c"), "code"), "measures_html": "<br/>".join(escape(m) for m in measures),
                     "measures_text": " ".join(measures)})
    spec = troubleshooting_component_spec(headers=[pair(T("ts.th1"), "content"), pair(T("ts.th2"), "content")],
                                          rows=rows, source_ref="native-pdf/page-19/troubleshooting",
                                          language=LANGUAGE)
    return [heading("ts.h", 2, "native-troubleshooting"), para("ts.p"), component_flow_node(spec, root=True)]


def specifications() -> list[dict]:
    out = [heading("spec.h", 2, "native-specifications")]
    for section, count in (("g", 7), ("i", 3), ("o", 9), ("e", 2)):
        title = T(f"spec.{section}.h")
        rows = []
        for r in range(1, count + 1):
            label = T(f"spec.{section}.r{r}.l")
            values = [k for k in T.rows if k.startswith(f"spec.{section}.r{r}.v")]
            rows.append((label, "\n".join(T(k) for k in values)))
        spec = spec_table_component_spec(section_title=title, rows=rows, language=LANGUAGE,
                                         source_ref=f"native-pdf/page-20/spec-{section}")
        out.append(component_flow_node(spec, carrier_flow=_spec_carrier(title, rows), root=True))
    return [*out, para("spec.tm"), para("spec.fn1"), para("spec.fn2"), para("spec.fn3")]


def warranty() -> list[dict]:
    def blocks_p(*keys: str) -> dict:
        texts = [T.peek(k) for k in keys]
        html = "<br/>".join(T.html(k) for k in keys)
        return {"kind": "paragraph", "html": f"<p>{html}</p>", "text": " ".join(texts)}

    def blocks_ul(*keys: str) -> dict:
        items = [T(k) for k in keys]
        return {"kind": "list", "items": items,
                "html": "<ul>" + "".join(f"<li>{escape(i)}</li>" for i in items) + "</ul>"}

    def section(index: int, title_key: str, blocks: list[dict]) -> list[dict]:
        # The shared card draws the body; its printed title pill is the heading before it.
        title = heading(title_key)
        spec = warranty_section_component_spec(title=T.peek(title_key), section_index=index, blocks=blocks,
                                               source_ref=f"native-pdf/page-21/warranty-{index}", language=LANGUAGE)
        return [title, component_flow_node(spec, root=True)]

    lead = warranty_lead_component_spec(accessibility_label=T.peek("war.h"), lead_html=T.html("war.lead"),
                                        local_note_html=T.html("war.vary"), source_ref="native-pdf/page-21/lead",
                                        language=LANGUAGE)
    periods = []
    for key in ("std", "ext"):
        number, unit = T(f"war.per.{key}.n").split(" ", 1)
        periods.append({"number": number, "unit": unit, "label": T(f"war.per.{key}.t"),
                        "body_html": T.html(f"war.per.{key}"), "body_text": T.peek(f"war.per.{key}")})
    period_title = heading("war.per.h")
    years = warranty_years_component_spec(title=T.peek("war.per.h"), periods=periods,
                                          source_ref="native-pdf/page-21/period", language=LANGUAGE)
    return [heading("war.h", 2, "native-warranty"), component_flow_node(lead, root=True),
            *section(1, "war.lim.h", [blocks_p("war.lim.p1"), blocks_p("war.lim.p2")]),
            period_title, component_flow_node(years, root=True),
            *section(2, "war.rep.h", [blocks_p("war.rep")]),
            *section(3, "war.orig.h", [blocks_p("war.orig")]),
            *section(4, "war.exc.h", [blocks_p("war.exc.lead"),
                                      blocks_ul("war.exc.l1", "war.exc.l2", "war.exc.l3", "war.exc.l4")]),
            *section(5, "war.int.h", [blocks_p("war.int")])]


def app_setup() -> list[dict]:
    columns = [{"role": "store", "text": T("app.s1.store")}, {"role": "qr", "text": T("app.s1.qr")}]
    for column in columns:
        column["html"] = escape(column["text"])
    download = app_download_component_spec(
        accessibility_label="Jackery App", columns=columns, source_art_ref="assets/app-qr.png",
        store_art_ref="assets/app-store.png", qr_art_ref="assets/app-qr.png",
        source_ref="native-pdf/page-22/download", language=LANGUAGE)
    carrier = [node("image", source="assets/app-qr.png", alt="Jackery App"),
               *(node("paragraph", [text(c["text"])]) for c in columns)]
    before, after = T("app.s21").split(" [+] ")
    plus = app_inline_control_component_spec(
        accessibility_label="+", paragraph_html=f"{escape(before)} <strong>+</strong> {escape(after)}",
        paragraph_text=f"{before} + {after}", source_ref="native-pdf/page-22/add-button", language=LANGUAGE,
        metadata={"visual_recovery": "outlined-pdf-vector-plus-control"})
    plus_carrier = node("paragraph", [text(before + " "), node("strong", [text("+")]), text(" " + after)])
    return [heading("app.h", 2, "native-app-setup"),
            heading("app.s1.h"), component_flow_node(download, carrier_flow=carrier, root=True),
            heading("app.s2.h"), component_flow_node(plus, carrier_flow=(plus_carrier,), root=True),
            para("app.s22"),
            figure("app-add", 22, ["fig.app.c21", "fig.app.c22"], T.peek("app.s2.h")),
            figure("app-buttons", 22, ["fig.btn.power", "fig.btn.usb", "fig.btn.ac"], T.peek("app.s2.h")),
            plain_callout("app.note1.l", ["app.note1"], "note", "native-pdf/page-22/note-1"),
            para("app.s23"),
            note_block("app.note2.l", [p("app.note2"), ul(["app.note2.i1", "app.note2.i2"])], "note",
                       "native-pdf/page-23/note-2"),
            para("app.s24"),
            plain_callout("app.note3.l", ["app.note3"], "note", "native-pdf/page-23/note-3"),
            para("app.s25"),
            figure("app-results", 23, ["fig.app.c23", "fig.app.c24", "fig.app.c25"], T.peek("app.s2.h")),
            para("app.shots"),
            plain_callout("app.caut.l", ["app.caut"], "caution", "native-pdf/page-23/caution"),
            heading("app.s3.h"), para("app.s3"),
            heading("app.s4.h"),
            heading("app.s41.h", 4), bullets(["app.s41.l1", "app.s41.l2"]),
            heading("app.s42.h", 4), bullets(["app.s42.l1", "app.s42.l2"]),
            heading("app.s43.h", 4), para("app.s43")]


CHAPTERS = (
    ("important", "IMPORTANT", preface), ("safety", "IMPORTANT SAFETY INFORMATION", safety),
    ("symbols", "MEANING OF SYMBOLS", symbols), ("fcc", "FCC", fcc_chapter),
    ("in_the_box", "WHAT'S IN THE BOX", in_the_box),
    ("product_overview", "PRODUCT OVERVIEW", overview), ("lcd_display", "LCD DISPLAY", lcd),
    ("operations", "OPERATIONS", operations), ("ups", "UNINTERRUPTIBLE POWER SUPPLY (UPS)", ups),
    ("connections", "CONNECTIONS", connections), ("charging", "CHARGING", charging),
    ("storage", "STORAGE", storage), ("troubleshooting", "TROUBLESHOOTING", troubleshooting),
    ("specifications", "SPECIFICATIONS", specifications), ("warranty", "WARRANTY", warranty),
    ("app_setup", "APP SETUP", app_setup),
)


def build() -> dict:
    chapters = [{"id": cid, "title": title, "nodes": make()} for cid, title, make in CHAPTERS]
    missing = [k for k in T.rows if k not in T.used]
    if missing:
        raise ValueError("Web transcription lines not bound: " + ", ".join(missing))
    return {"model": "JHP-3600A-RC", "region": "US", "language": LANGUAGE,
            "title": "Jackery HomePower 3600 Plus User Manual",
            "source_sha256": "ab7f7393ed6fd1e08656f19a48bdc7fce8f827ee9be629f8aebfd95b7d5cf857",
            "chapters": chapters}


def main() -> None:
    content = build()
    path = PACKAGE / "source/en/content.json"
    path.write_text(json.dumps(content, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"chapters": [c["id"] for c in content["chapters"]], "lines": len(T.used)}))


if __name__ == "__main__":
    main()
