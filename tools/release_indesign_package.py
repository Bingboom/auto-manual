"""InDesign package lineage for the release manifest (Milestone J P3).

The print deliverable is not the PDF alone: a printer or a designer needs the
InDesign document, the IDML it came from, the linked images, and the font
list — and whoever signs the release needs to know that document passed
preflight. `tools/idml/delivery.py` already assembles the IDML + `Links/` +
font manifest into a handoff zip, and the publish queue already copies that
zip into the release version directory. What was missing is that **nothing
pointed at any of it**: neither the release manifest nor `publish_meta.json`
named the package, and the INDD, the InDesign PDF, the preflight report and
the parity report had no canonical location at all.

This module gives those artifacts one convention — they sit beside the
production IDML in the build's ``idml/`` directory — and records whatever is
present, with hashes, into the release manifest.

Every part is optional by design. InDesign finalize and the parity check run
on an operator's Mac, not in CI, so an automated publish legitimately has no
INDD and no preflight verdict. A collector that demanded them would fail
every unattended release; instead the record says plainly what was found and
what was not, exactly as the asset-lineage collector does.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
FINALIZE_REPORT_NAME = "finalize_report.json"
PARITY_REPORT_NAME = "parity_report.json"
HANDOFF_SUFFIX = "_handoff.zip"


def _file_record(path: Path | None) -> dict[str, Any] | None:
    """{name, size, sha256} for a present file, else None."""
    if path is None or not path.is_file():
        return None
    data = path.read_bytes()
    return {
        "name": path.name,
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return payload if isinstance(payload, dict) else None


def _first(idml_dir: Path, pattern: str) -> Path | None:
    matches = sorted(p for p in idml_dir.glob(pattern) if p.is_file())
    return matches[0] if matches else None


def _preflight_summary(report: dict[str, Any] | None) -> dict[str, Any] | None:
    """The four numbers a release signer actually reads, plus the verdict."""
    if report is None:
        return None
    validation = report.get("pdf_export_validation") or {}
    toolchain = report.get("toolchain") or {}
    return {
        "success": report.get("success"),
        "page_count": report.get("page_count"),
        "overset_stories": len(report.get("overset_stories") or ()),
        "missing_fonts": len(report.get("missing_fonts") or ()),
        "bad_links": len(report.get("bad_links") or ()),
        "pdfx_validated": validation.get("pass"),
        "indesign": toolchain.get("indesign_actual"),
    }


def _parity_summary(report: dict[str, Any] | None) -> dict[str, Any] | None:
    if report is None:
        return None
    return {
        "schema_version": report.get("schema_version"),
        "accepted": report.get("accepted"),
    }


def collect_indesign_package(*, idml_dir: Path) -> dict[str, Any] | None:
    """Record whichever InDesign deliverables exist beside the production IDML.

    Returns ``None`` only when the target produced no IDML directory at all —
    a manual line that never runs the InDesign leg still gets a manifest.
    """
    if not idml_dir.is_dir():
        return None
    idml = _first(idml_dir, "manual_*.idml")
    if idml is None:
        return None

    finalize_report = idml_dir / FINALIZE_REPORT_NAME
    parity_report = idml_dir / PARITY_REPORT_NAME
    record = {
        "schema_version": SCHEMA_VERSION,
        "idml": _file_record(idml),
        "indd": _file_record(_first(idml_dir, "*.indd")),
        "indesign_pdf": _file_record(_first(idml_dir, "*_indesign.pdf")),
        "handoff_zip": _file_record(_first(idml_dir, f"*{HANDOFF_SUFFIX}")),
        "finalize_report": _file_record(finalize_report),
        "parity_report": _file_record(parity_report),
        "preflight": _preflight_summary(_read_json(finalize_report)),
        "parity": _parity_summary(_read_json(parity_report)),
    }
    record["complete"] = all(
        record[key] is not None
        for key in ("idml", "indd", "indesign_pdf", "handoff_zip", "finalize_report")
    )
    return record


def csv_columns(record: dict[str, Any] | None) -> dict[str, str]:
    """Flatten the package into scalar release-CSV columns (the I3 shape)."""
    package = record or {}
    preflight = package.get("preflight") or {}
    parity = package.get("parity") or {}

    def _sha(key: str) -> str:
        entry = package.get(key) or {}
        return str(entry.get("sha256") or "")

    return {
        "indesign_package_complete": "TRUE" if package.get("complete") else "FALSE",
        "indesign_idml_sha256": _sha("idml"),
        "indesign_indd_sha256": _sha("indd"),
        "indesign_handoff_zip_sha256": _sha("handoff_zip"),
        "indesign_preflight_success": (
            "" if preflight.get("success") is None
            else ("TRUE" if preflight.get("success") else "FALSE")
        ),
        "indesign_parity_accepted": (
            "" if parity.get("accepted") is None
            else ("TRUE" if parity.get("accepted") else "FALSE")
        ),
    }
