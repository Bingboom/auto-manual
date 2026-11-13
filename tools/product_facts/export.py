"""Own-product facts from the published Web manuals, as one versioned export other systems read.

Every published model in every market is one record: the figures its first language edition's specification table
states (English first, then the 产品矩阵's language order, since the table rules read English, Chinese and Japanese
labels), each with the table row it was read from; that edition's version and file hash and every edition's page;
the product's class from the 产品分类 snapshot; and the model's capability switches in that market. Nothing is
carried from one market's manual to another: a product sold in two markets has two records, and where their figures
differ the export lists the difference for a person to confirm (a regional specification, or a slip in one manual).

The figures are what the manuals state, read by the 产品矩阵's rules (``tools/rtd/product_matrix.py``). They are
derived candidates, not verified product data (Hello_Docs_Positioning §4). ``attributes.json`` defines each figure
once, so a consumer, such as the competitive-analysis workbench, maps its own fields to these keys. The export
holds no project codes or SKUs and no time of its own: the same inputs give the same bytes.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path, PurePosixPath
from typing import Any

from tools.rtd import product_matrix as matrix
from tools.rtd.product_catalog import load_catalog
from tools.rtd.production_evidence import read_publications
from tools.rtd.system_data import CAPABILITIES_CSV, LANGUAGES_CSV, SystemDataError, read_targets
from tools.utils.path_utils import Paths, PathSegments, docs_publish_of, docs_publish_web_of

SCHEMA = "hello-docs-product-facts/v1"
ATTRIBUTES_SCHEMA = "hello-docs-product-attributes/v1"
ATTRIBUTES = Path(__file__).with_name("attributes.json")
ASSETS = Path(__file__).resolve().parents[1] / "rtd_portal_assets"
SETTINGS = "settings.json"
TYPES = ("number", "integer", "text", "boolean")
_KEY = re.compile(r"[a-z][a-z0-9_]*")
BASIS = "已发布网页说明书规格表所写的数值，按产品矩阵的规则读取，未经人工核实。"


class ProductFactsError(ValueError):
    """The inputs cannot give an export."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_sha256(value: Any) -> str:
    return _sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def load_attributes(path: Path = ATTRIBUTES) -> list[dict[str, Any]]:
    """The attribute dictionary, checked: unique lower-case keys, a known type and a 产品矩阵 reading each."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != ATTRIBUTES_SCHEMA or not isinstance(data.get("attributes"), list):
        raise ProductFactsError(f"{path.name}: expected {ATTRIBUTES_SCHEMA} with an attributes list")
    fields = set(matrix.read_specs([]))
    keys: set[str] = set()
    for item in data["attributes"]:
        key = item.get("key") if isinstance(item, dict) else None
        if not isinstance(key, str) or not _KEY.fullmatch(key) or key in keys:
            raise ProductFactsError(f"{path.name}: attribute key {key!r} is missing, malformed or repeated")
        keys.add(key)
        if item.get("type") not in TYPES or item.get("field") not in fields or not str(item.get("label") or "").strip():
            raise ProductFactsError(f"{path.name}: {key} needs a label, a type in {TYPES} and a 产品矩阵 field")
        scope = item.get("applies_to")
        if scope is not None and (not isinstance(scope, list) or not all(isinstance(c, str) and c for c in scope)):
            raise ProductFactsError(f"{path.name}: {key}.applies_to must list 产品类别 names")
    return data["attributes"]


def _value(raw: Any, kind: str) -> Any:
    """A stated figure in the attribute's type; None when the table does not state it (False included)."""
    if raw is None or raw == "" or raw is False:
        return None
    if kind == "boolean":
        return True
    if kind == "text":
        return str(raw)
    if kind == "integer":
        return int(raw)
    number = float(raw)
    return int(number) if number.is_integer() else round(number, 2)


