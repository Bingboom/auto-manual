"""Derive the JE-3600A CN and JP shared-component editions from the Web-layout editions.

Operator, 2026-10-15: 「样式不要自己画」「明明有共享的」. The Web-layout editions drew
their tables, panels and figure overlays with source-local styles. This edition keeps
their reviewed copy and artwork and replays every block through the shared components
the JE-3600A EU edition already uses (symbol signal and icon tables, inbox, LCD icon
and LCD mode tables, key combinations, troubleshooting, specifications, warranty,
callouts, reference figures) or as plain shared flow. No source-local style remains.

The same file lives in both editions; it derives the one it sits in. Run from the
repository root:

    python data/manual_sources/JE-3600A/JP/git-20261015-fd06cd04-shared/derive_shared.py
    python data/manual_sources/JE-3600A/CN/git-20261015-caa5370a-shared/derive_shared.py

Every structural change is logged in source/<language>/shared_components.json, and
the visible copy is checked against the Web-layout edition (see audit_copy).
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import html
import json
from pathlib import Path
import re
import shutil
import sys

HERE = Path(__file__).resolve().parent
REPO = next(p for p in HERE.parents if (p / "build.py").is_file())
sys.path.insert(0, str(REPO))

from bs4 import BeautifulSoup  # noqa: E402

from tools.component_specs.callout import display_label  # noqa: E402
from tools.component_specs.app import (  # noqa: E402
    app_download_component_spec, app_inline_control_component_spec, app_qr_download_component_spec)
from tools.component_specs.inbox import inbox_component_spec  # noqa: E402
from tools.component_specs.key_combinations import key_combinations_component_spec  # noqa: E402
from tools.component_specs.lcd_mode import lcd_mode_component_spec  # noqa: E402
from tools.component_specs.manual_tables import (  # noqa: E402
    lcd_icon_component_spec, symbol_icon_component_spec, symbol_signal_component_spec,
    troubleshooting_component_spec,
)
from tools.component_specs.model import ComponentSpec  # noqa: E402
from tools.component_specs.spec_table import spec_table_component_spec  # noqa: E402
from tools.manual_ir.components import component_flow_node  # noqa: E402
from tools.manual_ir.flow import flow_nodes_to_html  # noqa: E402
from tools.web.frozen_ai_flow import callout as shared_callout  # noqa: E402
from tools.web.frozen_ai_flow import node, root, text  # noqa: E402
from tools.web.frozen_ai_table_components import _spec_carrier  # noqa: E402
from tools.component_specs.reference_figure_adapters import web_reference_figure_projection  # noqa: E402
from tools.web.composite_presentation import WebCompositeContext  # noqa: E402
from tools.web.presentation import _transform_reference_figure  # noqa: E402
from tools.web.reference_figure_component import _component_contract, _validate_carrier  # noqa: E402

EDITIONS = {
    "JP": {"language": "ja", "base": "git-20261013-fd06cd04-web-layout"},
    "CN": {"language": "zh", "base": "git-20261013-caa5370a-web-layout"},
}
# Headers the shared tables require; the prints have none (logged per table).
L10N = {
    "ja": {"symbol": ["記号", "意味"], "signal_label": "絵表示について", "symbol_label": "絵表示の説明",
           "lcd_label": "液晶画面", "lcd_mode_label": "LCDスクリーン", "callout_variants":
           {"ご注意": "caution", "注意": "caution", "警告": "warning", "説明": "note", "ヒント": "tip"}},
    "zh": {"symbol": ["图示", "含义"], "signal_label": "图标说明", "symbol_label": "图标说明",
           "lcd_label": "液晶屏", "lcd_mode_label": "LCD屏幕", "callout_variants":
           {"注意": "caution", "警告": "warning", "说明": "note", "提示": "tip", "小贴士": "tip"}},
}


def region_of(path: Path) -> str:
    return path.parent.name


REGION = region_of(HERE)
LANGUAGE = EDITIONS[REGION]["language"]
BASE = HERE.parent / EDITIONS[REGION]["base"]
LOG: list[dict] = []


def dump(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


# --- flow helpers --------------------------------------------------------------------------
def classes(item) -> list[str]:
    value = item.get("presentation", {}).get("html", {}).get("attributes", {}).get("class", "")
    return value.split() if isinstance(value, str) else list(value)


def has(item, name) -> bool:
    return name in classes(item)


def plain(item) -> str:
    kind = item.get("kind")
    if kind == "text":
        return item["text"]
    if kind == "line_break":
        return "\n"
    if kind == "image":
        return ""
    if kind == "component":
        return ""
    return "".join(plain(child) for child in item.get("children", []))


def squash(value: str) -> str:
    return re.sub(r"[ \t　]+", " ", value).strip()


def walk(item, found, predicate):
    if predicate(item):
        found.append(item)
        return found
    for child in item.get("children", []):
        walk(child, found, predicate)
    return found


def merge_text(item):
    """Adjacent text nodes render as one string; store them as one (the shared callout checks it)."""
    children = item.get("children")
    if children:
        merged = []
        for child in children:
            merge_text(child)
            if merged and child.get("kind") == "text" and merged[-1].get("kind") == "text":
                merged[-1] = text(merged[-1]["text"] + child["text"])
            else:
                merged.append(child)
        item["children"] = merged
    return item


def strip_styles(item):
    """Remove source-local (ht-*, native-*) classes and inline styles; keep shared hooks."""
    presentation = item.get("presentation")
    if presentation:
        attributes = presentation.get("html", {}).get("attributes", {})
        attributes.pop("style", None)
        names = [name for name in classes(item) if not name.startswith(("ht-", "native-"))]
        if "class" in attributes:
            if names:
                attributes["class"] = " ".join(names)
            else:
                attributes.pop("class")
        if not attributes:
            item.pop("presentation")
    for child in item.get("children", []):
        strip_styles(child)
    return item


def unwrap(nodes):
    """Groups that only carried source-local classes give way to their children."""
    result = []
    for item in nodes:
        if item.get("kind") == "group" and item.get("role") == "container" and classes(item) \
                and all(name.startswith("ht-") for name in classes(item)):
            result.extend(unwrap(item.get("children", [])))
        else:
            result.append(item)
    return result


def markup(items) -> str:
    items = [strip_styles(deepcopy(item)) for item in items]
    return flow_nodes_to_html([root(item) if "schema_version" not in item else item for item in items]).strip()


def cell_html(cell) -> tuple[str, str]:
    """A table cell's rich copy without images, as shared-table HTML and text."""
    children = [child for child in deepcopy(cell.get("children", [])) if child.get("kind") != "image"]
    for child in children:
        for image in walk(child, [], lambda n: n.get("kind") == "image"):
            image.clear()
            image.update(text(""))
    value = squash(plain({"children": children}).replace("\n", " "))
    content = markup(children) if children else html.escape(value)
    content = re.sub(r"^<p>(.*)</p>$", r"\1", content, flags=re.S) if content.count("<p>") == 1 else content
    return content, value


