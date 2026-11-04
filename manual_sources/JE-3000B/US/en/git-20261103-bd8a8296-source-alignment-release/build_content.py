"""Bind the reviewed JE-3000B US transcription to shared Web components.

Run from the repository root:

    python manual_sources/JE-3000B/US/en/git-20261028-bd8a8296/build_content.py

Every Web string comes from ``source/transcription.json`` by line id; this
module only decides which shared component carries each printed block, in
printed order. It writes ``source/en/content.json``, the frozen input that
``rebuild.py`` replays. The printed tables carry their own Buttons/Operation/
Function and Error Code/Name/Description headers, so no component chrome is
invented; ``source/differences.md`` lists every layout difference from the
print.
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
from tools.component_specs.manual_tables import lcd_icon_component_spec  # noqa: E402
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
CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲"
# Print-only chrome on a Web page: the 「US」 language badge above the preface.
PRINT_ONLY = {"pre.badge"}
# Printed run-in labels whose trailing colon the shared callout label slot drops.
CALLOUT_LABELS = {"safety.warn.label", "ground.warn.label", "op.warn.label", "danger.label"}


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
    """Shared grey text panel (web_manual.css ``.hb-text-panel``) for printed grey boxes, pills and bands."""
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
    """Printed box label and body; a printed trailing colon (WARNING:) is dropped from the shared label slot."""
    label = T(label_key)
    if label_key in CALLOUT_LABELS:
        if not label.endswith(":"):
            raise ValueError("callout label must end with its printed colon: " + label_key)
        label = label[:-1]
    return root(callout(label, body, variant=variant, language=LANGUAGE, source_ref=ref))


def item_list(keys: list[str]) -> dict:
    return node("list", [node("list_item", T.inline(k)) for k in keys], ordered=False)


def body_para(key: str) -> dict:
    return node("paragraph", T.inline(key))


def bold_para(key: str) -> dict:
    return node("paragraph", [node("strong", [text(T(key))])])


def pair(value: str, key: str) -> dict:
    return {f"{key}_html": escape(value), f"{key}_text": value}


def plain_table(header: list[dict], rows: list[list[dict]]) -> dict:
    """Declared plain table on the shared manual-table classes (shared_component_exceptions)."""
    parts = [node("table_head", [node("table_row", header)]), node("table_body", [node("table_row", r) for r in rows])]
    return root(node("group", [node("table", parts, presentation={"html": {"attributes": {"class": "manual-table"}}})],
                     role="container",
                     presentation={"html": {"attributes": {"class": "table-wrapper docutils container"}}}))


# --- chapters -------------------------------------------------------------

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
    # Printed under MOVING AND STORAGE INSTRUCTIONS, without a heading of its own. The
    # generic docutils container keeps that heading visible: the shared FCC style hides
    # the heading of a section whose direct child is the FCC figure.
    flow = component_flow_node(spec, carrier_flow=tuple(carrier))
    return root(node("group", [flow], role="container",
                     presentation={"html": {"attributes": {"class": "docutils container"}}}))


def safety() -> list[dict]:
    warning = callout_block("safety.warn.label", [
        bold_para("safety.warn.lead"), bold_para("safety.shock"),
        item_list([f"safety.w{i}" for i in range(1, 14)]),
    ], "warning", "native-pdf/page-4/warning")
    ground = callout_block("ground.warn.label", [bold_para("ground.warn")], "warning",
                           "native-pdf/page-4/grounding-warning")
    pack = callout_block("op.warn.label", [bold_para("op.warn")], "warning", "native-pdf/page-5/warning")
    danger = callout_block("danger.label", [bold_para("danger.l1"), bold_para("danger.l2")], "danger",
                           "native-pdf/page-5/danger")
    return [para("pre.p1"), para("pre.p2"), para("pre.p3"),
            chapter_heading("safety.h", "native-important-safety-information"),
            heading("safety.band"), warning,
            heading("ground.h"), para("ground.p"), ground,
            heading("maint.h"), para("maint.p"),
            heading("op.h"), bullets([f"op.i{i}" for i in range(1, 18)]), pack, danger,
            heading("move.h"), bullets([f"move.l{i}" for i in range(1, 7)]), fcc()]


def in_the_box() -> list[dict]:
    cards = [{"image_ref": ref, "label": T(key), "alt": T.rows[key]["text"]}
             for key, ref in (("box.c1", "assets/inbox-unit.png"), ("box.c2", "assets/inbox-cable.png"),
                              ("box.c3", "assets/inbox-manual.png"))]
    title = T.rows["box.h"]["text"]
    tip_label, tip_body = T("box.imp.l"), T("box.imp")
    spec = inbox_component_spec(accessibility_label=title, cards=cards, tip_label=tip_label, tip_body=tip_body,
                                source_ref="native-pdf/page-6/inbox", language=LANGUAGE)
    carrier = table([[node("table_cell", [node("image", source=c["image_ref"], alt=c["alt"]),
                                          node("paragraph", [text(c["label"])])], header=False) for c in cards]])
    tip = table([[node("table_cell", [text(tip_label)], header=False),
                  node("table_cell", [text(tip_body)], header=False)]])
    return [chapter_heading("box.h", "native-whats-in-the-box"),
            component_flow_node(spec, carrier_flow=(carrier, tip), root=True)]


def overview() -> list[dict]:
    front = ["names.f.power", "names.f.cig", "names.f.cig.v", "names.f.usbc", "names.f.usbc.v", "names.f.usba",
             "names.f.usba.v", "names.f.dcusb", "names.f.lcd", "names.f.ac1", "names.f.ac1.v", "names.f.ac2",
             "names.f.ac2.v", "names.f.acbtn"]
    right = ["names.r.reset", "names.r.acin", "names.r.acin.v", "names.r.dcin", "names.r.dcin.v1",
             "names.r.dcin.v2", "names.r.dcin.v3"]
    return [chapter_heading("names.h", "native-product-overview"),
            heading("names.front.h"), figure("assets/overview-front.png", "overview-front", 6, front),
            heading("names.right.h"), figure("assets/overview-right.png", "overview-right", 6, right)]


LCD_ROWS = [("1", "01-wifi"), ("2", "02-bluetooth"), ("3", "03-quiet-charging"), ("4a", "04a-battery-saving"),
            ("4b", "04b-self-powered"), ("5", "05-charging-plan"), ("6", "06-ac-power"), ("7", "07-input-power"),
            ("8", "08-remaining-charge-time"), ("9", "09-ac-wall-charging"), ("10", "10-car-charging"),
            ("11", "11-solar-charging"), ("12", "12-battery-power"), ("13", "13-low-battery"),
            ("14", "14-remaining-battery"), ("15", "15-fault-code"), ("16a", "16a-high-temperature"),
            ("16b", "16b-low-temperature"), ("17", "17-energy-saving"), ("18", "18-output-power"),
            ("19", "19-remaining-discharge-time")]


def lcd() -> list[dict]:
    values, refs = [], []
    for index, (number, slug) in enumerate(LCD_ROWS):
        name = T(f"lcd.r{number}.t")
        name_html, name_text = escape(name), name
        if f"lcd.r{number}.s" in T.rows:
            # The small "can be enabled / disabled in the Jackery APP" line printed under the name.
            sub = T(f"lcd.r{number}.s")
            name_html, name_text = f"{escape(name)}<br/>{escape(sub)}", f"{name} {sub}"
        keys = sorted((k for k in T.rows if k.startswith(f"lcd.r{number}.d")), key=lambda k: int(k.rsplit("d", 1)[1]))
        circled = CIRCLED[int(number.rstrip("ab")) - 1]
        values.append({**pair(circled, "number"), "name_html": name_html, "name_text": name_text,
                       "description_html": "<br/>".join(T.html(k) for k in keys),
                       "description_text": "".join(T.rows[k]["text"] for k in keys), "icon_alt": name,
                       "asset_index": index})
        refs.append(f"assets/lcd-{slug}.svg")
    spec = lcd_icon_component_spec(accessibility_label=T.rows["lcd.h"]["text"], rows=values, icon_refs=refs,
                                   source_ref="native-pdf/pages-7-8/lcd-icons", language=LANGUAGE,
                                   icon_locale_policy="exact")
    return [chapter_heading("lcd.h", "native-lcd-display"),
            figure("assets/lcd-map.png", "lcd-map", 7, [], label=T.rows["lcd.h"]["text"]),
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
                                   source_ref="native-pdf/page-10/lcd-mode", language=LANGUAGE)
    return component_flow_node(spec, root=True)


BUTTONS = {"Main Power Button": "assets/button-power.svg",
           "DC/USB Power Button": "assets/button-dc-usb.svg",
           "AC Power Button": "assets/button-ac.svg"}


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
    spec = key_combinations_component_spec(headers=headers, rows=rows, source_ref="native-pdf/page-11/keys",
                                           language=LANGUAGE)
    carrier = node("table", [node("table_head", [node("table_row", [
        node("table_cell", [text(h)], header=True) for h in headers])]), node("table_body", body)],
        presentation={"html": {"attributes": {"class": "hb-key-combination-table"}}})
    return [heading("keys.h"), component_flow_node(spec, carrier_flow=(carrier,), root=True)]


def operations() -> list[dict]:
    important = callout_block("ops.imp.l", [body_para("ops.imp")], "note", "native-pdf/page-9/important")
    return [chapter_heading("ops.h", "native-basic-operations"), important,
            heading("ops.power.h"),
            figure("assets/power.png", "power", 9,
                   ["fig.power.on", "fig.power.on.a", "fig.power.off", "fig.power.off.a", "fig.power.dur"]),
            panel_lines(["ops.power.box.t", "ops.power.box.b", "ops.power.box.n"]),
            heading("ops.ac.h"), panel_lines(["ops.ac.pre"]),
            figure("assets/ac-output.png", "ac-output", 9,
                   ["fig.ac.s1", "fig.ac.on", "fig.ac.on.a", "fig.ac.off", "fig.ac.off.a", "fig.ac.s2"]),
            panel([bold_para("ops.ac.reset.t"), body_para("ops.ac.reset")]),
            heading("ops.dc.h"), panel_lines(["ops.dc.pre"]),
            figure("assets/dc-usb.png", "dc-usb", 10, ["fig.dc.on", "fig.dc.on.a", "fig.dc.off", "fig.dc.off.a"]),
            heading("ops.lcd.h"), lcd_mode(), *key_combinations()]


def troubleshooting() -> list[dict]:
    def cell(children: list[dict], header: bool = False) -> dict:
        return node("table_cell", children, header=header)

    head = [cell([text(T(f"ts.th{i}"))], header=True) for i in (1, 2, 3)]
    rows = []
    for code in range(10):
        key = f"ts.f{code}"
        lines = sorted((k for k in T.rows if k.startswith(key + ".d")), key=lambda k: int(k.rsplit("d", 1)[1]))
        rows.append([cell([node("paragraph", [node("strong", [text(T(key + ".c"))])])]),
                     cell([node("paragraph", [node("strong", [text(T(key + ".n"))])])]),
                     cell([node("paragraph", [text(T(k))]) for k in lines])])
    return [chapter_heading("ts.h", "native-troubleshooting"), plain_table(head, rows)]


def ups() -> list[dict]:
    important = callout_block("ups.imp.l", [body_para("ups.i1"), body_para("ups.i2"), body_para("ups.i3")], "note",
                              "native-pdf/page-12/important")
    return [chapter_heading("ups.h", "native-ups"), para("ups.p1"), para("ups.p2"), para("ups.p3"),
            panel_lines(["ups.pre"]),
            figure("assets/ups.png", "ups", 12, [], label=T.rows["ups.h"]["text"]),
            panel_lines(["ups.bubble"]), important]


def charging() -> list[dict]:
    note = callout_block("chg.note.l", [body_para("chg.n1"), body_para("chg.n2"), body_para("chg.n3")], "note",
                         "native-pdf/page-13/note")
    solar = callout_block("chg.solar.imp.l", [body_para("chg.solar.imp")], "note",
                          "native-pdf/page-14/important-solar")
    car = callout_block("chg.car.imp.l", [body_para(f"chg.car.c{i}") for i in range(1, 5)], "note",
                        "native-pdf/page-14/important-car")
    return [chapter_heading("chg.h", "native-charging"), para("chg.green"), para("chg.green2"),
            strong("chg.first"), note,
            heading("chg.ac.h"),
            figure("assets/ac-charge.png", "ac-charge", 13, [], label=T.rows["chg.ac.h"]["text"]),
            para("chg.ac.cap"),
            heading("chg.solar.h"), para("chg.solar.p"),
            figure("assets/solar-two.png", "solar-two", 13, ["fig.solar1.cap"]),
            figure("assets/solar-connector.png", "solar-connector", 14, ["fig.solar2.cap"]),
            solar,
            heading("chg.car.h"), para("chg.car.p"), panel_lines(["chg.car.note"]),
            figure("assets/car-charge.png", "car-charge", 14, ["fig.car.vehicle"]),
            car]


def warranty() -> list[dict]:
    def section(index: int, title_key: str, blocks: list[dict]) -> list[dict]:
        # The shared card draws the body; its printed title pill is the heading before it.
        title = heading(title_key)
        spec = warranty_section_component_spec(title=T.rows[title_key]["text"], section_index=index, blocks=blocks,
                                               source_ref=f"native-pdf/warranty/{index}", language=LANGUAGE)
        return [title, component_flow_node(spec, root=True)]

    def p(key: str) -> dict:
        return {"kind": "paragraph", "html": f"<p>{T.html(key)}</p>", "text": T.rows[key]["text"]}

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
            *section(4, "war.exc.h", [p("war.exc.lead"), p("war.exc.l1"), p("war.exc.l2"), p("war.exc.l3"),
                                      p("war.exc.l4")]),
            *section(5, "war.int.h", [p("war.int.p")])]


def app_setup() -> list[dict]:
    columns = [{"role": "store", "text": T("app.s1.store")}, {"role": "qr", "text": T("app.s1.qr")}]
    for column in columns:
        column["html"] = escape(column["text"])
    download = app_download_component_spec(
        accessibility_label="Jackery App", columns=columns, source_art_ref="assets/app-qr.png",
        store_art_ref="assets/app-store.png", qr_art_ref="assets/app-qr.png",
        source_ref="native-pdf/page-16/download", language=LANGUAGE)
    carrier = [node("image", source="assets/app-qr.png", alt="Jackery App"),
               *(node("paragraph", [text(c["text"])]) for c in columns)]
    before, after = T("app.s21").split(" [+] ")
    plus = app_inline_control_component_spec(
        accessibility_label="+", paragraph_html=f"{escape(before)} <strong>+</strong> {escape(after)}",
        paragraph_text=f"{before} + {after}", source_ref="native-pdf/page-16/add-button", language=LANGUAGE,
        metadata={"visual_recovery": "outlined-pdf-vector-plus-control"})
    plus_carrier = node("paragraph", [text(before + " "), node("strong", [text("+")]), text(" " + after)])
    rem1 = callout_block("app.rem1.l", [body_para("app.rem1")], "note", "native-pdf/page-16/remarks")
    rem2 = callout_block("app.rem2.l", [body_para("app.rem2")], "note", "native-pdf/page-17/remarks-bound")
    rem3 = callout_block("app.rem3.l", [body_para("app.rem3")], "note", "native-pdf/page-17/remarks-band")
    return [chapter_heading("app.h", "native-app-setup"),
            heading("app.s1.h"), component_flow_node(download, carrier_flow=carrier, root=True),
            heading("app.s2.h"), component_flow_node(plus, carrier_flow=(plus_carrier,), root=True),
            para("app.s22"),
            figure("assets/app-add.png", "app-add", 16, ["fig.app.c21", "fig.app.c22"]),
            figure("assets/app-control.png", "app-control", 16, ["fig.ctl.power", "fig.ctl.dc", "fig.ctl.ac"]),
            rem1, para("app.s23"), rem2, bullets(["app.rem2.l1", "app.rem2.l2"]),
            para("app.s24"), rem3, para("app.s25"),
            figure("assets/app-results.png", "app-results", 17, ["fig.app.c23", "fig.app.c24", "fig.app.c25"]),
            para("app.shots"),
            heading("app.s3.h"), para("app.s3"),
            heading("app.s4.h"),
            heading("app.s41.h", level=4), bullets(["app.s41.l1", "app.s41.l2"]),
            heading("app.s42.h", level=4), bullets(["app.s42.l1", "app.s42.l2"]),
            heading("app.s43.h", level=4), bullets(["app.s43"])]


SPEC_GROUPS = (
    ("spec.gen.h", [(f"spec.g{i}.l", [f"spec.g{i}.v"]) for i in range(1, 8)]),
    ("spec.in.h", [("spec.i1.l", ["spec.i1.v"]), ("spec.i2.l", ["spec.i2.v"]),
                   ("spec.i3.l", ["spec.i3.v1", "spec.i3.v2", "spec.i3.v3"])]),
    ("spec.out.h", [(f"spec.o{i}.l", [f"spec.o{i}.v"]) for i in range(1, 7)]),
    ("spec.env.h", [("spec.e1.l", ["spec.e1.v"]), ("spec.e2.l", ["spec.e2.v1"]), (None, ["spec.e2.v2"])]),
)


def specifications() -> list[dict]:
    # The printed chapter band carries the product name and model; SPECIFICATIONS is the heading under it.
    flows = [chapter_heading("spec.h", "native-specifications"),
             panel_lines(["spec.band.name", "spec.band.model"], bold=True)]
    for index, (title_key, groups) in enumerate(SPEC_GROUPS, 1):
        title = T(title_key)
        # One printed cell is one value; lines printed inside one cell stay together.
        rows = [(T(label) if label else "", "\n".join(T(k) for k in values)) for label, values in groups]
        spec = spec_table_component_spec(section_title=title, rows=rows,
                                         source_ref=f"native-pdf/page-18/spec-{index}", language=LANGUAGE)
        flows.append(component_flow_node(spec, carrier_flow=_spec_carrier(title, rows), root=True))
    return [*flows, para("spec.tm")]


CHAPTERS = (
    ("safety", "IMPORTANT SAFETY INFORMATION", safety),
    ("in_the_box", "WHAT'S IN THE BOX", in_the_box),
    ("product_overview", "PRODUCT OVERVIEW", overview),
    ("lcd_display", "LCD DISPLAY", lcd),
    ("operations", "BASIC OPERATIONS", operations),
    ("troubleshooting", "TROUBLESHOOTING", troubleshooting),
    ("ups", "UPS", ups),
    ("charging", "CHARGING", charging),
    ("warranty", "WARRANTY", warranty),
    ("app_setup", "APP SETUP", app_setup),
    ("specifications", "SPECIFICATIONS", specifications),
)


def build() -> dict:
    chapters = [{"id": cid, "title": title, "nodes": make()} for cid, title, make in CHAPTERS]
    missing = [k for k in T.rows if k not in T.used]
    if missing:
        raise ValueError("Web transcription lines not bound: " + ", ".join(missing))
    return {"model": "JE-3000B", "region": "US", "language": LANGUAGE,
            "title": "Jackery Explorer 3000 User Manual",
            "source_sha256": "bd8a82962865ae64cd52e9c6ebf9a20d8495652773ba09806d1911cb0f360294",
            "chapters": chapters}


def main() -> None:
    content = build()
    path = PACKAGE / "source/en/content.json"
    path.write_text(json.dumps(content, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"chapters": [c["id"] for c in content["chapters"]], "lines": len(T.used)}))


if __name__ == "__main__":
    main()
