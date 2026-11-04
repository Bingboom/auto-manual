"""Bind the reviewed JE-76A JP transcription to shared Web components.

Run from the repository root:

    python manual_sources/JE-76A/JP/ja/git-20261103-d8f7d338/build_content.py

Every Web string comes from ``source/transcription.json`` by line id; this
module only decides which shared component carries each printed block, in
printed order. It writes ``source/ja/content.json``, the frozen input that
``rebuild.py`` replays. ``source_manifest.json:component_map`` lists the map,
``shared_component_exceptions`` the declared plain tables and
``source/differences.md`` every deliberate layout difference.
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
from tools.component_specs.spec_table import spec_table_component_spec  # noqa: E402
from tools.manual_ir.components import component_flow_node  # noqa: E402
from tools.web.composite_hashing import reference_source_fragment_sha256  # noqa: E402
from tools.web.frozen_ai_flow import callout, node, root, table, text  # noqa: E402
from tools.web.frozen_ai_table_components import _spec_carrier  # noqa: E402

LANGUAGE = "ja"
SOURCE_SHA256 = "d8f7d338fd208af056c0dda9991422227627ab771245e791858e1480978b013c"


class Lines:
    """Line lookup that records every id used, so coverage can be checked."""

    def __init__(self) -> None:
        source = json.loads((PACKAGE / "source/transcription.json").read_text(encoding="utf-8"))
        if source["source_sha256"] != SOURCE_SHA256:
            raise ValueError("transcription is bound to another source")
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


def strong_para(key: str) -> dict:
    return root(node("paragraph", [node("strong", [text(T(key))])]))


def heading(key: str, level: int = 3, anchor: str | None = None) -> dict:
    return root(node("heading", [text(T(key))], level=level, **({"anchor": anchor} if anchor else {})))


def chapter_heading(key: str, anchor: str) -> dict:
    # The print letter-spaces some chapter titles; the characters are unchanged.
    return heading(key, level=2, anchor=anchor)


def bullets(keys: list[str]) -> dict:
    return root(node("list", [node("list_item", [node("paragraph", T.inline(k))]) for k in keys], ordered=False))


def fragment_sha256(ref: str, reference_id: str, alt: str) -> str:
    """The shared renderer's source-fragment hash of a captionless semantic image."""
    soup = BeautifulSoup("", "html.parser")
    semantic = soup.new_tag("div", attrs={"class": "hb-reference-semantic",
                                          "data-reference-id": f"{reference_id}.semantic"})
    semantic.append(soup.new_tag("img", attrs={"alt": alt, "class": "hb-reference-art", "src": ref}))
    return reference_source_fragment_sha256(
        component={"id": reference_id, "image_key": reference_id, "captions_embedded": True},
        semantic=semantic, caption_labels=[], composite_locale=None)


def figure(ref: str, reference_id: str, page: int, alt: str, labels: tuple[str, ...] = ()) -> dict:
    """Complete source panel; printed leader letters stay in the art."""
    spec = reference_figure_component_spec(
        reference_id=reference_id, accessibility_label=alt, caption_mode="embedded",
        captions=(), adjacent_copy=None, source_art_ref=ref, source_art_locale_policy="exact",
        source_fragment_sha256=fragment_sha256(ref, reference_id, alt),
        source_ref=f"native-pdf/page-{page}/{reference_id}", language=LANGUAGE, image_key=reference_id,
        metadata={"embedded_labels": list(labels), "physical_page": page},
    )
    return component_flow_node(spec, carrier_flow=(root(node("image", source=ref, alt=alt)),), root=True)


def label(key: str) -> str:
    """Printed text reused as alt text without binding the line a second time."""
    return T.rows[key]["text"]


def cell(key: str, header: bool = False, rows: int = 1) -> dict:
    extra = {"row_span": rows} if rows > 1 else {}
    return node("table_cell", [text(T(key))], header=header, **extra)


def plain_table(header: list[dict] | None, rows: list[list[dict]]) -> dict:
    """Declared plain table on the shared manual-table classes (shared_component_exceptions)."""
    parts = [node("table_head", [node("table_row", header)])] if header else []
    parts.append(node("table_body", [node("table_row", row) for row in rows]))
    return root(node("group", [node("table", parts, presentation={"html": {"attributes": {"class": "manual-table"}}})],
                     role="container",
                     presentation={"html": {"attributes": {"class": "table-wrapper docutils container"}}}))


def safety_item(variant: str, band: str, title_key: str, body_keys: list[str], ref: str,
                list_keys: list[str] | None = None, tail: tuple[str, list[str]] | None = None) -> dict:
    body = [node("paragraph", [node("strong", [text(T(title_key))])])]
    if list_keys:
        body.append(node("list", [node("list_item", [text(T(k))]) for k in list_keys], ordered=False))
    body += [node("paragraph", [text(T(k))]) for k in body_keys]
    if tail:
        body.append(node("paragraph", [node("strong", [text(T(tail[0]))])]))
        body += [node("paragraph", [text(T(k))]) for k in tail[1]]
    return root(callout(band, body, variant=variant, language=LANGUAGE, source_ref=ref))


