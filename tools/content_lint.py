#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""content_lint.py — content-quality gate for the phase2 snapshot.

Consolidates the ad-hoc audits from the 2026-06-07 status-word session into a
single repeatable check. It runs against the **exported snapshot**
(``data/phase2/*.csv``) so it is deterministic and CI-friendly — the same
inputs the build consumes (System Evolution Strategy §4.2 Snapshot Layer).

Checks (rules: ``code-as-doc/content_quality_rules.md``):

  [1] status-word consistency  LCD state-prefixes (``On:`` / ``Off:`` / ``Blink:``
                               and localized forms) must match the canonical
                               Translation-Memory status words, per language.
  [2] english residue          English state words leaking into a localized
                               column (e.g. Italian copy still reading ``On:``).
  [3] slot-key collision       Two source rows collapsing to one ``spec_row_key``
                               (a blank ``Slot_key`` made the usb_c 100W row drop).
  [4] spec<->overview drift    Same port valued differently in the specifications
                               page vs the product-overview page (WARN — the
                               value-dedup project removes this class structurally).
  [5] tm duplicate             Duplicate ``en`` key in the status-word snapshot
                               (a stale duplicate TM row can win the sync index).

Severity: [1][2][3][5] are FAIL (block); [4] is WARN (surface for review).
Exit code is 1 when any FAIL-level check has findings, else 0.

Scope note: this prototype lints the **data tables + Translation-Memory**
dimensions. Template multilingual quality (per-language `.rst` parity,
placeholder resolution, units/accents rules) is a sibling check to add next;
full live-Translation-Memory duplicate detection is the scheduled online
extension described in the rules doc.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shlex
import subprocess
import sys
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Reuse the renderer's EXACT status-word matcher, so the lint checks precisely
# what the build will bold (single source of truth — no parallel logic to drift).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.csv_pages.renderers_lcd_icons import _match_status_prefix  # noqa: E402
from tools.source_record_index import resolve_findings  # noqa: E402
from tools.utils.path_utils import get_paths  # noqa: E402

# Non-English shipped EU languages.
DEFAULT_LANGS = ("fr", "es", "de", "it", "uk")
FINDING_SCHEMA_VERSION = "content-qc-finding/v1"
REPORT_SCHEMA_VERSION = "content-qc-report/v1"

# Per-file language→column-suffix maps (the snapshot is not uniform: uk vs ukr).
_LCD_DESC = {"en": "en", "fr": "fr", "es": "es", "de": "de", "it": "it", "uk": "ukr"}
_TROUBLE = {"en": "en", "fr": "fr", "es": "es", "de": "de", "it": "it", "uk": "ukr"}
_TEXT = {"en": "en", "fr": "fr", "es": "es", "de": "de", "it": "it", "uk": "uk"}
_VALUE = {"en": "source", "fr": "fr", "es": "es", "de": "de", "it": "it", "uk": "uk"}

# English state words that should never survive into a localized column.
_ENGLISH_RESIDUE = ("On:", "Off:", "Blinking", "Flashing")

_TRUE = {"y", "yes", "true", "1"}
_SAFE_PATH_CHARS = re.compile(r"[^A-Za-z0-9._-]+")


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _t(value: object) -> str:
    return str(value or "").strip()


def _truthy(value: object) -> bool:
    return _t(value).casefold() in _TRUE


def _lines(value: object) -> list[str]:
    return [ln.strip() for ln in _t(value).replace("\\n", "\n").split("\n") if ln.strip()]


def _status_labels(status_rows: list[dict[str, str]], lang: str) -> tuple[str, ...]:
    labels: list[str] = []
    for row in status_rows:
        if not _truthy(row.get("是否为 status word")):
            continue
        value = _t(row.get(lang))
        if value and value not in labels:
            labels.append(value)
    # Longest-first so a longer label wins over a shorter prefix (matches the renderer).
    return tuple(sorted(labels, key=len, reverse=True))


def _looks_like_prefix(line: str) -> bool:
    """A line that opens like a state label: <=2 words before the first colon."""
    if ":" not in line and "：" not in line:
        return False
    head = line.split(":")[0].split("：")[0]
    return 0 < len(head.split()) <= 2


def _table_name(filename: str) -> str:
    return filename[:-4] if filename.endswith(".csv") else filename


def _compact_dict(values: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in values.items()
        if value not in (None, "", [], {})
    }


def _source_ref(*, kind: str, table: str, file: str, **values: Any) -> dict[str, Any]:
    return _compact_dict({"kind": kind, "table": table, "file": file, **values})


def _first_present(row: dict[str, str], fields: tuple[str, ...]) -> str | None:
    for field in fields:
        value = _t(row.get(field))
        if value:
            return value
    return None


def _finding_hash(payload: dict[str, Any]) -> str:
    hash_input = {
        "rule": payload["rule"],
        "source_ref": payload["source_ref"],
        "lang": payload["lang"],
        "field": payload["field"],
        "evidence": payload["evidence"],
    }
    raw = json.dumps(hash_input, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _utc_now() -> str:
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _git_ref() -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=get_paths().root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    ref = completed.stdout.strip()
    return ref or None


def _safe_path_token(value: str) -> str:
    token = _SAFE_PATH_CHARS.sub("-", value.strip()).strip(".-")
    return token or "content-lint-local"


@dataclass(frozen=True)
class CheckSpec:
    name: str
    rule: str
    severity: str
    findings: list[dict[str, Any]]
    render_one: Callable[[dict[str, Any]], str]
    normalize_one: Callable[[dict[str, Any], str], dict[str, Any]]


def _normalized_finding(
    *,
    run_id: str,
    rule: str,
    severity: str,
    table: str,
    file: str,
    lang: str | None,
    field: str | None,
    source_ref: dict[str, Any],
    message: str,
    evidence: dict[str, Any],
    suggested_action: str,
) -> dict[str, Any]:
    finding: dict[str, Any] = {
        "schema_version": FINDING_SCHEMA_VERSION,
        "run_id": run_id,
        "finding_hash": "",
        "rule": rule,
        "severity": severity,
        "table": table,
        "file": file,
        "source_ref": source_ref,
        "record_id": None,
        "resolution_status": "snapshot_only",
        "lang": lang,
        "field": field,
        "message": message,
        "evidence": evidence,
        "suggested_action": suggested_action,
    }
    finding["finding_hash"] = _finding_hash(finding)
    return finding


# --- [1] status-word consistency ------------------------------------------------
def check_status_word_consistency(root: Path, langs: tuple[str, ...]) -> list[dict]:
    status = _read_csv(root / "Status_Words.csv")
    lcd = _read_csv(root / "lcd_icons_blocks.csv")
    findings: list[dict] = []
    for lang in langs:
        labels = _status_labels(status, lang)
        col = f"icon_desc_{_LCD_DESC[lang]}"
        for row in lcd:
            icon = _t(row.get("icon_en"))
            for line in _lines(row.get(col)):
                if _looks_like_prefix(line) and not _match_status_prefix(line, labels):
                    prefix = line.split(":")[0].split("：")[0].strip()
                    findings.append(
                        {
                            "lang": lang,
                            "icon": icon,
                            "model": _t(row.get("Model")),
                            "version": _t(row.get("Version")),
                            "prefix": prefix,
                            "line": line[:64],
                        }
                    )
    return findings


def _status_word_json(raw: dict[str, Any], run_id: str) -> dict[str, Any]:
    lang = _t(raw.get("lang"))
    field = f"icon_desc_{_LCD_DESC.get(lang, lang)}" if lang else None
    return _normalized_finding(
        run_id=run_id,
        rule="status_word_consistency",
        severity="FAIL",
        table="lcd_icons_blocks",
        file="lcd_icons_blocks.csv",
        lang=lang or None,
        field=field,
        source_ref=_source_ref(
            kind="lcd_icon",
            table="lcd_icons_blocks",
            file="lcd_icons_blocks.csv",
            key=_t(raw.get("icon")),
            model=_t(raw.get("model")),
            version=_t(raw.get("version")),
        ),
        message=f"Non-canonical status prefix {raw.get('prefix')!r} in LCD icon description.",
        evidence={
            "icon": raw.get("icon"),
            "prefix": raw.get("prefix"),
            "line": raw.get("line"),
        },
        suggested_action=(
            "Align the localized LCD status prefix with the canonical status word "
            "in Translation_Memory, then sync and re-run QC."
        ),
    )


# --- [2] english residue --------------------------------------------------------
def check_english_residue(root: Path, langs: tuple[str, ...]) -> list[dict]:
    targets = [
        ("lcd_icons_blocks.csv", "icon_desc_{s}", _LCD_DESC, ("icon_en",)),
        ("troubleshooting_blocks.csv", "corrective_measures_{s}", _TROUBLE, ("error_code",)),
        ("Spec_Footnotes.csv", "Text_{s}", _TEXT, ("Footnote_id",)),
        ("Spec_Notes.csv", "Text_{s}", _TEXT, ("Note_id",)),
    ]
    findings: list[dict] = []
    for filename, pattern, suffix_map, key_fields in targets:
        rows = _read_csv(root / filename)
        if not rows:
            continue
        for lang in langs:
            col = pattern.format(s=suffix_map[lang])
            for row in rows:
                value = _t(row.get(col))
                for token in _ENGLISH_RESIDUE:
                    if token in value:
                        findings.append(
                            {
                                "file": filename,
                                "lang": lang,
                                "field": col,
                                "key": _first_present(row, key_fields),
                                "model": _t(row.get("Model")),
                                "region": _t(row.get("Region")),
                                "version": _t(row.get("Version")),
                                "token": token,
                                "text": value[:64],
                            }
                        )
    return findings


def _english_residue_json(raw: dict[str, Any], run_id: str) -> dict[str, Any]:
    file = _t(raw.get("file"))
    token = _t(raw.get("token"))
    return _normalized_finding(
        run_id=run_id,
        rule="english_residue",
        severity="FAIL",
        table=_table_name(file),
        file=file,
        lang=_t(raw.get("lang")) or None,
        field=_t(raw.get("field")) or None,
        source_ref=_source_ref(
            kind=_table_name(file),
            table=_table_name(file),
            file=file,
            key=_t(raw.get("key")),
            model=_t(raw.get("model")),
            region=_t(raw.get("region")),
            version=_t(raw.get("version")),
        ),
        message=f"English token {token!r} appears in localized text.",
        evidence={
            "token": token,
            "text": raw.get("text"),
        },
        suggested_action="Fix the localized source field in Feishu, then sync and re-run QC.",
    )


# --- [3] slot-key collision -----------------------------------------------------
def check_slot_key_collision(root: Path) -> list[dict]:
    rows = _read_csv(root / "Spec_Master.csv")
    by_key: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        key = _t(row.get("spec_row_key"))
        if key:
            by_key[key].append(row)
    findings: list[dict] = []
    for key, group in by_key.items():
        if len(group) > 1:
            findings.append(
                {
                    "spec_row_key": key,
                    "count": len(group),
                    "rows": [f"{_t(r.get('document_key'))}/{_t(r.get('Row_key'))}" for r in group],
                }
            )
    return findings


def _slot_key_collision_json(raw: dict[str, Any], run_id: str) -> dict[str, Any]:
    spec_row_key = _t(raw.get("spec_row_key"))
    return _normalized_finding(
        run_id=run_id,
        rule="slot_key_collision",
        severity="FAIL",
        table="Spec_Master",
        file="Spec_Master.csv",
        lang=None,
        field="spec_row_key",
        source_ref=_source_ref(
            kind="spec_row_key",
            table="Spec_Master",
            file="Spec_Master.csv",
            key=spec_row_key,
            rows=raw.get("rows"),
        ),
        message=f"Duplicate spec_row_key {spec_row_key!r} collapses multiple source rows.",
        evidence={
            "spec_row_key": spec_row_key,
            "count": raw.get("count"),
            "rows": raw.get("rows"),
        },
        suggested_action="Assign distinct Slot_key values in the source table, then sync and re-run QC.",
    )


# --- [4] spec<->overview drift --------------------------------------------------
def check_spec_overview_drift(root: Path, langs: tuple[str, ...]) -> list[dict]:
    rows = _read_csv(root / "Spec_Master.csv")
    all_langs = ("en", *langs)
    index: dict[tuple[str, str], dict[str, dict[str, set]]] = defaultdict(
        lambda: {"spec": defaultdict(set), "overview": defaultdict(set)}
    )
    for row in rows:
        page = _t(row.get("Page")).casefold()
        if "specification" in page:
            side = "spec"
        elif "overview" in page or "product" in page:
            side = "overview"
        else:
            continue
        key = (_t(row.get("document_key")), _t(row.get("Row_key")))
        for lang in all_langs:
            # Normalize whitespace so pure multi-space formatting is not flagged.
            value = " ".join(_t(row.get(f"Value_{_VALUE[lang]}")).split())
            if value:
                index[key][side][lang].add(value)
    findings: list[dict] = []
    for (doc, row_key), sides in index.items():
        if not sides["spec"] or not sides["overview"]:
            continue  # not a shared port
        for lang in all_langs:
            spec_vals = sides["spec"].get(lang, set())
            over_vals = sides["overview"].get(lang, set())
            # Real drift = the two sides share NO value (filters out the case where
            # the overview row also carries a label callout alongside the value).
            if spec_vals and over_vals and not (spec_vals & over_vals):
                findings.append(
                    {
                        "document_key": doc,
                        "row_key": row_key,
                        "lang": lang,
                        "spec": sorted(spec_vals),
                        "overview": sorted(over_vals),
                    }
                )
    return findings


def _spec_overview_drift_json(raw: dict[str, Any], run_id: str) -> dict[str, Any]:
    lang = _t(raw.get("lang"))
    field = f"Value_{_VALUE.get(lang, lang)}" if lang else None
    return _normalized_finding(
        run_id=run_id,
        rule="spec_overview_drift",
        severity="WARN",
        table="Spec_Master",
        file="Spec_Master.csv",
        lang=lang or None,
        field=field,
        source_ref=_source_ref(
            kind="spec_master_row",
            table="Spec_Master",
            file="Spec_Master.csv",
            document_key=_t(raw.get("document_key")),
            key=_t(raw.get("row_key")),
            page_sides=["specifications", "Product overview"],
        ),
        message="Specifications and product-overview values differ for the same row key.",
        evidence={
            "document_key": raw.get("document_key"),
            "row_key": raw.get("row_key"),
            "spec": raw.get("spec"),
            "overview": raw.get("overview"),
        },
        suggested_action=(
            "Review the duplicated source values and reconcile the overview/specification "
            "copy, or wait for the value-dedup workstream if this is expected drift."
        ),
    )


# --- [5] tm duplicate (snapshot) ------------------------------------------------
def check_tm_duplicate(root: Path) -> list[dict]:
    rows = _read_csv(root / "Status_Words.csv")
    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        en = _t(row.get("en"))
        if en:
            counts[en] += 1
    return [{"en": en, "count": count} for en, count in counts.items() if count > 1]


def _tm_duplicate_json(raw: dict[str, Any], run_id: str) -> dict[str, Any]:
    en = _t(raw.get("en"))
    return _normalized_finding(
        run_id=run_id,
        rule="tm_duplicate",
        severity="FAIL",
        table="Status_Words",
        file="Status_Words.csv",
        lang="en",
        field="en",
        source_ref=_source_ref(
            kind="status_word",
            table="Status_Words",
            file="Status_Words.csv",
            key=en,
        ),
        message=f"Duplicate status-word English key {en!r} appears in the snapshot.",
        evidence={
            "en": en,
            "count": raw.get("count"),
        },
        suggested_action="Reconcile and remove the duplicate Translation_Memory/status-word source row.",
    )


def _render(name: str, severity: str, findings: list, render_one) -> bool:
    """Print one check's result line + findings. Return True if it counts as a failure."""
    ok = not findings
    mark = "PASS" if ok else (severity)
    dots = "." * max(2, 34 - len(name))
    print(f"  [{name}] {dots} {mark}" + ("" if ok else f" ({len(findings)})"))
    for item in findings[:12]:
        print("        - " + render_one(item))
    if len(findings) > 12:
        print(f"        … +{len(findings) - 12} more")
    return (not ok) and severity == "FAIL"


def _check_specs(root: Path, langs: tuple[str, ...]) -> list[CheckSpec]:
    return [
        CheckSpec(
            name="status-word consistency",
            rule="status_word_consistency",
            severity="FAIL",
            findings=check_status_word_consistency(root, langs),
            render_one=lambda f: (
                f"{f['lang']} · {f['icon']}: non-canonical prefix {f['prefix']!r}  | {f['line']!r}"
            ),
            normalize_one=_status_word_json,
        ),
        CheckSpec(
            name="english residue",
            rule="english_residue",
            severity="FAIL",
            findings=check_english_residue(root, langs),
            render_one=lambda f: f"{f['file']} [{f['lang']}]: {f['token']!r} in {f['text']!r}",
            normalize_one=_english_residue_json,
        ),
        CheckSpec(
            name="slot-key collision",
            rule="slot_key_collision",
            severity="FAIL",
            findings=check_slot_key_collision(root),
            render_one=lambda f: f"{f['spec_row_key']} ×{f['count']}  ({', '.join(f['rows'])})",
            normalize_one=_slot_key_collision_json,
        ),
        CheckSpec(
            name="spec<->overview drift",
            rule="spec_overview_drift",
            severity="WARN",
            findings=check_spec_overview_drift(root, langs),
            render_one=lambda f: (
                f"{f['document_key']} · {f['row_key']} [{f['lang']}]: "
                f"spec={f['spec']} overview={f['overview']}"
            ),
            normalize_one=_spec_overview_drift_json,
        ),
        CheckSpec(
            name="tm duplicate (snapshot)",
            rule="tm_duplicate",
            severity="FAIL",
            findings=check_tm_duplicate(root),
            render_one=lambda f: f"en={f['en']!r} appears ×{f['count']}",
            normalize_one=_tm_duplicate_json,
        ),
    ]


def _json_report(
    *,
    root: Path,
    langs: tuple[str, ...],
    run_id: str,
    checks: list[CheckSpec],
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    findings = [
        check.normalize_one(raw_finding, run_id)
        for check in checks
        for raw_finding in check.findings
    ]
    # F1: resolve findings to live Feishu record ids when a source_record_index
    # sidecar is present in the snapshot; otherwise they stay snapshot_only.
    findings = resolve_findings(findings, root)
    fail_count = sum(1 for finding in findings if finding["severity"] == "FAIL")
    warn_count = sum(1 for finding in findings if finding["severity"] == "WARN")
    rule_counts = {
        check.rule: len(check.findings)
        for check in checks
    }
    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "run_id": run_id,
        "data_root": root.as_posix(),
        "langs": list(langs),
        "result": "FAIL" if fail_count else "OK",
        "summary": {
            "total": len(findings),
            "fail": fail_count,
            "warn": warn_count,
            "info": sum(1 for finding in findings if finding["severity"] == "INFO"),
            "rules": rule_counts,
            "unresolved_record_count": sum(
                1 for finding in findings if finding.get("record_id") is None
            ),
        },
        "findings": findings,
    }
    if metadata:
        report["metadata"] = metadata
    return report


def _markdown_cell(value: object) -> str:
    text = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value or "")
    return text.replace("\n", " ").replace("|", "\\|")


def _markdown_report(report: dict[str, Any]) -> str:
    metadata = report.get("metadata") or {}
    summary = report["summary"]
    lines = [
        "# Content QC Report",
        "",
        "## Run",
        "",
        f"- Run ID: `{report['run_id']}`",
        f"- Result: `{report['result']}`",
        f"- Data root: `{report['data_root']}`",
        f"- Languages: `{', '.join(report['langs'])}`",
        f"- Target: `{metadata.get('target', 'snapshot')}`",
        f"- Git ref: `{metadata.get('git_ref') or 'unknown'}`",
        f"- Started at: `{metadata.get('started_at') or 'unknown'}`",
        f"- Finished at: `{metadata.get('finished_at') or 'unknown'}`",
        f"- Command: `{metadata.get('command') or 'unknown'}`",
        "",
        "## Summary",
        "",
        f"- Total findings: `{summary['total']}`",
        f"- Fail: `{summary['fail']}`",
        f"- Warn: `{summary['warn']}`",
        f"- Unresolved records: `{summary['unresolved_record_count']}`",
        "",
        "## Rule Counts",
        "",
        "| Rule | Count |",
        "| --- | ---: |",
    ]
    for rule, count in summary["rules"].items():
        lines.append(f"| `{rule}` | {count} |")

    lines.extend(
        [
            "",
            "## Findings",
            "",
        ]
    )
    findings = report["findings"]
    if not findings:
        lines.append("No findings.")
    else:
        lines.extend(
            [
                "| Severity | Rule | Source | Record(s) | Lang | Field | Message | Evidence |",
                "| --- | --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for finding in findings:
            source = finding.get("source_ref") or f"{finding.get('file')}#{finding.get('table')}"
            record_ids = finding.get("record_ids") or ([finding["record_id"]] if finding.get("record_id") else [])
            records_cell = ", ".join(record_ids) if record_ids else (finding.get("resolution_status") or "-")
            lines.append(
                "| "
                + " | ".join(
                    [
                        _markdown_cell(finding.get("severity")),
                        f"`{_markdown_cell(finding.get('rule'))}`",
                        _markdown_cell(source),
                        _markdown_cell(records_cell),
                        _markdown_cell(finding.get("lang") or "-"),
                        _markdown_cell(finding.get("field") or "-"),
                        _markdown_cell(finding.get("message")),
                        _markdown_cell(finding.get("evidence")),
                    ]
                )
                + " |"
            )
    return "\n".join(lines) + "\n"


def _default_report_dir(run_id: str) -> Path:
    return get_paths().content_qc_reports_dir / _safe_path_token(run_id)


def _write_local_reports(report: dict[str, Any], report_dir: Path) -> dict[str, Path]:
    report_dir.mkdir(parents=True, exist_ok=True)
    findings_path = report_dir / "findings.json"
    markdown_path = report_dir / "report.md"
    findings_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(_markdown_report(report), encoding="utf-8")
    return {"json": findings_path, "markdown": markdown_path}


def _render_text_report(*, root: Path, langs: tuple[str, ...], checks: list[CheckSpec]) -> bool:
    print(f"content-lint  (data-root: {root}, langs: {','.join(langs)})")
    print("=" * 60)
    failed = False
    for check in checks:
        failed |= _render(check.name, check.severity, check.findings, check.render_one)
    print("-" * 60)
    print(f"RESULT: {'FAIL' if failed else 'OK'}  (WARN-level findings do not fail the gate)")
    return failed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Content-quality lint for the phase2 snapshot.")
    parser.add_argument("--data-root", default="data/phase2", help="phase2 snapshot dir")
    parser.add_argument("--langs", default=",".join(DEFAULT_LANGS), help="comma-separated langs")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON instead of text")
    parser.add_argument(
        "--write-report",
        action="store_true",
        help="write findings.json and report.md under the default local QC report directory",
    )
    parser.add_argument(
        "--report-dir",
        help="write findings.json and report.md to this directory; implies --write-report",
    )
    parser.add_argument(
        "--run-id",
        default="content-lint-local",
        help="run identifier to include in JSON output; keep stable in tests and reports",
    )
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    args = parser.parse_args(raw_argv)

    root = Path(args.data_root)
    langs = tuple(part.strip() for part in args.langs.split(",") if part.strip())
    started_at = _utc_now()
    checks = _check_specs(root, langs)
    run_id = str(args.run_id or "").strip() or "content-lint-local"
    metadata = {
        "target": "snapshot",
        "git_ref": _git_ref(),
        "started_at": started_at,
        "finished_at": _utc_now(),
        "command": shlex.join(["tools/content_lint.py", *raw_argv]),
    }
    report = _json_report(root=root, langs=langs, run_id=run_id, checks=checks, metadata=metadata)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        failed = report["result"] == "FAIL"
    else:
        failed = _render_text_report(root=root, langs=langs, checks=checks)
    if args.write_report or args.report_dir:
        report_dir = Path(args.report_dir) if args.report_dir else _default_report_dir(run_id)
        try:
            written = _write_local_reports(report, report_dir)
        except OSError as exc:
            print(f"WARNING: failed to write QC report: {exc}", file=sys.stderr)
        else:
            if not args.json:
                print(f"REPORT: {written['json']} ; {written['markdown']}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
