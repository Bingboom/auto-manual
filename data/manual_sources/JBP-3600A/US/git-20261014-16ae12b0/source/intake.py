"""Generate the JBP-3600A US English, French and Spanish documents from the archived native PDF.

Run from the repository root: ``python3 data/manual_sources/JBP-3600A/US/git-20261014-16ae12b0/source/intake.py``.
For each language it writes ``source/<lang>/content.json`` and ``source/<lang>/coverage.json``
and fails while any body word is unclassified. Regions are reviewed PDF point rectangles
(``GEOMETRY``: the three printed bodies share one layout, shifted by their translations);
components are the shared ones the JBP-2000B and other frozen US manuals use.
"""
from copy import deepcopy
import html
import json
from pathlib import Path
import sys

from bs4 import BeautifulSoup

REPO = next(p for p in Path(__file__).resolve().parents if (p / "build.py").is_file())
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from native import LANGUAGES, OFFSET, Native, SOURCE, attrs, dump  # noqa: E402
from tools.component_specs.callout import display_label  # noqa: E402
from tools.component_specs.fcc import fcc_semantic_projection, fcc_component_spec  # noqa: E402
from tools.component_specs.inbox import inbox_component_spec  # noqa: E402
from tools.component_specs.inbox_adapters import web_inbox_projection  # noqa: E402
from tools.component_specs.manual_tables import (  # noqa: E402
    symbol_icon_component_spec, symbol_signal_component_spec, troubleshooting_component_spec,
)
from tools.component_specs.reference_table import reference_table_component_spec  # noqa: E402
from tools.component_specs.spec_table import spec_table_component_spec  # noqa: E402
from tools.component_specs.warranty import (  # noqa: E402
    warranty_lead_component_spec, warranty_section_component_spec, warranty_years_component_spec,
)
from tools.web.frozen_ai_flow import callout as shared_callout  # noqa: E402
from tools.web.frozen_ai_flow import heading, node, paragraph, table, text  # noqa: E402

FULL = 341.0  # right edge of the print's full-width text frame


def callout(n, label, body, *, variant):
    """Shared callout strip with the print's own signal word."""
    return shared_callout(display_label(label), body, variant=variant, language=n.language,
                          source_ref=f"native-pdf/{n.current['id']}/{variant}-{len(n.selections)}")


def cell(children, *, header=False, cls=None, **fields):
    if isinstance(children, str):
        children = [text(children)]
    extra = {"presentation": attrs(cls)} if cls else {}
    return node("table_cell", children, header=header, **fields, **extra)


def group(children, css):
    return node("group", children, role="container", presentation=attrs(css))


def insert_control(n, flow, marker, slot):
    """Place a source inline glyph right after the words the print sets before it."""
    image = n.control(slot)

    def visit(children):
        for i, child in enumerate(children):
            if child["kind"] == "text" and marker in child["text"]:
                before, after = child["text"].split(marker, 1)
                # The shared callout compares stripped text runs; the stylesheet spaces the glyph.
                children[i:i + 1] = [text(before + marker), image, text(after.lstrip())]
                return True
            if child.get("children") and visit(child["children"]):
                return True
        return False

    for block in flow:
        if visit([block]):
            return flow
    raise ValueError(f"inline glyph marker not found: {marker!r}")


def flow_plain(block):
    if block["kind"] == "text":
        return block["text"]
    if block["kind"] == "line_break":
        return "\n"
    return "".join(flow_plain(child) for child in block.get("children", []))


def flow_markup(block):
    if block["kind"] == "text":
        return html.escape(block["text"])
    if block["kind"] == "line_break":
        return "<br>"
    inner = "".join(flow_markup(child) for child in block.get("children", []))
    return f"<strong>{inner}</strong>" if block["kind"] == "strong" else inner


def rich(flow, key):
    """One print paragraph as a shared-table html/text pair; print breaks stay <br>."""
    if len(flow) != 1 or flow[0]["kind"] != "paragraph":
        raise ValueError(f"{key}: expected one print paragraph")
    return {key + "_html": flow_markup(flow[0]), key + "_text": " ".join(flow_plain(flow[0]).split())}


