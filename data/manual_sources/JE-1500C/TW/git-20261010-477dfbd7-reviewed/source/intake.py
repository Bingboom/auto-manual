"""Native TW selections, geometry and shared semantic components (no translation)."""

from pathlib import Path
import sys, html, json

REPO = next(p for p in Path(__file__).resolve().parents if (p / "build.py").is_file())
sys.path.insert(0, str(REPO))
import fitz
from native import Native, SOURCE, dump, normalize, pair, attrs, rich, rich_nodes, prose
from tools.component_specs.manual_tables import (
    symbol_signal_component_spec,
    symbol_icon_component_spec,
    lcd_icon_component_spec,
    troubleshooting_component_spec,
)
from tools.component_specs.inbox import inbox_component_spec
from tools.component_specs.spec_table import spec_table_component_spec
from tools.component_specs.lcd_mode import lcd_mode_component_spec
from tools.component_specs.warranty import (
    warranty_lead_component_spec,
    warranty_section_component_spec,
    warranty_years_component_spec,
)
from tools.component_specs.app import (
    app_download_component_spec,
    app_inline_control_component_spec,
)
from tools.manual_ir.components import component_flow_node
from tools.manual_ir.flow import flow_nodes_to_html
from tools.web.frozen_ai_flow import (
    node,
    text,
    heading,
    paragraph,
    callout,
    cell,
    table,
    root,
)

CSS = []
LABEL_LOG = []
N = Native("zh-TW")


def rect(b, pad=0.12):
    return [b[0] - pad, b[1] - pad, b[2] + pad, b[3] + pad]


def block(pg, i):
    return N.b(pg, i)


def body(pg, bbox):
    N.add(*prose(N.take(pg, bbox, unused=True, reading_order="vertical")[1]))


def chapter(pg, i, identity):
    N.chapter(identity, block(pg, i))


def h(pg, i):
    N.add(heading(block(pg, i), level=3))


def notice(pg, labelbox, bodybox, kind):
    label = N.t(pg, labelbox, unused=True)
    raw = N.take(pg, bodybox, unused=True, reading_order="vertical")[1]
    N.add(
        callout(
            label,
            prose(raw),
            variant=kind,
            language=N.language,
            source_ref=f"native-pdf/page-{pg}/notice-{len(N.selections)}",
        )
    )


def richcell(v):
    return {"html": rich(v), "text": v}


def bounded_group(children, classes):
    return node("group", children, role="container", presentation=attrs(classes))


