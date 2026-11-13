"""Build-time 产品矩阵 page: the products the published Web manuals describe, grouped as the 网页文档 table groups them.

``/products/matrix`` reads, at build time and from the repository only:

- the ``product_catalog`` snapshot (``tools/rtd/product_catalog.py``): each model's 产品类别, 产品系列, 容量档
  and 商品简称, and the 容量档 order. One product is one 商品简称; a model whose 商品简称 ends in a ``variant_marks`` word (沙金色 …) is
  that product's colour edition, and a model the snapshot records as sharing another model's pages
  (``pages_of``) shows as a row that links to those pages;
- ``docs/publish/publish_manifest.json``: the published routes, which give each model its markets, languages
  and manual pages;
- the published manual of each model (English first, then the language order in ``product_matrix.json``): its
  SPECIFICATIONS / 仕様 / 规格 table gives capacity, AC output, solar power, IP rating, weight and expansion,
  quoted as the manual prints them;
- ``product_matrix.json``: market letters and labels, variant marks, name overrides, short
  notes, and the partner products each manual names (``pairings``). An item links to a product only through
  its ``product`` key (that product's 商品简称); a label alone never links, since "Explorer 1000 Plus" may mean
  either generation;
- ``data/model_capabilities.csv`` for each model's 功能.

The page has a tab per 产品类别 with a grid of 产品系列 × the 容量档 its products use (one column where none has
a 容量档; a 容量未注明 column for a product without one beside products with one) and, per product, a detail that opens under its 系列 row: every model with its 商品简称, figures and a
link per market, the capability switches, the partner products in both directions, and the 通用指南 whose 适用产品
lists one of its models, and its own 快速指南 (a guide is no product and has no card of its own). A pairing shows only
while its text still appears in the manual it cites; anything dropped, and any published model the snapshot does
not list (shown under 其他), is a Sphinx warning, as is a 容量档 the manual's stated capacity does not fit. ``lines``, ``accessories`` and ``assign`` stay for the 产品知识
page (``positioning_groups``), and an ``evidence`` assignment whose quote has left its manual still warns here.
Without a readable manifest or a usable snapshot, or with a malformed config or capability table, the page and its
sidebar entry are skipped.
"""
from __future__ import annotations

import csv
import html
import json
import re
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path, PurePosixPath
from typing import Any

from tools.rtd.production_evidence import read_publications
from tools.rtd.system_data import CAPABILITIES_CSV, LANGUAGES_CSV, read_targets
from tools.utils.path_utils import Paths, PathSegments, repo_root

PAGE = "products/matrix"
TEMPLATE = "product_matrix.html"
CONFIG = "product_matrix.json"
OTHER = "其他"
UNSORTED = "未分类"
UNSTATED = "容量未注明"
# Where a quoted manual sentence starts or ends: sentence ends and Markdown headings.
_SENTENCE_MARKS = (". ", "。", "! ", "? ", "# ")

_TAG = re.compile(r"<[^>]+>")
_BREAK = re.compile(r"<br\s*/?>", re.I)
_SPEC_PAIR = re.compile(r"<th[^>]*>(.*?)</th>\s*<td[^>]*>(.*?)</td>", re.S)
# The source-layout spec lists (JE-2000A): a row of two paragraphs, label then value.
_SPEC_ROW = re.compile(r'data-source-layout="spec-row"[^>]*>\s*<p[^>]*>(.*?)</p>\s*<p[^>]*>(.*?)</p>', re.S)
_SPEC_HEADING = re.compile(r"^#{1,6}[^\n]*(?:SPECIFICATIONS|Specifications|仕様|规格|規格)", re.M)
_NAME_SUFFIX = re.compile(r"\s*(?:取扱説明書|用户指南|User Manual)\s*$")

