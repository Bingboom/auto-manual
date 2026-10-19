"""Positioned native-Japanese intake into existing shared components, with a line ledger."""

from pathlib import Path
from html import escape
import hashlib
import json
import re
import shutil
import sys

PACKAGE = Path(__file__).resolve().parents[1]
REPO = next(p for p in PACKAGE.parents if (p / "build.py").is_file())
sys.path.insert(0, str(REPO))
from tools.web.frozen_ai_flow import (
    node,
    paragraph,
    text,
    heading,
    root,
    callout,
    cell,
    table,
)  # noqa: E402
from tools.manual_ir.components import component_flow_node  # noqa: E402
from tools.component_specs.manual_tables import (
    symbol_signal_component_spec,
    symbol_icon_component_spec,
    lcd_icon_component_spec,
    troubleshooting_component_spec,
)  # noqa: E402
from tools.component_specs.inbox import inbox_component_spec  # noqa: E402
from tools.component_specs.lcd_mode import lcd_mode_component_spec  # noqa: E402
from tools.component_specs.auto_resume import auto_resume_component_spec  # noqa: E402
from tools.component_specs.key_combinations import key_combinations_component_spec  # noqa: E402
from tools.component_specs.warranty import (
    warranty_lead_component_spec,
    warranty_section_component_spec,
)  # noqa: E402
from tools.component_specs.app import (
    app_inline_control_component_spec,
    app_download_component_spec,
)  # noqa: E402
from tools.web.frozen_pdf_app import artwork_node  # noqa: E402
from tools.web.frozen_ai_table_components import specification_flow  # noqa: E402


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def joined(lines):
    result = ""
    for line in lines:
        part = line["text"].strip()
        if (
            result
            and part
            and re.search(r"[A-Za-z0-9]$", result)
            and re.match(r"[A-Za-z0-9]", part)
        ):
            result += " "
        result += part
    return re.sub(r"[ \t　]+", " ", result).strip()