# --- chapters -------------------------------------------------------------

def specifications() -> list[dict]:
    title = T("spec.h")
    rows: list[tuple[str, str]] = []
    for index in range(1, 22):
        label_text = T(f"spec.r{index}.l")
        values = [T(k) for k in sorted((k for k in T.rows if k.startswith(f"spec.r{index}.v")),
                                       key=lambda k: int(k.rsplit("v", 1)[1]))]
        rows.append((label_text, "\n".join(values)))
    spec = spec_table_component_spec(section_title=title, rows=rows, source_ref="native-pdf/page-2/spec",
                                     language=LANGUAGE)
    # The chapter title 「1.主な仕様」 is the shared spec section heading (h2).
    return [component_flow_node(spec, carrier_flow=_spec_carrier(title, rows), root=True),
            para("spec.cond"),
            para("cert.l"),
            figure("assets/certifications.png", "certifications", 3, label("cert.l").rstrip("：")),
            para("spec.tm")]


def in_the_box() -> list[dict]:
    refs = ("assets/inbox-unit.png", "assets/inbox-cable.png", "assets/inbox-manual.png", "assets/inbox-warranty.png")
    cards = [{"image_ref": ref, "label": T(f"box.c{i}"), "alt": label(f"box.c{i}")}
             for i, ref in enumerate(refs, 1)]
    spec = inbox_component_spec(accessibility_label=label("box.h"), cards=cards, tip_label="", tip_body="",
                                source_ref="native-pdf/page-3/inbox", language=LANGUAGE, require_tip=False)
    carrier = table([[node("table_cell", [node("image", source=c["image_ref"], alt=c["alt"]),
                                          node("paragraph", [text(c["label"])])], header=False) for c in cards]])
    recycle = plain_table(None, [[
        node("table_cell", [node("image", source="assets/recycle-li-ion.svg", alt=T("recycle.glyph"))], header=False),
        node("table_cell", [node("paragraph", [node("strong", [text(T("recycle.title"))])]),
                            *(node("paragraph", [text(T(k))]) for k in ("recycle.b1", "recycle.b2", "recycle.b3"))],
             header=False),
    ]])
    return [chapter_heading("box.h", "native-in-the-box"),
            component_flow_node(spec, carrier_flow=(carrier,), root=True),
            para("box.n1"), strong_para("spec.change"), recycle]


def product() -> list[dict]:
    keys = ["parts.a", "parts.b", "parts.c", "parts.d"]
    return [chapter_heading("parts.h", "native-product"),
            heading("parts.title"),
            figure("assets/overview.png", "overview", 4, label("parts.title"), labels=tuple("ABCDEFG")),
            *(para(k) for k in keys),
            para("parts.e"), *(para(f"parts.e{i}") for i in range(1, 6)),
            para("parts.f"), para("parts.g")]


def lcd() -> list[dict]:
    pct_name, pct_body = T("lcd.pct.t"), T("lcd.pct.b")
    charge = T("lcd.chg.t")
    charge_name, charge_rest = charge.split("（", 1)
    charge_body = "（" + charge_rest
    rows = [
        {"name_html": escape(pct_name), "name_text": pct_name, "description_html": escape(pct_body),
         "description_text": pct_body, "icon_alt": pct_name, "asset_index": 0},
        {"name_html": escape(charge_name), "name_text": charge_name, "description_html": escape(charge_body),
         "description_text": charge_body, "icon_alt": charge_name, "asset_index": 1},
    ]
    icons = lcd_icon_component_spec(accessibility_label=label("lcd.h"), rows=rows,
                                    icon_refs=["assets/lcd-percent.svg", "assets/lcd-charging.svg"],
                                    source_ref="native-pdf/page-5/lcd-icons", language=LANGUAGE,
                                    icon_locale_policy="exact", numbered=False)
    on_head = [cell("on.th1", True), cell("on.th2", True), cell("on.th3", True)]
    on_rows = [[cell("on.s1", rows=2), cell("on.r1.a"), cell("on.r1.b")],
               [cell("on.r2.a"), cell("on.r2.b")],
               [cell("on.s2", rows=3), cell("on.r3.a"), cell("on.r3.b")],
               [cell("on.r4.a"), cell("on.r4.b")],
               [cell("on.r5.a"), cell("on.r5.b")]]
    off_head = [cell("off.th1", True), cell("off.th2", True), cell("off.th3", True)]
    off_rows = [[cell("off.s1", rows=3), cell("off.r1.a"), cell("off.r1.b")],
                [cell("off.r2.a"), cell("off.r2.b")],
                [cell("off.r3.a"), cell("off.r3.b")]]
    return [chapter_heading("lcd.h", "native-lcd-display"),
            figure("assets/lcd-map.png", "lcd-map", 5, label("lcd.h")),
            component_flow_node(icons, root=True),
            heading("on.h"), plain_table(on_head, on_rows),
            heading("off.h"), plain_table(off_head, off_rows)]


