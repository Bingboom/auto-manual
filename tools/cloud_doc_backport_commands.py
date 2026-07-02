#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Single-command runners for cloud-doc backport: diff / apply-* / review /
verify-review / open-pr (split from the CLI conductor, G0)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.cloud_doc_backport_args import (  # noqa: E402
    _family_index_from_args,
    _value_index_from_args,
)
from tools.source_table_sync import (  # noqa: E402
    apply_change_requests,
    build_change_request_report,
    load_change_requests,
    load_sidecar_index,
    load_translation_suggestions,
    write_change_request_report,
    write_source_table_apply_report,
)
from tools.translation_memory_sync import apply_translation_suggestions  # noqa: E402
from tools.utils.path_utils import get_paths  # noqa: E402
from tools.cloud_doc_backport_pr import (  # noqa: E402,F401
    _compare_url,
    _default_backport_branch_name,
    _default_out_dir,
    _github_web_url,
    _parse_git_status_paths,
    _pr_body_from_manifest,
    _repo_relative,
    _resolve_existing_path,
    _run_pr_command,
    _safe_branch_segment,
    _validate_open_pr_manifest,
    open_backport_pr_from_manifest,
)
from tools.cloud_doc_backport_reports import (  # noqa: E402,F401
    _attach_source_evidence,
    _display_report_paths,
    _operator_locator,
    _rebuild_rediff_for_report,
    _rebuild_rediff_gate,
    _repo_text_changes_from_diff,
    _resolve_baseline_text,
    _resolve_report_source,
    _selection_payload,
    _source_kind_for_path,
    _source_table_routing_hint,
    _source_table_suggestions_from_diff,
    _source_target_payload,
    _suggestion_heading_text,
    _template_sync_proposals_from_diff,
    _verify_delta,
    build_report,
    build_review_run_report,
    build_review_verify_report,
    build_source_table_suggestions_report,
    build_template_sync_proposal_report,
    write_apply_report,
    write_reports,
    write_review_run_report,
    write_source_table_suggestions_report,
    write_template_sync_proposal_report,
    write_verify_report,
)
from tools.cloud_doc_backport_apply import (  # noqa: E402,F401
    _REVIEW_MARKUP_ROLE_RE,
    _apply_operation,
    _apply_review_block_operation,
    _apply_skip_reason,
    _heading_text_key,
    _match_review_block,
    _minimal_diff_rewrite,
    _refuse_unsafe_review_apply,
    _review_block_is_plain,
    _review_block_span,
    _rewrite_review_block,
    _rst_display_width,
    build_guarded_apply_report,
    build_review_apply_report,
    build_template_apply_report,
)
from tools.cloud_doc_backport_util import (  # noqa: E402,F401
    APPLY_SCHEMA_VERSION,
    NORMALIZER_VERSION,
    REPORT_SCHEMA_VERSION,
    RUN_SCHEMA_VERSION,
    SOURCE_TABLE_SUGGESTIONS_SCHEMA_VERSION,
    TEMPLATE_SYNC_PROPOSAL_SCHEMA_VERSION,
    VERIFY_SCHEMA_VERSION,
    _counter_dict,
    _git_ref,
    _load_json_file,
    _resolve_repo_file,
    _resolve_source_path,
    _utc_now,
    _validate_apply_source,
)
from tools.cloud_doc_backport_routing import (  # noqa: E402,F401
    DELTA_SCHEMA_VERSION,
    _BUTTON_TERMS,
    _OUTPUT_TERMS,
    _PLACEHOLDER_RE,
    _UNIT_VALUE_RE,
    _classify_route,
    _contains_any_term,
    _delta_hash,
    _is_image_asset_delta,
    _looks_data_like,
    _make_delta,
    _semantic_review_flags,
    _without_image_placeholders,
    diff_blocks,
)
from tools.cloud_doc_backport_model import (  # noqa: E402,F401
    Block,
    SectionSelection,
    _DOCUMENT_PREAMBLE_LABEL,
    _DOCUMENT_PREAMBLE_SECTION,
    _FEISHU_TEXT_TAG_RE,
    _HEADING_RE,
    _HTML_COMMENT_RE,
    _IMAGE_SENTINELS,
    _LARK_TAG_RE,
    _LIST_RE,
    _RST_HEADING_CHARS,
    _RST_HEADING_UNDERLINE_RE,
    _SAFE_PATH_CHARS,
    _TABLE_SEPARATOR_RE,
    _TITLE_TAG_RE,
    _apply_section_selection,
    _auto_section_for_source,
    _context,
    _display_path,
    _extract_doc_markdown,
    _heading_title,
    _is_document_preamble_section,
    _local_doc_path,
    _location,
    _normalize_inline,
    _preprocessed_lines,
    _read_text,
    _report_path_text,
    _rst_heading_level,
    _safe_path_token,
    _section_key,
    _source_path_prefers_document_preamble,
    _strip_document_title,
    _strip_lark_noise,
    _table_separator,
    _unwrap_markdown_link,
    fetch_doc_text,
    first_heading_title,
    parse_blocks,
    select_document_preamble_blocks,
    select_section_blocks,
)
from tools.cloud_doc_backport_transports import (  # noqa: E402,F401
    _parse_table_bindings,
    _source_table_transport,
    _tm_transport,
)
from tools.cloud_doc_backport_render import (  # noqa: E402,F401
    _markdown_cell,
    markdown_report,
    markdown_apply_report,
    markdown_verify_report,
    markdown_source_table_suggestions_report,
    markdown_template_sync_proposal_report,
    markdown_review_run_report,
)




