"""Bind the JE-2000C JP transcription to shared Web components.

Run from the repository root:

    python manual_sources/JE-2000C/JP/ja/git-20261103-88b78332/build_content.py

Every Web string comes from ``source/transcription.json`` (derived from the
PDF text layer by ``build_transcription.py``) by line id; this module only
decides which shared component carries each printed block, in printed order.
It writes ``source/ja/content.json``, the frozen input that ``rebuild.py``
replays. Component chrome that the shared components require (signal/symbol
table headers) follows the JE-1000D / JE-1500D JP V2 editions and is listed in
``source/differences.md``.
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
SOURCE_SHA256 = "88b78332342866ccd994cfa054a8a63a5fe30fa41131de5c7d53f16cd590690b"
CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳㉑"


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


def strong(key: str) -> dict:
    return root(node("paragraph", [node("strong", [text(T(key))])]))


def heading(key: str, level: int = 3, anchor: str | None = None) -> dict:
    value = T(key)
    return root(node("heading", [text(value)], level=level, **({"anchor": anchor} if anchor else {})))


def chapter_heading(key: str, anchor: str) -> dict:
    return heading(key, level=2, anchor=anchor)


def items(keys: list[str]) -> list[dict]:
    return [node("list_item", [node("paragraph", T.inline(k))]) for k in keys]


def bullets(keys: list[str]) -> dict:
    return root(node("list", items(keys), ordered=False))


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


def note(key: str, ref: str, list_keys: tuple[str, ...] = ()) -> dict:
    """A printed 「備考：…」 line: the prefix is the note label."""
    label, body = T(key).split("：", 1)
    children = [node("paragraph", [text(body)])]
    if list_keys:
        children.append(node("list", [node("list_item", [text(T(k))]) for k in list_keys], ordered=False))
    return root(callout(label, children, variant="note", language=LANGUAGE, source_ref=ref))


def plain_table(rows: list[list[list[dict]]], header: list[dict] | None = None) -> dict:
    body = node("table_body", [node("table_row", [node("table_cell", cell, header=False) for cell in row])
                               for row in rows])
    parts = ([node("table_head", [node("table_row", header)])] if header else []) + [body]
    return root(node("group", [node("table", parts, presentation={"html": {"attributes": {"class": "manual-table"}}})],
                     role="container",
                     presentation={"html": {"attributes": {"class": "table-wrapper docutils container"}}}))


def icon(ref: str, alt: str) -> dict:
    return node("image", source=ref, alt=alt)


ENERGY = "assets/lcd-energy-saving.svg"


def with_icon(key: str) -> list[dict]:
    """A printed cell whose [88H] mark is the LCD glyph itself."""
    before, after = T(key).split("[88H]")
    children = [text(before), icon(ENERGY, "88H")] + ([text(after)] if after else [])
    return [node("paragraph", children)]


# --- chapters -------------------------------------------------------------

SPEC_ROWS = 17


def specifications() -> list[dict]:
    rows: list[tuple[str, str]] = []
    for index in range(1, SPEC_ROWS + 1):
        label = T(f"spec.r{index}.l")
        if f"spec.r{index}.v" in T.rows:
            rows.append((label, T(f"spec.r{index}.v")))
        else:
            keys = sorted((k for k in T.rows if k.startswith(f"spec.r{index}.v")), key=lambda k: int(k[-1]))
            rows.append((label, "\n".join(T(k) for k in keys)))
        if f"spec.r{index}.v2" in T.rows and f"spec.r{index}.v" in T.rows:
            rows.append(("", T(f"spec.r{index}.v2")))
    title = T("spec.title")
    spec = spec_table_component_spec(section_title=title, rows=rows, source_ref="native-pdf/page-2/spec",
                                     language=LANGUAGE)
    recycle = plain_table([[
        [icon("assets/recycle-arrows.svg", T.rows["recycle.mark"]["text"]),
         node("paragraph", [node("strong", [text(T("recycle.mark"))])])],
        [node("paragraph", [node("strong", [text(T("recycle.title"))])]),
         *(node("paragraph", [text(T(k))]) for k in ("recycle.b1", "recycle.b2", "recycle.b3"))],
    ]])
    return [chapter_heading("spec.h", "native-specifications"),
            component_flow_node(spec, carrier_flow=_spec_carrier(title, rows), root=True),
            strong("spec.cert"),
            figure("assets/certifications.png", "certifications", 2, [],
                   label="UN38.3 / Qualcomm quick charge 3.0"),
            para("spec.tm1"), para("spec.tm2"), strong("spec.change"), recycle]


def overview() -> list[dict]:
    keys = ["names.f.power", "names.f.car", "names.f.usba", "names.f.usbc", "names.f.dcbtn", "names.f.lcd",
            "names.f.ac1", "names.f.ac2", "names.f.acbtn", "names.r.handle", "names.r.acexp",
            "names.r.acreset", "names.r.acin", "names.r.dcin", "names.r.dcexp"]
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
        rows=[[{"html": CIRCLED[i], "text": CIRCLED[i]},
               {"html": escape(T(f"lcd.n{i + 1}")), "text": T.rows[f"lcd.n{i + 1}"]["text"]}]
              for i in range(21)],
        source_ref="native-pdf/page-4/lcd-legend", language=LANGUAGE)
    header = [node("table_cell", [text(T(k))], header=True) for k in ("eco.th1", "eco.th2", "eco.th3")]
    header.append(node("table_cell", with_icon("eco.th4"), header=True))
    eco = plain_table([[[text(T(f"eco.r{r}.c1"))], [text(T(f"eco.r{r}.c2"))], [text(T(f"eco.r{r}.c3"))],
                        with_icon(f"eco.r{r}.c4")] for r in (1, 2, 3)], header=header)
    return [chapter_heading("lcd.h", "native-lcd-display"),
            figure("assets/lcd-map.png", "lcd-map", 3, [], label=T.rows["lcd.h"]["text"]),
            component_flow_node(legend, root=True),
            para("lcd.protect"), para("lcd.quiet"),
            lcd_rows([("lcd.d1.t", "lcd.d1.b", "assets/lcd-battery-power.svg"),
                      ("lcd.d2.t", "lcd.d2.b", "assets/lcd-low-battery.svg"),
                      ("lcd.d3.t", "lcd.d3.b", ENERGY)], "native-pdf/page-4/lcd-icons"),
            eco, para("eco.off"), para("eco.on"), strong("freq.h"), para("freq.p"),
            lcd_rows([("lcd.d4.t", "lcd.d4.b", "assets/lcd-fault-code.png"),
                      ("lcd.d5.t", "lcd.d5.b", "assets/lcd-high-temperature.svg"),
                      ("lcd.d6.t", "lcd.d6.b", "assets/lcd-low-temperature.png"),
                      ("lcd.d7.t", "lcd.d7.b", "assets/lcd-ac-expansion.svg")], "native-pdf/page-5/lcd-icons")]


def usage() -> list[dict]:
    return [chapter_heading("use.h", "native-usage"), heading("use.h2"),
            para("use.main"), para("use.ac"), para("use.usb"), strong("use.car.h"), para("use.car"),
            para("use.display"), para("use.display.note"), para("use.reset"), para("use.eps")]


def battery_pack() -> list[dict]:
    return [chapter_heading("pack.h", "native-battery-pack"), para("pack.p")]


def app_connection() -> list[dict]:
    return [chapter_heading("app.h", "native-app-connection"), strong("app.p")]


def charging() -> list[dict]:
    prohibited = [f"fig.x{i}.{k}" for i in (1, 2, 3) for k in ("left", "unit", "right")]
    return [chapter_heading("chg.h", "native-charging"),
            para("chg.green.h"), para("chg.green"),
            callout_block("chg.box.label", ["chg.box.i1", "chg.box.i2", "chg.box.i3"], "caution",
                          "native-pdf/page-6/caution"),
            heading("chg.ac.h"), para("chg.ac"),
            figure("assets/ac-charge.png", "ac-charge", 7, ["fig.ac.cable", "fig.ac.unit"]),
            heading("chg.solar.h"), heading("chg.solar.h2", level=4), para("chg.solar"),
            figure("assets/solar-3.png", "solar-3", 7, ["fig.s3.unit", "fig.s3.panels"]),
            figure("assets/solar-2-2.png", "solar-2-2", 7, ["fig.s22.left", "fig.s22.unit", "fig.s22.right"]),
            figure("assets/solar-3-3.png", "solar-3-3", 7, ["fig.s33.left", "fig.s33.unit", "fig.s33.right"]),
            para("chg.solar.note"), para("chg.prohibit"),
            figure("assets/solar-prohibited.png", "solar-prohibited", 8, prohibited),
            heading("chg.s80.h", level=4), para("chg.s80.p1"), para("chg.s80.p2"),
            figure("assets/solar-80.png", "solar-80", 8, ["fig.s80.out", "fig.s80.par"]),
            heading("chg.car.h"), para("chg.car"),
            figure("assets/car-charge.png", "car-charge", 9, ["fig.car.unit"]),
            heading("chg.safe.h"), para("chg.safe1"), para("chg.safe2"), para("chg.safe3"), para("chg.safe4")]


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
    w1 = T("w1.band")
    first = root(callout(w1, [
        node("paragraph", [node("strong", [text(T("w1.i1.t"))])]),
        node("list", [node("list_item", [text(T(f"w1.i1.l{i}"))]) for i in range(1, 6)], ordered=False),
        node("paragraph", [text(T("w1.i1.b1"))]), node("paragraph", [text(T("w1.i1.b2"))]),
        node("paragraph", [node("strong", [text(T("w1.i1.t2"))])]),
        node("paragraph", [text(T("w1.i1.b3"))]), node("paragraph", [text(T("w1.i1.b4"))]),
    ], variant=w, language=LANGUAGE, source_ref="native-pdf/page-10/warning-1"))
    w2 = T("w2.band")
    c1 = T("c1.band")
    return [chapter_heading("safety.h", "native-safety"), strong("safety.lead"),
            heading("safety.pict.h"), para("safety.pict1"), para("safety.pict2"),
            component_flow_node(signal, root=True),
            heading("symbols.h"), component_flow_node(symbols, root=True),
            first,
            safety_item(w, w1, "w1.i2.t", ["w1.i2.b"], "native-pdf/page-10/warning-2"),
            safety_item(w, w1, "w1.i3.t", ["w1.i3.b"], "native-pdf/page-10/warning-3"),
            safety_item(w, w1, "w1.i4.t", [], "native-pdf/page-10/warning-4"),
            *(safety_item(w, w2, f"w2.i{i}.t", [f"w2.i{i}.b"], f"native-pdf/page-11/warning-{i + 4}")
              for i in range(1, 8)),
            safety_item(c, c1, "c1.i1.t", ["c1.i1.b"], "native-pdf/page-11/caution-1"),
            safety_item(c, c1, "c1.i2.t", [], "native-pdf/page-11/caution-2",
                        list_keys=(["c1.i2.l1", "c1.i2.l2", "c1.i2.l3"],)),
            safety_item(c, c1, "c1.i3.t", ["c1.i3.b"], "native-pdf/page-11/caution-3"),
            safety_item(c, c1, "c1.i4.t", ["c1.i4.b"], "native-pdf/page-11/caution-4")]


def precautions() -> list[dict]:
    def item(*keys: str) -> dict:
        return node("list_item", [node("paragraph", [text(T(k))]) for k in keys])
    entries = [item(f"prec.l{i}") for i in range(1, 10)]
    entries += [item("prec.l10a", "prec.l10b"), item("prec.l11"), item("prec.l12.t", "prec.l12.b"),
                item("prec.l13.t", "prec.l13.b1", "prec.l13.b2"), item("prec.l14")]
    return [chapter_heading("prec.h", "native-usage-precautions"), root(node("list", entries, ordered=False))]


def in_the_box() -> list[dict]:
    refs = ("assets/inbox-unit.png", "assets/inbox-car-cable.png", "assets/inbox-ac-cable.png",
            "assets/inbox-pouch.png", "assets/inbox-manual.png", "assets/inbox-warranty.png")
    cards = []
    for index, ref in enumerate(refs, start=1):
        label = T(f"box.c{index}")  # the shared card draws the printed ①–⑥ badge
        cards.append({"image_ref": ref, "label": label, "alt": label})
    title = T.rows["box.h"]["text"]
    spec = inbox_component_spec(accessibility_label=title, cards=cards, tip_label="", tip_body="",
                                source_ref="native-pdf/page-13/inbox", language=LANGUAGE, require_tip=False)
    carrier = table([[node("table_cell", [node("image", source=c["image_ref"], alt=c["alt"]),
                                          node("paragraph", [text(c["label"])])], header=False) for c in cards]])
    return [chapter_heading("box.h", "native-in-the-box"),
            component_flow_node(spec, carrier_flow=(carrier,), root=True), para("box.note")]


def disclaimer() -> list[dict]:
    entries = [node("list_item", [node("paragraph", [text(T("disc.l1"))])]),
               node("list_item", [node("paragraph", [text(T("disc.l2a"))]),
                                  node("paragraph", [text(T("disc.l2b"))])]),
               *(node("list_item", [node("paragraph", [text(T(f"disc.l{i}"))])]) for i in range(3, 7))]
    return [chapter_heading("disc.h", "native-disclaimer"), root(node("list", entries, ordered=False))]


def app_manual() -> list[dict]:
    before, after = T("appm.s21").split("[+]")
    plus = app_inline_control_component_spec(
        accessibility_label="+", paragraph_html=f"{escape(before)} <strong>+</strong> {escape(after)}",
        paragraph_text=f"{before} + {after}", source_ref="native-pdf/page-14/add-button", language=LANGUAGE,
        metadata={"visual_recovery": "pdf-vector-plus-control-in-text-gap"})
    plus_carrier = node("paragraph", [text(before + " "), node("strong", [text("+")]), text(" " + after)])
    return [chapter_heading("appm.h", "native-app-manual"),
            heading("appm.s1.h"), para("appm.s1"),
            heading("appm.s2.h"), component_flow_node(plus, carrier_flow=(plus_carrier,), root=True),
            para("appm.s22"),
            figure("assets/app-add.png", "app-add", 14, ["fig.app.c21", "fig.app.c22"]),
            note("appm.note1", "native-pdf/page-14/note-1"),
            figure("assets/app-control.png", "app-control", 14, ["fig.ctl.dc", "fig.ctl.ac", "fig.ctl.power"]),
            para("appm.s23"),
            note("appm.note2", "native-pdf/page-14/note-2", ("appm.note2.l1", "appm.note2.l2")),
            para("appm.s24"), note("appm.note3", "native-pdf/page-15/note-3"), para("appm.s25"),
            figure("assets/app-results.png", "app-results", 15, ["fig.app.c23", "fig.app.c24", "fig.app.c25"]),
            para("appm.shots"),
            heading("appm.s3.h"), para("appm.s3"),
            heading("appm.s4.h"),
            para("appm.s41"), bullets(["appm.s41.l1", "appm.s41.l2"]),
            para("appm.s42"), bullets(["appm.s42.l1", "appm.s42.l2"]),
            para("appm.s43"), bullets(["appm.s43.l1"]),
            para("back.app"),
            figure("assets/app-store.png", "app-store", 16, [], label="App Store / Google Play"),
            figure("assets/app-qr.png", "app-qr", 16, [], label="Jackery App QR")]


CHAPTERS = (
    ("specifications", "spec.h", specifications), ("product_overview", "names.h", overview),
    ("lcd_display", "lcd.h", lcd), ("usage", "use.h", usage), ("battery_pack", "pack.h", battery_pack),
    ("app_connection", "app.h", app_connection), ("charging", "chg.h", charging),
    ("safety", "safety.h", safety), ("usage_precautions", "prec.h", precautions),
    ("in_the_box", "box.h", in_the_box), ("disclaimer", "disc.h", disclaimer),
    ("app_setup", "appm.h", app_manual),
)


def build() -> dict:
    chapters = [{"id": cid, "title": T.rows[key]["text"], "nodes": make()} for cid, key, make in CHAPTERS]
    missing = [k for k in T.rows if k not in T.used]
    if missing:
        raise ValueError("Web transcription lines not bound: " + ", ".join(missing))
    return {"model": "JE-2000C", "region": "JP", "language": LANGUAGE,
            "title": "Jackery ポータブル電源 2000 Plus 取扱説明書",
            "source_sha256": SOURCE_SHA256, "chapters": chapters}


def main() -> None:
    content = build()
    path = PACKAGE / "source/ja/content.json"
    path.write_text(json.dumps(content, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"chapters": [c["id"] for c in content["chapters"]], "lines": len(T.used)}))


if __name__ == "__main__":
    main()
