"""Bind the reviewed JE-1000H JP transcription to shared Web components.

Run from the repository root:

    python manual_sources/JE-1000H/JP/ja/git-20261103-717c813d/build_content.py

Every Web string comes from ``source/transcription.json`` by line id; this
module only decides which shared component carries each printed block, in
printed order. It writes ``source/ja/content.json``, the frozen input that
``rebuild.py`` replays. Component chrome that the shared components require
(signal/symbol table headers, the key-combination plus sign) follows the
JE-1000D JP V2 and JE-2000E JP editions and is listed in
``source/differences.md``. ``PENDING_SYMBOL_LINES`` are the captions of the
three printed symbol rows that no shared variant admits yet; they stay out of
the Web body until the shared catalog gains their variants.
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
from tools.component_specs.auto_resume import auto_resume_component_spec  # noqa: E402
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
from tools.web.frozen_ai_flow import callout, node, root, table, text  # noqa: E402
from tools.web.frozen_ai_table_components import _spec_carrier  # noqa: E402

LANGUAGE = "ja"
SOURCE_SHA256 = "717c813db4c64d57f90072da6f40081162131979cc181a440c589e70d9947da4"
ECO_ICON = "assets/lcd/22_energy_saving_mode.png"
# Printed symbol rows without an admissible shared variant (see source_manifest.json:pending_symbols).
PENDING_SYMBOL_LINES = ("sym.read", "sym.wet", "recycle.title", "recycle.b1", "recycle.b2", "recycle.b3")


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
    return root(node("heading", [text(T(key))], level=level, **({"anchor": anchor} if anchor else {})))


def chapter_heading(key: str, anchor: str) -> dict:
    return heading(key, level=2, anchor=anchor)


def items(keys: list[str], nested: dict[str, list[str]] | None = None) -> dict:
    nested = nested or {}
    out = []
    for key in keys:
        children = [node("paragraph", T.inline(key))]
        if key in nested:
            children.append(node("list", [node("list_item", [node("paragraph", T.inline(k))])
                                          for k in nested[key]], ordered=False))
        out.append(node("list_item", children))
    return node("list", out, ordered=False)


def bullets(keys: list[str], nested: dict[str, list[str]] | None = None) -> dict:
    return root(items(keys, nested))


def panel(children: list[dict]) -> dict:
    """Shared grey text panel (web_manual.css ``.hb-text-panel``)."""
    return root(node("group", children, role="container",
                     presentation={"html": {"attributes": {"class": "hb-text-panel"}}}))


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


def box(label_key: str, body: list[dict], variant: str, ref: str) -> dict:
    return root(callout(T(label_key), body, variant=variant, language=LANGUAGE, source_ref=ref))


def p(*keys: str) -> dict:
    """Body paragraph node (inside a callout) with printed bold spans."""
    children: list[dict] = []
    for key in keys:
        children += T.inline(key)
    return node("paragraph", children)


def bold(key: str) -> dict:
    return node("paragraph", [node("strong", [text(T(key))])])


def with_icon(key: str) -> dict:
    """A printed sentence whose [88H] mark is the LCD energy-saving icon itself."""
    before, after = T(key).split(" [88H] ")
    return root(node("paragraph", [text(before), node("image", source=ECO_ICON, alt="88H"), text(after)]))


# --- chapters -------------------------------------------------------------

SYMBOLS = [("sym.warning", "assets/symbol-warning.svg"), ("sym.fire", "assets/symbol-fire.svg"),
           ("sym.children", "assets/symbol-children.svg"), ("sym.dismantle", "assets/symbol-dismantle.svg"),
           ("sym.unplug", "assets/symbol-unplug.svg"), ("sym.wethand", "assets/symbol-wethand.svg"),
           ("sym.mandatory", "assets/symbol-mandatory.svg"), ("sym.prohibit", "assets/symbol-prohibit.svg")]


def pair(value: str, key: str) -> dict:
    return {f"{key}_html": escape(value), f"{key}_text": value}


def safety() -> list[dict]:
    signal = symbol_signal_component_spec(
        accessibility_label=T.rows["pict.h"]["text"],
        headers=[pair("表示", "content"), pair("意味", "content")],
        rows=[{"label": T(f"signal.{k}.l"), "show_icon": k in ("warn", "caut"), **pair(T(f"signal.{k}.m"), "meaning")}
              for k in ("warn", "caut", "expl", "hint")],
        source_ref="native-pdf/page-3/signal", language=LANGUAGE)
    meanings = [T(k) for k, _ in SYMBOLS]
    symbols = symbol_icon_component_spec(
        accessibility_label=T.rows["sym.h"]["text"],
        headers=[pair(v, "content") for v in ("記号", "意味", "記号", "意味")],
        panels=[[{"asset_index": i, "icon_alt": meanings[i], **pair(meanings[i], "meaning")} for i in rows]
                for rows in ((0, 1, 2, 3), (4, 5, 6, 7))],
        icon_refs=[ref for _, ref in SYMBOLS], source_ref="native-pdf/page-3/symbols", language=LANGUAGE)
    recycle_rows = []
    for index, prefix in enumerate(("weee", "battery")):
        keys = [f"{prefix}.b{i}" for i in (1, 2, 3)]
        values = [T(k) for k in keys]
        recycle_rows.append({"asset_index": index, "icon_alt": values[0], "meaning_text": "".join(values),
                             "meaning_html": "<br/>".join(escape(v) for v in values)})
    recycle = symbol_icon_component_spec(
        accessibility_label=T.rows["recycle.title"]["text"],
        headers=[pair(v, "content") for v in ("記号", "意味", "記号", "意味")],
        panels=[[recycle_rows[0]], [recycle_rows[1]]],
        icon_refs=["assets/symbol-weee.png", "assets/symbol-battery.png"],
        source_ref="native-pdf/page-4/recycling", language=LANGUAGE)
    warn = T.rows["w.h"]["text"]

    def item(label: str, variant: str, n: str, page: int, extra: list[dict] | None = None) -> dict:
        body = [bold(f"{n}.t"), *(extra or [])]
        if f"{n}.b" in T.rows:
            body.append(p(f"{n}.b"))
        return root(callout(label, body, variant=variant, language=LANGUAGE,
                            source_ref=f"native-pdf/page-{page}/{n}"))

    nodes = [chapter_heading("safety.h", "native-safety"), strong("safety.lead"),
             heading("pict.h"), para("pict.p1"), para("pict.p2"), component_flow_node(signal, root=True),
             heading("sym.h"), component_flow_node(symbols, root=True), component_flow_node(recycle, root=True),
             heading("w.h")]
    nodes += [item(warn, "warning", f"w{i}", 4) for i in range(1, 9)]
    warn2 = T("w2.h")
    nodes.append(root(callout(warn2, [
        bold("w9.t"), items([f"w9.l{i}" for i in range(1, 6)]), p("w9.b1"), p("w9.b2"),
        bold("w9.t2"), p("w9.b3"), p("w9.b4")], variant="warning", language=LANGUAGE,
        source_ref="native-pdf/page-5/w9")))
    nodes += [item(warn2, "warning", f"w{i}", 5) for i in (10, 11, 12)]
    caution = T.rows["c.h"]["text"]
    nodes += [heading("c.h"), item(caution, "caution", "c1", 5),
              item(caution, "caution", "c2", 5, [items(["c2.l1", "c2.l2", "c2.l3"])]),
              item(caution, "caution", "c3", 5), item(caution, "caution", "c4", 5)]
    return nodes


def precautions() -> list[dict]:
    return [chapter_heading("prec.h", "native-usage-precautions"),
            panel([p("prec.p1"), p("prec.p2"), p("prec.p3"), p("prec.p4")]),
            box("prec.caution.l", [p("prec.caution")], "caution", "native-pdf/page-6/caution"),
            heading("prec.s1.h"), para("prec.s1.p"), bullets([f"prec.s1.l{i}" for i in range(1, 5)]),
            heading("prec.s2.h"), bullets([f"prec.s2.l{i}" for i in range(1, 6)]),
            heading("prec.s3.h"), bullets(["prec.s3.l1", "prec.s3.l2"]),
            heading("prec.s4.h"), bullets(["prec.s4.l1", "prec.s4.l2", "prec.s4.l3"]),
            heading("prec.s5.h"),
            bullets(["prec.s5.l1", "prec.s5.l2", "prec.s5.l3"], {"prec.s5.l2": ["prec.s5.l2a", "prec.s5.l2b"]})]


def disclaimer() -> list[dict]:
    return [chapter_heading("disc.h", "native-disclaimer"), bullets([f"disc.l{i}" for i in range(1, 7)])]


def in_the_box() -> list[dict]:
    cards = []
    for index, (key, ref) in enumerate((("box.c1", "assets/inbox-unit.png"), ("box.c2", "assets/inbox-cable.png"),
                                        ("box.c3", "assets/inbox-manual.png")), 1):
        if T(f"box.k{index}") != str(index):  # printed card number, drawn by the shared card grid
            raise ValueError("in-the-box card numbering changed")
        cards.append({"image_ref": ref, "label": T(key), "alt": T.rows[key]["text"]})
    title = T.rows["box.h"]["text"]
    spec = inbox_component_spec(accessibility_label=title, cards=cards, tip_label="", tip_body="",
                                source_ref="native-pdf/page-8/inbox", language=LANGUAGE, require_tip=False)
    carrier = table([[node("table_cell", [node("image", source=c["image_ref"], alt=c["alt"]),
                                          node("paragraph", [text(c["label"])])], header=False) for c in cards]])
    return [chapter_heading("box.h", "native-in-the-box"), component_flow_node(spec, carrier_flow=(carrier,), root=True),
            para("box.n1"), para("box.n2"), para("box.n3"), strong("box.change")]


def overview() -> list[dict]:
    front = ["names.f.power", "names.f.car", "names.f.car.v", "names.f.dcbtn", "names.f.c140", "names.f.c140.v",
             "names.f.usba", "names.f.usba.v", "names.f.c30", "names.f.c30.v", "names.f.lcd", "names.f.ledbtn",
             "names.f.led", "names.f.ac1", "names.f.ac2", "names.f.acout", "names.f.acout.v"]
    return [chapter_heading("names.h", "native-product-overview"),
            heading("names.front"), figure("overview-front", 8, front),
            heading("names.left"), figure("overview-left", 9, ["names.l.dcx", "names.l.dcx.in", "names.l.dcx.out"]),
            heading("names.right"),
            figure("overview-right", 9, ["names.r.dcin", "names.r.dcin.pv", "names.r.dcin.car", "names.r.acin",
                                         "names.r.acin.v"])]


LCD_ICONS = ["01_wifi", "02_bluetooth", "03_quiet_charging_mode", "04_charging_plan", "05_self_powered_mode",
             "06_tou_mode", "07_ups", "08_ac_power_indicator", "09_output_voltage_and_frequency", "10_input_power",
             "11_remaining_charge_time", "12_ac_wall_charging_indicator", "13_car_charging_indicator",
             "14_solar_charging_indicator", "15_battery_saving_mode", "16_charging_power_limit",
             "17_battery_power_indicator", "18_low_battery_indicator", "19_remaining_battery_percentage",
             "20_discharge_timer", "21_connected_batteries", "22_energy_saving_mode",
             "23_high_temperature_indicator", "24_low_temperature_indicator", "25_fault_code", "26_output_power",
             "27_remaining_discharge_time"]
LCD_ROWS = [str(i) for i in range(1, 24)] + ["23b"] + [str(i) for i in range(24, 27)]


def lcd() -> list[dict]:
    rows, refs = [], []
    number = ""
    for index, (row, icon) in enumerate(zip(LCD_ROWS, LCD_ICONS, strict=True)):
        if f"lcd.r{row}.n" in T.rows:
            number = T(f"lcd.r{row}.n")  # 23b shares the printed number 23 of its merged cell
        name = T(f"lcd.r{row}.t")
        name_html, name_text = escape(name), name
        if f"lcd.r{row}.t2" in T.rows:
            sub = T(f"lcd.r{row}.t2")
            name_html, name_text = f"{name_html}<br/>{escape(sub)}", name + sub
        keys = sorted((k for k in T.rows if k.startswith(f"lcd.r{row}.b")), key=lambda k: int(k.rsplit("b", 1)[1]))
        bodies = [T.rows[k]["text"] for k in keys]
        rows.append({**pair(number, "number"), "name_html": name_html, "name_text": name_text,
                     "description_html": "<br/>".join(T.html(k) for k in keys),
                     "description_text": "".join(bodies), "icon_alt": name, "asset_index": index})
        refs.append(f"assets/lcd/{icon}.png")
    spec = lcd_icon_component_spec(accessibility_label=T.rows["lcd.h"]["text"], rows=rows, icon_refs=refs,
                                   source_ref="native-pdf/page-10-11/lcd-icons", language=LANGUAGE,
                                   icon_locale_policy="exact", numbered=True)
    return [chapter_heading("lcd.h", "native-lcd-display"),
            figure("lcd-map", 9, [f"lcd.map.{i}" for i in range(1, 27)], label=T.rows["lcd.h"]["text"]),
            component_flow_node(spec, root=True)]


def eco_table() -> dict:
    head = node("table_head", [node("table_row", [node("table_cell", [text(T(k))], header=True)
                                                  for k in ("eco.th1", "eco.th2", "eco.th3")])])
    rows = []
    for r in (1, 2):
        cells = [node("table_cell", [text(T(f"eco.r{r}.c1"))], header=False),
                 node("table_cell", [text(T(f"eco.r{r}.c2"))], header=False)]
        if r == 1:
            # The printed デフォルト設定 cell spans both output rows.
            cells.append(node("table_cell", [text(T("eco.default"))], header=False, row_span=2))
        rows.append(node("table_row", cells))
    return root(node("group", [node("table", [head, node("table_body", rows)],
                                    presentation={"html": {"attributes": {"class": "manual-table"}}})],
                     role="container",
                     presentation={"html": {"attributes": {"class": "table-wrapper docutils container"}}}))


def lcd_mode() -> dict:
    groups = []
    for state, prefix in (("mode.short", "mode.s"), ("mode.always", "mode.a")):
        actions = []
        state_text = T(state)
        for action in ("on", "off", "auto"):
            a, desc = T(f"{prefix}.{action}"), T(f"{prefix}.{action}.d")
            actions.append({**pair(a, "action"), **pair(desc, "description")})
        groups.append({**pair(state_text, "state"), "actions": actions})
    spec = lcd_mode_component_spec(accessibility_label=T.rows["mode.h"]["text"], groups=groups,
                                   artwork_ref="assets/lcd-mode.png", source_ref="native-pdf/page-15/lcd-mode",
                                   language=LANGUAGE)
    return component_flow_node(spec, root=True)


BUTTONS = {"主電源ボタン": "assets/button-power.svg", "AC 1出力ボタン": "assets/button-ac1.svg",
           "DC/USB出力ボタン": "assets/button-dc-usb.svg", "LEDライトボタン": "assets/button-light.png"}


def key_combinations() -> dict:
    headers = [T(k) for k in ("keys.th1", "keys.th2", "keys.th3")]
    rows, body = [], []
    for r in range(1, 5):
        names = [T(f"keys.r{r}.b1"), T(f"keys.r{r}.b2")]
        marking = T("keys.r4.b2art") if r == 4 else ""  # LIGHT is text-layer lettering inside the button art
        duration, operation, function = T(f"keys.r{r}.d"), T(f"keys.r{r}.op"), T(f"keys.r{r}.f")
        rows.append([f"{names[0]} ＋ {names[1]}", f"{duration} {operation}", function])

        def button(name: str, alt: str = "") -> dict:
            return node("inline_group", [node("image", source=BUTTONS[name], alt=alt),
                                         node("inline_group", [text(name)], presentation={
                                             "html": {"attributes": {"class": "hb-key-button-label"}}})],
                        presentation={"html": {"attributes": {"class": "hb-key-button"}}})

        pair_cell = node("group", [button(names[0]), node("inline_group", [text("＋")], presentation={
            "html": {"attributes": {"class": "hb-key-button-plus"}}}), button(names[1], marking)],
            role="container", presentation={"html": {"attributes": {"class": "hb-key-button-pair"}}})
        body.append(node("table_row", [
            node("table_cell", [pair_cell], header=False),
            node("table_cell", [node("inline_group", [text(duration)], presentation={
                "html": {"attributes": {"class": "hb-key-duration", "data-duration-icon": "clock"}}}),
                text(" " + operation)], header=False),
            node("table_cell", [text(function)], header=False)]))
    carrier = node("table", [node("table_head", [node("table_row", [node("table_cell", [text(h)], header=True)
                                                                     for h in headers])]),
                             node("table_body", body)],
                   presentation={"html": {"attributes": {"class": "hb-key-combination-table"}}})
    spec = key_combinations_component_spec(headers=headers, rows=rows, source_ref="native-pdf/page-15/key-combinations",
                                           language=LANGUAGE)
    return component_flow_node(spec, carrier_flow=(carrier,), root=True)


def auto_resume() -> dict:
    spec = auto_resume_component_spec(
        headers=[T("resume.th1"), T("resume.th2")],
        conditions=[[T(f"resume.y{i}") for i in (1, 2, 3)], [T(f"resume.n{i}") for i in (1, 2, 3, 4)]],
        source_ref="native-pdf/page-16/auto-resume", language=LANGUAGE)
    return component_flow_node(spec, root=True)


def usage() -> list[dict]:
    return [chapter_heading("use.h", "native-usage"),
            heading("use.power.h"),
            figure("power", 12, ["fig.power.on", "fig.power.on.i", "fig.power.off", "fig.power.off.i",
                                 "fig.power.3s", "fig.power.note"]),
            para("use.power.eco"),
            heading("use.ac.h"), para("use.ac.pre"),
            figure("ac-output", 12, ["fig.ac.on1", "fig.ac.on1.i", "fig.ac.off1", "fig.ac.off1.i",
                                     "fig.ac.on2", "fig.ac.on2.i", "fig.ac.off2", "fig.ac.off2.i"]),
            para("use.ac.p"),
            heading("use.freq.h"), panel([p("use.freq.default"), p("use.freq.auto"), p("use.freq.manual")]),
            figure("frequency", 13, ["fig.freq.50", "fig.freq.60"]),
            heading("use.usb.h"), para("use.usb.pre"),
            figure("dc-usb", 13, ["fig.usb.on", "fig.usb.on.i", "fig.usb.off", "fig.usb.off.i"]),
            box("use.usb.caution.l", [items(["use.usb.c1", "use.usb.c2", "use.usb.c3"])], "caution",
                "native-pdf/page-13/caution"),
            para("use.car.p1"), para("use.car.p2"),
            box("use.car.caution.l", [items(["use.car.c1", "use.car.c2", "use.car.c3"])], "caution",
                "native-pdf/page-14/caution"),
            heading("eco.h"), with_icon("eco.p1"), eco_table(), with_icon("eco.p2"), para("eco.p3"),
            figure("energy-saving", 14, ["fig.eco.ac1", "fig.eco.power", "fig.eco.3s", "fig.eco.onoff",
                                         "fig.eco.both"]),
            box("eco.note.l", [p("eco.note")], "note", "native-pdf/page-14/note"),
            heading("led.h"), para("led.p"),
            figure("led-light", 15, ["fig.led.light", "fig.led.1", "fig.led.s1", "fig.led.2", "fig.led.sos",
                                     "fig.led.s2", "fig.led.3", "fig.led.s3"]),
            heading("mode.h"), lcd_mode(), para("mode.app"),
            heading("keys.h"), key_combinations(),
            heading("resume.h"), para("resume.p"), auto_resume()]


def ups() -> list[dict]:
    return [chapter_heading("ups.h", "native-ups"), figure("ups", 16, ["fig.ups.note"]),
            panel([p("ups.p1"), p("ups.p2"), items(["ups.l1", "ups.l2", "ups.l3", "ups.l4"]), p("ups.p3"),
                   p("ups.p4"), p("ups.p5")])]


def connection() -> list[dict]:
    return [chapter_heading("conn.h", "native-connection"), heading("conn.bp.h"), para("conn.bp.p"),
            figure("expansion", 17, ["fig.exp.power", "fig.exp.bp", "fig.exp.gap"]),
            figure("expansion-accessories", 17, ["fig.acc.bp", "fig.acc.cable", "fig.acc.manual", "fig.acc.sold"]),
            box("conn.caution.l", [items([f"conn.c{i}" for i in range(1, 5)])], "caution",
                "native-pdf/page-17/caution")]


def charging() -> list[dict]:
    return [chapter_heading("chg.h", "native-charging"),
            strong("chg.green.h"), para("chg.green"),
            box("chg.c1.l", [items(["chg.c1.i1", "chg.c1.i2"])], "caution", "native-pdf/page-18/caution-1"),
            box("chg.c2.l", [items(["chg.c2.i1", "chg.c2.i2", "chg.c2.i3"])], "caution",
                "native-pdf/page-18/caution-2"),
            heading("chg.ac.h"), para("chg.ac.p"), figure("ac-charge", 18, ["fig.ac.caption"]),
            box("chg.c3.l", [p("chg.c3")], "caution", "native-pdf/page-18/caution-3"),
            strong("chg.emg.h"), para("chg.emg1"), para("chg.emg2"), para("chg.emg3"),
            heading("solar.h"), para("solar.p"),
            panel([p("solar.acc.h"), items(["solar.acc.l1", "solar.acc.l2"]), p("solar.acc.note")]),
            root(node("list", [node("list_item", [node("paragraph", T.inline(k))
                                                  for k in ("solar.two.l1", "solar.two.l2", "solar.two.l3")])],
                      ordered=False)),
            figure("solar-direct", 19, ["fig.solar2.caption"]),
            bullets(["solar.four.l1"], {"solar.four.l1": ["solar.four.s1", "solar.four.s2"]}),
            figure("solar-adapter", 20, ["fig.solar4.caption", "fig.solar4.adapter"]),
            box("solar.c.l", [p("solar.c.p1"), p("solar.c.p2"), p("solar.c.p3"),
                              items(["solar.c.i1", "solar.c.i2"])], "caution", "native-pdf/page-20/caution"),
            para("solar.brand"),
            heading("car.h"), strong("car.lead"), para("car.p"), bullets([f"car.l{i}" for i in range(1, 6)]),
            figure("car-charge", 21, ["fig.car.vehicle", "fig.car.caption"]),
            box("car.c.l", [items(["car.c1", "car.c2"])], "caution", "native-pdf/page-21/caution")]


def troubleshooting() -> list[dict]:
    rows = []
    for r in range(1, 10):
        codes = [k for k in (f"ts.r{r}.c", f"ts.r{r}.c1", f"ts.r{r}.c2") if k in T.rows]
        measures = sorted((k for k in T.rows if k.startswith(f"ts.r{r}.m")), key=lambda k: k[len(f"ts.r{r}.m"):])
        code_values = [T(k) for k in codes]
        rows.append({"code_html": "<br/>".join(escape(v) for v in code_values), "code_text": " ".join(code_values),
                     "measures_html": "<br/>".join(T.html(k) for k in measures),
                     "measures_text": "".join(T.rows[k]["text"] for k in measures)})
    spec = troubleshooting_component_spec(headers=[pair(T("ts.th1"), "content"), pair(T("ts.th2"), "content")],
                                          rows=rows, source_ref="native-pdf/page-22/errors", language=LANGUAGE)
    return [chapter_heading("ts.h", "native-troubleshooting"), para("ts.p1"), para("ts.p2"),
            component_flow_node(spec, root=True)]


def specifications() -> list[dict]:
    nodes = [chapter_heading("spec.h", "native-specifications")]
    for g in (1, 2, 3, 4):
        title = T(f"spec.g{g}")
        rows: list[tuple[str, str]] = []
        r = 1
        while f"spec.g{g}.r{r}.l" in T.rows:
            label = T(f"spec.g{g}.r{r}.l")
            values = [k for k in (f"spec.g{g}.r{r}.v", *(f"spec.g{g}.r{r}.v{i}" for i in (1, 2, 3))) if k in T.rows]
            for index, key in enumerate(values):
                # A further printed value line continues the same label (HB-TABLE-SPEC rowspan).
                rows.append((label if index == 0 else "", T(key)))
            r += 1
        spec = spec_table_component_spec(section_title=title, rows=rows,
                                         source_ref=f"native-pdf/page-23/spec-g{g}", language=LANGUAGE)
        nodes.append(component_flow_node(spec, carrier_flow=_spec_carrier(title, rows), root=True))
    return nodes + [para("spec.tm"), para("spec.fn1")]


def warranty() -> list[dict]:
    def section(index: int, title_key: str, blocks: list[dict]) -> list[dict]:
        # The shared card draws the body; its printed title pill is the heading before it.
        title = heading(title_key)
        spec = warranty_section_component_spec(title=T.rows[title_key]["text"], section_index=index, blocks=blocks,
                                               source_ref=f"native-pdf/warranty/{index}", language=LANGUAGE)
        return [title, component_flow_node(spec, root=True)]

    def wp(*keys: str, lead: bool = False) -> dict:
        texts = [T.rows[k]["text"] for k in keys]
        parts = [T.html(k) for k in keys]
        if lead:  # printed bold run-in title, the rest of the line regular
            parts[0] = f"<strong>{parts[0]}</strong>"
            html = parts[0] + "".join(parts[1:2]) + "".join("<br/>" + part for part in parts[2:])
        else:
            html = "<br/>".join(parts)
        return {"kind": "paragraph", "html": f"<p>{html}</p>", "text": "".join(texts)}

    def ul(*keys: str) -> dict:
        values = [T(k) for k in keys]
        return {"kind": "list", "items": values,
                "html": "<ul>" + "".join(f"<li>{escape(i)}</li>" for i in values) + "</ul>"}

    return [chapter_heading("war.h", "native-warranty"),
            panel([p("war.lead1"), p("war.lead2"), p("war.lead3")]),
            *section(1, "war.period.h", [ul("war.period1", "war.period2"), wp("war.period3"), wp("war.period4"),
                                        wp("war.period5"), wp("war.period.note")]),
            *section(2, "war.scope.h", [wp("war.scope1.t", "war.scope1.b"), wp("war.scope.note"),
                                       wp("war.scope2.t", "war.scope2.b")]),
            *section(3, "war.cond.h", [wp("war.cond.lead"), ul("war.cond.l1", "war.cond.l2", "war.cond.l3")]),
            *section(4, "war.excl.h", [wp("war.excl.lead", *(f"war.excl.l{i}" for i in range(1, 7)))]),
            *section(5, "war.proof.h", [wp("war.proof.lead"), ul("war.proof.l1", "war.proof.l2"),
                                       wp("war.proof.note")]),
            *section(6, "war.cont.h", [wp("war.cont1.t", "war.cont1.p", lead=True), ul("war.cont1.l1", "war.cont1.l2"),
                                      wp("war.cont2.t", "war.cont2.p", lead=True), ul("war.cont2.l1", "war.cont2.l2"),
                                      wp("war.cont3.t", "war.cont3.lead", lead=True),
                                      ul("war.cont3.l1", "war.cont3.l2", "war.cont3.l3"),
                                      wp("war.cont3.after"), wp("war.cont.note")]),
            panel([bold("war.disc.h"), *(p(f"war.disc{i}") for i in range(1, 6))]),
            panel([p("contact.web"), p("contact.mail"), p("contact.tel")])]


def app_manual() -> list[dict]:
    columns = [{"role": "store", "text": T("appm.s1.store")}, {"role": "qr", "text": T("appm.s1.qr")}]
    for column in columns:
        column["html"] = escape(column["text"])
    download = app_download_component_spec(
        accessibility_label="Jackery App", columns=columns, source_art_ref="assets/app-qr.png",
        store_art_ref="assets/app-store.png", qr_art_ref="assets/app-qr.png",
        source_ref="native-pdf/page-26/download", language=LANGUAGE)
    carrier = [node("image", source="assets/app-qr.png", alt="Jackery App"),
               *(node("paragraph", [text(c["text"])]) for c in columns)]
    before, after = T("appm.s21").split(" [+] ")
    plus = app_inline_control_component_spec(
        accessibility_label="+", paragraph_html=f"{escape(before)} <strong>+</strong> {escape(after)}",
        paragraph_text=f"{before} + {after}", source_ref="native-pdf/page-26/add-button", language=LANGUAGE,
        metadata={"visual_recovery": "pdf-vector-plus-control"})
    plus_carrier = node("paragraph", [text(before + " "), node("strong", [text("+")]), text(" " + after)])
    return [chapter_heading("appm.h", "native-app-manual"),
            heading("appm.s1.h"), component_flow_node(download, carrier_flow=carrier, root=True),
            heading("appm.s2.h"), component_flow_node(plus, carrier_flow=(plus_carrier,), root=True),
            para("appm.s22"),
            figure("app-add", 26, ["fig.app.c21", "fig.app.c22"]),
            figure("app-control", 26, ["fig.ctl.power", "fig.ctl.dc", "fig.ctl.ac2", "fig.ctl.ac1"]),
            para("appm.s23"),
            box("appm.note1.l", [p("appm.note1"), items(["appm.note1.l1", "appm.note1.l2"])], "note",
                "native-pdf/page-27/note-1"),
            para("appm.s24"),
            box("appm.note2.l", [p("appm.note2")], "note", "native-pdf/page-27/note-2"),
            para("appm.s25"),
            figure("app-results", 27, ["fig.app.c23", "fig.app.c24", "fig.app.c25", "fig.app.dev1", "fig.app.dev2"]),
            para("appm.shots"),
            box("appm.note3.l", [p("appm.note3")], "note", "native-pdf/page-27/note-3"),
            heading("appm.s3.h"), para("appm.s3"),
            heading("appm.s4.h"),
            heading("appm.s41.h", level=4), bullets(["appm.s41.l1", "appm.s41.l2"]),
            heading("appm.s42.h", level=4), bullets(["appm.s42.l1"]),
            heading("appm.s43.h", level=4), bullets(["appm.s43.l1"])]


CHAPTERS = (
    ("safety", "安全上のご注意", safety), ("usage_precautions", "使用上のご注意", precautions),
    ("disclaimer", "免責事項", disclaimer), ("in_the_box", "同梱品", in_the_box),
    ("product_overview", "各部の名称", overview), ("lcd_display", "液晶画面", lcd),
    ("usage", "使い方", usage), ("ups", "UPS 機能", ups), ("connection", "接続", connection),
    ("charging", "充電方法", charging), ("troubleshooting", "トラブルシューティング", troubleshooting),
    ("specifications", "主な仕様", specifications), ("warranty", "保証について", warranty),
    ("app_setup", "Jackeryアプリ ユーザーマニュアル", app_manual),
)


def build() -> dict:
    chapters = [{"id": cid, "title": title, "nodes": make()} for cid, title, make in CHAPTERS]
    missing = [k for k in T.rows if k not in T.used and k not in PENDING_SYMBOL_LINES]
    if missing:
        raise ValueError("Web transcription lines not bound: " + ", ".join(missing))
    if any(k in T.used for k in PENDING_SYMBOL_LINES):
        raise ValueError("a pending symbol line is bound; update PENDING_SYMBOL_LINES")
    return {"model": "JE-1000H", "region": "JP", "language": LANGUAGE,
            "title": "Jackery ポータブル電源 1000 Plus 取扱説明書",
            "source_sha256": SOURCE_SHA256, "chapters": chapters}


def main() -> None:
    content = build()
    path = PACKAGE / "source/ja/content.json"
    path.write_text(json.dumps(content, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"chapters": [c["id"] for c in content["chapters"]], "lines": len(T.used)}))


if __name__ == "__main__":
    main()
