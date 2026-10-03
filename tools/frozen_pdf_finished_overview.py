"""Explicit, hash-pinned finished Overview panels over retained semantic copy."""
from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup

from tools.component_specs.overview import COMPONENT_ID
from tools.manual_ir.hashing import file_sha256
from tools.web.composite_manifest import WebCompositeEntry
from tools.web.embedded_components import render_embedded_web_component


def bind_finished_overview(book, bindings: dict, manifest: Path) -> None:
    """Validate all declared panels; package only the requested locale's pair."""
    panels = bindings.get("overview_finished_panels")
    book.overview_finished_panels = {}
    if panels is None:
        return
    if set(panels) != {"uk", "pt", "nl", "pl"}:
        raise ValueError("finished Overview must declare uk/pt/nl/pl")
    for language, views in panels.items():
        if set(views) != {"front", "right"}:
            raise ValueError(f"{language}: finished Overview requires front and right")
        for view, record in views.items():
            source = (manifest.parent / record["path"]).resolve()
            if file_sha256(source) != record["sha256"]:
                raise ValueError(f"finished Overview artwork changed: {language}/{view}")
            if not isinstance(record.get("captions_embedded"), bool):
                raise ValueError("finished Overview must declare whether view headings are embedded")
            if record.get("source_ai_sha256") != book.read("source_manifest.json")["original_source"]["sha256"]:
                raise ValueError("finished Overview source identity disagrees with intake")
            if language != book.language:
                continue
            asset = {**record, "path": str(source),
                     "asset_ref": f"assets/{record['sha256'][:12]}_{source.name}"}
            book.assets[f"overview.finished.{view}"] = asset
            book.overview_finished_panels[view] = asset
    if not book.overview_finished_panels:
        raise ValueError(f"no finished Overview for {book.language}")
    for view in book.overview_instance["views"]:
        mappings = view["composite_locales"]
        if not any(item["locale"] == book.language for item in mappings):
            mappings.append({"locale": book.language, "source_patterns": []})


def finished_overview_composites(book, pages) -> list[dict]:
    """Freeze the public semantic fragment hash, retaining all IR callout copy."""
    panels = getattr(book, "overview_finished_panels", {})
    if not panels:
        return []

    def components(value):
        if isinstance(value, dict):
            if value.get("component_spec", {}).get("component_id") == COMPONENT_ID:
                yield value
            for child in value.values():
                yield from components(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                yield from components(child)

    found = list(components([payload for page in pages for _, payload in page.blocks]))
    if len(found) != 1:
        raise ValueError("finished Overview requires exactly one semantic component")
    markup = render_embedded_web_component(
        found[0], source_path=Path("product_overview.rst"),
        model=book.target["model"], region=book.target["region"], language=book.language,
        composite_manifest=None, contract=book.contract, overview_instance=book.overview_instance,
    )
    soup = BeautifulSoup(markup, "html.parser")
    result = []
    for view in book.overview_instance["views"]:
        key = view["web_replace_key"]
        figure = soup.find("figure", attrs={"data-web-replace-key": key})
        if figure is None:
            raise ValueError(f"finished Overview semantic fragment missing: {key}")
        asset = panels[view["id"]]
        result.append(WebCompositeEntry(
            asset_key=f"overview.finished.{book.language}.{view['id']}",
            web_replace_key=key, model_scope=book.target["model"], region_scope=book.target["region"],
            locale=book.language, source_page=asset["source_page"], content_sha256=asset["sha256"],
            path=asset["asset_ref"], format="png",
            source_fragment_sha256=figure["data-source-fragment-sha256"],
        ).to_payload())
    return result
