"""Web-source validation for the Callout ComponentSpec pilot."""
from __future__ import annotations

from bs4 import BeautifulSoup

from tools.component_specs.adapters import web_callout_classes
from tools.component_specs.callout import callout_component_spec
from tools.component_specs.model import ComponentSpec, ComponentSpecError


def validate_web_callout_html(
    callout_html: str,
    *,
    source_ref: str,
    error_type: type[Exception] = ComponentSpecError,
) -> ComponentSpec:
    """Validate protected Web callout HTML against the registered adapter."""
    soup = BeautifulSoup(callout_html, "html.parser")
    label_node = soup.select_one(".manual-callout-label")
    body_node = soup.select_one(".manual-callout-body")
    if label_node is None or body_node is None:
        raise error_type(f"{source_ref}: manual callout requires label and body cells")
    spec = callout_component_spec(
        label=label_node.get_text(" ", strip=True),
        body=body_node.get_text("\n", strip=True),
        items=[item.get_text(" ", strip=True) for item in body_node.select("li")],
        source_ref=source_ref,
        language=str((soup.table.get("lang") if soup.table else None) or "und"),
    )
    table_class = web_callout_classes(spec)["table"]
    if soup.select_one(f"table.{table_class}") is None:
        raise error_type(
            f"{source_ref}: callout does not satisfy the registered Web adapter"
        )
    return spec


__all__ = ["validate_web_callout_html"]
