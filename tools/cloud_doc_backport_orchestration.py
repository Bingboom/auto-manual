#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Multi-step orchestration for cloud-doc backport: review-branch resolution,
worktree sync, render-baseline diff, sibling scope, and the backport PR
flow (split from the CLI conductor, G0)."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.cloud_doc_backport_args import (  # noqa: E402
    _KNOWN_VALUE_LANGS,
    _family_index_from_args,
    _value_index_from_args,
)
from tools.source_table_sync import (  # noqa: E402
    build_change_request_report,
    load_sidecar_index,
    write_change_request_report,
)
from tools.backport_baseline import baseline_rel_path, load_baseline, store_baseline  # noqa: E402
from tools.review_branch_resolver import (  # noqa: E402
    doc_token,
    list_in_review_branches,
    match_review_branch,
    match_review_branch_by_name,
)
from tools.review_worktree import derive_review_source_rel, ensure_review_worktree  # noqa: E402
from tools.data_snapshot import STRUCTURED_DATA_DEFAULT_DIR  # noqa: E402
from tools.token_resolution_map import (  # noqa: E402
    SPEC_MASTER_FILE,
)
from tools.utils.path_utils import get_paths  # noqa: E402

# Revision-ledger ingest override: unset -> the repo default ledger; a path ->
# that ledger (tests point it at a tmp dir); "off" -> disabled.
REVISION_LEDGER_ENV = "AUTO_MANUAL_REVISION_LEDGER_PATH"


def _ledger_ingest_best_effort(report: dict[str, Any]) -> None:
    """Feed a diff report into the revision ledger without risking the run.

    This is the G1 closed-loop wiring: every review-branch backport round both
    records its deltas and (via the ledger's ingest piggyback semantics)
    settles earlier rounds' pending rows. Observability must never fail the
    backport itself, so every failure degrades to a stderr note.
    """
    target = os.environ.get(REVISION_LEDGER_ENV, "").strip()
    if target.lower() == "off":
        return
    try:
        from tools.revision_ledger import default_ledger_path, ingest_report, reconcile

        ledger_path = Path(target) if target else default_ledger_path()
        ingest_report(report, ledger_path=ledger_path)
        reconcile(ledger_path, root=get_paths().root, auto_merge_meta=True)
    except Exception as exc:  # noqa: BLE001 - ledger is observability, not the job
        print(f"cloud-doc-backport: revision-ledger ingest skipped: {exc}", file=sys.stderr)
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




def _fetch_build_table_records(lark_cli: str, identity: str) -> list[dict[str, Any]]:
    """Fetch the Document_link build table (文档构建表) records via lark-cli."""
    import os

    from tools.sync_data import LarkCliSource

    base = os.environ.get("FEISHU_PHASE2_BASE_TOKEN", "").strip()
    table = os.environ.get("FEISHU_PHASE2_DOCUMENT_LINK_TABLE_ID", "").strip()
    view = os.environ.get("FEISHU_PHASE2_DOCUMENT_LINK_VIEW_ID", "").strip() or None
    if not base or not table:
        raise RuntimeError("FEISHU_PHASE2_BASE_TOKEN + FEISHU_PHASE2_DOCUMENT_LINK_TABLE_ID are required")
    source = LarkCliSource(cli_bin=lark_cli, identity=identity)
    return source.fetch_records_with_ids(base_token=base, table_id=table, view_id=view)

def _default_worktrees_root() -> Path:
    import os

    env = os.environ.get("AUTO_MANUAL_REVIEW_WORKTREES_ROOT", "").strip()
    return Path(env) if env else (get_paths().root.parent / "review-worktrees")