def table_rows(table):
    rows = []
    for section in table.get("children", []):
        if section.get("kind") in {"table_head", "table_body"}:
            rows.extend(section.get("children", []))
    return rows


def image_in(item):
    images = walk(item, [], lambda n: n.get("kind") == "image")
    return images[0]["source"] if images else None


REFS: dict[str, int] = {}


def ref(chapter: str, kind: str) -> str:
    """A unique, stable component source_ref within this edition."""
    key = f"{chapter}/{kind}"
    REFS[key] = REFS.get(key, 0) + 1
    return f"{key}-{REFS[key]}"


def log(kind, **fields):
    LOG.append({"change": kind, **fields})


# --- table handlers ------------------------------------------------------------------------
def signal_table(table, chapter):
    rows = []
    for row in table_rows(table):
        label_cell, meaning_cell = row["children"]
        meaning_html, meaning_text = cell_html(meaning_cell)
        rows.append({"label": squash(plain(label_cell)), "show_icon": image_in(label_cell) is not None,
                     "meaning_html": meaning_html, "meaning_text": meaning_text})
    headers = [{"content_html": h, "content_text": h} for h in L10N[LANGUAGE]["symbol"]]
    spec = symbol_signal_component_spec(accessibility_label=L10N[LANGUAGE]["signal_label"], headers=headers,
                                        rows=rows, source_ref=ref(chapter, "symbol-signal"), language=LANGUAGE)
    log("signal-table", chapter=chapter, component="HB-TABLE-SYMBOL-SIGNAL", rows=len(rows),
        added_headers=L10N[LANGUAGE]["symbol"])
    return component_flow_node(spec, root=True)


def symbol_pair(group, chapter, assets):
    panels, refs = [], []
    tables = walk(group, [], lambda n: n.get("kind") == "table")
    if len(tables) != 2:
        raise ValueError(f"{chapter}: a symbol pair holds two tables")
    for table in tables:
        panel = []
        for row in table_rows(table):
            source = image_in(row)
            body = row["children"][-1]
            meaning_html, meaning_text = cell_html(body)
            panel.append({"asset_index": len(refs), "icon_alt": meaning_text.split("。")[0] + ("。" if "。" in meaning_text else ""),
                          "meaning_html": meaning_html, "meaning_text": meaning_text})
            refs.append(source)
            assets.add(source)
        panels.append(panel)
    headers = [{"content_html": h, "content_text": h} for h in L10N[LANGUAGE]["symbol"] * 2]
    spec = symbol_icon_component_spec(accessibility_label=L10N[LANGUAGE]["symbol_label"], headers=headers,
                                      panels=panels, icon_refs=refs, source_ref=ref(chapter, "symbol-icon"),
                                      language=LANGUAGE, icon_locale_policy="exact")
    log("symbol-pair", chapter=chapter, component="HB-TABLE-SYMBOL-ICON",
        rows=[len(p) for p in panels], added_headers=L10N[LANGUAGE]["symbol"] * 2)
    return component_flow_node(spec, root=True)


def safety_table(table, chapter, assets):
    """Icon + instruction list: rows an icon spans merge; the shared two-panel symbol table holds them."""
    groups = []
    for row in table_rows(table):
        cells = row["children"]
        if len(cells) == 2:
            groups.append({"icon": image_in(cells[0]), "bodies": [cells[1]]})
        elif len(cells) == 1 and groups:
            groups[-1]["bodies"].append(cells[0])
        else:
            raise ValueError(f"{chapter}: unexpected safety row")
    rows, refs = [], []
    for group in groups:
        parts = [cell_html(body) for body in group["bodies"]]
        body_html = "".join(part if part.startswith("<") else f"<p>{part}</p>" for part, _ in parts)
        body_text = " ".join(value for _, value in parts)
        heading = walk(group["bodies"][0], [], lambda n: n.get("kind") == "strong")
        alt = squash(plain(heading[0])) if heading else body_text.split("。")[0]
        rows.append({"asset_index": len(refs), "icon_alt": alt, "meaning_html": body_html, "meaning_text": body_text})
        refs.append(group["icon"])
        assets.add(group["icon"])
    # Two panels in reading order, balanced by copy length.
    total, running, split = sum(len(r["meaning_text"]) for r in rows), 0, len(rows)
    for index, row in enumerate(rows):
        running += len(row["meaning_text"])
        if running >= total / 2:
            split = index + 1
            break
    split = min(max(split, 1), len(rows) - 1)
    headers = [{"content_html": h, "content_text": h} for h in L10N[LANGUAGE]["symbol"] * 2]
    spec = symbol_icon_component_spec(accessibility_label=CURRENT_HEADING[0] or L10N[LANGUAGE]["symbol_label"],
                                      headers=headers, panels=[rows[:split], rows[split:]], icon_refs=refs,
                                      source_ref=ref(chapter, "symbol-icon"), language=LANGUAGE,
                                      icon_locale_policy="exact")
    log("safety-table", chapter=chapter, component="HB-TABLE-SYMBOL-ICON", rows=len(rows),
        merged_rows=sum(len(g["bodies"]) - 1 for g in groups), panels=[split, len(rows) - split],
        added_headers=L10N[LANGUAGE]["symbol"] * 2,
        note="icon + instruction list becomes the shared two-panel symbol table; rows one icon spans merge")
    return component_flow_node(spec, root=True)


