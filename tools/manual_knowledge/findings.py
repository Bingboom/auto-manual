"""Knowledge finding ledger: contract and check (machine-readable Phase 3a, P3-0).

The ledger is business content in Hello-Docs ``docs/knowledge/governance/findings.json``,
maintained through content PRs (D16). A finding names editions that differ from a
reference item of the observation artifact, the evidence behind the claim, the
authority each claimed edition is published from, and the human decisions taken on
it. Machines register ``candidate`` findings and write verification evidence only;
every other status is a decision by a named person in a role, with a date (D17).
``not_applicable`` and compliance verdicts belong to the certification owner (D18).
Approved wording is referenced as a TM-B record, never copied (D19); a finding the
machine can compare is ``closed`` only after verification found the difference gone (D21).

``python -m tools.manual_knowledge.findings check`` validates a ledger and reports
its totals; it never writes. Plan: ``code-as-doc/dev/machine_readable_knowledge_governance.md`` §6.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import json
from pathlib import Path
import re
import sys

from tools.utils.path_utils import PathSegments, repo_root

LEDGER = "findings.json"
SCHEMA = "auto-manual-knowledge-findings/v1"
TRANSITIONS = {
    "candidate": ("confirmed", "rejected", "not_applicable", "superseded"),
    "confirmed": ("change_approved", "superseded"),
    "change_approved": ("applied", "superseded"),
    "applied": ("closed", "superseded"),
    "closed": ("superseded",),
    "rejected": ("superseded",),
    "not_applicable": ("superseded",),
    "superseded": (),
}
CATEGORIES = ("warning", "safety", "compliance", "other")
PRIORITIES = ("high", "medium", "low")
CLAIM_KINDS = ("absent", "severity", "numbers", "manual")
TIERS = ("high", "medium", "low", "manual")
PILOT_CHECKS = ("real", "partly", "explainable", "false_positive")
ROLES = ("content_owner", "certification_owner", "operator")
# Release paths as tools/rtd/publication_catalog.py classifies each published edition.
RELEASE_PATHS = ("git_only_frozen", "unclassified", "queue", "legacy")
RESULTS = ("closed", "still_open", "not_comparable")
_REASONED = ("rejected", "not_applicable", "superseded")
_UNCHANGED = ("candidate", "confirmed", "rejected", "not_applicable")
_CHANGED = ("change_approved", "applied", "closed")
_PUBLISHED = ("applied", "closed")
_FIELDS = {
    "finding": ({"finding_id", "status", "category", "summary", "registered", "claims", "evidence", "authority",
                 "decisions", "changes", "verification"}, {"priority"}),
    "registered": ({"date", "source"}, set()),
    "claim": ({"kind", "variants", "references"}, set()),
    "reference": ({"knowledge_id", "source_ref"}, set()),
    "evidence": ({"tier", "observation_ids", "generator", "pilot_check"}, set()),
    "decision": ({"status", "by", "role", "date"}, {"note"}),
    "change": ({"variants", "wording", "pr", "published"}, set()),
    "verification": ({"result", "observed_at", "generator", "needs_recheck"}, set()),
}
_FINDING_ID = re.compile(r"fd-[a-z0-9]+(?:-[a-z0-9]+)*")
_VARIANT = re.compile(r"[A-Z0-9][A-Z0-9-]*/[A-Z]{2}/[a-z]+(?:-[a-z]+)?")
_KNOWLEDGE_ID = re.compile(r"kn:([^:\s]+):([a-z]+):[0-9a-f]{16}:\d+")
_SOURCE_REF = re.compile(r"([^/\s]+/[^/\s]+/[^/\s]+)/\S+\.html#\S*")
_OBSERVATION_ID = re.compile(r"obs:[a-z_]+:\S+:[0-9a-f]{16}")
_GENERATOR = re.compile(r"manual-observations/\d+\.\d+")
_WORDING = re.compile(r"tm:[A-Za-z0-9_-]+")
_PULL_REQUEST = re.compile(r"https://github\.com/[\w.-]+/[\w.-]+/pull/\d+")
_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


def default_ledger(base_root: Path) -> Path:
    return base_root / PathSegments.DOCS / PathSegments.KNOWLEDGE / PathSegments.GOVERNANCE / LEDGER


def _date(value: object) -> date | None:
    """A calendar date written as YYYY-MM-DD, else ``None``."""
    if not isinstance(value, str) or not _DATE.fullmatch(value):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _fields(record: object, kind: str, at: str, problems: list[str]) -> bool:
    """The record is an object with every required field of its kind and nothing unknown."""
    if not isinstance(record, dict):
        problems.append(f"{at}: {kind} must be an object")
        return False
    required, optional = _FIELDS[kind]
    missing, unknown = sorted(required - record.keys()), sorted(record.keys() - required - optional)
    if missing or unknown:
        problems.append(f"{at}: {kind} misses {missing} or has unknown fields {unknown}")
    return not missing


def _registered(finding: dict, at: str, problems: list[str]) -> date | None:
    registered = finding["registered"]
    if not _fields(registered, "registered", f"{at} registered", problems):
        return None
    when = _date(registered["date"])
    if when is None or not _text(registered["source"]):
        problems.append(f"{at}: registered needs a YYYY-MM-DD date and the source it came from")
    return when


def _variants(values: object, region: str, at: str, problems: list[str]) -> set[str]:
    if not isinstance(values, list) or not values:
        problems.append(f"{at}: variants must be a non-empty list")
        return set()
    valid = [value for value in values
             if isinstance(value, str) and _VARIANT.fullmatch(value) and value.split("/")[1] == region]
    if len(valid) != len(values) or len(set(valid)) != len(valid):
        problems.append(f"{at}: variants must be distinct {region} variant keys")
    return set(valid)


def _reference(reference: dict, claim: dict, variants: set[str], category: str, region: str, at: str,
               problems: list[str]) -> str | None:
    """Product (model/region) a compared claim is anchored in; manual claims may cite a page only."""
    source = reference["source_ref"]
    page = _SOURCE_REF.fullmatch(source) if isinstance(source, str) else None
    if page is None or not _VARIANT.fullmatch(page.group(1)) or page.group(1).split("/")[1] != region:
        problems.append(f"{at}: source_ref must be an anchor on a {region} manual page")
        return None
    compared, knowledge_id = claim["kind"] != "manual", reference["knowledge_id"]
    if knowledge_id is None and not compared:
        return None
    item = _KNOWLEDGE_ID.fullmatch(knowledge_id) if isinstance(knowledge_id, str) else None
    if item is None:
        problems.append(f"{at}: a compared claim needs the reference item's knowledge_id" if knowledge_id is None
                        else f"{at}: invalid knowledge_id {knowledge_id!r}")
        return None
    if item.group(1) != page.group(1) or item.group(2) != category:
        problems.append(f"{at}: knowledge_id must name the source_ref's edition and the finding's category")
    if compared and item.group(1) in variants:
        problems.append(f"{at}: the reference edition cannot also be claimed")
    return item.group(1).rsplit("/", 1)[0]


def _claim(claim: dict, category: str, region: str, at: str, problems: list[str]) -> set[str]:
    if claim["kind"] not in CLAIM_KINDS:
        problems.append(f"{at}: kind must be one of {CLAIM_KINDS}")
    variants = _variants(claim["variants"], region, at, problems)
    references = claim["references"]
    if not isinstance(references, list) or not references:
        problems.append(f"{at}: references must be a non-empty list")
        return variants
    anchored = set()
    for index, reference in enumerate(references):
        here = f"{at} references[{index}]"
        if _fields(reference, "reference", here, problems):
            anchored.add(_reference(reference, claim, variants, category, region, here, problems))
    loose = sorted(variant for variant in variants if variant.rsplit("/", 1)[0] not in anchored)
    if claim["kind"] != "manual" and loose:
        problems.append(f"{at}: no reference item in the same product for {loose}")
    return variants


def _claims(finding: dict, region: str, at: str, problems: list[str]) -> set[str]:
    """Every claimed edition; a claim compares its editions with reference items of the same product."""
    claims = finding["claims"]
    if not isinstance(claims, list) or not claims:
        problems.append(f"{at}: claims must be a non-empty list")
        return set()
    claimed: set[str] = set()
    for index, claim in enumerate(claims):
        here = f"{at} claims[{index}]"
        if _fields(claim, "claim", here, problems):
            claimed |= _claim(claim, finding["category"], region, here, problems)
    return claimed


def _evidence(finding: dict, at: str, problems: list[str]) -> None:
    evidence = finding["evidence"]
    if not _fields(evidence, "evidence", f"{at} evidence", problems):
        return
    tier, ids, generator = evidence["tier"], evidence["observation_ids"], evidence["generator"]
    if tier not in TIERS or evidence["pilot_check"] not in (None, *PILOT_CHECKS):
        problems.append(f"{at}: evidence needs a tier in {TIERS} and a pilot_check in {PILOT_CHECKS} or null")
    if not isinstance(ids, list) or not all(isinstance(i, str) and _OBSERVATION_ID.fullmatch(i) for i in ids) \
            or len(set(ids)) != len(ids):
        problems.append(f"{at}: observation_ids must be distinct observation ids")
        ids = []
    if tier != "manual" and not ids:
        problems.append(f"{at}: a finding the machine reported cites its observations")
    if (ids or generator is not None) and not (isinstance(generator, str) and _GENERATOR.fullmatch(generator)):
        problems.append(f"{at}: cited observations need the generator version that produced them")


def _authority(finding: dict, claimed: set[str], at: str, problems: list[str]) -> None:
    authority = finding["authority"]
    if not isinstance(authority, dict) or set(authority) != claimed:
        problems.append(f"{at}: authority must list exactly the claimed editions")
        return
    unknown = sorted(variant for variant, path in authority.items() if path not in RELEASE_PATHS)
    if unknown:
        problems.append(f"{at}: release path must be one of {RELEASE_PATHS} for {unknown}")


def _decider(decision: dict, category: str, at: str, problems: list[str]) -> None:
    """A named person in a role; applicability and compliance verdicts are the certification owner's (D18)."""
    status, role, note = decision["status"], decision["role"], decision.get("note")
    if not _text(decision["by"]) or role not in ROLES:
        problems.append(f"{at}: a decision needs the person (by) and a role in {ROLES}")
    if (status in _REASONED and not _text(note)) or not isinstance(note, str | None):
        problems.append(f"{at}: {status} needs a note with the reason")
    if (status == "not_applicable" or (category == "compliance" and status in ("confirmed", "rejected"))) \
            and role != "certification_owner":
        problems.append(f"{at}: {status} on this finding is the certification owner's decision")
    if status == "change_approved" and role != "operator":
        problems.append(f"{at}: the operator approves the change scope and wording")


