"""Bind the reviewed JE-1000D US transcription to shared Web components.

Run from the repository root:

    python manual_sources/JE-1000D/US/en/git-20261027-10d15090/build_content.py

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

from tools.component_specs.app import app_inline_control_component_spec  # noqa: E402
from tools.component_specs.inbox import inbox_component_spec  # noqa: E402
from tools.component_specs.manual_tables import lcd_icon_component_spec  # noqa: E402
from tools.component_specs.reference_figure import reference_figure_component_spec  # noqa: E402
from tools.component_specs.reference_table import reference_table_component_spec  # noqa: E402
from tools.component_specs.spec_table import spec_table_component_spec  # noqa: E402
from tools.manual_ir.components import component_flow_node  # noqa: E402
from tools.web.composite_hashing import reference_source_fragment_sha256  # noqa: E402
from tools.web.frozen_ai_flow import callout, node, root, table, text  # noqa: E402
from tools.web.frozen_ai_table_components import _spec_carrier  # noqa: E402

LANGUAGE = "en"
CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲"
SOURCE_SHA256 = "10d15090f944d3a0a1518e495dca4cf5cad15252220990c1b0e324564519316f"


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
    """A printed bold run-in line (smaller than the section headings)."""
    return root(node("paragraph", [node("strong", [text(T(key))])]))


def heading(key: str, level: int = 3, anchor: str | None = None) -> dict:
    value = T(key)
    return root(node("heading", [text(value)], level=level, **({"anchor": anchor} if anchor else {})))


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


def labelled(key: str) -> tuple[str, str]:
    """Split a printed run-in signal line ("WARNING: …") into its label and body."""
    label, body = T(key).split(": ", 1)
    return label, body


def callout_block(label: str, body: list[dict], variant: str, ref: str) -> dict:
    # The shared strip shows the signal word without its printed trailing colon
    # (callout label normalisation, as in the JE-1000D JP edition).
    return root(callout(label.rstrip(":"), body, variant=variant, language=LANGUAGE, source_ref=ref))


def items(keys: list[str]) -> dict:
    return node("list", [node("list_item", [text(T(k))]) for k in keys], ordered=False)


def image(ref: str, alt: str) -> dict:
    return node("image", source=ref, alt=alt)


# --- chapters -------------------------------------------------------------

SPEC_ROWS = 18


def specifications() -> list[dict]:
    band = panel([node("paragraph", [node("strong", [text(T("band.region"))]), text(" " + T("band.language"))]),
                  node("paragraph", [text(T("band.model"))])])
    rows = [(T(f"spec.r{i}.l"), T(f"spec.r{i}.v")) for i in range(1, SPEC_ROWS + 1)]
    # The printed TECHNICAL SPECIFICATIONS title is the chapter h2 the shared spec carrier draws.
    title = T("spec.h")
    spec = spec_table_component_spec(section_title=title, rows=rows, source_ref="native-pdf/page-2/spec",
                                     language=LANGUAGE)
    marks = root(node("paragraph", [image("assets/cert-fcc.svg", "FCC"), text(" "),
                                    image("assets/cert-bc.svg", "BC"), text(" "),
                                    image("assets/cert-weee.png", "WEEE")]))
    return [band, para("intro.p1"), para("intro.p2"), para("intro.p3"),
            component_flow_node(spec, carrier_flow=_spec_carrier(title, rows), root=True),
            heading("cert.h"), marks, para("spec.tm")]


def package_list() -> list[dict]:
    title = T.rows["box.h"]["text"]
    cards = [{"image_ref": ref, "label": T(key), "alt": T.rows[key]["text"]}
             for key, ref in (("box.c1", "assets/inbox-unit.png"), ("box.c2", "assets/inbox-cable.png"),
                              ("box.c3", "assets/inbox-manual.png"))]
    spec = inbox_component_spec(accessibility_label=title, cards=cards, tip_label="", tip_body="",
                                source_ref="native-pdf/page-2/inbox", language=LANGUAGE, require_tip=False)
    carrier = table([[node("table_cell", [node("image", source=c["image_ref"], alt=c["alt"]),
                                          node("paragraph", [text(c["label"])])], header=False) for c in cards]])
    return [heading("box.h", 2, "native-package-list"), component_flow_node(spec, carrier_flow=(carrier,), root=True)]


def overview() -> list[dict]:
    keys = ["names.f.power", "names.f.car", "names.f.usbc1", "names.f.usbc2", "names.f.usba", "names.f.dcbtn",
            "names.f.lcd", "names.f.led", "names.f.ledbtn", "names.f.acout", "names.f.acbtn",
            "names.r.dcin", "names.r.acin", "names.r.cap"]
    return [heading("names.h", 2, "native-get-to-know-your-gear"), heading("names.sub"),
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


def energy_table() -> dict:
    """Output / Output Power / Defaults, the Defaults cell printed once across the three rows."""
    head = node("table_head", [node("table_row", [node("table_cell", [text(T(k))], header=True)
                                                  for k in ("eco.th1", "eco.th2", "eco.th3")])])
    rows = []
    for r in (1, 2, 3):
        cells = [node("table_cell", [text(T(f"eco.r{r}.c1"))], header=False),
                 node("table_cell", [text(T(f"eco.r{r}.c2"))], header=False)]
        if r == 1:
            cells.append(node("table_cell", [text(T("eco.default"))], header=False, row_span=3))
        rows.append(node("table_row", cells))
    return root(node("group", [node("table", [head, node("table_body", rows)],
                                    presentation={"html": {"attributes": {"class": "manual-table"}}})],
                     role="container",
                     presentation={"html": {"attributes": {"class": "table-wrapper docutils container"}}}))


def lcd() -> list[dict]:
    legend = reference_table_component_spec(
        variant="lcd-descriptions", label=T.rows["lcd.h"]["text"], headers=[],
        rows=[[{"html": CIRCLED[i - 1], "text": CIRCLED[i - 1]},
               {"html": escape(T.rows[f"lcd.n{i}"]["text"]), "text": T(f"lcd.n{i}")}] for i in range(1, 20)],
        source_ref="native-pdf/page-3-4/lcd-legend", language=LANGUAGE)
    return [heading("lcd.h", 2, "native-lcd-display"),
            figure("assets/lcd-map.png", "lcd-map", 3, [], label=T.rows["lcd.h"]["text"]),
            component_flow_node(legend, root=True),
            strong("ups.h"), para("ups.p1"), para("ups.p2"),
            lcd_rows([("lcd.d19.t", "lcd.d19.b", "assets/lcd-battery-ring.svg"),
                      ("lcd.d10.t", "lcd.d10.b", "assets/lcd-low-battery.svg"),
                      ("lcd.d15.t", "lcd.d15.b", "assets/lcd-energy-saving.svg")], "native-pdf/page-4/lcd-icons"),
            energy_table(), strong("eco.off.h"), para("eco.off"), strong("eco.on.h"), para("eco.on"),
            lcd_rows([("lcd.d12.t", "lcd.d12.b", "assets/lcd-fault-code.svg"),
                      ("lcd.d13.t", "lcd.d13.b", "assets/lcd-high-temperature.svg"),
                      ("lcd.d14.t", "lcd.d14.b", "assets/lcd-low-temperature.svg"),
                      ("lcd.d2.t", "lcd.d2.b", "assets/lcd-quiet-charging.svg"),
                      ("lcd.d1.t", "lcd.d1.b", "assets/lcd-battery-saving.svg")], "native-pdf/page-5/lcd-icons")]


def basic_operations() -> list[dict]:
    caution = callout_block(T("ops.caut.label"), [items(["ops.caut.i1", "ops.caut.i2", "ops.caut.i3"])],
                            "caution", "native-pdf/page-5/caution")
    return [heading("ops.h", 2, "native-basic-operations"), heading("ops.power.h"),
            para("ops.power"), para("ops.power.note"), para("ops.ac"), para("ops.dc"), para("ops.car"), caution,
            strong("ops.lcd.h"), para("ops.lcd"), strong("ops.lcdauto.h"), para("ops.lcdauto"),
            para("ops.aod"), para("ops.aod2"), para("ops.tip"),
            heading("led.h"), para("led.p1"), para("led.p2"),
            figure("assets/led-modes.png", "led-modes", 6, ["fig.led.m1", "fig.led.m2", "fig.led.sos", "fig.led.m3"])]


def app_connection() -> list[dict]:
    return [heading("app.h", 2, "native-app-connection"), para("app.p")]


def charging() -> list[dict]:
    caution = callout_block(T("chg.caut.label"), [node("paragraph", [text(T("chg.caut.lead"))]),
                                                  items(["chg.caut.i1", "chg.caut.i2"])],
                            "caution", "native-pdf/page-8/caution")
    return [heading("chg.h", 2, "native-charging"), para("chg.first"), para("chg.note1"), para("chg.note2"),
            heading("chg.ac.h"), para("chg.ac"),
            strong("chg.emg.h"), para("chg.emg"), para("chg.emg.note"),
            figure("assets/ac-charge.png", "ac-charge", 7, ["fig.ac.charger", "fig.ac.unit"]),
            heading("chg.solar.h"), para("chg.solar"),
            figure("assets/solar-direct.png", "solar-direct", 7, ["fig.solar1.unit"]),
            figure("assets/solar-adapter.png", "solar-adapter", 7, ["fig.solar2.unit"]),
            caution,
            heading("chg.car.h"), para("chg.car"), para("chg.car.n1"), para("chg.car.n2"),
            figure("assets/car-charge.png", "car-charge", 8, ["fig.car.unit", "fig.car.vehicle"])]


def safety() -> list[dict]:
    letters = ["safety.a", "safety.b", "safety.c", "safety.d", "safety.e", "safety.f", "safety.g", "safety.h2",
               "safety.i", "safety.j", "safety.k", "safety.l", "safety.m"]
    warn_label, warn_body = labelled("opi.warn")
    danger_label, danger_body = labelled("opi.danger")
    return [heading("safety.h", 2, "native-safety"), heading("safety.ist.h"), para("safety.lead"),
            *(para(k) for k in letters),
            strong("safety.save"), heading("opi.h"),
            bullets([f"opi.l{i}" for i in range(1, 18)]),
            callout_block(warn_label, [node("paragraph", [text(warn_body)])], "warning", "native-pdf/page-10/warning"),
            callout_block(danger_label, [node("paragraph", [text(danger_body)])], "danger",
                          "native-pdf/page-10/danger"),
            heading("mov.h"), bullets([f"mov.l{i}" for i in range(1, 7)]),
            heading("maint.h"), para("maint"),
            root(node("paragraph", [image("assets/cert-fcc.svg", "FCC")])),
            para("fcc.note"), bullets(["fcc.l1", "fcc.l2", "fcc.l3", "fcc.l4"]), para("fcc.mod")]


def warranty() -> list[dict]:
    return [heading("war.h", 2, "native-warranty"), para("war.lead1"), para("war.lead2"),
            heading("war.lim.h"), para("war.lim1"), para("war.lim2"),
            heading("war.per.h"), para("war.per1"), para("war.per2"),
            heading("war.exch.h"), para("war.exch"),
            heading("war.orig.h"), para("war.orig"),
            heading("war.excl.h"), para("war.excl.lead"),
            *(para(f"war.excl{i}") for i in range(1, 5)),
            heading("app.dl.h"),
            figure("assets/app-store.png", "app-store", 11, [], label="App Store / Google Play")]


def app_manual() -> list[dict]:
    before, after = T("appm.s21").split(" [+] ")
    plus = app_inline_control_component_spec(
        accessibility_label="+", paragraph_html=f"{escape(before)} <strong>+</strong> {escape(after)}",
        paragraph_text=f"{before} + {after}", source_ref="native-pdf/page-12/add-button", language=LANGUAGE,
        metadata={"visual_recovery": "pdf-vector-plus-control"})
    plus_carrier = node("paragraph", [text(before + " "), node("strong", [text("+")]), text(" " + after)])

    def note(key: str, ref: str, extra: tuple[dict, ...] = ()) -> dict:
        label, body = labelled(key)
        return callout_block(label, [node("paragraph", [text(body)]), *extra], "note", ref)

    return [heading("appm.h", 2, "native-app-manual"),
            heading("appm.s1.h"), para("appm.s1"),
            heading("appm.s2.h"), component_flow_node(plus, carrier_flow=(plus_carrier,), root=True),
            para("appm.s22"),
            figure("assets/app-add.png", "app-add", 12, ["fig.app.c21", "fig.app.c22"]),
            note("appm.note1", "native-pdf/page-12/remarks-1"),
            figure("assets/app-control.png", "app-control", 12, ["fig.ctl.dc", "fig.ctl.ac", "fig.ctl.power"]),
            para("appm.s23"),
            note("appm.note2", "native-pdf/page-12/remarks-2", (items(["appm.note2.l1", "appm.note2.l2"]),)),
            para("appm.s24"), note("appm.note3", "native-pdf/page-13/remarks-3"), para("appm.s25"),
            figure("assets/app-results.png", "app-results", 13, ["fig.app.c23", "fig.app.c24", "fig.app.c25"]),
            para("appm.shots"),
            heading("appm.s3.h"), para("appm.s3"),
            heading("appm.s4.h"),
            heading("appm.s41.h", level=4), bullets(["appm.s41.l1", "appm.s41.l2"]),
            heading("appm.s42.h", level=4), bullets(["appm.s42.l1", "appm.s42.l2"]),
            heading("appm.s43.h", level=4), bullets(["appm.s43.l1"])]


CHAPTERS = (
    ("technical_specifications", "TECHNICAL SPECIFICATIONS", specifications),
    ("package_list", "PACKAGE LIST", package_list),
    ("product_overview", "GET TO KNOW YOUR GEAR", overview),
    ("lcd_display", "LCD DISPLAY", lcd),
    ("basic_operations", "BASIC OPERATIONS", basic_operations),
    ("app_connection", "APP CONNECTION", app_connection),
    ("charging", "CHARGING YOUR JACKERY EXPLORER 1000", charging),
    ("safety", "INSTRUCTIONS PERTAINING TO RISK OF FIRE, ELECTRIC SHOCK, OR INJURY TO PERSONS", safety),
    ("warranty", "WARRANTY", warranty),
    ("app_setup", "User Manual for Jackery App", app_manual),
)


def build() -> dict:
    chapters = [{"id": cid, "title": title, "nodes": make()} for cid, title, make in CHAPTERS]
    missing = [k for k in T.rows if k not in T.used]
    if missing:
        raise ValueError("Web transcription lines not bound: " + ", ".join(missing))
    return {"model": "JE-1000D", "region": "US", "language": LANGUAGE,
            "title": "Jackery Explorer 1000 USER MANUAL", "source_sha256": SOURCE_SHA256,
            "chapters": chapters}


def main() -> None:
    content = build()
    path = PACKAGE / "source/en/content.json"
    path.write_text(json.dumps(content, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"chapters": [c["id"] for c in content["chapters"]], "lines": len(T.used)}))


if __name__ == "__main__":
    main()
