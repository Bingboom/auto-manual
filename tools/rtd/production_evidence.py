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
from tools.rtd.system_workspace import CONTRACT_NAME, load_contract, load_corpus
from tools.utils.path_utils import Paths, skeletons_of
from tools.workspace_snapshot import snapshot_path

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


def production_metrics(targets: list[dict[str, Any]] | None, snapshot: dict[str, Any] | None,
                       web_source: dict[str, str], delivery_source: dict[str, str]) -> list[dict[str, Any]]:
    web = targets or []
    documents = (snapshot or {}).get("documents", [])
    manual_keys = ("model", "region")
    variant_keys = (*manual_keys, "lang")
    web_ids = _identities(web, variant_keys)
    known_ids = web_ids | _identities(documents, variant_keys)
    complete = targets is not None and snapshot is not None
    metrics = []
    for key, label, ids, valid, sources in (
        ("manuals", "Online Manuals", _identities(web, manual_keys), targets is not None, [web_source]),
        ("variants", "Language Variants", web_ids, targets is not None, [web_source]),
        ("targets", "Production Targets", known_ids, complete, [web_source, delivery_source]),
        ("published", "Published Targets", web_ids, targets is not None, [web_source]),
    ):
        metrics.append(metric(key, label, len(ids) if valid else None, unit="目标" if key != "manuals" else "本",
                              state=UNAVAILABLE, rule=" × ".join(manual_keys if key == "manuals" else variant_keys)
                              + " 去重；忽略版本、格式、重复构建", sources=sources,
                              scope="发布目录与交付快照的已标语言目标并集" if key == "targets" else "当前发布目录",
                              limitation="不代表全部在制目标；未标语言整本另列" if key == "targets" else
                              "发布目录存量；不证明首次发布时间或本次部署成功",
                              objects=[" / ".join(row) for row in sorted(ids)] if valid else []))
    for fmt, label in (("word", "Word Deliverables"), ("print", "Print Packages")):
        ids = {(d["model"], d.get("region", ""), d.get("lang") or "整本（语言未标）")
               for d in documents if fmt in d["formats"]}
        metrics.append(metric(fmt, label, len(ids) if snapshot is not None else None, unit="目标交付链接",
                              rule="model × region × lang/整本 × format 去重；不按版本累加",
                              sources=[delivery_source], state=UNAVAILABLE,
                              limitation="链接快照；未重新验证飞书访问权限或包内文件", objects=[" / ".join(i) for i in sorted(ids)]))
    for fmt in ("IDML", "PDF"):
        metrics.append(metric(fmt.lower(), f"{fmt} Deliverables", None, unit="已验证文件",
                              rule=f"需要独立的目标 × 版本 × {fmt} 产物记录", sources=[delivery_source],
                              limitation="现有印刷包链接未提供逐文件清单，不能拆算为独立交付"))
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


def skeleton_total(root: Path) -> int | None:
    """Count declared identities only; a copied file or fallback filename is not a new asset."""
    directory = skeletons_of(root)
    if not directory.is_dir():
        return None
    try:
        identities = set()
        for path in directory.glob("*/blueprint.yaml"):
            item = load_contract(path)
            identity = item.get("skeleton_id")
            if item.get("schema_version") != "skeleton-blueprint/v1" or not isinstance(identity, str) or not identity.strip():
                return None
            identities.add(identity)
        return len(identities)
    except ValueError:
        return None


def asset_metrics(root: Path, assets: Path, registry, today: dt.date) -> tuple[list[dict[str, Any]], list, dict[str, Any], list[str]]:
    paths = Paths(root=root)
    inspected = today.isoformat() + " · 构建时读取；非资产创建时间"
    component_source = source(paths.component_registry_contract, root, date=inspected)
    instance_source = source(paths.overview_component_instances_contract, root, date=inspected)
    relationships, total = component_references(paths)
    rows = [metric("components", "Shared Components", total, unit="component ID",
                   rule="Component Registry 的唯一 component ID；登记量", sources=[component_source], state=UNAVAILABLE)]
    rows.append(metric("skeletons", "Skeletons", skeleton_total(root),
                       unit="skeleton ID", rule="按 blueprint.skeleton_id 去重；登记量", state=UNAVAILABLE,
                       sources=[source(p, root, date=inspected) for p in sorted(skeletons_of(root).glob('*/blueprint.yaml'))]))
    corpus_domain = (registry or {}).get("corpus")
    corpus = None
    corpus_source = []
    if corpus_domain:
        corpus_path = snapshot_path(assets, corpus_domain["snapshot"])
        try:
            corpus, _ = load_corpus(load_contract(assets / CONTRACT_NAME), assets, corpus_domain["snapshot"])
        except (ValueError, KeyError, TypeError):
            pass
        corpus_source = [source(corpus_path, root, date=(corpus or {}).get("exported_at", ""))]
    for key, label in (("sentence_pairs", "Translation Pairs"), ("terms", "Terms")):
        rows.append(metric(key, label, corpus[key]["total"] if corpus else None, unit="快照记录行",
                           rule="快照 total；跨语言列不重复累加", sources=corpus_source, state=UNAVAILABLE,
                           limitation="含各状态记录；不宣称按文本去重，不能证明最终采用"))
    for key, label, unit in (("specs", "Structured Specs", "结构化字段"), ("artwork", "Artwork Assets", "资产 ID")):
        rows.append(metric(key, label, None, unit=unit, rule="需先确定规范资产身份与排除范围", sources=[],
                           limitation="尚未建立完整、可去重的资产口径"))
    reference_metric = metric("component-references", "Shared Component 引用目标", len({(r['model'], r['region']) for r in relationships})
                              if relationships is not None else None, unit="型号 × 区域", state=UNAVAILABLE,
                              rule="引用目标按 model × region 去重；关系按 component ID × model × region 去重；不展开语言",
                              sources=[component_source, instance_source], scope="Overview 明确绑定实例",
                              limitation="配置引用覆盖；不证明进入生产输出，不等于跨语言复用")
    rows[0]["references"] = reference_metric
    alerts = []
    if corpus and corpus_domain and (today - dt.date.fromisoformat(corpus["exported_at"])).days > corpus_domain["stale_after_days"]:
        alerts.append("语料快照超过来源规定的新鲜度期限，需刷新后复核。")
    return rows, relationships or [], reference_metric, alerts


def activity_windows(today: dt.date) -> list[dict[str, Any]]:
    return [{"days": days, "start": (today - dt.timedelta(days=days)).isoformat(), "end": today.isoformat(),
             "metrics": list(ACTIVITIES)} for days in (7, 30)]


def production_context(*, root: Path, assets: Path, manifest: Path, snapshot, registry, today: dt.date,
                       delivery_stale: list[str]) -> dict[str, Any]:
    targets, built_at = read_publications(manifest)
    web_source = source(manifest, root, date=built_at, business=True)
    domain = (registry or {}).get("deliverables_feishu", {})
    delivery_source = source(snapshot_path(assets, domain.get("snapshot", "deliverables_snapshot.json")), root,
                             date=(snapshot or {}).get("exported_at", ""))
    overview = production_metrics(targets, snapshot, web_source, delivery_source)
    asset_rows, relationships, reference, alerts = asset_metrics(root, assets, registry, today)
    alerts += delivery_stale
    if targets is None:
        alerts.append("发布目录 Unavailable：不能确认当前网页目标规模。")
    if snapshot is None:
        alerts.append("交付快照 Unavailable：不能确认 Word / 印刷交付。")
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