def fig(identity):
    """Every external source line is live, using its native baseline, never its oversized PDF font bbox."""
    g = N.figures[identity]
    pg = g["page"]
    box = fitz.Rect(g["bbox"])
    labels = []
    starts = {}
    for b in N.doc[pg - 1].get_text("rawdict")["blocks"]:
        for l in b.get("lines", []):
            for s in l["spans"]:
                chars = [c for c in s["chars"] if c["c"].strip()]
                if chars:
                    starts[tuple(round(v, 4) for v in s["origin"])] = chars[0]["bbox"][
                        0
                    ]
    baked = []
    if identity == "bottom-cleaning":
        baked = ["A", "B"]
    if identity == "app-result":
        baked = ["1500 Ultra"]
    lines = []
    for b in N.doc[pg - 1].get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            groups = []
            for span in l["spans"]:
                if (
                    not groups
                    or span["color"] != groups[-1][0]["color"]
                    or abs(span["size"] - groups[-1][0]["size"]) > 0.1
                ):
                    groups.append([])
                groups[-1].append(span)
            for group in groups:
                r = fitz.Rect(group[0]["bbox"])
                for span in group[1:]:
                    r |= fitz.Rect(span["bbox"])
                lines.append({"bbox": list(r), "spans": group})
    for l in lines:
        ss = [s for s in l["spans"] if box.contains(fitz.Point(*s["origin"]))]
        if not ss:
            continue
        value = normalize("".join(s["text"] for s in ss))
        if not value:
            continue
        # Source fields printed on device/screenshot remain part of the original image.
        if value in baked:
            continue
        # Complete word identifiers: no neighbouring line is selected by a tall CJK textbox.
        wb = [
            i
            for i, w in enumerate(N.words[pg])
            if abs(w[1] - l["bbox"][1]) < 2
            and l["bbox"][0] - 0.1 <= (w[0] + w[2]) / 2 <= l["bbox"][2] + 0.1
            and box.contains(fitz.Point((w[0] + w[2]) / 2, (w[1] + w[3]) / 2))
        ]
        # MuPDF dict blocks use the same stable native block/line numbering.
        if not wb:
            continue
        for i in wb:
            N.used.setdefault((pg, i), []).append("live-figure-label")
        N.selections.append(
            {
                "page": pg,
                "bbox": list(fitz.Rect(l["bbox"])),
                "purpose": "live-figure-label",
                "word_ids": wb,
                "raw": "".join(s["text"] for s in ss),
                "normalized": value,
            }
        )
        x = min(
            starts.get(tuple(round(v, 4) for v in s["origin"]), s["bbox"][0])
            for s in ss
        )
        size = max(s["size"] for s in ss)
        y = min(s["origin"][1] - s["size"] * 0.86 for s in ss)
        x1 = max(s["bbox"][2] for s in ss)
        children = []
        for s in ss:
            v = normalize(s["text"])
            children.extend(
                [node("strong", [text(v)])]
                if any(k in s["font"] for k in ["Bold", "Heavy", "Medium"])
                or v in ["開機", "關機", "開啟", "關閉"]
                else rich_nodes(v)
            )
        value_nodes = {"nodes": children, "bbox": [x, y, x1, y + size * 1.3]}
        geometry = [
            (x - box.x0) / box.width * 100,
            (y - box.y0) / box.height * 100,
            (x1 - x + 3) / box.width * 100,
            size * 1.5 / box.height * 100,
        ]
        idx = len(labels)
        labels.append((value_nodes, geometry))
        CSS.append(
            f'.native-{identity} [data-source-line="{idx}"]{{font-size:{size / box.width * 100 * (0.94 if identity == "overview-front" else 1):.4f}cqw!important;--hb-label-color:#{ss[0]["color"]:06x};}}'
        )
        LABEL_LOG.append(
            {
                "figure": identity,
                "physical_page": pg,
                "line": idx,
                "text": value,
                "rect": geometry,
                "font_pt": size,
                "native_origin": [x, y + size * 0.86],
                "word_ids": wb,
            }
        )
    for i, w in enumerate(N.words[pg]):
        if w[4] == "•" and box.contains(
            fitz.Point((w[0] + w[2]) / 2, (w[1] + w[3]) / 2)
        ):
            N.used.setdefault((pg, i), []).append("live-figure-list-marker")
            N.selections.append(
                {
                    "page": pg,
                    "bbox": list(w[:4]),
                    "purpose": "live-figure-list-marker",
                    "word_ids": [i],
                    "raw": "•",
                    "normalized": "•",
                }
            )
    out = N.figure(
        identity,
        labels,
        width="dense"
        if identity
        in [
            "overview-front",
            "dc-usb",
            "bottom-cleaning",
            "power",
            "ac-output",
            "energy-buttons",
            "app-result",
        ]
        else "regular",
    )
    return out


