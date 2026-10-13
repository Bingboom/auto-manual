"""Build-time 产品矩阵 page: the products the published Web manuals describe.

``/products/matrix`` reads, at build time and from the repository only:

- ``docs/publish/publish_manifest.json``: the published routes, which give each
  model its markets, languages and source manual;
- the published manual of each model (English first, then the language order in
  ``product_matrix.json``): its SPECIFICATIONS / 仕様 / 规格 table gives
  capacity, AC output, cycle life, weight, solar power and IP rating, quoted as
  the manual prints them;
- the manual-center catalog for product names, and the ``navigation`` groups in
  ``settings.json`` for product lines;
- ``product_matrix.json`` for what no manual states: the line of a model the
  navigation does not list (marked * on the page), capacity tiers, name
  overrides, short notes, products without their own manual, and which partner
  products a manual names;
- ``data/model_capabilities.csv`` for the capability switches.

A pairing or companion product is shown only when its text still appears in the
manual it cites; anything dropped, and any product the page cannot place, is a
Sphinx warning. Without a readable manifest, or with a malformed config or
capability table, the page and its sidebar entry are skipped with a warning.
"""
from __future__ import annotations

import csv
import html
import json
import re
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from tools.rtd.production_evidence import read_publications
from tools.rtd.system_data import CAPABILITIES_CSV, LANGUAGES_CSV, read_targets
from tools.utils.path_utils import Paths, PathSegments, repo_root

PAGE = "products/matrix"
TEMPLATE = "product_matrix.html"
CONFIG = "product_matrix.json"
INFERRED_NOTE = "导航表未收录，按名称或同平台归入"
OTHER_GROUP = "其他"

_TAG = re.compile(r"<[^>]+>")
_BREAK = re.compile(r"<br\s*/?>", re.I)
_SPEC_PAIR = re.compile(r"<th[^>]*>(.*?)</th>\s*<td[^>]*>(.*?)</td>", re.S)
_SPEC_HEADING = re.compile(r"^#{1,6}[^\n]*(?:SPECIFICATIONS|Specifications|仕様|规格|規格)", re.M)
_NAME_SUFFIX = re.compile(r"\s*(?:取扱説明書|用户指南|User Manual)\s*$")

# Spec-table labels, matched case-insensitively against the row header.
CAPACITY = (r"^Capacity$", r"定格容量", r"^容量$")
WEIGHT = (r"^Weight$", r"^重量$", r"サイズ＆重量")
CYCLES = (r"Cycle Life", r"循環壽命", r"サイクル寿命")
SOLAR = (r"Maximum Power \(P", r"Peak Power \(P")
IP_RATING = (r"IP Rating", r"防水防塵", r"Protection Rating")
OUTPUT = (r"^Output Power$",)
EXPANSION = r"Expansion|拡張"
AC_ROW = r"AC Total|Total AC|AC Output|AC出力|AC 出力|× AC|x AC|AC 連接埠"
NOT_AC_OUTPUT = r"Expansion|拡張|パススルー|Bypass|Input|入力"
AC_TOTAL = r"Total|合計"
AC_TOTAL_VALUE = r"in Total|rated total|rated in total"
AC_RATED = (r"(\d[\d,]*)\s?W\s?(?:Rated|rated|in Total|Max\b)", r"額定功率\s?(\d[\d,]*)\s?W",
            r"A，\s?(\d[\d,]*)\s?W", r"(?<!瞬間)最大\s?(\d[\d,]*)\s?W")
AC_SURGE = (r"(\d[\d,]*)\s?W\s?(?:Surge|surge)", r"突波峰值\s?(\d[\d,]*)\s?W", r"瞬間最大\s?(\d[\d,]*)\s?W")


class ProductMatrixError(ValueError):
    """The committed config or data no longer has the shape this page reads."""


def _clean(fragment: str) -> str:
    text = _TAG.sub("", _BREAK.sub(" / ", fragment))
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def plain_text(markup: str) -> str:
    """The manual's words without markup, for checking what it names."""
    return re.sub(r"\s+", " ", html.unescape(_TAG.sub(" ", markup))).strip()