def _applies(attribute: dict[str, Any], category: str | None) -> bool:
    """Whether a product of this category states the attribute; an unclassified model is read for every one."""
    scope = attribute.get("applies_to")
    return scope is None or category is None or category in scope


def read_facts(markup: str, attributes: list[dict[str, Any]], category: str | None
               ) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """Every figure a manual's table states, each with its row; the attributes its category states that it does not.

    ``applies_to`` only decides which missing figures are gaps: a stated figure is exported whatever the category.
    """
    pairs = matrix.spec_pairs(markup)
    figures = matrix.read_specs(pairs)
    rows = [(label, text, matrix.read_specs([(label, text)])) for label, text in pairs]
    facts: dict[str, dict[str, Any]] = {}
    unknown: list[str] = []
    for attribute in attributes:
        key, field, kind = attribute["key"], attribute["field"], attribute["type"]
        value = _value(figures[field], kind)
        if value is None:
            if _applies(attribute, category):
                unknown.append(key)
            continue
        quotes = [f"{label}: {text}" for label, text, parsed in rows if _value(parsed[field], kind) == value]
        facts[key] = {"value": value, "unit": attribute.get("unit"), "quote": quotes[0] if quotes else ""}
    return facts, unknown


def _manual_bytes(srcdir: Path, target: dict[str, Any]) -> bytes | None:
    """The published manual's bytes, or None when it is missing or its route leaves the Web source."""
    path = (srcdir / target["route"] / target["manual"]).resolve()
    if not path.is_relative_to(srcdir.resolve()) or not path.is_file():
        return None
    return path.read_bytes()


def _edition(short: str, marks: list[str]) -> tuple[str, str]:
    """The product a 商品简称 belongs to and its colour edition: E1000V2沙金色 -> (E1000V2, 沙金色)."""
    for mark in marks:
        if short.endswith(mark) and len(short) > len(mark):
            return short[: -len(mark)], mark
    return short, ""


def _product(entry: dict[str, Any] | None, marks: list[str]) -> dict[str, Any] | None:
    if entry is None:
        return None
    base, edition = _edition(entry["short"], marks)
    return {"short": entry["short"], "product": base, "edition": edition, "category": entry["category"],
            "series": entry["series"], "capacity_tier": entry.get("capacity", "")}


