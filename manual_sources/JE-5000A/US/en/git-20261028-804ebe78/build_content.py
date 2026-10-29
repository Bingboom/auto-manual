"""Bind the reviewed JE-5000A US transcription to shared Web components.

Run from the repository root:

    python manual_sources/JE-5000A/US/en/git-20261028-804ebe78/build_content.py

Every Web string comes from ``source/transcription.json`` by line id; this
module only decides which shared component carries each printed block, in
printed order. It writes ``source/en/content.json``, the frozen input that
``rebuild.py`` replays. The printed tables carry their own headers, so no
component chrome is invented; ``source/differences.md`` lists every layout
difference from the print.
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

from tools.component_specs.adapters import web_callout_classes  # noqa: E402
from tools.component_specs.app import app_download_component_spec, app_inline_control_component_spec  # noqa: E402
from tools.component_specs.callout import callout_component_spec  # noqa: E402
from tools.component_specs.fcc import fcc_component_spec, fcc_semantic_projection  # noqa: E402
from tools.component_specs.inbox import inbox_component_spec  # noqa: E402
from tools.component_specs.key_combinations import key_combinations_component_spec  # noqa: E402
from tools.component_specs.lcd_mode import lcd_mode_component_spec  # noqa: E402
from tools.component_specs.manual_tables import (  # noqa: E402
    lcd_icon_component_spec, symbol_icon_component_spec, symbol_signal_component_spec,
)
from tools.component_specs.reference_figure import reference_figure_component_spec  # noqa: E402
from tools.component_specs.spec_table import spec_table_component_spec  # noqa: E402
from tools.component_specs.warranty import (  # noqa: E402
    warranty_lead_component_spec, warranty_section_component_spec, warranty_years_component_spec,
)
from tools.manual_ir.components import component_flow_node  # noqa: E402
from tools.web.composite_hashing import reference_source_fragment_sha256  # noqa: E402
from tools.web.frozen_ai_flow import node, root, table, text  # noqa: E402
from tools.web.frozen_ai_table_components import _spec_carrier  # noqa: E402

LANGUAGE = "en"
SOURCE_SHA256 = "804ebe784c84a698800b2c1cc0f4d28ec692057b1600c48fcc3604e27c86f013"
CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳㉑㉒㉓"
# Print-only chrome on a Web page: the 「US」 language tab beside IMPORTANT.
PRINT_ONLY = {"imp.badge"}


def attrs(css: str, **extra: str) -> dict:
    return {"html": {"attributes": {"class": css, **extra}}}


class Lines:
    """Line lookup that records every id used, so coverage can be checked."""

    def __init__(self) -> None:
        source = json.loads((PACKAGE / "source/transcription.json").read_text(encoding="utf-8"))
        self.rows = {line["id"]: line for page in source["pages"] if page["web"] for line in page["lines"]
                     if line["id"] not in PRINT_ONLY}
        self.used: list[str] = []

    def __call__(self, key: str) -> str:
        if key in self.used:
            raise ValueError("transcription line bound twice: " + key)
        self.used.append(key)
        return self.rows[key]["text"]

    def spans(self, key: str) -> list[tuple[bool, str]]:
        """(bold, text) runs in printed order."""
        value = self(key)
        runs: list[tuple[bool, str]] = []
        cursor = 0
        for span in self.rows[key].get("strong", []):
            start = value.index(span, cursor)
            if start > cursor:
                runs.append((False, value[cursor:start]))
            runs.append((True, span))
            cursor = start + len(span)
        if cursor < len(value):
            runs.append((False, value[cursor:]))
        return runs

    def inline(self, key: str) -> list[dict]:
        return [node("strong", [text(value)]) if bold else text(value) for bold, value in self.spans(key)]

    def html(self, key: str) -> str:
        return "".join(f"<strong>{escape(value)}</strong>" if bold else escape(value)
                       for bold, value in self.spans(key))


T = Lines()


# --- flow helpers -----------------------------------------------------------

def p(key: str) -> dict:
    return node("paragraph", T.inline(key))


def para(key: str) -> dict:
    return root(p(key))


def strong_p(key: str) -> dict:
    return node("paragraph", [node("strong", [text(T(key))])])


def strong(key: str) -> dict:
    return root(strong_p(key))


def heading(key: str, level: int = 3, anchor: str | None = None) -> dict:
    return root(node("heading", [text(T(key))], level=level, **({"anchor": anchor} if anchor else {})))


def chapter_heading(key: str, anchor: str) -> dict:
    return heading(key, level=2, anchor=anchor)


def sold_heading(title_key: str, sold_key: str) -> dict:
    """Printed title plus the separate dark SOLD SEPARATELY pill."""
    return root(node("heading", [
        node("inline_group", [text(T(title_key))], presentation=attrs("hb-heading-title")),
        node("inline_group", [text(T(sold_key))], presentation=attrs("hb-sold-separately")),
    ], level=3, presentation=attrs("hb-heading-label-pair")))


def items(keys: list[str]) -> list[dict]:
    return [node("list_item", [p(k)]) for k in keys]


def bullets(keys: list[str]) -> dict:
    return root(node("list", items(keys), ordered=False))


def panel(children: list[dict]) -> dict:
    """Shared grey text panel (web_manual.css ``.hb-text-panel``) for printed grey boxes and pills."""
    return root(node("group", children, role="container", presentation=attrs("hb-text-panel")))


def fragment_sha256(ref: str, reference_id: str, alt: str) -> str:
    """The shared renderer's source-fragment hash of a captionless semantic image."""
    soup = BeautifulSoup("", "html.parser")
    semantic = soup.new_tag("div", attrs={"class": "hb-reference-semantic",
                                          "data-reference-id": f"{reference_id}.semantic"})
    semantic.append(soup.new_tag("img", attrs={"alt": alt, "class": "hb-reference-art", "src": ref}))
    return reference_source_fragment_sha256(
        component={"id": reference_id, "image_key": reference_id, "captions_embedded": True},
        semantic=semantic, caption_labels=[], composite_locale=None)


