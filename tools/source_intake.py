#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Source document intake helpers.

MVP scope: read a structured Markdown/Feishu document, extract source-table
candidates, and optionally emit approval-gated source-table change requests for
existing rows. Live writes remain owned by ``tools/cloud_doc_backport.py
apply-source-table`` / ``tools.source_table_sync``.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root


ROOT = bootstrap_repo_root(__file__, parent_count=1)

from tools.source_intake_extract import read_input_text  # noqa: E402
from tools.source_intake_closure import (  # noqa: E402
    build_apply_report,
    build_approval_report,
    build_closure_report,
    run_check_commands,
    write_apply_report,
    write_approval_report,
    write_closure_report,
)
from tools.source_intake_runtime import (  # noqa: E402
    enrich_candidates_with_snapshot,
    extract_candidates_from_text,
    write_intake_outputs,
)
from tools.utils.path_utils import get_paths  # noqa: E402


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert source specs/manual tables into reviewable source-table candidates.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser(
        "run",
        description=(
            "Extract candidates and, when --data-root is provided, emit source-table "
            "change requests for existing-row updates."
        ),
    )
    run.add_argument("--input", required=True, help="Markdown file, stdin '-', or Feishu/Lark doc URL")
    run.add_argument("--document-key", required=True, help="Target document key, e.g. JE-2000F_EU")
    run.add_argument("--source-lang", default="en", help="Source language code; default: en")
    run.add_argument("--version", default="", help="Optional source version carried onto candidates")
    run.add_argument("--data-root", help="Optional phase2 snapshot root used to classify create/update/noop")
    run.add_argument("--out", help="Output directory; defaults to reports/source_intake/<run-id>")
    run.add_argument("--run-id", default="source-intake-local", help="Stable run id for report paths")
    run.add_argument("--lark-cli", default="lark-cli", help="lark-cli binary when --input is a cloud doc")

    approve = subparsers.add_parser(
        "approve",
        description="Create a human-review approval artifact from a source-table change-request report.",
    )
    approve.add_argument("--report", required=True, help="source_intake_source_table_change_request.json")
    approve.add_argument("--approve", action="append", default=[], help="Human-approved delta_hash; repeatable")
    approve.add_argument(
        "--approve-all-resolved",
        action="store_true",
        help="Approve every resolved change request in the report",
    )
    approve.add_argument("--reviewer", default="", help="Reviewer/operator name recorded in the approval artifact")
    approve.add_argument("--out", help="Output directory; defaults to the change-request report directory")

    apply = subparsers.add_parser(
        "apply",
        description=(
            "Apply approved source-table requests through the existing approval-gated writer. "
            "Dry-run by default; add --write for live Feishu writes."
        ),
    )
    apply.add_argument("--report", required=True, help="source_intake_source_table_change_request.json")
    apply.add_argument("--approval", help="source_intake_approval.json")
    apply.add_argument("--approve", action="append", default=[], help="Additional human-approved delta_hash; repeatable")
    apply.add_argument("--out", help="Output directory; defaults to the change-request report directory")
    apply.add_argument("--write", action="store_true", help="Actually write approved+resolved requests to Feishu")
    apply.add_argument(
        "--table-binding",
        action="append",
        default=[],
        help="Writable table binding TABLE=BASE:TABLE_ID; repeatable and required with --write",
    )
    apply.add_argument("--lark-cli", default="lark-cli", help="lark-cli binary for --write")
    apply.add_argument("--identity", default="bot", help="lark-cli identity for --write; default: bot")

    verify = subparsers.add_parser(
        "verify",
        description="Run sync/build/review/backport checks and write a P4-P7 closure report.",
    )
    verify.add_argument("--candidates", required=True, help="source_intake_candidates.json")
    verify.add_argument("--change-request", required=True, help="source_intake_source_table_change_request.json")
    verify.add_argument("--approval", required=True, help="source_intake_approval.json")
    verify.add_argument("--apply-report", required=True, help="source_intake_apply.json")
    verify.add_argument(
        "--check-command",
        action="append",
        default=[],
        help=(
            "Verification command as LABEL=COMMAND; repeat for sync-data and build/review/backport, "
            "for example sync-data='python build.py sync-data ...'"
        ),
    )
    verify.add_argument(
        "--require-write",
        action="store_true",
        help="Require source_intake_apply.json to prove live writes, not only a dry-run apply plan",
    )
    verify.add_argument("--cwd", help="Working directory for --check-command; defaults to repo root")
    verify.add_argument("--out", help="Output directory; defaults to the candidates report directory")

    spec = subparsers.add_parser(
        "spec-extract",
        description=(
            "Extract structured candidates from a 产品规格书 (PDF/Markdown/cloud-doc) via the "
            "field-mapping rule library, with region-aware unit transforms. Optional pre-ingest "
            "completeness gate against a reference target (same product's sibling)."
        ),
    )
    spec.add_argument("--input", required=True, help="spec sheet: PDF/Markdown file, stdin '-', or cloud-doc URL")
    spec.add_argument("--rules", required=True, help="rule-library JSON (list of field-mapping rule dicts)")
    spec.add_argument("--document-key", required=True, help="Target document key, e.g. JE-2000E_JP")
    spec.add_argument("--region", default="US", help="US -> dual imperial/metric units; otherwise metric")
    spec.add_argument("--source-lang", default="en", help="Source language code; default: en")
    spec.add_argument("--reference", help="reference rows JSON (sibling target) for the completeness gate")
    spec.add_argument("--out", help="Output directory; defaults to reports/source_intake/<document-key>")
    spec.add_argument("--lark-cli", default="lark-cli", help="lark-cli binary when --input is a cloud doc")
    return parser


