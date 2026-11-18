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
                "path": None}
    return {"chips": chips, "capability_map": capability_map, "path": path,
            "main_line": {"text": data["main_line"], "umbrella": data["umbrella"], "source": path["link"]}}


def _fmt_int(value: int | None) -> str | None:
    return None if value is None else f"{value:,}"


def _count_tag(count: int, suffix: str) -> str:
    return f"{count} {suffix}" if count > 0 else ""


def _list_len(mapping: dict[str, Any] | None, key: str) -> int:
    return len(mapping.get(key) or []) if mapping else 0


def _str_field(mapping: dict[str, Any] | None, key: str) -> str:
    return str(mapping.get(key) or "") if mapping else ""


def _manual_counts(products: list[dict[str, Any]] | None) -> tuple[str | None, str, int]:
    """(formatted manual count, 'N 个市场 · M 语种' meta without code enumeration, single-language count)."""
    if not products:
        return None, "", 0
    markets = len({str(p["region"]).strip() for p in products if str(p.get("region") or "").strip()})
    languages = len({str(pub["lang"]).strip() for p in products
                     for pub in p.get("publications") or []
                     if pub.get("language_scope") == "single" and str(pub.get("lang") or "").strip()})
    parts = [part for part in (_count_tag(markets, "个市场"), _count_tag(languages, "语种")) if part]
    return f"{len(products):,}", " · ".join(parts), languages


def _corpus_pairs(corpus: dict[str, Any] | None) -> str | None:
    if not corpus:
        return None
    if corpus.get("approved"):
        return f"{corpus['counts']['pairs']:,}"
    tiles = {tile["key"]: tile for tile in corpus.get("tiles") or []}
    return (tiles.get("pairs") or {}).get("value")


def front_summary(matrix: dict[str, Any] | None, products: list[dict[str, Any]] | None,
                  corpus: dict[str, Any] | None) -> list[dict[str, Any]]:
    """知识资产's header summary capsule: products, published manuals and covered languages (None reads 暂无)."""
    facts = matrix.get("facts") or {} if matrix else {}
    manuals, _, manual_langs = _manual_counts(products)
    langs = _list_len(corpus, "listed") or manual_langs
    return [
        {"id": "models", "label": "收录机型", "value": _fmt_int(facts.get("products")), "unit": "款"},
        {"id": "manuals", "label": "正式说明书", "value": manuals, "unit": "份"},
        {"id": "languages", "label": "覆盖语种", "value": _fmt_int(langs or None), "unit": "种"},
    ]