def spec_pairs(markup: str) -> list[tuple[str, str]]:
    """Header/value rows of the specification table, from its heading on."""
    heading = _SPEC_HEADING.search(markup)
    section = markup[heading.start():] if heading else markup
    pairs = [(_clean(label), _clean(value)) for label, value in _SPEC_PAIR.findall(section)]
    return [(label, value) for label, value in pairs if label and value and len(label) < 80]


def _value(pairs: list[tuple[str, str]], labels: Iterable[str]) -> str:
    for label, value in pairs:
        if any(re.search(pattern, label, re.I) for pattern in labels):
            return value
    return ""


def _number(text: str) -> float:
    return float(text.replace(",", ""))


def _ac_output(pairs: list[tuple[str, str]]) -> tuple[float | None, float | None]:
    """Whole-unit AC rated and surge power: a Total row wins over the largest single port."""
    rated = surge = None
    total_seen = False
    for label, value in pairs:
        if not re.search(AC_ROW, label, re.I) or re.search(NOT_AC_OUTPUT, label, re.I):
            continue
        is_total = bool(re.search(AC_TOTAL, label, re.I) or re.search(AC_TOTAL_VALUE, value, re.I))
        rated_match = next((m for m in (re.search(p, value) for p in AC_RATED) if m), None)
        surge_match = next((m for m in (re.search(p, value) for p in AC_SURGE) if m), None)
        if rated_match:
            power = _number(rated_match.group(1))
            if is_total:
                rated, total_seen = power, True
            elif not total_seen:
                rated = max(rated or 0, power)
        if surge_match:
            surge = max(surge or 0, _number(surge_match.group(1)))
    return rated, surge


def read_specs(pairs: list[tuple[str, str]]) -> dict[str, Any]:
    """The figures the page compares, or None where the table does not state them."""
    capacity = re.search(r"(\d[\d,.]*)\s?Wh", _value(pairs, CAPACITY))
    weight = _value(pairs, WEIGHT)
    kilograms = re.search(r"([\d.]+)\s?kg", weight)
    grams = re.search(r"(\d+)\s?g\b", weight)
    cycles = re.search(r"(\d{3,5})", _value(pairs, CYCLES))
    solar = re.search(r"STC\*?:\s*(\d+)\s?W", _value(pairs, SOLAR))
    ip_rating = re.search(r"IP\d\d", _value(pairs, IP_RATING))
    output = re.search(r"(\d+)\s?W", _value(pairs, OUTPUT))
    rated, surge = _ac_output(pairs)
    return {
        "wh": _number(capacity.group(1)) if capacity else None,
        "kg": float(kilograms.group(1)) if kilograms else (round(int(grams.group(1)) / 1000, 2) if grams else None),
        "cycles": int(cycles.group(1)) if cycles else None,
        "ac": rated, "surge": surge,
        "pv": int(solar.group(1)) if solar else None,
        "ip": ip_rating.group(0) if ip_rating else "",
        "out": int(output.group(1)) if output else None,
        "expansion": any(re.search(EXPANSION, label, re.I) for label, _ in pairs),
    }


def number(value: float | None) -> str:
    """Thousands separators, at most two decimals, no trailing zeros; — for a missing figure."""
    if value is None:
        return "—"
    return f"{value:,.2f}".rstrip("0").rstrip(".")


def display_name(name: str, model: str) -> str:
    """A catalog label without the model code or the manual-type suffix it sometimes carries."""
    for mark in (f" · {model}", f" — {model}", f"（{model}）", f"({model})"):
        name = name.replace(mark, "")
    return _NAME_SUFFIX.sub("", name).strip() or model


