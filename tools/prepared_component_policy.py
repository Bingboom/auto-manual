"""Resolve reviewed prepared-Web admission policy independently of candidates.

Enrollment is a code-reviewed contract. This module never derives required
components or exceptions from the IR being admitted, and never updates debt.
"""
from __future__ import annotations

import json
from pathlib import Path

from tools.check_docs_capability import load_capabilities, load_known_missing
from tools.utils.path_utils import get_paths


POLICY_FILENAME = "prepared_component_admission.json"
POLICY_SCHEMA = "prepared-component-admission/v1"


def _debt(page_id: str, rows: list[dict], reasons: dict) -> list[dict]:
    result = []
    for row in rows:
        category = row["category"]
        reason = reasons.get(category)
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError(f"unreviewed component debt category: {category}")
        result.append({
            **row, "id": f"{page_id}:{row['kind']}:{row['location']}",
            "page_id": page_id, "reason": reason,
        })
    return result


def _chapter(page_id: str, row: dict, debt: list[dict], capabilities: dict) -> dict:
    capability = row.get("capability")
    if capability and capabilities.get(capability) is not True:
        raise ValueError(f"admitted chapter capability requires review: {page_id}/{capability}")
    requirements = [
        {"id": identity, "components": [identity], "minimum": minimum}
        for identity, minimum in row["components"].items()
    ]
    chapter = row.get("chapter")
    legacy = [r["id"] for r in debt if r["kind"] == "chapter"]
    if chapter == "app":
        for variant in ("download", "inline-control", "add-device"):
            identity = f"HB-SPECIAL-APP/{variant}"
            if identity not in row["components"]:
                requirements.append({"id": variant, "components": [identity], "legacy_debt": legacy})
    if chapter == "warranty" and not any(k.startswith("HB-WARRANTY-") for k in row["components"]):
        requirements.append({"id": "warranty", "components": ["HB-WARRANTY-LEAD"], "legacy_debt": legacy})
    return {"id": page_id, "pages": [page_id], "requirements": requirements,
            "inspect_images": chapter == "app"}


def _require_capability_chapters(entry, capabilities):
    bound = {row.get("capability") for row in entry["pages"].values()}
    for capability in ("AC/DC输出记忆恢复", "加电包扩容", "UPS功能"):
        if capabilities.get(capability) is True and capability not in bound:
            raise ValueError(f"new capability has no reviewed chapter binding: {capability}")


def resolve_prepared_component_policy(
    *, model: str, region: str, language: str,
    contract_path: Path | None = None, data_dir: Path | None = None,
) -> dict:
    """Load trusted enrollment and the existing capability SSOT; fail closed."""
    paths = get_paths()
    path = contract_path if contract_path is not None else paths.renderer_contracts_dir / POLICY_FILENAME
    data_root = data_dir if data_dir is not None else paths.data_dir
    contract = json.loads(path.read_text(encoding="utf-8"))
    if contract.get("schema_version") != POLICY_SCHEMA:
        raise ValueError("unsupported prepared component admission policy")
    key = f"{model}/{region}/{language}"
    entry = contract["targets"].get(key)
    if entry is None:
        raise ValueError(f"prepared component applicability must be reviewed before publication: {key}")
    document_key = f"{model}_{region}"
    capabilities = load_capabilities(data_root).get(document_key)
    if capabilities is None:
        if not load_known_missing(data_root).get(document_key):
            raise ValueError(f"unreviewed missing capability row: {document_key}")
        capabilities = {}
    _require_capability_chapters(entry, capabilities)
    chapters, debt = [], []
    for page_id, row in entry["pages"].items():
        records = _debt(page_id, row.get("debt", []), contract["debt_reasons"])
        chapters.append(_chapter(page_id, row, records, capabilities))
        debt.extend(records)
    return {
        "target": {"model": model, "region": region, "language": language},
        "capabilities": capabilities, "chapters": chapters, "legacy_debt": debt,
        "expected_pages": list(entry["pages"]),
        "expected_slots": {page: row["slot"] for page, row in entry["pages"].items()},
    }
