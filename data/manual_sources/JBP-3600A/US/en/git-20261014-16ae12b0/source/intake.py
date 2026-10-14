"""Generate the JBP-3600A US English semantic document from the archived native PDF.

Run from the repository root: ``python3 data/manual_sources/JBP-3600A/US/en/git-20261014-16ae12b0/source/intake.py``.
It writes ``source/en/content.json`` and ``source/en/coverage.json`` and fails
while any English body word is unclassified. Regions are reviewed PDF point
rectangles; components are the shared ones the other frozen US manuals use.
"""
from copy import deepcopy
import html
import json
from pathlib import Path
import sys

REPO = next(p for p in Path(__file__).resolve().parents if (p / "build.py").is_file())
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from native import LANGUAGE, Native, SOURCE, attrs, dump  # noqa: E402
from tools.component_specs.callout import display_label  # noqa: E402
from tools.component_specs.fcc import fcc_semantic_projection, fcc_component_spec  # noqa: E402
from tools.component_specs.inbox import inbox_component_spec  # noqa: E402
from tools.component_specs.inbox_adapters import web_inbox_projection  # noqa: E402
from tools.component_specs.manual_tables import (  # noqa: E402
    symbol_icon_component_spec, symbol_signal_component_spec, troubleshooting_component_spec,
)
from tools.component_specs.spec_table import spec_table_component_spec  # noqa: E402
from tools.component_specs.warranty import (  # noqa: E402
    warranty_lead_component_spec, warranty_section_component_spec, warranty_years_component_spec,
)
from tools.web.frozen_ai_flow import callout as shared_callout  # noqa: E402
from tools.web.frozen_ai_flow import heading, node, paragraph, table, text  # noqa: E402

FULL = 341.0  # right edge of the print's full-width text frame (pages 4-11)


def callout(n, label, body, *, variant):
    """Shared callout strip with the print's own signal word."""
    return shared_callout(display_label(label), body, variant=variant, language=LANGUAGE,
                          source_ref=f"native-pdf/{n.current['id']}/{variant}-{len(n.selections)}")


def cell(children, *, header=False, cls=None, **fields):
    if isinstance(children, str):
        children = [text(children)]
    extra = {"presentation": attrs(cls)} if cls else {}
    return node("table_cell", children, header=header, **fields, **extra)


def grid(head_rows, body_rows, css):
    """A native table in the shared scroll wrapper; head rows become <thead>."""
    parts = []
    if head_rows:
        parts.append(node("table_head", [node("table_row", r) for r in head_rows]))
    parts.append(node("table_body", [node("table_row", r) for r in body_rows]))
    table_node = node("table", parts, presentation=attrs("manual-table " + css))
    return node("group", [table_node], role="container",
                presentation=attrs("table-wrapper docutils container native-table-wrap"))


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
    """Warranty section blocks from print paragraphs."""
    return [{"kind": "paragraph", "text": " ".join(flow_plain(b).split()), "html": "<p>" + flow_markup(b) + "</p>"}
            for b in flow]


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


