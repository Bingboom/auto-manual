"""Bind the reviewed JE-2000A US en transcription to shared Web components.

Run from the repository root:

    python manual_sources/JE-2000A/US/en/git-20261027-a8ec2be7/build_content.py

Every Web string comes from ``source/transcription.json`` by line id; this
module only decides which shared component carries each printed block, in
printed order. It writes ``source/en/content.json``, the frozen input that
``rebuild.py`` replays. ``[ICON]`` in a transcribed line is the inline LCD
glyph printed at that position; it becomes the matching native icon asset.
The circled ①–⑮ LCD legend numbers are the printed cell markers.
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
from tools.component_specs.reference_figure import reference_figure_component_spec  # noqa: E402
from tools.component_specs.spec_table import spec_table_component_spec  # noqa: E402
from tools.component_specs.warranty import warranty_section_component_spec  # noqa: E402
from tools.manual_ir.components import component_flow_node  # noqa: E402
from tools.web.composite_hashing import reference_source_fragment_sha256  # noqa: E402
from tools.web.frozen_ai_flow import callout, node, root, table, text  # noqa: E402
from tools.web.frozen_ai_table_components import _spec_carrier  # noqa: E402

LANGUAGE = "en"
CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮"
ICON = "[ICON]"
ICONS = "assets/icons/"


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
    return heading(key, level=2, anchor=anchor)


def bullets(keys: list[str]) -> dict:
    """Printed "·" bullet lists (the marker is drawn by source/geometry.css)."""
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


def callout_block(label_key: str, body_key: str, variant: str, ref: str) -> dict:
    """A printed run-in label (Tip:, Caution:, WARNING：, DANGER:) and its sentence.

    The shared HB-CALLOUT-STRIP label slot carries the label word without its
    trailing colon (the strip draws the separation), as in JE-1000D JP 「備考：」.
    """
    label = T(label_key)
    if label[-1:] not in {":", "："}:
        raise ValueError("callout label must end with its printed colon: " + label_key)
    return root(callout(label[:-1], [node("paragraph", [text(T(body_key))])],
                        variant=variant, language=LANGUAGE, source_ref=ref))


def icon(ref: str, alt: str) -> dict:
    return node("image", source=ref, alt=alt)


def with_icons(key: str, refs: list[str], alt: str, *, strong: bool = False) -> dict:
    """A printed line whose [ICON] marks are the inline LCD glyphs."""
    parts = T(key).split(ICON)
    if len(parts) != len(refs) + 1:
        raise ValueError("inline icon count differs: " + key)
    children: list[dict] = [text(parts[0])] if parts[0] else []
    for ref, after in zip(refs, parts[1:], strict=True):
        children.append(icon(ref, alt))
        if after:
            children.append(text(after))
    return root(node("paragraph", [node("strong", children)] if strong else children))


def plain_table(header: list[dict] | None, rows: list[list[dict]]) -> dict:
    """Declared plain table on the shared manual-table classes (shared_component_exceptions)."""
    parts = [node("table_head", [node("table_row", header)])] if header else []
    parts.append(node("table_body", [node("table_row", row) for row in rows]))
    return root(node("group", [node("table", parts, presentation={"html": {"attributes": {"class": "manual-table"}}})],
                     role="container",
                     presentation={"html": {"attributes": {"class": "table-wrapper docutils container"}}}))


def cell(children: list[dict], *, header: bool = False, **fields) -> dict:
    return node("table_cell", children, header=header, **fields)


def text_cell(key: str, *, header: bool = False, **fields) -> dict:
    return cell([text(T(key))], header=header, **fields)


# --- chapters -------------------------------------------------------------

def specifications() -> list[dict]:
    def group(title_key: str, rows: list[tuple[str | None, str]], anchor: str) -> dict:
        title = T(title_key)
        values = [("" if label is None else T(label), T(value)) for label, value in rows]
        spec = spec_table_component_spec(section_title=title, rows=values,
                                         source_ref=f"native-pdf/page-2/{anchor}", language=LANGUAGE)
        return component_flow_node(spec, carrier_flow=_spec_carrier(title, values), root=True)

    def r(prefix: str, count: int) -> list[tuple[str, str]]:
        return [(f"{prefix}.r{i}.l", f"{prefix}.r{i}.v") for i in range(1, count + 1)]

    return [para("head.model"), para("intro.p1"), para("intro.p2"), para("intro.p3"),
            chapter_heading("spec.h", "native-technical-specifications"),
            group("spec.g1", r("spec.g1", 5), "general-info"),
            group("spec.g2", r("spec.g2", 4), "output-ports"),
            group("spec.g3", [("spec.g3.r1.l", "spec.g3.r1.v"), ("spec.g3.r2.l", "spec.g3.r2.v1"),
                              (None, "spec.g3.r2.v2")], "input-ports"),
            group("spec.g4", r("spec.g4", 2), "environmental-operating-temperature"),
            heading("cert.h"),
            figure("assets/cert-marks.png", "cert-marks", 2, ["cert.ices"]),
            para("tm.p1"), para("tm.p2"), para("tm.p3")]


INBOX = [("box.c1", "assets/inbox-unit.png"), ("box.c2", "assets/inbox-car-cable.png"),
         ("box.c3", "assets/inbox-ac-cable.png"), ("box.c4", "assets/inbox-adaptor.png"),
         ("box.c5", "assets/inbox-guide.png")]


def package_list() -> list[dict]:
    # The shared card component numbers the cards 1–5 in place of the printed ①–⑤ markers.
    cards = [{"image_ref": ref, "label": T(key), "alt": T.rows[key]["text"]} for key, ref in INBOX]
    title = T.rows["box.h"]["text"]
    spec = inbox_component_spec(accessibility_label=title, cards=cards, tip_label="", tip_body="",
                                source_ref="native-pdf/page-3/inbox", language=LANGUAGE, require_tip=False)
    carrier = table([[node("table_cell", [node("image", source=c["image_ref"], alt=c["alt"]),
                                          node("paragraph", [text(c["label"])])], header=False) for c in cards]])
    return [chapter_heading("box.h", "native-package-list"),
            component_flow_node(spec, carrier_flow=(carrier,), root=True)]


def overview() -> list[dict]:
    front = ["fig.f.ledlight", "fig.f.ledbtn", "fig.f.usba", "fig.f.usbc", "fig.f.usbbtn", "fig.f.lcdbtn",
             "fig.f.lcd", "fig.f.car", "fig.f.carbtn", "fig.f.acout", "fig.f.acbtn"]
    return [chapter_heading("gear.h", "native-get-to-know-your-gear"), para("gear.sub"),
            figure("assets/overview-front.png", "overview-front", 4, front),
            figure("assets/overview-rear.png", "overview-rear", 4, ["fig.r.acin", "fig.r.dcin"])]


LCD_ICONS = ["lcd-01-input-power", "lcd-02-remaining-charge-time", "lcd-03-solar-charging",
             "lcd-04-ac-wall-charging", "lcd-05-car-charging", "lcd-06-low-battery",
             "lcd-07-battery-percentage", "lcd-08-output-power", "lcd-09-remaining-discharge-time",
             "lcd-10-fault-code", "lcd-11-high-temperature", "lcd-12-low-temperature",
             "lcd-13-low-power-mode", "lcd-14-ac-power", "lcd-15-battery-power-ring"]


def lcd() -> list[dict]:
    rows = []  # the printed legend has no header row
    for index, name in enumerate(LCD_ICONS):
        label = T(f"lcd.n{index + 1}")
        rows.append([cell([text(CIRCLED[index])]), cell([icon(ICONS + name + ".png", label)]),
                     cell([text(label)])])
    legend = plain_table(None, rows)
    low_power = [[text_cell(f"lpm.r{r}.c{c}") for c in (1, 2, 3)] for r in (1, 2, 3)]
    lpm = plain_table([text_cell(k, header=True) for k in ("lpm.th1", "lpm.th2", "lpm.th3")], low_power)
    return [chapter_heading("lcd.h", "native-lcd-display"),
            figure("assets/lcd-map.png", "lcd-map", 5, [], label=T.rows["lcd.h"]["text"]),
            legend,
            with_icons("lcd.bpi.t", [ICONS + "lcd-inline-battery-ring.png"], T.rows["lcd.n15"]["text"], strong=True),
            para("lcd.bpi.b"),
            with_icons("lcd.lbi.t", [ICONS + "lcd-06-low-battery.png"], T.rows["lcd.n6"]["text"], strong=True),
            para("lcd.lbi.b"),
            with_icons("lcd.lpm.t", [ICONS + "lcd-inline-low-power-mode.png"], T.rows["lcd.n13"]["text"],
                       strong=True),
            para("lcd.lpm.b"), lpm, para("lpm.on"), para("lpm.off"),
            with_icons("lcd.fc.t", [ICONS + "lcd-inline-fault-code.png"], T.rows["lcd.n10"]["text"], strong=True),
            para("lcd.fc.b")]


def operations() -> list[dict]:
    return [chapter_heading("ops.h", "native-basic-operations"), heading("ops.power.h"),
            para("ops.ac"), para("ops.usb"), para("ops.car"),
            figure("assets/operations.png", "operations", 7, ["fig.ops.car", "fig.ops.ac", "fig.ops.usb"]),
            heading("ops.lcd.h"), para("ops.lcd.on"), para("ops.lcd.off"), para("ops.aod"), para("ops.aod.off"),
            callout_block("ops.tip.l", "ops.tip", "tip", "native-pdf/page-7/tip"),
            heading("led.h"), para("led.modes"), para("led.ops")]


def charging() -> list[dict]:
    return [chapter_heading("chg.h", "native-charging"), para("chg.green"), para("chg.priority"),
            heading("chg.wall.h"), para("chg.wall"),
            figure("assets/ac-charge.png", "ac-charge", 8, ["fig.ac.charger", "fig.ac.unit"]),
            heading("solar.h"), heading("solar.conn.h", level=4), para("solar.conn"),
            heading("solar.ports.h", level=4),
            figure("assets/solar-connector.png", "solar-connector", 9, ["fig.conn.out", "fig.conn.in", "fig.conn.sw"]),
            para("solar.p1"), para("solar.p2"), para("solar.p3"),
            heading("howto.h"), para("howto.p"), para("howto.two"),
            figure("assets/solar-two.png", "solar-two", 9,
                   ["fig.two.s1", "fig.two.dc8020", "fig.two.dc7909", "fig.two.s2", "fig.two.unit"]),
            para("howto.three"),
            figure("assets/solar-three.png", "solar-three", 10, ["fig.three.s1", "fig.three.s3", "fig.three.unit"]),
            para("howto.conn"),
            heading("guide.h"), para("guide.p"),
            heading("ex1.h", level=4), figure("assets/example-1.png", "example-1", 10, ["fig.ex1.s", "fig.ex1.unit"]),
            heading("ex2.h", level=4),
            figure("assets/example-2.png", "example-2", 10,
                   ["fig.ex2.s1", "fig.ex2.u1", "fig.ex2.or", "fig.ex2.s2", "fig.ex2.u2"]),
            heading("ex3.h", level=4), figure("assets/example-3.png", "example-3", 11, ["fig.ex3.unit", "fig.ex3.s"]),
            heading("ex4.h", level=4),
            figure("assets/example-4.png", "example-4", 11, ["fig.ex4.s1", "fig.ex4.unit", "fig.ex4.s2"]),
            heading("ex5.h", level=4),
            figure("assets/example-5.png", "example-5", 11, ["fig.ex5.s1", "fig.ex5.unit", "fig.ex5.s2"]),
            callout_block("ex.caution.l", "ex.caution", "caution", "native-pdf/page-11/caution"),
            para("prohib.lead"),
            figure("assets/prohibited-solar.png", "prohibited-solar", 12,
                   [f"fig.pro.r{r}.{k}" for r in (1, 2, 3) for k in ("s1", "u", "s2")])]


def car() -> list[dict]:
    return [chapter_heading("car.h", "native-charging-in-the-car"), para("car.p1"), para("car.p2"),
            figure("assets/car-charge.png", "car-charge", 12, ["fig.car.vehicle", "fig.car.unit"]),
            heading("adp.h"), para("adp.p"),
            figure("assets/adaptor-guide.png", "adaptor-guide", 13,
                   ["fig.adp.adaptor", "fig.adp.male", "fig.adp.female", "fig.adp.unit"])]


def safety_charging() -> list[dict]:
    return [chapter_heading("spc.h", "native-safety-precautions-when-charging"), para("spc.1"), para("spc.2"),
            figure("assets/prohibited-car-solar.png", "prohibited-car-solar", 13,
                   ["fig.spc.solar", "fig.spc.unit", "fig.spc.vehicle"]),
            para("spc.3"), para("spc.4")]


def safety_using() -> list[dict]:
    return [chapter_heading("spu.h", "native-safety-precautions-when-using"), para("spu.lead"),
            *(para(f"spu.{k}") for k in ("a", "b", "c", "d", "e", "f", "g", "h2", "i"))]


def instructions() -> list[dict]:
    letters = ["a", "b", "c", "d", "e", "f", "g", "h2", "i", "j"]
    return [chapter_heading("ins.h", "native-important-safety-instructions"), heading("ins.imp"), para("ins.warn"),
            *(para(f"ins.{k}") for k in letters),
            *(para(f"ins.j{i}") for i in range(1, 6)),
            *(para(f"ins.{k}") for k in ("k", "l", "m", "n")),
            heading("save.h"), bullets([f"save.{i}" for i in range(1, 19)]),
            callout_block("save.warn.l", "save.warn", "warning", "native-pdf/page-15/warning"),
            callout_block("save.danger.l", "save.danger", "danger", "native-pdf/page-15/danger"),
            heading("chgi.h"), *(para(f"chgi.{i}") for i in (1, 2, 3)),
            heading("dis.h"), *(para(f"dis.{i}") for i in (1, 2, 3)),
            heading("mov.h"), bullets([f"mov.{i}" for i in range(1, 7)]),
            heading("maint.h"), bullets(["maint.1", "maint.2"])]


def faq() -> list[dict]:
    nodes = [chapter_heading("faq.h", "native-faq")]
    for i in range(1, 8):
        nodes.append(para(f"faq.q{i}"))
        if i == 6:
            nodes.append(with_icons("faq.a6", [ICONS + "faq-low-power-mode.png"] * 2, T.rows["lcd.n13"]["text"]))
        else:
            nodes.append(para(f"faq.a{i}"))
    return nodes


def troubleshooting() -> list[dict]:
    head = [text_cell(k, header=True) for k in ("ts.th1", "ts.th2", "ts.th3")]
    rows = []
    for code in range(10):
        types = T(f"ts.f{code}.t")
        icon_cell = [node("paragraph", [icon(f"{ICONS}ts-f{code}.png", f"F{code}"), text(" " + types)])]
        row = [cell(icon_cell), text_cell(f"ts.f{code}.s")]
        if code == 0:
            row.insert(0, text_cell("ts.err", row_span=10))
        rows.append(row)
    for key, name in (("ht", "high"), ("lt", "low")):
        label = T.rows[f"ts.{key}.t"]["text"]
        rows.append([cell([icon(f"{ICONS}ts-{name}-temperature.png", label)]), text_cell(f"ts.{key}.t"),
                     text_cell(f"ts.{key}.s")])
    return [chapter_heading("ts.h", "native-troubleshooting"), plain_table(head, rows)]


def warranty() -> list[dict]:
    def section(index: int, title_key: str, body_keys: list[str]) -> list[dict]:
        title = heading(title_key)
        blocks = [{"kind": "paragraph", "html": f"<p>{T.html(k)}</p>", "text": T.rows[k]["text"]} for k in body_keys]
        spec = warranty_section_component_spec(title=T.rows[title_key]["text"], section_index=index, blocks=blocks,
                                               source_ref=f"native-pdf/warranty/{index}", language=LANGUAGE)
        return [title, component_flow_node(spec, root=True)]

    return [chapter_heading("war.h", "native-warranty"), para("war.note"),
            *section(1, "war.lim.h", ["war.lim1", "war.lim2"]),
            *section(2, "war.per.h", ["war.per"]),
            *section(3, "war.exc.h", ["war.exc"]),
            *section(4, "war.orig.h", ["war.orig"]),
            heading("inc.h"), para("inc.c"), para("inc.w"), para("inc.ed")]


CHAPTERS = (
    ("specifications", "TECHNICAL SPECIFICATIONS", specifications), ("package_list", "PACKAGE LIST", package_list),
    ("product_overview", "GET TO KNOW YOUR GEAR", overview), ("lcd_display", "LCD DISPLAY", lcd),
    ("basic_operations", "BASIC OPERATIONS", operations),
    ("charging", "CHARGING YOUR JACKERY EXPLORER 2000 PRO", charging),
    ("car_charging", "CHARGING IN THE CAR", car),
    ("safety_charging", "SAFETY PRECAUTIONS WHEN CHARGING", safety_charging),
    ("safety_using", "SAFETY PRECAUTIONS WHEN USING", safety_using),
    ("important_safety", "INSTRUCTIONS PERTAINING TO RISK OF FIRE, ELECTRIC SHOCK, OR INJURY TO PERSONS", instructions),
    ("faq", "FAQ", faq), ("troubleshooting", "TROUBLESHOOTING", troubleshooting), ("warranty", "WARRANTY", warranty),
)


def build() -> dict:
    chapters = [{"id": cid, "title": title, "nodes": make()} for cid, title, make in CHAPTERS]
    missing = [k for k in T.rows if k not in T.used]
    if missing:
        raise ValueError("Web transcription lines not bound: " + ", ".join(missing))
    return {"model": "JE-2000A", "region": "US", "language": LANGUAGE,
            "title": "Jackery Explorer 2000 Pro User Manual",
            "source_sha256": "a8ec2be735be6483d340f2f35c7bc13a9300bf7d9499f60099ed8d5ef5cf689f",
            "chapters": chapters}


def main() -> None:
    content = build()
    path = PACKAGE / "source/en/content.json"
    path.write_text(json.dumps(content, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"chapters": [c["id"] for c in content["chapters"]], "lines": len(T.used)}))


if __name__ == "__main__":
    main()
