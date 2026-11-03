"""Bind the reviewed JE-100A JP transcription to shared Web components.

Run from the repository root:

    python manual_sources/JE-100A/JP/ja/git-20261103-2becaa50/build_content.py

Every Web string comes from ``source/transcription.json`` by line id; this
module only decides which shared component carries each printed block, in
printed order. It writes ``source/ja/content.json``, the frozen input that
``rebuild.py`` replays. Component chrome that the shared components require
(signal/symbol table headers) follows the JE-1000D JP V2 edition;
``source_manifest.json:component_map`` lists the map and
``source/differences.md`` every deliberate layout difference.
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
from tools.component_specs.spec_table import spec_table_component_spec  # noqa: E402
from tools.manual_ir.components import component_flow_node  # noqa: E402
from tools.web.composite_hashing import reference_source_fragment_sha256  # noqa: E402
from tools.web.frozen_ai_flow import callout, node, root, table, text  # noqa: E402
from tools.web.frozen_ai_table_components import _spec_carrier  # noqa: E402

LANGUAGE = "ja"
SOURCE_SHA256 = "2becaa507bbfd8d051888ac85d96a5399f0959224e9e6acb85211599baa06262"
MARKS = {"strong": "strong", "sup": "superscript"}


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

    def spans(self, key: str) -> list[tuple[str, str | None]]:
        """(text, mark) runs: printed bold and superscript spans in order."""
        row = self.rows[key]
        runs: list[tuple[str, str | None]] = [(self(key), None)]
        for kind in MARKS:
            for span in row.get(kind, []):
                for index, (value, mark) in enumerate(runs):
                    if mark is None and span in value:
                        before, after = value.split(span, 1)
                        runs[index:index + 1] = [r for r in ((before, None), (span, kind), (after, None)) if r[0]]
                        break
                else:
                    raise ValueError(f"{key}: printed span not found: {span}")
        return runs

    def inline(self, key: str) -> list[dict]:
        return [text(value) if mark is None else node(MARKS[mark], [text(value)]) for value, mark in self.spans(key)]


T = Lines()


def para(key: str) -> dict:
    return root(node("paragraph", T.inline(key)))


def strong_para(key: str) -> dict:
    return root(node("paragraph", [node("strong", [text(T(key))])]))


def heading(key: str, level: int = 3, anchor: str | None = None) -> dict:
    value = T(key)
    return root(node("heading", [text(value)], level=level, **({"anchor": anchor} if anchor else {})))


def chapter_heading(key: str, anchor: str) -> dict:
    # The print letter-spaces some chapter titles; the characters are unchanged.
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


def safety_item(variant: str, label: str, title_key: str, body_keys: list[str], ref: str) -> dict:
    body = [node("paragraph", [node("strong", [text(T(title_key))])])]
    body += [node("paragraph", [text(T(k))]) for k in body_keys]
    return root(callout(label, body, variant=variant, language=LANGUAGE, source_ref=ref))


def plain_table(rows: list[list[list[dict]]], css: str = "manual-table") -> dict:
    body = node("table_body", [node("table_row", [node("table_cell", cell, header=False) for cell in row])
                               for row in rows])
    return root(node("group", [node("table", [body], presentation={"html": {"attributes": {"class": css}}})],
                     role="container",
                     presentation={"html": {"attributes": {"class": "table-wrapper docutils container"}}}))


def icon(ref: str, alt: str) -> dict:
    return node("image", source=ref, alt=alt)


# --- chapters -------------------------------------------------------------

def specifications() -> list[dict]:
    rows = []
    for index in range(1, 20):
        label = T(f"spec.r{index}.l")
        keys = [k for k in T.rows if k == f"spec.r{index}.v" or k.startswith(f"spec.r{index}.v")
                and k[len(f"spec.r{index}.v"):].isdigit()]
        rows.append((label, "\n".join(T(k) for k in keys)))
    # The printed chapter title is the shared spec section title (no separate table title is printed).
    title = T("spec.h")
    spec = spec_table_component_spec(section_title=title, rows=rows, source_ref="native-pdf/page-2/spec",
                                     language=LANGUAGE)
    recycle = plain_table([[
        [icon("assets/recycle-li-ion.svg", T("recycle.glyph"))],
        [node("paragraph", [node("strong", [text(T("recycle.title"))])]),
         *(node("paragraph", [text(T(k))]) for k in ("recycle.b1", "recycle.b2", "recycle.b3"))],
    ]])
    return [component_flow_node(spec, carrier_flow=_spec_carrier(title, rows), root=True),
            para("spec.tm"), para("spec.change"), recycle]


def in_the_box() -> list[dict]:
    cards = [{"image_ref": ref, "label": T(key), "alt": T.rows[key]["text"]}
             for key, ref in (("box.c1", "assets/inbox-unit.png"), ("box.c2", "assets/inbox-cable.png"),
                              ("box.c3", "assets/inbox-manual.png"))]
    title = T.rows["box.h"]["text"]
    spec = inbox_component_spec(accessibility_label=title, cards=cards, tip_label="", tip_body="",
                                source_ref="native-pdf/page-3/inbox", language=LANGUAGE, require_tip=False)
    carrier = table([[node("table_cell", [node("image", source=c["image_ref"], alt=c["alt"]),
                                          node("paragraph", [text(c["label"])])], header=False) for c in cards]])
    return [chapter_heading("box.h", "native-in-the-box"),
            component_flow_node(spec, carrier_flow=(carrier,), root=True)]


def overview() -> list[dict]:
    keys = ["names.lcd", "names.display", "names.usba", "names.usbc1", "names.usbc2", "names.usbc"]
    return [chapter_heading("ov.h", "native-product-overview"), heading("ov.sub"),
            figure("assets/overview.png", "overview", 3, keys)]


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
    first = [("lcd.ring.t", ["lcd.ring.b"], "assets/lcd-battery-ring.svg"),
             ("lcd.low.t", ["lcd.low.b"], "assets/lcd-low-battery.svg"),
             ("lcd.aod.t", ["lcd.aod.b"], "assets/lcd-always-on.svg"),
             ("lcd.eco.t", ["lcd.eco.b1", "lcd.eco.b2"], "assets/lcd-energy-saving.svg")]
    second = [("lcd.fault.t", ["lcd.fault.b"], "assets/shared-lcd/25_Fault_code_LaTmb4IQYo3vwvxMqQNcC2RgnIf.png"),
              ("lcd.ht.t", ["lcd.ht.b"], "assets/lcd-high-temperature.svg"),
              ("lcd.lt.t", ["lcd.lt.b"], "assets/lcd-low-temperature.svg")]
    return [chapter_heading("lcd.h", "native-lcd-display"),
            figure("assets/lcd-map.png", "lcd-map", 3, [f"fig.lcd.n{i}" for i in range(1, 10)]),
            lcd_rows(first, "native-pdf/page-4/lcd-icons-1"), para("lcd.eco.on"), para("lcd.eco.off"),
            lcd_rows(second, "native-pdf/page-4/lcd-icons-2")]


def operations() -> list[dict]:
    return [chapter_heading("ops.h", "native-basic-operations"), heading("ops.lcd.h"),
            para("ops.p1"), para("ops.p2"), para("ops.p3"), para("ops.tip")]


def charging() -> list[dict]:
    return [chapter_heading("chg.h", "native-charging"),
            heading("chg.note.h"),
            callout_block("chg.box.label", ["chg.box.i1", "chg.box.i2", "chg.box.i3", "chg.box.i4"], "caution",
                          "native-pdf/page-5/caution"),
            heading("chg.ac.h"), para("chg.ac.p"),
            figure("assets/ac-charge.png", "ac-charge", 5, ["fig.ac.cable", "fig.ac.unit"]),
            heading("chg.solar.h"), heading("chg.solar.g1.h", level=4), para("chg.solar.g1.p"),
            figure("assets/solar-100.png", "solar-100", 6,
                   ["fig.solar1.cable", "fig.solar1.male", "fig.solar1.port", "fig.solar1.panel", "fig.solar1.unit"]),
            heading("chg.solar.g2.h", level=4), para("chg.solar.g2.p80"),
            figure("assets/solar-80.png", "solar-80", 6,
                   ["fig.solar80.port", "fig.solar80.dc", "fig.solar80.panel", "fig.solar80.cable"]),
            para("chg.solar.g2.p40"),
            figure("assets/solar-40.png", "solar-40", 6,
                   ["fig.solar40.port", "fig.solar40.panel", "fig.solar40.dc", "fig.solar40.cable"]),
            heading("chg.car.h"), para("chg.car.p"),
            figure("assets/car-charge.png", "car-charge", 7,
                   ["fig.car.port", "fig.car.dc", "fig.car.cable", "fig.car.unit", "fig.car.vehicle"])]


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
        source_ref="native-pdf/page-7/signal", language=LANGUAGE)
    meanings = [T(k) for k, _ in SYMBOLS]
    symbols = symbol_icon_component_spec(
        accessibility_label=T.rows["symbols.h"]["text"],
        headers=[pair(v, "content") for v in ("記号", "意味", "記号", "意味")],
        panels=[[{"asset_index": i, "icon_alt": meanings[i], **pair(meanings[i], "meaning")} for i in rows]
                for rows in ((0, 1, 2), (3, 4, 5))],
        icon_refs=[ref for _, ref in SYMBOLS], source_ref="native-pdf/page-7/symbols", language=LANGUAGE)
    w, c = "warning", "caution"
    w1 = T("w1.band")
    first = root(callout(w1, [
        node("paragraph", T.inline("w1.i1.t")),
        node("list", [node("list_item", [text(T(f"w1.i1.l{i}"))]) for i in range(1, 6)], ordered=False),
        node("paragraph", [text(T("w1.i1.b1"))]), node("paragraph", [text(T("w1.i1.b2"))]),
        node("paragraph", T.inline("w1.i1.t2")),
        node("paragraph", [text(T("w1.i1.b3"))]), node("paragraph", [text(T("w1.i1.b4"))]),
    ], variant=w, language=LANGUAGE, source_ref="native-pdf/page-8/warning-1"))
    w2 = T("w2.band")
    c1 = T("c1.band")
    return [chapter_heading("safety.h", "native-safety"), para("safety.lead"),
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
            safety_item(c, c1, "c1.i2.t", [], "native-pdf/page-9/caution-2")]


def precautions() -> list[dict]:
    def item(*keys: str) -> dict:
        return node("list_item", [node("paragraph", [text(T(k))]) for k in keys])
    items = [item(f"prec.l{i}") for i in range(1, 14)]
    items.append(item("prec.l14.t", "prec.l14.b"))
    items.append(item("prec.l15.t", *(f"prec.l15.b{i}" for i in range(1, 6))))
    items.append(item("prec.l16.t", "prec.l16.b1", "prec.l16.b2", "prec.l16.b3"))
    return [chapter_heading("prec.h", "native-usage-precautions"), para("prec.p1"),
            root(node("list", items, ordered=False))]


def disclaimer() -> list[dict]:
    items = [node("list_item", [node("paragraph", [text(T("disc.l1"))])]),
             node("list_item", [node("paragraph", [text(T("disc.l2a"))]), node("paragraph", [text(T("disc.l2b"))])]),
             *(node("list_item", [node("paragraph", [text(T(f"disc.l{i}"))])]) for i in range(3, 7))]
    return [chapter_heading("disc.h", "native-disclaimer"), root(node("list", items, ordered=False))]


CHAPTERS = (
    ("specifications", "1. 技術仕様", specifications), ("in_the_box", "2. 同梱物", in_the_box),
    ("product_overview", "3. Jackery本体", overview), ("lcd_display", "4. LCDディスプレイ", lcd),
    ("basic_operations", "5. 基本操作", operations),
    ("charging", "6. Jackery Explorer 100 Plusの充電", charging),
    ("safety", "7. 安全上のご注意", safety), ("usage_precautions", "8. 使用上のご注意", precautions),
    ("disclaimer", "9. 免責事項", disclaimer),
)


def build() -> dict:
    chapters = [{"id": cid, "title": title, "nodes": make()} for cid, title, make in CHAPTERS]
    missing = [k for k in T.rows if k not in T.used]
    if missing:
        raise ValueError("Web transcription lines not bound: " + ", ".join(missing))
    return {"model": "JE-100A", "region": "JP", "language": LANGUAGE,
            "title": "Jackery Explorer 100 Plus 取扱説明書", "source_sha256": SOURCE_SHA256, "chapters": chapters}


def main() -> None:
    content = build()
    path = PACKAGE / "source/ja/content.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(content, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"chapters": [c["id"] for c in content["chapters"]], "lines": len(T.used)}))


if __name__ == "__main__":
    main()
