"""Ledger verification, candidate proposals and the coverage matrix against an observation artifact
(machine-readable Phase 3a, P3-1 and P3-2).

All read one ``manual-observations.json`` and a valid findings ledger. None touches an authority source,
and only ``verify --write`` changes the ledger, in its machine-owned ``verification`` fields (D17).

``verify_ledger`` judges every compared claim (plan §6.2): each claimed edition against each reference item
of the same product, through the ``language_parity`` relation (cluster) that holds the reference item. An
``absent`` pair is ``closed`` once the edition is a member of that cluster; a ``severity`` or ``numbers`` pair
once the edition's member has the reference's severity, or every number the reference states. A reference
item the artifact no longer has (its label or text changed), or an edition that took no part in the
comparison, is ``not_comparable`` and marks the finding ``needs_recheck``; nothing is dropped. A finding is
``still_open`` while any pair is, else ``not_comparable`` while any pair is, else ``closed``. Superseded
findings and findings with manual claims only are not verified.

``propose_findings`` registers nothing. It lists ``candidate`` findings for the absences, severity and
number differences of ``language_parity`` relations at or above a confidence, where the ledger does not
cover them yet: a relation that a finding cites was reviewed, and an edition is covered once a claim of the
same kind, or a manual claim, lists it with a reference among the relation's members. A severity that a
reviewed label explains (an icon, a pending style ruling) is not a difference. Each proposal follows the
ledger contract; a person names it, sets its priority and registers it through a Hello-Docs content PR.

``coverage_matrix`` lays every language-parity cluster of a model against every edition of that model (plan
§6.3). A member is ``present``. An edition the cluster lists as absent is ``absent`` once a person confirmed a
finding that claims it, ``not_applicable`` after that verdict, ``present`` when a person rejected the claim,
and ``needs_review`` until then. An edition the comparison left out is ``unknown``. Every edition is a
column, also for models without a second single-language edition, which have no rows. An absence is a
candidate, never an error.

Outputs depend only on the ledger and the artifact, so two runs give identical bytes.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import copy
from datetime import date
import hashlib
import json
from pathlib import Path
import re

from tools.manual_knowledge.findings import CLAIM_KINDS, RESULTS, check_finding
from tools.manual_knowledge.manifest import load_known_callout_labels
from tools.manual_knowledge.observe import SCHEMA as OBSERVATIONS_SCHEMA
from tools.manual_knowledge.relations import PIVOT_LANGUAGE, numbers
from tools.utils.path_utils import PathSegments, repo_root

VERIFICATION = "findings-verification.json"
PROPOSALS = "findings-proposals.json"
COVERAGE = "knowledge-coverage.json"
VERIFICATION_SCHEMA = "auto-manual-knowledge-findings-verification/v1"
PROPOSALS_SCHEMA = "auto-manual-knowledge-findings-proposals/v1"
COVERAGE_SCHEMA = "auto-manual-knowledge-coverage/v1"
STATES = ("present", "absent", "not_applicable", "needs_review", "unknown")
# A person's conclusion on an absence, strongest first; a superseded finding is history.
_CONCLUSIONS = (("not_applicable", {"not_applicable"}),
                ("absent", {"confirmed", "change_approved", "applied", "closed"}), ("present", {"rejected"}))
COMPARED = tuple(kind for kind in CLAIM_KINDS if kind != "manual")
# An icon carries no severity and a pending style ruling has none yet: neither is a content difference.
EXPLAINED_LABELS = ("icon_only", "pending_style_guide")
OUTCOMES = ("reviewed", "no_claim", "covered", "proposed")
_RANK = {"low": 0, "medium": 1, "high": 2}
_KIND_TEXT = {"absent": "缺少参照条目", "severity": "警示等级与参照不同", "numbers": "缺少参照条目中的数字"}
_EXCERPT = 60


def _observed(observations: dict, region: str) -> dict:
    """What the artifact describes; refuses one of another schema or region, or without a publication date."""
    if not isinstance(observations, dict) or observations.get("schema") != OBSERVATIONS_SCHEMA \
            or observations.get("region") != region:
        raise ValueError(f"needs an {OBSERVATIONS_SCHEMA} artifact of region {region}")
    try:
        published = date.fromisoformat(str(observations.get("published_at"))[:10])
    except ValueError as error:
        raise ValueError("the artifact has no publication date") from error
    return {"generator": observations["generator_version"], "observed_at": published.isoformat(),
            "published_at": observations["published_at"], "source_sha256": observations["source_sha256"],
            "corpus_sha256": observations["corpus_sha256"]}


def _index(observations: dict) -> tuple[dict[str, dict], dict[str, dict]]:
    """Items by knowledge_id, and the language-parity relation that holds each item."""
    items = {item["knowledge_id"]: item for item in observations["items"]}
    clusters = {member["knowledge_id"]: relation for relation in observations["relations"]
                if relation["kind"] == "language_parity" for member in relation["members"]}
    return items, clusters


def _product(variant: str) -> str:
    return variant.rsplit("/", 1)[0]


def _judge(kind: str, variant: str, reference: str, items: dict[str, dict], clusters: dict[str, dict]) -> dict:
    """One claimed edition against one reference item."""
    relation = clusters.get(reference)
    pair = {"kind": kind, "variant": variant, "reference": reference,
            "observation_id": relation["observation_id"] if relation else None}
    if reference not in items:
        return {**pair, "result": "not_comparable", "reason": "reference_missing"}
    if relation is None:
        return {**pair, "result": "not_comparable", "reason": "reference_uncompared"}
    member = next((member for member in relation["members"] if member["variant_key"] == variant), None)
    if member is None and all(entry["variant_key"] != variant for entry in relation["absent_in"]):
        return {**pair, "result": "not_comparable", "reason": "edition_uncompared"}
    if kind == "absent":
        return {**pair, "result": "still_open" if member is None else "closed", "reason": None}
    if member is None:
        return {**pair, "result": "not_comparable", "reason": "counterpart_missing"}
    same = (member["severity"] == items[reference]["severity"] if kind == "severity"
            else numbers(items[reference]["text"]) <= numbers(items[member["knowledge_id"]]["text"]))
    return {**pair, "result": "closed" if same else "still_open", "reason": None}


def _verify(finding: dict, items: dict[str, dict], clusters: dict[str, dict], header: dict) -> dict | None:
    pairs = [_judge(claim["kind"], variant, reference["knowledge_id"], items, clusters)
             for claim in finding["claims"] if claim["kind"] in COMPARED
             for variant in claim["variants"] for reference in claim["references"]
             if _product(reference["knowledge_id"].split(":")[1]) == _product(variant)]
    if not pairs:
        return None
    results = {pair["result"] for pair in pairs}
    result = next((result for result in ("still_open", "not_comparable") if result in results), "closed")
    return {"finding_id": finding["finding_id"], "status": finding["status"],
            "verification": {"result": result, "observed_at": header["observed_at"], "generator": header["generator"],
                             "needs_recheck": "not_comparable" in results},
            "pairs": pairs}


def verify_ledger(ledger: dict, observations: dict) -> dict:
    """Plan §6.2 verification of a valid ledger against one observation artifact."""
    header = _observed(observations, ledger["region"])
    items, clusters = _index(observations)
    verified: list[dict] = []
    skipped: list[dict] = []
    for finding in ledger["findings"]:
        entry = None if finding["status"] == "superseded" else _verify(finding, items, clusters, header)
        if entry is not None:
            verified.append(entry)
        else:
            skipped.append({"finding_id": finding["finding_id"],
                            "reason": "superseded" if finding["status"] == "superseded" else "manual_claims_only"})
    findings = Counter(entry["verification"]["result"] for entry in verified)
    pairs = Counter(pair["result"] for entry in verified for pair in entry["pairs"])
    return {"schema": VERIFICATION_SCHEMA, "region": ledger["region"], "observations": header,
            "totals": {"verified": len(verified), "not_verified": len(skipped),
                       "findings": {result: findings[result] for result in RESULTS},
                       "pairs": {result: pairs[result] for result in RESULTS},
                       "needs_recheck": [entry["finding_id"] for entry in verified
                                         if entry["verification"]["needs_recheck"]],
                       "reopened": [entry["finding_id"] for entry in verified if entry["status"] == "closed"
                                    and entry["verification"]["result"] == "still_open"]},
            "findings": verified, "not_verified": skipped}


def apply_verification(ledger: dict, report: dict) -> tuple[dict, list[str]]:
    """A copy of the ledger with each verified finding's verification replaced, and the findings it changed.

    A closed finding keeps the verification it was closed on; if its difference came back, the report lists
    it under ``reopened``.
    """
    results = {entry["finding_id"]: entry["verification"] for entry in report["findings"]}
    updated = copy.deepcopy(ledger)
    changed = []
    for finding in updated["findings"]:
        verification = results.get(finding["finding_id"])
        if verification is not None and finding["status"] != "closed" and finding["verification"] != verification:
            finding["verification"] = dict(verification)
            changed.append(finding["finding_id"])
    return updated, changed


def _coverage(ledger: dict) -> tuple[set[str], set[tuple[str, str, str]]]:
    """Observations the ledger cites, and the (kind, edition, reference item) its claims cover."""
    findings = ledger["findings"]
    cited = {observation for finding in findings for observation in finding["evidence"]["observation_ids"]}
    covered = {(kind, variant, reference["knowledge_id"]) for finding in findings for claim in finding["claims"]
               for kind in (COMPARED if claim["kind"] == "manual" else (claim["kind"],))
               for variant in claim["variants"] for reference in claim["references"]}
    return cited, covered


def _excerpt(text: str) -> str:
    text = " ".join(text.split())
    return text if len(text) <= _EXCERPT else f"{text[:_EXCERPT - 1]}…"


def _label(member: dict, items: dict[str, dict]) -> tuple[str, str]:
    return member["variant_key"], items[member["knowledge_id"]]["label"]


def _differences(relation: dict, items: dict[str, dict], explained: set[tuple[str, str]],
                 minimum: int) -> dict[str, tuple[list[str], str]]:
    """Claim kind → editions that differ from the relation's first member, and the claim's confidence.

    An absent edition carries its own confidence; differences between members take the relation's.
    """
    reference, others = relation["members"][0], relation["members"][1:]
    absent = [entry for entry in relation["absent_in"] if _RANK[entry["confidence"]] >= minimum]
    found = {"absent": ([entry["variant_key"] for entry in absent],
                        max((entry["confidence"] for entry in absent), key=_RANK.__getitem__, default="low"))}
    if _RANK[relation["confidence"]] >= minimum:
        if _label(reference, items) not in explained:
            found["severity"] = ([member["variant_key"] for member in others if member["severity"] !=
                                  reference["severity"] and _label(member, items) not in explained],
                                 relation["confidence"])
        wanted = numbers(items[reference["knowledge_id"]]["text"])
        found["numbers"] = ([member["variant_key"] for member in others
                             if not wanted <= numbers(items[member["knowledge_id"]]["text"])], relation["confidence"])
    return {kind: claim for kind, claim in found.items() if claim[0]}


def _summary(model: str, claims: dict[str, list[str]], reference: dict, count: int) -> str:
    """Generated description; the person who registers the finding rewrites it."""
    parts = "；".join(f"{'、'.join(variant.rsplit('/', 1)[1] for variant in variants)} 版{_KIND_TEXT[kind]}"
                     for kind, variants in claims.items())
    where = f"{reference['variant_key'].rsplit('/', 1)[1]} 版「{reference['source']['section_title']}」"
    return f"{model}：{parts}。参照 {where}{f'的 {count} 条，首条' if count > 1 else ''}：{_excerpt(reference['text'])}"


def _proposal(group: list[tuple[dict, dict]], items: dict[str, dict], release: dict[str, str | None],
              header: dict) -> dict:
    """One candidate for relations of one product with the same claims on items of one section."""
    first, claims = group[0]
    model, kinds = first["scope"]["model"], [kind for kind in COMPARED if kind in claims]
    ids = [relation["observation_id"] for relation, _ in group]
    references = [{"knowledge_id": relation["members"][0]["knowledge_id"],
                   "source_ref": relation["members"][0]["source_ref"]} for relation, _ in group]
    variants = sorted({variant for kind in kinds for variant in claims[kind][0]})
    tier = max((confidence for _, found in group for _, confidence in found.values()), key=_RANK.__getitem__)
    digest = hashlib.sha256("\x1f".join(ids).encode("utf-8")).hexdigest()[:8]
    return {"finding_id": f"fd-{re.sub(r'[^a-z0-9]', '', model.lower())}-{'-'.join(kinds)}-{digest}",
            "status": "candidate", "category": first["category"],
            "summary": _summary(model, {kind: claims[kind][0] for kind in kinds},
                                items[references[0]["knowledge_id"]], len(references)),
            "registered": {"date": header["observed_at"],
                           "source": f"{header['generator']} 观察产物（{header['observed_at']}）的机器候选"},
            "claims": [{"kind": kind, "variants": claims[kind][0], "references": references} for kind in kinds],
            "evidence": {"tier": tier, "observation_ids": ids, "generator": header["generator"],
                         "pilot_check": None},
            "authority": {variant: release.get(variant) for variant in variants},
            "decisions": [], "changes": [], "verification": None}


def _open_claims(relation: dict, items: dict[str, dict], explained: set[tuple[str, str]], minimum: int,
                 covered: set[tuple[str, str, str]]) -> tuple[str, dict[str, tuple[list[str], str]]]:
    """What the ledger makes of an unreviewed relation, and the claims it does not cover yet."""
    differences = _differences(relation, items, explained, minimum)
    members = [member["knowledge_id"] for member in relation["members"]]
    claims = {kind: (sorted(variant for variant in variants
                            if not any((kind, variant, member) in covered for member in members)), confidence)
              for kind, (variants, confidence) in differences.items()}
    claims = {kind: claim for kind, claim in claims.items() if claim[0]}
    return "no_claim" if not differences else "covered" if not claims else "proposed", claims


def propose_findings(ledger: dict, observations: dict, explained: set[tuple[str, str]],
                     min_confidence: str = "medium") -> dict:
    """Candidate findings for language-parity differences the ledger does not cover; registers nothing."""
    header = _observed(observations, ledger["region"])
    items, _ = _index(observations)
    minimum = _RANK[min_confidence]
    cited, covered = _coverage(ledger)
    outcomes: Counter[str] = Counter()
    groups: dict[tuple, list[tuple[dict, dict]]] = {}
    for relation in observations["relations"]:
        if relation["kind"] != "language_parity" or _RANK[relation["confidence"]] < minimum \
                or not set(relation["differences"]) & set(COMPARED):
            continue
        outcome, claims = (("reviewed", {}) if relation["observation_id"] in cited
                           else _open_claims(relation, items, explained, minimum, covered))
        outcomes[outcome] += 1
        if claims:
            key = (relation["scope"]["model"], relation["category"], relation["members"][0]["source_ref"],
                   tuple((kind, tuple(claims[kind][0])) for kind in COMPARED if kind in claims))
            groups.setdefault(key, []).append((relation, claims))
    release = {item["variant_key"]: item["observed_context"]["release_path"] for item in observations["items"]}
    proposals = [_proposal(group, items, release, header) for group in groups.values()]
    claimed = {variant for proposal in proposals for variant in proposal["authority"]}
    return {"schema": PROPOSALS_SCHEMA, "region": ledger["region"], "observations": header,
            "min_confidence": min_confidence,
            "totals": {"relations": {outcome: outcomes[outcome] for outcome in OUTCOMES},
                       "proposals": len(proposals), "claimed_editions": len(claimed)},
            "problems": [problem for proposal in proposals for problem in check_finding(proposal, ledger["region"])],
            "findings": proposals}


def _column_order(variant: str) -> tuple[bool, bool, str]:
    """The pivot language first, combined multi-language editions last."""
    language = variant.rsplit("/", 1)[1]
    return language == "multi", language != PIVOT_LANGUAGE, language


def _links(ledger: dict) -> dict[tuple[str, str], list[tuple[dict, str]]]:
    """Findings with the kind of their claim, by (claimed edition, referenced item)."""
    links: dict[tuple[str, str], list[tuple[dict, str]]] = defaultdict(list)
    for finding in ledger["findings"]:
        if finding["status"] == "superseded":
            continue
        for claim in finding["claims"]:
            for variant in claim["variants"]:
                for reference in claim["references"]:
                    if reference["knowledge_id"]:
                        links[variant, reference["knowledge_id"]].append((finding, claim["kind"]))
    return links


def _coverage_row(relation: dict, editions: list[str], links: dict, specific: set[str], items: dict[str, dict]) -> dict:
    """One cluster against every edition of its model, with the findings that name each edition."""
    members = {member["variant_key"]: member["knowledge_id"] for member in relation["members"]}
    absent = {entry["variant_key"]: entry["confidence"] for entry in relation["absent_in"]}
    cells: dict[str, str] = {}
    findings: dict[str, list[str]] = {}
    for variant in editions:
        linked = [pair for knowledge_id in members.values() for pair in links.get((variant, knowledge_id), ())]
        if linked:
            findings[variant] = sorted({finding["finding_id"] for finding, _ in linked})
        statuses = {finding["status"] for finding, kind in linked if kind in ("absent", "manual")}
        cells[variant] = ("present" if variant in members else "unknown" if variant not in absent
                          else next((state for state, accepted in _CONCLUSIONS if statuses & accepted), "needs_review"))
    pivot = relation["members"][0]
    item = items[pivot["knowledge_id"]]
    return {"observation_id": relation["observation_id"], "category": relation["category"],
            "product_specific": pivot["knowledge_id"] in specific,
            "reference": {"knowledge_id": pivot["knowledge_id"], "source_ref": pivot["source_ref"],
                          "section_title": item["source"]["section_title"], "excerpt": _excerpt(item["text"])},
            "cells": cells, "confidence": {variant: absent[variant] for variant in editions if variant in absent},
            "findings": findings}


def _coverage_model(model: str, columns: list[str], relations: list[dict], links: dict, specific: set[str],
                    items: dict[str, dict]) -> dict:
    columns = sorted(columns, key=_column_order)
    rows = [_coverage_row(relation, columns, links, specific, items) for relation in relations]
    counts = {variant: Counter(row["cells"][variant] for row in rows) for variant in columns}
    return {"model": model, "editions": columns, "compared": bool(rows),
            "by_edition": {variant: {state: count[state] for state in STATES if count[state]}
                           for variant, count in counts.items()},
            "rows": rows}


def coverage_matrix(ledger: dict, observations: dict) -> dict:
    """Plan §6.3: every language-parity cluster of a model against every edition of that model."""
    header = _observed(observations, ledger["region"])
    items, _ = _index(observations)
    links = _links(ledger)
    # A warning whose text no other model of that language uses is marked on the cluster it belongs to.
    specific = {member["knowledge_id"] for relation in observations["relations"]
                if relation["kind"] == "product_specific" for member in relation["members"]}
    clusters: dict[str, list[dict]] = defaultdict(list)
    for relation in observations["relations"]:
        if relation["kind"] == "language_parity":
            clusters[relation["scope"]["model"]].append(relation)
    # The artifact's edition list also names editions without any item.
    editions: dict[str, list[str]] = defaultdict(list)
    for variant in observations["summary"]["items_by_variant"]:
        editions[variant.rsplit("/", 2)[0]].append(variant)
    models = [_coverage_model(model, columns, clusters[model], links, specific, items)
              for model, columns in sorted(editions.items())]
    cells = Counter(state for model in models for row in model["rows"] for state in row["cells"].values())
    return {"schema": COVERAGE_SCHEMA, "region": ledger["region"], "observations": header, "states": list(STATES),
            "totals": {"models": len(models), "compared_models": sum(model["compared"] for model in models),
                       "editions": sum(len(model["editions"]) for model in models),
                       "rows": sum(len(model["rows"]) for model in models),
                       "cells": {state: cells[state] for state in STATES}},
            "models": models}


def serialize(value: dict) -> bytes:
    """The ledger's own layout, so a written ledger differs only where it changed."""
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.tmp")
    temporary.write_bytes(data)
    temporary.replace(path)


