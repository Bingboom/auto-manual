"""Table rows for the matrix base from a reading of the published manuals (``reader.read_publication``).

产品 and 来源 rows come from the editions (every published model × market and every language edition); 属性 rows from
``dictionary.json``; 事实 rows from the reading's facts, one per model × market × attribute read from the primary
edition, plus one per component value (条件 ``组件:<component>``). Every fact is a 候选 with its printed text (原文),
its source key, where it was printed (来源位置) and when it was recorded. A power row that prints no watt figure keeps
its printed text as the text value; it never becomes a bare voltage range.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools.product_matrix_base.reader import source_key
from tools.product_matrix_base.reader.values import POWER_KEYS
from tools.product_matrix_base.stage import (
    BRAND, CANDIDATE, SOURCE_TYPE, UNKNOWN_DATE_BASIS, _stamp, fact_key, product_key,
)

DICTIONARY = Path(__file__).with_name("dictionary.json")
COMPONENT = "组件:"
_NUMBER = re.compile(r"-?\d+(\.\d+)?")
_ABOUT = re.compile(r"約|约|about|approx|environ|aprox|ca\.|circa|około|ongeveer|etwa|cerca|приблизно|близько|약", re.I)
_PRINTED_IN = re.compile(r"printed in (\w+)")


def load_dictionary(path: Path = DICTIONARY) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))["attributes"]


def _name(name: str, model: str) -> str:
    from tools.rtd.product_matrix import display_name

    return display_name(name, model) if name else ""


def _name_field(name: str) -> str:
    """Which 名称 column a catalog name belongs in, by its script: kana is Japanese, other CJK Chinese."""
    if re.search(r"[぀-ヿ]", name):
        return "名称_ja"
    if re.search(r"[一-鿿]", name):
        return "名称_zh"
    return "名称_en"


def _product_row(edition: dict[str, Any], entry: dict[str, Any], recorded: str) -> dict[str, Any]:
    return {"产品键": product_key(edition["model"], edition["market"]), "型号": edition["model"],
            "市场": edition["market"], "品牌": BRAND, "商品简称": entry.get("short"), "产品类别": entry.get("category"),
            "产品系列": entry.get("series"), "容量档": entry.get("capacity"), "共用说明书于": entry.get("pages_of"),
            "最后更新": recorded}


def _source_row(edition: dict[str, Any], recorded: str, batch: str) -> dict[str, Any]:
    built = str(edition.get("built_at") or "")[:10]
    return {"来源键": edition["source_key"], "来源类型": SOURCE_TYPE, "型号": edition["model"],
            "市场": edition["market"], "语言": edition["language"], "版本": edition.get("version"),
            "版本日期依据": UNKNOWN_DATE_BASIS, "页面或文件": edition["page"], "文件哈希": edition.get("sha256"),
            "读取时间": recorded, "备注": f"网页构建时间 {built}" if built else None, "写入批次": batch}


def quote(fact: dict[str, Any]) -> str:
    """The printed text: `label: value` for one row; several rows already carry their labels.

    A value that already begins with a label-like segment as long as the label is not prefixed again.
    """
    rows = fact.get("rows") or []
    text = fact["value_text"]
    if not rows or len(rows) > 1 or ": " in text[: len(rows[0]["row_label_clean"]) + 2]:
        return text
    row = rows[0]
    column = f" [{row['col_header']}]" if row["col_header"] else ""
    return f"{row['row_label_clean']}{column}: {text}"


def _location(fact: dict[str, Any]) -> str:
    if not fact.get("source_section"):
        return "派生：同一说明书的多行" if fact.get("derived_from") else ""
    anchor = fact.get("source_anchor") or ""
    return f"{fact['source_section']}{' · #' + anchor if anchor else ''}"


def _value(fact: dict[str, Any], key: str) -> tuple[Any, str, str]:
    """Number, text value and printed unit of a fact."""
    metric = str(fact.get("value_metric") or "")
    number = (float(metric) if "." in metric else int(metric)) if _NUMBER.fullmatch(metric) else None
    printed = _PRINTED_IN.search(fact.get("numeric_detail") or "")
    if number is not None:
        return number, "", printed.group(1) if printed else (fact.get("unit_metric") or "")
    if key in POWER_KEYS and fact.get("range_min") and fact.get("range_unit") == "V":
        return None, fact["value_text"], ""  # no watt figure printed: keep the printed text, not a voltage range
    unit = printed.group(1) if printed else (fact.get("range_unit") or fact.get("unit_metric") or "")
    if fact.get("range_min"):
        return None, f"{fact['range_min']}~{fact['range_max']}", unit
    text = metric or fact["value_text"]
    return None, "是" if key == "expansion_port" and text == "yes" else text, unit


def _qualifier(fact: dict[str, Any], key: str) -> str:
    if key == "ac_surge_w":
        return "峰值"
    if key == "ac_rated_w":
        return "额定"
    return "约" if _ABOUT.search(fact.get("qualifier") or "") else "无"


def _remark(fact: dict[str, Any]) -> str:
    parts = (f"派生自 {fact['derived_from']}" if fact.get("derived_from") else "",
             f"语言版本核对: {fact['language_check']}" if fact.get("language_check") else "",
             f"解析细节: {fact['numeric_detail']}" if fact.get("numeric_detail") else "")
    return "; ".join(p for p in parts if p)


def _fact_row(fact: dict[str, Any], source: str, recorded: str, batch: str) -> dict[str, Any]:
    key = fact["attribute_key"]
    product = product_key(fact["model"], fact["region"])
    number, text, unit = _value(fact, key)
    return {"事实键": fact_key(product, key, "", source), "产品键": product, "属性键": key, "来源键": source,
            "原文": f"派生: {fact['value_text']}" if fact.get("derived_from") else quote(fact), "数值": number,
            "文本值": text, "原单位": unit, "限定": _qualifier(fact, key), "条件": fact.get("condition"),
            "来源位置": _location(fact), "记录时间": recorded, "核实状态": CANDIDATE, "写入批次": batch,
            "备注": _remark(fact)}


def _component_rows(components: list[dict[str, Any]], sources: dict[tuple[str, str, str], str], recorded: str,
                    batch: str) -> list[dict[str, Any]]:
    seen: Counter[tuple[str, str, str]] = Counter()
    rows = []
    for fact in components:
        product = product_key(fact["model"], fact["region"])
        condition = f"{COMPONENT}{fact['component_product']}"
        seen[(product, fact["attribute_key"], condition)] += 1
        count = seen[(product, fact["attribute_key"], condition)]
        condition_key = condition if count == 1 else f"{condition}#{count}"
        source = sources[(fact["model"], fact["region"], fact["source_language"])]
        rows.append({"事实键": fact_key(product, fact["attribute_key"], condition_key, source), "产品键": product,
                     "属性键": fact["attribute_key"], "来源键": source, "原文": quote(fact),
                     "文本值": fact["value_text"], "限定": "无", "条件": condition_key,
                     "来源位置": fact["source_section"], "记录时间": recorded, "核实状态": CANDIDATE,
                     "写入批次": batch, "备注": "随附或另售组件的数值，不并入主产品"})
    return rows


def _filled(row: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in row.items() if v not in ("", None, [])}


def stage_rows(reading: dict[str, Any], catalog_models: dict[str, Any], *, batch: str,
               names: dict[tuple[str, str], str] | None = None, models: Iterable[str] | None = None,
               markets: Iterable[str] | None = None, dictionary: list[dict[str, Any]] | None = None,
               now: datetime | None = None) -> dict[str, list[dict[str, Any]]]:
    """The rows each table would hold for the selected products, keyed by their primary field."""
    recorded = _stamp(now or datetime.now(timezone.utc))
    keep = lambda model, market: (not models or model in models) and (not markets or market in markets)  # noqa: E731
    editions = [e for e in reading["editions"] if keep(e["model"], e["market"])]
    products: dict[str, dict[str, Any]] = {}
    for edition in editions:
        row = products.setdefault(product_key(edition["model"], edition["market"]),
                                  _product_row(edition, catalog_models.get(edition["model"]) or {}, recorded))
        name = _name((names or {}).get((edition["model"], edition["market"]), ""), edition["model"])
        if name and not row.get(_name_field(name)):
            row[_name_field(name)] = name
    sources = {(e["model"], e["market"], e["language"]): source_key({
        "model": e["model"], "region": e["market"], "lang": e["language"], "version": e.get("version")})
        for e in reading["editions"]}
    facts = [_fact_row(f, sources[(f["model"], f["region"], f["source_language"])], recorded, batch)
             for f in reading["facts"] if keep(f["model"], f["region"])]
    facts += _component_rows([c for c in reading["components"] if keep(c["model"], c["region"])], sources, recorded,
                             batch)
    staged = {"产品": list(products.values()), "属性": dictionary if dictionary is not None else load_dictionary(),
              "来源": [_source_row(e, recorded, batch) for e in editions], "事实": facts}
    return {table: [_filled(row) for row in rows] for table, rows in staged.items()}


__all__ = ["COMPONENT", "DICTIONARY", "load_dictionary", "quote", "stage_rows"]
