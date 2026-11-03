"""Bind the frozen JE-1800B JP text layer to shared Web components.

Run from the repository root after ``extract_text.py``:

    python manual_sources/JE-1800B/JP/ja/git-20261103-754e8c1d-v2/build_content.py

Every Web string comes from ``source/transcription.json`` by line id; this
module only decides which shared component carries each printed block, in
printed order. Print line wraps are joined without inserting characters and
leading/trailing layout spaces are dropped. Printed list markers (•, ◦) and the
■ of bold sub-headings become list/heading markup; every other character is
kept. Each line of a Web page is accounted for exactly once in
``source/line_dispositions.json`` (bound copy, embedded artwork caption,
component number, or printed page number). Writes ``source/ja/content.json``.
"""
from __future__ import annotations

from html import escape
import json
from pathlib import Path
import re
import sys

from bs4 import BeautifulSoup

PACKAGE = Path(__file__).resolve().parent
ROOT = next(parent for parent in PACKAGE.parents if (parent / "build.py").is_file())
sys.path.insert(0, str(ROOT))

from tools.component_specs.app import app_download_component_spec, app_inline_control_component_spec  # noqa: E402
from tools.component_specs.inbox import inbox_component_spec  # noqa: E402
from tools.component_specs.key_combinations import key_combinations_component_spec  # noqa: E402
from tools.component_specs.lcd_mode import lcd_mode_component_spec  # noqa: E402
from tools.component_specs.manual_tables import (  # noqa: E402
    lcd_icon_component_spec, symbol_icon_component_spec, symbol_signal_component_spec,
    troubleshooting_component_spec,
)
from tools.component_specs.reference_figure import reference_figure_component_spec  # noqa: E402
from tools.component_specs.spec_table import spec_table_component_spec  # noqa: E402
from tools.component_specs.warranty import warranty_section_component_spec  # noqa: E402
from tools.manual_ir.components import component_flow_node  # noqa: E402
from tools.web.composite_hashing import reference_source_fragment_sha256  # noqa: E402
from tools.web.frozen_ai_flow import callout, node, root, table, text  # noqa: E402
from tools.web.frozen_ai_table_components import _spec_carrier  # noqa: E402

LANGUAGE = "ja"
SOURCE_SHA256 = "754e8c1d076b7d5fd9d84ac76ce9447dccec4a9351c7b7d756a3225255b4da52"
LCD = "assets/shared-lcd/"
ENERGY_ICON = LCD + "22_Energy_Saving_Mode_FdBWbTvwwosJ7TxfeVIc2Flinkh.png"
MARKERS = ("• ", "•", "◦ ", "◦", "■ ", "■")


class Lines:
    """Line lookup by id/block/range that records the disposition of every line."""

    def __init__(self) -> None:
        source = json.loads((PACKAGE / "source/transcription.json").read_text(encoding="utf-8"))
        if source["source_sha256"] != SOURCE_SHA256:
            raise ValueError("transcription is not bound to the authoritative PDF")
        self.rows = {line["id"]: line for page in source["pages"] if page["web"] for line in page["lines"]}
        self.order = list(self.rows)
        self.disposition: dict[str, str] = {}
        self.context = ""

    def ids(self, ref: str) -> list[str]:
        if ".." in ref:
            stem, last = ref.split("..")
            block, first = stem.rsplit("-l", 1)
            return [f"{block}-l{i}" for i in range(int(first), int(last) + 1)]
        if "-l" in ref:
            return [ref]
        found = [key for key in self.order if key.startswith(ref + "-l")]
        if not found:
            raise KeyError(ref)
        return found

    def take(self, refs: tuple[str, ...], disposition: str | None = None) -> list[dict]:
        rows = []
        for ref in refs:
            for key in self.ids(ref):
                if key in self.disposition:
                    raise ValueError("source line bound twice: " + key)
                self.disposition[key] = disposition or "bound:" + self.context
                rows.append(self.rows[key])
        return rows

    def __call__(self, *refs: str) -> str:
        return "".join(row["text"].strip() for row in self.take(refs))

    def peek(self, *refs: str) -> str:
        return "".join(self.rows[key]["text"].strip() for ref in refs for key in self.ids(ref))

    def item(self, *refs: str) -> str:
        """A printed bullet line: the list marker becomes list markup."""
        value = self(*refs)
        for marker in MARKERS:
            if value.startswith(marker):
                return value[len(marker):].strip()
        return value

    def inline(self, *refs: str) -> list[dict]:
        """Text children with printed bold spans as strong nodes."""
        children: list[dict] = []
        for row in self.take(refs):
            value = row["text"].strip()
            if row.get("bold"):
                children.append(node("strong", [text(value)]))
                continue
            for span in row.get("strong", []):
                span = span.strip()
                before, value = value.split(span, 1)
                if before:
                    children.append(text(before))
                children.append(node("strong", [text(span)]))
            if value:
                children.append(text(value))
        return children

    def html(self, *refs: str) -> tuple[str, str]:
        """Escaped HTML (bold spans strong) and plain text of joined lines."""
        html, plain = [], []
        for row in self.take(refs):
            value = row["text"].strip()
            plain.append(value)
            marked = escape(value)
            spans = [value] if row.get("bold") else [s.strip() for s in row.get("strong", [])]
            for span in spans:
                marked = marked.replace(escape(span), f"<strong>{escape(span)}</strong>", 1)
            html.append(marked)
        return "".join(html), "".join(plain)

    def mark(self, disposition: str, *refs: str) -> list[str]:
        return [row["text"].strip() for row in self.take(refs, disposition)]


T = Lines()


def para(*refs: str) -> dict:
    return root(node("paragraph", T.inline(*refs)))


def strong_para(*refs: str) -> dict:
    return root(node("paragraph", [node("strong", [text(T.item(*refs))])]))


def heading(*refs: str, level: int = 3, anchor: str | None = None) -> dict:
    value = T.item(*refs)
    return root(node("heading", [text(value)], level=level, **({"anchor": anchor} if anchor else {})))


def chapter(ref: str, anchor: str) -> dict:
    return heading(ref, level=2, anchor=anchor)


