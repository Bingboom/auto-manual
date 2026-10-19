#!/usr/bin/env python3
"""Submit scoped frozen-data PRs; never merge or write the default branch."""
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
    if "schema" in a and ("documents" in a or "sentence_pairs" in a):
        return content_digest(a) == content_digest(b)
    def state(value):
        return "success" if value in ("changed", "unchanged") else value
    keys = ("stage", "content_sha256", "failure_key")
    return state(a.get("status")) == state(b.get("status")) and all(a.get(key) == b.get(key) for key in keys)


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


def submit(root: Path, kind: str) -> str:
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
        if remote:
            command(["git", "fetch", "origin", branch], cwd=checkout)
            command(["git", "switch", "-c", branch, "FETCH_HEAD"], cwd=checkout)
        else:
            command(["git", "switch", "-c", branch], cwd=checkout)
        allowed = {(data_dir(root) / name).relative_to(root).as_posix() for name in (NAMES[kind], kind + "-status.json")}
        branch_paths = command(["git", "diff", "--name-only", "origin/main...HEAD"], cwd=checkout).splitlines()
        if set(branch_paths) - allowed:
            raise RuntimeError("content branch contains paths outside this source; review before retry")
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
            command(["git", "push", "origin", "HEAD:" + branch], cwd=checkout)
        prs = json.loads(command(["gh", "pr", "list", "--repo", REPOSITORY, "--head", branch,
                                  "--base", "main", "--state", "open", "--json", "url"]))
        if prs:
            return prs[0]["url"]
        if not changed:
            return "no-change"
        body = Path(tmp) / "body.md"
        body.write_text("刷新工作台冻结数据；生产源表保持权威，需审核后合入。\n\n"
                        "- 范围：仅 docs/knowledge/workspace-data 中对应来源的快照和状态。\n"
                        "- 校验：完整分页、来源身份、快照结构和减少保护；失败时保留上次有效数据。\n"
                        "- 执行证据：对应状态文件的 execution 与 content_sha256。\n"
                        "- 合入不代表线上生效；需 Workspace Data Verify 核验目标提交、快照和页面哈希。\n", encoding="utf-8")
        return command(["gh", "pr", "create", "--repo", REPOSITORY, "--base", "main", "--head", branch,
                        "--title", f"chore(workspace): refresh {kind} data", "--body-file", str(body)])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=NAMES)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    log = args.root / ".tmp/workspace-refresh/result.json"
    report = json.loads(log.read_text()) if log.exists() else {"kind": args.kind}
    try:
        outcome = submit(args.root.resolve(), args.kind)
        report["review"] = {"status": "not-needed" if outcome == "no-change" else "awaiting-review", "url": outcome}
        atomic_json(log, report)
        print(outcome)
        return 0
    except (RuntimeError, OSError, ValueError, KeyError, TypeError) as exc:
        report.setdefault("export_status", report.get("status"))
        report.update(stage="review-submission", status="failed", error_type=type(exc).__name__)
        atomic_json(log, report)
        print("Snapshot retained; review submission failed. Retry submission without rerunning production.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
