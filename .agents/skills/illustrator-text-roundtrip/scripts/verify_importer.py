#!/usr/bin/env python3
"""Regression checks for Illustrator_Text_Importer.jsx.

The importer is ExtendScript, so it is exercised through ``mock_illustrator.js``
(a stand-in for Illustrator's text DOM) under Node. Every case below is a shape
that actually appeared in production packaging artwork and that a naive
frame-level ``contents =`` assignment gets wrong.

Run directly::

    python3 .agents/skills/illustrator-text-roundtrip/scripts/verify_importer.py

Exits non-zero if any case fails. Requires ``node`` on PATH; see
``tests/test_illustrator_text_roundtrip.py`` for the unittest wrapper that
skips when Node is unavailable.
"""
from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
HARNESS = SCRIPTS / "mock_illustrator.js"
IMPORTER = SCRIPTS / "Illustrator_Text_Importer.jsx"

BOLD = "Gilroy-Bold"
MEDIUM = "Gilroy-Medium"
REGULAR = "Gilroy-Regular"


def _run(text: str, font: str = REGULAR, size: float = 6.8, baseline: float = 0.0) -> dict:
    return {"text": text, "font": font, "size": size, "baseline": baseline}


# Six frames reproducing the real hazards, in the order the harness reports them
# as T001..T006.
FIXTURE = [
    # T001 — stored casing differs from the rendered all-caps result. The CSV must
    # key off what is stored in the frame, not what the artwork looks like.
    {"paragraphs": [[_run("Input PORTS", BOLD, 9.0)]]},
    # T002 — one frame, many paragraphs, several carrying a trailing space.
    {"paragraphs": [
        [_run("Product Name ", REGULAR, 7.0)],
        [_run("Model No. ", REGULAR, 7.0)],
        [_run("Cycle Life", REGULAR, 7.0)],
    ]},
    # T003 — bold label + regular value; the bold run owns the trailing space.
    {"paragraphs": [[_run("Long Lifespan: ", BOLD, 20.5), _run("6000 Cycles", MEDIUM, 20.5)]]},
    # T004 — same split, but the space belongs to the leading edge of run 2.
    {"paragraphs": [[_run("Seamless Auto-Switching:", BOLD, 20.5), _run(" UPS 10ms", MEDIUM, 20.5)]]},
    # T005 — two byte-identical superscript runs where one must go and one must
    # stay. Unreachable by text matching; this is why positional mode exists.
    {"paragraphs": [[
        _run("AC Output in Bypass Mode", REGULAR, 6.8),
        _run("1", REGULAR, 4.0),
        _run(" | Sortie CA en mode dérivation", REGULAR, 6.8),
        _run("1", REGULAR, 4.0),
    ]]},
    # T006 — bold prefix plus body, both deleted.
    {"paragraphs": [[
        _run("WARNING: ", BOLD, 6.8),
        _run("Cancer and Reproductive Harm - www.P65Warnings.ca.gov.", REGULAR, 6.8),
    ]]},
]

GLOSSARY = [
    ("Input PORTS", "PORTAS DE ENTRADA"),
    ("Product Name", "Nome do produto"),
    ("Model No.", "Nº do modelo"),
    ("Cycle Life", "Vida útil de ciclos"),
    ("Long Lifespan: ", "Longa vida útil: "),
    ("6000 Cycles", "6.000 ciclos"),
    ("Seamless Auto-Switching:", "Comutação automática sem interrupção:"),
    (" UPS 10ms", " UPS de 10 ms"),
    ("AC Output in Bypass Mode", "Saída CA no Modo Bypass"),
    (" | Sortie CA en mode dérivation", "[[DELETE]]"),
    ("WARNING: ", "[[DELETE]]"),
    ("Cancer and Reproductive Harm - www.P65Warnings.ca.gov.", "[[DELETE]]"),
    ("A String Not Present In The Document", "nunca usado"),
]


