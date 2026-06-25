from __future__ import annotations

import json
import shlex
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tools.source_table_sync import (
    CHANGE_REQUEST_SCHEMA_VERSION,
    apply_change_requests,
    load_change_requests,
)


APPROVAL_SCHEMA_VERSION = "source-intake-approval/v1"
APPLY_SCHEMA_VERSION = "source-intake-apply/v1"
CLOSURE_SCHEMA_VERSION = "source-intake-closure/v1"


def _utc_now() -> str:
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return payload


def _clean_hashes(values: list[str] | tuple[str, ...] | set[str]) -> list[str]:
    out: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in out:
            out.append(text)
    return out


def build_approval_report(
    change_request_report: dict[str, Any],
    *,
    approved_hashes: list[str] | tuple[str, ...] | set[str],
    approve_all_resolved: bool = False,
    reviewer: str = "",
) -> dict[str, Any]:
    requests = [item for item in change_request_report.get("requests") or [] if isinstance(item, dict)]
    known = {str(item.get("delta_hash") or "") for item in requests if item.get("delta_hash")}
    resolved = {
        str(item.get("delta_hash") or "")
        for item in requests
        if item.get("delta_hash") and item.get("resolution_status") == "resolved" and item.get("record_id")
    }
    approved = set(_clean_hashes(approved_hashes))
    if approve_all_resolved:
        approved.update(resolved)
    unknown = sorted(item for item in approved if item not in known)
    approved_known = [item for item in sorted(approved) if item in known]
    approved_requests = [item for item in requests if item.get("delta_hash") in approved_known]
    blocked = [
        item
        for item in approved_requests
        if item.get("resolution_status") != "resolved" or not item.get("record_id")
    ]
    return {
        "schema_version": APPROVAL_SCHEMA_VERSION,
        "source_schema_version": change_request_report.get("schema_version") or CHANGE_REQUEST_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "reviewer": reviewer,
        "approve_all_resolved": approve_all_resolved,
        "summary": {
            "requests": len(requests),
            "resolved_requests": len(resolved),
            "approved_hashes": len(approved_known),
            "unknown_hashes": len(unknown),
            "blocked_approved_requests": len(blocked),
        },
        "approved_hashes": approved_known,
        "unknown_hashes": unknown,
        "blocked_approved_requests": [
            {
                "delta_hash": item.get("delta_hash"),
                "table": item.get("table"),
                "field": item.get("field"),
                "resolution_status": item.get("resolution_status"),
                "record_id": item.get("record_id"),
            }
            for item in blocked
        ],
        "approved_requests": [
            {
                "delta_hash": item.get("delta_hash"),
                "table": item.get("table"),
                "field": item.get("field"),
                "record_id": item.get("record_id"),
                "old_value": item.get("old_value"),
                "new_value": item.get("new_value"),
                "intake_candidate_hash": item.get("intake_candidate_hash"),
            }
            for item in approved_requests
        ],
    }


def approval_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") or {}
    lines = [
        "# Source Intake Approval",
        "",
        f"- Created at: `{report.get('created_at')}`",
        f"- Reviewer: `{report.get('reviewer') or 'not recorded'}`",
        f"- Approve all resolved: **{'yes' if report.get('approve_all_resolved') else 'no'}**",
        f"- Requests: {summary.get('requests', 0)}",
        f"- Resolved requests: {summary.get('resolved_requests', 0)}",
        f"- Approved hashes: {summary.get('approved_hashes', 0)}",
        f"- Unknown hashes: {summary.get('unknown_hashes', 0)}",
        f"- Blocked approved requests: {summary.get('blocked_approved_requests', 0)}",
        "",
        "## Approved",
        "",
    ]
    approved_requests = report.get("approved_requests") or []
    if not approved_requests:
        lines.append("- none")
    for item in approved_requests:
        lines.append(
            f"- `{item.get('delta_hash')}` {item.get('table')}::{item.get('field')} "
            f"record `{item.get('record_id')}`: {item.get('old_value')!r} -> {item.get('new_value')!r}"
        )
    unknown = report.get("unknown_hashes") or []
    if unknown:
        lines.extend(["", "## Unknown Hashes", ""])
        for item in unknown:
            lines.append(f"- `{item}`")
    blocked = report.get("blocked_approved_requests") or []
    if blocked:
        lines.extend(["", "## Blocked Approved Requests", ""])
        for item in blocked:
            lines.append(
                f"- `{item.get('delta_hash')}` {item.get('table')}::{item.get('field')} "
                f"status={item.get('resolution_status')} record={item.get('record_id') or '-'}"
            )
    lines.append("")
    return "\n".join(lines)