# Spec-table labels, matched case-insensitively against the row header.
CAPACITY = (r"^Capacity$", r"^Internal Battery$", r"定格容量", r"^容量$")
WEIGHT = (r"^Weight$", r"^重量$", r"サイズ＆重量")
CYCLES = (r"Cycle Life", r"循環壽命", r"サイクル寿命")
SOLAR = (r"Maximum Power \(P", r"Peak Power \(P")
IP_RATING = (r"IP Rating", r"防水防塵", r"Protection Rating")
OUTPUT = (r"^Output Power$",)
EXPANSION = r"Expansion|拡張"
AC_ROW = r"AC Total|Total AC|AC Output|AC出力|AC 出力|× AC|x AC|AC 連接埠"
# A "Total Output" row is the whole unit's AC output when it also states a surge figure (JE-1000D).
TOTAL_OUTPUT = r"^Total Output$"
NOT_AC_OUTPUT = r"Expansion|拡張|パススルー|Bypass|Input|入力"
AC_TOTAL = r"Total|合計"
AC_TOTAL_VALUE = r"in Total|rated total|rated in total"
AC_RATED = (r"(\d[\d,]*)\s?W\s?(?:Rated|rated|in Total|Max\b)", r"額定功率\s?(\d[\d,]*)\s?W",
            r"A，\s?(\d[\d,]*)\s?W", r"(?<!瞬間)最大\s?(\d[\d,]*)\s?W")
AC_SURGE = (r"(\d[\d,]*)\s?W\s?(?:peak\s)?(?:Surge|surge)", r"突波峰值\s?(\d[\d,]*)\s?W", r"瞬間最大\s?(\d[\d,]*)\s?W")


class ProductMatrixError(ValueError):
    """The committed config or data no longer has the shape this page reads."""


def _clean(fragment: str) -> str:
    text = _TAG.sub("", _BREAK.sub(" / ", fragment))
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def plain_text(markup: str) -> str:
    """The manual's words without markup, for checking what it names."""
    return re.sub(r"\s+", " ", html.unescape(_TAG.sub(" ", markup))).strip()


def spec_pairs(markup: str) -> list[tuple[str, str]]:
    """Header/value rows of the specification table, from its heading on; a label's trailing colon is dropped."""
    heading = _SPEC_HEADING.search(markup)
    section = markup[heading.start():] if heading else markup
    rows = _SPEC_PAIR.findall(section) or _SPEC_ROW.findall(section)
    pairs = [(_clean(label).rstrip(":：").strip(), _clean(value)) for label, value in rows]
    return [(label, value) for label, value in pairs if label and value and len(label) < 80]


def _value(pairs: list[tuple[str, str]], labels: Iterable[str]) -> str:
    for label, value in pairs:
        if any(re.search(pattern, label, re.I) for pattern in labels):
            return value
    return ""


def _number(text: str) -> float:
    return float(text.replace(",", ""))


def _ac_row(label: str, value: str) -> bool | None:
    """None for a row that is not AC output; else whether it states the whole unit's total."""
    if re.search(TOTAL_OUTPUT, label, re.I) and any(re.search(pattern, value) for pattern in AC_SURGE):
        return True
    if not re.search(AC_ROW, label, re.I) or re.search(NOT_AC_OUTPUT, label, re.I):
        return None
    return bool(re.search(AC_TOTAL, label, re.I) or re.search(AC_TOTAL_VALUE, value, re.I))


