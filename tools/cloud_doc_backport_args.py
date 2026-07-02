#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Argparse surface for cloud-doc backport (split from the CLI conductor, G0)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from typing import Any  # noqa: E402
from tools.family_scope import build_family_index  # noqa: E402
from tools.token_resolution_map import build_value_index  # noqa: E402
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




_KNOWN_VALUE_LANGS = ("pt-BR", "en", "fr", "es", "de", "it", "uk", "ja", "zh", "ko", "nl", "pl", "sv")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Feishu cloud-doc backport helpers.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    diff_parser = subparsers.add_parser(
        "diff",
        description="Fetch/read a cloud doc and compare it with a baseline.",
    )
    diff_parser.add_argument("--doc-url", required=True, help="Feishu doc URL or local fixture path")
    diff_parser.add_argument("--baseline", help="baseline markdown/RST file")
    diff_parser.add_argument("--source-path", help="repo source target path; also used as fallback baseline")
    diff_parser.add_argument("--template", help="repo template source path; shortcut for --source-path")
    diff_parser.add_argument("--section-heading", help="heading to compare within both fetched and baseline content")
    diff_parser.add_argument(
        "--no-auto-section",
        action="store_true",
        help="do not infer a section heading from the source target's first heading",
    )
    diff_parser.add_argument("--doc-type", required=True, choices=("review", "template"))
    diff_parser.add_argument("--out", help="output directory for JSON and Markdown reports")
    diff_parser.add_argument("--run-id", default="cloud-doc-backport-local")
    diff_parser.add_argument("--lark-cli", default="lark-cli", help="lark-cli binary for real docs")
    diff_parser.add_argument("--lang", help="value-column lang (e.g. fr) to enable data-origin (Class D) detection")
    diff_parser.add_argument("--data-root", help="phase2 snapshot dir for the token/copy value index (used with --lang)")
    diff_parser.add_argument("--sibling", action="append", default=[], help="sibling target source path for family-scope (R vs T) detection; repeatable")

    apply_parser = subparsers.add_parser(
        "apply-template",
        description="Plan or apply safe template text replacements from a diff report.",
    )
    apply_parser.add_argument("--report", required=True, help="cloud_doc_backport_report.json path")
    apply_parser.add_argument("--source-path", help="optional source template override")
    apply_parser.add_argument("--out", help="output directory for JSON and Markdown apply reports")
    apply_parser.add_argument("--write", action="store_true", help="write safe replacements to the source template")

    apply_review_parser = subparsers.add_parser(
        "apply-review",
        description="Plan or apply safe review text replacements from a diff report.",
    )
    apply_review_parser.add_argument("--report", required=True, help="cloud_doc_backport_report.json path")
    apply_review_parser.add_argument("--source-path", help="optional review source override")
    apply_review_parser.add_argument("--out", help="output directory for JSON and Markdown apply reports")
    apply_review_parser.add_argument("--write", action="store_true", help="write safe replacements to the review source")
    apply_review_parser.add_argument(
        "--allow-rst-baseline",
        action="store_true",
        help="legacy escape hatch: permit --write from a report diffed against the RST source (corrupts markup; prefer run-review-branch)",
    )

    verify_review_parser = subparsers.add_parser(
        "verify-review",
        description="Verify review backport residuals from a diff report against the current review source.",
    )
    verify_review_parser.add_argument("--report", required=True, help="cloud_doc_backport_report.json path")
    verify_review_parser.add_argument("--source-path", help="optional review source override")
    verify_review_parser.add_argument("--out", help="output directory for JSON and Markdown verify reports")

    run_review_parser = subparsers.add_parser(
        "run-review",
        description="Run review cloud-doc diff, guarded apply, and optional residual verify as one workflow.",
    )
    run_review_parser.add_argument("--doc-url", required=True, help="Feishu doc URL or local fixture path")
    run_review_parser.add_argument(
        "--source-path",
        required=True,
        help="docs/_review/... .rst source target; also used as the diff baseline",
    )
    run_review_parser.add_argument("--section-heading", help="heading to compare within fetched and review content")
    run_review_parser.add_argument(
        "--no-auto-section",
        action="store_true",
        help="do not infer a section heading from the review source's first heading",
    )
    run_review_parser.add_argument("--out", help="output directory for all JSON and Markdown reports")
    run_review_parser.add_argument("--run-id", default="cloud-doc-backport-local")
    run_review_parser.add_argument("--lark-cli", default="lark-cli", help="lark-cli binary for real docs")
    run_review_parser.add_argument("--lang", help="value-column lang (e.g. fr) to enable data-origin (Class D) detection")
    run_review_parser.add_argument("--data-root", help="phase2 snapshot dir for the token/copy value index (used with --lang)")
    run_review_parser.add_argument("--sibling", action="append", default=[], help="sibling target source path for family-scope (R vs T) detection; repeatable")
    run_review_parser.add_argument(
        "--write",
        action="store_true",
        help="write safe review replacements, then verify residuals",
    )
    run_review_parser.add_argument(
        "--allow-rst-baseline",
        action="store_true",
        help="legacy escape hatch: permit --write against the RST source (corrupts markup; prefer run-review-branch)",
    )

    open_pr_parser = subparsers.add_parser(
        "open-pr",
        description="Open a draft PR from a PR_READY review backport run manifest.",
    )
    open_pr_parser.add_argument("--manifest", required=True, help="cloud_doc_backport_run.json path")
    open_pr_parser.add_argument("--branch", help="optional PR branch name")
    open_pr_parser.add_argument("--base", default="main", help="base branch; defaults to main")
    open_pr_parser.add_argument("--repo-root", help="repo root override for tests or worktrees")
    open_pr_parser.add_argument("--git-bin", default="git", help="git binary")
    open_pr_parser.add_argument("--gh-bin", default="gh", help="GitHub CLI binary")
    open_pr_parser.add_argument("--json", action="store_true", help="print the PR result as JSON")

    apply_source_table_parser = subparsers.add_parser(
        "apply-source-table",
        description=(
            "Apply HUMAN-APPROVED source-table change requests to Bitable (F6). "
            "Dry-run by default; --write needs --table-binding mappings. Each request "
            "is R9-gated: human approval + exact record_id + content field + idempotent."
        ),
    )
    apply_source_table_parser.add_argument(
        "--report", required=True, help="cloud_doc_backport_source_table_change_request.json path"
    )
    apply_source_table_parser.add_argument(
        "--approve",
        action="append",
        default=[],
        metavar="DELTA_HASH",
        help="a human-approved delta_hash; repeatable. Only these are eligible to write.",
    )
    apply_source_table_parser.add_argument("--out", help="output directory (defaults to the report's directory)")
    apply_source_table_parser.add_argument(
        "--write",
        action="store_true",
        help="actually write approved+resolved requests to Bitable (else dry-run plan only)",
    )
    apply_source_table_parser.add_argument(
        "--table-binding",
        action="append",
        default=[],
        metavar="TABLE=BASE:TABLE_ID",
        help=(
            "writable Feishu binding for a change-request table, e.g. "
            "'Manual_Copy_Source=bascnXXXX:tblYYYY'; repeatable. Required (per table) "
            "with --write. Unmapped tables are skipped safely."
        ),
    )
    apply_source_table_parser.add_argument(
        "--tm-write",
        action="store_true",
        help=(
            "also write approved TRANSLATION suggestions back to the Translation_Memory "
            "(widest blast radius; gated separately from --write). Needs --tm-binding."
        ),
    )
    apply_source_table_parser.add_argument(
        "--tm-binding",
        metavar="BASE:TABLE_ID",
        help="Translation_Memory Feishu binding 'BASE_TOKEN:TABLE_ID'; required with --tm-write",
    )
    apply_source_table_parser.add_argument("--lark-cli", default="lark-cli", help="lark-cli binary for --write")
    apply_source_table_parser.add_argument("--identity", default="bot", help="lark-cli identity for --write")

    resolve_branch_parser = subparsers.add_parser(
        "resolve-review-branch",
        description=(
            "Resolve a Feishu cloud-doc to its in-review branch (Git_ref) + "
            "docs/_review/<model>/<region> path via the Document_link build table. "
            "The review _review tree lives on that branch, not the default branch."
        ),
    )
    resolve_branch_parser.add_argument("--cloud-doc", required=True, help="the edited Feishu cloud-doc URL or doc name (falls back to name -> model+region)")
    resolve_branch_parser.add_argument("--lark-cli", default="lark-cli", help="lark-cli binary")
    resolve_branch_parser.add_argument("--identity", default="bot", help="lark-cli identity (user|bot)")

    run_review_branch_parser = subparsers.add_parser(
        "run-review-branch",
        description=(
            "One-shot branch-targeted backport: resolve the cloud-doc's review branch, "
            "ensure a worktree of it, run-review against its docs/_review file (the "
            "source path is DERIVED, never a template), and optionally push to update "
            "its PR. Dry-run unless --write."
        ),
    )
    run_review_branch_parser.add_argument("--cloud-doc", required=True, help="the edited Feishu cloud-doc URL (used to FETCH the doc content)")
    run_review_branch_parser.add_argument("--doc-name", help="doc name (e.g. manual_je1000f_eu_en_0.8) to resolve the review branch by model+region when the URL is not registered (a 副本/copy)")
    run_review_branch_parser.add_argument("--page", help="a single review page (e.g. 00_preface.rst); omit to diff the WHOLE doc against every docs/_review/<model>/<region>/page/*.rst")
    run_review_branch_parser.add_argument("--write", action="store_true", help="apply edits to the worktree's _review file (else dry-run)")
    run_review_branch_parser.add_argument("--push", action="store_true", help="commit + push the review branch (updates its PR); needs --write")
    run_review_branch_parser.add_argument(
        "--seed",
        action="store_true",
        help="store the current cloud-doc as the render baseline (approach C) instead of diffing — declares the current state as 'already reviewed'. Use only when there are no pending un-backported edits. --push commits it.",
    )
    run_review_branch_parser.add_argument(
        "--reseed",
        action="store_true",
        help="with --seed: overwrite an existing baseline (default refuses to overwrite)",
    )
    run_review_branch_parser.add_argument("--worktrees-root", help="where to create review worktrees (default: ../review-worktrees)")
    run_review_branch_parser.add_argument("--remote", default="origin", help="git remote")
    run_review_branch_parser.add_argument("--git-bin", default="git", help="git binary")
    run_review_branch_parser.add_argument("--full-checkout", action="store_true", help="materialize the whole repo in the worktree (default: sparse, only docs/_review/<model>/<region>)")
    run_review_branch_parser.add_argument("--run-id", default="cloud-doc-backport-branch")
    run_review_branch_parser.add_argument("--out", help="output directory for run-review reports")
    run_review_branch_parser.add_argument("--lark-cli", default="lark-cli", help="lark-cli binary")
    run_review_branch_parser.add_argument("--identity", default="bot", help="lark-cli identity (user|bot)")
    run_review_branch_parser.add_argument(
        "--data-root", default=None,
        help="structured-content snapshot root for the F2 value-index (classifies a delta as Class D / source-bound when its old text matches a source value); defaults to the repo data/phase2 when it holds a synced Spec_Master.csv, else Class D falls back to the heuristic",
    )
    run_review_branch_parser.add_argument(
        "--lang",
        help="value-column lang suffix for the F2 value-index (en/fr/es/de/it/uk/ja/zh/pt-BR); auto-derived from --doc-name when omitted",
    )
    run_review_branch_parser.add_argument(
        "--sibling", action="append", default=[],
        help="explicit family-scope sibling source path (F3 / Class T); repeatable. Overrides the automatic page_shared/<lang> resolution",
    )
    run_review_branch_parser.add_argument(
        "--no-auto-sibling", action="store_true",
        help="disable the automatic page_shared/<lang> family-scope resolution (treat every prose delta as target-local Class R)",
    )

    sync_worktrees_parser = subparsers.add_parser(
        "sync-review-worktrees",
        description="Ensure a git worktree exists for every InReview branch in the build table (so a backport always has its docs/_review tree).",
    )
    sync_worktrees_parser.add_argument("--worktrees-root", help="where to create review worktrees (default: ../review-worktrees)")
    sync_worktrees_parser.add_argument("--remote", default="origin", help="git remote")
    sync_worktrees_parser.add_argument("--git-bin", default="git", help="git binary")
    sync_worktrees_parser.add_argument("--full-checkout", action="store_true", help="materialize the whole repo in each worktree (default: sparse, only docs/_review/<model>/<region>)")
    sync_worktrees_parser.add_argument("--lark-cli", default="lark-cli", help="lark-cli binary")
    sync_worktrees_parser.add_argument("--identity", default="bot", help="lark-cli identity (user|bot)")
    return parser.parse_args(argv)


def _value_index_from_args(args: argparse.Namespace) -> dict[str, Any] | None:
    """Build the token/copy value index when --lang and --data-root are given (F2)."""
    lang = getattr(args, "lang", None)
    data_root = getattr(args, "data_root", None)
    if not lang or not data_root:
        return None
    return build_value_index(Path(data_root), str(lang))

def _family_index_from_args(args: argparse.Namespace) -> dict[str, Any] | None:
    """Build the family-scope index from --sibling source paths (F3).

    A relative sibling path is resolved against the repo root so the index works
    regardless of the invoking CWD (``run-review-branch`` auto-resolves repo-relative
    shared-template paths; the per-page worker runs with cwd=repo root). The original
    (relative) string stays the blast-radius label.
    """
    siblings = getattr(args, "sibling", None) or []
    if not siblings:
        return None
    root = get_paths().root
    resolved = {
        str(path): (Path(path) if Path(path).is_absolute() else root / path)
        for path in siblings
    }
    return build_family_index(resolved)