def lcd_icon_table(table, chapter, assets):
    rows, refs, number = [], [], ""
    for row in table_rows(table):
        cells = {name: cell for cell in row["children"] for name in classes(cell)}
        if "ht-lcd-number" in cells:
            number = squash(plain(cells["ht-lcd-number"]))
        elif not number:
            raise ValueError(f"{chapter}: LCD row without a number")
        name_html, name_text = cell_html(cells["ht-lcd-name"])
        description_html, description_text = cell_html(cells["ht-lcd-desc"])
        source = image_in(cells["ht-lcd-icon"])
        refs.append(source)
        assets.add(source)
        rows.append({"number_html": html.escape(number), "number_text": number, "name_html": name_html,
                     "name_text": name_text, "description_html": description_html,
                     "description_text": description_text, "icon_alt": name_text, "asset_index": len(rows)})
    spec = lcd_icon_component_spec(accessibility_label=L10N[LANGUAGE]["lcd_label"], rows=rows, icon_refs=refs,
                                   source_ref=ref(chapter, "lcd-icon"), language=LANGUAGE, icon_locale_policy="exact")
    log("lcd-icon-table", chapter=chapter, component="HB-TABLE-LCD-ICON", rows=len(rows),
        note="Print row-spanned numbers repeat on each row of their span.")
    return component_flow_node(spec, root=True)


def lcd_mode_table(table, artwork, chapter, assets):
    groups, header = [], None
    for row in table_rows(table):
        cells = row["children"]
        if all(cell.get("header") for cell in cells):
            header = [squash(plain(cell)) for cell in cells]  # the shared table has no header row
            continue
        if any(has(cell, "ht-lcd-mode") for cell in cells):
            state_html, state_text = cell_html(cells[0])
            groups.append({"state_html": state_html, "state_text": state_text, "actions": []})
            cells = cells[1:]
        action_html, action_text = cell_html(cells[0])
        description_html, description_text = cell_html(cells[1])
        groups[-1]["actions"].append({"action_html": action_html, "action_text": action_text,
                                      "description_html": description_html,
                                      "description_text": description_text})
    assets.add(artwork)
    spec = lcd_mode_component_spec(accessibility_label=L10N[LANGUAGE]["lcd_mode_label"], groups=groups,
                                   artwork_ref=artwork, artwork_locale_policy="exact",
                                   source_ref=ref(chapter, "lcd-mode"), language=LANGUAGE)
    log("lcd-mode-table", chapter=chapter, component="HB-TABLE-LCD-MODE", states=len(groups),
        **({"dropped_header_row": header} if header else {}))
    return component_flow_node(spec, root=True)


def key_table(table, chapter):
    rows = [[squash(plain(cell).replace("\n", " ")) for cell in row["children"]] for row in table_rows(table)]
    spec = key_combinations_component_spec(headers=rows[0], rows=rows[1:], source_ref=ref(chapter, "key-combinations"),
                                           language=LANGUAGE)
    log("key-combinations", chapter=chapter, component="HB-TABLE-KEY-COMBINATIONS", rows=len(rows) - 1,
        dropped="button and clock glyphs beside the printed words (the shared table is text-only, as in EU)")
    return component_flow_node(spec, root=True)


def troubleshooting_table(table, chapter):
    rows = table_rows(table)
    headers = [{"content_html": html.escape(squash(plain(c))), "content_text": squash(plain(c))}
               for c in rows[0]["children"]]
    body = []
    for row in rows[1:]:
        code_html, code_text = cell_html(row["children"][0])
        measures_html, measures_text = cell_html(row["children"][1])
        body.append({"code_html": code_html, "code_text": code_text,
                     "measures_html": measures_html, "measures_text": measures_text})
    spec = troubleshooting_component_spec(headers=headers, rows=body, source_ref=ref(chapter, "troubleshooting"),
                                          language=LANGUAGE)
    log("troubleshooting", chapter=chapter, component="HB-TABLE-TROUBLESHOOTING", rows=len(body))
    return component_flow_node(spec, root=True)


def spec_table(table, title, chapter):
    rows, spanned, merged = [], 0, 0
    for row in table_rows(table):
        cells = row["children"]
        value = "\n".join(squash(part) for part in plain(cells[-1]).split("\n") if squash(part))
        if spanned and len(cells) == 1:
            # A label the print spans over several rows: one row, its values on separate lines.
            rows[-1] = (rows[-1][0], rows[-1][1] + "\n" + value)
            spanned -= 1
            merged += 1
            continue
        label = squash(plain(cells[0]).replace("\n", " "))
        spanned = (cells[0].get("row_span") or 1) - 1
        rows.append((label, value))
    spec = spec_table_component_spec(section_title=title, rows=rows, source_ref=ref(chapter, "spec"),
                                     language=LANGUAGE)
    log("spec-table", chapter=chapter, component="HB-TABLE-SPEC", title=title, rows=len(rows),
        spanned_rows_merged=merged)
    return component_flow_node(spec, carrier_flow=_spec_carrier(title, rows), root=True)


