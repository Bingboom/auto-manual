#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build-warning ratchet (Milestone I2, the esp-docs known-warnings pattern).

Warning noise is where real defects hide: #654's silently vanished App pages
sat behind counters that read zero. The ratchet makes warning debt explicit:
every warning stream is sanitized (paths, line numbers, ANSI stripped) and
diffed against a committed baseline under ``data/known_warnings/``. A warning
in the baseline is registered debt; a warning NOT in the baseline is news.

Enforcement is staged deliberately:

- the standalone CLI (``check``) is always strict — new warnings exit 1 and a
  missing baseline exits 2 (a check that silently skips is worse than none);
- the in-build hook (wired after every Sphinx run) defaults to REPORT mode so
  existing lines keep building while baselines accumulate; set
  ``AUTO_MANUAL_WARNING_RATCHET=strict`` to fail the build on new warnings.
  Flip the default once 2–3 queue rounds have seeded stable baselines.

Baselines are sanitized text, one warning per line, sorted — regenerate with
``update`` after an intentional change and review the diff like code.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

BASELINE_DIRNAME = "known_warnings"

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
# Keep the path tail from the last recognizable repo anchor; else basename.
# The leading `[\w.+~-]*` also captures relative paths (docs/_build/…), not
# only absolute ones — without it the pre-slash segment gets glued to the
# sanitized tail.
_PATH_TOKEN_RE = re.compile(r"(?:[A-Za-z]:)?[\w.+~-]*(?:[/\\][^\s:,'\"]+)+")
_ANCHORS = ("docs/", "tools/", "data/", "tests/", "configs/")
_LINE_NO_RE = re.compile(r":\d+(?=[:\s]|$)")


def _sanitize_path_token(token: str) -> str:
    normalized = token.replace("\\", "/")
    for anchor in _ANCHORS:
        if normalized.startswith(anchor):
            return normalized
        index = normalized.rfind("/" + anchor)
        if index != -1:
            return normalized[index + 1 :]
    return normalized.rsplit("/", 1)[-1]


def sanitize_line(line: str) -> str:
    """One warning line -> stable, machine-comparable form."""
    text = _ANSI_RE.sub("", line)
    text = _PATH_TOKEN_RE.sub(lambda m: _sanitize_path_token(m.group(0)), text)
    text = _LINE_NO_RE.sub("", text)
    return re.sub(r"\s+", " ", text).strip()


def sanitize_log(log_text: str) -> list[str]:
    lines = []
    for raw in log_text.splitlines():
        line = sanitize_line(raw)
        if line:
            lines.append(line)
    return lines


def baseline_path(baseline_dir: Path, stream: str) -> Path:
    return baseline_dir / f"{stream}-known-warnings.txt"


def load_baseline(baseline_dir: Path, stream: str) -> list[str] | None:
    path = baseline_path(baseline_dir, stream)
    if not path.exists():
        return None
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")]


def compare(log_lines: list[str], baseline_lines: list[str]) -> dict[str, list[str]]:
    """new = fails the ratchet; stale = registered debt no longer observed."""
    baseline = set(baseline_lines)
    seen = set(log_lines)
    return {
        "new": sorted(seen - baseline),
        "known": sorted(seen & baseline),
        "stale": sorted(baseline - seen),
    }


def write_baseline(baseline_dir: Path, stream: str, log_lines: list[str]) -> Path:
    path = baseline_path(baseline_dir, stream)
    path.parent.mkdir(parents=True, exist_ok=True)
    header = (
        "# Known-warnings baseline (warning ratchet, Milestone I2).\n"
        "# One sanitized warning per line; a warning NOT listed here fails the\n"
        "# strict check. Regenerate after an intentional change:\n"
        f"#   python tools/warning_ratchet.py update --stream {stream} --log <warnings.log>\n"
    )
    path.write_text(header + "\n".join(sorted(set(log_lines))) + "\n", encoding="utf-8")
    return path


def check_stream(
    *,
    stream: str,
    log_text: str,
    baseline_dir: Path,
    printer=print,
) -> int:
    """Strict semantics: 0 clean, 1 new warnings, 2 missing baseline."""
    log_lines = sanitize_log(log_text)
    baseline = load_baseline(baseline_dir, stream)
    if baseline is None:
        printer(
            f"[warning-ratchet] ERROR stream '{stream}': no baseline at "
            f"{baseline_path(baseline_dir, stream)} — seed it with the "
            "'update' command (a silently skipped check is worse than none)"
        )
        return 2
    result = compare(log_lines, baseline)
    for line in result["new"]:
        printer(f"[warning-ratchet] NEW {stream}: {line}")
    for line in result["stale"]:
        printer(f"[warning-ratchet] stale-baseline {stream}: {line}")
    printer(
        f"[warning-ratchet] {stream}: {len(result['new'])} new, "
        f"{len(result['known'])} known, {len(result['stale'])} stale"
    )
    return 1 if result["new"] else 0


def default_baseline_dir(repo_root: Path | None = None) -> Path:
    root = repo_root if repo_root is not None else _REPO_ROOT
    return root / "data" / BASELINE_DIRNAME


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="warning_ratchet",
        description="Diff a build warning log against its committed known-warnings baseline.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (
        ("check", "Fail on warnings missing from the baseline (1) or a missing baseline (2)."),
        ("update", "Rewrite the stream's baseline from a warning log."),
    ):
        cmd = sub.add_parser(name, help=help_text)
        cmd.add_argument("--stream", required=True, help="Stream name, e.g. sphinx-html.")
        cmd.add_argument("--log", required=True, type=Path, help="Warning log file.")
        cmd.add_argument(
            "--baseline-dir", type=Path, default=None,
            help="Baseline directory (default: data/known_warnings/).",
        )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    baseline_dir = args.baseline_dir or default_baseline_dir()
    log_text = args.log.read_text(encoding="utf-8") if args.log.exists() else ""
    if args.command == "update":
        path = write_baseline(baseline_dir, args.stream, sanitize_log(log_text))
        print(f"[warning-ratchet] wrote {path}")
        return 0
    return check_stream(stream=args.stream, log_text=log_text, baseline_dir=baseline_dir)


if __name__ == "__main__":
    raise SystemExit(main())