def run(args: argparse.Namespace, ledger: dict) -> int:
    """The ``verify``, ``propose`` and ``coverage`` commands of ``python -m tools.manual_knowledge.findings``."""
    try:
        observations = json.loads(args.observations.read_text(encoding="utf-8"))
        if args.command == "verify":
            report = verify_ledger(ledger, observations)
        elif args.command == "coverage":
            report = coverage_matrix(ledger, observations)
        else:
            explained = load_known_callout_labels(repo_root() / PathSegments.DATA, EXPLAINED_LABELS)
            report = propose_findings(ledger, observations, explained, args.min_confidence)
    except (OSError, ValueError) as error:
        print(json.dumps({"status": "refused", "problems": [str(error)]}, ensure_ascii=False, indent=2))
        return 1
    output = args.output or args.observations.parent / {"verify": VERIFICATION, "propose": PROPOSALS,
                                                         "coverage": COVERAGE}[args.command]
    _write(output, serialize(report))
    result: dict = {"status": "written", "path": str(output), "totals": report["totals"]}
    if args.command == "verify" and args.write:
        updated, changed = apply_verification(ledger, report)
        if changed:
            _write(args.ledger, serialize(updated))
        result["ledger"] = {"path": str(args.ledger), "updated": changed}
    problems = report.get("problems", [])
    if problems:
        result["problems"] = problems
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if problems else 0
