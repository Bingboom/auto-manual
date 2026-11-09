"""Conservative CI input classification, using Git objects and only the stdlib.

Only ordinary maintainer Markdown is editorial. Everything else is an input,
including unknown paths, executable/symlink Markdown, templates and contracts.
PR workflows execute this file from the trusted base, never from the candidate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def editorial(path: str) -> bool:
    parts = PurePosixPath(path).parts
    if not parts or ".." in parts or path.startswith("/"):
        return False
    if parts[-1] in {"AGENTS.md", "CLAUDE.md", "SKILL.md"}:
        return False
    return path == "README.md" or (
        parts[0] in {"code-as-doc", "user-guide"} and path.endswith(".md")
    )


def git(*args: str) -> bytes:
    return subprocess.run(
        ["git", *args], check=True, capture_output=True, timeout=60,
    ).stdout


def engineering_required(raw_diff: bytes) -> bool:
    """Parse NUL-delimited raw diff; disabling renames exposes both old/new paths."""
    fields = raw_diff.split(b"\0")
    if not fields[-1] == b"" or len(fields) < 3 or len(fields) % 2 != 1:
        return True  # Empty/unknown diff is not proof of an editorial-only change.
    for offset in range(0, len(fields) - 1, 2):
        header = fields[offset].decode("ascii").split()
        path = fields[offset + 1].decode("utf-8")
        if len(header) != 5 or header[4] not in {"A", "M", "D"}:
            return True
        if header[0] not in {":100644", ":000000"} or header[1] not in {"100644", "000000"}:
            return True
        if not editorial(path):
            return True
    return False


def input_fingerprint(tree: bytes) -> str:
    """Hash modes, names and blob IDs, without downloading file contents."""
    digest = hashlib.sha256()
    count = 0
    if not tree or not tree.endswith(b"\0"):
        raise ValueError("missing or incomplete Git tree")
    for entry in tree.split(b"\0")[:-1]:
        metadata, raw_path = entry.split(b"\t", 1)
        mode, kind, sha = metadata.split()
        if not re.fullmatch(rb"[0-9a-f]{40}", sha):
            raise ValueError("invalid Git object ID")
        if mode == b"100644" and kind == b"blob" and editorial(raw_path.decode("utf-8")):
            continue
        digest.update(entry + b"\0")
        count += 1
    if not count:
        raise ValueError("no engineering inputs")
    return digest.hexdigest()


def previous_run_succeeded(runs: list[dict], current_id: str) -> bool:
    """Do not reuse a cache after a failed/cancelled/manual retry of this workflow."""
    previous = [run for run in runs if str(run["id"]) != current_id]
    if not previous:
        return False
    latest = max(previous, key=lambda run: run["run_started_at"])
    return latest["status"] == "completed" and latest["conclusion"] == "success"


def last_run_ok() -> bool:
    """Read-only history check; unavailable or truncated history means render."""
    try:
        query = urlencode({"branch": os.environ["GITHUB_REF_NAME"], "per_page": 100})
        url = (f"{os.environ['GITHUB_API_URL']}/repos/{os.environ['GITHUB_REPOSITORY']}"
               f"/actions/workflows/nightly-render.yml/runs?{query}")
        request = Request(url, headers={
            "Authorization": f"Bearer {os.environ['GH_TOKEN']}",
            "Accept": "application/vnd.github+json",
        })
        with urlopen(request, timeout=30) as response:
            payload = json.load(response)
        # Pagination is deliberate: even an old manually rerun failure must not
        # disappear behind newer successful skipped runs. Any error runs render.
        runs = payload["workflow_runs"]
        page = 2
        while len(runs) < payload["total_count"]:
            if page > 20:
                return False
            request.full_url = url + f"&page={page}"
            with urlopen(request, timeout=30) as response:
                batch = json.load(response)["workflow_runs"]
            if not batch:
                return False
            runs.extend(batch)
            page += 1
        return previous_run_succeeded(runs, os.environ["GITHUB_RUN_ID"])
    except (OSError, URLError, KeyError, ValueError, TypeError):
        print("::warning::Nightly history unavailable; rendering to preserve retries")
        return False


def emit(key: str, value: str) -> None:
    print(f"{key}={value}")
    if output := os.environ.get("GITHUB_OUTPUT"):
        with Path(output).open("a", encoding="utf-8") as stream:
            stream.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("manual", "nightly"))
    parser.add_argument("--base", default="")
    args = parser.parse_args()
    if args.mode == "nightly":
        fingerprint = input_fingerprint(git("ls-tree", "-r", "-z", "HEAD"))
        # Periodic revalidation catches external toolchain/runner drift too.
        week = datetime.now(timezone.utc).strftime("%G-W%V")
        emit("cache_key", f"nightly-success-v1-{week}-{fingerprint}")
        emit("previous_ok", str(last_run_ok()).lower())
        return 0
    try:
        if not re.fullmatch(r"[0-9a-f]{40}", args.base) or set(args.base) == {"0"}:
            raise ValueError("missing comparison base")
        raw = git("diff", "--raw", "-z", "--no-renames", "--no-abbrev",
                  "--no-ext-diff", args.base, "HEAD", "--")
        required = engineering_required(raw)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"::warning::CI classification unavailable ({type(exc).__name__}); running full validation")
        required = True
    emit("engineering", str(required).lower())
    if summary := os.environ.get("GITHUB_STEP_SUMMARY"):
        with Path(summary).open("a", encoding="utf-8") as stream:
            stream.write("### Manual Validation scope\n" + (
                "Full engineering validation (changed inputs or conservative fallback).\n"
                if required else "Editorial Markdown only: secret scan, maintainability and doc links remain active.\n"
            ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
