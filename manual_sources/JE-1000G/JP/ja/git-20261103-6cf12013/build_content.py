"""Bind the reviewed JE-1000G JP transcription to shared Web components.

Run from the repository root:

    python manual_sources/JE-1000G/JP/ja/git-20261103-6cf12013/build_content.py

Every Web string comes from ``source/transcription.json`` by line id; this
module only decides which shared component carries each printed block, in
printed order. It writes ``source/ja/content.json``, the frozen input that
``rebuild.py`` replays. Component chrome follows the JE-1000D JP V2 and
JE-2000F US/en packages (same prepared-document flow and 1000 New / V2 layout
generation); ``source/differences.md`` lists every layout decision.
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
from tools.component_specs.auto_resume import auto_resume_component_spec  # noqa: E402
from tools.component_specs.callout import callout_component_spec  # noqa: E402
from tools.component_specs.inbox import inbox_component_spec  # noqa: E402
from tools.component_specs.key_combinations import key_combinations_component_spec  # noqa: E402
from tools.component_specs.lcd_mode import lcd_mode_component_spec  # noqa: E402
from tools.component_specs.manual_tables import (  # noqa: E402
    lcd_icon_component_spec, symbol_icon_component_spec, symbol_signal_component_spec,
    troubleshooting_component_spec,
)
from tools.component_specs.reference_figure import reference_figure_component_spec  # noqa: E402
from tools.component_specs.spec_table import spec_table_component_spec  # noqa: E402
from tools.component_specs.warranty import warranty_section_component_spec  # noqa: E402
from tools.manual_ir.components import component_flow_node  # noqa: E402
from tools.web.composite_hashing import reference_source_fragment_sha256  # noqa: E402
from tools.web.frozen_ai_flow import node, root, table, text  # noqa: E402
from tools.web.frozen_ai_table_components import _spec_carrier  # noqa: E402

LANGUAGE = "ja"
CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳㉑㉒㉓㉔㉕"
ECO_ICON = "assets/lcd-energy-saving.svg"


def attrs(css: str, **extra: str) -> dict:
    return {"html": {"attributes": {"class": css, **extra}}}


class Lines:
    """Line lookup that records every id used, so coverage can be checked.

    A symbol caption marked ``pending_shared_symbol`` is withheld from the Web
    until its shared symbol variant exists; it is not part of the coverage.
    """

    def __init__(self) -> None:
        source = json.loads((PACKAGE / "source/transcription.json").read_text(encoding="utf-8"))
        self.rows = {line["id"]: line for page in source["pages"] if page["web"] for line in page["lines"]
                     if not line.get("pending_shared_symbol")}
        self.used: list[str] = []

    def __call__(self, key: str) -> str:
        if key in self.used:
            raise ValueError("transcription line bound twice: " + key)
        self.used.append(key)
        return self.rows[key]["text"]

    def spans(self, key: str) -> list[tuple[str, str]]:
        """(style, text) runs: plain, strong or sub, in printed order."""
        value = self(key)
        marks = [(s, "strong") for s in self.rows[key].get("strong", [])]
        marks += [(s, "sub") for s in self.rows[key].get("subscript", [])]
        runs: list[tuple[str, str]] = []
        cursor = 0
        for span, style in sorted(marks, key=lambda m: value.index(m[0])):
            start = value.index(span, cursor)
            if start > cursor:
                runs.append(("plain", value[cursor:start]))
            runs.append((style, span))
            cursor = start + len(span)
        if cursor < len(value):
            runs.append(("plain", value[cursor:]))
        return runs

    def inline(self, key: str) -> list[dict]:
        kinds = {"strong": "strong", "sub": "subscript"}
        return [text(value) if style == "plain" else node(kinds[style], [text(value)])
                for style, value in self.spans(key)]

    def html(self, key: str) -> str:
        tags = {"strong": "strong", "sub": "sub"}
        return "".join(escape(value) if style == "plain" else f"<{tags[style]}>{escape(value)}</{tags[style]}>"
                       for style, value in self.spans(key))


T = Lines()


# --- flow helpers -----------------------------------------------------------

def p(key: str) -> dict:
    return node("paragraph", T.inline(key))


def para(key: str) -> dict:
    return root(p(key))


def strong_p(key: str) -> dict:
    return node("paragraph", [node("strong", [text(T(key))])])


def strong_para(key: str) -> dict:
    return root(strong_p(key))


def heading(key: str, level: int = 3, anchor: str | None = None) -> dict:
    return root(node("heading", [text(T(key))], level=level, **({"anchor": anchor} if anchor else {})))


def chapter_heading(key: str, anchor: str) -> dict:
    return heading(key, level=2, anchor=anchor)


def items(keys: list[str]) -> list[dict]:
    return [node("list_item", [p(k)]) for k in keys]


def ul(keys: list[str], ordered: bool = False) -> dict:
    return node("list", items(keys), ordered=ordered)


def bullets(keys: list[str], ordered: bool = False) -> dict:
    return root(ul(keys, ordered))


def panel(children: list[dict]) -> dict:
    """Shared grey text panel (web_manual.css ``.hb-text-panel``)."""
    return root(node("group", children, role="container", presentation=attrs("hb-text-panel")))


def icon(ref: str, alt: str) -> dict:
    return node("image", source=ref, alt=alt)


def with_icon(key: str) -> dict:
    """A printed line whose [88H] mark is the inline LCD energy-saving glyph."""
    before, after = T(key).split("[88H]")
    return node("paragraph", [text(before), icon(ECO_ICON, "88H"), text(after)])


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


def leaves(item: dict) -> list[str]:
    """Visible text runs as the shared callout carrier check reads them (stripped, non-empty)."""
    if item.get("kind") == "text":
        return [item["text"].strip()] if item["text"].strip() else []
    return [part for child in item.get("children", []) for part in leaves(child)]


def callout(label: str, body: list[dict], *, variant: str, ref: str) -> dict:
    """The shared callout carrier (JE-2000F US/en idiom)."""
    list_items = [" ".join(leaves(item)) for block in body if block["kind"] == "list" for item in block["children"]]
    spec = callout_component_spec(label=label, body="\n".join(part for b in body for part in leaves(b)),
                                  items=list_items, variant=variant, language=LANGUAGE, source_ref=ref)
    carrier = table([[node("table_cell", [text(label)], header=False, presentation=attrs("manual-callout-label")),
                      node("table_cell", body, header=False, presentation=attrs("manual-callout-body"))]],
                    css_class=f"manual-callout-table {web_callout_classes(spec)['table']}")
    return component_flow_node(spec, carrier_flow=[carrier])


def callout_block(label_key: str, body: list[dict], variant: str, ref: str) -> dict:
    return root(callout(T(label_key), body, variant=variant, ref=ref))


def callout_list(label_key: str, item_keys: list[str], variant: str, ref: str) -> dict:
    return callout_block(label_key, [ul(item_keys)], variant, ref)


def callout_text(label_key: str, keys: list[str], variant: str, ref: str) -> dict:
    return callout_block(label_key, [p(k) for k in keys], variant, ref)


def safety_item(label: str, variant: str, title_key: str, body: list[dict], ref: str) -> dict:
    """One printed pictogram row of a 警告/注意 band: bold title, then its copy."""
    return root(callout(label, [strong_p(title_key), *body], variant=variant, ref=ref))


def plain_table(head: list[dict] | None, rows: list[list[dict]]) -> dict:
    """A declared plain table on the shared manual-table classes (shared_component_exceptions)."""
    body = node("table_body", [node("table_row", row) for row in rows])
    return root(node("group", [node("table", [head, body] if head else [body], presentation=attrs("manual-table"))],
                     role="container", presentation=attrs("table-wrapper docutils container")))


def cell(children: list[dict], **fields) -> dict:
    return node("table_cell", children, header=False, **fields)


def pair(value: str, key: str) -> dict:
    return {f"{key}_html": escape(value), f"{key}_text": value}


def html_lines(keys: list[str]) -> tuple[str, str]:
    """Printed lines of one cell: HTML joined by line breaks, text joined without a separator."""
    return "<br/>".join(T.html(k) for k in keys), "".join(T.rows[k]["text"] for k in keys)


# --- chapters ---------------------------------------------------------------

SYMBOLS = [("sym.s1", "assets/symbol-01.svg"), ("sym.s2", "assets/symbol-02.svg"),
           ("sym.s4", "assets/symbol-03.svg"), ("sym.s5", "assets/symbol-04.svg"),
           ("sym.s6", "assets/symbol-05.svg"), ("sym.s7", "assets/symbol-06.svg"),
           ("sym.s8", "assets/symbol-07.svg"), ("sym.s9", "assets/symbol-08.svg"),
           ("sym.s10", "assets/symbol-09.svg")]
LEFT_PANEL = 4  # the printed left column (sym.s3 withheld: pending shared symbol)


def safety() -> list[dict]:
    signal = symbol_signal_component_spec(
        accessibility_label=T.rows["pict.h"]["text"],
        headers=[pair("表示", "content"), pair("意味", "content")],
        rows=[{"label": T(f"sig.{k}.l"), "show_icon": k in ("warn", "caut"), **pair(T(f"sig.{k}.m"), "meaning")}
              for k in ("warn", "caut", "note", "tip")],
        source_ref="native-pdf/page-3/signal", language=LANGUAGE)
    meanings = [T(k) for k, _ in SYMBOLS]
    symbols = symbol_icon_component_spec(
        accessibility_label=T.rows["sym.h"]["text"],
        headers=[pair(v, "content") for v in ("記号", "意味", "記号", "意味")],
        panels=[[{"asset_index": i, "icon_alt": meanings[i], **pair(meanings[i], "meaning")} for i in rows]
                for rows in (range(0, LEFT_PANEL), range(LEFT_PANEL, len(SYMBOLS)))],
        icon_refs=[ref for _, ref in SYMBOLS], source_ref="native-pdf/page-3/symbols", language=LANGUAGE,
        icon_locale_policy="exact")
    recycle = plain_table(None, [
        [cell([icon("assets/recycle-li-ion.svg", "Li-ion 32")]),
         cell([strong_p("recycle.title"), p("recycle.b1"), p("recycle.b2"), p("recycle.b3")])],
        [cell([icon("assets/weee.svg", "WEEE")]),
         cell([p("weee.b1"), p("weee.b2"), p("weee.b3")])]])
    w, c = "warning", "caution"
    band1 = T("w1.band")
    first = [safety_item(band1, w, f"w1.i{i}.t", [p(f"w1.i{i}.b")], f"native-pdf/page-4/warning-{i}")
             for i in range(1, 9)]
    band2 = T("w2.band")
    abnormal = safety_item(band2, w, "w2.i1.t", [
        ul([f"w2.i1.l{i}" for i in range(1, 6)]), p("w2.i1.b1"), strong_p("w2.i1.t2"), p("w2.i1.b2"), p("w2.i1.b3"),
    ], "native-pdf/page-5/warning-1")
    second = [safety_item(band2, w, "w2.i2.t", [p("w2.i2.b")], "native-pdf/page-5/warning-2"),
              safety_item(band2, w, "w2.i3.t", [p("w2.i3.b")], "native-pdf/page-5/warning-3"),
              safety_item(band2, w, "w2.i4.t", [], "native-pdf/page-5/warning-4")]
    band3 = T("c1.band")
    cautions = [safety_item(band3, c, "c1.i1.t", [p("c1.i1.b")], "native-pdf/page-5/caution-1"),
                safety_item(band3, c, "c1.i2.t", [ul(["c1.i2.l1", "c1.i2.l2", "c1.i2.l3"])],
                            "native-pdf/page-5/caution-2"),
                safety_item(band3, c, "c1.i3.t", [p("c1.i3.b")], "native-pdf/page-5/caution-3"),
                safety_item(band3, c, "c1.i4.t", [], "native-pdf/page-5/caution-4")]
    return [chapter_heading("safety.h", "native-safety"), strong_para("safety.lead"),
            heading("pict.h"), para("pict.p1"), para("pict.p2"), component_flow_node(signal, root=True),
            heading("sym.h"), component_flow_node(symbols, root=True), recycle,
            *first, abnormal, *second, *cautions]


def precautions() -> list[dict]:
    g5 = [node("list_item", [p("prec.g5.l1")]),
          node("list_item", [p("prec.g5.l2"), ul(["prec.g5.l2a", "prec.g5.l2b"])]),
          node("list_item", [p("prec.g5.l3")])]
    return [chapter_heading("prec.h", "native-usage-precautions"),
            panel([p(f"prec.p{i}") for i in range(1, 5)]),
            callout_text("prec.c.l", ["prec.c"], "caution", "native-pdf/page-6/caution"),
            strong_para("prec.g1.h"), para("prec.g1.p"), bullets([f"prec.g1.l{i}" for i in range(1, 5)]),
            strong_para("prec.g2.h"), bullets([f"prec.g2.l{i}" for i in range(1, 6)]),
            strong_para("prec.g3.h"), bullets(["prec.g3.l1", "prec.g3.l2"]),
            strong_para("prec.g4.h"), bullets(["prec.g4.l1", "prec.g4.l2", "prec.g4.l3"]),
            strong_para("prec.g5.h"), root(node("list", g5, ordered=False))]


def disclaimer() -> list[dict]:
    return [chapter_heading("disc.h", "native-disclaimer"), panel([ul([f"disc.l{i}" for i in range(1, 7)])])]


def in_the_box() -> list[dict]:
    cards = [{"image_ref": ref, "label": T(key), "alt": T.rows[key]["text"]}
             for key, ref in (("box.c1", "assets/inbox-unit.svg"), ("box.c2", "assets/inbox-ac-cable.svg"),
                              ("box.c3", "assets/inbox-documents.svg"))]
    title = T.rows["box.h"]["text"]
    spec = inbox_component_spec(accessibility_label=title, cards=cards, tip_label="", tip_body="",
                                source_ref="native-pdf/page-8/inbox", language=LANGUAGE, require_tip=False)
    carrier = table([[node("table_cell", [node("image", source=c["image_ref"], alt=c["alt"]),
                                          node("paragraph", [text(c["label"])])], header=False) for c in cards]])
    return [chapter_heading("box.h", "native-in-the-box"), component_flow_node(spec, carrier_flow=(carrier,), root=True),
            panel([p("box.n1"), p("box.n2"), p("box.n3")]), strong_para("box.change")]


def overview() -> list[dict]:
    front = ["ov.f.power", "ov.f.car", "ov.f.car.s", "ov.f.c30", "ov.f.c30.s", "ov.f.c100", "ov.f.c100.s",
             "ov.f.a18", "ov.f.a18.s", "ov.f.dcusb", "ov.f.lcd", "ov.f.ledbtn", "ov.f.led", "ov.f.ac2",
             "ov.f.acout", "ov.f.acout.s", "ov.f.ac1"]
    right = ["ov.r.handle", "ov.r.dcin", "ov.r.dcin.pv", "ov.r.dcin.car", "ov.r.acin", "ov.r.acin.s"]
    return [chapter_heading("names.h", "native-product-overview"),
            heading("names.front"), figure("assets/overview-front.png", "overview-front", 8, front),
            heading("names.right"), figure("assets/overview-right.png", "overview-right", 9, right)]


LCD_ICONS = ["wifi", "bluetooth", "quiet-charging", "charging-plan", "self-powered", "tou", "ups", "ac-power",
             "output-voltage-frequency", "input-power", "remaining-charge-time", "ac-wall-charging", "car-charging",
             "solar-charging", "battery-saving", "charging-power-limit", "battery-power", "low-battery",
             "remaining-battery-percentage", "discharge-timer", "energy-saving", "high-temperature",
             "low-temperature", "fault-code", "output-power", "remaining-discharge-time"]
LCD_NUMBERS = [*range(1, 23), 22, 23, 24, 25]


def lcd() -> list[dict]:
    rows, refs = [], []
    for index, (number, name_icon) in enumerate(zip(LCD_NUMBERS, LCD_ICONS, strict=True)):
        key = f"lcd.d{index + 1}"
        names = [k for k in (f"{key}.t", f"{key}.t2") if k in T.rows]
        name_html, name_text = html_lines(names)
        bodies = sorted((k for k in T.rows if k.startswith(f"{key}.b")), key=lambda k: int(k.rsplit("b", 1)[1]))
        body_html, body_text = html_lines(bodies)
        rows.append({"number_html": CIRCLED[number - 1], "number_text": CIRCLED[number - 1],
                     "name_html": name_html, "name_text": name_text, "description_html": body_html,
                     "description_text": body_text, "icon_alt": T.rows[f"{key}.t"]["text"], "asset_index": index})
        refs.append(f"assets/lcd-{name_icon}.svg")
    spec = lcd_icon_component_spec(accessibility_label=T.rows["lcd.h"]["text"], rows=rows, icon_refs=refs,
                                   source_ref="native-pdf/pages-10-11/lcd-icons", language=LANGUAGE,
                                   icon_locale_policy="exact", numbered=True)
    return [chapter_heading("lcd.h", "native-lcd-display"),
            figure("assets/lcd-map.svg", "lcd-map", 9, [], label=T.rows["lcd.h"]["text"]),
            component_flow_node(spec, root=True)]


def eco_table() -> dict:
    head = node("table_head", [node("table_row", [node("table_cell", [text(T(f"eco.th{i}"))], header=True)
                                                  for i in (1, 2, 3)])])
    rows = [[cell([text(T("eco.r1.c1"))]), cell([text(T("eco.r1.c2"))]),
             cell([text(T("eco.default"))], row_span=2)],
            [cell([text(T("eco.r2.c1"))]), cell([text(T("eco.r2.c2"))])]]
    return plain_table(head, rows)


def key_cell(left_key: str, left_art: str, right_key: str, right_art: str) -> dict:
    def button(key: str, art: str) -> dict:
        return node("group", [node("image", source=art, alt=""), node("paragraph", T.inline(key))],
                    role="container", presentation=attrs("hb-key-button"))
    return node("table_cell", [node("group", [
        button(left_key, left_art), node("inline_group", [], presentation=attrs("hb-key-button-plus")),
        button(right_key, right_art)], role="container", presentation=attrs("hb-key-button-pair"))], header=False)


KEY_ROWS = [("assets/button-power.svg", "assets/button-ac1.svg"),
            ("assets/button-power.svg", "assets/button-dc-usb.svg"),
            ("assets/button-ac1.svg", "assets/button-dc-usb.svg"),
            ("assets/button-power.svg", "assets/button-light.svg")]


def key_combinations() -> dict:
    headers = [T(f"key.th{i}") for i in (1, 2, 3)]
    rows, carriers = [], []
    for index, (left_art, right_art) in enumerate(KEY_ROWS, start=1):
        r = f"key.r{index}"
        left, right = T.rows[f"{r}.b1"]["text"], T.rows[f"{r}.b2"]["text"]
        first = key_cell(f"{r}.b1", left_art, f"{r}.b2", right_art)
        duration, operation, function = T(f"{r}.t"), T(f"{r}.o"), T(f"{r}.f")
        rows.append([f"{left} {right}", f"{duration} {operation}", function])
        second = node("table_cell", [
            node("inline_group", [text(duration)],
                 presentation=attrs("hb-key-duration", **{"data-duration-icon": "clock"})),
            node("paragraph", [text(operation)])], header=False)
        carriers.append(node("table_row", [first, second, node("table_cell", [text(function)], header=False)]))
    spec = key_combinations_component_spec(headers=headers, rows=rows,
                                           source_ref="native-pdf/page-16/key-combinations", language=LANGUAGE)
    carrier = node("table", [node("table_head", [node("table_row", [node("table_cell", [text(h)], header=True)
                                                                    for h in headers])]),
                             node("table_body", carriers)], presentation=attrs("hb-key-combination-table"))
    return component_flow_node(spec, carrier_flow=[carrier], root=True)


def lcd_screen() -> dict:
    groups = []
    for state in ("scr.m1", "scr.m2"):
        groups.append({**pair(T(state), "state"), "actions": [
            {**pair(T(f"{state}.a{a}"), "action"), **pair(T(f"{state}.d{a}"), "description")} for a in (1, 2, 3)]})
    spec = lcd_mode_component_spec(accessibility_label=T.rows["scr.h"]["text"], groups=groups,
                                   artwork_ref="assets/lcd-screen.png", artwork_locale_policy="exact",
                                   source_ref="native-pdf/page-15/lcd-screen", language=LANGUAGE)
    return component_flow_node(spec, root=True)


def auto_resume() -> dict:
    spec = auto_resume_component_spec(
        headers=[T("res.th1"), T("res.th2")],
        conditions=[[T(f"res.a{i}") for i in (1, 2, 3)], [T(f"res.n{i}") for i in (1, 2, 3, 4)]],
        source_ref="native-pdf/page-15/auto-resume", language=LANGUAGE)
    return component_flow_node(spec, root=True)


def usage() -> list[dict]:
    return [chapter_heading("use.h", "native-usage"),
            heading("pwr.h"),
            figure("assets/power-on-off.png", "power-on-off", 12,
                   ["fig.pwr.on", "fig.pwr.on.s", "fig.pwr.off", "fig.pwr.off.s", "fig.pwr.3s"]),
            panel([p("pwr.standby"), p("pwr.eco")]),
            heading("ac.h"), panel([p("ac.pre")]),
            figure("assets/ac-output.png", "ac-output", 12, ["fig.ac.on", "fig.ac.on.s", "fig.ac.off", "fig.ac.off.s"]),
            panel([p("ac.note")]),
            heading("freq.h"), panel([p("freq.p1"), p("freq.auto"), p("freq.manual")]),
            figure("assets/frequency.png", "frequency", 13, ["fig.freq.50", "fig.freq.60"]),
            heading("dc.h"), panel([p("dc.pre")]),
            figure("assets/dc-usb-output.png", "dc-usb-output", 13,
                   ["fig.dc.on", "fig.dc.on.s", "fig.dc.off", "fig.dc.off.s"]),
            callout_list("dc.c.l", ["dc.c.i1", "dc.c.i2", "dc.c.i3"], "caution", "native-pdf/page-13/usb-caution"),
            para("car.p1"), para("car.p2"),
            callout_list("car.c.l", ["car.c.i1", "car.c.i2", "car.c.i3"], "caution", "native-pdf/page-14/car-caution"),
            heading("eco.h"), panel([with_icon("eco.p")]), eco_table(),
            panel([with_icon("eco.n1"), p("eco.n2")]),
            figure("assets/energy-saving.png", "energy-saving", 14,
                   ["fig.eco.power", "fig.eco.ac", "fig.eco.3s", "fig.eco.onoff", "fig.eco.hold"]),
            callout_text("eco.note.l", ["eco.note"], "note", "native-pdf/page-14/note"),
            heading("res.h"), para("res.p"), auto_resume(),
            heading("led.h"), panel([p("led.p")]),
            figure("assets/led-light.png", "led-light", 15, ["fig.led.light", "fig.led.sos"]),
            bullets(["led.s1", "led.s2", "led.s3"], ordered=True),
            heading("scr.h"), lcd_screen(), para("scr.app"),
            heading("key.h"), key_combinations()]


def ups() -> list[dict]:
    return [chapter_heading("ups.h", "native-ups"),
            figure("assets/ups.png", "ups", 16, [], label=T.rows["ups.h"]["text"]), panel([p("ups.p")]),
            panel([p("ups.p1"), ul(["ups.l1", "ups.l2", "ups.l3", "ups.l4"]), p("ups.p2"), p("ups.p3"), p("ups.p4")])]


def charging() -> list[dict]:
    solar_caution = callout_block("chg.sol.c.l", [
        p("chg.sol.c.p1"), p("chg.sol.c.p2"), p("chg.sol.c.ex"), ul(["chg.sol.c.i1", "chg.sol.c.i2"]),
    ], "caution", "native-pdf/page-20/solar-caution")
    direct = root(node("list", [node("list_item", [p("chg.sol.d1"), p("chg.sol.d1b"), p("chg.sol.d1c")])],
                       ordered=False))
    adapter = root(node("list", [node("list_item", [p("chg.sol.d2"), ul(["chg.sol.d2a", "chg.sol.d2b"])])],
                        ordered=False))
    return [chapter_heading("chg.h", "native-charging"), strong_para("chg.green.h"), para("chg.green"),
            callout_list("chg.c1.l", ["chg.c1.i1", "chg.c1.i2"], "caution", "native-pdf/page-17/caution-1"),
            callout_list("chg.c2.l", ["chg.c2.i1", "chg.c2.i2", "chg.c2.i3"], "caution", "native-pdf/page-17/caution-2"),
            heading("chg.ac.h"), para("chg.ac.p"),
            figure("assets/charging-ac.png", "charging-ac", 18, ["fig.ac.cap"]),
            callout_text("chg.ac.c.l", ["chg.ac.c"], "caution", "native-pdf/page-18/ac-caution"),
            heading("chg.emg.h", level=4), para("chg.emg1"), para("chg.emg2"), para("chg.emg3"),
            heading("chg.sol.h"), para("chg.sol.p"),
            panel([p("chg.sol.acc.h"), ul(["chg.sol.acc1", "chg.sol.acc2"]), p("chg.sol.acc.n")]),
            direct, figure("assets/charging-solar-200.png", "solar-200", 19, ["fig.sol1"]),
            adapter, figure("assets/charging-solar-100air.png", "solar-100air", 19, ["fig.sol2", "fig.sol2.adapter"]),
            solar_caution, para("chg.sol.voc"),
            heading("chg.car.h"), para("chg.car.lead"), para("chg.car.p"),
            bullets([f"chg.car.l{i}" for i in range(1, 6)]),
            figure("assets/charging-car.png", "charging-car", 20, ["fig.car.vehicle", "fig.car.note"]),
            callout_list("car.c2.l", ["car.c2.i1", "car.c2.i2"], "caution", "native-pdf/page-20/car-caution")]


def troubleshooting() -> list[dict]:
    codes = [(["ts.r1.c1", "ts.r1.c2"], ["ts.r1.m"]), (["ts.r2.c"], ["ts.r2.m"]), (["ts.r3.c"], ["ts.r3.m"]),
             (["ts.r4.c"], [f"ts.r4.s{i}" for i in range(1, 6)]), (["ts.r5.c"], [f"ts.r5.s{i}" for i in range(1, 4)]),
             (["ts.r6.c"], ["ts.r6.m"]), (["ts.r7.c"], ["ts.r7.m"]), (["ts.r8.c"], ["ts.r8.m"])]
    rows = []
    for code_keys, measure_keys in codes:
        code_html, _ = html_lines(code_keys)
        code_text = " ".join(T.rows[k]["text"] for k in code_keys)
        html, value = html_lines(measure_keys)
        rows.append({"code_html": code_html, "code_text": code_text, "measures_html": html, "measures_text": value})
    spec = troubleshooting_component_spec(headers=[pair(T("ts.th1"), "content"), pair(T("ts.th2"), "content")],
                                          rows=rows, source_ref="native-pdf/page-21/troubleshooting",
                                          language=LANGUAGE)
    return [chapter_heading("ts.h", "native-troubleshooting"), para("ts.p1"), para("ts.p2"),
            component_flow_node(spec, root=True)]


def specifications() -> list[dict]:
    nodes = [chapter_heading("spec.h", "native-specifications")]
    for group, count in (("g", 6), ("i", 2), ("o", 7), ("t", 3)):
        title = T(f"spec.{group}.h")
        rows = []
        for index in range(1, count + 1):
            label = T(f"spec.{group}{index}.l")
            values = [T(k) for k in sorted(k for k in T.rows if k.startswith(f"spec.{group}{index}.v"))]
            rows.append((label, "\n".join(values)))
        spec = spec_table_component_spec(section_title=title, rows=rows, source_ref=f"native-pdf/page-22/{group}",
                                         language=LANGUAGE)
        nodes.append(component_flow_node(spec, carrier_flow=_spec_carrier(title, rows), root=True))
    return [*nodes, para("spec.tm"), para("spec.fn1")]


def warranty() -> list[dict]:
    def section(index: int, title_key: str, blocks: list[dict]) -> list[dict]:
        # The shared card draws the body; its printed title pill is the heading before it.
        title = heading(title_key)
        spec = warranty_section_component_spec(title=T.rows[title_key]["text"], section_index=index, blocks=blocks,
                                               source_ref=f"native-pdf/warranty/{index}", language=LANGUAGE)
        return [title, component_flow_node(spec, root=True)]

    def wp(*keys: str) -> dict:
        texts = [T.rows[k]["text"] for k in keys]
        html = "<br/>".join(T.html(k) for k in keys)
        return {"kind": "paragraph", "html": f"<p>{html}</p>", "text": "".join(texts)}

    def wl(*keys: str) -> dict:
        values = [T(k) for k in keys]
        return {"kind": "list", "items": values,
                "html": "<ul>" + "".join(f"<li>{escape(v)}</li>" for v in values) + "</ul>"}

    return [chapter_heading("war.h", "native-warranty"),
            panel([p("war.lead1"), p("war.lead2"), p("war.lead3")]),
            *section(1, "war.per.h", [wl("war.per1", "war.per2"), wp("war.per3", "war.per4"), wp("war.per5"),
                                      wp("war.per.note")]),
            *section(2, "war.scope.h", [wp("war.scope1.t", "war.scope1.b"), wp("war.scope.note"),
                                        wp("war.scope2.t", "war.scope2.b")]),
            *section(3, "war.cond.h", [wp("war.cond.lead"), wl("war.cond.l1", "war.cond.l2", "war.cond.l3")]),
            *section(4, "war.excl.h", [wp("war.excl.lead", *(f"war.excl.l{i}" for i in range(1, 7)))]),
            *section(5, "war.proof.h", [wp("war.proof.lead"), wl("war.proof.l1", "war.proof.l2"),
                                        wp("war.proof.note")]),
            *section(6, "war.cont.h", [wp("war.cont1.t"), wl("war.cont1.l1", "war.cont1.l2"),
                                       wp("war.cont2.t"), wl("war.cont2.l1", "war.cont2.l2"),
                                       wp("war.cont3.t", "war.cont3.lead"),
                                       wl("war.cont3.l1", "war.cont3.l2", "war.cont3.l3"),
                                       wp("war.cont3.after"), wp("war.cont.note")]),
            panel([strong_p("war.disc.h"), *(p(f"war.disc{i}") for i in range(1, 6))]),
            panel([p("contact.web"), p("contact.mail"), p("contact.tel")])]


def app_manual() -> list[dict]:
    columns = [{"role": "store", "text": T("appm.s1.store")}, {"role": "qr", "text": T("appm.s1.qr")}]
    for column in columns:
        column["html"] = escape(column["text"])
    download = app_download_component_spec(
        accessibility_label="Jackery App", columns=columns, source_art_ref="assets/app-qr.png",
        store_art_ref="assets/app-store.png", qr_art_ref="assets/app-qr.png",
        source_ref="native-pdf/page-25/download", language=LANGUAGE)
    carrier = [node("image", source="assets/app-store.png", alt="App Store / Google Play"),
               node("paragraph", [text(columns[0]["text"])]),
               node("image", source="assets/app-qr.png", alt="Jackery App"),
               node("paragraph", [text(columns[1]["text"])])]
    before, after = T("appm.s21").split(" [+] ")
    plus = app_inline_control_component_spec(
        accessibility_label="+", paragraph_html=f"{escape(before)} <strong>+</strong> {escape(after)}",
        paragraph_text=f"{before} + {after}", source_ref="native-pdf/page-25/add-button", language=LANGUAGE,
        metadata={"visual_recovery": "pdf-vector-plus-control"})
    plus_carrier = node("paragraph", [text(before + " "), node("strong", [text("+")]), text(" " + after)])
    note2 = callout_block("appm.note2.l", [p("appm.note2"), ul(["appm.note2.l1", "appm.note2.l2"])], "note",
                          "native-pdf/page-26/note-2")
    return [chapter_heading("appm.h", "native-app-manual"),
            heading("appm.s1.h"), component_flow_node(download, carrier_flow=carrier, root=True),
            heading("appm.s2.h"), component_flow_node(plus, carrier_flow=(plus_carrier,), root=True),
            para("appm.s22"),
            figure("assets/app-add.png", "app-add", 25, ["fig.app.c21", "fig.app.c22"]),
            callout_text("appm.note1.l", ["appm.note1"], "note", "native-pdf/page-25/note-1"),
            figure("assets/app-panel.png", "app-panel", 25, ["fig.ctl.power", "fig.ctl.dcusb", "fig.ctl.ac2",
                                                              "fig.ctl.ac1"]),
            para("appm.s23"), note2, para("appm.s24"),
            callout_text("appm.note3.l", ["appm.note3"], "note", "native-pdf/page-26/note-3"),
            para("appm.s25"),
            figure("assets/app-results.png", "app-results", 26, ["fig.app.c23", "fig.app.c24", "fig.app.c25"]),
            para("appm.shots"),
            callout_text("appm.note4.l", ["appm.note4"], "note", "native-pdf/page-26/note-4"),
            heading("appm.s3.h"), para("appm.s3"),
            heading("appm.s4.h"),
            heading("appm.s41.h", level=4), bullets(["appm.s41.l1", "appm.s41.l2"]),
            heading("appm.s42.h", level=4), bullets(["appm.s42.l1"]),
            heading("appm.s43.h", level=4), bullets(["appm.s43.l1"])]


CHAPTERS = (
    ("safety", "安全上のご注意", safety), ("usage_precautions", "使用上のご注意", precautions),
    ("disclaimer", "免責事項", disclaimer), ("in_the_box", "同梱品", in_the_box),
    ("product_overview", "各部の名称", overview), ("lcd_display", "液晶画面", lcd),
    ("usage", "使い方", usage), ("ups", "UPS 機能", ups), ("charging", "充電方法", charging),
    ("troubleshooting", "トラブルシューティング", troubleshooting), ("specifications", "主な仕様", specifications),
    ("warranty", "保証について", warranty), ("app_setup", "Jackeryアプリ ユーザーマニュアル", app_manual),
)


def build() -> dict:
    chapters = [{"id": cid, "title": title, "nodes": make()} for cid, title, make in CHAPTERS]
    missing = [k for k in T.rows if k not in T.used]
    if missing:
        raise ValueError("Web transcription lines not bound: " + ", ".join(missing))
    return {"model": "JE-1000G", "region": "JP", "language": LANGUAGE,
            "title": "Jackery ポータブル電源 1000 New 取扱説明書",
            "source_sha256": "6cf120136d8366ad37f590610d739e09754ddc38d4c8cd3123d9dca0de132aad",
            "chapters": chapters}


def main() -> None:
    content = build()
    path = PACKAGE / "source/ja/content.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(content, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"chapters": [c["id"] for c in content["chapters"]], "lines": len(T.used)}))


if __name__ == "__main__":
    main()