def write_approval_report(report: dict[str, Any], out_dir: Path) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "source_intake_approval.json"
    markdown_path = out_dir / "source_intake_approval.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(approval_markdown(report), encoding="utf-8")
    return {"approval": json_path, "approval_markdown": markdown_path}


def load_approved_hashes(approval_path: Path | None, extra_approved: list[str] | tuple[str, ...]) -> set[str]:
    hashes: set[str] = set(_clean_hashes(extra_approved))
    if approval_path is None:
        return hashes
    payload = _load_json(approval_path)
    if payload.get("schema_version") != APPROVAL_SCHEMA_VERSION:
        raise RuntimeError(f"{approval_path} is not a {APPROVAL_SCHEMA_VERSION} file")
    hashes.update(_clean_hashes(payload.get("approved_hashes") or []))
    return hashes


def apply_report_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") or {}
    lines = [
        "# Source Intake Apply",
        "",
        f"- External write: **{'yes' if report.get('external_write') else 'no (dry-run)'}**",
        f"- Approved hashes: {report.get('approved_count', 0)}",
        (
            f"- Plan: apply {summary.get('apply', 0)}, skip {summary.get('skip', 0)} / "
            f"written {summary.get('written', 0)}, already {summary.get('already_applied', 0)}, "
            f"drift_abstained {summary.get('drift_abstained', 0)}, verify_failed {summary.get('verify_failed', 0)}, "
            f"error {summary.get('error', 0)}"
        ),
        "",
    ]
    applied = report.get("applied") or []
    if applied:
        lines.extend(["## Applied / Planned", ""])
        for item in applied:
            detail = f" - {item.get('error')}" if item.get("error") else ""
            lines.append(
                f"- `{item.get('status')}` {item.get('table')}::{item.get('field')} "
                f"record `{item.get('record_id')}` delta `{item.get('delta_hash')}`{detail}"
            )
        lines.append("")
    skips = [item for item in (report.get("plan") or []) if item.get("action") == "skip"]
    if skips:
        lines.extend(["## Skipped", ""])
        for item in skips:
            lines.append(
                f"- {item.get('table')}::{item.get('field')} delta `{item.get('delta_hash')}` - {item.get('reason')}"
            )
        lines.append("")
    return "\n".join(lines)


def build_apply_report(
    change_request_report_path: Path,
    *,
    approval_path: Path | None = None,
    approved_hashes: list[str] | tuple[str, ...] = (),
    transport: Any = None,
    write: bool = False,
) -> dict[str, Any]:
    requests, run_id = load_change_requests(change_request_report_path)
    approved = load_approved_hashes(approval_path, approved_hashes)
    result = apply_change_requests(
        requests,
        approved_hashes=approved,
        transport=transport,
        write=write,
    )
    return {
        **result,
        "schema_version": APPLY_SCHEMA_VERSION,
        "source_schema_version": result.get("schema_version"),
        "source": "source-intake",
        "run_id": run_id,
        "approved_count": len(approved),
        "approval_path": str(approval_path) if approval_path else None,
        "change_request_path": str(change_request_report_path),
    }


def write_apply_report(report: dict[str, Any], out_dir: Path) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "source_intake_apply.json"
    markdown_path = out_dir / "source_intake_apply.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(apply_report_markdown(report), encoding="utf-8")
    return {"apply": json_path, "apply_markdown": markdown_path}


