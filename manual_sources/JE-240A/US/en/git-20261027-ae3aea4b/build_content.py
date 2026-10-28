"""Bind the reviewed JE-240A US English transcription to shared Web components.

Run from the repository root:

    python manual_sources/JE-240A/US/en/git-20261027-ae3aea4b/build_content.py

Every Web string comes from ``source/transcription.json`` by line id; this
module only decides which shared component carries each printed block, in
printed order. It writes ``source/en/content.json``, the frozen input that
``rebuild.py`` replays. ``source_manifest.json:component_map`` lists the map
and ``source/differences.md`` every deliberate layout difference.
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

from tools.component_specs.app import app_inline_control_component_spec  # noqa: E402
from tools.component_specs.fcc import fcc_component_spec, fcc_semantic_projection  # noqa: E402
from tools.component_specs.inbox import inbox_component_spec  # noqa: E402
from tools.component_specs.manual_tables import lcd_icon_component_spec  # noqa: E402
from tools.component_specs.reference_figure import reference_figure_component_spec  # noqa: E402
from tools.component_specs.reference_table import reference_table_component_spec  # noqa: E402
from tools.component_specs.spec_table import spec_table_component_spec  # noqa: E402
from tools.component_specs.warranty import warranty_section_component_spec  # noqa: E402
from tools.manual_ir.components import component_flow_node  # noqa: E402
from tools.web.composite_hashing import reference_source_fragment_sha256  # noqa: E402
from tools.web.frozen_ai_flow import node, root, table, text  # noqa: E402

LANGUAGE = "en"
SOURCE_SHA256 = "ae3aea4bcffa1c87f2de01cbe5c84792713a70eded1716039beb442e38a0a27f"
MARKS = {"strong": "strong", "sub": "subscript", "sup": "superscript"}
CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰"


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


def bullets(keys: list[str]) -> dict:
    return root(node("list", [node("list_item", [node("paragraph", T.inline(k))]) for k in keys], ordered=False))


def group(children: list[dict], css: str) -> dict:
    return root(node("group", children, role="container", presentation={"html": {"attributes": {"class": css}}}))


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


def pair(value: str, key: str) -> dict:
    return {f"{key}_html": escape(value), f"{key}_text": value}


def lcd_table(rows: list[tuple[str, str, str]], ref: str, label: str) -> dict:
    """Printed LCD blocks: icon, bold title, description (unnumbered, as printed)."""
    values, refs = [], []
    for index, (name_key, body_key, asset) in enumerate(rows):
        name = T(name_key)
        values.append({**pair(name, "name"), "description_html": T.html(body_key),
                       "description_text": T.rows[body_key]["text"], "icon_alt": name, "asset_index": index})
        refs.append(asset)
    spec = lcd_icon_component_spec(accessibility_label=label, rows=values, icon_refs=refs, source_ref=ref,
                                   language=LANGUAGE, icon_locale_policy="exact", numbered=False)
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


def fcc_carrier(spec) -> list[dict]:
    payload = fcc_semantic_projection(spec)
    result = [node("paragraph", [text(v)]) for v in payload["opening_copy"]]
    for block in payload["left_blocks"] + payload["right_blocks"]:
        if block["kind"] == "list":
            result.append(node("list", [node("list_item", [text(v)]) for v in block["items"]], ordered=False))
        else:
            result.append(node("paragraph", [text(" ".join(filter(None, [block.get("label"), block["text"]])))]))
    return result


def warranty_section(index: int, title_key: str, body_keys: list[str]) -> list[dict]:
    # The shared card draws the body; its printed bold title is the heading before it.
    title = heading(title_key)
    blocks = [{"kind": "paragraph", "html": f"<p>{T.html(k)}</p>", "text": T.rows[k]["text"]} for k in body_keys]
    spec = warranty_section_component_spec(title=T.rows[title_key]["text"], section_index=index, blocks=blocks,
                                           source_ref=f"native-pdf/page-11/warranty-{index}", language=LANGUAGE)
    return [title, component_flow_node(spec, root=True)]


# --- chapters -------------------------------------------------------------

def introduction() -> list[dict]:
    """Printed 01: the US English / Model band, the welcome text, specifications and package list."""
    band = root(node("heading", [text(T("intro.lang") + " "),
                                 node("inline_group", [text(T("intro.model"))],
                                      presentation={"html": {"attributes": {"class": "hb-heading-model"}}})],
                     level=2, anchor="native-introduction"))
    rows = [(T(f"spec.r{i}.l"), T(f"spec.r{i}.v")) for i in range(1, 19)]
    spec = spec_table_component_spec(section_title=T("spec.h"), rows=rows, source_ref="native-pdf/page-2/spec",
                                     language=LANGUAGE)
    cards = [{"image_ref": ref, "label": T(key), "alt": T.rows[key]["text"]}
             for key, ref in (("box.c1", "assets/inbox-unit.png"), ("box.c2", "assets/inbox-cable.png"),
                              ("box.c3", "assets/inbox-manual.png"))]
    inbox = inbox_component_spec(accessibility_label=T.rows["box.h"]["text"], cards=cards, tip_label="", tip_body="",
                                 source_ref="native-pdf/page-2/inbox", language=LANGUAGE, require_tip=False,
                                 variant="responsive-card-grid")
    carrier = table([[node("table_cell", [node("image", source=c["image_ref"], alt=c["alt"]),
                                          node("paragraph", [text(c["label"])])], header=False) for c in cards]])
    return [band, para("intro.p1"), para("intro.p2"), para("intro.p3"),
            component_flow_node(spec, carrier_flow=spec_carrier(spec), root=True),
            heading("cert.h"),
            figure("assets/certifications.png", "certifications", 2, [], label=T.rows["cert.h"]["text"]),
            para("spec.tm"),
            chapter("box.h", "native-package-list"), component_flow_node(inbox, carrier_flow=(carrier,), root=True)]


def gear() -> list[dict]:
    keys = ["names.power", "names.car", "names.usba", "names.usbc", "names.usbcio", "names.dcusb", "names.lcd",
            "names.led", "names.ledbtn", "names.acout", "names.acbtn", "names.acin"]
    return [chapter("gear.h", "native-gear"), heading("gear.sub"), figure("assets/overview.png", "overview", 3, keys)]


def lcd() -> list[dict]:
    legend = reference_table_component_spec(
        variant="lcd-descriptions", label=T.rows["lcd.h"]["text"], headers=[],
        rows=[[{"html": CIRCLED[i], "text": CIRCLED[i]},
               {"html": escape(T(f"lcd.n{i + 1}")), "text": T.rows[f"lcd.n{i + 1}"]["text"]}] for i in range(17)],
        source_ref="native-pdf/page-3/lcd-legend", language=LANGUAGE)
    head = node("table_head", [node("table_row", [node("table_cell", [text(T(k))], header=True)
                                                  for k in ("eco.th1", "eco.th2", "eco.th3")])])
    body = node("table_body", [node("table_row", [
        node("table_cell", [text(T(f"eco.r{r}.c1"))], header=False),
        node("table_cell", [text(T(f"eco.r{r}.c2"))], header=False),
        *([node("table_cell", [text(T("eco.c3"))], header=False, row_span=3)] if r == 1 else [])]) for r in (1, 2, 3)])
    # Shared table wrapper: the printed defaults cell spans the three output rows.
    eco = root(node("group", [node("table", [head, body],
                                   presentation={"html": {"attributes": {"class": "manual-table"}}})],
                    role="container",
                    presentation={"html": {"attributes": {"class": "table-wrapper docutils container"}}}))
    label = T.rows["lcd.h"]["text"]
    return [chapter("lcd.h", "native-lcd-display"),
            figure("assets/lcd-map.png", "lcd-map", 3, [], label=label),
            component_flow_node(legend, root=True),
            strong_para("ups.h"), para("ups.p"),
            lcd_table([("icon.ring.t", "icon.ring.b",
                        "assets/shared-lcd/17_Battery_Power_Indicator_VLufb9exvoVLfgxz47pcfnRGnaf.png"),
                       ("icon.low.t", "icon.low.b", "assets/lcd-low-battery.png"),
                       ("icon.eco.t", "icon.eco.b", "assets/lcd-energy-saving.png")], "native-pdf/page-4/lcd-icons", label),
            eco, strong_para("eco.off.h"), para("eco.off"), strong_para("eco.on.h"), para("eco.on"),
            lcd_table([("icon.fault.t", "icon.fault.b", "assets/shared-lcd/25_Fault_code_LaTmb4IQYo3vwvxMqQNcC2RgnIf.png"),
                       ("icon.high.t", "icon.high.b", "assets/lcd-high-temperature.png"),
                       ("icon.lowt.t", "icon.lowt.b", "assets/lcd-low-temperature.png")], "native-pdf/page-5/lcd-icons",
                      label)]


def operations() -> list[dict]:
    return [chapter("ops.h", "native-basic-operations"),
            heading("ops.out.h"), para("ops.main"), para("ops.ac"), para("ops.usb"),
            heading("ops.lcd.h"), para("ops.lcd.p"), para("ops.lcd.on"), para("ops.lcd.off"), para("ops.lcd.tip"),
            heading("ops.led.h"), para("ops.led.modes"), para("ops.led.ops")]


def app_connection() -> list[dict]:
    return [chapter("app.h", "native-app-connection"), para("app.p")]


def charging() -> list[dict]:
    return [chapter("chg.h", "native-charging"), para("chg.green"), para("chg.both"),
            strong_para("chg.note.h"), para("chg.note1"), para("chg.note2"),
            heading("chg.wall.h"), para("chg.wall"),
            heading("chg.emg.h", level=4), para("chg.emg"), para("chg.emg.note"),
            figure("assets/charging-ac.png", "charging-ac", 6, ["fig.ac.charger", "fig.ac.unit"]),
            heading("chg.solar.h"), heading("chg.solar.h2", level=4), para("chg.solar.p"),
            figure("assets/charging-solar.png", "charging-solar", 7,
                   ["fig.solar.adaptor", "fig.solar.male", "fig.solar.port", "fig.solar.panel", "fig.solar.unit"]),
            heading("chg.car.h"), para("chg.car.p"), para("chg.car.n1"), para("chg.car.n2"),
            figure("assets/charging-car.png", "charging-car", 7, ["fig.car.unit", "fig.car.vehicle"]),
            heading("chg.safe.h"), para("chg.safe1"), para("chg.safe2")]


def precautions() -> list[dict]:
    note_label, note_body = T("fcc.note").split(" ", 1)
    mod_label, mod_body = T("fcc.mod").split(" ", 1)
    fcc = fcc_component_spec(
        accessibility_label="FCC", opening_copy=[], mark_asset_ref="assets/fcc-mark.svg",
        left_blocks=[{"kind": "paragraph", "label": note_label, "text": note_body}],
        right_blocks=[{"kind": "list", "items": [T(f"fcc.l{i}") for i in range(1, 5)]},
                      {"kind": "paragraph", "label": mod_label, "text": mod_body}],
        source_ref="native-pdf/page-8/fcc", language=LANGUAGE)
    return [chapter("prec.h", "native-safety-precautions"), para("prec.lead"),
            *(para(f"prec.{k}") for k in ("a", "b", "c", "d", "e", "f", "g", "h2", "i")),
            group([component_flow_node(fcc, carrier_flow=fcc_carrier(fcc))], "hb-fcc-statement")]


def instructions() -> list[dict]:
    letters = ["a", "b", "c", "d", "e", "f", "g", "h3", "i", "j", "j1", "j2", "j3", "j4", "j5", "k", "l", "m", "n"]
    return [chapter("isi.h", "native-safety-instructions"), heading("isi.h2"), para("isi.lead"),
            *(para(f"isi.{k}") for k in letters),
            heading("op.h"), bullets([f"op.l{i}" for i in range(1, 18)]), para("op.warn"), para("op.danger"),
            heading("mov.h"), bullets([f"mov.l{i}" for i in range(1, 7)]),
            heading("maint.h"), para("maint.p")]


def warranty() -> list[dict]:
    return [chapter("war.h", "native-warranty"), para("war.lead1"), para("war.lead2"),
            *warranty_section(1, "war.lim.h", ["war.lim1", "war.lim2"]),
            *warranty_section(2, "war.per.h", ["war.per1", "war.per2"]),
            *warranty_section(3, "war.exc.h", ["war.exc"]),
            *warranty_section(4, "war.buyer.h", ["war.buyer"]),
            *warranty_section(5, "war.excl.h", ["war.excl.lead", "war.excl1", "war.excl2", "war.excl3", "war.excl4"]),
            heading("war.app"), figure("assets/app-badges.png", "app-badges", 11, [], label="App Store / Google Play")]


def app_manual() -> list[dict]:
    before, after = T("appm.s21").split(" [+] ")
    plus = app_inline_control_component_spec(
        accessibility_label="+", paragraph_html=f"{escape(before)} <strong>+</strong> {escape(after)}",
        paragraph_text=f"{before} + {after}", source_ref="native-pdf/page-12/add-button", language=LANGUAGE,
        metadata={"visual_recovery": "outlined-pdf-round-plus-control"})
    plus_carrier = node("paragraph", [text(before + " "), node("strong", [text("+")]), text(" " + after)])
    contact = group([node("paragraph", [node("strong", [text(T("back.company"))])]),
                     node("paragraph", [text(T("back.address"))]), node("paragraph", [text(T("back.contact"))])],
                    "hb-text-panel")
    return [chapter("appm.h", "native-app-manual"),
            heading("appm.s1.h"), para("appm.s1"),
            heading("appm.s2.h"), component_flow_node(plus, carrier_flow=(plus_carrier,), root=True), para("appm.s22"),
            figure("assets/app-add.png", "app-add", 12, ["fig.app.c21", "fig.app.c22"]),
            para("appm.rem1"),
            figure("assets/app-control.png", "app-control", 12, ["fig.ctl.dcusb", "fig.ctl.ac", "fig.ctl.power"]),
            para("appm.s23"), para("appm.rem2"), bullets(["appm.rem2.l1", "appm.rem2.l2"]),
            para("appm.s24"), para("appm.rem3"), para("appm.s25"),
            figure("assets/app-results.png", "app-results", 13, ["fig.app.c23", "fig.app.c24", "fig.app.c25"]),
            para("appm.shots"),
            heading("appm.s3.h"), para("appm.s3"),
            heading("appm.s4.h"),
            heading("appm.s41.h", level=4), bullets(["appm.s41.l1", "appm.s41.l2"]),
            heading("appm.s42.h", level=4), bullets(["appm.s42.l1", "appm.s42.l2"]),
            heading("appm.s43.h", level=4), bullets(["appm.s43.l1"]),
            contact]


CHAPTERS = (
    ("introduction", "US English", introduction), ("gear", "GET TO KNOW YOUR GEAR", gear),
    ("lcd_display", "LCD DISPLAY", lcd), ("basic_operations", "BASIC OPERATIONS", operations),
    ("app_connection", "APP CONNECTION", app_connection), ("charging", "CHARGING YOUR JACKERY EXPLORER 240", charging),
    ("safety_precautions", "SAFETY PRECAUTIONS WHEN USING", precautions),
    ("safety_instructions", "INSTRUCTIONS PERTAINING TO RISK OF FIRE, ELECTRIC SHOCK, OR INJURY TO PERSONS",
     instructions),
    ("warranty", "WARRANTY", warranty), ("app_manual", "USER MANUAL FOR JACKERY APP", app_manual),
)


def build() -> dict:
    chapters = [{"id": cid, "title": title, "nodes": make()} for cid, title, make in CHAPTERS]
    missing = [k for k in T.rows if k not in T.used]
    if missing:
        raise ValueError("Web transcription lines not bound: " + ", ".join(missing))
    return {"model": "JE-240A", "region": "US", "language": LANGUAGE,
            "title": "Jackery Explorer 240 User Manual", "source_sha256": SOURCE_SHA256, "chapters": chapters}


def main() -> None:
    content = build()
    path = PACKAGE / "source/en/content.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(content, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"chapters": [c["id"] for c in content["chapters"]], "lines": len(T.used)}))


if __name__ == "__main__":
    main()