# Important notice and safety.
chapter(2, 32, "preface")
body(2, [20, 35, 349, 106])
chapter(2, 31, "safety")
label = block(2, 33)
N.add(
    callout(
        "警告",
        prose(label.removeprefix("警告：").strip()),
        variant="warning",
        language=N.language,
        source_ref="native-pdf/page-2/warning",
    )
)
body(2, [20, 164, 349, 368])
h(2, 23)
body(2, [20, 386, 349, 500])
body(3, [20, 19, 349, 151])
h(3, 2)
body(3, [20, 164, 349, 198])
h(3, 5)
body(3, [20, 212, 349, 249])
chapter(3, 17, "restricted_substances")
# Original marks are vector drawings. Read against rendered p3, not empty PDF cells.
tab = N.doc[2].find_tables().tables[0]
N.take(3, [23, 281, 345, 468], purpose="structured-restricted-substances", unused=True)
heads = [
    "單元Unit",
    "鉛(Pb)",
    "汞(Hg)",
    "鎘(Cd)",
    "六價鉻(Cr+6)",
    "多溴聯苯(PBB)",
    "多溴二苯醚(PBDE)",
]
N.add(paragraph("限用物質及其化學符號"))
rows = [[v, *(["○"] * 6)] for v in ["塑膠外殼", "金屬鐵件", "電路板", "電源線"]]
rows[2][1] = rows[3][1] = "－"
restricted = table(
    [
        [cell(v, header=True) for v in heads],
        *[[cell(v, header=i == 0) for i, v in enumerate(r)] for r in rows],
    ]
)
restricted["presentation"] = attrs("manual-table native-restricted-table")
N.add(bounded_group([restricted], "native-table-scroll"))
notes = normalize(N.doc[2].get_text("blocks")[25][4])
notes = notes.replace('" "', '"○"', 2).replace('" "', '"－"')
# The two symbol gaps have different vector marks; preserve the English source clauses.
notes = '備考1. "超出 0.1 wt%" 及 "超出 0.01 wt %" 係指限用物質之百分比含量超出百分比含量基準值。\nNote 1: "Exceeding 0.1 wt %" and "exceeding 0.01 wt %" indicate that the percentage content of the restricted substance exceeds the reference percentage value of presence condition.\n備考 2. "○" 係指該項限用物質之百分比含量未超出百分比含量基準值。\nNote 2: "○" indicates that the percentage content of the restricted substance does not exceed the percentage of reference value of presence\n備考3. "－" 係指該項限用物質為排除項目。\nNote 3: The "－" indicates that the restricted substance corresponds to the exemption.'
for v in notes.splitlines():
    N.add(paragraph(v))

# Native signal words and pictograms.
chapter(4, 1, "symbols")
N.take(4, [24, 53, 330, 175], purpose="structured-signal-table", unused=True)
signals = [
    ("警告", "可能導致嚴重傷害、死亡和/或財產損失的危險行為。"),
    ("注意", "可能導致人身傷害和/或財產損失的危險行為。"),
    ("說明", "可能導致裝置損壞、資料遺失、性能下降或意外結果的危險行為。"),
    ("提示", "補充正文中的重要資訊或操作提示。"),
]
N.add(
    N.comp(
        symbol_signal_component_spec,
        accessibility_label="圖示含義",
        headers=[pair("content", "圖示"), pair("content", "含義")],
        rows=[
            {"label": l, "show_icon": True, **pair("meaning", v)} for l, v in signals
        ],
    )
)
ss = json.loads((SOURCE / "source/symbol_provenance.json").read_text())
panels = []
for start in [0, 3]:
    rows = []
    for idx, s in enumerate(ss[start : start + 3], start):
        meaning = N.t(4, s["caption_bbox"])
        rows.append(
            {"asset_index": idx, "icon_alt": meaning, **pair("meaning", meaning)}
        )
    panels.append(rows)
N.take(4, [24, 180, 334, 203], purpose="symbol-table-headers", unused=True)
N.add(
    N.comp(
        symbol_icon_component_spec,
        accessibility_label="圖示含義",
        headers=[pair("content", "圖示"), pair("content", "含義")] * 2,
        panels=panels,
        icon_refs=[s["asset_ref"] for s in ss],
        icon_locale_policy="exact",
    )
)

# Box and complete overview; no printed cover repetition.
chapter(5, 15, "in_the_box")
N.take(5, [24, 52, 340, 143], purpose="structured-inbox", unused=True)
labels = [
    "Jackery Explorer 1500 Ultra 不斷電式電源供應器（UPS）",
    "AC 充電線",
    "USB-C 線材",
    "說明書",
]
tip = block(5, 13)
N.add(
    N.comp(
        inbox_component_spec,
        accessibility_label="包裝清單",
        cards=[
            {"label": v, "alt": v, "image_ref": "assets/" + k + ".svg"}
            for v, k in zip(
                labels,
                ["inbox-main", "inbox-ac", "inbox-usbc", "inbox-manual"],
                strict=True,
            )
        ],
        tip_label="提示",
        tip_body=tip.removeprefix("提示：").strip(),
    )
)
chapter(5, 16, "product_overview")
h(5, 17)
N.add(fig("overview-front"))

# LCD icon list shares checked assets, with native source numbering.
chapter(6, 0, "lcd_display")
N.add(fig("lcd-map"))
lcd = json.loads((SOURCE / "source/lcd_provenance.json").read_text())
rows = []
for pg in [6, 7]:
    t = N.doc[pg - 1].find_tables().tables[0]
    for r in t.extract():
        number, name, desc = r[0], normalize(r[2]), normalize(r[3])
        i = len(rows)
        rows.append(
            {
                "asset_index": i,
                "icon_alt": name,
                **pair("number", number),
                **pair("name", name),
                **pair("description", desc),
            }
        )
    N.take(pg, rect(t.bbox), purpose="structured-lcd-table", unused=True)