def _default_out_dir(run_id: str) -> Path:
    safe = "".join(ch if ch.isalnum() or ch in "._-" else "-" for ch in run_id).strip(".-")
    return get_paths().source_intake_reports_dir / (safe or "source-intake-local")


def _run(args: argparse.Namespace) -> int:
    data_root = Path(args.data_root).resolve() if args.data_root else None
    out_dir = Path(args.out).resolve() if args.out else _default_out_dir(str(args.run_id or "source-intake-local"))
    try:
        text = read_input_text(args.input, lark_cli=args.lark_cli)
        candidates = extract_candidates_from_text(
            text,
            document_key=str(args.document_key or "").strip(),
            source_lang=str(args.source_lang or "en").strip() or "en",
            version=str(args.version or "").strip(),
        )
        if data_root is not None:
            candidates = enrich_candidates_with_snapshot(candidates, data_root=data_root)
        paths = write_intake_outputs(
            out_dir=out_dir,
            candidates=candidates,
            run_id=str(args.run_id or "source-intake-local"),
            source=str(args.input),
            document_key=str(args.document_key),
            data_root=data_root,
        )
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"source-intake: {exc}", file=sys.stderr)
        return 2

    for label, path in sorted(paths.items()):
        print(f"WROTE {label} {path}")
    print(f"CANDIDATES {len(candidates)}")
    return 0


def _approval(args: argparse.Namespace) -> int:
    report_path = Path(args.report).resolve()
    out_dir = Path(args.out).resolve() if args.out else report_path.parent
    try:
        import json

        change_report = json.loads(report_path.read_text(encoding="utf-8"))
        approval = build_approval_report(
            change_report,
            approved_hashes=args.approve or [],
            approve_all_resolved=bool(args.approve_all_resolved),
            reviewer=str(args.reviewer or ""),
        )
        paths = write_approval_report(approval, out_dir)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"source-intake: {exc}", file=sys.stderr)
        return 2
    for label, path in sorted(paths.items()):
        print(f"WROTE {label} {path}")
    summary = approval.get("summary") or {}
    print(
        f"APPROVED {summary.get('approved_hashes', 0)} "
        f"UNKNOWN {summary.get('unknown_hashes', 0)} "
        f"BLOCKED {summary.get('blocked_approved_requests', 0)}"
    )
    return 1 if summary.get("unknown_hashes") or summary.get("blocked_approved_requests") else 0