def _ac_output(pairs: list[tuple[str, str]]) -> tuple[float | None, float | None]:
    """Whole-unit AC rated and surge power: a Total row wins over the largest single port."""
    rated = surge = None
    total_seen = False
    for label, value in pairs:
        is_total = _ac_row(label, value)
        if is_total is None:
            continue
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
    # 「3,000回」 and 「4000 cycles」: a thousands separator is part of the count, never its end.
    cycles = re.search(r"(\d{1,2}(?:,\d{3})+|\d{3,5})", _value(pairs, CYCLES))
    solar = re.search(r"STC\*?:\s*(\d+)\s?W", _value(pairs, SOLAR))
    ip_rating = re.search(r"IP\d\d", _value(pairs, IP_RATING))
    output = re.search(r"(\d+)\s?W", _value(pairs, OUTPUT))
    rated, surge = _ac_output(pairs)
    return {
        "wh": _number(capacity.group(1)) if capacity else None,
        "kg": float(kilograms.group(1)) if kilograms else (round(int(grams.group(1)) / 1000, 2) if grams else None),
        "cycles": int(cycles.group(1).replace(",", "")) if cycles else None,
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


def _assignments(raw: dict[str, Any], lines: list[dict[str, Any]], accessories: list[dict[str, Any]],
                 ids: list[str]) -> dict[str, dict[str, Any]]:
    """Each assigned model as {"line", "evidence"?} or {"same_as"}, checked against the lines."""
    evidence_lines = {entry["id"] for entry in lines if entry.get("evidence")}
    navigation_models = {model for entry in lines + accessories for model in entry["models"]}
    assign = {}
    for model, entry in raw.items():
        entry = {"line": entry} if isinstance(entry, str) else dict(entry)
        if "same_as" in entry:
            # One product in another market follows the operator's own placement of it.
            if "line" in entry or entry["same_as"] not in navigation_models:
                raise ProductMatrixError(f"{CONFIG}: {model} same_as must name a navigation-listed model, "
                                         "without a line of its own")
        elif entry.get("line") not in ids:
            raise ProductMatrixError(f"{CONFIG}: {model} is assigned to unknown group {entry.get('line')!r}")
        elif entry["line"] in evidence_lines and not str(entry.get("evidence") or "").strip():
            raise ProductMatrixError(f"{CONFIG}: {model} needs an evidence quote from its manual for {entry['line']!r}")
        assign[model] = entry
    return assign


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
    assign = _assignments(config.get("assign", {}), lines, accessories, ids)
    _check_display(config)
    return {**config, "lines": lines, "accessories": accessories, "assign": assign}


def _check_display(config: dict[str, Any]) -> None:
    """The page's market letters and labels, and the words that name a colour edition."""
    markets = config.get("markets", {})
    if not isinstance(markets, dict) or not all(
            isinstance(m, dict) and str(m.get("letter") or "").strip() and str(m.get("label") or "").strip()
            for m in markets.values()):
        raise ProductMatrixError(f"{CONFIG}: markets must give each market a letter and a label")
    marks = config.get("variant_marks", [])
    if not isinstance(marks, list) or not all(isinstance(mark, str) and mark.strip() for mark in marks):
        raise ProductMatrixError(f"{CONFIG}: variant_marks must list the words that name a colour edition")


def positioning_groups(assets: Path, settings: dict[str, Any]) -> dict[str, set[str]]:
    """Each group id with the models placed there: navigation, the config's lines and groups, then ``assign``.

    The 产品知识 page reads this, so a model the navigation does not list still
    finds its knowledge. A navigation-listed model keeps its navigation group and
    a ``same_as`` model joins the groups of the model it names, as on the matrix page.
    Only the config is read: an evidence line keeps its assigned models here, and
    the quote is checked where the manual is read. Any missing, unreadable or
    malformed config raises ProductMatrixError.
    """
    try:
        config = load_config(assets, settings)
    except ProductMatrixError:
        raise
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        raise ProductMatrixError(f"{CONFIG} is unreadable or malformed: {type(exc).__name__}: {exc}") from exc
    groups = {group["id"]: set(group["models"]) for rows in (settings.get("navigation") or {}).values() for group in rows}
    for entry in config["lines"] + config["accessories"]:
        groups.setdefault(entry["id"], set()).update(entry["models"])
    placed = set().union(*groups.values())
    for model, entry in config["assign"].items():
        if model in placed:
            continue
        if "same_as" in entry:
            keys = [key for key, members in groups.items() if entry["same_as"] in members]
        else:
            keys = [entry["line"]]
        for key in keys:
            groups[key].add(model)
    return groups


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


def evidence_excerpt(text: str, quote: str, limit: int = 140) -> str:
    """The manual sentence holding a quote (case and spacing ignored), or "" when the manual lacks it."""
    words = quote.split()
    if not words:
        return ""
    match = re.search(r"\s+".join(re.escape(word) for word in words), text, re.I)
    if match is None:
        return ""
    # Widen to the enclosing sentence or heading, but never past `limit` characters on either side.
    before = [text.rfind(mark, 0, match.start()) + len(mark) for mark in _SENTENCE_MARKS
              if text.rfind(mark, 0, match.start()) >= 0]
    after = [text.find(mark, match.end()) + len(mark.rstrip()) for mark in _SENTENCE_MARKS
             if text.find(mark, match.end()) >= 0]
    start = max([match.start() - limit, *before], default=match.start() - limit)
    end = min([match.end() + limit, *after], default=match.end() + limit)
    start, end = max(0, start), min(len(text), end)
    clipped_start = start == match.start() - limit and start > 0
    clipped_end = end == match.end() + limit and end < len(text)
    return ("…" if clipped_start else "") + text[start:end].strip(" #") + ("…" if clipped_end else "")


def _partner(item: str | dict[str, str]) -> tuple[str, str]:
    if isinstance(item, str):
        return item, item
    return item["label"], item.get("match") or item["label"]


_TIER = re.compile(r"(\d+(?:\.\d+)?)度(电|以下)")


def capacity_mismatch(tier: str, wh: float | None) -> bool:
    """Whether a manual's stated capacity does not fit its 容量档: 「X度电」 within a quarter of X kWh, 「X度以下」
    under X kWh. A tier the rule cannot read, or a manual without a capacity, is never a mismatch."""
    match = _TIER.fullmatch(tier)
    if wh is None or not match:
        return False
    kwh = float(match.group(1))
    return wh >= kwh * 1000 if match.group(2) == "以下" else abs(wh / 1000 - kwh) > kwh / 4




# Figures a product detail can show, in column order; a column shows only when one of the product's models states it.
COLUMNS = (("wh", "容量"), ("ac", "AC 额定 / 峰值"), ("pv", "太阳能功率"), ("out", "输出"), ("ip", "防护"),
           ("kg", "重量"), ("expansion", "扩展口"), ("note", "说明"))
_UNITS = {"wh": "{} Wh", "pv": "STC {} W", "out": "{} W", "kg": "{} kg"}


def _figure(row: dict[str, Any], key: str) -> str:
    """One model's figure for a detail column, or — when its manual does not state it."""
    value = row.get(key)
    if not value:
        return "—"
    if key == "ac":
        return f"{number(value)} / {number(row['surge'])} W" if row.get("surge") else f"{number(value)} W"
    if key in _UNITS:
        return _UNITS[key].format(number(value))
    return "有" if key == "expansion" else str(value)


def _market(region: str, config: dict[str, Any]) -> dict[str, str]:
    return config.get("markets", {}).get(region) or {"letter": region, "label": region}


def _pages(rows: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Each market's page to link (English first, then the configured language order) and its languages."""
    rank = {code: index for index, code in enumerate(config["language_order"])}
    pages: dict[str, dict[str, Any]] = {}
    for region in _order((row["region"] for row in rows), config["region_order"]):
        editions = sorted((row for row in rows if row["region"] == region),
                          key=lambda row: (rank.get(row["lang"], len(rank)), row["lang"]))
        pages[region] = {"doc": f"{editions[0]['route']}/{PurePosixPath(editions[0]['manual']).stem}",
                         "langs": [row["lang"] for row in editions]}
    return pages


def read_models(srcdir: Path, targets: list[dict[str, Any]], catalog: list[dict[str, Any]], config: dict[str, Any],
                warnings: list[str]) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    """One row per published model, keyed by model, and each model's manual text."""
    by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for target in targets:
        by_model[target["model"]].append(target)
    names: dict[str, dict[str, str]] = defaultdict(dict)
    for product in catalog:
        names[product["model"]].setdefault(product["region"], product.get("name") or "")
    models, texts = {}, {}
    for model, rows in sorted(by_model.items()):
        source = _source(rows, config)
        markup = _manual(srcdir, source)
        if markup is None:
            warnings.append(f"{model}: published manual {source['route']}/{source['manual']} is not readable")
            markup = ""
        texts[model] = plain_text(markup)
        pages = _pages(rows, config)
        catalog_name = next((names[model][region] for region in [source["region"], *pages] if names[model].get(region)), "")
        models[model] = {
            "model": model, "name": config.get("names", {}).get(model) or display_name(catalog_name, model),
            "regions": list(pages), "pages": pages, "note": config.get("notes", {}).get(model, ""),
            **read_specs(spec_pairs(markup)),
        }
    return models, texts


def _check_evidence(config: dict[str, Any], texts: dict[str, str], warnings: list[str]) -> None:
    """产品知识 places an ``evidence`` assignment on its manual's word: warn when the manual no longer has it."""
    for model, entry in config["assign"].items():
        quote = str(entry.get("evidence") or "").strip()
        if quote and model in texts and not evidence_excerpt(texts[model], quote):
            warnings.append(f"{model}: manual does not state {quote!r} ({CONFIG} assign, read by 产品知识)")


def _edition(short: str, marks: list[str]) -> tuple[str, str]:
    """The product a 商品简称 belongs to and its colour edition: E1000V2沙金色 -> (E1000V2, 沙金色)."""
    for mark in marks:
        if short.endswith(mark) and len(short) > len(mark):
            return short[: -len(mark)], mark
    return short, ""


def _rows_by_product(models: dict[str, dict[str, Any]], catalog: dict[str, Any], config: dict[str, Any],
                     warnings: list[str]) -> dict[str, list[dict[str, Any]]]:
    """Model rows keyed by their product's 商品简称: published models, then editions sold on another model's pages."""
    entries, marks = catalog["models"], list(config.get("variant_marks", []))
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for model, row in models.items():
        entry = entries.get(model)
        if entry is None:
            warnings.append(f"{model}: the 产品分类 snapshot does not list it; shown under {OTHER}")
            entry = {"category": OTHER, "series": UNSORTED, "short": model}
        base, edition = _edition(entry["short"], marks)
        grouped[base].append({**row, "short": entry["short"], "edition": edition, "category": entry["category"],
                              "series": entry["series"], "tier": entry.get("capacity", "")})
    for model, entry in entries.items():
        host = models.get(entry.get("pages_of", ""))
        if model in models or host is None:
            continue
        base, edition = _edition(entry["short"], marks)
        regions = _order({route.split("/")[1] for route in entry["routes"]} & set(host["pages"]), config["region_order"])
        grouped[base].append({"model": model, "name": host["name"], "short": entry["short"], "edition": edition,
                              "category": entry["category"], "series": entry["series"],
                              "tier": entry.get("capacity", ""), "shares": host["model"],
                              "regions": regions, "pages": {region: host["pages"][region] for region in regions}})
    return grouped


def _anchor(short: str, taken: set[str]) -> str:
    key = "p-" + re.sub(r"[\s#/?%]+", "-", short)
    while key in taken:
        key += "-"
    taken.add(key)
    return key


def build_products(models: dict[str, dict[str, Any]], catalog: dict[str, Any], config: dict[str, Any],
                   warnings: list[str]) -> list[dict[str, Any]]:
    """One product per 商品简称, its rows in order: own pages before shared ones, most markets first."""
    products: list[dict[str, Any]] = []
    taken: set[str] = set()
    for short, rows in sorted(_rows_by_product(models, catalog, config, warnings).items()):
        rows.sort(key=lambda row: ("shares" in row, -len(row["regions"]), row["model"]))
        primary = rows[0]
        if "shares" in primary:
            continue
        if len({(row["category"], row["series"], row["tier"]) for row in rows}) > 1:
            warnings.append(f"{short}: its models are classified differently; shown as "
                            f"{primary['category']}/{primary['series']}/{primary['tier'] or '—'}")
        if capacity_mismatch(primary["tier"], primary.get("wh")):
            warnings.append(f"{short}: 容量档 {primary['tier']} does not fit the {number(primary['wh'])} Wh "
                            f"its manual states")
        products.append({
            "key": _anchor(short, taken), "short": short, "name": primary["name"],
            "category": primary["category"], "series": primary["series"], "tier": primary["tier"],
            "wh": primary.get("wh"),
            "wh_text": f"{number(primary['wh'])} Wh" if primary.get("wh") else "",
            "regions": _order((region for row in rows for region in row["regions"]), config["region_order"]),
            "editions": list(dict.fromkeys(row["edition"] for row in rows if row["edition"])), "rows": rows,
        })
    return products


def capability_view(root: Path, config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Each model in the capability table: switches on in every region, in some (with where), and off."""
    paths = Paths(root)
    names, targets = read_targets(paths.data_dir / CAPABILITIES_CSV, paths.data_dir / LANGUAGES_CSV, paths.review_dir)
    labels = config.get("capability_labels", {})
    by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for target in targets:
        by_model[target["model"]].append(target)
    view: dict[str, dict[str, Any]] = {}
    for model, rows in by_model.items():
        regions = [row["region"] for row in rows]
        entry: dict[str, Any] = {"model": model, "all": [], "some": [], "none": []}
        for index, name in enumerate(names):
            label = labels.get(name, name)
            supported = [row["region"] for row in rows if row["caps"][index]]
            if supported and len(supported) == len(regions):
                entry["all"].append(label)
            elif supported:
                unsupported = " · ".join(region for region in regions if region not in supported)
                entry["some"].append({"name": label, "tip": f"{' · '.join(supported)} 支持；{unsupported} 不支持"})
            else:
                entry["none"].append(label)
        view[model] = entry
    return view


def _linked(item: str | dict[str, str], by_short: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    """The product a pairing item names through its ``product`` key, when that product has a published manual."""
    short = item.get("product") if isinstance(item, dict) else None
    return by_short.get(short) if short else None


def pairing_index(models: dict[str, dict[str, Any]], texts: dict[str, str], products: list[dict[str, Any]],
                  config: dict[str, Any], warnings: list[str]) -> tuple[dict[str, list[dict[str, str]]],
                                                                       dict[str, list[dict[str, str]]]]:
    """What each model's manual names, and per product key the other manuals that name it."""
    by_short = {product["short"]: product for product in products}
    owner = {row["model"]: product for product in products for row in product["rows"]}
    named: dict[str, list[dict[str, str]]] = defaultdict(list)
    named_by: dict[str, list[dict[str, str]]] = defaultdict(list)
    for entry in config.get("pairings", []):
        model = entry["model"]
        if model not in models:
            warnings.append(f"{model}: pairing listed in {CONFIG} but no published manual")
            continue
        text = texts.get(model, "").lower()
        for item in [*entry.get("parts", []), *entry.get("solar", [])]:
            label, match = _partner(item)
            if re.sub(r"（.*?）", "", match).strip().lower() not in text:
                warnings.append(f"{model}: manual no longer names {match!r}; pairing dropped")
                continue
            target, source = _linked(item, by_short), owner[model]
            named[model].append({"label": label, "key": target["key"] if target else ""})
            if target is not None and target is not source:
                named_by[target["key"]].append({"key": source["key"], "name": source["name"], "model": model,
                                                "label": label})
    return named, named_by


def _detail_rows(product: dict[str, Any], keys: list[str], config: dict[str, Any],
                 languages: dict[str, str]) -> list[dict[str, Any]]:
    rows = []
    for row in product["rows"]:
        docs = []
        for region, page in row["pages"].items():
            label = _market(region, config)["label"]
            names = "、".join(languages.get(code, code) for code in page["langs"])
            docs.append({"label": label, "doc": page["doc"], "title": f"{label}：{names}"})
        entry = {"model": row["model"], "short": row["short"], "docs": docs}
        if "shares" in row:
            labels = "、".join(_market(region, config)["label"] for region in row["regions"])
            entry["note"] = f"与 {row['shares']} 共用{labels}说明书"
        else:
            entry["figures"] = [_figure(row, key) for key in keys]
        rows.append(entry)
    return rows


def related_guides(product: dict[str, Any], guides: dict[str, dict[str, Any]], guide_models: dict[str, dict[str, Any]],
                   config: dict[str, Any], languages: dict[str, str]) -> list[dict[str, Any]]:
    """The guides whose 适用产品 lists one of the product's models (its 快速指南 first), a link per published market."""
    models = {row["model"] for row in product["rows"]}
    related = []
    for code, guide in guides.items():
        if code not in guide_models or not models & set(guide["applies_to"]):
            continue
        docs = []
        for region, page in guide_models[code]["pages"].items():
            label = _market(region, config)["label"]
            docs.append({"label": label, "doc": page["doc"],
                         "title": f"{label}：{'、'.join(languages.get(c, c) for c in page['langs'])}"})
        quick = guide["kind"] == "快速指南"
        related.append({"label": "快速指南" if quick else guide["short"], "quick": quick, "docs": docs})
    return sorted(related, key=lambda item: not item["quick"])


def product_detail(product: dict[str, Any], capabilities: dict[str, dict[str, Any]],
                   named: dict[str, list[dict[str, str]]], named_by: dict[str, list[dict[str, str]]],
                   config: dict[str, Any], languages: dict[str, str],
                   guides: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """The detail under a product's row: model rows, the first capability row, partner products and guides."""
    own = [row for row in product["rows"] if "shares" not in row]
    keys = [key for key, _ in COLUMNS if any(row.get(key) for row in own)]
    features = next((capabilities[row["model"]] for row in own if row["model"] in capabilities), None)
    items = list({item["label"]: item for row in own for item in named.get(row["model"], [])}.values())
    by = named_by.get(product["key"], [])
    return {"columns": [label for key, label in COLUMNS if key in keys],
            "rows": _detail_rows(product, keys, config, languages), "features": features,
            "pairing": {"named": items, "named_by": by} if items or by else None, "guides": guides or []}


def _series_rows(members: list[dict[str, Any]], series: list[str], columns: list[str]) -> list[dict[str, Any]]:
    """A row per 产品系列 with products, each card in its 容量档 column (the last column when it has none)."""
    rows = []
    for line in series:
        in_line = sorted((p for p in members if p["series"] == line), key=lambda p: (p["wh"] or 0, p["short"]))
        if not in_line:
            continue
        cells: list[list[dict[str, Any]]] = [[] for _ in columns]
        for product in in_line:
            cells[columns.index(product["tier"]) if product["tier"] in columns else len(columns) - 1].append(product)
        rows.append({"title": line, "products": in_line, "cells": cells})
    return rows


def category_views(products: list[dict[str, Any]], catalog: dict[str, Any], config: dict[str, Any],
                   settings: dict[str, Any]) -> list[dict[str, Any]]:
    """A tab per 产品类别: its 产品系列 rows × the 容量档 its products use (one 产品 column when none has one)."""
    styles, tiers = settings.get("catalog_categories", {}), catalog.get("capacity_tiers", [])
    order = [(item["name"], list(item["series"])) for item in catalog["categories"]] + [(OTHER, [UNSORTED])]
    views = []
    for index, (name, series) in enumerate(order, 1):
        members = [product for product in products if product["category"] == name]
        if not members:
            continue
        used = [tier for tier in tiers if any(product["tier"] == tier for product in members)]
        tiered = bool(used)
        columns = used or ["产品"]
        if tiered and not all(product["tier"] in used for product in members):
            columns.append(UNSTATED)
        style = styles.get(name) or {"id": "other" if name == OTHER else f"category-{index}", "icon": "other"}
        views.append({"id": style["id"], "title": name, "icon": style["icon"], "count": len(members),
                      "tiered": tiered, "columns": columns,
                      "rows": _series_rows(members, series, columns),
                      "markets": _order((r for p in members for r in p["regions"]), config["region_order"])})
    return views


def matrix_context(root: Path, srcdir: Path, manifest: Path, assets: Path, settings: dict[str, Any],
                   catalog: list[dict[str, Any]], product_catalog: dict[str, Any] | None) -> dict[str, Any] | None:
    """Everything the page renders, or None without a readable publish manifest or a usable 产品分类 snapshot."""
    targets, built_at = read_publications(manifest)
    if targets is None or product_catalog is None:
        return None
    config = load_config(assets, settings)
    warnings: list[str] = []
    models, texts = read_models(srcdir, targets, catalog, config, warnings)
    # A 通用指南 is no product: its pages show under the products its 适用产品 lists.
    guides = product_catalog.get("guides", {})
    guide_models = {code: models.pop(code) for code in list(models) if code in guides}
    _check_evidence(config, texts, warnings)
    products = build_products(models, product_catalog, config, warnings)
    capabilities = capability_view(root, config)
    named, named_by = pairing_index(models, texts, products, config, warnings)
    languages = settings.get("language_labels", {})
    for product in products:
        product["detail"] = product_detail(product, capabilities, named, named_by, config, languages,
                                           related_guides(product, guides, guide_models, config, languages))
    return {
        "built_on": built_at[:10], "classified_on": product_catalog["exported_at"],
        "facts": {"products": len(products), "models": sum(len(product["rows"]) for product in products)},
        "markets": config.get("markets", {}), "categories": category_views(products, product_catalog, config, settings),
        "warnings": warnings,
    }


def product_matrix_page_context(app, assets: Path, settings: dict[str, Any], catalog: list[dict[str, Any]],
                                product_catalog: dict[str, Any] | None) -> dict[str, Any] | None:
    """Context for PAGE, or None (with a warning) without a manifest or snapshot, or with drifted data."""
    from sphinx.util import logging as sphinx_logging

    logger = sphinx_logging.getLogger(__name__)
    srcdir = Path(app.srcdir)
    try:
        context = matrix_context(repo_root(), srcdir, srcdir.parent / PathSegments.PUBLISH_MANIFEST_JSON,
                                 assets, settings, catalog, product_catalog)
    except (ValueError, OSError, KeyError, TypeError, csv.Error) as exc:
        logger.warning("Product matrix page skipped: %s", exc)
        return None
    if context is None:
        # Expected before the first publish snapshot (the RTD bootstrap build); a missing 产品分类 snapshot
        # already warned when the portal read it.
        logger.info("Product matrix page skipped: no readable publish manifest or 产品分类 snapshot")
        return None
    for message in context["warnings"]:
        logger.warning("Product matrix: %s", message)
    return context


__all__ = [
    "COLUMNS", "PAGE", "ProductMatrixError", "TEMPLATE", "build_products", "capacity_mismatch", "capability_view",
    "category_views",
    "display_name", "evidence_excerpt", "load_config", "matrix_context", "number", "pairing_index", "plain_text",
    "positioning_groups", "product_detail", "product_matrix_page_context", "read_models", "read_specs", "spec_pairs",
]