# --- reference figures ----------------------------------------------------------------------
CJK = re.compile(r"[　-ヿ㐀-鿿＀-￯]")
FONT = re.compile(r"font-size:\s*([0-9.]+)cqw")
LABEL_SIZES: dict[str, dict[int, float]] = {}


def join_lines(left: str, right: str) -> str:
    if not left or not right:
        return left + right
    if CJK.search(left[-1]) or CJK.search(right[0]):
        return left.rstrip() + right.lstrip()
    return left.rstrip() + " " + right.lstrip()


def line_size(line):
    for item in walk(line, [], lambda n: "style" in n.get("presentation", {}).get("html", {}).get("attributes", {})):
        match = FONT.search(item["presentation"]["html"]["attributes"]["style"])
        if match:
            return float(match.group(1))
    return None


def reference_flow(spec, flow):
    """Shared reference-figure validation, as the frozen intakes run it."""
    payload = web_reference_figure_projection(spec)
    count = len(payload["captions"])
    payload.update(capture_following_lines=count, captions_origin="carrier", composite_locale="")
    soup = BeautifulSoup(flow_nodes_to_html([root(deepcopy(v)) for v in flow]), "html.parser")
    image = _validate_carrier(payload, soup)
    _transform_reference_figure(soup, image=image, spec=_component_contract(payload),
                                source_path=Path(spec.source_ref),
                                composites=WebCompositeContext(None, "JE-3600A", REGION, spec.language, ValueError))
    data = spec.to_dict()
    data["metadata"].update(capture_following_lines=count,
                            source_fragment_sha256=soup.figure["data-source-fragment-sha256"])
    return component_flow_node(ComponentSpec.from_dict(data), carrier_flow=flow, root=True)


def callout_from(table, chapter):
    label_cell, body_cell = table_rows(table)[0]["children"]
    label = display_label(squash(plain(label_cell)))
    variant = L10N[LANGUAGE]["callout_variants"][label]
    body = [strip_styles(deepcopy(child)) for child in body_cell["children"]]
    body = [merge_text(child) for child in body]
    for item in walk({"children": body}, [], lambda n: n.get("kind") == "list_item"):
        if len(item.get("children", [])) == 1 and item["children"][0].get("kind") == "paragraph":
            item["children"] = item["children"][0]["children"]
    return shared_callout(label, body, variant=variant, language=LANGUAGE, source_ref=ref(chapter, variant))


def plain_table(item):
    table = strip_styles(deepcopy(walk(item, [], lambda n: n.get("kind") == "table")[0]))
    table.setdefault("presentation", {"html": {"attributes": {"class": "manual-table"}}})
    return node("group", [table], role="container",
                presentation={"html": {"attributes": {"class": "table-wrapper docutils container"}}})


def clean_markup(value: str) -> str:
    """Drop source-local classes and inline styles from a component's stored HTML."""
    soup = BeautifulSoup(value, "html.parser")
    for tag in soup.find_all(True):
        tag.attrs.pop("style", None)
        names = [name for name in tag.get("class", []) if not name.startswith("ht-")]
        if names:
            tag["class"] = names
        else:
            tag.attrs.pop("class", None)
    return str(soup)


def clean_component(component):
    item = deepcopy(component)
    item["carrier_flow"] = [strip_styles(child) for child in item.get("carrier_flow", [])]

    def visit(value):
        if isinstance(value, dict):
            return {k: (clean_markup(v) if isinstance(v, str) and k.endswith("html") else visit(v))
                    for k, v in value.items()}
        if isinstance(value, list):
            return [visit(v) for v in value]
        if isinstance(value, str) and "ht-" in value and "<" in value:
            return clean_markup(value)
        return value
    item["component_spec"]["slots"] = visit(item["component_spec"]["slots"])
    if not item["carrier_flow"]:
        item.pop("carrier_flow")
    return item


# Reviewed crops (percent of the art: left, top, right, bottom). Prose and tables the
# print sets in panels around the drawing come out as shared flow; the art keeps the
# drawing only, inset 2% so no partial print frame remains; the shared panel frames it.
CROPS = {
    "ja": {"energy-saving-p14": [2, 62, 98, 98], "usb-output-p13": [2, 2, 98, 60.5]},
    "zh": {},
}
CROPPED: dict[str, str] = {}
NOWRAP: dict[str, list[int]] = {}


# Reviewed per-card art boxes on each print's inbox panel (percent: left, top, right, bottom).
# One square-ish box per card, centred on its drawing, clear of the card frames.
INBOX = {
    "ja": {"inbox-p8": [[4, 28, 30.5, 67], [37.25, 28, 63.75, 67], [70.6, 28, 97.1, 67]]},
    "zh": {"inbox-p3": [[2.2, 16, 27.8, 61], [37.2, 16, 62.8, 61], [71.7, 16, 97.3, 61]]},
}