def figure(reference_id: str, page: int, label_keys: list[str], label: str | None = None) -> dict:
    """Complete source panel; printed labels stay in the art and the alt text."""
    ref = f"assets/{reference_id}.png"
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


def leaves(item: dict) -> list[str]:
    """Visible text runs as the shared callout carrier check reads them (stripped, non-empty)."""
    if item.get("kind") == "text":
        return [item["text"].strip()] if item["text"].strip() else []
    return [part for child in item.get("children", []) for part in leaves(child)]


def callout(label_key: str, body: list[dict], variant: str, ref: str) -> dict:
    """The shared callout carrier; a bold lead-in followed by plain copy keeps its space."""
    label = T(label_key)
    list_items = [" ".join(leaves(item)) for block in body if block["kind"] == "list" for item in block["children"]]
    spec = callout_component_spec(label=label, body="\n".join(part for b in body for part in leaves(b)),
                                  items=list_items, variant=variant, language=LANGUAGE, source_ref=ref)
    carrier = table([[node("table_cell", [text(label)], header=False, presentation=attrs("manual-callout-label")),
                      node("table_cell", body, header=False, presentation=attrs("manual-callout-body"))]],
                    css_class=f"manual-callout-table {web_callout_classes(spec)['table']}")
    return root(component_flow_node(spec, carrier_flow=[carrier]))


def callout_lines(label_key: str, keys: list[str], variant: str, ref: str) -> dict:
    return callout(label_key, [p(k) for k in keys], variant, ref)


def callout_list(label_key: str, keys: list[str], variant: str, ref: str) -> dict:
    return callout(label_key, [node("list", items(keys), ordered=False)], variant, ref)


def pair(value: str, key: str) -> dict:
    return {f"{key}_html": escape(value), f"{key}_text": value}


# --- chapters -----------------------------------------------------------------

def important() -> list[dict]:
    return [chapter_heading("imp.h", "native-important"), para("imp.p1"), para("imp.p2"), para("imp.p3")]


SYMBOLS = [("sym.warning", "assets/symbol-01.svg"), ("sym.shock", "assets/symbol-02.svg"),
           ("sym.charging", "assets/symbol-03.svg"), ("sym.explosive", "assets/symbol-04.svg"),
           ("sym.heavy", "assets/symbol-05.svg"), ("sym.fire", "assets/symbol-06.svg"),
           ("sym.children", "assets/symbol-07.svg"), ("sym.manual", "assets/symbol-08.svg")]


def fcc() -> dict:
    def block(key: str) -> dict:
        value = T(key)
        for label in ("NOTE:", "MODIFICATION:"):
            if value.startswith(label + " "):
                return {"kind": "paragraph", "label": label, "text": value[len(label) + 1:]}
        return {"kind": "paragraph", "label": "", "text": value}

    left = [block("fcc.note")]
    right = [{"kind": "list", "items": [T(f"fcc.m{i}") for i in range(1, 5)]}, block("fcc.mod")]
    spec = fcc_component_spec(accessibility_label="FCC", opening_copy=[], left_blocks=left, right_blocks=right,
                              source_ref="native-pdf/page-5/fcc", language=LANGUAGE,
                              mark_asset_ref="assets/fcc-mark.svg")
    payload = fcc_semantic_projection(spec)
    carrier = []
    for item in payload["left_blocks"] + payload["right_blocks"]:
        if item["kind"] == "list":
            carrier.append(node("list", [node("list_item", [text(v)]) for v in item["items"]], ordered=False))
        else:
            carrier.append(node("paragraph", [text(" ".join(filter(None, [item.get("label"), item["text"]])))]))
    # Printed under MEANING OF SYMBOLS without a heading of its own. The generic
    # docutils container keeps that heading visible: the shared FCC style hides
    # the heading of a section whose direct child is the FCC figure.
    flow = component_flow_node(spec, carrier_flow=tuple(carrier))
    return root(node("group", [flow], role="container", presentation=attrs("docutils container")))


