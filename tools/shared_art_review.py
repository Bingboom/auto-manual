"""Read-only, byte-deduplicated review of existing artwork and live snapshots.

This is a review derivative, never another registry or an approval authority.
"""
from __future__ import annotations

from collections import defaultdict
import csv
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import re
import shutil
import subprocess

from tools.asset_registry import REGISTRY_RELATIVE_PATH

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".svg", ".webp"}


def category(names: str) -> str:
    """Conservative navigation hints only; never infer approved applicability."""
    value = names.lower()
    if re.search(r"lcd[._/-]icon|lcd_icons|wifi|bluetooth|charging_indicator", value):
        return "LCD icons 专表"
    if re.search(r"symbols?[/_.-]|weee|recycle|warning_triangle", value):
        return "Symbols 专表"
    if re.search(r"solar|solarsaga|太阳能", value):
        return "太阳能板与连接图"
    if re.search(r"car[_-]?(charg|cable)|charging[_-]car|车充", value):
        return "车充与车充线"
    if re.search(r"cable|adapter|connector|inbox|in.the.box|manual_icon", value):
        return "线材、配件与装箱图"
    if re.search(r"operation|energy|ups|frequency|clock|lcd_mode|button", value):
        return "操作与按键图"
    if re.search(r"app|qrcode|qr_code", value):
        return "App 与二维码（核对文字及链接）"
    if re.search(r"overview|product|main_unit|lcd|screen|hero", value):
        return "主机与屏幕（型号限定）"
    return "其他图（人工筛选）"


def tracked_art(repo: Path) -> list[Path]:
    raw = subprocess.check_output(["git", "ls-files", "-z", "--", "docs", "manual_sources"], cwd=repo)
    return [repo / name.decode() for name in raw.split(b"\0") if name
            and Path(name.decode()).suffix.lower() in IMAGE_SUFFIXES]


def _group_bytes(repo: Path, files: list[Path]) -> tuple[dict, list]:
    groups: dict[str, dict] = {}
    missing = []
    for path in sorted(files):
        if not path.is_file():
            missing.append(str(path))
            continue
        digest = sha256(path.read_bytes()).hexdigest()
        item = groups.setdefault(digest, {"sha256": digest, "paths": [], "registry": [], "live": []})
        item["paths"].append(str(path.relative_to(repo)) if path.is_relative_to(repo) else str(path))
    return groups, missing


def _bind_registry(repo: Path, groups: dict) -> list:
    with (repo / REGISTRY_RELATIVE_PATH).open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    unmatched_registry = []
    for row in rows:
        hashes = [v.rsplit(":", 1)[-1].strip().lower() for v in row.get("内容哈希", "").split(",")]
        matches = [g for h, g in groups.items() if any(len(v) >= 8 and h.startswith(v) for v in hashes)]
        for item in matches:
            item["registry"].append(row)
        if not matches:
            unmatched_registry.append(row["asset_key"])
    return unmatched_registry


def _bind_live(snapshots: Path, groups: dict) -> tuple[dict, dict, list]:
    counts = {}
    live_by_key = defaultdict(list)
    missing_attachments = []
    for name in ("definitions", "exports", "lcd", "symbols"):
        path = snapshots / f"live-{name}.json"
        if not path.is_file():
            raise ValueError(f"missing live snapshot: {path}")
        records = json.loads(path.read_text(encoding="utf-8"))
        counts[name] = len(records)
        for row in records:
            fields = row["fields"]
            ref = {"table": name, "record_id": row["record_id"], "fields": fields}
            if name in {"lcd", "symbols"} and not fields.get("figure" if name == "lcd" else "Figure") and not row.get("download_sha256"):
                missing_attachments.append(ref)
            if fields.get("asset_key"):
                live_by_key[fields["asset_key"]].append(ref)
            digest = fields.get("content_sha256") or row.get("download_sha256")
            if digest in groups:
                groups[digest]["live"].append(ref)
    return counts, live_by_key, missing_attachments


def _archive_evidence(exact_tables: set[str]) -> str:
    if exact_tables & {"lcd", "symbols"}:
        return "专表原附件已下载并按字节匹配"
    if "exports" in exact_tables:
        return "导出表声明相同哈希（未下载复核）"
    if "definitions" in exact_tables:
        return "只有定义记录；未匹配导出字节"
    return "未匹配本轮飞书快照"