def bullets(*items: tuple[str, ...] | str) -> dict:
    return root(bullet_list(*items))


def bullet_list(*items: tuple[str, ...] | str) -> dict:
    nodes = []
    for item in items:
        refs = (item,) if isinstance(item, str) else item
        nodes.append(node("list_item", [node("paragraph", [text(T.item(*refs))])]))
    return node("list", nodes, ordered=False)


def panel(children: list[dict]) -> dict:
    """Shared grey text panel (web_manual.css ``.hb-text-panel``)."""
    return root(node("group", children, role="container",
                     presentation={"html": {"attributes": {"class": "hb-text-panel"}}}))


def with_energy_icon(*refs: str, gap_after: str | None = None) -> dict:
    """A printed paragraph whose blank gap holds the 88H energy-saving LCD glyph.

    The gap is a run of spaces inside a line, or (``gap_after``) the trailing
    spaces of that line, which the line strip removes.
    """
    if gap_after:
        index = refs.index(gap_after) + 1
        if not T.rows[T.ids(gap_after)[-1]]["text"].endswith("   "):
            raise ValueError("printed icon gap moved: " + gap_after)
        before, after = T(*refs[:index]), T(*refs[index:])
    else:
        before, after = re.split(r" {3,}", T(*refs), maxsplit=1)
    return node("paragraph", [text(before + " "), node("image", source=ENERGY_ICON, alt="88H"), text(" " + after)])


def fragment_sha256(ref: str, reference_id: str, alt: str) -> str:
    """The shared renderer's source-fragment hash of a captionless semantic image."""
    soup = BeautifulSoup("", "html.parser")
    semantic = soup.new_tag("div", attrs={"class": "hb-reference-semantic",
                                          "data-reference-id": f"{reference_id}.semantic"})
    semantic.append(soup.new_tag("img", attrs={"alt": alt, "class": "hb-reference-art", "src": ref}))
    return reference_source_fragment_sha256(
        component={"id": reference_id, "image_key": reference_id, "captions_embedded": True},
        semantic=semantic, caption_labels=[], composite_locale=None)


def figure(reference_id: str, page: int, *label_refs: str, label: str | None = None) -> dict:
    """Complete source panel; printed labels stay in the art and the alt text."""
    ref = f"assets/{reference_id}.png"
    labels = T.mark("embedded:" + reference_id, *label_refs)
    alt = label or " / ".join(labels)
    spec = reference_figure_component_spec(
        reference_id=reference_id, accessibility_label=alt, caption_mode="embedded",
        captions=(), adjacent_copy=None, source_art_ref=ref, source_art_locale_policy="exact",
        source_fragment_sha256=fragment_sha256(ref, reference_id, alt),
        source_ref=f"native-pdf/page-{page}/{reference_id}", language=LANGUAGE, image_key=reference_id,
        metadata={"embedded_labels": labels, "physical_page": page},
    )
    return component_flow_node(spec, carrier_flow=(root(node("image", source=ref, alt=alt)),), root=True)


def notice(label_ref: str | None, label: str, body: list[dict], variant: str, ref: str) -> dict:
    if label_ref:
        T.mark("bound:" + T.context + "/callout-label", label_ref)
    return root(callout(label, body, variant=variant, language=LANGUAGE, source_ref=ref))


def item_body(title: tuple[str, ...], body: tuple[str, ...] = (), extra: list[dict] | None = None) -> list[dict]:
    blocks = [node("paragraph", [node("strong", [text(T(*title))])])]
    blocks += extra or []
    if body:
        blocks.append(node("paragraph", [text(T(*body))]))
    return blocks


def plain_table(rows: list[list[dict]], header: list[dict] | None = None) -> dict:
    head = [node("table_head", [node("table_row", header)])] if header else []
    body = node("table_body", [node("table_row", row) for row in rows])
    return root(node("group", [node("table", [*head, body],
                                    presentation={"html": {"attributes": {"class": "manual-table"}}})],
                     role="container",
                     presentation={"html": {"attributes": {"class": "table-wrapper docutils container"}}}))


def cell(refs: tuple[str, ...], header: bool = False, **fields) -> dict:
    return node("table_cell", [text(T(*refs))], header=header, **fields)


# --- chapters -------------------------------------------------------------

