#!/usr/bin/env python3
"""Daily external-credential health check for the Feishu queue stack.

scripts/validate_required_env.sh only checks whether env vars are present,
never that the credentials behind them actually work. Tokens, cookies, and
app permissions can expire silently; the first symptom today is a failed
queue row hours later. This script exercises each external dependency
with a minimal read-only call and emits a status table to stdout plus
$GITHUB_STEP_SUMMARY.

Two probes:
1. Feishu / Lark CLI - shell out to `python build.py sync-data --dry-run`
   which authenticates the app token and validates table bindings before
   any real sync.
2. GitHub - `gh auth status` confirms the bot token is still valid.

Exits non-zero if any probe fails. The scheduled workflow uses that
signal to open or update a tracking issue.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

from tools.utils.redaction import redact_identifiers


REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class ProbeResult:
    name: str
    status: str  # "ok", "skipped", "failed"
    detail: str

    @property
    def is_failure(self) -> bool:
        return self.status == "failed"


def _run(cmd: Sequence[str], *, cwd: Path | None = None, timeout: int = 60) -> tuple[int, str, str]:
    completed = subprocess.run(
        list(cmd),
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()


def probe_feishu(config: str) -> ProbeResult:
    cmd = [
        sys.executable,
        "build.py",
        "sync-data",
        "--config",
        config,
        "--data-root",
        ".tmp/health-check",
        "--dry-run",
    ]
    started = time.monotonic()
    try:
        code, stdout, stderr = _run(cmd, cwd=REPO_ROOT, timeout=180)
    except subprocess.TimeoutExpired:
        return ProbeResult("Feishu/Lark", "failed", "sync-data --dry-run timed out after 180s")
    elapsed = time.monotonic() - started
    if code == 0:
        return ProbeResult("Feishu/Lark", "ok", f"sync-data --dry-run ok in {elapsed:.1f}s")
    return ProbeResult(
        "Feishu/Lark", "failed", f"sync-data --dry-run failed: {_failure_detail(stderr, stdout, code)}"
    )


def _failure_detail(stderr: str, stdout: str, code: int) -> str:
    """A diagnosable, publishable one-liner from a failed command's output.

    The detail is printed to the job summary of a public repository, so it is
    built from an allowlist: for lark-cli's JSON error dump only the numeric
    ``code``, a bounded and scrubbed ``message`` and the logical table name
    that sync-data prefixes (``[table: …]``); nothing else from the payload
    (log ids, request ids, troubleshooting URLs) is passed through. Other
    output falls back to the last error-ish line, scrubbed the same way. The
    old ``last line`` heuristic returned literally ``}`` for a multi-line JSON
    dump, and a plain keyword scan returned ``"error": {`` whenever the
    message itself had no keyword.
    """
    text = "\n".join(part for part in (stderr, stdout) if part)
    table = _table_label(text)
    suffix = f" table={table}" if table else ""
    lark_error = _lark_error(text)
    if lark_error is not None:
        error_code, message = lark_error
        return f"code={error_code} message={_sanitize(message, _MESSAGE_CAP)}{suffix}"
    lines = [line.strip() for line in (stderr or stdout).splitlines() if line.strip()]
    if not lines:
        return f"exit={code}"
    error_re = re.compile(r"error|failed|denied|permission|exception|traceback|missing", re.IGNORECASE)
    for line in reversed(lines):
        if error_re.search(line) and len(line) > 3:
            return _sanitize(line, _DETAIL_CAP)
    return _sanitize(" | ".join(lines[-3:]), _DETAIL_CAP)


_DETAIL_CAP = 300
_MESSAGE_CAP = 160
_MAX_JSON_STARTS = 200
_TABLE_LABEL_RE = re.compile(r"\[table: ([A-Za-z0-9_. -]{1,80})\]")
_CODE_RE = re.compile(r'"code"\s*:\s*"?(-?\d{1,10})"?')
_MESSAGE_RE = re.compile(r'"(?:message|msg)"\s*:\s*"((?:[^"\\\n]|\\.){0,400})')


def _sanitize(text: str, cap: int) -> str:
    """Single line, no control characters, ids scrubbed, length bounded."""
    flat = " ".join("".join(ch if ch.isprintable() else " " for ch in text).split())
    flat = redact_identifiers(flat)
    return flat if len(flat) <= cap else flat[: cap - 1].rstrip() + "\u2026"


def _table_label(text: str) -> str:
    match = _TABLE_LABEL_RE.search(text)
    return match.group(1).strip() if match else ""


def _as_code(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and re.fullmatch(r"-?\d{1,10}", value.strip()):
        return int(value.strip())
    return None


def _error_from_payload(payload: object) -> tuple[int, str] | None:
    if not isinstance(payload, dict):
        return None
    nested = payload.get("error")
    for candidate in (nested, payload):
        if not isinstance(candidate, dict):
            continue
        error_code = _as_code(candidate.get("code"))
        if error_code is not None and error_code != 0:
            message = candidate.get("message", candidate.get("msg", ""))
            return error_code, message if isinstance(message, str) else ""
    return None


def _lark_error(text: str) -> tuple[int, str] | None:
    """``(code, message)`` from the first JSON error object in ``text``, if any."""
    decoder = json.JSONDecoder()
    start = text.find("{")
    for _ in range(_MAX_JSON_STARTS):
        if start < 0:
            break
        try:
            payload, _end = decoder.raw_decode(text, start)
        except ValueError:
            payload = None
        found = _error_from_payload(payload)
        if found is not None:
            return found
        start = text.find("{", start + 1)
    # Truncated dump: still report the code when it is unambiguous.
    code_match = _CODE_RE.search(text)
    error_code = int(code_match.group(1)) if code_match else 0
    if error_code == 0:
        return None
    message_match = _MESSAGE_RE.search(text)
    return error_code, message_match.group(1) if message_match else ""


def probe_github() -> ProbeResult:
    if not os.environ.get("GITHUB_TOKEN"):
        return ProbeResult("GitHub", "skipped", "GITHUB_TOKEN unset")
    gh = shutil.which("gh")
    if gh is None:
        return ProbeResult("GitHub", "skipped", "gh CLI not installed")
    try:
        code, _stdout, stderr = _run([gh, "auth", "status"], timeout=30)
    except subprocess.TimeoutExpired:
        return ProbeResult("GitHub", "failed", "gh auth status timed out")
    if code == 0:
        return ProbeResult("GitHub", "ok", "gh auth status: logged in")
    last_line = stderr.splitlines()[-1] if stderr else str(code)
    return ProbeResult("GitHub", "failed", f"gh auth status failed: {_sanitize(last_line, _DETAIL_CAP)}")


def render_table(results: Sequence[ProbeResult]) -> str:
    rows = ["| Probe | Status | Detail |", "|---|---|---|"]
    for result in results:
        marker = {"ok": "ok", "skipped": "skipped", "failed": "FAILED"}.get(result.status, result.status)
        rows.append(f"| {result.name} | {marker} | {result.detail} |")
    return "\n".join(rows)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="External credential health check.")
    parser.add_argument(
        "--config",
        default="configs/config.us.yaml",
        help="Config file passed to build.py sync-data --dry-run (default: configs/config.us.yaml).",
    )
    parser.add_argument(
        "--summary",
        default=os.environ.get("GITHUB_STEP_SUMMARY"),
        help="Path to write a Markdown summary (defaults to $GITHUB_STEP_SUMMARY when set).",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    probes: list[Callable[[], ProbeResult]] = [
        lambda: probe_feishu(args.config),
        probe_github,
    ]
    results = [probe() for probe in probes]

    print("## Cred Health Check")
    print()
    print(render_table(results))

    if args.summary:
        summary_path = Path(args.summary)
        try:
            summary_path.parent.mkdir(parents=True, exist_ok=True)
            with summary_path.open("a", encoding="utf-8") as handle:
                handle.write("## Cred Health Check\n\n")
                handle.write(render_table(results))
                handle.write("\n")
        except OSError as exc:
            print(f"[cred-health-check] could not write summary {args.summary}: {exc}", file=sys.stderr)

    failures = [r for r in results if r.is_failure]
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
