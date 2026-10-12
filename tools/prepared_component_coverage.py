"""Audit prepared-document bindings against a trusted admission policy.

The caller supplies reviewed target capabilities, chapter applicability and
bounded debt independently of the candidate. This audit does not replace IR
schema, component-slot or packaged-asset validation. Historical replay need
not satisfy a new publication policy.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from copy import deepcopy
from typing import Any


PROFILE = "prepared-shared-components/v1"


def node_digest(node: dict) -> str:
    """Pin the complete legacy node, including copy, structure and asset refs."""
    encoded = json.dumps(node, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def chapter_digest(page: dict) -> str:
    """Pin flow content, normalizing only component source-directory prefixes."""
    nodes = [deepcopy(block["payload"]) for block in page["blocks"]]

    def normalize(node):
        if node.get("kind") == "component":
            spec = node["component_spec"]
            source = spec.get("source_ref", "")
            path, separator, fragment = source.partition("#")
            spec["source_ref"] = path.replace("\\", "/").rsplit("/", 1)[-1] + separator + fragment
        for child in node.get("children", []):
            normalize(child)

    for node in nodes:
        normalize(node)
    return node_digest({"blocks": nodes})


def _active_chapters(policy):
    capabilities = policy["capabilities"]
    chapters = []
    for rule in policy["chapters"]:
        capability = rule.get("capability")
        if capability is not None:
            if type(capabilities.get(capability)) is not bool:
                raise ValueError(f"unknown capability in admission policy: {capability}")
            if not capabilities[capability]:
                continue
        chapters.append(rule)
    return chapters


def _debt_index(policy):
    records = {}
    ids = set()
    for row in policy.get("legacy_debt", []):
        key = (row["page_id"], row["location"], row["kind"], row["sha256"])
        if key in records or row["id"] in ids or not row.get("reason", "").strip():
            raise ValueError("legacy debt requires unique identities, nodes and review reasons")
        records[key] = row
        ids.add(row["id"])
    return records


def _finished_panel(node, metadata):
    attrs = node.get("presentation", {}).get("html", {}).get("attributes", {})
    if "manual-finished-illustration" not in attrs.get("class", []):
        return None
    path = attrs.get("data-web-finished-panel-path")
    digest = attrs.get("data-web-finished-panel-sha256")
    provenance = metadata.get("illustration_provenance") or {}
    matches = [r for r in provenance.get("illustrations", [])
               if r.get("path") == path and r.get("sha256") == digest]
    if (not path or not digest or len(matches) != 1
            or metadata.get("asset_sha256", {}).get(node.get("source")) != digest):
        raise ValueError("finished panel lacks matching provenance and packaged asset")
    return {"path": path, "sha256": digest}


def _scan_page(page, *, inspect_images, metadata, debt):
    counts: Counter = Counter()
    legacy, panels, issues = [], [], []
    page_id = page["page_id"]
    chapter_debt = debt.get((page_id, "", "chapter", chapter_digest(page)))
    if chapter_debt is not None:
        legacy.append(chapter_debt)

    def visit(node, location):
        kind = node.get("kind")
        if kind == "component":
            spec = node.get("component_spec", {})
            identity = spec.get("component_id")
            if not isinstance(identity, str) or not identity:
                issues.append(f"{page_id}/{location}: component identity missing")
            else:
                counts[identity] += 1
                if spec.get("variant"):
                    counts[f"{identity}/{spec['variant']}"] += 1
            return
        if kind == "image":
            try:
                panel = _finished_panel(node, metadata)
                if panel is not None:
                    panels.append({"page_id": page_id, "location": location, **panel})
            except ValueError as exc:
                issues.append(f"{page_id}/{location}: {exc}")
        if kind == "table" or (inspect_images and kind == "image"):
            key = (page_id, location, kind, node_digest(node))
            if key in debt:
                legacy.append(debt[key])
                return
            if chapter_debt is None:
                issues.append(f"{page_id}/{location}: unbound {kind}")
        for index, child in enumerate(node.get("children", [])):
            visit(child, f"{location}/{index}")

    for index, block in enumerate(page.get("blocks", [])):
        visit(block["payload"], str(index))
    return counts, legacy, panels, issues


def _check_chapter(rule, page_counts, used_debt):
    issues = []
    counts: Counter = Counter()
    for page_id in rule["pages"]:
        if page_id not in page_counts:
            issues.append(f"{rule['id']}: required page missing: {page_id}")
        counts.update(page_counts.get(page_id, {}))
    for requirement in rule["requirements"]:
        actual = sum(counts[identity] for identity in requirement["components"])
        actual += sum(
            row["id"] in requirement.get("legacy_debt", [])
            and row["page_id"] in rule["pages"] for row in used_debt
        )
        minimum = requirement.get("minimum", 1)
        if actual < minimum:
            issues.append(f"{rule['id']}/{requirement['id']}: expected at least {minimum}, found {actual}")
    return issues


def _applicability_issues(raw, policy, metadata):
    issues = []
    expected_pages = policy.get("expected_pages")
    if expected_pages is not None:
        observed = {page["page_id"] for page in raw.get("pages", [])}
        issues.extend(f"unexpected page: {p}" for p in sorted(observed - set(expected_pages)))
        issues.extend(f"missing admitted page: {p}" for p in sorted(set(expected_pages) - observed))
    slots = metadata.get("page_slots", {})
    for page_id, expected_slot in policy.get("expected_slots", {}).items():
        if slots.get(page_id) != expected_slot:
            issues.append(f"{page_id}: assembly slot differs from reviewed applicability")
    return issues


def _projection_metadata(raw, policy):
    if any(raw.get(key) != policy["target"][key] for key in ("model", "region", "language")):
        raise ValueError("component admission target does not match trusted policy")
    metadata = raw.get("metadata") or {}
    if (raw.get("source") != "prepared-document"
            or metadata.get("projection") != "whole-document-components/v1"):
        raise ValueError("component admission requires prepared-document component projection")
    return metadata


def _asset_debt_issues(debt, metadata):
    actual = metadata.get("asset_sha256", {})
    return [f"legacy debt asset changed: {row['id']}/{path}"
            for row in debt.values() for path, digest in row.get("asset_sha256", {}).items()
            if actual.get(path) != digest]


def audit_prepared_component_coverage(raw: dict, policy: dict) -> dict[str, Any]:
    """Count actual chapter nodes; never trust a candidate coverage summary."""
    metadata = _projection_metadata(raw, policy)
    chapters = _active_chapters(policy)
    debt = _debt_index(policy)
    image_pages = {p for rule in chapters if rule.get("inspect_images") for p in rule["pages"]}
    page_counts, legacy, panels, issues = {}, [], [], []
    issues.extend(_applicability_issues(raw, policy, metadata))
    issues.extend(_asset_debt_issues(debt, metadata))
    for page in raw.get("pages", []):
        page_id = page["page_id"]
        if page_id in page_counts:
            issues.append(f"duplicate page: {page_id}")
            continue
        counts, used, figures, errors = _scan_page(
            page, inspect_images=page_id in image_pages, metadata=metadata, debt=debt,
        )
        page_counts[page_id] = counts
        legacy.extend(used)
        panels.extend(figures)
        issues.extend(errors)
    for rule in chapters:
        issues.extend(_check_chapter(rule, page_counts, legacy))
    used_ids = {row["id"] for row in legacy}
    issues.extend(f"unused legacy debt: {row['id']}" for row in debt.values() if row["id"] not in used_ids)
    totals: Counter = Counter()
    for counts in page_counts.values():
        totals.update(counts)
    return {
        "profile": PROFILE, "target": policy["target"],
        "components": {key: value for key, value in totals.items() if "/" not in key},
        "variants": {key: value for key, value in totals.items() if "/" in key},
        "pages": {key: dict(value) for key, value in page_counts.items()},
        "legacy_debt": legacy, "governed_finished_panels": panels, "issues": issues,
    }
