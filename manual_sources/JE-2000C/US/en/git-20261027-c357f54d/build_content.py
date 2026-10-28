"""Bind the reviewed JE-2000C US/en transcription to shared Web components.

Run from the repository root:

    python manual_sources/JE-2000C/US/en/git-20261027-c357f54d/build_content.py

Every Web string comes from ``source/transcription.json`` by line id; this
module only decides which shared component carries each printed block, in
printed order. It writes ``source/en/content.json``, the frozen input that
``rebuild.py`` replays. Layout decisions are listed in ``source/differences.md``.
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

from tools.component_specs.fcc import fcc_component_spec  # noqa: E402
from tools.component_specs.inbox import inbox_component_spec  # noqa: E402
from tools.component_specs.manual_tables import lcd_icon_component_spec  # noqa: E402
from tools.component_specs.reference_figure import reference_figure_component_spec  # noqa: E402
from tools.component_specs.reference_table import reference_table_component_spec  # noqa: E402
from tools.component_specs.spec_table import spec_table_component_spec  # noqa: E402
from tools.component_specs.warranty import warranty_section_component_spec  # noqa: E402
from tools.manual_ir.components import component_flow_node  # noqa: E402
from tools.web.composite_hashing import reference_source_fragment_sha256  # noqa: E402
from tools.web.frozen_ai_flow import callout, node, root, table, text  # noqa: E402
from tools.web.frozen_ai_table_components import _spec_carrier  # noqa: E402

LANGUAGE = "en"
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


def signal_callout(key: str, variant: str, ref: str) -> dict:
    """A printed bold signal word and its sentence: the word is the callout label."""
    label, body = T(key).split(":", 1)
    return root(callout(label.strip(), [node("paragraph", [text(body.strip())])],
                        variant=variant, language=LANGUAGE, source_ref=ref))


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


# --- chapters -------------------------------------------------------------

SPEC_GROUPS = (("spec.g1", 6), ("spec.g2", 8), ("spec.g3", 3), ("spec.g4", 2))


def specifications() -> list[dict]:
    nodes = [para("pre.p1"), para("pre.p2"), para("pre.p3"),
             chapter_heading("spec.h", "native-technical-specifications")]
    for group, count in SPEC_GROUPS:
        title = T(f"{group}.h")
        rows: list[tuple[str, str]] = []
        for index in range(1, count + 1):
            label = T(f"{group}.r{index}.l")
            if f"{group}.r{index}.v" in T.rows:
                rows.append((label, T(f"{group}.r{index}.v")))
            else:
                values = [T(k) for k in T.rows if k.startswith(f"{group}.r{index}.v")]
                rows += [(label, values[0]), *(("", v) for v in values[1:])]
        spec = spec_table_component_spec(section_title=title, rows=rows,
                                         source_ref=f"native-pdf/page-2/{group}", language=LANGUAGE)
        nodes.append(component_flow_node(spec, carrier_flow=_spec_carrier(title, rows), root=True))
    return [*nodes, heading("cert.h"),
            figure("assets/certifications.png", "certifications", 2, [],
                   label="FCC / BC / Qualcomm quick charge 3.0 / WEEE"),
            para("cert.fn1"), para("cert.fn2"), para("fcc.mod")]


def package_list() -> list[dict]:
    refs = ("assets/inbox-unit.png", "assets/inbox-car-cable.png", "assets/inbox-ac-cable.png",
            "assets/inbox-adaptor.png", "assets/inbox-manual.png", "assets/inbox-bag.png")
    title = T.rows["box.h"]["text"]
    heading_node = chapter_heading("box.h", "native-package-list")
    cards = []
    for index, ref in enumerate(refs, start=1):
        label = T(f"box.c{index}")  # the shared card draws the printed ①–⑥ badge
        cards.append({"image_ref": ref, "label": label, "alt": label})
    spec = inbox_component_spec(accessibility_label=title, cards=cards, tip_label="", tip_body="",
                                source_ref="native-pdf/page-3/package-list", language=LANGUAGE, require_tip=False)
    carrier = table([[node("table_cell", [node("image", source=c["image_ref"], alt=c["alt"]),
                                          node("paragraph", [text(c["label"])])], header=False) for c in cards]])
    return [heading_node, component_flow_node(spec, carrier_flow=(carrier,), root=True)]


def gear() -> list[dict]:
    front = ["gear.f.power", "gear.f.car", "gear.f.usba", "gear.f.usbc", "gear.f.dcbtn", "gear.f.ac1",
             "gear.f.ac2", "gear.f.acbtn"]
    rear = ["gear.r.handle", "gear.r.handle.note", "gear.r.acexp", "gear.r.acreset", "gear.r.acin",
            "gear.r.dcin", "gear.r.dcexp"]
    return [chapter_heading("gear.h", "native-get-to-know-your-gear"), heading("gear.h2"),
            figure("assets/overview-front.png", "overview-front", 3, front),
            figure("assets/overview-rear.png", "overview-rear", 3, rear)]


def lcd() -> list[dict]:
    legend = reference_table_component_spec(
        variant="lcd-descriptions", label=T.rows["lcd.h"]["text"], headers=[],
        rows=[[{"html": CIRCLED[i], "text": CIRCLED[i]},
               {"html": escape(T(f"lcd.n{i + 1}")), "text": T.rows[f"lcd.n{i + 1}"]["text"]}]
              for i in range(21)],
        source_ref="native-pdf/page-4/lcd-legend", language=LANGUAGE)
    head = node("table_head", [node("table_row", [node("table_cell", [text(T(k))], header=True)
                                                  for k in ("eco.th1", "eco.th2", "eco.th3")])])
    rows = []
    for r in (1, 2, 3):
        cells = [node("table_cell", [text(T(f"eco.r{r}.c1"))], header=False),
                 node("table_cell", [text(T(f"eco.r{r}.c2"))], header=False)]
        if r == 1:
            cells.append(node("table_cell", [text(T("eco.all"))], header=False, row_span=3))
        rows.append(node("table_row", cells))
    eco = root(node("group", [node("table", [head, node("table_body", rows)],
                                   presentation={"html": {"attributes": {"class": "manual-table"}}})],
                    role="container",
                    presentation={"html": {"attributes": {"class": "table-wrapper docutils container"}}}))
    return [chapter_heading("lcd.h", "native-lcd-display"),
            figure("assets/lcd-map.png", "lcd-map", 4, [], label=T.rows["lcd.h"]["text"]),
            component_flow_node(legend, root=True),
            para("lcd.bsm"), para("lcd.qcm"),
            lcd_rows([("lcd.d1.t", "lcd.d1.b", "assets/lcd-battery-power.png"),
                      ("lcd.d2.t", "lcd.d2.b", "assets/lcd-low-battery.png"),
                      ("lcd.d3.t", "lcd.d3.b", "assets/lcd-energy-saving.png")], "native-pdf/page-4/lcd-icons"),
            eco, strong("eco.off.h"), para("eco.off"), strong("eco.on.h"), para("eco.on"),
            lcd_rows([("lcd.d4.t", "lcd.d4.b", "assets/lcd-fault-code.png"),
                      ("lcd.d5.t", "lcd.d5.b", "assets/lcd-high-temperature.png"),
                      ("lcd.d6.t", "lcd.d6.b", "assets/lcd-low-temperature.png"),
                      ("lcd.d7.t", "lcd.d7.b", "assets/lcd-ac-expansion.png")], "native-pdf/page-5/lcd-icons")]


def operations() -> list[dict]:
    return [chapter_heading("ops.h", "native-basic-operations"), heading("ops.h2"),
            para("ops.main"), para("ops.ac"), para("ops.usb"),
            heading("ops.lcd.h"), para("ops.lcd"), para("ops.aod.on"), para("ops.aod.off"), para("ops.aod.tip"),
            para("ops.acout.reset"), para("ops.acin.reset"), strong("ops.eps.h"), para("ops.eps")]


def battery_pack() -> list[dict]:
    return [chapter_heading("pack.h", "native-battery-pack"), para("pack.p"), heading("pack.safe.h"),
            para("pack.safe1"), para("pack.safe2")]


def app_connection() -> list[dict]:
    return [chapter_heading("app.h", "native-app-connection"), para("app.p")]


def charging() -> list[dict]:
    return [chapter_heading("chg.h", "native-charging"), para("chg.p1"), para("chg.p2"),
            heading("chg.wall.h"), para("chg.wall"),
            figure("assets/wall-charge.png", "wall-charge", 7, ["fig.wall.unit", "fig.wall.cable"]),
            heading("chg.solar.h"), heading("chg.solar.h2", level=4), para("chg.solar"),
            figure("assets/solar-3.png", "solar-3", 7, ["fig.s3.unit", "fig.s3.panels"]),
            figure("assets/solar-2-2.png", "solar-2-2", 7, ["fig.s22.left", "fig.s22.unit", "fig.s22.right"]),
            figure("assets/solar-3-3.png", "solar-3-3", 8, ["fig.s33.unit", "fig.s33.left", "fig.s33.right"]),
            para("chg.solar.caution"), para("chg.prohibit.h"),
            figure("assets/solar-prohibited.png", "solar-prohibited", 8,
                   [f"fig.x{i}.{k}" for i in (1, 2, 3) for k in ("left", "unit", "right")]),
            heading("chg.s80.h", level=4), para("chg.s80.p1"), para("chg.s80.p2"),
            figure("assets/solar-80.png", "solar-80", 9, ["fig.s80.out", "fig.s80.par"]),
            para("chg.s80.tip"),
            heading("chg.adp.h", level=4), para("chg.adp"),
            figure("assets/solar-adaptor.png", "solar-adaptor", 9,
                   ["fig.adp.female", "fig.adp.adaptor", "fig.adp.male", "fig.adp.unit"]),
            heading("car.h"), para("car.p1"), para("car.p2"),
            figure("assets/car-charge.png", "car-charge", 10, ["fig.car.unit", "fig.car.vehicle"]),
            heading("safe.chg.h"), para("safe.chg1"), para("safe.chg2"),
            figure("assets/car-solar-prohibited.png", "car-solar-prohibited", 10,
                   ["fig.xcar.solar", "fig.xcar.unit", "fig.xcar.vehicle"]),
            para("safe.chg3"), para("safe.chg4")]


def safety() -> list[dict]:
    letters = ["isi.a", "isi.b", "isi.c", "isi.d", "isi.e", "isi.f", "isi.g", "isi.h1", "isi.i", "isi.j",
               "isi.j1", "isi.j2", "isi.j3", "isi.j4", "isi.j5", "isi.k", "isi.l", "isi.m", "isi.n"]
    note = T("fcc.note").split(":", 1)[1].strip()
    measures = [T(f"fcc.l{i}") for i in range(1, 5)]
    fcc = fcc_component_spec(
        accessibility_label="FCC", opening_copy=(),
        left_blocks=[{"kind": "paragraph", "label": "NOTE:", "text": note}],
        right_blocks=[{"kind": "list", "items": measures}],
        source_ref="native-pdf/page-12/fcc", language=LANGUAGE, mark_asset_ref="assets/fcc-mark.svg",
        metadata={"physical_page": 12, "list_marker_printed": "--"})
    fcc_carrier = (root(node("paragraph", [node("strong", [text("NOTE:")]), text(" " + note)])),
                   root(node("list", [node("list_item", [node("paragraph", [text(m)])]) for m in measures],
                             ordered=False)))
    return [chapter_heading("isi.h", "native-safety-instructions"), heading("isi.h2"), para("isi.lead"),
            *(para(k) for k in letters),
            heading("op.h"), bullets([f"op.{i}" for i in range(1, 18)]),
            signal_callout("op.warning", "warning", "native-pdf/page-12/warning"),
            signal_callout("op.danger", "danger", "native-pdf/page-12/danger"),
            heading("mv.h"), bullets([f"mv.{i}" for i in range(1, 7)]),
            heading("mt.h"), para("mt.p"),
            component_flow_node(fcc, carrier_flow=fcc_carrier, root=True)]


def warranty() -> list[dict]:
    def section(index: int, title_key: str, keys: list[str]) -> list[dict]:
        title = heading(title_key)
        blocks = [{"kind": "paragraph", "html": f"<p>{escape(T.rows[k]['text'])}</p>",
                   "text": T(k)} for k in keys]
        spec = warranty_section_component_spec(title=T.rows[title_key]["text"], section_index=index, blocks=blocks,
                                               source_ref=f"native-pdf/warranty/{index}", language=LANGUAGE)
        return [title, component_flow_node(spec, root=True)]

    return [chapter_heading("war.h", "native-warranty"), para("war.note"),
            *section(1, "war.lim.h", ["war.lim1", "war.lim2"]),
            *section(2, "war.per.h", ["war.per1", "war.per2"]),
            *section(3, "war.ex.h", ["war.ex"]),
            *section(4, "war.orig.h", ["war.orig"]),
            *section(5, "war.excl.h", ["war.excl.lead", "war.excl1", "war.excl2", "war.excl3", "war.excl4"]),
            heading("app.dl"),
            figure("assets/app-store.png", "app-store", 13, [], label="App Store / Google Play")]


CHAPTERS = (
    ("technical_specifications", "TECHNICAL SPECIFICATIONS", specifications),
    ("package_list", "PACKAGE LIST", package_list),
    ("get_to_know_your_gear", "GET TO KNOW YOUR GEAR", gear),
    ("lcd_display", "LCD DISPLAY", lcd),
    ("basic_operations", "BASIC OPERATIONS", operations),
    ("battery_pack", "USE WITH BATTERY PACK (SOLD SEPARATELY)", battery_pack),
    ("app_connection", "APP CONNECTION", app_connection),
    ("charging", "CHARGING YOUR JACKERY EXPLORER 2000 PLUS", charging),
    ("safety_instructions", "INSTRUCTIONS PERTAINING TO RISK OF FIRE, ELECTRIC SHOCK, OR INJURY TO PERSONS", safety),
    ("warranty", "WARRANTY", warranty),
)


def build() -> dict:
    chapters = [{"id": cid, "title": title, "nodes": make()} for cid, title, make in CHAPTERS]
    missing = [k for k in T.rows if k not in T.used]
    if missing:
        raise ValueError("Web transcription lines not bound: " + ", ".join(missing))
    return {"model": "JE-2000C", "region": "US", "language": LANGUAGE,
            "title": "Jackery Explorer 2000 Plus · JE-2000C",
            "source_sha256": "c357f54dfed27d11d72a2a4893e485450a49c1b562e21f0f272708857f1510ab",
            "chapters": chapters}


def main() -> None:
    content = build()
    path = PACKAGE / "source/en/content.json"
    path.write_text(json.dumps(content, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"chapters": [c["id"] for c in content["chapters"]], "lines": len(T.used)}))


if __name__ == "__main__":
    main()