def make():
    n = Native()
    symbols = json.loads((SOURCE / "source/symbols.json").read_text())

    # ---- p4 IMPORTANT SAFETY INFORMATION, MEANING OF SYMBOLS ----------------------
    n.chapter("safety", 4, [25, 28, 345, 50])
    n.add(*n.prose(4, [25, 50, 345, 150], right=FULL))
    n.chapter("symbols", 4, [25, 152, 345, 175])
    headers = [rich([paragraph(n.t(4, [30, 182, 105, 197]))], "content"),
               rich([paragraph(n.t(4, [105, 182, 345, 197]))], "content")]
    rows = []
    for y0, y1 in [(198, 222), (222, 248), (248, 275), (275, 298)]:
        label = n.t(4, [30, y0, 105, y1])
        rows.append({"label": label, "show_icon": True, **rich(n.prose(4, [105, y0, 345, y1], right=FULL), "meaning")})
    n.add(n.comp(symbol_signal_component_spec, lambda spec: None, accessibility_label="Signal words",
                 headers=headers, rows=rows))
    headers = [rich([paragraph(n.t(4, box))], "content")
               for box in ([30, 304, 70, 320], [70, 304, 185, 320], [187, 304, 222, 320], [222, 304, 345, 320])]
    panels = [[], []]
    for index, row in enumerate(symbols):
        n.take(4, row["glyph_search_box"], purpose="native-symbol/" + row["shared_symbol_key"])
        right = 182.0 if row["glyph_search_box"][0] < 100 else FULL
        meaning = rich(n.prose(4, row["caption_search_box"], right=right), "meaning")
        panels[0 if right < 200 else 1].append({"asset_index": index, "icon_alt": meaning["meaning_text"], **meaning})
    n.add(n.comp(symbol_icon_component_spec, lambda spec: None, accessibility_label="Meaning of symbols",
                 headers=headers, panels=panels, icon_refs=[r["local_path"] for r in symbols]))

    # ---- p5 FCC (printed under MEANING OF SYMBOLS, without a heading) ------------------
    n.take(5, [29, 30, 71, 68], purpose="native-symbol/fcc")
    note = n.t(5, [70, 30, 190, 60])
    label, body = note.split(":", 1)
    limits = n.t(5, [30, 60, 190, 135]) + " " + n.t(5, [193, 30, 345, 57])
    measures = lines_of(n.prose(5, [193, 57, 345, 110], right=337.5))
    modification = n.t(5, [193, 110, 345, 135])
    mod_label, mod_body = modification.split(":", 1)
    # Columns as printed. The shared FCC renderer runs the two left paragraphs together
    # (recorded in the README). The wrapper keeps MEANING OF SYMBOLS visible: the shared
    # style hides the heading of a section whose direct child is the FCC figure.
    fcc = n.comp(fcc_component_spec, fcc_carrier, accessibility_label="FCC", opening_copy=[],
                 mark_asset_ref="assets/fcc_mark.svg",
                 left_blocks=[{"kind": "paragraph", "label": label + ":", "text": body.strip()},
                              {"kind": "paragraph", "label": "", "text": limits}],
                 right_blocks=[{"kind": "list", "items": measures},
                               {"kind": "paragraph", "label": mod_label + ":", "text": mod_body.strip()}])
    n.add(group([fcc], "native-fcc"))

    # ---- p5 WHAT'S IN THE BOX, PRODUCT OVERVIEW ------------------------------------
    n.chapter("in-the-box", 5, [25, 160, 345, 190])
    n.take(5, [30, 198, 345, 218], purpose="shared-inbox-live-ordinal")
    cards = []
    for slot, box in [("inbox-unit", [30, 286, 123, 300]), ("inbox-cable", [137, 286, 230, 300]),
                      ("inbox-manual", [246, 286, 339, 300])]:
        n.embedded(slot)
        name = n.t(5, box)
        cards.append({"image_ref": n.figures[slot]["local_path"], "label": name, "alt": name})
    n.add(n.comp(inbox_component_spec, inbox_carrier, accessibility_label=n.current["title"], cards=cards,
                 tip_label="", tip_body="", require_tip=False, variant="responsive-card-grid"))
    n.chapter("product-overview", 5, [25, 325, 345, 350])
    views = []
    for box, slot in [([35, 362, 150, 376], "overview-front"), ([160, 362, 345, 376], "overview-left")]:
        views.append(group([heading(n.t(5, box), level=3), n.figure(slot, width="view")], "native-view"))
    n.add(group(views, "native-views " + "native-views-pair"))

    # ---- p6 LCD DISPLAY, OPERATIONS --------------------------------------------------
    n.chapter("lcd-display", 6, [25, 28, 345, 50])
    n.add(n.figure("lcd-display", width="wide"))
    rows = []
    for y0, y1 in [(113, 156), (156, 171)]:
        name = n.prose(6, [30, y0, 105, y1], right=104.0)
        rows.append([cell(name[0]["children"], cls="native-lcd-name"),
                     cell(n.prose(6, [105, y0, 341, y1], right=336.0)[0]["children"])])
    n.add(grid([], rows, "native-print-grid native-lcd-table native-fit"))
    n.chapter("operations", 6, [25, 182, 345, 203])
    n.h(6, [35, 208, 345, 224])                                  # POWER ON/OFF
    note = callout(n, n.t(6, [36, 311, 78, 353]), n.prose(6, [78, 311, 336, 353], right=326.0), variant="note")
    n.add(group([n.figure("power-on-off", width="wide"), note], "native-frame"))
    n.h(6, [35, 362, 345, 378])                                  # LCD DISPLAY ON/OFF
    strip = n.prose(6, [35, 468, 341, 490], right=336.0)
    for block in strip:
        block["presentation"] = attrs("native-strip")
    n.add(group([n.figure("lcd-on-off", width="wide"), *strip], "native-frame"))

    # ---- p7-8 TROUBLESHOOTING, CONNECTIONS ------------------------------------------
    n.chapter("troubleshooting", 7, [25, 28, 345, 50])
    n.add(*n.prose(7, [25, 50, 345, 75], right=FULL))
    headers = [rich([paragraph(n.t(7, [28, 78, 70, 93]))], "content"),
               rich([paragraph(n.t(7, [70, 78, 345, 93]))], "content")]
    rows = []
    for y0, y1 in [(93, 109), (109, 124), (124, 139), (139, 154), (154, 169), (169, 197), (197, 215)]:
        # Codes are centred in their cells: each printed code line is its own line.
        rows.append({**rich(n.prose(7, [28, y0, 70, y1], right=70.0, every_line=True), "code"),
                     **rich(n.prose(7, [70, y0, 341, y1], right=336.0), "measures")})
    n.add(group([n.comp(troubleshooting_component_spec, lambda spec: None, headers=headers, rows=rows)],
                "native-fit-phone"))
    n.chapter("connections", 7, [25, 238, 345, 260])
    n.add(*n.prose(7, [25, 262, 345, 284], right=FULL))
    n.add(callout(n, n.t(7, [30, 286, 90, 332]), n.prose(7, [90, 286, 341, 332], right=FULL), variant="caution"))
    n.add(n.figure("clearance", width="wide"))
    n.add(n.figure("stacking", width="wide"))
    notes = insert_control(n, n.prose(8, [72, 199, 341, 250], right=FULL), "of the", "connection-icon")
    n.add(callout(n, n.t(8, [30, 199, 72, 250]), notes, variant="note"))
    n.add(n.figure("locking", width="wide"))

    # ---- p9 CHARGING ----------------------------------------------------------------
    n.chapter("charging", 9, [25, 28, 345, 50])
    n.h(9, [35, 52, 345, 67])                                    # CHARGING VIA AC WALL OUTLET
    n.add(*n.prose(9, [25, 67, 345, 80], right=FULL))
    n.add(callout(n, n.t(9, [30, 82, 80, 110]), n.prose(9, [80, 82, 339, 110], right=336.0), variant="warning"))
    n.add(n.figure("ac-charging", width="wide"))
    title = n.t(9, [35, 284, 160, 298])
    badge = n.t(9, [160, 284, 225, 298])
    n.add(node("heading", [text(title + " "), node("inline_group", [text(badge)],
                                                    presentation=attrs("native-sold-separately"))], level=3))
    n.add(*n.prose(9, [25, 298, 345, 318], right=FULL))
    n.add(n.figure("solar-charging", width="wide"))

    # ---- p10 STORAGE, SPECIFICATIONS -------------------------------------------------
    n.chapter("storage", 10, [25, 28, 345, 50])
    n.add(group(n.prose(10, [28, 59, 340, 131], right=334.5), "native-panel"))
    n.chapter("specifications", 10, [25, 160, 345, 182])
    tables = [([35, 186, 345, 202], [(204, 215.5), (215.5, 226.5), (226.5, 237.5), (237.5, 248.5),
                                      (248.5, 259.5), (259.5, 270.5), (270.5, 282)]),
              ([35, 292, 345, 308], [(310, 324), (324, 336), (336, 348)]),
              ([35, 362, 345, 378], [(383, 395), (395, 407)])]
    for title_box, bands in tables:
        title = n.t(10, title_box)
        rows = [[n.t(10, [28, y0, 180, y1]), n.t(10, [180, y0, 341, y1])] for y0, y1 in bands]
        n.add(n.comp(spec_table_component_spec, spec_carrier, section_title=title, rows=rows))

    # ---- p11 WARRANTY ---------------------------------------------------------------
    n.chapter("warranty", 11, [25, 28, 345, 50])
    lead, local = n.t(11, [30, 55, 345, 82]), n.t(11, [25, 84, 345, 98])
    n.add(n.comp(warranty_lead_component_spec, lambda spec: None, accessibility_label=n.current["title"],
                 lead_html="<strong>" + html.escape(lead) + "</strong>", local_note_html=html.escape(local)))
    sections = [([38, 99, 200, 113], [35, 113, 341, 160]), ([38, 169, 200, 183], None),
                ([38, 268, 200, 282], [35, 282, 341, 312]), ([38, 320, 200, 334], [35, 334, 341, 356]),
                ([38, 366, 200, 380], [35, 380, 341, 450]), ([38, 459, 200, 474], [35, 476, 341, 495])]
    for index, (title_box, body_box) in enumerate(sections, start=1):
        title = n.t(11, title_box)
        n.add(heading(title, level=3))
        if body_box is None:
            periods = []
            for x0, x1, right in [(35, 215, 210.0), (216, 341, 333.0)]:
                number = n.t(11, [x0, 185, x0 + 30, 215])
                unit = n.t(11, [x0 + 22, 188, x0 + 80, 203.5])
                name = n.t(11, [x0 + 22, 203.5, x1, 213.5])
                body = n.prose(11, [x0, 214, x1, 260], right=right)
                periods.append({"number": number, "unit": unit, "label": name,
                                "body_html": flow_markup(body[0]), "body_text": " ".join(flow_plain(body[0]).split())})
            n.add(n.comp(warranty_years_component_spec, lambda spec: None, title=title, periods=periods))
            continue
        n.add(n.comp(warranty_section_component_spec, lambda spec: None, title=title, section_index=index,
                     blocks=html_blocks(n.prose(11, body_box, right=FULL))))

    problems = n.finish()
    print("chapters", len(n.chapters), "problems", len(problems))
    return problems


if __name__ == "__main__":
    problems = make()
    dump(SOURCE / "source/unmapped.json", deepcopy(problems))
    if problems:
        raise SystemExit("Unmapped or unbalanced native words: see source/unmapped.json")
