"""Web renderer for governed reference-figure ComponentSpecs."""
from __future__ import annotations

from pathlib import Path
from urllib.parse import unquote, urlparse

from bs4 import BeautifulSoup, Tag

from tools.component_specs.model import ComponentSpec
from tools.component_specs.reference_figure_adapters import web_reference_figure_projection
from tools.manual_ir.hashing import file_sha256
from tools.web_composite_manifest import WebCompositeEntry, WebCompositeManifest
from tools.web_composite_presentation import WebCompositeContext


def _local_asset(value: str) -> Path | None:
    parsed = urlparse(value)
    if parsed.scheme != "file":
        return None
    return Path(unquote(parsed.path))


def _component_contract(payload: dict) -> dict:
    approved = payload.get("approved_composite")
    component = {
        "id": payload["reference_id"],
        "image_key": payload["image_key"],
        "captions_embedded": payload["caption_mode"] == "embedded",
        "caption_layout": payload["caption_layout"],
        "web_replace_key": payload["web_replace_key"],
    }
    capture_lines = int(payload.get("capture_following_lines") or 0)
    if capture_lines:
        component["capture_following_lines"] = capture_lines
    if payload.get("captions_origin") == "configured":
        component["caption_labels"] = [item["text"] for item in payload["captions"]]
    if isinstance(payload.get("adjacent_copy"), dict):
        component["capture_adjacent_paragraph"] = True
    resolved_locale = str(payload.get("composite_locale") or "").strip()
    if resolved_locale.casefold() == "shared":
        component["composite_locale"] = "shared"
    elif isinstance(approved, dict):
        if str(approved["locale"]).casefold() == "shared":
            component["composite_locale"] = "shared"
        else:
            component["composite_locales"] = [{"locale": approved["locale"]}]
    return component


def _manifest(payload: dict) -> WebCompositeManifest | None:
    approved = payload.get("approved_composite")
    if not isinstance(approved, dict):
        return None
    asset = str(approved["asset_ref"])
    path = _local_asset(asset)
    if path is None or not path.is_file():
        raise ValueError("embedded approved composite is not a packaged local asset")
    actual = file_sha256(path)
    if actual != approved["content_sha256"]:
        raise ValueError(
            "embedded approved composite SHA-256 changed; "
            f"expected {approved['content_sha256']}, got {actual}"
        )
    entry = WebCompositeEntry(
        asset_key=str(approved["asset_key"]),
        web_replace_key=str(payload["web_replace_key"]),
        model_scope="ALL",
        region_scope="ALL",
        locale=str(approved["locale"]),
        source_page=None,
        content_sha256=str(approved["content_sha256"]),
        path=asset,
        format=path.suffix.lstrip(".") or "png",
        source_fragment_sha256=str(approved["source_fragment_sha256"]),
    )
    return WebCompositeManifest(entries=(entry,), source=path.parent)


def _validate_carrier(payload: dict, soup: BeautifulSoup) -> Tag:
    images = [
        image
        for image in soup.find_all("img")
        if str(image.get("src") or "") == str(payload["source_art"])
    ]
    if len(images) != 1:
        raise ValueError("reference figure carrier has no unique semantic artwork")
    adjacent = payload.get("adjacent_copy")
    if isinstance(adjacent, dict):
        paragraphs = soup.find_all("p", recursive=False)
        if len(paragraphs) != 1 or paragraphs[0].get_text(" ", strip=True) != adjacent["text"]:
            raise ValueError("reference figure adjacent carrier disagrees with slots")
    if payload.get("captions_origin") == "carrier":
        blocks = soup.select(".line-block")
        lines = blocks[0].find_all(class_="line", recursive=False) if len(blocks) == 1 else []
        if [line.get_text(" ", strip=True) for line in lines] != [
            item["text"] for item in payload["captions"]
        ]:
            raise ValueError("reference figure label carrier disagrees with slots")
    return images[0]


def render_reference_figure_component(
    spec: ComponentSpec,
    carrier_html: str,
    *,
    source_path: Path,
    model: str,
    region: str,
    language: str,
) -> str:
    """Render from a bound carrier and frozen ComponentSpec, not a page scan."""

    payload = web_reference_figure_projection(spec)
    payload.update(
        {
            "capture_following_lines": int(
                spec.metadata.get("capture_following_lines") or 0
            ),
            "captions_origin": str(spec.metadata.get("captions_origin") or "carrier"),
            "composite_locale": str(spec.metadata.get("composite_locale") or ""),
        }
    )
    soup = BeautifulSoup(carrier_html, "html.parser")
    image = _validate_carrier(payload, soup)
    component = _component_contract(payload)
    context = WebCompositeContext(
        _manifest(payload), model, region, language, ValueError
    )
    # This transform receives the already claimed component carrier. It does
    # not search the reconstructed page or reopen source/config at replay.
    from tools.web_presentation import _transform_reference_figure

    _transform_reference_figure(
        soup,
        image=image,
        spec=component,
        source_path=source_path,
        composites=context,
    )
    figure = soup.select_one("figure.hb-reference-figure")
    if not isinstance(figure, Tag):
        raise ValueError(f"{spec.source_ref}: reference figure renderer produced no figure")
    if str(figure.get("data-source-fragment-sha256") or "") != str(
        payload["source_fragment_sha256"]
    ):
        raise ValueError(f"{spec.source_ref}: reference source-fragment hash disagrees")
    figure["data-component-id"] = spec.component_id
    return str(figure)


__all__ = ["render_reference_figure_component"]
