#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Backport closed-loop integration harness (L5 of the test plan).

Runs the **entire** cloud-doc backport pipeline end to end over realistic
*multi-edit* documents and asserts the aggregate outcome:

    value-index  ->  build_report (diff + classify)  ->  build_change_request_report
                 ->  plan_apply (dry-run, no transport)

Each fixture is a *whole document* with several simultaneous edits across route
classes (prose, spec value, table cell, semantic trap, plus pure noise that must
produce no delta). This is the integration layer above the single-delta golden
corpus (``tests/test_backport_golden_corpus.py``): it catches aggregation and
interaction bugs, and exercises the F6 change-request build + plan chain — the
write side — that the corpus does not touch.

The ``check`` command is **offline** (no Feishu) and CI-safe; it is also runnable
by an operator as a quick green/red gate:

    python3 tools/backport_harness.py check            # run all fixtures, assert
    python3 tools/backport_harness.py check --json     # machine-readable report
    python3 tools/backport_harness.py list             # list fixtures

For a true LIVE round-trip, run ``tools/cloud_doc_backport.py`` against a seeded
test-tenant doc in dry-run. Live source-table writes must target an
operator-nominated **sandbox** data-root (never production source tables), so they
are intentionally out of this harness.

To grow coverage, add a :class:`Fixture` to ``_FIXTURES`` — a new model/region/
language or a new real-case document shape becomes one more end-to-end assertion.
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.cloud_doc_backport import build_report  # noqa: E402
from tools.source_record_index import build_index  # noqa: E402
from tools.source_table_sync import build_change_request_report, plan_apply  # noqa: E402
from tools.token_resolution_map import build_value_index  # noqa: E402


@dataclass
class SpecRow:
    """One Spec_Master source row, used to build both the value index and (when
    ``record_id`` is set) the sidecar so the F6 write path resolves to a record."""

    document_key: str
    page: str
    row_key: str
    slot_key: str
    source_lang: str
    value: str
    record_id: str | None = None

    def source_table(self) -> str:
        return "Spec_Master" if "specification" in self.page.lower() else "Page_Placeholders_Source"


@dataclass
class Fixture:
    name: str
    lang: str
    baseline: str
    edits: list[tuple[str, str]]
    spec_rows: list[SpecRow] = field(default_factory=list)
    doc_type: str = "review"
    expect_total: int | None = None
    expect_routes: dict[str, int] = field(default_factory=dict)
    expect_semantic: int = 0
    expect_resolved_requests: int | None = None
    expect_plan_applies: list[str] = field(default_factory=list)  # expected new cell values


def _apply_edits(baseline: str, edits: list[tuple[str, str]]) -> str:
    """Produce the edited (``fetched``) text. Each ``find`` must be present, so a
    fixture cannot silently apply a no-op edit and pass for the wrong reason."""
    text = baseline
    for find, replace in edits:
        if find not in text:
            raise ValueError(f"edit target not found in fixture baseline: {find!r}")
        text = text.replace(find, replace)
    return text


def _spec_master_csv(spec_rows: list[SpecRow], lang: str) -> str:
    header = "document_key,Page,Row_key,Slot_key,Source_lang,Value_" + lang
    lines = [header]
    for row in spec_rows:
        lines.append(
            ",".join([row.document_key, row.page, row.row_key, row.slot_key, row.source_lang, row.value])
        )
    return "\n".join(lines) + "\n"


def _sidecar(spec_rows: list[SpecRow]) -> dict[str, Any] | None:
    rows_by_table: dict[str, list[tuple[dict[str, Any], str]]] = {}
    for row in spec_rows:
        if not row.record_id:
            continue
        rows_by_table.setdefault(row.source_table(), []).append(
            ({"document_key": row.document_key, "Row_key": row.row_key, "Slot_key": row.slot_key}, row.record_id)
        )
    return build_index(rows_by_table) if rows_by_table else None


def run_fixture(fixture: Fixture) -> dict[str, Any]:
    """Run the full chain for one fixture and compare against its expectations."""
    fetched = _apply_edits(fixture.baseline, fixture.edits)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        value_index = None
        if fixture.spec_rows:
            (root / "Spec_Master.csv").write_text(
                _spec_master_csv(fixture.spec_rows, fixture.lang), encoding="utf-8"
            )
            value_index = build_value_index(root, fixture.lang)
        report = build_report(
            run_id=f"harness:{fixture.name}",
            doc_type=fixture.doc_type,
            doc_url="https://x.feishu.cn/wiki/harness",
            baseline_path=Path("baseline.md"),
            fetched_text=fetched,
            baseline_text=fixture.baseline,
            command=["backport_harness"],
            source_path=None,
            section_title=None,
            value_index=value_index,
        )
    sidecar = _sidecar(fixture.spec_rows)
    change_requests = build_change_request_report(report, sidecar_index=sidecar)
    requests = change_requests["requests"]
    plan = plan_apply(requests, approved_hashes={r["delta_hash"] for r in requests})

    summary = report["summary"]
    observed = {
        "total": summary["total_deltas"],
        "routes": summary["route_classes"],
        "semantic": summary["semantic_review_required"],
        "resolved_requests": change_requests["summary"]["resolved_record_ids"],
        "plan_applies": [entry["value"] for entry in plan if entry["action"] == "apply"],
    }

    mismatches: list[str] = []
    if fixture.expect_total is not None and observed["total"] != fixture.expect_total:
        mismatches.append(f"total {observed['total']} != {fixture.expect_total}")
    if observed["routes"] != fixture.expect_routes:
        mismatches.append(f"routes {observed['routes']} != {fixture.expect_routes}")
    if observed["semantic"] != fixture.expect_semantic:
        mismatches.append(f"semantic {observed['semantic']} != {fixture.expect_semantic}")
    if fixture.expect_resolved_requests is not None and observed["resolved_requests"] != fixture.expect_resolved_requests:
        mismatches.append(f"resolved_requests {observed['resolved_requests']} != {fixture.expect_resolved_requests}")
    if sorted(observed["plan_applies"]) != sorted(fixture.expect_plan_applies):
        mismatches.append(f"plan_applies {observed['plan_applies']} != {fixture.expect_plan_applies}")

    return {"name": fixture.name, "lang": fixture.lang, "passed": not mismatches, "observed": observed, "mismatches": mismatches}


