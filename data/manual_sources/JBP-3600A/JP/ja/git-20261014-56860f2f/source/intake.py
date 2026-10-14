"""Generate the JBP-3600A JP Japanese semantic document from the archived production sheet.

Run from the repository root: ``python3 data/manual_sources/JBP-3600A/JP/ja/git-20261014-56860f2f/source/intake.py``.
It writes ``source/ja/content.json`` and ``source/ja/coverage.json`` and fails
while any word on the sheet is unclassified. Regions are reviewed panel-local
PDF point rectangles (panel 3 = printed page 01); components are the shared
ones the other frozen manuals use.
"""
from copy import deepcopy
from pathlib import Path
import sys

REPO = next(p for p in Path(__file__).resolve().parents if (p / "build.py").is_file())
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from native import LANGUAGE, SHEET, Native, SOURCE, attrs, dump  # noqa: E402
from tools.component_specs.callout import display_label  # noqa: E402
from tools.component_specs.inbox import inbox_component_spec  # noqa: E402
from tools.component_specs.warranty import warranty_section_component_spec  # noqa: E402
from tools.manual_ir.flow import flow_nodes_to_html  # noqa: E402
from tools.web.frozen_ai_flow import callout as shared_callout  # noqa: E402
from tools.web.frozen_ai_flow import node, root, text  # noqa: E402
from tools.web.frozen_ai_table_components import troubleshooting_flow  # noqa: E402

FULL = 337.2  # right edge of the print's full-width text frame
TRIANGLE = "assets/signal-triangle.svg"

# Production metadata on the sheet, outside the twelve panels (page 0, sheet points).
SHEET_REGIONS = [
    ("frame-grid", "Drawing-frame zone letters A-P and numbers 1-11 on the sheet border.",
     [[-30, -30, 3750, 60], [-30, 2500, 3750, 2640], [-30, -30, 120, 2640], [3600, -30, 3750, 2640]]),
    ("revision-table", "Revision table: 版次 V0.1 第一次发行 and its empty sign-off columns.",
     [[2390, 60, 3660, 260]]),
    ("title-block", "Title block: 产品名称 HTP0113600A, 语言/国家 JP, 产品料号 16-0102-000060, 版本 V0.1, "
     "页数 01, drafter, date 2025-12-8 and packaging tolerances.", [[1900, 2150, 3660, 2500]]),
    ("production-notes", "Production notes: part title and RoHS/REACH, 成品尺寸 130*185mm, 80g书纸 正反面印刷, "
     "90%黑, 装订方式 折页.", [[200, 2050, 1700, 2420]]),
]
EXCLUDED_PANELS = [
    (1, "printed-cover", "Printed cover: model badge, product image, title, support pill and the four "
     "お買い上げ notes. Operator: 「封面和目录 不用体现在web版面上」."),
    (2, "contents", "Printed contents 01-10; the Web navigation carries the chapters."),
]


def classify_sheet(n):
    for panel, purpose, _ in EXCLUDED_PANELS:
        n.take(panel, [-1, -1, 370, 526], purpose=purpose)
    for purpose, _, boxes in SHEET_REGIONS:
        for box in boxes:
            n.take(SHEET, box, purpose="production-metadata/" + purpose)


def callout(n, label, body, *, variant, lockup=False):
    """Shared callout strip; optional warning lockup with the print's filled triangle."""
    item = shared_callout(display_label(label), body, variant=variant, language=LANGUAGE,
                          source_ref=f"native-pdf/{n.current['id']}/{variant}-{len(n.selections)}")
    carrier = item["carrier_flow"][0]
    classes = carrier["presentation"]["html"]["attributes"]["class"] + " hb-callout-label-shaded"
    if lockup:
        classes += " hb-source-warning-lockup"
        label_cell = carrier["children"][0]["children"][0]["children"][0]
        label_cell["children"] = [node("inline_group", [
            node("image", source=TRIANGLE, alt=""), text(display_label(label))],
            presentation=attrs("hb-warning-lockup"))]
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


def panel(children, css):
    return node("group", children, role="container", presentation=attrs(css))


def inline(flow):
    """The inline children of a one-paragraph prose selection."""
    if len(flow) != 1 or flow[0]["kind"] != "paragraph":
        raise ValueError("expected one printed paragraph")
    return flow[0]["children"]


