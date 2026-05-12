from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request

from tools.review_support import review_dir_for_target
from tools.utils.targets import resolve_output_lang


def format_command(cmd: list[str]) -> str:
    return subprocess.list2cmdline([str(part) for part in cmd])


def run_command(cmd: list[str], *, root: Path, cwd: Path | None = None) -> str:
    resolved_cwd = cwd or root
    print(f"[review-start] {format_command(cmd)}")
    proc = subprocess.run(
        cmd,
        cwd=str(resolved_cwd),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    if proc.returncode:
        lines = [line.strip() for line in (proc.stderr or proc.stdout or "").splitlines() if line.strip()]
        message = lines[-1] if lines else "command failed"
        raise RuntimeError(f"{message} (exit={proc.returncode}, cmd={format_command(cmd)})")
    return proc.stdout or ""


def run_git(args: list[str], *, root: Path, cwd: Path | None = None) -> str:
    return run_command(["git", *args], root=root, cwd=cwd)


def build_py_command(
    worktree: Path,
    *,
    action: str,
    config_path: Path,
    model: str | None = None,
    region: str | None = None,
    data_root: str | None = None,
    source: str | None = None,
    refresh_review: bool = False,
) -> list[str]:
    cmd = [
        sys.executable,
        str(worktree / "build.py"),
        action,
        "--config",
        str(config_path),
    ]
    if model:
        cmd += ["--model", model]
    if region:
        cmd += ["--region", region]
    if data_root:
        cmd += ["--data-root", data_root]
    if source:
        cmd += ["--source", source]
    if refresh_review:
        cmd.append("--refresh-review")
    return cmd


def sync_phase2_snapshot_before_review_start(*, root: Path, config_path: Path, data_root: str | None) -> None:
    run_command(
        [
            sys.executable,
            str(root / "build.py"),
            "sync-data",
            "--config",
            str(config_path),
            *(["--data-root", data_root] if data_root else []),
        ],
        root=root,
    )


def resolve_docs_dir_for_config(
    *,
    root: Path,
    config_path: Path,
    cfg: dict[str, Any] | None,
    load_config_fn: Callable[[Path], dict[str, Any]],
) -> Path:
    resolved_config_path = config_path if config_path.is_absolute() else (root / config_path)
    loaded_cfg = cfg if cfg is not None else load_config_fn(resolved_config_path)
    paths_cfg_raw = loaded_cfg.get("paths", {})
    paths_cfg = paths_cfg_raw if isinstance(paths_cfg_raw, dict) else {}
    raw = paths_cfg.get("docs_dir")
    if isinstance(raw, str) and raw.strip():
        candidate = Path(raw.strip())
        return candidate if candidate.is_absolute() else (resolved_config_path.parent / candidate)
    return resolved_config_path.parent / "docs"


def review_dir_for_target_config(
    *,
    root: Path,
    config_path: Path,
    model: str,
    region: str,
    load_config_fn: Callable[[Path], dict[str, Any]],
) -> Path:
    cfg = load_config_fn(config_path)
    docs_dir = resolve_docs_dir_for_config(root=root, config_path=config_path, cfg=cfg, load_config_fn=load_config_fn)
    output_lang = resolve_output_lang(cfg)
    candidate = review_dir_for_target(docs_dir=docs_dir, model=model, region=region, lang=output_lang)
    if candidate.exists():
        return candidate
    return review_dir_for_target(docs_dir=docs_dir, model=model, region=region)


def review_root_for_target_config(
    *,
    root: Path,
    config_path: Path,
    model: str,
    region: str,
    load_config_fn: Callable[[Path], dict[str, Any]],
) -> Path:
    cfg = load_config_fn(config_path)
    docs_dir = resolve_docs_dir_for_config(root=root, config_path=config_path, cfg=cfg, load_config_fn=load_config_fn)
    return review_dir_for_target(docs_dir=docs_dir, model=model, region=region)
def worktree_dir_for_branch(*, root: Path, branch_name: str, slug_branch_token_fn: Callable[[str], str]) -> Path:
    return root / ".tmp" / "review-start-worktrees" / slug_branch_token_fn(branch_name)


def remove_worktree(*, root: Path, path: Path) -> None:
    if not path.exists():
        return
    proc = subprocess.run(
        ["git", "worktree", "remove", "--force", str(path)],
        cwd=str(root),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if proc.returncode != 0 and path.exists():
        shutil.rmtree(path, ignore_errors=True)


def prepare_branch_worktree(
    *,
    root: Path,
    branch_name: str,
    base_ref: str,
    slug_branch_token_fn: Callable[[str], str],
) -> Path:
    run_git(["fetch", "origin", "--prune"], root=root)
    worktree = worktree_dir_for_branch(root=root, branch_name=branch_name, slug_branch_token_fn=slug_branch_token_fn)
    remove_worktree(root=root, path=worktree)
    worktree.parent.mkdir(parents=True, exist_ok=True)
    source_ref = f"origin/{base_ref}"
    run_git(["worktree", "add", "--force", str(worktree), source_ref], root=root)
    run_git(["checkout", "-B", branch_name, source_ref], root=root, cwd=worktree)
    return worktree


def configure_git_identity(*, worktree: Path, root: Path) -> None:
    run_git(
        [
            "config",
            "user.name",
            os.environ.get("GIT_AUTHOR_NAME", "github-actions[bot]"),
        ],
        root=root,
        cwd=worktree,
    )
    run_git(
        [
            "config",
            "user.email",
            os.environ.get("GIT_AUTHOR_EMAIL", "41898282+github-actions[bot]@users.noreply.github.com"),
        ],
        root=root,
        cwd=worktree,
    )


def ensure_review_bundle_on_branch(
    *,
    root: Path,
    worktree: Path,
    build_config_path: Path,
    model: str,
    region: str,
    data_root: str | None,
    load_config_fn: Callable[[Path], dict[str, Any]],
) -> Path:
    worktree_config_path = worktree / build_config_path.name

    run_command(
        build_py_command(
            worktree,
            action="rst",
            config_path=worktree_config_path,
            model=model,
            region=region,
            data_root=data_root,
            source="runtime",
        ),
        root=root,
        cwd=worktree,
    )
    run_command(
        build_py_command(
            worktree,
            action="review",
            config_path=worktree_config_path,
            model=model,
            region=region,
            data_root=data_root,
            refresh_review=True,
        ),
        root=root,
        cwd=worktree,
    )
    review_dir = review_dir_for_target_config(
        root=root,
        config_path=worktree_config_path,
        model=model,
        region=region,
        load_config_fn=load_config_fn,
    )
    if not review_dir.exists():
        raise RuntimeError(f"Review bundle was not created: {review_dir}")
    return review_dir


def commit_review_bundle_if_changed(*, root: Path, worktree: Path, review_dir: Path, record: Any) -> bool:
    review_rel = review_dir.relative_to(worktree).as_posix()
    run_git(["add", "--", review_rel], root=root, cwd=worktree)
    proc = subprocess.run(
        ["git", "diff", "--cached", "--quiet", "--", review_rel],
        cwd=str(worktree),
        check=False,
    )
    if proc.returncode == 0:
        return False
    if proc.returncode != 1:
        raise RuntimeError(f"Unable to inspect staged review changes for {review_rel}")
    run_git(
        [
            "commit",
            "-m",
            f"seed review bundle for {record.document_id or record.document_key}",
        ],
        root=root,
        cwd=worktree,
    )
    return True


def push_branch(*, root: Path, worktree: Path, branch_name: str) -> None:
    run_git(["push", "--force-with-lease", "-u", "origin", branch_name], root=root, cwd=worktree)


def create_empty_review_start_commit(*, root: Path, worktree: Path, record: Any) -> None:
    run_git(
        [
            "commit",
            "--allow-empty",
            "-m",
            f"start review for {record.document_id or record.document_key}",
        ],
        root=root,
        cwd=worktree,
    )


def github_api_request(*, method: str, path: str, token: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    body = None
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib_request.Request(
        "https://api.github.com" + path,
        data=body,
        headers=headers,
        method=method,
    )
    try:
        with urllib_request.urlopen(request) as response:
            raw = response.read().decode("utf-8") or "{}"
            return json.loads(raw)
    except urllib_error.HTTPError as exc:
        detail = exc.read().decode("utf-8")
        raise RuntimeError(f"GitHub API {method} {path} failed: {detail or exc}") from exc


def ensure_pull_request_for_branch(
    *,
    root: Path,
    repository: str,
    branch_name: str,
    base_ref: str,
    token: str,
    record: Any,
    worktree: Path | None = None,
) -> str:
    owner = repository.split("/", 1)[0]
    query = urllib_parse.urlencode(
        {
            "state": "open",
            "head": f"{owner}:{branch_name}",
            "base": base_ref,
        }
    )
    existing = github_api_request(
        method="GET",
        path=f"/repos/{repository}/pulls?{query}",
        token=token,
    )
    if isinstance(existing, list) and existing:
        first = existing[0]
        if isinstance(first, dict):
            url = str(first.get("html_url") or "").strip()
            if url:
                return url

    payload = {
        "title": f"Start review for {record.document_id or record.document_key}",
        "head": branch_name,
        "base": base_ref,
        "body": "\n".join(
            [
                "Auto-generated review start branch.",
                "",
                f"- Document_ID: {record.document_id}",
                f"- Document_Key: {record.document_key}",
                f"- Lang: {record.lang}",
                f"- Version: {record.version}",
            ]
        ),
    }
    try:
        created = github_api_request(
            method="POST",
            path=f"/repos/{repository}/pulls",
            token=token,
            payload=payload,
        )
    except RuntimeError as exc:
        if worktree is None or "No commits between" not in str(exc):
            raise
        create_empty_review_start_commit(root=root, worktree=worktree, record=record)
        push_branch(root=root, worktree=worktree, branch_name=branch_name)
        created = github_api_request(
            method="POST",
            path=f"/repos/{repository}/pulls",
            token=token,
            payload=payload,
        )
    url = str(created.get("html_url") or "").strip()
    if not url:
        raise RuntimeError("GitHub pull request creation did not return html_url")
    return url


def start_review_for_record(
    *,
    root: Path,
    record: Any,
    build_config_path: Path,
    snapshot_data_root: str | None,
    base_ref: str,
    repository: str,
    token: str,
    slug_branch_token_fn: Callable[[str], str],
    resolve_target_for_review_start_fn: Callable[[Any], tuple[str, str]],
    generate_review_branch_name_fn: Callable[[Any], str],
    load_config_fn: Callable[[Path], dict[str, Any]],
) -> tuple[str, str]:
    model, region = resolve_target_for_review_start_fn(record)
    branch_name = generate_review_branch_name_fn(record)
    worktree = prepare_branch_worktree(
        root=root,
        branch_name=branch_name,
        base_ref=base_ref,
        slug_branch_token_fn=slug_branch_token_fn,
    )
    try:
        configure_git_identity(worktree=worktree, root=root)
        review_dir = ensure_review_bundle_on_branch(
            root=root,
            worktree=worktree,
            build_config_path=build_config_path,
            model=model,
            region=region,
            data_root=snapshot_data_root,
            load_config_fn=load_config_fn,
        )
        commit_review_bundle_if_changed(root=root, worktree=worktree, review_dir=review_dir, record=record)
        push_branch(root=root, worktree=worktree, branch_name=branch_name)
        pr_url = ensure_pull_request_for_branch(
            root=root,
            repository=repository,
            branch_name=branch_name,
            base_ref=base_ref,
            token=token,
            record=record,
            worktree=worktree,
        )
        return branch_name, pr_url
    finally:
        remove_worktree(root=root, path=worktree)
