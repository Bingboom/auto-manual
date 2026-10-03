"""Reviewed English inheritance at the existing fresh Web admission boundary."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re

from tools.prepared_component_policy import POLICY_FILENAME, POLICY_SCHEMA
from tools.manual_ir.hashing import file_sha256
from tools.utils.path_utils import get_paths
from tools.web_language_structure import (
    component_references, digest, structure_differences, summarize_language_structure,
)


SCHEMA = "web-language-baseline/v1"


def _sha(value, label):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError(f"language baseline requires SHA-256: {label}")
    return value


def _text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"language baseline requires {label}")
    return value


def _asset_paths(value, path=""):
    if isinstance(value, dict):
        if "sha256" in value:
            yield path, value["sha256"]
        for key, child in value.items():
            yield from _asset_paths(child, path + "/" + key)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _asset_paths(child, path + "/" + str(index))


def candidate_language_baseline(raw: dict, package_root: Path, *, revision: str,
                                page_map: dict, source_sha256: str, component_map: dict | None = None) -> dict:
    """Produce review material only. There is intentionally no approve switch."""
    if raw["language"] != "en":
        raise ValueError("language baseline candidate must use English")
    component_map = component_map if component_map is not None else {r: r for r in component_references(raw)}
    snapshot = summarize_language_structure(raw, package_root, page_map, component_map)
    return {
        "schema_version": SCHEMA, "status": "candidate", "revision": _text(revision, "revision"),
        "model": raw["model"], "region": raw["region"], "baseline_language": "en",
        "source_sha256": _sha(source_sha256, "original source"),
        "ir_content_sha256": _sha(raw["content_sha256"], "English IR"),
        "structure": snapshot, "structure_sha256": digest(snapshot), "approval": None,
        "asset_decisions": {path: {"sha256": sha, "source_ref": "", "content_mode": "",
                                   "text_owner": "", "frame_policy": "", "leader_policy": "",
                                   "applicability": ""} for path, sha in _asset_paths(snapshot)},
        "locales": {"en": {"page_map": page_map, "component_map": component_map, "snapshot_sha256": raw["snapshot_sha256"],
                            "source_sha256": source_sha256, "source_pages": [], "differences": []}},
    }


def review_digest(entry):
    """Bind operator approval to source, artwork decisions and English mappings."""
    return digest({k: entry.get(k) for k in (
        "model", "region", "baseline_language", "revision", "source_sha256",
        "ir_content_sha256", "structure_sha256", "asset_decisions",
    )} | {"english_mapping": entry.get("locales", {}).get("en")})


def _visual_evidence(approval, evidence_root):
    for viewport in ("desktop", "mobile"):
        evidence = approval.get(viewport) or {}
        _text(evidence.get("path"), f"approval.{viewport}.path")
        _sha(evidence.get("sha256"), f"approval.{viewport}.sha256")
        path = evidence_root / evidence["path"]
        if (Path(evidence["path"]).is_absolute() or path.is_symlink()
                or not path.resolve().is_relative_to(evidence_root.resolve())
                or not path.is_file() or file_sha256(path) != evidence["sha256"]):
            raise ValueError(f"operator confirmation {viewport} evidence is missing or changed")


def _approval(entry, evidence_root):
    if entry.get("schema_version") != SCHEMA or entry.get("baseline_language") != "en":
        raise ValueError("invalid English language baseline schema/identity")
    if entry.get("status") != "approved":
        raise ValueError("English language baseline is not operator-approved")
    _text(entry.get("revision"), "revision")
    _sha(entry.get("source_sha256"), "original source")
    _sha(entry.get("ir_content_sha256"), "English IR")
    approval = entry.get("approval") or {}
    for field in ("operator", "record"):
        _text(approval.get(field), f"approval.{field}")
    for field in ("ir_content_sha256", "structure_sha256", "review_sha256"):
        if approval.get(field) != entry.get(field):
            raise ValueError("operator confirmation is detached from the English baseline")
    _visual_evidence(approval, evidence_root)
    if entry.get("review_sha256") != review_digest(entry):
        raise ValueError("English review decisions changed after confirmation")
    structure = entry["structure"]
    if digest(structure) != _sha(entry.get("structure_sha256"), "structure"):
        raise ValueError("English baseline structure digest mismatch")
    if (structure["model"], structure["region"]) != (entry["model"], entry["region"]):
        raise ValueError("English baseline structure identity mismatch")
    assets = dict(_asset_paths(structure))
    decisions = entry.get("asset_decisions", {})
    if set(assets) != set(decisions):
        raise ValueError("English baseline requires exact per-asset decisions")
    for path, sha in assets.items():
        decision = decisions[path]
        if decision.get("sha256") != sha:
            raise ValueError(f"baseline asset decision digest mismatch: {path}")
        for field in ("source_ref", "content_mode", "text_owner", "frame_policy", "leader_policy", "applicability"):
            _text(decision.get(field), f"asset decision {path}/{field}")


def _reviewed_differences(deltas, rules, source_sha, source_pages):
    approved = {}
    for row in rules:
        path = _text(row.get("path"), "difference path")
        if not path.startswith("/pages/") or "*" in path or path in approved:
            raise ValueError("language differences require unique exact page/slot paths")
        for field in ("reason", "approval_record", "source_ref"):
            _text(row.get(field), f"difference {path}/{field}")
        for field in ("expected_sha256", "actual_sha256", "source_sha256"):
            _sha(row.get(field), f"difference {path}/{field}")
        if row["source_sha256"] != source_sha:
            raise ValueError("reviewed language difference is detached from its source")
        pages = row.get("source_pages")
        if not isinstance(pages, list) or not pages or any(
                type(p) is not int or p not in source_pages for p in pages):
            raise ValueError("reviewed language difference requires exact original pages")
        approved[path] = row
    issues, used = [], set()
    for delta in deltas:
        path = delta["path"]
        rule = approved.get(path)
        if rule and all(rule[k] == delta[k] for k in ("expected_sha256", "actual_sha256")):
            used.add(path)
        else:
            issues.append(f"{path}: differs from confirmed English baseline")
    issues.extend(f"{path}: stale reviewed language difference" for path in approved.keys() - used)
    return issues


def audit_language_baseline(raw: dict, package_root: Path, entry: dict,
                            *, evidence_root: Path | None = None) -> dict:
    """Validate a trusted record, then compare actual IR and packaged bytes."""
    target = f"{raw['model']}/{raw['region']}/{raw['language']}"
    report = {"target": target, "status": "blocked", "differences": [], "issues": []}
    try:
        if not isinstance(entry, dict):
            raise ValueError("invalid language baseline record")
        _approval(entry, evidence_root or get_paths().root)
        report.update(revision=entry["revision"], structure_sha256=entry["structure_sha256"])
        if (entry["model"], entry["region"]) != (raw["model"], raw["region"]):
            raise ValueError("English baseline target identity mismatch")
        marker = raw.get("metadata", {}).get("language_baseline")
        if marker != {"revision": entry["revision"], "sha256": entry["structure_sha256"]}:
            raise ValueError("missing or stale language baseline reference in candidate IR")
        locale = entry["locales"].get(raw["language"])
        if not isinstance(locale, dict):
            raise ValueError("language has no reviewed source/page mapping")
        if raw["snapshot_sha256"] != _sha(locale.get("snapshot_sha256"), "locale snapshot"):
            raise ValueError("language source snapshot differs from reviewed mapping")
        _sha(locale.get("source_sha256"), "locale source")
        pages = locale.get("source_pages")
        if not isinstance(pages, list) or not pages or any(type(p) is not int or p < 1 for p in pages):
            raise ValueError("language source requires explicit one-based original pages")
        if raw["language"] == "en" and raw["content_sha256"] != entry["ir_content_sha256"]:
            raise ValueError("English content changed after confirmation")
        actual = summarize_language_structure(raw, package_root, locale["page_map"], locale["component_map"])
        deltas = structure_differences(entry["structure"], actual)
        report["differences"] = deltas
        report["issues"] = _reviewed_differences(
            deltas, locale.get("differences", []), locale["source_sha256"], pages,
        )
        if not report["issues"]:
            report["status"] = "verified"
    except (ValueError, KeyError, TypeError, OSError) as exc:
        report["issues"].append(str(exc))
    return report


def require_language_baseline(raw: dict, package_root: Path, *, contract_path: Path | None = None) -> dict:
    """Enrollment comes exclusively from the existing code-reviewed contract."""
    path = contract_path or get_paths().renderer_contracts_dir / POLICY_FILENAME
    contract = json.loads(path.read_text(encoding="utf-8"))
    if contract.get("schema_version") != POLICY_SCHEMA:
        raise ValueError("invalid shared admission contract")
    entries = contract.get("language_baselines", {})
    if not isinstance(entries, dict):
        raise ValueError("invalid language-baseline enrollment")
    key = f"{raw['model']}/{raw['region']}"
    if key not in entries:
        return {"status": "not_enrolled", "target": key, "issues": []}
    report = audit_language_baseline(raw, package_root, entries[key])
    if report["issues"]:
        raise ValueError(f"language baseline admission failed for {report['target']}: " + "; ".join(report["issues"]))
    return report


def baseline_trial(raw: dict, package_root: Path, entry: dict, *, page_map: dict, component_map: dict) -> dict:
    """Read-only pre-approval comparison. Never returns an admission pass."""
    snapshot = deepcopy(entry["structure"])
    actual = summarize_language_structure(raw, package_root, page_map, component_map)
    return {"status": "candidate_trial", "publication_eligible": False,
            "target": f"{raw['model']}/{raw['region']}/{raw['language']}",
            "differences": structure_differences(snapshot, actual)}
