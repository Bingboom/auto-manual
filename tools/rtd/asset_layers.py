"""四类资产 (2026-11 design, step 12; REV-51): the private portal pages for the four asset layers.

The operator maintains four layers of assets, in this priority order: 产品信息, 内容与表现, 视觉媒体 and 语言
(``LAYERS``). Each layer page answers the same six questions in the same blocks (``BLOCKS``): 规模, 在哪里维护,
清单, 被谁使用, 来源与时间, 质量与缺口. Every figure is read at build time from data the site already reads, or
cheaply computed from it, and carries its date; a block with nothing real to show says 待统计 or 建设中 and never
an invented number. A layer's maturity status is not shown here: it will come from registered ledger rows.

产品信息 keeps its existing pages (产品矩阵 ``products/matrix``, 产品知识 ``products/knowledge``) and adds 属性字典
(``products/attributes``); the three share the layer header and a tab row. The other three layers are new pages
under ``assets/``. This module builds the views; ``tools/rtd/asset_media.py`` reads the media inventories and
``tools/rtd/portal.py`` yields the pages, on the private (combined) site only.
"""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from typing import Any

from tools.product_facts.export import ProductFactsError, load_attributes
from tools.rtd import asset_media
from tools.rtd.production_evidence import component_references
from tools.utils.path_utils import Paths, PathSegments, skeletons_of

PRODUCT_TABS = (("products/matrix", "产品矩阵"), ("products/attributes", "属性字典"),
                ("products/knowledge", "产品知识"))
ATTRIBUTES_PAGE, ATTRIBUTES_TEMPLATE = "products/attributes", "product_attributes.html"
LAYERS = (
    {"id": "product", "order": 1, "title": "产品信息", "icon": "product", "page": "products/matrix",
     "lead": "参数、功能、规格、使用限制、适用型号和地区差异。"},
    {"id": "content", "order": 2, "title": "内容与表现", "icon": "chapters", "page": "assets/content/index",
     "template": "asset_content.html", "lead": "说明书的骨架、通用章节、内容组件和版式样式。写一次，各型号、各语言复用。"},
    {"id": "media", "order": 3, "title": "视觉媒体", "icon": "image", "page": "assets/media/index",
     "template": "asset_media.html", "lead": "产品图、接口图、步骤插图、图标和共用符号。每项写明适用的型号、市场和语言，以及出处。"},
    {"id": "language", "order": 4, "title": "语言", "icon": "languages", "page": "assets/language/index",
     "template": "asset_language.html", "lead": "术语、翻译记忆、标准句对和术语规则。翻译和改写时先查这里，查不到的再新译。"},
)
BLOCKS = (("scale", "规模"), ("maintained", "在哪里维护"), ("inventory", "清单"), ("used-by", "被谁使用"),
          ("sources", "来源与时间"), ("gaps", "质量与缺口"))
PENDING, BUILDING = "待统计", "建设中"
TERMINOLOGY_RULES_CSV = "terminology_rules.csv"
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


def product_tabs(matrix_built: bool) -> list[tuple[str, str]]:
    return [(page, label) for page, label in PRODUCT_TABS if matrix_built or page != "products/matrix"]


# --- 产品信息 ----------------------------------------------------------------------------------------------------


def attributes_view(path: Path | None = None) -> dict[str, Any] | None:
    """The attribute keys the product-facts export reads, with their definitions; None when unreadable."""
    try:
        rows = load_attributes(path) if path else load_attributes()
    except (OSError, ValueError, ProductFactsError):
        return None
    items = [{"key": row["key"], "label": row["label"], "label_en": row.get("label_en") or "",
              "unit": row.get("unit") or "", "type": row.get("type") or "", "dimension": row.get("dimension") or "",
              "applies_to": list(row.get("applies_to") or []), "definition": row.get("definition") or ""}
             for row in rows]
    return {"total": len(items), "items": items,
            "scoped": sum(bool(item["applies_to"]) for item in items)}


def product_layer(matrix: dict[str, Any] | None, attributes: dict[str, Any] | None, *, topics: int | None,
                  build_date: str) -> dict[str, Any]:
    """The 产品信息 header and side blocks shared by its three tabs."""
    facts = (matrix or {}).get("facts") or {}
    return {**layer("product"), "build_date": build_date, "tabs": product_tabs(matrix is not None),
            "products": facts.get("products"), "models": facts.get("models"),
            "attributes": attributes["total"] if attributes else None, "topics": topics,
            "built_on": (matrix or {}).get("built_on") or "", "classified_on": (matrix or {}).get("classified_on") or ""}


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


def terminology_rules(path: Path) -> dict[str, Any] | None:
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            rows = [row for row in csv.DictReader(handle) if str(row.get("rule_id") or "").strip()]
    except (OSError, csv.Error, UnicodeDecodeError):
        return None
    items = [{"id": row["rule_id"].strip(), "lang": str(row.get("lang") or "").strip(),
              "avoid": str(row.get("deprecated_regex") or "").strip(), "prefer": str(row.get("preferred") or "").strip(),
              "note": str(row.get("note") or "").strip()} for row in rows]
    return {"total": len(items), "by_lang": Counter(item["lang"] for item in items).most_common(), "items": items}


