"""Generate three source-local semantic documents from the pinned native PDF."""
from pathlib import Path
import sys

REPO = next(p for p in Path(__file__).resolve().parents if (p / "build.py").is_file())
sys.path.insert(0, str(REPO))

import html  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402

from native import Native, SOURCE, dump, normalize, pair, prose  # noqa: E402
from tools.component_specs.callout import display_label  # noqa: E402
from tools.component_specs.app import app_download_component_spec  # noqa: E402
from tools.component_specs.fcc import fcc_component_spec  # noqa: E402
from tools.component_specs.lcd_mode import lcd_mode_component_spec  # noqa: E402
from tools.component_specs.inbox import inbox_component_spec  # noqa: E402
from tools.component_specs.manual_tables import (  # noqa: E402
    lcd_icon_component_spec, symbol_icon_component_spec,
    symbol_signal_component_spec, troubleshooting_component_spec,
)
from tools.component_specs.spec_table import spec_table_component_spec  # noqa: E402
from tools.component_specs.warranty import (  # noqa: E402
    warranty_lead_component_spec, warranty_section_component_spec,
    warranty_years_component_spec,
)
from tools.web.frozen_ai_flow import callout as shared_callout  # noqa: E402
from tools.web.frozen_ai_flow import cell, heading, node, paragraph, scroll_table, text  # noqa: E402


def callout(label, body, **kwargs):
    # Some native labels carry punctuation. Bind the canonical display label
    # identically in the shared component and its independently checked carrier.
    return shared_callout(display_label(label), body, **kwargs)


def notice(n, p, labelbox, bodybox, variant):
    label = n.t(p, labelbox)
    _, raw, _ = n.take(p, bodybox, unused=True, reading_order="vertical")
    n.add(callout(label, prose(raw), variant=variant, language=n.language,
                  source_ref=f"native-pdf/page-{p}/notice-{len(n.selections)}"))


def words_in_table(n, p, table, cuts):
    starts = sorted({round(row.bbox[1], 4) for row in table.rows})
    ends = starts[1:] + [table.bbox[3]]
    rows = []
    for y0, y1 in zip(starts, ends, strict=True):
        rows.append([n.t(p, [x0, y0, x1, y1])
                     for x0, x1 in zip(cuts[:-1], cuts[1:], strict=True)])
    return rows


