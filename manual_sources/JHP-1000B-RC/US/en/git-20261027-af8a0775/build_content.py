"""Bind the reviewed JHP-1000B-RC US transcription to shared Web components.

Run from the repository root:

    python manual_sources/JHP-1000B-RC/US/en/git-20261027-af8a0775/build_content.py

Every Web string comes from ``source/transcription.json`` by line id; this
module only decides which shared component carries each printed block, in
printed order. It writes ``source/en/content.json``, the frozen input that
``rebuild.py`` replays. Component chrome follows the JHP-3600A US reviewed
edition and the JE-1000D JP V2 prepared package; ``source/differences.md``
lists every layout decision.
"""
from __future__ import annotations

from html import escape
import re
import json
from pathlib import Path
import sys

from bs4 import BeautifulSoup

PACKAGE = Path(__file__).resolve().parent
ROOT = next(parent for parent in PACKAGE.parents if (parent / "build.py").is_file())
sys.path.insert(0, str(ROOT))

from tools.component_specs.adapters import web_callout_classes  # noqa: E402
from tools.component_specs.callout import callout_component_spec  # noqa: E402
from tools.component_specs.app import app_download_component_spec, app_inline_control_component_spec  # noqa: E402
from tools.component_specs.auto_resume import auto_resume_component_spec  # noqa: E402
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
from tools.web.frozen_ai_flow import node, root, table, text  # noqa: E402
from tools.web.frozen_ai_table_components import _spec_carrier  # noqa: E402

LANGUAGE = "en"
CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳㉑㉒㉓㉔㉕㉖"


def attrs(css: str, **extra: str) -> dict:
    return {"html": {"attributes": {"class": css, **extra}}}


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

    def label_and_rest(self, key: str) -> tuple[str, str]:
        """A printed bold lead-in label and the copy after it."""
        (style, label), *rest = self.spans(key)
        if style != "strong":
            raise ValueError("line has no bold lead-in: " + key)
        return label.strip(), "".join(value for _, value in rest).strip()


T = Lines()


# --- flow helpers -----------------------------------------------------------

def para(key: str) -> dict:
    return root(node("paragraph", T.inline(key)))


def strong_para(key: str) -> dict:
    return root(node("paragraph", [node("strong", [text(T(key))])]))


def heading(key: str, level: int = 3, anchor: str | None = None) -> dict:
    return root(node("heading", [text(T(key))], level=level, **({"anchor": anchor} if anchor else {})))


def chapter_heading(key: str, anchor: str) -> dict:
    return heading(key, level=2, anchor=anchor)


def sold_heading(title_key: str, sold_key: str) -> dict:
    """Printed title pill plus the separate dark SOLD SEPARATELY pill."""
    return root(node("heading", [
        node("inline_group", [text(T(title_key))], presentation=attrs("hb-heading-title")),
        node("inline_group", [text(T(sold_key))], presentation=attrs("hb-sold-separately")),
    ], level=3, presentation=attrs("hb-heading-label-pair")))


def items(keys: list[str]) -> list[dict]:
    return [node("list_item", [node("paragraph", T.inline(k))]) for k in keys]


def bullets(keys: list[str], ordered: bool = False) -> dict:
    return root(node("list", items(keys), ordered=ordered))


def panel(children: list[dict]) -> dict:
    """Shared grey text panel (web_manual.css ``.hb-text-panel``)."""
    return root(node("group", children, role="container", presentation=attrs("hb-text-panel")))


def p(key: str) -> dict:
    return node("paragraph", T.inline(key))


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
    """The shared callout carrier of ``tools.web.frozen_ai_flow.callout``.

    Its semantic body/items are built from stripped runs so a bold lead-in
    followed by plain copy in one printed line keeps its space in the carrier.
    """
    items = [" ".join(leaves(item)) for block in body if block["kind"] == "list" for item in block["children"]]
    spec = callout_component_spec(label=label, body="\n".join(part for b in body for part in leaves(b)),
                                  items=items, variant=variant, language=LANGUAGE, source_ref=ref)
    carrier = table([[node("table_cell", [text(label)], header=False, presentation=attrs("manual-callout-label")),
                      node("table_cell", body, header=False, presentation=attrs("manual-callout-body"))]],
                    css_class=f"manual-callout-table {web_callout_classes(spec)['table']}")
    return component_flow_node(spec, carrier_flow=[carrier])