def html_blocks(flow):
    """Warranty section blocks from print paragraphs and printed bullet lists."""
    blocks = []
    for b in flow:
        if b["kind"] == "list":
            items = [" ".join(flow_plain(item).split()) for item in b["children"]]
            markup = "".join("<li>" + flow_markup(item) + "</li>" for item in b["children"])
            blocks.append({"kind": "list", "items": items, "html": "<ul>" + markup + "</ul>"})
        else:
            blocks.append({"kind": "paragraph", "text": " ".join(flow_plain(b).split()),
                           "html": "<p>" + flow_markup(b) + "</p>"})
    return blocks


def lines_of(flow):
    """Printed statements of one paragraph (split at its print line breaks)."""
    return [" ".join(part.split()) for b in flow for part in flow_plain(b).split("\n")]


def inbox_carrier(spec):
    cards = web_inbox_projection(spec)["cards"]
    return [table([[node("table_cell", [node("image", source=c["image_ref"], alt=c["alt"]), paragraph(c["label"])],
                         header=False) for c in cards]])]


def fcc_carrier(spec):
    payload = fcc_semantic_projection(spec)
    result = [paragraph(v) for v in payload["opening_copy"]]
    for block in payload["left_blocks"] + payload["right_blocks"]:
        if block["kind"] == "list":
            result.append(node("list", [node("list_item", [text(v)]) for v in block["items"]], ordered=False))
        else:
            result.append(paragraph(" ".join(filter(None, [block.get("label"), block["text"]]))))
    return result


def spec_carrier(spec):
    slot = lambda role: spec.slot(role).content  # noqa: E731
    title = node("heading", [node("inline_group", [text(slot("section_title"))],
                                  presentation=attrs("hb-spec-section-text"))], level=2,
                 presentation=attrs("hb-spec-section hb-spec-group"))
    rows = [[cell(r["label"] if i == 0 else "", header=True), cell(v["text"])]
            for r in slot("rows") for i, v in enumerate(r["values"])]
    return [title, table(rows)]


