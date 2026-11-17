"""四类资产 (2026-11 design, step 12; REV-51): the private portal pages for the four asset layers.

The operator maintains four layers of assets, in this priority order: 产品信息, 内容与表现, 视觉媒体 and 语料库 (once 语言)
(``LAYERS``). Each layer page answers the same six questions in the same blocks (``BLOCKS``): 规模, 在哪里维护,
清单, 被谁使用, 来源与时间, 质量与缺口. Every figure is read at build time from data the site already reads, or
cheaply computed from it, and carries its date; a block with nothing real to show says 待统计 or 建设中 and never
an invented number. A layer's status chip comes only from registered ledger rows (asset_layers.yaml).

Since the front cleanup (2026-11-17) the six-block anatomy remains only on 内容与表现 and 视觉媒体, which sit under
维护 for maintainers. 产品信息 (产品矩阵) and 产品知识 are front pages with no blocks, and 语言 is the plain 语料库
page (``language_view``). ``tools/rtd/asset_pages.py`` assembles the pages and the home cards; the
pages are built on the private (combined) site only.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from tools.rtd import asset_media
from tools.rtd.production_evidence import component_references
from tools.utils.path_utils import Paths, PathSegments, skeletons_of

LAYERS = (
    {"id": "product", "order": 1, "title": "产品信息", "icon": "product", "page": "products/matrix",
     "lead": "参数、功能、规格、使用限制、适用型号和地区差异。"},
    {"id": "content", "order": 2, "title": "内容与表现", "icon": "chapters", "page": "assets/content/index",
     "template": "asset_content.html", "lead": "说明书的骨架、通用章节、内容组件和版式样式。写一次，各型号、各语言复用。"},
    {"id": "media", "order": 3, "title": "视觉媒体", "icon": "image", "page": "assets/media/index",
     "template": "asset_media.html", "lead": "产品图、接口图、步骤插图、图标和共用符号。每项写明适用的型号、市场和语言，以及出处。"},
    {"id": "language", "order": 4, "title": "语料库", "icon": "languages", "page": "assets/language/index",
     "template": "asset_language.html", "lead": "翻译时先查这里，已经批准的句对和术语可以直接复用。"},
)
BLOCKS = (("scale", "规模"), ("maintained", "在哪里维护"), ("inventory", "清单"), ("used-by", "被谁使用"),
          ("sources", "来源与时间"), ("gaps", "质量与缺口"))
PENDING, BUILDING = "待统计", "建设中"
# Shared chapters named in plain words; any other stem shows without its number prefix.
CHAPTER_LABELS = {"01_user_maintenance_instructions": "用户维护说明", "02_whats_in_the_box": "包装清单",
                  "06_ups_mode": "UPS 模式", "08_charging_methods": "充电方式",
                  "09_storage_and_maintenance": "存储与维护", "10_troubleshooting": "故障排除",
                  "11_warranty": "保修"}
DESIGN_TABS = (("overview", "概览"), ("colors", "颜色"), ("type", "字体"), ("components", "组件"),
               ("assets", "图标与素材"), ("print", "印刷规格"))


def layer(layer_id: str) -> dict[str, Any]:
    return next(item for item in LAYERS if item["id"] == layer_id)


def layer_entries(matrix_built: bool) -> list[dict[str, Any]]:
    """The sidebar's 资产 group: each layer's title, icon, order and entry page (产品信息 opens on 产品矩阵 if built)."""
    entries = [dict(item) for item in LAYERS]
    if not matrix_built:
        entries[0]["page"] = "products/knowledge"
    return entries


# --- 内容与表现 --------------------------------------------------------------------------------------------------


def chapter_label(stem: str) -> str:
    return CHAPTER_LABELS.get(stem) or stem.split("_", 1)[-1].replace("_", " ")


def shared_chapters(templates: Path) -> dict[str, Any] | None:
    """Shared chapter pages under ``page_shared``: per language, and each chapter's languages; None when absent."""
    root = templates / "page_shared"
    try:
        found = {lang.name: sorted(page.stem for page in lang.glob("*.rst")) for lang in sorted(root.iterdir())
                 if lang.is_dir()}
    except OSError:
        return None
    found = {lang: stems for lang, stems in found.items() if stems}
    if not found:
        return None
    stems = sorted(set().union(*map(set, found.values())))
    return {"pages": sum(len(rows) for rows in found.values()), "languages": list(found),
            "per_language": [{"lang": lang, "count": len(rows)} for lang, rows in found.items()],
            "chapters": [{"stem": stem, "label": chapter_label(stem),
                          "langs": [lang for lang, rows in found.items() if stem in rows]} for stem in stems]}


def _names(folder: Path, pattern: str = "*", *, dirs: bool) -> list[str] | None:
    try:
        return sorted(p.name for p in folder.glob(pattern) if (p.is_dir() if dirs else p.is_file()))
    except OSError:
        return None


def components_view(paths: Paths) -> dict[str, Any] | None:
    """The registered components, and the 产品总览 instances bound to models (the only use the site computes)."""
    import yaml

    try:
        registry = yaml.safe_load(paths.component_registry_contract.read_text(encoding="utf-8"))["components"]
    except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError):
        return None
    relationships, _ = component_references(paths)
    bound: dict[str, set[tuple[str, str]]] = {}
    for row in relationships or []:
        bound.setdefault(row["component"], set()).add((row["model"], row["region"]))
    rows = []
    for component_id, entry in registry.items():
        web = ((entry or {}).get("adapters") or {}).get("web") or {}
        targets = sorted(bound.get(component_id, set()))
        rows.append({"id": component_id, "kinds": list((entry or {}).get("source_kinds") or []),
                     "variants": len((entry or {}).get("variants") or []), "web": web.get("capability") or "",
                     "targets": [f"{model} · {region}" for model, region in targets] if targets else []})
    return {"total": len(rows), "rows": rows, "references_readable": relationships is not None,
            "with_targets": sum(bool(row["targets"]) for row in rows)}


def content_view(root: Path, *, build_date: str, web_languages: int | None = None) -> dict[str, Any]:
    paths = Paths(root=root)
    templates = paths.templates_dir
    try:
        recipes: list[Path] | None = [p for p in (templates / PathSegments.RECIPES).rglob("*") if p.is_file()]
    except OSError:
        recipes = None
    recipe_sets = _names(templates / PathSegments.RECIPES, dirs=True)
    families = _names(templates, "page_*", dirs=True)
    return {**layer("content"), "build_date": build_date, "chapters": shared_chapters(templates),
            "skeletons": _names(skeletons_of(root), dirs=True), "recipes": len(recipes) if recipes else None, "recipe_sets": recipe_sets or [],
            "families": [name for name in families or [] if name != "page_shared"] if families is not None else None,
            "components": components_view(paths), "design_tabs": DESIGN_TABS, "web_languages": web_languages}


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
    the translation memory's code to the library's.
    """
    corpus = (system or {}).get("corpus")
    if corpus and labels:
        rows = [{**row, "label": labels.get(str(row.get("manual") or row.get("code")), row["label"])}
                for row in corpus.get("rows") or []]
        corpus = {**corpus, "rows": rows}
    tiles = {tile["key"]: tile for tile in (corpus or {}).get("tiles") or []}
    return {**layer("language"), "corpus": corpus, "tiles": tiles}


__all__ = ["BLOCKS", "BUILDING", "LAYERS", "PENDING", "chapter_label", "components_view", "content_view",
           "language_view", "layer", "layer_entries", "media_view", "shared_chapters", "web_languages"]
