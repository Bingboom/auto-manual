"""Generate the JA-TS02A US French and Spanish semantic documents from the archived native PDF.

Run from the repository root:
``python3 data/manual_sources/JA-TS02A/US/added-locales/git-20261014-11ce66b1/source/intake.py``.
For each language it writes ``source/<lang>/content.json`` and ``source/<lang>/coverage.json``
and fails while any body word is unclassified. The layout reference is the accepted English
edition (``../../en/git-20261013-11ce66b1``): same chapters, components, figures, callouts and
tables, in the same order. Regions are reviewed PDF point rectangles per language
(``GEOMETRY``); each language's body is set with its own translation, so its boxes differ.
"""
from copy import deepcopy
import html
from pathlib import Path
import sys

REPO = next(p for p in Path(__file__).resolve().parents if (p / "build.py").is_file())
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from native import LANGUAGES, Native, SOURCE, attrs, dump  # noqa: E402
from tools.component_specs.app import app_download_component_spec  # noqa: E402
from tools.component_specs.callout import display_label  # noqa: E402
from tools.component_specs.spec_table import spec_table_component_spec  # noqa: E402
from tools.component_specs.warranty import (  # noqa: E402
    warranty_lead_component_spec, warranty_section_component_spec,
)
from tools.web.frozen_ai_flow import callout as shared_callout  # noqa: E402
from tools.web.frozen_ai_flow import node, paragraph, table, text  # noqa: E402


def page_of(language):
    """Physical page of a language's body page, from the English page that prints the same content."""
    if language == "fr":
        return lambda p: p + 22
    return lambda p: p + 44 if p <= 20 else p + 45  # the Spanish print repeats its p20 (PDF 64 = 65)