# Reviewed regions per printed body, in PDF points on the English page numbers (the
# French and Spanish bodies sit 8 and 16 pages later). Shared x splits stay inline below.
GEOMETRY = {
    "en": {
        "safety": 150, "symbols_title": (152, 175), "signal_head": (182, 197), "signal_split": 105,
        "signal_rows": [(198, 222), (222, 248), (248, 275), (275, 298)],
        "fcc_note": [[70, 30, 190, 60]], "fcc_limits": ([30, 60, 190, 135], [193, 30, 345, 57]),
        "fcc_measures": [193, 57, 345, 110], "fcc_mod": [193, 110, 345, 135],
        "lcd_rows": [(113, 156), (156, 171)], "note": ([36, 311, 78, 353], [78, 311, 336, 353]),
        "lcd_text": (468, 490), "ts_split": 70, "connections": ((238, 260), (262, 284)),
        "caution": ([30, 286, 90, 332], [90, 286, 341, 332]), "notes": ([30, 199, 72, 250], [72, 199, 341, 250]),
        "icon_after": "of the", "warning": ([30, 82, 80, 110], [80, 82, 339, 110]),
        "solar": ([35, 284, 160, 298], [160, 284, 225, 298], (298, 318)), "storage": 131,
        "lead": (55, 82), "local": (84, 98),
        "sections": [((99, 113), (113, 160)), ((169, 183), None), ((268, 282), (282, 312)),
                     ((320, 334), (334, 356)), ((366, 380), (380, 450)), ((459, 474), (476, 495))],
        "years": ([(35, 215, 210.0), (216, 341, 333.0)], 30, (188, 203.5, 213.5), (214, 260)),
    },
    "fr": {
        "safety": 163, "symbols_title": (165, 190), "signal_head": (194, 209), "signal_split": 130,
        "signal_rows": [(209, 233), (233, 254), (254, 279), (279, 300)],
        "fcc_note": [[60, 30, 190, 54], [30, 54, 190, 60.5]], "fcc_limits": ([30, 60.5, 190, 135], [190, 33, 345, 50]),
        "fcc_measures": [193, 52, 345, 100], "fcc_mod": [190, 100, 345, 131],
        "lcd_rows": [(113, 159), (159, 180)], "note": ([36, 315, 95, 365], [95, 315, 336, 365]),
        "lcd_text": (473.5, 492), "ts_split": 80, "connections": ((232, 256), (256, 282)),
        "caution": ([30, 282, 84, 325], [84, 282, 341, 325]), "notes": ([30, 200, 86, 250], [86, 200, 341, 250]),
        "icon_after": "de l’icône", "warning": ([30, 82, 95, 110], [95, 82, 339, 110]),
        "solar": ([35, 274, 195, 290], [195, 274, 270, 290], (290, 318)), "storage": 137,
        "lead": (54, 85), "local": (85, 98),
        "sections": [((97, 112), (112, 170)), ((172, 189), None), ((270, 287), (287, 314)),
                     ((318, 334), (334, 362)), ((366, 381), (381, 462)), ((465, 482), (482, 498))],
        "years": ([(35, 230, 228.0), (232, 341, 336.0)], 30, (190, 207, 219), (219, 265)),
    },
    "es": {
        "safety": 160, "symbols_title": (163, 188), "signal_head": (192, 207), "signal_split": 128,
        "signal_rows": [(207, 231), (231, 255), (255, 278), (278, 300)],
        "fcc_note": [[60, 30, 190, 53], [30, 53, 190, 59.3]], "fcc_limits": ([30, 59.3, 190, 135], [190, 32, 345, 54]),
        "fcc_measures": [193, 55, 345, 100], "fcc_mod": [190, 99, 345, 130],
        "lcd_rows": [(113, 153), (153, 172)], "note": ([36, 311, 95, 353], [95, 311, 336, 353]),
        "lcd_text": (466.6, 490), "ts_split": 80, "connections": ((224, 248), (249, 272)),
        "caution": ([30, 272, 92, 322], [92, 272, 341, 322]), "notes": ([30, 198, 100, 252], [100, 198, 341, 252]),
        "icon_after": "del icono", "warning": ([30, 80, 95, 108], [95, 80, 339, 108]),
        "solar": ([35, 274, 184, 290], [184, 274, 270, 290], (290, 312)), "storage": 137,
        "lead": (54, 80), "local": (80, 97),
        "sections": [((97, 112), (112, 168)), ((170, 188), None), ((270, 287), (287, 316)),
                     ((322, 337), (337, 360)), ((365, 380), (380, 455)), ((462, 477), (477, 496))],
        "years": ([(35, 222, 220.0), (224, 341, 333.0)], 30, (188, 206, 218), (218, 264)),
    },
}


