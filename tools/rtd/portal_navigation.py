"""说明书资料库 navigation: published manuals grouped by 产品类别, then 产品系列.

The grouping is the 网页文档 table's, read from the ``product_catalog``
snapshot (``tools/rtd/product_catalog.py``), so this page and the 产品矩阵 sort
products the same way; this module never infers a group. Categories and series
keep the table's order, and each category takes the anchor id and icon that
``settings.json`` names under ``catalog_categories`` (a category it does not
name gets ``category-<n>`` and a plain icon). A published model the snapshot
does not list lands in a visible 其他说明书 group, never disappears. Without a
usable snapshot the page falls back to the product types in ``categories``.
"""
from __future__ import annotations

import re

OTHER = {"id": "other", "title": "其他说明书", "icon": "other"}
_ID = re.compile(r"[a-z][a-z0-9-]*")
_NUMBER = re.compile(r"\d+")


def _model_key(product: dict) -> tuple:
    """Natural order inside a series: JE-100C before JE-1000F."""
    number = _NUMBER.search(product["model"])
    return (int(number.group(0)) if number else 0, product["model"], product["region"])


def _styles(settings: dict) -> dict[str, dict[str, str]]:
    styles = settings.get("catalog_categories", {})
    if not isinstance(styles, dict):
        raise ValueError("catalog_categories must map a category to its id and icon")
    for name, style in styles.items():
        if not isinstance(style, dict) or not _ID.fullmatch(str(style.get("id") or "")) \
                or not str(style.get("icon") or "").strip():
            raise ValueError(f"catalog_categories.{name} needs a lower-case id and an icon")
    ids = [style["id"] for style in styles.values()]
    if len(set(ids)) != len(ids) or OTHER["id"] in ids:
        raise ValueError("catalog_categories ids must be unique and not 'other'")
    return styles


def _category(cid: str, title: str, icon: str, series: list[tuple[str, list[dict]]]) -> dict:
    groups = [{"id": f"{cid}-{index}", "title": line, "products": sorted(members, key=_model_key)}
              for index, (line, members) in enumerate(series, 1) if members]
    return {"id": cid, "title": title, "icon": icon, "series": groups,
            "models": len({product["model"] for _, members in series for product in members})}


def library_view(settings: dict, products: list[dict], catalog: dict | None) -> dict:
    """Every product in one category and series: the snapshot's grouping, or the product types without it."""
    if catalog is None:
        labels = settings.get("category_labels", {})
        categories = [_category(f"category-{index}", labels.get(kind, kind), "other",
                                [("", [p for p in products if p["category"] == kind])])
                      for index, kind in enumerate(settings["categories"], 1)]
        return {"categories": [c for c in categories if c["series"]], "classified": False}
    styles = _styles(settings)
    categories = []
    for index, item in enumerate(catalog["categories"], 1):
        style = styles.get(item["name"], {"id": f"category-{index}", "icon": "other"})
        members = [p for p in products if p.get("product_category") == item["name"]]
        category = _category(style["id"], item["name"], style["icon"],
                             [(line, [p for p in members if p["product_series"] == line]) for line in item["series"]])
        if category["series"]:
            categories.append(category)
    unclassified = [p for p in products if not p.get("product_category")]
    if unclassified:
        categories.append(_category(OTHER["id"], OTHER["title"], OTHER["icon"], [("", unclassified)]))
    return {"categories": categories, "classified": True}