def inbox_cards(component, chapter):
    """The print's three drawn cards become the shared inbox component."""
    spec = component["component_spec"]
    reference = next(s["content"] for s in spec["slots"] if s["role"] == "reference_id")
    captions = next(s["content"] for s in spec["slots"] if s["role"] == "captions")
    labels = spec["metadata"]["base_art_layout"]["labels"]
    source = component["carrier_flow"][0]["source"]
    boxes = INBOX[LANGUAGE][reference]
    names, notes = ["" for _ in boxes], []
    for label, caption in sorted(zip(labels, captions, strict=True), key=lambda pair: pair[0]["rect"][1]):
        if re.fullmatch(r"[0-9]+", caption["text"]):
            continue  # the shared card draws its own number
        if label["rect"][1] > 80:  # notes set in the panel under the cards
            notes.append(node("paragraph", [text(caption["text"])]))
            continue
        centre = label["rect"][0] + label["rect"][2] / 2
        card = next(i for i, box in enumerate(boxes) if box[0] - 4 <= centre <= box[2] + 4)
        # A name the print breaks over two lines reads as one; Latin after CJK keeps a space.
        names[card] = (names[card] + " " + caption["text"]) if names[card] else caption["text"]
    cards = []
    for number, (box, name) in enumerate(zip(boxes, names, strict=True), start=1):
        cards.append({"image_ref": crop_svg(source, box, f"card-{number}"), "label": name, "alt": name})
    built = inbox_component_spec(accessibility_label=CURRENT_TITLE[0], cards=cards, tip_label="", tip_body="",
                                 require_tip=False, source_ref=ref(chapter, "inbox"), language=LANGUAGE)
    log("inbox", chapter=chapter, figure=reference, component="HB-SPECIAL-INBOX", cards=names, boxes=boxes,
        notes=len(notes),
        note="drawn card panel becomes the shared inbox cards; each card's art is cropped from the print")
    carrier = [node("table", [node("table_body", [node("table_row", [
        node("table_cell", [node("image", source=c["image_ref"], alt=c["alt"]), node("paragraph", [text(c["label"])])],
             header=False)
        for c in cards])])], presentation={"html": {"attributes": {"class": "manual-table"}}})]
    return [component_flow_node(built, carrier_flow=carrier, root=True), *notes]


# Reviewed App download panels: store badges and QR boxes on the print art (percent).
APP_DOWNLOAD = {
    "ja": {"app-download-p28": {"store": [0.5, 41, 20.2, 90.5], "qr": [60, 41.5, 75.3, 97.5]}},
    "zh": {},
}


def app_download(component, chapter):
    """Store copy + badges and QR copy + code become the shared App download columns."""
    spec = component["component_spec"]
    reference = next(s["content"] for s in spec["slots"] if s["role"] == "reference_id")
    captions = next(s["content"] for s in spec["slots"] if s["role"] == "captions")
    labels = spec["metadata"]["base_art_layout"]["labels"]
    if len(captions) != 2:
        raise ValueError(f"{chapter}: App download expects store and QR copy")
    ordered = [caption for _, caption in sorted(zip(labels, captions, strict=True), key=lambda pair: pair[0]["rect"][0])]
    source = component["carrier_flow"][0]["source"]
    boxes = APP_DOWNLOAD[LANGUAGE][reference]
    columns = [{"role": role, "html": html.escape(caption["text"], quote=False), "text": caption["text"]}
               for role, caption in zip(("store", "qr"), ordered, strict=True)]
    built = app_download_component_spec(
        accessibility_label=CURRENT_HEADING[0] or CURRENT_TITLE[0], columns=columns, source_art_ref=source,
        store_art_ref=crop_svg(source, boxes["store"], "store"), qr_art_ref=crop_svg(source, boxes["qr"], "qr"),
        source_ref=ref(chapter, "app-download"), language=LANGUAGE)
    carrier = [node("image", source=source, alt=CURRENT_HEADING[0] or CURRENT_TITLE[0]),
               *[node("paragraph", [text(column["text"])]) for column in columns]]
    log("app-download", chapter=chapter, figure=reference, component="HB-SPECIAL-APP", boxes=boxes,
        note="store and QR copy set beside drawn art become the shared App download columns")
    return component_flow_node(built, carrier_flow=carrier, root=True)


def app_qr_download(group, chapter):
    """Store copy beside one QR code becomes the shared App QR-only download."""
    lines = [p for p in walk(group, [], lambda n: n.get("kind") == "paragraph")]
    image = walk(group, [], lambda n: n.get("kind") == "image")[0]
    inline = []
    for line in lines:
        if inline:
            inline.append(node("line_break"))
        inline.append(text(squash(plain(line))))  # print indents are layout, not copy
    paragraph = node("paragraph", inline)
    rendered = flow_nodes_to_html([root(deepcopy(paragraph))])
    copy = {"html": re.sub(r"^<p>(.*)</p>$", r"\1", rendered.strip(), flags=re.S),
            "text": BeautifulSoup(rendered, "html.parser").get_text(" ", strip=True)}
    spec = app_qr_download_component_spec(label=CURRENT_HEADING[0] or CURRENT_TITLE[0], paragraph=copy,
                                          image_ref=image["source"], source_ref=ref(chapter, "app-qr-download"),
                                          language=LANGUAGE)
    log("app-qr-download", chapter=chapter, component="HB-SPECIAL-APP", lines=len(lines),
        note="store copy and QR code become the shared App QR-only download; print line indents dropped")
    return component_flow_node(spec, carrier_flow=[paragraph, node("image", source=image["source"],
                                                                   alt=image.get("alt", ""))], root=True)


def certificate(group, chapter):
    """The QC certificate: its heading and a plain shared table; the stamp lines read as one cell."""
    heading = next(c for c in group["children"] if c.get("kind") == "heading")
    table = walk(group, [], lambda n: n.get("kind") == "table")[0]
    rows = []
    for row in table_rows(table):
        cells = []
        for cell in row["children"]:
            value = " ".join(squash(plain(line)) for line in
                             walk(cell, [], lambda n: n.get("kind") == "group" and has(n, "ht-qc-line"))) \
                or squash(plain(cell))
            cells.append(node("table_cell", [node("paragraph", [text(value)])] if value else [], header=False,
                              **({"row_span": cell["row_span"]} if cell.get("row_span") else {})))
        rows.append(node("table_row", cells))
    log("certificate", chapter=chapter, component="table", note="QC certificate drawn with source CSS becomes a plain table")
    rest = [strip_styles(deepcopy(c)) for c in group["children"] if c is not heading and c is not table]
    return [strip_styles(deepcopy(heading)),
            node("table", [node("table_body", rows)], presentation={"html": {"attributes": {"class": "manual-table"}}}),
            *rest]