# --------------------------------------------------------------------------- #
# Fixtures: realistic multi-edit documents across model / region / language.
# --------------------------------------------------------------------------- #
_FIXTURES: list[Fixture] = [
    Fixture(
        name="je2000f_eu_fr_mixed",
        lang="fr",
        baseline="\n\n".join(
            [
                "L'appareil démarre la charge automatiquement.",
                "Sortie USB-A 18 W",
                "Appuyez sur la sortie pour commencer.",
                "Cette phrase ne change pas.",
            ]
        ),
        edits=[
            ("L'appareil démarre", "L'appareil commence"),  # prose -> repo_review_text
            ("Sortie USB-A 18 W", "Sortie USB-A 20 W"),  # spec value -> source_table (resolved)
            ("Appuyez sur la sortie", "Appuyez sur le bouton"),  # sortie->bouton -> semantic
        ],
        spec_rows=[
            SpecRow("JE-2000F_EU", "Specifications", "usb_a", "front.spec", "fr", "Sortie USB-A 18 W", "recSPEC_FR"),
        ],
        expect_total=3,
        expect_routes={"repo_review_text": 1, "source_table_suggestion": 1, "needs_human_mapping": 1},
        expect_semantic=1,
        expect_resolved_requests=1,
        expect_plan_applies=["Sortie USB-A 20 W"],
    ),
    Fixture(
        name="je1000f_us_en_table_and_noise",
        lang="en",
        baseline="\n\n".join(
            [
                "Charge the battery before first use.",
                "| Port | Spec |",
                "| --- | --- |",
                "| DC IN | DC 12 V |",
                "| ![diagram](https://x/img/TOKEN_A) |",
                "Keep the device dry.",
            ]
        ),
        edits=[
            ("Charge the battery before first use.", "Charge the battery fully before first use."),  # prose -> R
            ("| DC IN | DC 12 V |", "| DC IN | DC 24 V |"),  # table cell -> source_table (resolved, cell extract)
            ("TOKEN_A", "TOKEN_B"),  # image re-host -> noise (no delta)
        ],
        spec_rows=[
            SpecRow("JE-1000F_US", "Specifications", "dc_in", "front.spec", "en", "DC 12 V", "recSPEC_EN"),
        ],
        expect_total=2,
        expect_routes={"repo_review_text": 1, "source_table_suggestion": 1},
        expect_semantic=0,
        expect_resolved_requests=1,
        expect_plan_applies=["DC 24 V"],
    ),
    Fixture(
        name="je1000f_jp_ja_prose_only",
        lang="ja",
        baseline="\n\n".join(
            [
                "デバイスは自動的に充電を開始します。",
                "ケーブルをしっかり差し込んでください。",
                "この文は変更されません。",
            ]
        ),
        edits=[
            ("自動的に充電を開始します", "自動的に充電を始めます"),  # prose -> R
            ("しっかり差し込んで", "確実に差し込んで"),  # prose -> R
        ],
        spec_rows=[],
        expect_total=2,
        expect_routes={"repo_review_text": 2},
        expect_semantic=0,
        expect_resolved_requests=0,
        expect_plan_applies=[],
    ),
]


def get_fixtures() -> list[Fixture]:
    return list(_FIXTURES)


def _cmd_check(args: argparse.Namespace) -> int:
    results = [run_fixture(fx) for fx in _FIXTURES]
    failed = [r for r in results if not r["passed"]]
    if args.json:
        print(json.dumps({"passed": not failed, "results": results}, ensure_ascii=False, indent=2))
    else:
        for r in results:
            mark = "PASS" if r["passed"] else "FAIL"
            print(f"[{mark}] {r['name']} ({r['lang']}) routes={r['observed']['routes']}")
            for mismatch in r["mismatches"]:
                print(f"        - {mismatch}")
        print(f"\n{len(results) - len(failed)}/{len(results)} fixtures passed")
    return 1 if failed else 0


def _cmd_list(_args: argparse.Namespace) -> int:
    for fx in _FIXTURES:
        print(f"{fx.name}\t(lang={fx.lang}, edits={len(fx.edits)}, doc_type={fx.doc_type})")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Backport closed-loop integration harness")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="run every fixture through the full pipeline and assert")
    check.add_argument("--json", action="store_true", help="emit a machine-readable report")
    check.set_defaults(func=_cmd_check)
    listing = sub.add_parser("list", help="list the harness fixtures")
    listing.set_defaults(func=_cmd_list)
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
