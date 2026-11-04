"""Bind the reviewed JE-3000A JP transcription to shared Web components.

Run from the repository root:

    python manual_sources/JE-3000A/JP/ja/git-20261103-002fde5a/build_content.py

Every Web string comes from ``source/transcription.json`` by line id; this
module only decides which shared component carries each printed block, in
printed order. It writes ``source/ja/content.json``, the frozen input that
``rebuild.py`` replays. Component chrome that the shared components require
(signal/symbol table headers) follows the JE-1000D JP V2 edition and is listed
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
from tools.component_specs.manual_tables import (  # noqa: E402
    lcd_icon_component_spec, symbol_icon_component_spec, symbol_signal_component_spec,
)
from tools.component_specs.reference_figure import reference_figure_component_spec  # noqa: E402
from tools.component_specs.reference_table import reference_table_component_spec  # noqa: E402
from tools.component_specs.spec_table import spec_table_component_spec  # noqa: E402
from tools.manual_ir.components import component_flow_node  # noqa: E402
from tools.web.composite_hashing import reference_source_fragment_sha256  # noqa: E402
from tools.web.frozen_ai_flow import callout, node, root, table, text  # noqa: E402
from tools.web.frozen_ai_table_components import _spec_carrier  # noqa: E402

LANGUAGE = "ja"
SOURCE_SHA256 = "002fde5a36f8dfc4192a8534e8f43a98e249bfbc491027b7c1b0c819d75e2002"
CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲"
ENERGY = "assets/lcd-energy-saving.svg"
LOW_TEMP = "assets/lcd-low-temperature.svg"


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


T = Lines()


def para(key: str) -> dict:
    return root(node("paragraph", T.inline(key)))


def heading(key: str, level: int = 3, anchor: str | None = None) -> dict:
    value = T(key)
    return root(node("heading", [text(value)], level=level, **({"anchor": anchor} if anchor else {})))


def chapter_heading(key: str, anchor: str) -> dict:
    # The print letter-spaces chapter titles; the characters are unchanged.
    return heading(key, level=2, anchor=anchor)


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


def strong(key: str) -> dict:
    return root(node("paragraph", [node("strong", [text(T(key))])]))


def safety_item(variant: str, label: str, title_key: str, body_keys: list[str], ref: str,
                list_keys: tuple[list[str], ...] = ()) -> dict:
    body = [node("paragraph", [node("strong", [text(T(title_key))])])]
    for keys in list_keys:
        body.append(node("list", [node("list_item", [text(T(k))]) for k in keys], ordered=False))
    body += [node("paragraph", [text(T(k))]) for k in body_keys]
    return root(callout(label, body, variant=variant, language=LANGUAGE, source_ref=ref))


def plain_table(header: list[dict] | None, rows: list[list[list[dict]]]) -> dict:
    """A declared plain table on the shared manual-table classes inside the shared wrapper."""
    body = node("table_body", [node("table_row", [node("table_cell", cell, header=False) for cell in row])
                               for row in rows])
    return root(node("group", [node("table", [header, body] if header else [body],
                                    presentation={"html": {"attributes": {"class": "manual-table"}}})],
                     role="container",
                     presentation={"html": {"attributes": {"class": "table-wrapper docutils container"}}}))


def icon(ref: str, alt: str) -> dict:
    return node("image", source=ref, alt=alt)


def with_icon(key: str, marker: str, ref: str, alt: str) -> list[dict]:
    """Inline children where the bracketed marker is the printed LCD glyph itself."""
    before, after = T(key).split(marker)
    return [text(before), icon(ref, alt), text(after)]



# --- chapters -------------------------------------------------------------

def specifications() -> list[dict]:
    rows = []
    for index in range(1, 15):
        labels = [T(k) for k in (f"spec.r{index}.l", f"spec.r{index}.l2") if k in T.rows]
        values = [T(k) for k in T.rows if k.startswith(f"spec.r{index}.v")]
        rows.append(("\n".join(labels), "\n".join(values)))
    title = T("spec.title")
    spec = spec_table_component_spec(section_title=title, rows=rows, source_ref="native-pdf/page-2/spec",
                                     language=LANGUAGE)
    recycle = plain_table(None, [[
        [icon("assets/recycle-li-ion.svg", T("recycle.glyph"))],
        [node("paragraph", [node("strong", [text(T("recycle.title"))])]),
         *(node("paragraph", [text(T(k))]) for k in ("recycle.b1", "recycle.b2", "recycle.b3"))],
    ]])
    return [chapter_heading("spec.h", "native-specifications"),
            component_flow_node(spec, carrier_flow=_spec_carrier(title, rows), root=True),
            figure("assets/qc-logo.png", "qc-logo", 2, ["fig.qc.logo"]),
            para("spec.tm1"), para("spec.tm2"), para("spec.tm3"), para("spec.change"), recycle]


def overview() -> list[dict]:
    keys = ["names.f.power", "names.f.car", "names.f.usba", "names.f.usbc", "names.f.dcbtn", "names.f.lcd",
            "names.f.acout1", "names.f.acout2", "names.f.acbtn", "names.r.handle", "names.r.reset",
            "names.r.acin", "names.r.dcin"]
    return [chapter_heading("names.h", "native-product-overview"),
            figure("assets/overview.png", "overview", 3, keys)]


def lcd_rows(rows: list[tuple[str, str, str]], ref: str) -> dict:
    values, refs = [], []
    for index, (title_key, body_key, asset) in enumerate(rows):
        name, body = T(title_key), T(body_key)
        values.append({"name_html": escape(name), "name_text": name, "description_html": escape(body),
                       "description_text": body, "icon_alt": name, "asset_index": index})
        refs.append(asset)
    spec = lcd_icon_component_spec(accessibility_label=values[0]["name_text"], rows=values, icon_refs=refs,
                                   source_ref=ref, language=LANGUAGE, icon_locale_policy="exact", numbered=False)
    return component_flow_node(spec, root=True)


def lcd() -> list[dict]:
    legend = reference_table_component_spec(
        variant="lcd-descriptions", label=T.rows["lcd.h"]["text"], headers=[],
        rows=[[{"html": CIRCLED[i], "text": CIRCLED[i]}, {"html": escape(T(f"lcd.n{i + 1}")),
                                                          "text": T.rows[f"lcd.n{i + 1}"]["text"]}]
              for i in range(19)],
        source_ref="native-pdf/page-4/lcd-legend", language=LANGUAGE)
    cell = lambda key: node("table_cell", [text(T(key))], header=False)  # noqa: E731
    head = node("table_head", [node("table_row", [node("table_cell", [text(T(f"eco.th{i}"))], header=True)
                                                  for i in range(1, 5)])])
    body = node("table_body", [node("table_row", [
        cell(f"eco.r{r}.c1"), cell(f"eco.r{r}.c2"), cell(f"eco.r{r}.c3"),
        node("table_cell", [node("paragraph", with_icon(f"eco.r{r}.c4", "[88H]", ENERGY, "88H"))], header=False),
    ]) for r in (1, 2, 3)])
    # Shared table wrapper: the four columns scroll inside the component on phones.
    eco = root(node("group", [node("table", [head, body],
                                   presentation={"html": {"attributes": {"class": "manual-table"}}})],
                    role="container",
                    presentation={"html": {"attributes": {"class": "table-wrapper docutils container"}}}))
    # 低温モード: bold run-in lead, then the printed thermometer mark inline in the sentence.
    lead = T.rows["lowtemp.mode"]["strong"][0]
    before, after = T("lowtemp.mode").split(lead, 1)[1].split("[LT]")
    low_temp = root(node("paragraph", [node("strong", [text(lead)]), text(before),
                                       icon(LOW_TEMP, T.rows["lcd.n15"]["text"]), text(after)]))
    return [chapter_heading("lcd.h", "native-lcd-display"),
            figure("assets/lcd-map.png", "lcd-map", 3, [], label=T.rows["lcd.h"]["text"]),
            component_flow_node(legend, root=True),
            para("lcd.protect"), para("lcd.quiet"),
            lcd_rows([("lcd.d10.t", "lcd.d10.b", "assets/lcd-battery-ring.svg"),
                      ("lcd.d11.t", "lcd.d11.b", "assets/lcd-low-battery.svg"),
                      ("lcd.d16.t", "lcd.d16.b", ENERGY)], "native-pdf/page-4/lcd-icons"),
            eco, strong("eco.off.h"), para("eco.off"), strong("eco.on.h"), para("eco.on"),
            para("freq.h"), para("freq.auto"), para("freq.manual"),
            lcd_rows([("lcd.d13.t", "lcd.d13.b", "assets/lcd-fault-code.svg"),
                      ("lcd.d14.t", "lcd.d14.b", "assets/lcd-high-temperature.svg"),
                      ("lcd.d15.t", "lcd.d15.b", LOW_TEMP)], "native-pdf/page-5/lcd-icons"),
            low_temp]


def usage() -> list[dict]:
    return [chapter_heading("use.h", "native-usage"), heading("use.power.h"), para("use.power"),
            strong("use.ac.h"), para("use.ac"), strong("use.usb.h"), para("use.usb"),
            strong("use.car.h"), para("use.car"),
            para("use.display"), para("use.display.note"), para("use.reset"), para("use.eps")]


def charging() -> list[dict]:
    caution_items = [node("list_item", [text(T(k))]) for k in ("chg.box.i1", "chg.box.i2")]
    caution_items.append(node("list_item", [node("paragraph", [text(T("chg.box.i3"))]),
                                            node("paragraph", [text(T("chg.box.i3b"))])]))
    label = T("chg.box.label")
    caution = root(callout(label, [node("list", caution_items, ordered=False)], variant="caution",
                           language=LANGUAGE, source_ref="native-pdf/page-6/caution"))
    return [chapter_heading("chg.h", "native-charging"),
            para("chg.green.h"), para("chg.green"), caution,
            heading("chg.ac.h"), para("chg.ac.lead"),
            figure("assets/ac-charge.png", "ac-charge", 6, ["fig.ac.cable", "fig.ac.unit"]),
            heading("chg.solar.h"), heading("chg.ss.h", level=4), para("chg.ss"),
            figure("assets/solar-three.png", "solar-three", 7, ["fig.s3.panels", "fig.s3.unit"]),
            figure("assets/solar-four.png", "solar-four", 7, ["fig.s4.left", "fig.s4.unit", "fig.s4.right"]),
            figure("assets/solar-six.png", "solar-six", 7, ["fig.s6.left", "fig.s6.unit", "fig.s6.right"]),
            para("chg.ss.note"), para("chg.ss.note2"),
            figure("assets/prohibited-1.png", "prohibited-1", 8, ["fig.x1.left", "fig.x1.unit", "fig.x1.right"]),
            figure("assets/prohibited-2.png", "prohibited-2", 8, ["fig.x2.left", "fig.x2.unit", "fig.x2.right"]),
            figure("assets/prohibited-3.png", "prohibited-3", 8, ["fig.x3.left", "fig.x3.unit", "fig.x3.right"]),
            heading("chg.s80.h", level=4), para("chg.s80"), para("chg.s80.b"),
            figure("assets/solarsaga80.png", "solarsaga80", 8, ["fig.s80.port", "fig.s80.parallel"]),
            para("chg.s80.point"),
            heading("chg.tj.h", level=4), para("chg.tj1"), para("chg.tj2"),
            figure("assets/transjack.png", "transjack", 9,
                   ["fig.tj.dc8020", "fig.tj.jack", "fig.tj.dc7909", "fig.tj.unit"]),
            para("chg.tj.note"),
            heading("chg.car.h"), para("chg.car"),
            figure("assets/car-charge.png", "car-charge", 9, ["fig.car.unit"]),
            heading("chg.safe.h"), para("chg.safe1"), para("chg.safe2")]


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
        source_ref="native-pdf/page-10/signal", language=LANGUAGE)
    meanings = [T(k) for k, _ in SYMBOLS]
    symbols = symbol_icon_component_spec(
        accessibility_label=T.rows["symbols.h"]["text"],
        headers=[pair(v, "content") for v in ("記号", "意味", "記号", "意味")],
        panels=[[{"asset_index": i, "icon_alt": meanings[i], **pair(meanings[i], "meaning")} for i in rows]
                for rows in ((0, 1, 2), (3, 4, 5))],
        icon_refs=[ref for _, ref in SYMBOLS], source_ref="native-pdf/page-10/symbols", language=LANGUAGE)
    w, c = "warning", "caution"
    first = root(callout(T("w1.band"), [
        node("paragraph", [node("strong", [text(T("w1.i1.t"))])]),
        node("list", [node("list_item", [text(T(f"w1.i1.l{i}"))]) for i in range(1, 6)], ordered=False),
        node("paragraph", [text(T("w1.i1.b1"))]), node("paragraph", [text(T("w1.i1.b2"))]),
        node("paragraph", [node("strong", [text(T("w1.i1.t2"))])]),
        node("paragraph", [text(T("w1.i1.b3"))]), node("paragraph", [text(T("w1.i1.b4"))]),
    ], variant=w, language=LANGUAGE, source_ref="native-pdf/page-10/warning-1"))
    warn = T.rows["w1.band"]["text"]
    w2 = T("w2.band")
    c1 = T("c1.band")
    return [chapter_heading("safety.h", "native-safety"),
            strong("safety.lead"),
            heading("safety.pict.h"), para("safety.pict1"), para("safety.pict2"),
            component_flow_node(signal, root=True),
            heading("symbols.h"), component_flow_node(symbols, root=True),
            first,
            safety_item(w, warn, "w1.i2.t", ["w1.i2.b"], "native-pdf/page-10/warning-2"),
            safety_item(w, warn, "w1.i3.t", ["w1.i3.b"], "native-pdf/page-10/warning-3"),
            safety_item(w, warn, "w1.i4.t", [], "native-pdf/page-10/warning-4"),
            *(safety_item(w, w2, f"w2.i{i}.t", [f"w2.i{i}.b"], f"native-pdf/page-11/warning-{i + 4}")
              for i in range(1, 8)),
            safety_item(c, c1, "c1.i1.t", ["c1.i1.b"], "native-pdf/page-11/caution-1"),
            safety_item(c, c1, "c1.i2.t", [], "native-pdf/page-11/caution-2",
                        list_keys=(["c1.i2.l1", "c1.i2.l2", "c1.i2.l3"],)),
            safety_item(c, c1, "c1.i3.t", ["c1.i3.b"], "native-pdf/page-11/caution-3")]


def precautions() -> list[dict]:
    item = lambda *keys: node("list_item", [node("paragraph", [text(T(k))]) for k in keys])  # noqa: E731
    items = [item(f"prec.l{i}") for i in range(1, 12)]
    items += [item("prec.l12.t", "prec.l12.b"), item("prec.l13.t", "prec.l13.b1", "prec.l13.b2"), item("prec.l14")]
    return [chapter_heading("prec.h", "native-usage-precautions"), root(node("list", items, ordered=False))]


INBOX = [("box.c1", "assets/inbox-unit.png"), ("box.c2", "assets/inbox-car-adapter.png"),
         ("box.c3", "assets/inbox-ac-cable.png"), ("box.c4", "assets/inbox-pouch.png"),
         ("box.c5", "assets/inbox-transjack.png"), ("box.c6", "assets/inbox-manual.png"),
         ("box.c7", "assets/inbox-warranty.png")]


def in_the_box() -> list[dict]:
    cards = [{"image_ref": ref, "label": T(key), "alt": T.rows[key]["text"]} for key, ref in INBOX]
    title = T.rows["box.h"]["text"]
    spec = inbox_component_spec(accessibility_label=title, cards=cards, tip_label="", tip_body="",
                                source_ref="native-pdf/page-13/inbox", language=LANGUAGE, require_tip=False)
    carrier = table([[node("table_cell", [node("image", source=c["image_ref"], alt=c["alt"]),
                                          node("paragraph", [text(c["label"])])], header=False) for c in cards]])
    return [chapter_heading("box.h", "native-in-the-box"),
            component_flow_node(spec, carrier_flow=(carrier,), root=True), para("box.n1")]


def disclaimer() -> list[dict]:
    item = lambda *keys: node("list_item", [node("paragraph", [text(T(k))]) for k in keys])  # noqa: E731
    items = [item("disc.l1"), item("disc.l2a", "disc.l2b"), item("disc.l3"), item("disc.l4"), item("disc.l5"),
             item("disc.l6a", "disc.l6b")]
    return [chapter_heading("disc.h", "native-disclaimer"), root(node("list", items, ordered=False))]


def app_download() -> list[dict]:
    # Back-cover notice: printed without a heading, so it stays an unheaded shared text panel.
    return [panel([node("paragraph", [text(T("back.app1"))]), node("paragraph", [text(T("back.app2"))])]),
            figure("assets/app-store.png", "app-store", 14, ["fig.badge.apple", "fig.badge.google"])]


CHAPTERS = (
    ("specifications", "1.主な仕様", specifications), ("product_overview", "2.各部の名称", overview),
    ("lcd_display", "3.液晶画面", lcd), ("usage", "4.使用について", usage),
    ("charging", "5.充電方法", charging), ("safety", "6.安全上のご注意", safety),
    ("usage_precautions", "7.使用上のご注意", precautions), ("in_the_box", "8.同梱品", in_the_box),
    ("disclaimer", "9.免責事項", disclaimer), ("app_download", "Jackery App", app_download),
)


def build() -> dict:
    chapters = [{"id": cid, "title": title, "nodes": make()} for cid, title, make in CHAPTERS]
    missing = [k for k in T.rows if k not in T.used]
    if missing:
        raise ValueError("Web transcription lines not bound: " + ", ".join(missing))
    return {"model": "JE-3000A", "region": "JP", "language": LANGUAGE,
            "title": "Jackery ポータブル電源 3000 Pro 取扱説明書",
            "source_sha256": SOURCE_SHA256, "chapters": chapters}


def main() -> None:
    content = build()
    path = PACKAGE / "source/ja/content.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(content, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"chapters": [c["id"] for c in content["chapters"]], "lines": len(T.used)}))


if __name__ == "__main__":
    main()
