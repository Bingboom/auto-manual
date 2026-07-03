#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Three-flow dashboard: one command, two faces (Milestone H3).

Aggregates the existing run artifacts — revision ledger, TM hit-rate ledger,
pdf_annotate run ledger, TM candidate files, content-audit reports, family
configs, release manifests — into a single report with two faces:

- **ops face** (运营面, system health for the operator): reflow rate, TM hit
  rate, second-revision rate, template recurrence rate, template-sentence
  corpus coverage.
- **value face** (价值面, output proof for stakeholders): audited-PDF count,
  model/region/language coverage, findings counts, revision-reflow counts,
  TM candidate counts, and the time-saved narrative metric.

Design rules:

- *Record from zero*: a metric whose data source does not exist yet is shown
  as ``no_data`` with the reason — never fabricated, never silently dropped.
  A metric without history cannot show a trend, so the empty row itself is
  the starting point.
- *Read-only*: this module only reads artifacts other tools wrote; the only
  thing it writes is its own report under ``reports/flow_dashboard/``.
- Every ledger-backed metric also buckets by month (``YYYY-MM``) so a monthly
  trend review is possible as soon as a metric has more than one month of
  history.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.tm_hit_rate import load_ledger as load_jsonl_ledger  # noqa: E402
from tools.tm_hit_rate import summarize as summarize_tm_hit_rate  # noqa: E402
from tools.utils.path_utils import (  # noqa: E402
    PathSegments,
    flow_dashboard_reports_of,
    get_paths,
    pdf_annotate_reports_of,
    releases_of,
    revision_ledger_of,
    tm_hit_rate_of,
)

DASHBOARD_SCHEMA_VERSION = 1

OPS_FACE = "ops"
VALUE_FACE = "value"

# revision_ledger.py status vocabulary (kept in sync with that module).
_LEDGER_ACCEPTED = "accepted"
_LEDGER_PENDING = "pending"

_TM_CANDIDATES_GLOB = "tm_candidates*.jsonl"
_MISSING_TRANSLATIONS_CSV = "manual_copy_missing_translations.csv"


def _metric(
    key: str,
    face: str,
    label: str,
    *,
    value: Any = None,
    status: str = "ok",
    note: str = "",
    source: str = "",
    monthly: dict[str, Any] | None = None,
    detail: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "key": key,
        "face": face,
        "label": label,
        "status": status,
        "value": value,
        "note": note,
        "source": source,
        "monthly": monthly or {},
        "detail": detail or {},
    }


def _no_data(key: str, face: str, label: str, note: str, source: str = "") -> dict[str, Any]:
    return _metric(key, face, label, status="no_data", note=note, source=source)


def _month_of(timestamp: str | None) -> str | None:
    if not timestamp or not isinstance(timestamp, str):
        return None
    return timestamp[:7] if len(timestamp) >= 7 else None


def _monthly_counts(rows: list[dict[str, Any]], *, key: str) -> dict[str, int]:
    buckets: dict[str, int] = {}
    for row in rows:
        month = _month_of(row.get(key))
        if month:
            buckets[month] = buckets.get(month, 0) + 1
    return dict(sorted(buckets.items()))


# --- revision ledger ---------------------------------------------------------


def load_revision_ledgers(paths: list[Path]) -> tuple[list[dict[str, Any]], list[str]]:
    """Load and de-duplicate (by delta_hash) rows from one or more ledgers.

    Multiple paths exist because each checkout accumulates its own ledger;
    de-duplication keeps a delta counted once even when two ledgers saw it.
    """
    rows: list[dict[str, Any]] = []
    missing: list[str] = []
    seen: set[str] = set()
    for path in paths:
        if not path.exists():
            missing.append(str(path))
            continue
        for row in load_jsonl_ledger(path):
            key = str(row.get("delta_hash") or "") or json.dumps(row, sort_keys=True)
            if key in seen:
                continue
            seen.add(key)
            rows.append(row)
    return rows, missing


