"""Bind the reviewed JE-1500B JP transcription to shared Web components.

Run from the repository root:

    python manual_sources/JE-1500B/JP/ja/git-20261103-f61d0d68/build_content.py

Every Web string comes from ``source/transcription.json`` by line id; this
module only decides which shared component carries each printed block, in
printed order. It writes ``source/ja/content.json``, the frozen input that
``rebuild.py`` replays. Component chrome that the shared components require
(signal table headers) follows the JE-1000D JP V2 edition and is listed in
``source/differences.md``.

The 絵表示の説明 symbol table (``PENDING_LINES``) is not bound yet: symbol
admission cannot rebuild its source reference from this PDF (see
``source/asset_recipe.json:pending_symbols``). Every other Web line must be
bound exactly once.
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
from tools.component_specs.manual_tables import lcd_icon_component_spec, symbol_signal_component_spec  # noqa: E402
from tools.component_specs.reference_figure import reference_figure_component_spec  # noqa: E402
from tools.component_specs.reference_table import reference_table_component_spec  # noqa: E402
from tools.component_specs.spec_table import spec_table_component_spec  # noqa: E402
from tools.manual_ir.components import component_flow_node  # noqa: E402
from tools.web.composite_hashing import reference_source_fragment_sha256  # noqa: E402
from tools.web.frozen_ai_flow import callout, node, root, table, text  # noqa: E402
from tools.web.frozen_ai_table_components import _spec_carrier  # noqa: E402

LANGUAGE = "ja"
SOURCE_SHA256 = "f61d0d68f37c32ceb7441d0853da40ad1087e7241a4bf925089d86f8074b0a65"
PENDING_LINES = ("symbols.h", "sym.unplug", "sym.mandatory", "sym.disassemble", "sym.wet", "sym.wethand",
                 "sym.prohibit")


class Lines:
    """Line lookup that records every id used, so coverage can be checked."""

    def __init__(self) -> None:
        source = json.loads((PACKAGE / "source/transcription.json").read_text(encoding="utf-8"))
        self.rows = {line["id"]: line for page in source["pages"] if page["web"] for line in page["lines"]}
        self.used: list[str] = []

    def __call__(self, key: str) -> str:
        if key in self.used:
            raise ValueError("transcription line bound twice: " + key)
        if key in PENDING_LINES:
            raise ValueError("pending symbol line bound: " + key)
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


def run_in_callout(keys: list[str], variant: str, ref: str) -> dict:
    """A printed run-in signal word (``ご注意：``, ``注意：``) becomes the shared callout label.

    The shared callout shows its label without the colon (as 備考： in the
    JE-1000D JP precedent); the words themselves are unchanged.
    """
    label, body = T(keys[0]).split("：", 1)
    paragraphs = [node("paragraph", [text(body)])] + [node("paragraph", [text(T(k))]) for k in keys[1:]]
    return root(callout(label, paragraphs, variant=variant, language=LANGUAGE, source_ref=ref))


def plain_table(header_keys: list[str], rows: list[list[list[dict]]]) -> dict:
    head = node("table_head", [node("table_row", [node("table_cell", [text(T(k))], header=True)
                                                  for k in header_keys])]) if header_keys else None
    body = node("table_body", [node("table_row", [node("table_cell", cell, header=False) for cell in row])
                               for row in rows])
    return root(node("group", [node("table", [head, body] if head else [body],
                                    presentation={"html": {"attributes": {"class": "manual-table"}}})],
                     role="container",
                     presentation={"html": {"attributes": {"class": "table-wrapper docutils container"}}}))


def lcd_title(key: str) -> str:
    """The printed title 「名称（[LCD]）：」: the bracketed LCD glyph is the row icon."""
    name, rest = T(key).split("（[LCD]）", 1)
    if rest not in ("：", ":"):
        raise ValueError("unexpected LCD title punctuation: " + key)
    return name


def lcd_rows(rows: list[tuple[str, str, str]], ref: str) -> dict:
    values, refs = [], []
    for index, (title_key, body_key, asset) in enumerate(rows):
        name, body = lcd_title(title_key), T(body_key)
        values.append({"name_html": escape(name), "name_text": name, "description_html": escape(body),
                       "description_text": body, "icon_alt": name, "asset_index": index})
        refs.append(asset)
    spec = lcd_icon_component_spec(accessibility_label=values[0]["name_text"], rows=values, icon_refs=refs,
                                   source_ref=ref, language=LANGUAGE, icon_locale_policy="exact", numbered=False)
    return component_flow_node(spec, root=True)


def items(entries: list[list[str]]) -> dict:
    """An unordered list; each entry is one printed bullet with its continuation lines."""
    return root(node("list", [node("list_item", [node("paragraph", T.inline(k)) for k in keys])
                              for keys in entries], ordered=False))


# --- chapters -------------------------------------------------------------

def specifications() -> list[dict]:
    rows = []
    for index in range(1, 14):
        label = T(f"spec.r{index}.l")
        keys = [k for k in T.rows if k.startswith(f"spec.r{index}.v")]
        rows.append((label, "\n".join(T(k) for k in keys)))
    title = T("spec.title")
    spec = spec_table_component_spec(section_title=title, rows=rows, source_ref="native-pdf/page-2/spec",
                                     language=LANGUAGE)
    recycle = plain_table([], [[
        [node("image", source="assets/recycle-li-ion.svg", alt=T("recycle.glyph"))],
        [node("paragraph", [node("strong", [text(T("recycle.title"))])]),
         *(node("paragraph", [text(T(k))]) for k in ("recycle.b1", "recycle.b2", "recycle.b3"))],
    ]])
    return [chapter_heading("spec.h", "native-specifications"),
            component_flow_node(spec, carrier_flow=_spec_carrier(title, rows), root=True),
            figure("qc-mark", 2, ["fig.qc"]),
            para("spec.tm"), para("spec.qc1"), para("spec.qc2"), para("spec.change"), recycle]


def overview() -> list[dict]:
    keys = ["names.acin", "names.dcin", "names.ledbtn", "names.led", "names.usba", "names.usbc", "names.qc",
            "names.usbbtn", "names.lcd", "names.dispbtn", "names.carport", "names.carbtn", "names.acout",
            "names.acbtn"]
    return [chapter_heading("names.h", "native-product-overview"), figure("overview", 3, keys)]


def lcd() -> list[dict]:
    legend_keys = [f"lcd.n{i}" for i in range(1, 16)]
    legend = reference_table_component_spec(
        variant="lcd-descriptions", label=T.rows["lcd.h"]["text"], headers=[],
        rows=[[{"html": escape(T.rows[k]["marker"]), "text": T.rows[k]["marker"]},
               {"html": escape(T(k)), "text": T.rows[k]["text"]}] for k in legend_keys],
        source_ref="native-pdf/page-3/lcd-legend", language=LANGUAGE)
    low_power = plain_table(["lpm.th1", "lpm.th2", "lpm.th3"],
                            [[[text(T(f"lpm.r{r}.c{c}"))] for c in (1, 2, 3)] for r in (1, 2, 3)])
    return [chapter_heading("lcd.h", "native-lcd-display"),
            figure("lcd-map", 3, [], label=T.rows["lcd.h"]["text"]),
            component_flow_node(legend, root=True),
            lcd_rows([("lcd.ring.t", "lcd.ring.b", "assets/lcd-battery-power.svg"),
                      ("lcd.lowbat.t", "lcd.lowbat.b", "assets/lcd-low-battery.svg"),
                      ("lcd.lpm.t", "lcd.lpm.b", "assets/lcd-low-power-mode.svg")], "native-pdf/page-4/lcd-icons"),
            low_power, para("lpm.on"), para("lpm.off"), para("freq.h"), para("freq.p"),
            lcd_rows([("lcd.fault.t", "lcd.fault.b", "assets/lcd-fault-code.svg")], "native-pdf/page-4/fault-code")]


def usage() -> list[dict]:
    return [chapter_heading("use.h", "native-usage"), heading("use.power.h"),
            *(para(k) for k in ("use.ac.h", "use.ac", "use.usb.h", "use.usb", "use.car.h", "use.car")),
            heading("use.lcd.h"), para("use.lcd"), para("use.lcd.note"),
            heading("use.led.h"), para("use.led")]


def charging() -> list[dict]:
    caution = root(callout(T("chg.box.label"), [
        node("list", [node("list_item", [text(T(k))]) for k in ("chg.box.i1", "chg.box.i2", "chg.box.i3")],
             ordered=False),
        node("paragraph", [text(T("chg.box.after"))]),
    ], variant="caution", language=LANGUAGE, source_ref="native-pdf/page-6/caution"))
    return [chapter_heading("chg.h", "native-charging"), para("chg.green"),
            lcd_rows([("chg.hot.t", "chg.hot.b", "assets/lcd-high-temperature.svg"),
                      ("chg.cold.t", "chg.cold.b", "assets/lcd-low-temperature.svg")], "native-pdf/page-6/lcd-icons"),
            caution,
            heading("chg.ac.h"), para("chg.ac"), figure("ac-charge", 6, ["fig.ac.cable", "fig.ac.unit"]),
            heading("chg.solar.h"), heading("chg.solar.h2", level=4), para("chg.solar.p1"), para("chg.solar.p2"),
            figure("solar-three", 6, ["fig.s3.panels", "fig.s3.unit"]),
            figure("solar-two-two", 7, ["fig.s22.left", "fig.s22.unit", "fig.s22.right"]),
            figure("solar-three-three", 7, ["fig.s33.left", "fig.s33.unit", "fig.s33.right"]),
            run_in_callout(["solar.caution", "solar.caution2"], "caution", "native-pdf/page-7/caution"),
            figure("solar-prohibited", 7, [f"fig.x{r}.{p}" for r in (1, 2, 3) for p in ("left", "unit", "right")]),
            heading("s80.h", level=4), para("s80.p1"), para("s80.p2"),
            figure("solar-saga80", 8, ["fig.s80.par", "fig.s80.out"]),
            heading("tj.h", level=4), para("tj.p"),
            figure("adaptor", 8, ["fig.tj.jack", "fig.tj.dc7909", "fig.tj.dc8020", "fig.tj.unit"]),
            run_in_callout(["tj.note"], "caution", "native-pdf/page-8/caution"),
            heading("car.h"), para("car.p"), figure("car-charge", 8, ["fig.car.unit"]),
            heading("chg.safe.h"), para("chg.safe1"), para("chg.safe2")]


def safety() -> list[dict]:
    def pair(value: str, key: str) -> dict:
        return {f"{key}_html": escape(value), f"{key}_text": value}

    def item(variant: str, label: str, title_key: str, body_keys: list[str], ref: str,
             list_keys: list[str] | None = None) -> dict:
        body = [node("paragraph", [node("strong", [text(T(title_key))])])]
        if list_keys:
            body.append(node("list", [node("list_item", [text(T(k))]) for k in list_keys], ordered=False))
        body += [node("paragraph", [text(T(k))]) for k in body_keys]
        return root(callout(label, body, variant=variant, language=LANGUAGE, source_ref=ref))

    signal = symbol_signal_component_spec(
        accessibility_label=T.rows["safety.pict.h"]["text"],
        headers=[pair("表示", "content"), pair("意味", "content")],
        rows=[{"label": T(f"signal.{k}.l"), "show_icon": True, **pair(T(f"signal.{k}.m"), "meaning")}
              for k in ("warn", "caut")],
        source_ref="native-pdf/page-9/signal", language=LANGUAGE)
    w1, w2, c1 = T("w1.band"), T("w2.band"), T("c1.band")
    first = root(callout(w1, [
        node("paragraph", [node("strong", [text(T("w1.i1.t"))])]),
        node("list", [node("list_item", [text(T(f"w1.i1.l{i}"))]) for i in range(1, 6)], ordered=False),
        node("paragraph", [text(T("w1.i1.b1"))]), node("paragraph", [text(T("w1.i1.b2"))]),
        node("paragraph", [node("strong", [text(T("w1.i1.t2"))])]),
        node("paragraph", [text(T("w1.i1.b3"))]), node("paragraph", [text(T("w1.i1.b4"))]),
    ], variant="warning", language=LANGUAGE, source_ref="native-pdf/page-9/warning-1"))
    return [chapter_heading("safety.h", "native-safety"), para("safety.lead"),
            heading("safety.pict.h"), para("safety.pict1"), para("safety.pict2"),
            component_flow_node(signal, root=True),
            first,
            item("warning", w1, "w1.i2.t", ["w1.i2.b"], "native-pdf/page-10/warning-2"),
            item("warning", w1, "w1.i3.t", ["w1.i3.b"], "native-pdf/page-10/warning-3"),
            item("warning", w1, "w1.i4.t", [], "native-pdf/page-10/warning-4"),
            *(item("warning", w2, f"w2.i{i}.t", [f"w2.i{i}.b"], f"native-pdf/page-10/warning-{i + 4}")
              for i in range(1, 8)),
            item("caution", c1, "c1.i1.t", ["c1.i1.b"], "native-pdf/page-10/caution-1"),
            item("caution", c1, "c1.i2.t", [], "native-pdf/page-10/caution-2",
                 list_keys=["c1.i2.l1", "c1.i2.l2", "c1.i2.l3"]),
            item("caution", c1, "c1.i3.t", ["c1.i3.b"], "native-pdf/page-10/caution-3")]


def precautions() -> list[dict]:
    entries = [[f"prec.l{i}"] for i in range(1, 9)]
    entries += [["prec.l9", "prec.l9b"], ["prec.l10", "prec.l10b"], ["prec.l11"], ["prec.l12.t", "prec.l12.b"],
                ["prec.l13.t", "prec.l13.b1", "prec.l13.b2", "prec.l13.b3"], ["prec.l14"]]
    return [chapter_heading("prec.h", "native-usage-precautions"), items(entries),
            para("prec.q"), *(para(f"prec.p{i}") for i in range(1, 8)),
            para("life.h"), items([["life.l1"], ["life.l2"], ["life.l3"]])]


def in_the_box() -> list[dict]:
    refs = ["inbox-unit", "inbox-car-cable", "inbox-ac-cable", "inbox-transjack", "inbox-manual", "inbox-warranty",
            "inbox-pouch"]
    cards = [{"image_ref": f"assets/{ref}.png", "label": T(f"box.c{i}"), "alt": T.rows[f"box.c{i}"]["text"]}
             for i, ref in enumerate(refs, start=1)]
    title = T.rows["box.h"]["text"]
    spec = inbox_component_spec(accessibility_label=title, cards=cards, tip_label="", tip_body="",
                                source_ref="native-pdf/page-13/inbox", language=LANGUAGE, require_tip=False)
    carrier = table([[node("table_cell", [node("image", source=c["image_ref"], alt=c["alt"]),
                                          node("paragraph", [text(c["label"])])], header=False) for c in cards]])
    return [chapter_heading("box.h", "native-in-the-box"), component_flow_node(spec, carrier_flow=(carrier,), root=True),
            para("box.n1")]


def disclaimer() -> list[dict]:
    return [chapter_heading("disc.h", "native-disclaimer"),
            items([["disc.l1"], ["disc.l2a", "disc.l2b"], ["disc.l3"], ["disc.l4"], ["disc.l5"],
                   ["disc.l6a", "disc.l6b"]])]


CHAPTERS = (
    ("specifications", "1.主な仕様", specifications), ("product_overview", "2.各部の名称", overview),
    ("lcd_display", "3.液晶画面", lcd), ("usage", "4.使用について", usage), ("charging", "5.充電方法", charging),
    ("safety", "6.安全上のご注意", safety), ("usage_precautions", "7.使用上のご注意", precautions),
    ("in_the_box", "8.同梱品", in_the_box), ("disclaimer", "9.免責事項", disclaimer),
)


def build() -> dict:
    chapters = [{"id": cid, "title": title, "nodes": make()} for cid, title, make in CHAPTERS]
    missing = [k for k in T.rows if k not in T.used and k not in PENDING_LINES]
    if missing:
        raise ValueError("Web transcription lines not bound: " + ", ".join(missing))
    return {"model": "JE-1500B", "region": "JP", "language": LANGUAGE,
            "title": "Jackery ポータブル電源 1500 Pro 取扱説明書",
            "source_sha256": SOURCE_SHA256, "pending_source_lines": list(PENDING_LINES),
            "chapters": chapters}


def main() -> None:
    content = build()
    path = PACKAGE / "source/ja/content.json"
    path.write_text(json.dumps(content, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"chapters": [c["id"] for c in content["chapters"]], "lines": len(T.used)}))


if __name__ == "__main__":
    main()
