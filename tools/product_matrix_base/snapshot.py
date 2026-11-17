"""A read-only snapshot of the product matrix base for the private site's product pages.

``build_snapshot(run)`` reads the 产品, 属性, 来源 and 事实 tables and returns one deterministic document: products,
parameters, sources, main-product values and component values, each sorted by its key, plus a header (when the base
was read, row counts, the snapshot schema). It carries no Feishu record ids, table ids, tokens or URLs, and no raw
edition labels (they hold pipeline build codes): a source is identified by an opaque id and linked by its page path.

The snapshot holds project numbers, which may go to the private Hello-Docs mirror and the private site but never to
the public auto-manual repository or the public site (operator, 2026-11-17). ``safe_destination`` enforces where it
may be written: only under ``docs/knowledge/`` of a checkout that is the Hello-Docs mirror.
"""
from __future__ import annotations

import hashlib
import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools.product_matrix_base.stage import CST, LoadError, Runner, _instant, _text, read_rows, table_ids

SCHEMA = "hello-docs-product-matrix-snapshot/v1"
FILE_NAME = "snapshot.json"
PRIVATE_MIRROR = "Hello-Docs"
KNOWLEDGE = Path("docs") / "knowledge"
PROJECT_SOURCE = "项目号（仅飞书）"
COMPONENT = "组件:"
EXCLUDED_STATES = {"已驳回", "已取代"}

PRODUCT_FIELDS = ("产品键", "型号", "市场", "品牌", "商品简称", "名称_en", "名称_ja", "名称_zh", "产品类别", "产品系列",
                  "容量档", "共用说明书于", PROJECT_SOURCE, "上市日期", "上市日期依据", "停售日期", "产品阶段")
NAME_FIELDS = tuple(field for field in PRODUCT_FIELDS if field.startswith("名称_"))
PARAMETER_FIELDS = ("属性键", "中文名", "英文名", "分组", "值类型", "规范单位", "定义", "适用类别", "说明书通常写", "状态",
                    "排序")
SOURCE_FIELDS = ("来源键", "来源类型", "型号", "市场", "语言", "版本日期", "版本日期依据", "页面或文件")
FACT_FIELDS = ("事实键", "产品键", "属性键", "来源键", "原文", "数值", "文本值", "原单位", "限定", "条件", "来源位置",
               "生效起", "生效止", "记录时间", "核实状态", "当前值", "冲突")


class SnapshotError(ValueError):
    """The snapshot cannot be written where it was asked to go."""


def _cell(value: Any) -> Any:
    """A read cell as plain JSON: one-item selects become their option, empty cells None."""
    if isinstance(value, list):
        items = [_text(v) for v in value if _text(v)]
        return items or None
    if isinstance(value, dict):
        return _text(value) or None
    return None if value in ("", None) else value


def _date(value: Any) -> str | None:
    """A datetime cell as its Beijing-time date."""
    seconds = _instant(value)
    return datetime.fromtimestamp(seconds, CST).strftime("%Y-%m-%d") if seconds is not None else None


def source_id(key: str) -> str:
    """An opaque, stable id for a source: the source key holds edition labels that do not leave Feishu."""
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]


def _single(value: Any) -> Any:
    value = _cell(value)
    return value[0] if isinstance(value, list) and len(value) == 1 else value


def _product(row: dict[str, Any]) -> dict[str, Any]:
    return {"key": _text(row.get("产品键")), "model": _single(row.get("型号")), "market": _single(row.get("市场")),
            "brand": _single(row.get("品牌")), "short_name": _single(row.get("商品简称")),
            "names": {field.split("_", 1)[1]: _single(row.get(field)) for field in NAME_FIELDS if _single(row.get(field))},
            "category": _single(row.get("产品类别")), "series": _single(row.get("产品系列")),
            "capacity_tier": _single(row.get("容量档")), "shares_manual_with": _single(row.get("共用说明书于")),
            "project": _single(row.get(PROJECT_SOURCE)), "launch_date": _date(row.get("上市日期")),
            "launch_date_basis": _single(row.get("上市日期依据")), "end_of_sale": _date(row.get("停售日期")),
            "stage": _single(row.get("产品阶段"))}


def _parameter(row: dict[str, Any]) -> dict[str, Any]:
    applies = _cell(row.get("适用类别"))
    return {"key": _text(row.get("属性键")), "name_zh": _single(row.get("中文名")), "name_en": _single(row.get("英文名")),
            "group": _single(row.get("分组")), "value_type": _single(row.get("值类型")),
            "unit": _single(row.get("规范单位")), "definition": _single(row.get("定义")),
            "applies_to": applies if isinstance(applies, list) else ([applies] if applies else []),
            "usually_printed": bool(row.get("说明书通常写")), "status": _single(row.get("状态")) or "启用",
            "order": _single(row.get("排序"))}


def _source(row: dict[str, Any]) -> dict[str, Any]:
    return {"id": source_id(_text(row.get("来源键"))), "kind": _single(row.get("来源类型")),
            "model": _single(row.get("型号")), "market": _single(row.get("市场")), "language": _single(row.get("语言")),
            "edition_date": _date(row.get("版本日期")), "edition_date_basis": _single(row.get("版本日期依据")),
            "page": _single(row.get("页面或文件"))}


def _value(row: dict[str, Any]) -> dict[str, Any]:
    return {"product": _text(row.get("产品键")), "parameter": _text(row.get("属性键")),
            "source": source_id(_text(row.get("来源键"))), "condition": _single(row.get("条件")),
            "printed": _single(row.get("原文")), "number": _single(row.get("数值")), "text": _single(row.get("文本值")),
            "printed_unit": _single(row.get("原单位")), "qualifier": _single(row.get("限定")),
            "position": _single(row.get("来源位置")), "state": _single(row.get("核实状态")) or "候选",
            "effective_from": _date(row.get("生效起")), "effective_to": _date(row.get("生效止")),
            "recorded": _date(row.get("记录时间")), "current": bool(row.get("当前值")), "conflict": bool(row.get("冲突"))}


