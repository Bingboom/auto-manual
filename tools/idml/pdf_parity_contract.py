"""Approved-source, PDF structure, export, and editability parity gates."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import zipfile
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from tools.idml.reference_layout_plan import validate_approved_reference_plan
from tools.manual_ir import ManualIR
from tools.utils.path_utils import PathSegments


APPROVED_PLAN_SCHEMA = "approved-reference-layout-plan/v1"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_pdfinfo(text: str) -> dict[str, Any]:
    pages = re.search(r"(?m)^Pages:\s+(\d+)", text)
    size = re.search(
        r"(?m)^Page(?:\s+\d+)? size:\s+([\d.]+) x ([\d.]+) pts", text,
    )
    if not pages or not size:
        raise ValueError("pdfinfo output is missing page count or page size")
    version = re.search(r"(?m)^PDF version:\s+([^\r\n]+)", text)
    subtype = re.search(r"(?m)^PDF subtype:\s+([^\r\n]+)", text)
    return {
        "page_count": int(pages.group(1)),
        "page_width_pt": float(size.group(1)),
        "page_height_pt": float(size.group(2)),
        "pdf_version": version.group(1).strip() if version else None,
        "pdf_subtype": subtype.group(1).strip() if subtype else None,
    }


def _parse_page_sizes(text: str, expected_count: int) -> list[dict[str, Any]]:
    rows = [
        {
            "page": int(match.group(1)),
            "width_pt": float(match.group(2)),
            "height_pt": float(match.group(3)),
        }
        for match in re.finditer(
            r"(?m)^Page\s+(\d+) size:\s+([\d.]+) x ([\d.]+) pts", text,
        )
    ]
    rotations = {
        int(match.group(1)): int(match.group(2))
        for match in re.finditer(r"(?m)^Page\s+(\d+) rot:\s+(-?\d+)", text)
    }
    if len(rows) != expected_count:
        raise ValueError(
            f"pdfinfo reported {len(rows)} page sizes; expected {expected_count}",
        )
    if [row["page"] for row in rows] != list(range(1, expected_count + 1)):
        raise ValueError("pdfinfo page-size rows are not contiguous")
    if sorted(rotations) != list(range(1, expected_count + 1)):
        raise ValueError("pdfinfo page-rotation rows are not contiguous")
    for row in rows:
        row["rotation"] = rotations[row["page"]]
    return rows


def _pdf_info(path: Path) -> dict[str, Any]:
    summary = subprocess.run(
        ["pdfinfo", str(path)], check=True, capture_output=True, text=True,
    )
    parsed = _parse_pdfinfo(summary.stdout)
    details = subprocess.run(
        [
            "pdfinfo", "-f", "1", "-l", str(parsed["page_count"]), "-box",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return {
        "path": str(path.resolve()),
        "sha256": _sha256(path),
        **parsed,
        "page_sizes_pt": _parse_page_sizes(details.stdout, parsed["page_count"]),
    }


def _reference_plan_path(args: argparse.Namespace, manual_ir: Path) -> Path | None:
    if args.reference_layout_plan:
        explicit = Path(args.reference_layout_plan)
        if not explicit.is_file():
            raise FileNotFoundError(f"approved reference plan not found: {explicit}")
        return explicit
    adjacent = manual_ir.parent / PathSegments.REFERENCE_LAYOUT_PLAN_JSON
    return adjacent if adjacent.is_file() else None


def _read_reference_plan(
    path: Path | None,
    manual_ir: ManualIR,
) -> dict[str, Any] | None:
    if path is None:
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != APPROVED_PLAN_SCHEMA:
        raise ValueError(
            f"reference plan schema must be {APPROVED_PLAN_SCHEMA}: {path}",
        )
    issues = validate_approved_reference_plan(payload, manual_ir)
    if issues:
        raise ValueError("invalid approved reference plan: " + "; ".join(issues))
    return payload


def _approved_contract_report(
    *,
    plan_path: Path | None,
    plan: dict[str, Any] | None,
    manual_ir: dict[str, Any],
    reference: dict[str, Any],
) -> dict[str, Any]:
    if plan is None:
        return {
            "enforced": True,
            "path": None,
            "missing": True,
            "pass": False,
        }
    expected_reference = plan["reference_pdf"]
    expected_source = plan["source_identity"]
    source_fields = {
        "manual_content_sha256": "content_sha256",
        "snapshot_sha256": "snapshot_sha256",
        "style_contract_sha256": "style_contract_sha256",
        "layout_params_sha256": "layout_params_sha256",
    }
    source_checks = {
        contract_key: {
            "expected": expected_source.get(contract_key),
            "actual": manual_ir.get(ir_key),
            "pass": expected_source.get(contract_key) == manual_ir.get(ir_key),
        }
        for contract_key, ir_key in source_fields.items()
    }
    reference_checks = {
        "sha256": {
            "expected": expected_reference["sha256"],
            "actual": reference["sha256"],
            "pass": expected_reference["sha256"] == reference["sha256"],
        },
        "byte_size": {
            "expected": expected_reference["byte_size"],
            "actual": Path(reference["path"]).stat().st_size,
            "pass": expected_reference["byte_size"]
            == Path(reference["path"]).stat().st_size,
        },
        "page_count": {
            "expected": expected_reference["page_count"],
            "actual": reference["page_count"],
            "pass": expected_reference["page_count"] == reference["page_count"],
        },
    }
    return {
        "enforced": True,
        "path": str(plan_path.resolve()) if plan_path else None,
        "sha256": _sha256(plan_path) if plan_path else None,
        "logical_id": expected_reference.get("logical_id"),
        "approval": plan.get("approval"),
        "source_identity": source_checks,
        "reference_pdf": reference_checks,
        "pass": all(item["pass"] for item in source_checks.values())
        and all(item["pass"] for item in reference_checks.values()),
    }


def _structure_report(
    reference: dict[str, Any],
    indesign: dict[str, Any],
    *,
    plan: dict[str, Any] | None,
    fallback_tolerance: float,
) -> dict[str, Any]:
    expected_count = (
        plan["reference_pdf"]["page_count"] if plan else reference["page_count"]
    )
    expected_size = (
        plan["reference_pdf"]["page_size_pt"]
        if plan else {
            "width": reference["page_width_pt"],
            "height": reference["page_height_pt"],
        }
    )
    tolerance = (
        plan["reference_pdf"]["page_size_tolerance_pt"]
        if plan else fallback_tolerance
    )
    page_deltas = []
    for row in indesign["page_sizes_pt"]:
        raw_width_delta = abs(row["width_pt"] - expected_size["width"])
        raw_height_delta = abs(row["height_pt"] - expected_size["height"])
        page_deltas.append({
            "page": row["page"],
            "rotation": row["rotation"],
            "width_delta_pt": round(raw_width_delta, 6),
            "height_delta_pt": round(raw_height_delta, 6),
            "size_pass": max(raw_width_delta, raw_height_delta) <= tolerance,
            "rotation_pass": row["rotation"] == 0,
        })
    max_delta = max(
        (
            max(row["width_delta_pt"], row["height_delta_pt"])
            for row in page_deltas
        ),
        default=float("inf"),
    )
    failing_pages = [
        row["page"]
        for row in page_deltas
        if not row["size_pass"]
    ]
    rotated_pages = [row["page"] for row in page_deltas if not row["rotation_pass"]]
    count_match = (
        reference["page_count"] == expected_count
        and indesign["page_count"] == expected_count
    )
    return {
        "expected_page_count": expected_count,
        "reference_page_count": reference["page_count"],
        "indesign_page_count": indesign["page_count"],
        "page_count_match": count_match,
        "expected_page_size_pt": expected_size,
        "page_size_tolerance_pt": tolerance,
        "max_indesign_page_size_delta_pt": round(max_delta, 6),
        "failing_page_sizes": failing_pages,
        "rotated_pages": rotated_pages,
        "indesign_page_size_deltas_pt": page_deltas,
        "pass": count_match and not failing_pages and not rotated_pages,
    }


def _preflight_gate(
    preflight: dict[str, Any],
    *,
    indesign_pdf: Path,
    expected_page_count: int,
    plan: dict[str, Any] | None,
) -> dict[str, Any]:
    expected_reference = plan["reference_pdf"] if plan else {}
    export = preflight.get("pdf_export") or {}
    export_validation = preflight.get("pdf_export_validation") or {}
    raw_output = preflight.get("output_pdf")
    try:
        output_path_match = (
            isinstance(raw_output, str)
            and Path(raw_output).resolve() == indesign_pdf.resolve()
        )
    except OSError:
        output_path_match = False
    checks = {
        "reported_success": bool(preflight.get("success")),
        "output_pdf_match": output_path_match,
        "page_count_match": preflight.get("page_count") == expected_page_count,
        "stage_complete": preflight.get("stage") == "complete",
        "zero_overset": preflight.get("overset_stories") == [],
        "zero_missing_fonts": preflight.get("missing_fonts") == [],
        "zero_bad_links": preflight.get("bad_links") == [],
        "preset_applied": (
            bool(export.get("requested_preset"))
            and export.get("requested_preset") == export.get("applied_preset")
            and expected_reference.get("pdfx", "") in export.get("applied_preset", "")
        ),
        "all_pages_exported": export.get("page_range") == "ALL_PAGES",
        "document_profile_match": (
            export.get("requested_output_intent")
            == expected_reference.get("output_intent")
            == export.get("applied_document_cmyk_profile")
        ),
        "export_validation_pass": bool(export_validation.get("pass")),
        "validated_pdfx_match": (
            export_validation.get("actual_pdfx")
            == expected_reference.get("pdfx")
            == export_validation.get("expected_pdfx")
        ),
        "validated_output_intent_match": (
            export_validation.get("expected_output_intent")
            == expected_reference.get("output_intent")
            and export_validation.get("output_intent_match") is True
        ),
        "validated_output_condition_match": (
            export_validation.get("expected_output_condition")
            == expected_reference.get("output_condition")
            and export_validation.get("output_condition_match") is True
        ),
    }
    return {
        **preflight,
        "binding_checks": checks,
        "pass": all(checks.values()),
    }


def _idml_editability_gate(
    idml_path: Path | None,
    plan: dict[str, Any] | None,
) -> dict[str, Any]:
    contract = plan.get("idml_contract") if plan else None
    if not contract:
        return {"enforced": False, "pass": True}
    forbidden = set(contract["forbidden_visible_whole_page_links"])
    if idml_path is None or not idml_path.is_file():
        return {
            "enforced": True,
            "path": str(idml_path.resolve()) if idml_path else None,
            "missing": True,
            "forbidden_visible_whole_page_links": sorted(forbidden),
            "pass": False,
        }
    linked_names: list[str] = []
    with zipfile.ZipFile(idml_path) as package:
        for member in package.namelist():
            if not member.startswith("Spreads/") or not member.endswith(".xml"):
                continue
            xml = package.read(member).decode("utf-8")
            for uri in re.findall(r'LinkResourceURI="([^"]+)"', xml):
                parsed = urlparse(uri)
                linked_names.append(Path(unquote(parsed.path)).name)
    violations = sorted(forbidden.intersection(linked_names))
    return {
        "enforced": True,
        "path": str(idml_path.resolve()),
        "sha256": _sha256(idml_path),
        "linked_file_names": sorted(set(linked_names)),
        "forbidden_visible_whole_page_links": sorted(forbidden),
        "violations": violations,
        "pass": not violations,
    }


def _pdf_output_contract(
    indesign_pdf: Path,
    indesign_info: dict[str, Any],
    plan: dict[str, Any] | None,
) -> dict[str, Any]:
    if plan is None:
        return {"enforced": True, "missing_approved_plan": True, "pass": False}
    expected = plan["reference_pdf"]
    payload = indesign_pdf.read_bytes()
    output_intent_token = (
        "/Info(" + expected["output_intent"] + ")"
    ).encode("ascii")
    output_condition_token = (
        "/OutputConditionIdentifier(" + expected["output_condition"] + ")"
    ).encode("ascii")
    checks = {
        "pdfx": {
            "expected": expected["pdfx"],
            "actual": indesign_info.get("pdf_subtype"),
            "pass": indesign_info.get("pdf_subtype") == expected["pdfx"],
        },
        "output_intent": {
            "expected": expected["output_intent"],
            "pass": output_intent_token in payload,
        },
        "output_condition": {
            "expected": expected["output_condition"],
            "pass": output_condition_token in payload,
        },
        "output_intents_dictionary": {
            "expected": "/OutputIntents[...] /S/GTS_PDFX",
            "pass": b"/OutputIntents[" in payload and b"/S/GTS_PDFX" in payload,
        },
    }
    return {
        "enforced": True,
        "checks": checks,
        "pass": all(item["pass"] for item in checks.values()),
    }