def safety() -> list[dict]:
    warning = callout("safety.warn.label", [
        strong_p("safety.warn.lead"),
        node("list", items([f"safety.w{i}" for i in range(1, 12)]), ordered=False),
    ], "warning", "native-pdf/page-4/warning")
    operating = []
    for i in range(1, 16):
        key = f"op.i{i}"
        children = [p(key)]
        for sub in ("a", "b", "c"):
            if f"{key}.{sub}" in T.rows:
                children.append(p(f"{key}.{sub}"))
        operating.append(node("list_item", children))
    danger = callout("danger.label", [node("paragraph", [node("strong", [text(T("danger.l1"))])]),
                                      node("paragraph", [text("※ "), node("strong", [text(T("danger.l2")[2:])])])],
                     "danger", "native-pdf/page-5/danger")
    signal = symbol_signal_component_spec(
        accessibility_label=T.rows["sym.h"]["text"],
        headers=[pair(T("sig.th1"), "content"), pair(T("sig.th2"), "content")],
        rows=[{"label": T(f"sig.{k}.l"), "show_icon": True, **pair(T(f"sig.{k}.m"), "meaning")}
              for k in ("warn", "caut")],
        source_ref="native-pdf/page-5/signal", language=LANGUAGE)
    headers = [pair(T(f"sym.th{i}"), "content") for i in range(1, 5)]
    meanings = [T(k) for k, _ in SYMBOLS]
    icons = symbol_icon_component_spec(
        accessibility_label=T.rows["sym.h"]["text"], headers=headers,
        panels=[[{"asset_index": i, "icon_alt": meanings[i], **pair(meanings[i], "meaning")} for i in rows]
                for rows in (range(0, 4), range(4, 8))],
        icon_refs=[ref for _, ref in SYMBOLS], source_ref="native-pdf/page-5/symbols", language=LANGUAGE)
    return [chapter_heading("safety.h", "native-important-safety-information"),
            heading("safety.band"), warning,
            heading("op.h"), heading("op.save", level=4), root(node("list", operating, ordered=False)),
            danger, heading("maint.h"), para("maint.p"),
            heading("sym.h"), component_flow_node(signal, root=True), component_flow_node(icons, root=True), fcc()]


def in_the_box() -> list[dict]:
    refs = ["inbox-unit", "inbox-cable", "inbox-wrench", "inbox-manual", "inbox-usbc"]
    cards = [{"image_ref": f"assets/{ref}.png", "label": T(f"box.c{i}"), "alt": T.rows[f"box.c{i}"]["text"]}
             for i, ref in enumerate(refs, 1)]
    title = T.rows["box.h"]["text"]
    tip_label, tip_body = T("box.tip.l"), T("box.tip")
    spec = inbox_component_spec(accessibility_label=title, cards=cards, tip_label=tip_label, tip_body=tip_body,
                                source_ref="native-pdf/page-6/inbox", language=LANGUAGE)
    carrier = table([[node("table_cell", [node("image", source=c["image_ref"], alt=c["alt"]),
                                          node("paragraph", [text(c["label"])])], header=False) for c in cards]])
    tip = table([[node("table_cell", [text(tip_label)], header=False),
                  node("table_cell", [text(tip_body)], header=False)]])
    return [chapter_heading("box.h", "native-whats-in-the-box"),
            component_flow_node(spec, carrier_flow=(carrier, tip), root=True)]


def overview() -> list[dict]:
    front = ["lcd", "dcbtn", "cig", "cig.v", "acbtn", "main", "usbc", "usbc.v", "usba", "usba.v", "usbbtn", "ac",
             "ac.nema", "ac.v1", "ac.v2", "ac.v3", "ac.v4", "tl", "tl.v", "tr", "tr.v"]
    left = ["handle", "exp", "exp.a", "exp.in", "exp.out", "l14", "l14.v", "l14.d", "1450", "1450.v", "1450.d",
            "reset", "reset.d", "brake", "wheels"]
    right = ["handle", "handle.d", "low", "low.v1", "low.v2", "high", "high.v", "switch", "switch.d", "acin",
             "acin.v", "dcexp", "dcexp.d", "bottom"]
    return [chapter_heading("names.h", "native-product-overview"),
            heading("names.front.h"), figure("overview-front", 6, [f"names.f.{k}" for k in front]),
            heading("names.left.h"), figure("overview-left", 7, [f"names.l.{k}" for k in left]),
            heading("names.right.h"), figure("overview-right", 7, [f"names.r.{k}" for k in right])]


