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
from tools.rtd.asset_media import front_view
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
                "path": None, "product_value": ""}
    return {"chips": chips, "capability_map": capability_map, "path": path, "product_value": data["product_value"],
            "main_line": {"text": data["main_line"], "umbrella": data["umbrella"], "source": path["link"]}}


def front_cards(matrix: dict[str, Any] | None, learning: dict[str, Any] | None,
                corpus: dict[str, Any] | None) -> list[dict[str, Any]]:
    """知识库首页's three asset cards: name, one line, one figure with its date (None reads 待统计)."""
    facts = (matrix or {}).get("facts") or {}
    tiles = {tile["key"]: tile for tile in (corpus or {}).get("tiles") or []}
    topics = None if learning is None or learning.get("content_missing") else len(learning.get("topics") or [])
    cards = [{"id": "product", "title": "产品信息矩阵", "icon": "product", "page": "products/matrix",
              "line": "项目 · 属性 · 时间", "value": facts.get("products"), "unit": "款产品",
              "date": (matrix or {}).get("built_on") or ""}] if matrix else []
    return cards + [
        {"id": "knowledge", "title": "产品知识", "icon": "chapters", "page": "products/knowledge",
         "line": "功能 · 限制 · 关系", "value": topics, "unit": "个知识点",
         "date": (learning or {}).get("latest_added") or ""},
        {"id": "corpus", "title": "语料库", "icon": "languages", "page": "assets/language/index",
         "line": "句对 · 术语 · 复用", "value": (tiles.get("pairs") or {}).get("value"), "unit": "句对",
         "date": (corpus or {}).get("exported_at") or ""},
    ]


def asset_layer_pages(*, srcdir: Path, assets: Path, settings: dict, products: list[dict], system, matrix,
                      learning: dict[str, Any] | None, build_date: str, warn, design=None) -> dict:
    """The layer pages' contexts, 知识库首页's cards and the 系统建设 part.

    Since the front cleanup (2026-11-17) 产品信息 carries only the operator's value statement as its lead; 内容与表现
    is not shown (its address forwards to 设计规范); 视觉媒体 is a page for colleagues; 语言 is the 语料库 page; the
    former 属性字典 address forwards to 产品信息.
    """
    root = repo_root()
    publications = [item for product in products for item in product["publications"]]
    extra = curated(assets, root, system, warn)
    chips = extra["chips"]
    media = {**layers.media_view(root, srcdir, publications, build_date=build_date), "chip": chips["media"]}
    language = layers.language_view(system)
    moved = "products/matrix#matrix" if matrix else "products/knowledge#knowledge-list"
    pages = [
        ("products/attributes", {"moved_target": moved, "moved_title": "产品信息" if matrix else "产品知识"},
         "moved_page.html"),
        # 内容与表现 is not shown (operator, 2026-11-17: 「这个 不用放出来呀」); its address forwards to 设计规范.
        ("assets/content/index", {"moved_target": "workspace/design/index#overview" if design else "workspace/index#now",
                                  "moved_title": "设计规范" if design else "知识资产"}, "moved_page.html"),
        # 视觉媒体 is a front page for colleagues; its inventory (counts, hashes, gaps) sits at the foot of
        # 设计规范 › 图标与素材 (`media_inventory` below, passed to the design page by portal.py).
        ("assets/media/index", {"media": front_view((design or {}).get("asset_library"), (design or {}).get("grounds") or {},
                                                    media["symbols"], build_date=build_date)}, "asset_media.html"),
        ("assets/language/index", {"layer": language}, "asset_language.html"),
    ]
    return {"product": {"value": extra["product_value"]}, "pages": pages, "media_inventory": media,
            "cards": front_cards(matrix, learning, language["corpus"]),
            "system": {"asset_map": extra["capability_map"], "asset_path": extra["path"],
                       "asset_layers": layers.layer_entries(matrix is not None), "asset_chips": chips}}


__all__ = ["asset_layer_pages", "curated", "front_cards"]