def write_glossary(path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.writer(fh)
        writer.writerow(["Source", "Target"])
        writer.writerows(GLOSSARY)


def invoke(node: str, work: Path, fixture: Path, csv_in: Path, report: Path,
           overrides: dict) -> tuple[list[dict], list[dict]]:
    """Run the importer under the mock DOM; return (report rows, frame states)."""
    proc = subprocess.run(
        [node, str(HARNESS), str(fixture), str(csv_in), str(report),
         json.dumps(overrides), str(IMPORTER)],
        capture_output=True, text=True, cwd=work,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"harness failed:\n{proc.stdout}\n{proc.stderr}")
    with report.open(newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    state = json.loads((report.with_suffix(report.suffix + ".doc.json")).read_text(encoding="utf-8"))
    return rows, state["frames"]


def by_label(frames: list[dict]) -> dict:
    return {f["label"]: f for f in frames}


def run_all(node: str) -> list[tuple[str, bool, str]]:
    results: list[tuple[str, bool, str]] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        results.append((name, bool(ok), detail))

    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        fixture = work / "fixture.json"
        fixture.write_text(json.dumps(FIXTURE, ensure_ascii=False), encoding="utf-8")
        glossary = work / "glossary.csv"
        write_glossary(glossary)

        # --- 1. dry run must not touch the document -----------------------
        dry_report = work / "dryrun.csv"
        dry_rows, dry_frames = invoke(
            node, work, fixture, glossary, dry_report,
            {"Dry run": True, "Match ignoring surrounding spaces": True, "Include locked": True},
        )
        dry = by_label(dry_frames)
        check("dry run leaves the document untouched",
              dry["T003"]["contents"] == "Long Lifespan: 6000 Cycles",
              dry["T003"]["contents"])
        check("dry run still reports what would change",
              any(r["Action"] == "REPLACE" for r in dry_rows))

        # --- 2. glossary apply --------------------------------------------
        applied_report = work / "applied.csv"
        app_rows, app_frames = invoke(
            node, work, fixture, glossary, applied_report,
            {"Dry run": False, "Match ignoring surrounding spaces": True, "Include locked": True},
        )
        app = by_label(app_frames)

        check("stored casing is matched, not the rendered all-caps form",
              app["T001"]["contents"] == "PORTAS DE ENTRADA", app["T001"]["contents"])

        check("multi-paragraph frame keeps its paragraph breaks",
              app["T002"]["contents"] == "Nome do produto \rNº do modelo \rVida útil de ciclos",
              app["T002"]["contents"])

        # The whole point: bold/medium survive a run-level replacement.
        check("mixed-run paragraph keeps both fonts (trailing-space case)",
              app["T003"]["contents"] == "Longa vida útil: 6.000 ciclos"
              and app["T003"]["runs"] == [f"{BOLD}@20.5", f"{MEDIUM}@20.5"],
              f'{app["T003"]["contents"]!r} runs={app["T003"]["runs"]}')

        check("mixed-run paragraph keeps both fonts (leading-space case)",
              app["T004"]["contents"] == "Comutação automática sem interrupção: UPS de 10 ms"
              and app["T004"]["runs"] == [f"{BOLD}@20.5", f"{MEDIUM}@20.5"],
              f'{app["T004"]["contents"]!r} runs={app["T004"]["runs"]}')

        check("[[DELETE]] removes text including its whitespace",
              app["T006"]["contents"] == "", repr(app["T006"]["contents"]))

        # Pinned limitation, not a passing behaviour: glossary mode keeps both
        # superscripts because it cannot tell the two "1" runs apart.
        check("glossary mode cannot separate identical runs (known limit)",
              app["T005"]["contents"] == "Saída CA no Modo Bypass11",
              app["T005"]["contents"])

        check("unused CSV rows are reported",
              any(r["Action"] == "CSV_ROW_UNUSED" for r in app_rows))

        # --- 3. positional round-trip of the importer's own report ---------
        filled = work / "dryrun_filled.csv"
        rows = list(dry_rows)
        ones = [r for r in rows
                if r["Frame"] == "T005" and r["Paragraph"] == "1" and r["SourceText"] == "1"]
        check("report addresses identical runs separately", len(ones) == 2, str(len(ones)))
        if ones:
            last = max(ones, key=lambda r: int(r["RangeStart"]))
            last["TargetText"] = "[[DELETE]]"
        with filled.open("w", newline="", encoding="utf-8-sig") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

        pos_report = work / "positional.csv"
        pos_rows, pos_frames = invoke(
            node, work, fixture, filled, pos_report,
            {"Dry run": False, "Include locked": True},
        )
        pos = by_label(pos_frames)

        check("positional mode deletes one superscript and keeps the other",
              pos["T005"]["contents"] == "Saída CA no Modo Bypass1"
              and f"{REGULAR}@4" in pos["T005"]["runs"],
              f'{pos["T005"]["contents"]!r} runs={pos["T005"]["runs"]}')

        check("positional round-trip reproduces the glossary result elsewhere",
              pos["T003"]["contents"] == "Longa vida útil: 6.000 ciclos"
              and pos["T004"]["contents"] == "Comutação automática sem interrupção: UPS de 10 ms"
              and pos["T006"]["contents"] == "",
              f'{pos["T003"]["contents"]!r} / {pos["T004"]["contents"]!r}')

        check("deletions round-trip through the report as [[DELETE]]",
              any(r["Action"] == "DELETE" and r["TargetText"] == "[[DELETE]]" for r in dry_rows))

        # --- 4. a stale report is refused, not misapplied -----------------
        stale = work / "dryrun_stale.csv"
        rows2 = json.loads(json.dumps(rows))  # deep copy
        tampered = 0
        for r in rows2:
            if r["Frame"] == "T001":
                r["SourceText"] = "Input PORTS (someone edited the artwork)"
                tampered += 1
        with stale.open("w", newline="", encoding="utf-8-sig") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows2[0].keys()))
            writer.writeheader()
            writer.writerows(rows2)

        stale_report = work / "stale.csv"
        stale_rows, stale_frames = invoke(
            node, work, fixture, stale, stale_report,
            {"Dry run": False, "Include locked": True},
        )
        st = by_label(stale_frames)
        check("stale row is refused", tampered > 0
              and any(r["Action"] == "REFUSED_STALE" for r in stale_rows))
        check("refused position is left untouched",
              st["T001"]["contents"] == "Input PORTS", st["T001"]["contents"])
        check("a refusal does not block the other positions",
              st["T003"]["contents"] == "Longa vida útil: 6.000 ciclos",
              st["T003"]["contents"])

    return results


def main() -> int:
    node = shutil.which("node")
    if not node:
        print("node not found on PATH; cannot exercise the ExtendScript importer.")
        return 2
    if not HARNESS.exists() or not IMPORTER.exists():
        print(f"missing harness or importer under {SCRIPTS}")
        return 2

    results = run_all(node)
    width = max(len(name) for name, _, _ in results)
    failed = 0
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}"
              + (f"   -> {detail}" if (detail and not ok) else ""))
        if not ok:
            failed += 1
    print(f"\n{len(results) - failed}/{len(results)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