N.add(
    N.comp(
        lcd_icon_component_spec,
        accessibility_label="顯示螢幕介面",
        rows=rows,
        icon_refs=[r["asset_ref"] for r in lcd],
        icon_locale_policy="exact",
    )
)

# Source-complete operation groups plus CSS caption plates.
chapter(8, 0, "operations")
h(8, 12)
N.add(fig("power"))
h(8, 13)
N.add(fig("ac-output"))
h(9, 2)
N.add(fig("dc-usb"))
h(10, 25)
body(10, [20, 35, 348, 128])
N.add(fig("energy-buttons"))
notice(10, [30, 220, 80, 247], [24, 220, 345, 247], "note")
h(10, 1)
# Six source actions remain editable; shared hybrid component owns artwork/table geometry.
N.take(10, [170, 273, 341, 384], purpose="structured-lcd-mode", unused=True)
groups = [
    {
        **pair("state", "螢幕顯示"),
        "actions": [
            {**pair("action", a), **pair("description", b)}
            for a, b in [
                ("開啟", "按電源鍵，或在產品充電時自動點亮。"),
                ("關閉", "按電源鍵。"),
                ("自動熄螢幕", "無操作 2 分鐘後，螢幕自動熄滅並進入休眠模式。"),
            ]
        ],
    },
    {
        **pair("state", "常亮顯示模式（充電或放電狀態下）"),
        "actions": [
            {**pair("action", a), **pair("description", b)}
            for a, b in [
                ("開啟", "螢幕點亮時，雙擊電源鍵。"),
                ("關閉", "按電源鍵。"),
                (
                    "自動熄螢幕",
                    "產品在未充電、未放電，且 DC 12V 連接埠與 USB 連接埠總輸出低於 3W 達 2 小時後，常亮顯示模式自動關閉。",
                ),
            ]
        ],
    },
]
N.add(
    N.comp(
        lcd_mode_component_spec,
        accessibility_label="螢幕顯示",
        groups=groups,
        artwork_ref="assets/lcd-button.svg",
        artwork_locale_policy="exact",
    )
)
h(10, 17)
N.take(10, [24, 402, 345, 498], purpose="structured-key-combinations", unused=True)


def key(name, label):
    return bounded_group(
        [node("image", source="assets/key-" + name + ".png", alt=""), paragraph(label)],
        "hb-key-button",
    )


pairkeys = bounded_group(
    [
        key("power", "電源鍵"),
        node("inline_group", [text("＋")], presentation=attrs("hb-key-button-plus")),
        key("ac", "AC 輸出按鍵"),
    ],
    "hb-key-button-pair",
)
duration = node(
    "inline_group",
    [text("3 秒")],
    presentation={
        "html": {
            "attributes": {"class": "hb-key-duration", "data-duration-icon": "clock"}
        }
    },
)
keys = table(
    [
        [cell(v, header=True) for v in ["按鍵", "操作", "功能"]],
        [
            node("table_cell", [pairkeys], header=False),
            node("table_cell", [duration, paragraph("同時長按 3 秒")], header=False),
            cell("開啟/關閉節能模式"),
        ],
        [
            node("table_cell", [key("power", "電源鍵")], header=False),
            cell("長按 3 秒關閉產品後，繼續長按 10 秒"),
            cell("重設本產品"),
        ],
    ]
)
keys["presentation"] = attrs("hb-key-combination-table")
N.add(bounded_group([keys], "hb-key-combination-composition"))

