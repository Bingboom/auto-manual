"""Read-only production metrics. Snapshots never stand in for event history."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.parse import quote

from tools.component_specs.overview_instance import load_overview_instance_registry, resolve_overview_instance
from tools.component_specs.registry import load_component_registry
from tools.utils.path_utils import Paths

NOT_TRACKED = "Not tracked yet"
UNAVAILABLE = "Unavailable"
NOT_APPLICABLE = "Not applicable"
GUIDE = "https://github.com/Bingboom/auto-manual/blob/main/code-as-doc/dev/workspace_production_evidence.md"
ACTIVITIES = (
    "New Manuals", "New Language Variants", "Build Attempts", "Build Retries",
    "Successful Builds", "First Published Variants", "Repeat Publications",
    "Review Corrections", "Backports", "TM Additions", "Shared Component Additions",
    "Agent Executions",
)


def source(path: Path, root: Path, *, date: str, business: bool = False) -> dict[str, str]:
    """Content hash identifies the exact inspected file even if its branch link moves."""
    try:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        digest = "Unavailable"
    try:
        relative = path.relative_to(root).as_posix()
    except ValueError:
        relative = path.name
    if business:
        relative = "docs/publish/publish_manifest.json"
    repo = "Hello-Docs" if business or relative.startswith("docs/knowledge/") else "auto-manual"
    return {"label": relative, "href": f"https://github.com/Bingboom/{repo}/blob/main/{quote(relative)}",
            "date": date or "Not tracked yet", "sha256": digest}


def metric(key: str, label: str, value: int | None, *, unit: str, rule: str,
           sources: list[dict[str, str]], state: str = NOT_TRACKED,
           scope: str = "当前冻结输入", limitation: str = "", objects: list[str] | None = None) -> dict[str, Any]:
    return {"id": key, "label": label, "value": value, "display": str(value) if value is not None else state,
            "state": "available" if value is not None else state, "unit": unit, "rule": rule,
            "scope": scope, "limitation": limitation, "sources": sources, "objects": objects or [],
            "denominator": NOT_APPLICABLE, "guide": GUIDE}


def read_publications(path: Path) -> tuple[list[dict[str, Any]] | None, str]:
    """A valid empty catalog is zero; unreadable/malformed data is unavailable."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        targets = data["targets"]
        if not isinstance(targets, list):
            raise ValueError("targets must be a list")
        for target in targets:
            if not isinstance(target, dict) or not all(
                isinstance(target.get(k), str) and target[k].strip()
                for k in ("model", "region", "lang", "route", "manual")
            ):
                raise ValueError("incomplete target identity")
        return targets, str(data.get("built_at") or "")
    except (OSError, ValueError, TypeError, KeyError):
        return None, ""


def _identities(rows: list[dict[str, Any]], keys: tuple[str, ...]) -> set[tuple[str, ...]]:
    return {tuple(row[k] for k in keys) for row in rows if all(row.get(k) for k in keys)}


def publication_facts(targets: list[dict[str, Any]]) -> dict[str, Any]:
    """The one count of the Web catalog that every RTD page shows.

    说明书 (unit 本) is one model × region; 语言版本 (unit 个) is one model ×
    region × language. Repeated routes, versions and rebuilds of one identity
    count once; a row without a model or region is no publication, one without
    a language no language version. An empty catalog is all zeros.
    """
    books = _identities(targets, ("model", "region"))
    variants = _identities(targets, ("model", "region", "lang"))
    by_region: dict[str, int] = {}
    for region in sorted(region for _model, region in books):
        by_region[region] = by_region.get(region, 0) + 1
    built = [str(t["built_at"])[:10] for t in targets if t.get("model") and t.get("region") and t.get("built_at")]
    return {"books": len(books), "variants": len(variants), "models": len({model for model, _ in books}),
            "books_by_region": by_region, "last_published": max(built, default=""),
            "book_ids": sorted(books), "variant_ids": sorted(variants)}


def production_metrics(targets: list[dict[str, Any]] | None, web_source: dict[str, str]) -> list[dict[str, Any]]:
    """The Web catalog's counts; the workbench counts Web manuals only (2026-11-09), not Feishu cloud documents."""
    web = publication_facts(targets or [])
    manual_keys = ("model", "region")
    variant_keys = (*manual_keys, "lang")
    web_ids = set(web["variant_ids"])
    metrics = []
    for key, label, ids in (
        ("manuals", "Online Manuals", set(web["book_ids"])),
        ("variants", "Language Variants", web_ids),
        ("published", "Published Targets", web_ids),
    ):
        metrics.append(metric(key, label, len(ids) if targets is not None else None, unit="目标" if key != "manuals" else "本",
                              state=UNAVAILABLE, rule=" × ".join(manual_keys if key == "manuals" else variant_keys)
                              + " 去重；忽略版本、格式、重复构建", sources=[web_source], scope="当前发布目录",
                              limitation="发布目录存量；不证明首次发布时间或本次部署成功",
                              objects=[" / ".join(row) for row in sorted(ids)] if targets is not None else []))
    return metrics


