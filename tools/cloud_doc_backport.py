#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Feishu cloud document backport helpers.

The diff command fetches/reads a Feishu cloud document, normalizes it, compares
it with a baseline, and writes structured JSON + Markdown diff reports.

The apply-template/apply-review commands can turn a diff report into guarded
local source edits. They never edit generated output or Feishu bitable rows.

Review writes funnel through ``run-review-branch`` (render-vs-render diff against a
stored baseline). A direct ``apply-review`` / ``run-review --write`` against the
``_review`` RST *source* is refused (it corrupts RST markup; see
``Backport_Rendered_Baseline_Design.md`` §1) unless ``--allow-rst-baseline`` is set.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
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
from tools.source_table_sync import build_change_request_report  # noqa: E402,F401
from tools.cloud_doc_backport_cli import (  # noqa: E402,F401
    _auto_sibling_rels,
    _backport_pr_branch,
    _default_worktrees_root,
    _diff_delta_count,
    _family_index_from_args,
    _fetch_build_table_records,
    _lang_from_doc_name,
    _open_backport_pr,
    _parse_args,
    _resolve_backport_data_root,
    _resolve_review_branch_siblings,
    _run_apply,
    _run_apply_review,
    _run_apply_source_table,
    _run_apply_template,
    _run_diff,
    _run_open_pr,
    _run_resolve_review_branch,
    _run_review,
    _run_review_branch,
    _run_review_branch_baseline,
    _run_sync_review_worktrees,
    _run_verify_review,
    _value_index_from_args,
    main,
)


if __name__ == "__main__":
    raise SystemExit(main())