def _decisions(finding: dict, registered: date | None, at: str, problems: list[str]) -> None:
    """Decisions replay the status history from ``candidate``; dates never go backwards."""
    decisions = finding["decisions"]
    if not isinstance(decisions, list):
        problems.append(f"{at}: decisions must be a list")
        return
    state, last = "candidate", registered
    for index, decision in enumerate(decisions):
        here = f"{at} decisions[{index}]"
        if not _fields(decision, "decision", here, problems):
            return
        if decision["status"] not in TRANSITIONS.get(state, ()):
            problems.append(f"{here}: {state} cannot move to {decision['status']!r}")
        when = _date(decision["date"])
        if when is None or (last is not None and when < last):
            problems.append(f"{here}: date must be YYYY-MM-DD, not before the registration or the previous decision")
        _decider(decision, finding["category"], here, problems)
        state, last = decision["status"] if isinstance(decision["status"], str) else "invalid", when or last
    if state != finding["status"]:
        problems.append(f"{at}: status {finding['status']!r} does not follow from its decisions ({state!r})")


def _change(change: dict, claimed: set[str], at: str, problems: list[str]) -> set[str]:
    """Editions this change published through a pull request."""
    variants = change["variants"]
    if not isinstance(variants, list) or not variants \
            or not all(isinstance(variant, str) and variant in claimed for variant in variants):
        problems.append(f"{at}: variants must be claimed editions")
        variants = []
    wording = change["wording"]
    if not isinstance(wording, list) or not all(isinstance(ref, str) and _WORDING.fullmatch(ref) for ref in wording):
        problems.append(f"{at}: wording lists TM-B records (tm:<record id>), never the text itself")
    pull_request = change["pr"]
    if pull_request is not None and not (isinstance(pull_request, str) and _PULL_REQUEST.fullmatch(pull_request)):
        problems.append(f"{at}: pr must be a GitHub pull request URL")
    published = change["published"]
    if not isinstance(published, dict) or not all(
            variant in variants and isinstance(version, str) and version.startswith(f"{variant}@")
            and len(version) > len(variant) + 1 for variant, version in published.items()):
        problems.append(f"{at}: published maps changed editions to their new manual_variant_id")
        return set()
    return set(published) if pull_request is not None else set()