def web_languages(publications: list[dict[str, Any]], labels: dict[str, str]) -> list[dict[str, Any]]:
    """Languages with a verified single-language Web manual, with their language versions; most first."""
    counts = Counter(str(p.get("lang")) for p in publications if p.get("language_scope") == "single" and p.get("lang"))
    return [{"code": code, "label": labels.get(code, code), "versions": count} for code, count in counts.most_common()]


def language_view(system: dict[str, Any] | None, publications: list[dict[str, Any]], *, root: Path,
                  labels: dict[str, str], build_date: str) -> dict[str, Any]:
    """语言: the translation-memory snapshot as 系统建设 reads it, the Web manual languages and the terminology rules."""
    corpus = (system or {}).get("corpus")
    rows = (corpus or {}).get("rows") or []
    tiles = {tile["key"]: tile for tile in (corpus or {}).get("tiles") or []}
    return {**layer("language"), "build_date": build_date, "corpus": corpus, "tiles": tiles,
            "corpus_fallback": ((system or {}).get("fallbacks") or {}).get("corpus") or "语料快照当前不可读",
            "registered": len(rows), "with_pairs": sum(1 for row in rows if row["count"]),
            "web": web_languages(publications, labels),
            "rules": terminology_rules(Paths(root=root).data_dir / TERMINOLOGY_RULES_CSV),
            "system_entry": system is not None}




# --- 知识库首页 (step 12, frame B) ---------------------------------------------------------------------------------


def _figure(value: object, unit: str, label: str, date: str) -> dict[str, Any]:
    """A home-card figure; None shows as 待统计, never 0."""
    return {"value": None if value is None else (f"{value:,}" if isinstance(value, int) else str(value)),
            "unit": unit, "label": label, "date": date}


def home_cards(product: dict[str, Any], content: dict[str, Any], media: dict[str, Any], language: dict[str, Any],
               chips: dict[str, dict[str, Any] | None]) -> list[dict[str, Any]]:
    """The four layer cards of 知识库首页, from the same views the layer pages render (no figure is read twice)."""
    built = f"构建 {product['build_date']}"
    chapters, components = content.get("chapters"), content.get("components")
    registry, symbols = media.get("registry"), media.get("symbols")
    corpus, tiles = language.get("corpus"), language.get("tiles") or {}
    exported = f"导出 {corpus['exported_at']}" if corpus else ""
    approved = (tiles.get("approved") or {}).get("value", "")
    cards = [
        {"figures": [_figure(product.get("models"), "个", "型号（产品矩阵）",
                             f"发布清单 {product['built_on']}" if product.get("built_on") else built),
                     _figure(product.get("attributes"), "项", "属性定义", built)],
         "where": "说明书规格表；产品信息矩阵建设中", "weak": "数值未经人工核实，也没有生效日期。"},
        {"figures": [_figure(chapters["pages"] if chapters else None, "篇", "通用章节", built),
                     _figure(components["total"] if components else None, "个", "登记组件", built)],
         "where": "工程仓库",
         "weak": (f"通用章节 {len(chapters['languages'])} 种语言，网页说明书 {content['web_languages']} 种。"
                  if chapters and content.get("web_languages") else "每个章节、组件用进了哪几本：待统计。")},
        {"figures": [_figure(registry["total"] if registry else None, "项", "已登记素材", built),
                     _figure(symbols["total"] if symbols else None, "个", "共用符号", built)],
         "where": "工程仓库 · 素材登记表", "weak": "素材没有版本字段，换图后分不出新旧。"},
        {"figures": [_figure((tiles.get("pairs") or {}).get("value") if corpus else None, "", "句对", exported),
                     _figure(approved or None if corpus else None, "", "句对已批准", exported)],
         "where": "翻译记忆库（飞书多维表）",
         "weak": _language_weak(corpus, approved)},
    ]
    entries = layer_entries(any(page == "products/matrix" for page, _ in product["tabs"]))
    return [{**entries[index], **card, "chip": chips.get(LAYERS[index]["id"])} for index, card in enumerate(cards)]


def _language_weak(corpus: dict[str, Any] | None, approved: str) -> str:
    if not corpus:
        return "语料快照不可读。"
    unapproved = f"{100 - int(approved[:-1])}% 句对未批准" if approved.endswith("%") and approved[:-1].isdigit() else ""
    stale = f"数字停在 {corpus['exported_at']} 的导出" if corpus.get("stale") else ""
    return "；".join(part for part in (unapproved, stale) if part) + "。" if unapproved or stale else "使用记录：待统计。"


__all__ = ["ATTRIBUTES_PAGE", "ATTRIBUTES_TEMPLATE", "BLOCKS", "BUILDING", "LAYERS", "PENDING", "PRODUCT_TABS",
           "attributes_view", "chapter_label", "components_view", "content_view", "home_cards", "language_view",
           "layer", "layer_entries", "media_view", "product_layer", "product_tabs", "shared_chapters",
           "terminology_rules", "web_languages"]
