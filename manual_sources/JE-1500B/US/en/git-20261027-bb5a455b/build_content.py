"""Bind the reviewed JE-1500B US transcription to shared Web components.

Run from the repository root:

    python manual_sources/JE-1500B/US/en/git-20261027-bb5a455b/build_content.py

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
SOURCE_SHA256 = "bb5a455b5c3e03b70ee95d6d6ceb74a9c98b671addc1d30d9637f9bb974a7dbb"


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
    return root(node("heading", [text(T(key))], level=level, **({"anchor": anchor} if anchor else {})))


def chapter_heading(key: str, anchor: str) -> dict:
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


def run_in_callout(key: str, variant: str, ref: str) -> dict:
    """A printed run-in signal word (``Caution:``, ``Tip:``) becomes the shared callout label.

    The shared callout normalizes its label without the colon (as 備考： in the
    JE-1000D JP precedent); the words themselves are unchanged.
    """
    value = T(key)
    label, body = value.split(":", 1)
    return root(callout(label, [node("paragraph", [text(body.lstrip(" "))])],
                        variant=variant, language=LANGUAGE, source_ref=ref))


# --- chapters -------------------------------------------------------------

def specifications() -> list[dict]:
    groups = [
        ("spec.g1", [("spec.g1.r1.l", ["spec.g1.r1.v"]), ("spec.g1.r2.l", ["spec.g1.r2.v"]),
                     ("spec.g1.r3.l", ["spec.g1.r3.v"]), ("spec.g1.r4.l", ["spec.g1.r4.v"]),
                     ("spec.g1.r5.l", ["spec.g1.r5.v"]), ("spec.g1.r6.l", ["spec.g1.r6.v"])]),
        ("spec.g2", [("spec.g2.r1.l", ["spec.g2.r1.v"]), ("spec.g2.r2.l", ["spec.g2.r2.v"]),
                     ("spec.g2.r3.l", ["spec.g2.r3.v"]), ("spec.g2.r4.l", ["spec.g2.r4.v"])]),
        ("spec.g3", [("spec.g3.r1.l", ["spec.g3.r1.v"]), ("spec.g3.r2.l", ["spec.g3.r2.v1", "spec.g3.r2.v2"])]),
        ("spec.g4", [("spec.g4.r1.l", ["spec.g4.r1.v"]), ("spec.g4.r2.l", ["spec.g4.r2.v"])]),
    ]
    nodes = [strong("band.model"), para("intro.p1"), para("intro.p2"), para("intro.p3"),
             chapter_heading("spec.h", "native-technical-specifications")]
    for title_key, rows_keys in groups:
        title = T(title_key)
        rows: list[tuple[str, str]] = []
        for label_key, value_keys in rows_keys:
            label = T(label_key)
            for index, value_key in enumerate(value_keys):
                # A second printed value line continues the same label (HB-TABLE-SPEC rowspan).
                rows.append((label if index == 0 else "", T(value_key)))
        spec = spec_table_component_spec(section_title=title, rows=rows,
                                         source_ref=f"native-pdf/page-2/{title_key}", language=LANGUAGE)
        nodes.append(component_flow_node(spec, carrier_flow=_spec_carrier(title, rows), root=True))
    nodes += [heading("spec.cert"), figure("certifications", 2, [], label=T.rows["spec.cert"]["text"]),
              para("spec.fn1"), para("spec.fn2a"), para("spec.fn2b"), para("mod.p")]
    return nodes


def package_list() -> list[dict]:
    keys = [("box.c1", "inbox-unit"), ("box.c2", "inbox-car-cable"), ("box.c3", "inbox-ac-cable"),
            ("box.c4", "inbox-adaptor"), ("box.c5", "inbox-guide")]
    cards = [{"image_ref": f"assets/{ref}.png", "label": T(key), "alt": T.rows[key]["text"]} for key, ref in keys]
    title = T.rows["box.h"]["text"]
    spec = inbox_component_spec(accessibility_label=title, cards=cards, tip_label="", tip_body="",
                                source_ref="native-pdf/page-3/inbox", language=LANGUAGE, require_tip=False)
    carrier = table([[node("table_cell", [node("image", source=c["image_ref"], alt=c["alt"]),
                                          node("paragraph", [text(c["label"])])], header=False) for c in cards]])
    return [chapter_heading("box.h", "native-package-list"),
            component_flow_node(spec, carrier_flow=(carrier,), root=True)]


def overview() -> list[dict]:
    keys = ["names.dcin", "names.acin", "names.ledbtn", "names.led", "names.usba", "names.usbc", "names.qc",
            "names.usbbtn", "names.lcdbtn", "names.car", "names.carbtn", "names.acout", "names.acbtn"]
    return [chapter_heading("gear.h", "native-get-to-know-your-gear"), heading("gear.h2"),
            figure("overview", 3, keys)]


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


def low_power_table() -> dict:
    head = node("table_head", [node("table_row", [node("table_cell", [text(T(k))], header=True)
                                                  for k in ("lpm.th1", "lpm.th2", "lpm.th3")])])
    rows = []
    for r in (1, 2, 3):
        cells = [node("table_cell", [text(T(f"lpm.r{r}.c1"))], header=False),
                 node("table_cell", [text(T(f"lpm.r{r}.c2"))], header=False)]
        if r == 1:
            # The printed Defaults cell spans the three output rows.
            cells.append(node("table_cell", [text(T("lpm.default"))], header=False, row_span=3))
        rows.append(node("table_row", cells))
    return root(node("group", [node("table", [head, node("table_body", rows)],
                                    presentation={"html": {"attributes": {"class": "manual-table"}}})],
                     role="container",
                     presentation={"html": {"attributes": {"class": "table-wrapper docutils container"}}}))


def lcd() -> list[dict]:
    legend_keys = [f"lcd.n{i}" for i in range(1, 16)]
    legend = reference_table_component_spec(
        variant="lcd-descriptions", label=T.rows["lcd.h"]["text"], headers=[],
        rows=[[{"html": escape(T.rows[k]["marker"]), "text": T.rows[k]["marker"]},
               {"html": escape(T(k)), "text": T.rows[k]["text"]}] for k in legend_keys],
        source_ref="native-pdf/page-4/lcd-legend", language=LANGUAGE)
    return [chapter_heading("lcd.h", "native-lcd-display"),
            figure("lcd-map", 4, [], label=T.rows["lcd.h"]["text"]),
            component_flow_node(legend, root=True),
            lcd_rows([("lcd.ring.t", "lcd.ring.b", "assets/lcd-battery-power.svg"),
                      ("lcd.lowbat.t", "lcd.lowbat.b", "assets/lcd-low-battery.svg"),
                      ("lcd.lpm.t", "lcd.lpm.b", "assets/lcd-low-power-mode.svg")], "native-pdf/page-4/lcd-icons"),
            low_power_table(), strong("lpm.on.h"), para("lpm.on"), strong("lpm.off.h"), para("lpm.off"),
            lcd_rows([("lcd.fault.t", "lcd.fault.b", "assets/lcd-fault-code.svg"),
                      ("lcd.hot.t", "lcd.hot.b", "assets/lcd-high-temperature.svg"),
                      ("lcd.cold.t", "lcd.cold.b", "assets/lcd-low-temperature.svg")], "native-pdf/page-5/lcd-icons")]


def basic_operations() -> list[dict]:
    return [chapter_heading("ops.h", "native-basic-operations"),
            heading("ops.power.h"), para("ops.ac"), para("ops.usb"), para("ops.car"),
            heading("ops.lcd.h"), *(para(k) for k in ("ops.lcd1", "ops.lcd2", "ops.lcd3", "ops.lcd4")),
            run_in_callout("ops.lcd.tip", "tip", "native-pdf/page-5/tip"),
            heading("ops.led.h"), para("ops.led1"), para("ops.led2")]


def charging() -> list[dict]:
    return [chapter_heading("chg.h", "native-charging"), para("chg.p1"), para("chg.p2")]


def charging_wall() -> list[dict]:
    return [chapter_heading("wall.h", "native-charging-from-the-wall"), para("wall.p"),
            figure("ac-charge", 6, ["fig.ac.charger", "fig.ac.unit"])]


def solar() -> list[dict]:
    return [chapter_heading("solar.h", "native-solar-energy-charging"),
            heading("solar.g1.h"), para("solar.g1.p1"), para("solar.g1.p2"),
            figure("solar-three", 6, ["fig.s3.unit", "fig.s3.panels"]),
            figure("solar-two-two", 6, ["fig.s22.left", "fig.s22.unit", "fig.s22.right"]),
            figure("solar-three-three", 7, ["fig.s33.unit", "fig.s33.left", "fig.s33.right"]),
            run_in_callout("solar.caution", "caution", "native-pdf/page-7/caution"),
            para("solar.prohibited"),
            figure("solar-prohibited", 7, [f"fig.x{r}.{p}" for r in (1, 2, 3) for p in ("left", "unit", "right")]),
            heading("solar.g2.h"), para("solar.g2.p1"), para("solar.g2.p2"),
            figure("solar-saga80", 8, ["fig.s80.out", "fig.s80.par"]),
            run_in_callout("solar.g2.tip", "tip", "native-pdf/page-8/warm-tip"),
            heading("solar.g3.h"), para("solar.g3.p"),
            figure("adaptor", 8, ["fig.ad.female", "fig.ad.adaptor", "fig.ad.male", "fig.ad.unit"])]


def car() -> list[dict]:
    return [chapter_heading("car.h", "native-charging-in-the-car"), para("car.p1"), para("car.p2"),
            figure("car-charge", 9, ["fig.car.vehicle", "fig.car.unit"]),
            heading("car.safe.h"), para("car.safe1"), para("car.safe2")]


def safety() -> list[dict]:
    items = ("safety.a", "safety.b", "safety.c", "safety.d", "safety.e", "safety.f", "safety.g", "safety.h2",
             "safety.i", "safety.j", "safety.k")
    return [chapter_heading("safety.h", "native-safety-precautions"), strong("safety.lead"),
            *(para(k) for k in items),
            figure("fcc-mark", 9, [], label="FCC"),
            para("fcc.note"), *(para(f"fcc.m{i}") for i in range(1, 5))]


def warranty() -> list[dict]:
    return [chapter_heading("war.h", "native-warranty"), strong("war.note"),
            heading("war.lim.h"), para("war.lim1"), para("war.lim2"),
            heading("war.per.h"), para("war.per1"), para("war.per2"),
            heading("war.exc.h"), para("war.exc"),
            heading("war.buy.h"), para("war.buy"),
            heading("war.ex.h"), *(para(k) for k in ("war.ex.lead", "war.ex1", "war.ex2", "war.ex3", "war.ex4"))]


CHAPTERS = (
    ("specifications", "TECHNICAL SPECIFICATIONS", specifications), ("package_list", "PACKAGE LIST", package_list),
    ("product_overview", "GET TO KNOW YOUR GEAR", overview), ("lcd_display", "LCD DISPLAY", lcd),
    ("basic_operations", "BASIC OPERATIONS", basic_operations),
    ("charging", "CHARGING YOUR JACKERY EXPLORER 1500 PRO", charging),
    ("charging_wall", "CHARGING FROM THE WALL", charging_wall), ("solar_charging", "SOLAR ENERGY CHARGING", solar),
    ("car_charging", "CHARGING IN THE CAR", car), ("safety", "SAFETY PRECAUTIONS WHEN USING", safety),
    ("warranty", "WARRANTY", warranty),
)


def build() -> dict:
    chapters = [{"id": cid, "title": title, "nodes": make()} for cid, title, make in CHAPTERS]
    missing = [k for k in T.rows if k not in T.used]
    if missing:
        raise ValueError("Web transcription lines not bound: " + ", ".join(missing))
    return {"model": "JE-1500B", "region": "US", "language": LANGUAGE,
            "title": "Jackery Explorer 1500 Pro User Manual",
            "source_sha256": SOURCE_SHA256, "chapters": chapters}


def main() -> None:
    content = build()
    path = PACKAGE / "source/en/content.json"
    path.write_text(json.dumps(content, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"chapters": [c["id"] for c in content["chapters"]], "lines": len(T.used)}))


if __name__ == "__main__":
    main()