def callout_block(label_key: str, body: list[dict], variant: str, ref: str) -> dict:
    return root(callout(T(label_key), body, variant=variant, ref=ref))



def callout_list(label_key: str, item_keys: list[str], variant: str, ref: str) -> dict:
    return callout_block(label_key, [node("list", items(item_keys), ordered=False)], variant, ref)


def callout_text(label_key: str, keys: list[str], variant: str, ref: str) -> dict:
    return callout_block(label_key, [p(k) for k in keys], variant, ref)


def strong_p(key: str) -> dict:
    return node("paragraph", [node("strong", [text(T(key))])])


# --- chapters ---------------------------------------------------------------

def preface() -> list[dict]:
    # The EN badge beside IMPORTANT is a language marker of the print layout (web_exclusions).
    T("pre.badge")
    return [chapter_heading("pre.h", "native-important"),
            para("pre.p1"), para("pre.p2"), para("pre.p3"), para("pre.n1"), para("pre.n2")]


def safety() -> list[dict]:
    risk = callout_block("w0.label", [strong_p("w0.text")], "warning", "native-pdf/page-4/warning-risk")
    basic = callout_block("w1.label", [strong_p("w1.text"),
                                       node("list", items([f"w1.l{i}" for i in range(1, 12)]), ordered=False)],
                          "warning", "native-pdf/page-4/warning-basic")
    operating = []
    for i in range(1, 15):
        children = [p(f"op.l{i}")]
        if i in (2, 3):
            children += [p(f"op.l{i}a"), p(f"op.l{i}b")]
        operating.append(node("list_item", children))
    grounding = callout_list("gr.w", ["gr.w1"], "warning", "native-pdf/page-4/grounding-warning")
    danger = callout_block("danger.label", [strong_p("danger.b1"), strong_p("danger.b2")],
                           "danger", "native-pdf/page-5/danger")
    return [chapter_heading("safety.h", "native-safety"), risk, basic,
            heading("op.h"), heading("op.save", level=4), root(node("list", operating, ordered=False)),
            heading("gr.h", level=4), bullets(["gr.l1"]), grounding,
            danger, heading("maint.h"), para("maint.p")]


SYMBOLS = [f"sym.s{i}" for i in range(1, 8)]
SYMBOL_ASSETS = ["assets/symbol-01.svg", "assets/symbol-02.svg", "assets/symbol-03.svg", "assets/symbol-04.svg",
                 "assets/symbol-05.svg", "assets/symbol-06.svg", "assets/symbol-07.png"]


def symbols() -> list[dict]:
    def pair(value: str, key: str) -> dict:
        return {f"{key}_html": escape(value), f"{key}_text": value}
    title = T.rows["sym.h"]["text"]
    signal = symbol_signal_component_spec(
        accessibility_label=title, headers=[pair(T("sig.th1"), "content"), pair(T("sig.th2"), "content")],
        rows=[{"label": T(f"sig.{k}.l"), "show_icon": True, **pair(T(f"sig.{k}.m"), "meaning")}
              for k in ("warn", "caut", "note", "tip")],
        source_ref="native-pdf/page-5/signal", language=LANGUAGE)
    headers = [pair(T(f"sym.th{i}"), "content") for i in range(1, 5)]
    meanings = [T(k) for k in SYMBOLS]
    pictograms = symbol_icon_component_spec(
        accessibility_label=title, headers=headers,
        panels=[[{"asset_index": i, "icon_alt": meanings[i], **pair(meanings[i], "meaning")} for i in rows]
                for rows in (range(0, 4), range(4, 7))],
        icon_refs=SYMBOL_ASSETS, source_ref="native-pdf/page-5/symbols", language=LANGUAGE,
        icon_locale_policy="exact")
    return [chapter_heading("sym.h", "native-meaning-of-symbols"),
            component_flow_node(signal, root=True), component_flow_node(pictograms, root=True)]


