"""Bind the reviewed JHP-2000A-RC US transcription to shared Web components.

Run from the repository root:

    python manual_sources/JHP-2000A-RC/US/en/git-20261027-e27d4db5/build_content.py

Every Web string comes from ``source/transcription.json`` by line id; this
module only decides which shared component carries each printed block, in
printed order. It writes ``source/en/content.json``, the frozen input that
``rebuild.py`` replays. Component chrome follows the JHP-3600A US reviewed
edition and the JE-1000D JP V2 prepared package; ``source/differences.md``
lists every layout decision.
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


# --- chapters ---------------------------------------------------------------

def preface() -> list[dict]:
    return [chapter_heading("pre.h", "native-important"),
            para("pre.p1"), para("pre.p2"), para("pre.p3"), para("pre.n1"), para("pre.n2")]


def safety() -> list[dict]:
    warning = callout_block("safety.w.label", [
        node("paragraph", [node("strong", [text(T("safety.w.title"))])]),
        node("paragraph", [node("strong", [text(T("safety.lead"))])]),
        node("list", items([f"safety.b{i}" for i in range(1, 12)]), ordered=False),
    ], "warning", "native-pdf/page-4/warning")
    operating = []
    for i in range(1, 16):
        children = [p(f"op.b{i}")]
        if i in (2, 3):
            children += [p(f"op.b{i}.s1"), p(f"op.b{i}.s2")]
        operating.append(node("list_item", children))
    w2 = callout_block("w2.label", [node("paragraph", [node("strong", [text(T("w2.body"))])])],
                       "warning", "native-pdf/page-5/warning")
    danger = callout_block("dg.label", [node("paragraph", [node("strong", [text(T(k))])]) for k in ("dg.body", "dg.body2")],
                           "danger", "native-pdf/page-5/danger")
    return [chapter_heading("safety.h", "native-safety"), warning,
            heading("op.h"), heading("op.save", level=4), root(node("list", operating, ordered=False)),
            w2, danger, heading("maint.h"), para("maint.p")]


SYMBOLS = ["sym.alert", "sym.manual", "sym.shock", "sym.charging", "sym.explosive", "sym.heavy",
           "sym.dismantle", "sym.fire", "sym.children", "sym.liion", "sym.weee"]
SYMBOL_ASSETS = ["assets/symbol-01.svg", "assets/symbol-02.svg", "assets/symbol-03.svg", "assets/symbol-04.svg",
                 "assets/symbol-05.svg", "assets/symbol-06.svg", "assets/symbol-07.svg", "assets/symbol-08.svg",
                 "assets/symbol-09.svg", "assets/symbol-10.svg", "assets/symbol-11.png"]


def symbols() -> list[dict]:
    def pair(value: str, key: str) -> dict:
        return {f"{key}_html": escape(value), f"{key}_text": value}
    title = T.rows["sym.h"]["text"]
    signal = symbol_signal_component_spec(
        accessibility_label=title, headers=[pair(T("sig.th1"), "content"), pair(T("sig.th2"), "content")],
        rows=[{"label": T(f"sig.{k}.l"), "show_icon": k in ("warn", "caut"), **pair(T(f"sig.{k}.m"), "meaning")}
              for k in ("warn", "caut", "note", "tip")],
        source_ref="native-pdf/page-5/signal", language=LANGUAGE)
    headers = [pair(T(f"symt.th{i}"), "content") for i in range(1, 5)]
    meanings = [T(k) for k in SYMBOLS]
    pictograms = symbol_icon_component_spec(
        accessibility_label=title, headers=headers,
        panels=[[{"asset_index": i, "icon_alt": meanings[i], **pair(meanings[i], "meaning")} for i in rows]
                for rows in (range(0, 6), range(6, 11))],
        icon_refs=SYMBOL_ASSETS, source_ref="native-pdf/page-5/symbols", language=LANGUAGE,
        icon_locale_policy="exact")
    return [chapter_heading("sym.h", "native-meaning-of-symbols"),
            component_flow_node(signal, root=True), component_flow_node(pictograms, root=True)]


def compliance() -> list[dict]:
    def labelled(key: str) -> dict:
        label, rest = T.label_and_rest(key)
        return {"kind": "paragraph", "label": label, "text": rest}

    def plain(key: str) -> dict:
        return {"kind": "paragraph", "label": "", "text": T(key)}
    opening = [T("fcc.p1"), T("fcc.p1a")]
    left = [plain("fcc.p1b"), labelled("fcc.note"), plain("fcc.p2"), plain("fcc.p3")]
    right = [{"kind": "list", "items": [T(f"fcc.l{i}") for i in range(1, 5)]}, labelled("fcc.mod"),
             {"kind": "paragraph", "label": T("fcc.rf.h"), "text": T("fcc.rf")}]
    fcc = fcc_component_spec(accessibility_label="FCC", opening_copy=opening, left_blocks=left, right_blocks=right,
                             source_ref="native-pdf/page-6/fcc", language=LANGUAGE,
                             mark_asset_ref="assets/fcc-mark.svg")
    ised = panel([node("paragraph", [node("strong", [text(T("ised.h"))])]),
                  *(p(f"ised.p{i}") for i in range(1, 6)),
                  node("paragraph", [node("strong", [text(T("ised.rf.h"))])]), p("ised.rf")])
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
    front = ["ov.f.power", "ov.f.dc12", "ov.f.dc12.v", "ov.f.dcusb", "ov.f.usbc30", "ov.f.usbc30.v", "ov.f.usba",
             "ov.f.usba.v", "ov.f.usbc140", "ov.f.usbc140.v", "ov.f.lcd", "ov.f.ledbtn", "ov.f.led", "ov.f.ac1",
             "ov.f.ac2", "ov.f.acout", "ov.f.acout.v"]
    return [chapter_heading("ov.h", "native-product-overview"),
            heading("ov.front.h"), figure("assets/overview-front.png", "overview-front", 7, front),
            heading("ov.left.h"),
            figure("assets/overview-left.png", "overview-left", 7, ["ov.l.handle", "ov.l.dcexp", "ov.l.dcexp.v"]),
            heading("ov.right.h"),
            figure("assets/overview-right.png", "overview-right", 7,
                   ["ov.r.dcin", "ov.r.dcin.v1", "ov.r.dcin.v2", "ov.r.acin", "ov.r.acin.v"])]


LCD_ROWS = [  # (number index, transcription row key, icon)
    (1, "d1", "assets/lcd-wifi.svg"), (2, "d2", "assets/lcd-bluetooth.svg"),
    (3, "d3", "assets/lcd-quiet-charging.svg"), (4, "d4", "assets/lcd-charging-plan.svg"),
    (5, "d5", "assets/lcd-self-powered.svg"), (6, "d6", "assets/lcd-tou.svg"), (7, "d7", "assets/lcd-ups.svg"),
    (8, "d8", "assets/lcd-ac-power.svg"), (9, "d9", "assets/lcd-output-voltage-frequency.svg"),
    (10, "d10", "assets/lcd-input-power.svg"), (11, "d11", "assets/lcd-remaining-charge-time.svg"),
    (12, "d12", "assets/lcd-ac-wall-charging.svg"), (13, "d13", "assets/lcd-car-charging.svg"),
    (14, "d14", "assets/lcd-solar-charging.svg"), (15, "d15", "assets/lcd-battery-saving.svg"),
    (16, "d16", "assets/lcd-charging-power-limit.svg"), (17, "d17", "assets/lcd-battery-power.svg"),
    (18, "d18", "assets/lcd-low-battery.svg"), (19, "d19", "assets/lcd-remaining-battery-percentage.svg"),
    (20, "d20", "assets/lcd-discharge-timer.svg"), (21, "d21", "assets/lcd-connected-batteries.svg"),
    (22, "d22", "assets/lcd-energy-saving.svg"), (23, "d23a", "assets/lcd-high-temperature.svg"),
    (23, "d23b", "assets/lcd-low-temperature.svg"), (24, "d24", "assets/lcd-fault-code.svg"),
    (25, "d25", "assets/lcd-output-power.svg"), (26, "d26", "assets/lcd-remaining-discharge-time.svg"),
]


def lcd() -> list[dict]:
    rows, refs = [], []
    for index, (number, key, asset) in enumerate(LCD_ROWS):
        name = T(f"lcd.{key}.t")
        bodies = sorted((k for k in T.rows if k.startswith(f"lcd.{key}.b")), key=lambda k: int(k.rsplit("b", 1)[1]))
        texts = [T.rows[k]["text"] for k in bodies]
        html = "<br/>".join(T.html(k) for k in bodies)
        rows.append({"number_html": CIRCLED[number - 1], "number_text": CIRCLED[number - 1],
                     "name_html": escape(name), "name_text": name, "description_html": html,
                     "description_text": " ".join(texts), "icon_alt": name, "asset_index": index})
        refs.append(asset)
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


KEY_ROWS = [("assets/button-power.svg", "assets/button-dc-usb.svg"),
            ("assets/button-power.svg", "assets/button-ac1.svg"),
            ("assets/button-ac1.svg", "assets/button-dc-usb.svg"),
            ("assets/button-power.svg", "assets/button-light.svg")]


def key_combinations() -> dict:
    headers = [T(f"key.th{i}") for i in (1, 2, 3)]
    rows, carriers = [], []
    for index, (left_art, right_art) in enumerate(KEY_ROWS, start=1):
        r = f"key.r{index}"
        left, right = T.rows[f"{r}.a"]["text"], T.rows[f"{r}.b"]["text"]
        first = key_cell(f"{r}.a", left_art, f"{r}.b", right_art)
        duration, operation, function = T(f"{r}.op"), T(f"{r}.op2"), T(f"{r}.fn")
        rows.append([f"{left} {right}", f"{duration} {operation}", function])
        second = node("table_cell", [
            node("inline_group", [text(duration)],
                 presentation=attrs("hb-key-duration", **{"data-duration-icon": "clock"})),
            node("paragraph", [text(operation)])], header=False)
        carriers.append(node("table_row", [first, second, node("table_cell", [text(function)], header=False)]))
    spec = key_combinations_component_spec(headers=headers, rows=rows, source_ref="native-pdf/page-14/key-combinations",
                                           language=LANGUAGE)
    carrier = node("table", [node("table_head", [node("table_row", [node("table_cell", [text(h)], header=True)
                                                                    for h in headers])]),
                             node("table_body", carriers)], presentation=attrs("hb-key-combination-table"))
    return component_flow_node(spec, carrier_flow=[carrier], root=True)


def lcd_screen() -> dict:
    def pair(value: str, key: str) -> dict:
        return {f"{key}_html": escape(value), f"{key}_text": value}
    groups = []
    for state, prefix in (("lcdm.short", "lcdm.s"), ("lcdm.steady", "lcdm.t")):
        groups.append({**pair(T(state), "state"), "actions": [
            {**pair(T(f"{prefix}.{a}"), "action"), **pair(T(f"{prefix}.{a}.v"), "description")}
            for a in ("on", "off", "auto")]})
    spec = lcd_mode_component_spec(accessibility_label=T.rows["opr.lcd.h"]["text"], groups=groups,
                                   artwork_ref="assets/lcd-screen.png", artwork_locale_policy="exact",
                                   source_ref="native-pdf/page-14/lcd-screen", language=LANGUAGE)
    return component_flow_node(spec, root=True)


def auto_resume() -> dict:
    spec = auto_resume_component_spec(
        headers=[T("res.th1"), T("res.th2")],
        conditions=[[T(f"res.a{i}") for i in (1, 2, 3)], [T(f"res.n{i}") for i in (1, 2, 3, 4)]],
        source_ref="native-pdf/page-14/auto-resume", language=LANGUAGE)
    return component_flow_node(spec, root=True)


def operations() -> list[dict]:
    return [chapter_heading("opr.h", "native-operations"),
            heading("opr.power.h"),
            figure("assets/power-on-off.png", "power-on-off", 11,
                   ["fig.power.on", "fig.power.on.v", "fig.power.off", "fig.power.off.v", "fig.power.3s"]),
            panel([p("opr.power.standby"), p("opr.power.standby2"), p("opr.power.standby3")]),
            panel([p("opr.power.eco")]),
            heading("opr.ac.h"), panel([p("opr.ac.pre")]), panel([p("opr.ac.p")]),
            figure("assets/ac-output.png", "ac-output", 11, ["fig.ac.on", "fig.ac.on.v", "fig.ac.off", "fig.ac.off.v"]),
            heading("opr.dc.h"), panel([p("opr.dc.pre")]),
            figure("assets/dc-usb-output.png", "dc-usb-output", 12,
                   ["fig.dc.on", "fig.dc.on.v", "fig.dc.off", "fig.dc.off.v"]),
            callout_list("opr.usb.caut.l", ["opr.usb.caut1", "opr.usb.caut2", "opr.usb.caut3"], "caution",
                         "native-pdf/page-12/usb-caution"),
            panel([p("opr.car.p")]),
            callout_list("opr.car.caut.l", ["opr.car.caut1", "opr.car.caut2", "opr.car.caut3"], "caution",
                         "native-pdf/page-12/car-caution"),
            heading("opr.eco.h"), panel([p("opr.eco.p1")]),
            figure("assets/energy-saving.png", "energy-saving", 13,
                   ["fig.eco.main", "fig.eco.ac1", "fig.eco.3s", "fig.eco.onoff", "fig.eco.hold"]),
            panel([p("opr.eco.p2"), p("opr.eco.p3")]),
            callout_text("opr.eco.note.l", ["opr.eco.note"], "note", "native-pdf/page-13/note"),
            callout_text("opr.eco.warn.l", ["opr.eco.warn"], "warning", "native-pdf/page-13/warning"),
            heading("opr.led.h"), panel([p("opr.led.p")]),
            figure("assets/led-light.png", "led-light", 13, [], label=T.rows["opr.led.h"]["text"]),
            bullets(["opr.led.s1", "opr.led.s2", "opr.led.s3"], ordered=True),
            heading("opr.lcd.h"), lcd_screen(), para("opr.lcd.app"),
            heading("opr.key.h"), key_combinations(),
            heading("opr.resume.h"), para("opr.resume.p"), auto_resume()]


def ups() -> list[dict]:
    warning = callout_block("ups.warn.l", [
        p("ups.warn1"), p("ups.warn2"),
        node("list", items(["ups.warn.l1", "ups.warn.l2", "ups.warn.l3"]), ordered=False), p("ups.warn3"),
    ], "warning", "native-pdf/page-15/warning")
    return [chapter_heading("ups.h", "native-ups"), para("ups.p1"),
            figure("assets/ups.png", "ups", 15, [], label=T.rows["ups.h"]["text"]),
            panel([p("ups.fig1"), p("ups.fig2")]), para("ups.p2"),
            callout_list("ups.caut.l", ["ups.caut1", "ups.caut2", "ups.caut3", "ups.caut4"], "caution",
                         "native-pdf/page-15/caution"),
            warning]


def battery_packs() -> list[dict]:
    sold = root(node("paragraph", [node("inline_group", [text(T("bp.sold"))],
                                        presentation=attrs("hb-sold-separately"))]))
    return [chapter_heading("bp.h", "native-battery-packs"), sold, para("bp.p"),
            figure("assets/battery-stack.png", "battery-stack", 16, ["fig.bp.dist"]),
            callout_list("bp.caut.l", ["bp.caut1", "bp.caut2", "bp.caut3", "bp.caut4"], "caution",
                         "native-pdf/page-16/caution"),
            figure("assets/battery-accessories.png", "battery-accessories", 16,
                   ["fig.bp.pack", "fig.bp.cable", "fig.bp.docs", "fig.bp.sold"])]


def charging() -> list[dict]:
    solar_caution = callout_block("chg.solar.caut2.l", [
        p("chg.solar.caut2"),
        node("list", items(["chg.solar.caut2.l1", "chg.solar.caut2.l2"]), ordered=False),
    ], "caution", "native-pdf/page-18/solar-caution")
    return [chapter_heading("chg.h", "native-charging"), para("chg.green"), strong_para("chg.first"),
            callout_list("chg.note.l", ["chg.note1", "chg.note2"], "note", "native-pdf/page-17/note"),
            heading("chg.ac.h"),
            figure("assets/charging-ac.png", "charging-ac", 17, [], label=T.rows["chg.ac.h"]["text"]),
            panel([p("chg.ac.fig")]),
            callout_text("chg.ac.caut.l", ["chg.ac.caut"], "caution", "native-pdf/page-17/ac-caution"),
            heading("chg.emg.h", level=4), para("chg.emg.p"), para("chg.emg.n"),
            sold_heading("chg.solar.h", "chg.solar.sold"), para("chg.solar.p"),
            callout_text("chg.solar.caut.l", ["chg.solar.caut"], "caution", "native-pdf/page-17/solar-caution"),
            figure("assets/charging-solar.png", "charging-solar", 18, ["fig.solar.panels"]),
            solar_caution, para("chg.solar.voc"),
            sold_heading("chg.car.h", "chg.car.sold"), para("chg.car.p"),
            figure("assets/charging-car.png", "charging-car", 18, ["fig.car.vehicle", "fig.car.note"]),
            callout_list("chg.car.caut.l", ["chg.car.caut1", "chg.car.caut2", "chg.car.caut3"], "caution",
                         "native-pdf/page-18/car-caution")]


def storage() -> list[dict]:
    return [chapter_heading("sto.h", "native-storage"),
            panel([p("sto.p"), node("list", items(["sto.l1", "sto.l2", "sto.l3"]), ordered=False), p("sto.p2")])]


TS_CODES = ["f0", "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "fc", "fe"]


def troubleshooting() -> list[dict]:
    def pair(value: str, key: str) -> dict:
        return {f"{key}_html": escape(value), f"{key}_text": value}
    rows = []
    for code in TS_CODES:
        keys = sorted((k for k in T.rows if k.startswith(f"ts.{code}.m")), key=lambda k: k[-1])
        texts = [T.rows[k]["text"] for k in keys]
        html = "<br />".join(T.html(k) for k in keys)
        rows.append({**pair(T(f"ts.{code}.c"), "code"), "measures_html": html, "measures_text": " ".join(texts)})
    spec = troubleshooting_component_spec(headers=[pair(T("ts.th1"), "content"), pair(T("ts.th2"), "content")],
                                          rows=rows, source_ref="native-pdf/page-19/troubleshooting",
                                          language=LANGUAGE)
    return [chapter_heading("ts.h", "native-troubleshooting"), para("ts.p"), component_flow_node(spec, root=True)]


def specifications() -> list[dict]:
    nodes = [chapter_heading("spec.h", "native-specifications")]
    for group in ("gen", "in", "out", "env"):
        title = T(f"spec.{group}.h")
        rows = []
        index = 1
        while f"spec.{group}.r{index}.l" in T.rows:
            label = T(f"spec.{group}.r{index}.l")
            values = [T(k) for k in sorted(k for k in T.rows if k.startswith(f"spec.{group}.r{index}.v"))]
            rows.append((label, "\n".join(values)))
            index += 1
        spec = spec_table_component_spec(section_title=title, rows=rows, source_ref=f"native-pdf/page-20/{group}",
                                         language=LANGUAGE)
        nodes.append(component_flow_node(spec, carrier_flow=_spec_carrier(title, rows), root=True))
    return [*nodes, para("spec.tm"), para("spec.fn1")]


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
                                               source_ref=f"native-pdf/page-21/warranty-{index}", language=LANGUAGE)
        return [title, component_flow_node(spec, root=True)]

    lead_text, note_text = T("war.lead"), T("war.note")
    lead = warranty_lead_component_spec(accessibility_label=T.rows["war.h"]["text"],
                                        lead_html=f"<p><strong>{escape(lead_text)}</strong></p>",
                                        local_note_html=f"<p>{escape(note_text)}</p>",
                                        source_ref="native-pdf/page-21/lead", language=LANGUAGE)
    periods = []
    for y in ("y1", "y2"):
        body = T(f"war.{y}.b")
        periods.append({"number": T(f"war.{y}.n"), "unit": T(f"war.{y}.u"), "label": T(f"war.{y}.l"),
                        "body_html": f"<p>{escape(body)}</p>", "body_text": body})
    period_title = heading("war.s2.h")
    years = warranty_years_component_spec(title=T.rows["war.s2.h"]["text"], periods=periods,
                                          source_ref="native-pdf/page-21/period", language=LANGUAGE)
    return [chapter_heading("war.h", "native-warranty"), component_flow_node(lead, root=True),
            *section(1, "war.s1.h", [block("war.s1.p1"), block("war.s1.p2")]),
            period_title, component_flow_node(years, root=True),
            *section(2, "war.s3.h", [block("war.s3.p")]),
            *section(3, "war.s4.h", [block("war.s4.p")]),
            *section(4, "war.s5.h", [block("war.s5.p"), ul("war.s5.l1", "war.s5.l2", "war.s5.l3", "war.s5.l4")]),
            *section(5, "war.s6.h", [block("war.s6.p")])]


def app_setup() -> list[dict]:
    columns = [{"role": "store", "text": T("app.s1.store")}, {"role": "qr", "text": T("app.s1.qr")}]
    for column in columns:
        column["html"] = escape(column["text"])
    download = app_download_component_spec(
        accessibility_label="Jackery App", columns=columns, source_art_ref="assets/app-qr.png",
        store_art_ref="assets/app-store.png", qr_art_ref="assets/app-qr.png",
        source_ref="native-pdf/page-22/download", language=LANGUAGE)
    carrier = [node("image", source="assets/app-store.png", alt="App Store / Google Play"),
               node("paragraph", [text(columns[0]["text"])]),
               node("image", source="assets/app-qr.png", alt="Jackery App"),
               node("paragraph", [text(columns[1]["text"])])]
    before, after = T("app.s21").split(" [+] ")
    plus = app_inline_control_component_spec(
        accessibility_label="+", paragraph_html=f"{escape(before)} <strong>+</strong> {escape(after)}",
        paragraph_text=f"{before} + {after}", source_ref="native-pdf/page-22/add-button", language=LANGUAGE,
        metadata={"visual_recovery": "outlined-pdf-vector-plus-control"})
    plus_carrier = node("paragraph", [text(before + " "), node("strong", [text("+")]), text(" " + after)])
    note1 = callout_block("app.note1.l", [
        p("app.note1"), node("list", items(["app.note1.l1", "app.note1.l2"]), ordered=False),
    ], "note", "native-pdf/page-22/note")
    return [chapter_heading("app.h", "native-app-setup"),
            heading("app.s1.h"), component_flow_node(download, carrier_flow=carrier, root=True),
            heading("app.s2.h"), component_flow_node(plus, carrier_flow=(plus_carrier,), root=True),
            para("app.s22"),
            figure("assets/app-add.png", "app-add", 22, ["fig.app.c21", "fig.app.c22"]),
            figure("assets/app-panel.png", "app-panel", 22,
                   ["fig.panel.main", "fig.panel.dcusb", "fig.panel.ac1", "fig.panel.ac2"]),
            para("app.s23"), note1, para("app.s24"),
            callout_text("app.note2.l", ["app.note2"], "note", "native-pdf/page-23/note"),
            para("app.s25"),
            figure("assets/app-results.png", "app-results", 23, ["fig.app.c23", "fig.app.c24", "fig.app.c25"]),
            para("app.shots"),
            callout_text("app.caut.l", ["app.caut"], "caution", "native-pdf/page-23/caution"),
            heading("app.s3.h"), para("app.s3"),
            heading("app.s4.h"),
            heading("app.s41.h", level=4), bullets(["app.s41.l1", "app.s41.l2"]),
            heading("app.s42.h", level=4), para("app.s42"),
            heading("app.s43.h", level=4), para("app.s43")]


CHAPTERS = (
    ("preface", "IMPORTANT", preface), ("safety", "IMPORTANT SAFETY INFORMATION", safety),
    ("symbols", "MEANING OF SYMBOLS", symbols), ("fcc", "FCC", compliance), ("in_the_box", "WHAT'S IN THE BOX", in_the_box),
    ("product_overview", "PRODUCT OVERVIEW", overview), ("lcd_display", "LCD DISPLAY", lcd),
    ("operations", "OPERATIONS", operations), ("ups", "UNINTERRUPTIBLE POWER SUPPLY (UPS)", ups),
    ("battery_packs", "CONNECT TO BATTERY PACK(S)", battery_packs), ("charging", "CHARGING", charging),
    ("storage", "STORAGE", storage), ("troubleshooting", "TROUBLESHOOTING", troubleshooting),
    ("specifications", "SPECIFICATIONS", specifications), ("warranty", "WARRANTY", warranty),
    ("app_setup", "APP SETUP", app_setup),
)


def build() -> dict:
    chapters = [{"id": cid, "title": title, "nodes": make()} for cid, title, make in CHAPTERS]
    missing = [k for k in T.rows if k not in T.used]
    if missing:
        raise ValueError("Web transcription lines not bound: " + ", ".join(missing))
    return {"model": "JHP-2000A-RC", "region": "US", "language": LANGUAGE,
            "title": "Jackery HomePower 2000 Plus User Manual",
            "source_sha256": "e27d4db5606c140439dd32b7d17ab4ed428a62fbfbb5567c7664d8ac22032d51",
            "chapters": chapters}


def main() -> None:
    content = build()
    path = PACKAGE / "source/en/content.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(content, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"chapters": [c["id"] for c in content["chapters"]], "lines": len(T.used)}))


if __name__ == "__main__":
    main()