def _command_result(label: str, command: str, *, cwd: Path) -> dict[str, Any]:
    argv = shlex.split(command)
    if not argv:
        raise RuntimeError(f"empty verification command for {label!r}")
    completed = subprocess.run(
        argv,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return {
        "label": label,
        "command": argv,
        "returncode": completed.returncode,
        "passed": completed.returncode == 0,
        "stdout_tail": "\n".join((completed.stdout or "").splitlines()[-40:]),
        "stderr_tail": "\n".join((completed.stderr or "").splitlines()[-40:]),
    }


def parse_check_command(spec: str) -> tuple[str, str]:
    label, sep, command = str(spec or "").partition("=")
    label = label.strip()
    command = command.strip()
    if not (sep and label and command):
        raise RuntimeError("--check-command must look like LABEL=COMMAND")
    return label, command


def run_check_commands(specs: list[str] | tuple[str, ...], *, cwd: Path) -> list[dict[str, Any]]:
    return [
        _command_result(label, command, cwd=cwd)
        for label, command in (parse_check_command(spec) for spec in specs)
    ]


def build_closure_report(
    *,
    candidates_path: Path,
    change_request_path: Path,
    approval_path: Path,
    apply_report_path: Path,
    command_results: list[dict[str, Any]],
    require_write: bool = False,
) -> dict[str, Any]:
    candidates = _load_json(candidates_path)
    change_request = _load_json(change_request_path)
    approval = _load_json(approval_path)
    apply_report = _load_json(apply_report_path)
    approval_summary = approval.get("summary") or {}
    apply_summary = apply_report.get("summary") or {}
    p4 = approval_summary.get("approved_hashes", 0) > 0 and approval_summary.get("unknown_hashes", 0) == 0
    if require_write:
        p5 = bool(apply_report.get("external_write")) and apply_summary.get("written", 0) + apply_summary.get("already_applied", 0) > 0
    else:
        p5 = apply_summary.get("apply", 0) > 0 and apply_summary.get("error", 0) == 0 and apply_summary.get("verify_failed", 0) == 0
    labels = {str(item.get("label") or ""): item for item in command_results}
    p6 = any(label.startswith("sync-data") and item.get("passed") for label, item in labels.items())
    p7 = any(
        (label.startswith("build") or label.startswith("review") or label.startswith("backport")) and item.get("passed")
        for label, item in labels.items()
    )
    passed_commands = all(item.get("passed") for item in command_results)
    phase_status = {
        "P4_human_review": p4,
        "P5_source_table_apply": p5,
        "P6_sync_data": p6,
        "P7_build_review_backport": p7,
    }
    return {
        "schema_version": CLOSURE_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "require_write": require_write,
        "summary": {
            "passed": all(phase_status.values()) and passed_commands,
            "candidates": (candidates.get("summary") or {}).get("candidates", 0),
            "requests": (change_request.get("summary") or {}).get("requests", 0),
            "approved_hashes": approval_summary.get("approved_hashes", 0),
            "apply": apply_summary.get("apply", 0),
            "written": apply_summary.get("written", 0),
            "commands": len(command_results),
            "commands_failed": sum(1 for item in command_results if not item.get("passed")),
        },
        "phase_status": phase_status,
        "artifacts": {
            "candidates": str(candidates_path),
            "change_request": str(change_request_path),
            "approval": str(approval_path),
            "apply": str(apply_report_path),
        },
        "command_results": command_results,
    }


def closure_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") or {}
    phase_status = report.get("phase_status") or {}
    lines = [
        "# Source Intake Closure",
        "",
        f"- Created at: `{report.get('created_at')}`",
        f"- Result: **{'PASS' if summary.get('passed') else 'FAIL'}**",
        f"- Require live write: **{'yes' if report.get('require_write') else 'no'}**",
        "",
        "## Phase Checklist",
        "",
    ]
    for key, label in (
        ("P4_human_review", "P4 human review approval"),
        ("P5_source_table_apply", "P5 source-table apply"),
        ("P6_sync_data", "P6 sync-data verification"),
        ("P7_build_review_backport", "P7 build/review/backport verification"),
    ):
        lines.append(f"- [{'x' if phase_status.get(key) else ' '}] {label}")
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Candidates: {summary.get('candidates', 0)}",
            f"- Requests: {summary.get('requests', 0)}",
            f"- Approved hashes: {summary.get('approved_hashes', 0)}",
            f"- Apply-plan entries: {summary.get('apply', 0)}",
            f"- Written rows: {summary.get('written', 0)}",
            f"- Commands: {summary.get('commands', 0)}",
            f"- Commands failed: {summary.get('commands_failed', 0)}",
            "",
            "## Commands",
            "",
        ]
    )
    for item in report.get("command_results") or []:
        lines.append(f"- `{'PASS' if item.get('passed') else 'FAIL'}` {item.get('label')}: `{' '.join(item.get('command') or [])}`")
    lines.append("")
    return "\n".join(lines)


def write_closure_report(report: dict[str, Any], out_dir: Path) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "source_intake_closure.json"
    markdown_path = out_dir / "source_intake_closure.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(closure_markdown(report), encoding="utf-8")
    return {"closure": json_path, "closure_markdown": markdown_path}
