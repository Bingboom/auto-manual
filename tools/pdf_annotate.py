#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render QC findings as highlight annotations on a built PDF (G5 MVP).

Architecture rule: **annotate on the PDF, correct at the source.** The PDF is a
rendered artifact — an edit made on it is overwritten by the next build, and
mapping PDF coordinates back to RST/source tables is the hardest reverse
engineering in the pipeline. So this module is a read-only *presentation*
layer: it takes `content_lint` findings (or any finding list), locates each
finding's text on the built PDF via text search, and writes highlight + note
annotations naming the source location, so a PDF-only reviewer can see exactly
what QC flagged and route the fix through the existing docx/cloud-doc backport
path. The shipped PDF is never modified; output is a sidecar
``*_annotated.pdf``.

Locating degrades, never lies: a finding whose text cannot be found gets no
misplaced highlight — it lands in a summary note on page 1 (and in the JSON
result) as ``unlocated``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.utils.path_utils import get_paths, pdf_annotate_reports_of  # noqa: E402

LEDGER_SCHEMA_VERSION = 1
LEDGER_FILENAME = "ledger.jsonl"

# RGB 0..1 — a soft amber, distinct from reviewer-pen colors.
HIGHLIGHT_COLOR = (1.0, 0.82, 0.3)

_EVIDENCE_TEXT_KEYS = ("text", "value", "copy", "expected", "actual", "snippet")
MIN_LOCATOR_LENGTH = 6


def locator_texts(finding: dict[str, Any]) -> list[str]:
    """Candidate strings to search for on the page, most specific first.

    Pulls string values out of the finding's ``evidence`` (the content-bearing
    field of a ``content_lint`` finding), longest first — longer needles give
    fewer false anchors. Strings shorter than ``MIN_LOCATOR_LENGTH`` are
    dropped rather than risking a wrong highlight.
    """
    evidence = finding.get("evidence") or {}
    candidates: list[str] = []
    if isinstance(evidence, dict):
        for key in _EVIDENCE_TEXT_KEYS:
            value = evidence.get(key)
            if isinstance(value, str) and len(value.strip()) >= MIN_LOCATOR_LENGTH:
                candidates.append(value.strip())
        for value in evidence.values():
            if (
                isinstance(value, str)
                and len(value.strip()) >= MIN_LOCATOR_LENGTH
                and value.strip() not in candidates
            ):
                candidates.append(value.strip())
    return sorted(candidates, key=len, reverse=True)


def _annotation_note(finding: dict[str, Any]) -> str:
    """The reviewer-facing note: what is wrong and where the source lives."""
    source_ref = finding.get("source_ref") or {}
    where = ", ".join(
        f"{key}={value}"
        for key, value in source_ref.items()
        if value not in (None, "") and key != "kind"
    )
    parts = [
        f"[{finding.get('severity', 'info')}] {finding.get('rule', 'finding')}",
        str(finding.get("message") or ""),
    ]
    if where:
        parts.append(f"source: {where}")
    action = finding.get("suggested_action")
    if action:
        parts.append(f"action: {action}")
    parts.append("Fix at the source (backport path); this PDF is a rendered artifact.")
    return "\n".join(part for part in parts if part)


def annotate_pdf(
    pdf_path: Path,
    findings: list[dict[str, Any]],
    out_path: Path,
    *,
    color: tuple[float, float, float] = HIGHLIGHT_COLOR,
) -> dict[str, Any]:
    """Write ``out_path`` = ``pdf_path`` + one highlight+note per located finding.

    Returns a summary: located / unlocated findings and the annotation count.
    The input PDF is opened read-only and never modified.
    """
    import fitz  # PyMuPDF; imported lazily so the repo works without it

    located: list[dict[str, Any]] = []
    unlocated: list[dict[str, Any]] = []
    doc = fitz.open(str(pdf_path))
    try:
        for finding in findings:
            hit = None
            for needle in locator_texts(finding):
                for page in doc:
                    rects = page.search_for(needle)
                    if rects:
                        hit = (page, rects, needle)
                        break
                if hit:
                    break
            if not hit:
                unlocated.append(finding)
                continue
            page, rects, needle = hit
            annot = page.add_highlight_annot(rects)
            annot.set_colors(stroke=color)
            annot.set_info(
                title="auto-manual QC",
                content=_annotation_note(finding),
            )
            annot.update()
            located.append(
                {
                    "rule": finding.get("rule"),
                    "page": page.number + 1,
                    "needle": needle,
                }
            )

        if unlocated:
            first = doc[0]
            lines = [
                f"{len(unlocated)} QC finding(s) could not be located on the page "
                "(text not found after rendering); fix them at the source:",
            ]
            for finding in unlocated:
                source_ref = finding.get("source_ref") or {}
                lines.append(
                    f"- [{finding.get('severity', 'info')}] {finding.get('rule')}: "
                    f"{finding.get('message')} ({json.dumps(source_ref, ensure_ascii=False)})"
                )
            note = first.add_text_annot(fitz.Point(36, 36), "\n".join(lines))
            note.set_info(title="auto-manual QC (unlocated findings)")
            note.update()

        out_path.parent.mkdir(parents=True, exist_ok=True)
        doc.save(str(out_path))
    finally:
        doc.close()
    return {
        "pdf": str(pdf_path),
        "out": str(out_path),
        "findings": len(findings),
        "located": located,
        "unlocated": len(unlocated),
        "annotations": len(located) + (1 if unlocated else 0),
    }