def inventory(repo: Path, files: list[Path], snapshots: Path) -> dict:
    groups, missing = _group_bytes(repo, files)
    unmatched_registry = _bind_registry(repo, groups)
    counts, live_by_key, missing_attachments = _bind_live(snapshots, groups)
    items = []
    for digest, item in sorted(groups.items()):
        keys = [r["asset_key"] for r in item["registry"]]
        for key in keys:
            # Definition presence is not proof of matching export bytes.
            item["live"].extend(r for r in live_by_key[key] if r["table"] == "definitions")
        item["live"] = list({(r["table"], r["record_id"]): r for r in item["live"]}.values())
        exact_tables = {r["table"] for r in item["live"]}
        item["category"] = ("LCD icons 专表" if "lcd" in exact_tables else
                            "Symbols 专表" if "symbols" in exact_tables else
                            category(" ".join(keys + [Path(p).name for p in item["paths"]])))
        item["id"] = "ART-" + digest[:12]
        item["status"] = "待操作者选定；不可由重复次数推断跨型号适用"
        item["shared_eligible"] = item["category"] != "操作与按键图"
        targets = {p.split('/')[1] for p in item['paths'] if p.startswith('manual_sources/')}
        item["priority"] = bool(exact_tables & {"lcd", "symbols"} or len(targets) > 1
                                or any(r.get("适用机型") == "ALL" for r in item["registry"])
                                or item["category"] in {"太阳能板与连接图", "车充与车充线"})
        item["priority"] = item["priority"] and item["shared_eligible"]
        item["archive_evidence"] = _archive_evidence(exact_tables)
        items.append(item)
    return {"schema_version": "shared-art-review/v1", "publication_eligible": False,
            "scan_files": len(files), "missing_files": missing, "unique_bytes": len(items),
            "live_counts": counts, "dedicated_missing_attachments": missing_attachments,
            "unmatched_registry": unmatched_registry, "items": items}


def apply_review_annotations(report: dict, selections: dict | None = None,
                             identities: dict | None = None) -> None:
    """Apply explicit review input; never turn it into registry or release approval."""
    by_id = {item["id"]: item for item in report["items"]}
    pending = []
    for kind, document in (("selection", selections), ("identity", identities)):
        seen = set()
        for row in (document or {}).get("items", []):
            key = row.get("id")
            if key not in by_id or key in seen:
                raise ValueError(f"unknown or duplicate {kind} id: {key}")
            seen.add(key)
            item = by_id[key]
            if kind == "selection":
                if row.get("decision") not in {"reuse", "limited", "exclude"}:
                    raise ValueError(f"invalid selection: {key}")
                if not item["shared_eligible"] and row["decision"] != "exclude":
                    raise ValueError(f"operation/button artwork is not shared: {key}")
                values = {"operator_selection": dict(row)}
            else:
                if row.get("sha256") != item["sha256"] or not row.get("label", "").strip():
                    raise ValueError(f"identity requires exact hash and label: {key}")
                canonical = by_id.get(row.get("canonical_id"))
                if canonical is None or canonical["category"] != item["category"]:
                    raise ValueError(f"invalid identity canonical: {key}")
                if not row.get("evidence", "").strip():
                    raise ValueError(f"identity requires evidence: {key}")
                values = {"identity_review": dict(row)}
            pending.append((item, values))
    for item, values in pending:
        item.update(values)
    for item in report["items"]:
        if not item["shared_eligible"] or item.get("operator_selection", {}).get("decision") == "exclude":
            item["priority"] = False
    report["publication_eligible"] = False


def _display_identity(item: dict) -> tuple[str, str]:
    keys = ", ".join(r["asset_key"] for r in item["registry"])
    scopes = "; ".join(f"{r['适用机型']} / {r['适用区域']} / {r['语言维度']}" for r in item["registry"])
    dedicated = [r["fields"] for r in item["live"] if r["table"] in {"lcd", "symbols"}]
    if dedicated:
        keys = ", ".join(str(r.get("icon_zh") or r.get("label_zh") or r.get("symbol_key") or r.get("icon_en") or "共用图标") for r in dedicated)
        scopes = "专表适用型号：" + "; ".join(", ".join(r.get("Model") or []) or "需核对" for r in dedicated)
    keys = item.get("identity_review", {}).get("label") or keys
    return keys or Path(item["paths"][0]).name, scopes or "尚未登记适用范围（来源详见下方）"


