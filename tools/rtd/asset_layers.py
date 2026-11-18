"""四类资产 (2026-11 design, step 12; REV-51): the private portal pages for the four asset layers.

The operator maintains four layers of assets, in this priority order: 产品信息, 内容与表现, 视觉媒体 and 语料库 (once 语言)
(``LAYERS``). Each layer page answers the same six questions in the same blocks (``BLOCKS``): 规模, 在哪里维护,
清单, 被谁使用, 来源与时间, 质量与缺口. Every figure is read at build time from data the site already reads, or
cheaply computed from it, and carries its date; a block with nothing real to show says 待统计 or 建设中 and never
an invented number. A layer's status chip comes only from registered ledger rows (asset_layers.yaml).

Since the front cleanup (2026-11-17) the six-block anatomy remains only in 视觉媒体's inventory (``media_view``), at
the foot of 设计规范; 内容与表现 is no longer built (its address forwards to 设计规范). 产品信息 (产品矩阵) and 产品知识
are front pages with no blocks, and 语言 is the plain 语料库 page (``language_view``). ``tools/rtd/asset_pages.py`` assembles the pages and the home cards; the
pages are built on the private (combined) site only.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from tools.rtd import asset_media
from tools.utils.path_utils import Paths

LAYERS = (
    {"id": "product", "order": 1, "title": "产品信息", "icon": "product", "page": "products/matrix",
     "lead": "参数、功能、规格、使用限制、适用型号和地区差异。"},
    {"id": "content", "order": 2, "title": "内容与表现", "icon": "chapters", "page": "assets/content/index",
     "lead": "说明书的骨架、通用章节、内容组件和版式样式。写一次，各型号、各语言复用。"},
    {"id": "media", "order": 3, "title": "视觉媒体", "icon": "image", "page": "assets/media/index",
     "lead": "产品图、接口图、步骤插图、图标和共用符号。每项写明适用的型号、市场和语言，以及出处。"},
    {"id": "language", "order": 4, "title": "语料库", "icon": "languages", "page": "assets/language/index",
     "lead": "翻译时先查这里，已经批准的句对和术语可以直接复用。"},
)
BLOCKS = (("scale", "规模"), ("maintained", "在哪里维护"), ("inventory", "清单"), ("used-by", "被谁使用"),
          ("sources", "来源与时间"), ("gaps", "质量与缺口"))
PENDING, BUILDING = "待统计", "建设中"


def layer(layer_id: str) -> dict[str, Any]:
    return next(item for item in LAYERS if item["id"] == layer_id)


def layer_entries(matrix_built: bool) -> list[dict[str, Any]]:
    """The sidebar's 资产 group: each layer's title, icon, order and entry page (产品信息 opens on 产品矩阵 if built)."""
    entries = [dict(item) for item in LAYERS]
    if not matrix_built:
        entries[0]["page"] = "products/knowledge"
    return entries


# --- 视觉媒体 ----------------------------------------------------------------------------------------------------


def media_view(root: Path, srcdir: Path, publications: list[dict[str, Any]], *, build_date: str) -> dict[str, Any]:
    return {**layer("media"), "build_date": build_date,
            "registry": asset_media.registry_view(Paths(root=root).data_dir / asset_media.ASSET_REGISTRY_CSV),
            "symbols": asset_media.symbols_view(root, srcdir, publications)}


# --- 语言 --------------------------------------------------------------------------------------------------------


def web_languages(publications: list[dict[str, Any]], labels: dict[str, str]) -> list[dict[str, Any]]:
    """Languages with a verified single-language Web manual, with their language versions; most first."""
    counts = Counter(str(p.get("lang")) for p in publications if p.get("language_scope") == "single" and p.get("lang"))
    return [{"code": code, "label": labels.get(code, code), "versions": count} for code, count in counts.most_common()]


def language_view(system: dict[str, Any] | None, labels: dict[str, str] | None = None) -> dict[str, Any]:
    """语料库: the translation-memory snapshot as 系统建设 reads it (totals, each language's pairs, export date).

    Each language is named as the manual library names it (``language_labels``: English, 日本語); a code the library
    does not list keeps the snapshot's label; a row's ``manual`` code (``system_workspace.yaml``) maps
    the translation memory's code to the library's. ``listed`` holds the languages the page lists (those with
    pairs or terms), so the page's language figure is the number of rows it shows.

    When the snapshot carries approved rows per language (``approved_only``, schema v1.1) the page counts approved
    entries only: the pair and term figures, each language's row and so the languages listed; ``approved`` is
    then true and the page drops its 其中 … 已批准 lines. 系统建设 keeps the whole-corpus figures.
    """
    corpus = (system or {}).get("corpus")
    if corpus:
        approved = corpus.get("approved_only")
        if approved:
            corpus = {**corpus, "rows": approved["rows"], "approved": True,
                      "counts": {**(corpus.get("counts") or {}), "pairs": approved["pairs"], "terms": approved["terms"]}}
        rows = [{**row, "label": labels.get(str(row.get("manual") or row.get("code")), row["label"])}
                for row in corpus.get("rows") or []] if labels else list(corpus.get("rows") or [])
        corpus = {**corpus, "rows": rows, "listed": [row for row in rows if row.get("count") or row.get("terms")]}
    tiles = {tile["key"]: tile for tile in (corpus or {}).get("tiles") or []}
    return {**layer("language"), "corpus": corpus, "tiles": tiles}


__all__ = ["BLOCKS", "BUILDING", "LAYERS", "PENDING", "language_view", "layer", "layer_entries", "media_view",
           "web_languages"]
