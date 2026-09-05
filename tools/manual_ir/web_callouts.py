"""Prepared Web callout source adapter; rich HTML is an explicit replay payload."""
from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup, Tag

from tools.component_specs.callout import CALLOUT_VARIANTS
from tools.component_specs.registry import load_component_registry
from tools.component_specs.web_source import validate_web_callout_html
from tools.manual_ir.hashing import file_sha256, value_sha256
from tools.manual_ir.source import ManualSource
from tools.manual_ir.web_source import make_web_source
from tools.utils.path_utils import Paths, repo_root


def decode_callout_payload(
    html: str, *, source_ref: str, declaration: dict | None = None,
) -> dict:
    """Keep all authored markup, but reject ambiguous label/body geometry."""
    if declaration is not None and (
        not isinstance(declaration, dict)
        or set(declaration) != {"language", "variant"}
        or not isinstance(declaration["language"], str)
        or not declaration["language"].strip()
        or (declaration["variant"] is not None and (
            not isinstance(declaration["variant"], str)
            or declaration["variant"] not in CALLOUT_VARIANTS
        ))
    ):
        raise ValueError(f"{source_ref}: invalid callout declaration")
    soup = BeautifulSoup(html, "html.parser")
    roots = [node for node in soup.contents if isinstance(node, Tag) or str(node).strip()]
    table = soup.select_one("table.manual-callout-table")
    if len(roots) != 1 or roots[0] is not table or table is None:
        raise ValueError(f"{source_ref}: expected exactly one declared callout table")
    rows = table.find_all("tr")
    cells = rows[0].find_all(["th", "td"], recursive=False) if len(rows) == 1 else []
    if (
        table.find(["table", "thead", "tfoot"])
        or len(table.find_all("tbody", recursive=False)) != 1
        or len(rows) != 1 or rows[0].parent is not table.tbody
        or len(cells) != 2
        or "manual-callout-label" not in cells[0].get("class", [])
        or "manual-callout-body" not in cells[1].get("class", [])
        or len(table.select(".manual-callout-label, .manual-callout-body")) != 2
        or any(str(cell.get(attr, "1")) != "1" for cell in cells
               for attr in ("rowspan", "colspan"))
    ):
        raise ValueError(f"{source_ref}: callout requires one row with label/body cells")
    spec = validate_web_callout_html(html, source_ref=source_ref, **(declaration or {}))
    payload = {
        "component_spec": spec.to_dict(),
        "table_html": html,
        "markup_assets": [{"src": str(image["src"])}
                          for image in table.select("img[src]") if image["src"]],
    }
    if declaration is not None:
        payload["declaration"] = dict(declaration)
    return payload


def load_web_callout_source(
    html: str, *, source_path: Path, model: str | None = None,
    region: str | None = None, declaration: dict | None = None,
) -> ManualSource:
    payload = decode_callout_payload(html, source_ref=str(source_path), declaration=declaration)
    return make_web_source(
        html, source_path=source_path,
        blocks=(("web_callout", payload),), projection="web-callout",
        style_contract_sha256=value_sha256({
            "registry": load_component_registry(),
            "web_css": file_sha256(Paths(root=repo_root()).renderer_contracts_dir / "web_manual.css"),
        }),
        language=payload["component_spec"]["language"], model=model, region=region,
    )