def write_review(report: dict, output: Path, repo: Path) -> None:
    """Write a new portable gallery; source artwork is copied without changes."""
    output.mkdir(parents=True, exist_ok=False)
    (output / "assets").mkdir()
    for item in report["items"]:
        path = Path(item["paths"][0])
        source = path if path.is_absolute() else repo / path
        name = item["sha256"] + source.suffix.lower()
        shutil.copyfile(source, output / "assets" / name)
        item["preview"] = "assets/" + name
    (output / "inventory.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    cards = []
    for item in sorted(report["items"], key=lambda r: (r["category"], r["id"])):
        keys, scopes = _display_identity(item)
        refs = ", ".join(f"{r['table']}: {r['record_id']}" for r in item["live"])
        search = " ".join([item["id"], keys, scopes, item["category"], *item["paths"]])
        details = escape(json.dumps({k: item[k] for k in ("paths", "registry", "live")}, ensure_ascii=False, indent=2))
        decision = item.get("operator_selection", {}).get("decision", "pending")
        note = item.get("operator_selection", {}).get("note", "")
        if not item.get("shared_eligible", True):
            decision, note = "exclude", "操作与按键图不纳入共用库；共享组件继续复用"
        options_html = "".join(f'<option value="{value}"{chr(32) + "selected" if decision == value else ""}>{label}</option>' for value, label in (("pending", "待确认"), ("reuse", "按现有适用范围复用"), ("limited", "按确认条件复用"), ("exclude", "不作为共用图")))
        cards.append(f'<article data-priority="{str(item["priority"]).lower()}" data-category="{escape(item["category"], quote=True)}" data-search="{escape(search.lower(), quote=True)}">'
                     f'<h2 data-id="{item["id"]}">{escape(keys)}</h2><a href="{item["preview"]}" target="_blank"><img loading="lazy" src="{item["preview"]}" alt="{escape(keys, quote=True)}"></a>'
                     f'<p><b>{escape(keys)}</b></p><p>{escape(scopes)}</p><p>{escape(item["archive_evidence"])}</p>'
                     f'<p>{len(item["paths"])} 个原字节相同的文件 · {escape(refs)}</p>'
                     f'<label>确认选择 <select class="choice">{options_html}</select></label>'
                     f'<input class="note" value="{escape(note, quote=True)}" placeholder="限定范围或意见">'
                     f'<details><summary>来源与原有登记</summary><pre>{details}</pre></details></article>')
    categories = sorted({r["category"] for r in report["items"]})
    options = ''.join(f'<option>{escape(c)}</option>' for c in categories)
    page = '''<!doctype html><html lang="zh"><meta charset="utf-8"><title>共用图候选确认</title>
<style>body{font:15px system-ui;margin:24px;background:#f4f6f8;color:#18212b}header{position:sticky;top:0;background:#f4f6f8;padding:12px;z-index:2}main{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:16px}article{background:white;padding:16px;border:1px solid #cdd5dd;border-radius:8px;overflow:hidden}article[hidden]{display:none}h2{font-size:16px}img{width:100%;height:190px;object-fit:contain;background:repeating-conic-gradient(#eee 0% 25%,#fff 0% 50%) 0/16px 16px}input,select,button{font:inherit;padding:8px;margin:4px 0;max-width:100%;box-sizing:border-box}.note{width:100%}p,pre{overflow-wrap:anywhere}pre{white-space:pre-wrap;font-size:12px}small{display:block}</style>
<header><h1>共用图候选确认</h1><p>原图未改动；只合并字节完全相同的文件。相似图、不同接口、屏幕和语言仍分别保留。选择可导出；刷新前请导出保存。</p>
<select id="scope"><option value="priority">优先候选：既有共用、跨型号原字节相同、太阳能及车充</option><option value="all">全量图片（含型号专用及历史版本）</option></select>
<select id="category"><option value="">全部分类</option>''' + options + '''</select> <input id="search" placeholder="搜索：solar / car / 型号 / asset_key"> <button id="export">导出确认清单</button><small id="count"></small></header><main>''' + ''.join(cards) + '''</main>
<script>const cards=[...document.querySelectorAll('article')];const category=document.querySelector('#category'),search=document.querySelector('#search'),scope=document.querySelector('#scope');function filter(){let n=0;for(const c of cards){c.hidden=!!((scope.value==='priority'&&c.dataset.priority!=='true')||(category.value&&c.dataset.category!==category.value)||!c.dataset.search.includes(search.value.toLowerCase()));if(!c.hidden)n++}document.querySelector('#count').textContent=`显示 ${n} / ${cards.length} 个不同字节版本`;}category.onchange=filter;scope.onchange=filter;search.oninput=filter;filter();document.querySelector('#export').onclick=()=>{const rows=cards.filter(c=>c.querySelector('.choice').value!=='pending').map(c=>({id:c.querySelector('h2').dataset.id,decision:c.querySelector('.choice').value,note:c.querySelector('.note').value}));const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify({status:'operator-selection-for-review',items:rows},null,2)],{type:'application/json'}));a.download='shared-art-selections.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);};</script></html>'''
    (output / "index.html").write_text(page, encoding="utf-8")