def safety() -> list[dict]:
    def pair(value: str, key: str) -> dict:
        return {f"{key}_html": escape(value), f"{key}_text": value}

    def signal_row(label_ref: str, *meaning: str) -> dict:
        label = T.mark("bound:safety/signal-label", label_ref)[0]
        return {"label": label, "show_icon": True, **pair(T(*meaning), "meaning")}

    signal = symbol_signal_component_spec(
        accessibility_label=T.peek("p3-b21"), headers=[pair("表示", "content"), pair("意味", "content")],
        rows=[signal_row("p3-b16", "p3-b12", "p3-b13"), signal_row("p3-b17", "p3-b14", "p3-b15"),
              signal_row("p3-b22", "p3-b24", "p3-b25", "p3-b26"), signal_row("p3-b23", "p3-b27")],
        source_ref="native-pdf/page-3/signal", language=LANGUAGE)

    def symbol_table(label: str, columns: list[list[str]], first: int, ref: str):
        refs, panels, index = [], [], first
        for column in columns:
            rows = []
            for block in column:
                meaning = T(*block.split())
                rows.append({"asset_index": len(refs), "icon_alt": meaning, **pair(meaning, "meaning")})
                refs.append(f"assets/symbol-{index:02d}.svg")
                index += 1
            panels.append(rows)
        spec = symbol_icon_component_spec(
            accessibility_label=label, headers=[pair(v, "content") for v in ("記号", "意味", "記号", "意味")],
            panels=panels, icon_refs=refs, source_ref=ref, language=LANGUAGE)
        return component_flow_node(spec, root=True)

    T.context = "safety"
    nodes = [chapter("p3-b18", "native-safety"), strong_para("p3-b10"),
             heading("p3-b21"), para("p3-b11-l0..1"), para("p3-b11-l2"),
             component_flow_node(signal, root=True), heading("p3-b20"),
             symbol_table(T.peek("p3-b20"), [["p3-b4", "p3-b5", "p3-b6", "p3-b7", "p3-b8"],
                                             ["p3-b0", "p3-b3", "p3-b9", "p3-b1", "p3-b2"]], 1,
                          "native-pdf/page-3/symbols"),
             # The bold box title of the Li-ion row is a heading: the admitted
             # meaning is the hash-bound caption text beside the glyph.
             heading("p4-b5", level=4),
             symbol_table(T.peek("p4-b5"), [["p4-b3"], ["p4-b4", "p4-b13"]], 11,
                          "native-pdf/page-4/disposal-symbols")]
    warn = T.peek("p4-b7")

    def w(title, body=(), extra=None, page=4, n=0, label_ref=None):
        return notice(label_ref, warn, item_body(title, body, extra), "warning", f"native-pdf/page-{page}/warning-{n}")

    nodes += [
        w(("p4-b0-l0..2",), ("p4-b0-l3..4",), n=1, label_ref="p4-b7"),
        w(("p4-b1-l0..1",), ("p4-b1-l2..3",), n=2), w(("p4-b2-l0..1",), ("p4-b2-l2",), n=3),
        w(("p4-b9-l0..1",), ("p4-b9-l2",), n=4), w(("p4-b10-l0..1",), ("p4-b10-l2",), n=5),
        w(("p4-b11-l0..1",), ("p4-b11-l2",), n=6), w(("p4-b12-l0",), ("p4-b12-l1..3",), n=7),
        w(("p4-b6-l0..1",), ("p4-b6-l2..4",), n=8),
        w(("p5-b19",), ("p5-b7",), [bullet_list("p5-b17-l0", "p5-b17-l1", "p5-b17-l2", "p5-b18-l0", "p5-b18-l1")],
          page=5, n=9, label_ref="p5-b14"),
        w(("p5-b9",), ("p5-b8",), page=5, n=10), w(("p5-b16-l1",), ("p5-b16-l0",), page=5, n=11),
        w(("p5-b11",), ("p5-b10",), page=5, n=12), w(("p5-b12",), page=5, n=13),
    ]
    caution = T.peek("p5-b15")
    nodes += [
        notice("p5-b15", caution, item_body(("p5-b3-l0",), ("p5-b3-l1",)), "caution", "native-pdf/page-5/caution-1"),
        notice(None, caution, item_body(("p5-b4",), (), [bullet_list("p5-b0", "p5-b1", "p5-b2")]), "caution",
               "native-pdf/page-5/caution-2"),
        notice(None, caution, item_body(("p5-b5-l0",), ("p5-b5-l1",)), "caution", "native-pdf/page-5/caution-3"),
        notice(None, caution, item_body(("p5-b6",)), "caution", "native-pdf/page-5/caution-4"),
    ]
    return nodes


def precautions() -> list[dict]:
    T.context = "usage_precautions"
    lead = panel([node("paragraph", [text(T(*refs))]) for refs in
                  (("p6-b20", "p6-b21", "p6-b22", "p6-b23"), ("p6-b24",), ("p6-b25", "p6-b26"),
                   ("p6-b27", "p6-b28"))])
    note = notice("p6-b17-l4", T.peek("p6-b17-l4"), [node("paragraph", [text(T("p6-b17-l0..3"))])],
                  "caution", "native-pdf/page-6/caution")
    sub = []
    sub += [heading("p6-b0", level=4), para("p6-b1"),
            bullets(("p6-b2", "p6-b3"), ("p6-b4", "p6-b5"), "p6-b6", ("p6-b7", "p6-b8")),
            heading("p6-b9", level=4),
            bullets(("p6-b10", "p6-b11"), "p6-b12", "p6-b13", ("p6-b14", "p6-b15"), "p6-b16"),
            heading("p7-b7", level=4), bullets("p7-b8", ("p7-b9", "p7-b10"), "p7-b11"),
            heading("p7-b12", level=4), bullets("p7-b13", "p7-b14", "p7-b15"),
            heading("p7-b16", level=4)]
    temperature = node("list_item", [node("paragraph", [text(T.item("p7-b18", "p7-b19"))]),
                                     bullet_list(("p7-b20", "p7-b21"), ("p7-b22", "p7-b23"))])
    sub.append(root(node("list", [node("list_item", [node("paragraph", [text(T.item("p7-b17"))])]), temperature,
                                  node("list_item", [node("paragraph", [text(T.item("p7-b24"))])])],
                         ordered=False)))
    return [chapter("p6-b18", "native-usage-precautions"), lead, note, *sub]


def disclaimer() -> list[dict]:
    T.context = "disclaimer"
    return [chapter("p7-b6", "native-disclaimer"),
            panel([bullet_list("p7-b0", "p7-b1", "p7-b2", "p7-b3", "p7-b4", "p7-b5")])]


def in_the_box() -> list[dict]:
    T.context = "in_the_box"
    head = chapter("p8-b3", "native-in-the-box")
    T.mark("component-number:in_the_box", "p8-b5", "p8-b10")
    cards = [{"image_ref": ref, "label": T(key), "alt": T.peek(key)}
             for key, ref in (("p8-b6-l1", "assets/inbox-unit.png"), ("p8-b6-l0", "assets/inbox-cable.svg"),
                              ("p8-b27", "assets/inbox-manual.png"))]
    title = T.peek("p8-b3")
    spec = inbox_component_spec(accessibility_label=title, cards=cards, tip_label="", tip_body="",
                                source_ref="native-pdf/page-8/inbox", language=LANGUAGE, require_tip=False)
    carrier = table([[node("table_cell", [node("image", source=c["image_ref"], alt=c["alt"]),
                                          node("paragraph", [text(c["label"])])], header=False) for c in cards]])
    notes = panel([node("paragraph", [text(T(k))]) for k in ("p8-b7", "p8-b8", "p8-b9-l0", "p8-b9-l1")])
    return [head, component_flow_node(spec, carrier_flow=(carrier,), root=True), notes, strong_para("p8-b2")]


