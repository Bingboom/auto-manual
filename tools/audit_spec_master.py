#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import csv
from collections import Counter
import sys
from pathlib import Path

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=1)

from tools.utils.spec_master import (  # noqa: E402
    SpecMasterAuditIssue,
    SpecMasterAuditResult,
    SpecMasterSectionSummary,
    audit_spec_master_csv,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser("audit Spec_Master.csv quality and section consistency")
    parser.add_argument(
        "--csv",
        default="data/phase1/Spec_Master.csv",
        help="path to Spec_Master.csv",
    )
    parser.add_argument(
        "--out-dir",
        default="reports/spec_master",
        help="directory for generated audit reports",
    )
    parser.add_argument(
        "--sample-limit",
        type=int,
        default=40,
        help="max issue rows to inline in the markdown report",
    )
    return parser.parse_args()


def resolve_path(raw_path: str) -> Path:
    path = Path(raw_path)
    return path if path.is_absolute() else (ROOT / path)


def write_section_summary_csv(path: Path, summaries: tuple[SpecMasterSectionSummary, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "section",
                "suggested_section",
                "category",
                "row_count",
                "orders",
                "models",
                "regions",
                "note",
            ],
        )
        writer.writeheader()
        for summary in summaries:
            writer.writerow(
                {
                    "section": summary.section,
                    "suggested_section": summary.suggested_section,
                    "category": summary.category,
                    "row_count": summary.row_count,
                    "orders": ", ".join(summary.orders),
                    "models": ", ".join(summary.models),
                    "regions": ", ".join(summary.regions),
                    "note": summary.note,
                }
            )


def write_issues_csv(path: Path, issues: tuple[SpecMasterAuditIssue, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["code", "line", "model", "region", "section", "row_key", "message"],
        )
        writer.writeheader()
        for issue in issues:
            writer.writerow(
                {
                    "code": issue.code,
                    "line": issue.line or "",
                    "model": issue.model or "",
                    "region": issue.region or "",
                    "section": issue.section or "",
                    "row_key": issue.row_key or "",
                    "message": issue.message,
                }
            )


def render_markdown(
    audit: SpecMasterAuditResult,
    *,
    csv_path: Path,
    section_csv_path: Path,
    issues_csv_path: Path,
    sample_limit: int,
) -> str:
    issue_counts = Counter(issue.code for issue in audit.issues)
    lines = [
        "# Spec_Master Audit",
        "",
        f"- Source CSV: `{csv_path}`",
        f"- Total rows: {audit.total_rows}",
        f"- Unique sections: {audit.unique_sections}",
        f"- Total issues: {len(audit.issues)}",
        f"- Section summary CSV: `{section_csv_path}`",
        f"- Issues CSV: `{issues_csv_path}`",
        "",
        "## Recommended Section Map",
        "",
        "| Section | Suggested Section | Category | Rows | Orders | Note |",
        "| --- | --- | --- | ---: | --- | --- |",
    ]
    for summary in audit.section_summaries:
        lines.append(
            "| {section} | {suggested} | {category} | {rows} | {orders} | {note} |".format(
                section=summary.section,
                suggested=summary.suggested_section,
                category=summary.category,
                rows=summary.row_count,
                orders=", ".join(summary.orders) or "-",
                note=summary.note or "-",
            )
        )

    lines.extend(["", "## Section Order Conflicts", ""])
    if audit.order_conflicts:
        for conflict in audit.order_conflicts:
            lines.append(
                f"- `Section_order={conflict.section_order}` is used by: {', '.join(conflict.sections)}"
            )
    else:
        lines.append("- None")

    lines.extend(["", "## Issue Counts", ""])
    if issue_counts:
        for code, count in sorted(issue_counts.items()):
            lines.append(f"- `{code}`: {count}")
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            f"## Sample Issues (first {sample_limit})",
            "",
            "| Code | Line | Model | Region | Section | Row Key | Message |",
            "| --- | ---: | --- | --- | --- | --- | --- |",
        ]
    )
    for issue in audit.issues[:sample_limit]:
        lines.append(
            "| {code} | {line} | {model} | {region} | {section} | {row_key} | {message} |".format(
                code=issue.code,
                line=issue.line or "",
                model=issue.model or "",
                region=issue.region or "",
                section=issue.section or "",
                row_key=issue.row_key or "",
                message=issue.message.replace("|", "\\|"),
            )
        )
    if not audit.issues:
        lines.append("| - | - | - | - | - | - | No issues detected. |")

    lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    csv_path = resolve_path(args.csv)
    out_dir = resolve_path(args.out_dir)

    audit = audit_spec_master_csv(csv_path)

    out_dir.mkdir(parents=True, exist_ok=True)
    section_csv_path = out_dir / "section_summary.csv"
    issues_csv_path = out_dir / "issues.csv"
    report_path = out_dir / "spec_master_audit.md"

    write_section_summary_csv(section_csv_path, audit.section_summaries)
    write_issues_csv(issues_csv_path, audit.issues)
    report_path.write_text(
        render_markdown(
            audit,
            csv_path=csv_path,
            section_csv_path=section_csv_path,
            issues_csv_path=issues_csv_path,
            sample_limit=max(args.sample_limit, 0),
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"[audit_spec_master] Wrote: {report_path}")
    print(f"[audit_spec_master] Wrote: {section_csv_path}")
    print(f"[audit_spec_master] Wrote: {issues_csv_path}")
    print(
        "[audit_spec_master] Summary: "
        f"rows={audit.total_rows}, sections={audit.unique_sections}, issues={len(audit.issues)}"
    )


if __name__ == "__main__":
    main()
