"""Generate the JE-300E EU English semantic document from the archived native booklet.

Run from the repository root:
``python3 data/manual_sources/JE-300E/EU/en/git-20261016-50b910fd/source/intake.py``.
It writes ``source/en/content.json`` and ``source/en/coverage.json`` and fails while
any English word in scope is unclassified. Regions are reviewed PDF point rectangles.
Every printed block maps to a shared component or plain shared flow (see
``audit/component-map.json``): no package class, inline style or plain table.
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

from native import Native, SOURCE, dump  # noqa: E402
from tools.component_specs.callout import display_label  # noqa: E402
from tools.component_specs.inbox import inbox_component_spec  # noqa: E402
from tools.component_specs.inbox_adapters import web_inbox_projection  # noqa: E402
from tools.component_specs.lcd_mode import lcd_mode_component_spec  # noqa: E402
from tools.component_specs.manual_tables import (  # noqa: E402
    lcd_icon_component_spec, symbol_icon_component_spec, symbol_signal_component_spec,
    troubleshooting_component_spec,
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
    return shared_callout(display_label(label), body, variant=variant, language="en",
                          source_ref=f"native-pdf/{n.current['id']}/{variant}-{len(n.selections)}")


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


def pair(value, key):
    return {key + "_html": html.escape(value), key + "_text": value}


def cell_pair(flow):
    item = rich(flow, "x")
    return {"html": item["x_html"], "text": BeautifulSoup(item["x_html"], "html.parser").get_text("\n", strip=True)}


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


def inbox_carrier(spec):
    cards = web_inbox_projection(spec)["cards"]
    return [table([[node("table_cell", [node("image", source=c["image_ref"], alt=c["alt"]), paragraph(c["label"])],
                         header=False) for c in cards]])]


def spec_carrier(spec):
    slot = lambda role: spec.slot(role).content  # noqa: E731
    title = node("heading", [node("inline_group", [text(slot("section_title"))],
                                  presentation={"html": {"attributes": {"class": "hb-spec-section-text"}}})],
                 level=2, presentation={"html": {"attributes": {"class": "hb-spec-section hb-spec-group"}}})
    rows = [[node("table_cell", [text(r["label"] if i == 0 else "")], header=True),
             node("table_cell", [text(v["text"])], header=False)]
            for r in slot("rows") for i, v in enumerate(r["values"])]
    return [title, table(rows)]


def sections(n, pages, *, top=None):
    """Recycling-guide pages: Bold 10 pt lines are subheadings, Bold 8 pt lines sub-subheadings.

    Each body between two headings is read as print prose. Heading geometry comes
    from the native line sizes, so no heading text is typed here.
    """
    for p in pages:
        lines = n.lines(p, [20, top if p == pages[0] and top else 20, 350, 498], record=False)
        marks = [ln for ln in lines if ln.size >= 7.9 and all(strong for _, strong in ln.runs if _.strip())]
        bounds = [(ln.y0, ln.y1, 3 if ln.size >= 9.9 else 4) for ln in marks]
        for index, (y0, y1, level) in enumerate(bounds):
            n.h(p, [20, y0 - 1, 350, y1 + 0.5], level=level)
            end = bounds[index + 1][0] - 1 if index + 1 < len(bounds) else 498
            yield p, [20, y1 + 0.5, 350, end]


def make():
    n = Native()

    # ---- p3 IMPORTANT (English half of the front-matter page) ----------------------
    n.take(3, [30, 30, 54, 50], purpose="printed-badge")                    # US
    n.chapter("introduction", 3, [54, 30, 345, 50])
    n.add(*n.prose(3, [30, 50, 345, 165], right=335.0))

    # ---- p7 IMPORTANT SAFETY INFORMATION --------------------------------------------
    n.chapter("safety", 7, [28, 26, 345, 50])
    n.take(7, [28, 54, 60, 86], purpose="native-symbol/warning-box-triangle")
    # The print boxes this statement with a triangle and no signal word; the shared
    # warning strip carries the word WARNING, as on the JE-3600A EU Web manual.
    n.add(callout(n, "WARNING", n.prose(7, [60, 56, 341, 86], right=336.0), variant="warning"))
    n.add(*n.prose(7, [28, 86, 345, 236], right=FULL))
    n.h(7, [28, 280, 200, 297])                                             # USER MAINTENANCE INSTRUCTIONS
    n.add(*n.prose(7, [26, 298, 345, 330], right=FULL))

    # ---- p7-8 MEANING OF SYMBOLS ----------------------------------------------------
    n.chapter("symbols", 7, [28, 342, 345, 366])
    headers = [pair(n.t(7, [30, 371, 104, 388]), "content"), pair(n.t(7, [104, 371, 341, 388]), "content")]
    rows = []
    for y0, y1 in [(388, 413), (413, 439), (439, 464), (464, 490)]:
        rows.append({"label": n.t(7, [30, y0, 104, y1]), "show_icon": True,
                     **rich(n.prose(7, [104, y0, 341, y1], right=336.0), "meaning")})
    n.add(n.comp(symbol_signal_component_spec, lambda spec: None, accessibility_label="Signal words",
                 headers=headers, rows=rows))
    symbols = json.loads((SOURCE / "source/symbols.json").read_text())
    headers = [pair(n.t(8, box), "content")
               for box in ([30, 28, 68, 44], [68, 28, 186, 44], [186, 28, 222, 44], [222, 28, 341, 44])]
    panels = [[], []]
    for index, row in enumerate(symbols):
        n.take(8, row["glyph_search_box"], purpose="native-symbol/" + row["shared_symbol_key"])
        right = 182.0 if row["glyph_search_box"][0] < 100 else 337.0
        meaning = rich(n.prose(8, row["caption_search_box"], right=right), "meaning")
        panels[0 if right < 200 else 1].append({"asset_index": index, "icon_alt": meaning["meaning_text"], **meaning})
    n.add(n.comp(symbol_icon_component_spec, lambda spec: None, accessibility_label=n.current["title"],
                 headers=headers, panels=panels, icon_refs=[r["local_path"] for r in symbols]))

    # ---- p9 WHAT'S IN THE BOX, PRODUCT OVERVIEW ---------------------------------------
    n.chapter("in_the_box", 9, [30, 26, 345, 50])
    n.take(9, [60, 64, 320, 84], purpose="shared-inbox-live-ordinal")     # 1-4: the shared cards number themselves
    cards = []
    for slot, (x0, x1) in [("inbox-unit", (31, 105)), ("inbox-adapter", (109, 183)),
                           ("inbox-car-cable", (186, 262)), ("inbox-documents", (266, 342))]:
        n.embedded(slot)
        name = n.t(9, [x0, 164, x1, 180])
        cards.append({"image_ref": n.figures[slot]["local_path"], "label": name, "alt": name})
    n.add(n.comp(inbox_component_spec, inbox_carrier, accessibility_label=n.current["title"], cards=cards,
                 tip_label="", tip_body="", require_tip=False, variant="responsive-card-grid"))
    n.chapter("product_overview", 9, [30, 225, 345, 248])
    n.h(9, [36, 254, 200, 272])                                             # FRONT VIEW
    n.add(n.figure("overview-front"))

    # ---- p10-11 LCD DISPLAY -----------------------------------------------------------
    n.chapter("lcd_display", 10, [28, 26, 345, 52])
    n.add(n.figure("lcd-display"))
    glyphs = json.loads((SOURCE / "source/glyphs.json").read_text())
    icons = [g for g in glyphs if g["slot"].startswith("lcd-")]
    grid = [(10, (237, 274.9), (48.7, 91.8, 181.2)), (10, (274.9, 306.1), (48.7, 91.8, 181.2)),
            (10, (306.1, 337.9), (48.7, 91.8, 181.2)), (10, (337.9, 369.0), (48.7, 91.8, 181.2)),
            (10, (369.0, 405.6), (48.7, 91.8, 181.2)), (10, (405.6, 448.8), (48.7, 91.8, 181.2)),
            (10, (448.8, 496.0), (48.7, 91.8, 181.2)), (11, (31.0, 68.9), (47.7, 85.7, 179.0)),
            (11, (68.9, 100.4), (47.7, 85.7, 179.0)), (11, (100.4, 134.3), (47.7, 85.7, 179.0)),
            (11, (134.3, 167.2), (47.7, 85.7, 179.0)), (11, (167.2, 206.0), (47.7, 85.7, 179.0))]
    rows, refs, number = [], [], ""
    for index, (icon, (p, (y0, y1), (c1, c2, c3))) in enumerate(zip(icons, grid, strict=True)):
        if index != 10:  # the print spans number 10 over its high and low temperature rows
            number = n.t(p, [28, y0, c1, y1 if index != 9 else 167.2])
        n.take(p, icon["search_box"], purpose="native-lcd-icon/" + icon["slot"])
        name = n.t(p, [c2, y0, c3, y1])
        description = rich(n.prose(p, [c3, y0, 341, y1], right=336.0), "description")
        refs.append(icon["local_path"])
        rows.append({**pair(number, "number"), **pair(name, "name"), **description,
                     "icon_alt": name, "asset_index": index})
    n.add(n.comp(lcd_icon_component_spec, lambda spec: None, accessibility_label=n.current["title"],
                 rows=rows, icon_refs=refs, icon_locale_policy="exact"))

    # ---- p11-14 OPERATIONS ------------------------------------------------------------
    n.chapter("operations", 11, [28, 232, 345, 256])
    n.h(11, [36, 262, 200, 280])                                            # POWER ON/OFF
    n.add(n.figure("power-on-off"))
    n.h(12, [36, 26, 200, 43])                                              # AC OUTPUT ON/OFF
    n.add(n.figure("ac-output"))
    n.h(12, [36, 232, 200, 250])                                            # DC 12V OUTPUT ON/OFF
    n.add(n.figure("dc-output"))
    n.add(*n.prose(12, [40, 405, 342, 427], right=338.0))                  # lifted from the panel
    n.add(callout(n, n.t(12, [32, 440, 76, 490]), n.prose(12, [76, 440, 341, 490], right=336.0), variant="caution"))
    n.add(callout(n, n.t(13, [30, 32, 73, 77]), n.prose(13, [73, 32, 341, 77], right=331.0), variant="caution"))
    n.h(13, [36, 84, 200, 101])                                             # USB OUTPUT ON/OFF
    n.add(n.figure("usb-output"))
    n.h(13, [36, 256, 200, 273])                                            # ENERGY SAVING MODE
    n.add(*n.prose(13, [40, 286, 330, 351], right=322.0))
    n.add(n.figure("energy-saving"))
    n.add(callout(n, n.t(13, [42, 450, 85, 485]), n.prose(13, [85, 450, 333, 485], right=324.0), variant="note"))
    n.h(14, [34, 24, 200, 41])                                              # LCD SCREEN ON/OFF
    n.embedded("lcd-screen")
    groups = []
    for (y0, y1), bands in [((152, 231.8), [(152, 180.7), (180.7, 204.7), (204.7, 231.8)]),
                            ((231.8, 301), [(231.8, 251.6), (251.6, 271.4), (271.4, 301)])]:
        state = n.t(14, [30, y0, 110.1, y1])
        actions = [{**pair(n.t(14, [110.1, a, 166.1, b]), "action"),
                    **pair(n.t(14, [166.1, a, 332, b]), "description")} for a, b in bands]
        groups.append({**pair(state, "state"), "actions": actions})
    n.add(n.comp(lcd_mode_component_spec, lambda spec: None, accessibility_label="LCD SCREEN ON/OFF",
                 groups=groups, artwork_ref=n.figures["lcd-screen"]["local_path"], artwork_locale_policy="exact"))

    # ---- p14-16 CHARGING --------------------------------------------------------------
    n.chapter("charging", 14, [28, 325, 345, 348])
    n.add(*n.prose(14, [26, 348, 341, 386], right=338.0))
    n.add(*n.prose(14, [30, 386, 200, 400], right=338.0))                  # Fully charge ... first use.
    n.add(callout(n, n.t(14, [40, 404, 75, 453]), n.prose(14, [75, 404, 340, 453], right=334.0), variant="note"))
    n.add(callout(n, n.t(14, [40, 457, 75, 491]), n.prose(14, [75, 457, 340, 491], right=338.0), variant="note"))
    n.h(15, [34, 27, 250, 42])                                              # CHARGING VIA 65W AC ADAPTER
    n.add(*n.prose(15, [28, 42, 341, 53], right=338.0))
    n.add(n.figure("charging-ac"))
    n.h(15, [34, 183, 250, 197])                                            # CHARGING VIA USB-C PORT (100W MAX)
    n.add(*n.prose(15, [28, 196, 341, 207], right=338.0))
    n.add(n.figure("charging-usbc"))
    n.add(callout(n, n.t(15, [34, 346, 62, 362]), n.prose(15, [64, 346, 340, 362], right=336.0), variant="note"))
    n.h(15, [34, 370, 200, 387])                                            # DC INPUT INDICATOR
    n.add(n.figure("dc-input-led"))
    headers = [cell_pair(n.prose(15, [106.2, 389, 176.2, 404.9], right=176.0)),
               cell_pair(n.prose(15, [176.2, 389, 336, 404.9], right=336.0))]
    rows = [[cell_pair(n.prose(15, [106.2, y0, 176.2, y1], right=176.0)),
             cell_pair(n.prose(15, [176.2, y0, 336, y1], right=336.0))]
            for y0, y1 in [(404.9, 427.9), (427.9, 447.5), (447.5, 468)]]
    n.add(n.comp(reference_table_component_spec, lambda spec: None, variant="lcd-actions-compact",
                 label="DC INPUT INDICATOR", headers=headers, rows=rows))
    n.add(callout(n, n.t(15, [34, 476, 62, 492]), n.prose(15, [64, 476, 340, 492], right=336.0), variant="note"))
    n.h(16, [34, 25, 250, 40])                                              # CHARGING VIA SOLAR PANELS (100W MAX)
    n.add(*n.prose(16, [28, 40, 341, 51], right=338.0))
    n.add(n.figure("charging-solar"))
    n.add(*n.prose(16, [28, 178, 341, 197], right=338.0))
    n.add(callout(n, n.t(16, [36, 200, 82, 233]), n.prose(16, [82, 200, 342, 233], right=336.0), variant="caution"))
    n.h(16, [28, 262, 250, 277])                                            # CHARGING WITH A CAR CHARGER
    n.add(*n.prose(16, [28, 276, 341, 297], right=338.0))
    n.add(n.figure("charging-car"))
    n.add(callout(n, n.t(16, [38, 430, 90, 491]), n.prose(16, [90, 430, 342, 491], right=338.0), variant="caution"))

    # ---- p17 STORAGE, TROUBLESHOOTING ------------------------------------------------
    n.chapter("storage", 17, [28, 28, 345, 52])
    n.add(*n.prose(17, [30, 58, 338, 120], right=334.0))
    n.chapter("troubleshooting", 17, [28, 128, 345, 150])
    n.add(*n.prose(17, [26, 151, 341, 172], right=FULL))
    headers = [pair(n.t(17, [29, 175, 55.6, 199]), "content"), pair(n.t(17, [55.6, 175, 341, 199]), "content")]
    rows = []
    # F0-F3: four printed code cells beside one merged measure cell. Operator decision D6
    # (2026-10-16, 「拆成4行」): one row per code, each carrying the merged cell's measure.
    measures = rich(n.prose(17, [55.6, 199, 341, 271.6], right=336.0), "measures")
    for y0, y1 in [(199, 217.2), (217.2, 235.3), (235.3, 253.4), (253.4, 271.6)]:
        rows.append({**pair(n.t(17, [29, y0, 55.6, y1]), "code"), **measures})
    for y0, y1 in [(271.6, 289.7), (289.7, 307.8), (307.8, 387.8), (387.8, 441.1), (441.1, 469.1), (469.1, 498)]:
        rows.append({**pair(n.t(17, [29, y0, 55.6, y1]), "code"),
                     **rich(n.prose(17, [55.6, y0, 341, y1], right=336.0, keep_marks=True), "measures")})
    n.add(n.comp(troubleshooting_component_spec, lambda spec: None, headers=headers, rows=rows))

    # ---- p18 SPECIFICATIONS ---------------------------------------------------------
    n.chapter("specifications", 18, [28, 26, 345, 50])
    tables = [((55, 74), [77, 91.6, 105.1, 118.3, 131.7, 145.0, 158.0, 172]),
              ((180, 198), [201, 215.5, 246]),
              ((255, 273), [273, 296.0, 318.2, 329.4, 342.7, 357.7, 376]),
              ((375, 394), [397, 412.7, 427])]
    for (t0, t1), bounds in tables:
        title = n.t(18, [36, t0, 300, t1])
        rows = []
        for y0, y1 in zip(bounds[:-1], bounds[1:], strict=True):
            label = n.t(18, [29, y0, 126, y1])
            # Each printed value line (2 x AC Output, AC Total Output, DC8020) becomes a value row the
            # label spans, the shared spec table's continuation form.
            lines = [" ".join(line.split()) for b in n.prose(18, [126, y0, 342, y1], right=338.0,
                                                             every_line=True, keep_marks=True)
                     for line in flow_plain(b).split("\n")]
            rows += [(label if i == 0 else "", line) for i, line in enumerate(lines)]
        n.add(n.comp(spec_table_component_spec, spec_carrier, section_title=title, rows=rows))
    n.add(*n.prose(18, [26, 430, 341, 446], right=338.0))                  # ※ USB Type-C ... trademarks
    n.add(callout(n, n.t(18, [36, 454, 62, 470]), n.prose(18, [66, 454, 330, 472], right=324.0), variant="note"))

    # ---- p19 WARRANTY ---------------------------------------------------------------
    n.chapter("warranty", 19, [28, 26, 345, 50])
    lead = n.t(19, [33, 56, 338, 80])
    local = n.t(19, [26, 82, 341, 95])
    n.add(n.comp(warranty_lead_component_spec, lambda spec: None, accessibility_label=n.current["title"],
                 lead_html="<strong>" + html.escape(lead) + "</strong>", local_note_html=html.escape(local)))
    sections_19 = [((97, 112), (112, 160)), ((167, 182), None), ((266, 281), (281, 310)),
                   ((321, 336), (336, 358)), ((369, 384), (384, 452)), ((463, 477), (477, 495))]
    for index, ((t0, t1), body) in enumerate(sections_19, start=1):
        title = n.t(19, [38, t0, 240, t1])
        n.add(heading(title, level=3))
        if body is None:
            periods = []
            for (x0, x1, right), number_box in [((35, 214, 212.0), [40, 182, 62, 216]),
                                                ((216, 337, 330.0), [222, 182, 244, 216])]:
                number = n.t(19, number_box)
                unit = n.t(19, [number_box[2] - 4, 185, number_box[2] + 50, 200.5])
                name = n.t(19, [number_box[2] - 4, 200.5, x1, 212])
                flow = n.prose(19, [x0, 212, x1, 258], right=right)
                periods.append({"number": number, "unit": unit, "label": name,
                                "body_html": "<p>" + flow_markup(flow[0]) + "</p>",
                                "body_text": " ".join(flow_plain(flow[0]).split())})
            n.add(n.comp(warranty_years_component_spec, lambda spec: None, title=title, periods=periods))
            continue
        n.add(n.comp(warranty_section_component_spec, lambda spec: None, title=title, section_index=index,
                     blocks=html_blocks(n.prose(19, [35, body[0], 337, body[1]], right=FULL))))

    # ---- p20-23 RETURN FOR RECYCLING SERVICE ------------------------------------------
    n.chapter("recycling", 20, [28, 27, 345, 50])
    for p, box in sections(n, [20, 21, 22, 23], top=50):
        if p == 23 and box[1] > 400:   # Contact Us: the e-mail line carries the print's envelope pictogram
            n.add(*n.prose(23, [20, box[1], 350, 428], right=FULL))
            n.add(node("paragraph", [n.glyph("glyph-mail-p23"), text(" " + n.t(23, [36, 432, 200, 446]))]))
            continue
        flow = n.prose(p, box, right=342.0)
        for block in flow:
            for leaf in [block, *block.get("children", [])]:
                if leaf.get("kind") == "text":
                    leaf["text"] = n.joined(p, leaf["text"])
        n.add(*flow)

    # ---- p24 HOW TO READ YOUR SERIAL NUMBER -------------------------------------------
    n.chapter("serial_number", 24, [28, 28, 345, 52])
    n.add(*n.prose(24, [26, 60, 341, 88], right=338.0))
    n.add(n.figure("serial-number"))

    # ---- p97 EU Regulations (back cover) --------------------------------------------
    n.chapter("eu-declaration", 97, [36, 362, 120, 380])
    n.add(n.figure("ce-mark"))
    n.add(*n.prose(97, [26, 378, 320, 432], right=310.0))
    n.add(*n.prose(97, [24, 444, 280, 458], right=262.0))                  # MANUFACTURER
    n.add(*n.prose(97, [24, 456, 280, 487], right=262.0))                  # Address
    contact = []
    for slot, box in [("glyph-phone", [36, 486, 96, 500]), ("glyph-mail", [108, 486, 182, 500]),
                      ("glyph-web", [194, 486, 270, 500])]:
        if contact:
            contact.append(text(" "))
        contact += [n.glyph(slot), text(" " + n.t(97, box))]
    n.add(node("paragraph", contact))
    n.add(n.figure("manufacturer-qr"))

    problems = n.finish()
    print("chapters", len(n.chapters), "problems", len(problems))
    return problems


if __name__ == "__main__":
    problems = make()
    dump(SOURCE / "source/unmapped.json", deepcopy(problems))
    if problems:
        raise SystemExit("Unmapped or unbalanced native words: see source/unmapped.json")
