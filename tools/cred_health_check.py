#!/usr/bin/env python3
"""Daily external-credential health check for the Feishu queue stack.

scripts/validate_required_env.sh only checks whether env vars are present,
never that the credentials behind them actually work. Tokens, cookies, and
app permissions can expire silently; the first symptom today is a failed
queue row hours later. This script exercises each external dependency
with a minimal read-only call and emits a status table to stdout plus
$GITHUB_STEP_SUMMARY.

Three probes:
1. Feishu / Lark CLI - shell out to `python build.py sync-data --dry-run`
   which authenticates the app token and validates table bindings before
   any real sync.
2. DingTalk - call tools.dingtalk.auth.get_app_only_token() directly to
   hit the live OAuth2 token endpoint. Skipped (not failed) if the
   DingTalk env vars are not configured.
3. GitHub - `gh auth status` confirms the bot token is still valid.

Exits non-zero if any probe fails. The scheduled workflow uses that
signal to open or update a tracking issue.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence


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
    """A diagnosable one-liner from a failed command's output.

    The old ``last line`` heuristic returned literally ``}`` whenever the error
    was a multi-line JSON dump, which made every distinct failure look
    identical. Prefer the last line that carries an error-ish signal; fall back
    to the last few non-empty lines joined together.
    """
    lines = [line.strip() for line in (stderr or stdout).splitlines() if line.strip()]
    if not lines:
        return f"exit={code}"
    error_re = re.compile(r"error|failed|denied|permission|exception|traceback|missing", re.IGNORECASE)
    for line in reversed(lines):
        if error_re.search(line) and len(line) > 3:
            return line[:300]
    return " | ".join(lines[-3:])[:300]


def probe_dingtalk() -> ProbeResult:
    required = ("DINGTALK_CLIENT_ID", "DINGTALK_CLIENT_SECRET", "DINGTALK_CORP_ID")
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        return ProbeResult(
            "DingTalk",
            "skipped",
            f"env not configured ({', '.join(missing)} unset)",
        )
    try:
        sys.path.insert(0, str(REPO_ROOT))
        from tools.dingtalk.auth import get_app_only_token

        token = get_app_only_token(
            client_id_env="DINGTALK_CLIENT_ID",
            client_secret_env="DINGTALK_CLIENT_SECRET",
            corp_id_env="DINGTALK_CORP_ID",
        )
    except Exception as exc:
        return ProbeResult("DingTalk", "failed", f"get_app_only_token error: {exc}")
    return ProbeResult(
        "DingTalk",
        "ok",
        f"app-only token issued (ttl={token.expires_in_seconds}s)",
    )


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
    return ProbeResult("GitHub", "failed", f"gh auth status failed: {stderr.splitlines()[-1] if stderr else code}")


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
        probe_dingtalk,
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