def overview() -> list[dict]:
    T.context = "product_overview"
    front = ["p8-b22", "p8-b23", "p8-b13", "p8-b16", "p8-b26", "p8-b17", "p8-b25", "p8-b18", "p8-b24",
             "p8-b15-l1", "p8-b19", "p8-b20", "p8-b21", "p8-b14", "p8-b11", "p8-b12", "p8-b15-l0"]
    right = ["p9-b8", "p9-b6-l1", "p9-b7", "p9-b4", "p9-b5", "p9-b6-l0", "p9-b3"]
    return [chapter("p8-b1", "native-product-overview"), heading("p8-b0"),
            figure("overview-front", 8, *front), heading("p9-b1"), figure("overview-right", 9, *right)]


LCD_ICONS = ["1_Wi-Fi_WuAbbIls6okb8pxBe5RcObWUnNd", "2_Bluetooth_EaovbGeSmoIldpxVoWrcVankn5d",
             "3_Quiet_Charging_Mode_IRdmbJVhco57yOx8m0pcdgkXnbe", "4_Charging_Plan_PBCtblGMaoHz4fx08tRcoXUJnIf",
             "5_Self-powered_Mode_VLkXbWOFpoMJYsxWp0xcXkkpn1g", "6_TOU_Mode_BLMAblms7oeDxUxsFb9cgzXvnId",
             "7_UPS_JMnybDJHdoLbjExEMbGcfAkznQh", "8_AC_Power_Indicator_IqesbVEWTo0ANfxDkoDcLP6jnSc",
             "9_Output_Voltage_and_Frequency_XtL4bA80pogLmOx7VJ3ca5fEnl8", "10_Input_Power_BiBvbNteAoNsHqxoMICc11cjnHc",
             # Printed ⑪ is 8.8 H: native vector glyph, not the shared 88H-style file.
             "assets/lcd-remaining-charge-time.svg",
             "12_AC_Wall_Charging_Indicator_OG9ebaP1HoaLvZxbGEAcIXkPnkb",
             "13_Car_Charging_Indicator_WgbebOblvoTtesxjb9ec8CkUnyg",
             "14_Solar_Charging_Indicator_ZMSkb6bWWoKo8WxhBk0cZN5Lnpg",
             "15_Battery_Saving_Mode_QIQlbf95uoUmsFxyEQuc1zxkn22", "16_Charging_Power_Limit_YgjLbaQ2YoZwavxUqrHclXNdnuK",
             "17_Battery_Power_Indicator_VLufb9exvoVLfgxz47pcfnRGnaf",
             "19_Low_Battery_Indicator_TcggbK0LLodgNwx04T6cEqjPn5f",
             "18_Remaining_Battery_Percentage_F7gbbsgPKo4mdkx4JqccMfQRngc",
             "20_Discharge_Timer_X2jjb9dwIomvH6xVJLJclRzpnAh", "22_Energy_Saving_Mode_FdBWbTvwwosJ7TxfeVIc2Flinkh",
             "23_High_Temperature_Indicator_UmkEbOgCKoKyxoxDSINcfO6LnQd",
             "24_Low_Temperature_Indicator_JDMEbD96noSbyWxbOnVcgip1nab", "25_Fault_code_LaTmb4IQYo3vwvxMqQNcC2RgnIf",
             "26_Output_Power_PviebR618oofvKxcKVRcHLlInqd", "27_Remaining_Discharge_Time_QvCQbFmEhoQR3kxgWt4c6H9zn0b"]

# (number line, name line groups, description statements); each statement is joined print lines.
LCD_ROWS = [
    ("p10-b9", [("p10-b17",)], [("p10-b25-l0",), ("p10-b25-l1",), ("p10-b25-l2",)]),
    ("p10-b10", [("p10-b18",)], [("p10-b26-l0",), ("p10-b26-l1",), ("p10-b26-l2",)]),
    ("p10-b11", [("p10-b14",)], [("p10-b19-l0..1",), ("p10-b19-l2",), ("p10-b19-l3", "p10-b20")]),
    ("p10-b12", [("p10-b15",)], [("p10-b21-l0..3",), ("p10-b21-l4", "p10-b22")]),
    ("p10-b13", [("p10-b16",)], [("p10-b23-l0..2",), ("p10-b23-l3",), ("p10-b23-l4", "p10-b24")]),
    ("p10-b1", [("p10-b34",)], [("p10-b36-l0..4",), ("p10-b36-l5..7",), ("p10-b36-l8", "p10-b37")]),
    ("p10-b2", [("p10-b35",)], [("p10-b38-l0..2",), ("p10-b38-l3",)]),
    ("p10-b3", [("p10-b39",)], [("p10-b40",)]),
    ("p10-b4", [("p10-b41-l0",)], [("p10-b41-l1",)]),
    ("p10-b5", [("p10-b27",)], [("p10-b30",)]),
    ("p10-b6", [("p10-b31-l0",)], [("p10-b31-l1",)]),
    ("p10-b7", [("p10-b28",)], [("p10-b32",)]),
    ("p10-b8", [("p10-b29",)], [("p10-b33",)]),
    ("p11-b27", [("p11-b16",)], [("p11-b7",)]),
    ("p11-b28", [("p11-b24-l0",), ("p11-b24-l1..2",)],
     [("p11-b25-l0..1",), ("p11-b25-l2", "p11-b26-l0"), ("p11-b26-l1..2",)]),
    ("p11-b29", [("p11-b17",)], [("p11-b22-l0",), ("p11-b22-l1",), ("p11-b22-l2", "p11-b23")]),
    ("p11-b30", [("p11-b8",)], [("p11-b9",)]),
    ("p11-b31", [("p11-b10",)], [("p11-b18-l0",), ("p11-b18-l1",), ("p11-b18-l2",)]),
    ("p11-b32", [("p11-b38-l1..2",)], [("p11-b38-l0",)]),
    ("p11-b33", [("p11-b11",)], [("p11-b19-l0",), ("p11-b19-l1",), ("p11-b19-l2..3",)]),
    ("p11-b37", [("p11-b12",)], [("p11-b13-l0",), ("p11-b13-l1",), ("p11-b13-l2",)]),
    ("p11-b34", [("p11-b4",)], [("p11-b1",)]),
    (None, [("p11-b5",)], [("p11-b2",)]),
    ("p11-b35", [("p11-b3",)], [("p11-b0",)]),
    ("p11-b36", [("p11-b14",)], [("p11-b20",)]),
    ("p11-b15-l2", [("p11-b15-l0..1",)], [("p11-b21",)]),
]


