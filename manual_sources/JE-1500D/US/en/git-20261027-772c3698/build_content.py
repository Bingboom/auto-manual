"""Bind the reviewed JE-1500D US transcription to shared Web components.

Run from the repository root:

    python manual_sources/JE-1500D/US/en/git-20261027-772c3698/build_content.py

Every Web string comes from ``source/transcription.json`` by line id; this
module only decides which shared component carries each printed block, in
printed order. It writes ``source/en/content.json``, the frozen input that
``rebuild.py`` replays. The printed tables carry their own Symbol/Meaning,
Error Code/Corrective Measures and Buttons/Operation/Function headers, so no
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

from tools.component_specs.app import app_download_component_spec, app_inline_control_component_spec  # noqa: E402
from tools.component_specs.fcc import fcc_component_spec, fcc_semantic_projection  # noqa: E402
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
CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳㉑㉒㉓"
# Print-only chrome on a Web page: the 「EN」 language tab beside IMPORTANT.
PRINT_ONLY = {"imp.badge"}


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


def para(key: str) -> dict:
    return root(node("paragraph", T.inline(key)))


def strong(key: str) -> dict:
    return root(node("paragraph", [node("strong", [text(T(key))])]))


def heading(key: str, level: int = 3, anchor: str | None = None) -> dict:
    value = T(key)
    return root(node("heading", [text(value)], level=level, **({"anchor": anchor} if anchor else {})))


def chapter_heading(key: str, anchor: str) -> dict:
    return heading(key, level=2, anchor=anchor)


def bullets(keys: list[str]) -> dict:
    return root(node("list", [node("list_item", [node("paragraph", T.inline(k))]) for k in keys], ordered=False))


def panel(children: list[dict]) -> dict:
    """Shared grey text panel (web_manual.css ``.hb-text-panel``) for printed grey boxes and pills."""
    return root(node("group", children, role="container",
                     presentation={"html": {"attributes": {"class": "hb-text-panel"}}}))


def panel_lines(keys: list[str], bold: bool = False) -> dict:
    return panel([node("paragraph", [node("strong", [text(T(k))])] if bold else T.inline(k)) for k in keys])


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


def callout_block(label_key: str, body: list[dict], variant: str, ref: str) -> dict:
    return root(callout(T(label_key), body, variant=variant, language=LANGUAGE, source_ref=ref))


def item_list(keys: list[str]) -> dict:
    return node("list", [node("list_item", T.inline(k)) for k in keys], ordered=False)


def body_para(key: str) -> dict:
    return node("paragraph", T.inline(key))


def pair(value: str, key: str) -> dict:
    return {f"{key}_html": escape(value), f"{key}_text": value}


# --- chapters -------------------------------------------------------------

def important() -> list[dict]:
    return [chapter_heading("imp.h", "native-important"), para("imp.p1"), para("imp.p2"), para("imp.p3")]


def safety() -> list[dict]:
    warning = callout_block("safety.warn.label", [
        node("paragraph", [node("strong", [text(T("safety.warn.lead"))])]),
        item_list([f"safety.w{i}" for i in range(1, 12)]),
    ], "warning", "native-pdf/page-4/warning")
    items = []
    for key in [f"op.i{i}" for i in range(1, 15)]:
        children = [body_para(key)]
        for sub in (f"{key}.a", f"{key}.b"):
            if sub in T.rows:
                children.append(body_para(sub))
        items.append(node("list_item", children))
    danger = callout_block("danger.label", [body_para("danger.l1"), body_para("danger.l2")], "danger",
                           "native-pdf/page-5/danger")
    return [chapter_heading("safety.h", "native-important-safety-information"),
            heading("safety.band"), warning,
            heading("op.h"), heading("op.save", level=4), root(node("list", items, ordered=False)),
            danger, heading("maint.h"), para("maint.p")]


SYMBOLS = [("sym.warning", "assets/symbol-01.svg"), ("sym.manual", "assets/symbol-02.svg"),
           ("sym.shock", "assets/symbol-03.svg"), ("sym.charging", "assets/symbol-04.svg"),
           ("sym.explosive", "assets/symbol-05.svg"), ("sym.heavy", "assets/symbol-06.svg"),
           ("sym.dismantle", "assets/symbol-07.svg"), ("sym.fire", "assets/symbol-08.svg"),
           ("sym.children", "assets/symbol-09.svg"), ("sym.liion", "assets/symbol-10.svg"),
           ("sym.weee", "assets/symbol-11.png")]


def fcc() -> dict:
    def block(key: str) -> dict:
        value = T(key)
        for label in ("NOTE:", "MODIFICATION:"):
            if value.startswith(label + " "):
                return {"kind": "paragraph", "label": label, "text": value[len(label) + 1:]}
        return {"kind": "paragraph", "label": "", "text": value}

    left = [block(k) for k in ("fcc.p1", "fcc.p2", "fcc.note", "fcc.limits")]
    right = [block("fcc.if"), {"kind": "list", "items": [T(f"fcc.m{i}") for i in range(1, 5)]}, block("fcc.mod")]
    spec = fcc_component_spec(accessibility_label="FCC", opening_copy=[], left_blocks=left, right_blocks=right,
                              source_ref="native-pdf/page-6/fcc", language=LANGUAGE,
                              mark_asset_ref="assets/fcc-mark.svg")
    payload = fcc_semantic_projection(spec)
    carrier = []
    for item in payload["left_blocks"] + payload["right_blocks"]:
        if item["kind"] == "list":
            carrier.append(node("list", [node("list_item", [text(v)]) for v in item["items"]], ordered=False))
        else:
            carrier.append(node("paragraph", [text(" ".join(filter(None, [item.get("label"), item["text"]])))]))
    # Printed under MEANING OF SYMBOLS, without a heading of its own. The generic
    # docutils container keeps that chapter heading visible: the shared FCC style
    # hides the heading of a section whose direct child is the FCC figure.
    flow = component_flow_node(spec, carrier_flow=tuple(carrier))
    return root(node("group", [flow], role="container",
                     presentation={"html": {"attributes": {"class": "docutils container"}}}))


def symbols() -> list[dict]:
    signal = symbol_signal_component_spec(
        accessibility_label=T.rows["sym.h"]["text"],
        headers=[pair(T("sig.th1"), "content"), pair(T("sig.th2"), "content")],
        rows=[{"label": T(f"sig.{k}.l"), "show_icon": True, **pair(T(f"sig.{k}.m"), "meaning")}
              for k in ("warn", "caut", "note", "tip")],
        source_ref="native-pdf/page-5/signal", language=LANGUAGE)
    headers = [pair(T(f"sym.th{i}"), "content") for i in range(1, 5)]
    meanings = [T(k) for k, _ in SYMBOLS]
    icons = symbol_icon_component_spec(
        accessibility_label=T.rows["sym.h"]["text"], headers=headers,
        panels=[[{"asset_index": i, "icon_alt": meanings[i], **pair(meanings[i], "meaning")} for i in rows]
                for rows in (range(0, 6), range(6, 11))],
        icon_refs=[ref for _, ref in SYMBOLS], source_ref="native-pdf/page-5/symbols", language=LANGUAGE)
    return [chapter_heading("sym.h", "native-meaning-of-symbols"),
            component_flow_node(signal, root=True), component_flow_node(icons, root=True), fcc()]


def in_the_box() -> list[dict]:
    cards = [{"image_ref": ref, "label": T(key), "alt": T.rows[key]["text"]}
             for key, ref in (("box.c1", "assets/inbox-unit.png"), ("box.c2", "assets/inbox-cable.svg"),
                              ("box.c3", "assets/inbox-manual.png"))]
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
    front = ["names.f.power", "names.f.dc12", "names.f.dc12.v", "names.f.usbc1", "names.f.usbc1.v",
             "names.f.usbc2", "names.f.usbc2.v", "names.f.usba", "names.f.usba.v", "names.f.dcusb",
             "names.f.lcd", "names.f.ledbtn", "names.f.led", "names.f.ac", "names.f.ac.v", "names.f.acbtn"]
    right = ["names.r.handle", "names.r.acin", "names.r.acin.v", "names.r.dcin", "names.r.dcin.v1",
             "names.r.dcin.v2", "names.r.dcin.v3"]
    return [chapter_heading("names.h", "native-product-overview"),
            heading("names.front.h"), figure("assets/overview-front.png", "overview-front", 7, front),
            heading("names.right.h"), figure("assets/overview-right.png", "overview-right", 7, right)]


LCD_ROWS = [("1", "01-wifi", ["d1", "d2", "d3"]), ("2", "02-bluetooth", ["d1", "d2", "d3"]),
            ("3", "03-quiet-charging", ["d1", "d2", "d3"]), ("4", "04-battery-saving", ["d1", "d2", "d3"]),
            ("5", "05-charging-plan", ["d1"]), ("6", "06-self-powered", ["d1"]),
            ("7", "07-charging-power-limit", ["d1", "d2"]), ("8", "08-ups", ["d1", "d2"]),
            ("9", "09-ac-power", ["d1"]), ("10", "10-output-voltage-frequency", ["d1"]),
            ("11", "11-input-power", ["d1"]), ("12", "12-remaining-charge-time", ["d1"]),
            ("13", "13-ac-wall-charging", ["d1"]), ("14", "14-car-charging", ["d1"]),
            ("15", "15-solar-charging", ["d1"]), ("16", "16-battery-power", ["d1", "d2"]),
            ("17", "17-low-battery", ["d1", "d2", "d3"]), ("18", "18-remaining-battery", ["d1"]),
            ("19", "19-fault-code", ["d1"]), ("20a", "20a-high-temperature", ["d1"]),
            ("20b", "20b-low-temperature", ["d1"]), ("21", "21-energy-saving", ["d1", "d2"]),
            ("22", "22-output-power", ["d1"]), ("23", "23-remaining-discharge-time", ["d1"])]


def lcd() -> list[dict]:
    values, refs = [], []
    for index, (number, slug, lines) in enumerate(LCD_ROWS):
        name = T(f"lcd.r{number}.t")
        keys = [f"lcd.r{number}.{d}" for d in lines]
        texts = [T.rows[k]["text"] for k in keys]
        circled = CIRCLED[int(number.rstrip("ab")) - 1]
        values.append({**pair(circled, "number"), **pair(name, "name"),
                       "description_html": "<br/>".join(T.html(k) for k in keys),
                       "description_text": "".join(texts), "icon_alt": name, "asset_index": index})
        refs.append(f"assets/lcd-{slug}.svg")
    spec = lcd_icon_component_spec(accessibility_label=T.rows["lcd.h"]["text"], rows=values, icon_refs=refs,
                                   source_ref="native-pdf/pages-8-9/lcd-icons", language=LANGUAGE,
                                   icon_locale_policy="exact")
    return [chapter_heading("lcd.h", "native-lcd-display"),
            figure("assets/lcd-map.png", "lcd-map", 8, [], label=T.rows["lcd.h"]["text"]),
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
                                   source_ref="native-pdf/page-12/lcd-mode", language=LANGUAGE)
    return component_flow_node(spec, root=True)


def operations() -> list[dict]:
    caution = callout_block("ops.dc.caut.l", [item_list(["ops.dc.c1", "ops.dc.c2", "ops.dc.c3"])], "caution",
                            "native-pdf/page-11/caution")
    tip = callout_block("ops.dc.tip.l", [body_para("ops.dc.tip")], "tip", "native-pdf/page-11/tip")
    return [chapter_heading("ops.h", "native-operations"),
            heading("ops.power.h"),
            figure("assets/power.png", "power", 10,
                   ["fig.power.on", "fig.power.on.a", "fig.power.off", "fig.power.off.a", "fig.power.dur"]),
            panel_lines(["ops.power.box.t", "ops.power.box.b", "ops.power.box.n"]),
            para("ops.power.eco"),
            heading("ops.ac.h"), panel_lines(["ops.ac.pre"], bold=True),
            figure("assets/ac-output.png", "ac-output", 10, ["fig.ac.on", "fig.ac.on.a", "fig.ac.off", "fig.ac.off.a"]),
            heading("ops.dc.h"), panel_lines(["ops.dc.pre"], bold=True),
            figure("assets/dc-usb.png", "dc-usb", 11, ["fig.dc.on", "fig.dc.on.a", "fig.dc.off", "fig.dc.off.a"]),
            tip, caution,
            heading("ops.led.h"), panel_lines(["ops.led.modes"]),
            figure("assets/led-light.png", "led-light", 11, ["fig.led.s1", "fig.led.s2", "fig.led.s3"]),
            panel_lines(["ops.led.n1", "ops.led.n2"]),
            heading("ops.lcd.h"), lcd_mode()]


BUTTONS = {"Main Power Button": "assets/shared-buttons/power.svg",
           "DC/USB Power Button": "assets/shared-buttons/dc_usb.svg",
           "AC Power Button": "assets/shared-buttons/ac.svg"}


def key_combinations() -> list[dict]:
    headers = [T(f"keys.th{i}") for i in (1, 2, 3)]
    rows, body = [], []
    for r in (1, 2, 3):
        first, second = T(f"keys.r{r}.b1"), T(f"keys.r{r}.b2")
        duration, operation, function = T(f"keys.r{r}.dur"), T(f"keys.r{r}.op"), T(f"keys.r{r}.fn")
        rows.append([f"{first} + {second}", f"{duration} {operation}", function])

        def button(name: str) -> dict:
            return node("group", [node("image", source=BUTTONS[name], alt=""),
                                  node("inline_group", [node("strong", [text(name)])])],
                        role="container", presentation={"html": {"attributes": {"class": "hb-key-button"}}})

        pair_cell = node("group", [button(first),
                                   node("inline_group", [text("+")],
                                        presentation={"html": {"attributes": {"class": "hb-key-button-plus"}}}),
                                   button(second)],
                         role="container", presentation={"html": {"attributes": {"class": "hb-key-button-pair"}}})
        body.append(node("table_row", [
            node("table_cell", [pair_cell], header=False),
            node("table_cell", [node("paragraph", [text(duration)], presentation={"html": {"attributes": {
                "class": "hb-key-duration", "data-duration-icon": "clock"}}}),
                node("paragraph", [text(operation)])], header=False),
            node("table_cell", [text(function)], header=False)]))
    spec = key_combinations_component_spec(headers=headers, rows=rows, source_ref="native-pdf/page-13/keys",
                                           language=LANGUAGE)
    carrier = node("table", [node("table_head", [node("table_row", [
        node("table_cell", [text(h)], header=True) for h in headers])]), node("table_body", body)],
        presentation={"html": {"attributes": {"class": "hb-key-combination-table"}}})
    return [heading("keys.h"), component_flow_node(spec, carrier_flow=(carrier,), root=True)]


def energy_saving() -> list[dict]:
    note = callout_block("eco.note.l", [item_list(["eco.n1", "eco.n2", "eco.n3"])], "note",
                         "native-pdf/page-12/note")
    return [chapter_heading("eco.h", "native-energy-saving-mode"), para("eco.p1"), para("eco.p2"),
            panel_lines(["eco.onoff"]),
            figure("assets/energy-controls.png", "energy-controls", 12, [], label=T.rows["eco.onoff"]["text"]),
            note, *key_combinations()]


def ups() -> list[dict]:
    caution = callout_block("ups.caut.l", [item_list(["ups.c1", "ups.c2", "ups.c3"])], "caution",
                            "native-pdf/page-13/caution")
    return [chapter_heading("ups.h", "native-ups"), para("ups.p1"),
            figure("assets/ups.png", "ups", 13, [], label=T.rows["ups.h"]["text"]),
            para("ups.p2"), para("ups.p3"), para("ups.p4"), caution]


def charging() -> list[dict]:
    note = callout_block("chg.note.l", [item_list(["chg.n1", "chg.n2"])], "note", "native-pdf/page-14/note")
    ac_caution = callout_block("chg.ac.caut.l", [body_para("chg.ac.caut")], "caution",
                               "native-pdf/page-14/caution-ac")
    solar_caution = callout_block("chg.solar.caut.l", [body_para("chg.solar.c0"),
                                                        item_list(["chg.solar.c1", "chg.solar.c2"])],
                                  "caution", "native-pdf/page-14/caution-solar")
    solar2 = callout_block("chg.solar2.caut.l", [body_para("chg.solar2.caut")], "caution",
                           "native-pdf/page-15/caution-solar-ports")
    car_caution = callout_block("chg.car.caut.l", [item_list(["chg.car.c1", "chg.car.c2", "chg.car.c3"])],
                                "caution", "native-pdf/page-15/caution-car")
    return [chapter_heading("chg.h", "native-charging"), para("chg.green"), para("chg.green2"),
            strong("chg.first"), note,
            heading("chg.ac.h"), para("chg.ac.p"), strong("chg.emg.h"), para("chg.emg.p"), para("chg.emg.n"),
            figure("assets/ac-charge.png", "ac-charge", 14, [], label=T.rows["chg.ac.h"]["text"]),
            ac_caution,
            heading("chg.solar.h"), para("chg.solar.p"), solar_caution,
            figure("assets/solar-adapter.png", "solar-adapter", 15, ["fig.solar.cap"]),
            solar2, para("chg.solar.p2"),
            heading("chg.car.h"), para("chg.car.p"), panel_lines(["chg.car.note"]),
            figure("assets/car-charge.png", "car-charge", 15, ["fig.car.vehicle"]),
            car_caution]


def storage() -> list[dict]:
    return [chapter_heading("sto.h", "native-storage"), para("sto.p1"), bullets(["sto.l1", "sto.l2", "sto.l3"]),
            para("sto.p2")]


def troubleshooting() -> list[dict]:
    restart = T("ts.f03.m")
    rows = [{**pair(T(f"ts.f{i}"), "code"), **pair(restart, "measures")} for i in range(4)]
    for code, keys in (("f4", ["ts.f4.m"]), ("f5", ["ts.f5.m"]), ("f6", [f"ts.f6.m{i}" for i in range(1, 6)]),
                       ("f7", [f"ts.f7.m{i}" for i in range(1, 4)]), ("f8", ["ts.f8.m"]), ("f9", ["ts.f9.m"])):
        texts = [T.rows[k]["text"] for k in keys]
        rows.append({**pair(T(f"ts.{code}"), "code"),
                     "measures_html": "<br/>".join(T.html(k) for k in keys), "measures_text": "".join(texts)})
    spec = troubleshooting_component_spec(headers=[pair(T("ts.th1"), "content"), pair(T("ts.th2"), "content")],
                                          rows=rows, source_ref="native-pdf/page-16/troubleshooting",
                                          language=LANGUAGE)
    return [chapter_heading("ts.h", "native-troubleshooting"), para("ts.p"), component_flow_node(spec, root=True)]


SPEC_GROUPS = (
    ("spec.gen.h", [("spec.g1.l", ["spec.g1.v"]), ("spec.g2.l", ["spec.g2.v"]), ("spec.g3.l", ["spec.g3.v"]),
                    ("spec.g4.l", ["spec.g4.v"]), ("spec.g5.l", ["spec.g5.v"]), ("spec.g6.l", ["spec.g6.v"]),
                    ("spec.g7.l", ["spec.g7.v"])]),
    ("spec.in.h", [("spec.i1.l", ["spec.i1.v1", "spec.i1.v2"]), ("spec.i2.l", ["spec.i2.v1", "spec.i2.v2"])]),
    ("spec.out.h", [("spec.o1.l", ["spec.o1.v1", "spec.o1.v2"]), ("spec.o2.l", ["spec.o2.v"]),
                    ("spec.o3.l", ["spec.o3.v"]), ("spec.o4.l", ["spec.o4.v1", "spec.o4.v2"]),
                    (None, ["spec.o4.v3"]), ("spec.o5.l", ["spec.o5.v"]), ("spec.o6.l", ["spec.o6.v"])]),
    ("spec.env.h", [("spec.e1.l", ["spec.e1.v"]), ("spec.e2.l", ["spec.e2.v"])]),
)


def specifications() -> list[dict]:
    flows = [chapter_heading("spec.h", "native-specifications")]
    for index, (title_key, groups) in enumerate(SPEC_GROUPS, 1):
        title = T(title_key)
        # One printed cell is one value; lines printed inside one cell stay together.
        rows = [(T(label) if label else "", "\n".join(T(k) for k in values)) for label, values in groups]
        spec = spec_table_component_spec(section_title=title, rows=rows,
                                         source_ref=f"native-pdf/page-17/spec-{index}", language=LANGUAGE)
        flows.append(component_flow_node(spec, carrier_flow=_spec_carrier(title, rows), root=True))
    return [*flows, para("spec.fn1"), para("spec.tm")]


def warranty() -> list[dict]:
    def section(index: int, title_key: str, blocks: list[dict]) -> list[dict]:
        # The shared card draws the body; its printed title pill is the heading before it.
        title = heading(title_key)
        spec = warranty_section_component_spec(title=T.rows[title_key]["text"], section_index=index, blocks=blocks,
                                               source_ref=f"native-pdf/warranty/{index}", language=LANGUAGE)
        return [title, component_flow_node(spec, root=True)]

    def p(key: str) -> dict:
        return {"kind": "paragraph", "html": f"<p>{T.html(key)}</p>", "text": T.rows[key]["text"]}

    def ul(*keys: str) -> dict:
        items = [T(k) for k in keys]
        return {"kind": "list", "items": items,
                "html": "<ul>" + "".join(f"<li>{escape(i)}</li>" for i in items) + "</ul>"}

    lead = warranty_lead_component_spec(
        accessibility_label=T.rows["war.h"]["text"], lead_html=f"<strong>{T.html('war.lead')}</strong>",
        local_note_html=T.html("war.note"), source_ref="native-pdf/warranty/lead", language=LANGUAGE)
    periods = []
    for y in ("y1", "y2"):
        body = T(f"war.{y}.b")
        periods.append({"number": T(f"war.{y}.n"), "unit": T(f"war.{y}.u"), "label": T(f"war.{y}.l"),
                        "body_html": escape(body), "body_text": body})
    years_title = heading("war.per.h")
    years = warranty_years_component_spec(title=T.rows["war.per.h"]["text"], periods=periods,
                                          source_ref="native-pdf/warranty/years", language=LANGUAGE)
    return [chapter_heading("war.h", "native-warranty"), component_flow_node(lead, root=True),
            *section(1, "war.lim.h", [p("war.lim.p1"), p("war.lim.p2")]),
            years_title, component_flow_node(years, root=True),
            *section(2, "war.rep.h", [p("war.rep.p")]),
            *section(3, "war.buy.h", [p("war.buy.p")]),
            *section(4, "war.exc.h", [p("war.exc.lead"), ul("war.exc.l1", "war.exc.l2", "war.exc.l3", "war.exc.l4")]),
            *section(5, "war.int.h", [p("war.int.p")])]


def app_setup() -> list[dict]:
    columns = [{"role": "store", "text": T("app.s1.store")}, {"role": "qr", "text": T("app.s1.qr")}]
    for column in columns:
        column["html"] = escape(column["text"])
    download = app_download_component_spec(
        accessibility_label="Jackery App", columns=columns, source_art_ref="assets/app-qr.png",
        store_art_ref="assets/app-store.png", qr_art_ref="assets/app-qr.png",
        source_ref="native-pdf/page-19/download", language=LANGUAGE)
    carrier = [node("image", source="assets/app-qr.png", alt="Jackery App"),
               *(node("paragraph", [text(c["text"])]) for c in columns)]
    before, after = T("app.s21").split(" [+] ")
    plus = app_inline_control_component_spec(
        accessibility_label="+", paragraph_html=f"{escape(before)} <strong>+</strong> {escape(after)}",
        paragraph_text=f"{before} + {after}", source_ref="native-pdf/page-19/add-button", language=LANGUAGE,
        metadata={"visual_recovery": "outlined-pdf-vector-plus-control"})
    plus_carrier = node("paragraph", [text(before + " "), node("strong", [text("+")]), text(" " + after)])
    note1 = callout_block("app.note1.l", [body_para("app.note1")], "note", "native-pdf/page-19/note")
    # The shared callout binds its body as plain text, so the printed bold quote is plain here.
    note2 = callout_block("app.note2.l", [node("paragraph", [text(T("app.note2"))]),
                                          item_list(["app.note2.l1", "app.note2.l2"])],
                          "note", "native-pdf/page-20/note-bound")
    note3 = callout_block("app.note3.l", [body_para("app.note3")], "note", "native-pdf/page-20/note-band")
    return [chapter_heading("app.h", "native-app-setup"),
            heading("app.s1.h"), component_flow_node(download, carrier_flow=carrier, root=True),
            heading("app.s2.h"), component_flow_node(plus, carrier_flow=(plus_carrier,), root=True),
            para("app.s22"),
            figure("assets/app-add.png", "app-add", 19, ["fig.app.c21", "fig.app.c22"]),
            figure("assets/app-control.png", "app-control", 19, ["fig.ctl.power", "fig.ctl.dc", "fig.ctl.ac"]),
            note1, para("app.s23"), note2, para("app.s24"), note3, para("app.s25"),
            figure("assets/app-results.png", "app-results", 20, ["fig.app.c23", "fig.app.c24", "fig.app.c25"]),
            para("app.shots"),
            heading("app.s3.h"), para("app.s3"),
            heading("app.s4.h"),
            heading("app.s41.h", level=4), bullets(["app.s41.l1", "app.s41.l2"]),
            heading("app.s42.h", level=4), bullets(["app.s42.l1", "app.s42.l2"]),
            heading("app.s43.h", level=4), para("app.s43")]


CHAPTERS = (
    ("important", "IMPORTANT", important),
    ("safety", "IMPORTANT SAFETY INFORMATION", safety),
    ("symbols", "MEANING OF SYMBOLS", symbols),
    ("in_the_box", "WHAT'S IN THE BOX", in_the_box),
    ("product_overview", "PRODUCT OVERVIEW", overview),
    ("lcd_display", "LCD DISPLAY", lcd),
    ("operations", "OPERATIONS", operations),
    ("energy_saving", "ENERGY SAVING MODE", energy_saving),
    ("ups", "UNINTERRUPTIBLE POWER SUPPLY (UPS)", ups),
    ("charging", "CHARGING", charging),
    ("storage", "STORAGE", storage),
    ("troubleshooting", "TROUBLESHOOTING", troubleshooting),
    ("specifications", "SPECIFICATIONS", specifications),
    ("warranty", "WARRANTY", warranty),
    ("app_setup", "APP SETUP", app_setup),
)


def build() -> dict:
    chapters = [{"id": cid, "title": title, "nodes": make()} for cid, title, make in CHAPTERS]
    missing = [k for k in T.rows if k not in T.used]
    if missing:
        raise ValueError("Web transcription lines not bound: " + ", ".join(missing))
    return {"model": "JE-1500D", "region": "US", "language": LANGUAGE,
            "title": "Jackery Explorer 1500 User Manual",
            "source_sha256": "772c36987b4233c2c243d64cf0a2e9c8a3fd1f37ad87ad739600cbf474977a79",
            "chapters": chapters}


def main() -> None:
    content = build()
    path = PACKAGE / "source/en/content.json"
    path.write_text(json.dumps(content, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"chapters": [c["id"] for c in content["chapters"]], "lines": len(T.used)}))


if __name__ == "__main__":
    main()