def _changes(finding: dict, claimed: set[str], at: str, problems: list[str]) -> None:
    changes, status = finding["changes"], finding["status"]
    if not isinstance(changes, list):
        problems.append(f"{at}: changes must be a list")
        return
    if status in _UNCHANGED and changes:
        problems.append(f"{at}: changes are recorded from change_approved on")
    if status in _CHANGED and not changes:
        problems.append(f"{at}: {status} needs the approved change")
    published: set[str] = set()
    for index, change in enumerate(changes):
        here = f"{at} changes[{index}]"
        if _fields(change, "change", here, problems):
            published |= _change(change, claimed, here, problems)
    if status in _PUBLISHED and not claimed <= published:
        problems.append(f"{at}: {status} needs a pull request and a published version for "
                        f"{sorted(claimed - published)}")


def _verification(finding: dict, at: str, problems: list[str]) -> None:
    verification = finding["verification"]
    if verification is not None and _fields(verification, "verification", f"{at} verification", problems):
        generator = verification["generator"]
        if verification["result"] not in RESULTS or _date(verification["observed_at"]) is None \
                or not isinstance(verification["needs_recheck"], bool) \
                or not (isinstance(generator, str) and _GENERATOR.fullmatch(generator)):
            problems.append(f"{at}: verification needs a result in {RESULTS}, observed_at, the generator "
                            "and needs_recheck")
    claims = finding["claims"] if isinstance(finding["claims"], list) else []
    compared = any(isinstance(claim, dict) and claim.get("kind") != "manual" for claim in claims)
    if finding["status"] == "closed" and compared and (verification or {}).get("result") != "closed":
        problems.append(f"{at}: closed needs a verification that found the difference gone")