def reflow_metrics(rows: list[dict[str, Any]], missing: list[str]) -> list[dict[str, Any]]:
    """回灌率 (ops) + 回收数 (value) from the revision ledger."""
    source = "reports/revision_ledger/ledger.jsonl"
    if not rows:
        note = "还没有任何回收的评审 delta"
        if missing:
            note += f"（未找到台账: {', '.join(missing)}）"
        return [
            _no_data("reflow_rate", OPS_FACE, "回灌率", note, source),
            _no_data("reflow_count", VALUE_FACE, "回收 delta 数", note, source),
        ]
    total = len(rows)
    accepted = sum(1 for row in rows if row.get("final_status") == _LEDGER_ACCEPTED)
    pending = sum(1 for row in rows if (row.get("final_status") or _LEDGER_PENDING) == _LEDGER_PENDING)
    resolved = total - pending
    monthly = _monthly_counts(rows, key="generated_at")
    reflow_rate = round(accepted / total, 4) if total else None
    note = f"accepted {accepted} / 总 {total}（pending {pending}，已裁决 {resolved}）"
    if missing:
        note += f"；未找到台账: {', '.join(missing)}"
    return [
        _metric(
            "reflow_rate", OPS_FACE, "回灌率",
            value=reflow_rate, note=note, source=source, monthly=monthly,
            detail={"total": total, "accepted": accepted, "pending": pending},
        ),
        _metric(
            "reflow_count", VALUE_FACE, "回收 delta 数",
            value=total, note=note, source=source, monthly=monthly,
        ),
    ]