def subscript(children, word, digits):
    """LiFePO4: the print sets the 4 as a 4 pt subscript."""
    for i, child in enumerate(children):
        if child["kind"] == "text" and word + digits in child["text"]:
            before, after = child["text"].split(word + digits, 1)
            children[i:i + 1] = [text(before + word), node("subscript", [text(digits)]), text(after)]
            return children
    raise ValueError("subscript marker not found")


def insert_glyph(flow, marker, image):
    """Place a source inline glyph where the print leaves its gap after marker (CSS spaces it)."""
    def visit(children):
        for i, child in enumerate(children):
            if child["kind"] == "text" and marker in child["text"]:
                before, after = child["text"].split(marker, 1)
                children[i:i + 1] = [text(before + marker), image, text(after.lstrip())]
                return True
            if child.get("children") and visit(child["children"]):
                return True
        return False
    for block in flow:
        if visit([block]):
            return flow
    raise ValueError(f"inline glyph marker not found: {marker!r}")


def plain(block):
    if block["kind"] == "text":
        return block["text"]
    if block["kind"] == "line_break":
        return "\n"
    return "".join(plain(child) for child in block.get("children", []))


def markup(block):
    return flow_nodes_to_html([root(deepcopy(block))])


def warranty_blocks(flow):
    blocks = []
    for block in flow:
        if block["kind"] == "list":
            blocks.append({"kind": "list", "html": markup(block),
                           "items": [plain(item) for item in block["children"]]})
        else:
            blocks.append({"kind": "paragraph", "text": plain(block), "html": markup(block)})
    return blocks


