#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Backport reminder sentinel: surface un-backported review-doc edits.

The cloud-doc backport is CLI-only (#453) and runs when an operator remembers
to run it. This sentinel closes that gap the same way the schema-parity
sentinel does — a daily, read-only check that reports and never acts:

For every InReview row of the build table that carries a review cloud doc, the
live doc text is compared against the committed render baseline on the row's
review branch (``docs/_review/<model>/<region>/.backport/<token>.baseline.md``,
read via ``git show`` — no worktree needed). A difference means reviewer edits
exist that no backport has collected; a missing baseline means the review has
never been backported at all. Timestamps are deliberately not used: pending
content is the signal, and the alert clears exactly when a backport advances
the baseline.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.backport_baseline import baseline_rel_path  # noqa: E402
from tools.cloud_doc_backport_model import fetch_doc_text, parse_blocks  # noqa: E402
from tools.document_link_queue import field_value, scalar_text  # noqa: E402
from tools.review_branch_resolver import (  # noqa: E402
    CLOUD_DOC_FIELDS,
    DOCUMENT_ID_FIELDS,
    GIT_REF_FIELDS,
    IN_REVIEW_STATUS,
    REVIEW_STATUS_FIELDS,
    doc_token,
    parse_document_id,
)

PENDING = "pending_edits"
NO_BASELINE = "no_baseline"
SYNCED = "synced"
ERROR = "error"


def in_review_docs(raw_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Every InReview build-table row that names a review cloud doc."""
    docs: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for record in raw_records:
        fields = record.get("fields") or {}
        if not isinstance(fields, dict):
            continue
        if scalar_text(field_value(fields, *REVIEW_STATUS_FIELDS)) != IN_REVIEW_STATUS:
            continue
        cloud_doc = scalar_text(field_value(fields, *CLOUD_DOC_FIELDS))
        git_ref = scalar_text(field_value(fields, *GIT_REF_FIELDS))
        document_id = scalar_text(field_value(fields, *DOCUMENT_ID_FIELDS))
        parsed = parse_document_id(document_id)
        if not (cloud_doc and git_ref and parsed):
            continue
        model, region, _version = parsed
        key = (git_ref, doc_token(cloud_doc))
        if key in seen:
            continue
        seen.add(key)
        docs.append(
            {
                "cloud_doc": cloud_doc,
                "git_ref": git_ref,
                "document_id": document_id,
                "review_dir": f"docs/_review/{model}/{region}",
            }
        )
    return docs


def baseline_from_git(
    git_ref: str, rel_path: str, *, remote: str = "origin", repo_root: Path | None = None
) -> str | None:
    """Read the committed baseline file from the remote-tracking review branch."""
    ref = f"{remote}/{git_ref}" if remote else git_ref
    try:
        proc = subprocess.run(
            ["git", "show", f"{ref}:{rel_path}"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
            check=False,
            cwd=str(repo_root) if repo_root else None,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout


def _normalized(text: str) -> str:
    """The same normalized text space the backport diffs in."""
    return " ".join(block.normalized for block in parse_blocks(text))


def check_docs(
    docs: list[dict[str, Any]],
    *,
    lark_cli: str = "lark-cli",
    remote: str = "origin",
    repo_root: Path | None = None,
    fetch: Callable[..., str] = fetch_doc_text,
    baseline_reader: Callable[..., str | None] = baseline_from_git,
) -> dict[str, Any]:
    """Classify every in-review doc; report-only, no writes anywhere."""
    results: list[dict[str, Any]] = []
    for doc in docs:
        rel_path = baseline_rel_path(doc["review_dir"], doc_token(doc["cloud_doc"]))
        entry = {**doc, "baseline_path": rel_path}
        baseline = baseline_reader(
            doc["git_ref"], rel_path, remote=remote, repo_root=repo_root
        )
        if baseline is None:
            results.append({**entry, "status": NO_BASELINE})
            continue
        try:
            doc_text = fetch(doc["cloud_doc"], lark_cli=lark_cli)
        except (OSError, RuntimeError, ValueError) as exc:
            results.append({**entry, "status": ERROR, "error": str(exc)})
            continue
        if _normalized(doc_text) == _normalized(baseline):
            results.append({**entry, "status": SYNCED})
        else:
            results.append({**entry, "status": PENDING})

    by_status: dict[str, int] = {}
    for result in results:
        by_status[result["status"]] = by_status.get(result["status"], 0) + 1
    needs_attention = [r for r in results if r["status"] in (PENDING, NO_BASELINE)]
    return {
        "checked": len(results),
        "by_status": by_status,
        "needs_attention": needs_attention,
        "results": results,
        "ok": not needs_attention and not by_status.get(ERROR),
    }


def _fetch_build_table_records(lark_cli: str, identity: str) -> list[dict[str, Any]]:
    from tools.cloud_doc_backport_orchestration import (
        _fetch_build_table_records as fetch_records,
    )

    return fetch_records(lark_cli, identity)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="backport_reminder",
        description="Report review cloud docs whose edits no backport has collected.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    chk = sub.add_parser("check", help="Check every InReview doc against its baseline.")
    chk.add_argument("--lark-cli", default="lark-cli", help="lark-cli binary.")
    chk.add_argument("--identity", default="bot", help="lark-cli identity.")
    chk.add_argument("--remote", default="origin", help="Git remote holding review branches.")
    chk.add_argument("--json", action="store_true", help="Print the full JSON report.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "check":
        records = _fetch_build_table_records(args.lark_cli, args.identity)
        report = check_docs(
            in_review_docs(records), lark_cli=args.lark_cli, remote=args.remote
        )
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print(
                f"[backport-reminder] checked {report['checked']} doc(s): "
                + ", ".join(f"{k}={v}" for k, v in sorted(report["by_status"].items()))
            )
            for entry in report["needs_attention"]:
                print(
                    f"[backport-reminder] {entry['status']}: {entry['document_id']} "
                    f"({entry['git_ref']}) {entry['cloud_doc']}"
                )
        return 0 if report["ok"] else 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