def compliance() -> list[dict]:
    def plain(key: str) -> dict:
        return {"kind": "paragraph", "label": "", "text": T(key)}

    def labelled(label_key: str, key: str) -> dict:
        return {"kind": "paragraph", "label": T(label_key), "text": T(key)}
    opening = [T("fcc.o1"), T("fcc.o2")]
    left = [plain("fcc.o3"), labelled("fcc.note.l", "fcc.note"), plain("fcc.limits"), plain("fcc.if")]
    right = [{"kind": "list", "items": [T(f"fcc.m{i}") for i in range(1, 5)]}, labelled("fcc.mod.l", "fcc.mod"),
             labelled("fcc.rf.h", "fcc.rf")]
    fcc = fcc_component_spec(accessibility_label="FCC", opening_copy=opening, left_blocks=left, right_blocks=right,
                             source_ref="native-pdf/page-6/fcc", language=LANGUAGE,
                             mark_asset_ref="assets/fcc-mark.svg")
    ised = panel([strong_p("ic.h"), *(p(f"ic.p{i}") for i in range(1, 6)), strong_p("ic.rf.h"), p("ic.rf")])
    carrier = [node("paragraph", [text(line)]) for line in opening]
    for block in left + right:
        if block["kind"] == "list":
            carrier.append(node("list", [node("list_item", [text(item)]) for item in block["items"]], ordered=False))
        else:
            label = [node("strong", [text(block["label"])]), text(" ")] if block["label"] else []
            carrier.append(node("paragraph", [*label, text(block["text"])]))
    # Shared chrome: the FCC section keeps a navigation-only "FCC" title (hidden by the
    # shared web_fcc_components.css), as every published FCC section does; the print has none.
    title = root(node("heading", [text("FCC")], level=2, anchor="native-fcc"))
    return [title, component_flow_node(fcc, carrier_flow=carrier, root=True), ised]


def in_the_box() -> list[dict]:
    cards = [{"image_ref": ref, "label": T(key), "alt": T.rows[key]["text"]}
             for key, ref in (("box.c1", "assets/inbox-unit.png"), ("box.c2", "assets/inbox-cable.png"),
                              ("box.c3", "assets/inbox-documents.png"))]
    title = T.rows["box.h"]["text"]
    T("box.h")
    tip_label, tip_body = T("box.tip.l"), T("box.tip")
    spec = inbox_component_spec(accessibility_label=title, cards=cards, tip_label=tip_label, tip_body=tip_body,
                                source_ref="native-pdf/page-6/inbox", language=LANGUAGE)
    carrier = table([[node("table_cell", [node("image", source=c["image_ref"], alt=c["alt"]),
                                          node("paragraph", [text(c["label"])])], header=False) for c in cards]])
    tip = table([[node("table_cell", [text(tip_label)], header=False),
                  node("table_cell", [text(tip_body)], header=False)]])
    return [root(node("heading", [text(title)], level=2, anchor="native-whats-in-the-box")),
            component_flow_node(spec, carrier_flow=(carrier, tip), root=True)]


def overview() -> list[dict]:
    front = ["ov.f.power", "ov.f.dc12", "ov.f.dc12.s", "ov.f.dcusb", "ov.f.c140", "ov.f.c140.s", "ov.f.a18",
             "ov.f.a18.s", "ov.f.c30", "ov.f.c30.s", "ov.f.lcd", "ov.f.ledbtn", "ov.f.led", "ov.f.ac1", "ov.f.ac2",
             "ov.f.acout", "ov.f.acout.s"]
    return [chapter_heading("ov.h", "native-product-overview"),
            heading("ov.front"), figure("assets/overview-front.png", "overview-front", 7, front),
            heading("ov.left"),
            figure("assets/overview-left.png", "overview-left", 7, ["ov.l.exp", "ov.l.exp.in", "ov.l.exp.out"]),
            heading("ov.right"),
            figure("assets/overview-right.png", "overview-right", 7,
                   ["ov.r.dcin", "ov.r.dcin.pv", "ov.r.dcin.car", "ov.r.acin", "ov.r.acin.s"])]


LCD_ICONS = ["wifi", "bluetooth", "quiet-charging", "charging-plan", "self-powered", "tou", "ups", "ac-power",
             "output-voltage-frequency", "input-power", "remaining-charge-time", "ac-wall-charging", "car-charging",
             "solar-charging", "battery-saving", "charging-power-limit", "battery-power", "low-battery",
             "remaining-battery-percentage", "discharge-timer", "connected-batteries", "energy-saving",
             "high-temperature", "low-temperature", "fault-code", "output-power", "remaining-discharge-time"]
LCD_NUMBERS = [*range(1, 24), 23, 24, 25, 26]
PNG_ICONS = {"output-voltage-frequency"}  # reused JHP-3000D raster glyph