def component_references(paths: Paths) -> tuple[list[dict[str, str]] | None, int | None]:
    """Use the production resolver for inheritance, never its implicit default target."""
    try:
        registry = load_component_registry(paths.component_registry_contract)
    except (OSError, ValueError, KeyError, TypeError):
        return None, None
    total = len(registry["components"])
    try:
        instances = load_overview_instance_registry(paths.overview_component_instances_contract)
        relationships: dict[tuple[str, str, str], dict[str, str]] = {}
        for instance_id in instances["instances"]:
            item = resolve_overview_instance(model=None, region=None, instance_id=instance_id, registry=instances)
            component = item["component_id"]
            if component not in registry["components"]:
                raise ValueError("unregistered component")
            target = item["target"]
            key = (component, target["model"], target["region"])
            relationship = relationships.setdefault(key, {"component": component, "model": key[1],
                                                         "region": key[2], "instances": ""})
            relationship["instances"] += (", " if relationship["instances"] else "") + instance_id
        return sorted(relationships.values(), key=lambda r: (r["component"], r["model"], r["region"])), total
    except (OSError, ValueError, KeyError, TypeError):
        return None, total


def asset_metrics(root: Path, today: dt.date) -> tuple[list[dict[str, Any]], list, dict[str, Any]]:
    """The asset ledger this page keeps; corpus and skeleton totals belong to 系统建设, which the page links."""
    paths = Paths(root=root)
    inspected = today.isoformat() + " · 构建时读取；非资产创建时间"
    component_source = source(paths.component_registry_contract, root, date=inspected)
    instance_source = source(paths.overview_component_instances_contract, root, date=inspected)
    relationships, total = component_references(paths)
    rows = [metric("components", "Shared Components", total, unit="component ID",
                   rule="Component Registry 的唯一 component ID；登记量", sources=[component_source], state=UNAVAILABLE)]
    for key, label, unit in (("specs", "Structured Specs", "结构化字段"), ("artwork", "Artwork Assets", "资产 ID")):
        rows.append(metric(key, label, None, unit=unit, rule="需先确定规范资产身份与排除范围", sources=[],
                           limitation="尚未建立完整、可去重的资产口径"))
    reference_metric = metric("component-references", "Shared Component 引用目标", len({(r['model'], r['region']) for r in relationships})
                              if relationships is not None else None, unit="型号 × 区域", state=UNAVAILABLE,
                              rule="引用目标按 model × region 去重；关系按 component ID × model × region 去重；不展开语言",
                              sources=[component_source, instance_source], scope="Overview 明确绑定实例",
                              limitation="配置引用覆盖；不证明进入生产输出，不等于跨语言复用")
    rows[0]["references"] = reference_metric
    return rows, relationships or [], reference_metric


def activity_windows(today: dt.date) -> list[dict[str, Any]]:
    return [{"days": days, "start": (today - dt.timedelta(days=days)).isoformat(), "end": today.isoformat(),
             "metrics": list(ACTIVITIES)} for days in (7, 30)]


def production_context(*, root: Path, manifest: Path, today: dt.date) -> dict[str, Any]:
    targets, built_at = read_publications(manifest)
    web_source = source(manifest, root, date=built_at, business=True)
    overview = production_metrics(targets, web_source)
    asset_rows, relationships, reference = asset_metrics(root, today)
    alerts = []
    if targets is None:
        alerts.append("发布目录 Unavailable：不能确认当前网页目标规模。")
    for item in asset_rows:
        if item["state"] == UNAVAILABLE:
            alerts.append(f"{item['label']} 来源 Unavailable，当前值未知。")
    if reference["state"] == UNAVAILABLE:
        alerts.append("组件引用关系 Unavailable：本次无法计算引用目标。")
    return {"overview": overview, "assets": asset_rows, "references": relationships, "reference_metric": reference,
            "windows": activity_windows(today), "alerts": alerts, "as_of": today.isoformat(), "guide": GUIDE,
            "backflow": ["已记录 Review / Correction", "已关联资产更新的修订", "原目标后续版本再次采用", "其他 Manual / Variant 再次采用"],
            "agents": ["Product Information Queries", "Build Executions", "Translation Preprocessing",
                       "Review / Impact Analysis", "Successfully Automated Tasks", "Tasks Requiring Human Intervention"],
            "history_reason": "现有输入没有覆盖该窗口的完整事件身份、时间和结束状态；不能用快照、Git 次数或文件修改时间代替。"}
