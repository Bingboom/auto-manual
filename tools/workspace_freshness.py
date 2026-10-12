"""Build-time freshness and source identity; never substitutes build time for reads."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

from tools.workspace_snapshot import NAMES, data_dir, snapshot_path


def inventory(root: Path) -> dict:
    assets = root / "tools" / "rtd_portal_assets"
    result = {}
    for kind, name in NAMES.items():
        path = snapshot_path(assets, name)
        state = data_dir(root) / (kind + "-status.json")
        result[kind] = {"snapshot_sha256": hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None,
                        "status_sha256": hashlib.sha256(state.read_bytes()).hexdigest() if state.exists() else None}
    return result


def freshness(root: Path, registry: dict, today: dt.date) -> list[dict]:
    assets = root / "tools" / "rtd_portal_assets"
    rows = []
    for kind, domain, label in (("deliverables", "deliverables_feishu", "交付快照"), ("corpus", "corpus", "语料快照")):
        row = {"kind": kind, "label": label, "state": "Unavailable", "date": "无有效数据", "hash": "", "execution": ""}
        try:
            path = snapshot_path(assets, NAMES[kind])
            payload = json.loads(path.read_text())
            if kind == "deliverables":
                from tools.rtd.deliverables import snapshot_problems
                problems = snapshot_problems(payload)
            else:
                from tools.rtd.system_workspace import CONTRACT_NAME, corpus_problems, load_contract
                contract = load_contract(assets / CONTRACT_NAME)
                problems = corpus_problems(payload, [v["code"] for v in contract["corpus"]["languages"]])
            if problems:
                raise ValueError("unavailable snapshot")
            date = dt.date.fromisoformat(payload["exported_at"])
            row.update(date=date.isoformat(), hash=hashlib.sha256(path.read_bytes()).hexdigest(),
                       state="待更新" if (today - date).days > registry[domain]["stale_after_days"] else "有效")
            status_path = data_dir(root) / (kind + "-status.json")
            if status_path.exists():
                status = json.loads(status_path.read_text())
                if status.get("status") == "failed":
                    row["state"] = "更新失败 · 沿用旧数据"
                row["execution"] = status.get("execution", "")
        except (OSError, ValueError, KeyError, TypeError):
            pass
        rows.append(row)
    return rows