APP_PLUS = "assets/shared-app-plus.svg"


def app_inline_control(paragraph, chapter):
    """The App's add-device '+' drawn as an inline picture becomes the shared inline control."""
    flat = []
    for child in [strip_styles(deepcopy(c)) for c in paragraph["children"]]:
        flat.extend(child.get("children", [child]) if child.get("kind") == "inline_group" else [child])
    inline = [node("strong", [text("+")]) if c.get("kind") == "image" and c.get("source") == APP_PLUS else c
              for c in flat]
    carrier = node("paragraph", inline)
    rendered = flow_nodes_to_html([root(deepcopy(carrier))])
    spec = app_inline_control_component_spec(
        accessibility_label="+", paragraph_html=rendered,
        paragraph_text=BeautifulSoup(rendered, "html.parser").get_text(" ", strip=True),
        source_ref=ref(chapter, "app-inline-control"), language=LANGUAGE)
    log("app-inline-control", chapter=chapter, component="HB-SPECIAL-APP",
        note="add-device '+' picture becomes the shared inline control icon")
    return component_flow_node(spec, carrier_flow=[carrier], root=True)


def crop_svg(source: str, box, suffix: str = "crop") -> str:
    """Write a cropped copy of an SVG asset (viewBox only; every path unchanged)."""
    path = BASE / source
    data = path.read_text()
    match = re.search(r'<svg[^>]*\bviewBox="([0-9.\s-]+)"', data)
    x, y, width, height = (float(v) for v in match.group(1).split())
    left, top, right, bottom = box
    view = [x + width * left / 100, y + height * top / 100, width * (right - left) / 100, height * (bottom - top) / 100]
    head = data[:data.index(">", match.start()) + 1]
    new_head = re.sub(r'\bviewBox="[^"]*"', 'viewBox="%.5f %.5f %.5f %.5f"' % tuple(view), head)
    new_head = re.sub(r'\bwidth="[^"]*"', 'width="%.5f"' % view[2], new_head, count=1)
    new_head = re.sub(r'\bheight="[^"]*"', 'height="%.5f"' % view[3], new_head, count=1)
    name = f"{Path(source).stem}-{suffix}.svg"
    CROPPED["assets/" + name] = new_head + data[len(head):]
    return "assets/" + name


def recrop(rect, box):
    left, top, right, bottom = box
    return [(rect[0] - left) * 100 / (right - left), (rect[1] - top) * 100 / (bottom - top),
            rect[2] * 100 / (right - left), rect[3] * 100 / (bottom - top)]


def clean_figure(component, chapter):
    """Strip drawn overlays; lift tables out; merge prose cut into print lines."""
    spec = deepcopy(component["component_spec"])
    reference = next(s["content"] for s in spec["slots"] if s["role"] == "reference_id")
    image, block = component["carrier_flow"][0], component["carrier_flow"][1]
    layout = spec["metadata"]["base_art_layout"]
    rects = {label["line"]: label for label in layout["labels"]}
    after, kept, moved = [], [], []
    for index, line in enumerate(block["children"]):
        tables = walk(line, [], lambda n: n.get("kind") == "table")
        if tables:
            if reference in CROPS[LANGUAGE] and not has(tables[0], "ht-figure-callout-table"):
                moved.append((rects[index]["rect"][1], plain_table(line)))
                log("figure-table", chapter=chapter, figure=reference, component="table",
                    note="table drawn as a figure label becomes a shared table in its printed place")
                continue
            if has(tables[0], "ht-figure-callout-table"):
                after.append(callout_from(tables[0], chapter))
                log("figure-callout", chapter=chapter, figure=reference, component="HB-CALLOUT-STRIP",
                    note="ご注意 box drawn as a figure label becomes a shared callout after the figure")
            else:
                after.append(plain_table(line))
                log("figure-table", chapter=chapter, figure=reference, component="table",
                    note="table drawn as a figure label becomes a shared table after the figure")
            continue
        kept.append({"line": line, "rect": deepcopy(rects[index]), "size": line_size(line)})
    # Prose the print sets as consecutive full-width lines: one live label per paragraph.
    merged = []
    for item in kept:
        rect = item["rect"]["rect"]
        previous = merged[-1] if merged else None
        continues = bool(previous and previous["prose"] and "fill" not in item["rect"]
                         and abs(previous["rect"]["rect"][0] - rect[0]) < 3
                         and 0 <= rect[1] - (previous["rect"]["rect"][1] + previous["rect"]["rect"][3]) < 0.4 * rect[3])
        # A short last line of a paragraph continues the prose above it.
        prose = continues or (rect[2] >= 40 and "fill" not in item["rect"])
        if continues:
            prev_rect = previous["rect"]["rect"]
            bottom = rect[1] + rect[3]
            previous["rect"]["rect"] = [min(prev_rect[0], rect[0]), prev_rect[1],
                                        max(prev_rect[0] + prev_rect[2], rect[0] + rect[2]) - min(prev_rect[0], rect[0]),
                                        bottom - prev_rect[1]]
            previous["parts"].append(item["line"])
            previous["merged"] += 1
            continue
        merged.append({**item, "prose": prose, "parts": [item["line"]], "merged": 1})
    box = CROPS[LANGUAGE].get(reference)
    if box:
        staying = []
        for item in merged:
            if item["prose"]:
                inline = []
                for part in item["parts"]:
                    flat = []
                    for child in [strip_styles(deepcopy(c)) for c in part["children"]]:
                        flat.extend(child.get("children", [child]) if child.get("kind") == "inline_group" else [child])
                    if inline and flat and inline[-1].get("kind") == "text" and flat[0].get("kind") == "text":
                        inline[-1] = text(join_lines(inline[-1]["text"], flat[0]["text"]))
                        flat = flat[1:]
                    inline.extend(flat)
                moved.append((item["rect"]["rect"][1], node("paragraph", inline)))
                log("figure-prose-out", chapter=chapter, figure=reference, lines=item["merged"],
                    note="body prose set in a print panel becomes a paragraph outside the figure")
            else:
                item["rect"]["rect"] = recrop(item["rect"]["rect"], box)
                staying.append(item)
        merged = staying
    lines, captions, labels, sizes = [], [], [], {}
    for index, item in enumerate(merged):
        inline = []
        for part in item["parts"]:
            children = [strip_styles(deepcopy(c)) for c in part["children"]]
            flat = []
            for child in children:
                flat.extend(child.get("children", [child]) if child.get("kind") == "inline_group" else [child])
            if inline and flat and inline[-1].get("kind") == "text" and flat[0].get("kind") == "text":
                joined = join_lines(inline[-1]["text"], flat[0]["text"])
                inline[-1] = text(joined)
                flat = flat[1:]
            inline.extend(flat)
        lines.append(node("group", inline, role="container", presentation={"html": {"attributes": {"class": "line"}}}))
        rendered = markup(inline)
        captions.append({"html": rendered,
                         "text": BeautifulSoup(rendered, "html.parser").get_text(" ", strip=True)})
        label = {**item["rect"], "line": index}
        labels.append(label)
        if item["size"]:
            sizes[index] = item["size"]
        if item["merged"] > 1:
            log("figure-prose", chapter=chapter, figure=reference, lines=item["merged"],
                note="print lines of one paragraph become one live label")
    LABEL_SIZES[reference] = sizes
    # A label the print sets on one line stays on one line (live fonts run slightly wider).
    NOWRAP[reference] = [index for index, item in enumerate(merged)
                         if item["merged"] == 1 and not item["prose"] and "fill" not in item["rect"]]
    layout["labels"] = labels
    for slot in spec["slots"]:
        if slot["role"] == "captions":
            slot["content"] = captions
    spec["metadata"]["capture_following_lines"] = len(lines)
    image = strip_styles(deepcopy(image))
    if box:
        new_art = crop_svg(image["source"], box)
        image["source"] = new_art
        for asset in spec["assets"]:
            if asset["asset_ref"] == component["carrier_flow"][0]["source"]:
                asset["asset_ref"] = new_art
        layout["art_sha256"] = hashlib.sha256(CROPPED[new_art].encode()).hexdigest()
        layout["preserve_frame"] = False
        log("figure-crop", chapter=chapter, figure=reference, box=box, asset=new_art)
    rebuilt = reference_flow(ComponentSpec.from_dict(spec),
                             [image,
                              node("group", lines, role="container",
                                   presentation={"html": {"attributes": {"class": "line-block"}}})])
    above = [flow for y, flow in sorted(moved, key=lambda m: m[0]) if box and y < box[1]]
    below = [flow for y, flow in sorted(moved, key=lambda m: m[0]) if not box or y >= box[1]]
    return [*above, rebuilt, *below, *after]


