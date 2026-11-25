#!/usr/bin/env python3
"""Validate pure-ASCII ExtendScript and execute it in Adobe Illustrator on macOS."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Iterable

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_LIB = SCRIPT_DIR / "ai_edit_lib.jsx"


def find_non_ascii(text: str) -> list[tuple[int, int, str, str]]:
    """Return (line_no, col_no, char, unicode_escape) for every non-ASCII character."""
    hits: list[tuple[int, int, str, str]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        for col_no, ch in enumerate(line, start=1):
            code = ord(ch)
            if code >= 128:
                esc = f"\\u{code:04X}" if code <= 0xFFFF else f"\\u{{{code:X}}}"
                hits.append((line_no, col_no, ch, esc))
    return hits


def check_pure_ascii(text: str, label: str = "script") -> list[str]:
    """Return human-readable diagnostics for any non-ASCII character in text."""
    hits = find_non_ascii(text)
    if not hits:
        return []
    messages = [
        f"{label}: line {ln}, col {col}: non-ASCII character {ch!r} (use {esc})"
        for ln, col, ch, esc in hits[:20]
    ]
    if len(hits) > 20:
        messages.append(f"{label}: ... and {len(hits) - 20} more non-ASCII characters")
    return messages


def guard_distinct_paths(source: Path | None, output: Path | None) -> None:
    """Refuse to run when source and output resolve to the same file."""
    if source is None or output is None:
        return
    if source.resolve() == output.resolve():
        raise ValueError(
            f"Refusing to overwrite source master: --source and --out resolve to {source.resolve()}"
        )


def bundle_jsx(script_path: Path, lib_path: Path | None = None) -> str:
    """Return combined ExtendScript source, optionally prepending ai_edit_lib.jsx."""
    script_text = script_path.read_text(encoding="utf-8")
    if lib_path is None:
        return script_text
    lib_text = lib_path.read_text(encoding="utf-8")
    lines = script_text.splitlines(keepends=True)
    header: list[str] = []
    body_start = 0
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("#target"):
            header.append(line)
            body_start = idx + 1
        elif stripped == "" and idx == body_start:
            header.append(line)
            body_start = idx + 1
        else:
            break
    body = "".join(lines[body_start:])
    return "".join(header) + lib_text.rstrip() + "\n\n" + body


def scan_log_issues(log_text: str) -> list[str]:
    """Return WARNING/ERROR lines from an Illustrator run log."""
    issues: list[str] = []
    for line in log_text.splitlines():
        stripped = line.strip()
        if stripped.startswith(("WARNING:", "ERROR:")):
            issues.append(stripped)
    return issues


def run_in_illustrator(jsx_path: Path, app_name: str = "Adobe Illustrator") -> tuple[int, str, str]:
    """Execute a .jsx file in Adobe Illustrator via macOS osascript."""
    escaped = str(jsx_path.resolve()).replace("\\", "\\\\").replace('"', '\\"')
    apple_script = f'tell application "{app_name}" to do javascript file "{escaped}"'
    proc = subprocess.run(
        ["osascript", "-e", apple_script],
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate pure-ASCII ExtendScript and run it in Adobe Illustrator on macOS."
    )
    parser.add_argument("--script", required=True, type=Path, help="Path to task .jsx file.")
    parser.add_argument(
        "--with-lib",
        action="store_true",
        help="Prepend bundled ai_edit_lib.jsx into a temporary script before execution.",
    )
    parser.add_argument(
        "--lib",
        type=Path,
        default=DEFAULT_LIB,
        help="Path to ExtendScript helper library (used with --with-lib).",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=None,
        help="Optional source master path; verified distinct from --out.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Optional deliverable output path; verified distinct from --source.",
    )
    parser.add_argument(
        "--log",
        type=Path,
        default=None,
        help="Optional Illustrator log file to print and scan for WARNING:/ERROR: lines.",
    )
    parser.add_argument(
        "--app",
        default="Adobe Illustrator",
        help='macOS application name for osascript (default: "Adobe Illustrator").',
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Validate pure ASCII and path guards without launching Illustrator.",
    )
    parser.add_argument(
        "--emit-bundled",
        type=Path,
        default=None,
        help="Write the validated (and optionally lib-bundled) .jsx to this path.",
    )
    parser.add_argument(
        "--allow-warnings",
        action="store_true",
        help="Do not fail non-zero when WARNING:/ERROR: lines appear in --log.",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if not args.script.is_file():
        print(f"ERROR: script not found: {args.script}", file=sys.stderr)
        return 2

    try:
        guard_distinct_paths(args.source, args.out)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    lib_path = args.lib if args.with_lib else None
    if lib_path is not None and not lib_path.is_file():
        print(f"ERROR: library not found: {lib_path}", file=sys.stderr)
        return 2

    combined = bundle_jsx(args.script, lib_path=lib_path)
    ascii_errors = check_pure_ascii(combined, label=str(args.script))
    if ascii_errors:
        print("FAIL: non-ASCII characters detected in ExtendScript:", file=sys.stderr)
        for msg in ascii_errors:
            print(f"  {msg}", file=sys.stderr)
        return 1

    print(f"PASS: pure-ASCII check passed ({len(combined)} bytes).")

    if args.emit_bundled is not None:
        args.emit_bundled.parent.mkdir(parents=True, exist_ok=True)
        args.emit_bundled.write_text(combined, encoding="ascii")
        print(f"Wrote bundled script: {args.emit_bundled}")

    if args.check_only:
        return 0

    tmp_path: Path | None = None
    try:
        if args.with_lib:
            fd, raw_tmp = tempfile.mkstemp(prefix="ai_direct_edit_", suffix=".jsx")
            os.close(fd)
            tmp_path = Path(raw_tmp)
            tmp_path.write_text(combined, encoding="ascii")
            target_jsx = tmp_path
        else:
            target_jsx = args.script

        rc, stdout, stderr = run_in_illustrator(target_jsx, app_name=args.app)
    finally:
        if tmp_path is not None and tmp_path.exists():
            tmp_path.unlink()

    if stdout:
        print(stdout)
    if stderr:
        print(stderr, file=sys.stderr)
    if rc != 0:
        print(f"ERROR: Adobe Illustrator execution failed (exit {rc}).", file=sys.stderr)
        return rc

    if args.log is not None:
        if not args.log.is_file():
            print(f"ERROR: expected log file was not created: {args.log}", file=sys.stderr)
            return 1
        log_text = args.log.read_text(encoding="utf-8", errors="replace")
        print(log_text)
        issues = scan_log_issues(log_text)
        if issues and not args.allow_warnings:
            print(f"FAIL: {len(issues)} warning/error line(s) found in run log.", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