def make(language):
    n = Native(language)
    g = GEOMETRY[language]
    p = {page: page + OFFSET[language] for page in range(4, 12)}
    symbols = [r for r in json.loads((SOURCE / "source/symbols.json").read_text()) if r["language"] == language]
    plain = lambda flow: " ".join(" ".join(flow_plain(b).split()) for b in flow)  # noqa: E731

    # ---- p4 IMPORTANT SAFETY INFORMATION, MEANING OF SYMBOLS ----------------------
    n.chapter("safety", p[4], [25, 28, 345, 51])
    n.add(*n.prose(p[4], [25, 51, 345, g["safety"]], right=FULL))
    n.chapter("symbols", p[4], [25, *g["symbols_title"][:1], 345, g["symbols_title"][1]])
    y0, y1 = g["signal_head"]
    split = g["signal_split"]
    headers = [rich([paragraph(n.t(p[4], [30, y0, split, y1]))], "content"),
               rich([paragraph(n.t(p[4], [split, y0, 345, y1]))], "content")]
    rows = []
    for y0, y1 in g["signal_rows"]:
        label = n.t(p[4], [30, y0, split, y1])
        rows.append({"label": label, "show_icon": True,
                     **rich(n.prose(p[4], [split, y0, 345, y1], right=FULL), "meaning")})
    n.add(n.comp(symbol_signal_component_spec, lambda spec: None, accessibility_label="Signal words",
                 headers=headers, rows=rows))
    headers = [rich([paragraph(n.t(p[4], box))], "content")
               for box in ([30, 304, 70, 320], [70, 304, 185, 320], [187, 304, 222, 320], [222, 304, 345, 320])]
    panels = [[], []]
    for index, row in enumerate(symbols):
        n.take(p[4], row["glyph_search_box"], purpose="native-symbol/" + row["shared_symbol_key"])
        right = 182.0 if row["glyph_search_box"][0] < 100 else FULL
        meaning = rich(n.prose(p[4], row["caption_search_box"], right=right), "meaning")
        panels[0 if right < 200 else 1].append({"asset_index": index, "icon_alt": meaning["meaning_text"], **meaning})
    n.add(n.comp(symbol_icon_component_spec, lambda spec: None, accessibility_label="Meaning of symbols",
                 headers=headers, panels=panels, icon_refs=[r["local_path"] for r in symbols]))

    # ---- p5 FCC (printed under MEANING OF SYMBOLS, without a heading) ------------------
    n.take(p[5], [29, 30, 71, 68], purpose="native-symbol/fcc")
    note = n.joined(p[5], " ".join(n.t(p[5], box) for box in g["fcc_note"]))
    label, body = note.split(":", 1)
    label = label.rstrip() + (" :" if label.endswith(" ") else ":")
    left, right_top = g["fcc_limits"]
    limits = n.joined(p[5], n.t(p[5], left) + " " + plain(n.prose(p[5], right_top, right=337.5)))
    measures = lines_of(n.prose(p[5], g["fcc_measures"], right=337.5))
    mod_label, mod_body = plain(n.prose(p[5], g["fcc_mod"], right=337.5)).split(":", 1)
    # Columns as printed. The shared FCC renderer runs the two left paragraphs together
    # (recorded in the README). The wrapper keeps MEANING OF SYMBOLS visible: the shared
    # style hides the heading of a section whose direct child is the FCC figure.
    fcc = n.comp(fcc_component_spec, fcc_carrier, accessibility_label="FCC", opening_copy=[],
                 mark_asset_ref=n.glyphs["fcc-mark"]["local_path"],
                 left_blocks=[{"kind": "paragraph", "label": label, "text": body.strip()},
                              {"kind": "paragraph", "label": "", "text": limits}],
                 right_blocks=[{"kind": "list", "items": measures},
                               {"kind": "paragraph", "label": mod_label + ":", "text": mod_body.strip()}])
    n.add(group([fcc], "native-fcc"))

    # ---- p5 WHAT'S IN THE BOX, PRODUCT OVERVIEW ------------------------------------
    n.chapter("in-the-box", p[5], [25, 160, 345, 190])
    n.take(p[5], [30, 196, 345, 222], purpose="shared-inbox-live-ordinal")
    cards = []
    for slot, (x0, x1) in [("inbox-unit", (30, 123)), ("inbox-cable", (137, 230)), ("inbox-manual", (246, 339))]:
        n.embedded(slot)
        name = n.t(p[5], [x0, 282, x1, 300])
        cards.append({"image_ref": n.figures[slot]["local_path"], "label": name, "alt": name})
    n.add(n.comp(inbox_component_spec, inbox_carrier, accessibility_label=n.current["title"], cards=cards,
                 tip_label="", tip_body="", require_tip=False, variant="responsive-card-grid"))
    n.chapter("product-overview", p[5], [25, 325, 345, 360])
    # Stacked views, as on the JBP-2000B and JBP-3600A EU Web manuals.
    for box, slot in [([35, 361, 162, 380], "overview-front"), ([165, 361, 345, 380], "overview-left")]:
        n.add(heading(n.t(p[5], box), level=3), n.figure(slot, width="wide"))

    # ---- p6 LCD DISPLAY, OPERATIONS --------------------------------------------------
    n.chapter("lcd-display", p[6], [25, 28, 345, 50])
    n.add(n.figure("lcd-display", width="wide"))
    # The shared LCD description table the JBP-3600A EU Web uses; no header row, as printed.
    rows = []
    for y0, y1 in g["lcd_rows"]:
        # The shared table reads the text back from the HTML, one text run per line.
        rows.append([{"html": flow_markup(b),
                      "text": BeautifulSoup(flow_markup(b), "html.parser").get_text("\n", strip=True)}
                     for b in (n.prose(p[6], [30, y0, 105, y1], right=104.0, every_line=True)[0],
                               n.prose(p[6], [105, y0, 341, y1], right=336.0)[0])])
    n.add(n.comp(reference_table_component_spec, lambda spec: None, variant="lcd-descriptions",
                 label=n.current["title"], headers=[], rows=rows))
    n.chapter("operations", p[6], [25, 182, 345, 210])
    if language == "es":
        # White leftover layer text behind the POWER panel; invisible in the print.
        n.take(p[6], [280, 212, 369, 232], purpose="invisible-print-text")
    n.h(p[6], [35, 210, 200, 228])                               # POWER ON/OFF
    n.add(n.figure("power-on-off", width="wide"))
    label_box, body_box = g["note"]
    n.add(callout(n, n.t(p[6], label_box), n.prose(p[6], body_box, right=326.0), variant="note"))
    n.h(p[6], [35, 362, 345, 390])                               # LCD DISPLAY ON/OFF
    n.add(n.figure("lcd-on-off", width="wide"))
    n.add(*n.prose(p[6], [35, g["lcd_text"][0], 341, g["lcd_text"][1]], right=336.0))

    # ---- p7-8 TROUBLESHOOTING, CONNECTIONS (print order) ---------------------------
    n.chapter("troubleshooting", p[7], [25, 28, 345, 50])
    n.add(*n.prose(p[7], [25, 50, 345, 75], right=FULL))
    split = g["ts_split"]
    headers = [rich([paragraph(n.t(p[7], [28, 78, split, 93]))], "content"),
               rich([paragraph(n.t(p[7], [split, 78, 345, 93]))], "content")]
    rows = []
    for y0, y1 in [(93, 109), (109, 124), (124, 139), (139, 154), (154, 169), (169, 197), (197, 215)]:
        # Codes are centred in their cells: each printed code line is its own line.
        rows.append({**rich(n.prose(p[7], [28, y0, split, y1], right=split, every_line=True), "code"),
                     **rich(n.prose(p[7], [split, y0, 341, y1], right=336.0), "measures")})
    n.add(group([n.comp(troubleshooting_component_spec, lambda spec: None, headers=headers, rows=rows)],
                "native-fit-phone"))
    (t0, t1), (b0, b1) = g["connections"]
    n.chapter("connections", p[7], [25, t0, 345, t1])
    n.add(*n.prose(p[7], [25, b0, 345, b1], right=FULL))
    label_box, body_box = g["caution"]
    n.add(callout(n, n.t(p[7], label_box), n.prose(p[7], body_box, right=FULL), variant="caution"))
    n.add(n.figure("clearance", width="wide"))
    n.add(n.figure("stacking", width="wide"))
    label_box, body_box = g["notes"]
    notes = insert_control(n, n.prose(p[8], body_box, right=FULL), g["icon_after"], "connection-icon")
    n.add(callout(n, n.t(p[8], label_box), notes, variant="note"))
    n.add(n.figure("locking", width="wide"))

    # ---- p9 CHARGING ----------------------------------------------------------------
    n.chapter("charging", p[9], [25, 28, 345, 50])
    n.h(p[9], [35, 52, 345, 67])                                 # CHARGING VIA AC WALL OUTLET
    n.add(*n.prose(p[9], [25, 67, 345, 80], right=FULL))
    label_box, body_box = g["warning"]
    n.add(callout(n, n.t(p[9], label_box), n.prose(p[9], body_box, right=336.0), variant="warning"))
    n.add(n.figure("ac-charging", width="wide"))
    title_box, badge_box, (y0, y1) = g["solar"]
    title, badge = n.t(p[9], title_box), n.t(p[9], badge_box)
    n.add(node("heading", [text(title + " "), node("inline_group", [text(badge)],
                                                    presentation=attrs("native-sold-separately"))], level=3))
    n.add(*n.prose(p[9], [25, y0, 345, y1], right=FULL))
    n.add(n.figure("solar-charging", width="wide"))

    # ---- p10 STORAGE, SPECIFICATIONS -------------------------------------------------
    n.chapter("storage", p[10], [25, 28, 345, 50])
    n.add(*n.prose(p[10], [28, 59, 340, g["storage"]], right=334.5))
    n.chapter("specifications", p[10], [25, 160, 345, 182])
    tables = [([35, 186, 345, 202], [(204, 215.5), (215.5, 226.5), (226.5, 237.5), (237.5, 248.5),
                                      (248.5, 259.5), (259.5, 270.5), (270.5, 282)]),
              ([35, 292, 345, 308], [(310, 324), (324, 336), (336, 348)]),
              ([35, 362, 345, 381], [(383, 395), (395, 409)])]
    for title_box, bands in tables:
        title = n.t(p[10], title_box)
        rows = [[n.t(p[10], [28, y0, 180, y1]), n.t(p[10], [180, y0, 341, y1])] for y0, y1 in bands]
        n.add(n.comp(spec_table_component_spec, spec_carrier, section_title=title, rows=rows))

    # ---- p11 WARRANTY ---------------------------------------------------------------
    n.chapter("warranty", p[11], [25, 28, 345, 50])
    lead = n.t(p[11], [30, g["lead"][0], 345, g["lead"][1]])
    local = n.t(p[11], [25, g["local"][0], 345, g["local"][1]])
    n.add(n.comp(warranty_lead_component_spec, lambda spec: None, accessibility_label=n.current["title"],
                 lead_html="<strong>" + html.escape(lead) + "</strong>", local_note_html=html.escape(local)))
    for index, ((t0, t1), body) in enumerate(g["sections"], start=1):
        title = n.t(p[11], [38, t0, 240, t1])
        n.add(heading(title, level=3))
        if body is None:
            columns, number_width, (u0, u1, name1), (b0, b1) = g["years"]
            periods = []
            for x0, x1, right in columns:
                number = n.t(p[11], [x0, u0 - 3, x0 + number_width, u1 + 12])
                unit = n.t(p[11], [x0 + 20, u0, x0 + 80, u1])
                name = n.t(p[11], [x0 + 20, u1, x1, name1])
                flow = n.prose(p[11], [x0, b0, x1, b1], right=right)
                periods.append({"number": number, "unit": unit, "label": name,
                                "body_html": flow_markup(flow[0]), "body_text": " ".join(flow_plain(flow[0]).split())})
            n.add(n.comp(warranty_years_component_spec, lambda spec: None, title=title, periods=periods))
            continue
        n.add(n.comp(warranty_section_component_spec, lambda spec: None, title=title, section_index=index,
                     blocks=html_blocks(n.prose(p[11], [35, body[0], 341, body[1]], right=FULL))))

    problems = n.finish()
    print(language, "chapters", len(n.chapters), "problems", len(problems))
    return problems


if __name__ == "__main__":
    failures = {}
    for lang in LANGUAGES:
        problems = make(lang)
        if problems:
            failures[lang] = deepcopy(problems)
    dump(SOURCE / "source/unmapped.json", failures)
    if failures:
        raise SystemExit("Unmapped or unbalanced native words: see source/unmapped.json")