# Reviewed regions per language. Keys name the English intake's regions; values are
# [x0, y0, x1, y1] in PDF points on that language's page (see page_of).
GEOMETRY = {
    "fr": {
        # p3-5 safety
        "header": [0, 20, 369, 50], "safety": [25, 50, 345, 70], "disclaimer": [25, 70, 345, 82],
        "disclaimer-body": [25, 82, 345, 162], "warning": [25, 162, 345, 177], "warning-body": [25, 177, 345, 503],
        "warning-body-2": [25, 24, 345, 172], "caution": [25, 172, 345, 186], "caution-body": [25, 186, 345, 285],
        "fcc": [25, 285, 345, 300], "fcc-body": [25, 300, 345, 503],
        "ic": [25, 26, 345, 40], "ic-body": [25, 40, 345, 140], "ingestion-symbol": [24, 140, 64, 220],
        "ingestion-body": [64, 142, 345, 220], "symbols": [25, 226, 345, 240], "symbols-body": [25, 240, 345, 264],
        "symbols-head": [[28, 268, 80, 284], [80, 268, 345, 284]],
        "symbols-rows": [[283, 304], [304, 327], [327, 349], [349, 372]],
        # p6 specifications, package list
        "specifications": [25, 24, 345, 45], "spec-top": 49.5, "spec-split": 185, "spec-note": [25, 253.5, 345, 278],
        "package-list": [25, 285, 345, 306],
        # p7 what you need
        "what-you-need": [25, 35, 345, 58], "optionals": [25, 157, 345, 174],
        "cable-cols": [30, 140, 170, 225, 270, 345], "cable-head": [174, 189],
        "cable-groups": [[189, 200.5, 212.5, 224.5, 236.5], [236.5, 248.5, 260.5, 272.5, 285]],
        "cable-last": [285, 316], "cable-note": [25, 320, 345, 350],
        # p8-10 product overview
        "product-overview": [25, 33, 345, 52], "dimensions": [25, 52, 345, 66], "dimensions-note": [25, 262, 345, 278],
        "covered": [25, 298, 345, 313],
        "iot": [20, 24, 345, 37], "iot-body": [20, 37, 345, 106], "estop": [20, 106, 345, 117],
        "estop-body": [20, 117, 345, 139], "led": [20, 139, 345, 152],
        "led-cols": [28, 71, 138, 345], "led-head": [152, 165],
        "led-bounds": [165, 185, 205, 218, 239, 274, 287, 299.5, 312, 323.5, 335.8, 348],
        "uncovered": [20, 349, 345, 363],
        "normal-backup": [20, 24, 345, 35.5], "normal-backup-body": [20, 35.5, 345, 70],
        "caution-1-label": [30, 74, 100, 100], "caution-1-body": [100, 74, 345, 100], "callout-right": 330.0,
        "ups": [20, 102, 345, 113], "ups-body": [20, 113, 345, 182],
        "caution-2-label": [30, 186, 100, 240], "caution-2-body": [100, 186, 345, 240],
        # p10-11 pre-installation
        "pre-installation": [20, 256, 345, 276.5], "system-overview": [20, 276.5, 345, 289],
        "wifi-notes": [20, 22, 345, 59], "location": [20, 59, 345, 74], "location-body": [20, 74, 345, 88],
        "location-triangle": [18, 86, 50, 112], "location-label": [50, 90, 150, 111],
        "location-list": [20, 112, 345, 175],
        # p11-16 installation guide
        "installation-guide": [20, 175, 345, 192], "note": [20, 192, 345, 223], "surface": [20, 223, 345, 237],
        "surface-triangle": [18, 237, 50, 262], "surface-lead": [50, 237, 345, 262], "surface-lead-right": 322.0,
        "bracket-steps": [20, 264, 150, 325], "bracket-right": 149.0, "template-step": [20, 370, 345, 398],
        "fasten-step": [20, 24, 345, 44],
        "cable-entry": [20, 142, 345, 157], "cable-entry-body": [20, 157, 345, 192],
        "electrical": [20, 370, 345, 385], "electrical-body": [20, 385, 345, 503],
        "grid": [20, 176, 345, 190], "grid-body": [20, 190, 345, 333],
        "load": [20, 24, 345, 38], "load-body": [20, 38, 345, 198],
        "torque-title": [20, 393, 345, 407], "torque-cols": [20, 47, 117, 165, 213, 284, 345],
        "torque-head": [407, 427], "torque-rows": [[427, 444], [444, 462], [462, 479], [479, 497]],
        "estop-install": [20, 28, 345, 44], "estop-install-body": [20, 44, 345, 86],
        "deadfront": [20, 226, 345, 239], "deadfront-warning": [20, 239, 345, 315],
        "deadfront-body": [20, 315, 345, 340],
        "power-station": [20, 24, 345, 37], "power-station-body": [20, 37, 345, 52],
        "energizing": [20, 256, 345, 269], "energizing-body": [20, 269, 345, 313],
        "locking": [20, 313, 345, 328],
        "recommended-breakers": [20, 447.5, 345, 458], "breakers-body": [20, 458, 345, 503],
        # p17-19 internet setup
        "internet-setup": [25, 22, 345, 42], "download": [25, 42, 345, 53],
        "store-text": [25, 53, 345, 78], "qr-text": [25, 106, 345, 125],
        "add-device": [25, 180, 345, 196], "pairing-step": [25, 196, 165, 248], "pairing-right": 118.0,
        "status-panel": [25, 262, 168, 292], "status-right": 157.0,
        "add-step": [25, 330, 150, 415], "add-right": 122.0, "add-marker": "Appuyez sur ",
        "wifi-step": [20, 28, 345, 55],
        "voltage": [20, 256, 345, 271], "voltage-1": [20, 271, 185, 298], "voltage-2": [185, 271, 345, 298],
        "voltage-1-marker": "Appuyez sur ",
        "voltage-steps": [20, 28, 345, 66],
        "voltage-markers": ["Appuyez sur ", "puis sur ", "Enfin appuyez sur "],
        "edit-name": [20, 201, 345, 214], "edit-name-body": [20, 214, 352, 227],
        "edit-name-step": [20, 358, 345, 376], "edit-name-marker": "appuyez sur ",
        # p20-23 App quick start
        "app-quick-start": [35, 22, 345, 44], "dashboard": [45, 44, 345, 64], "dashboard-body": [160, 66, 345, 242],
        "app-text-right": 323.0, "circuits": [45, 262, 345, 286], "circuits-body": [45, 480, 345, 505.5],
        "app-full-right": 310.0,
        "working-modes": [40, 24, 345, 46],
        "modes-copy": [([148, 62, 345, 76], [148, 76, 345, 195]), ([148, 204, 345, 218], [148, 218, 345, 262])],
        "modes-right": 329.0,
        "self-powered": [40, 274, 345, 288], "self-powered-body": [40, 288, 345, 345],
        "plan": [40, 345, 345, 363], "plan-body": [40, 363, 345, 460], "modes-full-right": 312.0,
        "backup-only": [45, 26, 345, 52], "backup-only-body": [160, 58, 345, 185], "backup-only-right": 328.0,
        "backup-priority": [45, 268, 345, 294], "backup-priority-body": [160, 298, 345, 494],
        "backup-priority-right": 320.0,
        "ups-mode": [45, 26, 345, 52], "ups-mode-body": [160, 66, 345, 262], "ups-mode-right": 330.0,
        # p24 warranty
        "warranty": [25, 28, 345, 49], "warranty-lead": [25, 49, 345, 69.5], "warranty-note": [25, 69.5, 345, 95],
        "warranty-titles": [98, 189.5, 262, 313.5, 354, 465.5, 503],
    },
    "es": {
        "header": [0, 20, 369, 50], "safety": [25, 50, 345, 70], "disclaimer": [25, 70, 345, 82],
        "disclaimer-body": [25, 82, 345, 162], "warning": [25, 162, 345, 177], "warning-body": [25, 177, 345, 503],
        "warning-body-2": [25, 24, 345, 166], "caution": [25, 166, 345, 182], "caution-body": [25, 182, 345, 286],
        "fcc": [25, 286, 345, 301], "fcc-body": [25, 301, 345, 503],
        "ic": [25, 26, 345, 40], "ic-body": [25, 40, 345, 135], "ingestion-symbol": [24, 135, 64, 220],
        "ingestion-body": [64, 137, 345, 220], "symbols": [25, 222, 345, 237], "symbols-body": [25, 237, 345, 262],
        "symbols-head": [[28, 268, 80, 284], [80, 268, 345, 284]],
        "symbols-rows": [[283, 304], [304, 327], [327, 349], [349, 372]],
        "specifications": [25, 24, 345, 45], "spec-top": 49.5, "spec-split": 175, "spec-note": [25, 253.5, 345, 278],
        "package-list": [25, 285, 345, 306],
        "what-you-need": [25, 28, 345, 50], "optionals": [25, 153, 345, 170],
        "cable-cols": [30, 145, 172, 225, 270, 345], "cable-head": [170, 185],
        "cable-groups": [[185, 197, 209, 221, 233], [233, 245, 257, 269.3, 282]],
        "cable-last": [282, 322], "cable-note": [25, 322, 345, 352],
        "product-overview": [25, 30, 345, 51], "dimensions": [25, 51, 345, 62], "dimensions-note": [25, 258, 345, 274],
        "covered": [25, 293, 345, 306.5],
        "iot": [20, 28, 345, 41], "iot-body": [20, 41, 345, 104], "estop": [20, 104, 345, 115.5],
        "estop-body": [20, 115.5, 345, 138], "led": [20, 138, 345, 150.5],
        "led-cols": [30, 82, 142, 345], "led-head": [150.5, 164],
        "led-bounds": [164, 185, 200, 212, 232, 268, 280.5, 300, 313.5, 325, 336.8, 349],
        "uncovered": [20, 352, 345, 366],
        "normal-backup": [20, 28, 345, 40], "normal-backup-body": [20, 40, 345, 76],
        "caution-1-label": [30, 79, 98, 104], "caution-1-body": [98, 79, 345, 104], "callout-right": 336.0,
        "ups": [20, 107, 345, 118], "ups-body": [20, 118, 345, 186],
        "caution-2-label": [30, 190, 98, 245], "caution-2-body": [98, 190, 345, 245],
        "pre-installation": [20, 255, 345, 274.6], "system-overview": [20, 274.6, 345, 287],
        "wifi-notes": [20, 22, 345, 60], "location": [20, 60, 345, 72.65], "location-body": [20, 72.65, 345, 88],
        "location-triangle": [18, 86, 50, 109], "location-label": [50, 88, 150, 108],
        "location-list": [20, 108, 345, 172],
        "installation-guide": [20, 172, 345, 191], "note": [20, 191, 345, 220.5], "surface": [20, 220.5, 345, 234],
        "surface-triangle": [18, 234, 52, 259], "surface-lead": [52, 234, 345, 259], "surface-lead-right": 322.0,
        "bracket-steps": [20, 260, 150, 325], "bracket-right": 140.0, "template-step": [20, 372, 345, 399],
        "fasten-step": [20, 24, 345, 43],
        "cable-entry": [20, 156, 345, 171], "cable-entry-body": [20, 171, 345, 206],
        "electrical": [20, 366, 130, 381], "electrical-body": [20, 381, 345, 503],
        "grid": [20, 180, 345, 193], "grid-body": [20, 193, 345, 338],
        "load": [15, 24, 345, 38], "load-body": [15, 38, 345, 198],
        "torque-title": [15, 389, 345, 405], "torque-cols": [15, 36, 108, 161, 206, 278, 345],
        "torque-head": [405, 425], "torque-rows": [[425, 442], [442, 461], [461, 479], [479, 497]],
        "estop-install": [20, 30, 345, 45], "estop-install-body": [20, 45, 345, 88],
        "deadfront": [20, 231, 345, 244.5], "deadfront-warning": [20, 244.5, 345, 314],
        "deadfront-body": [20, 314, 345, 337],
        "power-station": [20, 24, 345, 37], "power-station-body": [20, 37, 345, 52],
        "energizing": [20, 256, 345, 272], "energizing-body": [20, 272, 345, 308],
        "locking": [20, 308, 345, 322],
        "recommended-breakers": [20, 446, 345, 458.5], "breakers-body": [20, 458.5, 345, 503],
        "internet-setup": [25, 28, 345, 50], "download": [25, 50, 345, 61.5],
        "store-text": [25, 61.5, 345, 86], "qr-text": [25, 115, 345, 131],
        "add-device": [25, 190, 345, 204], "pairing-step": [25, 204, 175, 264], "pairing-right": 119.0,
        "status-panel": [25, 278, 178, 306], "status-right": 172.0,
        "add-step": [25, 340, 160, 412], "add-right": 132.0, "add-marker": "Pulsa ",
        "wifi-step": [20, 35, 345, 62],
        "voltage": [20, 273, 345, 289], "voltage-1": [20, 289, 185, 305], "voltage-2": [185, 289, 345, 305],
        "voltage-1-marker": "Pulsa ",
        "voltage-steps": [20, 26, 345, 62],
        "voltage-markers": ["Pulsa ", "Después, pulsa ", "Finalmente, pulsa "],
        "edit-name": [20, 196, 345, 209], "edit-name-body": [20, 209, 345, 222],
        "edit-name-step": [20, 353, 345, 371], "edit-name-marker": "pulsa ",
        "app-quick-start": [35, 22, 345, 43.5], "dashboard": [45, 43.5, 345, 63], "dashboard-body": [160, 63, 345, 185],
        "app-text-right": 318.5, "circuits": [45, 262, 345, 285], "circuits-body": [45, 490, 345, 505.9],
        "app-full-right": 297.0,
        "working-modes": [40, 28, 345, 52],
        "modes-copy": [([150, 62, 345, 74], [150, 74, 345, 172]), ([150, 182, 345, 193], [150, 193, 345, 250])],
        "modes-right": 323.0,
        "self-powered": [40, 278, 345, 290], "self-powered-body": [40, 290, 345, 342],
        "plan": [40, 342, 345, 353], "plan-body": [40, 353, 345, 450], "modes-full-right": 310.0,
        "backup-only": [45, 24, 345, 48], "backup-only-body": [160, 60, 345, 170], "backup-only-right": 313.0,
        "backup-priority": [45, 270, 345, 295], "backup-priority-body": [160, 300, 345, 490],
        "backup-priority-right": 308.0,
        "ups-mode": [45, 24, 345, 46], "ups-mode-body": [160, 60, 345, 252], "ups-mode-right": 312.0,
        "warranty": [20, 24, 345, 43], "warranty-lead": [20, 43, 345, 66], "warranty-note": [20, 66, 345, 92],
        "warranty-titles": [95.5, 191, 264.5, 316, 355.5, 459.5, 503],
    },
}