chapter(11, 1, "ups")
body(11, [20, 50, 345, 120])
N.add(fig("ups"))
notice(11, [25, 280, 55, 315], [55, 260, 344, 335], "caution")
chapter(11, 10, "charging")
body(11, [20, 362, 345, 403])
N.add(paragraph(block(11, 16)))
notice(11, [29, 432, 58, 466], [65, 420, 343, 478], "note")
h(12, 3)
body(12, [20, 37, 345, 58])
N.add(fig("ac-charge"))
notice(12, [30, 170, 61, 201], [72, 167, 344, 201], "caution")
h(12, 6)
body(12, [20, 213, 345, 234])
N.add(fig("solar-direct"))
body(12, [20, 339, 345, 370])
N.add(fig("solar-connectors"))
N.add(fig("solar-incorrect"))
notice(13, [34, 139, 65, 171], [74, 138, 344, 170], "caution")
notice(13, [34, 185, 65, 218], [78, 169, 344, 234], "caution")
body(13, [20, 230, 345, 263])
h(13, 10)
body(13, [20, 277, 345, 310])
N.add(fig("car-charge"))
notice(13, [33, 447, 65, 481], [75, 431, 344, 499], "caution")

chapter(14, 1, "bottom_cleaning")
N.add(fig("bottom-cleaning"))
for i in [12, 13]:
    N.b(14, i, purpose="fixed-art-marking")
chapter(15, 2, "storage")
body(15, [20, 48, 345, 136])
chapter(15, 3, "troubleshooting")
body(15, [20, 168, 345, 191])
t = N.doc[14].find_tables().tables[0]
N.take(15, rect(t.bbox), purpose="structured-troubleshooting", unused=True)
rows = [[normalize(v or "") for v in r] for r in t.extract()[1:]]
rows[7][1] = (
    rows[7][1].replace("（V ）。 oc", "（Voc）。").replace("（V ）。oc", "（Voc）。")
)
N.add(
    N.comp(
        troubleshooting_component_spec,
        headers=[pair("content", "故障代碼"), pair("content", "處理方法")],
        rows=[{**pair("code", a), **pair("measures", b)} for a, b in rows],
    )
)

chapter(16, 9, "specifications")
for i, t in enumerate(N.doc[15].find_tables().tables):
    title = block(16, [10, 36, 25, 41][i])
    rows = [[normalize(v or "") for v in r] for r in t.extract()]
    N.take(16, rect(t.bbox), purpose="structured-specifications", unused=True)
    N.add(N.comp(spec_table_component_spec, section_title=title, rows=rows))
body(16, [20, 434, 345, 477])

chapter(17, 4, "warranty")
lead = N.t(17, [25, 50, 344, 79])
note = block(17, 3)
N.add(
    N.comp(
        warranty_lead_component_spec,
        accessibility_label="保固",
        lead_html=html.escape(lead),
        local_note_html=html.escape(note),
    )
)
for index, hi, bbox in [
    (1, 13, [28, 112, 344, 168]),
    (3, 14, [28, 282, 344, 318]),
    (4, 16, [28, 338, 344, 361]),
    (5, 23, [28, 378, 344, 457]),
    (6, 24, [28, 471, 344, 500]),
]:
    if index == 3:
        title = block(17, 25)
        N.take(
            17, [25, 171, 335, 251], purpose="structured-warranty-years", unused=True
        )
        periods = []
        for number, label, b in [
            ("3", "標準保固", [28, 210, 190, 265]),
            ("2", "延長保固", [213, 214, 335, 252]),
        ]:
            value = N.t(17, b)
            periods.append(
                {"number": number, "unit": "年", "label": label, **pair("body", value)}
            )
        N.add(
            bounded_group(
                [
                    node(
                        "heading", [text(title)], level=3, presentation=attrs("rubric")
                    ),
                    N.comp(warranty_years_component_spec, title=title, periods=periods),
                ],
                "hb-source-warranty",
            )
        )
    title = block(17, hi)
    raw = N.take(17, bbox, unused=True, reading_order="vertical")[1]
    nodes = prose(raw)
    blocks = []
    for v in nodes:
        vhtml = flow_nodes_to_html([root(v)])
        if v["kind"] == "list":
            blocks.append(
                {
                    "kind": "list",
                    "html": vhtml,
                    "items": [
                        normalize("".join(c.get("text", "") for c in item["children"]))
                        for item in v["children"]
                    ],
                }
            )
        else:
            blocks.append(
                {
                    "kind": "paragraph",
                    "html": vhtml,
                    "text": normalize(raw)
                    if len(nodes) == 1
                    else "".join(c.get("text", "") for c in v["children"]),
                }
            )
    N.add(
        bounded_group(
            [
                node("heading", [text(title)], level=3, presentation=attrs("rubric")),
                N.comp(
                    warranty_section_component_spec,
                    title=title,
                    section_index=index,
                    blocks=blocks,
                ),
            ],
            "hb-source-warranty",
        )
    )

