"""Compatibility Web renderer for embedded Operation ComponentSpecs."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from bs4 import BeautifulSoup, Tag

from tools.component_specs.model import ComponentSpec
from tools.component_specs.operation_adapters import web_operation_projection
from tools.web_composite_presentation import WebCompositeContext


def render_operation_component(
    spec: ComponentSpec,
    carrier_html: str,
    *,
    source_path: Path,
    presentation: Mapping[str, Any],
    composites: WebCompositeContext,
) -> str:
    """Render through the established transform so frozen hashes do not move."""

    projection = web_operation_projection(spec, presentation)
    soup = BeautifulSoup(carrier_html, "html.parser")
    # The flow carrier intentionally owns only the operation panel, while the
    # surrounding section remains ordinary document flow. Recreate that parent
    # solely for the compatibility transform, then return its children so the
    # replay does not add a nested section.
    section = soup.new_tag("section")
    for child in list(soup.contents):
        section.append(child.extract())
    soup.append(section)
    supporting_copy = projection["supporting_copy"]
    if supporting_copy:
        image = soup.find("img")
        if not isinstance(image, Tag):
            raise ValueError(f"{spec.source_ref}: operation carrier has no artwork")
        step_block = image.find_next_sibling()
        if not isinstance(step_block, Tag) or "line-block" not in step_block.get(
            "class", []
        ):
            raise ValueError(f"{spec.source_ref}: operation carrier has no step block")
        step_line_count = sum(len(step["parts"]) for step in projection["steps"])
        carrier_lines = step_block.find_all(class_="line", recursive=False)
        if len(carrier_lines) < step_line_count:
            raise ValueError(
                f"{spec.source_ref}: operation carrier has fewer lines than its steps"
            )
        insertion_point = (
            carrier_lines[step_line_count]
            if len(carrier_lines) > step_line_count
            else None
        )
        for value in supporting_copy:
            line = soup.new_tag("div", attrs={"class": "line"})
            fragment = BeautifulSoup(str(value), "html.parser")
            for child in list(fragment.contents):
                line.append(child.extract())
            if insertion_point is None:
                step_block.append(line)
            else:
                insertion_point.insert_before(line)
    image = soup.find("img")
    if not isinstance(image, Tag):
        raise ValueError(f"{spec.source_ref}: operation carrier has no artwork")
    # Delayed import avoids making the shared ComponentSpec layer depend on a
    # Web module while preserving the frozen compatibility transform in cut 3.
    from tools.web_presentation import _transform_operation_figure

    _transform_operation_figure(
        soup,
        image=image,
        spec=dict(presentation),
        source_path=source_path,
        composites=composites,
    )
    figure = soup.select_one("figure.hb-operation-figure")
    if isinstance(figure, Tag):
        figure["data-component-id"] = spec.component_id
    return section.decode_contents()


__all__ = ["render_operation_component"]