def _mark_disagreement(values: list[dict[str, Any]]) -> None:
    """Flag a product's parameter whose sources print different values (beside any 冲突 a person set)."""
    seen: dict[tuple[str, str], set[str]] = defaultdict(set)
    for value in values:
        if value["state"] not in EXCLUDED_STATES:
            seen[(value["product"], value["parameter"])].add(json.dumps([value["number"], value["text"]]))
    for value in values:
        value["sources_disagree"] = len(seen[(value["product"], value["parameter"])]) > 1


def build_snapshot(run: Runner, now: datetime | None = None) -> dict[str, Any]:
    """The snapshot document, every list sorted by its key so successive snapshots diff cleanly."""
    ids = table_ids(run)
    missing = [name for name in ("产品", "属性", "来源", "事实") if name not in ids]
    if missing:
        raise LoadError(f"tables missing in the base: {missing}")
    products = [_product(r) for r in read_rows(run, ids["产品"], list(PRODUCT_FIELDS), sensitive=True)]
    parameters = [_parameter(r) for r in read_rows(run, ids["属性"], list(PARAMETER_FIELDS), sensitive=True)]
    sources = [_source(r) for r in read_rows(run, ids["来源"], list(SOURCE_FIELDS), sensitive=True)]
    facts = read_rows(run, ids["事实"], list(FACT_FIELDS), sensitive=True)
    main = [_value(r) for r in facts if not _text(r.get("条件")).startswith(COMPONENT)]
    components = [{**_value(r), "component": _text(r.get("条件"))[len(COMPONENT):].split("#")[0]}
                  for r in facts if _text(r.get("条件")).startswith(COMPONENT)]
    _mark_disagreement(main)
    order = (lambda v: (v["product"], v["parameter"], v["condition"] or "", v["source"]))
    document = {
        "schema": SCHEMA,
        "read_at": (now or datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "counts": {"products": len(products), "parameters": len(parameters), "sources": len(sources),
                   "values": len(main), "component_values": len(components),
                   "products_with_project": sum(1 for p in products if p["project"])},
        "products": sorted(products, key=lambda p: p["key"]),
        "parameters": sorted(parameters, key=lambda p: (p["order"] if isinstance(p["order"], (int, float)) else 1e9,
                                                         p["key"])),
        "sources": sorted(sources, key=lambda s: (s["model"] or "", s["market"] or "", s["language"] or "", s["id"])),
        "values": sorted(main, key=order),
        "component_values": sorted(components, key=lambda v: (*order(v), v["component"])),
    }
    return document


def encode(document: dict[str, Any]) -> bytes:
    return (json.dumps(document, ensure_ascii=False, indent=1, sort_keys=True) + "\n").encode("utf-8")


def _checkout_root(path: Path) -> Path | None:
    probe = path.resolve()
    return next((parent for parent in [probe, *probe.parents] if (parent / ".git").exists()), None)


def safe_destination(out_dir: Path) -> Path:
    """The snapshot file path, only under docs/knowledge/ of a Hello-Docs mirror checkout; else SnapshotError."""
    from tools.check_maintainability_guardrails import mirror_name, origin_repository

    root = _checkout_root(out_dir if out_dir.exists() else out_dir.parent)
    if root is None:
        raise SnapshotError(f"{out_dir} is not inside a git checkout; the snapshot goes to the Hello-Docs mirror")
    remote = origin_repository(root)
    if remote != PRIVATE_MIRROR.lower():
        raise SnapshotError(f"{out_dir} is in a checkout whose origin is {remote or 'unreadable'}; the snapshot "
                            f"holds project numbers and may only go to a checkout of the {PRIVATE_MIRROR} repository")
    mirror = mirror_name(root)
    if mirror != PRIVATE_MIRROR:
        raise SnapshotError(f"{out_dir} is in a checkout of {mirror or 'auto-manual (public)'}; the snapshot "
                            f"holds project numbers and may only go to the {PRIVATE_MIRROR} mirror")
    knowledge = (root / KNOWLEDGE).resolve()
    target = out_dir.resolve()
    if target != knowledge and knowledge not in target.parents:
        raise SnapshotError(f"{out_dir} is outside {KNOWLEDGE}/ of the {PRIVATE_MIRROR} checkout")
    if (target / FILE_NAME).is_symlink():
        raise SnapshotError(f"{FILE_NAME} under {out_dir} is a symbolic link; refusing to write through it")
    return target / FILE_NAME


def write_snapshot(target: Path, document: dict[str, Any]) -> None:
    """Write through a temporary file in the same directory and rename it over the target (never follows a link)."""
    if target.is_symlink():
        raise SnapshotError(f"{target.name} is a symbolic link; refusing to write through it")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.tmp")
    if temporary.is_symlink():
        temporary.unlink()
    temporary.write_bytes(encode(document))
    os.replace(temporary, target)


def summary(document: dict[str, Any]) -> str:
    """Counts only: never a project number, a value or a source key."""
    counts = document["counts"]
    return (f"产品 {counts['products']}（带项目号 {counts['products_with_project']}），参数 {counts['parameters']}，"
            f"来源 {counts['sources']}，主产品值 {counts['values']}，组件值 {counts['component_values']}")


__all__ = ["FILE_NAME", "SCHEMA", "SnapshotError", "build_snapshot", "encode", "safe_destination", "source_id",
           "summary", "write_snapshot"]
