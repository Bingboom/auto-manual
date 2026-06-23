#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Live verification of the backport closed loop against the Feishu tenant.

Where ``tools/backport_harness.py`` is the OFFLINE, CI-safe integration harness,
this module runs the same closed loop **live** by composing the proven pipeline
functions against a real cloud doc:

    fetch_doc_text (live, via lark-cli)  ->  build_report (diff + classify)
        ->  build_change_request_report  ->  [--write] apply_change_requests

It is **operator-run, not CI** (CI has no tenant credentials). Its purpose is the
proactive real-doc coverage the reactive patches (#466 / #423) lacked: point it at
a cloud doc carrying known edits and assert the live pipeline routes them exactly
as the offline model predicts.

Safety:

- Live source-table writes go ONLY to the operator-nominated **sandbox**
  ``--table-binding TABLE=BASE:TABLE_ID``. The command **refuses ``--write``
  without one**, and prints the exact target base:table before writing, so a
  production source table is never touched by accident.
- Without ``--write`` it is read-only (fetch + diff + classify + assert).
- The write reuses the same exact-or-abstain F6 path as production
  (``apply_change_requests``): it GET-checks each cell, skips ``already_applied``,
  abstains on drift, and GET-verifies every write.

Usage (operator):

    # read-only: fetch the edited doc, diff vs baseline, assert routing
    python3 tools/backport_live_check.py \\
        --cloud-doc <edited doc url> --baseline-md baseline.md --lang fr \\
        --data-root data/phase2 --expect expect.json

    # sandbox write: apply the resolved Class D edits to a sandbox table + verify
    python3 tools/backport_live_check.py ... \\
        --write --table-binding Spec_Master=<SANDBOX_BASE>:<SANDBOX_TABLE>

``expect.json`` (all keys optional): ``{"routes": {"repo_review_text": 1}, "total": 1, "semantic": 0}``.
The cloud doc must already carry the known edits (prepare it once, or import a
scratch doc with existing tooling).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.cloud_doc_backport import (  # noqa: E402
    _parse_table_bindings,
    _source_table_transport,
    build_change_request_report,
    build_report,
    fetch_doc_text,
)
from tools.source_table_sync import apply_change_requests, load_sidecar_index  # noqa: E402
from tools.token_resolution_map import build_value_index  # noqa: E402


def run_live(
    *,
    cloud_doc: str,
    baseline_text: str,
    lang: str,
    data_root: str | None = None,
    expect: dict[str, Any] | None = None,
    write: bool = False,
    bindings: dict[str, tuple[str, str]] | None = None,
    lark_cli: str = "lark-cli",
    identity: str = "bot",
    fetch_fn: Callable[[str], str] | None = None,
    transport_factory: Callable[[], Any] | None = None,
    value_index: dict[str, Any] | None = None,
    sidecar: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run one live round-trip and compare against ``expect``.

    ``fetch_fn`` / ``transport_factory`` / ``value_index`` / ``sidecar`` are
    injection points for tests; in production they default to the live fetch, the
    live sandbox transport, and the snapshot-built index/sidecar from ``data_root``.
    """
    fetch = fetch_fn or (lambda url: fetch_doc_text(url, lark_cli=lark_cli))
    fetched = fetch(cloud_doc)

    if value_index is None and data_root:
        value_index = build_value_index(Path(data_root), lang)
    if sidecar is None and data_root:
        sidecar = load_sidecar_index(Path(data_root))

    report = build_report(
        run_id="live",
        doc_type="review",
        doc_url=cloud_doc,
        baseline_path=Path("baseline.md"),
        fetched_text=fetched,
        baseline_text=baseline_text,
        command=["backport_live_check"],
        source_path=None,
        section_title=None,
        value_index=value_index,
    )
    change_requests = build_change_request_report(report, sidecar_index=sidecar)
    summary = report["summary"]
    result: dict[str, Any] = {
        "routes": summary["route_classes"],
        "total": summary["total_deltas"],
        "semantic": summary["semantic_review_required"],
        "requests": len(change_requests["requests"]),
        "resolved_requests": change_requests["summary"]["resolved_record_ids"],
        "wrote": False,
    }

    mismatches: list[str] = []
    if expect:
        if "routes" in expect and result["routes"] != expect["routes"]:
            mismatches.append(f"routes {result['routes']} != {expect['routes']}")
        if "total" in expect and result["total"] != expect["total"]:
            mismatches.append(f"total {result['total']} != {expect['total']}")
        if "semantic" in expect and result["semantic"] != expect["semantic"]:
            mismatches.append(f"semantic {result['semantic']} != {expect['semantic']}")

    if write:
        if not bindings:
            raise RuntimeError(
                "--write requires a sandbox --table-binding TABLE=BASE:TABLE_ID; refusing to write"
            )
        transport = (transport_factory or (lambda: _source_table_transport(bindings, lark_cli=lark_cli, identity=identity)))()
        requests = change_requests["requests"]
        apply_result = apply_change_requests(
            requests,
            approved_hashes={r["delta_hash"] for r in requests},
            transport=transport,
            write=True,
        )
        result["wrote"] = True
        result["applied"] = apply_result["summary"]
        bad = {k: apply_result["summary"].get(k, 0) for k in ("drift_abstained", "verify_failed", "error")}
        if any(bad.values()):
            mismatches.append(f"sandbox write had non-clean outcomes: {bad}")

    result["mismatches"] = mismatches
    result["passed"] = not mismatches
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Live backport closed-loop verification (operator-run)")
    parser.add_argument("--cloud-doc", required=True, help="URL of the edited cloud doc")
    parser.add_argument("--baseline-md", required=True, help="path to the baseline markdown (R0) file")
    parser.add_argument("--lang", required=True, help="value-column language suffix (fr/es/de/it/uk/en/...)")
    parser.add_argument("--data-root", default=None, help="snapshot root for the value index + sidecar")
    parser.add_argument("--expect", default=None, help="path to a JSON file of expected routes/total/semantic")
    parser.add_argument("--write", action="store_true", help="apply resolved Class D edits to the sandbox table")
    parser.add_argument(
        "--table-binding",
        action="append",
        default=[],
        help="sandbox binding TABLE=BASE:TABLE_ID (required for --write; never a production table)",
    )
    parser.add_argument("--lark-cli", default="lark-cli", help="lark-cli binary")
    parser.add_argument("--identity", default="bot", help="lark-cli identity (user|bot)")
    parser.add_argument("--json", action="store_true", help="emit a machine-readable result")
    args = parser.parse_args(argv)

    baseline_text = Path(args.baseline_md).read_text(encoding="utf-8")
    expect = json.loads(Path(args.expect).read_text(encoding="utf-8")) if args.expect else None
    bindings = _parse_table_bindings(args.table_binding) if args.table_binding else None

    if args.write:
        if not bindings:
            print("ERROR: --write requires a sandbox --table-binding TABLE=BASE:TABLE_ID", file=sys.stderr)
            return 2
        for table, (base, table_id) in bindings.items():
            print(f"[live-write] sandbox target: {table} -> base={base} table={table_id}", file=sys.stderr)

    result = run_live(
        cloud_doc=args.cloud_doc,
        baseline_text=baseline_text,
        lang=args.lang,
        data_root=args.data_root,
        expect=expect,
        write=args.write,
        bindings=bindings,
        lark_cli=args.lark_cli,
        identity=args.identity,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        mark = "PASS" if result["passed"] else "FAIL"
        print(f"[{mark}] routes={result['routes']} total={result['total']} wrote={result['wrote']}")
        if result.get("applied"):
            print(f"        applied={result['applied']}")
        for mismatch in result["mismatches"]:
            print(f"        - {mismatch}")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