class Intake:
    def __init__(self):
        self.pages = {
            p["page"]: p
            for p in json.loads((PACKAGE / "source/native-pages.json").read_text())
        }
        self.used = {}
        self.chapters = []
        self.body = []
        self.reuse = []
        self.figures = json.loads(
            (PACKAGE / "source/extracted-artwork.json").read_text()
        )
        self.setup_shared_assets()
        for p, data in self.pages.items():
            for row in data["lines"]:
                if p not in range(3, 27):
                    self.mark(p, row, "print-only")
                elif row["origin"][1] >= 500:
                    self.mark(p, row, "printed-folio")
        # Only dense diagrams, screen UI, and product silk remain embedded.
        keep_modes = {
            "dense-labeled-diagram",
            "numbered-display-map",
            "display-art",
            "store-badges",
            "qr",
            "ui-screenshot",
        }
        for f in self.figures:
            p = f["page"]
            for row in self.select(p, f["crop"]):
                if (
                    f["mode"] in keep_modes
                    or row["size"] <= 4
                    or row["text"].strip() in f.get("keep_text", [])
                ):
                    if (p, row["id"]) not in self.used:
                        self.mark(p, row, "embedded-art/" + f["key"])

    def mark(self, p, row, role):
        key = (p, row["id"])
        if key in self.used:
            raise ValueError(
                f"duplicate source selection {key}: {self.used[key]['role']}, {role}"
            )
        self.used[key] = {"page": p, **row, "role": role}

    def select(self, p, box, *, available=False):
        x0, y0, x1, y1 = box
        return sorted(
            [
                r
                for r in self.pages[p]["lines"]
                if x0 <= r["origin"][0] < x1
                and y0 <= r["origin"][1] < y1
                and (not available or (p, r["id"]) not in self.used)
            ],
            key=lambda r: (round(r["origin"][1], 1), r["origin"][0]),
        )

    def take(self, p, box=None, ids=None, role="live-copy"):
        rows = (
            self.select(p, box)
            if box
            else [r for r in self.pages[p]["lines"] if r["id"] in ids]
        )
        if not rows:
            raise ValueError(f"empty selection {p} {box} {ids}")
        rows.sort(key=lambda r: (round(r["origin"][1], 1), r["origin"][0]))
        for r in rows:
            self.mark(p, r, role)
        return joined(rows)

    def ref(self, name):
        return "native-pdf/" + self.chapters[-1]["id"] + "/" + name

    def add(self, *nodes):
        self.body.extend(root(n) for n in nodes)

    def chapter(self, identity, p, line):
        title = self.take(p, ids=[line])
        self.body = []
        self.chapters.append({"id": identity, "title": title, "nodes": self.body})
        self.add(heading(title, level=1, anchor=identity))

    def subtitle(self, p, box=None, ids=None):
        value = self.take(p, box=box, ids=ids)
        self.add(heading(value.lstrip("■ ").strip(), level=2))
        return value

    def flow(self, p, box):
        rows = self.select(p, box, available=True)
        groups = []
        current = []
        for r in rows:
            value = r["text"].strip()
            is_head = r["size"] >= 7.8 or value.startswith("■")
            is_bullet = bool(re.match(r"^[•・◦]", value))
            if current and (
                is_head or is_bullet or r["origin"][1] - current[-1]["origin"][1] > 16
            ):
                groups.append(current)
                current = []
            current.append(r)
            if is_head:
                groups.append(current)
                current = []
        if current:
            groups.append(current)
        for group in groups:
            for r in group:
                self.mark(p, r, "live-copy")
            value = joined(group)
            if group[0]["size"] >= 7.8 or value.startswith("■"):
                self.add(heading(value.lstrip("■ ").strip(), level=2))
            elif re.match(r"^[•・◦]", value):
                item = node("list_item", [paragraph(value[1:].strip())])
                # Adjacent bullet paragraphs share one semantic list.
                if (
                    self.body
                    and self.body[-1].get("kind") == "list"
                    and not self.body[-1].get("ordered")
                ):
                    self.body[-1]["children"].append(item)
                else:
                    self.add(node("list", [item], ordered=False))
            else:
                self.add(paragraph(value))

    def notice(self, p, box, *, label=None, bullet_ids=()):
        rows = self.select(p, box, available=True)
        label_rows = [
            r
            for r in rows
            if r["text"].strip() in {"ご注意", "注意", "説明", "備考", "警告", "ヒント"}
        ]
        if label_rows:
            label = label or label_rows[0]["text"].strip()
            for r in label_rows:
                self.mark(p, r, "live-copy/callout-label")
            rows = [r for r in rows if r not in label_rows]
        if not label or not rows:
            raise ValueError(f"incomplete callout on {p}")
        body = []
        if bullet_ids:
            lead = [r for r in rows if r["id"] not in bullet_ids]
            if lead:
                body.append(paragraph(joined(lead)))
            body.append(
                node(
                    "list",
                    [
                        node("list_item", [paragraph(r["text"].strip())])
                        for r in rows
                        if r["id"] in bullet_ids
                    ],
                    ordered=False,
                )
            )
        else:
            body.append(paragraph(joined(rows)))
        for r in rows:
            self.mark(p, r, "live-copy/callout-body")
        variant = {
            "警告": "warning",
            "注意": "caution",
            "ご注意": "caution",
            "ヒント": "tip",
        }.get(label, "note")
        self.add(
            callout(
                label,
                body,
                variant=variant,
                language="ja",
                source_ref=self.ref(f"page-{p}-notice-{len(self.body)}"),
            )
        )

    def comp(self, spec):
        carrier = None
        if spec.component_id == "HB-SPECIAL-INBOX":
            cards = spec.slot("cards").content
            cells = []
            for card, asset in zip(cards, spec.assets, strict=True):
                cells.append(
                    node(
                        "table_cell",
                        [
                            node("image", source=asset.asset_ref, alt=card["alt"]),
                            paragraph(card["label"]),
                        ],
                        header=False,
                    )
                )
            carrier = [table([cells])]
        elif spec.component_id == "HB-TABLE-KEY-COMBINATIONS":

            def styled(kind, children, css, **fields):
                return node(
                    kind,
                    children,
                    presentation={"html": {"attributes": {"class": css}}},
                    **fields,
                )

            body_rows = []
            for buttons, duration, feature in spec.slot("rows").content:
                names = buttons.split(" + ")
                parts = []
                for i, name in enumerate(names):
                    if i:
                        parts.append(
                            styled("inline_group", [text("+")], "hb-key-button-plus")
                        )
                    parts.append(
                        styled(
                            "inline_group",
                            [
                                node("image", source=self.buttons[name], alt=""),
                                node("strong", [text(name)]),
                            ],
                            "hb-key-button",
                        )
                    )
                pair = styled("inline_group", parts, "hb-key-button-pair")
                button_cell = node("table_cell", [pair], header=False)
                duration_cell = node(
                    "table_cell",
                    [styled("paragraph", [text(duration)], "hb-key-duration")],
                    header=False,
                )
                body_rows.append(
                    node("table_row", [button_cell, duration_cell, cell(feature)])
                )
            carrier = [
                node(
                    "table",
                    [
                        node(
                            "table_head",
                            [
                                node(
                                    "table_row",
                                    [
                                        cell(v, header=True)
                                        for v in spec.slot("headers").content
                                    ],
                                )
                            ],
                        ),
                        node("table_body", body_rows),
                    ],
                    presentation={
                        "html": {"attributes": {"class": "hb-key-combination-table"}}
                    },
                )
            ]
        elif spec.component_id == "HB-SPECIAL-APP" and spec.variant == "download":
            art = next(a.asset_ref for a in spec.assets if a.role == "source_art")
            carrier = [
                node(
                    "image",
                    source=art,
                    alt=str(spec.slot("accessibility_label").content),
                ),
                *[paragraph(c["text"]) for c in spec.slot("columns").content],
            ]
        self.add(
            component_flow_node(spec, carrier_flow=carrier, root=True)
            if carrier
            else component_flow_node(spec, root=True)
        )

    def picture(self, key, label, *, semantic=""):
        art = next(f for f in self.figures if f["key"] == key)
        # Dense overview annotations already appear once, inside the figure.
        # Their source copy is kept in alt text for assistive technology.
        embedded = [
            r["text"] for r in self.used.values() if r["role"] == "embedded-art/" + key
        ]
        alt = label + (
            ": " + " ".join(embedded)
            if embedded and art["mode"] == "dense-labeled-diagram"
            else ""
        )
        self.add(
            artwork_node(
                art["path"], key, "ja", self.ref("art/" + key), accessibility_label=alt
            )
        )

    def reuse_asset(self, relative, name, reason):
        source = REPO / relative
        if not source.is_file():
            raise ValueError("missing shared asset " + relative)
        dest = PACKAGE / "assets" / name
        shutil.copyfile(source, dest)
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        self.reuse.append(
            {
                "path": "assets/" + name,
                "sha256": digest,
                "source_path": relative,
                "decision": "reuse unchanged",
                "reason": reason,
                "background": "preserve approved source bytes",
            }
        )
        return "assets/" + name

    def setup_shared_assets(self):
        self.symbol = {}
        base = "docs/renderers/web/assets/shared/symbols/native-v1/"
        keys = [
            "warning_triangle",
            "read_manual",
            "no_open_flame",
            "keep_away_from_children",
            "do_not_dismantle",
            "unplug",
            "no_wet_hands",
            "keep_dry",
            "mandatory",
            "prohibited",
            "battery_recycle",
            "weee",
        ]
        for key in keys:
            self.symbol[key] = self.reuse_asset(
                base + "h1-jp-" + key + ".svg",
                "symbol-" + key + ".svg",
                "Shared Japanese pictogram variant matches the source role and silhouette; no language recrop",
            )
        self.buttons = {}
        for name, filename in [
            ("主電源ボタン", "power.svg"),
            ("AC出力ボタン", "ac.svg"),
            ("DC/USB出力ボタン", "dc_usb.svg"),
            ("ライトボタン", "led.svg"),
        ]:
            self.buttons[name] = self.reuse_asset(
                "docs/renderers/web/assets/shared/buttons/" + filename,
                "button-" + filename,
                "Same button face and fixed product marking; reuse shared transparent SVG unchanged",
            )
        reference = (
            REPO
            / "manual_sources/JE-1000F/JP/ja/git-20260930-d88b32fe-jp-reviewed/web/ja/assets"
        )
        self.lcd = {}
        mapping = [*range(1, 18), 19, 18, 20, 22, 23, 24, 25, 26, 27]
        for no, old in enumerate(mapping, 1):
            path = next((reference / "shared-lcd").glob(str(old) + "_*.png"))
            self.lcd[no] = self.reuse_asset(
                str(path.relative_to(REPO)),
                f"lcd-{no:02}.png",
                "Same LCD function; map semantic meaning independently from printed numbering",
            )
        self.cable = self.reuse_asset(
            str((reference / "inbox-ac-cable.svg").relative_to(REPO)),
            "inbox-ac-cable.svg",
            "Same Japanese AC cable accessory and drawing",
        )
        self.documents = self.reuse_asset(
            str((reference / "inbox-documents.svg").relative_to(REPO)),
            "inbox-documents.svg",
            "Same generic document-pack drawing; external caption is native Japanese",
        )

    def symbol_panels(self, p, title, groups):
        refs = []
        panels = []
        for panel in groups:
            result = []
            for key, ids in panel:
                value = self.take(p, ids=ids)
                i = len(refs)
                refs.append(self.symbol[key])
                result.append(
                    {
                        "asset_index": i,
                        "icon_alt": value,
                        "meaning_html": escape(value),
                        "meaning_text": value,
                    }
                )
            panels.append(result)
        self.comp(
            symbol_icon_component_spec(
                accessibility_label=title,
                headers=[
                    {"content_html": v, "content_text": v}
                    for v in ["記号", "意味", "記号", "意味"]
                ],
                panels=panels,
                icon_refs=refs,
                source_ref=self.ref("symbols-" + str(p) + "-" + str(len(self.body))),
                language="ja",
            )
        )

    def build(self):
        self.chapter("safety", 3, "18:0")
        self.flow(3, [20, 55, 345, 78])
        self.subtitle(3, ids=["21:0"])
        self.flow(3, [20, 105, 345, 139])
        rows = []
        for label_ids, body_ids in [
            (["16:0"], ["12:0", "13:0"]),
            (["17:0"], ["14:0", "15:0"]),
            (["22:0"], ["24:0", "25:0", "26:0"]),
            (["23:0"], ["27:0"]),
        ]:
            label = self.take(3, ids=label_ids)
            value = self.take(3, ids=body_ids)
            rows.append(
                {
                    "label": label,
                    "show_icon": label in {"警告", "注意"},
                    "meaning_text": value,
                    "meaning_html": escape(value),
                }
            )
        self.comp(
            symbol_signal_component_spec(
                accessibility_label="絵表示について",
                headers=[
                    {"content_text": v, "content_html": v} for v in ["表示", "意味"]
                ],
                rows=rows,
                source_ref=self.ref("signals"),
                language="ja",
            )
        )
        self.subtitle(3, ids=["20:0"])
        self.symbol_panels(
            3,
            "絵表示の説明",
            [
                [
                    ("warning_triangle", ["4:0", "4:1", "4:2"]),
                    ("read_manual", ["5:0", "5:1"]),
                    ("no_open_flame", ["6:0", "6:1"]),
                    ("keep_away_from_children", ["7:0", "7:1"]),
                    ("do_not_dismantle", ["8:0", "8:1"]),
                ],
                [
                    ("unplug", ["0:0", "0:1"]),
                    ("no_wet_hands", ["3:0", "3:1"]),
                    ("keep_dry", ["9:0"]),
                    ("mandatory", ["1:0"]),
                    ("prohibited", ["2:0"]),
                ],
            ],
        )
        self.symbol_panels(
            4,
            "リサイクルについて",
            [
                [("battery_recycle", ["5:0", *[f"3:{i}" for i in range(7)]])],
                [("weee", [f"4:{i}" for i in range(11)])],
            ],
        )
        self.notice(4, [65, 155, 345, 220], label="説明")
        self.subtitle(4, ids=["7:0"])
        self.symbol_panels(
            4,
            "警告",
            [
                [
                    ("prohibited", [f"0:{i}" for i in range(5)]),
                    ("prohibited", [f"1:{i}" for i in range(4)]),
                    ("keep_dry", [f"2:{i}" for i in range(3)]),
                    ("no_wet_hands", [f"9:{i}" for i in range(3)]),
                ],
                [
                    ("prohibited", [f"10:{i}" for i in range(3)]),
                    ("prohibited", [f"11:{i}" for i in range(3)]),
                    ("mandatory", [f"12:{i}" for i in range(4)]),
                    ("mandatory", [f"6:{i}" for i in range(5)]),
                ],
            ],
        )
        self.subtitle(5, ids=["14:0"])
        self.notice(
            5,
            [65, 53, 345, 180],
            label="警告",
            bullet_ids=("17:0", "17:1", "17:2", "18:0", "18:1"),
        )
        self.flow(5, [65, 185, 345, 280])
        self.subtitle(5, ids=["15:0"])
        self.flow(5, [65, 312, 345, 497])

        self.chapter("usage-notes", 6, "27:0")
        self.flow(6, [25, 68, 345, 175])
        self.notice(6, [50, 185, 345, 237])
        self.flow(6, [25, 250, 345, 498])
        self.flow(7, [25, 25, 345, 270])
        self.chapter("disclaimer", 7, "6:0")
        self.flow(7, [25, 320, 345, 498])

        self.chapter("in-the-box", 8, "3:0")
        labels = [
            self.take(8, ids=["6:1"]),
            self.take(8, ids=["6:0"]),
            self.take(8, ids=["45:0"]),
        ]
        self.take(8, ids=["5:0", "5:1", "10:0"], role="printed-card-number")
        self.comp(
            inbox_component_spec(
                accessibility_label="同梱品",
                cards=[
                    {"image_ref": "assets/inbox-unit.png", "label": labels[0]},
                    {"image_ref": self.cable, "label": labels[1]},
                    {"image_ref": self.documents, "label": labels[2]},
                ],
                tip_label="",
                tip_body="",
                require_tip=False,
                source_ref=self.ref("cards"),
                language="ja",
            )
        )
        self.flow(8, [25, 190, 345, 275])
        self.chapter("product-overview", 8, "1:0")
        self.subtitle(8, ids=["0:0"])
        self.picture("overview-front", "各部の名称：正面")
        self.subtitle(9, ids=["1:0"])
        self.picture("overview-right", "各部の名称：右側面")
        self.chapter("lcd-display", 9, "2:0")
        self.picture("lcd-map", "液晶画面：1–25の表示位置")
        lcd_rows = []
        for p, edges in [
            (10, [25, 61, 87, 132, 187, 239, 331, 371, 395, 415, 438, 455, 474, 499]),
            (11, [26, 60, 115, 155, 185, 217, 248, 284, 320, 352, 385, 416, 446, 498]),
        ]:
            for y0, y1 in zip(edges, edges[1:], strict=False):
                idx = len(lcd_rows) + 1
                if p == 10:
                    number = self.take(p, [25, y0, 50, y1])
                else:
                    number_ids = [
                        "27:0",
                        "28:0",
                        "29:0",
                        "30:0",
                        "31:0",
                        "32:0",
                        "33:0",
                        "37:0",
                        "34:0",
                        None,
                        "35:0",
                        "36:0",
                        "15:2",
                    ]
                    native_id = number_ids[idx - 14]
                    number = self.take(p, ids=[native_id]) if native_id else "22"
                label = self.take(p, [80, y0, 166, y1])
                value = self.take(p, [166, y0, 345, y1])
                lcd_rows.append(
                    {
                        "asset_index": idx - 1,
                        "icon_alt": label,
                        "number_text": number,
                        "number_html": escape(number),
                        "name_text": label,
                        "name_html": escape(label),
                        "description_text": value,
                        "description_html": escape(value),
                    }
                )
        assert len(lcd_rows) == 26
        self.comp(
            lcd_icon_component_spec(
                accessibility_label="液晶画面",
                rows=lcd_rows,
                icon_refs=[self.lcd[i] for i in range(1, 27)],
                source_ref=self.ref("catalog"),
                language="ja",
            )
        )

        self.chapter("operations", 12, "2:0")
        self.subtitle(12, ids=["0:0"])
        self.picture("power-operation", "主電源ボタン")
        self.flow(12, [260, 95, 345, 165])
        self.flow(12, [160, 175, 345, 215])
        self.flow(12, [40, 228, 345, 252])
        self.subtitle(12, ids=["1:0"])
        self.flow(12, [30, 305, 345, 323])
        self.picture("ac-operation", "AC出力")
        self.flow(12, [285, 337, 345, 385])
        self.subtitle(13, ids=["5:0"])
        self.flow(13, [40, 52, 345, 110])
        self.take(13, ids=["3:0", "3:1"], role="printed-frequency-label")
        self.picture("frequency-displays", "50Hz / 60Hz")
        self.subtitle(13, ids=["0:0"])
        self.flow(13, [35, 242, 345, 257])
        self.picture("usb-operation", "USB / カーポート出力")
        self.flow(13, [293, 256, 345, 305])
        self.notice(13, [30, 414, 345, 498])
        self.flow(14, [25, 25, 345, 70])
        self.notice(14, [25, 73, 345, 124])
        self.subtitle(14, ids=["3:0"])
        self.flow(14, [40, 157, 345, 209])
        energy = table(
            [
                [cell(self.take(14, ids=[f"16:{i}"]), header=True) for i in [1, 2, 0]],
                [
                    cell(self.take(14, ids=["17:0"])),
                    cell(self.take(14, ids=["17:1"])),
                    cell(self.take(14, ids=["19:0"]), row_span=2),
                ],
                [cell(self.take(14, ids=["18:0"])), cell(self.take(14, ids=["18:1"]))],
            ]
        )
        self.add(
            node(
                "group",
                [energy],
                role="container",
                presentation={
                    "html": {
                        "attributes": {"class": "table-wrapper docutils container"}
                    }
                },
            )
        )
        self.flow(14, [40, 285, 345, 345])
        self.flow(14, [175, 400, 345, 465])
        self.notice(14, [25, 475, 345, 498])
        self.subtitle(15, ids=["1:0"])
        self.flow(15, [25, 43, 345, 57])
        heads = [self.take(15, ids=["31:0"]), self.take(15, ids=["31:1"])]
        conditions = [
            [
                self.take(15, ids=["32:0"]),
                self.take(15, ids=["34:0", "34:1"]),
                self.take(15, ids=["33:0"]),
            ],
            [self.take(15, ids=[f"{i}:0"]) for i in [35, 37, 38, 36]],
        ]
        self.comp(
            auto_resume_component_spec(
                headers=heads,
                conditions=conditions,
                source_ref=self.ref("auto-resume"),
                language="ja",
            )
        )
        self.subtitle(15, ids=["4:0"])
        self.flow(15, [40, 158, 345, 185])
        self.picture("led-operation", "LEDライト")
        self.flow(15, [210, 194, 345, 273])
        self.subtitle(15, ids=["3:0"])
        groups = []
        for state_id, action_ids, description_ids in [
            (
                "5:0",
                ["16:0", "8:0", "12:0"],
                [["13:0", "13:1"], ["14:0"], ["15:0", "15:1"]],
            ),
            (
                "6:0",
                ["11:0", "10:0", "9:0"],
                [["17:0", "17:1"], ["18:0"], ["19:0", "19:1", "19:2"]],
            ),
        ]:
            state = self.take(15, ids=[state_id])
            actions = []
            for aid, dids in zip(action_ids, description_ids, strict=True):
                a = self.take(15, ids=[aid])
                v = self.take(15, ids=dids)
                actions.append(
                    {
                        "action_text": a,
                        "action_html": escape(a),
                        "description_text": v,
                        "description_html": escape(v),
                    }
                )
            groups.append(
                {"state_text": state, "state_html": escape(state), "actions": actions}
            )
        self.comp(
            lcd_mode_component_spec(
                accessibility_label="LCDスクリーン",
                groups=groups,
                artwork_ref="assets/lcd-operation.png",
                source_ref=self.ref("lcd-mode"),
                language="ja",
            )
        )
        self.flow(15, [25, 440, 345, 455])
        self.subtitle(16, ids=["3:0"])
        key_headers = [self.take(16, ids=[f"15:{i}"]) for i in range(3)]
        key_rows = []
        for btn, seconds, hold, feature in [
            (["5:0", "5:1"], ["4:0"], ["7:0"], ["10:0"]),
            (["18:0", "21:0"], ["17:0"], ["19:0"], ["20:0"]),
            (["16:0", "6:0"], ["8:0"], ["9:0"], ["11:0"]),
            (["22:0", "22:1"], ["12:0"], ["13:0"], ["14:0", "14:1"]),
        ]:
            buttons = " + ".join(self.take(16, ids=[v]) for v in btn)
            sec = self.take(16, ids=seconds)
            duration = self.take(16, ids=hold)
            key_rows.append(
                [buttons, sec + " — " + duration, self.take(16, ids=feature)]
            )
        self.comp(
            key_combinations_component_spec(
                headers=key_headers,
                rows=key_rows,
                source_ref=self.ref("shortcuts"),
                language="ja",
            )
        )
        self.take(16, ids=["23:0"], role="fixed-button-marking")
        self.chapter("ups", 16, "1:0")
        self.picture("ups", "UPS接続")
        self.flow(16, [145, 420, 345, 452])
        self.flow(17, [25, 25, 345, 224])
        self.chapter("charging", 17, "18:0")
        self.flow(17, [20, 265, 345, 309])
        self.notice(17, [25, 318, 345, 354])
        self.notice(17, [25, 368, 345, 414])
        self.subtitle(17, ids=["17:0"])
        self.flow(17, [20, 440, 345, 492])
        self.picture("ac-charge", "AC充電ケーブル")
        self.flow(18, [170, 128, 345, 145])
        self.notice(18, [25, 175, 345, 211])
        self.flow(18, [25, 229, 345, 295])
        self.subtitle(18, ids=["1:0"])
        self.flow(18, [25, 323, 345, 498])
        self.picture("solar-direct", "ソーラーパネルを1枚または2枚接続")
        self.flow(19, [250, 145, 345, 160])
        self.flow(19, [25, 170, 345, 220])
        self.picture("solar-adapter", "ソーラーパネルを4枚接続")
        self.flow(19, [25, 350, 345, 391])
        self.notice(19, [25, 402, 345, 492])
        self.flow(20, [25, 25, 345, 67])
        self.subtitle(20, ids=["2:0"])
        self.flow(20, [25, 90, 345, 195])
        self.picture("car-charge", "シガーソケット充電")
        self.flow(20, [25, 232, 345, 337])
        self.notice(20, [25, 375, 345, 418])

        self.chapter("troubleshooting", 21, "3:0")
        self.flow(21, [25, 58, 345, 84])
        h = [self.take(21, ids=["4:0"]), self.take(21, ids=["4:1"])]
        rows = []
        for y0, y1 in [
            (114, 145),
            (150, 171),
            (174, 196),
            (200, 296),
            (300, 349),
            (355, 375),
            (383, 412),
            (421, 445),
        ]:
            c = self.take(21, [25, y0, 80, y1])
            v = self.take(21, [80, y0, 345, y1])
            # Numbered troubleshooting steps remain one cell with semantic line breaks.
            rich = escape(v)
            rich = re.sub(r" (?=[2-9]\. )", "<br/>", rich)
            rows.append(
                {
                    "code_text": c,
                    "code_html": escape(c),
                    "measures_text": v,
                    "measures_html": rich,
                }
            )
        self.comp(
            troubleshooting_component_spec(
                headers=[{"content_text": v, "content_html": escape(v)} for v in h],
                rows=rows,
                source_ref=self.ref("faults"),
                language="ja",
            )
        )

        self.chapter("specifications", 22, "30:0")
        groups = {}
        group_titles = []
        for key, title_id, rows in [
            ("general", "1:0", [(f"{i}:0", [f"{i + 6}:0"]) for i in range(2, 8)]),
            (
                "inputs",
                "14:0",
                [("15:0", ["18:0", "19:0"]), ("17:0", ["20:0", "21:0"])],
            ),
            (
                "outputs",
                "22:0",
                [
                    ("39:1", ["38:0", "39:0"]),
                    ("40:0", ["36:0"]),
                    ("41:0", ["35:0"]),
                    ("42:0", ["37:0"]),
                    ("43:0", ["33:0"]),
                    ("44:0", ["34:0"]),
                ],
            ),
            (
                "temperature",
                "26:0",
                [
                    ("23:0", ["27:0"]),
                    ("24:0", ["28:0"]),
                    ("25:0", ["32:0", "32:1", "32:2"]),
                ],
            ),
        ]:
            group_titles.append(self.take(22, ids=[title_id]))
            groups[key] = []
            for label_ids, value_ids in rows:
                label = self.take(22, ids=[label_ids])
                value = self.take(22, ids=value_ids)
                groups[key].append({"label": label, "value": value})
        self.take(22, ids=["16:0"], role="empty-table-cell") if any(
            r["id"] == "16:0" for r in self.pages[22]["lines"]
        ) else None
        self.body.extend(
            specification_flow(
                {"groups": groups},
                group_headings=group_titles,
                source_ref=self.ref("spec"),
                language="ja",
            )
        )
        self.flow(22, [25, 437, 345, 485])

        self.chapter("warranty", 23, "2:0")
        lead = self.take(23, ids=["1:0", "1:1"])
        note = self.take(23, ids=["1:2"])
        self.comp(
            warranty_lead_component_spec(
                accessibility_label="保証について",
                lead_html=escape(lead),
                local_note_html=escape(note),
                source_ref=self.ref("lead"),
                language="ja",
            )
        )
        sections = [
            (23, "9:0", [25, 110, 345, 173]),
            (23, "11:0", [25, 199, 345, 249]),
            (23, "14:0", [25, 276, 345, 310]),
            (23, "16:0", [25, 342, 345, 421]),
            (23, "18:0", [25, 449, 345, 495]),
            (24, "11:0", [25, 48, 345, 223]),
            (24, "12:0", [25, 254, 345, 340]),
        ]
        for i, (p, tid, box) in enumerate(sections, 1):
            title = self.take(p, ids=[tid])
            rs = self.select(p, box, available=True)
            # Warranty copy follows visual order and retains every printed condition.
            for r in rs:
                self.mark(p, r, "live-copy/warranty")
            segments = []
            current = []
            for row in rs:
                if current and (
                    re.match(r"^[・•]|^[1-9][.．]", row["text"].strip())
                    or row["origin"][1] - current[-1]["origin"][1] > 13
                ):
                    segments.append(current)
                    current = []
                current.append(row)
            if current:
                segments.append(current)
            blocks = [
                {
                    "kind": "paragraph",
                    "html": escape(joined(group)),
                    "text": joined(group),
                }
                for group in segments
            ]
            self.add(heading(title, level=2))
            self.comp(
                warranty_section_component_spec(
                    title=title,
                    section_index=i,
                    blocks=blocks,
                    source_ref=self.ref("section-" + str(i)),
                    language="ja",
                )
            )
        self.flow(24, [25, 440, 345, 499])

        self.chapter("app-setup", 25, "14:0")
        self.subtitle(25, ids=["12:0"])
        col1 = self.take(25, [25, 65, 215, 98])
        col2 = self.take(25, [220, 65, 345, 98])
        self.comp(
            app_download_component_spec(
                accessibility_label="Jackeryアプリのダウンロード",
                columns=[
                    {"role": "store", "html": escape(col1), "text": col1},
                    {"role": "qr", "html": escape(col2), "text": col2},
                ],
                source_art_ref="assets/app-store.png",
                store_art_ref="assets/app-store.png",
                qr_art_ref="assets/app-qr.png",
                source_ref=self.ref("download"),
                language="ja",
            )
        )
        self.subtitle(25, ids=["1:0"])
        source_plus = self.take(25, ids=["5:0"], role="live-copy/inline-plus-gap")
        tail = "をクリックします。"
        prefix = source_plus.removesuffix(tail).strip()
        carrier = node(
            "paragraph",
            [text(prefix + " "), node("strong", [text("+")]), text(" " + tail)],
        )
        copy = prefix + " + " + tail
        spec = app_inline_control_component_spec(
            accessibility_label="+",
            paragraph_html=escape(copy),
            paragraph_text=copy,
            source_ref=self.ref("add-device-plus"),
            language="ja",
        )
        self.add(component_flow_node(spec, carrier_flow=[carrier], root=True))
        self.flow(25, [25, 196, 345, 230])
        self.picture("app-phones", "デバイスの追加：2.1 / 2.2")
        self.picture("app-control", "各ボタンの位置")
        self.flow(26, [25, 25, 345, 38])
        self.notice(26, [25, 39, 345, 78], bullet_ids=("26:0", "26:1"))
        self.flow(26, [25, 80, 345, 100])
        self.notice(26, [25, 104, 345, 126])
        self.flow(26, [25, 130, 345, 140])
        self.picture("app-results", "デバイスの追加：2.3 / 2.4 / 2.5")
        self.flow(26, [25, 285, 345, 292])
        self.notice(26, [25, 296, 345, 325])
        self.subtitle(26, ids=["2:0"])
        self.flow(26, [25, 340, 345, 364])
        self.subtitle(26, ids=["21:0"])
        self.flow(26, [25, 380, 355, 498])
        self.finish()

    def finish(self):
        missing = []
        for p in range(3, 27):
            for r in self.pages[p]["lines"]:
                if (p, r["id"]) not in self.used:
                    missing.append({"page": p, **r})
        dump(PACKAGE / "source/unmapped.json", missing)
        dump(PACKAGE / "source/reused-assets.json", self.reuse)
        dump(
            PACKAGE / "source/line-ledger.json",
            [self.used[k] for k in sorted(self.used)],
        )
        dump(
            PACKAGE / "source/ja/content.json",
            {
                "model": "JE-2000F",
                "region": "JP",
                "language": "ja",
                "title": "Jackery ポータブル電源 2000 New（JE-2000F / JE-2000F-SG / JE-2000F-WH）取扱説明書",
                "source_sha256": "d10ae5e04ad48907538f5cf18f3afa964ac261fceb40684b6fc1ee0963003e95",
                "physical_pages": list(range(3, 27)),
                "chapters": self.chapters,
            },
        )
        print(
            "chapters",
            len(self.chapters),
            "selected lines",
            len(self.used),
            "unmapped",
            len(missing),
        )
        if missing:
            for r in missing:
                print("UNMAPPED", r["page"], r["id"], r["origin"], r["text"])


if __name__ == "__main__":
    Intake().build()
