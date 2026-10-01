"""Mechanical native-copy preparation for the existing solar RST/CSV lane."""

from pathlib import Path
import argparse
import hashlib
import csv
import json
import re
import fitz

ROOT = Path(__file__).resolve().parents[7]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--master", type=Path, required=True)
args = parser.parse_args()
OUT = ROOT / "data/manual_sources/JS-100I/EU/added-locales/2026-09-28"
assert hashlib.sha256(args.master.read_bytes()).hexdigest() == (
    "6fd4533fd713b25d95547afa0d839d7a52c74e6e6e40ebf2228c6c8218cbc92f"
), "Source master changed"
DOC = fitz.open(args.master)
assert len(DOC) == 87
LOCALES = {
    "fr": list(range(14, 23)),
    "es": list(range(23, 32)),
    "de": [32, 33, 34, 36, 37, 38, 39, 40, 41],
    "it": list(range(42, 51)),
    "uk": list(range(51, 60)),
    "pt": list(range(60, 69)),
    "nl": list(range(69, 78)),
    "pl": list(range(78, 87)),
}
LIG = str.maketrans({"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl"})
RECORDS = []


def normalize(s):
    s = s.translate(LIG)
    s = re.sub(r"jack-\s*\n\s*ery", "jackery", s)
    s = re.sub(r"klantenser-\s*\n\s*vice", "klantenservice", s)
    return (
        " ".join(s.split())
        .replace("fonctionne ment", "fonctionnement")
        .replace("funcionamien to", "funcionamiento")
    )


def T(n, box, key):
    lines = []
    glyphs = []
    for bi, b in enumerate(DOC[n - 1].get_text("rawdict")["blocks"]):
        for li, l in enumerate(b.get("lines", [])):
            chars = []
            loc = []
            for si, s in enumerate(l["spans"]):
                x = (s["bbox"][0] + s["bbox"][2]) / 2
                y = sum(c["origin"][1] for c in s["chars"]) / max(1, len(s["chars"]))
                if box[0] <= x < box[2] and box[1] <= y < box[3]:
                    for ci, c in enumerate(s["chars"]):
                        chars.append(c["c"])
                        loc.append(c["origin"])
                        glyphs.append(f"{n}:{bi}:{li}:{si}:{ci}")
            if chars:
                lines.append(
                    (min(p[1] for p in loc), min(p[0] for p in loc), "".join(chars))
                )
    lines.sort(key=lambda z: (round(z[0], 1), z[1]))
    native = "\n".join(z[2] for z in lines)
    value = normalize(native)
    if not value:
        raise ValueError((n, key, box))
    RECORDS.append(
        {
            "key": key,
            "physical_page": n,
            "bbox_pt": box,
            "native_text": native,
            "text": value,
            "glyph_ids": glyphs,
        }
    )
    return value


def H(s, level=1):
    return s + "\n" + {1: "=", 2: "-", 3: "~"}[level] * max(50, len(s) + 3) + "\n\n"


def E(s):
    return s.replace("\\", "\\\\").replace("*", "\\*").replace("|", "\\|")


def image(name, caption, labels=()):
    folder = "js100i_eu_added" if name.startswith("views_") else "js100i_eu_shared"
    text = " · ".join(labels) if labels else caption
    text = re.sub(r"^([1-4])\. ", r"\1\\. ", E(text))
    cls = "manual-step-figure" + (
        " manual-detail-figure" if name.startswith("angle_choice") else ""
    )
    return f".. figure:: renderers/web/assets/{folder}/{name}.png\n   :alt: {E(caption)}\n   :figclass: {cls}\n   :width: 100%\n\n   {text}\n\n"


def note(label, body):
    return (
        ".. list-table::\n   :header-rows: 0\n   :widths: 15 85\n\n   * - **"
        + E(label)
        + "**\n     - "
        + E(body)
        + "\n\n"
    )


def write_csv(name, fields, rows):
    path = OUT / "phase2" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fields)
        w.writeheader()
        w.writerows(rows)