def callout(n, label, body, *, variant, lockup=None, shaded=False):
    """Shared callout strip; optional native warning lockup or shaded signal cell."""
    item = shared_callout(display_label(label), body, variant=variant, language=n.language,
                          source_ref=f"native-pdf/{n.current['id']}/{variant}-{len(n.selections)}")
    carrier = item["carrier_flow"][0]
    classes = carrier["presentation"]["html"]["attributes"]["class"]
    if lockup:
        classes += " hb-source-warning-lockup"
        label_cell = carrier["children"][0]["children"][0]["children"][0]
        label_cell["children"] = [node("inline_group", [
            node("image", source=lockup, alt=""), text(display_label(label))],
            presentation=attrs("hb-warning-lockup"))]
    if shaded:
        classes += " hb-callout-label-shaded"
    carrier["presentation"]["html"]["attributes"]["class"] = classes
    return item


def cell(children, *, header=False, **fields):
    if isinstance(children, str):
        children = [text(children)]
    return node("table_cell", children, header=header, **fields)


def head(n, p, box, **fields):
    """A header cell; the shared table theme sets its weight."""
    return cell(n.t(p, box), header=True, scope="col", **fields)


def grid(head_rows, body_rows):
    """A plain shared table (declared in shared_component_exceptions); head rows become <thead>."""
    parts = []
    if head_rows:
        parts.append(node("table_head", [node("table_row", r) for r in head_rows]))
    parts.append(node("table_body", [node("table_row", r) for r in body_rows]))
    table = node("table", parts, presentation=attrs("manual-table"))
    return node("group", [table], role="container", presentation=attrs("table-wrapper docutils container"))