chapter(18, 8, "app_setup")
h(18, 5)
copy = N.t(18, [37, 119, 344, 153])
N.add(
    N.comp(
        app_download_component_spec,
        accessibility_label="下載 App",
        columns=[
            {"role": "store", "html": html.escape(copy), "text": copy},
            {"role": "qr", "html": "QR Code", "text": "QR Code"},
        ],
        source_art_ref="assets/app-download.svg",
        store_art_ref="assets/app-store.svg",
        qr_art_ref="assets/app-qr.png",
    )
)
h(18, 2)
# The plus control is a source vector rather than extractable text.
a = block(18, 6)
before, after = a.split("點選", 1)
spec = app_inline_control_component_spec(
    accessibility_label="+",
    paragraph_html=f"<p>{html.escape(before)}點選 <strong>+</strong> {html.escape(after)}</p>",
    paragraph_text=f"{before}點選 + {after}",
    source_ref="native-pdf/page-18#add-button",
    language=N.language,
    metadata={"visual_recovery": "native-pdf-vector-plus-control"},
)
carrier = node(
    "paragraph",
    [text(before + "點選 "), node("strong", [text("+")]), text(" " + after)],
)
N.add(component_flow_node(spec, carrier_flow=(carrier,), root=True))
body(18, [34, 176, 344, 212])
N.add(fig("app-add"))
N.add(fig("app-network"))
notice(18, [43, 460, 75, 490], [85, 460, 336, 491], "caution")
N.add(paragraph(block(19, 4)))
notice(19, [43, 44, 75, 79], [88, 39, 343, 80], "note")
N.add(paragraph(block(19, 16)))
notice(19, [43, 88, 75, 119], [88, 92, 343, 120], "note")
N.add(paragraph(block(19, 17)))
N.add(fig("app-result"))
N.b(19, 2, purpose="fixed-screenshot-marking")
N.b(19, 3, purpose="fixed-screenshot-marking")
N.add(paragraph(block(19, 18)))
notice(19, [43, 317, 75, 351], [88, 311, 343, 356], "caution")
h(19, 7)
body(19, [30, 365, 345, 398])
h(19, 10)
for hi, bb in [
    (11, [32, 413, 344, 438]),
    (13, [32, 438, 344, 453]),
    (15, [32, 462, 344, 499]),
]:
    h(19, hi)
    body(19, bb)
N.chapter("reporting", block(20, 0))
body(20, [20, 433, 302, 505])
N.add(N.figure("reporting-qr"))

# PUA digits are a font-encoding recovery, with native page/span evidence.
recoveries = []
for pg in range(1, 21):
    for span in N.spans(pg):
        for char in sorted(set(span["text"])):
            if "\uf6be" <= char <= "\uf6c7":
                recoveries.append(
                    {
                        "physical_page": pg,
                        "font": span["font"],
                        "bbox": span["bbox"],
                        "raw": span["text"],
                        "glyph": f"U+{ord(char):04X}",
                        "recovered": str(ord(char) - 0xF6BE),
                        "method": "native visible glyph; corroborated p5 interface labels, p10 duration, p17 warranty and p18 step headings",
                    }
                )
dump(SOURCE / "source/glyph_recoveries.json", recoveries)
dump(
    SOURCE / "source/source_anomalies.json",
    [
        {
            "physical_page": 14,
            "text": "妥產品所有防護蓋，避免清洗過程中進水。",
            "policy": "preserved verbatim; the odd initial wording is visible in the authoritative PDF, not silently corrected",
        },
        {
            "physical_page": 3,
            "symbols": ["○", "－"],
            "policy": "recovered from native vector objects and rendered restricted-substances table; PDF text cells are empty",
        },
    ],
)
dump(SOURCE / "source/figure_labels.json", LABEL_LOG)
missing = N.finish()
(SOURCE / "source/label_geometry.css").write_text("\n".join(CSS) + "\n")
print(
    "chapters",
    len(N.chapters),
    "figure labels",
    len(LABEL_LOG),
    "unmapped",
    len(missing),
)
print(json.dumps(missing, ensure_ascii=False, indent=2))