def lcd() -> list[dict]:
    rows, refs = [], []
    for index, (number, icon) in enumerate(zip(LCD_NUMBERS, LCD_ICONS, strict=True)):
        key = f"d{index + 1}"
        name = T(f"lcd.{key}.t")
        bodies = sorted((k for k in T.rows if k.startswith(f"lcd.{key}.b")), key=lambda k: int(k.rsplit("b", 1)[1]))
        texts = [T.rows[k]["text"] for k in bodies]
        html = "<br/>".join(T.html(k) for k in bodies)
        rows.append({"number_html": CIRCLED[number - 1], "number_text": CIRCLED[number - 1],
                     "name_html": escape(name), "name_text": name, "description_html": html,
                     "description_text": " ".join(texts), "icon_alt": name, "asset_index": index})
        refs.append(f"assets/lcd-{icon}.png" if icon in PNG_ICONS else f"assets/lcd-{icon}.svg")
    spec = lcd_icon_component_spec(accessibility_label=T.rows["lcd.h"]["text"], rows=rows, icon_refs=refs,
                                   source_ref="native-pdf/page-8/lcd-icons", language=LANGUAGE,
                                   icon_locale_policy="exact", numbered=True)
    return [chapter_heading("lcd.h", "native-lcd-display"),
            figure("assets/lcd-map.png", "lcd-map", 8, [], label=T.rows["lcd.h"]["text"]),
            component_flow_node(spec, root=True)]


def key_cell(left_key: str, left_art: str, right_key: str, right_art: str) -> dict:
    def button(key: str, art: str) -> dict:
        return node("group", [node("image", source=art, alt=""), node("paragraph", T.inline(key))],
                    role="container", presentation=attrs("hb-key-button"))
    return node("table_cell", [node("group", [
        button(left_key, left_art), node("inline_group", [], presentation=attrs("hb-key-button-plus")),
        button(right_key, right_art)], role="container", presentation=attrs("hb-key-button-pair"))], header=False)