def charging() -> list[dict]:
    return [chapter_heading("chg.h", "native-charging"),
            heading("chg.st.h"), para("chg.st"),
            figure("assets/charging-station.png", "charging-station", 6, label("chg.st.h")),
            heading("chg.note.h"), bullets(["chg.note1", "chg.note2"]),
            heading("chg.usb.h"), para("chg.usb"),
            figure("assets/charging-usb-c.png", "charging-usb-c", 7, label("chg.usb.h"))]


def temperature() -> list[dict]:
    return [chapter_heading("temp.h", "native-temperature-protection"),
            para("temp.p1"), para("temp.p2"), para("temp.ff"),
            figure("assets/lcd-ff.png", "lcd-ff", 8, "FF")]


def error_codes() -> list[dict]:
    head = [cell(f"err.th{i}", True) for i in (1, 2, 3)]
    rows = []
    for index in range(1, 8):
        description = [k for k in (f"err.r{index}.d", f"err.r{index}.d1", f"err.r{index}.d2") if k in T.rows]
        rows.append([cell(f"err.r{index}.c"), cell(f"err.r{index}.n"),
                     node("table_cell", [node("paragraph", [text(T(k))]) for k in description], header=False)])
    return [chapter_heading("err.h", "native-error-codes"), plain_table(head, rows)]


def safety() -> list[dict]:
    w, c = "warning", "caution"
    w1, w2, c1 = T("w1.band"), T("w2.band"), T("c1.band")
    return [
        safety_item(w, w1, "w1.i1.t", ["w1.i1.b1", "w1.i1.b2"], "native-pdf/page-9/warning-1",
                    list_keys=[f"w1.i1.l{i}" for i in range(1, 6)], tail=("w1.i1.t2", ["w1.i1.b3", "w1.i1.b4"])),
        safety_item(w, w1, "w1.i2.t", ["w1.i2.b"], "native-pdf/page-9/warning-2"),
        safety_item(w, w1, "w1.i3.t", ["w1.i3.b"], "native-pdf/page-9/warning-3"),
        safety_item(w, w1, "w1.i4.t", [], "native-pdf/page-9/warning-4"),
        *(safety_item(w, w2, f"w2.i{i}.t", [f"w2.i{i}.b"], f"native-pdf/page-10/warning-{i}") for i in range(1, 8)),
        safety_item(c, c1, "c1.i1.t", ["c1.i1.b"], "native-pdf/page-11/caution-1"),
        safety_item(c, c1, "c1.i2.t", [], "native-pdf/page-11/caution-2",
                    list_keys=["c1.i2.l1", "c1.i2.l2", "c1.i2.l3"]),
        safety_item(c, c1, "c1.i3.t", ["c1.i3.b"], "native-pdf/page-11/caution-3"),
    ]


def disclaimer() -> list[dict]:
    def item(*keys: str) -> dict:
        return node("list_item", [node("paragraph", [text(T(k))]) for k in keys])
    items = [item("disc.l1"), item("disc.l2a", "disc.l2b"), item("disc.l3"), item("disc.l4"), item("disc.l5"),
             item("disc.l6a", "disc.l6b")]
    return [chapter_heading("disc.h", "native-disclaimer"), root(node("list", items, ordered=False))]


def precautions() -> list[dict]:
    def item(*keys: str) -> dict:
        return node("list_item", [node("paragraph", [text(T(k))]) for k in keys])
    items = [item(f"prec.l{i}") for i in range(1, 8)]
    items.append(item("prec.l8.t", *(f"prec.l8.b{i}" for i in range(1, 7))))
    items.append(item("prec.l9", *(f"prec.l9.b{i}" for i in range(1, 7))))
    return [chapter_heading("prec.h", "native-usage-precautions"), root(node("list", items, ordered=False))]


CHAPTERS = (
    ("specifications", "1.主な仕様", specifications), ("in_the_box", "2.同梱品", in_the_box),
    ("product", "3.使用製品", product), ("lcd_display", "4.LCD表示画面", lcd),
    ("charging", "5.充電の方法", charging), ("temperature_protection", "6.温度保護機能", temperature),
    ("error_codes", "7.エラーコード", error_codes), ("safety", "警告・注意", safety),
    ("disclaimer", "8.免責事項", disclaimer), ("usage_precautions", "9.使用上のご注意", precautions),
)


def build() -> dict:
    chapters = [{"id": cid, "title": title, "nodes": make()} for cid, title, make in CHAPTERS]
    missing = [k for k in T.rows if k not in T.used]
    if missing:
        raise ValueError("Web transcription lines not bound: " + ", ".join(missing))
    return {"model": "JE-76A", "region": "JP", "language": LANGUAGE,
            "title": "Jackery Power Bank 取扱説明書", "source_sha256": SOURCE_SHA256, "chapters": chapters}


def main() -> None:
    content = build()
    path = PACKAGE / "source/ja/content.json"
    path.write_text(json.dumps(content, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"chapters": [c["id"] for c in content["chapters"]], "lines": len(T.used)}))


if __name__ == "__main__":
    main()