def second_revision_metric(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """二次修订率: 同一处内容在多个 run 里被反复修 → 修完没修对的比例."""
    source = "reports/revision_ledger/ledger.jsonl"
    if not rows:
        return _no_data("second_revision_rate", OPS_FACE, "二次修订率", "无回收数据", source)
    runs_by_target: dict[str, set[str]] = {}
    for row in rows:
        target = " ".join(str(row.get("machine_text") or "").split())
        if not target:
            continue
        run_id = str(row.get("run_id") or "")
        runs_by_target.setdefault(target, set()).add(run_id)
    if not runs_by_target:
        return _no_data("second_revision_rate", OPS_FACE, "二次修订率", "台账行缺 machine_text", source)
    repeated = sum(1 for runs in runs_by_target.values() if len(runs) > 1)
    total = len(runs_by_target)
    distinct_runs = len({str(row.get("run_id") or "") for row in rows})
    metric = _metric(
        "second_revision_rate", OPS_FACE, "二次修订率",
        value=round(repeated / total, 4),
        note=f"{repeated} / {total} 处内容出现在多个回写 run 中（共 {distinct_runs} 个 run）",
        source=source,
        detail={"targets": total, "repeated": repeated, "runs": distinct_runs},
    )
    if distinct_runs < 2:
        metric["note"] += "；不足 2 个 run，数字尚无判别力"
    return metric


# --- TM hit rate --------------------------------------------------------------


def tm_hit_rate_metric(ledger_path: Path) -> dict[str, Any]:
    source = "reports/tm_hit_rate/ledger.jsonl"
    if not ledger_path.exists():
        return _no_data("tm_hit_rate", OPS_FACE, "TM 命中率", "还没有预翻译 run 台账", source)
    rows = load_jsonl_ledger(ledger_path)
    summary = summarize_tm_hit_rate(rows)
    if not summary.get("units_total"):
        return _no_data("tm_hit_rate", OPS_FACE, "TM 命中率", "台账里还没有带计数器的 run", source)
    pair_bits = ", ".join(
        f"{pair} {bucket['hit_rate']:.1%}"
        for pair, bucket in summary["by_language_pair"].items()
        if bucket.get("hit_rate") is not None
    )
    return _metric(
        "tm_hit_rate", OPS_FACE, "TM 命中率",
        value=summary.get("hit_rate"),
        note=f"{summary['runs']} 个 run；分语言对: {pair_bits}",
        source=source,
        monthly=_monthly_counts(rows, key="recorded_at"),
        detail=summary,
    )


# --- template flow (awaits H1 / H2) -------------------------------------------


def template_flow_placeholders() -> list[dict[str, Any]]:
    return [
        _no_data(
            "template_recurrence_rate", OPS_FACE, "模板复发修正率",
            "等 H2 台账复发挖掘（需 2–3 轮实弹台账）", "revision_ledger template-candidates (H2)",
        ),
        _no_data(
            "template_corpus_coverage", OPS_FACE, "模板句语料覆盖率",
            "等 H1 模板句↔语料对账 lint 出基线", "template_corpus_lint (H1)",
        ),
    ]


# --- pdf annotate --------------------------------------------------------------


def audited_pdf_metric(ledger_path: Path) -> dict[str, Any]:
    source = "reports/pdf_annotate/ledger.jsonl"
    if not ledger_path.exists():
        return _no_data(
            "audited_pdf_count", VALUE_FACE, "已审计 PDF 数",
            "运行台账刚启用，从零起步；历史审计可用 pdf_annotate --backfill-summary 补账",
            source,
        )
    rows = load_jsonl_ledger(ledger_path)
    distinct_pdfs = {row.get("pdf") for row in rows if row.get("pdf")}
    findings_total = sum(int(row.get("findings") or 0) for row in rows)
    return _metric(
        "audited_pdf_count", VALUE_FACE, "已审计 PDF 数",
        value=len(distinct_pdfs),
        note=f"{len(rows)} 次审计 run，累计标注 {findings_total} 条发现",
        source=source,
        monthly=_monthly_counts(rows, key="recorded_at"),
        detail={"runs": len(rows), "findings_total": findings_total},
    )


# --- coverage from configs ------------------------------------------------------


def coverage_metric(configs_dir: Path) -> dict[str, Any]:
    """覆盖面: distinct models / regions / languages across family configs."""
    source = "configs/config.*.yaml"
    try:
        import yaml
    except ImportError:
        return _no_data("coverage", VALUE_FACE, "覆盖面（型号/区域/语言）", "PyYAML 不可用", source)
    models: set[str] = set()
    regions: set[str] = set()
    languages: set[str] = set()
    for config_path in sorted(configs_dir.glob("config.*.yaml")):
        try:
            cfg = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            continue
        build = cfg.get("build") or {}
        for lang in build.get("languages") or []:
            languages.add(str(lang))
        for target in build.get("targets") or []:
            if isinstance(target, dict):
                if target.get("model"):
                    models.add(str(target["model"]))
                if target.get("region"):
                    regions.add(str(target["region"]))
    if not models:
        return _no_data("coverage", VALUE_FACE, "覆盖面（型号/区域/语言）", "configs 下没有可解析的 targets", source)
    return _metric(
        "coverage", VALUE_FACE, "覆盖面（型号/区域/语言）",
        value=f"{len(models)} 型号 / {len(regions)} 区域 / {len(languages)} 语言",
        note=f"型号: {', '.join(sorted(models))}；区域: {', '.join(sorted(regions))}",
        source=source,
        detail={
            "models": sorted(models),
            "regions": sorted(regions),
            "languages": sorted(languages),
        },
    )


# --- findings / candidates -----------------------------------------------------


def findings_metric(base_root: Path) -> dict[str, Any]:
    """发现数: 内容审计与 QC 报告里被机器点名的问题条数."""
    sources: dict[str, int] = {}
    audit_csv = (
        base_root / PathSegments.REPORTS / "content_audit" / _MISSING_TRANSLATIONS_CSV
    )
    if audit_csv.exists():
        lines = [ln for ln in audit_csv.read_text(encoding="utf-8").splitlines() if ln.strip()]
        if len(lines) > 1:
            sources["缺翻译行"] = len(lines) - 1
    qc_dir = base_root / PathSegments.REPORTS / PathSegments.CONTENT_QC
    if qc_dir.exists():
        qc_count = 0
        for findings_file in qc_dir.rglob("*.json"):
            try:
                payload = json.loads(findings_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(payload, dict):
                payload = payload.get("findings") or []
            if isinstance(payload, list):
                qc_count += len(payload)
        if qc_count:
            sources["QC findings"] = qc_count
    if not sources:
        return _no_data(
            "findings_count", VALUE_FACE, "机器发现数（过期/重复/缺失）",
            "还没有落盘的审计/QC 报告", "reports/content_audit + reports/content_qc",
        )
    total = sum(sources.values())
    return _metric(
        "findings_count", VALUE_FACE, "机器发现数（过期/重复/缺失）",
        value=total,
        note="；".join(f"{name} {count}" for name, count in sources.items()),
        source="reports/content_audit + reports/content_qc",
        detail=sources,
    )


def tm_candidates_metric(ledger_dir: Path) -> dict[str, Any]:
    source = "reports/revision_ledger/tm_candidates*.jsonl"
    files = sorted(ledger_dir.glob(_TM_CANDIDATES_GLOB)) if ledger_dir.exists() else []
    if not files:
        return _no_data(
            "tm_candidate_count", VALUE_FACE, "TM 候选句对数",
            "还没有落盘的 tm-candidates 输出（人批过的语料收割暂未计入）", source,
        )
    total = 0
    for path in files:
        total += sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    return _metric(
        "tm_candidate_count", VALUE_FACE, "TM 候选句对数",
        value=total, note=f"{len(files)} 个候选文件", source=source,
    )


# --- time saved -----------------------------------------------------------------


def time_saved_metric(releases_dir: Path, baseline_hours: float | None) -> dict[str, Any]:
    """省时叙事: 已发布手册数 × 操作者给的\"以前手工做一本要多久\"基准."""
    source = "reports/releases + 操作者基准数"
    manuals = 0
    if releases_dir.exists():
        manuals = sum(1 for path in releases_dir.rglob("release_manifest*.json"))
        if not manuals:
            manuals = sum(1 for path in releases_dir.rglob("*.json"))
    if baseline_hours is None:
        return _metric(
            "time_saved", VALUE_FACE, "省时叙事",
            status="needs_baseline",
            value=None,
            note=f"已发布 {manuals} 份可计数产物；缺基准数（--baseline-hours-per-manual，"
            "= 以前手工做一本要多少小时）",
            source=source,
            detail={"manuals_counted": manuals},
        )
    return _metric(
        "time_saved", VALUE_FACE, "省时叙事",
        value=round(manuals * baseline_hours, 1),
        note=f"{manuals} 份 × {baseline_hours} 小时/份（操作者基准）",
        source=source,
        detail={"manuals_counted": manuals, "baseline_hours": baseline_hours},
    )


# --- report assembly -------------------------------------------------------------


def build_dashboard(
    *,
    base_root: Path,
    revision_ledgers: list[Path],
    tm_ledger: Path,
    pdf_ledger: Path,
    configs_dir: Path,
    baseline_hours: float | None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    ledger_rows, missing = load_revision_ledgers(revision_ledgers)
    metrics: list[dict[str, Any]] = []
    metrics.extend(reflow_metrics(ledger_rows, missing))
    metrics.append(tm_hit_rate_metric(tm_ledger))
    metrics.append(second_revision_metric(ledger_rows))
    metrics.extend(template_flow_placeholders())
    metrics.append(audited_pdf_metric(pdf_ledger))
    metrics.append(coverage_metric(configs_dir))
    metrics.append(findings_metric(base_root))
    metrics.append(tm_candidates_metric(revision_ledger_of(base_root)))
    metrics.append(time_saved_metric(releases_of(base_root), baseline_hours))
    return {
        "dashboard_schema_version": DASHBOARD_SCHEMA_VERSION,
        "generated_at": generated_at
        or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "faces": {
            OPS_FACE: [m for m in metrics if m["face"] == OPS_FACE],
            VALUE_FACE: [m for m in metrics if m["face"] == VALUE_FACE],
        },
    }


def _format_value(metric: dict[str, Any]) -> str:
    if metric["status"] == "no_data":
        return "暂无数据"
    if metric["status"] == "needs_baseline":
        return "待基准数"
    value = metric["value"]
    if isinstance(value, float) and 0 <= value <= 1 and metric["key"].endswith("_rate"):
        return f"{value:.1%}"
    if metric["key"] == "tm_hit_rate" and isinstance(value, float):
        return f"{value:.1%}"
    if metric["key"] == "time_saved" and value is not None:
        return f"约 {value} 小时"
    return str(value)


def render_markdown(dashboard: dict[str, Any]) -> str:
    lines = [
        "# 三流转双面仪表",
        "",
        f"生成时间: {dashboard['generated_at']}（原则: 从零起步、只读聚合、无数据不造数）",
        "",
    ]
    face_titles = {OPS_FACE: "## 运营面（系统健康）", VALUE_FACE: "## 价值面（产出证明）"}
    for face in (OPS_FACE, VALUE_FACE):
        lines.append(face_titles[face])
        lines.append("")
        lines.append("| 指标 | 数值 | 说明 | 数据源 |")
        lines.append("| --- | --- | --- | --- |")
        for metric in dashboard["faces"][face]:
            lines.append(
                f"| {metric['label']} | {_format_value(metric)} "
                f"| {metric['note'] or '—'} | {metric['source'] or '—'} |"
            )
        lines.append("")
        trend_rows = [
            metric for metric in dashboard["faces"][face]
            if len(metric.get("monthly") or {}) >= 1
        ]
        if trend_rows:
            lines.append("### 月度轨迹（条目数）")
            lines.append("")
            for metric in trend_rows:
                trail = ", ".join(f"{month}: {count}" for month, count in metric["monthly"].items())
                lines.append(f"- {metric['label']}: {trail}")
            lines.append("")
    return "\n".join(lines)


_HTML_STYLE = """
:root {
  --ground: #F7F8F6; --card: #FFFFFF; --ink: #1F2A2E; --muted: #5C6B68;
  --accent: #0F6B5C; --ok: #2E7D4F; --warn: #B7791F; --crit: #B3402A;
  --ghost: #8A9490; --line: #E2E7E4;
}
* { box-sizing: border-box; margin: 0; }
body {
  background: var(--ground); color: var(--ink);
  font-family: -apple-system, "PingFang SC", "Noto Sans SC", "Microsoft YaHei", sans-serif;
  line-height: 1.5; padding: 40px 24px 64px;
}
.wrap { max-width: 1080px; margin: 0 auto; }
header h1 { font-size: 26px; font-weight: 700; letter-spacing: 0.02em; }
header .meta { color: var(--muted); font-size: 13px; margin-top: 6px; }
section { margin-top: 36px; }
.face-title { display: flex; align-items: baseline; gap: 12px; border-bottom: 2px solid var(--ink); padding-bottom: 8px; }
.face-title h2 { font-size: 17px; font-weight: 700; }
.face-title span { color: var(--muted); font-size: 13px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 14px; margin-top: 16px; }
.card { background: var(--card); border: 1px solid var(--line); border-radius: 6px; padding: 16px 18px; display: flex; flex-direction: column; gap: 8px; }
.card.nodata { background: transparent; border: 1px dashed var(--ghost); color: var(--ghost); }
.card .label { font-size: 12px; letter-spacing: 0.08em; color: var(--muted); text-transform: uppercase; }
.card.nodata .label { color: var(--ghost); }
.card .value { font-size: 30px; font-weight: 700; font-variant-numeric: tabular-nums; font-family: "SF Mono", Menlo, Consolas, monospace; }
.card .value.small { font-size: 18px; line-height: 1.35; font-family: inherit; }
.card.nodata .value { font-size: 16px; font-weight: 600; font-family: inherit; }
.chip { display: inline-block; font-size: 11px; padding: 1px 8px; border-radius: 999px; align-self: flex-start; }
.chip.ok { background: #E4F0E8; color: var(--ok); }
.chip.warn { background: #F6ECD9; color: var(--warn); }
.chip.crit { background: #F5E2DC; color: var(--crit); }
.chip.ghost { background: #ECEFED; color: var(--ghost); }
.gauge { height: 6px; background: var(--line); border-radius: 3px; overflow: hidden; }
.gauge i { display: block; height: 100%; background: var(--accent); }
.note { font-size: 13px; color: var(--muted); }
.card.nodata .note { color: var(--ghost); }
.src { font-size: 11px; color: var(--ghost); font-family: "SF Mono", Menlo, Consolas, monospace; word-break: break-all; }
.trend { display: flex; align-items: flex-end; gap: 3px; height: 34px; margin-top: 2px; }
.trend b { display: block; width: 18px; background: var(--accent); opacity: 0.75; border-radius: 2px 2px 0 0; }
.trend-lbl { font-size: 10px; color: var(--ghost); font-family: "SF Mono", Menlo, monospace; }
"""


def _html_escape(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;").replace("<", "&lt;")
        .replace(">", "&gt;").replace('"', "&quot;")
    )


def _metric_card_html(metric: dict[str, Any]) -> str:
    status = metric["status"]
    is_rate = metric["key"].endswith("_rate") or metric["key"] == "tm_hit_rate"
    ghost = status in ("no_data", "needs_baseline")
    chip = {"no_data": ("ghost", "暂无数据"), "needs_baseline": ("warn", "待基准数")}.get(status)
    if chip is None:
        # A 0% rate over real rows is a live warning, not health.
        if is_rate and metric["value"] == 0 and metric.get("detail", {}).get("total"):
            chip = ("crit", "需要关注")
        else:
            chip = ("ok", "有数据")
    value = _format_value(metric)
    value_class = "value"
    if ghost:
        value_class = "value"
    elif not is_rate and not str(value).replace("约 ", "").replace(" 小时", "").replace(".", "").isdigit():
        value_class = "value small"
    parts = [
        '<div class="card%s">' % (" nodata" if ghost else ""),
        f'<div class="label">{_html_escape(metric["label"])}</div>',
        f'<div class="{value_class}">{_html_escape(value)}</div>',
        f'<span class="chip {chip[0]}">{chip[1]}</span>',
    ]
    if is_rate and isinstance(metric["value"], (int, float)) and not ghost:
        pct = max(0.0, min(1.0, float(metric["value"]))) * 100
        parts.append(f'<div class="gauge"><i style="width:{pct:.1f}%"></i></div>')
    monthly = metric.get("monthly") or {}
    if monthly and not ghost:
        peak = max(monthly.values()) or 1
        bars = "".join(
            f'<b style="height:{max(8, round(count / peak * 100))}%" title="{month}: {count}"></b>'
            for month, count in monthly.items()
        )
        labels = " · ".join(f"{month} {count}" for month, count in monthly.items())
        parts.append(f'<div class="trend">{bars}</div><div class="trend-lbl">{labels}</div>')
    if metric.get("note"):
        parts.append(f'<div class="note">{_html_escape(metric["note"])}</div>')
    if metric.get("source"):
        parts.append(f'<div class="src">{_html_escape(metric["source"])}</div>')
    parts.append("</div>")
    return "".join(parts)


def render_html_body(dashboard: dict[str, Any]) -> str:
    """The dashboard as a self-contained HTML fragment (style + content)."""
    faces = [
        (OPS_FACE, "运营面", "系统健康 · 给自己看"),
        (VALUE_FACE, "价值面", "产出证明 · 给别人看"),
    ]
    sections = []
    for face, title, subtitle in faces:
        cards = "".join(_metric_card_html(metric) for metric in dashboard["faces"][face])
        sections.append(
            f'<section><div class="face-title"><h2>{title}</h2>'
            f"<span>{subtitle}</span></div>"
            f'<div class="grid">{cards}</div></section>'
        )
    return (
        f"<style>{_HTML_STYLE}</style>"
        '<div class="wrap"><header><h1>三流转双面仪表</h1>'
        f'<div class="meta">生成时间 {_html_escape(dashboard["generated_at"])}'
        " · 原则：从零起步 / 只读聚合 / 无数据不造数</div></header>"
        + "".join(sections)
        + "</div>"
    )


def render_html(dashboard: dict[str, Any]) -> str:
    return (
        "<!doctype html>\n<html lang=\"zh-CN\">\n<head>\n<meta charset=\"utf-8\">\n"
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>三流转双面仪表</title>\n</head>\n<body>\n"
        + render_html_body(dashboard)
        + "\n</body>\n</html>\n"
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="flow_dashboard",
        description="Emit the two-face three-flow dashboard from existing run artifacts.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    report = sub.add_parser("report", help="Build and write the dashboard (json + markdown).")
    report.add_argument(
        "--revision-ledger",
        type=Path,
        action="append",
        default=None,
        help="Revision-ledger JSONL path; repeatable to merge ledgers from "
        "several checkouts (default: this repo's ledger).",
    )
    report.add_argument("--tm-ledger", type=Path, default=None, help="TM hit-rate ledger path.")
    report.add_argument("--pdf-ledger", type=Path, default=None, help="pdf_annotate run-ledger path.")
    report.add_argument("--configs-dir", type=Path, default=None, help="Family configs directory.")
    report.add_argument(
        "--baseline-hours-per-manual",
        type=float,
        default=None,
        help="操作者基准: 以前手工做一本手册要多少小时（省时叙事指标用）。",
    )
    report.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Output directory (default: reports/flow_dashboard/).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    paths = get_paths()
    base_root = paths.root
    revision_ledgers = args.revision_ledger or [revision_ledger_of(base_root) / "ledger.jsonl"]
    tm_ledger = args.tm_ledger or tm_hit_rate_of(base_root) / "ledger.jsonl"
    pdf_ledger = args.pdf_ledger or pdf_annotate_reports_of(base_root) / "ledger.jsonl"
    configs_dir = args.configs_dir or paths.configs_dir
    dashboard = build_dashboard(
        base_root=base_root,
        revision_ledgers=revision_ledgers,
        tm_ledger=tm_ledger,
        pdf_ledger=pdf_ledger,
        configs_dir=configs_dir,
        baseline_hours=args.baseline_hours_per_manual,
    )
    out_dir = args.out_dir or flow_dashboard_reports_of(base_root)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "dashboard.json"
    md_path = out_dir / "dashboard.md"
    json_path.write_text(
        json.dumps(dashboard, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown = render_markdown(dashboard)
    md_path.write_text(markdown + "\n", encoding="utf-8")
    html_path = out_dir / "dashboard.html"
    html_path.write_text(render_html(dashboard), encoding="utf-8")
    print(markdown)
    print(f"\nWROTE {json_path}\nWROTE {md_path}\nWROTE {html_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