# (number, row key, icon, description line count)
LCD_ROWS = [(1, "1", "01-wifi", 3), (2, "2", "02-bluetooth", 3), (3, "3", "03-quiet-charging", 2),
            (4, "4", "04-battery-saving", 2), (5, "5", "05-charging-plan", 1), (6, "6", "06-online-ups", 2),
            (7, "7", "07-ac-power", 1), (8, "8", "08-input-power", 1), (9, "9", "09-remaining-charge-time", 1),
            (10, "10", "10-ac-wall-charging", 1), (11, "11", "11-car-charging", 1), (12, "12a", "12a-high-pv", 1),
            (12, "12b", "12b-low-pv", 1), (13, "13a", "13a-ac-expansion-charging", 1),
            (13, "13b", "13b-ac-expansion-discharging", 1), (14, "14", "14-smart-transfer-switch", 1),
            (15, "15", "15-battery-power", 1), (16, "16", "16-low-battery", 3), (17, "17", "17-remaining-battery", 1),
            (18, "18", "18-battery-pack", 1), (19, "19", "19-fault-code", 1), (20, "20a", "20a-high-temperature", 1),
            (20, "20b", "20b-low-temperature", 1), (21, "21", "21-energy-saving", 2), (22, "22", "22-output-power", 1),
            (23, "23", "23-remaining-discharge-time", 1)]


def lcd() -> list[dict]:
    values, refs = [], []
    for index, (number, row, icon, count) in enumerate(LCD_ROWS):
        name = T(f"lcd.r{row}.t")
        name_html, name_text = escape(name), name
        if f"lcd.r{row}.n" in T.rows:
            hint = T(f"lcd.r{row}.n")
            name_html += f"<br/><small>{escape(hint)}</small>"
            name_text += " " + hint
        keys = [f"lcd.r{row}.d{d}" for d in range(1, count + 1)]
        texts = [T.rows[k]["text"] for k in keys]
        values.append({**pair(CIRCLED[number - 1], "number"), "name_html": name_html, "name_text": name_text,
                       "description_html": "<br/>".join(T.html(k) for k in keys),
                       "description_text": " ".join(texts), "icon_alt": name, "asset_index": index})
        refs.append(f"assets/lcd-{icon}.svg")
    spec = lcd_icon_component_spec(accessibility_label=T.rows["lcd.h"]["text"], rows=values, icon_refs=refs,
                                   source_ref="native-pdf/pages-8-9/lcd-icons", language=LANGUAGE,
                                   icon_locale_policy="exact",
                                   metadata={"number_cell_layout": "span-adjacent-equal"})
    return [chapter_heading("lcd.h", "native-lcd-display"),
            figure("lcd-map", 8, [], label=T.rows["lcd.h"]["text"]),
            component_flow_node(spec, root=True)]


def lcd_mode() -> dict:
    groups = []
    for state in ("s1", "s2"):
        actions = []
        for action in ("on", "off", "auto"):
            name, description = T(f"lcdm.{state}.{action}"), T(f"lcdm.{state}.{action}.d")
            actions.append({**pair(name, "action"), **pair(description, "description")})
        groups.append({**pair(T(f"lcdm.{state}"), "state"), "actions": actions})
    spec = lcd_mode_component_spec(accessibility_label=T.rows["ops.lcd.h"]["text"], groups=groups,
                                   artwork_ref="assets/lcd-button.png", artwork_locale_policy="exact",
                                   source_ref="native-pdf/page-11/lcd-mode", language=LANGUAGE)
    return component_flow_node(spec, root=True)


BUTTONS = {"Main Power Button": "assets/button-power.svg", "USB Power Button": "assets/button-usb.svg",
           "AC Power Button": "assets/button-ac.svg", "DC Power Button": "assets/button-dc.svg"}