def load_config(assets: Path, settings: dict[str, Any]) -> dict[str, Any]:
    """The curated config with every line and group resolved against the navigation."""
    config = json.loads((assets / CONFIG).read_text(encoding="utf-8"))
    navigation = {group["id"]: group for groups in (settings.get("navigation") or {}).values() for group in groups}

    def resolve(entries: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
        resolved = []
        for entry in entries:
            group = navigation.get(entry["id"], {})
            title = entry.get("title") or group.get("title")
            if not title:
                raise ProductMatrixError(f"{CONFIG}: {kind} {entry['id']!r} is not a navigation group and has no title")
            resolved.append({**entry, "title": title, "models": list(group.get("models") or [])})
        return resolved

    lines, accessories = resolve(config["lines"], "line"), resolve(config["accessories"], "accessory group")
    ids = [entry["id"] for entry in lines + accessories]
    if len(set(ids)) != len(ids):
        raise ProductMatrixError(f"{CONFIG}: line and accessory ids must be unique")
    for model, group in config.get("assign", {}).items():
        if group not in ids:
            raise ProductMatrixError(f"{CONFIG}: {model} is assigned to unknown group {group!r}")
    tiers = config["tiers"]
    if not tiers or any("below" not in tier for tier in tiers[:-1]) or "below" in tiers[-1]:
        raise ProductMatrixError(f"{CONFIG}: every tier but the last needs 'below', and the last none")
    return {**config, "lines": lines, "accessories": accessories}


def _order(values: Iterable[str], preferred: list[str]) -> list[str]:
    rank = {value: index for index, value in enumerate(preferred)}
    return sorted(set(values), key=lambda value: (rank.get(value, len(rank)), value))


def _source(targets: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    languages = {code: index for index, code in enumerate(config["language_order"])}
    regions = {code: index for index, code in enumerate(config["region_order"])}
    return min(targets, key=lambda t: (languages.get(t["lang"], len(languages)), regions.get(t["region"], len(regions)),
                                       t["lang"], t["region"]))


def _manual(srcdir: Path, target: dict[str, Any]) -> str | None:
    path = (srcdir / target["route"] / target["manual"]).resolve()
    if not path.is_relative_to(srcdir.resolve()) or not path.is_file():
        return None
    return path.read_text(encoding="utf-8", errors="replace")


def _partner(item: str | dict[str, str]) -> tuple[str, str]:
    if isinstance(item, str):
        return item, item
    return item["label"], item.get("match") or item["label"]


def read_products(srcdir: Path, targets: list[dict[str, Any]], catalog: list[dict[str, Any]],
                  config: dict[str, Any], warnings: list[str]) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    """One row per published model, keyed by model, and each model's manual text."""
    by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for target in targets:
        by_model[target["model"]].append(target)
    names: dict[str, dict[str, str]] = defaultdict(dict)
    for product in catalog:
        names[product["model"]].setdefault(product["region"], product.get("name") or "")
    placed = {model: group["id"] for group in config["lines"] + config["accessories"] for model in group["models"]}
    products, texts = {}, {}
    for model, rows in sorted(by_model.items()):
        source = _source(rows, config)
        markup = _manual(srcdir, source)
        if markup is None:
            warnings.append(f"{model}: published manual {source['route']}/{source['manual']} is not readable")
            markup = ""
        texts[model] = plain_text(markup)
        regions = _order((row["region"] for row in rows), config["region_order"])
        catalog_name = next((names[model][region] for region in [source["region"], *regions] if names[model].get(region)), "")
        group = placed.get(model) or config.get("assign", {}).get(model)
        if group is None:
            warnings.append(f"{model}: no navigation group or {CONFIG} assignment; listed under {OTHER_GROUP}")
        products[model] = {
            "model": model,
            "name": config.get("names", {}).get(model) or display_name(catalog_name, model),
            "group": group, "inferred": model not in placed,
            "regions": regions, "langs": sorted({row["lang"] for row in rows}), "routes": len(rows),
            "source": f"{source['route']}（{source['lang']}）",
            "note": config.get("notes", {}).get(model, ""),
            **read_specs(spec_pairs(markup)),
        }
    return products, texts


def _tier(wh: float | None, tiers: list[dict[str, Any]]) -> int | None:
    if wh is None:
        return None
    return next(index for index, tier in enumerate(tiers) if "below" not in tier or wh < tier["below"])


def _energy_facts(product: dict[str, Any], line: dict[str, Any]) -> list[str]:
    facts = [f"{number(product['wh'])} Wh"]
    if product["ac"]:
        facts.append(f"AC {number(product['ac'])} W")
    elif line.get("fallback"):
        facts.append(line["fallback"])
    if product["kg"]:
        facts.append(f"{number(product['kg'])} kg")
    return facts


def _accessory_facts(product: dict[str, Any]) -> list[str]:
    facts = [product["note"]] if product["note"] else []
    if product["pv"]:
        facts.append(f"STC {product['pv']} W")
    if product["out"] and not product["note"]:
        facts.append(f"输出 {product['out']} W")
    if product["ip"]:
        facts.append(product["ip"])
    if product["kg"]:
        facts.append(f"{number(product['kg'])} kg")
    return facts


def _card(product: dict[str, Any], facts: list[str]) -> dict[str, Any]:
    return {key: product[key] for key in ("model", "name", "regions", "inferred", "source")} | {"facts": facts}


def positioning(products: dict[str, dict[str, Any]], config: dict[str, Any],
                warnings: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Energy products by line and capacity tier, and the accessory groups."""
    tiers = config["tiers"]
    lines = []
    for line in config["lines"]:
        cells: list[list[dict[str, Any]]] = [[] for _ in tiers]
        members = sorted((p for p in products.values() if p["group"] == line["id"]), key=lambda p: (p["wh"] or 0, p["model"]))
        for product in members:
            tier = _tier(product["wh"], tiers)
            if tier is None:
                warnings.append(f"{product['model']}: the manual states no capacity; left out of the positioning grid")
                continue
            cells[tier].append(_card(product, _energy_facts(product, line)))
        lines.append({"id": line["id"], "title": line["title"], "count": len(members), "cells": cells})
    groups = []
    for group in [*config["accessories"], {"id": None, "title": OTHER_GROUP, "models": []}]:
        # Navigation order first (it is curated), then the assigned models.
        rank = {model: index for index, model in enumerate(group["models"])}
        members = sorted((p for p in products.values() if p["group"] == group["id"]),
                         key=lambda p: (rank.get(p["model"], len(rank)), p["model"]))
        cards = [_card(p, _accessory_facts(p)) for p in members]
        if group["id"] is not None or cards:
            groups.append({"title": group["title"], "cards": cards})
    return lines, groups


def companions(products: dict[str, dict[str, Any]], texts: dict[str, str], config: dict[str, Any],
               warnings: list[str]) -> list[dict[str, Any]]:
    """Products without a manual of their own, shown only while the manual they cite names them."""
    groups: dict[str, list[dict[str, Any]]] = {}
    for item in config.get("companions", []):
        source = products.get(item["source"])
        if source is None or item["model"].lower() not in texts.get(item["source"], "").lower():
            warnings.append(f"{item['model']}: not named in the published {item['source']} manual; companion dropped")
            continue
        groups.setdefault(item["title"], []).append({
            "model": item["model"], "name": item["name"], "regions": source["regions"], "inferred": False,
            "source": source["source"], "facts": [item["spec"], f"见 {source['name']} 说明书"],
        })
    return [{"title": title, "cards": cards, "ghost": True} for title, cards in groups.items()]


def pairings(products: dict[str, dict[str, Any]], texts: dict[str, str], config: dict[str, Any],
             warnings: list[str]) -> list[dict[str, Any]]:
    """Partner products each manual names, as the config lists them and only while the text still names them."""
    rows = []
    for entry in config.get("pairings", []):
        model = entry["model"]
        if model not in products:
            warnings.append(f"{model}: pairing listed in {CONFIG} but no published manual")
            continue
        text = texts.get(model, "").lower()
        kept: dict[str, list[str]] = {"parts": [], "solar": []}
        for kind in kept:
            for item in entry.get(kind, []):
                label, match = _partner(item)
                if re.sub(r"（.*?）", "", match).strip().lower() in text:
                    kept[kind].append(label)
                else:
                    warnings.append(f"{model}: manual no longer names {match!r}; pairing dropped")
        if kept["parts"] or kept["solar"]:
            rows.append({"model": model, "name": products[model]["name"], **kept})
    return rows


def capability_rows(root: Path, products: dict[str, dict[str, Any]],
                    config: dict[str, Any]) -> tuple[list[str], list[dict[str, Any]]]:
    """Each model in the capability table, with all/some/none per switch across its regions."""
    paths = Paths(root)
    names, targets = read_targets(paths.data_dir / CAPABILITIES_CSV, paths.data_dir / LANGUAGES_CSV, paths.review_dir)
    by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for target in targets:
        by_model[target["model"]].append(target)
    line_rank = {line["id"]: index for index, line in enumerate(config["lines"])}

    def rank(model: str) -> tuple:
        product = products.get(model)
        if product is None:
            return (len(line_rank) + 1, 0, model)
        return (line_rank.get(product["group"], len(line_rank)), product["wh"] or 0, model)

    rows = []
    for model in sorted(by_model, key=rank):
        regions = [target["region"] for target in by_model[model]]
        cells = []
        for index, name in enumerate(names):
            supported = [target["region"] for target in by_model[model] if target["caps"][index]]
            if supported and len(supported) == len(regions):
                cells.append({"state": "all", "tip": f"{name}：全部 {len(regions)} 个区域"})
            elif supported:
                unsupported = [region for region in regions if region not in supported]
                cells.append({"state": "some",
                              "tip": f"{name}：{' · '.join(supported)} 支持；{' · '.join(unsupported)} 不支持"})
            else:
                cells.append({"state": "none", "tip": f"{name}：不支持"})
        product = products.get(model)
        rows.append({"model": model, "name": product["name"] if product else "", "regions": regions,
                     "published": product["regions"] if product else [], "cells": cells})
    labels = config.get("capability_labels", {})
    return [labels.get(name, name) for name in names], rows


def spec_rows(products: dict[str, dict[str, Any]], config: dict[str, Any]) -> list[dict[str, Any]]:
    """Energy products for the sortable spec table, smallest capacity first."""
    titles = {line["id"]: line["title"] for line in config["lines"]}
    energy = sorted((p for p in products.values() if p["group"] in titles), key=lambda p: (p["wh"] or 0, p["model"]))
    return [{
        "model": p["model"], "name": p["name"], "line": titles[p["group"]], "regions": p["regions"],
        "figures": [(p[key] or 0, number(p[key])) for key in ("wh", "ac", "surge", "cycles", "kg")],
        "expansion": p["expansion"], "langs": len(p["langs"]),
    } for p in energy]


def matrix_context(root: Path, srcdir: Path, manifest: Path, assets: Path, settings: dict[str, Any],
                   catalog: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Everything the page renders, or None without a readable publish manifest."""
    targets, built_at = read_publications(manifest)
    if targets is None:
        return None
    config = load_config(assets, settings)
    warnings: list[str] = []
    products, texts = read_products(srcdir, targets, catalog, config, warnings)
    lines, accessories = positioning(products, config, warnings)
    capability_names, capabilities = capability_rows(root, products, config)
    line_ids = {line["id"] for line in config["lines"]}
    pending = [row["model"] for row in capabilities if row["model"] not in products]
    return {
        "built_on": built_at[:10],
        "facts": {
            "models": len(products), "routes": len(targets),
            "energy": sum(1 for p in products.values() if p["group"] in line_ids),
            "accessories": sum(1 for p in products.values() if p["group"] not in line_ids),
            "pending": len(pending),
        },
        "markets": _order((region for p in products.values() for region in p["regions"]), config["region_order"]),
        "tiers": [tier["label"] for tier in config["tiers"]],
        "lines": lines, "accessories": accessories + companions(products, texts, config, warnings),
        "capability_names": capability_names, "capabilities": capabilities,
        "specs": spec_rows(products, config), "pairings": pairings(products, texts, config, warnings),
        "footnotes": list(config.get("footnotes", [])), "inferred_note": INFERRED_NOTE,
        "warnings": warnings,
    }


def product_matrix_page_context(app, assets: Path, settings: dict[str, Any],
                                catalog: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Context for PAGE, or None (with a warning) without a manifest or with drifted data."""
    from sphinx.util import logging as sphinx_logging

    logger = sphinx_logging.getLogger(__name__)
    srcdir = Path(app.srcdir)
    try:
        context = matrix_context(repo_root(), srcdir, srcdir.parent / PathSegments.PUBLISH_MANIFEST_JSON,
                                 assets, settings, catalog)
    except (ValueError, OSError, KeyError, TypeError, csv.Error) as exc:
        logger.warning("Product matrix page skipped: %s", exc)
        return None
    if context is None:
        # Expected before the first publish snapshot (the RTD bootstrap build), so not a warning.
        logger.info("Product matrix page skipped: no readable publish manifest")
        return None
    for message in context["warnings"]:
        logger.warning("Product matrix: %s", message)
    return context


__all__ = [
    "PAGE", "ProductMatrixError", "TEMPLATE", "capability_rows", "display_name", "load_config", "matrix_context",
    "number", "pairings", "plain_text", "positioning", "product_matrix_page_context", "read_products",
    "read_specs", "spec_pairs", "spec_rows",
]