def make(language):
    n = Native(language)
    p = n.page
    n.chapter("preface", n.t(2, [54, {"en": 30, "fr": 165, "es": 310}[language],
                                 340, {"en": 51, "fr": 185, "es": 329}[language]]))
    n.current["nodes"][0].update(level=1, presentation={"html": {"attributes": {"class": "hb-preface-heading"}}})
    # The EN/FR/ES badge is outlined artwork on p2, transcribed from its pixels.
    badge = language.upper()
    n.current["title"] = badge + " " + n.current["title"]
    n.current["nodes"][0]["children"][:0] = [node("inline_group", [text(badge)],
        presentation={"html": {"attributes": {"class": "hb-preface-region"}}}), text(" ")]
    for index in range({"en": 0, "fr": 4, "es": 8}[language],
                       {"en": 4, "fr": 8, "es": 12}[language]):
        n.add(paragraph(n.b(2, index)))
    preface_prose = n.current["nodes"][1:]
    n.current["nodes"][1:] = []
    n.add(node("group", preface_prose, role="container", presentation={
        "html": {"attributes": {"class": "hb-preface-prose"}}}))

    a = p(4)
    n.chapter("safety", n.t(a, [25, 25, 345, 50]))
    n.h(a, [60, 55, 345, 90])
    top = {"en": 96, "fr": 96, "es": 89}[language]
    label_end = {"en": 119, "fr": 119, "es": 107}[language]
    label = n.t(a, [72, top, 188, label_end])
    body = n.take(a, [72, label_end, 188, {"en": 145, "fr": 145, "es": 133}[language]],
                  unused=True)[1]
    n.add(callout(label, prose(body), variant="warning", language=language,
                  source_ref=f"native-pdf/page-{a}/warning"))
    left = n.take(a, [25, {"en": 141, "fr": 141, "es": 133}[language], 188, 263])[1]
    right = n.take(a, [190, {"en": 88, "fr": 95, "es": 86}[language], 345, 263])[1]
    n.add(*prose(left + "\n" + right))
    n.h(a, [25, 263, 190, 281])
    n.h(a, [25, 279, 190, 296], level=4)
    bottom = {"en": 442, "fr": 453, "es": 450}[language]
    left = n.take(a, [25, 292, 188, bottom], unused=True)[1]
    right = n.take(a, [190, 292, 345, bottom])[1]
    n.add(*prose(left + "\n" + right))
    ground = n.take(a, [25, bottom, 345, 500])[1].split("\n")
    n.add(heading(normalize(ground[0])), paragraph(normalize("\n".join(ground[1:]))))

    a = p(5)
    if language == "en":
        notices = [([48, 30, 105, 68], [48, 28, 345, 67], "warning"),
                   ([48, 72, 105, 104], [48, 70, 345, 110], "danger")]
    elif language == "fr":
        notices = [([48, 30, 126, 68], [48, 28, 345, 69], "warning"),
                   ([48, 76, 125, 118], [48, 74, 345, 120], "warning")]
    else:
        notices = [([48, 28, 112, 76], [48, 26, 345, 76], "warning"),
                   ([48, 78, 95, 121], [48, 77, 345, 123], "danger")]
    # Signal labels share blocks with bodies in EN/FR but separate columns in ES.
    for index, (labelbox, bodybox, variant) in enumerate(notices):
        values = n.take(a, labelbox)
        labels = {"warning": {"en": "WARNING", "fr": "AVERTISSEMENT", "es": "ADVERTENCIA"},
                  "danger": {"en": "DANGER", "fr": "DANGER", "es": "PELIGRO"}}
        label = labels[variant][language]
        raw = n.take(a, bodybox, unused=True)[1]
        # Mixed native blocks put the label last; preserve body and consume label separately.
        raw = (values[1] + "\n" + raw).replace(label, "").strip()
        n.add(callout(label, prose(raw), variant=variant, language=language,
                      source_ref=f"native-pdf/page-{a}/{variant}-{index}"))
    y = {"en": 116, "fr": 128, "es": 133}[language]
    n.h(a, [25, y, 345, y + 13])
    sy = {"en": 173, "fr": 184, "es": 187}[language]
    n.paras(a, [25, y + 13, 345, sy])
    n.chapter("symbols", n.t(a, [25, sy, 345, sy + 18]))
    signal_y = {"en": 199, "fr": 216, "es": 219}[language]
    headers = [pair("content", n.t(a, [25, signal_y - 1, 83, signal_y + 14])),
               pair("content", n.t(a, [83, signal_y - 1, 345, signal_y + 14]))]
    labels = {"en": ["WARNING", "CAUTION", "NOTE", "TIP"],
              "fr": ["AVERTISSEMENT", "ATTENTION", "REMARQUE", "CONSEILS"],
              "es": ["ADVERTENCIA", "PRECAUCIÓN", "NOTA", "CONSEJOS"]}[language]
    starts = {"en": [213, 239, 264, 291, 314],
              "fr": [230, 256, 281, 307, 333],
              "es": [233, 259, 284, 311, 333]}[language]
    rows = []
    for i, label in enumerate(labels):
        raw = n.t(a, [45, starts[i], 345, starts[i + 1]])
        rows.append({"label": label, "show_icon": True,
                     **pair("meaning", raw.replace(label, "").strip())})
    n.add(n.comp(symbol_signal_component_spec, accessibility_label="Signal words",
                 headers=headers, rows=rows))
    gy = {"en": 320, "fr": 338, "es": 342}[language]
    symbol_headers = [pair("content", n.t(a, [25, gy - 1, 70, gy + 14])),
                      pair("content", n.t(a, [70, gy - 1, 180, gy + 14])),
                      pair("content", n.t(a, [180, gy - 1, 220, gy + 14])),
                      pair("content", n.t(a, [220, gy - 1, 345, gy + 14]))]
    panels, symbol_rows = [], []
    bounds = {"en": [333, 364, 390, 418, 494],
              "fr": [353, 384, 411, 443, 496],
              "es": [357, 388, 417, 446, 496]}[language]
    for i in range(4):
        v = n.t(a, [70, bounds[i], 180, bounds[i + 1]])
        symbol_rows.append({"asset_index": i, "icon_alt": v, **pair("meaning", v)})
    panels.append(symbol_rows)
    bounds = {"en": [333, 360, 386, 494],
              "fr": [353, 383, 411, 496],
              "es": [357, 388, 414, 496]}[language]
    symbol_rows = []
    for i in range(3):
        v = n.t(a, [220, bounds[i], 345, bounds[i + 1]])
        symbol_rows.append({"asset_index": i + 4, "icon_alt": v, **pair("meaning", v)})
    panels.append(symbol_rows)
    icons = ["symbol_warning_triangle.svg", "symbol_read_manual_person.svg",
             "symbol_keep_away_from_children_gray_jp.svg", "symbol_li_ion.svg",
             "symbol_do_not_dismantle.svg", "symbol_no_open_flame_gray_jp.svg", "symbol_weee.png"]
    n.add(n.comp(symbol_icon_component_spec, accessibility_label="Safety symbols",
                 headers=symbol_headers, panels=panels, icon_refs=["assets/" + x for x in icons]))

    a = p(6)
    n.chapter("fcc", "FCC")
    opening = n.t(a, [60, 25, 190, 86])
    note = n.t(a, [25, 81, 190, 177], unused=True)
    note_label, note_body = note.split(":", 1)
    _, right, _ = n.take(a, [190, 25, 345, 118])
    intro, *items = re.split(r"(?:^|\n)\s*[•·]\s*", right)
    modification = n.t(a, [190, 120, 345, 180])
    mod_label, mod_body = modification.split(":", 1)
    n.add(n.comp(fcc_component_spec, accessibility_label="FCC",
                 opening_copy=[opening], mark_asset_ref="assets/fcc-mark.svg",
                 left_blocks=[{"kind": "paragraph", "label": note_label + ":", "text": note_body.strip()}],
                 right_blocks=[
                     {"kind": "paragraph", "label": "", "text": normalize(intro)},
                     {"kind": "list", "items": [normalize(item) for item in items]},
                     {"kind": "paragraph", "label": mod_label + ":", "text": mod_body.strip()},
                 ]))
    n.chapter("inbox", n.t(a, [25, 202, 345, 229]))
    n.take(a, [25, 274, 345, 300], purpose="shared-inbox-live-ordinal")
    cards = []
    for box, asset in [([25, 380, 150, 400], "inbox-main.svg"),
                       ([150, 380, 240, 400], "inbox-cable.png"),
                       ([240, 380, 345, 400], "inbox-manual.png")]:
        label = n.t(a, box)
        cards.append({"image_ref": "assets/" + asset, "label": label, "alt": label})
    tip_raw = n.t(a, [25, 439, 345, 484])
    tip_label = {"en": "TIP", "fr": "CONSEILS", "es": "CONSEJOS"}[language]
    n.add(n.comp(inbox_component_spec, accessibility_label=n.current["title"], cards=cards,
                 tip_label=tip_label, tip_body=tip_raw.replace(tip_label, "").strip(),
                 require_tip=True, variant="responsive-card-grid"))

    a = p(7)
    n.chapter("overview", n.t(a, [25, 25, 345, 50]))
    n.h(a, [25, 54, 180, 76])
    boxes = [
        [25, 90, 145, 112], [25, 112, 145, 138], [25, 138, 145, 172],
        [25, 172, 145, 208], [25, 216, 145, 240], [25, 240, 145, 265],
        [275, 90, 345, 112], [280, 114, 345, 148], [275, 172, 345, 205],
        [275, 210, 345, 240], [25, 296, 170, 326], [25, 345, 150, 386],
        [245, 320, 345, 357], [225, 382, 345, 437],
    ]
    rects = [[0, 1, 32, 5], [0, 8, 32, 6], [0, 15, 32, 9],
             [0, 25, 32, 9], [0, 38, 34, 5], [0, 45, 34, 5],
             [81, 1, 18, 5], [81, 9, 18, 10], [81, 24, 18, 10],
             [81, 36, 18, 10], [4, 62, 50, 5], [0, 78, 30, 9],
             [73, 69, 26, 10], [66, 88, 33, 12]]
    n.add(n.figure("overview", n.labels(a, boxes, [(r,) for r in rects]),
                   width="dense"))

    a = p(8)
    n.chapter("lcd", n.t(a, [25, 25, 345, 50]))
    # All 25 external numbering labels become HTML; screen internals stay artwork.
    labels = []
    for i, word in enumerate(n.words[a]):
        if 50 <= (word[1] + word[3]) / 2 < 197 and re.fullmatch(r"\d{1,2}", word[4]):
            v = n.t(a, [word[0] - .05, word[1] - .05, word[2] + .05, word[3] + .05])
            labels.append((v, [(word[0] - 40) / 285 * 100,
                               (word[1] - 52) / 144 * 100, 3, 6]))
    n.add(n.figure("lcd-map", labels, width="lcd"))
    lcd = []
    for k, page in enumerate([a, p(9)]):
        table = n.doc[page - 1].find_tables().tables[0]
        cuts = [28, 45, 74 if k == 0 else 83, 144 if k == 0 else 146, 345]
        source_rows = words_in_table(n, page, table, cuts)
        for number, _, name, description in source_rows:
            # Native thermal number spans both subrows; repeat its index in HTML.
            if not number:
                number = "21"
            j = len(lcd)
            lcd.append({"asset_index": j, "icon_alt": name,
                        **pair("number", number), **pair("name", name),
                        **pair("description", description)})
    assert len(lcd) == 26
    n.add(n.comp(lcd_icon_component_spec, accessibility_label=n.current["title"], rows=lcd,
                 icon_refs=json.loads((SOURCE / "source/lcd_refs.json").read_text())))

    a = p(10)
    n.chapter("operations", n.t(a, [25, 25, 345, 50]))
    n.h(a, [25, 53, 345, 70])
    regions = [[260, 78, 345, 105], [260, 105, 345, 129 if language == "en" else 133],
               [275, 130, 293, 150], [160, 147, 340, 190], [35, 194, 335, 232]]
    geoms = [([75, 3, 24, 17],), ([75, 21, 24, 20],), ([80, 36, 9, 7],),
             ([43, 44, 54, 25], "#f2f2f3"), ([3, 73, 94, 22], "#f2f2f3")]
    n.add(n.figure("power", n.labels(a, regions, geoms), width="dense"))
    n.h(a, [25, 245, 345, 263])
    regions = [[35, 272, 175, 288], [282, 281, 343, 306],
               [282, 307, 343, 334], [35, 441, 340, 476]]
    geoms = [([2, 2, 44, 8], "#f2f2f3"), ([83, 6, 16, 12],),
             ([83, 19, 16, 12],), ([3, 85, 94, 12], "#f2f2f3")]
    n.add(n.figure("ac-output", n.labels(a, regions, geoms), width="dense"))

    a = p(11)
    n.h(a, [25, 23, 345, 41])
    panel_start = len(n.current["nodes"])
    n.add(n.figure("dc-output", n.labels(a, [
        [35, 47, 190, 65], [270, 59, 345, 83], [270, 83, 345, 110]],
        [([2, 3, 47, 9], "#f2f2f3"), ([80, 10, 19, 13],), ([80, 24, 19, 13],)]),
        width="dense"))
    notice(n, a, [25, 204, 90, 299], [90, 204, 345, {"en": 285, "fr": 302, "es": 302}[language]], "caution")
    cy = {"en": 286, "fr": 308, "es": 304}[language]
    resume = {"en": 374, "fr": 394, "es": 397}[language]
    n.paras(a, [25, cy, 345, cy + 22])
    notice(n, a, [25, cy + 22, 90, resume], [90, cy + 22, 345, resume - 4], "caution")
    panel_nodes = n.current["nodes"][panel_start:]
    n.current["nodes"][panel_start:] = []
    n.add(node("group", panel_nodes, role="container", presentation={
        "html": {"attributes": {"class": "native-operation-frame native-dc-panel"}}}))
    n.h(a, [25, resume - 1, 345, resume + 13])
    n.paras(a, [25, resume + 12, 345, resume + 34])
    table = n.doc[a - 1].find_tables().tables[0]
    split = {"en": 210, "fr": 162, "es": 162}[language]
    headers = [cell(n.t(a, [28, table.bbox[1] - 13, split, table.bbox[1]]), header=True),
               cell(n.t(a, [split, table.bbox[1] - 13, 345, table.bbox[1]]), header=True)]
    rows = words_in_table(n, a, table, [28, split, 345])
    last = [n.t(a, [x0, table.bbox[3], x1, 498])
            for x0, x1 in [(28, split), (split, 345)]]
    n.add(scroll_table([headers] + [[cell(v) for v in row] for row in rows + [last]]))

    a = p(12)
    energy_raw = n.take(a, [25, 22, 345, {"en": 122, "fr": 122, "es": 131}[language]])[1]
    title, *body = energy_raw.split("\n")
    n.add(heading(normalize(title)), paragraph(normalize("\n".join(body))))
    # Source labels in the FR art remain English, as printed.
    y = {"en": 180, "fr": 184, "es": 191}[language]
    action_x = {"en": 220, "fr": 210, "es": 188}[language]
    n.add(n.figure("energy", n.labels(a, [
        [140, y, 235, y + 12], [240, y, 340, y + 12],
        [action_x, y + 13, 350, y + 45], [170, y + 13, action_x, y + 45]],
        [([39, 57, 30, 11],), ([72, 57, 27, 11],),
         ([62, 74, 37, 25],), ([58, 83, 6, 10],)]),
        width="dense"))
    ly = {"en": 227, "fr": 231, "es": 238}[language]
    label = {"en": "NOTE", "fr": "REMARQUE", "es": "NOTA"}[language]
    value = n.t(a, [25, ly, 345, ly + 27]).replace(label, "").strip()
    n.add(callout(label, [paragraph(value)], variant="note", language=language,
                  source_ref=f"native-pdf/page-{a}/energy-note"))
    hy = {"en": 267, "fr": 264, "es": 271}[language]
    n.h(a, [25, hy - 1, 345, hy + 14])
    panel_start = len(n.current["nodes"])
    # Six rows; first column has two native rowspans, preserved in live HTML.
    base = {"en": 374, "fr": 371.6, "es": 378.4}[language]
    x1 = {"en": 97, "fr": 91, "es": 71}[language]
    x2 = {"en": 121, "fr": 121, "es": 98}[language]
    modes = [n.t(a, [28, base, x1, base + 31]),
             n.t(a, [28, base + 31, x1, base + 65])]
    rows = []
    for i in range(6):
        row = []
        if i in {0, 3}:
            row.append(cell(modes[i // 3], row_span=3, header=True))
        # Actions can have two typographic lines inside one 10pt source row.
        action_words = [w for w in n.words[a] if x1 <= (w[0] + w[2]) / 2 < x2
                        and base - 2 <= w[1] < base + 65]
        action_words.sort(key=lambda w: w[1])
        # Read each native label block near the action's known baseline.
        yy = base + i * 10
        candidates = [b for b in n.doc[a - 1].get_text("blocks")
                      if x1 <= (b[0] + b[2]) / 2 < x2 and abs(b[1] - yy) < 4]
        if candidates:
            b = min(candidates, key=lambda b: abs(b[1] - yy))
            action = n.t(a, [x1, b[1] - .1, x2, b[3] + .1])
        else:
            action = n.t(a, [x1, yy - 1, x2, yy + 9])
        desc = n.t(a, [x2, yy - 1, 345, yy + 9])
        row.extend([cell(action), cell(desc)])
        rows.append(row)
    state_groups = []
    for i in range(2):
        state_groups.append({
            **pair("state", modes[i]),
            "actions": [{**pair("action", rows[i * 3 + j][-2]["children"][0]["text"]),
                         **pair("description", rows[i * 3 + j][-1]["children"][0]["text"])}
                     for j in range(3)],
        })
    n.add(n.comp(lcd_mode_component_spec, accessibility_label="LCD screen modes",
                 groups=state_groups, artwork_ref="assets/lcd-button.svg"))
    n.paras(a, [25, base + 65, 345, base + 87])
    panel_nodes = n.current["nodes"][panel_start:]
    n.current["nodes"][panel_start:] = []
    n.add(node("group", panel_nodes, role="container", presentation={
        "html": {"attributes": {"class": "native-operation-frame native-lcd-panel"}}}))

    a = p(13)
    n.h(a, [25, 22, 345, 40])
    table = n.doc[a - 1].find_tables().tables[0]
    rows = words_in_table(n, a, table, [28, 154, 236, 345])
    controls = [["power.svg", "ac.svg"], ["power.svg", "dc_usb.svg"], ["dc_usb.svg", "ac.svg"]]
    table_rows = [[cell(v, header=True) for v in rows[0]]]
    for row, icons in zip(rows[1:], controls, strict=True):
        images = [node("image", source="assets/" + image, alt="", presentation={
            "html": {"attributes": {"class": "native-button-icon"}}}) for image in icons]
        first = node("table_cell", [*images, text(row[0])], header=False)
        table_rows.append([first, cell(row[1]), cell(row[2])])
    n.add(scroll_table(table_rows))
    n.chapter("ups", n.t(a, [25, 190, 345, 217]))
    n.paras(a, [25, 215, 345, 306], )
    n.add(n.figure("ups"))
    notice(n, a, [25, 429, 84, 498], [84, 429, 345, 498], "caution")

    a = p(14)
    n.chapter("charging", n.t(a, [25, 25, 345, 50]))
    n.paras(a, [25, 50, 345, {"en": 92, "fr": 99, "es": 101}[language]])
    n.paras(a, [25, {"en": 94, "fr": 99, "es": 102}[language], 345, 117])
    notice(n, a, [25, 118, 72, 194], [72, 118, 345, 194], "note")
    n.h(a, [25, 196, 345, 222])
    n.paras(a, [25, 216, 345, 234])
    n.add(n.figure("ac-charge"))
    label = {"en": "CAUTION", "fr": "ATTENTION", "es": "PRECAUCIÓN"}[language]
    value = n.t(a, [25, 375, 345, 431]).replace(label, "").strip()
    n.add(callout(label, [paragraph(value)], variant="caution", language=language,
                  source_ref=f"native-pdf/page-{a}/ac-caution"))
    a = p(15)
    n.h(a, [25, 23, 345, 41])
    end = {"en": 73, "fr": 86, "es": 89}[language]
    n.paras(a, [25, 40, 345, end])
    n.add(n.figure("solar", [(n.t(a, [245, 220, 335, 260]), [70, 86, 28, 9])]))
    cy = {"en": 265, "fr": 283, "es": 283}[language]
    raw = n.t(a, [25, cy, 345, cy + 16]).replace(label, "").strip()
    n.add(callout(label, [paragraph(raw)], variant="caution", language=language,
                  source_ref=f"native-pdf/page-{a}/solar-limit"))
    bottom = {"en": 357, "fr": 370, "es": 370}[language]
    notice(n, a, [25, cy + 17, 84, bottom], [84, cy + 17, 345, bottom], "caution")
    n.paras(a, [25, bottom, 345, 419])
    a = p(16)
    n.h(a, [25, 22, 345, 40])
    n.paras(a, [25, 38, 345, 59])
    n.add(n.figure("car", [
        (n.t(a, [235, 92, 280, 115]), [65, 23, 20, 9]),
        (n.t(a, [150, 181, 340, 201]), [41, 80, 56, 12], "#ffffff"),
    ], panel="#f2f2f3"))
    notice(n, a, [25, 217, 84, 300], [84, 217, 345, 300], "caution")

    a = p(17)
    n.chapter("storage", n.t(a, [25, 25, 345, 50]))
    raw = n.take(a, [25, 50, 345, 140])[1]
    # Keep the paragraph after the three duration bullets outside the list.
    lines = raw.split("\n")
    start = next(i for i, line in enumerate(lines) if line.startswith(("If this", "Si ce", "Si este")))
    n.add(*prose("\n".join(lines[:start])), paragraph(normalize("\n".join(lines[start:]))))
    n.chapter("troubleshooting", n.t(a, [25, 145, 345, 168]))
    n.paras(a, [25, 170, 345, 194])
    table = n.doc[a - 1].find_tables().tables[0]
    headers = [pair("content", n.t(a, [28, 195, 78, 211])),
               pair("content", n.t(a, [78, 195, 345, 211]))]
    # First four codes share one merged native corrective-measures cell.
    source_rows = words_in_table(n, a, table, [28, 78, 345])
    combined = source_rows[:4]
    rows = [{**pair("code", " / ".join(row[0] for row in combined)),
             **pair("measures", " ".join(row[1] for row in combined if row[1]))}]
    rows.extend({**pair("code", row[0]), **pair("measures", row[1])}
                for row in source_rows[4:])
    rows.append({**pair("code", n.t(a, [28, table.bbox[3], 78, 451])),
                 **pair("measures", n.t(a, [78, table.bbox[3], 345, 451]))})
    for row in rows:
        value = row["measures_text"]
        steps = re.split(r"(?<!\d)(?=\d\.\s)", value)
        if len(steps) > 2 and not steps[0].strip():
            items = [re.sub(r"^\d\.\s*", "", v).strip() for v in steps[1:]]
            row["measures_html"] = "<ol>" + "".join("<li>" + html.escape(v) + "</li>" for v in items) + "</ol>"
    n.add(n.comp(troubleshooting_component_spec, headers=headers, rows=rows))

    a = p(18)
    n.chapter("specifications", n.t(a, [25, 25, 345, 50]))
    tables = n.doc[a - 1].find_tables().tables
    for table in tables:
        title = n.t(a, [25, table.bbox[1] - 17, 345, table.bbox[1]])
        split = table.rows[0].cells[0][2]
        rows = words_in_table(n, a, table, [28, split, 345])
        n.add(n.comp(spec_table_component_spec, section_title=title, rows=rows))
    for block in sorted(n.doc[a - 1].get_text("blocks"), key=lambda b: b[1]):
        if tables[-1].bbox[3] <= block[1] < 420:
            value = n.take(a, list(block[:4]))[0]
            marker = re.search(r"[①②]", value)
            if marker:
                value = marker[0] + " " + value.replace(marker[0], "").strip()
            n.add(paragraph(value))

    a = p(19)
    n.chapter("warranty", n.t(a, [25, 25, 345, 50]))
    lead = n.t(a, [25, 53, 345, 81])
    local = n.t(a, [25, 82, 345, {"en": 97, "fr": 104, "es": 104}[language]])
    n.add(n.comp(warranty_lead_component_spec, accessibility_label=n.current["title"],
                 lead_html="<strong>" + html.escape(lead) + "</strong>",
                 local_note_html=html.escape(local)))
    # Native section headings differ in height by locale. Font/position binds each.
    blocks = n.doc[a - 1].get_text("dict")["blocks"]
    titles = []
    for block in blocks:
        for line in block.get("lines", []):
            if 96 < line["bbox"][1] < 470 and any(6.8 < s["size"] < 8.5 for s in line["spans"]):
                raw = "".join(s["text"] for s in line["spans"])
                if line["bbox"][0] < 50 and len(raw) < 100:
                    titles.append((line["bbox"], normalize(raw)))
    titles.sort(key=lambda item: item[0][1])
    assert len(titles) == 6, (language, titles)
    for i, (box, title) in enumerate(titles):
        n.t(a, [box[0] - .1, box[1] - .1, box[2] + .1, box[3] + .1])
        end = titles[i + 1][0][1] if i < 5 else 499
        n.add(heading(title, level=3))
        if i == 1:
            title_y = box[3]
            body_y = {"en": 213, "fr": 223, "es": 221}[language]
            labels = [n.t(a, [35, title_y, 213, body_y - 1]),
                      n.t(a, [220, title_y, 345, body_y - 1])]
            standard = n.t(a, [35, body_y - 1, 215, end])
            extended = n.t(a, [220, body_y - 1, 345, end])
            periods = []
            unit = {"en": "YEARS", "fr": "ANS", "es": "ÑOS"}[language]
            for number, raw, body in zip(["3", "2"], labels, [standard, extended], strict=True):
                clean = re.sub(r"\b(?:3|2|YEARS|ANS|A?ÑOS)\b", "", raw).strip()
                periods.append({"number": number, "unit": unit, "label": clean,
                                "body_html": html.escape(body), "body_text": body})
            n.add(n.comp(warranty_years_component_spec, title=title, periods=periods))
        else:
            _, raw, _ = n.take(a, [25, box[3], 345, end], unused=True)
            flow = prose(raw)
            content = []
            for item in flow:
                if item["kind"] == "list":
                    values = [c["children"][0]["text"] for c in item["children"]]
                    content.append({"kind": "list", "items": values,
                                    "html": "<ul>" + "".join("<li>" + html.escape(v) + "</li>"
                                                            for v in values) + "</ul>"})
                else:
                    value = item["children"][0]["text"]
                    content.append({"kind": "paragraph", "text": value, "html": html.escape(value)})
            n.add(n.comp(warranty_section_component_spec, title=title,
                         section_index=i + 1, blocks=content))

    a = p(20)
    n.chapter("app", n.t(a, [25, 25, 345, 48]))
    n.h(a, [25, 48, 345, 67])
    columns = [
        {"role": "store", "text": n.t(a, [25, 119, 190, 160])},
        {"role": "qr", "text": n.t(a, [190, 119, 345, 160])},
    ]
    for col in columns:
        col["html"] = html.escape(col["text"])
    n.add(n.comp(app_download_component_spec, accessibility_label="App download", columns=columns,
                 source_art_ref="assets/app_store_badges.png",
                 store_art_ref="assets/app_store_badges.png", qr_art_ref="assets/app_download_qr.png"))
    n.h(a, [25, 155 if language == "en" else 160, 190, 175])
    app_steps = {step: index for index, block in enumerate(n.doc[a - 1].get_text("blocks"))
                 for step in ("2.1", "2.2") if block[1] < 250 and block[4].startswith(step)}
    first_step = n.b(a, app_steps["2.1"])
    button_word = {"en": "button", "fr": "bouton", "es": "botón"}[language]
    before, after = first_step.split(button_word, 1)
    n.add(node("paragraph", [text(before + button_word + " "),
          node("inline_group", [text("+")],
               presentation={"html": {"attributes": {"class": "native-inline-plus"}}}),
          text(after)]))
    n.add(paragraph(n.b(a, app_steps["2.2"])))
    # Matching screenshot counters are already embedded, not second captions.
    n.take(a, [25, 350, 345, 394], purpose="embedded-counter/app_add.png")
    control_y = {"en": 391, "fr": 402, "es": 402}[language]
    n.add(node("group", [
        reference_image("app_add.png", "App steps 2.1 and 2.2", language),
        n.figure("app-control", n.labels(a, [
            [25, control_y, 115, control_y + 25], [25, control_y + 25, 115, 450],
            [250, 400, 345, 450]],
            [([0, 12, 24, 27],), ([0, 46, 24, 27],), ([76, 44, 24, 28],)]),
            width="controls"),
    ], role="container", presentation={"html": {"attributes": {"class": "native-app-add"}}}))
    a = p(21)
    blocks = n.doc[a - 1].get_text("blocks")
    app_steps = {step: index for index, block in enumerate(blocks)
                 for step in ("2.3", "2.4", "2.5") if block[1] < 250 and block[4].startswith(step)}
    for step, next_step in [("2.3", "2.4"), ("2.4", "2.5")]:
        n.add(paragraph(n.b(a, app_steps[step])))
        start = blocks[app_steps[step]][3] + .1
        end = blocks[app_steps[next_step]][1] - .1
        notice(n, a, [25, start, 86, end], [86, start, 345, end], "note")
    n.add(paragraph(n.b(a, app_steps["2.5"])))
    n.add(reference_image("app_connect_result_steps.png", "App steps 2.3, 2.4 and 2.5", language))
    n.take(a, [25, 280, 345, 305], purpose="embedded-counter/app_connect_result_steps.png")
    caption_y = {"en": 302, "fr": 305, "es": 309}[language]
    n.paras(a, [25, caption_y, 345, caption_y + 12])
    y = {"en": 317, "fr": 317, "es": 321}[language]
    value = n.t(a, [25, y, 345, {"en": 342, "fr": 347, "es": 351}[language]])
    caution_label = {"en": "CAUTION", "fr": "ATTENTION", "es": "PRECAUCIÓN"}[language]
    n.add(callout(caution_label, [paragraph(value.replace(caution_label, "").strip())],
                  variant="caution", language=language, source_ref=f"native-pdf/page-{a}/bluetooth"))
    # Keep native subheadings and bullet structure from the final block group.
    for block in sorted(n.doc[a - 1].get_text("blocks"), key=lambda b: b[1]):
        if 348 <= block[1] < 500:
            raw = n.take(a, list(block[:4]), unused=True)[1]
            lines = raw.split("\n")
            if lines[0].startswith(("3.", "4.")):
                for line in lines:
                    if line.startswith(("3.", "4.")):
                        n.add(heading(normalize(line), level=3 if line.startswith(("3. ", "4. ")) else 4))
                    else:
                        n.add(*prose(line))
            else:
                n.add(*prose(raw))
    n.chapter("contact", n.b(58, 0))
    n.add(paragraph(n.b(58, 2)), paragraph(n.b(58, 1)))
    missing = n.finish()
    print(language, "chapters", len(n.chapters), "unmapped", len(missing))
    return missing


def reference_image(name, label, language):
    """Reuse complete App frames through the shared figure component."""
    from native import reference_flow, sha
    from tools.component_specs.reference_figure import reference_figure_component_spec
    return reference_flow(reference_figure_component_spec(
        reference_id=name.removesuffix(".png"), accessibility_label=label,
        caption_mode="embedded", captions=[], adjacent_copy=None,
        source_art_ref="assets/" + name, source_art_locale_policy="shared",
        source_fragment_sha256=sha(SOURCE / "assets" / name),
        source_ref="native-pdf/app/" + name, language=language,
        image_key=name.removesuffix(".png"),
    ), [node("image", source="assets/" + name, alt=label)])


if __name__ == "__main__":
    failures = {}
    for lang in ("en", "fr", "es"):
        missing = make(lang)
        if missing:
            failures[lang] = missing
    dump(SOURCE / "source/unmapped.json", failures)
    if failures:
        raise SystemExit("Unmapped native words: see source/unmapped.json")
