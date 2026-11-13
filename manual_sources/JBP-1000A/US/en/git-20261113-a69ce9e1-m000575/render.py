"""Replay one source-bound English manual through the existing shared ManualIR Web pipeline."""

from __future__ import annotations

from html import escape
import json
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace

PACKAGE = Path(__file__).resolve().parent
ROOT = next(p for p in PACKAGE.parents if (p / "build.py").is_file())
sys.path.insert(0, str(ROOT))

from tools.component_specs.spec_table import spec_table_component_spec  # noqa: E402
from tools.component_specs.fcc import fcc_component_spec  # noqa: E402
from tools.component_specs.inbox import inbox_component_spec  # noqa: E402
from tools.component_specs.reference_table import reference_table_component_spec  # noqa: E402
from tools.component_specs.warranty import (
    warranty_section_component_spec,
    warranty_years_component_spec,
)  # noqa: E402
from tools.manual_ir.components import component_flow_node  # noqa: E402
from tools.manual_ir.flow import html_to_flow_nodes  # noqa: E402
from tools.manual_ir.hashing import file_sha256, value_sha256  # noqa: E402
from tools.manual_ir.source import SourcePage  # noqa: E402
from tools.web.frozen_ai_flow import (
    callout,
    cell,
    heading,
    node,
    paragraph,
    root,
    scroll_table,
    table,
)  # noqa: E402
from tools.web.frozen_ai_media_components import figure_node  # noqa: E402
from tools.web.frozen_ai_table_components import (
    symbol_pictogram_flow,
    symbol_signal_flow,
    troubleshooting_flow,
)  # noqa: E402
from tools.web.frozen_ai_web import assemble_book  # noqa: E402
from tools.web.prepared_style_audit import (
    require_prepared_document_styles,
    table_text_sha256,
)  # noqa: E402


def text_table(block: dict) -> dict:
    header = block.get("headers", [])
    rows = [[cell(str(v), header=True) for v in header]] if header else []

    def rich_cell(v):
        if isinstance(v, dict):
            return node(
                "table_cell",
                [
                    node(
                        "image",
                        source=v["image"],
                        alt=v["text"],
                        presentation={"html": {"attributes": {"width": "80"}}},
                    ),
                    paragraph(v["text"]),
                ],
                header=False,
            )
        lines = str(v).split("\n")
        content = []
        for index, line in enumerate(lines):
            if index:
                content.append(node("line_break"))
            content.append(node("text", text=line))
        return node("table_cell", content, header=False)

    rows += [[rich_cell(v) for v in row] for row in block["rows"]]
    return root(scroll_table(rows))


def exceptions(transcription: dict) -> list[dict]:
    return [
        {
            "language": "en",
            "page_id": chapter["id"],
            "kind": "table",
            "text_sha256": table_text_sha256(text_table(block)),
            "reason": block["reason"],
        }
        for chapter in transcription["chapters"]
        for block in chapter["blocks"]
        if block["kind"] == "plain_table"
    ]


def check_inputs(manifest: dict) -> None:
    for item in manifest["inputs"]:
        path = (PACKAGE / item["path"]).resolve()
        if (
            not path.is_relative_to(PACKAGE)
            or not path.is_file()
            or file_sha256(path) != item["sha256"]
            or path.stat().st_size != item["size"]
        ):
            raise ValueError(f"frozen input changed: {item['path']}")
    for item in manifest.get("repo_inputs", []):
        path = (ROOT / item["path"]).resolve()
        if not path.is_relative_to(ROOT) or file_sha256(path) != item["sha256"]:
            raise ValueError(f"repository input changed: {item['path']}")
    if (
        manifest["publication_eligible"]
        or manifest["publication_status"] != "review-candidate-no-release-authorization"
    ):
        raise ValueError(
            "this source adapter is a review candidate, not release authorization"
        )