def lcd() -> list[dict]:
    T.context = "lcd_display"
    nodes = [chapter("p9-b2", "native-lcd-display")]
    numbers = ["p9-b14", "p9-b16", "p9-b15", "p9-b9", "p9-b10", "p9-b13", "p9-b12", "p9-b11"]
    nodes.append(figure("lcd-map", 9, *numbers, label=T.peek("p9-b2")))
    rows, last_number = [], ""
    for index, (number_ref, names, statements) in enumerate(LCD_ROWS):
        # Two temperature rows share printed number 22.
        number = T.mark("component-number:lcd_display", number_ref)[0] if number_ref else last_number
        last_number = number
        name_parts = [T.html(*group) for group in names]
        desc_parts = [T.html(*group) for group in statements]
        rows.append({"number_html": escape(number), "number_text": number,
                     "name_html": "<br/>".join(h for h, _ in name_parts),
                     "name_text": "".join(t for _, t in name_parts),
                     "description_html": "<br/>".join(h for h, _ in desc_parts),
                     "description_text": "".join(t for _, t in desc_parts),
                     "icon_alt": name_parts[0][1], "asset_index": index})
    spec = lcd_icon_component_spec(accessibility_label=T.peek("p9-b2"), rows=rows,
                                   icon_refs=[name if name.startswith("assets/") else f"{LCD}{name}.png"
                                              for name in LCD_ICONS],
                                   source_ref="native-pdf/page-10/lcd-icons", language=LANGUAGE)
    nodes.append(component_flow_node(spec, root=True))
    return nodes


def key_carrier(headers: list[str], rows: list[tuple]) -> dict:
    """The JE-1500D JP V2 shared key-combination carrier with shared button art."""
    def button(name: str, art: str) -> dict:
        return node("group", [node("image", source=f"assets/shared-buttons/{art}.svg", alt=""),
                              node("inline_group", [node("strong", [text(name)])])], role="container",
                    presentation={"html": {"attributes": {"class": "hb-key-button"}}})
    head = node("table_head", [node("table_row", [node("table_cell", [text(h)], header=True) for h in headers])])
    body = []
    for (first, first_art), (second, second_art), duration, action, function in rows:
        pair = node("group", [button(first, first_art),
                              node("inline_group", [text("＋")],
                                   presentation={"html": {"attributes": {"class": "hb-key-button-plus"}}}),
                              button(second, second_art)], role="container",
                    presentation={"html": {"attributes": {"class": "hb-key-button-pair"}}})
        body.append(node("table_row", [
            node("table_cell", [pair], header=False),
            node("table_cell", [node("paragraph", [text(duration)], presentation={"html": {"attributes": {
                "class": "hb-key-duration", "data-duration-icon": "clock"}}}),
                node("paragraph", [text(action)])], header=False),
            node("table_cell", [text(function)], header=False)]))
    return node("table", [head, node("table_body", body)],
                presentation={"html": {"attributes": {"class": "hb-key-combination-table"}}})


def operations() -> list[dict]:
    T.context = "operations"
    nodes = [chapter("p12-b2", "native-operations"),
             heading("p12-b0"),
             figure("power", 12, "p12-b7", "p12-b9", "p12-b8", "p12-b10", "p12-b11", "p12-b12", "p12-b13",
                    "p12-b14"),
             panel([node("paragraph", [text(T("p12-b5", "p12-b6"))])]),
             heading("p12-b1"),
             figure("ac-output", 12, "p12-b3", "p12-b15", "p12-b17", "p12-b16", "p12-b18"),
             heading("p13-b5"),
             panel([node("paragraph", [text(T(*refs))]) for refs in
                    (("p13-b4-l0",), ("p13-b4-l1..2",), ("p13-b4-l3..4",))]),
             figure("frequency", 13, "p13-b3-l0", "p13-b3-l1"),
             heading("p13-b0"),
             figure("dc-usb", 13, "p13-b1", "p13-b10", "p13-b12", "p13-b11", "p13-b13"),
             notice("p13-b6", T.peek("p13-b6"), [bullet_list(("p13-b7",), ("p13-b8",), ("p13-b9",))], "caution",
                    "native-pdf/page-13/caution"),
             para("p14-b20"), para("p14-b21"),
             notice("p14-b22", T.peek("p14-b22"), [bullet_list(("p14-b23",), ("p14-b24",), ("p14-b25",))],
                    "caution", "native-pdf/page-14/caution"),
             heading("p14-b3")]
    lead = with_energy_icon("p14-b5", "p14-b6", "p14-b7", "p14-b8")
    header = [cell(("p14-b16-l1",), True), cell(("p14-b16-l2",), True), cell(("p14-b16-l0",), True)]
    rows = [[cell(("p14-b17-l0",)), cell(("p14-b17-l1",)), cell(("p14-b19",), row_span=2)],
            [cell(("p14-b18-l0",)), cell(("p14-b18-l1",))]]
    nodes += [panel([lead]), plain_table(rows, header),
              panel([with_energy_icon("p14-b9", "p14-b10", "p14-b11", gap_after="p14-b10"),
                     node("paragraph", [text(T("p14-b12", "p14-b13"))])]),
              figure("energy-controls", 14, "p14-b4-l0", "p14-b4-l1", "p14-b0-l0", "p14-b1", "p14-b0-l1"),
              notice("p14-b14", T.peek("p14-b14"), [node("paragraph", [text(T("p14-b15"))])], "note",
                     "native-pdf/page-14/note"),
              heading("p15-b2"), panel([node("paragraph", [text(T("p15-b19", "p15-b20"))])]),
              figure("led-light", 15, "p15-b27", "p15-b21", "p15-b22", "p15-b29-l0", "p15-b29-l1", "p15-b23",
                     "p15-b24", "p15-b28", "p15-b25", "p15-b26", "p15-b29-l2"),
              heading("p15-b1")]

    def group(state: str, actions: list[tuple[str, tuple[str, ...]]]) -> dict:
        value = T(state)
        out = []
        for action_ref, description in actions:
            action, desc = T(action_ref), T(*description)
            out.append({"action_html": escape(action), "action_text": action,
                        "description_html": escape(desc), "description_text": desc})
        return {"state_html": escape(value), "state_text": value, "actions": out}
    mode = lcd_mode_component_spec(
        accessibility_label=T.peek("p15-b1"),
        groups=[group("p15-b3", [("p15-b14", ("p15-b11",)), ("p15-b6", ("p15-b12",)), ("p15-b10", ("p15-b13",))]),
                group("p15-b4", [("p15-b9", ("p15-b15",)), ("p15-b8", ("p15-b16",)),
                                 ("p15-b7", ("p15-b17", "p15-b18"))])],
        artwork_ref="assets/lcd-button.png", source_ref="native-pdf/page-15/lcd-mode", language=LANGUAGE)
    nodes += [component_flow_node(mode, root=True), para("p15-b5"), heading("p16-b3")]
    headers = [T("p16-b15-l0"), T("p16-b15-l1"), T("p16-b15-l2")]
    raw = [((T("p16-b5-l0"), "power"), (T("p16-b5-l1"), "ac"), T("p16-b4"), T("p16-b7"), T("p16-b10")),
           ((T("p16-b18"), "power"), (T("p16-b21"), "dc_usb"), T("p16-b17"), T("p16-b19"), T("p16-b20")),
           ((T("p16-b16"), "ac"), (T("p16-b6"), "dc_usb"), T("p16-b8"), T("p16-b9"), T("p16-b11")),
           ((T("p16-b22-l0"), "power"), (T("p16-b22-l1"), "led"), T("p16-b12"), T("p16-b13"), T("p16-b14"))]
    T.mark("embedded:shared-buttons", "p16-b23")
    rows3 = [[f"{a[0]} ＋ {b[0]}", f"{d} {act}", fn] for a, b, d, act, fn in raw]
    spec = key_combinations_component_spec(headers=headers, rows=rows3,
                                           source_ref="native-pdf/page-16/key-combinations", language=LANGUAGE)
    nodes.append(component_flow_node(spec, carrier_flow=(key_carrier(headers, raw),), root=True))
    return nodes


