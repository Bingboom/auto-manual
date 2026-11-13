"""Bind each verbatim Japanese transcript once to existing shared components."""

import json
from pathlib import Path
import sys
from bs4 import BeautifulSoup

PACKAGE = Path(__file__).resolve().parent
REPO = next(p for p in PACKAGE.parents if (p / "build.py").is_file())
sys.path.insert(0, str(REPO))
from tools.component_specs.inbox import inbox_component_spec  # noqa: E402
from tools.component_specs.reference_figure import reference_figure_component_spec  # noqa: E402
from tools.component_specs.spec_table import spec_table_component_spec  # noqa: E402
from tools.manual_ir.components import component_flow_node  # noqa: E402
from tools.web.composite_hashing import reference_source_fragment_sha256  # noqa: E402
from tools.web.frozen_ai_flow import node, root, table, text  # noqa: E402
from tools.web.frozen_ai_table_components import _spec_carrier  # noqa: E402
from tools.web.frozen_pdf_reference import labeled_artwork_node  # noqa: E402

transcript = json.loads((PACKAGE / "source/transcription.json").read_text())
ROWS = {
    r["id"]: r
    for p in transcript["pages"]
    for r in p["lines"]
    if r["disposition"] != "web-excluded"
}
USED = []
NEW = transcript["material"].endswith("000464")


def T(key):
    if key in USED:
        raise ValueError("line bound twice: " + key)
    USED.append(key)
    return ROWS[key]["text"]


def para(key, strong=False):
    children = [text(T(key))]
    if strong:
        children = [node("strong", children)]
    return root(node("paragraph", children))


def heading(key, level=1):
    return root(node("heading", [text(T(key))], level=level))


def group(children):
    return root(
        node(
            "group",
            [{k: v for k, v in x.items() if k != "schema_version"} for x in children],
            role="container",
            presentation={"html": {"attributes": {"class": "hb-text-panel"}}},
        )
    )


def fig(asset, identity, alt):
    ref = "assets/" + asset
    s = BeautifulSoup("", "html.parser")
    semantic = s.new_tag(
        "div",
        attrs={
            "class": "hb-reference-semantic",
            "data-reference-id": identity + ".semantic",
        },
    )
    semantic.append(
        s.new_tag("img", attrs={"alt": alt, "class": "hb-reference-art", "src": ref})
    )
    digest = reference_source_fragment_sha256(
        component={"id": identity, "image_key": identity, "captions_embedded": True},
        semantic=semantic,
        caption_labels=[],
        composite_locale=None,
    )
    spec = reference_figure_component_spec(
        reference_id=identity,
        accessibility_label=alt,
        caption_mode="embedded",
        captions=(),
        adjacent_copy=None,
        source_art_ref=ref,
        source_art_locale_policy="exact",
        source_fragment_sha256=digest,
        source_ref="source/transcription.json#" + identity,
        language="ja",
        image_key=identity,
        metadata={
            "artwork_origin": "source-bound-candidate-crop",
            "candidate_only": True,
        },
    )
    return component_flow_node(
        spec, carrier_flow=(root(node("image", source=ref, alt=alt)),), root=True
    )


def guide():
    children = [heading("guide.h")]
    for i in range(1, 6):
        children.append(
            group(
                [
                    para(f"guide.s{i}"),
                    fig(f"unfold-{i}.png", f"unfold-{i}", T(f"guide.art{i}")),
                ]
            )
        )
    return children


def spec_block(title, keys, identity):
    title = T(title)
    rows = [(T(a), T(b)) for a, b in keys]
    s = spec_table_component_spec(
        section_title=title,
        rows=rows,
        source_ref="source/transcription.json#" + identity,
        language="ja",
    )
    return component_flow_node(s, carrier_flow=_spec_carrier(title, rows), root=True)


def specs():
    ids = range(1, 21 if NEW else 12)
    out = []
    if NEW:
        out.append(heading("spec.h"))
        title = "spec.product.h"
    else:
        title = "spec.h"
    out.append(
        spec_block(
            title, [(f"spec.r{i}.l", f"spec.r{i}.v") for i in ids], "specification-main"
        )
    )
    out.append(para("spec.stc"))
    if NEW:
        out.append(
            spec_block(
                "adapter.h",
                [(f"adapter.r{i}.l", f"adapter.r{i}.v") for i in [1, 2]],
                "specification-adapter",
            )
        )
    return out


