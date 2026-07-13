#!/usr/bin/env python3
"""Open same-source IDML in InDesign, save INDD, export PDF, and preflight."""
from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ModuleNotFoundError:  # direct script execution
    from script_bootstrap import bootstrap_repo_root


ROOT = bootstrap_repo_root(__file__, parent_count=1)
JSX = ROOT / "tools" / "idml" / "indesign_finalize.jsx"


def _job(args: argparse.Namespace) -> dict[str, str]:
    return {
        "input_idml": str(Path(args.idml).resolve()),
        "output_indd": str(Path(args.indd).resolve()),
        "output_pdf": str(Path(args.pdf).resolve()),
        "report_json": str(Path(args.report).resolve()),
        "pdf_preset": args.pdf_preset,
    }


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
    parser.add_argument("--idml", required=True)
    parser.add_argument("--indd", required=True)
    parser.add_argument("--pdf", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--pdf-preset", default="[High Quality Print]")
    parser.add_argument("--application", default="Adobe InDesign 2026")
    args = parser.parse_args()
    job = _job(args)
    if not Path(job["input_idml"]).is_file():
        print(f"[indesign-finalize] ERROR: IDML not found: {job['input_idml']}")
        return 1
    _run_jsx(job, application=args.application)
    report = json.loads(Path(job["report_json"]).read_text(encoding="utf-8"))
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
