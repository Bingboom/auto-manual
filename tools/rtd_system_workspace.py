#!/usr/bin/env python3
"""Build-time System Workspace page: curated status plus frozen facts, no network.

``/workspace/system/`` joins inputs that already exist in the tree RTD builds
from:

- ``tools/rtd_portal_assets/system_workspace.yaml``: the curated status
  contract (current-focus lanes, capability cards, flow links, gate labels);
  every entry carries evidence refs;
- ``docs/publish/publish_manifest.json``: the published-target catalog and the
  source of the publication counts;
- the execution ledger named by ``now_next.source``: REV statuses, the
  composition of the G1-G4 gates and the progress of each focus lane;
- the corpus snapshot registered as the ``corpus`` domain of
  ``source_registry.yaml``: translation-memory counts (never its text) plus the
  headline of earlier months, written from the live TM base by
  ``corpus-export`` and committed like any other frozen input;
- the skeleton blueprints under ``docs/manifests/skeletons``: which product
  families already generate their manual structure from a skeleton;
- the source registry (``source_registry.yaml``, REV-44): every snapshot name,
  freshness limit and fallback text the page shows, listed on the page as
  数据来源.

Data drift never breaks the build: a missing evidence file, a REV whose status
moved, or an entry older than the ``capabilities`` domain's review cycle
renders as 待复核. An authoring error (vocabulary, card ceiling, evidence
rules, an unsound source registry) drops only this page
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

from tools.rtd_system_tooling import (  # noqa: E402
    hook_facts,
    skill_facts,
    tooling_findings,
    tooling_problems,
    tooling_view,
)
from tools.rtd_source_registry import (  # noqa: E402
    REGISTRY_NAME,
    Registry,
    file_refs,
    load_registry,
    snapshot_date,
    sources_view,
    stale_reason,
)
from tools.utils.path_utils import PathSegments, repo_root, skeletons_of  # noqa: E402

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
CORPUS_SCHEMA = "hello-docs-tm-corpus/v1"
CORPUS_STATUS_FIELD = "Status"
CORPUS_APPROVED = "Approved"
CORPUS_UNLABELLED = "(未标注)"
CORPUS_HISTORY_KEYS = ("exported_at", "sentence_pairs", "terms", "approved")
CORPUS_HISTORY_KEEP = 24  # months of headline figures carried by each snapshot
HORIZON_LABELS = {
    "now": "01 · 当前主线", "support": "同期 · 持续支撑",
    "next": "02 · 代表试点", "later": "03 · 稳定后扩展", "deferred": "后置 · 按需",
}
FOCUS_METRICS = ("publications", "regions", "corpus", "skeletons")
SKELETON_SCHEMA = "skeleton-blueprint/v1"
_UNSTATUSED = frozenset({"hero", "focus"})  # evidence-bearing entries without a status

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
        raise ContractError(f"revs must be a non-empty list: {tokens!r}")
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


def skeleton_facts(root: Path) -> list[dict[str, str]] | None:
    """One ``{id, family}`` per skeleton cell; None (no data) when there is none or one is unreadable.

    An unreadable blueprint makes the whole count unknown rather than one
    lower: the page never shows a number it cannot stand behind.
    """
    cells: list[dict[str, str]] = []
    for path in sorted(skeletons_of(root).glob(f"*/{PathSegments.SKELETON_BLUEPRINT_YAML}")):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError):
            return None
        if not isinstance(data, dict) or data.get("schema_version") != SKELETON_SCHEMA \
                or not data.get("skeleton_family"):
            return None
        cells.append({"id": str(data.get("skeleton_id") or path.parent.name),
                      "family": str(data["skeleton_family"])})
    return cells or None


# --- rules --------------------------------------------------------------------


def _entries(contract: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """Every evidence-bearing entry with a readable location."""
    found: list[tuple[str, dict[str, Any]]] = [("hero", contract.get("hero") or {})]
    if isinstance(contract.get("focus"), dict):
        found.append(("focus", contract["focus"]))
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
        if where not in _UNSTATUSED:
            status = entry.get("status")
            if status not in statuses:
                error(where, f"status {status!r} not in vocabulary")
            if status == "planned" and "rev" not in kinds:
                error(where, "planned needs a rev: reference")
            if status == "retired":
                error(where, "retired entries do not belong on the public page")
        for field in ("label", "note", "summary", "subtitle"):
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
        if not isinstance(card.get("fold", False), bool):
            error(cid, "fold must be true or false")
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

    now_next = contract.get("now_next") or {}
    try:
        ledger_ref(contract)
    except ContractError as exc:
        error("now_next.source", str(exc))
    for gate in now_next.get("gates") or []:
        gid = str(gate.get("id"))
        if not isinstance(gate.get("fold", False), bool):
            error(f"gate {gid}", "fold must be true or false")
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

    corpus = contract.get("corpus")
    if corpus is not None:
        languages = corpus.get("languages") if isinstance(corpus, dict) else None
        codes = [str(lang.get("code")) for lang in languages or [] if isinstance(lang, dict)]
        if not codes or len(set(codes)) != len(codes) or not all(
                isinstance(lang, dict) and lang.get("label") for lang in languages or []):
            error("corpus.languages", "needs unique codes, each with a label")

    if "focus" in contract:
        gate_ids = {str(gate.get("id")) for gate in now_next.get("gates") or []}
        out += _focus_findings(contract["focus"], card_ids=card_ids, gate_ids=gate_ids,
                               ledger=ledger, has_corpus=corpus is not None)
    if "tooling" in contract:
        lane_ids = {str(lane.get("id")) for lane in (contract.get("focus") or {}).get("lanes") or []
                    if isinstance(lane, dict)}
        out += [Finding("error", "tooling", problem) for problem in tooling_problems(contract["tooling"], lane_ids)]
    return out


def _focus_findings(focus: object, *, card_ids: dict[str, set[str]], gate_ids: set[str],
                    ledger: Ledger | None, has_corpus: bool) -> list[Finding]:
    """Rules for the current-focus lanes: every reference resolves, progress comes from the ledger."""
    if not isinstance(focus, dict) or not isinstance(focus.get("lanes"), list) or not focus["lanes"]:
        return [Finding("error", "focus", "needs a non-empty lanes list")]
    out: list[Finding] = []

    def error(where: str, message: str) -> None:
        out.append(Finding("error", where, message))

    seen: set[str] = set()
    for lane in focus["lanes"]:
        if not isinstance(lane, dict):
            error("focus", f"lane must be a mapping: {lane!r}")
            continue
        lid = str(lane.get("id"))
        where = f"focus.{lid}"
        if lid in seen:
            error(where, "duplicate lane id")
        seen.add(lid)
        if lane.get("horizon") not in HORIZON_LABELS:
            error(where, f"horizon must be one of {sorted(HORIZON_LABELS)}")
        if not lane.get("title"):
            error(where, "needs a title")
        if "card" in lane and lane["card"] not in card_ids:
            error(where, f"unknown card {lane['card']!r}")
        for ref in lane.get("items") or []:
            cid, _, iid = str(ref).partition(".")
            if iid not in card_ids.get(cid, set()):
                error(where, f"unknown item {ref!r}")
        for metric in lane.get("metrics") or []:
            if metric not in FOCUS_METRICS:
                error(where, f"unknown metric {metric!r}")
            elif metric == "corpus" and not has_corpus:
                error(where, "the corpus metric needs the corpus section")
        for gid in lane.get("gates") or []:
            if str(gid) not in gate_ids:
                error(where, f"unknown gate {gid!r}")
        if "revs" in lane:
            try:
                revs = expand_revs(lane["revs"])
            except ContractError as exc:
                error(where, str(exc))
                revs = []
            unknown = [rev for rev in revs if ledger is not None and rev not in ledger.statuses]
            if unknown:
                error(where, f"REV ids missing from the ledger: {unknown}")
        if _QUANTITY.search(str(lane.get("goal") or "")):
            out.append(Finding("warning", where, "goal states a quantity; counts must come from the snapshot"))
    regions = focus.get("regions", {})
    if not isinstance(regions, dict) or not all(isinstance(v, str) and v for v in regions.values()):
        error("focus.regions", "must map region codes to labels")
    families = focus.get("skeleton_families", [])
    if not isinstance(families, list) or not all(
            isinstance(entry, dict) and entry.get("family") and entry.get("label") for entry in families):
        error("focus.skeleton_families", "each entry needs a family and a label")
    return out


def drift_reasons(entry: dict[str, Any], *, contract: dict[str, Any], root: Path,
                  ledger: Ledger | None, today: dt.date, review_days: int) -> list[str]:
    """Why an entry should read 待复核 right now; empty when it is current.

    ``review_days`` is the ``capabilities`` domain's review cycle in the source registry.
    """
    reasons: list[str] = []
    verified = entry.get("verified_on") or contract.get("verified_on")
    limit = review_days
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


def check_contract(contract: dict[str, Any], *, root: Path, today: dt.date,
                   assets: Path | None = None, registry: Registry | None = None) -> list[Finding]:
    """Offline check: rules, the source registry, in-tree evidence files, REV ids, drift and snapshots.

    ``registry`` defaults to ``source_registry.yaml`` in ``assets``.
    """
    assets = assets or DEFAULT_CONTRACT.parent
    ledger = load_ledger(contract, root)
    findings = structural_findings(contract, ledger)
    if ledger is None:
        findings.append(Finding("error", "now_next.source", "execution ledger is not readable"))
    if registry is None:
        registry, problems = load_registry(assets)
        findings += [Finding("error", REGISTRY_NAME, problem) for problem in problems]
    if registry is not None:
        for domain_id, repo, path in file_refs(registry):
            if _checkable(repo, root) and not (root / path).exists():
                findings.append(Finding("error", f"{REGISTRY_NAME}: {domain_id}", f"authority does not exist: {path}"))
    if registry is None or any(f.severity == "error" for f in findings):
        return findings
    review_days = int(registry["capabilities"]["stale_after_days"])
    for where, entry in _entries(contract):
        for reason in drift_reasons(entry, contract=contract, root=root, ledger=ledger, today=today,
                                    review_days=review_days):
            broken = reason.startswith(("证据文件不存在", "台账中找不到"))
            findings.append(Finding("error" if broken else "warning", where, reason))
    corpus_domain = registry["corpus"]
    snapshot, problems = load_corpus(contract, assets, str(corpus_domain["snapshot"]))
    findings += [Finding("error", "corpus", problem) for problem in problems]
    if snapshot is not None:
        findings += [Finding("warning", "corpus", reason) for reason in
                     corpus_view(contract, snapshot, today, int(corpus_domain["stale_after_days"]))["stale"]]
    for domain_id, domain in registry.items():
        if domain["read"] != "snapshot" or domain_id == "corpus":
            continue  # the corpus snapshot is checked in depth above
        exported = snapshot_date(assets, domain)
        reason = (f"cannot read the exported_at of {domain['snapshot']}" if exported is None
                  else stale_reason(domain, exported, today))
        if reason:
            findings.append(Finding("warning", f"{REGISTRY_NAME}: {domain_id}", reason))
    lanes = (contract.get("focus") or {}).get("lanes") or []
    if any("skeletons" in (lane.get("metrics") or []) for lane in lanes) and skeleton_facts(root) is None:
        findings.append(Finding("warning", "focus", "no readable skeleton blueprints; the skeleton metric shows 无数据"))
    if "tooling" in contract:
        findings += [Finding(*finding) for finding in
                     tooling_findings(contract["tooling"], skill_facts(root), hook_facts(root))]
    return findings


# --- corpus snapshot (aggregates of the translation memory; never its text) ----


def _count(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def corpus_problems(snapshot: object, codes: list[str]) -> list[str]:
    """Why a committed corpus snapshot cannot be shown; empty when it is sound."""
    if not isinstance(snapshot, dict) or snapshot.get("schema") != CORPUS_SCHEMA:
        return [f"snapshot schema must be {CORPUS_SCHEMA}"]
    problems = []
    try:
        exported = dt.date.fromisoformat(str(snapshot.get("exported_at")))
    except ValueError:
        problems.append("exported_at must be an ISO date")
        exported = None
    extra = set(snapshot) - {"schema", "exported_at", "sentence_pairs", "terms", "history"}
    if extra:
        problems.append(f"snapshot carries unexpected keys {sorted(extra)} (aggregates only)")
    problems += _history_problems(snapshot.get("history", []), exported)
    for key in ("sentence_pairs", "terms"):
        block = snapshot.get(key)
        if not isinstance(block, dict) or not _count(block.get("total")):
            problems.append(f"{key}.total must be a non-negative integer")
            continue
        total = block["total"]
        if set(block) - {"total", "by_language", "by_status"}:
            problems.append(f"{key} carries unexpected keys (aggregates only)")
        by_language = block.get("by_language")
        if not isinstance(by_language, dict) or set(by_language) != set(codes):
            problems.append(f"{key}.by_language must list exactly the contract languages")
        elif not all(_count(v) and v <= total for v in by_language.values()):
            problems.append(f"{key}.by_language counts must be integers between 0 and total")
        by_status = block.get("by_status")
        if (not isinstance(by_status, dict) or not all(_count(v) for v in by_status.values())
                or sum(by_status.values()) != total):
            problems.append(f"{key}.by_status must be integer counts that sum to total")
    return problems


def _history_problems(history: object, exported: dt.date | None) -> list[str]:
    """Earlier months' headline figures: counts only, oldest first, all before this export."""
    if not isinstance(history, list):
        return ["history must be a list"]
    previous: dt.date | None = None
    for entry in history:
        if not isinstance(entry, dict) or set(entry) != set(CORPUS_HISTORY_KEYS):
            return [f"history entries carry exactly {list(CORPUS_HISTORY_KEYS)} (aggregates only)"]
        try:
            when = dt.date.fromisoformat(str(entry["exported_at"]))
        except ValueError:
            return ["history exported_at must be an ISO date"]
        if (previous and when <= previous) or (exported and when >= exported):
            return ["history must run oldest first and end before this export"]
        if not all(_count(entry[key]) for key in CORPUS_HISTORY_KEYS[1:]) \
                or entry["approved"] > entry["sentence_pairs"]:
            return ["history counts must be non-negative integers, approved at most sentence_pairs"]
        previous = when
    return []