def load_findings(findings_path: Path) -> list[dict[str, Any]]:
    """Load a content_lint ``findings.json`` (a list, or a dict with ``findings``)."""
    payload = json.loads(findings_path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        payload = payload.get("findings") or []
    if not isinstance(payload, list):
        raise ValueError(f"{findings_path} does not contain a findings list")
    return [finding for finding in payload if isinstance(finding, dict)]


def default_out_path(pdf_path: Path) -> Path:
    return pdf_path.with_name(f"{pdf_path.stem}_annotated{pdf_path.suffix}")


def default_ledger_path(base_root: Path | None = None) -> Path:
    if base_root is None:
        return get_paths().pdf_annotate_reports_dir / LEDGER_FILENAME
    return pdf_annotate_reports_of(base_root) / LEDGER_FILENAME


def _ledger_run_key(summary: dict[str, Any]) -> str:
    fingerprint = json.dumps(
        {
            "pdf": summary.get("pdf"),
            "out": summary.get("out"),
            "findings": summary.get("findings"),
            "located": len(summary.get("located") or []),
            "unlocated": summary.get("unlocated"),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha1(fingerprint.encode("utf-8")).hexdigest()


def ledger_entry_from_summary(
    summary: dict[str, Any], *, recorded_at: str | None = None
) -> dict[str, Any]:
    """Project one annotate run summary into a ledger entry.

    The entry is what the flow dashboard's audited-PDF count reads, so a run
    (or an operator backfill of a historical run) records only the summary
    facts — never the finding contents.
    """
    return {
        "ledger_schema_version": LEDGER_SCHEMA_VERSION,
        "run_key": _ledger_run_key(summary),
        "recorded_at": recorded_at
        or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pdf": summary.get("pdf"),
        "out": summary.get("out"),
        "findings": summary.get("findings"),
        "located": len(summary.get("located") or []),
        "unlocated": summary.get("unlocated"),
    }


def load_ledger(ledger_path: Path) -> list[dict[str, Any]]:
    if not ledger_path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in ledger_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def append_run_to_ledger(
    summary: dict[str, Any], *, ledger_path: Path, recorded_at: str | None = None
) -> dict[str, Any]:
    """Append one run to the ledger; re-appending the same run is a no-op."""
    entry = ledger_entry_from_summary(summary, recorded_at=recorded_at)
    existing = {row.get("run_key") for row in load_ledger(ledger_path)}
    if entry["run_key"] in existing:
        return {"ledger": str(ledger_path), "written": 0, "skipped": 1, "entry": entry}
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
    return {"ledger": str(ledger_path), "written": 1, "skipped": 0, "entry": entry}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="pdf_annotate",
        description="Render QC findings as highlight annotations on a built PDF "
        "(sidecar output; the shipped PDF is never touched).",
    )
    parser.add_argument("--pdf", type=Path, help="Built PDF to annotate.")
    parser.add_argument(
        "--findings",
        type=Path,
        help="content_lint findings.json (list or {'findings': [...]}).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output path (default: <pdf-stem>_annotated.pdf next to the input).",
    )
    parser.add_argument(
        "--ledger",
        type=Path,
        default=None,
        help="Run-ledger JSONL path (default: reports/pdf_annotate/ledger.jsonl).",
    )
    parser.add_argument(
        "--no-ledger",
        action="store_true",
        help="Do not append this run to the run ledger.",
    )
    parser.add_argument(
        "--backfill-summary",
        type=Path,
        default=None,
        help="Append a historical run's summary JSON to the ledger without "
        "annotating (operator backfill; mutually exclusive with --pdf).",
    )
    args = parser.parse_args(argv)
    if args.backfill_summary is None and (args.pdf is None or args.findings is None):
        parser.error("--pdf and --findings are required unless --backfill-summary is given")
    if args.backfill_summary is not None and args.pdf is not None:
        parser.error("--backfill-summary cannot be combined with --pdf")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    ledger_path = args.ledger or default_ledger_path()
    if args.backfill_summary is not None:
        summary = json.loads(args.backfill_summary.read_text(encoding="utf-8"))
        if not isinstance(summary, dict):
            raise ValueError(f"{args.backfill_summary} is not a JSON object")
        print(json.dumps(
            append_run_to_ledger(summary, ledger_path=ledger_path),
            ensure_ascii=False, indent=2,
        ))
        return 0
    findings = load_findings(args.findings)
    out_path = args.out or default_out_path(args.pdf)
    summary = annotate_pdf(args.pdf, findings, out_path)
    if not args.no_ledger:
        try:
            ledger_result = append_run_to_ledger(summary, ledger_path=ledger_path)
            summary["ledger"] = {
                "path": ledger_result["ledger"],
                "written": ledger_result["written"],
            }
        except OSError as exc:  # ledger append is best-effort, never blocks the sidecar
            summary["ledger"] = {"error": str(exc)}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