# --- chapter walk --------------------------------------------------------------------------
def table_of(item):
    tables = walk(item, [], lambda n: n.get("kind") == "table")
    return tables[0] if len(tables) == 1 else None


def heading_of(item):
    if item.get("kind") == "heading":
        return item
    if item.get("kind") == "group":
        children = [c for c in item.get("children", []) if c.get("kind") != "text"]
        if len(children) == 1 and children[0].get("kind") == "heading":
            return children[0]
    return None


# Inline pictograms whose vector extraction lost the drawing reuse this edition's shared LCD icon.
INLINE_REUSE = {
    "ja": {"assets/native-inline-parallel-connected-p18.svg": "assets/lcd-parallel.png"},
    "zh": {},
}


def reuse_inline(item, chapter):
    for image in walk(item, [], lambda n: n.get("kind") == "image"):
        replacement = INLINE_REUSE[LANGUAGE].get(image.get("source"))
        if replacement:
            log("inline-icon-reuse", chapter=chapter, source=image["source"], asset=replacement,
                note="extracted vector covers the glyph with a filled box; the LCD table's icon is reused")
            image["source"] = replacement
    return item


CURRENT_TITLE = [""]
CURRENT_HEADING = [""]


def transform(chapter, assets):
    CURRENT_TITLE[0] = chapter.get("title") or chapter["id"]
    nodes = chapter["nodes"]
    out = []
    index = 0
    while index < len(nodes):
        item = nodes[index]
        index += 1
        table = table_of(item) if item.get("kind") == "group" else None
        if item.get("kind") == "group" and has(item, "ht-symbol-pair"):
            out.append(symbol_pair(item, chapter["id"], assets))
            continue
        if item.get("kind") == "heading" or heading_of(item) is not None:
            CURRENT_HEADING[0] = squash(plain(heading_of(item) or item))
        if item.get("kind") == "group" and has(item, "ht-native-app-download"):
            out.append(app_qr_download(item, chapter["id"]))
            continue
        if item.get("kind") == "group" and has(item, "ht-certificate"):
            out.extend(certificate(item, chapter["id"]))
            continue
        if table is not None and has(table, "ht-signal-table"):
            out.append(signal_table(table, chapter["id"]))
            continue
        if table is not None and has(table, "ht-safety-table"):
            out.append(safety_table(table, chapter["id"], assets))
            continue
        if table is not None and has(table, "ht-lcd-icons"):
            out.append(lcd_icon_table(table, chapter["id"], assets))
            continue
        if table is not None and has(table, "ht-key-combinations"):
            out.append(key_table(table, chapter["id"]))
            continue
        if table is not None and has(table, "ht-troubleshooting"):
            out.append(troubleshooting_table(table, chapter["id"]))
            continue
        if item.get("kind") == "group" and has(item, "ht-lcd-pair"):
            figure = [c for c in item["children"] if has(c, "ht-figure")][0]
            artwork = image_in(figure)
            modes = walk(item, [], lambda n: n.get("kind") == "table" and has(n, "ht-lcd-modes"))[0]
            out.append(lcd_mode_table(modes, artwork, chapter["id"], assets))
            continue
        # A spec group title (heading in a prose group) followed by its grid.
        title = heading_of(item)
        if title is not None and index < len(nodes):
            following = table_of(nodes[index]) if nodes[index].get("kind") == "group" else None
            if following is not None and has(following, "ht-spec-grid"):
                out.append(spec_table(following, squash(plain(title)), chapter["id"]))
                index += 1
                continue
        out.append(item)
    final = []
    CURRENT_HEADING[0] = ""
    for item in unwrap(out):
        if item.get("kind") == "heading":
            CURRENT_HEADING[0] = squash(plain(item))
        if item.get("kind") == "component" and item["component_spec"]["component_id"] == "HB-SPECIAL-REFERENCE-FIGURE" \
                and next(s["content"] for s in item["component_spec"]["slots"]
                         if s["role"] == "reference_id") in INBOX[LANGUAGE]:
            final.extend(inbox_cards(item, chapter["id"]))
        elif item.get("kind") == "component" and item["component_spec"]["component_id"] == "HB-SPECIAL-REFERENCE-FIGURE" \
                and next(s["content"] for s in item["component_spec"]["slots"]
                         if s["role"] == "reference_id") in APP_DOWNLOAD[LANGUAGE]:
            final.extend(app_download(flow, chapter["id"]) if flow.get("kind") == "component"
                         and flow["component_spec"]["component_id"] == "HB-SPECIAL-REFERENCE-FIGURE" else flow
                         for flow in clean_figure(item, chapter["id"]))
        elif item.get("kind") == "component" and item["component_spec"]["component_id"] == "HB-SPECIAL-REFERENCE-FIGURE" \
                and "base_art_layout" in item["component_spec"]["metadata"]:
            final.extend(clean_figure(item, chapter["id"]))
        elif item.get("kind") == "paragraph" and any(
                n.get("source") == APP_PLUS for n in walk(item, [], lambda n: n.get("kind") == "image")):
            final.append(app_inline_control(item, chapter["id"]))
        elif item.get("kind") == "component":
            final.append(clean_component(item))
        else:
            final.append(reuse_inline(strip_styles(item), chapter["id"]))
    for item in final:
        nested = walk(item, [], lambda n, top=item: n is not top and "schema_version" in n)
        for child in nested:
            child.pop("schema_version")
        item["schema_version"] = "manual-flow/v2"
    chapter["nodes"] = final
    return chapter


