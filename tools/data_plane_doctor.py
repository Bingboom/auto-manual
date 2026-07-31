"""Read-only data-plane preflight for one new manual target."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.data_snapshot import inspect_phase2_snapshot
from tools.validate_spec_master_runtime import collect_spec_master_validation_issues


DataPlaneFinding = tuple[str, str, str]


def collect_data_plane_findings(
    *,
    cfg: dict[str, Any],
    cfg_path: Path,
    repo_root: Path,
    model: str | None,
    region: str | None,
    data_root: str | None,
) -> list[DataPlaneFinding]:
    """Check snapshot completeness and target rows without syncing or writing."""

    findings: list[DataPlaneFinding] = []
    if not model or not region:
        return [
            (
                "ERROR",
                "data_plane.target",
                "data-plane preflight requires one explicit model and region",
            )
        ]

    snapshot = inspect_phase2_snapshot(
        cfg,
        repo_root=repo_root,
        data_root=data_root,
        model=model,
        region=region,
    )
    if not snapshot.valid:
        findings.extend(
            (
                "ERROR",
                "data_plane.snapshot",
                issue,
            )
            for issue in snapshot.issues
        )
        return findings

    findings.append(
        (
            "OK",
            "data_plane.snapshot",
            f"complete phase2 snapshot found at {snapshot.export_root}",
        )
    )

    try:
        issues = collect_spec_master_validation_issues(
            cfg_path=cfg_path,
            model=model,
            region=region,
            all_targets=False,
            data_root=data_root,
            source_mode="runtime",
        )
    except Exception as exc:
        findings.append(("ERROR", "data_plane.spec_master", f"validation failed: {exc}"))
        return findings

    if issues:
        findings.extend(
            (
                "ERROR",
                "data_plane.spec_master",
                f"{issue.code}: {issue.message}",
            )
            for issue in issues
        )
    else:
        findings.append(
            (
                "OK",
                "data_plane.spec_master",
                f"required source rows are present for {model}/{region}",
            )
        )
    return findings


__all__ = ("DataPlaneFinding", "collect_data_plane_findings")