def key_combinations() -> list[dict]:
    headers = [T(f"keys.th{i}") for i in (1, 2, 3)]
    rows, body = [], []

    def button(name: str) -> dict:
        return node("group", [node("image", source=BUTTONS[name], alt=""),
                              node("inline_group", [node("strong", [text(name)])])],
                    role="container", presentation=attrs("hb-key-button"))

    for r in (1, 2, 3, 4):
        first, second = T(f"keys.r{r}.b1"), T(f"keys.r{r}.b2")
        duration, operation, function = T(f"keys.r{r}.dur"), T(f"keys.r{r}.op"), T(f"keys.r{r}.fn")
        rows.append([f"{first} + {second}", f"{duration} {operation}", function])
        pair_cell = node("group", [button(first),
                                   node("inline_group", [text("+")], presentation=attrs("hb-key-button-plus")),
                                   button(second)],
                         role="container", presentation=attrs("hb-key-button-pair"))
        body.append(node("table_row", [
            node("table_cell", [pair_cell], header=False),
            node("table_cell", [node("paragraph", [text(duration)],
                                     presentation=attrs("hb-key-duration", **{"data-duration-icon": "clock"})),
                                node("paragraph", [text(operation)])], header=False),
            node("table_cell", [text(function)], header=False)]))
    spec = key_combinations_component_spec(headers=headers, rows=rows, source_ref="native-pdf/page-12/keys",
                                           language=LANGUAGE)
    carrier = node("table", [node("table_head", [node("table_row", [
        node("table_cell", [text(h)], header=True) for h in headers])]), node("table_body", body)],
        presentation=attrs("hb-key-combination-table"))
    return [heading("keys.h"), component_flow_node(spec, carrier_flow=(carrier,), root=True)]


def operations() -> list[dict]:
    on_off = ["on", "on.a", "off", "off.a"]
    return [chapter_heading("ops.h", "native-operations"),
            callout_lines("ops.note.l", ["ops.note"], "note", "native-pdf/page-10/note"),
            heading("ops.power.h"),
            figure("power", 10, [f"fig.power.{k}" for k in [*on_off, "dur"]]),
            panel([p("ops.power.box.t"), node("list", items(["ops.power.box.b", "ops.power.box.c"]), ordered=False)]),
            heading("ops.ac.h"), panel([p("ops.ac.pre")]),
            figure("ac-output", 10, [f"fig.ac.{k}" for k in on_off]),
            heading("ops.usb.h"), panel([p("ops.usb.pre")]),
            figure("usb-output", 11, [f"fig.usb.{k}" for k in on_off]),
            heading("ops.dc.h"), panel([p("ops.dc.pre")]), para("ops.dc.warn"),
            figure("dc-output", 11, [f"fig.dc.{k}" for k in on_off]),
            heading("ops.lcd.h"), lcd_mode(),
            *key_combinations()]


