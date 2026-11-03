"""Bind the JE-1000C JP transcription to shared Web components.

Run from the repository root:

    python manual_sources/JE-1000C/JP/ja/git-20261103-a369a8d0/build_content.py

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
from tools.component_specs.app import app_inline_control_component_spec  # noqa: E402
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
CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱"
SOURCE_SHA256 = "a369a8d0ac33d7f6d7843d404796f7eacfc69c221948318f81f6ca9d2311d9d3"


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


def bullets(keys: list[str]) -> dict:
    return root(node("list", [node("list_item", [node("paragraph", T.inline(k))]) for k in keys], ordered=False))


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


def strong_para(key: str) -> dict:
    return root(node("paragraph", [node("strong", [text(T(key))])]))


def safety_item(variant: str, label: str, title_key: str, body_keys: list[str], ref: str,
                list_keys: tuple[list[str], ...] = ()) -> dict:
    body = [node("paragraph", [node("strong", [text(T(title_key))])])]
    for keys in list_keys:
        body.append(node("list", [node("list_item", [text(T(k))]) for k in keys], ordered=False))
    body += [node("paragraph", [text(T(k))]) for k in body_keys]
    return root(callout(label, body, variant=variant, language=LANGUAGE, source_ref=ref))


def plain_table(header_keys: list[str], rows: list[list[list[dict]]], head_cells: list[list[dict]] | None = None) -> dict:
    cells = head_cells or [[text(T(k))] for k in header_keys]
    head = node("table_head", [node("table_row", [node("table_cell", c, header=True) for c in cells])]) if cells else None
    body = node("table_body", [node("table_row", [node("table_cell", cell, header=False) for cell in row])
                               for row in rows])
    # Shared table wrapper: wide tables scroll inside the component on phones.
    return root(node("group", [node("table", [head, body] if head else [body],
                                    presentation={"html": {"attributes": {"class": "manual-table"}}})],
                     role="container",
                     presentation={"html": {"attributes": {"class": "table-wrapper docutils container"}}}))


def icon(ref: str, alt: str) -> dict:
    return node("image", source=ref, alt=alt)


ECO_ICON = "assets/lcd-energy-saving.svg"


def with_icon(key: str) -> list[dict]:
    """A printed cell whose [12H] mark is the LCD glyph itself."""
    before, after = T(key).split("[12H]")
    return [node("paragraph", [text(before), icon(ECO_ICON, "12H"), text(after)])]


# --- chapters -------------------------------------------------------------

def specifications() -> list[dict]:
    rows = []
    for index in range(1, 17):
        label = T(f"spec.r{index}.l")
        keys = [k for k in T.rows if k.startswith(f"spec.r{index}.v")]
        rows.append((label, "\n".join(T(k) for k in keys)))
    title = T("spec.title")
    spec = spec_table_component_spec(section_title=title, rows=rows, source_ref="native-pdf/page-2/spec",
                                     language=LANGUAGE)
    recycle = plain_table([], [[
        [icon("assets/recycle-li-ion.svg", T("recycle.glyph"))],
        [node("paragraph", [node("strong", [text(T("recycle.title"))])]),
         *(node("paragraph", [text(T(k))]) for k in ("recycle.b1", "recycle.b2", "recycle.b3"))],
    ]])
    return [chapter_heading("spec.h", "native-specifications"),
            component_flow_node(spec, carrier_flow=_spec_carrier(title, rows), root=True),
            para("spec.tm"), para("spec.change"), recycle]


def overview() -> list[dict]:
    keys = ["names.f.lcd", "names.f.ledbtn", "names.f.power", "names.f.led", "names.f.car", "names.f.usba",
            "names.f.carbtn", "names.f.usbc", "names.f.acout", "names.f.usbbtn", "names.f.acbtn",
            "names.r.acin", "names.r.dcin", "names.r.ext"]
    return [chapter_heading("names.h", "native-product-overview"), figure("overview", 3, keys)]


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
    keys = [f"lcd.n{i}" for i in range(1, 19)]
    legend = reference_table_component_spec(
        variant="lcd-descriptions", label=T.rows["lcd.h"]["text"], headers=[],
        rows=[[{"html": CIRCLED[i], "text": CIRCLED[i]}, {"html": escape(T(k)), "text": T.rows[k]["text"]}]
              for i, k in enumerate(keys)],
        source_ref="native-pdf/page-3/lcd-legend", language=LANGUAGE)
    head = [[text(T(k))] for k in ("eco.th1", "eco.th2", "eco.th3", "eco.th4")]
    rows = [[[text(T(f"eco.r{r}.c1"))], [text(T(f"eco.r{r}.c2"))], [text(T(f"eco.r{r}.c3"))], with_icon(f"eco.r{r}.c4")]
            for r in (1, 2, 3)]
    return [chapter_heading("lcd.h", "native-lcd-display"),
            figure("lcd-map", 3, [], label=T.rows["lcd.h"]["text"]),
            component_flow_node(legend, root=True),
            lcd_rows([("lcd.ring.t", ["lcd.ring.b"], "assets/lcd-battery-ring.svg"),
                      ("lcd.low.t", ["lcd.low.b"], "assets/lcd-low-battery.svg"),
                      ("lcd.eco.t", ["lcd.eco.b"], ECO_ICON)], "native-pdf/page-4/lcd-icons"),
            plain_table([], rows, head_cells=head),
            para("eco.on"), para("eco.off"), para("freq.h"), para("freq.auto"), para("freq.manual"),
            lcd_rows([("lcd.fault.t", ["lcd.fault.b1", "lcd.fault.b2", "lcd.fault.b3", "lcd.fault.b4"],
                       "assets/lcd-fault-code.svg"),
                      ("lcd.hot.t", ["lcd.hot.b"], "assets/lcd-high-temperature.svg"),
                      ("lcd.cold.t", ["lcd.cold.b"], "assets/lcd-low-temperature.svg")], "native-pdf/page-4/lcd-alerts")]


def usage() -> list[dict]:
    return [chapter_heading("use.h", "native-usage"), heading("use.h2"),
            para("use.power"), para("use.ac"), para("use.usb.h"), para("use.usb"), para("use.car.h"), para("use.car"),
            para("use.display"), para("use.display.note"), para("use.eps")]


def battery_pack() -> list[dict]:
    return [chapter_heading("pack.h", "native-battery-pack"), para("pack.p")]


def app_connection() -> list[dict]:
    return [chapter_heading("app.h", "native-app-connection"), para("app.p")]


def charging() -> list[dict]:
    box = root(callout(T("chg.box.label"), [node("list", [node("list_item", [text(T(k))])
                                                          for k in ("chg.box.i1", "chg.box.i2", "chg.box.i3")],
                                                     ordered=False)],
                       variant="caution", language=LANGUAGE, source_ref="native-pdf/page-6/caution"))
    return [chapter_heading("chg.h", "native-charging"),
            para("chg.green.h"), para("chg.green"), box,
            heading("chg.ac.h"), para("chg.ac.lead"),
            figure("ac-charge", 6, ["fig.ac.cable", "fig.ac.unit"]),
            para("chg.ac.outlet"),
            heading("chg.solar.h"), heading("chg.solar.h2", level=4), para("chg.solar"),
            figure("solar-direct", 6, ["fig.solar1.left", "fig.solar1.unit", "fig.solar1.right"]),
            figure("solar-adapter", 6, ["fig.solar2.left", "fig.solar2.unit", "fig.solar2.right"]),
            para("chg.solar.note"),
            heading("chg.s80.h", level=4), para("chg.s80.p1"), para("chg.s80.p2"),
            figure("solar-saga80", 7, ["fig.s80.port", "fig.s80.par"]),
            heading("chg.car.h"), para("chg.car"),
            figure("car-charge", 7, ["fig.car.unit"]),
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
        source_ref="native-pdf/page-8/signal", language=LANGUAGE)
    meanings = [T(k) for k, _ in SYMBOLS]
    symbols = symbol_icon_component_spec(
        accessibility_label=T.rows["symbols.h"]["text"],
        headers=[pair(v, "content") for v in ("記号", "意味", "記号", "意味")],
        panels=[[{"asset_index": i, "icon_alt": meanings[i], **pair(meanings[i], "meaning")} for i in rows]
                for rows in ((0, 1, 2), (3, 4, 5))],
        icon_refs=[ref for _, ref in SYMBOLS], source_ref="native-pdf/page-8/symbols", language=LANGUAGE)
    w, c = "warning", "caution"
    w1, w2, c1 = T("w1.band"), T("w2.band"), T("c1.band")
    first = root(callout(w1, [
        node("paragraph", [node("strong", [text(T("w1.i1.t"))])]),
        node("list", [node("list_item", [text(T(f"w1.i1.l{i}"))]) for i in range(1, 6)], ordered=False),
        node("paragraph", [text(T("w1.i1.b1"))]), node("paragraph", [text(T("w1.i1.b2"))]),
        node("paragraph", [node("strong", [text(T("w1.i1.t2"))])]),
        node("paragraph", [text(T("w1.i1.b3"))]), node("paragraph", [text(T("w1.i1.b4"))]),
    ], variant=w, language=LANGUAGE, source_ref="native-pdf/page-8/warning-1"))
    return [chapter_heading("safety.h", "native-safety"),
            strong_para("safety.lead"),
            heading("safety.pict.h"), para("safety.pict1"), para("safety.pict2"),
            component_flow_node(signal, root=True),
            heading("symbols.h"), component_flow_node(symbols, root=True),
            first,
            safety_item(w, w1, "w1.i2.t", ["w1.i2.b"], "native-pdf/page-8/warning-2"),
            safety_item(w, w1, "w1.i3.t", ["w1.i3.b"], "native-pdf/page-8/warning-3"),
            safety_item(w, w1, "w1.i4.t", [], "native-pdf/page-8/warning-4"),
            *(safety_item(w, w2, f"w2.i{i}.t", [f"w2.i{i}.b"], f"native-pdf/page-9/warning-{i + 4}")
              for i in range(1, 8)),
            safety_item(c, c1, "c1.i1.t", ["c1.i1.b"], "native-pdf/page-9/caution-1"),
            safety_item(c, c1, "c1.i2.t", [], "native-pdf/page-9/caution-2",
                        list_keys=(["c1.i2.l1", "c1.i2.l2", "c1.i2.l3"],)),
            safety_item(c, c1, "c1.i3.t", ["c1.i3.b"], "native-pdf/page-9/caution-3"),
            safety_item(c, c1, "c1.i4.t", ["c1.i4.b"], "native-pdf/page-9/caution-4")]


def precautions() -> list[dict]:
    items = [node("list_item", [node("paragraph", [text(T(f"prec.l{i}"))])]) for i in range(1, 15)]
    items.append(node("list_item", [node("paragraph", [text(T("prec.l15.t"))]),
                                    node("paragraph", [text(T("prec.l15.b"))])]))
    items.append(node("list_item", [node("paragraph", [text(T(k))]) for k in
                                    ("prec.l16.t", "prec.l16.b1", "prec.l16.b2")]))
    items.append(node("list_item", [node("paragraph", [text(T("prec.l17"))])]))
    return [chapter_heading("prec.h", "native-usage-precautions"),
            *(para(f"prec.p{i}") for i in range(1, 7)), para("prec.life"),
            root(node("list", items, ordered=False))]


INBOX = (("box.c1", "inbox-unit.png"), ("box.c2", "inbox-car-adapter.png"), ("box.c3", "inbox-cable.svg"),
         ("box.c4", "inbox-pouch.png"), ("box.c5", "inbox-manual.png"), ("box.c6", "inbox-warranty.png"))


def in_the_box() -> list[dict]:
    cards = [{"image_ref": f"assets/{ref}", "label": T(key), "alt": T.rows[key]["text"]} for key, ref in INBOX]
    title = T.rows["box.h"]["text"]
    spec = inbox_component_spec(accessibility_label=title, cards=cards, tip_label="", tip_body="",
                                source_ref="native-pdf/page-11/inbox", language=LANGUAGE, require_tip=False)
    carrier = table([[node("table_cell", [node("image", source=c["image_ref"], alt=c["alt"]),
                                          node("paragraph", [text(c["label"])])], header=False) for c in cards]])
    return [chapter_heading("box.h", "native-in-the-box"), component_flow_node(spec, carrier_flow=(carrier,), root=True),
            para("box.n1")]


def disclaimer() -> list[dict]:
    items = [node("list_item", [node("paragraph", [text(T("disc.l1"))])]),
             node("list_item", [node("paragraph", [text(T("disc.l2a"))]), node("paragraph", [text(T("disc.l2b"))])]),
             *(node("list_item", [node("paragraph", [text(T(f"disc.l{i}"))])]) for i in range(3, 7))]
    return [chapter_heading("disc.h", "native-disclaimer"), root(node("list", items, ordered=False))]


def app_manual() -> list[dict]:
    before, after = T("appm.s21").split(" [+] ")
    plus = app_inline_control_component_spec(
        accessibility_label="+", paragraph_html=f"{escape(before)} <strong>+</strong> {escape(after)}",
        paragraph_text=f"{before} + {after}", source_ref="native-pdf/page-12/add-button", language=LANGUAGE,
        metadata={"visual_recovery": "outlined-pdf-vector-plus-control"})
    plus_carrier = node("paragraph", [text(before + " "), node("strong", [text("+")]), text(" " + after)])

    def note(key: str, ref: str, list_keys: tuple[str, ...] = ()) -> dict:
        label, body = T(key).split("：", 1)
        blocks = [node("paragraph", [text(body)])]
        if list_keys:
            blocks.append(node("list", [node("list_item", [text(T(k))]) for k in list_keys], ordered=False))
        return root(callout(label, blocks, variant="note", language=LANGUAGE, source_ref=ref))

    return [chapter_heading("appm.h", "native-app-manual"),
            heading("appm.s1.h"), para("appm.s1"),
            heading("appm.s2.h"), component_flow_node(plus, carrier_flow=(plus_carrier,), root=True),
            para("appm.s22"),
            figure("app-add", 12, ["fig.app.c21", "fig.app.c22"]),
            note("appm.note1", "native-pdf/page-12/note-1"),
            figure("app-control", 12, ["fig.ctl.dc", "fig.ctl.ac", "fig.ctl.power"]),
            para("appm.s23"),
            note("appm.note2", "native-pdf/page-12/note-2", ("appm.note2.l1", "appm.note2.l2")),
            para("appm.s24"), note("appm.note3", "native-pdf/page-13/note-3"), para("appm.s25"),
            figure("app-results", 13, ["fig.app.c23", "fig.app.c24", "fig.app.c25"]),
            para("appm.shots"),
            heading("appm.s3.h"), para("appm.s3"),
            heading("appm.s4.h"),
            heading("appm.s41.h", level=4), bullets(["appm.s41.l1", "appm.s41.l2"]),
            heading("appm.s42.h", level=4), bullets(["appm.s42.l1", "appm.s42.l2"]),
            heading("appm.s43.h", level=4), bullets(["appm.s43.l1"])]


CHAPTERS = (
    ("specifications", "1.主な仕様", specifications), ("product_overview", "2.各部の名称", overview),
    ("lcd_display", "3.液晶画面", lcd), ("usage", "4.使用について", usage),
    ("battery_pack", "5. バッテリーパック（別売）と併用", battery_pack),
    ("app_connection", "6.アプリの接続", app_connection), ("charging", "7.充電方法", charging),
    ("safety", "8.安全上のご注意", safety), ("usage_precautions", "9.使用上のご注意", precautions),
    ("in_the_box", "10.同梱品", in_the_box), ("disclaimer", "11.免責事項", disclaimer),
    ("app_setup", "Jackeryアプリ ユーザーマニュアル", app_manual),
)


def build() -> dict:
    chapters = [{"id": cid, "title": title, "nodes": make()} for cid, title, make in CHAPTERS]
    missing = [k for k in T.rows if k not in T.used]
    if missing:
        raise ValueError("Web transcription lines not bound: " + ", ".join(missing))
    return {"model": "JE-1000C", "region": "JP", "language": LANGUAGE,
            "title": "Jackery ポータブル電源 1000 Plus 取扱説明書",
            "source_sha256": SOURCE_SHA256, "chapters": chapters}


def main() -> None:
    content = build()
    path = PACKAGE / "source/ja/content.json"
    path.write_text(json.dumps(content, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"chapters": [c["id"] for c in content["chapters"]], "lines": len(T.used)}))


if __name__ == "__main__":
    main()
