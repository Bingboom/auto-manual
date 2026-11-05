"""Bind the reviewed JE-100C JP transcription to shared Web components.

Run from the repository root:

    python manual_sources/JE-100C/JP/ja/git-20261103-64dd5f53/build_content.py

Every Web string comes from ``source/transcription.json`` by line id; this
module only decides which shared component carries each printed block, in
printed order. It writes ``source/ja/content.json``, the frozen input that
``rebuild.py`` replays. ``source_manifest.json:component_map`` lists the map
and ``source/differences.md`` every deliberate layout difference. The JE-100C
US English edition supplies the component map of the shared LCD, spec and
charging blocks; the JE-1000D JP V2 edition supplies the Japanese safety map.
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
from tools.component_specs.warranty import warranty_section_component_spec  # noqa: E402
from tools.manual_ir.components import component_flow_node  # noqa: E402
from tools.web.composite_hashing import reference_source_fragment_sha256  # noqa: E402
from tools.web.frozen_ai_flow import callout, node, root, table, text  # noqa: E402

LANGUAGE = "ja"
SOURCE_SHA256 = "64dd5f5336e40426277bd217a555194461ab2b66f396e4a23308fac43d0203c3"
MARKS = {"strong": "strong", "sub": "subscript", "sup": "superscript"}


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
        """(text, mark) runs: printed bold, subscript and superscript spans in order."""
        row = self.rows[key]
        marks = [(span, kind) for kind in MARKS for span in row.get(kind, [])]
        runs: list[tuple[str, str | None]] = [(self(key), None)]
        for span, kind in marks:
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

    def html(self, key: str) -> str:
        tags = {"strong": "strong", "sub": "sub", "sup": "sup"}
        return "".join(escape(value) if mark is None else f"<{tags[mark]}>{escape(value)}</{tags[mark]}>"
                       for value, mark in self.spans(key))


T = Lines()


def para(key: str) -> dict:
    return root(node("paragraph", T.inline(key)))


def strong_para(key: str) -> dict:
    return root(node("paragraph", [node("strong", [text(T(key))])]))


def heading(key: str, level: int = 3, anchor: str | None = None) -> dict:
    return root(node("heading", [text(T(key))], level=level, **({"anchor": anchor} if anchor else {})))


def chapter(key: str, anchor: str) -> dict:
    return heading(key, level=2, anchor=anchor)


def items(keys: list[str]) -> dict:
    return node("list", [node("list_item", [node("paragraph", T.inline(k))]) for k in keys], ordered=False)


def bullets(keys: list[str]) -> dict:
    return root(items(keys))


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


def callout_items(label_key: str, item_keys: list[str], variant: str, ref: str) -> dict:
    return root(callout(T(label_key), [items(item_keys)], variant=variant, language=LANGUAGE, source_ref=ref))


def callout_text(label_key: str, body_keys: list[str], variant: str, ref: str) -> dict:
    body = [node("paragraph", T.inline(k)) for k in body_keys]
    return root(callout(T(label_key), body, variant=variant, language=LANGUAGE, source_ref=ref))


def safety_item(variant: str, label: str, body: list[dict], ref: str) -> dict:
    return root(callout(label, body, variant=variant, language=LANGUAGE, source_ref=ref))


def bold(key: str) -> dict:
    return node("paragraph", [node("strong", [text(T(key))])])


def plain(key: str) -> dict:
    return node("paragraph", T.inline(key))


def pair(value: str, key: str) -> dict:
    return {f"{key}_html": escape(value), f"{key}_text": value}


def lcd_table(rows: list[tuple[str, list[str], str]], ref: str, numbered: bool, label: str,
              list_keys: tuple[str, ...] = ()) -> dict:
    """Printed LCD rows: icon, bold name, description lines (print breaks kept as <br/>)."""
    values, refs = [], []
    for index, (name_key, body_keys, asset) in enumerate(rows):
        name = T(name_key)
        html_lines, text_lines, entries = [], [], []
        for key in body_keys:
            target = entries if key in list_keys else html_lines
            target.append(T.html(key))
            text_lines.append(T.rows[key]["text"])
        description_html = "<br/>".join(html_lines)
        if entries:
            description_html += "<ul>" + "".join(f"<li>{entry}</li>" for entry in entries) + "</ul>"
        row = {**pair(name, "name"), "description_html": description_html,
               "description_text": " ".join(text_lines), "icon_alt": name, "asset_index": index}
        if numbered:
            row.update(pair(str(index + 1), "number"))
        values.append(row)
        refs.append(asset)
    spec = lcd_icon_component_spec(accessibility_label=label, rows=values, icon_refs=refs, source_ref=ref,
                                   language=LANGUAGE, icon_locale_policy="exact", numbered=numbered)
    return component_flow_node(spec, root=True)


def spec_carrier(spec) -> list[dict]:
    slot = lambda role: spec.slot(role).content  # noqa: E731
    title = node("heading", [node("inline_group", [text(slot("section_title"))],
                                  presentation={"html": {"attributes": {"class": "hb-spec-section-text"}}})],
                 level=2, presentation={"html": {"attributes": {"class": "hb-spec-section hb-spec-group"}}})
    rows = [[node("table_cell", [text(r["label"] if i == 0 else "")], header=True),
             node("table_cell", [text(v["text"])], header=False)]
            for r in slot("rows") for i, v in enumerate(r["values"])]
    return [title, table(rows)]


def spec_block(title_key: str, rows: list[tuple[str, list[str]]], ref: str) -> dict:
    """One printed ● spec table; a multi-line value continues under the same label."""
    title = T(title_key)
    flat = []
    for label_key, value_keys in rows:
        label = T(label_key)
        flat += [(label if i == 0 else "", T(k)) for i, k in enumerate(value_keys)]
    spec = spec_table_component_spec(section_title=title, rows=flat, source_ref=ref, language=LANGUAGE)
    return component_flow_node(spec, carrier_flow=spec_carrier(spec), root=True)


# --- chapters -------------------------------------------------------------

SYMBOLS = [(("sym.warning",), "assets/symbol-01.svg"), (("sym.manual",), "assets/symbol-02.svg"),
           (("sym.fire",), "assets/symbol-03.svg"), (("sym.children",), "assets/symbol-04.svg"),
           (("sym.dismantle",), "assets/symbol-05.svg"), (("sym.wethand",), "assets/symbol-06.svg"),
           (("sym.mandatory",), "assets/symbol-07.svg"),
           (("sym.liion.t", "sym.liion.b1", "sym.liion.b2", "sym.liion.b3"), "assets/symbol-08.svg"),
           (("sym.weee.b1", "sym.weee.b2", "sym.weee.b3"), "assets/symbol-09.svg"),
           (("sym.wet",), "assets/symbol-10.svg"), (("sym.prohibit",), "assets/symbol-11.svg")]


def safety() -> list[dict]:
    signal = symbol_signal_component_spec(
        accessibility_label=T.rows["safety.pict.h"]["text"],
        headers=[pair("表示", "content"), pair("意味", "content")],
        rows=[{"label": T(f"signal.{k}.l"), "show_icon": True, **pair(T(f"signal.{k}.m"), "meaning")}
              for k in ("warn", "caut", "expl", "hint")],
        source_ref="native-pdf/page-2/signal", language=LANGUAGE)
    meanings = []
    for keys, _ in SYMBOLS:
        values = [T(k) for k in keys]
        meanings.append({"meaning_html": "<br/>".join(escape(v) for v in values), "meaning_text": "".join(values),
                         "icon_alt": values[0]})
    symbols = symbol_icon_component_spec(
        accessibility_label=T.rows["symbols.h"]["text"],
        headers=[pair(v, "content") for v in ("記号", "意味", "記号", "意味")],
        panels=[[{"asset_index": i, **meanings[i]} for i in rows] for rows in (range(0, 7), range(7, 11))],
        icon_refs=[ref for _, ref in SYMBOLS], source_ref="native-pdf/page-2/symbols", language=LANGUAGE)
    w, c = "warning", "caution"
    w1, w2, c1 = T("w1.band"), T("w2.band"), T("c1.band")
    first = [plain("w2.i1.lead"), items(["w2.i1.l1", "w2.i1.l2", "w2.i1.l3", "w2.i1.l4"]), plain("w2.i1.b"),
             bold("w2.i1.t2"), plain("w2.i1.b2"), plain("w2.i1.b3")]
    return [chapter("safety.h", "native-safety"), strong_para("safety.lead"),
            heading("safety.pict.h"), para("safety.pict1"), para("safety.pict2"),
            component_flow_node(signal, root=True),
            heading("symbols.h"), component_flow_node(symbols, root=True),
            *(safety_item(w, w1, [bold(f"w1.i{i}.t"), plain(f"w1.i{i}.b")], f"native-pdf/page-3/warning-{i}")
              for i in range(1, 9)),
            safety_item(w, w2, first, "native-pdf/page-3/warning-9"),
            safety_item(w, w2, [bold("w2.i2.t"), plain("w2.i2.b")], "native-pdf/page-3/warning-10"),
            safety_item(w, w2, [bold("w2.i3.t"), plain("w2.i3.b")], "native-pdf/page-3/warning-11"),
            safety_item(w, w2, [bold("w2.i4.t")], "native-pdf/page-3/warning-12"),
            safety_item(c, c1, [bold("c1.i1.t"), plain("c1.i1.b")], "native-pdf/page-4/caution-1"),
            safety_item(c, c1, [bold("c1.i2.t"), items(["c1.i2.l1", "c1.i2.l2", "c1.i2.l3"])],
                        "native-pdf/page-4/caution-2"),
            safety_item(c, c1, [bold("c1.i3.t"), plain("c1.i3.b")], "native-pdf/page-4/caution-3"),
            safety_item(c, c1, [bold("c1.i4.t")], "native-pdf/page-4/caution-4")]


def precautions() -> list[dict]:
    temperature = node("list", [
        node("list_item", [plain("prec.io.l1")]),
        node("list_item", [plain("prec.io.l2"), items(["prec.io.l2a", "prec.io.l2b"])]),
        node("list_item", [plain("prec.io.l3")])], ordered=False)
    return [chapter("prec.h", "native-usage-precautions"),
            para("prec.p1"), para("prec.p2"), para("prec.p3"),
            callout_text("prec.box.l", ["prec.box.b"], "caution", "native-pdf/page-4/caution"),
            panel([bold("prec.feed.h"), plain("prec.feed.p"), items(["prec.feed.l1", "prec.feed.l2"])]),
            panel([bold("prec.env.h"), items([f"prec.env.l{i}" for i in range(1, 5)])]),
            panel([bold("prec.conn.h"), items(["prec.conn.l1", "prec.conn.l2"])]),
            panel([bold("prec.care.h"), items(["prec.care.l1", "prec.care.l2", "prec.care.l3"])]),
            panel([bold("prec.io.h"), temperature])]


def disclaimer() -> list[dict]:
    return [chapter("disc.h", "native-disclaimer"), panel([items([f"disc.l{i}" for i in range(1, 6)])])]


def in_the_box() -> list[dict]:
    cards = [{"image_ref": ref, "label": T(key), "alt": T.rows[key]["text"]}
             for key, ref in (("box.c1", "assets/inbox_unit.png"), ("box.c2", "assets/inbox_cable.png"),
                              ("box.c3", "assets/inbox_manual.png"))]
    title = T.rows["box.h"]["text"]
    spec = inbox_component_spec(accessibility_label=title, cards=cards, tip_label="", tip_body="",
                                source_ref="native-pdf/page-6/inbox", language=LANGUAGE, require_tip=False,
                                variant="responsive-card-grid")
    carrier = table([[node("table_cell", [node("image", source=c["image_ref"], alt=c["alt"]),
                                          node("paragraph", [text(c["label"])])], header=False) for c in cards]])
    return [chapter("box.h", "native-in-the-box"), component_flow_node(spec, carrier_flow=(carrier,), root=True),
            panel([plain(f"box.n{i}") for i in range(1, 5)]), strong_para("box.change")]


def overview() -> list[dict]:
    keys = ["names.handle", "names.lcd", "names.c1", "names.c1.in", "names.c1.out", "names.a", "names.a.v",
            "names.display", "names.c2", "names.c2.v"]
    return [chapter("ov.h", "native-product-overview"), heading("ov.sub"),
            figure("assets/overview.png", "overview", 6, keys), para("ov.strap")]


def lcd() -> list[dict]:
    a = "assets/shared-lcd/"
    interface1 = [("lcd.i1.n", ["lcd.i1.d"], a + "lcd_input.png"),
                  ("lcd.i2.n", ["lcd.i2.d"], a + "lcd_charge_time.png"),
                  ("lcd.i3.n", ["lcd.i3.d1", "lcd.i3.d2"], a + "lcd_steady.png"),
                  ("lcd.i4.n", ["lcd.i4.d1", "lcd.i4.d2"], a + "lcd_thermal.png"),
                  ("lcd.i5.n", ["lcd.i5.d1", "lcd.i5.d2"], a + "lcd_energy.png"),
                  ("lcd.i6.n", ["lcd.i6.d"], a + "lcd_ring.png"),
                  ("lcd.i7.n", ["lcd.i7.d1", "lcd.i7.d2", "lcd.i7.d3"], a + "lcd_low_battery.png"),
                  ("lcd.i8.n", ["lcd.i8.d"], a + "lcd_percentage.png"),
                  ("lcd.i9.n", ["lcd.i9.d"], a + "lcd_discharge_time.png"),
                  ("lcd.i10.n", ["lcd.i10.d"], a + "lcd_output.png")]
    states = [("lcd.f.n", ["lcd.f.d"], a + "lcd_fault.png"),
              ("lcd.ht.n", ["lcd.ht.d"], a + "lcd_high_temperature.png"),
              ("lcd.lt.n", ["lcd.lt.d"], a + "lcd_low_temperature.png")]
    interface2 = [("lcd.p1.n", ["lcd.p1.d"], a + "lcd_discharging.png"),
                  ("lcd.p2.n", ["lcd.p2.d"], a + "lcd_charging.png"),
                  ("lcd.p3.n", ["lcd.p3.d"], a + "lcd_watts.png")]
    interface3 = [("lcd.h1.n", ["lcd.h1.d", "lcd.h1.l1", "lcd.h1.l2", "lcd.h1.l3"], a + "lcd_health.png"),
                  ("lcd.h2.n", ["lcd.h2.d"], a + "lcd_temperature.png")]
    if1, if2, if3 = (T.rows[k]["text"] for k in ("lcd.if1", "lcd.if2", "lcd.if3"))
    return [chapter("lcd.h", "native-lcd-display"),
            heading("lcd.if1"), figure("assets/lcd_interface_1.png", "lcd-interface-1", 7, [], label=if1),
            lcd_table(interface1, "native-pdf/page-7/interface-1", True, if1),
            lcd_table(states, "native-pdf/page-8/interface-1-states", False, if1),
            heading("lcd.if2"), figure("assets/lcd_interface_2.png", "lcd-interface-2", 8, [], label=if2),
            lcd_table(interface2, "native-pdf/page-8/interface-2", True, if2),
            heading("lcd.if3"), figure("assets/lcd_interface_3.png", "lcd-interface-3", 8, [], label=if3),
            lcd_table(interface3, "native-pdf/page-9/interface-3", True, if3,
                      list_keys=("lcd.h1.l1", "lcd.h1.l2", "lcd.h1.l3"))]


def operations() -> list[dict]:
    headers = [{"html": escape(T(k)), "text": T.rows[k]["text"]} for k in ("op.lcd.th1", "op.lcd.th2")]
    rows = [[{"html": escape(T(f"op.lcd.r{i}.f")), "text": T.rows[f"op.lcd.r{i}.f"]["text"]},
             {"html": escape(T(f"op.lcd.r{i}.d")), "text": T.rows[f"op.lcd.r{i}.d"]["text"]}] for i in range(1, 6)]
    screen = reference_table_component_spec(variant="lcd-actions-compact", label=T.rows["op.lcd.h"]["text"],
                                            headers=headers, rows=rows, source_ref="native-pdf/page-11/lcd-screen",
                                            language=LANGUAGE)
    return [chapter("op.h", "native-operations"),
            heading("op.out.h"), para("op.out.l1"),
            figure("assets/operation-output.png", "operation-output", 10, [], label=T.rows["op.out.h"]["text"]),
            callout_items("op.caution.l", ["op.caution.i1", "op.caution.i2", "op.caution.i3"], "caution",
                          "native-pdf/page-10/caution"),
            heading("op.eco.h"), para("op.eco.p1"), para("op.eco.p2"), para("op.eco.p3"),
            figure("assets/operation-energy.png", "operation-energy", 10, ["fig.eco.press"]),
            callout_text("op.eco.note.l", ["op.eco.note.b"], "caution", "native-pdf/page-10/note"),
            heading("op.lcd.h"),
            figure("assets/operation-lcd.png", "operation-lcd", 11, [], label=T.rows["op.lcd.h"]["text"]),
            component_flow_node(screen, root=True)]


def charging() -> list[dict]:
    return [chapter("chg.h", "native-charging"),
            callout_items("chg.caution.l", [f"chg.caution.i{i}" for i in range(1, 6)], "caution",
                          "native-pdf/page-11/caution"),
            heading("chg.usbc.h"),
            figure("assets/charging_ac.png", "charging-usbc", 12, [], label=T.rows["chg.usbc.h"]["text"]),
            para("chg.usbc.sold"),
            heading("chg.solar.h"), strong_para("chg.solar.lead"),
            figure("assets/charging_solar.png", "charging-solar", 12, ["fig.solar.panel"]),
            para("chg.solar.sold"), para("chg.solar.p1"), para("chg.solar.p2"),
            callout_text("chg.solar.note.l", ["chg.solar.note.b"], "caution", "native-pdf/page-12/caution"),
            heading("chg.car.h"), para("chg.car.lead"), para("chg.car.p"),
            bullets([f"chg.car.l{i}" for i in range(1, 6)]),
            figure("assets/charging_car.png", "charging-car", 13, ["fig.car.vehicle"]),
            para("chg.car.sold")]


def specifications() -> list[dict]:
    g = "spec.gen.r"
    return [chapter("spec.h", "native-specifications"),
            spec_block("spec.gen.h", [(f"{g}{i}.l", [f"{g}{i}.v"]) for i in range(1, 7)], "native-pdf/page-14/general"),
            spec_block("spec.in.h", [("spec.in.r1.l", ["spec.in.r1.v1", "spec.in.r1.v2", "spec.in.r1.v3"])],
                       "native-pdf/page-14/input"),
            spec_block("spec.out.h", [(f"spec.out.r{i}.l", [f"spec.out.r{i}.v"]) for i in (1, 2)],
                       "native-pdf/page-14/output"),
            spec_block("spec.tot.h", [(f"spec.tot.r{i}.l", [f"spec.tot.r{i}.v"]) for i in (1, 2, 3)],
                       "native-pdf/page-14/total"),
            spec_block("spec.env.h", [(f"spec.env.r{i}.l", [f"spec.env.r{i}.v"]) for i in (1, 2, 3)],
                       "native-pdf/page-14/environment"),
            para("spec.tm")]


def warranty() -> list[dict]:
    def section(index: int, title_key: str, blocks: list[dict]) -> list[dict]:
        # The shared card draws the body; its printed title pill is the heading before it.
        title = heading(title_key)
        spec = warranty_section_component_spec(title=T.rows[title_key]["text"], section_index=index, blocks=blocks,
                                               source_ref=f"native-pdf/page-15/warranty-{index}", language=LANGUAGE)
        return [title, component_flow_node(spec, root=True)]

    def p(*keys: str) -> dict:
        texts = [T.rows[k]["text"] for k in keys]
        html = "<br/>".join(T.html(k) for k in keys)
        return {"kind": "paragraph", "html": f"<p>{html}</p>", "text": "".join(texts)}

    def ul(*keys: str) -> dict:
        entries = [T(k) for k in keys]
        return {"kind": "list", "items": entries,
                "html": "<ul>" + "".join(f"<li>{escape(i)}</li>" for i in entries) + "</ul>"}

    return [chapter("war.h", "native-warranty"),
            *section(1, "war.contact.h", [p("war.contact.p"), p("war.contact.tel", "war.contact.mail")]),
            *section(2, "war.service.h", [ul("war.service.l1", "war.service.l2")]),
            panel([plain(k) for k in ("back.web", "back.mail", "back.tel")])]


CHAPTERS = (
    ("safety", "安全上のご注意", safety), ("usage_precautions", "使用上のご注意", precautions),
    ("disclaimer", "免責事項", disclaimer), ("in_the_box", "同梱品", in_the_box),
    ("product_overview", "各部の名称", overview), ("lcd_display", "液晶画面", lcd),
    ("operations", "使い方", operations), ("charging", "充電方法", charging),
    ("specifications", "主な仕様", specifications), ("warranty", "保証について", warranty),
)


def build() -> dict:
    chapters = [{"id": cid, "title": title, "nodes": make()} for cid, title, make in CHAPTERS]
    missing = [k for k in T.rows if k not in T.used]
    if missing:
        raise ValueError("Web transcription lines not bound: " + ", ".join(missing))
    return {"model": "JE-100C", "region": "JP", "language": LANGUAGE,
            "title": "Jackery Explorer 100D 取扱説明書", "source_sha256": SOURCE_SHA256, "chapters": chapters}


def main() -> None:
    content = build()
    path = PACKAGE / "source/ja/content.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(content, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"chapters": [c["id"] for c in content["chapters"]], "lines": len(T.used)}))


if __name__ == "__main__":
    main()