def troubleshooting() -> list[dict]:
    """Error Code / Name / Description: three printed columns (declared plain table)."""
    head = node("table_head", [node("table_row", [node("table_cell", [text(T(f"ts.th{i}"))], header=True)
                                                  for i in (1, 2, 3)])])
    rows = []
    for code in ("f0", "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "fa", "fc"):
        descriptions = []
        for d in range(1, 5):
            key = f"ts.{code}.d{d}"
            if key in T.rows:
                if descriptions:
                    descriptions.append(node("line_break"))
                descriptions.append(text(T(key)))
        rows.append(node("table_row", [
            node("table_cell", [node("strong", [text(T(f"ts.{code}.c"))])], header=False),
            node("table_cell", [node("strong", [text(T(f"ts.{code}.n"))])], header=False),
            node("table_cell", descriptions, header=False)]))
    group = node("group", [node("table", [head, node("table_body", rows)], presentation=attrs("manual-table"))],
                 role="container", presentation=attrs("table-wrapper docutils container"))
    return [chapter_heading("ts.h", "native-troubleshooting"), root(group)]


def ups() -> list[dict]:
    return [chapter_heading("ups.h", "native-ups"), para("ups.p1"), para("ups.p2"),
            heading("ups.b.h"), para("ups.b.p1"), para("ups.b.p2"),
            figure("ups", 13, [], label=T.rows["ups.b.h"]["text"]), panel([p("ups.bubble")]),
            heading("ups.o.h"), para("ups.o.p"), para("ups.o.l1"), para("ups.o.l2"),
            callout_lines("ups.note.l", ["ups.n1", "ups.n2", "ups.n3"], "note", "native-pdf/page-13/note")]


def connections() -> list[dict]:
    return [chapter_heading("con.h", "native-connections"),
            sold_heading("con.bp.h", "con.bp.sold"), para("con.bp.p"),
            figure("battery-packs", 14, ["fig.bp.gap1", "fig.bp.gap2"]),
            callout_lines("con.bp.caut.l", ["con.bp.c1", "con.bp.c2"], "caution", "native-pdf/page-14/caution"),
            sold_heading("con.sts.h", "con.sts.sold"),
            figure("sts-connect", 14, [], label=T.rows["con.sts.h"]["text"]), panel([p("con.sts.p")])]


def charging() -> list[dict]:
    return [chapter_heading("chg.h", "native-charging"), para("chg.green"), para("chg.green2"),
            strong("chg.first"),
            callout_lines("chg.note.l", ["chg.n1", "chg.n2"], "note", "native-pdf/page-15/note"),
            heading("chg.ac.h"), figure("ac-charge", 15, [], label=T.rows["chg.ac.h"]["text"]), para("chg.ac.p"),
            heading("chg.sts.h"), para("chg.sts.p1"), para("chg.sts.p2"),
            figure("sts-charge", 15, ["fig.sts.s1", "fig.sts.s2", "fig.sts.app"]),
            callout_lines("chg.sts.note.l", ["chg.sts.note"], "note", "native-pdf/page-15/note-sts"),
            heading("chg.solar.h"),
            callout_lines("chg.solar.caut.l", ["chg.solar.caut"], "caution", "native-pdf/page-16/caution-series"),
            heading("chg.low.h", level=4), para("chg.low.range"), para("chg.low.p"),
            figure("low-pv-500", 16, ["fig.low1.dc", "fig.low1.cap"]),
            figure("low-pv-200", 16, ["fig.low2.dc1", "fig.low2.dc2", "fig.low2.cap"]),
            callout_lines("chg.low.caut.l", ["chg.low.c1", "chg.low.c2", "chg.low.c3"], "caution",
                          "native-pdf/page-16/caution-low-pv"),
            heading("chg.high.h", level=4), para("chg.high.range"),
            callout_lines("chg.high.caut.l", ["chg.high.c1", "chg.high.c2", "chg.high.c3"], "caution",
                          "native-pdf/page-17/caution-high-pv"),
            panel([p("chg.high.mc4")]), figure("high-pv", 17, [], label=T.rows["chg.high.h"]["text"]),
            strong("chg.lock.h"), para("chg.lock.p"), strong("chg.unlock.h"), para("chg.unlock.p"),
            figure("high-pv-lock", 17, [], label=T.rows["chg.lock.h"]["text"] + " / " + T.rows["chg.unlock.h"]["text"]),
            heading("chg.dual.h", level=4), para("chg.dual.l1"), para("chg.dual.l2"),
            figure("dual-pv", 18, [], label=T.rows["chg.dual.h"]["text"]),
            heading("chg.car.h"), para("chg.car.p"),
            figure("car-charge", 18, ["fig.car.vehicle"]), panel([p("chg.car.note")]),
            callout_lines("chg.car.caut.l", ["chg.car.c1", "chg.car.c2", "chg.car.c3"], "caution",
                          "native-pdf/page-18/caution-car")]


def warranty() -> list[dict]:
    def block(key: str) -> dict:
        return {"kind": "paragraph", "html": f"<p>{T.html(key)}</p>", "text": T.rows[key]["text"]}

    def section(index: int, title_key: str, blocks: list[dict]) -> list[dict]:
        # The shared card draws the body; its printed title pill is the heading before it.
        title = heading(title_key)
        spec = warranty_section_component_spec(title=T.rows[title_key]["text"], section_index=index, blocks=blocks,
                                               source_ref=f"native-pdf/page-19/warranty-{index}", language=LANGUAGE)
        return [title, component_flow_node(spec, root=True)]

    lead_text, note_text = T("war.lead"), T("war.note")
    lead = warranty_lead_component_spec(accessibility_label=T.rows["war.h"]["text"],
                                        lead_html=f"<p><strong>{escape(lead_text)}</strong></p>",
                                        local_note_html=f"<p>{escape(note_text)}</p>",
                                        source_ref="native-pdf/page-19/lead", language=LANGUAGE)
    periods = []
    for y in ("y1", "y2"):
        body = T(f"war.{y}.b")
        periods.append({"number": T(f"war.{y}.n"), "unit": T(f"war.{y}.u"), "label": T(f"war.{y}.l"),
                        "body_html": f"<p>{escape(body)}</p>", "body_text": body})
    period_title = heading("war.per.h")
    years = warranty_years_component_spec(title=T.rows["war.per.h"]["text"], periods=periods,
                                          source_ref="native-pdf/page-19/period", language=LANGUAGE)
    return [chapter_heading("war.h", "native-warranty"), component_flow_node(lead, root=True),
            *section(1, "war.lim.h", [block("war.lim.p1"), block("war.lim.p2")]),
            period_title, component_flow_node(years, root=True),
            *section(2, "war.rep.h", [block("war.rep.p")]),
            *section(3, "war.buy.h", [block("war.buy.p")]),
            *section(4, "war.exc.h", [block("war.exc.lead"), block("war.exc.l1"), block("war.exc.l2"),
                                      block("war.exc.l3"), block("war.exc.l4")]),
            *section(5, "war.int.h", [block("war.int.p")])]


def app_setup() -> list[dict]:
    columns = [{"role": "store", "text": T("app.s1.store")}, {"role": "qr", "text": T("app.s1.qr")}]
    for column in columns:
        column["html"] = escape(column["text"])
    download = app_download_component_spec(
        accessibility_label="Jackery App", columns=columns, source_art_ref="assets/app-qr.png",
        store_art_ref="assets/app-store.png", qr_art_ref="assets/app-qr.png",
        source_ref="native-pdf/page-20/download", language=LANGUAGE)
    carrier = [node("image", source="assets/app-store.png", alt="App Store / Google Play"),
               node("paragraph", [text(columns[0]["text"])]),
               node("image", source="assets/app-qr.png", alt="Jackery App"),
               node("paragraph", [text(columns[1]["text"])])]
    before, after = T("app.s21").split(" [+] ")
    plus = app_inline_control_component_spec(
        accessibility_label="+", paragraph_html=f"{escape(before)} <strong>+</strong> {escape(after)}",
        paragraph_text=f"{before} + {after}", source_ref="native-pdf/page-20/add-button", language=LANGUAGE,
        metadata={"visual_recovery": "pdf-vector-plus-control"})
    plus_carrier = node("paragraph", [text(before + " "), node("strong", [text("+")]), text(" " + after)])
    remark2 = callout("app.rem2.l", [p("app.rem2"), node("list", items(["app.rem2.l1", "app.rem2.l2"]), ordered=False)],
                      "note", "native-pdf/page-21/remarks-bound")
    return [chapter_heading("app.h", "native-app-setup"),
            heading("app.s1.h"), component_flow_node(download, carrier_flow=carrier, root=True),
            heading("app.s2.h"), component_flow_node(plus, carrier_flow=(plus_carrier,), root=True),
            para("app.s22"),
            figure("app-add", 20, ["fig.app.c21", "fig.app.c22"]),
            figure("app-control", 20, ["fig.ctl.dc", "fig.ctl.ac", "fig.ctl.main", "fig.ctl.usb"]),
            callout_lines("app.rem1.l", ["app.rem1"], "note", "native-pdf/page-20/remarks"),
            para("app.s23"), remark2, para("app.s24"),
            callout_lines("app.rem3.l", ["app.rem3"], "note", "native-pdf/page-21/remarks-band"),
            para("app.s25"),
            figure("app-results", 21, ["fig.app.c23", "fig.app.c24", "fig.app.c25"]),
            para("app.shots"),
            heading("app.s3.h"), para("app.s3"),
            heading("app.s4.h"),
            heading("app.s41.h", level=4), bullets(["app.s41.l1", "app.s41.l2"]),
            heading("app.s42.h", level=4), bullets(["app.s42.l1", "app.s42.l2"]),
            heading("app.s43.h", level=4), bullets(["app.s43.l1"])]


def spec_tables(prefix: str, groups: list[tuple[str, list[tuple[str, list[str]]]]], page: int) -> list[dict]:
    flows = []
    for title_key, rows_spec in groups:
        title = T(prefix + title_key)
        rows: list[tuple[str, str]] = []
        for label_key, value_keys in rows_spec:
            values = [T(prefix + k) for k in value_keys] or [""]
            # Each printed value row is its own row; a label printed once spans them.
            rows.append((T(prefix + label_key), values[0]))
            rows.extend(("", value) for value in values[1:])
        spec = spec_table_component_spec(section_title=title, rows=rows,
                                         source_ref=f"native-pdf/page-{page}/{prefix}{title_key}", language=LANGUAGE)
        flows.append(component_flow_node(spec, carrier_flow=_spec_carrier(title, rows), root=True))
    return flows


def labelled(key: str, *values: str) -> tuple[str, list[str]]:
    return f"{key}.l", [f"{key}.{v}" for v in values]


EXPLORER_SPEC = [
    ("gen.h", [labelled(f"g{i}", "v") for i in range(1, 12)]),
    ("in.h", [labelled("i1", "v"), labelled("i2", "v1", "v2"), labelled("i3", "v"), labelled("i4"),
              labelled("i5", "v"), labelled("i6", "v"), labelled("i7", "v1", "v2")]),
    ("out.h", [labelled(f"o{i}", "v") for i in range(1, 10)]),
    ("env.h", [labelled("e1", "v"), labelled("e2", "v1", "v2")]),
]


def ingestion(key: str) -> dict:
    """The INGESTION HAZARD notice with its printed glyph (shared catalog variant)."""
    return root(node("paragraph", [node("image", source="assets/ingestion-hazard.svg", alt=""), text(" "),
                                   *T.inline(key)]))


def specifications() -> list[dict]:
    return [chapter_heading("spec.h", "native-specifications"), *spec_tables("spec.", EXPLORER_SPEC, 22),
            ingestion("spec.ing"), para("spec.tm")]


def band(title_key: str, model_key: str, anchor: str) -> list[dict]:
    """A dark product band of the AC ESS guide: the product name (chapter strip) and its model."""
    return [chapter_heading(title_key, anchor), strong(model_key)]


def ac_ess() -> list[dict]:
    caution = callout_lines("ess.caut.l", [f"ess.c{i}" for i in range(1, 11)], "caution", "native-pdf/page-23/caution")
    battery = [("gen.h", [labelled(f"g{i}", "v") for i in range(1, 10)])]
    battery_rest = [("io.h", [labelled("io1", "v"), labelled("io2", "v")]),
                    ("env.h", [labelled("e1", "v"), labelled("e2", "v")])]
    sts = [("gen.h", [labelled(f"g{i}", "v") for i in range(1, 18)])]
    return [chapter_heading("ess.h", "native-ac-ess-installation-guide"),
            panel([strong_p("ess.model.l"), p("ess.model")]),
            para("ess.p1"), para("ess.p2"),
            figure("ess", 23, [], label=T.rows["ess.h"]["text"]), para("ess.cap"), caution,
            *band("ess.e.h", "ess.e.model", "native-explorer-5000-plus"), heading("ess.e.spec"),
            *spec_tables("ess.e.", EXPLORER_SPEC, 24), ingestion("ess.e.ing"), para("ess.e.tm"),
            *band("ess.b.h", "ess.b.model", "native-battery-pack-5000-plus"), sold_heading("ess.b.spec", "ess.b.sold"),
            *spec_tables("ess.b.", battery, 25), para("ess.b.only"), *spec_tables("ess.b.", battery_rest, 25),
            ingestion("ess.b.ing"),
            *band("ess.s.h", "ess.s.model", "native-smart-transfer-switch"), sold_heading("ess.s.spec", "ess.s.sold"),
            *spec_tables("ess.s.", sts, 25), para("ess.s.mains"),
            callout_lines("ess.note.l", ["ess.note"], "note", "native-pdf/page-26/note"),
            heading("ess.pkg.h"),
            figure("package-unit", 26, [f"fig.pkg.u{i}" for i in range(1, 6)]),
            figure("package-battery", 26, ["fig.pkg.b1", "fig.pkg.b2", "fig.pkg.b3", "fig.pkg.b.sold"]),
            figure("package-sts", 26, [*(f"fig.pkg.s{i}" for i in range(1, 9)), "fig.pkg.s.sold"])]


CHAPTERS = (
    ("important", "IMPORTANT", important),
    ("safety", "IMPORTANT SAFETY INFORMATION", safety),
    ("in_the_box", "WHAT'S IN THE BOX", in_the_box),
    ("product_overview", "PRODUCT OVERVIEW", overview),
    ("lcd_display", "LCD DISPLAY", lcd),
    ("operations", "OPERATIONS", operations),
    ("troubleshooting", "TROUBLESHOOTING", troubleshooting),
    ("ups", "UNINTERRUPTIBLE POWER SUPPLY (UPS)", ups),
    ("connections", "CONNECTIONS", connections),
    ("charging", "CHARGING", charging),
    ("warranty", "WARRANTY", warranty),
    ("app_setup", "APP SETUP", app_setup),
    ("specifications", "SPECIFICATIONS", specifications),
    ("ac_ess", "SMART HOME BACKUP SYSTEM (AC ESS) INSTALLATION GUIDE", ac_ess),
)


def build() -> dict:
    chapters = [{"id": cid, "title": title, "nodes": make()} for cid, title, make in CHAPTERS]
    missing = [k for k in T.rows if k not in T.used]
    if missing:
        raise ValueError("Web transcription lines not bound: " + ", ".join(missing))
    return {"model": "JE-5000A", "region": "US", "language": LANGUAGE,
            "title": "Jackery Explorer 5000 Plus User Manual", "source_sha256": SOURCE_SHA256,
            "chapters": chapters}


def main() -> None:
    content = build()
    path = PACKAGE / "source/en/content.json"
    path.write_text(json.dumps(content, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"chapters": [c["id"] for c in content["chapters"]], "lines": len(T.used)}))


if __name__ == "__main__":
    main()
