"""Responsive Web adapter for the shared product-overview ComponentSpec."""
from __future__ import annotations

import html
from pathlib import Path
from typing import Any, Mapping

from bs4 import BeautifulSoup, Tag

from tools.component_specs.overview_adapters import web_overview_projection
from tools.component_specs.overview_html import parse_overview_html
from tools.web_composite_presentation import WebCompositeContext


def _append_markup(target: Tag, markup: str) -> None:
    parsed = BeautifulSoup(markup, "html.parser")
    for child in list(parsed.contents):
        target.append(child.extract())


def _callout_markup(callout: Mapping[str, Any]) -> str:
    paragraphs = [
        f"<p><strong>{html.escape(str(callout['label']))}</strong></p>"
    ]
    paragraphs.extend(
        f"<p>{html.escape(str(value))}</p>"
        for value in callout.get("body", [])
    )
    return "\n".join(paragraphs)


def _points_text(points: list[list[float]]) -> str:
    return " ".join(f"{float(x):g},{float(y):g}" for x, y in points)


def _leader_layer(soup: BeautifulSoup, view: Mapping[str, Any]) -> Tag:
    svg = soup.new_tag(
        "svg",
        attrs={
            "class": "hb-leader-layer",
            "viewBox": "0 0 100 100",
            "preserveAspectRatio": "none",
            "aria-hidden": "true",
            "focusable": "false",
        },
    )
    for callout in view["callouts"]:
        svg.append(
            soup.new_tag(
                "polyline",
                attrs={
                    "class": "hb-leader",
                    "data-callout-id": (
                        f"overview.{view['id']}.{callout['id']}"
                    ),
                    "points": _points_text(callout["leader"]),
                },
            )
        )
    for index, points in enumerate(view.get("decorative_leaders", []), start=1):
        svg.append(
            soup.new_tag(
                "polyline",
                attrs={
                    "class": "hb-leader-decoration",
                    "data-decoration-id": (
                        f"overview.{view['id']}.decoration-{index}"
                    ),
                    "points": _points_text(points),
                },
            )
        )
    return svg


def _overview_figure(
    soup: BeautifulSoup,
    *,
    image: Tag,
    view: Mapping[str, Any],
    source_path: Path,
    composites: WebCompositeContext,
) -> Tag:
    figure = soup.new_tag(
        "figure",
        attrs={
            "class": "hb-annotated-figure",
            "data-figure-id": f"product-overview-{view['id']}",
        },
    )
    stage = soup.new_tag(
        "div",
        attrs={
            "class": "hb-annotated-stage",
            "style": f"--hb-aspect-ratio:{float(view['aspect_ratio']):g}",
        },
    )
    image["class"] = [*image.get("class", []), "hb-annotated-art"]
    image.replace_with(figure)
    stage.append(image)
    stage.append(_leader_layer(soup, view))

    for item in view["callouts"]:
        x, y, width, height = (float(value) for value in item["rect"])
        align = str(item["align"])
        callout = soup.new_tag(
            "div",
            attrs={
                "class": ["hb-figure-callout", f"hb-align-{align}"],
                "data-callout-id": f"overview.{view['id']}.{item['id']}",
                "style": (
                    f"--hb-x:{x:g}%;--hb-y:{y:g}%;--hb-width:{width:g}%;"
                    f"--hb-height:{height:g}%;--hb-align:{align}"
                ),
            },
        )
        _append_markup(callout, _callout_markup(item))
        stage.append(callout)
    composites.append_semantic(
        soup=soup,
        figure=figure,
        semantic=stage,
        component=dict(view),
        source_path=source_path,
        image_key=str(view["image_key"]),
    )
    figure.append(stage)
    return figure


def transform_overview(
    soup: BeautifulSoup,
    *,
    source_path: Path,
    instance: Mapping[str, Any],
    composites: WebCompositeContext,
    error_type: type[Exception],
) -> None:
    parsed = parse_overview_html(
        soup,
        source_path=source_path,
        instance=instance,
        error_type=error_type,
    )
    projection = web_overview_projection(parsed.spec, instance)
    html_views = {view.view_id: view for view in parsed.views}
    for view in projection["views"]:
        view_id = str(view["id"])
        html_view = html_views[view_id]
        _overview_figure(
            soup,
            image=html_view.image,
            view=view,
            source_path=source_path,
            composites=composites,
        )
        for table in list(html_view.section.find_all("table", recursive=False)):
            table.decompose()


__all__ = ["transform_overview"]