KEY_ROWS = [("assets/button-power.svg", "assets/button-ac1.svg"),
            ("assets/button-power.svg", "assets/button-dc-usb.svg"),
            ("assets/button-dc-usb.svg", "assets/button-ac1.svg"),
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
    spec = key_combinations_component_spec(headers=headers, rows=rows, source_ref="native-pdf/page-13/key-combinations",
                                           language=LANGUAGE)
    carrier = node("table", [node("table_head", [node("table_row", [node("table_cell", [text(h)], header=True)
                                                                    for h in headers])]),
                             node("table_body", carriers)], presentation=attrs("hb-key-combination-table"))
    return component_flow_node(spec, carrier_flow=[carrier], root=True)


def lcd_screen() -> dict:
    def pair(value: str, key: str) -> dict:
        return {f"{key}_html": escape(value), f"{key}_text": value}
    groups = []
    for state in ("scr.m1", "scr.m2"):
        groups.append({**pair(T(state), "state"), "actions": [
            {**pair(T(f"{state}.a{a}"), "action"), **pair(T(f"{state}.d{a}"), "description")} for a in (1, 2, 3)]})
    spec = lcd_mode_component_spec(accessibility_label=T.rows["scr.h"]["text"], groups=groups,
                                   artwork_ref="assets/lcd-screen.png", artwork_locale_policy="exact",
                                   source_ref="native-pdf/page-12/lcd-screen", language=LANGUAGE)
    return component_flow_node(spec, root=True)


def auto_resume() -> dict:
    spec = auto_resume_component_spec(
        headers=[T("res.th1"), T("res.th2")],
        conditions=[[T(f"res.a{i}") for i in (1, 2, 3)], [T(f"res.n{i}") for i in (1, 2, 3, 4)]],
        source_ref="native-pdf/page-13/auto-resume", language=LANGUAGE)
    return component_flow_node(spec, root=True)


def operations() -> list[dict]:
    return [chapter_heading("ops.h", "native-operations"),
            heading("pwr.h"),
            figure("assets/power-on-off.png", "power-on-off", 10,
                   ["fig.pwr.btn", "fig.pwr.on", "fig.pwr.on.s", "fig.pwr.off", "fig.pwr.off.s", "fig.pwr.3s"]),
            panel([p("pwr.standby"), p("pwr.standby2"), p("pwr.standby3")]),
            para("pwr.eco"),
            heading("ac.h"), panel([p("ac.pre")]),
            figure("assets/ac-output.png", "ac-output", 10,
                   ["fig.ac.on1", "fig.ac.on1.s", "fig.ac.off1", "fig.ac.off1.s", "fig.ac.btn1",
                    "fig.ac.on2", "fig.ac.on2.s", "fig.ac.off2", "fig.ac.off2.s", "fig.ac.btn2"]),
            panel([p("ac.note")]),
            heading("dc.h"), panel([p("dc.pre")]),
            figure("assets/dc-usb-output.png", "dc-usb-output", 11,
                   ["fig.dc.btn", "fig.dc.on", "fig.dc.on.s", "fig.dc.off", "fig.dc.off.s"]),
            callout_list("dc.c1.l", ["dc.c1.i1", "dc.c1.i2", "dc.c1.i3"], "caution", "native-pdf/page-11/usb-caution"),
            para("dc.car"),
            callout_list("dc.c2.l", ["dc.c2.i1", "dc.c2.i2", "dc.c2.i3"], "caution", "native-pdf/page-11/car-caution"),
            heading("led.h"), panel([p("led.modes")]),
            figure("assets/led-light.png", "led-light", 11, ["fig.led.btn", "fig.led.sos"]),
            bullets(["fig.led.s1", "fig.led.s2", "fig.led.s3"], ordered=True),
            heading("scr.h"), lcd_screen(), para("scr.app"),
            heading("eco.h"), para("eco.p"), panel([p("eco.disable")]),
            figure("assets/energy-saving.png", "energy-saving", 12,
                   ["fig.eco.ac1", "fig.eco.power", "fig.eco.3s", "fig.eco.onoff", "fig.eco.hold"]),
            callout_text("eco.note.l", ["eco.note"], "note", "native-pdf/page-12/note"),
            callout_text("eco.warn.l", ["eco.warn"], "warning", "native-pdf/page-12/warning"),
            heading("res.h"), para("res.p"), auto_resume(),
            heading("key.h"), key_combinations()]


def ups() -> list[dict]:
    warning = callout_block("ups.w.l", [
        p("ups.w.p1"), p("ups.w.p2"),
        node("list", items(["ups.w.i1", "ups.w.i2", "ups.w.i3"]), ordered=False), p("ups.w.p3"),
    ], "warning", "native-pdf/page-14/warning")
    return [chapter_heading("ups.h", "native-ups"), para("ups.p"),
            figure("assets/ups.png", "ups", 13, ["fig.ups.ac2", "fig.ups.ac1"]),
            para("ups.p1"), para("ups.p2"), para("ups.p3"), para("ups.p4"),
            callout_list("ups.c.l", ["ups.c.i1", "ups.c.i2", "ups.c.i3", "ups.c.i4"], "caution",
                         "native-pdf/page-14/caution"),
            warning]


def battery_packs() -> list[dict]:
    return [chapter_heading("bp.h", "native-battery-packs"), para("bp.p"),
            figure("assets/battery-stack.png", "battery-stack", 14, ["fig.bp.gap"]),
            figure("assets/battery-accessories.png", "battery-accessories", 14,
                   ["fig.bp.c1", "fig.bp.c2", "fig.bp.c3", "fig.bp.sold"]),
            callout_list("bp.c.l", ["bp.c.i1", "bp.c.i2", "bp.c.i3", "bp.c.i4"], "caution",
                         "native-pdf/page-15/caution")]


def charging() -> list[dict]:
    solar_caution = callout_block("chg.sol.c2.l", [
        p("chg.sol.c2"), node("list", items(["chg.sol.c2.i1", "chg.sol.c2.i2"]), ordered=False),
    ], "caution", "native-pdf/page-16/solar-caution-2")
    car_caution = callout_list("car.c.l", ["car.c.i1", "car.c.i2", "car.c.i3"], "caution",
                               "native-pdf/page-17/car-caution")
    return [chapter_heading("chg.h", "native-charging"), para("chg.green"), root(strong_p("chg.first")),
            callout_list("chg.note.l", ["chg.note.i1", "chg.note.i2"], "note", "native-pdf/page-15/note"),
            heading("chg.ac.h"),
            figure("assets/charging-ac.png", "charging-ac", 15, [], label=T.rows["chg.ac.h"]["text"]),
            panel([p("chg.ac.p")]),
            callout_text("chg.ac.c.l", ["chg.ac.c"], "caution", "native-pdf/page-15/ac-caution"),
            heading("chg.emg.h", level=4), para("chg.emg"), para("chg.emg.n"),
            heading("chg.sol.h"), para("chg.sol.p"),
            figure("assets/charging-solar.png", "charging-solar", 16, ["fig.sol.label"]),
            callout_text("chg.sol.c1.l", ["chg.sol.c1"], "caution", "native-pdf/page-16/solar-caution-1"),
            solar_caution, para("chg.sol.voc"),
            heading("chg.car.h"), para("chg.car.p"),
            figure("assets/charging-car.png", "charging-car", 16, ["fig.car.note", "fig.car.vehicle"]),
            car_caution]


def storage() -> list[dict]:
    return [chapter_heading("sto.h", "native-storage"),
            para("sto.p"), bullets(["sto.l1", "sto.l2", "sto.l3"]), para("sto.p2")]


def measures(key: str) -> tuple[str, str]:
    """A printed numbered list is shown one step per line; the copy is unchanged."""
    value = T(key)
    steps = re.split(r"(?<=\.) (?=\d\. )", value)
    return value, "<br />".join(escape(step) for step in steps)


def troubleshooting() -> list[dict]:
    def pair(value: str, key: str) -> dict:
        return {f"{key}_html": escape(value), f"{key}_text": value}
    rows = []
    for index in range(1, 10):
        code = T(f"ts.r{index}.c")
        value, html = measures(f"ts.r{index}.m")
        rows.append({**pair(code, "code"), "measures_html": html, "measures_text": value})
    spec = troubleshooting_component_spec(headers=[pair(T("ts.th1"), "content"), pair(T("ts.th2"), "content")],
                                          rows=rows, source_ref="native-pdf/page-17/troubleshooting",
                                          language=LANGUAGE)
    return [chapter_heading("ts.h", "native-troubleshooting"), para("ts.p"), component_flow_node(spec, root=True)]


def specifications() -> list[dict]:
    nodes = [chapter_heading("spec.h", "native-specifications")]
    for group, count in (("g", 7), ("i", 3), ("o", 7), ("t", 2)):
        title = T(f"spec.{group}.h")
        rows = []
        for index in range(1, count + 1):
            label = T(f"spec.{group}{index}.l")
            values = [T(k) for k in sorted(k for k in T.rows if k.startswith(f"spec.{group}{index}.v"))]
            rows.append((label, "\n".join(values)))
        spec = spec_table_component_spec(section_title=title, rows=rows, source_ref=f"native-pdf/page-18/{group}",
                                         language=LANGUAGE)
        nodes.append(component_flow_node(spec, carrier_flow=_spec_carrier(title, rows), root=True))
    return [*nodes, para("spec.fn1"), para("spec.fn2"), para("spec.tm")]


def warranty() -> list[dict]:
    def block(*keys: str) -> dict:
        return {"kind": "paragraph", "html": "<p>" + "<br/>".join(T.html(k) for k in keys) + "</p>",
                "text": " ".join(T.rows[k]["text"] for k in keys)}

    def ul(*keys: str) -> dict:
        values = [T(k) for k in keys]
        return {"kind": "list", "items": values,
                "html": "<ul>" + "".join(f"<li>{escape(v)}</li>" for v in values) + "</ul>"}

    def section(index: int, title_key: str, blocks: list[dict]) -> list[dict]:
        title = heading(title_key)
        spec = warranty_section_component_spec(title=T.rows[title_key]["text"], section_index=index, blocks=blocks,
                                               source_ref=f"native-pdf/page-19/warranty-{index}", language=LANGUAGE)
        return [title, component_flow_node(spec, root=True)]

    lead_text, note_text = T("war.lead"), T("war.local")
    lead = warranty_lead_component_spec(accessibility_label=T.rows["war.h"]["text"],
                                        lead_html=f"<p><strong>{escape(lead_text)}</strong></p>",
                                        local_note_html=f"<p>{escape(note_text)}</p>",
                                        source_ref="native-pdf/page-19/lead", language=LANGUAGE)
    periods = []
    for y in ("std", "ext"):
        body = T(f"war.per.{y}")
        periods.append({"number": T(f"war.per.{y}.n"), "unit": T(f"war.per.{y}.u"), "label": T(f"war.per.{y}.l"),
                        "body_html": f"<p>{escape(body)}</p>", "body_text": body})
    period_title = heading("war.per.h")
    years = warranty_years_component_spec(title=T.rows["war.per.h"]["text"], periods=periods,
                                          source_ref="native-pdf/page-19/period", language=LANGUAGE)
    return [chapter_heading("war.h", "native-warranty"), component_flow_node(lead, root=True),
            *section(1, "war.lim.h", [block("war.lim.p1"), block("war.lim.p2")]),
            period_title, component_flow_node(years, root=True),
            *section(2, "war.rep.h", [block("war.rep")]),
            *section(3, "war.buy.h", [block("war.buy")]),
            *section(4, "war.exc.h", [block("war.exc"), ul("war.exc.i1", "war.exc.i2", "war.exc.i3", "war.exc.i4")]),
            *section(5, "war.int.h", [block("war.int")])]


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
        metadata={"visual_recovery": "outlined-pdf-vector-plus-control"})
    plus_carrier = node("paragraph", [text(before + " "), node("strong", [text("+")]), text(" " + after)])
    note1 = callout_block("app.n1.l", [
        p("app.n1"), node("list", items(["app.n1.i1", "app.n1.i2"]), ordered=False),
    ], "note", "native-pdf/page-21/note-1")
    return [chapter_heading("app.h", "native-app-setup"),
            heading("app.s1.h"), component_flow_node(download, carrier_flow=carrier, root=True),
            heading("app.s2.h"), component_flow_node(plus, carrier_flow=(plus_carrier,), root=True),
            para("app.s22"),
            figure("assets/app-add.png", "app-add", 20, ["fig.app.c21", "fig.app.c22"]),
            figure("assets/app-panel.png", "app-panel", 20,
                   ["fig.ctl.power", "fig.ctl.dcusb", "fig.ctl.ac2", "fig.ctl.ac1"]),
            para("app.s23"), note1, para("app.s24"),
            callout_text("app.n2.l", ["app.n2"], "note", "native-pdf/page-21/note-2"),
            para("app.s25"),
            figure("assets/app-results.png", "app-results", 21, ["fig.app.c23", "fig.app.c24", "fig.app.c25"]),
            para("app.shots"),
            callout_text("app.c.l", ["app.c"], "caution", "native-pdf/page-21/caution"),
            heading("app.s3.h"), para("app.s3"),
            heading("app.s4.h"),
            heading("app.s41.h", level=4), bullets(["app.s41.i1", "app.s41.i2"]),
            heading("app.s42.h", level=4), bullets(["app.s42.i1"]),
            heading("app.s43.h", level=4), para("app.s43")]