def corpus_headline(snapshot: dict[str, Any]) -> dict[str, Any]:
    """The figures one month keeps in later snapshots' history."""
    pairs = snapshot["sentence_pairs"]
    return {"exported_at": snapshot["exported_at"], "sentence_pairs": pairs["total"],
            "terms": snapshot["terms"]["total"], "approved": pairs["by_status"].get(CORPUS_APPROVED, 0)}


def load_corpus(contract: dict[str, Any], assets: Path, name: str) -> tuple[dict[str, Any] | None, list[str]]:
    """The committed corpus snapshot ``name`` (from the source registry), or None with the reasons."""
    config = contract.get("corpus")
    if not config:
        return None, []
    try:
        data = json.loads((assets / name).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return None, [f"cannot read {name}: {exc}"]
    problems = corpus_problems(data, [str(lang["code"]) for lang in config["languages"]])
    return (None if problems else data), problems


def corpus_view(contract: dict[str, Any], snapshot: dict[str, Any], today: dt.date,
                stale_days: int) -> dict[str, Any]:
    config = contract["corpus"]
    pairs, terms = snapshot["sentence_pairs"], snapshot["terms"]
    total = pairs["total"]
    rows = [{"code": lang["code"], "label": lang["label"], "count": pairs["by_language"][lang["code"]]}
            for lang in config["languages"]]
    rows.sort(key=lambda row: -row["count"])  # stable: ties keep the contract order
    for row in rows:
        row["percent"] = round(100 * row["count"] / total) if total else 0
        row["count_text"] = f"{row['count']:,}"
    approved = pairs["by_status"].get(CORPUS_APPROVED, 0)
    share = round(100 * approved / total) if total else None
    exported = dt.date.fromisoformat(snapshot["exported_at"])
    limit = stale_days
    stale = [f"语料快照已超过 {limit} 天（导出于 {exported.isoformat()}）"] if (today - exported).days > limit else []
    history = snapshot.get("history") or []
    last = history[-1] if history else None

    def change(now: int | None, before: int | None, unit: str = "") -> str:
        if last is None or now is None or before is None:
            return ""
        diff = now - before
        return f"较 {last['exported_at']} {diff:+,}{unit}" if diff else f"较 {last['exported_at']} 持平"

    before_share = (round(100 * last["approved"] / last["sentence_pairs"])
                    if last and last["sentence_pairs"] else None)
    return {
        "tiles": [
            {"key": "pairs", "label": "句对", "value": f"{total:,}",
             "delta": change(total, last["sentence_pairs"] if last else None)},
            {"key": "terms", "label": "术语", "value": f"{terms['total']:,}",
             "delta": change(terms["total"], last["terms"] if last else None)},
            # Languages with any translated pair: corpus coverage, not manual localization.
            {"key": "languages", "label": "语料覆盖语言", "value": str(sum(1 for row in rows if row["count"])),
             "delta": ""},
            {"key": "approved", "label": "句对已批准", "value": f"{share}%" if share is not None else "—",
             "delta": change(share, before_share, " 个百分点")},
        ],
        "rows": rows,
        "exported_at": exported.isoformat(),
        "previous": last["exported_at"] if last else "",
        "stale": stale,
    }


def _field_name(item: object) -> str:
    if isinstance(item, dict):
        return str(item.get("field_name") or item.get("name") or "")
    return str(item)


def _filled(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return any(_filled(part) for part in value)
    return True


def _cell_text(value: object) -> str:
    if isinstance(value, list):
        value = value[0] if value else ""
    if isinstance(value, dict):
        value = value.get("text") or value.get("name") or ""
    return str(value).strip() if value is not None else ""


def _table_rows(run, base_token: str, table_id: str) -> tuple[list[str], list[dict[str, Any]]]:
    """Every row of one table as {field: value}; +record-list caps a page at 200."""
    header: list[str] = []
    rows: list[dict[str, Any]] = []
    offset = 0
    while True:
        payload = run(["base", "+record-list", "--base-token", base_token, "--table-id", table_id,
                       "--format", "json", "--limit", "200", "--offset", str(offset)])
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, dict):
            raise RuntimeError(f"record-list returned no data payload for {table_id}")
        names = [_field_name(item) for item in data.get("fields") or []]
        header = header or names
        page = data.get("data") or []
        rows += [dict(zip(names, row)) for row in page if isinstance(row, list)]
        if len(page) < 200:
            return header, rows
        offset += 200


def _table_aggregate(header: list[str], rows: list[dict[str, Any]], codes: list[str]) -> dict[str, Any]:
    missing = [name for name in [*codes, CORPUS_STATUS_FIELD] if name not in header]
    if missing:
        raise RuntimeError(f"translation-memory table is missing columns {missing}")
    status: dict[str, int] = {}
    for row in rows:
        key = _cell_text(row.get(CORPUS_STATUS_FIELD)) or CORPUS_UNLABELLED
        status[key] = status.get(key, 0) + 1
    return {
        "total": len(rows),
        "by_language": {code: sum(_filled(row.get(code)) for row in rows) for code in codes},
        "by_status": dict(sorted(status.items())),
    }


def corpus_export(contract: dict[str, Any], *, base_token: str, run, today: dt.date,
                  previous: dict[str, Any] | None = None) -> dict[str, Any]:
    """Aggregate the live TM base into a snapshot; read-only, counts only.

    ``previous`` is the snapshot being replaced. Its headline joins the
    history when it came from an earlier month; a re-export within the same
    month supersedes it, so history keeps one entry per month.
    """
    from tools.lang_asset_sweep import TM_SENTENCE_TABLE, TM_TERMS_TABLE

    codes = [str(lang["code"]) for lang in contract["corpus"]["languages"]]
    snapshot: dict[str, Any] = {
        "schema": CORPUS_SCHEMA,
        "exported_at": today.isoformat(),
        "sentence_pairs": _table_aggregate(*_table_rows(run, base_token, TM_SENTENCE_TABLE), codes),
        "terms": _table_aggregate(*_table_rows(run, base_token, TM_TERMS_TABLE), codes),
    }
    month = today.isoformat()[:7]
    history = list((previous or {}).get("history") or [])
    if previous:
        history.append(corpus_headline(previous))
    history = [entry for entry in history if str(entry["exported_at"])[:7] < month][-CORPUS_HISTORY_KEEP:]
    if history:
        snapshot["history"] = history
    return snapshot


def lark_runner(cli_bin: str, identity: str):
    """``run(args) -> payload`` over the shared hardened lark-cli transport."""
    from tools.feishu_record_transport import run_lark_cli_json
    from tools.phase2_support import parse_json_payload, resolved_cli_command_parts

    def run(args: list[str]) -> dict[str, Any]:
        if identity:
            args = [*args[:2], "--as", identity, *args[2:]]
        return run_lark_cli_json(cli_bin=cli_bin, args=args, repo_root=_REPO_ROOT,
                                 resolved_cli_command_parts=resolved_cli_command_parts,
                                 parse_json_payload=parse_json_payload, on_command=lambda cmd: None)

    return run


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


def _progress(revs: list[str], ledger: Ledger) -> dict[str, Any]:
    """Done count, bar width, state and tally for a set of ledger rows."""
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
    return {"state": state, "tally": tally, "done": done, "total": len(revs),
            "percent": round(100 * done / len(revs))}


def _metric(label: str, value: object = None, unit: str = "", sub: str = "", delta: str = "") -> dict[str, Any]:
    if value is None:
        return {"label": label, "no_data": True, "value": "", "unit": "", "sub": "", "delta": ""}
    return {"label": label, "no_data": False, "value": str(value), "unit": unit, "sub": sub, "delta": delta}


def lane_metrics(name: str, *, focus: dict[str, Any], facts: dict[str, Any] | None,
                 corpus: dict[str, Any] | None, skeletons: list[dict[str, str]] | None) -> list[dict[str, Any]]:
    """The figures one focus lane shows; each source missing renders as 无数据, never as zero."""
    if name == "publications":
        if not facts:
            return [_metric("在线手册")]
        return [_metric("在线手册", facts["books"], "本", f"{facts['editions']} 个语言版")]
    if name == "regions":
        if not facts:
            return [_metric("覆盖区域")]
        labels = focus.get("regions") or {}
        books: dict[str, int] = {}
        for _model, region in {(t["model"], t["region"]) for t in facts["targets"]}:
            books[region] = books.get(region, 0) + 1
        order = sorted(books, key=lambda region: (-books[region], region))
        sub = " · ".join(f"{labels.get(region, region)} {books[region]} 本" for region in order)
        return [_metric("覆盖区域", len(books), "个", sub)]
    if name == "corpus":
        if not corpus:
            return [_metric("语料快照")]
        tiles = {tile["key"]: tile for tile in corpus["tiles"]}
        return [_metric(tiles[key]["label"], tiles[key]["value"], delta=tiles[key]["delta"])
                for key in ("pairs", "terms", "approved")]
    if not skeletons:
        return [_metric("产品骨架")]
    declared = {str(entry["family"]): str(entry["label"]) for entry in focus.get("skeleton_families") or []}
    counts: dict[str, int] = {}
    for cell in skeletons:
        counts[cell["family"]] = counts.get(cell["family"], 0) + 1
    families = [*declared, *sorted(set(counts) - set(declared))]
    sub = " · ".join(f"{declared.get(family, family)} {counts[family]}" if family in counts
                     else f"{declared[family]} 未建" for family in families)
    return [_metric("产品骨架", len(skeletons), "个", sub)]


def build_context(contract: dict[str, Any], *, root: Path, ledger: Ledger | None,
                  facts: dict[str, Any] | None, today: dt.date,
                  registry: Registry, assets: Path,
                  corpus: dict[str, Any] | None = None,
                  skeletons: list[dict[str, str]] | None = None,
                  skills: list[dict[str, Any]] | None = None,
                  hooks: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    repositories = {k: str(v).rstrip("/") for k, v in (contract.get("repositories") or {}).items()}
    ledger_repo, ledger_path = ledger_ref(contract)
    ledger_url = f"{repositories[ledger_repo]}/blob/main/{ledger_path}"
    focus = contract.get("focus") or {}
    lanes = focus.get("lanes") or []
    review_days = int(registry["capabilities"]["stale_after_days"])

    def entry_view(entry: dict[str, Any]) -> dict[str, Any]:
        return {
            **_status_view(entry["status"]),
            "note": entry.get("note") or "",
            "stale": drift_reasons(entry, contract=contract, root=root, ledger=ledger, today=today,
                                   review_days=review_days),
            "evidence": [evidence_view(ref, repositories, ledger_url) for ref in entry["evidence"]],
        }

    def lane_tag(lane: dict[str, Any]) -> dict[str, str]:
        return {"title": lane["title"], "horizon": lane["horizon"], "horizon_label": HORIZON_LABELS[lane["horizon"]]}

    cards = []
    items_by_ref: dict[str, dict[str, Any]] = {}
    for card in contract["capabilities"]:
        entries = []
        for item in card["items"]:
            view = {"label": item["label"], "short": item.get("short") or item["label"], **entry_view(item)}
            items_by_ref[f"{card['id']}.{item['id']}"] = view
            entries.append(view)
        cards.append({"id": card["id"], "title": card["title"], "en": card.get("en") or "",
                      "summary": card.get("summary") or "", "entries": entries, "fold": bool(card.get("fold")),
                      "lanes": [lane_tag(lane) for lane in lanes if lane.get("card") == card["id"]],
                      **_status_view(card["status"])})

    flow = [{"source": link["from"], "target": link["to"], "mode": link["mode"],
             "mode_label": MODE_LABELS[link["mode"]], **entry_view(link)} for link in contract["flow"]]

    gates, now = [], []
    if ledger is not None:
        for gate in contract["now_next"]["gates"]:
            gates.append({"id": gate["id"], "label": gate["label"], "fold": bool(gate.get("fold")),
                          "lanes": [lane_tag(lane) for lane in lanes if gate["id"] in (lane.get("gates") or [])],
                          **_progress(expand_revs(gate["revs"]), ledger)})
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

    corpus_block = corpus_view(contract, corpus, today, int(registry["corpus"]["stale_after_days"])) if corpus else None
    gates_by_id = {gate["id"]: gate for gate in gates}

    def lane_view(lane: dict[str, Any]) -> dict[str, Any]:
        tracked = bool(lane.get("gates") or lane.get("revs"))
        progress: list[dict[str, Any]] = []
        if ledger is not None:
            for gid in lane.get("gates") or []:
                if gid in gates_by_id:
                    progress.append({"kind": "gate", **gates_by_id[gid]})
            if lane.get("revs"):
                revs = expand_revs(lane["revs"])
                rows = []
                for rev in revs:
                    state = ledger.statuses.get(rev, "planned")
                    rows.append({"rev": rev, "status": state, "status_label": LEDGER_LABELS.get(state, state),
                                 "href": f"{ledger_url}#{rev.lower()}"})
                progress.append({"kind": "revs", "id": "台账", "label": "执行台账", "revs": rows,
                                 **_progress(revs, ledger)})
        return {
            "id": lane["id"], "title": lane["title"], "goal": lane.get("goal") or "",
            "action": lane.get("action") or "",
            "horizon": lane["horizon"], "horizon_label": HORIZON_LABELS[lane["horizon"]],
            "card": lane.get("card") or "",
            "metrics": [metric for name in lane.get("metrics") or []
                        for metric in lane_metrics(name, focus=focus, facts=facts,
                                                   corpus=corpus_block, skeletons=skeletons)],
            # Not "items": Jinja resolves lane.items to the dict method.
            "entries": [items_by_ref[ref] for ref in lane.get("items") or []],
            "progress": progress,
            "untracked": not tracked and lane["horizon"] != "deferred",
            "ledger_missing": tracked and ledger is None,
        }

    focus_view = None
    if lanes:
        groups = []
        for horizon, label in HORIZON_LABELS.items():
            views = [lane_view(lane) for lane in lanes if lane["horizon"] == horizon]
            if views:
                groups.append({"horizon": horizon, "label": label, "lanes": views})
        focus_view = {
            "note": focus.get("note") or "",
            "groups": groups,
            "evidence": [evidence_view(ref, repositories, ledger_url) for ref in focus.get("evidence") or []],
            "stale": drift_reasons(focus, contract=contract, root=root, ledger=ledger, today=today,
                                   review_days=review_days),
        }

    tooling = None
    if contract.get("tooling"):
        tooling = tooling_view(contract["tooling"], skills or [], hooks or [],
                               {lane["id"]: lane_tag(lane) for lane in lanes})

    status_vocabulary = contract["vocabulary"]["status"]
    return {
        "hero": contract["hero"],
        "focus": focus_view,
        "legend": [{"status": s, "label": STATUS_LABELS[s], "description": status_vocabulary[s]}
                   for s in STATUS_ORDER if s in status_vocabulary and s != "retired"],
        "cards": cards,
        "flow": flow,
        "gates": gates,
        "now": now,
        "working": working,
        "stale_after_days": review_days,
        "verified_on": contract["verified_on"].isoformat(),
        "build_date": today.isoformat(),
        "last_published": (facts or {}).get("last_published", ""),
        "ledger_url": ledger_url,
        "corpus_enabled": bool(contract.get("corpus")),
        "corpus": corpus_block,
        "tooling": tooling,
        "fallbacks": {domain_id: domain["fallback"] for domain_id, domain in registry.items()},
        "sources": sources_view(registry, assets=assets, today=today,
                                link=lambda ref: evidence_view(ref, repositories, ledger_url)),
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
    registry, problems = load_registry(assets)
    errors += [Finding("error", REGISTRY_NAME, problem) for problem in problems]
    if errors or registry is None:
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
    corpus, problems = load_corpus(contract, assets, str(registry["corpus"]["snapshot"]))
    if problems:
        logger.warning("System workspace corpus block shows no data: %s", "; ".join(problems[:3]))
    return build_context(contract, root=root, ledger=ledger, facts=facts, today=today,
                         registry=registry, assets=assets, corpus=corpus,
                         skeletons=skeleton_facts(root), skills=skill_facts(root), hooks=hook_facts(root))


# --- CLI ----------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check the System Workspace status contract.")
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check", help="validate rules, evidence refs, drift and the corpus snapshot")
    check.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    check.add_argument("--root", type=Path, default=None,
                       help="tree that file: evidence resolves against (default: this checkout)")
    check.add_argument("--today", type=_iso_date, default=None,
                       help="ISO date used for staleness (default: today, UTC)")
    check.add_argument("--online", action="store_true",
                       help="also confirm pr: refs are merged and url: refs answer 200")
    export = commands.add_parser("corpus-export",
                                 help="write the aggregate translation-memory snapshot (read-only Feishu read)")
    export.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    export.add_argument("--output", type=Path, default=None,
                        help="default: the corpus snapshot named in source_registry.yaml, next to the contract")
    export.add_argument("--base-token", default=os.environ.get("FEISHU_TRANSLATION_MEMORY_BASE_TOKEN", ""),
                        help="TM base token (default: $FEISHU_TRANSLATION_MEMORY_BASE_TOKEN)")
    export.add_argument("--cli-bin", default="lark-cli", help='lark-cli command, e.g. "lark-cli --profile prod"')
    export.add_argument("--as", dest="identity", default="", help="lark-cli identity (user or bot); default: the CLI default")
    export.add_argument("--today", type=_iso_date, default=None, help="export date to record (default: today, UTC)")
    args = parser.parse_args(argv)
    if args.command == "corpus-export":
        return _run_corpus_export(args)

    root = (args.root or repo_root()).resolve()
    try:
        contract = load_contract(args.contract)
        findings = check_contract(contract, root=root, today=args.today or _utc_today(),
                                  assets=args.contract.resolve().parent)
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


def _run_corpus_export(args) -> int:
    try:
        contract = load_contract(args.contract)
    except ContractError as exc:
        print(f"ERROR   {exc}")
        return 1
    if not contract.get("corpus"):
        print("ERROR   the contract has no corpus section")
        return 1
    if not args.base_token:
        print("ERROR   need --base-token or $FEISHU_TRANSLATION_MEMORY_BASE_TOKEN")
        return 1
    assets = args.contract.resolve().parent
    registry, problems = load_registry(assets)
    if registry is None:
        print("ERROR   " + "; ".join(problems))
        return 1
    output = args.output or assets / str(registry["corpus"]["snapshot"])
    previous, problem = _previous_snapshot(output)
    if problem:
        print(f"ERROR   {problem}")
        return 1
    try:
        snapshot = corpus_export(contract, base_token=args.base_token, run=lark_runner(args.cli_bin, args.identity),
                                 today=args.today or _utc_today(), previous=previous)
    except RuntimeError as exc:
        print(f"ERROR   {exc}")
        return 1
    problems = corpus_problems(snapshot, [str(lang["code"]) for lang in contract["corpus"]["languages"]])
    if problems:
        print("ERROR   " + "; ".join(problems))
        return 1
    output.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    pairs, terms = snapshot["sentence_pairs"], snapshot["terms"]
    print(f"wrote {output}: {pairs['total']} sentence pairs, {terms['total']} terms, exported "
          f"{snapshot['exported_at']}; history carries {len(snapshot.get('history') or [])} earlier month(s)")
    return 0


def _previous_snapshot(path: Path) -> tuple[dict[str, Any] | None, str]:
    """The snapshot an export replaces (its history is carried forward), or the reason it cannot be."""
    if not path.exists():
        return None, ""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return None, f"cannot read the snapshot being replaced ({path.name}): {exc}"
    # Judge it by its own language set: a language added to the contract since
    # then must not block carrying the earlier months forward.
    pairs = data.get("sentence_pairs") if isinstance(data, dict) else None
    languages = list((pairs.get("by_language") or {})) if isinstance(pairs, dict) else []
    problems = corpus_problems(data, languages)
    if problems:
        return None, (f"the snapshot being replaced ({path.name}) is unsound, so its history cannot be "
                      "carried: " + "; ".join(problems))
    return data, ""


if __name__ == "__main__":
    sys.exit(main())
