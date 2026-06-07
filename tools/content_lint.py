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
import sys
from collections import defaultdict
from pathlib import Path

# Reuse the renderer's EXACT status-word matcher, so the lint checks precisely
# what the build will bold (single source of truth — no parallel logic to drift).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.csv_pages.renderers_lcd_icons import _match_status_prefix  # noqa: E402

# Non-English shipped EU languages.
DEFAULT_LANGS = ("fr", "es", "de", "it", "uk")

# Per-file language→column-suffix maps (the snapshot is not uniform: uk vs ukr).
_LCD_DESC = {"en": "en", "fr": "fr", "es": "es", "de": "de", "it": "it", "uk": "ukr"}
_TROUBLE = {"en": "en", "fr": "fr", "es": "es", "de": "de", "it": "it", "uk": "ukr"}
_TEXT = {"en": "en", "fr": "fr", "es": "es", "de": "de", "it": "it", "uk": "uk"}
_VALUE = {"en": "source", "fr": "fr", "es": "es", "de": "de", "it": "it", "uk": "uk"}

# English state words that should never survive into a localized column.
_ENGLISH_RESIDUE = ("On:", "Off:", "Blinking", "Flashing")

_TRUE = {"y", "yes", "true", "1"}


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
                        {"lang": lang, "icon": icon, "prefix": prefix, "line": line[:64]}
                    )
    return findings


# --- [2] english residue --------------------------------------------------------
def check_english_residue(root: Path, langs: tuple[str, ...]) -> list[dict]:
    targets = [
        ("lcd_icons_blocks.csv", "icon_desc_{s}", _LCD_DESC),
        ("troubleshooting_blocks.csv", "corrective_measures_{s}", _TROUBLE),
        ("Spec_Footnotes.csv", "Text_{s}", _TEXT),
        ("Spec_Notes.csv", "Text_{s}", _TEXT),
    ]
    findings: list[dict] = []
    for filename, pattern, suffix_map in targets:
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
                            {"file": filename, "lang": lang, "token": token, "text": value[:64]}
                        )
    return findings


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


# --- [5] tm duplicate (snapshot) ------------------------------------------------
def check_tm_duplicate(root: Path) -> list[dict]:
    rows = _read_csv(root / "Status_Words.csv")
    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        en = _t(row.get("en"))
        if en:
            counts[en] += 1
    return [{"en": en, "count": count} for en, count in counts.items() if count > 1]


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Content-quality lint for the phase2 snapshot.")
    parser.add_argument("--data-root", default="data/phase2", help="phase2 snapshot dir")
    parser.add_argument("--langs", default=",".join(DEFAULT_LANGS), help="comma-separated langs")
    args = parser.parse_args(argv)

    root = Path(args.data_root)
    langs = tuple(part.strip() for part in args.langs.split(",") if part.strip())
    print(f"content-lint  (data-root: {root}, langs: {','.join(langs)})")
    print("=" * 60)

    failed = False
    failed |= _render(
        "status-word consistency", "FAIL",
        check_status_word_consistency(root, langs),
        lambda f: f"{f['lang']} · {f['icon']}: non-canonical prefix {f['prefix']!r}  | {f['line']!r}",
    )
    failed |= _render(
        "english residue", "FAIL",
        check_english_residue(root, langs),
        lambda f: f"{f['file']} [{f['lang']}]: {f['token']!r} in {f['text']!r}",
    )
    failed |= _render(
        "slot-key collision", "FAIL",
        check_slot_key_collision(root),
        lambda f: f"{f['spec_row_key']} ×{f['count']}  ({', '.join(f['rows'])})",
    )
    failed |= _render(
        "spec<->overview drift", "WARN",
        check_spec_overview_drift(root, langs),
        lambda f: f"{f['document_key']} · {f['row_key']} [{f['lang']}]: spec={f['spec']} overview={f['overview']}",
    )
    failed |= _render(
        "tm duplicate (snapshot)", "FAIL",
        check_tm_duplicate(root),
        lambda f: f"en={f['en']!r} appears ×{f['count']}",
    )

    print("-" * 60)
    print(f"RESULT: {'FAIL' if failed else 'OK'}  (WARN-level findings do not fail the gate)")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