CHAPTERS = (
    ("preface", "IMPORTANT", preface), ("safety", "IMPORTANT SAFETY INFORMATION", safety),
    ("symbols", "MEANING OF SYMBOLS", symbols), ("fcc", "FCC", compliance),
    ("in_the_box", "WHAT'S IN THE BOX", in_the_box), ("product_overview", "PRODUCT OVERVIEW", overview),
    ("lcd_display", "LCD DISPLAY", lcd), ("operations", "OPERATIONS", operations),
    ("ups", "UNINTERRUPTIBLE POWER SUPPLY (UPS)", ups),
    ("battery_packs", "CONNECT TO BATTERY PACK(S) (SOLD SEPARATELY)", battery_packs),
    ("charging", "CHARGING", charging), ("storage", "STORAGE", storage),
    ("troubleshooting", "TROUBLESHOOTING", troubleshooting), ("specifications", "SPECIFICATIONS", specifications),
    ("warranty", "WARRANTY", warranty), ("app_setup", "APP SETUP", app_setup),
)


def build() -> dict:
    chapters = [{"id": cid, "title": title, "nodes": make()} for cid, title, make in CHAPTERS]
    missing = [k for k in T.rows if k not in T.used]
    if missing:
        raise ValueError("Web transcription lines not bound: " + ", ".join(missing))
    return {"model": "JHP-1000B-RC", "region": "US", "language": LANGUAGE,
            "title": "Jackery HomePower 1000 Plus User Manual",
            "source_sha256": "af8a0775d0ba23a137fe024ae961c8b77f35797e1c8838a943ddbf8d418d9251",
            "chapters": chapters}


def main() -> None:
    content = build()
    path = PACKAGE / "source/en/content.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(content, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"chapters": [c["id"] for c in content["chapters"]], "lines": len(T.used)}))


if __name__ == "__main__":
    main()