def _run_resolve_review_branch(args: argparse.Namespace) -> int:
    try:
        result = match_review_branch(args.cloud_doc, _fetch_build_table_records(args.lark_cli, args.identity))
    except (OSError, RuntimeError) as exc:
        print(f"cloud-doc-backport: {exc}", file=sys.stderr)
        return 2
    if result is None:
        print(json.dumps({"resolved": False, "cloud_doc": args.cloud_doc}, ensure_ascii=False))
        return 1
    print(json.dumps({"resolved": True, **result}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0

def _run_sync_review_worktrees(args: argparse.Namespace) -> int:
    worktrees_root = Path(args.worktrees_root) if args.worktrees_root else _default_worktrees_root()
    try:
        branches = list_in_review_branches(_fetch_build_table_records(args.lark_cli, args.identity))
    except (OSError, RuntimeError) as exc:
        print(f"cloud-doc-backport: {exc}", file=sys.stderr)
        return 2
    results: list[dict[str, Any]] = []
    for branch in branches:
        try:
            path = ensure_review_worktree(
                branch["git_ref"],
                worktrees_root=worktrees_root,
                repo_root=get_paths().root,
                remote=args.remote,
                git_bin=args.git_bin,
                sparse_paths=None if args.full_checkout else [branch["review_dir"]],
            )
            results.append({**branch, "worktree": path})
            print(f"WORKTREE {branch['git_ref']} -> {path}")
        except (OSError, RuntimeError) as exc:
            results.append({**branch, "error": str(exc)})
            print(f"cloud-doc-backport: worktree for {branch['git_ref']} failed: {exc}", file=sys.stderr)
    print(json.dumps({"in_review": len(branches), "ensured": sum(1 for r in results if "worktree" in r)}, ensure_ascii=False))
    return 0 if branches and all("worktree" in r for r in results) else (0 if not branches else 1)

def _diff_delta_count(page_out: Path) -> int:
    """Real section-matched delta count from a run-review diff report.

    Counts deltas ONLY when the page's section was actually located in the cloud
    doc (``section_selection.applied``). A page whose section is absent falls back
    to a whole-document diff (every block differs) — a false positive in a
    whole-doc backport — so it is reported as 0.
    """
    try:
        payload = json.loads((page_out / "cloud_doc_backport_report.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return 0
    if not (payload.get("section_selection") or {}).get("applied"):
        return 0
    return int((payload.get("summary") or {}).get("total_deltas") or 0)

def _backport_pr_branch(git_ref: str, run_id: str) -> str:
    """Name of the sub-branch that carries backport edits as a PR into the review branch."""
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", f"{git_ref}-{run_id}").strip("-")[:80] or "edits"
    return f"backport/{safe}"

def _lang_from_doc_name(doc_name: str | None) -> str:
    """Best-effort value-column lang from a doc name, e.g. ``manual_je1000f_eu_en_0.8`` -> ``en``."""
    for part in re.split(r"[_\s]+", str(doc_name or "").strip()):
        if part in _KNOWN_VALUE_LANGS:
            return part
    return ""

def _open_backport_pr(
    *, worktree: str, git_ref: str, run_id: str, changed_rels: list[str], git_bin: str, remote: str
) -> tuple[bool, str]:
    """Put the changed ``_review`` pages on a ``backport/`` sub-branch and open a DRAFT
    PR whose base IS the review branch, so the operator verifies before anything lands
    on the review branch. Returns ``(pushed, pr_url)``. The worktree is on the review
    branch on entry and is restored to it on exit."""
    pr_branch = _backport_pr_branch(git_ref, run_id)
    _run_pr_command([git_bin, "switch", "-C", pr_branch], root=Path(worktree))
    try:
        for rel in changed_rels:
            _run_pr_command([git_bin, "add", rel], root=Path(worktree))
        if not _run_pr_command([git_bin, "status", "--porcelain"], root=Path(worktree)).strip():
            return False, ""
        _run_pr_command(
            [git_bin, "commit", "-m", f"backport: review edits for {git_ref} ({run_id})"],
            root=Path(worktree),
        )
        _run_pr_command(
            [git_bin, "push", "--force-with-lease", "-u", remote, pr_branch], root=Path(worktree)
        )
        body = (
            f"Backport of reviewer cloud-doc edits (review-prose / Class R), targeting "
            f"the review branch `{git_ref}`.\n\nChanged pages:\n"
            + "\n".join(f"- `{rel}`" for rel in changed_rels)
            + "\n\nVerify, then merge into the review branch."
        )
        pr_title = f"backport: review edits for {git_ref} ({run_id})"
        try:
            pr_url = _run_pr_command(
                [
                    "gh", "pr", "create", "--base", git_ref, "--head", pr_branch,
                    "--draft", "--title", pr_title,
                    "--body", body,
                ],
                root=Path(worktree),
            ).splitlines()[-1].strip()
        except RuntimeError as exc:
            compare = _compare_url(
                root=Path(worktree),
                base_ref=git_ref,
                head_ref=pr_branch,
                git_bin=git_bin,
                remote=remote,
            )
            print(f"PR_CREATE_FAILED {exc}", file=sys.stderr)
            print(f"COMPARE {compare}", file=sys.stderr)
            print(f"PR_TITLE {pr_title}", file=sys.stderr)
            print("PR_BODY", file=sys.stderr)
            print(body, file=sys.stderr)
            return True, compare
        return True, pr_url
    finally:
        _run_pr_command([git_bin, "switch", git_ref], root=Path(worktree))

def _run_review_branch(args: argparse.Namespace) -> int:
    worktrees_root = Path(args.worktrees_root) if args.worktrees_root else _default_worktrees_root()
    try:
        records = _fetch_build_table_records(args.lark_cli, args.identity)
        doc_name = (getattr(args, "doc_name", None) or "").strip()
        # Resolve by the doc NAME when given (robust for a 副本 whose URL is not in
        # the build table); else by the cloud-doc URL. The fetch always uses --cloud-doc.
        resolved = match_review_branch_by_name(doc_name, records) if doc_name else match_review_branch(args.cloud_doc, records)
        if resolved is None:
            raise RuntimeError(f"no review branch found for cloud-doc {doc_name or args.cloud_doc}")
        git_ref = resolved["git_ref"]
        review_dir = resolved["review_dir"]
        worktree = ensure_review_worktree(
            git_ref,
            worktrees_root=worktrees_root,
            repo_root=get_paths().root,
            remote=args.remote,
            git_bin=args.git_bin,
            sparse_paths=None if args.full_checkout else [review_dir],
        )
        doc_tok = doc_token(args.cloud_doc)
        if args.seed:
            # Store the current cloud-doc as the render baseline (approach C). Used
            # to declare "the current state is already reviewed"; subsequent backports
            # diff against this. Refuses to clobber an existing baseline unless --reseed.
            if not doc_tok:
                raise RuntimeError("--seed needs a resolvable cloud-doc token in --cloud-doc")
            if load_baseline(worktree, review_dir, doc_tok) is not None and not args.reseed:
                raise RuntimeError("a render baseline already exists for this doc; pass --reseed to overwrite")
            baseline_rel = store_baseline(worktree, review_dir, doc_tok, fetch_doc_text(args.cloud_doc, lark_cli=args.lark_cli))
            pushed = False
            if args.push:
                _run_pr_command([args.git_bin, "add", baseline_rel], root=Path(worktree))
                if _run_pr_command([args.git_bin, "status", "--porcelain", baseline_rel], root=Path(worktree)).strip():
                    _run_pr_command([args.git_bin, "commit", "-m", f"backport: seed render baseline for {git_ref}"], root=Path(worktree))
                    _run_pr_command([args.git_bin, "push"], root=Path(worktree))
                    pushed = True
            print(json.dumps(
                {"seeded": True, "git_ref": git_ref, "baseline": baseline_rel, "worktree": worktree, "pushed": pushed},
                ensure_ascii=False, sort_keys=True,
            ))
            return 0
        # Approach C: diff the cloud-doc against a render baseline (render-vs-render →
        # only the reviewer's real edits) instead of the RST-source-vs-rendered per-page
        # diff. Whole-doc only — the baseline is the whole doc, so --page falls through
        # to the legacy per-page path. Two baseline sources, in order of preference:
        #   1. the 基线文档 doc recorded on the build-table row (a frozen copy made at
        #      build time) — fetched and diffed (the copy-doc baseline model);
        #   2. the on-branch .backport/<doc-token>.baseline.md file (the --seed model).
        # F2 (Class D): resolve the snapshot root once — explicit --data-root, else the
        # repo data/phase2 when it holds a synced Spec_Master.csv (the snapshot CSVs are
        # gitignored sync artifacts, so without them Class D degrades to the heuristic).
        # Both the baseline path and the per-page worker read it off args.
        args.data_root = _resolve_backport_data_root(getattr(args, "data_root", None))
        # F3 (Class T): resolve the target language once, then auto-resolve the
        # family-scope siblings (the page_shared/<lang> shared templates) unless the
        # operator passed explicit --sibling or --no-auto-sibling. A reviewer delta that
        # matches a shared-template line is routed Class T (a report-only template-sync
        # proposal) instead of being written as target-local Class R. Both the baseline
        # path and the per-page worker read args.lang / args.sibling.
        if not getattr(args, "lang", None):
            args.lang = _lang_from_doc_name(doc_name)
        explicit_siblings = bool(getattr(args, "sibling", None))
        args.sibling = _resolve_review_branch_siblings(args)
        if args.sibling and not explicit_siblings:
            print(
                f"[backport] F3 family-scope: {len(args.sibling)} shared template(s) "
                f"(page_shared/{args.lang}) — a shared-prose delta routes to Class T "
                f"(template-sync proposal), not the _review write",
                file=sys.stderr,
            )
        baseline_text = None
        # baseline_from_seed marks the on-branch .backport/ seed — a locally advanceable
        # cursor. The copy-doc 基线文档 is a frozen R0 that only advances via a Feishu
        # re-snapshot (operator follow-up), so it is never advanced locally.
        baseline_from_seed = False
        baseline_doc_url = (resolved.get("baseline_doc_url") or "").strip()
        if baseline_doc_url and not args.page:
            baseline_text = fetch_doc_text(baseline_doc_url, lark_cli=args.lark_cli)
        elif doc_tok and not args.page:
            baseline_text = load_baseline(worktree, review_dir, doc_tok)
            baseline_from_seed = baseline_text is not None
        if baseline_text is not None:
            return _run_review_branch_baseline(
                args, resolved=resolved, worktree=worktree,
                review_dir=review_dir, doc_tok=doc_tok, baseline_text=baseline_text,
                baseline_from_seed=baseline_from_seed,
            )
        # Safety guard: a whole-doc run with NO render baseline falls back to the
        # per-page RST-source-vs-rendered diff, which over-reports and whose --write
        # would splatter rendered text across many RST pages (corrupting `.. raw::
        # latex` / line-blocks). Refuse the mass write — seed a baseline so the diff
        # is clean (run-review-branch --seed), or target one page with --page.
        if args.write and not args.page:
            raise RuntimeError(
                "refusing whole-doc --write without a render baseline: the per-page "
                "RST-vs-rendered diff over-reports and writing it corrupts the RST "
                "source. Seed a baseline first (run-review-branch --seed) for a clean "
                "diff, or pass --page <file> to write one targeted page."
            )
        # Pages to backport. With --page: that one. Without: every
        # docs/_review/<model>/<region>/page/*.rst (whole-doc diff — find which pages
        # the cloud-doc changed). The source path is always DERIVED from the resolved
        # review dir (template guard), so a backport can only ever write docs/_review.
        if args.page:
            source_rels = [derive_review_source_rel(review_dir, args.page)]
        else:
            pages = _review_bundle_pages(worktree, review_dir)
            if not pages:
                raise RuntimeError(
                    f"no .rst pages under {review_dir}/page or {review_dir}/<lang>/page "
                    f"on branch {git_ref}"
                )
            bundle_root = Path(worktree) / review_dir
            source_rels = [
                f"{review_dir}/{page.relative_to(bundle_root).as_posix()}" for page in pages
            ]
        run_id = str(args.run_id or "").strip() or "cloud-doc-backport-branch"
        out_dir = Path(args.out) if args.out else _default_out_dir(run_id)
        out_dir.mkdir(parents=True, exist_ok=True)
        # Fetch the cloud-doc ONCE; diff every page against this local fixture so a
        # whole-doc backport does not re-fetch per page.
        fixture = out_dir / "cloud_doc_fetched.md"
        fixture.write_text(fetch_doc_text(args.cloud_doc, lark_cli=args.lark_cli), encoding="utf-8")
    except (OSError, RuntimeError) as exc:
        print(f"cloud-doc-backport: {exc}", file=sys.stderr)
        return 2
    print(f"BRANCH {git_ref}  WORKTREE {worktree}  PAGES {len(source_rels)}")
    changed_rels: list[str] = []
    failed = False
    for source_rel in source_rels:
        source_abs = Path(worktree) / source_rel
        if not source_abs.is_file():
            continue
        page_out = out_dir / Path(source_rel).stem
        review_cmd = [
            sys.executable, str(Path(__file__).resolve()), "run-review",
            "--doc-url", str(fixture), "--source-path", str(source_abs),
            "--run-id", f"{run_id}-{Path(source_rel).stem}", "--out", str(page_out), "--lark-cli", args.lark_cli,
            # Internal per-page worker: the source path is DERIVED from the resolved
            # review dir and the whole-doc no-baseline --write is already refused above
            # (#417), so the RST-baseline guard would be redundant here — bypass it.
            "--allow-rst-baseline",
        ]
        # F2 (Class D) for the per-page worker too: forward the resolved data-root + lang.
        page_lang = (getattr(args, "lang", None) or _lang_from_doc_name(getattr(args, "doc_name", "") or "")).strip()
        if args.data_root and page_lang:
            review_cmd += ["--data-root", args.data_root, "--lang", page_lang]
        # F3 (Class T): forward the auto-resolved (or explicit) family-scope siblings so
        # the per-page worker flags shared-template prose as Class T. Resolved against
        # the worker's cwd (repo root); repeatable.
        for sibling_rel in (getattr(args, "sibling", None) or []):
            review_cmd += ["--sibling", sibling_rel]
        if args.write:
            review_cmd.append("--write")
        proc = subprocess.run(review_cmd, cwd=str(get_paths().root), capture_output=True, text=True)
        if proc.returncode not in (0, 1):  # run-review returns 1 only on a FAIL residual result
            failed = True
            print(f"  ERROR {source_rel} (rc {proc.returncode})", file=sys.stderr)
            continue
        deltas = _diff_delta_count(page_out)
        if deltas > 0:
            changed_rels.append(source_rel)
            print(f"  CHANGED {source_rel}  deltas={deltas}")
    pushed = False
    backport_pr_url = ""
    if args.write and args.push and changed_rels:
        try:
            pushed, backport_pr_url = _open_backport_pr(
                worktree=worktree, git_ref=git_ref, run_id=run_id,
                changed_rels=changed_rels, git_bin=args.git_bin, remote=args.remote,
            )
        except (OSError, RuntimeError) as exc:
            print(f"cloud-doc-backport: backport PR into {git_ref} failed: {exc}", file=sys.stderr)
            return 2
    print(json.dumps(
        {"git_ref": git_ref, "worktree": worktree, "pages": len(source_rels),
         "changed": changed_rels, "wrote": bool(args.write), "pushed": pushed,
         "backport_pr_url": backport_pr_url, "review_branch_pr_url": resolved.get("pr_url")},
        ensure_ascii=False, sort_keys=True,
    ))
    return 1 if failed else 0

def _review_bundle_pages(worktree: str, review_dir: str) -> list[Path]:
    """Every review page of the bundle, covering both bundle layouts.

    Flat families keep pages at ``<review_dir>/page/*.rst``; families with
    ``include_lang_in_output_path`` (us-en, au-en, kr-ko, …) nest them one
    level deeper at ``<review_dir>/<lang>/page/*.rst``. Missing either layout
    is fine — the caller decides whether an empty result is an error.
    """
    bundle_root = Path(worktree) / review_dir
    page_dirs: list[Path] = []
    flat = bundle_root / "page"
    if flat.is_dir():
        page_dirs.append(flat)
    if bundle_root.is_dir():
        for child in sorted(bundle_root.iterdir()):
            if not child.is_dir() or child.name.startswith(".") or child.name == "page":
                continue
            nested = child / "page"
            if nested.is_dir():
                page_dirs.append(nested)
    return [page for page_dir in page_dirs for page in sorted(page_dir.glob("*.rst"))]


def _run_review_branch_baseline(
    args: argparse.Namespace,
    *,
    resolved: dict[str, Any],
    worktree: str,
    review_dir: str,
    doc_tok: str,
    baseline_text: str,
    baseline_from_seed: bool = False,
) -> int:
    """Approach C phase 2: diff the cloud-doc against the stored render baseline.

    Both sides are the Feishu fetch of the doc (the baseline is the render that was
    pushed / last backported), so the diff is render-vs-render and surfaces only the
    reviewer's real edits — not the RST-source-vs-rendered noise of the per-page path.

    The clean deltas are classified (phase 3): the F2 value-index marks a delta whose
    old text matches a source value as ``source_table_suggestion`` (Class D → write
    back to the source table / TM via the approval-gated ``apply-source-table``, NOT
    the RST), the F3 family-index flags shared-template spans, and the rest are
    ``repo_review_text`` (Class R → the ``_review`` RST). With ``--write`` the Class R
    deltas are applied to the matching ``_review`` page via the guarded apply (only
    unique, safe matches) and ``--push`` opens a PR INTO the review branch; Class D is
    never written to the RST.

    Cursor advance (design §5 step 6 / §6): on a **full apply** — every reported delta
    resolved (pure Class R, all uniquely applied; any pending Class D or ambiguous delta
    blocks it so nothing is buried below the cursor) — we advance the **seed** baseline
    (``baseline_from_seed``): rewrite ``.backport/<doc>.baseline.md`` to ``C_now`` and
    commit it with the ``_review`` change, so the next run diffs only NEW edits. The
    frozen copy-doc ``基线文档`` is NOT advanced here — re-snapshotting it is a Feishu
    write (operator follow-up); until then a copy-doc re-run re-reports prior edits
    (idempotent no-ops on apply).
    """
    git_ref = resolved["git_ref"]
    run_id = str(args.run_id or "").strip() or "cloud-doc-backport-branch"
    out_dir = Path(args.out) if args.out else _default_out_dir(run_id)
    # F2 value-index: derive the value-column lang from --lang, else the doc name.
    if not getattr(args, "lang", None):
        args.lang = _lang_from_doc_name(getattr(args, "doc_name", "") or "")
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        c_now = fetch_doc_text(args.cloud_doc, lark_cli=args.lark_cli)
        baseline_rel = baseline_rel_path(review_dir, doc_tok)
        # F2 value-index (Class D / data-origin). Build it once so we can report whether
        # the classifier is deterministic (data synced) or falling back to the heuristic.
        value_index = _value_index_from_args(args)
        f2_data_root = getattr(args, "data_root", None)
        if value_index:
            print(f"F2 value-index: {len(value_index)} value(s) from {f2_data_root} (lang={args.lang}) — Class D is deterministic")
        else:
            print(f"F2 value-index: empty (data-root={f2_data_root or 'none'}, lang={args.lang or 'none'}) — Class D uses the _looks_data_like heuristic; sync data/phase2 for deterministic detection")
        report = build_report(
            run_id=run_id,
            doc_type="review",
            doc_url=args.cloud_doc,
            baseline_path=Path(baseline_rel),
            fetched_text=c_now,
            baseline_text=baseline_text,
            command=["tools/cloud_doc_backport.py", "run-review-branch", "--baseline-diff"],
            source_path=None,
            section_title=None,
            section_inferred_from=None,
            require_section_match=False,
            value_index=value_index,
            family_index=_family_index_from_args(args),
        )
    except (OSError, RuntimeError) as exc:
        print(f"cloud-doc-backport: {exc}", file=sys.stderr)
        return 2
    written = write_reports(report, out_dir)
    _ledger_ingest_best_effort(report)
    # Emit the actionable Class D / Class T artifacts (parity with the per-page run-review
    # worker). The blessed baseline path classifies these deltas but previously wrote only
    # the diff report, so the operator had nothing to feed `apply-source-table` (which reads
    # the change-request report, not the diff report) or the template-sync role.
    artifact_cmd = ["tools/cloud_doc_backport.py", "run-review-branch", "--baseline-diff"]
    write_source_table_suggestions_report(
        build_source_table_suggestions_report(diff_report=report, command=artifact_cmd), out_dir
    )
    proposal_report = build_template_sync_proposal_report(diff_report=report, command=artifact_cmd)
    proposal_written = write_template_sync_proposal_report(proposal_report, out_dir)
    proposal_count = proposal_report["summary"]["proposals"]
    sidecar_index = load_sidecar_index(Path(args.data_root)) if getattr(args, "data_root", None) else None
    change_request_path = write_change_request_report(
        build_change_request_report(report, sidecar_index=sidecar_index), out_dir
    )
    deltas = report["summary"]["total_deltas"]
    route_classes = report["summary"].get("route_classes") or {}
    source_bound = route_classes.get("source_table_suggestion", 0)
    review_bound = route_classes.get("repo_review_text", 0)
    print(f"BRANCH {git_ref}  WORKTREE {worktree}  BASELINE-DIFF deltas={deltas}  routes={json.dumps(route_classes, ensure_ascii=False)}")
    print(f"WROTE {written['json']}")
    print(f"WROTE {written['markdown']}")
    # Class D (source-bound) goes to the source table / TM (F6), NOT the RST. The
    # change-request report (not the diff report) is the apply-source-table input.
    if source_bound:
        print(
            f"ROUTE: {source_bound} source-bound (Class D) delta(s) -> run "
            f"`apply-source-table --report {change_request_path}` (approval-gated F6/TM), NOT the _review RST."
        )
    # Class T (shared across the family) goes to the template-sync role, NOT _review.
    if proposal_count:
        print(
            f"ROUTE: {proposal_count} shared-template (Class T) delta(s) -> review "
            f"{proposal_written['markdown']} and apply via the template-sync role, NOT the _review RST."
        )
    # Class R (review prose): apply the CLEAN deltas to the matching _review page via
    # the guarded apply (only unique, safe matches; ambiguous ones are skipped), then
    # open a PR INTO the review branch. This is the clean write path — it never touches
    # Class D deltas and never writes the per-page RST-vs-rendered garbage.
    changed_rels: list[str] = []
    applied_hashes: set[str] = set()
    baseline_advanced = False
    # R7 rebuild+rediff gate (§5.1 R7): per changed page, the source pre->post change must
    # be EXACTLY the Class R deltas the apply claims it made — no collateral (unexpected),
    # none missing. For an applied delta the guarded apply literally replaces old->new in
    # the source, so the source re-diff equals the expected pairs; anything else is a
    # corrupted apply. A failure blocks the cursor advance and the PR push (the worktree is
    # left for inspection) — so a backport PR is only ever opened from a verified-clean apply.
    all_deltas = report.get("deltas") or []
    gate_pages: list[dict[str, Any]] = []
    gate_passed = True
    if args.write and review_bound:
        bundle_root = Path(worktree) / review_dir
        for page in _review_bundle_pages(worktree, review_dir):
            pre_text = page.read_text(encoding="utf-8") if page.is_file() else ""
            apply_rep = build_review_apply_report(
                report, source_path=page, write=True,
                command=["tools/cloud_doc_backport.py", "run-review-branch", "--baseline-apply"],
            )
            page_applied = {
                str(op["delta_hash"])
                for op in (apply_rep.get("operations") or [])
                if op.get("status") == "applied" and op.get("delta_hash")
            }
            applied_hashes |= page_applied
            if apply_rep["summary"].get("changed"):
                changed_rels.append(f"{review_dir}/{page.relative_to(bundle_root).as_posix()}")
                gate = _rebuild_rediff_gate(
                    baseline_text=pre_text,
                    edited_text=page.read_text(encoding="utf-8"),
                    deltas=[d for d in all_deltas if str(d.get("delta_hash")) in page_applied],
                    run_id=f"{run_id}-{page.stem}",
                )
                gate["page"] = page.name
                gate_pages.append(gate)
                if gate["passed"]:
                    print(f"  APPLIED (Class R) {page.name}  [rebuild+rediff gate OK]")
                else:
                    gate_passed = False
                    print(
                        f"  GATE FAIL {page.name}: the apply changed more than the intended "
                        f"deltas (unexpected={gate['unexpected']} missing={gate['missing']})",
                        file=sys.stderr,
                    )
        if not changed_rels:
            print("NOTE: no review-prose delta matched a _review page uniquely (nothing written; handle manually if needed).")
        # Cursor advance (§6): only on a clean gate AND a FULL apply — every reported delta
        # resolved (len(applied) == deltas). A pending Class D / ambiguous delta leaves
        # applied < deltas, so we keep the baseline put and the next run re-diffs the same
        # window (already-applied edits are idempotent no-ops), never burying anything. A
        # gate failure also holds the cursor (the apply is suspect).
        if gate_passed and deltas > 0 and len(applied_hashes) == deltas:
            if baseline_from_seed:
                store_baseline(worktree, review_dir, doc_tok, c_now)
                changed_rels.append(baseline_rel)
                baseline_advanced = True
                print(f"  ADVANCED seed baseline cursor -> {baseline_rel} (full apply: {deltas} edit(s) resolved)")
            else:
                print(
                    f"NOTE: full apply ({deltas} edit(s)), but the copy-doc 基线文档 baseline is "
                    "frozen — re-snapshot it to advance the cursor (operator follow-up). "
                    "Re-runs re-report (idempotent)."
                )
    pushed = False
    backport_pr_url = ""
    if args.write and args.push and changed_rels and not gate_passed:
        print(
            "cloud-doc-backport: rebuild+rediff gate FAILED — refusing to push the backport "
            "PR (the apply changed more than the intended Class R deltas). Inspect the worktree.",
            file=sys.stderr,
        )
    elif args.write and args.push and changed_rels:
        try:
            pushed, backport_pr_url = _open_backport_pr(
                worktree=worktree, git_ref=git_ref, run_id=run_id,
                changed_rels=changed_rels, git_bin=args.git_bin, remote=args.remote,
            )
        except (OSError, RuntimeError) as exc:
            print(f"cloud-doc-backport: backport PR into {git_ref} failed: {exc}", file=sys.stderr)
            return 2
    print(json.dumps(
        {"git_ref": git_ref, "worktree": worktree, "mode": "baseline-diff",
         "baseline": baseline_rel, "deltas": deltas, "result": report["result"],
         "route_classes": route_classes, "report": str(written["json"]),
         "source_table_change_request": str(change_request_path),
         "template_sync_proposal": str(proposal_written["json"]),
         "template_sync_proposals": proposal_count,
         "changed": changed_rels,
         "wrote": bool(args.write), "pushed": pushed, "backport_pr_url": backport_pr_url,
         "baseline_advanced": baseline_advanced,
         "rebuild_rediff": {"passed": gate_passed, "pages": gate_pages},
         "review_branch_pr_url": resolved.get("pr_url")},
        ensure_ascii=False, sort_keys=True,
    ))
    return 0 if gate_passed else 1

def _auto_sibling_rels(lang: str) -> list[str]:
    """Auto-resolve family-scope siblings (F3 / Class T) for ``run-review-branch``.

    The cross-region shared-prose surface is ``docs/templates/page_shared/<lang>/``:
    the manifests assemble each page from it plus the per-region ``page_<region>-<lang>``
    templates. A reviewer's old span that matches a line in a shared template is
    family-shared content (routed Class ``T`` → template-sync proposal, with that
    shared template as the blast radius), so it is withheld from the target-local
    ``_review`` write; a span that only exists in the region template stays Class ``R``.
    Region-specific templates and other languages are deliberately NOT indexed — they
    would over-flag or never text-match. Single-region languages (``ja``/``zh``) have no
    ``page_shared`` directory, so they correctly resolve to no siblings (no Class ``T``).

    Read from the repo root: ``docs/templates`` is absent from the sparse review
    worktree and is branch-stable. Returns repo-relative paths (clean blast-radius
    labels); ``_family_index_from_args`` resolves them against the root.
    """
    lang = (lang or "").strip()
    if not lang:
        return []
    root = get_paths().root
    shared_dir = get_paths().templates_dir / "page_shared" / lang
    if not shared_dir.is_dir():
        return []
    return [path.relative_to(root).as_posix() for path in sorted(shared_dir.glob("*.rst"))]

def _resolve_review_branch_siblings(args: argparse.Namespace) -> list[str]:
    """Effective F3 family-scope siblings for ``run-review-branch``.

    Explicit ``--sibling`` wins; ``--no-auto-sibling`` disables detection (every prose
    delta stays target-local Class ``R``); otherwise auto-resolve the
    ``page_shared/<lang>`` shared templates (empty when the language is unknown or
    single-region).
    """
    explicit = getattr(args, "sibling", None) or []
    if explicit:
        return list(explicit)
    if getattr(args, "no_auto_sibling", False):
        return []
    return _auto_sibling_rels((getattr(args, "lang", None) or "").strip())

def _resolve_backport_data_root(explicit: str | None) -> str | None:
    """Effective F2 snapshot dir for run-review-branch (Class D / data-origin detection).

    Use the explicit ``--data-root`` when given, else default to the repo's
    ``data/phase2`` **only when it actually holds a synced ``Spec_Master.csv``**. The
    snapshot CSVs are gitignored ``sync-data`` artifacts, so a fresh clone / CI has none
    — there we return ``None`` and Class D falls back to the ``_looks_data_like``
    heuristic (the prior behavior). When the operator has synced the data, Class D
    becomes deterministic with no extra flag.
    """
    if explicit:
        return explicit
    default = get_paths().root / STRUCTURED_DATA_DEFAULT_DIR
    return str(default) if (default / SPEC_MASTER_FILE).exists() else None