def referenced_assets(value) -> set[str]:
    return set(re.findall(r"assets/[A-Za-z0-9_.\-]+", json.dumps(value, ensure_ascii=False)))


def write_stylesheet():
    """Source-local geometry only: each figure's printed label size. No colour, border or fill."""
    rules = ["/* JE-3600A shared-component edition: source geometry only.",
             "   Shared Web theme owns every table, callout, card, label and figure style.",
             "   Each figure keeps the print's label size (container-relative), nothing else. */"]
    # Shared contact pictograms sit inline in their paragraph at text size (geometry only).
    rules.append('#furo-main-content p > img[src*="shared-contact-"] '
                 "{ width: 1.25em; height: 1.25em; margin: 0 0.4em 0 0; vertical-align: -0.25em; }")
    # The brand QR in the manufacturer footer keeps a print-like size.
    rules.append('#furo-main-content img[src*="manufacturer-qr"] { width: 7rem !important; height: auto !important; }')
    # Print pictograms set inside a sentence keep text height.
    rules.append('#furo-main-content :is(p, li) > img:not([src*="shared-contact-"]) '
                 "{ width: auto; height: 1.3em; margin: 0 0.15em; vertical-align: -0.3em; }")
    for reference, sizes in sorted(LABEL_SIZES.items()):
        if not sizes:
            continue
        common = max(set(sizes.values()), key=list(sizes.values()).count)
        selector = f'#furo-main-content .hb-reference-figure[data-reference-id="{reference}"]'
        rules.append(f"{selector} .hb-reference-live-label {{ font-size: {common:.4f}cqw; }}")
        for line in NOWRAP.get(reference, []):
            rules.append(f'{selector} .hb-reference-live-label[data-source-line="{line}"] {{ white-space: nowrap; }}')
        for line, size in sorted(sizes.items()):
            if abs(size - common) > 1e-4:
                rules.append(f'{selector} .hb-reference-live-label[data-source-line="{line}"] '
                             f"{{ font-size: {size:.4f}cqw; }}")
    (HERE / "source/presentation.css").write_text("\n".join(rules) + "\n")


def derive():
    content = json.loads((BASE / f"source/{LANGUAGE}/content.json").read_text())
    assets: set[str] = set()
    chapters = [transform(deepcopy(chapter), assets) for chapter in content["chapters"]]
    result = {**content, "chapters": chapters}
    dump(HERE / f"source/{LANGUAGE}/content.json", result)
    dump(HERE / f"source/{LANGUAGE}/shared_components.json", {"base_edition": BASE.name, "changes": LOG})
    target = HERE / "assets"
    if target.exists():
        shutil.rmtree(target)
    target.mkdir()
    for ref in sorted(referenced_assets(result)):
        if ref in CROPPED:
            (target / Path(ref).name).write_text(CROPPED[ref])
        else:
            shutil.copy2(BASE / ref, target / Path(ref).name)
    write_stylesheet()
    print(json.dumps({"edition": HERE.name, "changes": len(LOG),
                      "assets": len(list(target.iterdir()))}, ensure_ascii=False))


if __name__ == "__main__":
    derive()
