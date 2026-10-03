#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Markdown report renderers for cloud-doc backport.

Pure ``report dict -> markdown`` functions, extracted from cloud_doc_backport.py
(debt-paydown D2). No dependency on the Block model or the diff/apply pipeline,
so they import only stdlib. Re-exported by cloud_doc_backport for callers.
"""
from __future__ import annotations

import json
from typing import Any


def _markdown_cell(value: object) -> str:
    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False)
    else:
        text = str(value or "")
    return text.replace("\n", " ").replace("|", "\\|")

def markdown_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    source_target = report.get("source_target") or {}
    section_selection = report.get("section_selection") or {}
    lines = [
        "# Cloud Doc Backport Diff Report",
        "",
        "## Run",
        "",
        f"- Run ID: `{report['run_id']}`",
        f"- Result: `{report['result']}`",
        f"- Doc type: `{report['doc_type']}`",
        f"- Baseline: `{report['baseline']}`",
        f"- Source target: `{source_target.get('path') or '-'}`",
        f"- Normalizer: `{report['normalizer_version']}`",
        f"- Git ref: `{report['metadata'].get('git_ref') or 'unknown'}`",
        f"- Generated at: `{report['metadata']['generated_at']}`",
        f"- Command: `{report['metadata']['command']}`",
        f"- Section: `{section_selection.get('resolved_title') or '-'}`",
        f"- Section applied: `{section_selection.get('applied', False)}`",
        "",
        "## Summary",
        "",
        f"- Total deltas: `{summary['total_deltas']}`",
        f"- Baseline blocks: `{summary['baseline_blocks']}`",
        f"- Fetched blocks: `{summary['fetched_blocks']}`",
        f"- Change types: `{json.dumps(summary['change_types'], ensure_ascii=False)}`",
        f"- Route classes: `{json.dumps(summary['route_classes'], ensure_ascii=False)}`",
        "",
        "## Deltas",
        "",
    ]
    if not report["deltas"]:
        lines.append("No deltas.")
    else:
        lines.extend(
            [
                "| # | Type | Route | Confidence | Location | Old | New |",
                "| ---: | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for index, delta in enumerate(report["deltas"], start=1):
            location = delta["location"]
            heading = " > ".join(location.get("heading_path") or [])
            location_text = f"{location.get('kind', '-')}:L{location.get('line_no', '-')}"
            if heading:
                location_text = f"{heading} / {location_text}"
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(index),
                        _markdown_cell(delta["change_type"]),
                        _markdown_cell(delta["route_class"]),
                        _markdown_cell(delta["confidence"]),
                        _markdown_cell(location_text),
                        _markdown_cell(delta.get("old_text")),
                        _markdown_cell(delta.get("new_text")),
                    ]
                )
                + " |"
            )
    return "\n".join(lines) + "\n"

def markdown_apply_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Cloud Doc Backport Apply Report",
        "",
        "## Run",
        "",
        f"- Mode: `{report['mode']}`",
        f"- Source target: `{report['source_target']['path']}`",
        f"- Changed: `{summary['changed']}`",
        f"- Git ref: `{report['metadata'].get('git_ref') or 'unknown'}`",
        f"- Generated at: `{report['metadata']['generated_at']}`",
        f"- Command: `{report['metadata']['command']}`",
        "",
        "## Summary",
        "",
        f"- Total operations: `{summary['total_operations']}`",
        f"- Statuses: `{json.dumps(summary['statuses'], ensure_ascii=False)}`",
        "",
        "## Operations",
        "",
    ]
    if not report["operations"]:
        lines.append("No operations.")
    else:
        lines.extend(
            [
                "| # | Status | Reason | Matches | Old | New |",
                "| ---: | --- | --- | ---: | --- | --- |",
            ]
        )
        for operation in report["operations"]:
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(operation["index"]),
                        _markdown_cell(operation.get("status")),
                        _markdown_cell(operation.get("reason")),
                        _markdown_cell(operation.get("matches")),
                        _markdown_cell(operation.get("old_text")),
                        _markdown_cell(operation.get("new_text")),
                    ]
                )
                + " |"
            )
    return "\n".join(lines) + "\n"

def markdown_verify_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Cloud Doc Backport Verify Report",
        "",
        "## Run",
        "",
        f"- Result: `{report['result']}`",
        f"- Source target: `{report['source_target']['path']}`",
        f"- Git ref: `{report['metadata'].get('git_ref') or 'unknown'}`",
        f"- Generated at: `{report['metadata']['generated_at']}`",
        f"- Command: `{report['metadata']['command']}`",
        "",
        "## Summary",
        "",
        f"- Total results: `{summary['total_results']}`",
        f"- Categories: `{json.dumps(summary['categories'], ensure_ascii=False)}`",
        f"- Failing categories: `{json.dumps(summary['failing_categories'], ensure_ascii=False)}`",
        f"- Source-table suggestions: `{summary['source_table_suggestions']}`",
        "",
        "## Results",
        "",
    ]
    if not report["results"]:
        lines.append("No results.")
    else:
        lines.extend(
            [
                "| # | Category | Status | Reason | Old matches | New matches | Old | New |",
                "| ---: | --- | --- | --- | ---: | ---: | --- | --- |",
            ]
        )
        for result in report["results"]:
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(result["index"]),
                        _markdown_cell(result.get("category")),
                        _markdown_cell(result.get("status")),
                        _markdown_cell(result.get("reason")),
                        _markdown_cell(result.get("old_matches")),
                        _markdown_cell(result.get("new_matches")),
                        _markdown_cell(result.get("old_text")),
                        _markdown_cell(result.get("new_text")),
                    ]
                )
                + " |"
            )
    suggestions = report.get("source_table_suggestions") or []
    lines.extend(["", "## Source-Table Suggestions", ""])
    if not suggestions:
        lines.append("No source-table suggestions.")
    else:
        lines.extend(
            [
                "| # | Location | Old | New | Evidence |",
                "| ---: | --- | --- | --- | --- |",
            ]
        )
        for suggestion in suggestions:
            location = suggestion.get("location") or {}
            heading = " > ".join(location.get("heading_path") or [])
            location_text = f"{location.get('kind', '-')}:L{location.get('line_no', '-')}"
            if heading:
                location_text = f"{heading} / {location_text}"
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(suggestion.get("index")),
                        _markdown_cell(location_text),
                        _markdown_cell(suggestion.get("old_text")),
                        _markdown_cell(suggestion.get("new_text")),
                        _markdown_cell(suggestion.get("source_evidence")),
                    ]
                )
                + " |"
            )
    return "\n".join(lines) + "\n"

def markdown_source_table_suggestions_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    source_target = report.get("source_target") or {}
    lines = [
        "# Cloud Doc Backport Source-Table Suggestions",
        "",
        "## Contract",
        "",
        "- External write: `False`",
        "- Purpose: review data-like deltas before updating Feishu phase2 source tables.",
        f"- Source target: `{source_target.get('path') or '-'}`",
        f"- Git ref: `{report['metadata'].get('git_ref') or 'unknown'}`",
        f"- Generated at: `{report['metadata']['generated_at']}`",
        "",
        "## Summary",
        "",
        f"- Result: `{report['result']}`",
        f"- Total suggestions: `{summary['total_suggestions']}`",
        f"- Route keys: `{json.dumps(summary['route_keys'], ensure_ascii=False)}`",
        f"- Candidate source tables: `{', '.join(summary['candidate_source_tables']) or '-'}`",
        "",
        "## Suggested Operator Steps",
        "",
    ]
    for step in report["operator_contract"]["next_steps"]:
        lines.append(f"- {step}")
    lines.extend(["", "## Suggestions", ""])
    suggestions = report.get("suggestions") or []
    if not suggestions:
        lines.append("No source-table suggestions.")
        return "\n".join(lines) + "\n"
    lines.extend(
        [
            "| # | Route | Candidate Tables | Confidence | Location | Old | New |",
            "| ---: | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for suggestion in suggestions:
        routing = suggestion.get("routing_hint") or {}
        locator = suggestion.get("operator_locator") or {}
        location_parts = []
        if locator.get("heading"):
            location_parts.append(str(locator.get("heading")))
        if locator.get("kind") or locator.get("line_no"):
            location_parts.append(f"{locator.get('kind', '-')}:L{locator.get('line_no', '-')}")
        lines.append(
            "| "
            + " | ".join(
                [
                    str(suggestion.get("index")),
                    _markdown_cell(routing.get("route_key")),
                    _markdown_cell(", ".join(routing.get("candidate_source_tables") or [])),
                    _markdown_cell(routing.get("confidence")),
                    _markdown_cell(" / ".join(location_parts) or "-"),
                    _markdown_cell(suggestion.get("old_text")),
                    _markdown_cell(suggestion.get("new_text")),
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"

def markdown_template_sync_proposal_report(report: dict[str, Any]) -> str:
    proposals = report.get("proposals") or []
    lines = [
        "# Template Sync Proposal",
        "",
        f"- Run ID: `{report.get('run_id')}`",
        f"- Proposals: `{report['summary']['proposals']}`",
        "- External write: `false` (report-only; apply via the template-sync role)",
        "",
    ]
    if not proposals:
        lines.append("_No shared-across-family (Class T) deltas in this run._")
        return "\n".join(lines) + "\n"
    lines += ["| # | change | targets | old | new |", "| --- | --- | --- | --- | --- |"]
    for proposal in proposals:
        lines.append(
            "| {index} | {change} | {targets} | {old} | {new} |".format(
                index=proposal.get("index"),
                change=_markdown_cell(proposal.get("change_type")),
                targets=_markdown_cell(", ".join(proposal.get("target_templates") or [])),
                old=_markdown_cell(proposal.get("old_text")),
                new=_markdown_cell(proposal.get("new_text")),
            )
        )
    return "\n".join(lines) + "\n"

def markdown_review_run_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Cloud Doc Backport Run Report",
        "",
        "## Run",
        "",
        f"- Result: `{report['result']}`",
        f"- Mode: `{report['mode']}`",
        f"- Source target: `{(report.get('source_target') or {}).get('path') or '-'}`",
        f"- Section: `{(report.get('section_selection') or {}).get('resolved_title') or '-'}`",
        f"- Section applied: `{(report.get('section_selection') or {}).get('applied', False)}`",
        f"- Git ref: `{report['metadata'].get('git_ref') or 'unknown'}`",
        f"- Generated at: `{report['metadata']['generated_at']}`",
        f"- Command: `{report['metadata']['command']}`",
        "",
        "## Summary",
        "",
        f"- Total deltas: `{summary['total_deltas']}`",
        f"- Route classes: `{json.dumps(summary['route_classes'], ensure_ascii=False)}`",
        f"- Apply statuses: `{json.dumps(summary['apply_statuses'], ensure_ascii=False)}`",
        f"- Verify categories: `{json.dumps(summary['verify_categories'], ensure_ascii=False)}`",
        f"- Verify failing categories: `{json.dumps(summary['verify_failing_categories'], ensure_ascii=False)}`",
        f"- Changed: `{summary['changed']}`",
        f"- PR ready: `{summary['pr_ready']}`",
        f"- Review-source changes: `{summary['review_source_changes']}`",
        f"- Source-table suggestions: `{summary['source_table_suggestions']}`",
        "",
        "## Reports",
        "",
    ]
    for label, path in report["reports"].items():
        lines.append(f"- {label}: `{path}`")
    lines.extend(["", "## Next Actions", ""])
    for action in report["next_actions"]:
        lines.append(f"- {action}")

    changes = report.get("review_source_changes") or []
    lines.extend(["", "## Review-Source Changes", ""])
    if not changes:
        lines.append("No review-source changes.")
    else:
        lines.extend(
            [
                "| # | Type | Location | Old | New |",
                "| ---: | --- | --- | --- | --- |",
            ]
        )
        for change in changes:
            location = change.get("location") or {}
            heading = " > ".join(location.get("heading_path") or [])
            location_text = f"{location.get('kind', '-')}:L{location.get('line_no', '-')}"
            if heading:
                location_text = f"{heading} / {location_text}"
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(change.get("index")),
                        _markdown_cell(change.get("change_type")),
                        _markdown_cell(location_text),
                        _markdown_cell(change.get("old_text")),
                        _markdown_cell(change.get("new_text")),
                    ]
                )
                + " |"
            )

    suggestions = report.get("source_table_suggestions") or []
    lines.extend(["", "## Source-Table Suggestions", ""])
    if not suggestions:
        lines.append("No source-table suggestions.")
    else:
        lines.extend(
            [
                "| # | Location | Old | New |",
                "| ---: | --- | --- | --- |",
            ]
        )
        for suggestion in suggestions:
            location = suggestion.get("location") or {}
            heading = " > ".join(location.get("heading_path") or [])
            location_text = f"{location.get('kind', '-')}:L{location.get('line_no', '-')}"
            if heading:
                location_text = f"{heading} / {location_text}"
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(suggestion.get("index")),
                        _markdown_cell(location_text),
                        _markdown_cell(suggestion.get("old_text")),
                        _markdown_cell(suggestion.get("new_text")),
                    ]
                )
                + " |"
            )
    return "\n".join(lines) + "\n"