def _apply(args: argparse.Namespace) -> int:
    report_path = Path(args.report).resolve()
    approval_path = Path(args.approval).resolve() if args.approval else None
    out_dir = Path(args.out).resolve() if args.out else report_path.parent
    try:
        transport = None
        if args.write:
            from tools.cloud_doc_backport_transports import _parse_table_bindings, _source_table_transport

            bindings = _parse_table_bindings(args.table_binding or [])
            if not bindings:
                raise RuntimeError("--write requires at least one --table-binding TABLE=BASE:TABLE_ID")
            transport = _source_table_transport(
                bindings,
                lark_cli=str(args.lark_cli or "lark-cli"),
                identity=str(args.identity or "bot"),
            )
        apply_report = build_apply_report(
            report_path,
            approval_path=approval_path,
            approved_hashes=args.approve or [],
            transport=transport,
            write=bool(args.write),
        )
        paths = write_apply_report(apply_report, out_dir)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"source-intake: {exc}", file=sys.stderr)
        return 2
    for label, path in sorted(paths.items()):
        print(f"WROTE {label} {path}")
    summary = apply_report.get("summary") or {}
    print(
        f"APPLY {summary.get('apply', 0)} SKIP {summary.get('skip', 0)} "
        f"WRITTEN {summary.get('written', 0)} VERIFY_FAILED {summary.get('verify_failed', 0)} "
        f"ERROR {summary.get('error', 0)} "
        f"({'WRITE' if apply_report.get('external_write') else 'dry-run'})"
    )
    return 1 if summary.get("verify_failed") or summary.get("error") else 0


def _verify(args: argparse.Namespace) -> int:
    cwd = Path(args.cwd).resolve() if args.cwd else ROOT
    out_dir = Path(args.out).resolve() if args.out else Path(args.candidates).resolve().parent
    try:
        command_results = run_check_commands(args.check_command or [], cwd=cwd)
        closure = build_closure_report(
            candidates_path=Path(args.candidates).resolve(),
            change_request_path=Path(args.change_request).resolve(),
            approval_path=Path(args.approval).resolve(),
            apply_report_path=Path(args.apply_report).resolve(),
            command_results=command_results,
            require_write=bool(args.require_write),
        )
        paths = write_closure_report(closure, out_dir)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"source-intake: {exc}", file=sys.stderr)
        return 2
    for label, path in sorted(paths.items()):
        print(f"WROTE {label} {path}")
    summary = closure.get("summary") or {}
    print(f"CLOSURE {'PASS' if summary.get('passed') else 'FAIL'}")
    return 0 if summary.get("passed") else 1


def _spec_extract(args: argparse.Namespace) -> int:
    import collections
    import json

    from tools.source_intake_completeness import check_completeness
    from tools.source_intake_extract import read_input_text
    from tools.source_intake_rules import FieldRule, extract_candidates

    out_dir = Path(args.out).resolve() if args.out else _default_out_dir(str(args.document_key))
    report = None
    try:
        text = read_input_text(args.input, lark_cli=args.lark_cli)
        rules = [FieldRule.from_dict(d) for d in json.loads(Path(args.rules).read_text(encoding="utf-8"))]
        candidates = extract_candidates(
            text, rules, region=str(args.region or "US"),
            document_key=str(args.document_key), source_lang=str(args.source_lang or "en"),
        )
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "spec_intake_candidates.json").write_text(
            json.dumps(candidates, ensure_ascii=False, indent=2), encoding="utf-8")
        if args.reference:
            ref = json.loads(Path(args.reference).read_text(encoding="utf-8"))
            report = check_completeness(candidates, ref)
            (out_dir / "spec_intake_completeness.json").write_text(json.dumps({
                "passed": report.passed, "summary": report.summary(),
                "missing_rows": report.missing_rows, "extra_rows": report.extra_rows,
                "field_gaps": report.field_gaps,
            }, ensure_ascii=False, indent=2), encoding="utf-8")
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"source-intake: {exc}", file=sys.stderr)
        return 2
    print(f"WROTE candidates {out_dir / 'spec_intake_candidates.json'}")
    print(f"CANDIDATES {len(candidates)}  {dict(collections.Counter(c['status'] for c in candidates))}")
    if report is not None:
        print(f"COMPLETENESS {report.summary()}")
        return 0 if report.passed else 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.command == "spec-extract":
        return _spec_extract(args)
    if args.command == "run":
        return _run(args)
    if args.command == "approve":
        return _approval(args)
    if args.command == "apply":
        return _apply(args)
    if args.command == "verify":
        return _verify(args)
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