SPEC = []
NOTES = []
TITLES = []
DATA = {}
base = list(
    csv.DictReader(
        open(ROOT / "data/manual_sources/JS-100I/EU/en/2.0/phase2/Spec_Master.csv")
    )
)
for lang, pages in LOCALES.items():
    start = len(RECORDS)
    p0, p1, p2, p3, p4, p5, p6, p7, p8 = pages

    def t(n, box, key, lang=lang):
        return T(n, box, lang + "/" + key)

    a = {}
    a["pages"] = pages
    a["safety_title"] = t(p0, [20, 25, 350, 50], "safety/title")
    # Inbox heading is the second >11pt heading, safely after safety columns.
    headings = [
        s
        for b in DOC[p0 - 1].get_text("dict")["blocks"]
        for l in b.get("lines", [])
        for s in l["spans"]
        if s["size"] > 11 and 200 < s["origin"][1] < 270
    ]
    box_y = min(s["bbox"][1] for s in headings)
    a["inbox_title"] = t(p0, [20, box_y, 350, box_y + 20], "inbox/title")
    a["safety"] = [
        t(p0, [25, 50, 185, box_y], "safety/left"),
        t(p0, [185, 50, 345, box_y], "safety/right"),
    ]
    a["inbox_labels"] = [
        t(p0, [x0, 320, x1, 362 if x0 >= 235 else 361], "inbox/card" + str(i + 1))
        for i, (x0, x1) in enumerate([(25, 135), (135, 235), (235, 345)])
    ] + [
        t(p0, [25, 425, 135, 455], "inbox/card4"),
        t(p0, [135, 425, 235, 455], "inbox/card5"),
    ]
    a["note_label"] = t(p0, [25, 458, 68, 500], "inbox/note-label")
    a["note_body"] = t(p0, [68, 458, 346, 500], "inbox/note-body")
    a["views_title"] = t(p1, [20, 25, 350, 50], "views/title")
    a["views_caption"] = [
        t(p1, [20, 63, 110, 82], "views/front"),
        t(p1, [20, 197, 110, 220], "views/rear"),
    ]
    a["views_labels"] = " · ".join(
        t(p1, box, "views/label" + str(i))
        for i, box in enumerate(
            [
                [190, 80, 345, 150],
                [20, 220, 165, 270],
                [40, 360, 170, 405],
                [180, 350, 345, 405],
            ]
        )
    )
    a["unfold_title"] = t(p2, [35, 20, 348, 53], "unfold/title")
    a["fold_title"] = t(p3, [35, 143, 348, 178], "fold/title")

    # Extract numbered source paragraphs as whole native blocks, including wrapped lines.
    def steps(n, lang=lang):
        result = {}
        for b in DOC[n - 1].get_text("dict")["blocks"]:
            if b["type"] != 0:
                continue
            s = "\n".join("".join(z["text"] for z in l["spans"]) for l in b["lines"])
            m = re.match(r"\s*([1-4])\.\s+", s)
            if m:
                box = list(b["bbox"])
                box = [box[0] - 0.2, box[1] - 0.2, box[2] + 0.2, box[3] + 0.2]
                result[int(m[1])] = T(n, box, lang + f"/steps/{n}/{m[1]}")
        return result

    st = steps(p2)
    st2 = steps(p3)

    if lang == "pt":
        st2[4] = t(p3, [30, 29, 345, 54], "unfold/step4-complete")
    a["unfold"] = [st[i] for i in (1, 2, 3)] + [st2[4]]
    a["fold"] = [st2[i] for i in (1, 2, 3)]
    a["charge_title"] = t(p4, [30, 22, 348, 44], "charge/title")
    a["charge_intro"] = t(p4, [30, 44, 348, 61], "charge/intro")
    a["dc_title"] = t(p4, [30, 61, 348, 73], "charge/dc-title")
    a["dc_body"] = t(p4, [30, 73, 348, 101], "charge/dc-body")
    a["dc_label"] = t(p4, [155, 100, 300, 136], "charge/dc-label")
    a["adapter_title"] = t(p4, [30, 264, 348, 285], "charge/adapter-title")
    a["adapter_body"] = t(p4, [30, 285, 348, 311], "charge/adapter-body")
    a["adapter_label"] = t(p4, [140, 311, 310, 340], "charge/adapter-label")
    a["usbc_title"] = t(p5, [30, 20, 349, 39], "charge/usbc-title")
    a["usbc_body"] = t(p5, [30, 39, 349, 58], "charge/usbc-body")
    a["usbc_label"] = t(p5, [140, 58, 300, 86], "charge/usbc-label")
    a["usbc_note_label"] = t(p5, [25, 196, 67, 233], "charge/usbc-note-label")
    a["usbc_note"] = t(p5, [67, 196, 348, 233], "charge/usbc-note")
    a["parallel_title"] = t(p5, [25, 233, 348, 250], "charge/parallel-title")
    a["parallel_body"] = t(p5, [30, 250, 348, 279], "charge/parallel-body")
    a["parallel_labels"] = [
        t(p5, [140, 279, 275, 315], "charge/parallel-label1"),
        t(p5, [150, 385, 305, 423], "charge/parallel-label2"),
    ]
    a["parallel_note"] = t(p5, [30, 429, 347, 466], "charge/parallel-note")
    a["angle_title"] = t(p6, [30, 20, 349, 42], "angle/title")
    a["angle_intro"] = t(p6, [30, 42, 349, 67], "angle/intro")
    a["angle_body"] = t(p6, [30, 184, 349, 224], "angle/body")
    a["angle_labels"] = [
        t(p6, [212, 102, 292, 131], "angle/label1"),
        t(p6, [271, 140, 348, 155], "angle/label2"),
        t(p6, [271, 155, 348, 181], "angle/label3"),
    ]
    a["angle_choices"] = [
        t(p6, [114, 229, 181, 266], "angle/choice1"),
        t(p6, [270, 229, 349, 266], "angle/choice2"),
    ]
    a["angle_note_label"] = t(p6, [25, 268, 67, 308], "angle/note-label")
    a["angle_note"] = t(p6, [67, 268, 348, 308], "angle/note")
    a["device_title"] = t(p6, [30, 311, 348, 336], "device/title")
    a["device_labels"] = [
        t(p6, [35, 426, 140, 444], "device/product"),
        t(p6, [250, 340, 345, 370], "device/adapter"),
    ]
    a["device_port_labels"] = [
        t(p6, [203, 366, 216, 375], "device/port-usbc-original"),
        t(p6, [216, 367, 225, 376], "device/port-led-original"),
        t(p6, [223, 373, 234, 381], "device/port-usba-original"),
    ]
    a["device_engraving"] = t(p6, [202, 409, 214, 417], "device/engraving")
    a["device_outputs"] = [
        t(p6, [x0, 465, x1, 483], f"device/output{i}")
        for i, (x0, x1) in enumerate([(135, 188), (188, 232), (232, 272)])
    ]
    a["dust_note"] = t(p7, [28, 27, 182, 77], "device/dust-note")
    a["spec_title"] = t(p7, [28, 129, 345, 152], "spec/title")
    a["spec_product_title"] = t(p7, [30, 152, 345, 165], "spec/product-title")
    a["spec_groups"] = [
        t(p7, [25, 165, 345, 178], "spec/group1"),
        t(p7, [25, 264, 345, 280], "spec/group2"),
        t(p7, [25, 464, 345, 473], "spec/group3"),
    ]
    sr = []
    for i, row in enumerate(base):
        if i < 7:
            edges = [177, 190.8, 202.8, 214.5, 226.2, 238.5, 251, 264]
            y0, y1 = edges[i : i + 2]
            label = t(p7, [28, y0, 157, y1], f"spec/row{i}/label")
            value = t(p7, [157, y0, 345, y1], f"spec/row{i}/value")
        elif i < 19:
            j = i - 7
            edges = [
                291,
                303,
                314,
                325.2,
                338.5,
                351.5,
                363,
                374.5,
                386.8,
                399,
                411.5,
                424,
                435.5,
            ]
            y0, y1 = edges[j : j + 2]
            # Two wrapped Italian labels extend below their row; native baselines remain inside row.
            label = t(p7, [27, y0, 157, y1], f"spec/row{i}/label")
            if j < 5:
                v1 = t(p7, [157, y0, 247, y1], f"spec/row{i}/stc")
                v2 = t(p7, [247, y0, 345, y1], f"spec/row{i}/bnpi")
                value = f"STC*: {v1} / BNPI*: {v2}"
            else:
                value = t(p7, [157, y0, 345, y1], f"spec/row{i}/value")
        else:
            y0 = 473 + (i - 19) * 11
            y1 = y0 + 11
            label = t(p7, [27, y0, 156, y1], f"spec/row{i}/label")
            value = t(p7, [156, y0, 345, y1], f"spec/row{i}/value")
        group = a["spec_groups"][0 if i < 7 else 1 if i < 19 else 2]
        sr.append(
            {
                **row,
                "Source_lang": lang,
                "Section": group,
                "Row_label_source": label,
                "Value_source": value,
                "page_title_source": a["spec_title"] if i == 0 else "",
            }
        )
    # The CSV field names are the existing formal contract.
    a["spec_rows"] = sr
    SPEC += sr
    a["spec_notes"] = t(p7, [25, 435, 347, 464], "spec/notes")
    for j, n in enumerate(re.split(r"(?=\* (?:STC|BNPI))", a["spec_notes"])):
        if n.strip():
            NOTES.append(
                {
                    "Note_id": f"note{j}",
                    "Region": "EU",
                    "Model": "JS-100I",
                    "Source_lang": lang,
                    "Is_Latest": "TRUE",
                    "Page": "specifications",
                    "Note_order": j + 1,
                    "Text_en": n.strip(),
                    "Enabled": "TRUE",
                }
            )
    a["warranty_title"] = t(p8, [25, 25, 345, 51], "warranty/title")
    a["period_title"] = t(p8, [25, 60, 345, 81], "warranty/period-title")
    a["periods"] = []
    for j, (x0, x1, nx0, ux0) in enumerate([(35, 210, 35, 62), (214, 337, 214, 244)]):
        a["periods"].append(
            {
                "number": t(p8, [nx0, 78, ux0, 110], f"warranty/{j}/number"),
                "unit": t(p8, [ux0, 78, x1, 99], f"warranty/{j}/unit"),
                "label": t(p8, [ux0, 99, x1, 110], f"warranty/{j}/label"),
                "body": t(p8, [x0, 110, x1, 198], f"warranty/{j}/body"),
            }
        )
    # Contact/customer headings and body start differ by locale, so take the bold spans below 198.
    h = []
    for b in DOC[p8 - 1].get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            for s in l["spans"]:
                if s["origin"][1] > 198 and "Bold" in s["font"] and s["text"].strip():
                    h.append(s)
    customer = min(s["bbox"][1] for s in h if s["bbox"][1] > 260)
    contact = min(s["bbox"][1] for s in h if s["bbox"][1] < 260)
    contact_end = max(s["bbox"][3] for s in h if s["bbox"][1] < 260) + 0.2
    a["contact_title"] = t(
        p8, [28, contact, 345, contact_end], "warranty/contact-title"
    )
    a["contact_body"] = t(p8, [28, contact_end, 345, customer], "warranty/contact-body")
    a["customer_title"] = t(
        p8, [28, customer, 345, customer + 16], "warranty/customer-title"
    )
    a["customer_body"] = t(p8, [28, customer + 17, 345, 360], "warranty/customer-body")
    a["legal_title"] = t(87, [25, 346, 345, 370], "legal/title")
    a["legal"] = t(87, [25, 371, 345, 500], "legal/body")
    DATA[lang] = a
    p = OUT / "source" / f"{lang}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(a, ensure_ascii=False, indent=2) + "\n")

    # Use the exact existing solar slot filenames and structure, replacing only locale copy.
    dest = ROOT / "docs/templates/page_solar" / lang
    dest.mkdir(parents=True, exist_ok=True)
    text = (
        H(a["safety_title"])
        + "".join(
            "* " + E(s.strip()) + "\n"
            for col in a["safety"]
            for s in col.split("*")
            if s.strip()
        )
        + "\n"
    )
    (dest / "01_safety_tips.rst").write_text(text)
    text = (
        H(a["inbox_title"])
        + ".. list-table::\n   :header-rows: 0\n   :widths: 20 20 20 20 20\n\n"
    )
    for j, (name, label) in enumerate(
        zip(["panel", "bag", "cable", "adapter", "manual"], a["inbox_labels"])
    ):
        text += (
            ("   * - " if j == 0 else "     - ")
            + f".. image:: renderers/web/assets/js100i_eu_en/inbox_{name}.png\n          :alt: {E(label)}\n\n       **{E(label)}**\n"
        )
    text += "\n" + note(a["note_label"], a["note_body"])
    (dest / "02_whats_in_the_box.rst").write_text(text)
    text = H(a["views_title"]) + image(
        f"views_{lang}", a["views_title"], a["views_caption"] + [a["views_labels"]]
    )
    (dest / "03_product_views.rst").write_text(text)
    text = H(a["unfold_title"])
    for i, s in enumerate(a["unfold"], 1):
        text += image(f"unfold_{i}", s, [s])
    (dest / "04_unfolding.rst").write_text(text)
    text = H(a["fold_title"])
    for i, s in enumerate(a["fold"], 1):
        text += image(f"fold_{i}", s, [s])
    (dest / "05_folding.rst").write_text(text)
    text = H(a["charge_title"]) + E(a["charge_intro"]) + "\n\n"
    for tag, art in [("dc", "dc8020"), ("adapter", "dc7909"), ("usbc", "usbc")]:
        text += (
            H(a[tag + "_title"], 2)
            + E(a[tag + "_body"])
            + "\n\n"
            + image(art, a[tag + "_title"], [a[tag + "_label"]])
        )
        if tag == "usbc":
            text += note(a["usbc_note_label"], a["usbc_note"])
    text += (
        H(a["parallel_title"], 2)
        + E(a["parallel_body"])
        + "\n\n"
        + image("parallel", a["parallel_title"], a["parallel_labels"])
        + E(a["parallel_note"])
        + "\n\n"
    )
    (dest / "06_charging_connections.rst").write_text(text)
    text = (
        H(a["angle_title"])
        + E(a["angle_intro"])
        + "\n\n"
        + image("angle", a["angle_title"], a["angle_labels"])
        + E(a["angle_body"])
        + "\n\n"
    )
    for i, s in enumerate(a["angle_choices"], 1):
        text += image(f"angle_choice_{i}", s, [s])
    text += (
        note(a["angle_note_label"], a["angle_note"])
        + H(a["device_title"], 2)
        + image(
            "device",
            a["device_title"],
            a["device_labels"]
            + ["USB-C", "LED" if lang != "uk" else "Світлодіод", "USB-A"]
            + a["device_outputs"],
        )
        + image("dust", a["dust_note"], [a["dust_note"]])
    )
    (dest / "07_angle_and_device.rst").write_text(text)
    text = H(a["warranty_title"]) + H(a["period_title"], 2)
    for pr in a["periods"]:
        text += (
            H(f"{pr['number']} {pr['unit']} — {pr['label']}", 3)
            + E(pr["body"])
            + "\n\n"
        )
    text += (
        H(a["contact_title"], 2)
        + E(a["contact_body"])
        + "\n\n"
        + H(a["customer_title"], 2)
        + E(a["customer_body"])
        + "\n\n"
        + H(a["legal_title"], 2)
        + E(a["legal"])
        + "\n"
    )
    (dest / "09_warranty.rst").write_text(text)