def _names(products: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    """Each model's catalog name per market, from the portal's manual catalog (``tools/rtd/portal.py``)."""
    names: dict[str, dict[str, str]] = defaultdict(dict)
    for product in products:
        names[product["model"]].setdefault(product["region"], product.get("name") or "")
    return names


def _name(model: str, market: str, context: dict[str, Any]) -> str:
    """The 产品矩阵's name: a ``names`` override, else this market's catalog name, else another market's, else the code."""
    override = context["config_names"].get(model)
    if override:
        return override
    by_market = context["names"].get(model, {})
    rank = {code: index for index, code in enumerate(context["market_order"])}
    for region in [market, *sorted(by_market, key=lambda code: (rank.get(code, len(rank)), code))]:
        if by_market.get(region):
            return matrix.display_name(by_market[region], model)
    return model


def _capabilities(root: Path) -> tuple[list[str], dict[tuple[str, str], list[bool]], dict[str, Any]]:
    """Capability names, each model/market's switches, and the registry's hash (its project column is not read out)."""
    paths = Paths(root)
    registry = paths.data_dir / CAPABILITIES_CSV
    try:
        names, rows = read_targets(registry, paths.data_dir / LANGUAGES_CSV, paths.review_dir)
    except (OSError, SystemDataError, KeyError) as exc:
        raise ProductFactsError(f"capability registry is unreadable: {exc}") from exc
    switches = {(row["model"], row["region"]): row["caps"] for row in rows}
    return names, switches, {"path": f"{PathSegments.DATA}/{CAPABILITIES_CSV}", "sha256": _sha256(registry.read_bytes())}


def _page(target: dict[str, Any]) -> str:
    return f"{target['route']}/{PurePosixPath(target['manual']).stem}.html"


def _editions(rows: list[dict[str, Any]], language_order: list[str]) -> list[dict[str, Any]]:
    """A market's language editions in the 产品矩阵's reading order: English first, then the configured order."""
    rank = {code: index for index, code in enumerate(language_order)}
    return sorted(rows, key=lambda row: (rank.get(row["lang"], len(rank)), row["lang"], row["route"]))


def _record(srcdir: Path, rows: list[dict[str, Any]], context: dict[str, Any], problems: list[str]) -> dict[str, Any]:
    """One model in one market: its product, the figures its first edition states, its capability switches."""
    editions = _editions(rows, context["language_order"])
    target = editions[0]
    model, region = target["model"], target["region"]
    data = _manual_bytes(srcdir, target)
    if data is None:
        problems.append(f"{model}/{region}/{target['lang']}: published manual {target['route']}/{target['manual']} "
                        "is not readable")
    entry = context["catalog"]["models"].get(model)
    if entry is None:
        problems.append(f"{model}: the 产品分类 snapshot does not list it, so its record has no product")
    product = _product(entry, context["marks"])
    markup = data.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n") if data else ""
    facts, unknown = read_facts(markup, context["attributes"], product and product["category"])
    page = _page(target)
    switches = context["switches"].get((model, region))
    return {
        "id": f"{model}/{region}", "model": model, "market": region, "name": _name(model, region, context),
        "product": product,
        "manual": {"language": target["lang"], "version": target.get("version") or None,
                   "published_at": target.get("built_at") or None, "page": page,
                   "url": f"{context['site']}/{page}" if context["site"] else None,
                   "source": f"{target['route']}/{target['manual']}", "sha256": _sha256(data) if data else None},
        "editions": [{"language": row["lang"], "version": row.get("version") or None, "page": _page(row)}
                     for row in editions],
        "facts": facts, "unknown": unknown,
        "capabilities": dict(zip(context["capability_names"], switches, strict=True)) if switches else None,
    }


def _guides(targets: list[dict[str, Any]], catalog: dict[str, Any]) -> list[dict[str, Any]]:
    """The 通用指南 and 快速指南: no product of their own, each with the models it applies to and its manuals."""
    pages: dict[str, list[dict[str, str]]] = defaultdict(list)
    for target in targets:
        if target["model"] in catalog.get("guides", {}):
            pages[target["model"]].append({"market": target["region"], "language": target["lang"],
                                           "page": _page(target)})
    return [{"code": code, "kind": guide["kind"], "short": guide["short"], "applies_to": guide["applies_to"],
             "manuals": pages[code]} for code, guide in sorted(catalog.get("guides", {}).items()) if pages[code]]


def differences(records: list[dict[str, Any]], attributes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Each product figure its manuals state differently, with the records behind each value."""
    seen: dict[tuple[str, str], dict[str, list[str]]] = defaultdict(dict)
    for record in records:
        if record["product"] is None:
            continue
        for key, fact in record["facts"].items():
            seen[(record["product"]["product"], key)].setdefault(json.dumps(fact["value"]), []).append(record["id"])
    order = {attribute["key"]: index for index, attribute in enumerate(attributes)}
    return [{"product": product, "attribute": key,
             "values": [{"value": json.loads(value), "records": ids} for value, ids in values.items()]}
            for (product, key), values in sorted(seen.items(), key=lambda item: (item[0][0], order[item[0][1]]))
            if len(values) > 1]


def _inputs(manifest: Path, catalog: dict[str, Any], registry: dict[str, Any], attributes_path: Path) -> dict:
    data = manifest.read_bytes()
    return {"publish_manifest": {"path": f"{PathSegments.DOCS}/{PathSegments.PUBLISH}/{PathSegments.PUBLISH_MANIFEST_JSON}",
                                 "sha256": _sha256(data), "built_at": json.loads(data).get("built_at") or None},
            "product_catalog": {"exported_at": catalog.get("exported_at"), "sha256": _json_sha256(catalog)},
            "capability_registry": registry,
            "attributes": {"schema": ATTRIBUTES_SCHEMA, "sha256": _sha256(attributes_path.read_bytes())}}


def build_export(root: Path, assets: Path = ASSETS, attributes_path: Path = ATTRIBUTES,
                 products: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """The export for the frozen Web publication under ``root``'s docs directory.

    ``products`` is the manual catalog the names come from; by default the portal reads it from the Web source.
    """
    docs = Paths(root).docs_dir
    manifest = docs_publish_of(docs) / PathSegments.PUBLISH_MANIFEST_JSON
    targets, _built_at = read_publications(manifest)
    if targets is None:
        raise ProductFactsError(f"{manifest} is missing or malformed")
    catalog, catalog_problems = load_catalog(assets)
    if catalog is None:
        raise ProductFactsError(f"the 产品分类 snapshot is unusable: {'; '.join(catalog_problems)}")
    settings = json.loads((assets / SETTINGS).read_text(encoding="utf-8"))
    config = json.loads((assets / matrix.CONFIG).read_text(encoding="utf-8"))
    attributes = load_attributes(attributes_path)
    capability_names, switches, registry = _capabilities(root)
    if products is None:
        from tools.rtd.portal import catalog as manual_catalog

        products = manual_catalog(docs_publish_web_of(docs), settings)
    context = {"catalog": catalog, "marks": list(config.get("variant_marks", [])), "attributes": attributes,
               "site": str(settings.get("site_base_url") or "").rstrip("/"), "capability_names": capability_names,
               "switches": switches, "language_order": list(config.get("language_order", [])),
               "market_order": list(config.get("region_order", [])), "names": _names(products),
               "config_names": dict(config.get("names", {}))}
    problems: list[str] = []
    ordered = sorted(targets, key=lambda t: (t["model"], t["region"], t["lang"], t["route"]))
    markets: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for target in ordered:
        if target["model"] not in catalog.get("guides", {}):
            markets[(target["model"], target["region"])].append(target)
    records = [_record(docs_publish_web_of(docs), rows, context, problems) for _key, rows in sorted(markets.items())]
    return _document(records, _guides(ordered, catalog), attributes, problems,
                     _inputs(manifest, catalog, registry, attributes_path), config, catalog)


def _document(records: list[dict[str, Any]], guides: list[dict[str, Any]], attributes: list[dict[str, Any]],
              problems: list[str], inputs: dict[str, Any], config: dict[str, Any],
              catalog: dict[str, Any]) -> dict[str, Any]:
    found = differences(records, attributes)
    products = {record["product"]["product"] for record in records if record["product"]}
    summary = {"records": len(records), "products": len(products), "models": len({r["model"] for r in records}),
               "facts": sum(len(r["facts"]) for r in records), "unknown": sum(len(r["unknown"]) for r in records),
               "differences": len(found), "problems": len(problems)}
    return {"schema": SCHEMA, "basis": BASIS,
            "inputs": inputs, "attributes": attributes,
            "classes": {"categories": catalog["categories"], "capacity_tiers": catalog.get("capacity_tiers", [])},
            "market_order": list(config.get("region_order", [])),
            "language_order": list(config.get("language_order", [])),
            "capability_labels": config.get("capability_labels", {}), "summary": summary,
            "records": records, "guides": guides, "differences": found, "problems": problems}


def encode(document: dict[str, Any]) -> bytes:
    """The export's bytes, exactly as ``workspace_snapshot.atomic_json`` writes them (sorted keys, two-space indent)."""
    return (json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


__all__ = ["ATTRIBUTES", "ProductFactsError", "SCHEMA", "build_export", "differences", "encode", "load_attributes",
           "read_facts"]
