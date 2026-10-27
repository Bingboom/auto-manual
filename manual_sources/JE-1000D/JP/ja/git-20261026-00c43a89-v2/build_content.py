"""Bind the reviewed JE-1000D JP transcription to shared Web components.

Run from the repository root:

    python manual_sources/JE-1000D/JP/ja/git-20261026-00c43a89-v2/build_content.py

Every Web string comes from ``source/transcription.json`` by line id; this
module only decides which shared component carries each printed block, in
printed order. It writes ``source/ja/content.json``, the frozen input that
``rebuild.py`` replays. Component chrome that the shared components require
(signal/symbol table headers) follows the JE-1500D JP V2 edition and is listed
in ``source/differences.md``.
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

from tools.component_specs.inbox import inbox_component_spec  # noqa: E402
from tools.component_specs.app import app_download_component_spec, app_inline_control_component_spec  # noqa: E402
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

LANGUAGE = "ja"
CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲"


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


def heading(key: str, level: int = 3, anchor: str | None = None) -> dict:
    value = T(key)
    return root(node("heading", [text(value)], level=level, **({"anchor": anchor} if anchor else {})))


def chapter_heading(key: str, anchor: str) -> dict:
    # The print letter-spaces chapter titles; the characters are unchanged.
    return heading(key, level=2, anchor=anchor)


def bullets(keys: list[str]) -> dict:
    return root(node("list", [node("list_item", [node("paragraph", T.inline(k))]) for k in keys], ordered=False))


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


def callout_block(label_key: str, item_keys: list[str], variant: str, ref: str) -> dict:
    label = T(label_key)
    body = [node("list", [node("list_item", [text(T(k))]) for k in item_keys], ordered=False)]
    return root(callout(label, body, variant=variant, language=LANGUAGE, source_ref=ref))


def safety_item(variant: str, label: str, title_key: str, body_keys: list[str], ref: str,
                list_keys: tuple[list[str], ...] = ()) -> dict:
    body = [node("paragraph", [node("strong", [text(T(title_key))])])]
    for keys in list_keys:
        body.append(node("list", [node("list_item", [text(T(k))]) for k in keys], ordered=False))
    body += [node("paragraph", [text(T(k))]) for k in body_keys]
    return root(callout(label, body, variant=variant, language=LANGUAGE, source_ref=ref))


def plain_table(header_keys: list[str], rows: list[list[list[dict]]], css: str = "manual-table") -> dict:
    head = node("table_head", [node("table_row", [node("table_cell", [text(T(k))], header=True)
                                                  for k in header_keys])]) if header_keys else None
    body = node("table_body", [node("table_row", [node("table_cell", cell, header=False) for cell in row])
                               for row in rows])
    return root(node("group", [node("table", [head, body] if head else [body],
                                    presentation={"html": {"attributes": {"class": css}}})],
                     role="container",
                     presentation={"html": {"attributes": {"class": "table-wrapper docutils container"}}}))


def icon(ref: str, alt: str) -> dict:
    return node("image", source=ref, alt=alt)


def with_icon(key: str, ref: str) -> list[dict]:
    """A printed cell whose bracketed [88H] mark is the LCD glyph itself."""
    before, after = T(key).split("[88H]")
    return [node("paragraph", [text(before), icon(ref, "88H"), text(after)])]


# --- chapters -------------------------------------------------------------

def specifications() -> list[dict]:
    rows = []
    for index in range(1, 17):
        label = T(f"spec.r{index}.l")
        keys = [k for k in T.rows if k.startswith(f"spec.r{index}.v")]
        rows.append((label, "\n".join(T(k) for k in keys)))
    title = T("spec.title")
    spec = spec_table_component_spec(section_title=title, rows=rows, source_ref="native-pdf/page-3/spec",
                                     language=LANGUAGE)
    from tools.web.frozen_ai_table_components import _spec_carrier
    recycle = plain_table([], [[
        [icon("assets/recycle-li-ion.svg", T("recycle.glyph"))],
        [node("paragraph", [node("strong", [text(T("recycle.title"))])]),
         *(node("paragraph", [text(T(k))]) for k in ("recycle.b1", "recycle.b2", "recycle.b3"))],
    ]])
    return [chapter_heading("spec.h", "native-specifications"),
            component_flow_node(spec, carrier_flow=_spec_carrier(title, rows), root=True),
            para("spec.tm"), para("spec.fn1"), root(node("paragraph", [node("strong", [text(T("spec.change"))])])),
            recycle]


def overview() -> list[dict]:
    keys = ["names.f.lcd", "names.f.power", "names.f.ledbtn", "names.f.car", "names.f.led", "names.f.usbc1",
            "names.f.usbc2", "names.f.acout", "names.f.usba", "names.f.acbtn", "names.f.dcbtn",
            "names.r.acin", "names.r.dcin", "names.r.cap"]
    return [chapter_heading("names.h", "native-product-overview"),
            figure("assets/overview.png", "overview", 4, keys)]


LCD_LEGEND = [f"lcd.n{i}" for i in range(1, 20)]


def lcd_rows(rows: list[tuple[str, list[str], str]], ref: str) -> dict:
    values, refs = [], []
    for index, (title_key, body_keys, asset) in enumerate(rows):
        name = T(title_key)
        bodies = [T(k) for k in body_keys]
        values.append({"name_html": escape(name), "name_text": name,
                       "description_html": "<br/>".join(escape(b) for b in bodies),
                       "description_text": "".join(bodies), "icon_alt": name, "asset_index": index})
        refs.append(asset)
    spec = lcd_icon_component_spec(accessibility_label=values[0]["name_text"], rows=values, icon_refs=refs,
                                   source_ref=ref, language=LANGUAGE, icon_locale_policy="exact", numbered=False)
    return component_flow_node(spec, root=True)


def lcd() -> list[dict]:
    legend = reference_table_component_spec(
        variant="lcd-descriptions", label=T.rows["lcd.h"]["text"], headers=[],
        rows=[[{"html": CIRCLED[i], "text": CIRCLED[i]}, {"html": escape(T(k)), "text": T.rows[k]["text"]}]
              for i, k in enumerate(LCD_LEGEND)],
        source_ref="native-pdf/page-5/lcd-legend", language=LANGUAGE)
    energy = "assets/lcd-energy-saving.svg"
    head = node("table_head", [node("table_row", [
        *(node("table_cell", [text(T(k))], header=True) for k in ("eco.th1", "eco.th2", "eco.th3")),
        node("table_cell", with_icon("eco.th4", energy), header=True)])])
    body = node("table_body", [node("table_row", [
        node("table_cell", [text(T(f"eco.r{r}.c1"))], header=False),
        node("table_cell", [text(T(f"eco.r{r}.c2"))], header=False),
        node("table_cell", [text(T(f"eco.r{r}.c3"))], header=False),
        node("table_cell", with_icon(f"eco.r{r}.c4", energy), header=False)]) for r in (1, 2, 3)])
    # Shared table wrapper: the four columns scroll inside the component on phones.
    eco = root(node("group", [node("table", [head, body],
                                   presentation={"html": {"attributes": {"class": "manual-table"}}})],
                    role="container",
                    presentation={"html": {"attributes": {"class": "table-wrapper docutils container"}}}))
    return [chapter_heading("lcd.h", "native-lcd-display"),
            figure("assets/lcd-map.png", "lcd-map", 4, [], label=T.rows["lcd.h"]["text"]),
            component_flow_node(legend, root=True),
            lcd_rows([("lcd.d10.t", ["lcd.d10.b"], "assets/shared-lcd/17_Battery_Power_Indicator_VLufb9exvoVLfgxz47pcfnRGnaf.png"),
                      ("lcd.d11.t", ["lcd.d11.b"], "assets/lcd-low-battery.svg"),
                      ("lcd.d16.t", ["lcd.d16.b"], energy)], "native-pdf/page-5/lcd-icons"),
            eco, para("eco.off"), para("eco.on"), para("freq.h"), para("freq.auto"), para("freq.manual"),
            lcd_rows([("lcd.d13.t", ["lcd.d13.b1", "lcd.d13.b2", "lcd.d13.b3", "lcd.d13.b4"],
                       "assets/shared-lcd/25_Fault_code_LaTmb4IQYo3vwvxMqQNcC2RgnIf.png"),
                      ("lcd.d14.t", ["lcd.d14.b"], "assets/lcd-high-temperature.svg"),
                      ("lcd.d15.t", ["lcd.d15.b"], "assets/lcd-low-temperature.svg"),
                      ("lcd.d3.t", ["lcd.d3.b"], "assets/lcd-quiet-charging.svg"),
                      ("lcd.d4.t", ["lcd.d4.b"], "assets/lcd-battery-saving.svg")], "native-pdf/page-6/lcd-icons")]


def usage() -> list[dict]:
    return [chapter_heading("use.h", "native-usage"), heading("use.h2"),
            *(para(k) for k in ("use.power", "use.eco", "use.eco1", "use.eco2", "use.ac")),
            root(node("paragraph", [node("strong", [text(T("use.usb.h"))])])),
            *(para(k) for k in ("use.usb", "use.display", "use.display.note", "use.ups", "use.ups2",
                                "use.led", "use.led2"))]


def app_connection() -> list[dict]:
    return [chapter_heading("app.h", "native-app-connection"), para("app.p")]


def charging() -> list[dict]:
    strong = lambda key: root(node("paragraph", [node("strong", [text(T(key))])]))  # noqa: E731
    return [chapter_heading("chg.h", "native-charging"),
            para("chg.green.h"), para("chg.green"), strong("chg.note.h"), para("chg.note1"), para("chg.note2"),
            callout_block("chg.box.label", ["chg.box.i1", "chg.box.i2", "chg.box.i3"], "caution",
                          "native-pdf/page-7/caution"),
            heading("chg.ac.h"), para("chg.ac.lead"), para("chg.ac.emg"), para("chg.ac.emg2"),
            para("chg.ac.note.h"), para("chg.ac.note"),
            figure("assets/ac-charge.png", "ac-charge", 8, ["fig.ac.cable", "fig.ac.unit"]),
            para("chg.ac.outlet"),
            heading("chg.solar.h"), para("chg.solar"), para("chg.solar.note.h"), para("chg.solar.note"),
            para("chg.solar.ex"), bullets(["chg.solar.ex1", "chg.solar.ex2"]),
            figure("assets/solar-direct.png", "solar-direct", 8, ["fig.solar1.unit"]),
            figure("assets/solar-adapter.png", "solar-adapter", 8, ["fig.solar2.unit"]),
            heading("chg.car.h"), para("chg.car"),
            figure("assets/car-charge.png", "car-charge", 9, ["fig.car.unit", "fig.car.note"]),
            heading("chg.safe.h"), para("chg.safe1"), para("chg.safe2"), para("chg.safe3")]


SYMBOLS = [("sym.unplug", "assets/symbol-01.svg"), ("sym.disassemble", "assets/symbol-02.svg"),
           ("sym.wethand", "assets/symbol-03.svg"), ("sym.mandatory", "assets/symbol-04.svg"),
           ("sym.wet", "assets/symbol-05.svg"), ("sym.prohibit", "assets/symbol-06.svg")]


def safety() -> list[dict]:
    def pair(value: str, key: str) -> dict:
        return {f"{key}_html": escape(value), f"{key}_text": value}
    signal = symbol_signal_component_spec(
        accessibility_label=T.rows["safety.pict.h"]["text"],
        headers=[pair("表示", "content"), pair("意味", "content")],
        rows=[{"label": T(f"signal.{k}.l"), "show_icon": True, **pair(T(f"signal.{k}.m"), "meaning")}
              for k in ("warn", "caut")],
        source_ref="native-pdf/page-9/signal", language=LANGUAGE)
    meanings = [T(k) for k, _ in SYMBOLS]
    symbols = symbol_icon_component_spec(
        accessibility_label=T.rows["symbols.h"]["text"],
        headers=[pair(v, "content") for v in ("記号", "意味", "記号", "意味")],
        panels=[[{"asset_index": i, "icon_alt": meanings[i], **pair(meanings[i], "meaning")} for i in rows]
                for rows in ((0, 1, 2), (3, 4, 5))],
        icon_refs=[ref for _, ref in SYMBOLS], source_ref="native-pdf/page-9/symbols", language=LANGUAGE)
    w, c = "warning", "caution"
    t1 = [T(f"w1.i1.l{i}") for i in range(1, 6)]
    first = root(callout(T("w1.band"), [
        node("paragraph", [node("strong", [text(T("w1.i1.t"))])]),
        node("list", [node("list_item", [text(v)]) for v in t1], ordered=False),
        node("paragraph", [text(T("w1.i1.b1"))]), node("paragraph", [text(T("w1.i1.b2"))]),
        node("paragraph", [node("strong", [text(T("w1.i1.t2"))])]),
        node("paragraph", [text(T("w1.i1.b3"))]), node("paragraph", [text(T("w1.i1.b4"))]),
    ], variant=w, language=LANGUAGE, source_ref="native-pdf/page-10/warning-1"))
    w2 = T("w2.band")
    c1 = T("c1.band")
    return [chapter_heading("safety.h", "native-safety"),
            root(node("paragraph", [node("strong", [text(T("safety.lead"))])])),
            heading("safety.pict.h"), para("safety.pict1"), para("safety.pict2"),
            component_flow_node(signal, root=True),
            heading("symbols.h"), component_flow_node(symbols, root=True),
            first,
            safety_item(w, "警告", "w1.i2.t", ["w1.i2.b"], "native-pdf/page-10/warning-2"),
            safety_item(w, "警告", "w1.i3.t", ["w1.i3.b"], "native-pdf/page-10/warning-3"),
            safety_item(w, "警告", "w1.i4.t", [], "native-pdf/page-10/warning-4"),
            *(safety_item(w, w2, f"w2.i{i}.t", [f"w2.i{i}.b"], f"native-pdf/page-10/warning-{i + 4}")
              for i in range(1, 9)),
            safety_item(c, c1, "c1.i1.t", ["c1.i1.b"], "native-pdf/page-11/caution-1"),
            safety_item(c, c1, "c1.i2.t", [], "native-pdf/page-11/caution-2",
                        list_keys=(["c1.i2.l1", "c1.i2.l2", "c1.i2.l3"],)),
            safety_item(c, c1, "c1.i3.t", ["c1.i3.b"], "native-pdf/page-11/caution-3"),
            safety_item(c, c1, "c1.i4.t", [], "native-pdf/page-11/caution-4")]


def precautions() -> list[dict]:
    items = [node("list_item", [node("paragraph", [text(T(f"prec.l{i}"))])]) for i in (1, 2)]
    items += [node("list_item", [node("paragraph", [text(T(f"prec.l{i}"))])]) for i in range(3, 13)]
    items.append(node("list_item", [node("paragraph", [text(T("prec.l13.t"))]),
                                    node("paragraph", [text(T("prec.l13.b"))])]))
    items.append(node("list_item", [node("paragraph", [text(T(k))]) for k in
                                    ("prec.l14.t", "prec.l14.b1", "prec.l14.b2", "prec.l14.b3")]))
    items.append(node("list_item", [node("paragraph", [text(T("prec.l15"))])]))
    return [chapter_heading("prec.h", "native-usage-precautions"),
            *(para(f"prec.p{i}") for i in range(1, 6)),
            root(node("list", items, ordered=False))]


def in_the_box() -> list[dict]:
    cards = [{"image_ref": ref, "label": T(key), "alt": T.rows[key]["text"]}
             for key, ref in (("box.c1", "assets/inbox-unit.png"), ("box.c2", "assets/inbox-cable.svg"),
                              ("box.c3", "assets/inbox-manual.png"))]
    title = T.rows["box.h"]["text"]
    spec = inbox_component_spec(accessibility_label=title, cards=cards, tip_label="", tip_body="",
                                source_ref="native-pdf/page-13/inbox", language=LANGUAGE, require_tip=False)
    carrier = table([[node("table_cell", [node("image", source=c["image_ref"], alt=c["alt"]),
                                          node("paragraph", [text(c["label"])])], header=False) for c in cards]])
    strong = lambda key: root(node("paragraph", [node("strong", [text(T(key))])]))  # noqa: E731
    return [chapter_heading("box.h", "native-in-the-box"), component_flow_node(spec, carrier_flow=(carrier,), root=True),
            strong("box.n1"), strong("box.n2"), strong("box.n3")]


def disclaimer() -> list[dict]:
    items = [node("list_item", [node("paragraph", [text(T("disc.l1"))])]),
             node("list_item", [node("paragraph", [text(T("disc.l2a"))]), node("paragraph", [text(T("disc.l2b"))])]),
             *(node("list_item", [node("paragraph", [text(T(f"disc.l{i}"))])]) for i in range(3, 7))]
    return [chapter_heading("disc.h", "native-disclaimer"), root(node("list", items, ordered=False))]


def app_manual() -> list[dict]:
    columns = [{"role": "store", "text": T("appm.s1.store")}, {"role": "qr", "text": T("appm.s1.qr")}]
    for column in columns:
        column["html"] = escape(column["text"])
    download = app_download_component_spec(
        accessibility_label="Jackery App", columns=columns, source_art_ref="assets/app-qr.png",
        store_art_ref="assets/app-store.png", qr_art_ref="assets/app-qr.png",
        source_ref="native-pdf/page-14/download", language=LANGUAGE)
    carrier = [node("image", source="assets/app-qr.png", alt="Jackery App"),
               *(node("paragraph", [text(c["text"])]) for c in columns)]
    before, after = T("appm.s21").split(" [+] ")
    plus = app_inline_control_component_spec(
        accessibility_label="+", paragraph_html=f"{escape(before)} <strong>+</strong> {escape(after)}",
        paragraph_text=f"{before} + {after}", source_ref="native-pdf/page-14/add-button", language=LANGUAGE,
        metadata={"visual_recovery": "outlined-pdf-vector-plus-control"})
    plus_carrier = node("paragraph", [text(before + " "), node("strong", [text("+")]), text(" " + after)])
    note = lambda key, ref: root(callout(  # noqa: E731
        T.rows[key]["text"].split("：", 1)[0],
        [node("paragraph", [text(T(key).split("：", 1)[1])])], variant="note", language=LANGUAGE, source_ref=ref))
    note2_label, note2_body = T.rows["appm.note2"]["text"].split("：", 1)
    T("appm.note2")
    note2 = root(callout(note2_label, [
        node("paragraph", [text(note2_body)]),
        node("list", [node("list_item", [text(T(k))]) for k in ("appm.note2.l1", "appm.note2.l2")], ordered=False),
    ], variant="note", language=LANGUAGE, source_ref="native-pdf/page-14/note-2"))
    return [chapter_heading("appm.h", "native-app-manual"),
            heading("appm.s1.h"), component_flow_node(download, carrier_flow=carrier, root=True),
            heading("appm.s2.h"), component_flow_node(plus, carrier_flow=(plus_carrier,), root=True),
            para("appm.s22"),
            figure("assets/app-add.png", "app-add", 14, ["fig.app.c21", "fig.app.c22"]),
            note("appm.note1", "native-pdf/page-14/note-1"),
            figure("assets/app-control.png", "app-control", 14, ["fig.ctl.power", "fig.ctl.dc", "fig.ctl.ac"]),
            para("appm.s23"), note2, para("appm.s24"), note("appm.note3", "native-pdf/page-15/note-3"),
            para("appm.s25"),
            figure("assets/app-results.png", "app-results", 15, ["fig.app.c23", "fig.app.c24", "fig.app.c25"]),
            para("appm.shots"),
            heading("appm.s3.h"), para("appm.s3"),
            heading("appm.s4.h"),
            heading("appm.s41.h", level=4), bullets(["appm.s41.l1", "appm.s41.l2"]),
            heading("appm.s42.h", level=4), bullets(["appm.s42.l1", "appm.s42.l2"]),
            heading("appm.s43.h", level=4), bullets(["appm.s43.l1"])]


def warranty() -> list[dict]:
    def section(index: int, title_key: str, blocks: list[dict]) -> list[dict]:
        # The shared card draws the body; its printed title pill is the heading before it.
        title = heading(title_key)
        spec = warranty_section_component_spec(title=T.rows[title_key]["text"], section_index=index, blocks=blocks,
                                               source_ref=f"native-pdf/warranty/{index}", language=LANGUAGE)
        return [title, component_flow_node(spec, root=True)]

    def p(*keys: str) -> dict:
        texts = [T.rows[k]["text"] for k in keys]
        html = "<br/>".join(T.html(k) for k in keys)
        return {"kind": "paragraph", "html": f"<p>{html}</p>", "text": "".join(texts)}

    def ul(*keys: str) -> dict:
        items = [T(k) for k in keys]
        return {"kind": "list", "items": items,
                "html": "<ul>" + "".join(f"<li>{escape(i)}</li>" for i in items) + "</ul>"}

    return [chapter_heading("war.h", "native-warranty"),
            panel([node("paragraph", [text(T(k))]) for k in ("war.lead1", "war.lead2", "war.lead3")]),
            *section(1, "war.period.h", [p("war.period1"), p("war.period2"), p("war.period.note")]),
            *section(2, "war.scope.h", [p("war.scope1.t", "war.scope1.b"), p("war.scope.note"),
                                       p("war.scope2.t", "war.scope2.b")]),
            *section(3, "war.cond.h", [p("war.cond.lead"), ul("war.cond.l1", "war.cond.l2", "war.cond.l3")]),
            *section(4, "war.excl.h", [p("war.excl.lead", *(f"war.excl.l{i}" for i in range(1, 7)))]),
            *section(5, "war.proof.h", [p("war.proof.lead"), ul("war.proof.l1", "war.proof.l2"),
                                       p("war.proof.note")]),
            *section(6, "war.cont.h", [p("war.cont1.t"), ul("war.cont1.l1", "war.cont1.l2"),
                                      p("war.cont2.t"), ul("war.cont2.l1", "war.cont2.l2"),
                                      p("war.cont3.t", "war.cont3.lead"),
                                      ul("war.cont3.l1", "war.cont3.l2", "war.cont3.l3"),
                                      p("war.cont3.after"), p("war.cont.note")]),
            panel([node("paragraph", [node("strong", [text(T("war.disc.h"))])]),
                   *(node("paragraph", [text(T(f"war.disc{i}"))]) for i in range(1, 6))]),
            panel([node("paragraph", [text(T(k))]) for k in ("contact.web", "contact.mail", "contact.tel")])]


CHAPTERS = (
    ("specifications", "1.主な仕様", specifications), ("product_overview", "2.各部の名称", overview),
    ("lcd_display", "3.液晶画面", lcd), ("usage", "4.使用について", usage),
    ("app_connection", "5.アプリの接続", app_connection), ("charging", "6.充電方法", charging),
    ("safety", "7.安全上のご注意", safety), ("usage_precautions", "8.使用上のご注意", precautions),
    ("in_the_box", "9.同梱品", in_the_box), ("disclaimer", "10.免責事項", disclaimer),
    ("app_setup", "Jackeryアプリ ユーザーマニュアル", app_manual), ("warranty", "保証について", warranty),
)


def build() -> dict:
    chapters = [{"id": cid, "title": title, "nodes": make()} for cid, title, make in CHAPTERS]
    missing = [k for k in T.rows if k not in T.used]
    if missing:
        raise ValueError("Web transcription lines not bound: " + ", ".join(missing))
    return {"model": "JE-1000D", "region": "JP", "language": LANGUAGE,
            "title": "Jackery ポータブル電源 1000 取扱説明書",
            "source_sha256": "00c43a89bd07babbea3a82b6bfbbc4a1c7b52f7a72cb8030b0dbfb349de601a4",
            "chapters": chapters}


def main() -> None:
    content = build()
    path = PACKAGE / "source/ja/content.json"
    path.write_text(json.dumps(content, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"chapters": [c["id"] for c in content["chapters"]], "lines": len(T.used)}))


if __name__ == "__main__":
    main()