def check_finding(finding: object, region: str) -> list[str]:
    """Every contract problem in one finding."""
    at = str(finding.get("finding_id")) if isinstance(finding, dict) else "finding"
    problems: list[str] = []
    if not isinstance(finding, dict) or not _fields(finding, "finding", at, problems):
        return problems or [f"{at}: finding must be an object"]
    if not isinstance(finding["finding_id"], str) or not _FINDING_ID.fullmatch(finding["finding_id"]):
        problems.append(f"{at}: finding_id must look like fd-<lower-case words>")
    if finding["status"] not in tuple(TRANSITIONS) or finding["category"] not in CATEGORIES \
            or not _text(finding["summary"]):
        problems.append(f"{at}: needs a status in {tuple(TRANSITIONS)}, a category in {CATEGORIES} and a summary")
    if finding.get("priority", "high") not in PRIORITIES:
        problems.append(f"{at}: priority, when set, is one of {PRIORITIES}")
    registered = _registered(finding, at, problems)
    claimed = _claims(finding, region, at, problems)
    _evidence(finding, at, problems)
    _authority(finding, claimed, at, problems)
    _decisions(finding, registered, at, problems)
    _changes(finding, claimed, at, problems)
    _verification(finding, at, problems)
    return problems


def check_ledger(ledger: object) -> list[str]:
    """Every contract problem in a ledger; an empty list means it is valid."""
    if not isinstance(ledger, dict) or ledger.get("schema") != SCHEMA:
        return [f"ledger: schema must be {SCHEMA}"]
    region, findings = ledger.get("region"), ledger.get("findings")
    if not isinstance(region, str) or not region.strip() or not isinstance(findings, list) \
            or set(ledger) != {"schema", "region", "findings"}:
        return ["ledger: needs exactly schema, region and a findings list"]
    problems: list[str] = []
    seen: set[str] = set()
    for finding in findings:
        problems.extend(check_finding(finding, region))
        key = finding.get("finding_id") if isinstance(finding, dict) else None
        if isinstance(key, str) and key in seen:
            problems.append(f"{key}: finding_id is not unique")
        seen.add(str(key))
    return problems


def summarize(ledger: dict) -> dict:
    """Totals of a valid ledger."""
    findings = ledger["findings"]
    return {"findings": len(findings),
            "by_status": dict(sorted(Counter(finding["status"] for finding in findings).items())),
            "by_tier": dict(sorted(Counter(finding["evidence"]["tier"] for finding in findings).items())),
            "by_category": dict(sorted(Counter(finding["category"] for finding in findings).items())),
            "claimed_editions": len({variant for finding in findings for variant in finding["authority"]})}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Knowledge finding ledger (machine-readable Phase 3a)")
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check", help="validate a ledger against the contract; never writes")
    check.add_argument("--ledger", type=Path, default=default_ledger(repo_root()),
                       help="ledger file (default: docs/knowledge/governance/findings.json in this checkout)")
    args = parser.parse_args(argv)
    if not args.ledger.is_file():
        print(json.dumps({"status": "missing", "path": str(args.ledger)}, ensure_ascii=False, indent=2))
        return 1
    try:
        ledger = json.loads(args.ledger.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        ledger, problems = None, [f"ledger: not JSON ({error})"]
    else:
        problems = check_ledger(ledger)
    result: dict = {"status": "invalid" if problems else "valid", "path": str(args.ledger), "problems": problems}
    if not problems:
        result["totals"] = summarize(ledger)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