# Each output language owns a snapshot; Source_lang is not a row filter.
base_root = ROOT / "data/manual_sources/JS-100I/EU/en/2.0/phase2"
for lang in LOCALES:
    write_csv(
        f"{lang}/Spec_Master.csv",
        list(base[0]),
        [r for r in SPEC if r["Source_lang"] == lang],
    )
    notes_fields = [
        f"Text_{lang}" if f == "Text_en" else f
        for f in next(csv.reader(open(base_root / "Spec_Notes.csv")))
    ]
    write_csv(
        f"{lang}/Spec_Notes.csv",
        notes_fields,
        [
            {
                f: r.get("Text_en" if f == f"Text_{lang}" else f, "")
                for f in notes_fields
            }
            for r in NOTES
            if r["Source_lang"] == lang
        ],
    )
    write_csv(
        f"{lang}/Spec_Footnotes.csv",
        next(csv.reader(open(base_root / "Spec_Footnotes.csv"))),
        [],
    )
    write_csv(
        f"{lang}/page_registry.csv",
        next(csv.reader(open(base_root / "page_registry.csv"))),
        [
            {
                "page_id": "spec",
                "order": 20,
                "page_type": "csv_page",
                "sku_scope": "ALL",
                "langs": ",".join(LOCALES),
                "template": "spec_template.rst",
                "content_query": "page_id=spec",
                "asset_ref": "",
                "enabled": 1,
            }
        ],
    )
    write_csv(
        f"{lang}/spec_titles.csv",
        next(csv.reader(open(base_root / "spec_titles.csv"))),
        [],
    )
(OUT / "source" / "positioned_copy.json").write_text(
    "[\n"
    + ",\n".join(
        "  " + json.dumps(r, ensure_ascii=False, separators=(",", ":")) for r in RECORDS
    )
    + "\n]\n"
)
print("authored", len(DATA), "locales", len(RECORDS), "fields")

# Keep generated carriers normalized without trailing blank paragraphs.
for language in LOCALES:
    for carrier in (ROOT / "docs/templates/page_solar" / language).glob("*.rst"):
        carrier.write_text(carrier.read_text().rstrip() + "\n")