def render(output: Path) -> dict:
    output = output.resolve()
    if output.exists():
        raise ValueError("use a new output directory")
    manifest = json.loads((PACKAGE / "source_manifest.json").read_text())
    check_inputs(manifest)
    data = json.loads((PACKAGE / "source/transcription.json").read_text())
    assets = json.loads((PACKAGE / "source/asset_decisions.json").read_text())["assets"]
    if manifest.get("shared_component_exceptions", []) != exceptions(data):
        raise ValueError(
            "declared plain-table exceptions differ from the source transcription"
        )
    output.mkdir(parents=True)
    hashes = {}
    for record in assets.values():
        source = PACKAGE / record["path"]
        if file_sha256(source) != record["sha256"]:
            raise ValueError("source artwork changed")
        destination = output / record["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        hashes[record["path"]] = record["sha256"]
    figures, art = [], {}

    def convert(block: dict, chapter: dict, index: int) -> list[dict]:
        kind = block["kind"]
        ref = f"source/transcription.json#{chapter['id']}/{index}"
        if kind == "panel":
            children = []
            for child_index, child in enumerate(block["blocks"]):
                children.extend(convert(child, chapter, index * 100 + child_index))
            return [root(node(
                "group", [{k: v for k, v in child.items() if k != "schema_version"}
                          for child in children], role="container",
                presentation={"html": {"attributes": {"class": "hb-text-panel"}}},
            ))]
        if kind == "html":
            return [root(v) for v in html_to_flow_nodes(block["html"])]
        if kind == "paragraph":
            return [root(paragraph(block["text"]))]
        if kind == "list":
            return [
                root(
                    node(
                        "list",
                        [node("list_item", [paragraph(v)]) for v in block["items"]],
                        ordered=block.get("ordered", False),
                    )
                )
            ]
        if kind == "years":
            periods = [
                {
                    "number": v["number"],
                    "unit": v["unit"],
                    "label": v["label"],
                    "body_html": "<p>" + escape(v["body"]) + "</p>",
                    "body_text": v["body"],
                }
                for v in block["periods"]
            ]
            return [
                component_flow_node(
                    warranty_years_component_spec(
                        title=block["title"],
                        periods=periods,
                        source_ref=ref,
                        language="en",
                    ),
                    root=True,
                )
            ]
        if kind == "heading":
            return [root(heading(block["text"], level=block.get("level", 2)))]
        if kind == "link":
            html = f'<p>{escape(block.get("label", ""))} <a href="{escape(block["url"], quote=True)}">{escape(block["url"])}</a></p>'
            return [root(v) for v in html_to_flow_nodes(html)]
        if kind == "figure":
            key = block["asset"]
            a = assets[key]
            figures.append(
                {
                    "slug": key,
                    "section_id": chapter["id"],
                    "physical_page": block["source_page"],
                    "presentation": "complete-source-illustration",
                }
            )
            art[key] = {"asset_ref": a["path"], "sha256": a["sha256"]}
            return [
                figure_node(
                    asset_ref=a["path"],
                    content_sha256=a["sha256"],
                    reference_id=key,
                    alt=block["alt"],
                    language="en",
                    source_ref=ref,
                )
            ]
        if kind == "image":
            a = assets[block["asset"]]
            dimensions = {
                key: str(block[key]) for key in ("width", "height") if key in block
            }
            image = node(
                "image",
                source=a["path"],
                alt=block["alt"],
                **(
                    {"presentation": {"html": {"attributes": dimensions}}}
                    if dimensions
                    else {}
                ),
            )
            # A standalone functional mark is inline copy, not full-width artwork.
            return [root(node("paragraph", [image]) if dimensions else image)]
        if kind == "specification":

            def inline(value):
                if isinstance(value, dict):
                    parts = [
                        node("text", text=value["before"]),
                        node("subscript", [node("text", text=value["subscript"])]),
                        node("text", text=value["after"]),
                    ]
                    return parts, "\n".join(
                        [value["before"], value["subscript"], value["after"]]
                    )
                return [node("text", text=value)], value

            semantic_rows, carrier_rows = [], []
            for label, value in block["rows"]:
                label_nodes, label_text = inline(label)
                value_nodes, value_text = inline(value)
                semantic_rows.append([label_text, value_text])
                carrier_rows.append(
                    [
                        node("table_cell", label_nodes, header=True),
                        node("table_cell", value_nodes, header=False),
                    ]
                )
            spec = spec_table_component_spec(
                section_title=block["title"],
                rows=semantic_rows,
                source_ref=ref,
                language="en",
            )
            title = node(
                "heading",
                [
                    node(
                        "inline_group",
                        [node("text", text=block["title"])],
                        presentation={
                            "html": {"attributes": {"class": "hb-spec-section-text"}}
                        },
                    )
                ],
                level=2,
                presentation={"html": {"attributes": {"class": "hb-spec-section"}}},
            )
            return [
                component_flow_node(
                    spec, carrier_flow=[title, table(carrier_rows)], root=True
                )
            ]
        if kind == "callout":
            return [
                root(
                    callout(
                        block["label"],
                        [paragraph(v) for v in block["paragraphs"]],
                        variant=block["variant"],
                        language="en",
                        source_ref=ref,
                    )
                )
            ]
        if kind == "signals":
            return symbol_signal_flow(
                {"rows": [{"label": a, "meaning": b} for a, b in block["rows"]]},
                headings=["Signal", "Meaning"],
                accessibility_label="Signal meanings",
                source_ref=ref,
                language="en",
            )
        if kind == "pictograms":
            rows = block["rows"]
            mid = (len(rows) + 1) // 2
            return symbol_pictogram_flow(
                {
                    "pictograms": [
                        {
                            "meaning": caption,
                            "meaning_bbox": [0 if i < mid else 1, i, 0, 0],
                        }
                        for i, (_, caption) in enumerate(rows)
                    ]
                },
                headings=["Symbol", "Description"],
                accessibility_label="Symbol meanings",
                icon_refs=[assets[k]["path"] for k, _ in rows],
                source_ref=ref,
                language="en",
            )
        if kind == "inbox":
            cards = [
                {"image_ref": assets[key]["path"], "label": label, "alt": label}
                for key, label in block["cards"]
            ]
            spec = inbox_component_spec(
                accessibility_label=chapter["title"],
                cards=cards,
                tip_label="",
                tip_body="",
                require_tip=False,
                metadata={"desktop_columns": 3},
                language="en",
                source_ref=ref,
            )
            carrier = table(
                [
                    [
                        node(
                            "table_cell",
                            [
                                node("image", source=c["image_ref"], alt=c["alt"]),
                                paragraph(c["label"]),
                            ],
                            header=False,
                        )
                        for c in cards
                    ]
                ]
            )
            return [component_flow_node(spec, carrier_flow=[carrier], root=True)]
        if kind == "reference_table":
            pair = lambda v: {
                "html": escape(str(v)).replace("\n", "<br/>"),
                "text": str(v),
            }
            spec = reference_table_component_spec(
                variant=block["variant"],
                label=chapter["title"],
                headers=[pair(v) for v in block.get("headers", [])],
                rows=[[pair(v) for v in row] for row in block["rows"]],
                source_ref=ref,
                language="en",
            )
            return [component_flow_node(spec, root=True)]
        if kind == "troubleshooting":
            return troubleshooting_flow(
                {"rows": [{"code": a, "action": b} for a, b in block["rows"]]},
                headings=block["headers"],
                source_ref=ref,
                language="en",
            )
        if kind == "warranty":
            spec = warranty_section_component_spec(
                title=block["title"],
                section_index=index + 1,
                blocks=[
                    {"kind": "paragraph", "html": "<p>" + escape(v) + "</p>", "text": v}
                    for v in block["paragraphs"]
                ],
                source_ref=ref,
                language="en",
            )
            return [
                root(heading(block["title"], level=2)),
                component_flow_node(spec, root=True),
            ]
        if kind == "fcc":
            # Shared HB-SPECIAL-FCC (shared mark/fcc), as printed: NOTE, "--" measures, optional MODIFICATION.
            right = [{"kind": "list", "items": block["measures"]}]
            carrier = [paragraph("NOTE: " + block["note"])]
            carrier += [paragraph("--" + v) for v in block["measures"]]
            if "modification" in block:
                right.append(
                    {"kind": "paragraph", "label": "MODIFICATION:", "text": block["modification"]}
                )
                carrier.append(paragraph("MODIFICATION: " + block["modification"]))
            spec = fcc_component_spec(
                accessibility_label="FCC",
                opening_copy=[],
                left_blocks=[{"kind": "paragraph", "label": "NOTE:", "text": block["note"]}],
                right_blocks=right,
                source_ref=ref,
                language="en",
                mark_asset_ref=assets["fcc-mark"]["path"],
            )
            return [
                root(
                    node(
                        "group",
                        [component_flow_node(spec, carrier_flow=carrier)],
                        role="container",
                        presentation={"html": {"attributes": {"class": "hb-fcc-balanced-flow"}}},
                    )
                )
            ]
        if kind == "plain_table":
            return [text_table(block)]
        raise ValueError(f"unknown source block {kind}")

    pages = []
    for chapter in data["chapters"]:
        nodes = (
            []
            if chapter.get("heading_from_first_component")
            else [root(heading(chapter["title"], level=1))]
        )
        for index, block in enumerate(chapter["blocks"]):
            nodes.extend(convert(block, chapter, index))
        pages.append(
            SourcePage(
                page_id=chapter["id"],
                source_ref=f"source/transcription.json#{chapter['id']}",
                source_path="source/transcription.json",
                language="en",
                source_sha256=value_sha256(chapter),
                blocks=tuple(("flow", v) for v in nodes),
            )
        )
    book = SimpleNamespace(
        output=output,
        language="en",
        target=manifest["target"],
        source_kind="prepared-document",
        manifest=manifest,
        provenance={
            "intake_method": "image-only-source-ocr-hand-corrected-transcription",
            "pending_source_review": manifest["pending_source_review"],
            "artwork_standardizations": manifest.get("artwork_standardizations", []),
        },
        errata={"source_concerns": data.get("source_concerns", [])},
        hashes=hashes,
        figures=figures,
        art=art,
        target_layout={"media": {"overview": {"presentation": "reference-figures"}}},
        expected_reference_count=len(figures),
    )
    ir = assemble_book(book, manifest["web_title"], tuple(pages))
    report = require_prepared_document_styles(
        ir.to_dict(), exceptions=manifest.get("shared_component_exceptions", [])
    )
    (output / "shared-style-admission.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    )
    result = {
        "model": data["model"],
        "pages": len(pages),
        "components": ir.metadata["component_inventory"],
        "publication_eligible": False,
        "shared_style_issues": report["issues"],
        "output": str(output),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    render(Path(sys.argv[1]))
