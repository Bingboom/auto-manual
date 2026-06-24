#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PR / git helpers for cloud-doc backport (D2-8).

Branch naming, git-status parsing, gh PR creation + compare-url fallback, and
open_backport_pr_from_manifest. Imports leaf modules; re-exported.
"""
from __future__ import annotations

import sys
from pathlib import Path
import shlex
import subprocess
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.utils.path_utils import get_paths  # noqa: E402
from tools.cloud_doc_backport_model import (  # noqa: E402
    _SAFE_PATH_CHARS,
    _safe_path_token,
)
from tools.cloud_doc_backport_util import (  # noqa: E402
    RUN_SCHEMA_VERSION,
    _load_json_file,
    _resolve_repo_file,
    _validate_apply_source,
)


def _default_out_dir(run_id: str) -> Path:
    return get_paths().cloud_doc_backport_reports_dir / _safe_path_token(run_id)

def _resolve_existing_path(value: str | None, *, label: str) -> Path | None:
    if not value:
        return None
    path = Path(value)
    if not path.is_absolute():
        path = get_paths().root / path
    if not path.exists():
        raise RuntimeError(f"{label} does not exist: {value}")
    if not path.is_file():
        raise RuntimeError(f"{label} must be a file: {value}")
    return path

def _repo_relative(root: Path, path: Path) -> str:
    return path.resolve(strict=False).relative_to(root.resolve(strict=False)).as_posix()

def _parse_git_status_paths(stdout: str) -> list[str]:
    paths: list[str] = []
    for raw_line in stdout.splitlines():
        if not raw_line.strip():
            continue
        path_text = raw_line[3:].strip() if len(raw_line) > 3 else raw_line.strip()
        if " -> " in path_text:
            path_text = path_text.split(" -> ", 1)[1].strip()
        if path_text:
            paths.append(path_text)
    return paths

def _run_pr_command(command: list[str], *, root: Path, stdin: str | None = None) -> str:
    completed = subprocess.run(
        command,
        cwd=root,
        input=stdin,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise RuntimeError(f"{detail or 'command failed'} (exit={completed.returncode}, cmd={shlex.join(command)})")
    return completed.stdout.strip()

def _github_web_url(remote_url: str) -> str | None:
    value = remote_url.strip()
    if not value:
        return None
    if value.startswith("git@github.com:"):
        path = value.removeprefix("git@github.com:")
        return "https://github.com/" + path.removesuffix(".git")
    if value.startswith("https://github.com/") or value.startswith("http://github.com/"):
        return value.removesuffix(".git")
    return None

def _compare_url(
    *,
    root: Path,
    base_ref: str,
    head_ref: str,
    git_bin: str = "git",
    remote: str = "origin",
) -> str:
    try:
        remote_url = _run_pr_command([git_bin, "remote", "get-url", remote], root=root)
    except RuntimeError:
        remote_url = ""
    web_url = _github_web_url(remote_url)
    if web_url:
        return f"{web_url}/compare/{base_ref}...{head_ref}"
    return f"{base_ref}...{head_ref}"

def _safe_branch_segment(value: str) -> str:
    return _SAFE_PATH_CHARS.sub("-", value.strip()).strip(".-") or "backport"

def _default_backport_branch_name(manifest: dict[str, Any], manifest_path: Path) -> str:
    source_path = str((manifest.get("source_target") or {}).get("path") or "")
    parts = Path(source_path).parts
    model = "manual"
    region = "review"
    if "_review" in parts:
        index = parts.index("_review")
        if index + 1 < len(parts):
            model = parts[index + 1]
        if index + 2 < len(parts):
            region = parts[index + 2]
    run_token = _safe_branch_segment(manifest_path.parent.name)[-32:]
    return f"review/{_safe_branch_segment(model)}-{_safe_branch_segment(region)}-cloud-doc-backport-{run_token}"

def _validate_open_pr_manifest(manifest: dict[str, Any], *, source_path: Path) -> None:
    if manifest.get("schema_version") != RUN_SCHEMA_VERSION:
        raise RuntimeError("manifest schema is not cloud-doc-backport-run/v1")
    if manifest.get("result") != "PR_READY":
        raise RuntimeError(f"manifest result must be PR_READY, got {manifest.get('result') or '-'}")
    summary = manifest.get("summary") if isinstance(manifest.get("summary"), dict) else {}
    if summary.get("pr_ready") is not True:
        raise RuntimeError("manifest summary.pr_ready must be true")
    if summary.get("changed") is not True:
        raise RuntimeError("manifest summary.changed must be true")
    source_target = manifest.get("source_target") if isinstance(manifest.get("source_target"), dict) else {}
    if source_target.get("kind") != "review":
        raise RuntimeError("manifest source_target.kind must be review")
    _validate_apply_source(source_path, kind="review")

def _pr_body_from_manifest(
    manifest: dict[str, Any],
    *,
    manifest_rel: str,
    source_rel: str,
) -> str:
    summary = manifest.get("summary") if isinstance(manifest.get("summary"), dict) else {}
    reports = manifest.get("reports") if isinstance(manifest.get("reports"), dict) else {}
    lines = [
        "## Summary",
        "",
        "- What changed: Applied accepted Feishu cloud-doc review revisions to the in-review source.",
        f"- Why it changed: `{manifest_rel}` reported `PR_READY` for `{source_rel}`.",
        "",
        "---",
        "",
        "## Change Type",
        "",
        "- [x] Bug fix",
        "- [ ] Feature",
        "- [ ] Refactor",
        "- [ ] Performance",
        "- [ ] Config / schema change",
        "- [ ] Workflow / CI change",
        "",
        "---",
        "",
        "## Impact Surface",
        "",
        "- [ ] CSV schema / structured snapshot",
        "- [ ] Template / page assembly",
        "- [ ] Build entrypoint / CLI",
        "- [x] Review / diff / publish / release flow",
        "- [x] External integrations (Feishu / DingTalk / OpenClaw)",
        "- [ ] Docs / CI / maintainer workflow",
        "",
        "---",
        "",
        "## Anti-Debt Checklist",
        "",
        "- [x] New low-level logic was kept out of `build.py`, `tools/build_docs.py`, and `tools/process_build_queue.py`",
        "- [x] No new config was added only because the model changed",
        "",
        "---",
        "",
        "## Cloud-Doc Backport Manifest",
        "",
        f"- Manifest: `{manifest_rel}`",
        f"- Source: `{source_rel}`",
        f"- Result: `{manifest.get('result') or '-'}`",
        f"- Mode: `{manifest.get('mode') or '-'}`",
        f"- Total deltas: `{summary.get('total_deltas', 0)}`",
        f"- Source-table suggestions: `{summary.get('source_table_suggestions', 0)}`",
        "",
        "Reports remain local evidence and are not committed by this helper:",
    ]
    for label, path in sorted(reports.items()):
        lines.append(f"- {label}: `{path}`")
    lines.extend(
        [
            "",
            "---",
            "",
            "## Validation",
            "",
            "- [ ] `python -m unittest`",
            "- [ ] Additional targeted verification:",
            f"  - `python tools/cloud_doc_backport.py open-pr --manifest {manifest_rel}`",
        ]
    )
    return "\n".join(lines) + "\n"

def open_backport_pr_from_manifest(
    *,
    manifest_path: Path,
    repo_root: Path,
    branch_name: str | None = None,
    base_ref: str = "main",
    git_bin: str = "git",
    gh_bin: str = "gh",
) -> dict[str, Any]:
    root = repo_root.resolve(strict=False)
    manifest_file = _resolve_repo_file(root, str(manifest_path), label="manifest")
    manifest = _load_json_file(manifest_file)
    source_target = manifest.get("source_target") if isinstance(manifest.get("source_target"), dict) else {}
    source_file = _resolve_repo_file(root, str(source_target.get("path") or ""), label="source target")
    _validate_open_pr_manifest(manifest, source_path=source_file)

    manifest_rel = _repo_relative(root, manifest_file)
    source_rel = _repo_relative(root, source_file)
    report_dir_rel = _repo_relative(root, manifest_file.parent)
    status_paths = _parse_git_status_paths(_run_pr_command([git_bin, "status", "--porcelain"], root=root))
    unexpected = [
        path
        for path in status_paths
        if path != source_rel and not path.startswith(f"{report_dir_rel}/")
    ]
    if unexpected:
        raise RuntimeError(
            "refusing to open PR with unrelated working-tree changes: " + ", ".join(unexpected[:5])
        )
    if source_rel not in status_paths:
        raise RuntimeError(f"source target has no working-tree change to commit: {source_rel}")

    current_branch = _run_pr_command([git_bin, "branch", "--show-current"], root=root)
    if current_branch != base_ref:
        raise RuntimeError(f"open-pr must run from {base_ref}; current branch is {current_branch or '-'}")

    resolved_branch = branch_name or _default_backport_branch_name(manifest, manifest_file)
    commit_title = "fix(backport): apply cloud doc review revisions"
    pr_body = _pr_body_from_manifest(manifest, manifest_rel=manifest_rel, source_rel=source_rel)

    _run_pr_command([git_bin, "switch", "-c", resolved_branch], root=root)
    _run_pr_command([git_bin, "add", source_rel], root=root)
    _run_pr_command(
        [
            git_bin,
            "commit",
            "-m",
            commit_title,
            "-m",
            f"Source: {source_rel}\nManifest: {manifest_rel}",
        ],
        root=root,
    )
    commit_sha = _run_pr_command([git_bin, "rev-parse", "HEAD"], root=root)
    _run_pr_command([git_bin, "push", "-u", "origin", resolved_branch], root=root)
    pr_url = ""
    pr_create_error = ""
    pr_create_command = [
        gh_bin,
        "pr",
        "create",
        "--base",
        base_ref,
        "--head",
        resolved_branch,
        "--draft",
        "--title",
        commit_title,
        "--body",
        pr_body,
    ]
    try:
        pr_url = _run_pr_command(pr_create_command, root=root).splitlines()[-1].strip()
    except RuntimeError as exc:
        pr_create_error = str(exc)
    switch_back_warning = ""
    try:
        _run_pr_command([git_bin, "switch", base_ref], root=root)
    except RuntimeError as exc:
        switch_back_warning = str(exc)
    result = {
        "schema_version": "cloud-doc-backport-pr/v1",
        "result": "PR_OPENED" if pr_url else "PR_CREATE_FAILED",
        "branch": resolved_branch,
        "base_ref": base_ref,
        "commit": commit_sha,
        "pr_url": pr_url,
        "manifest_path": manifest_rel,
        "source_path": source_rel,
        "source_table_suggestions": int((manifest.get("summary") or {}).get("source_table_suggestions") or 0),
    }
    if not pr_url:
        result.update(
            {
                "compare_url": _compare_url(
                    root=root,
                    base_ref=base_ref,
                    head_ref=resolved_branch,
                    git_bin=git_bin,
                    remote="origin",
                ),
                "pr_title": commit_title,
                "pr_body": pr_body,
                "pr_create_error": pr_create_error,
                "pr_create_command": shlex.join(pr_create_command),
            }
        )
    if switch_back_warning:
        result["warning"] = f"branch pushed, but switching back to {base_ref} failed: {switch_back_warning}"
    return result
