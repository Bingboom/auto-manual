"""四类资产 page assembly for the private portal: the layer pages, 知识库首页's layer cards and main line, and the
regrouped capability map and staged path of 系统建设 (REV-51; code-as-doc/dev/rtd_manual_portal/asset-layers.md).

``tools/rtd/portal.py`` calls :func:`asset_layer_pages` once per build and passes each part to its page. The views
come from ``asset_layers`` (figures), ``asset_media`` (media inventories) and ``asset_layer_data`` (wording, chips,
regrouping, path). A malformed ``asset_layers.yaml`` or a REV id the ledger lacks is logged as a warning: the
pages then show no chip, the home page no main line and 系统建设 its capability cards as before.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.rtd import asset_layer_data as layer_data
from tools.rtd import asset_layers as layers
from tools.rtd.system_workspace import CONTRACT_NAME, ContractError, load_contract, load_ledger
from tools.utils.path_utils import repo_root


def _ledger(assets: Path, root: Path):
    try:
        contract = load_contract(assets / CONTRACT_NAME)
        repositories = {k: str(v).rstrip("/") for k, v in (contract.get("repositories") or {}).items()}
        return load_ledger(contract, root), repositories
    except (ContractError, OSError):
        return None, {}


def _source_url(data: dict[str, Any], repositories: dict[str, str]) -> str:
    _, repo, path = data["source"].split(":", 2)
    return f"{repositories.get(repo, '')}/blob/main/{path}" if repositories.get(repo) else ""


def curated(assets: Path, root: Path, system: dict[str, Any] | None, warn) -> dict[str, Any]:
    """Chips, main line, the regrouped capability map and the path; empty parts when the data file is unusable.

    Without a readable contract or ledger no chip can be derived: every layer shows none, with a warning.
    """
    ledger, repositories = _ledger(assets, root)
    if ledger is None:
        warn("四类资产 chips skipped: the execution ledger (system_workspace.yaml now_next.source) is unreadable")
    try:
        data = layer_data.load_layer_data(assets)
        chips = layer_data.layer_chips(data, ledger)
        capability_map = layer_data.capability_map(data, system["cards"]) if system else None
        path = layer_data.path_view(data, ledger, _source_url(data, repositories))
    except layer_data.LayerDataError as exc:
        warn("四类资产 data skipped: %s", exc)
        return {"chips": dict.fromkeys(layer_data.LAYER_IDS), "main_line": None, "capability_map": None,
                "path": None}
    return {"chips": chips, "capability_map": capability_map, "path": path,
            "main_line": {"text": data["main_line"], "umbrella": data["umbrella"], "source": path["link"]}}


def asset_layer_pages(*, srcdir: Path, assets: Path, settings: dict, products: list[dict], system, matrix,
                      topics: int | None, build_date: str, coverage: dict[str, Any] | None, warn) -> dict:
    """Everything the four layers add to one build: page contexts, the home part and the 系统建设 part."""
    root = repo_root()
    publications = [item for product in products for item in product["publications"]]
    labels = dict(settings.get("language_labels") or {})
    web = layers.web_languages(publications, labels)
    attributes = layers.attributes_view()
    extra = curated(assets, root, system, warn)
    chips = extra["chips"]
    product = {**layers.product_layer(matrix, attributes, topics=topics, build_date=build_date),
               "chip": chips["product"]}
    content = {**layers.content_view(root, build_date=build_date, web_languages=len(web)), "chip": chips["content"]}
    media = {**layers.media_view(root, srcdir, publications, build_date=build_date), "chip": chips["media"]}
    language = {**layers.language_view(system, publications, root=root, labels=labels, build_date=build_date),
                "chip": chips["language"]}
    pages = [
        (layers.ATTRIBUTES_PAGE, {"product": product, "attributes": attributes}, layers.ATTRIBUTES_TEMPLATE),
        ("assets/content/index", {"layer": content}, "asset_content.html"),
        ("assets/media/index", {"layer": media}, "asset_media.html"),
        ("assets/language/index", {"layer": language}, "asset_language.html"),
    ]
    matrix_stage = next((stage for stage in (extra["path"] or {}).get("stages") or [] if stage["id"] == "matrix"), None)
    home = {"cards": layers.home_cards(product, content, media, language, chips),
            "main_line": extra["main_line"], "coverage": coverage, "matrix_stage": matrix_stage}
    return {"product": product, "pages": pages, "home": home,
            "system": {"asset_map": extra["capability_map"], "asset_path": extra["path"],
                       "asset_layers": layers.layer_entries(matrix is not None), "asset_chips": chips}}


__all__ = ["asset_layer_pages", "curated"]
