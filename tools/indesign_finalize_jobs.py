"""Validate and run a batch of isolated InDesign finalize jobs."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

JOBS_SCHEMA_VERSION = "indesign-finalize-jobs/v1"
_REQUIRED_JOB_FIELDS = (
    "idml",
    "indd",
    "pdf",
    "report",
    "pdf_preset",
    "output_intent",
    "output_condition",
    "pdfx",
)


class FinalizeJobsError(ValueError):
    """A jobs manifest cannot be safely validated or executed."""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FinalizeJobsError(f"cannot read jobs manifest {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise FinalizeJobsError(f"jobs manifest must contain an object: {path}")
    return payload


def validate_jobs_manifest(payload: dict[str, Any]) -> list[str]:
    """Return all manifest-shape errors without touching InDesign or files."""
    issues: list[str] = []
    if payload.get("schema_version") != JOBS_SCHEMA_VERSION:
        issues.append(f"schema_version must be {JOBS_SCHEMA_VERSION}")
    jobs = payload.get("jobs")
    if not isinstance(jobs, list) or not jobs:
        issues.append("jobs must be a non-empty list")
        return issues

    ids: set[str] = set()
    output_paths: dict[str, str] = {}
    for index, raw in enumerate(jobs):
        prefix = f"jobs[{index}]"
        if not isinstance(raw, dict):
            issues.append(f"{prefix} must be an object")
            continue
        job_id = raw.get("id")
        if not isinstance(job_id, str) or not job_id.strip():
            issues.append(f"{prefix}.id must be a non-empty string")
        elif job_id in ids:
            issues.append(f"duplicate job id: {job_id}")
        else:
            ids.add(job_id)
        for field in _REQUIRED_JOB_FIELDS:
            value = raw.get(field)
            if not isinstance(value, str) or not value.strip():
                issues.append(f"{prefix}.{field} must be explicitly provided")
        application = raw.get("application", "Adobe InDesign 2026")
        if not isinstance(application, str) or not application.strip():
            issues.append(f"{prefix}.application must be a non-empty string")
        for field in ("indd", "pdf", "report"):
            value = raw.get(field)
            if not isinstance(value, str) or not value.strip():
                continue
            key = str(Path(value).resolve())
            previous = output_paths.setdefault(key, f"{prefix}.{field}")
            if previous != f"{prefix}.{field}":
                issues.append(
                    f"{prefix}.{field} collides with {previous}: {value}"
                )
    return issues


def _resolve(raw: str, *, base: Path) -> str:
    path = Path(raw)
    return str((base / path).resolve()) if not path.is_absolute() else str(path.resolve())


def normalize_jobs(payload: dict[str, Any], *, base: Path) -> list[dict[str, str]]:
    """Resolve paths relative to the manifest and retain explicit job settings."""
    issues = validate_jobs_manifest(payload)
    if issues:
        raise FinalizeJobsError("; ".join(issues))
    jobs: list[dict[str, str]] = []
    for raw in payload["jobs"]:
        jobs.append({
            "job_id": raw["id"],
            "input_idml": _resolve(raw["idml"], base=base),
            "output_indd": _resolve(raw["indd"], base=base),
            "output_pdf": _resolve(raw["pdf"], base=base),
            "report_json": _resolve(raw["report"], base=base),
            "pdf_preset": raw["pdf_preset"],
            "output_intent": raw["output_intent"],
            "output_condition": raw["output_condition"],
            "pdfx": raw["pdfx"],
            "application": raw.get("application", "Adobe InDesign 2026"),
        })
    return jobs


def scan_incomplete_packages(jobs: list[dict[str, str]]) -> dict[str, Any]:
    """Inventory incomplete package directories and group them by build path."""
    from tools.release_indesign_package import collect_indesign_package

    items: list[dict[str, Any]] = []
    groups: dict[str, list[str]] = {}
    for job in jobs:
        idml_dir = str(Path(job["input_idml"]).parent)
        package = collect_indesign_package(idml_dir=Path(idml_dir))
        if package is None:
            item = {"job_id": job["job_id"], "idml_dir": idml_dir, "status": "missing_idml"}
        elif package.get("complete"):
            item = {"job_id": job["job_id"], "idml_dir": idml_dir, "status": "complete"}
        else:
            missing = [
                key for key in ("indd", "indesign_pdf", "handoff_zip", "finalize_report")
                if package.get(key) is None
            ]
            item = {
                "job_id": job["job_id"],
                "idml_dir": idml_dir,
                "status": "incomplete",
                "missing": missing,
            }
            groups.setdefault(idml_dir, []).append(job["job_id"])
        items.append(item)
    return {
        "scanned": len(items),
        "complete_count": sum(item["status"] == "complete" for item in items),
        "incomplete_count": sum(item["status"] == "incomplete" for item in items),
        "missing_idml_count": sum(item["status"] == "missing_idml" for item in items),
        "items": items,
        "batches": [
            {"idml_dir": idml_dir, "job_ids": job_ids}
            for idml_dir, job_ids in sorted(groups.items())
        ],
    }


def run_jobs_manifest(
    manifest_path: Path,
    *,
    aggregate_report: Path | None = None,
    allow_version_mismatch: bool = False,
    runner: Callable[[dict[str, str], str, str], dict[str, Any]] | None = None,
    version_checker: Callable[[], tuple[str, str]] | None = None,
) -> int:
    """Run every valid job, isolating job failures and writing one aggregate."""
    manifest_path = manifest_path.resolve()
    payload = _read_json(manifest_path)
    jobs = normalize_jobs(payload, base=manifest_path.parent)
    report_path = aggregate_report or payload.get("aggregate_report")
    if report_path is None:
        report_path = manifest_path.with_name(f"{manifest_path.stem}.report.json")
    elif not isinstance(report_path, (str, Path)):
        raise FinalizeJobsError("aggregate_report must be a path")
    report_path = Path(report_path)
    if not report_path.is_absolute():
        report_path = manifest_path.parent / report_path
    report_path = report_path.resolve()

    if version_checker is None:
        from tools.indesign_finalize import check_version_pin

        version_checker = check_version_pin
    pin_status, pin_message = version_checker()
    before = scan_incomplete_packages(jobs)
    aggregate: dict[str, Any] = {
        "schema_version": JOBS_SCHEMA_VERSION,
        "manifest": str(manifest_path),
        "version_pin": {"status": pin_status, "message": pin_message},
        "package_scan_before": before,
        "jobs": [],
    }

    if pin_status == "no_indesign" or (
        pin_status == "mismatch" and not allow_version_mismatch
    ):
        aggregate["success"] = False
        aggregate["error"] = pin_message
        aggregate["package_scan_after"] = before
        _write_report(report_path, aggregate)
        return 2

    if runner is None:
        from tools.indesign_finalize import run_finalize_jobs

        aggregate["jobs"] = run_finalize_jobs(
            jobs, pin_status=pin_status, pin_message=pin_message,
        )
    else:
        for job in jobs:
            try:
                result = runner(job, pin_status, pin_message)
            except Exception as exc:  # injectable per-job path used by tests/callers
                result = {
                    "job_id": job["job_id"],
                    "success": False,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            result.setdefault("job_id", job["job_id"])
            aggregate["jobs"].append(result)

    after = scan_incomplete_packages(jobs)
    aggregate["package_scan_after"] = after
    aggregate["success"] = bool(aggregate["jobs"]) and all(
        bool(job.get("success")) for job in aggregate["jobs"]
    )
    _write_report(report_path, aggregate)
    print(
        f"[indesign-finalize] batch {'OK' if aggregate['success'] else 'FAIL'}: "
        f"jobs={len(jobs)} failed={sum(not job.get('success') for job in aggregate['jobs'])} "
        f"incomplete_packages={after['incomplete_count']} report={report_path}"
    )
    return 0 if aggregate["success"] else 1


def _write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


__all__ = (
    "FinalizeJobsError",
    "JOBS_SCHEMA_VERSION",
    "normalize_jobs",
    "run_jobs_manifest",
    "scan_incomplete_packages",
    "validate_jobs_manifest",
)