def _run_diff(args: argparse.Namespace, raw_argv: list[str]) -> int:
    run_id = str(args.run_id or "").strip() or "cloud-doc-backport-local"
    out_dir = Path(args.out) if args.out else _default_out_dir(run_id)
    try:
        if args.template and args.source_path:
            raise RuntimeError("--template and --source-path are mutually exclusive")
        if args.template and args.doc_type != "template":
            raise RuntimeError("--template requires --doc-type template")
        source_path = _resolve_existing_path(args.template or args.source_path, label="source target")
        baseline_path = _resolve_existing_path(args.baseline, label="baseline")
        if baseline_path is None:
            baseline_path = source_path
        if baseline_path is None:
            raise RuntimeError("--baseline is required unless --template or --source-path is supplied")
        baseline_text = _read_text(baseline_path)
        fetched_text = fetch_doc_text(args.doc_url, lark_cli=args.lark_cli)
        section_title = str(args.section_heading or "").strip() or None
        section_inferred_from = None
        if section_title is None and source_path is not None and not args.no_auto_section:
            section_title, section_inferred_from = _auto_section_for_source(source_path, _read_text(source_path))
    except (OSError, RuntimeError) as exc:
        print(f"cloud-doc-backport: {exc}", file=sys.stderr)
        return 2
    try:
        report = build_report(
            run_id=run_id,
            doc_type=args.doc_type,
            doc_url=args.doc_url,
            baseline_path=_display_path(baseline_path),
            fetched_text=fetched_text,
            baseline_text=baseline_text,
            command=["tools/cloud_doc_backport.py", *raw_argv],
            source_path=_display_path(source_path) if source_path else None,
            section_title=section_title,
            section_inferred_from=section_inferred_from,
            require_section_match=bool(args.section_heading),
            value_index=_value_index_from_args(args),
            family_index=_family_index_from_args(args),
        )
    except RuntimeError as exc:
        print(f"cloud-doc-backport: {exc}", file=sys.stderr)
        return 2
    written = write_reports(report, out_dir)
    print(f"WROTE {written['json']}")
    print(f"WROTE {written['markdown']}")
    return 0

def _run_apply(
    args: argparse.Namespace,
    raw_argv: list[str],
    *,
    build_apply_report: Any,
) -> int:
    try:
        report_path = _resolve_source_path(args.report, label="diff report")
        source_override = _resolve_source_path(args.source_path, label="source target") if args.source_path else None
        diff_report = _load_json_file(report_path)
        _refuse_unsafe_review_apply(
            diff_report,
            write=bool(args.write),
            allow_rst_baseline=getattr(args, "allow_rst_baseline", False),
        )
        apply_report = build_apply_report(
            diff_report,
            source_path=source_override,
            write=bool(args.write),
            command=["tools/cloud_doc_backport.py", *raw_argv],
        )
    except (OSError, RuntimeError) as exc:
        print(f"cloud-doc-backport: {exc}", file=sys.stderr)
        return 2
    out_dir = Path(args.out) if args.out else report_path.parent
    written = write_apply_report(apply_report, out_dir)
    print(f"WROTE {written['json']}")
    print(f"WROTE {written['markdown']}")
    if args.write and apply_report["summary"]["changed"]:
        print(f"UPDATED {apply_report['source_target']['path']}")
    return 0

def _run_apply_template(args: argparse.Namespace, raw_argv: list[str]) -> int:
    return _run_apply(args, raw_argv, build_apply_report=build_template_apply_report)

def _run_apply_review(args: argparse.Namespace, raw_argv: list[str]) -> int:
    return _run_apply(args, raw_argv, build_apply_report=build_review_apply_report)