def inbox():
    title = T("box.h")
    keys = [k for k in ROWS if k.startswith("box.c")]
    cards = []
    for key in keys:
        value = T(key)
        cards.append(
            {"image_ref": "assets/" + ROWS[key]["asset"], "label": value, "alt": value}
        )
    s = inbox_component_spec(
        accessibility_label=title,
        cards=cards,
        tip_label="",
        tip_body="",
        source_ref="source/transcription.json#inbox",
        language="ja",
        require_tip=False,
        metadata={"desktop_columns": 3} if NEW else {},
    )
    carrier = table(
        [
            [
                node(
                    "table_cell",
                    [
                        node("image", source=c["image_ref"], alt=c["alt"]),
                        node("paragraph", [text(c["label"])]),
                    ],
                    header=False,
                )
                for c in cards
            ]
        ]
    )
    out = [
        root(node("heading", [text(title)], level=1)),
        component_flow_node(s, carrier_flow=(carrier,), root=True),
    ]
    if NEW:
        out.append(group([para("box.note")]))
    return out


def safety():
    return [
        heading("safety.h"),
        group([para("safety.lead", True)]),
        root(
            node(
                "list",
                [
                    node("list_item", [node("paragraph", [text(T(f"safety.i{i}"))])])
                    for i in range(1, 12)
                ],
                ordered=False,
            )
        ),
    ]


def power():
    labels = [
        T("power." + name)
        for name in ["panel", "adapter", "dc", "jack", "phone", "bank", "tablet"]
    ]
    # Rectangles are measured on the exact textless art crop; percentages stay inside this source panel.
    boxes = [
        [113, 103.6, 163, 110.5],
        [111, 130, 150, 136.8],
        [170, 138.5, 186, 144.5],
        [154, 144.3, 244, 157],
        [72, 192.6, 104, 199.5],
        [113, 192.6, 154, 199.5],
        [165, 192.6, 190, 199.5],
    ]
    layout = {
        "art_sha256": __import__("hashlib")
        .sha256((PACKAGE / "assets/power-device.png").read_bytes())
        .hexdigest(),
        "panel_top": 0,
        "panel_fill": "#ffffff",
        "preserve_frame": False,
        "labels": [
            {
                "line": i,
                "rect": [
                    (r[0] - 18) / 226 * 100,
                    (r[1] - 28) / 172 * 100,
                    (r[2] - r[0]) / 226 * 100,
                    (r[3] - r[1]) / 172 * 100,
                ],
            }
            for i, r in enumerate(boxes)
        ],
    }
    figure = {
        "slug": "power-device",
        "physical_page": 26,
        "live_captions": [
            {"text": value, "bbox": bbox}
            for value, bbox in zip(labels, boxes, strict=True)
        ],
        "base_art_layout": layout,
    }
    picture = labeled_artwork_node(figure, "assets/power-device.png", "ja")
    picture["component_spec"]["metadata"]["retained_fixed_port_markings"] = T(
        "power.ports"
    )
    return [heading("power.h"), picture, group([para("power.note")])]


chapters = []


def add(identity, nodes):
    chapters.append({"id": identity, "nodes": nodes})


if not NEW:
    add(
        "preface",
        [
            para("preface.scope", True),
            para("preface.support"),
            para("preface.lead", True),
            para("preface.read"),
            para("preface.keep"),
            para("preface.update"),
        ],
    )
add("guide", guide())
add("specifications", specs())
if NEW:
    add("power_your_device", power())
add("in_the_box", inbox())
add("safety", safety())
if NEW:
    add(
        "contact",
        [
            heading("contact.h"),
            group([para("contact.body")]),
            heading("service.h"),
            group(
                [
                    para("service.warranty"),
                    para("service.support"),
                    para("service.mail"),
                    para("service.web"),
                ]
            ),
            heading("company.h"),
            para("company.copy"),
            group([para("manufacturer.h", True), para("manufacturer.address")]),
            fig("contact-qr.png", "contact-qr", T("qr")),
        ],
    )
else:
    add("contact", [fig("contact-qr.png", "contact-qr", T("qr"))])
if set(USED) != set(ROWS):
    raise ValueError("unbound source transcript: " + str(set(ROWS) - set(USED)))
content = {
    "model": "JS-40A",
    "region": "JP",
    "language": "ja",
    "title": "Jackery SolarSaga 40 Mini 取扱説明書",
    "source_sha256": transcript["source_sha256"],
    "material": transcript["material"],
    "chapters": chapters,
}
(PACKAGE / "source/content.json").write_text(
    json.dumps(content, ensure_ascii=False, indent=2) + "\n"
)
(PACKAGE / "evidence/transcription-coverage.json").write_text(
    json.dumps(
        {
            "source_sha256": transcript["source_sha256"],
            "source_rows": len(ROWS),
            "bound_rows": len(USED),
            "all_source_rows_bound_once": True,
            "excluded_rows": [
                r
                for p in transcript["pages"]
                for r in p["lines"]
                if r["disposition"] == "web-excluded"
            ],
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\n"
)
print(
    json.dumps(
        {
            "material": transcript["material"],
            "bound_rows": len(USED),
            "chapters": len(chapters),
        },
        ensure_ascii=False,
    )
)