def ups() -> list[dict]:
    T.context = "ups"
    return [chapter("p16-b1", "native-ups"), figure("ups", 16, "p16-b2"),
            panel([node("paragraph", [text(T(*refs))]) for refs in
                   (("p17-b1", "p17-b2", "p17-b3", "p17-b4"), ("p17-b5",), ("p17-b6",), ("p17-b7",), ("p17-b8",),
                    ("p17-b9", "p17-b10"), ("p17-b11", "p17-b12"), ("p17-b13", "p17-b14", "p17-b15", "p17-b16"))])]


def charging() -> list[dict]:
    T.context = "charging"
    caution = "ご注意"
    nodes = [chapter("p17-b18", "native-charging"), para("p17-b27-l0"), para("p17-b27-l1..3"),
             notice("p17-b19", T.peek("p17-b19"), [bullet_list(("p17-b20", "p17-b21"), "p17-b22")], "caution",
                    "native-pdf/page-17/caution-1"),
             notice("p17-b23", T.peek("p17-b23"), [bullet_list("p17-b24", "p17-b25", "p17-b26")], "caution",
                    "native-pdf/page-17/caution-2"),
             heading("p17-b17"), para("p17-b28", "p17-b29", "p17-b30", "p17-b31"),
             figure("ac-charge", 18, "p18-b6"),
             notice("p18-b7", caution, [node("paragraph", [text(T("p18-b8", "p18-b9", "p18-b10"))])], "caution",
                    "native-pdf/page-18/caution"),
             panel([node("paragraph", T.inline("p18-b11-l0..3")), node("paragraph", [text(T("p18-b11-l4..5"))])]),
             heading("p18-b1"), para("p18-b2", "p18-b3"),
             panel([node("paragraph", [text(T("p18-b4-l0"))]), bullet_list("p18-b4-l1", ("p18-b4-l2..3",)),
                    node("paragraph", [text(T("p18-b4-l4..5"))])]),
             heading("p18-b12", level=4),
             root(node("list", [node("list_item", [node("paragraph", [text(T.item("p18-b5-l0"))]),
                                                   node("paragraph", [text(T("p18-b5-l1..2"))])])], ordered=False)),
             figure("solar-direct", 19, "p19-b1"),
             heading("p19-b11", level=4),
             root(node("list", [node("list_item", [node("paragraph", [text(T.item("p19-b2-l0"))]),
                                                   bullet_list(("p19-b2-l1..2",), ("p19-b2-l3..4",))])],
                       ordered=False)),
             figure("solar-adapter", 19, "p19-b10", "p19-b9"),
             notice("p19-b3", caution, [node("paragraph", [text(T("p19-b4"))]),
                                        node("paragraph", [text(T("p19-b5"))]),
                                        node("paragraph", [text(T("p19-b6"))]),
                                        bullet_list(("p19-b7",), ("p19-b8",))], "caution",
                    "native-pdf/page-19/caution"),
             para("p20-b1"),
             heading("p20-b2"),
             root(node("paragraph", [node("strong", [text(T.item("p20-b4"))])])),
             para("p20-b5"), para("p20-b6"),
             bullets(("p20-b7", "p20-b8"), "p20-b9", "p20-b10", ("p20-b11", "p20-b12"), "p20-b13"),
             figure("car-charge", 20, "p20-b17", "p20-b3"),
             notice("p20-b14", caution, [bullet_list(("p20-b15",), ("p20-b16",))], "caution",
                    "native-pdf/page-20/caution")]
    return nodes


