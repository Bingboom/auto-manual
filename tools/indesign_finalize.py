#!/usr/bin/env python3
"""Open same-source IDML in InDesign, save INDD, export PDF, and preflight."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
import unicodedata
import zipfile
from collections import defaultdict
from pathlib import Path

try:
    from tools.script_bootstrap import bootstrap_repo_root
    from tools.toolchain_provenance import indesign_version
except ModuleNotFoundError:  # direct script execution
    from script_bootstrap import bootstrap_repo_root
    from toolchain_provenance import indesign_version


ROOT = bootstrap_repo_root(__file__, parent_count=1)
JSX = ROOT / "tools" / "idml" / "indesign_finalize.jsx"
BATCH_JSX = ROOT / "tools" / "idml" / "indesign_finalize_batch.jsx"
# Milestone K7: the committed InDesign version pin. The finalize leg is the one
# delivery step outside CI, so version drift between hosts is invisible unless
# checked here, at finalize time.
VERSION_PIN = ROOT / "tools" / "idml" / "indesign_version_pin.json"
DEFAULT_PDF_PRESET = "[PDF/X-4:2008 (Japan)]"
DEFAULT_OUTPUT_INTENT = "Japan Color 2001 Coated"
DEFAULT_OUTPUT_CONDITION = "JC200103"
DEFAULT_PDFX = "PDF/X-4"


# distinguishes "caller did not supply a version" (collect from this host) from
# an explicit None ("this host has no InDesign") in check/write below
_COLLECT = object()


def check_version_pin(pin_path: Path = VERSION_PIN, actual: str | None | object = _COLLECT) -> tuple[str, str]:
    """Compare this host's InDesign against the committed pin.

    Returns ``(status, message)`` with status in ``match`` / ``mismatch`` /
    ``no_pin`` / ``no_indesign``. Exact string comparison on the provenance
    collector's output (app bundle name + CFBundleShortVersionString) — even a
    patch-level difference makes finalize output non-comparable across hosts,
    so a deliberate upgrade re-pins instead of loosening the match.
    """
    if actual is _COLLECT:
        actual = indesign_version()
    if not pin_path.is_file():
        return "no_pin", (
            f"no committed InDesign version pin at {pin_path}; "
            "seed it on the blessed host with --write-pin"
        )
    expected = json.loads(pin_path.read_text(encoding="utf-8")).get("expected")
    if not actual:
        return "no_indesign", (
            f"no InDesign installation detected on this host (pin expects: {expected!r})"
        )
    if actual == expected:
        return "match", f"InDesign matches the committed pin: {actual}"
    return "mismatch", (
        f"InDesign version MISMATCH: this host has {actual!r} but the committed pin "
        f"expects {expected!r}. Finalize output from a drifted InDesign is not "
        "comparable across hosts. Either run on a matching host, or — for a "
        "deliberate upgrade — re-pin with --write-pin and upgrade every finalize "
        "host together (see code-as-doc/dev/indesign_second_host_runbook.md)."
    )


def write_version_pin(pin_path: Path = VERSION_PIN, actual: str | None | object = _COLLECT) -> str:
    """Seed/refresh the committed pin from this host's InDesign (K7 --write-pin)."""
    if actual is _COLLECT:
        actual = indesign_version()
    if not actual:
        raise RuntimeError("cannot write a version pin: no InDesign installation detected")
    from datetime import date

    pin_path.parent.mkdir(parents=True, exist_ok=True)
    pin_path.write_text(
        json.dumps(
            {
                "expected": actual,
                "pinned_at": date.today().isoformat(),
                "note": (
                    "Milestone K7: the finalize leg's pinned InDesign version. Every "
                    "finalize host must match it (tools/indesign_finalize.py "
                    "--check-host). Re-pin ONLY on a deliberate upgrade, with "
                    "--write-pin, and upgrade every finalize host together."
                ),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return actual


def _idml_document_language(path: Path) -> str:
    if not path.is_file():
        return ""
    try:
        with zipfile.ZipFile(path) as package:
            designmap = package.read("designmap.xml").decode("utf-8")
    except (KeyError, OSError, UnicodeDecodeError, zipfile.BadZipFile):
        return ""
    match = re.search(r'\bLabel="hb:language=([A-Za-z0-9_-]+)"', designmap)
    return match.group(1) if match else ""


def _job(args: argparse.Namespace) -> dict[str, str]:
    input_idml = Path(args.idml).resolve()
    return {
        "input_idml": str(input_idml),
        "document_language": _idml_document_language(input_idml),
        "output_indd": str(Path(args.indd).resolve()),
        "output_pdf": str(Path(args.pdf).resolve()),
        "report_json": str(Path(args.report).resolve()),
        "pdf_preset": args.pdf_preset,
        "output_intent": args.output_intent,
        "output_condition": args.output_condition,
        "pdfx": args.pdfx,
    }


def _parse_pdf_export_compliance(
    *,
    pdfinfo_text: str,
    pdf_bytes: bytes,
    expected_pdfx: str,
    expected_output_intent: str,
    expected_output_condition: str,
) -> dict[str, object]:
    subtype = re.search(r"(?m)^PDF subtype:\s+([^\r\n]+)", pdfinfo_text)
    actual_pdfx = subtype.group(1).strip() if subtype else None
    pdfx_match = actual_pdfx == expected_pdfx
    intent_match = expected_output_intent.encode("ascii") in pdf_bytes
    condition_match = expected_output_condition.encode("ascii") in pdf_bytes
    return {
        "expected_pdfx": expected_pdfx,
        "actual_pdfx": actual_pdfx,
        "pdfx_match": pdfx_match,
        "expected_output_intent": expected_output_intent,
        "output_intent_match": intent_match,
        "expected_output_condition": expected_output_condition,
        "output_condition_match": condition_match,
        "pass": pdfx_match and intent_match and condition_match,
    }


def _pdf_export_compliance(path: Path, job: dict[str, str]) -> dict[str, object]:
    result = subprocess.run(
        ["pdfinfo", str(path)], check=True, capture_output=True, text=True,
    )
    return _parse_pdf_export_compliance(
        pdfinfo_text=result.stdout,
        pdf_bytes=path.read_bytes(),
        expected_pdfx=job["pdfx"],
        expected_output_intent=job["output_intent"],
        expected_output_condition=job["output_condition"],
    )


def _pdf_missing_glyphs(path: Path) -> list[dict[str, object]]:
    """Return visible U+FFFD or .notdef uses from every PDF text trace.

    PyMuPDF's trace walks page text after placed PDF form XObjects have been
    assembled into the exported document, so this covers both native InDesign
    text and text retained inside placed graphics.  ``glyph_id == 0`` is the
    PDF font's .notdef glyph; text extraction alone is insufficient because a
    ToUnicode map can still return the intended character for that glyph.
    """

    import fitz

    findings: list[dict[str, object]] = []
    with fitz.open(path) as document:
        for page_index, page in enumerate(document, start=1):
            for span_index, span in enumerate(page.get_texttrace(), start=1):
                font = str(span.get("font") or "")
                for char_index, raw_char in enumerate(
                    span.get("chars", ()), start=1,
                ):
                    if len(raw_char) < 2:
                        raise ValueError(
                            "PDF text trace character is missing codepoint/glyph id"
                        )
                    codepoint = int(raw_char[0])
                    glyph_id = int(raw_char[1])
                    try:
                        character = chr(codepoint)
                    except ValueError as exc:
                        raise ValueError(
                            f"PDF text trace contains invalid codepoint: {codepoint}"
                        ) from exc
                    visible = (
                        not character.isspace()
                        and not unicodedata.category(character).startswith("C")
                    )
                    reasons: list[str] = []
                    if codepoint == 0xFFFD:
                        reasons.append("replacement_character")
                    if glyph_id == 0 and visible:
                        reasons.append("notdef_glyph")
                    if not reasons:
                        continue
                    bbox = raw_char[3] if len(raw_char) > 3 else None
                    findings.append({
                        "page": page_index,
                        "span": span_index,
                        "character_index": char_index,
                        "character": character,
                        "codepoint": f"U+{codepoint:04X}",
                        "glyph_id": glyph_id,
                        "font": font,
                        "reasons": reasons,
                        **(
                            {"bbox": [float(value) for value in bbox]}
                            if bbox is not None
                            else {}
                        ),
                    })
    return findings


def _clear_outputs(job: dict[str, str]) -> None:
    for key in ("output_indd", "output_pdf", "report_json"):
        output = Path(job[key])
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.exists():
            output.unlink()


def _run_applescript(wrapper: Path, *, application: str, job_count: int) -> None:
    script_timeout = 600 * max(1, job_count)
    process_timeout = script_timeout + 60
    apple_script = (
        f"with timeout of {script_timeout} seconds\n"
        f'tell application "{application}" to do script '
        f'(POSIX file {json.dumps(str(wrapper))}) language javascript\n'
        "end timeout"
    )
    subprocess.run(
        ["osascript", "-e", apple_script], check=True, timeout=process_timeout,
    )


def _run_jsx(job: dict[str, str], *, application: str) -> None:
    _clear_outputs(job)
    with tempfile.TemporaryDirectory(prefix="auto-manual-indesign-") as td:
        temp = Path(td)
        job_path = temp / "job.json"
        wrapper = temp / "run.jsx"
        job_path.write_text(json.dumps(job, ensure_ascii=False, indent=2), encoding="utf-8")
        wrapper.write_text(
            "var HB_JOB_PATH = " + json.dumps(str(job_path)) + ";\n"
            + JSX.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        _run_applescript(wrapper, application=application, job_count=1)


def _run_jsx_jobs(jobs: list[dict[str, str]], *, application: str) -> None:
    """Finalize one application-homogeneous job group in one InDesign script."""
    if not jobs:
        return
    for job in jobs:
        _clear_outputs(job)
    with tempfile.TemporaryDirectory(prefix="auto-manual-indesign-batch-") as td:
        temp = Path(td)
        batch_jobs: list[dict[str, str]] = []
        for index, job in enumerate(jobs):
            job_path = temp / f"job-{index:04d}.json"
            job_path.write_text(
                json.dumps(job, ensure_ascii=False, indent=2), encoding="utf-8",
            )
            batch_jobs.append({
                "job_id": job.get("job_id", ""),
                "job_path": str(job_path),
                "report_json": job["report_json"],
            })
        transport_report = temp / "batch-report.json"
        wrapper = temp / "run-batch.jsx"
        wrapper.write_text(
            "var HB_BATCH_JOBS = " + json.dumps(batch_jobs, ensure_ascii=False) + ";\n"
            "var HB_FINALIZE_SCRIPT_PATH = " + json.dumps(str(JSX)) + ";\n"
            "var HB_BATCH_REPORT_PATH = " + json.dumps(str(transport_report)) + ";\n"
            + BATCH_JSX.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        _run_applescript(wrapper, application=application, job_count=len(jobs))
        if not transport_report.is_file():
            raise RuntimeError("InDesign batch returned without a transport report")


def _collect_finalize_result(
    job: dict[str, str], *, pin_status: str,
) -> dict[str, object]:
    job_id = job.get("job_id", "")
    report_path = Path(job["report_json"])
    if not report_path.is_file():
        return {
            "job_id": job_id,
            "success": False,
            "exit_code": 1,
            "error": f"finalize report not found: {report_path}",
        }
    report = json.loads(report_path.read_text(encoding="utf-8"))
    post_reopen = report.get("post_reopen") or {}
    requires_reopen_gate = report.get("schema_version") == "indesign-preflight/v2"
    reopen_gate_pass = (
        not requires_reopen_gate
        or (
            post_reopen.get("completed") is True
            and post_reopen.get("page_count") == report.get("page_count")
            and post_reopen.get("story_count") == report.get("story_count")
            and not post_reopen.get("overset_stories")
            and not post_reopen.get("overset_table_cells")
            and not post_reopen.get("missing_fonts")
            and not post_reopen.get("bad_links")
        )
    )
    output_pdf = Path(job["output_pdf"])
    if output_pdf.is_file():
        compliance = _pdf_export_compliance(output_pdf, job)
        report["pdf_export_validation"] = compliance
        try:
            missing_glyphs = _pdf_missing_glyphs(output_pdf)
            glyph_validation: dict[str, object] = {
                "pass": not missing_glyphs,
                "finding_count": len(missing_glyphs),
            }
        except Exception as exc:
            missing_glyphs = []
            glyph_validation = {
                "pass": False,
                "finding_count": 0,
                "error": str(exc),
            }
        report["missing_glyphs"] = missing_glyphs
        report["pdf_glyph_validation"] = glyph_validation
        report["success"] = (
            bool(report.get("success"))
            and bool(compliance["pass"])
            and bool(glyph_validation["pass"])
            and reopen_gate_pass
        )
        if not compliance["pass"] and not report.get("error"):
            report["error"] = "exported PDF does not satisfy the PDF/X output contract"
        if not glyph_validation["pass"] and not report.get("error"):
            report["error"] = (
                "exported PDF contains replacement or .notdef glyphs"
                if missing_glyphs
                else "exported PDF glyph validation could not be completed"
            )
        if not reopen_gate_pass and not report.get("error"):
            report["error"] = (
                "saved INDD failed the mandatory close/reopen preflight gate"
            )
    report["toolchain"] = {
        "indesign_actual": indesign_version(),
        "version_pin_status": pin_status,
    }
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )
    success = bool(report.get("success"))
    status = "OK" if success else "PREFLIGHT FAIL"
    overset = (
        len(report.get("overset_stories", []))
        + len(report.get("overset_table_cells", []))
        + len(post_reopen.get("overset_stories", []))
        + len(post_reopen.get("overset_table_cells", []))
    )
    missing_fonts = (
        len(report.get("missing_fonts", []))
        + len(post_reopen.get("missing_fonts", []))
    )
    missing_glyphs = len(report.get("missing_glyphs", []))
    bad_links = (
        len(report.get("bad_links", []))
        + len(post_reopen.get("bad_links", []))
    )
    overset_pages = _overset_pages(report)
    print(
        f"[indesign-finalize] {status}: pages={report.get('page_count')} "
        f"overset={overset} fonts={missing_fonts} glyphs={missing_glyphs} "
        f"links={bad_links} "
        f"overset_pages={','.join(str(page) for page in overset_pages) or '-'} "
        f"report={job['report_json']}"
    )
    if report.get("error"):
        print(f"[indesign-finalize] ERROR: {report['error']}")
    return {
        "job_id": job_id,
        "success": success,
        "exit_code": 0 if success else 1,
        "report_json": job["report_json"],
        "page_count": report.get("page_count"),
        "overset_count": overset,
        "missing_fonts_count": missing_fonts,
        "missing_glyphs_count": missing_glyphs,
        "bad_links_count": bad_links,
        "overset_pages": overset_pages,
        **({"error": report["error"]} if report.get("error") else {}),
    }


def _overset_pages(report: dict[str, object]) -> list[int]:
    """Return unique physical pages from every structured overset finding."""

    pages: set[int] = set()
    states = [report, report.get("post_reopen") or {}]
    for state in states:
        if not isinstance(state, dict):
            continue
        for finding in state.get("overset_table_cells", []) or []:
            if isinstance(finding, dict):
                page = finding.get("page")
                if isinstance(page, int) and page > 0:
                    pages.add(page)
        for finding in state.get("overset_stories", []) or []:
            if not isinstance(finding, dict):
                continue
            for container in finding.get("text_containers", []) or []:
                if isinstance(container, dict):
                    page = container.get("page")
                    if isinstance(page, int) and page > 0:
                        pages.add(page)
    return sorted(pages)


def run_finalize_job(
    job: dict[str, str],
    *,
    application: str,
    pin_status: str,
    pin_message: str,
) -> dict[str, object]:
    """Run one already validated finalize job and return a report summary.

    Version-pin validation belongs to the caller because a batch should check
    the host once and then isolate failures per job. The single-job CLI also
    uses this function so both entrypoints retain the same preflight contract.
    """
    marker = "WARNING" if pin_status != "match" else "version-pin"
    print(f"[indesign-finalize] {marker} {pin_status}: {pin_message}")
    job_id = job.get("job_id", "")
    input_idml = job["input_idml"]
    if not Path(input_idml).is_file():
        error = f"IDML not found: {input_idml}"
        print(f"[indesign-finalize] ERROR: {error}")
        return {"job_id": job_id, "success": False, "exit_code": 1, "error": error}

    _run_jsx(job, application=application)
    return _collect_finalize_result(job, pin_status=pin_status)


def run_finalize_jobs(
    jobs: list[dict[str, str]], *, pin_status: str, pin_message: str,
) -> list[dict[str, object]]:
    """Run each application group in one JSX loop and preserve manifest order."""
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for job in jobs:
        grouped[job["application"]].append(job)

    results: dict[str, dict[str, object]] = {}
    for application, application_jobs in grouped.items():
        marker = "WARNING" if pin_status != "match" else "version-pin"
        print(
            f"[indesign-finalize] {marker} {pin_status}: {pin_message}; "
            f"application={application} jobs={len(application_jobs)}"
        )
        runnable: list[dict[str, str]] = []
        for job in application_jobs:
            if not Path(job["input_idml"]).is_file():
                results[job["job_id"]] = {
                    "job_id": job["job_id"],
                    "success": False,
                    "exit_code": 1,
                    "error": f"IDML not found: {job['input_idml']}",
                }
            else:
                runnable.append(job)
        if not runnable:
            continue
        try:
            _run_jsx_jobs(runnable, application=application)
        except Exception as exc:
            for job in runnable:
                results[job["job_id"]] = {
                    "job_id": job["job_id"],
                    "success": False,
                    "exit_code": 1,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            continue
        for job in runnable:
            try:
                results[job["job_id"]] = _collect_finalize_result(
                    job, pin_status=pin_status,
                )
            except Exception as exc:
                results[job["job_id"]] = {
                    "job_id": job["job_id"],
                    "success": False,
                    "exit_code": 1,
                    "error": f"{type(exc).__name__}: {exc}",
                }
    return [results[job["job_id"]] for job in jobs]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs", type=Path,
                        help="run an isolated batch from an indesign-finalize-jobs/v1 manifest")
    parser.add_argument("--aggregate-report", type=Path,
                        help="override the batch aggregate report path")
    parser.add_argument("--idml")
    parser.add_argument("--indd")
    parser.add_argument("--pdf")
    parser.add_argument("--report")
    parser.add_argument("--pdf-preset", default=DEFAULT_PDF_PRESET)
    parser.add_argument("--output-intent", default=DEFAULT_OUTPUT_INTENT)
    parser.add_argument("--output-condition", default=DEFAULT_OUTPUT_CONDITION)
    parser.add_argument("--pdfx", default=DEFAULT_PDFX)
    parser.add_argument("--application", default="Adobe InDesign 2026")
    parser.add_argument("--check-host", action="store_true",
                        help="only check this host's InDesign against the committed pin, then exit (0=match)")
    parser.add_argument("--write-pin", action="store_true",
                        help="(re)seed the committed version pin from this host's InDesign — deliberate upgrades only")
    parser.add_argument("--allow-version-mismatch", action="store_true",
                        help="proceed despite a pin mismatch; the mismatch is still recorded in the report")
    args = parser.parse_args()

    if args.jobs:
        if args.check_host or args.write_pin:
            parser.error("--jobs cannot be combined with --check-host or --write-pin")
        if any(getattr(args, key) for key in ("idml", "indd", "pdf", "report")):
            parser.error("--jobs cannot be combined with single-job output arguments")
        try:
            from tools.indesign_finalize_jobs import run_jobs_manifest

            return run_jobs_manifest(
                args.jobs,
                aggregate_report=args.aggregate_report,
                allow_version_mismatch=args.allow_version_mismatch,
            )
        except ValueError as exc:
            print(f"[indesign-finalize] ERROR: {exc}")
            return 2

    if args.write_pin:
        try:
            actual = write_version_pin()
        except RuntimeError as exc:
            print(f"[indesign-finalize] ERROR: {exc}")
            return 2
        print(f"[indesign-finalize] version pin written: {actual} -> {VERSION_PIN}")
        return 0
    pin_status, pin_message = check_version_pin()
    if args.check_host:
        print(f"[indesign-finalize] version-pin {pin_status}: {pin_message}")
        return 0 if pin_status == "match" else 2

    if not all((args.idml, args.indd, args.pdf, args.report)):
        parser.error("--idml, --indd, --pdf and --report are required to run finalize")
    if pin_status == "no_indesign":
        print(f"[indesign-finalize] ERROR: {pin_message}")
        return 2
    if pin_status == "mismatch" and not args.allow_version_mismatch:
        print(f"[indesign-finalize] ERROR: {pin_message}")
        print("[indesign-finalize] refusing to run; pass --allow-version-mismatch to override (recorded).")
        return 2
    job = _job(args)
    result = run_finalize_job(
        job,
        application=args.application,
        pin_status=pin_status,
        pin_message=pin_message,
    )
    return int(result["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
