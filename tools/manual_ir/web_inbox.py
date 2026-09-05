"""Prepared Inbox composite source: three cards and their existing owned tip."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from bs4 import BeautifulSoup

from tools.component_specs.inbox_html import InboxHtmlSource, parse_inbox_html
from tools.component_specs.model import ComponentSpec
from tools.component_specs.registry import load_component_registry, require_valid_component_spec
from tools.component_specs.theme import load_manual_theme, require_component_theme_roles
from tools.manual_ir.model import ManualBlock
from tools.manual_ir.hashing import value_sha256
from tools.manual_ir.source import ManualSource
from tools.manual_ir.web_source import make_web_source


def inbox_payload(source: InboxHtmlSource) -> dict:
    """Validate complete row geometry without changing other source adapters."""
    for table, width in ((source.inbox_table, 3), (source.tip_table, 2)):
        rows = table.find_all("tr")
        cells = rows[0].find_all(["td", "th"], recursive=False) if len(rows) == 1 else []
        if (table.find("table") or len(rows) != 1 or len(cells) != width
                or any(str(cell.get(attr, "1")) != "1" for cell in cells
                       for attr in ("rowspan", "colspan"))):
            raise ValueError(f"{source.spec.source_ref}: Inbox requires complete unspanned card/tip rows")
    nodes = (source.heading, source.inbox_table, source.tip_table)
    return {
        "component_spec": source.spec.to_dict(),
        "heading_html": str(source.heading),
        "inbox_html": str(source.inbox_table),
        "tip_html": str(source.tip_table),
        "markup_assets": [{"src": str(image["src"])} for node in nodes
                          for image in node.select("img[src]") if image["src"]],
    }


def load_web_inbox_source(
    html: str, *, source_path: Path, language: str,
    model: str | None = None, region: str | None = None,
) -> ManualSource:
    source = parse_inbox_html(
        BeautifulSoup(html, "html.parser"), source_path=source_path,
        language=language, error_type=ValueError,
    )
    registry = load_component_registry()
    return make_web_source(
        html, source_path=source_path, blocks=(("web_inbox", inbox_payload(source)),),
        projection="web-inbox", language=language, model=model, region=region,
        style_contract_sha256=value_sha256({
            "registry": registry,
            "theme": load_manual_theme(component_registry=registry),
        }),
    )


def decode_inbox_payload(block: ManualBlock, *, source_path: Path, language: str) -> InboxHtmlSource:
    """Check retained markup against the owned semantic payload before replay."""
    payload = block.payload
    if (block.kind != "web_inbox" or not isinstance(payload, dict)
            or not isinstance(payload.get("component_spec"), dict)
            or not all(isinstance(payload.get(key), str)
                       for key in ("heading_html", "inbox_html", "tip_html"))):
        raise ValueError(f"{block.source_ref}: incomplete Web Inbox payload")
    spec = require_component_theme_roles(require_valid_component_spec(
        ComponentSpec.from_dict(payload["component_spec"]),
    ))
    soup = BeautifulSoup(
        payload["heading_html"] + payload["inbox_html"] + payload["tip_html"],
        "html.parser",
    )
    source = parse_inbox_html(
        soup, source_path=source_path, language=language, error_type=ValueError,
    )
    if value_sha256(inbox_payload(source)) != value_sha256(payload):
        raise ValueError(f"{block.source_ref}: Inbox semantics/assets do not match retained markup")
    return replace(source, spec=spec)