def troubleshooting() -> list[dict]:
    T.context = "troubleshooting"

    def pair(value_html: str, value_text: str, key: str) -> dict:
        return {f"{key}_html": value_html, f"{key}_text": value_text}

    def row(codes: tuple[str, ...], measures: tuple[tuple[str, ...], ...]) -> dict:
        code = [T.html(c) for c in codes]
        parts = [T.html(*m) for m in measures]
        return {**pair("<br/>".join(h for h, _ in code), "".join(t for _, t in code), "code"),
                **pair("<br/>".join(h for h, _ in parts), "".join(t for _, t in parts), "measures")}
    header = [T("p21-b4-l0"), T("p21-b4-l1")]
    rows = [row(("p21-b14-l1", "p21-b14-l0"), (("p21-b15",),)),
            row(("p21-b13-l0",), (("p21-b13-l1",),)),
            row(("p21-b9",), (("p21-b12",),)),
            row(("p21-b8",), (("p21-b17",), ("p21-b18",), ("p21-b19",), ("p21-b20",), ("p21-b21",))),
            row(("p21-b7",), (("p21-b22",), ("p21-b23",), ("p21-b24",))),
            row(("p21-b6",), (("p21-b16",),)),
            row(("p21-b5",), (("p21-b10",),)),
            row(("p21-b11-l0",), (("p21-b11-l1",),))]
    spec = troubleshooting_component_spec(headers=[pair(escape(h), h, "content") for h in header], rows=rows,
                                          source_ref="native-pdf/page-21/troubleshooting", language=LANGUAGE)
    return [chapter("p21-b3", "native-troubleshooting"), para("p21-b1"), para("p21-b2"),
            component_flow_node(spec, root=True)]


def specifications() -> list[dict]:
    T.context = "specifications"

    def spec_table(title_ref: str, rows: list[tuple[str, tuple[str, ...]]], ref: str) -> dict:
        title = T.item(title_ref)
        values = [(T(label) if label else "", "\n".join(T(v) for v in value)) for label, value in rows]
        spec = spec_table_component_spec(section_title=title, rows=values, source_ref=ref, language=LANGUAGE)
        return component_flow_node(spec, carrier_flow=_spec_carrier(title, values), root=True)
    nodes = [chapter("p22-b30", "native-specifications"),
             spec_table("p22-b1", [("p22-b2", ("p22-b8",)), ("p22-b3", ("p22-b9",)), ("p22-b4", ("p22-b10",)),
                                   ("p22-b5", ("p22-b11",)), ("p22-b6", ("p22-b12",)), ("p22-b7", ("p22-b13",))],
                        "native-pdf/page-22/spec-basic"),
             spec_table("p22-b14", [("p22-b15", ("p22-b18",)), ("", ("p22-b19",)), ("p22-b17", ("p22-b20",)),
                                    ("", ("p22-b21",))], "native-pdf/page-22/spec-input")]
    output = [("p22-b39-l1", None), ("p22-b40", ("p22-b36",)), ("p22-b41", ("p22-b35",)),
              ("p22-b42", ("p22-b37",)), ("p22-b43", ("p22-b33",)), ("p22-b44", ("p22-b34",))]
    title = T.item("p22-b22")
    values = []
    for label, value in output:
        name = T(label)
        values.append((name, T("p22-b38", "p22-b39-l0") if value is None else T(*value)))
    spec = spec_table_component_spec(section_title=title, rows=values, source_ref="native-pdf/page-22/spec-output",
                                     language=LANGUAGE)
    nodes.append(component_flow_node(spec, carrier_flow=_spec_carrier(title, values), root=True))
    temperature_title = T.item("p22-b26")
    temperature = [(T("p22-b23"), T("p22-b27")), (T("p22-b24"), T("p22-b28")),
                   (T("p22-b25"), "\n".join(T(f"p22-b32-l{i}") for i in range(3)))]
    spec = spec_table_component_spec(section_title=temperature_title, rows=temperature,
                                     source_ref="native-pdf/page-22/spec-temperature", language=LANGUAGE)
    nodes.append(component_flow_node(spec, carrier_flow=_spec_carrier(temperature_title, temperature), root=True))
    # The two ® marks are separate 4 pt text lines printed in the gaps after
    # "Type-C" and "USB-C"; they are placed back where they are printed.
    trademark = T("p22-b29-l1")
    marks = T("p22-b29-l2") + T("p22-b29-l3")
    if marks != "®®" or trademark.count("   ") != 2:
        raise ValueError("trademark line layout changed")
    trademark = trademark.replace("   ", "® ", 2)
    nodes += [para("p22-b29-l0"), root(node("paragraph", [text(trademark)])), para("p22-b31")]
    return nodes


def warranty() -> list[dict]:
    T.context = "warranty"

    def section(index: int, title_ref: str, blocks: list[dict]) -> list[dict]:
        title_text = T.peek(title_ref)
        title = heading(title_ref)
        spec = warranty_section_component_spec(title=title_text, section_index=index, blocks=blocks,
                                               source_ref=f"native-pdf/warranty/{index}", language=LANGUAGE)
        return [title, component_flow_node(spec, root=True)]

    def p(*groups: tuple[str, ...] | str) -> dict:
        parts = [T.html(*((g,) if isinstance(g, str) else g)) for g in groups]
        return {"kind": "paragraph", "html": "<p>" + "<br/>".join(h for h, _ in parts) + "</p>",
                "text": "".join(t for _, t in parts)}

    return [chapter("p23-b2", "native-warranty"),
            panel([node("paragraph", [text(T(f"p23-b1-l{i}"))]) for i in range(3)]),
            *section(1, "p23-b9", [p("p23-b5-l0", "p23-b5-l1", "p23-b5-l2"), p("p23-b6"), p("p23-b4"),
                                   p("p23-b19")]),
            *section(2, "p23-b11", [p("p23-b7-l0", "p23-b7-l1"), p("p23-b3"), p("p23-b8-l0", "p23-b8-l1")]),
            *section(3, "p23-b14", [p("p23-b12", "p23-b13-l0", "p23-b13-l1", "p23-b13-l2")]),
            *section(4, "p23-b16", [p("p23-b15-l0", "p23-b15-l1", ("p23-b15-l2", "p23-b15-l3"), "p23-b15-l4",
                                      "p23-b15-l5", "p23-b15-l6", "p23-b15-l7")]),
            *section(5, "p23-b18", [p("p23-b17-l0", "p23-b17-l1", "p23-b17-l2"), p("p23-b10")]),
            *section(6, "p24-b11", [p("p24-b8-l0", ("p24-b8-l1", "p24-b8-l2"), "p24-b8-l3"),
                                    p("p24-b9-l0", "p24-b9-l1", ("p24-b9-l2", "p24-b9-l3")),
                                    p(*(f"p24-b10-l{i}" for i in range(6))), p(("p24-b1-l0", "p24-b1-l1"))]),
            panel([node("paragraph", [node("strong", [text(T("p24-b12"))])]),
                   node("paragraph", [text(T("p24-b2", "p24-b3"))]), node("paragraph", [text(T("p24-b4"))]),
                   node("paragraph", [text(T("p24-b5"))]), node("paragraph", [text(T("p24-b6"))]),
                   node("paragraph", [text(T("p24-b7"))])]),
            panel([node("paragraph", [text(T(k))]) for k in ("p24-b13", "p24-b14", "p24-b15")])]