def _run_verify_review(args: argparse.Namespace, raw_argv: list[str]) -> int:
    try:
        report_path = _resolve_source_path(args.report, label="diff report")
        source_override = _resolve_source_path(args.source_path, label="source target") if args.source_path else None
        diff_report = _load_json_file(report_path)
        verify_report = build_review_verify_report(
            diff_report,
            source_path=source_override,
            command=["tools/cloud_doc_backport.py", *raw_argv],
        )
    except (OSError, RuntimeError) as exc:
        print(f"cloud-doc-backport: {exc}", file=sys.stderr)
        return 2
    out_dir = Path(args.out) if args.out else report_path.parent
    written = write_verify_report(verify_report, out_dir)
    suggestions_report = build_source_table_suggestions_report(
        diff_report=diff_report,
        verify_report=verify_report,
        command=["tools/cloud_doc_backport.py", *raw_argv],
    )
    suggestions_written = write_source_table_suggestions_report(suggestions_report, out_dir)
    proposal_report = build_template_sync_proposal_report(
        diff_report=diff_report,
        command=["tools/cloud_doc_backport.py", *raw_argv],
    )
    proposal_written = write_template_sync_proposal_report(proposal_report, out_dir)
    print(f"WROTE {written['json']}")
    print(f"WROTE {written['markdown']}")
    print(f"WROTE {suggestions_written['json']}")
    print(f"WROTE {suggestions_written['markdown']}")
    print(f"WROTE {proposal_written['json']}")
    print(f"WROTE {proposal_written['markdown']}")
    return 0 if verify_report["result"] == "PASS" else 1

def _run_review(args: argparse.Namespace, raw_argv: list[str]) -> int:
    run_id = str(args.run_id or "").strip() or "cloud-doc-backport-local"
    out_dir = Path(args.out) if args.out else _default_out_dir(run_id)
    command = ["tools/cloud_doc_backport.py", *raw_argv]
    try:
        source_path = _resolve_source_path(args.source_path, label="source target")
        _validate_apply_source(source_path, kind="review")
        baseline_text = _read_text(source_path)
        fetched_text = fetch_doc_text(args.doc_url, lark_cli=args.lark_cli)
        section_title = str(args.section_heading or "").strip() or None
        section_inferred_from = None
        if section_title is None and not args.no_auto_section:
            section_title, section_inferred_from = _auto_section_for_source(source_path, baseline_text)
        diff_report = build_report(
            run_id=run_id,
            doc_type="review",
            doc_url=args.doc_url,
            baseline_path=_display_path(source_path),
            fetched_text=fetched_text,
            baseline_text=baseline_text,
            command=command,
            source_path=_display_path(source_path),
            section_title=section_title,
            section_inferred_from=section_inferred_from,
            require_section_match=bool(args.section_heading),
            value_index=_value_index_from_args(args),
            family_index=_family_index_from_args(args),
        )
        _refuse_unsafe_review_apply(
            diff_report,
            write=bool(args.write),
            allow_rst_baseline=getattr(args, "allow_rst_baseline", False),
        )
        output_paths = {f"diff_{key}": value for key, value in write_reports(diff_report, out_dir).items()}
        apply_report: dict[str, Any] | None = None
        verify_report: dict[str, Any] | None = None
        if diff_report["summary"]["total_deltas"]:
            apply_report = build_review_apply_report(
                diff_report,
                source_path=source_path,
                write=bool(args.write),
                command=command,
            )
            output_paths.update(
                {f"apply_{key}": value for key, value in write_apply_report(apply_report, out_dir).items()}
            )
            if args.write:
                verify_report = build_review_verify_report(
                    diff_report,
                    source_path=source_path,
                    command=command,
                    # The pre-edit source, captured before the in-place apply above — lets
                    # the rebuild+rediff gate (R7) run instead of skipping when the report's
                    # baseline is the in-place review source (the common run-review case).
                    baseline_text=baseline_text,
                )
                output_paths.update(
                    {f"verify_{key}": value for key, value in write_verify_report(verify_report, out_dir).items()}
                )
        suggestions_report = build_source_table_suggestions_report(
            diff_report=diff_report,
            verify_report=verify_report,
            command=command,
        )
        output_paths.update(
            {
                f"source_table_suggestions_{key}": value
                for key, value in write_source_table_suggestions_report(suggestions_report, out_dir).items()
            }
        )
        proposal_report = build_template_sync_proposal_report(diff_report=diff_report, command=command)
        output_paths.update(
            {
                f"template_sync_proposal_{key}": value
                for key, value in write_template_sync_proposal_report(proposal_report, out_dir).items()
            }
        )
        sidecar_index = load_sidecar_index(Path(args.data_root)) if getattr(args, "data_root", None) else None
        change_request_report = build_change_request_report(diff_report, sidecar_index=sidecar_index)
        output_paths["source_table_change_request_json"] = write_change_request_report(
            change_request_report, out_dir
        )
        run_report = build_review_run_report(
            diff_report,
            apply_report=apply_report,
            verify_report=verify_report,
            write=bool(args.write),
            output_paths=output_paths,
            command=command,
        )
    except (OSError, RuntimeError) as exc:
        print(f"cloud-doc-backport: {exc}", file=sys.stderr)
        return 2

    run_written = write_review_run_report(run_report, out_dir)
    output_paths.update({f"run_{key}": value for key, value in run_written.items()})
    for label, path in sorted(output_paths.items()):
        print(f"WROTE {path}")
    if args.write and apply_report and apply_report["summary"]["changed"]:
        print(f"UPDATED {apply_report['source_target']['path']}")
    return 1 if run_report["result"] == "FAIL" else 0