def make():
    n = Native()

    # ---- 01-02 安全上のご注意 -------------------------------------------------------
    n.chapter("safety", 3, [30, 25, 345, 50])
    n.add(*n.prose(3, [25, 55, 345, 70], right=FULL))                 # bold lead line
    n.add(*n.prose(3, [25, 70, 345, 270], right=FULL))
    n.h(3, [30, 275, 345, 292])                                        # 絵表示について
    n.add(*n.prose(3, [25, 292, 345, 325], right=331.0))
    bounds = [334, 360, 386, 412, 439.5]
    rows = []
    for i, (y0, y1) in enumerate(zip(bounds[:-1], bounds[1:], strict=True)):
        label = n.t(3, [36, y0, 98, y1])
        children = [node("strong", [text(label)])]
        if i < 2:  # 警告 and 注意 carry the filled triangle
            children.insert(0, node("image", source=TRIANGLE, alt=""))
        rows.append([cell([node("inline_group", children, presentation=attrs("hb-warning-lockup"))],
                          cls="native-signal-label"),
                     cell(inline(n.prose(3, [98, y0, 340, y1], right=333.5)))])
    n.embedded("signal-triangle")
    n.add(grid([], rows, "native-print-grid native-signal native-fit"))
    n.h(4, [30, 25, 345, 46])                                          # 絵表示の説明
    ys = [53.7, 93.6, 130.9, 171.0, 211.1, 253.3, 305.7, 363.5, 440.3]
    slots = ["symbol-warning", "symbol-read-manual", "symbol-no-open-flame", "symbol-children",
             "symbol-do-not-dismantle", "symbol-li-ion", "symbol-weee", "symbol-battery-weee"]
    rows = []
    for slot, y0, y1 in zip(slots, ys[:-1], ys[1:], strict=True):
        n.embedded(slot)  # the Li-ion word is part of its symbol
        meaning = inline(n.prose(4, [70, y0, 345, y1], right=339.5))
        first = plain({"kind": "paragraph", "children": meaning}).split("\n")[0]
        alt = first if "。" not in first else first[:first.index("。") + 1]
        if slot == "symbol-weee":  # its first statement wraps onto the second print line
            alt = plain({"kind": "paragraph", "children": meaning}).split("。")[0] + "。"
        source = n.figures[slot]["local_path"]
        rows.append([cell([node("image", source=source, alt=alt)], cls="native-symbol-cell"), cell(meaning)])
    n.add(grid([], rows, "native-print-grid native-symbols native-fit"))

    # ---- 03 同梱品, 各部の名称 ------------------------------------------------------------
    n.chapter("inbox", 5, [30, 25, 345, 50])
    n.take(5, [30, 65, 340, 88], purpose="component-number/inbox")  # card numbers 1-3
    cards = []
    for slot, box in [("inbox-unit", [30, 186, 130, 206]), ("inbox-cable", [134, 186, 235, 206]),
                      ("inbox-manual", [239, 186, 340, 206])]:
        n.embedded(slot)
        label = n.t(5, box)
        cards.append({"image_ref": n.figures[slot]["local_path"], "alt": label, "label": label})

    def inbox_carrier(spec):
        return [node("table", [node("table_body", [node("table_row", [
            cell([node("image", source=c["image_ref"], alt=c["alt"]), node("paragraph", [text(c["label"])])])
            for c in cards])])], presentation=attrs("manual-table"))]
    n.add(n.comp(inbox_component_spec, inbox_carrier, accessibility_label=n.current["title"],
                 cards=cards, tip_label="", tip_body="", require_tip=False))
    n.add(panel(n.prose(5, [35, 232, 340, 272], right=330.0, lists="none"), "native-note-panel"))
    notice = n.t(5, [36, 282, 345, 302])
    n.add(node("paragraph", [node("strong", [text(n.recovered(5, [29, 285, 40, 300]) + notice)])]))
    n.chapter("overview", 5, [30, 326, 345, 352])
    n.add(n.figure("overview", width="wide"))

    # ---- 04 液晶画面, 製品の使用方法について ------------------------------------------------
    n.chapter("lcd", 6, [30, 25, 345, 50])
    n.add(n.figure("lcd-map", width="wide"))
    rows = []
    for y0, y1 in [(122, 158), (158, 178)]:
        label = inline(n.prose(6, [30, y0, 108, y1], right=105.0, every_line=True))
        rows.append([cell([node("strong", [text(plain(c))]) if c["kind"] != "line_break" else c
                           for c in label], cls="native-key"),
                     cell(inline(n.prose(6, [108, y0, 340, y1], right=334.5)))])
    n.add(grid([], rows, "native-print-grid native-lcd native-fit"))
    n.chapter("usage", 6, [30, 190, 345, 215])
    n.h(6, [38, 215, 345, 230])                                        # オン/オフ
    n.add(n.figure("power-on-off", width="wide"))
    n.add(callout(n, n.t(6, [36, 315, 75, 358]), n.prose(6, [75, 312, 340, 358], right=327.5),
                  variant="note"))
    n.h(6, [38, 365, 345, 382])                                        # LCDディスプレイのオン/オフ
    n.add(n.figure("lcd-control", width="wide"))
    n.add(panel(n.prose(6, [36, 470, 340, 492], right=332.0), "native-note-panel"))

    # ---- 05-06 ポータブル電源との併用 ------------------------------------------------------
    n.chapter("power-station", 7, [30, 25, 345, 50])
    n.add(*n.prose(7, [25, 52, 345, 78], right=330.5))
    n.add(callout(n, n.t(7, [36, 95, 80, 125]), n.prose(7, [80, 85, 340, 138], right=333.5),
                  variant="caution"))
    n.add(n.figure("clearance", width="wide"))
    n.add(n.figure("stacking", width="wide"))
    body = n.prose(8, [66, 30, 340, 90], right=331.5)
    insert_glyph(body, "）に", n.glyph("inline-connected-batteries"))
    n.add(callout(n, n.t(8, [30, 45, 66, 68]), body, variant="caution"))
    n.add(n.figure("locking", width="wide"))

    # ---- 07 充電方法 -------------------------------------------------------------------------
    n.chapter("charging", 9, [30, 25, 345, 46])
    n.h(9, [36, 50, 345, 66])                                          # AC充電
    n.add(*n.prose(9, [25, 66, 345, 78], right=FULL))
    n.add(callout(n, n.t(9, [48, 82, 75, 108]), n.prose(9, [75, 84, 340, 108], right=325.0),
                  variant="warning", lockup=True))
    n.add(n.figure("ac-charging", width="wide"))
    n.add(node("heading", [text(n.t(9, [36, 282, 90, 300]) + n.t(9, [90, 282, 130, 300]))], level=3))
    n.add(*n.prose(9, [25, 300, 345, 322], right=333.5))
    n.add(n.figure("solar-charging", width="wide"))

    # ---- 08 トラブルシューティング, 主な仕様 ---------------------------------------------------
    n.chapter("troubleshooting", 10, [30, 25, 345, 46])
    n.add(*n.prose(10, [25, 52, 345, 72], right=FULL))
    # Shared troubleshooting table (as JBP-2000B / JBP-3600A EU); the print has its header row.
    headings = [n.t(10, [28, 76, 70, 88]), n.t(10, [70, 76, 340, 88])]
    bounds = [88, 99, 110, 121, 132, 143, 160.5, 171.5, 182.5, 194, 205, 216, 227.5, 239.3]
    rows = [{"code": n.t(10, [28, y0, 70, y1]),
             "action": plain(n.prose(10, [70, y0, 340, y1], right=313.0)[0])}  # column text frame
            for y0, y1 in zip(bounds[:-1], bounds[1:], strict=True)]
    n.add(*troubleshooting_flow({"rows": rows}, headings=headings,
                                source_ref="native-pdf/troubleshooting", language=LANGUAGE))
    n.chapter("specifications", 10, [30, 250, 345, 270])
    bounds = [275, 290.7, 305.7, 320.7, 335.7, 350.7, 365.7, 380.7, 395.7, 410.7, 453.3]
    rows = []
    for y0, y1 in zip(bounds[:-1], bounds[1:], strict=True):
        value = inline(n.prose(10, [128, y0, 340, y1], right=338.0, lists="none", every_line=True))
        if any(c["kind"] == "text" and "LiFePO4" in c["text"] for c in value):
            value = subscript(value, "LiFePO", "4")
        rows.append([cell(n.t(10, [28, y0, 128, y1]), cls="native-key"), cell(value)])
    n.add(grid([], rows, "native-print-grid native-spec native-fit"))
    n.add(node("paragraph", [text(n.t(10, [30, 455, 100, 470]) + " " + n.recovered(10, [130, 455, 175, 470]))],
               presentation=attrs("native-certification")))
    n.add(*n.prose(10, [30, 472, 345, 494], right=FULL))

    # ---- 09-10 保証について ----------------------------------------------------------------
    n.chapter("warranty", 11, [30, 25, 345, 50])
    # The print's grey introduction panel holds three lines; the shared warranty lead would
    # split its last line out as a local note, so the panel keeps all three.
    n.add(panel(n.prose(11, [30, 52, 345, 92], right=FULL), "native-note-panel"))
    sections = [
        (11, [36, 95, 100, 110], [30, 110, 345, 165], "all"),       # 保証期間
        (11, [36, 170, 100, 186], [30, 186, 345, 250], "all"),      # 保証の適用範囲
        (11, [36, 254, 100, 268], [30, 268, 345, 312], "all"),      # 保証の適用条件
        (11, [36, 316, 130, 330], [30, 330, 345, 422], "all"),      # 保証対象外となる場合
        (11, [36, 428, 110, 444], [30, 444, 345, 495], "all"),      # 購入証明について
        (12, [36, 26, 80, 44], [30, 44, 345, 218], "bullets"),      # 保証内容
    ]
    # Text frames: the p09 cards run to 340 pt; the p10 card's text frame ends at 320 pt.
    rights = {11: 340.0, 12: 320.0}
    for index, (p, title_box, body_box, lists) in enumerate(sections, 1):
        title = n.t(p, title_box)
        n.add(node("heading", [text(title)], level=3))
        flow = n.prose(p, body_box, right=rights[p], lists=lists)
        n.add(n.comp(warranty_section_component_spec, lambda spec: None, title=title,
                     section_index=index, blocks=warranty_blocks(flow)))
    # 免責事項 is a grey panel with a bold title, not a tagged card, in the print.
    n.h(12, [30, 235, 100, 252])
    n.add(panel(n.prose(12, [30, 252, 345, 337], right=334.0), "native-note-panel"))
    contacts = []
    for slot, box in [("contact-web", [44, 441, 200, 458]), ("contact-mail", [44, 460, 200, 477]),
                      ("contact-phone", [44, 479, 200, 497])]:
        contacts.append(node("paragraph", [n.glyph(slot, css="native-contact-icon"), text(n.t(12, box))]))
    n.add(panel([panel(contacts, "native-contact-lines"), n.figure("contact-qr", width="qr")],
                "native-contact"))

    problems = n.finish(classify_sheet)
    print("chapters", len(n.chapters), "problems", len(problems))
    return problems


if __name__ == "__main__":
    problems = make()
    dump(SOURCE / "source/unmapped.json", deepcopy(problems))
    if problems:
        raise SystemExit("Unmapped or unbalanced native words: see source/unmapped.json")
