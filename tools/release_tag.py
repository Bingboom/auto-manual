#!/usr/bin/env python3
"""Plan, create, and verify an annotated Git tag for one release manifest."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=1)

_FULL_SHA_RE = re.compile(r"[0-9a-f]{40}")
_SHA256_RE = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True)
class ReleaseTagPlan:
    tag: str
    git_sha: str
    manifest_sha256: str
    annotation: str


def _required_text(payload: dict[str, Any], field: str) -> str:
    value = str(payload.get(field) or "").strip()
    if not value:
        raise RuntimeError(f"release manifest requires {field}")
    return value


def build_release_tag_plan(manifest_path: Path) -> ReleaseTagPlan:
    try:
        raw = manifest_path.read_bytes()
        payload = json.loads(raw.decode("utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cannot read release manifest: {manifest_path}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("release manifest root must be an object")

    tag = _required_text(payload, "release_tag")
    if not tag.startswith("manual-release/"):
        raise RuntimeError(f"unsupported release tag namespace: {tag}")
    git_sha = _required_text(payload, "git_sha").lower()
    if not _FULL_SHA_RE.fullmatch(git_sha):
        raise RuntimeError("release manifest git_sha must be a full 40-character SHA")

    languages_raw = payload.get("build_languages")
    if not isinstance(languages_raw, list) or not languages_raw:
        raise RuntimeError("release manifest requires build_languages")
    languages = ",".join(str(value).strip() for value in languages_raw if str(value).strip())
    if not languages:
        raise RuntimeError("release manifest requires build_languages")

    snapshot_raw = payload.get("snapshot")
    snapshot = snapshot_raw if isinstance(snapshot_raw, dict) else {}
    snapshot_sha256 = str(snapshot.get("snapshot_sha256") or "").strip().lower()
    if not _SHA256_RE.fullmatch(snapshot_sha256):
        raise RuntimeError(
            "release manifest snapshot.snapshot_sha256 must be a 64-character SHA-256"
        )
    manifest_sha256 = hashlib.sha256(raw).hexdigest()
    annotation = "\n".join(
        (
            "auto-manual-release-tag/v1",
            f"release_tag={tag}",
            f"git_sha={git_sha}",
            f"release_version={_required_text(payload, 'release_version')}",
            f"model={_required_text(payload, 'model')}",
            f"region={_required_text(payload, 'region')}",
            f"build_languages={languages}",
            f"manifest_sha256={manifest_sha256}",
            f"snapshot_sha256={snapshot_sha256}",
        )
    )
    return ReleaseTagPlan(
        tag=tag,
        git_sha=git_sha,
        manifest_sha256=manifest_sha256,
        annotation=annotation,
    )


def _run_git(
    repo_root: Path,
    args: list[str],
    *,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(repo_root),
        check=check,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def _tag_exists(repo_root: Path, tag: str) -> bool:
    result = _run_git(
        repo_root,
        ["show-ref", "--verify", "--quiet", f"refs/tags/{tag}"],
        check=False,
    )
    return result.returncode == 0


def verify_local_tag(repo_root: Path, plan: ReleaseTagPlan) -> None:
    if not _tag_exists(repo_root, plan.tag):
        raise RuntimeError(f"release tag does not exist: {plan.tag}")
    object_type = _run_git(repo_root, ["cat-file", "-t", f"refs/tags/{plan.tag}"]).stdout.strip()
    if object_type != "tag":
        raise RuntimeError(f"release tag must be annotated, found {object_type}: {plan.tag}")
    target = _run_git(repo_root, ["rev-list", "-n", "1", plan.tag]).stdout.strip().lower()
    if target != plan.git_sha:
        raise RuntimeError(
            f"release tag target mismatch for {plan.tag}: expected {plan.git_sha}, found {target}"
        )
    annotation = _run_git(
        repo_root,
        ["for-each-ref", "--format=%(contents)", f"refs/tags/{plan.tag}"],
    ).stdout.rstrip("\n")
    if annotation != plan.annotation:
        raise RuntimeError(
            f"release tag annotation mismatch for {plan.tag}; the manifest binding changed"
        )


def _remote_tag_exists(repo_root: Path, *, remote: str, tag: str) -> bool:
    if remote.startswith("-"):
        raise RuntimeError("remote name must not start with '-'")
    result = _run_git(
        repo_root,
        ["ls-remote", "--tags", "--refs", remote, f"refs/tags/{tag}"],
        check=False,
    )
    if result.returncode != 0:
        message = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"cannot inspect remote {remote}: {message}")
    return bool(result.stdout.strip())


def apply_release_tag(
    *,
    repo_root: Path,
    plan: ReleaseTagPlan,
    write: bool,
    push: bool,
    remote: str,
) -> str:
    _run_git(repo_root, ["cat-file", "-e", f"{plan.git_sha}^{{commit}}"])

    remote_exists = False
    if push:
        remote_exists = _remote_tag_exists(repo_root, remote=remote, tag=plan.tag)
        if remote_exists:
            _run_git(
                repo_root,
                ["fetch", remote, f"refs/tags/{plan.tag}:refs/tags/{plan.tag}"],
            )

    if _tag_exists(repo_root, plan.tag):
        verify_local_tag(repo_root, plan)
        if push and not remote_exists:
            _run_git(repo_root, ["push", remote, f"refs/tags/{plan.tag}"])
            return "verified-and-pushed"
        return "verified"
    if not write:
        return "planned"

    _run_git(repo_root, ["tag", "-a", plan.tag, plan.git_sha, "-m", plan.annotation])
    verify_local_tag(repo_root, plan)
    if push and not remote_exists:
        _run_git(repo_root, ["push", remote, f"refs/tags/{plan.tag}"])
    return "created-and-pushed" if push else "created"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plan or create an immutable annotated Git tag bound to a release manifest."
    )
    parser.add_argument("--manifest", required=True, help="Versioned release manifest JSON")
    parser.add_argument("--write", action="store_true", help="Create the local annotated tag")
    parser.add_argument("--push", action="store_true", help="Push the verified tag to the remote")
    parser.add_argument("--remote", default="origin", help="Git remote used with --push")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.push and not args.write:
        print("[release-tag] ERROR: --push requires --write", file=sys.stderr)
        return 1
    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = ROOT / manifest_path
    try:
        plan = build_release_tag_plan(manifest_path)
        status = apply_release_tag(
            repo_root=ROOT,
            plan=plan,
            write=args.write,
            push=args.push,
            remote=str(args.remote),
        )
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        message = exc.stderr.strip() if isinstance(exc, subprocess.CalledProcessError) and exc.stderr else str(exc)
        print(f"[release-tag] ERROR: {message}", file=sys.stderr)
        return 1

    print(f"[release-tag] status={status}")
    print(f"[release-tag] tag={plan.tag}")
    print(f"[release-tag] git_sha={plan.git_sha}")
    print(f"[release-tag] manifest_sha256={plan.manifest_sha256}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
