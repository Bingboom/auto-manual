#!/usr/bin/env python3
"""Open same-source IDML in InDesign, save INDD, export PDF, and preflight."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path

try:
    from tools.script_bootstrap import bootstrap_repo_root
    from tools.toolchain_provenance import indesign_version
except ModuleNotFoundError:  # direct script execution
    from script_bootstrap import bootstrap_repo_root
    from toolchain_provenance import indesign_version


ROOT = bootstrap_repo_root(__file__, parent_count=1)
JSX = ROOT / "tools" / "idml" / "indesign_finalize.jsx"
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


def _job(args: argparse.Namespace) -> dict[str, str]:
    return {
        "input_idml": str(Path(args.idml).resolve()),
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


def _run_jsx(job: dict[str, str], *, application: str) -> None:
    for key in ("output_indd", "output_pdf", "report_json"):
        output = Path(job[key])
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.exists():
            output.unlink()
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
        apple_script = (
            "with timeout of 600 seconds\n"
            f'tell application "{application}" to do script '
            f'(POSIX file {json.dumps(str(wrapper))}) language javascript\n'
            "end timeout"
        )
        subprocess.run(["osascript", "-e", apple_script], check=True, timeout=660)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
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
    marker = "WARNING" if pin_status != "match" else "version-pin"
    print(f"[indesign-finalize] {marker} {pin_status}: {pin_message}")

    job = _job(args)
    if not Path(job["input_idml"]).is_file():
        print(f"[indesign-finalize] ERROR: IDML not found: {job['input_idml']}")
        return 1
    _run_jsx(job, application=args.application)
    report_path = Path(job["report_json"])
    report = json.loads(report_path.read_text(encoding="utf-8"))
    output_pdf = Path(job["output_pdf"])
    if output_pdf.is_file():
        compliance = _pdf_export_compliance(output_pdf, job)
        report["pdf_export_validation"] = compliance
        report["success"] = bool(report.get("success")) and bool(compliance["pass"])
        if not compliance["pass"] and not report.get("error"):
            report["error"] = "exported PDF does not satisfy the PDF/X output contract"
    report["toolchain"] = {
        "indesign_actual": indesign_version(),
        "version_pin_status": pin_status,
    }
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )
    status = "OK" if report.get("success") else "PREFLIGHT FAIL"
    print(
        f"[indesign-finalize] {status}: pages={report.get('page_count')} "
        f"overset={len(report.get('overset_stories', []))} "
        f"fonts={len(report.get('missing_fonts', []))} "
        f"links={len(report.get('bad_links', []))} report={job['report_json']}"
    )
    if report.get("error"):
        print(f"[indesign-finalize] ERROR: {report['error']}")
    return 0 if report.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
