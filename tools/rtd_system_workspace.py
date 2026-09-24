#!/usr/bin/env python3
"""Build-time System Workspace page: curated status plus frozen facts, no network.

``/workspace/system/`` joins three inputs that already exist in the tree RTD
builds from:

- ``tools/rtd_portal_assets/system_workspace.yaml``: the curated status
  contract (capability cards, flow links, gate labels); every entry carries
  evidence refs;
- ``docs/publish/publish_manifest.json``: the published-target catalog and the
  only source of the counts the page shows;
- the execution ledger named by ``now_next.source``: REV statuses and the
  composition of the G1-G4 gates.

Data drift never breaks the build: a missing evidence file, a REV whose status
moved, or an entry older than ``stale_after_days`` renders as 待复核. An
authoring error (vocabulary, card ceiling, evidence rules) drops only this page
with a Sphinx warning, so the manual site around it keeps building. ``check``
catches both classes before merge.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path, PurePosixPath
from typing import Any, NamedTuple
from urllib.parse import quote, urlsplit

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.utils.path_utils import PathSegments, repo_root  # noqa: E402

SCHEMA = "hello-docs-system-workspace/v1"
CONTRACT_NAME = "system_workspace.yaml"
DEFAULT_CONTRACT = Path(__file__).with_name("rtd_portal_assets") / CONTRACT_NAME
SYSTEM_PAGE = "workspace/system/index"
SYSTEM_TEMPLATE = "system_workspace.html"

STATUS_ORDER = {
    "available": 5, "validated": 4, "in_progress": 3, "blocked": 2,
    "planned": 1, "no_data": 0, "retired": -1,
}
IMPLEMENTED = frozenset({"available", "validated", "in_progress"})
STATUS_LABELS = {
    "available": "可用", "validated": "已验证", "in_progress": "建设中", "planned": "已规划",
    "blocked": "受阻", "no_data": "无数据", "retired": "已停用",
}
MODE_LABELS = {"automated": "自动衔接", "manual": "人工衔接"}
LEDGER_LABELS = {"done": "完成", "verifying": "在验", "planned": "待做", "deferred": "暂缓"}
EVIDENCE_KINDS = ("pr", "file", "url", "rev", "ack")

_QUANTITY = re.compile(r"\d+\s*(个|本|项|种|条|份|%|倍)")
_ACK = re.compile(r"\S+ (\d{4}-\d{2}-\d{2})「.+」")
_REV = re.compile(r"REV-\d+")
_REV_ROW = re.compile(r"^\|[^|]*?(REV-\d+)\s*\|")
_GATE_ROW = re.compile(r"^\|\s*(G\d+|IDML)\b[^|]*\|([^|]*)\|")
_REV_RANGE = re.compile(r"REV-(\d+)[–-](\d+)")
_DOCNAME = re.compile(r"^[A-Za-z0-9_.-]+(/[A-Za-z0-9_.-]+)*$")


class ContractError(ValueError):
    """The status contract cannot be read or parsed."""


class Finding(NamedTuple):
    severity: str  # "error" or "warning"
    where: str
    message: str


class Ledger(NamedTuple):
    statuses: dict[str, str]
    gates: dict[str, frozenset[str]]


# --- reading ------------------------------------------------------------------


def load_contract(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ContractError(f"cannot read {path.name}: {exc}") from exc
    if not isinstance(data, dict):
        raise ContractError(f"{path.name} is not a mapping")
    return data


def parse_ledger(text: str) -> Ledger:
    """REV row statuses and the REV ids each gate row names (ranges expanded)."""
    statuses: dict[str, str] = {}
    gates: dict[str, frozenset[str]] = {}
    for line in text.splitlines():
        row = _REV_ROW.match(line)
        if row:
            cells = [cell.strip() for cell in line.split("|")]
            if len(cells) > 5:
                statuses[row.group(1)] = cells[5]
            continue
        gate = _GATE_ROW.match(line)
        if gate:
            named = {f"REV-{int(n):02d}" for n in re.findall(r"REV-(\d+)", gate.group(2))}
            for start, end in _REV_RANGE.findall(gate.group(2)):
                named.update(f"REV-{i:02d}" for i in range(int(start), int(end) + 1))
            gates[gate.group(1)] = frozenset(named)
    return Ledger(statuses, gates)


def parse_evidence(ref: object) -> tuple[str, str, str]:
    """Split one evidence ref into ``(kind, first, second)``; raise when malformed."""
    if not isinstance(ref, str):
        raise ContractError(f"evidence must be a string: {ref!r}")
    kind, sep, rest = ref.partition(":")
    if not sep or kind not in EVIDENCE_KINDS:
        raise ContractError(f"unknown evidence kind: {ref!r}")
    if kind == "pr":
        repo, sep, number = rest.partition("#")
        if not sep or not repo or not number.isdigit():
            raise ContractError(f"pr evidence wants pr:<repo>#<number>: {ref!r}")
        return kind, repo, number
    if kind == "file":
        repo, sep, path = rest.partition(":")
        parts = PurePosixPath(path).parts
        if not sep or not repo or not path or path.startswith("/") or ".." in parts:
            raise ContractError(f"file evidence wants file:<repo>:<relative path>: {ref!r}")
        return kind, repo, path
    if kind == "url":
        parts = urlsplit(rest)
        if parts.scheme != "https" or not parts.netloc:
            raise ContractError(f"url evidence must be an https URL: {ref!r}")
        return kind, "", rest
    if kind == "rev":
        rev, sep, status = rest.partition("=")
        if not _REV.fullmatch(rev) or not sep or status not in LEDGER_LABELS:
            raise ContractError(f"rev evidence wants rev:REV-nn=<ledger status>: {ref!r}")
        return kind, rev, status
    match = _ACK.fullmatch(rest)
    if not match:
        raise ContractError(f"ack evidence wants ack:<who> <YYYY-MM-DD>「quote」: {ref!r}")
    return kind, match.group(1), rest


def expand_revs(tokens: object) -> list[str]:
    if not isinstance(tokens, list) or not tokens:
        raise ContractError(f"gate revs must be a non-empty list: {tokens!r}")
    revs: list[str] = []
    for token in tokens:
        text = str(token)
        if ".." in text:
            start, _, end = text.partition("..")
            if not (_REV.fullmatch(start) and _REV.fullmatch(end)):
                raise ContractError(f"bad REV range: {text!r}")
            low, high = int(start[4:]), int(end[4:])
            revs.extend(f"REV-{i:02d}" for i in range(low, high + 1))
        elif _REV.fullmatch(text):
            revs.append(text)
        else:
            raise ContractError(f"bad REV id: {text!r}")
    return revs


def ledger_ref(contract: dict[str, Any]) -> tuple[str, str]:
    kind, repo, path = parse_evidence((contract.get("now_next") or {}).get("source"))
    if kind != "file":
        raise ContractError("now_next.source must be a file: evidence ref")
    return repo, path


def load_ledger(contract: dict[str, Any], root: Path) -> Ledger | None:
    _, path = ledger_ref(contract)
    try:
        return parse_ledger((root / path).read_text(encoding="utf-8"))
    except OSError:
        return None


def publication_facts(manifest_path: Path) -> dict[str, Any] | None:
    """Counts from the frozen publish manifest (REV-04: a book is one model x region)."""
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    targets = data.get("targets") if isinstance(data, dict) else None
    if not isinstance(targets, list):
        return None
    editions = [t for t in targets if isinstance(t, dict) and t.get("model") and t.get("region")]
    if not editions:
        return None
    built = sorted(str(t.get("built_at") or "")[:10] for t in editions if t.get("built_at"))
    return {
        "books": len({(t["model"], t["region"]) for t in editions}),
        "editions": len(editions),
        "last_published": built[-1] if built else "",
        "targets": editions,
    }


# --- rules --------------------------------------------------------------------


def _entries(contract: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """Every evidence-bearing entry with a readable location."""
    found: list[tuple[str, dict[str, Any]]] = [("hero", contract.get("hero") or {})]
    for card in contract.get("capabilities") or []:
        for item in card.get("items") or []:
            found.append((f"{card.get('id')}.{item.get('id')}", item))
    for index, link in enumerate(contract.get("flow") or [], 1):
        found.append((f"flow#{index} {link.get('from')}→{link.get('to')}", link))
    return found


def structural_findings(contract: dict[str, Any], ledger: Ledger | None) -> list[Finding]:
    """Authoring errors that make the contract unrenderable, plus text warnings."""
    out: list[Finding] = []

    def error(where: str, message: str) -> None:
        out.append(Finding("error", where, message))

    if contract.get("schema") != SCHEMA:
        error("schema", f"expected {SCHEMA}, found {contract.get('schema')!r}")
    vocabulary = contract.get("vocabulary") or {}
    statuses = set((vocabulary.get("status") or {}))
    modes = set((vocabulary.get("mode") or {}))
    if not statuses or not statuses <= set(STATUS_ORDER):
        error("vocabulary.status", f"must be a subset of {sorted(STATUS_ORDER)}")
    if not modes or not modes <= set(MODE_LABELS):
        error("vocabulary.mode", f"must be a subset of {sorted(MODE_LABELS)}")
    repositories = contract.get("repositories") or {}
    for name, url in repositories.items():
        if urlsplit(str(url)).scheme != "https":
            error(f"repositories.{name}", "must be an https URL")
    if not isinstance(contract.get("verified_on"), dt.date):
        error("verified_on", "must be an ISO date")

    for where, entry in _entries(contract):
        evidence = entry.get("evidence") or []
        if not evidence:
            error(where, "no evidence")
            continue
        kinds = []
        for ref in evidence:
            try:
                kind, first, _ = parse_evidence(ref)
            except ContractError as exc:
                error(where, str(exc))
                continue
            kinds.append(kind)
            if kind in {"pr", "file"} and first not in repositories:
                error(where, f"unknown repository {first!r} in {ref!r}")
        if kinds and set(kinds) == {"ack"}:
            error(where, "an operator ack cannot be the only evidence")
        if where != "hero":
            status = entry.get("status")
            if status not in statuses:
                error(where, f"status {status!r} not in vocabulary")
            if status == "planned" and "rev" not in kinds:
                error(where, "planned needs a rev: reference")
            if status == "retired":
                error(where, "retired entries do not belong on the public page")
        for field in ("label", "note", "summary", "subtitle", "stage", "stage_note"):
            if _QUANTITY.search(str(entry.get(field) or "")):
                out.append(Finding("warning", where, f"{field} states a quantity; counts must come from the snapshot"))

    card_ids: dict[str, set[str]] = {}
    for card in contract.get("capabilities") or []:
        cid = str(card.get("id"))
        if cid in card_ids:
            error(cid, "duplicate card id")
        items = card.get("items") or []
        if not items:
            error(cid, "card has no items")
        card_ids[cid] = {str(item.get("id")) for item in items}
        if card.get("status") not in statuses:
            error(cid, f"card status {card.get('status')!r} not in vocabulary")
            continue
        implemented = [i.get("status") for i in items if i.get("status") in IMPLEMENTED]
        if implemented:
            ceiling = min(implemented, key=STATUS_ORDER.__getitem__)
            if STATUS_ORDER[card["status"]] > STATUS_ORDER[ceiling]:
                error(cid, f"card status {card['status']} is above its weakest implemented item ({ceiling})")
        if _QUANTITY.search(str(card.get("summary") or "")):
            out.append(Finding("warning", cid, "summary states a quantity; counts must come from the snapshot"))

    for index, link in enumerate(contract.get("flow") or [], 1):
        if link.get("mode") not in modes:
            error(f"flow#{index}", f"mode {link.get('mode')!r} not in vocabulary")

    for tile in contract.get("snapshot") or []:
        key = tile.get("key")
        sources = [name for name in ("source", "items", "card") if name in tile]
        if len(sources) != 1:
            error(f"snapshot.{key}", "needs exactly one of source / items / card")
        elif "source" in tile and tile["source"] not in {"publications", "build_date"}:
            error(f"snapshot.{key}", f"unknown source {tile['source']!r}")
        elif "card" in tile and tile["card"] not in card_ids:
            error(f"snapshot.{key}", f"unknown card {tile['card']!r}")
        elif "items" in tile:
            for ref in tile["items"]:
                cid, _, iid = str(ref).partition(".")
                if iid not in card_ids.get(cid, set()):
                    error(f"snapshot.{key}", f"unknown item {ref!r}")

    now_next = contract.get("now_next") or {}
    try:
        ledger_ref(contract)
    except ContractError as exc:
        error("now_next.source", str(exc))
    for gate in now_next.get("gates") or []:
        gid = str(gate.get("id"))
        try:
            revs = expand_revs(gate.get("revs"))
        except ContractError as exc:
            error(f"gate {gid}", str(exc))
            continue
        if ledger is None:
            continue
        unknown = [rev for rev in revs if rev not in ledger.statuses]
        if unknown:
            error(f"gate {gid}", f"REV ids missing from the ledger: {unknown}")
        named = ledger.gates.get(gid)
        if named is None:
            error(f"gate {gid}", "the ledger's gate table has no such gate")
        elif not set(revs) <= named:
            error(f"gate {gid}", f"REV ids the ledger's gate row does not name: {sorted(set(revs) - named)}")
    for rev in now_next.get("now_labels") or {}:
        if ledger is not None and rev not in ledger.statuses:
            error("now_labels", f"{rev} is not in the ledger")

    for entry in contract.get("working_today") or []:
        where = f"working_today.{entry.get('id')}"
        has_page, has_publication = "page" in entry, "publication" in entry
        if has_page == has_publication:
            error(where, "needs exactly one of page / publication")
        elif has_page and not _is_docname(entry["page"]):
            error(where, f"page must be a site docname: {entry['page']!r}")
        elif has_publication:
            publication = entry["publication"] or {}
            if not all(publication.get(k) for k in ("model", "region", "lang")):
                error(where, "publication needs model, region and lang")
    return out


def drift_reasons(entry: dict[str, Any], *, contract: dict[str, Any], root: Path,
                  ledger: Ledger | None, today: dt.date) -> list[str]:
    """Why an entry should read 待复核 right now; empty when it is current."""
    reasons: list[str] = []
    verified = entry.get("verified_on") or contract.get("verified_on")
    limit = int(contract.get("stale_after_days") or 30)
    if isinstance(verified, dt.date) and (today - verified).days > limit:
        reasons.append(f"超过 {limit} 天未复核（上次 {verified.isoformat()}）")
    for ref in entry.get("evidence") or []:
        kind, first, second = parse_evidence(ref)
        if kind == "file" and _checkable(first, root) and not (root / second).exists():
            reasons.append(f"证据文件不存在：{second}")
        elif kind == "rev":
            current = ledger.statuses.get(first) if ledger else None
            if current is None:
                reasons.append(f"台账中找不到 {first}")
            elif current != second:
                reasons.append(f"{first} 在台账中已变为 {current}（记录为 {second}）")
    return reasons


def _is_docname(value: object) -> bool:
    text = str(value)
    return bool(_DOCNAME.fullmatch(text)) and not {".", ".."} & set(text.split("/"))


def _checkable(repo: str, root: Path) -> bool:
    """Business-plane refs only resolve inside a tree that carries docs/publish."""
    return repo != "hello-docs" or (root / PathSegments.DOCS / PathSegments.PUBLISH).is_dir()


def check_contract(contract: dict[str, Any], *, root: Path, today: dt.date) -> list[Finding]:
    """Offline check: rules, in-tree evidence files, REV ids and drift."""
    ledger = load_ledger(contract, root)
    findings = structural_findings(contract, ledger)
    if ledger is None:
        findings.append(Finding("error", "now_next.source", "execution ledger is not readable"))
    if any(f.severity == "error" for f in findings):
        return findings
    for where, entry in _entries(contract):
        for reason in drift_reasons(entry, contract=contract, root=root, ledger=ledger, today=today):
            broken = reason.startswith(("证据文件不存在", "台账中找不到"))
            findings.append(Finding("error" if broken else "warning", where, reason))
    return findings


def online_findings(contract: dict[str, Any]) -> list[Finding]:
    """Confirm pr: refs are merged, business-plane files are on main and url: refs answer 200."""
    findings: list[Finding] = []
    repositories = contract.get("repositories") or {}
    refs = sorted({ref for _, entry in _entries(contract) for ref in entry.get("evidence") or []})
    for ref in refs:
        kind, first, second = parse_evidence(ref)
        owner_repo = urlsplit(str(repositories.get(first, ""))).path.strip("/")
        if kind == "pr":
            payload = _get_json(f"https://api.github.com/repos/{owner_repo}/pulls/{second}")
            if not isinstance(payload, dict) or payload.get("merged") is not True:
                findings.append(Finding("error", ref, "pull request is not merged or not readable"))
        elif kind == "file" and first == "hello-docs":
            # Offline these resolve only inside a Hello-Docs tree; online, ask its main.
            status = _http_status(f"https://api.github.com/repos/{owner_repo}/contents/{quote(second)}?ref=main")
            if status != 200:
                findings.append(Finding("error", ref, f"not on main (HTTP {status})"))
        elif kind == "url":
            status = _http_status(second)
            if status != 200:
                findings.append(Finding("error", ref, f"answered HTTP {status}"))
    return findings


def _request(url: str) -> urllib.request.Request:
    headers = {"User-Agent": "hello-docs-system-workspace-check"}
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token and url.startswith("https://api.github.com/"):
        headers["Authorization"] = f"Bearer {token}"
    return urllib.request.Request(url, headers=headers)


def _get_json(url: str) -> object:
    try:
        with urllib.request.urlopen(_request(url), timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, ValueError, TimeoutError):
        return None


def _http_status(url: str) -> int:
    try:
        with urllib.request.urlopen(_request(url), timeout=20) as response:
            return int(response.status)
    except urllib.error.HTTPError as exc:
        return int(exc.code)
    except (urllib.error.URLError, TimeoutError):
        return 0


# --- page context -------------------------------------------------------------


def evidence_view(ref: str, repositories: dict[str, str], ledger_url: str) -> dict[str, str]:
    kind, first, second = parse_evidence(ref)
    if kind == "pr":
        prefix = "HD" if first == "hello-docs" else ""
        return {"label": f"{prefix}#{second}", "href": f"{repositories[first]}/pull/{second}",
                "title": f"{first} pull request #{second}"}
    if kind == "file":
        return {"label": PurePosixPath(second).name, "href": f"{repositories[first]}/blob/main/{second}",
                "title": f"{first}: {second}"}
    if kind == "url":
        parts = urlsplit(second)
        return {"label": (parts.netloc + parts.path).rstrip("/"), "href": second, "title": second}
    if kind == "rev":
        return {"label": first, "href": f"{ledger_url}#{first.lower()}",
                "title": f"执行台账 {first}（复核时为 {second}）"}
    return {"label": f"操作者确认 {first}", "href": "", "title": second}


def _status_view(status: str) -> dict[str, str]:
    return {"status": status, "status_label": STATUS_LABELS[status]}


def build_context(contract: dict[str, Any], *, root: Path, ledger: Ledger | None,
                  facts: dict[str, Any] | None, today: dt.date) -> dict[str, Any]:
    repositories = {k: str(v).rstrip("/") for k, v in (contract.get("repositories") or {}).items()}
    ledger_repo, ledger_path = ledger_ref(contract)
    ledger_url = f"{repositories[ledger_repo]}/blob/main/{ledger_path}"

    def entry_view(entry: dict[str, Any]) -> dict[str, Any]:
        return {
            **_status_view(entry["status"]),
            "note": entry.get("note") or "",
            "stale": drift_reasons(entry, contract=contract, root=root, ledger=ledger, today=today),
            "evidence": [evidence_view(ref, repositories, ledger_url) for ref in entry["evidence"]],
        }

    cards = []
    items_by_ref: dict[str, dict[str, Any]] = {}
    for card in contract["capabilities"]:
        entries = []
        for item in card["items"]:
            view = {"label": item["label"], "short": item.get("short") or item["label"], **entry_view(item)}
            items_by_ref[f"{card['id']}.{item['id']}"] = view
            entries.append(view)
        cards.append({"id": card["id"], "title": card["title"], "en": card.get("en") or "",
                      "summary": card.get("summary") or "", "entries": entries,
                      **_status_view(card["status"])})
    cards_by_id = {card["id"]: card for card in cards}

    tiles = []
    for tile in contract.get("snapshot") or []:
        view: dict[str, Any] = {"label": tile["label"], "kind": "no_data"}
        if tile.get("source") == "publications" and facts:
            view.update(kind="number", value=facts["books"], unit="本",
                        sub=f"{facts['editions']} 个语言版")
        elif tile.get("source") == "build_date":
            view.update(kind="date", value=today.isoformat(),
                        sub=f"最近发布 {facts['last_published']}" if facts and facts["last_published"] else "")
        elif "card" in tile:
            view.update(kind="status", **_status_view(cards_by_id[tile["card"]]["status"]))
        elif "items" in tile:
            view.update(kind="list", entries=[
                {"label": items_by_ref[ref]["short"], "status": items_by_ref[ref]["status"],
                 "note": "" if items_by_ref[ref]["status"] == "available" else items_by_ref[ref]["status_label"]}
                for ref in tile["items"]
            ])
        tiles.append(view)

    flow = [{"source": link["from"], "target": link["to"], "mode": link["mode"],
             "mode_label": MODE_LABELS[link["mode"]], **entry_view(link)} for link in contract["flow"]]

    gates, now = [], []
    if ledger is not None:
        for gate in contract["now_next"]["gates"]:
            revs = expand_revs(gate["revs"])
            counts: dict[str, int] = {}
            for rev in revs:
                state = ledger.statuses.get(rev, "planned")
                counts[state] = counts.get(state, 0) + 1
            done = counts.get("done", 0)
            if done == len(revs):
                state = "done"
            elif counts.get("deferred", 0) == len(revs):
                state = "deferred"
            elif done or counts.get("verifying"):
                state = "active"
            else:
                state = "idle"
            tally = " · ".join(f"{LEDGER_LABELS.get(k, k)} {counts[k]}" for k in LEDGER_LABELS if counts.get(k))
            gates.append({"id": gate["id"], "label": gate["label"], "state": state, "tally": tally,
                          "done": done, "total": len(revs), "percent": round(100 * done / len(revs))})
        for rev, label in (contract["now_next"].get("now_labels") or {}).items():
            state = ledger.statuses.get(rev, "planned")
            now.append({"rev": rev, "label": label, "status": state,
                        "status_label": LEDGER_LABELS.get(state, state), "href": f"{ledger_url}#{rev.lower()}"})

    working = []
    for entry in contract.get("working_today") or []:
        view = {"label": entry["label"], "note": entry.get("note") or "", "docname": "", "meta": ""}
        if "page" in entry:
            view["docname"] = entry["page"]
        else:
            wanted = entry["publication"]
            match = next((t for t in (facts or {}).get("targets", [])
                          if (t.get("model"), t.get("region"), t.get("lang"))
                          == (wanted["model"], wanted["region"], wanted["lang"])), None)
            if match and match.get("route") and match.get("manual"):
                view["docname"] = f"{match['route']}/{PurePosixPath(match['manual']).stem}"
                view["meta"] = f"版本 {match.get('version') or '未标注'}"
        working.append(view)

    status_vocabulary = contract["vocabulary"]["status"]
    return {
        "hero": contract["hero"],
        "tiles": tiles,
        "legend": [{"status": s, "label": STATUS_LABELS[s], "description": status_vocabulary[s]}
                   for s in STATUS_ORDER if s in status_vocabulary and s != "retired"],
        "cards": cards,
        "flow": flow,
        "gates": gates,
        "now": now,
        "working": working,
        "stale_after_days": int(contract.get("stale_after_days") or 30),
        "verified_on": contract["verified_on"].isoformat(),
        "build_date": today.isoformat(),
        "last_published": (facts or {}).get("last_published", ""),
        "ledger_url": ledger_url,
    }


def _utc_today() -> dt.date:
    return dt.datetime.now(dt.timezone.utc).date()


def _iso_date(value: str) -> dt.date:
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not an ISO date: {value!r}") from None


def system_page_context(app, assets: Path) -> dict[str, Any] | None:
    """Context for SYSTEM_PAGE, or None (with a warning) when the page cannot render."""
    from sphinx.util import logging as sphinx_logging

    logger = sphinx_logging.getLogger(__name__)
    contract_path = assets / CONTRACT_NAME
    if not contract_path.is_file():
        return None
    root = repo_root()
    try:
        contract = load_contract(contract_path)
        ledger = load_ledger(contract, root)
        errors = [f for f in structural_findings(contract, ledger) if f.severity == "error"]
    except ContractError as exc:
        errors = [Finding("error", CONTRACT_NAME, str(exc))]
    if errors:
        logger.warning("System workspace page skipped: %s",
                       "; ".join(f"{f.where}: {f.message}" for f in errors[:5]))
        return None
    today = _utc_today()
    configured = str(app.config.rtd_system_workspace_date or "")
    if configured:
        try:
            today = dt.date.fromisoformat(configured)
        except ValueError:
            logger.warning("rtd_system_workspace_date %r is not an ISO date; using %s", configured, today)
    facts = publication_facts(Path(app.srcdir).parent / PathSegments.PUBLISH_MANIFEST_JSON)
    return build_context(contract, root=root, ledger=ledger, facts=facts, today=today)


# --- CLI ----------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check the System Workspace status contract.")
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check", help="validate rules, evidence refs and drift")
    check.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    check.add_argument("--root", type=Path, default=None,
                       help="tree that file: evidence resolves against (default: this checkout)")
    check.add_argument("--today", type=_iso_date, default=None,
                       help="ISO date used for staleness (default: today, UTC)")
    check.add_argument("--online", action="store_true",
                       help="also confirm pr: refs are merged and url: refs answer 200")
    args = parser.parse_args(argv)

    root = (args.root or repo_root()).resolve()
    try:
        contract = load_contract(args.contract)
        findings = check_contract(contract, root=root, today=args.today or _utc_today())
        if args.online and not any(f.severity == "error" for f in findings):
            findings += online_findings(contract)
    except ContractError as exc:
        findings = [Finding("error", args.contract.name, str(exc))]
    for finding in findings:
        print(f"{finding.severity.upper():7} {finding.where}: {finding.message}")
    errors = sum(f.severity == "error" for f in findings)
    unchecked = ("" if args.online or _checkable("hello-docs", root)
                 else "; hello-docs file refs unchecked (use --online or a Hello-Docs --root)")
    print(f"system workspace contract: {errors} error(s), {len(findings) - errors} warning(s){unchecked}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