def app_manual() -> list[dict]:
    T.context = "app_setup"
    nodes = [chapter("p25-b21", "native-app-manual"), heading("p25-b12")]
    columns = [{"role": "store", "text": T("p25-b6", "p25-b7", "p25-b8")},
               {"role": "qr", "text": T("p25-b9", "p25-b10", "p25-b11")}]
    for column in columns:
        column["html"] = escape(column["text"])
    download = app_download_component_spec(
        accessibility_label="Jackery App", columns=columns, source_art_ref="assets/app-qr.png",
        store_art_ref="assets/app-store.png", qr_art_ref="assets/app-qr.png",
        source_ref="native-pdf/page-25/download", language=LANGUAGE)
    carrier = [node("image", source="assets/app-qr.png", alt="Jackery App"),
               *(node("paragraph", [text(c["text"])]) for c in columns)]
    before, after = re.split(r" {6,}", T("p25-b5"), maxsplit=1)
    plus = app_inline_control_component_spec(
        accessibility_label="+", paragraph_html=f"{escape(before)} <strong>+</strong> {escape(after)}",
        paragraph_text=f"{before} + {after}", source_ref="native-pdf/page-25/add-button", language=LANGUAGE,
        metadata={"visual_recovery": "pdf-vector-plus-control-in-printed-gap"})
    plus_carrier = node("paragraph", [text(before + " "), node("strong", [text("+")]), text(" " + after)])

    def note(label_ref: str, body: list[dict], ref: str) -> dict:
        return notice(label_ref, T.peek(label_ref), body, "note", ref)

    nodes += [component_flow_node(download, carrier_flow=carrier, root=True),
              heading("p25-b1"), component_flow_node(plus, carrier_flow=(plus_carrier,), root=True),
              para("p25-b2", "p25-b3", "p25-b4"),
              figure("app-add", 25, "p25-b13-l0", "p25-b13-l1"),
              figure("app-control", 25, "p25-b23", "p25-b24", "p25-b22"),
              para("p26-b1"),
              note("p26-b32-l2", [node("paragraph", [text(T("p26-b31"))]),
                                  bullet_list("p26-b32-l0", "p26-b32-l1")], "native-pdf/page-26/note-1"),
              para("p26-b6"),
              note("p26-b29", [node("paragraph", [text(T("p26-b8"))])], "native-pdf/page-26/note-2"),
              para("p26-b7"),
              figure("app-results", 26, "p26-b9-l1", "p26-b9-l2", "p26-b9-l0", "p26-b15", "p26-b16"),
              para("p26-b5"),
              note("p26-b30-l3", [node("paragraph", [text(T("p26-b30-l0..2"))])], "native-pdf/page-26/note-3"),
              heading("p26-b2"), para("p26-b3", "p26-b4"),
              heading("p26-b27"),
              heading("p26-b28", level=4), bullets("p26-b24", ("p26-b25", "p26-b26")),
              heading("p26-b20", level=4), bullets(("p26-b18", "p26-b19")),
              heading("p26-b23", level=4), bullets(("p26-b21", "p26-b22"))]
    return nodes


CHAPTERS = (
    ("safety", "安全上のご注意", safety), ("usage_precautions", "使用上のご注意", precautions),
    ("disclaimer", "免責事項", disclaimer), ("in_the_box", "同梱品", in_the_box),
    ("product_overview", "各部の名称", overview), ("lcd_display", "液晶画面", lcd),
    ("operations", "使い方", operations), ("ups", "UPS 機能", ups), ("charging", "充電方法", charging),
    ("troubleshooting", "トラブルシューティング", troubleshooting), ("specifications", "主な仕様", specifications),
    ("warranty", "保証について", warranty), ("app_setup", "Jackeryアプリ ユーザーマニュアル", app_manual),
)


def build() -> dict:
    global T
    T = Lines()
    chapters = [{"id": cid, "title": title, "nodes": make()} for cid, title, make in CHAPTERS]
    for key, row in T.rows.items():
        # Printed folios: 6 pt digits on the bottom margin.
        if key not in T.disposition and row["bbox"][1] >= 503 and row["text"].strip().isdigit():
            T.disposition[key] = "excluded:printed-page-number"
    missing = [k for k in T.order if k not in T.disposition]
    if missing:
        raise ValueError("Web-page source lines not accounted for: " + ", ".join(missing))
    return {"model": "JE-1800B", "region": "JP", "language": LANGUAGE,
            "title": "Jackery ポータブル電源 1800 取扱説明書", "source_sha256": SOURCE_SHA256,
            "chapters": chapters}


def dispositions() -> dict:
    return {"schema_version": "je1800b-jp-line-dispositions/v1", "source_sha256": SOURCE_SHA256,
            "lines": {key: T.disposition[key] for key in T.order}}


def main() -> None:
    content = build()
    (PACKAGE / "source/ja/content.json").write_text(json.dumps(content, ensure_ascii=False, indent=1) + "\n",
                                                    encoding="utf-8")
    (PACKAGE / "source/line_dispositions.json").write_text(
        json.dumps(dispositions(), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"chapters": [c["id"] for c in content["chapters"]], "lines": len(T.disposition)}))


if __name__ == "__main__":
    main()
