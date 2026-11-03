"""Bind the reviewed JE-2000F JP transcription to shared Web components.

Run from the repository root:

    python manual_sources/JE-2000F/JP/ja/git-20261103-63cdf705/build_content.py

Every Web string comes from ``source/transcription.json`` by line id; this
module only decides which shared component carries each printed block, in
printed order. It writes ``source/ja/content.json``, the frozen input that
``rebuild.py`` replays. Component chrome follows the same-model JE-2000F US/en
package and the JE-1000D JP V2 package; ``source/differences.md`` lists every
layout decision.
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
ENERGY_ICON = "assets/lcd-energy-saving.svg"
# Printed list markers that are text-layer characters; the shared list draws its own marker.
LIST_MARKERS = ("• ", "◦ ")


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

    def peek(self, key: str) -> str:
        return self.rows[key]["text"]

    def spans(self, key: str, value: str | None = None) -> list[tuple[str, str]]:
        """(style, text) runs: plain, strong or sub, in printed order."""
        value = self(key) if value is None else value
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

    def item(self, key: str) -> str:
        """A list item line without its printed text-layer marker."""
        value = self(key)
        for marker in LIST_MARKERS:
            if value.startswith(marker):
                return value[len(marker):]
        return value


T = Lines()


# --- flow helpers -----------------------------------------------------------

def p(key: str) -> dict:
    return node("paragraph", T.inline(key))


def para(key: str) -> dict:
    return root(p(key))


def strong_p(key: str) -> dict:
    return node("paragraph", [node("strong", [text(T(key))])])


def heading(key: str, level: int = 3, anchor: str | None = None) -> dict:
    return root(node("heading", [text(T(key))], level=level, **({"anchor": anchor} if anchor else {})))


def chapter_heading(key: str, anchor: str) -> dict:
    return heading(key, level=2, anchor=anchor)


def li(keys: list[str], nested: list[str] | None = None) -> dict:
    children = [node("paragraph", [text(T.item(k))]) for k in keys]
    if nested:
        children.append(node("list", [node("list_item", [node("paragraph", [text(T.item(k))])]) for k in nested],
                             ordered=False))
    return node("list_item", children)


def ul(keys: list[str]) -> dict:
    return node("list", [li([k]) for k in keys], ordered=False)


def bullets(keys: list[str], ordered: bool = False) -> dict:
    return root(node("list", [li([k]) for k in keys], ordered=ordered))


def panel(children: list[dict]) -> dict:
    """Shared grey text panel (web_manual.css ``.hb-text-panel``)."""
    return root(node("group", children, role="container", presentation=attrs("hb-text-panel")))


def with_icon(key: str, marker: str, ref: str, alt: str) -> dict:
    """A printed line whose bracketed marker is a drawn glyph, set inline as that glyph."""
    before, after = T(key).split(marker)
    return node("paragraph", [text(before.rstrip() + " "), node("image", source=ref, alt=alt),
                              text(" " + after.lstrip())])


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
    """The shared callout carrier of ``tools.web.frozen_ai_flow.callout`` (JE-2000F US/en idiom)."""
    items = [" ".join(leaves(item)) for block in body if block["kind"] == "list" for item in block["children"]]
    spec = callout_component_spec(label=label, body="\n".join(part for b in body for part in leaves(b)),
                                  items=items, variant=variant, language=LANGUAGE, source_ref=ref)
    carrier = table([[node("table_cell", [text(label)], header=False, presentation=attrs("manual-callout-label")),
                      node("table_cell", body, header=False, presentation=attrs("manual-callout-body"))]],
                    css_class=f"manual-callout-table {web_callout_classes(spec)['table']}")
    return component_flow_node(spec, carrier_flow=[carrier])


def callout_block(label_key: str, body: list[dict], variant: str, ref: str, *, label: str | None = None) -> dict:
    return root(callout(label if label is not None else T(label_key), body, variant=variant, ref=ref))


def caution_list(label_key: str, keys: list[str], ref: str) -> dict:
    return callout_block(label_key, [ul(keys)], "caution", ref)


def plain_table(header: list[dict] | None, rows: list[list[dict]]) -> dict:
    """Declared plain table on the shared manual-table classes (shared_component_exceptions)."""
    body = node("table_body", [node("table_row", row) for row in rows])
    parts = ([node("table_head", [node("table_row", header)])] if header else []) + [body]
    return root(node("group", [node("table", parts, presentation=attrs("manual-table"))],
                     role="container", presentation=attrs("table-wrapper docutils container")))


def cell(children: list[dict], *, header: bool = False, **fields) -> dict:
    return node("table_cell", children, header=header, **fields)


def pair(value: str, key: str) -> dict:
    return {f"{key}_html": escape(value), f"{key}_text": value}


# --- chapters ---------------------------------------------------------------

SYMBOLS = [("sym.s1", "assets/symbol-01.svg"), ("sym.s2", "assets/symbol-02.svg"),
           ("sym.s3", "assets/symbol-03.svg"), ("sym.s4", "assets/symbol-04.svg"),
           ("sym.s5", "assets/symbol-05.svg"), ("sym.s6", "assets/symbol-06.svg"),
           ("sym.s7", "assets/symbol-07.svg"), ("sym.s8", "assets/symbol-08.svg"),
           ("sym.s9", "assets/symbol-09.svg"), ("sym.s10", "assets/symbol-10.svg")]
DISPOSAL = [(["rec.weee.b1", "rec.weee.b2", "rec.weee.b3"], "assets/symbol-11.png"),
            (["rec.bin.b1", "rec.bin.b2", "rec.bin.b3"], "assets/symbol-12.png")]
# Shared component chrome (JE-1000D / JE-1500D JP V2), not source text.
SIGNAL_HEADERS = ("表示", "意味")
SYMBOL_HEADERS = ("記号", "意味", "記号", "意味")


def warning_item(label: str, title_key: str, body_keys: list[str], ref: str, *,
                 list_keys: list[str] | None = None, tail: list[dict] | None = None) -> dict:
    body = [strong_p(title_key)]
    if list_keys:
        body.append(ul(list_keys))
    body += [p(k) for k in body_keys]
    body += tail or []
    return callout_block("", body, "warning" if label == "警告" else "caution", ref, label=label)


def safety() -> list[dict]:
    signal = symbol_signal_component_spec(
        accessibility_label=T.peek("pict.h"),
        headers=[pair(v, "content") for v in SIGNAL_HEADERS],
        rows=[{"label": T(f"sig.{k}.l"), "show_icon": k in ("warn", "caut"), **pair(T(f"sig.{k}.m"), "meaning")}
              for k in ("warn", "caut", "note", "tip")],
        source_ref="native-pdf/page-3/signal", language=LANGUAGE)
    meanings = [T(k) for k, _ in SYMBOLS]
    pictograms = symbol_icon_component_spec(
        accessibility_label=T.peek("sym.h"), headers=[pair(v, "content") for v in SYMBOL_HEADERS],
        panels=[[{"asset_index": i, "icon_alt": meanings[i], **pair(meanings[i], "meaning")} for i in rows]
                for rows in (range(0, 5), range(5, 10))],
        icon_refs=[ref for _, ref in SYMBOLS], source_ref="native-pdf/page-3/symbols", language=LANGUAGE,
        icon_locale_policy="exact")
    # Li-ion 32 recycling notice: no shared symbol variant passes admission yet (pending_shared_symbols);
    # the original PDF vector mark sits in a declared plain two-cell table (JE-1000D JP idiom).
    recycle = plain_table(None, [[
        cell([node("image", source="assets/recycle-li-ion.svg", alt=T.peek("rec.liion.t"))]),
        cell([strong_p("rec.liion.t"), p("rec.liion.b1"), p("rec.liion.b2"), p("rec.liion.b3")]),
    ]])
    disposal_html = ["<br/>".join(T.html(k) for k in keys) for keys, _ in DISPOSAL]
    disposal_text = ["".join(T.peek(k) for k in keys) for keys, _ in DISPOSAL]
    disposal = symbol_icon_component_spec(
        accessibility_label=T.peek("rec.liion.t"), headers=[pair(v, "content") for v in SYMBOL_HEADERS],
        panels=[[{"asset_index": i, "icon_alt": disposal_text[i], "meaning_html": disposal_html[i],
                  "meaning_text": disposal_text[i]}] for i in (0, 1)],
        icon_refs=[ref for _, ref in DISPOSAL], source_ref="native-pdf/page-4/disposal", language=LANGUAGE,
        icon_locale_policy="exact")
    w1, w2, c1 = T("w1.band"), T("w2.band"), T("c1.band")
    grid = [warning_item(w1, f"w1.i{i}.t", [f"w1.i{i}.b"], f"native-pdf/page-4/warning-{i}") for i in range(1, 9)]
    first = warning_item(w2, "w2.i1.t", ["w2.i1.b1", "w2.i1.b2"], "native-pdf/page-5/warning-1",
                         list_keys=[f"w2.i1.l{i}" for i in range(1, 6)],
                         tail=[strong_p("w2.i1.t2"), p("w2.i1.b3"), p("w2.i1.b4")])
    return [chapter_heading("safety.h", "native-safety"), root(strong_p("safety.lead")),
            heading("pict.h"), para("pict.p1"), para("pict.p2"), component_flow_node(signal, root=True),
            heading("sym.h"), component_flow_node(pictograms, root=True),
            recycle, component_flow_node(disposal, root=True),
            *grid, first,
            warning_item(w2, "w2.i2.t", ["w2.i2.b"], "native-pdf/page-5/warning-2"),
            warning_item(w2, "w2.i3.t", ["w2.i3.b"], "native-pdf/page-5/warning-3"),
            warning_item(w2, "w2.i4.t", [], "native-pdf/page-5/warning-4"),
            warning_item(c1, "c1.i1.t", ["c1.i1.b"], "native-pdf/page-5/caution-1"),
            warning_item(c1, "c1.i2.t", [], "native-pdf/page-5/caution-2",
                         list_keys=["c1.i2.l1", "c1.i2.l2", "c1.i2.l3"]),
            warning_item(c1, "c1.i3.t", ["c1.i3.b"], "native-pdf/page-5/caution-3"),
            warning_item(c1, "c1.i4.t", [], "native-pdf/page-5/caution-4")]


def precautions() -> list[dict]:
    temps = root(node("list", [li(["prec.s5.l1"]), li(["prec.s5.l2"], ["prec.s5.l2a", "prec.s5.l2b"]),
                               li(["prec.s5.l3"])], ordered=False))
    return [chapter_heading("prec.h", "native-usage-precautions"),
            panel([p("prec.p1"), p("prec.p2"), p("prec.p3"), p("prec.p4")]),
            callout_block("prec.c.l", [p("prec.c")], "caution", "native-pdf/page-6/caution"),
            root(strong_p("prec.s1.h")), para("prec.s1.p"), bullets([f"prec.s1.l{i}" for i in range(1, 5)]),
            root(strong_p("prec.s2.h")), bullets([f"prec.s2.l{i}" for i in range(1, 6)]),
            root(strong_p("prec.s3.h")), bullets([f"prec.s3.l{i}" for i in range(1, 4)]),
            root(strong_p("prec.s4.h")), bullets([f"prec.s4.l{i}" for i in range(1, 4)]),
            root(strong_p("prec.s5.h")), temps]


def disclaimer() -> list[dict]:
    return [chapter_heading("disc.h", "native-disclaimer"),
            panel([ul([f"disc.l{i}" for i in range(1, 7)])])]


def in_the_box() -> list[dict]:
    cards = [{"image_ref": ref, "label": T(key), "alt": T.peek(key)}
             for key, ref in (("box.c1", "assets/inbox-unit.png"), ("box.c2", "assets/inbox-ac-cable.svg"),
                              ("box.c3", "assets/inbox-documents.svg"))]
    title = T.peek("box.h")
    spec = inbox_component_spec(accessibility_label=title, cards=cards, tip_label="", tip_body="",
                                source_ref="native-pdf/page-8/inbox", language=LANGUAGE, require_tip=False)
    carrier = table([[node("table_cell", [node("image", source=c["image_ref"], alt=c["alt"]),
                                          node("paragraph", [text(c["label"])])], header=False) for c in cards]])
    return [chapter_heading("box.h", "native-in-the-box"), component_flow_node(spec, carrier_flow=(carrier,), root=True),
            panel([p("box.n1"), p("box.n2"), p("box.n3"), p("box.n4")]), root(strong_p("box.change"))]


def overview() -> list[dict]:
    front = ["ov.f.power", "ov.f.car", "ov.f.car.s", "ov.f.c30", "ov.f.c30.s", "ov.f.c100", "ov.f.c100.s",
             "ov.f.a18", "ov.f.a18.s", "ov.f.dcusb", "ov.f.lcd", "ov.f.ledbtn", "ov.f.led", "ov.f.acout",
             "ov.f.acout.s", "ov.f.acbtn"]
    right = ["ov.r.handle", "ov.r.acin", "ov.r.acin.s", "ov.r.dcin", "ov.r.dcin.pv", "ov.r.dcin.car"]
    return [chapter_heading("ov.h", "native-product-overview"),
            heading("ov.front"), figure("assets/overview-front.png", "overview-front", 8, front),
            heading("ov.right"), figure("assets/overview-right.png", "overview-right", 9, right)]


LCD_ICONS = ["wifi", "bluetooth", "quiet-charging", "charging-plan", "self-powered", "tou", "ups", "ac-power",
             "output-voltage-frequency", "input-power", "remaining-charge-time", "ac-wall-charging", "car-charging",
             "solar-charging", "battery-saving", "charging-power-limit", "battery-power", "low-battery",
             "remaining-battery-percentage", "discharge-timer", "energy-saving", "high-temperature",
             "low-temperature", "fault-code", "output-power", "remaining-discharge-time"]
LCD_NUMBERS = [*range(1, 23), 22, 23, 24, 25]


def lcd() -> list[dict]:
    rows, refs = [], []
    for index, (number, icon) in enumerate(zip(LCD_NUMBERS, LCD_ICONS, strict=True)):
        key = f"d{index + 1}"
        name = T(f"lcd.{key}.t")
        name_html, name_text = escape(name), name
        if f"lcd.{key}.s" in T.rows:  # small second line printed in the name cell
            sub = T(f"lcd.{key}.s")
            name_html, name_text = f"{name_html}<br/>{escape(sub)}", f"{name} {sub}"
        bodies = sorted((k for k in T.rows if k.startswith(f"lcd.{key}.b")), key=lambda k: int(k.rsplit("b", 1)[1]))
        html = "<br/>".join(T.html(k) for k in bodies)
        value = " ".join(T.peek(k) for k in bodies)
        rows.append({"number_html": CIRCLED[number - 1], "number_text": CIRCLED[number - 1],
                     "name_html": name_html, "name_text": name_text, "description_html": html,
                     "description_text": value, "icon_alt": name, "asset_index": index})
        refs.append(f"assets/lcd-{icon}.svg")
    spec = lcd_icon_component_spec(accessibility_label=T.peek("lcd.h"), rows=rows, icon_refs=refs,
                                   source_ref="native-pdf/pages-10-11/lcd-icons", language=LANGUAGE,
                                   icon_locale_policy="exact", numbered=True)
    return [chapter_heading("lcd.h", "native-lcd-display"),
            figure("assets/lcd-map.png", "lcd-map", 9, [], label=T.peek("lcd.h")),
            component_flow_node(spec, root=True)]


def key_cell(left_key: str, left_art: str, right_key: str, right_art: str) -> dict:
    def button(key: str, art: str) -> dict:
        return node("group", [node("image", source=art, alt=""), node("paragraph", [text(T(key))])],
                    role="container", presentation=attrs("hb-key-button"))
    return node("table_cell", [node("group", [
        button(left_key, left_art), node("inline_group", [], presentation=attrs("hb-key-button-plus")),
        button(right_key, right_art)], role="container", presentation=attrs("hb-key-button-pair"))], header=False)


KEY_ROWS = [("assets/button-power.svg", "assets/button-ac.svg"),
            ("assets/button-power.svg", "assets/button-dc-usb.svg"),
            ("assets/button-ac.svg", "assets/button-dc-usb.svg"),
            ("assets/button-power.svg", "assets/button-light.svg")]


def key_combinations() -> dict:
    headers = [T(f"key.th{i}") for i in (1, 2, 3)]
    rows, carriers = [], []
    for index, (left_art, right_art) in enumerate(KEY_ROWS, start=1):
        r = f"key.r{index}"
        left, right = T.peek(f"{r}.b1"), T.peek(f"{r}.b2")
        first = key_cell(f"{r}.b1", left_art, f"{r}.b2", right_art)
        duration, operation, function = T(f"{r}.t"), T(f"{r}.o"), T(f"{r}.f")
        rows.append([f"{left} {right}", f"{duration} {operation}", function])
        second = node("table_cell", [
            node("inline_group", [text(duration)],
                 presentation=attrs("hb-key-duration", **{"data-duration-icon": "clock"})),
            node("paragraph", [text(operation)])], header=False)
        carriers.append(node("table_row", [first, second, node("table_cell", [text(function)], header=False)]))
    spec = key_combinations_component_spec(headers=headers, rows=rows, source_ref="native-pdf/page-16/key-combinations",
                                           language=LANGUAGE)
    carrier = node("table", [node("table_head", [node("table_row", [node("table_cell", [text(h)], header=True)
                                                                    for h in headers])]),
                             node("table_body", carriers)], presentation=attrs("hb-key-combination-table"))
    return component_flow_node(spec, carrier_flow=[carrier], root=True)


def lcd_screen() -> dict:
    groups = []
    for state in ("scr.m1", "scr.m2"):
        groups.append({**pair(T(state), "state"), "actions": [
            {**pair(T(f"{state}.a{a}"), "action"), **pair(T(f"{state}.d{a}"), "description")} for a in (1, 2, 3)]})
    spec = lcd_mode_component_spec(accessibility_label=T.peek("scr.h"), groups=groups,
                                   artwork_ref="assets/lcd-screen.png", artwork_locale_policy="exact",
                                   source_ref="native-pdf/page-15/lcd-screen", language=LANGUAGE)
    return component_flow_node(spec, root=True)


def auto_resume() -> dict:
    spec = auto_resume_component_spec(
        headers=[T("res.th1"), T("res.th2")],
        conditions=[[T(f"res.a{i}") for i in (1, 2, 3)], [T(f"res.n{i}") for i in (1, 2, 3, 4)]],
        source_ref="native-pdf/page-15/auto-resume", language=LANGUAGE)
    return component_flow_node(spec, root=True)


def energy_table() -> dict:
    head = [cell([text(T(f"eco.th{i}"))], header=True) for i in (1, 2, 3)]
    rows = [[cell([text(T("eco.r1.c1"))]), cell([text(T("eco.r1.c2"))]),
             cell([text(T("eco.default"))], row_span=2)],
            [cell([text(T("eco.r2.c1"))]), cell([text(T("eco.r2.c2"))])]]
    return plain_table(head, rows)


def usage() -> list[dict]:
    energy_alt = "88H"
    return [chapter_heading("use.h", "native-usage"),
            heading("pwr.h"),
            figure("assets/power-on-off.png", "power-on-off", 12,
                   ["fig.pwr.on", "fig.pwr.on.s", "fig.pwr.off", "fig.pwr.off.s", "fig.pwr.3s"]),
            panel([p("pwr.standby")]), panel([p("pwr.eco")]),
            heading("ac.h"), panel([p("ac.pre")]),
            figure("assets/ac-output.png", "ac-output", 12, ["fig.ac.on", "fig.ac.on.s", "fig.ac.off", "fig.ac.off.s"]),
            heading("freq.h"), panel([p("freq.p1"), p("freq.p2"), p("freq.p3")]),
            figure("assets/frequency.png", "frequency", 13, ["fig.freq.50", "fig.freq.60"]),
            heading("dc.h"), panel([p("dc.pre")]),
            figure("assets/dc-usb-output.png", "dc-usb-output", 13,
                   ["fig.dc.on", "fig.dc.on.s", "fig.dc.off", "fig.dc.off.s"]),
            caution_list("dc.c.l", ["dc.c.i1", "dc.c.i2", "dc.c.i3"], "native-pdf/page-13/usb-caution"),
            para("car.p1"), para("car.p2"),
            caution_list("car.c.l", ["car.c.i1", "car.c.i2", "car.c.i3"], "native-pdf/page-14/car-caution"),
            heading("eco.h"), panel([with_icon("eco.p", "[88H]", ENERGY_ICON, energy_alt)]),
            energy_table(),
            panel([with_icon("eco.off", "[88H]", ENERGY_ICON, energy_alt), p("eco.how")]),
            figure("assets/energy-saving.png", "energy-saving", 14,
                   ["fig.eco.power", "fig.eco.ac", "fig.eco.3s", "fig.eco.onoff", "fig.eco.hold"]),
            callout_block("eco.note.l", [p("eco.note")], "note", "native-pdf/page-14/note"),
            heading("res.h"), para("res.p"), auto_resume(),
            heading("led.h"), panel([p("led.modes")]),
            figure("assets/led-light.png", "led-light", 15,
                   ["fig.led.btn", "fig.led.n1", "fig.led.n2", "fig.led.sos", "fig.led.n3"]),
            bullets(["led.s1", "led.s2", "led.s3"], ordered=True),
            heading("scr.h"), lcd_screen(), para("scr.app"),
            heading("key.h"), key_combinations()]


def ups() -> list[dict]:
    return [chapter_heading("ups.h", "native-ups"),
            figure("assets/ups.png", "ups", 16, [], label=T.peek("ups.h")),
            panel([p("ups.fig")]),
            panel([p("ups.p1"), p("ups.p2"), *(p(f"ups.l{i}") for i in range(1, 5)), p("ups.p3"),
                   p("ups.p4"), p("ups.p5")])]


def charging() -> list[dict]:
    four = root(node("list", [li(["sol.four.l1"], ["sol.four.l1a", "sol.four.l1b"])], ordered=False))
    two = root(node("list", [li(["sol.two.l1", "sol.two.l2", "sol.two.l3"])], ordered=False))
    solar_caution = callout_block("sol.c.l", [p("sol.c.p1"), p("sol.c.p2"), p("sol.c.p3"),
                                              ul(["sol.c.i1", "sol.c.i2"])], "caution",
                                  "native-pdf/page-19/solar-caution")
    return [chapter_heading("chg.h", "native-charging"),
            root(strong_p("chg.green.h")), para("chg.green"),
            caution_list("chg.c1.l", ["chg.c1.i1", "chg.c1.i2"], "native-pdf/page-17/caution-1"),
            caution_list("chg.c2.l", ["chg.c2.i1", "chg.c2.i2", "chg.c2.i3"], "native-pdf/page-17/caution-2"),
            heading("chg.ac.h"), para("chg.ac.p"),
            figure("assets/charging-ac.png", "charging-ac", 18, ["fig.chg.ac"]),
            callout_block("chg.ac.c.l", [p("chg.ac.c")], "caution", "native-pdf/page-18/ac-caution"),
            panel([p("chg.emg"), p("chg.emg.n")]),
            heading("sol.h"), para("sol.p"),
            panel([strong_p("sol.acc.h"), ul(["sol.acc.l1", "sol.acc.l2"]), p("sol.acc.n")]),
            root(strong_p("sol.two.h")), two,
            figure("assets/charging-solar-200.png", "solar-two", 19, ["fig.sol1"]),
            root(strong_p("sol.four.h")), four,
            figure("assets/charging-solar-100air.png", "solar-four", 19, ["fig.sol2", "fig.sol2.adapter"]),
            solar_caution, para("sol.voc"),
            heading("car.h"), root(strong_p("car.lead")), para("car.intro"),
            bullets([f"car.l{i}" for i in range(1, 6)]),
            figure("assets/charging-car.png", "charging-car", 20, ["fig.car.vehicle", "fig.car.note"]),
            caution_list("car.c2.l", ["car.c2.i1", "car.c2.i2"], "native-pdf/page-20/car-caution")]


def troubleshooting() -> list[dict]:
    rows = []
    for index in range(1, 9):
        codes = sorted(k for k in T.rows if k.startswith(f"ts.r{index}.c"))
        steps = sorted(k for k in T.rows if k.startswith(f"ts.r{index}.m"))
        code_values = [T(k) for k in codes]
        rows.append({"code_html": "<br />".join(escape(v) for v in code_values), "code_text": " ".join(code_values),
                     "measures_html": "<br />".join(T.html(k) for k in steps),
                     "measures_text": " ".join(T.peek(k) for k in steps)})
    spec = troubleshooting_component_spec(headers=[pair(T("ts.th1"), "content"), pair(T("ts.th2"), "content")],
                                          rows=rows, source_ref="native-pdf/page-21/troubleshooting",
                                          language=LANGUAGE)
    return [chapter_heading("ts.h", "native-troubleshooting"), para("ts.p1"), para("ts.p2"),
            component_flow_node(spec, root=True)]


def specifications() -> list[dict]:
    nodes = [chapter_heading("spec.h", "native-specifications")]
    for group, count in (("g", 6), ("i", 2), ("o", 6), ("t", 3)):
        title = T(f"spec.{group}.h")
        rows = []
        for index in range(1, count + 1):
            label = T(f"spec.{group}{index}.l")
            values = [T(k) for k in sorted(k for k in T.rows if k.startswith(f"spec.{group}{index}.v"))]
            rows.append((label, "\n".join(values)))
        spec = spec_table_component_spec(section_title=title, rows=rows, source_ref=f"native-pdf/page-22/{group}",
                                         language=LANGUAGE)
        nodes.append(component_flow_node(spec, carrier_flow=_spec_carrier(title, rows), root=True))
    return [*nodes, para("spec.cert"), para("spec.tm"), para("spec.fn1")]


def warranty() -> list[dict]:
    def block(*keys: str) -> dict:
        return {"kind": "paragraph", "html": "<p>" + "<br/>".join(T.html(k) for k in keys) + "</p>",
                "text": "".join(T.peek(k) for k in keys)}

    def section(index: int, title_key: str, blocks: list[dict]) -> list[dict]:
        # The shared card draws the body; its printed title pill is the heading before it.
        title = heading(title_key)
        spec = warranty_section_component_spec(title=T.peek(title_key), section_index=index, blocks=blocks,
                                               source_ref=f"native-pdf/warranty/{index}", language=LANGUAGE)
        return [title, component_flow_node(spec, root=True)]

    return [chapter_heading("war.h", "native-warranty"),
            panel([p("war.lead1"), p("war.lead2"), p("war.lead3")]),
            *section(1, "war.per.h", [block("war.per.p1", "war.per.l1", "war.per.l2"), block("war.per.p2"),
                                      block("war.per.n"), block("war.per.p3")]),
            *section(2, "war.sc.h", [block("war.sc.t1", "war.sc.b1"), block("war.sc.n"),
                                     block("war.sc.t2", "war.sc.b2")]),
            *section(3, "war.cond.h", [block("war.cond.p", "war.cond.l1", "war.cond.l2", "war.cond.l3")]),
            *section(4, "war.ex.h", [block("war.ex.p", *(f"war.ex.l{i}" for i in range(1, 7)))]),
            *section(5, "war.proof.h", [block("war.proof.p", "war.proof.l1", "war.proof.l2"), block("war.proof.n")]),
            *section(6, "war.cont.h", [block("war.cont1.t", "war.cont1.l1", "war.cont1.l2"),
                                       block("war.cont2.t", "war.cont2.l1", "war.cont2.l2"),
                                       block("war.cont3.t", "war.cont3.p", "war.cont3.l1", "war.cont3.l2",
                                             "war.cont3.l3", "war.cont3.after"),
                                       block("war.cont.n")]),
            panel([strong_p("war.disc.h"), *(p(f"war.disc{i}") for i in range(1, 6))]),
            panel([p("contact.web"), p("contact.mail"), p("contact.tel")])]


def app_setup() -> list[dict]:
    columns = [{"role": "store", "text": T("app.s1.store")}, {"role": "qr", "text": T("app.s1.qr")}]
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
    before, after = T("app.s21").split(" [+] ")
    plus = app_inline_control_component_spec(
        accessibility_label="+", paragraph_html=f"{escape(before)} <strong>+</strong> {escape(after)}",
        paragraph_text=f"{before} + {after}", source_ref="native-pdf/page-25/add-button", language=LANGUAGE,
        metadata={"visual_recovery": "pdf-vector-plus-control"})
    plus_carrier = node("paragraph", [text(before + " "), node("strong", [text("+")]), text(" " + after)])
    note1 = callout_block("app.n1.l", [p("app.n1"), ul(["app.n1.i1", "app.n1.i2"])], "note",
                          "native-pdf/page-26/note-1")
    return [chapter_heading("app.h", "native-app-setup"),
            heading("app.s1.h"), component_flow_node(download, carrier_flow=carrier, root=True),
            heading("app.s2.h"), component_flow_node(plus, carrier_flow=(plus_carrier,), root=True),
            para("app.s22"),
            figure("assets/app-add.png", "app-add", 25, ["fig.app.c21", "fig.app.c22"]),
            figure("assets/app-panel.png", "app-panel", 25, ["fig.ctl.power", "fig.ctl.dcusb", "fig.ctl.ac"]),
            para("app.s23"), note1, para("app.s24"),
            callout_block("app.n2.l", [p("app.n2")], "note", "native-pdf/page-26/note-2"),
            para("app.s25"),
            figure("assets/app-results.png", "app-results", 26, ["fig.app.c23", "fig.app.c24", "fig.app.c25"]),
            para("app.shots"),
            callout_block("app.n3.l", [p("app.n3")], "note", "native-pdf/page-26/note-3"),
            heading("app.s3.h"), para("app.s3"),
            heading("app.s4.h"),
            heading("app.s41.h", level=4), bullets(["app.s41.i1", "app.s41.i2"]),
            heading("app.s42.h", level=4), para("app.s42"),
            heading("app.s43.h", level=4), para("app.s43")]


CHAPTERS = (
    ("safety", "安全上のご注意", safety), ("usage_precautions", "使用上のご注意", precautions),
    ("disclaimer", "免責事項", disclaimer), ("in_the_box", "同梱品", in_the_box),
    ("product_overview", "各部の名称", overview), ("lcd_display", "液晶画面", lcd),
    ("usage", "使い方", usage), ("ups", "UPS 機能", ups), ("charging", "充電方法", charging),
    ("troubleshooting", "トラブルシューティング", troubleshooting), ("specifications", "主な仕様", specifications),
    ("warranty", "保証について", warranty), ("app_setup", "Jackeryアプリ ユーザーマニュアル", app_setup),
)


def build() -> dict:
    chapters = [{"id": cid, "title": title, "nodes": make()} for cid, title, make in CHAPTERS]
    missing = [k for k in T.rows if k not in T.used]
    if missing:
        raise ValueError("Web transcription lines not bound: " + ", ".join(missing))
    return {"model": "JE-2000F", "region": "JP", "language": LANGUAGE,
            "title": "Jackery ポータブル電源 2000 New 取扱説明書",
            "source_sha256": "63cdf705e41a1680ca974cc69e5f233cd0e5e4d278d5cc5302dcb3389b361393",
            "chapters": chapters}


def main() -> None:
    content = build()
    path = PACKAGE / "source/ja/content.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(content, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"chapters": [c["id"] for c in content["chapters"]], "lines": len(T.used)}))


if __name__ == "__main__":
    main()