def _run_open_pr(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root) if args.repo_root else get_paths().root
    try:
        result = open_backport_pr_from_manifest(
            manifest_path=Path(args.manifest),
            repo_root=repo_root,
            branch_name=str(args.branch or "").strip() or None,
            base_ref=str(args.base or "main").strip() or "main",
            git_bin=str(args.git_bin or "git").strip() or "git",
            gh_bin=str(args.gh_bin or "gh").strip() or "gh",
        )
    except (OSError, RuntimeError) as exc:
        print(f"cloud-doc-backport: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    elif result.get("result") == "PR_CREATE_FAILED":
        print(f"PR_CREATE_FAILED {result.get('pr_create_error') or '-'}")
        print(f"COMPARE {result.get('compare_url') or '-'}")
        print(f"BRANCH {result['branch']}")
        print(f"COMMIT {result['commit']}")
        print("PR_TITLE")
        print(result.get("pr_title") or "")
        print("PR_BODY")
        print(result.get("pr_body") or "")
    else:
        print(f"PR {result['pr_url']}")
        print(f"BRANCH {result['branch']}")
        print(f"COMMIT {result['commit']}")
    return 0 if result.get("result") == "PR_OPENED" else 1

def _run_apply_source_table(args: argparse.Namespace, raw_argv: list[str]) -> int:
    try:
        report_path = _resolve_source_path(args.report, label="change-request report")
        change_requests, run_id = load_change_requests(report_path)
        approved = {h for h in (args.approve or []) if h}
        transport = None
        if args.write:
            bindings = _parse_table_bindings(args.table_binding or [])
            if not bindings:
                raise RuntimeError("--write requires at least one --table-binding TABLE=BASE:TABLE_ID")
            transport = _source_table_transport(bindings, lark_cli=args.lark_cli, identity=args.identity)
        apply_result = apply_change_requests(
            change_requests,
            approved_hashes=approved,
            transport=transport,
            write=bool(args.write),
        )
        # Translation copy edits abstain at the source boundary; their home is the
        # Translation_Memory. Apply approved ones there, gated SEPARATELY (--tm-write
        # + --tm-binding) since TM is the widest-blast-radius write.
        translation_suggestions = load_translation_suggestions(report_path)
        tm_transport = None
        if args.tm_write:
            if not args.tm_binding:
                raise RuntimeError("--tm-write requires --tm-binding BASE:TABLE_ID")
            tm_transport = _tm_transport(args.tm_binding, lark_cli=args.lark_cli, identity=args.identity)
        tm_apply_result = apply_translation_suggestions(
            translation_suggestions,
            approved_hashes=approved,
            transport=tm_transport,
            write=bool(args.tm_write),
        )
    except (OSError, RuntimeError) as exc:
        print(f"cloud-doc-backport: {exc}", file=sys.stderr)
        return 2
    report = {
        **apply_result,
        "run_id": run_id,
        "approved_count": len(approved),
        "translation_apply": tm_apply_result,
        "command": ["tools/cloud_doc_backport.py", *raw_argv],
    }
    out_dir = Path(args.out) if args.out else report_path.parent
    written = write_source_table_apply_report(report, out_dir)
    print(f"WROTE {written['json']}")
    print(f"WROTE {written['markdown']}")
    summary = report.get("summary") or {}
    tm_summary = tm_apply_result.get("summary") or {}
    print(
        f"APPLY plan: apply {summary.get('apply', 0)} skip {summary.get('skip', 0)} "
        f"| written {summary.get('written', 0)} verify_failed {summary.get('verify_failed', 0)} "
        f"error {summary.get('error', 0)} ({'WRITE' if report.get('external_write') else 'dry-run'})"
    )
    print(
        f"TM plan: apply {tm_summary.get('apply', 0)} skip {tm_summary.get('skip', 0)} "
        f"| written {tm_summary.get('written', 0)} already {tm_summary.get('already', 0)} "
        f"verify_failed {tm_summary.get('verify_failed', 0)} error {tm_summary.get('error', 0)} "
        f"({'WRITE' if tm_apply_result.get('external_write') else 'dry-run'})"
    )
    wrote_with_failures = (report.get("external_write") and (summary.get("verify_failed") or summary.get("error"))) or (
        tm_apply_result.get("external_write") and (tm_summary.get("verify_failed") or tm_summary.get("error"))
    )
    return 1 if wrote_with_failures else 0