def media(art, copy, *, art_first=False):
    """Print text and its figure in reading order, as plain flow (stacked at every width)."""
    return [art, *copy] if art_first else [*copy, art]


def spec_carrier(spec):
    slot = lambda role: spec.slot(role).content  # noqa: E731
    title = node("heading", [node("inline_group", [text(slot("section_title"))],
                                  presentation=attrs("hb-spec-section-text"))], level=2,
                 presentation=attrs("hb-spec-section hb-spec-group"))
    rows = [[cell(r["label"] if i == 0 else "", header=True), cell(v["text"])]
            for r in slot("rows") for i, v in enumerate(r["values"])]
    return [title, table(rows)]


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


def make(language):
    n = Native(language)
    g = GEOMETRY[language]
    P = page_of(language)

    # ---- p3-5 SAFETY INSTRUCTIONS ------------------------------------------------
    n.take(P(3), g["header"], purpose="printed-header")  # FR / Français / Modèle badge
    n.chapter("safety", P(3), g["safety"])
    n.h(P(3), g["disclaimer"])
    n.add(*n.prose(P(3), g["disclaimer-body"], right=342.0))
    n.h(P(3), g["warning"])
    n.add(*n.prose(P(3), g["warning-body"], right=345.0, extra=[(P(4), g["warning-body-2"])]))
    n.h(P(4), g["caution"])
    n.add(*n.prose(P(4), g["caution-body"], right=345.0))
    n.h(P(4), g["fcc"])
    n.add(*n.prose(P(4), g["fcc-body"], right=345.0, keep_marks=True))
    n.h(P(5), g["ic"])
    n.add(*n.prose(P(5), g["ic-body"], right=345.0))
    n.take(P(5), g["ingestion-symbol"], purpose="native-symbol/ingestion-hazard")
    hazard = n.prose(P(5), g["ingestion-body"], right=345.0)
    n.add(node("image", source=n.symbol("ingestion-hazard"), alt=""), *hazard)
    n.h(P(5), g["symbols"])
    n.add(*n.prose(P(5), g["symbols-body"], right=345.0))
    head_rows = [[head(n, P(5), box) for box in g["symbols-head"]]]
    rows = []
    for key, (y0, y1) in zip(["grounding", "caution", "electric-shock", "read-manual"], g["symbols-rows"], strict=True):
        meaning = n.t(P(5), [80, y0, 345, y1])
        rows.append([cell([node("image", source=n.symbol(key), alt=meaning)]), cell(meaning)])
    n.add(grid(head_rows, rows))

    # ---- p6 SPECIFICATIONS, PACKAGE LIST -----------------------------------------
    n.chapter("specifications", P(6), g["specifications"])
    tops = [g["spec-top"] + 12 * i for i in range(18)]
    split = g["spec-split"]
    rows = [(n.t(P(6), [26, y0, split, y1]), n.t(P(6), [split, y0, 345, y1]))
            for y0, y1 in zip(tops[:-1], tops[1:], strict=True)]
    # The print's specification table has no title of its own; the shared spec table takes the chapter's.
    n.add(n.comp(spec_table_component_spec, spec_carrier, section_title=n.current["title"], rows=rows))
    n.add(*n.prose(P(6), g["spec-note"], right=345.0))
    n.chapter("package-list", P(6), g["package-list"])
    n.add(n.figure("package-list"))

    # ---- p7 WHAT YOU NEED ---------------------------------------------------------
    n.chapter("what-you-need", P(7), g["what-you-need"])
    n.add(n.figure("optional-tools"))
    n.h(P(7), g["optionals"])
    x = g["cable-cols"]
    h0, h1 = g["cable-head"]
    head_rows = [[head(n, P(7), [x[0], h0, x[2], h1], column_span=2), head(n, P(7), [x[2], h0, x[3], h1]),
                  head(n, P(7), [x[3], h0, x[4], h1]), head(n, P(7), [x[4], h0, x[5], h1])]]
    rows = []
    for ys in g["cable-groups"]:
        label, current = n.t(P(7), [x[0], ys[0], x[1], ys[-1]]), n.t(P(7), [x[3], ys[0], x[4], ys[-1]])
        for i, (y0, y1) in enumerate(zip(ys[:-1], ys[1:], strict=True)):
            row = []
            if i == 0:
                row.append(cell(label, row_span=4))
            row += [cell(n.t(P(7), [x[1], y0, x[2], y1])),
                    cell(n.t(P(7), [x[2], y0, x[3], y1]))]
            if i == 0:
                row.append(cell(current, row_span=4))
            row.append(cell(n.t(P(7), [x[4], y0, x[5], y1])))
            rows.append(row)
    y0, y1 = g["cable-last"]
    rows.append([cell(n.t(P(7), [x[0], y0, x[1], y1]))]
                + [cell(n.t(P(7), [a, y0, b, y1])) for a, b in zip(x[1:-1], x[2:], strict=True)])
    n.add(grid(head_rows, rows))
    n.add(*n.prose(P(7), g["cable-note"], right=345.0))

    # ---- p8-10 PRODUCT OVERVIEW ---------------------------------------------------
    n.chapter("product-overview", P(8), g["product-overview"])
    n.h(P(8), g["dimensions"])
    n.add(n.figure("dimensions"))
    n.add(*n.prose(P(8), g["dimensions-note"], right=345.0))
    n.h(P(8), g["covered"])
    n.add(n.figure("covered-overview"))
    n.h(P(9), g["iot"], level=4)
    n.add(*n.prose(P(9), g["iot-body"], right=345.0))
    n.h(P(9), g["estop"], level=4)
    n.add(*n.prose(P(9), g["estop-body"], right=345.0))
    n.h(P(9), g["led"])
    c = g["led-cols"]
    h0, h1 = g["led-head"]
    head_rows = [[head(n, P(9), [a, h0, b, h1]) for a, b in zip(c[:-1], c[1:], strict=True)]]
    bounds = g["led-bounds"]
    rows, index = [], 0
    for span in (3, 3, 3, 2):
        name = n.t(P(9), [c[0], bounds[index], c[1], bounds[index + span]])
        for k in range(span):
            y0, y1 = bounds[index], bounds[index + 1]
            row = [cell(name, row_span=span)] if k == 0 else []
            row += [cell(n.t(P(9), [c[1], y0, c[2], y1])), cell(n.t(P(9), [c[2], y0, c[3], y1]))]
            rows.append(row)
            index += 1
    n.add(grid(head_rows, rows))
    n.h(P(9), g["uncovered"])
    n.add(n.figure("uncovered-overview"))
    n.h(P(10), g["normal-backup"], level=4)
    n.add(*n.prose(P(10), g["normal-backup-body"], right=345.0))
    n.add(callout(n, n.t(P(10), g["caution-1-label"]),
                  n.prose(P(10), g["caution-1-body"], right=g["callout-right"]), variant="caution", shaded=True))
    n.h(P(10), g["ups"], level=4)
    n.add(*n.prose(P(10), g["ups-body"], right=345.0))
    n.add(callout(n, n.t(P(10), g["caution-2-label"]),
                  n.prose(P(10), g["caution-2-body"], right=g["callout-right"]), variant="caution", shaded=True))

    # ---- p10-11 PRE-INSTALLATION -----------------------------------------------------
    n.chapter("pre-installation", P(10), g["pre-installation"])
    n.h(P(10), g["system-overview"])
    n.add(n.figure("system-overview"))
    n.add(*n.prose(P(11), g["wifi-notes"], right=345.0))
    n.h(P(11), g["location"])
    n.add(*n.prose(P(11), g["location-body"], right=345.0))
    n.take(P(11), g["location-triangle"], purpose="native-symbol/warning-triangle")
    n.add(callout(n, n.t(P(11), g["location-label"]), n.prose(P(11), g["location-list"], right=345.0),
                  variant="warning", lockup=n.symbol("lockup-installation-location")))

    # ---- p11-16 INSTALLATION GUIDE -------------------------------------------------
    n.chapter("installation-guide", P(11), g["installation-guide"])
    n.add(*n.prose(P(11), g["note"], right=345.0))
    n.h(P(11), g["surface"])
    n.take(P(11), g["surface-triangle"], purpose="native-symbol/warning-triangle")
    lead = n.prose(P(11), g["surface-lead"], right=g["surface-lead-right"])
    first = lead[0]["children"][0]
    label, _, rest = first["text"].partition(":")
    first["text"] = rest.lstrip()
    n.add(callout(n, label.strip(), lead, variant="warning", lockup=n.symbol("lockup-surface-mounting")))
    n.add(*media(n.figure("mounting-brackets"),
                n.prose(P(11), g["bracket-steps"], right=g["bracket-right"])))
    n.add(*n.prose(P(11), g["template-step"], right=345.0))
    n.add(n.figure("mounting-template"))
    n.add(*n.prose(P(12), g["fasten-step"], right=345.0))
    n.add(n.figure("mounting-fasteners"))
    n.h(P(12), g["cable-entry"])
    n.add(*n.prose(P(12), g["cable-entry-body"], right=345.0))
    n.add(n.figure("cable-entry"))
    n.h(P(12), g["electrical"])
    n.add(*n.prose(P(12), g["electrical-body"], right=345.0))
    n.add(n.figure("grid-preparation"))
    n.h(P(13), g["grid"], level=4)
    n.add(*n.prose(P(13), g["grid-body"], right=345.0))
    n.add(n.figure("grid-wiring"))
    n.h(P(14), g["load"], level=4)
    n.add(*n.prose(P(14), g["load-body"], right=347.0))
    n.add(n.figure("load-wiring"))
    n.add(*n.prose(P(14), g["torque-title"], right=345.0))  # Conductor Tightening Torque
    cols = g["torque-cols"]
    h0, h1 = g["torque-head"]
    head_rows = [[head(n, P(14), [x0, h0, x1, h1]) for x0, x1 in zip(cols[:-1], cols[1:], strict=True)]]
    rows = [[cell(n.t(P(14), [x0, y0, x1, y1])) for x0, x1 in zip(cols[:-1], cols[1:], strict=True)]
            for y0, y1 in g["torque-rows"]]
    n.add(grid(head_rows, rows))
    n.h(P(15), g["estop-install"], level=4)
    n.add(*n.prose(P(15), g["estop-install-body"], right=345.0))
    n.add(n.figure("external-emergency-stop"))
    n.h(P(15), g["deadfront"], level=4)
    # The French and Spanish prints set this warning as a plain line above the checks, with no triangle.
    n.add(*n.prose(P(15), g["deadfront-warning"], right=345.0, keep_marks=True))
    n.add(*n.prose(P(15), g["deadfront-body"], right=345.0))
    n.add(n.figure("deadfront-installation"))
    n.h(P(16), g["power-station"], level=4)
    n.add(*n.prose(P(16), g["power-station-body"], right=345.0))
    n.add(n.figure("power-station-connections"))
    n.h(P(16), g["energizing"], level=4)
    n.add(*n.prose(P(16), g["energizing-body"], right=345.0))
    n.h(P(16), g["locking"], level=4)
    n.add(n.figure("locking-panel"))
    # The French and Spanish prints set this title at the size of the subheadings above it, not as a
    # chapter title; it follows the print (operator decision D2, 2026-10-15).
    n.h(P(16), g["recommended-breakers"], level=4)
    n.add(*n.prose(P(16), g["breakers-body"], right=345.0))

    # ---- p17-19 INTERNET AND INITIALIZATION SETUP -------------------------------------
    n.chapter("internet-setup", P(17), g["internet-setup"])
    n.h(P(17), g["download"])
    n.embedded("app-store-badges")
    n.embedded("app-download-qr")
    columns = [{"role": "store", "text": n.t(P(17), g["store-text"])},
               {"role": "qr", "text": n.t(P(17), g["qr-text"])}]
    for column in columns:
        column["html"] = html.escape(column["text"])
    badges = n.figures["app-store-badges"]

    def app_carrier(spec):
        return [node("image", source=badges["local_path"], alt=badges["caption"]),
                *[paragraph(c["text"]) for c in columns]]
    n.add(n.comp(app_download_component_spec, app_carrier, accessibility_label=badges["caption"],
                 columns=columns, source_art_ref=badges["local_path"],
                 store_art_ref=badges["local_path"], qr_art_ref=n.figures["app-download-qr"]["local_path"]))
    n.h(P(17), g["add-device"])
    step = n.prose(P(17), g["pairing-step"], right=g["pairing-right"])
    note = n.prose(P(17), g["status-panel"], right=g["status-right"], every_line=True)
    n.add(*media(n.figure("iot-pairing"), step + note))
    step = insert_control(n, n.prose(P(17), g["add-step"], right=g["add-right"]), g["add-marker"], "inline-add-device")
    n.add(*media(n.figure("app-add-device"), step))
    n.add(*n.prose(P(18), g["wifi-step"], right=345.0))
    n.add(n.figure("app-wifi"))
    n.h(P(18), g["voltage"])
    first = insert_control(n, n.prose(P(18), g["voltage-1"], right=185.0), g["voltage-1-marker"], "inline-settings")
    second = insert_control(n, n.prose(P(18), g["voltage-2"], right=345.0), "", "inline-voltage-config", at_end=True)
    first[0]["children"] += [text(" ")] + second[0]["children"]
    n.add(*first)
    n.add(n.figure("app-voltage-menu"))
    steps = n.prose(P(19), g["voltage-steps"], right=345.0)
    for marker, slot in zip(g["voltage-markers"], ["inline-edit", "inline-link-circuits", "inline-save"], strict=True):
        insert_control(n, steps, marker, slot)
    n.add(*steps)
    n.add(n.figure("app-voltage-settings"))
    n.h(P(19), g["edit-name"])
    n.add(*n.prose(P(19), g["edit-name-body"], right=352.0))
    n.add(n.figure("app-circuit-list"))
    n.add(*insert_control(n, n.prose(P(19), g["edit-name-step"], right=345.0), g["edit-name-marker"], "inline-edit-name"))
    n.add(n.figure("app-circuit-name"))

    # ---- p20-23 JACKERY APP QUICK START GUIDE -------------------------------------
    n.chapter("app-quick-start", P(20), g["app-quick-start"])
    n.h(P(20), g["dashboard"])
    n.add(*media(n.figure("app-dashboard"), n.prose(P(20), g["dashboard-body"], right=g["app-text-right"]),
                art_first=True))
    n.h(P(20), g["circuits"])
    n.add(n.figure("app-circuits"))
    n.add(*n.prose(P(20), g["circuits-body"], right=g["app-full-right"]))
    n.h(P(21), g["working-modes"])
    copy = []
    for heading_box, body_box in g["modes-copy"]:
        copy.append(node("heading", [text(n.t(P(21), heading_box))], level=3))
        copy += n.prose(P(21), body_box, right=g["modes-right"])
    n.add(*media(n.figure("app-working-modes"), copy, art_first=True))
    n.h(P(21), g["self-powered"], level=4)
    n.add(*n.prose(P(21), g["self-powered-body"], right=g["modes-full-right"]))
    n.h(P(21), g["plan"], level=4)
    n.add(*n.prose(P(21), g["plan-body"], right=g["modes-full-right"]))
    n.h(P(22), g["backup-only"])
    n.add(*media(n.figure("app-backup-only"),
                n.prose(P(22), g["backup-only-body"], right=g["backup-only-right"]), art_first=True))
    n.h(P(22), g["backup-priority"])
    n.add(*media(n.figure("app-backup-priority"),
                n.prose(P(22), g["backup-priority-body"], right=g["backup-priority-right"]), art_first=True))
    n.h(P(23), g["ups-mode"])
    n.add(*media(n.figure("app-ups-mode"),
                n.prose(P(23), g["ups-mode-body"], right=g["ups-mode-right"]), art_first=True))

    # ---- p24 WARRANTY --------------------------------------------------------------
    n.chapter("warranty", P(24), g["warranty"])
    lead, note = n.t(P(24), g["warranty-lead"]), n.t(P(24), g["warranty-note"])
    n.add(n.comp(warranty_lead_component_spec, lambda spec: None, accessibility_label=n.current["title"],
                 lead_html=html.escape(lead), local_note_html=html.escape(note)))
    titles = g["warranty-titles"]
    for i, (y0, y1) in enumerate(zip(titles[:-1], titles[1:], strict=True)):
        title = n.t(P(24), [20, y0, 345, y0 + 13])
        n.add(node("heading", [text(title)], level=3))
        blocks = []
        for block in n.prose(P(24), [20, y0 + 13, 345, y1], right=345.0):
            value = flow_plain(block)
            markup = "<p>" + flow_markup(block) + "</p>"
            blocks.append({"kind": "paragraph", "text": value, "html": markup})
        n.add(n.comp(warranty_section_component_spec, lambda spec: None, title=title,
                     section_index=i + 1, blocks=blocks))

    problems = n.finish()
    print(language, "chapters", len(n.chapters), "problems", len(problems))
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
    problems = {language: make(language) for language in LANGUAGES}
    dump(SOURCE / "source/unmapped.json", deepcopy(problems))
    if any(problems.values()):
        raise SystemExit("Unmapped or unbalanced native words: see source/unmapped.json")
