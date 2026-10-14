"""Generate the JA-TS02A US English semantic document from the archived native PDF.

Run from the repository root: ``python3 data/manual_sources/JA-TS02A/US/en/git-20261013-11ce66b1/source/intake.py``.
It writes ``source/en/content.json`` and ``source/en/coverage.json`` and fails
while any English body word is unclassified. Regions are reviewed PDF point
rectangles; components are the shared ones the other frozen US manuals use.
"""
from copy import deepcopy
import html
from pathlib import Path
import sys

REPO = next(p for p in Path(__file__).resolve().parents if (p / "build.py").is_file())
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from native import LANGUAGE, Native, SOURCE, attrs, dump  # noqa: E402
from tools.component_specs.app import app_download_component_spec  # noqa: E402
from tools.component_specs.callout import display_label  # noqa: E402
from tools.component_specs.warranty import (  # noqa: E402
    warranty_lead_component_spec, warranty_section_component_spec,
)
from tools.web.frozen_ai_flow import callout as shared_callout  # noqa: E402
from tools.web.frozen_ai_flow import node, paragraph, text  # noqa: E402

FULL = 342.0      # right edge of the print's full-width text frame (pages 3-19, 24)
APP_TEXT = 317.2  # right edge of the App-guide text frames beside a phone (pages 20-23)
APP_FULL = 302.6  # right edge of full-width App-guide text (pages 20-23)
TRIANGLE = "assets/symbol_warning_triangle_yellow.svg"


def callout(n, label, body, *, variant, lockup=False, shaded=False):
    """Shared callout strip; optional native warning lockup or shaded signal cell."""
    item = shared_callout(display_label(label), body, variant=variant, language=LANGUAGE,
                          source_ref=f"native-pdf/{n.current['id']}/{variant}-{len(n.selections)}")
    carrier = item["carrier_flow"][0]
    classes = carrier["presentation"]["html"]["attributes"]["class"]
    if lockup:
        classes += " hb-source-warning-lockup native-lockup-open"
        label_cell = carrier["children"][0]["children"][0]["children"][0]
        label_cell["children"] = [node("inline_group", [
            node("image", source=TRIANGLE, alt=""), text(display_label(label))],
            presentation=attrs("hb-warning-lockup"))]
    if shaded:
        classes += " hb-callout-label-shaded"
    carrier["presentation"]["html"]["attributes"]["class"] = classes
    return item


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
    table = node("table", parts, presentation=attrs("manual-table " + css))
    return node("group", [table], role="container",
                presentation=attrs("table-wrapper docutils container native-table-wrap"))


def media(art, copy, *, art_first=False, css=""):
    """Print text beside its figure: text and art stay one reading unit."""
    copy_group = node("group", copy, role="container", presentation=attrs("native-media-copy"))
    art_group = node("group", [art], role="container", presentation=attrs("native-media-art"))
    order = [art_group, copy_group] if art_first else [copy_group, art_group]
    return node("group", order, role="container",
                presentation=attrs(("native-media native-media-art-first " if art_first else "native-media ") + css))


def insert_control(n, flow, marker, slot, *, at_end=False):
    """Place a source inline App control where the print leaves its gap."""
    image = n.control(slot)

    def visit(children):
        for i, child in enumerate(children):
            if child["kind"] == "text" and (at_end or marker in child["text"]):
                value = child["text"]
                if at_end:
                    children[i + 1:i + 1] = [text(" "), image]
                    return True
                before, after = value.split(marker, 1)
                children[i:i + 1] = [text(before + marker), image, text(" " + after.lstrip())]
                return True
            if child.get("children") and visit(child["children"]):
                return True
        return False

    for block in flow:
        if visit([block]):
            return flow
    raise ValueError(f"inline control marker not found: {marker!r}")


