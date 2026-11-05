#!/usr/bin/env python3
"""Submit scoped frozen-data PRs; only a sound daily web_progress PR merges itself.

No source writes the default branch directly. Operator 2026-11-04 (「把每日刷新的内容PR也设成自动合入」)
lets the scheduled 网页说明书进度 PR squash-merge at the head this run validated; every other source
and every failed export still waits for review.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.workspace_snapshot import NAMES, atomic_json, content_digest, data_dir, loss_problems

REPOSITORY = "Bingboom/Hello-Docs"
AUTO_MERGE_KINDS = frozenset({"web_progress"})
# A merge made with the workflow token starts no push workflow, so verification is dispatched.
VERIFY_WORKFLOW = "workspace-data-verify.yml"


def command(args, *, cwd=None) -> str:
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False)
    if result.returncode:
        # Do not echo transport errors: authenticated URLs can occur in stderr.
        raise RuntimeError(f"{args[0]} failed (exit {result.returncode}); retry this stage")
    return result.stdout.strip()


def equivalent(left: Path, right: Path) -> bool:
    if not left.exists() or not right.exists():
        return False
    a, b = json.loads(left.read_text()), json.loads(right.read_text())
    if "schema" in a and ("documents" in a or "sentence_pairs" in a or "timeline" in a):
        return content_digest(a) == content_digest(b)
    def state(value):
        return "success" if value in ("changed", "unchanged") else value
    keys = ("stage", "content_sha256", "failure_key")
    return state(a.get("status")) == state(b.get("status")) and all(a.get(key) == b.get(key) for key in keys)


def open_prs(branch: str) -> list[dict]:
    return json.loads(command(["gh", "pr", "list", "--repo", REPOSITORY, "--head", branch,
                               "--base", "main", "--state", "open", "--json", "url"]))


def _candidates(root: Path, kind: str):
    log = root / ".tmp/workspace-refresh/result.json"
    report = json.loads(log.read_text()) if log.exists() else {}
    candidate = root / ".tmp/workspace-refresh" / (kind + "-candidate.json")
    snapshot = data_dir(root) / NAMES[kind]
    if candidate.exists() and report.get("export_status", report.get("status")) != "failed":
        snapshot = candidate
    candidates = [(snapshot, data_dir(root) / NAMES[kind]),
                  (data_dir(root) / (kind + "-status.json"), data_dir(root) / (kind + "-status.json"))]
    if report.get("export_status", report.get("status")) == "failed":
        candidates = candidates[1:]
    candidates = [(source, dest) for source, dest in candidates if source.exists()]
    return candidates, report


def pr_body(kind: str) -> str:
    merge_rule = "导出成功时自动合入（操作者 2026-11-04 授权）。" if kind in AUTO_MERGE_KINDS else "需审核后合入。"
    return (f"刷新工作台冻结数据；生产源表保持权威，{merge_rule}\n\n"
            "- 范围：仅 docs/knowledge/workspace-data 中对应来源的快照和状态。\n"
            "- 校验：完整分页、来源身份、快照结构和减少保护；失败时保留上次有效数据。\n"
            "- 执行证据：对应状态文件的 execution 与 content_sha256。\n"
            "- 合入不代表线上生效；需 Workspace Data Verify 核验目标提交、快照和页面哈希。\n")


def submit(root: Path, kind: str, state: dict | None = None) -> str:
    """Open or update the content PR; ``state["head"]`` receives the commit it now points at."""
    candidates, report = _candidates(root, kind)
    if not candidates:
        return "no-change"
    branch = "chore/workspace-" + kind
    with tempfile.TemporaryDirectory(prefix="workspace-content-") as tmp:
        checkout = Path(tmp) / "content"
        command(["git", "-c", "credential.helper=!gh auth git-credential", "clone", "--quiet", "--filter=blob:none", "--sparse", "--single-branch", "https://github.com/" + REPOSITORY + ".git", str(checkout)])
        command(["git", "sparse-checkout", "set", "docs/knowledge/workspace-data"], cwd=checkout)
        command(["git", "config", "credential.helper", "!gh auth git-credential"], cwd=checkout)
        remote = command(["git", "ls-remote", "--heads", "origin", branch], cwd=checkout)
        allowed = {(data_dir(root) / name).relative_to(root).as_posix() for name in (NAMES[kind], kind + "-status.json")}
        pending = []
        if remote:
            command(["git", "fetch", "origin", branch], cwd=checkout)
            branch_paths = command(["git", "diff", "--name-only", "origin/main...FETCH_HEAD"], cwd=checkout).splitlines()
            if set(branch_paths) - allowed:
                raise RuntimeError("content branch contains paths outside this source; review before retry")
            pending = open_prs(branch)
        # Only an open content PR keeps its branch. A branch without one is left over from a merged or
        # closed PR, and its squash-merged commits would conflict with main, so the run starts from main.
        command(["git", "switch", "-c", branch, "FETCH_HEAD" if pending else "origin/main"], cwd=checkout)
        changed = []
        for source, destination in candidates:
            relative = destination.relative_to(root)
            target = checkout / relative
            payload = json.loads(source.read_text())
            unchanged = report.get("export_status", report.get("status")) == "unchanged"
            if not target.exists() and (payload.get("status") == "unchanged" or unchanged):
                continue
            if target.exists() and source.name == kind + "-candidate.json":
                if loss_problems(payload, json.loads(target.read_text())):
                    raise RuntimeError("candidate regresses pending snapshot; review source before retry")
            if equivalent(source, target):
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            changed.append(relative.as_posix())
        if changed:
            command(["git", "config", "user.name", "github-actions[bot]"], cwd=checkout)
            command(["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"], cwd=checkout)
            command(["git", "add", "--", *changed], cwd=checkout)
            command(["git", "commit", "-m", f"chore(workspace): refresh {kind} snapshot"], cwd=checkout)
            push = ["git", "push", "origin", "HEAD:refs/heads/" + branch]
            if remote and not pending:
                # Replace the leftover branch only while it still holds the commit read above.
                push.insert(2, f"--force-with-lease=refs/heads/{branch}:{remote.split()[0]}")
            command(push, cwd=checkout)
        if state is not None:  # main() merges only a run that names a PR, at this head
            state["head"] = command(["git", "rev-parse", "HEAD"], cwd=checkout)
        if pending:
            return pending[0]["url"]
        if not changed:
            return "no-change"
        body = Path(tmp) / "body.md"
        body.write_text(pr_body(kind), encoding="utf-8")
        return command(["gh", "pr", "create", "--repo", REPOSITORY, "--base", "main", "--head", branch,
                        "--title", f"chore(workspace): refresh {kind} data", "--body-file", str(body)])


def exported(report: dict) -> bool:
    return report.get("export_status", report.get("status")) in ("changed", "unchanged")


def auto_merge(url: str, head: str, report: dict) -> None:
    """Squash-merge ``url`` only while it still points at ``head``, then start online verification."""
    report["stage"] = "auto-merge"
    command(["gh", "pr", "merge", url, "--squash", "--match-head-commit", head])
    report["review"] = {"status": "auto-merged", "url": url, "head": head}
    report["stage"] = "verify-dispatch"
    command(["gh", "workflow", "run", VERIFY_WORKFLOW, "--repo", REPOSITORY, "--ref", "main"])
    report["stage"] = "verify-dispatched"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=NAMES)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    log = args.root / ".tmp/workspace-refresh/result.json"
    report = json.loads(log.read_text()) if log.exists() else {"kind": args.kind}
    state: dict = {}
    try:
        outcome = submit(args.root.resolve(), args.kind, state)
        report["review"] = {"status": "not-needed" if outcome == "no-change" else "awaiting-review", "url": outcome}
        atomic_json(log, report)
        print(outcome)
    except (RuntimeError, OSError, ValueError, KeyError, TypeError) as exc:
        report.setdefault("export_status", report.get("status"))
        report.update(stage="review-submission", status="failed", error_type=type(exc).__name__)
        atomic_json(log, report)
        print("Snapshot retained; review submission failed. Retry submission without rerunning production.")
        return 1
    if outcome == "no-change" or args.kind not in AUTO_MERGE_KINDS or not exported(report) or "head" not in state:
        return 0
    try:
        auto_merge(outcome, state["head"], report)
    except RuntimeError as exc:
        report.setdefault("export_status", report.get("status"))
        report.update(status="failed", error_type=type(exc).__name__)
        atomic_json(log, report)
        print("Snapshot retained. Auto-merge stopped at " + report["stage"] + ": an unmerged PR waits for "
              "review; a merged one needs Workspace Data Verify run by hand.")
        return 1
    atomic_json(log, report)
    print("merged", outcome)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