def _product_card(matrix: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not matrix:
        return []
    facts = matrix.get("facts") or {}
    return [{
        "id": "product", "title": "产品信息", "icon": "product", "page": "products/matrix",
        "line": "按类别、系列与容量档查找机型，对比各市场规格并追溯说明书出处。",
        "value": _fmt_int(facts.get("products")), "unit": "款产品",
        "meta": _count_tag(_list_len(matrix, "categories"), "个产品类别"),
        "date": _str_field(matrix, "built_on"),
    }]


def _learning_stats(learning: dict[str, Any] | None) -> tuple[str | None, str]:
    if not learning or learning.get("content_missing"):
        return None, ""
    return _fmt_int(_list_len(learning, "topics")), _count_tag(_list_len(learning, "themes"), "个知识主题")


def front_cards(matrix: dict[str, Any] | None, learning: dict[str, Any] | None,
                corpus: dict[str, Any] | None, *,
                products: list[dict[str, Any]] | None = None,
                media_front: dict[str, Any] | None = None,
                market: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """知识资产's unified entry cards: icon, title, concise description, figure and count-only meta (None reads 暂无)."""
    manuals, manual_meta, _ = _manual_counts(products)
    topics, topic_meta = _learning_stats(learning)
    media_count = media_front.get("count") if media_front else None
    policy_records = _list_len(market, "records")
    countries = int(market.get("country_count") or 0) if market else 0
    return _product_card(matrix) + [
        {
            "id": "manuals", "title": "说明书资料库", "icon": "book", "page": "index",
            "line": "按市场区域、型号、商品简称或正文关键词查阅已发布的网页说明书。",
            "value": manuals, "unit": "份说明书", "meta": manual_meta, "date": "",
        },
        {
            "id": "corpus", "title": "语料库", "icon": "languages", "page": "assets/language/index",
            "line": "已批准的多语言标准句对与专业术语，供云文档与设计稿直接复用。",
            "value": _corpus_pairs(corpus), "unit": "组句对",
            "meta": _count_tag(_list_len(corpus, "listed"), "语种对照"),
            "date": _str_field(corpus, "exported_at"),
        },
        {
            "id": "knowledge", "title": "产品知识", "icon": "chapters", "page": "products/knowledge",
            "line": "围绕电池管理、逆变、充电、扩容与备电切换的最少必要工程原理。",
            "value": topics, "unit": "个知识点", "meta": topic_meta,
            "date": _str_field(learning, "latest_added"),
        },
        {
            "id": "media", "title": "视觉媒体", "icon": "image", "page": "assets/media/index",
            "line": "说明书共用的标准安规符号、无字化产品线稿与界面插图素材。",
            "value": _fmt_int(media_count), "unit": "件素材",
            "meta": _count_tag(_list_len(media_front, "types"), "类共用图元"),
            "date": _str_field(media_front, "updated"),
        },
        {
            "id": "policy", "title": "市场与政策", "icon": "globe", "page": "market/policy",
            "line": "各目标市场的安规准入、认证标志与环保法规参考资料。",
            "value": _fmt_int(policy_records or None), "unit": "条资料",
            "meta": _count_tag(countries, "个国家与地区"),
            "date": _str_field(market, "reviewed"),
        },
    ]


def asset_layer_pages(*, srcdir: Path, assets: Path, settings: dict, products: list[dict], system, matrix,
                      learning: dict[str, Any] | None, build_date: str, warn, design=None) -> dict:
    """The layer pages' contexts, 知识库首页's cards and the 系统建设 part.

    Since the front cleanup (2026-11-17) 产品信息 (产品库) has no lead; 内容与表现 is not shown (its address
    forwards to 设计规范); 视觉媒体 is a page for colleagues; 语言 is the 语料库 page; the
    former 属性字典 address forwards to 产品信息.
    """
    root = repo_root()
    publications = [item for product in products for item in product["publications"]]
    labels = dict(settings.get("language_labels") or {})
    extra = curated(assets, root, system, warn)
    chips = extra["chips"]
    media = {**layers.media_view(root, srcdir, publications, build_date=build_date), "chip": chips["media"]}
    media_front = front_view((design or {}).get("asset_library"), (design or {}).get("grounds") or {},
                             media["symbols"], build_date=build_date)
    language = layers.language_view(system, labels)
    moved = "products/matrix#matrix" if matrix else "products/knowledge#knowledge-list"
    pages = [
        ("products/attributes", {"moved_target": moved, "moved_title": "产品信息" if matrix else "产品知识"},
         "moved_page.html"),
        # 内容与表现 is not shown (operator, 2026-11-17: 「这个 不用放出来呀」); its address forwards to 设计规范.
        ("assets/content/index", {"moved_target": "workspace/design/index#overview" if design else "workspace/index#now",
                                  "moved_title": "设计规范" if design else "知识资产"}, "moved_page.html"),
        # 视觉媒体 is a front page for colleagues; its inventory (counts, hashes, gaps) sits at the foot of
        # 设计规范 › 图标与素材 (`media_inventory` below, passed to the design page by portal.py).
        ("assets/media/index", {"media": media_front}, "asset_media.html"),
        ("assets/language/index", {"layer": language}, "asset_language.html"),
    ]
    return {"pages": pages, "media_inventory": media, "media_front": media_front, "corpus": language["corpus"],
            "cards": front_cards(matrix, learning, language["corpus"], products=products, media_front=media_front),
            "system": {"asset_map": extra["capability_map"], "asset_path": extra["path"],
                       "asset_layers": layers.layer_entries(matrix is not None), "asset_chips": chips}}


__all__ = ["asset_layer_pages", "curated", "front_cards", "front_summary"]