def make():
    n = Native()

    # ---- p3-5 SAFETY INSTRUCTIONS ------------------------------------------------
    n.take(3, [0, 20, 369, 46], purpose="printed-header")  # US / English / Model badge
    n.chapter("safety", 3, [25, 50, 345, 66])
    n.h(3, [25, 68, 345, 80])                                   # Disclaimer
    n.add(*n.prose(3, [25, 80, 345, 160], right=FULL))
    n.h(3, [25, 162, 345, 176])                                 # Warning
    n.add(*n.prose(3, [25, 176, 345, 500], right=FULL, extra=[(4, [25, 24, 345, 156])]))
    n.h(4, [25, 158, 345, 171])                                 # Caution
    n.add(*n.prose(4, [25, 171, 345, 280], right=FULL))
    n.h(4, [25, 284, 345, 298])                                 # FCC Statement
    n.add(*n.prose(4, [25, 298, 345, 500], right=FULL, keep_marks=True))
    n.h(5, [25, 25, 345, 38])                                   # IC Warning
    n.add(*n.prose(5, [25, 38, 345, 135], right=FULL))
    n.take(5, [24, 135, 64, 212], purpose="native-symbol/ingestion-hazard")
    hazard = n.prose(5, [64, 136, 345, 215], right=FULL)
    n.add(node("group", [node("image", source="assets/symbol_ingestion_hazard.svg", alt=""), *hazard],
               role="container", presentation=attrs("native-ingestion")))
    n.h(5, [25, 222, 345, 236])                                 # Meaning of symbols
    n.add(*n.prose(5, [25, 236, 345, 262], right=FULL))
    head = [[cell(n.t(5, [28, 266, 80, 282]), header=True, scope="col"),
             cell(n.t(5, [80, 266, 345, 282]), header=True, scope="col")]]
    icons = [("assets/symbol_grounding.png", [283, 304]), ("assets/symbol_warning_triangle.svg", [304, 327]),
             ("assets/symbol_electric_shock.svg", [327, 349]), ("assets/symbol_read_manual.svg", [349, 372])]
    rows = []
    for source, (y0, y1) in icons:
        meaning = n.t(5, [80, y0, 345, y1])
        rows.append([cell([node("image", source=source, alt=meaning)], cls="native-symbol-cell"), cell(meaning)])
    n.add(grid(head, rows, "native-print-grid native-symbols native-fit"))

    # ---- p6 SPECIFICATIONS, PACKAGE LIST -----------------------------------------
    n.chapter("specifications", 6, [25, 24, 345, 40])
    tops = [48, 60.4, 72.5, 84.6, 96.7, 108.7, 120.8, 132.9, 145, 157.1, 169.2, 181.2, 193.3,
            205.4, 217.5, 229.6, 241.6, 253.7]
    rows = [[cell(n.t(6, [26, y0, 185, y1])), cell(n.t(6, [185, y0, 345, y1]))]
            for y0, y1 in zip(tops[:-1], tops[1:], strict=True)]
    n.add(grid([], rows, "native-spec-rules native-fit"))
    n.add(*n.prose(6, [25, 254, 345, 268], right=FULL))
    n.chapter("package-list", 6, [25, 283, 345, 298])
    n.add(n.figure("package-list", width="wide"))

    # ---- p7 WHAT YOU NEED ---------------------------------------------------------
    n.chapter("what-you-need", 7, [25, 24, 345, 40])
    n.add(n.figure("optional-tools", width="wide"))
    n.h(7, [25, 131, 345, 146])                                 # Optionals
    head = [[cell(n.t(7, [30, 148, 175, 160]), header=True, scope="col", column_span=2),
             cell(n.t(7, [175, 148, 230, 160]), header=True, scope="col"),
             cell(n.t(7, [230, 148, 275, 160]), header=True, scope="col"),
             cell(n.t(7, [275, 148, 345, 160]), header=True, scope="col")]]
    groups = [([30, 160, 145, 208], [230, 160, 275, 208], [160, 172, 184, 196, 208]),
              ([30, 208, 145, 257], [230, 208, 275, 257], [208, 220, 232, 245, 257])]
    rows = []
    for label_box, current_box, ys in groups:
        label, current = n.t(7, label_box), n.t(7, current_box)
        for i, (y0, y1) in enumerate(zip(ys[:-1], ys[1:], strict=True)):
            colour = n.t(7, [175, y0, 230, y1])
            row = []
            if i == 0:
                row.append(cell(label, row_span=4, cls="native-cable-group"))
            row += [cell(n.t(7, [145, y0, 175, y1])), cell(colour, cls="native-wire native-wire-" + colour.lower())]
            if i == 0:
                row.append(cell(current, row_span=4))
            row.append(cell(n.t(7, [275, y0, 345, y1])))
            rows.append(row)
    rows.append([cell(n.t(7, [30, 258, 145, 300]), cls="native-cable-group"), cell(n.t(7, [145, 258, 175, 300])),
                 cell(n.t(7, [175, 258, 230, 300])), cell(n.t(7, [230, 258, 275, 300])),
                 cell(n.t(7, [275, 258, 345, 300]))])
    n.add(grid(head, rows, "native-print-grid native-cables"))
    n.add(*n.prose(7, [25, 303, 345, 330], right=FULL))

    # ---- p8-10 PRODUCT OVERVIEW ---------------------------------------------------
    n.chapter("product-overview", 8, [25, 26, 345, 44])
    n.h(8, [25, 47, 345, 62])                                   # Dimensions
    n.add(n.figure("dimensions", width="wide"))
    n.add(*n.prose(8, [25, 266, 345, 282], right=FULL))
    n.h(8, [25, 293, 345, 306])                                 # With Deadfront Cover Installed
    n.add(n.figure("covered-overview", width="wide"))
    n.h(9, [20, 25, 345, 37], level=4)                          # IoT Button with Indicator
    n.add(*n.prose(9, [20, 37, 345, 85], right=FULL))
    n.h(9, [20, 85, 345, 97], level=4)                          # Emergency Stop Button
    n.add(*n.prose(9, [20, 97, 345, 120], right=FULL))
    n.h(9, [20, 125, 345, 140])                                 # LED Indicators
    head = [[cell(n.t(9, [30, 141, 88, 153]), header=True, scope="col"),
             cell(n.t(9, [88, 141, 148, 153]), header=True, scope="col"),
             cell(n.t(9, [148, 141, 345, 153]), header=True, scope="col")]]
    bounds = [153, 164.5, 176.5, 188.5, 207.5, 241, 253, 265, 277, 289, 301, 313]
    names = [([30, 153, 88, 188.5], 3), ([30, 188.5, 88, 253], 3), ([30, 253, 88, 289], 3), ([30, 289, 88, 313], 2)]
    rows, index = [], 0
    for box, span in names:
        name = n.t(9, box)
        for k in range(span):
            y0, y1 = bounds[index], bounds[index + 1]
            row = [cell(name, row_span=span, cls="native-led-name")] if k == 0 else []
            row += [cell(n.t(9, [88, y0, 148, y1])), cell(n.t(9, [148, y0, 345, y1]))]
            rows.append(row)
            index += 1
    n.add(grid(head, rows, "native-print-grid native-led"))
    n.h(9, [20, 331, 345, 343])                                 # With Deadfront Cover Removed
    n.add(n.figure("uncovered-overview", width="wide"))
    n.h(10, [20, 28, 345, 40], level=4)                         # Normal Backup Mode
    n.add(*n.prose(10, [20, 40, 345, 70], right=FULL))
    n.add(callout(n, n.t(10, [30, 75, 82, 101]), n.prose(10, [82, 75, 345, 101], right=330.0),
                  variant="caution", shaded=True))
    n.h(10, [20, 106, 345, 118], level=4)                       # UPS Mode
    n.add(*n.prose(10, [20, 118, 345, 183], right=FULL))
    n.add(callout(n, n.t(10, [30, 186, 84, 241]), n.prose(10, [84, 186, 345, 241], right=330.0),
                  variant="caution", shaded=True))

    # ---- p10-11 PRE-INSTALLATION -----------------------------------------------------
    n.chapter("pre-installation", 10, [20, 256, 345, 272])
    n.h(10, [20, 272, 345, 285])                                # System Overview
    n.add(n.figure("system-overview", width="wide"))
    n.add(*n.prose(11, [20, 22, 345, 56], right=FULL))
    n.h(11, [20, 58, 345, 70])                                  # Installation Location
    n.add(*n.prose(11, [20, 72, 345, 86], right=FULL))
    n.take(11, [20, 86, 50, 108], purpose="native-symbol/warning-triangle")
    n.add(callout(n, n.t(11, [50, 88, 150, 106]), n.prose(11, [20, 108, 345, 156], right=FULL),
                  variant="warning", lockup=True))

    # ---- p11-16 INSTALLATION GUIDE -------------------------------------------------
    n.chapter("installation-guide", 11, [20, 157, 345, 172])
    n.add(*n.prose(11, [20, 174, 345, 198], right=FULL))       # Note:
    n.h(11, [20, 198, 345, 210])                                # Surface Mounting
    n.take(11, [20, 210, 50, 236], purpose="native-symbol/warning-triangle")
    lead = n.prose(11, [50, 210, 345, 236], right=320.0)
    first = lead[0]["children"][0]
    label, _, rest = first["text"].partition(":")
    first["text"] = rest.lstrip()
    n.add(callout(n, label, lead, variant="warning", lockup=True))
    n.add(media(n.figure("mounting-brackets", width="art"), n.prose(11, [20, 240, 148, 310], right=141.0)))
    n.add(*n.prose(11, [20, 358, 345, 388], right=FULL))
    n.add(n.figure("mounting-template", width="wide"))
    n.add(*n.prose(12, [20, 24, 345, 40], right=FULL))
    n.add(n.figure("mounting-fasteners", width="wide"))
    n.h(12, [20, 158, 345, 172])                                # Locating STS Cable Entry
    n.add(*n.prose(12, [20, 172, 345, 210], right=FULL))
    n.add(n.figure("cable-entry", width="wide"))
    n.h(12, [20, 385, 345, 398])                                # Electrical Connections
    n.add(*n.prose(12, [20, 400, 345, 500], right=FULL))
    n.add(n.figure("grid-preparation", width="wide"))
    n.h(13, [20, 179, 345, 192], level=4)                       # Connecting the Grid Conductors
    n.add(*n.prose(13, [20, 192, 345, 335], right=FULL))
    n.add(n.figure("grid-wiring", width="wide"))
    n.h(14, [20, 24, 345, 38], level=4)                         # Connecting the Home Load Conductors
    n.add(*n.prose(14, [20, 38, 345, 195], right=347.0))
    n.add(n.figure("load-wiring", width="wide"))
    n.add(*n.prose(14, [20, 384, 345, 398], right=FULL))       # Conductor Tightening Torque
    cols = [20, 48, 115, 165, 210, 282, 345]
    head = [[cell(n.t(14, [x0, 400, x1, 414]), header=True, scope="col") for x0, x1 in zip(cols[:-1], cols[1:], strict=True)]]
    rows = [[cell(n.t(14, [x0, y0, x1, y1])) for x0, x1 in zip(cols[:-1], cols[1:], strict=True)]
            for y0, y1 in [(414, 434), (434, 455), (455, 475), (475, 497)]]
    n.add(grid(head, rows, "native-print-grid native-torque"))
    n.h(15, [20, 31, 345, 44], level=4)                         # Installing an Emergency Stop Button
    n.add(*n.prose(15, [20, 45, 345, 86], right=FULL))
    n.add(n.figure("external-emergency-stop", width="wide"))
    n.h(15, [20, 219, 345, 233], level=4)                       # Installing the Deadfront Cover
    n.take(15, [20, 233, 40, 252], purpose="native-symbol/warning-triangle")
    n.add(callout(n, n.t(15, [40, 235, 150, 252]), n.prose(15, [20, 252, 345, 305], right=FULL, keep_marks=True),
                  variant="warning", lockup=True))
    n.add(*n.prose(15, [20, 305, 345, 332], right=FULL))
    n.add(n.figure("deadfront-installation", width="wide"))
    n.h(16, [20, 24, 345, 37], level=4)                         # Connecting with Power Station
    n.add(*n.prose(16, [20, 37, 345, 50], right=FULL))
    n.add(n.figure("power-station-connections", width="wide"))
    n.h(16, [20, 258, 345, 271], level=4)                       # Energizing
    n.add(*n.prose(16, [20, 271, 345, 296], right=FULL))
    n.h(16, [20, 297, 345, 310], level=4)                       # Locking the Panel
    n.add(n.figure("locking-panel", width="narrow"))
    n.chapter("recommended-breakers", 16, [20, 435, 345, 452])
    n.add(*n.prose(16, [20, 452, 345, 500], right=FULL))

    # ---- p17-19 INTERNET AND INITIALIZATION SETUP -------------------------------------
    n.chapter("internet-setup", 17, [30, 22, 345, 40])
    n.h(17, [30, 40, 345, 52])                                  # To download the App and log in
    n.embedded("app-store-badges")
    n.embedded("app-download-qr")
    columns = [{"role": "store", "text": n.t(17, [30, 52, 345, 77])},
               {"role": "qr", "text": n.t(17, [30, 106, 345, 121])}]
    for column in columns:
        column["html"] = html.escape(column["text"])

    def app_carrier(spec):
        return [node("image", source="assets/app-store-badges.png", alt="App Store and Google Play"),
                *[paragraph(c["text"]) for c in columns]]
    n.add(n.comp(app_download_component_spec, app_carrier, accessibility_label="App download",
                 columns=columns, source_art_ref="assets/app-store-badges.png",
                 store_art_ref="assets/app-store-badges.png", qr_art_ref="assets/app-download-qr.png"))
    n.h(17, [30, 182, 345, 196])                                # To add device
    step = n.prose(17, [30, 196, 165, 252], right=118.0)
    note = n.prose(17, [30, 262, 168, 292], right=157.0, every_line=True)
    for line in note:  # two status lines in one grey panel
        line["presentation"] = attrs("native-status-panel")
    n.add(media(n.figure("iot-pairing", width="art"), step + note))
    step = insert_control(n, n.prose(17, [30, 330, 160, 400], right=124.0), "Tap ", "inline-add-device")
    n.add(media(n.figure("app-add-device", width="phone"), step))
    n.add(*n.prose(18, [20, 24, 345, 50], right=FULL))
    n.add(n.figure("app-wifi", width="wide"))
    n.h(18, [20, 262, 345, 276])                                # Voltage configuration
    first = insert_control(n, n.prose(18, [20, 277, 185, 293], right=FULL), "Tap ", "inline-settings")
    second = insert_control(n, n.prose(18, [185, 277, 345, 293], right=FULL), "", "inline-voltage-config", at_end=True)
    first[0]["children"] += second[0]["children"]
    n.add(*first)
    n.add(n.figure("app-voltage-menu", width="wide"))
    steps = n.prose(19, [20, 24, 345, 60], right=FULL)
    for marker, slot in [("Tap ", "inline-edit"), ("tap the ", "inline-link-circuits"), ("finally tap ", "inline-save")]:
        insert_control(n, steps, marker, slot)
    n.add(*steps)
    n.add(n.figure("app-voltage-settings", width="wide"))
    n.h(19, [20, 195, 345, 207])                                # Edit circuit name
    n.add(*n.prose(19, [20, 207, 345, 220], right=FULL))
    n.add(n.figure("app-circuit-list", width="wide"))
    n.add(*insert_control(n, n.prose(19, [20, 352, 345, 370], right=FULL), "tap ", "inline-edit-name"))
    n.add(n.figure("app-circuit-name", width="wide"))

    # ---- p20-23 JACKERY APP QUICK START GUIDE -------------------------------------
    n.chapter("app-quick-start", 20, [45, 22, 345, 40])
    n.h(20, [45, 43, 345, 62])                                  # Dashboard
    n.add(media(n.figure("app-dashboard", width="phone"), n.prose(20, [160, 66, 345, 190], right=APP_TEXT),
                art_first=True))
    n.h(20, [45, 270, 345, 288])                                # Circuits
    n.add(n.figure("app-circuits", width="wide"))
    n.add(*n.prose(20, [45, 478, 345, 503], right=APP_FULL))
    n.h(21, [45, 24, 345, 42])                                  # Working Modes
    copy = []
    for heading_box, body_box in [([160, 60, 345, 74], [160, 74, 345, 195]), ([160, 197, 345, 211], [160, 211, 345, 250])]:
        copy.append(node("heading", [text(n.t(21, heading_box))], level=3))
        copy += n.prose(21, body_box, right=APP_TEXT)
    n.add(media(n.figure("app-working-modes", width="phone"), copy, art_first=True))
    n.h(21, [45, 270, 345, 283], level=4)                       # Self-powered mode
    n.add(*n.prose(21, [45, 283, 345, 335], right=APP_FULL))
    n.h(21, [45, 337, 345, 350], level=4)                       # Charging-discharging plan
    n.add(*n.prose(21, [45, 350, 345, 445], right=APP_FULL))
    n.h(22, [45, 24, 345, 42])                                  # Backup-only mode
    n.add(media(n.figure("app-backup-only", width="phone"), n.prose(22, [160, 50, 345, 135], right=APP_TEXT),
                art_first=True))
    n.h(22, [45, 272, 345, 290])                                # Backup priority
    n.add(media(n.figure("app-backup-priority", width="phone"), n.prose(22, [168, 300, 345, 455], right=APP_TEXT),
                art_first=True))
    n.h(23, [45, 24, 345, 42])                                  # UPS mode
    n.add(media(n.figure("app-ups-mode", width="phone"), n.prose(23, [160, 50, 345, 195], right=APP_TEXT),
                art_first=True))

    # ---- p24 WARRANTY --------------------------------------------------------------
    n.chapter("warranty", 24, [25, 25, 345, 42])
    lead, note = n.t(24, [25, 43, 345, 66]), n.t(24, [25, 67, 345, 92])
    n.add(n.comp(warranty_lead_component_spec, lambda spec: None, accessibility_label=n.current["title"],
                 lead_html=html.escape(lead), local_note_html=html.escape(note)))
    titles = [96, 191, 265, 316, 356, 460, 490]
    for i, (y0, y1) in enumerate(zip(titles[:-1], titles[1:], strict=True)):
        title = n.t(24, [25, y0, 345, y0 + 13])
        n.add(node("heading", [text(title)], level=3))
        blocks = []
        for block in n.prose(24, [25, y0 + 13, 345, y1], right=FULL):
            value = flow_plain(block)
            markup = "<p>" + flow_markup(block) + "</p>"
            blocks.append({"kind": "paragraph", "text": value, "html": markup})
        n.add(n.comp(warranty_section_component_spec, lambda spec: None, title=title,
                     section_index=i + 1, blocks=blocks))

    problems = n.finish()
    print("chapters", len(n.chapters), "problems", len(problems))
    return problems


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


if __name__ == "__main__":
    problems = make()
    dump(SOURCE / "source/unmapped.json", deepcopy(problems))
    if problems:
        raise SystemExit("Unmapped or unbalanced native words: see source/unmapped.json")
