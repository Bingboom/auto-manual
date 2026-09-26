"""Source registry (SSOT): where each workspace-page fact comes from, how fresh it must be, what shows without it.

``tools/rtd_portal_assets/source_registry.yaml`` holds one entry per data
domain (REV-44; design in ``code-as-doc/dev/ssot_source_registry_design.md``).
The system and deliverables pages take snapshot names, freshness limits and
fallback text from it instead of hardcoding them; the system page lists it
publicly as 数据来源; agents look up a fact's authority here.

A registry that cannot be read or breaks these rules is an authoring error:
the system page drops out with a Sphinx warning, like a broken status
contract, and the deliverables page shows its Feishu columns as unavailable.
"""
from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path
from typing import Any, Callable

import yaml

REGISTRY_NAME = "source_registry.yaml"
REGISTRY_SCHEMA = "hello-docs-source-registry/v1"
READ_LABELS = {"build": "构建时读", "snapshot": "读快照"}
# The domains the workspace pages read; each must be registered.
PAGE_DOMAINS = ("publications", "ledger", "corpus", "deliverables_feishu", "skeletons", "tooling",
                "capabilities", "focus")

_ID = re.compile(r"^[a-z][a-z0-9_]*$")
_SNAPSHOT = re.compile(r"^[A-Za-z0-9_.-]+\.json$")
_FILE_REF = re.compile(r"^file:(auto-manual|hello-docs):(\S+)$")

Registry = dict[str, dict[str, Any]]


def authorities(domain: dict[str, Any]) -> list[str]:
    value = domain.get("authority")
    return [str(item) for item in value] if isinstance(value, list) else [str(value or "")]


def file_refs(registry: Registry) -> list[tuple[str, str, str]]:
    """Every ``(domain id, repo, path)`` a domain names with a ``file:`` ref."""
    refs = []
    for domain_id, domain in registry.items():
        for ref in authorities(domain):
            match = _FILE_REF.fullmatch(ref)
            if match:
                refs.append((domain_id, match.group(1), match.group(2)))
    return refs


def registry_problems(data: object) -> list[str]:
    """Why the registry cannot be used; empty when it is sound."""
    if not isinstance(data, dict):
        return [f"{REGISTRY_NAME} is not a mapping"]
    problems: list[str] = []
    if data.get("schema") != REGISTRY_SCHEMA:
        problems.append(f"schema is {data.get('schema')!r}, expected {REGISTRY_SCHEMA!r}")
    domains = data.get("domains")
    if not isinstance(domains, list) or not domains:
        return [*problems, "domains must be a non-empty list"]
    seen: set[str] = set()
    for index, domain in enumerate(domains):
        if not isinstance(domain, dict):
            problems.append(f"domains[{index}] is not a mapping")
            continue
        domain_id = str(domain.get("id") or "")
        where = f"domain {domain_id or index}"
        if not _ID.fullmatch(domain_id):
            problems.append(f"{where}: id must be lower_snake_case")
        if domain_id in seen:
            problems.append(f"{where}: duplicate id")
        seen.add(domain_id)
        for field in ("label", "fallback", "used_by"):
            if not str(domain.get(field) or "").strip():
                problems.append(f"{where}: needs {field}")
        if not all(ref.strip() for ref in authorities(domain)):
            problems.append(f"{where}: authority must be text or a list of texts")
        read = domain.get("read")
        if read not in READ_LABELS:
            problems.append(f"{where}: read must be one of {sorted(READ_LABELS)}")
        stale = domain.get("stale_after_days")
        if stale is not None and (isinstance(stale, bool) or not isinstance(stale, int) or stale <= 0):
            problems.append(f"{where}: stale_after_days must be a positive integer")
        if read == "snapshot":
            if not _SNAPSHOT.fullmatch(str(domain.get("snapshot") or "")):
                problems.append(f"{where}: snapshot must name a .json file next to the registry")
            if not str(domain.get("refresh") or "").strip():
                problems.append(f"{where}: a snapshot needs its refresh command")
            if stale is None:
                problems.append(f"{where}: a snapshot needs stale_after_days")
        elif "snapshot" in domain or "refresh" in domain:
            problems.append(f"{where}: only snapshot domains name a snapshot or a refresh command")
    missing = [domain_id for domain_id in PAGE_DOMAINS if domain_id not in seen]
    if missing:
        problems.append(f"domains the pages read are not registered: {missing}")
    return problems


def load_registry(assets: Path) -> tuple[Registry | None, list[str]]:
    """Domains by id, or None with the reasons the registry cannot be used."""
    try:
        data = yaml.safe_load((assets / REGISTRY_NAME).read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        return None, [f"cannot read {REGISTRY_NAME}: {exc}"]
    problems = registry_problems(data)
    if problems:
        return None, problems
    return {str(domain["id"]): domain for domain in data["domains"]}, []


def snapshot_date(assets: Path, domain: dict[str, Any]) -> dt.date | None:
    """A snapshot domain's ``exported_at``, or None when the file cannot say."""
    try:
        data = json.loads((assets / str(domain["snapshot"])).read_text(encoding="utf-8"))
        return dt.date.fromisoformat(str(data["exported_at"]))
    except (OSError, ValueError, KeyError, TypeError):
        return None


def stale_reason(domain: dict[str, Any], exported: dt.date, today: dt.date) -> str:
    """The 待复核 reason for a snapshot past its limit, else ""."""
    limit = int(domain["stale_after_days"])
    if (today - exported).days > limit:
        return f"{domain['label']}快照已超过 {limit} 天（导出于 {exported.isoformat()}）"
    return ""


def sources_view(registry: Registry, *, assets: Path, today: dt.date,
                 link: Callable[[str], dict[str, str]]) -> list[dict[str, Any]]:
    """Rows for the public 数据来源 table, in registry order.

    ``link`` turns a ``file:<repo>:<path>`` ref into the page's evidence link,
    labelled with the full path (two directories may share a basename); any
    other authority shows as plain text.
    """
    rows = []
    for domain in registry.values():
        sources = []
        for ref in authorities(domain):
            match = _FILE_REF.fullmatch(ref)
            sources.append({**link(ref), "label": match.group(2)} if match
                           else {"label": ref, "href": "", "title": ref})
        stale: list[str] = []
        if domain["read"] == "snapshot":
            how = f"{READ_LABELS['snapshot']} {domain['snapshot']}"
            exported = snapshot_date(assets, domain)
            freshness = f"{domain['stale_after_days']} 天 · " + (
                f"快照 {exported.isoformat()}" if exported else domain["fallback"])
            if exported and (reason := stale_reason(domain, exported, today)):
                stale.append(reason)
        else:
            how = READ_LABELS["build"]
            freshness = f"{domain['stale_after_days']} 天复核" if domain.get("stale_after_days") else "随构建"
        rows.append({
            "id": domain["id"], "label": domain["label"], "sources": sources, "how": how,
            "refresh": domain.get("refresh") or "", "freshness": freshness, "stale": stale,
            "fallback": domain["fallback"], "used_by": domain["used_by"],
        })
    return rows
