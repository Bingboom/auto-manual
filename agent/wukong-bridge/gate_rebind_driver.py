#!/usr/bin/env python3
"""同源门重绑驱动：在 auto-manual 工程仓执行操作者已批准的契约重绑并开 PR。

前置：一个 verdict=content_only 的诊断作业（gate_diff_driver 产物）。
守卫：契约现值必须仍等于诊断时记录的 old_content_sha（否则要求重新诊断）；
装配变更一律拒绝。流程：worktree → rebind --write（带批准记录）→ 机械更新
测试里钉的内容 sha → 针对性测试 → commit → push → gh pr create。
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import traceback
from datetime import datetime, timezone
from pathlib import Path

AM = Path(os.environ.get(
    "AUTO_MANUAL_REPO_ROOT",
    os.environ.get("HELLO_DOCS_REPO_ROOT", str(Path(__file__).resolve().parents[2])),
))
AM_PY = AM / ".venv/bin/python3"


def sh(args, cwd=None, timeout=1800):
    proc = subprocess.run([str(a) for a in args], cwd=cwd, capture_output=True,
                          text=True, timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError(
            f"command failed ({' '.join(str(a) for a in args)}): "
            f"{proc.stdout[-400:]} {proc.stderr[-1200:]}")
    return proc.stdout


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--diff-job-dir", required=True)
    parser.add_argument("--job-dir", required=True)
    parser.add_argument("--approved-by", required=True)
    parser.add_argument("--approval-note", default="")
    args = parser.parse_args()
    job_dir = Path(args.job_dir)
    diff_dir = Path(args.diff_job_dir)
    result: dict = {"job_kind": "idml_gate_rebind",
                    "started_at": datetime.now(timezone.utc).isoformat()}
    worktree = job_dir / "am-worktree"
    try:
        diff_result = json.loads((diff_dir / "result.json").read_text(encoding="utf-8"))
        if diff_result.get("verdict") != "content_only":
            raise RuntimeError(
                f"诊断结论是 {diff_result.get('verdict')!r}，只有 content_only 允许自动重绑——"
                "装配变更需人工排查根因后走手工路线。")
        diff = diff_result["diff"]
        model, region = diff_result["model"], diff_result["region"]
        ir_path = Path(diff_result["ir_path"])
        if not ir_path.is_file():
            raise RuntimeError("诊断作业的 manual.ir.json 不在了——重新跑诊断。")
        plan_rel = diff["plan_rel"]
        old_sha = diff["old_content_sha"]

        job8 = job_dir.name[:8]
        branch = f"fix/idml-rebind-{model}-{region}-{job8}".lower()
        sh(["git", "fetch", "origin", "main"], cwd=AM)
        sh(["git", "worktree", "add", "--force", worktree, "-b", branch,
            "origin/main"], cwd=AM)

        plan_path = worktree / plan_rel
        if not plan_path.is_file():
            raise RuntimeError(f"工程仓里找不到契约 {plan_rel}")
        current_sha = json.loads(plan_path.read_text(encoding="utf-8"))[
            "identity"]["content"]["manual_content_sha256"]
        if current_sha != old_sha:
            raise RuntimeError(
                f"契约在诊断之后变过（现 {current_sha[:12]} ≠ 诊断时 {old_sha[:12]}）——"
                "重新跑 idml_gate_diff 再批准。")

        approved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        method = ("wukong chat approval + idml_gate_diff summary "
                  f"(job {diff_dir.name}): structure/order/language identical, "
                  f"{len(diff['changed'])} content pages refreshed")
        if args.approval_note:
            method += f"; note: {args.approval_note}"
        sh([AM_PY, "tools/reference_layout_rebind.py", "--plan", plan_rel,
            "--manual-ir", ir_path, "--approve-content-change",
            "--approved-by", args.approved_by, "--approved-at", approved_at,
            "--approval-method", method, "--write"], cwd=worktree)
        new_sha = json.loads(plan_path.read_text(encoding="utf-8"))[
            "identity"]["content"]["manual_content_sha256"]

        pinned_tests = []
        for test_file in sorted((worktree / "tests").glob("*.py")):
            text = test_file.read_text(encoding="utf-8")
            if old_sha in text:
                test_file.write_text(text.replace(old_sha, new_sha), encoding="utf-8")
                pinned_tests.append(test_file.name)
        sh([AM_PY, "-m", "unittest", "tests.test_reference_layout_plan"],
           cwd=worktree)

        sh(["git", "add", plan_rel, *[f"tests/{n}" for n in pinned_tests]],
           cwd=worktree)
        message = (
            f"fix(idml): rebind {model}/{region} reference layout "
            f"(content-only, operator-approved)\n\n"
            f"Approved by {args.approved_by} at {approved_at} via wukong gate flow.\n"
            f"idml_gate_diff job {diff_dir.name}: {diff['pinned_pages']} pages, "
            f"structure/order/language identical, {len(diff['changed'])} page "
            f"digests refreshed, {diff['same_count']} unchanged.\n"
            f"Content sha {old_sha[:12]} -> {new_sha[:12]}; "
            f"test pins updated: {', '.join(pinned_tests) or 'none'}.")
        sh(["git", "commit", "-m", message], cwd=worktree)
        sh(["git", "push", "-u", "origin", branch], cwd=worktree)
        pr_out = sh(["gh", "pr", "create", "--repo", "Bingboom/auto-manual",
                     "--base", "main", "--head", branch,
                     "--title", f"fix(idml): rebind {model}/{region} reference "
                                f"layout (content-only)",
                     "--body", message + "\n\nFull validation runs in CI. "
                     "Merge, wait for the mirror sync, then re-dispatch Publish."],
                    cwd=worktree)
        result.update(status="done", pr_url=pr_out.strip().splitlines()[-1],
                      branch=branch, new_content_sha=new_sha,
                      pinned_tests=pinned_tests)
    except Exception as exc:  # noqa: BLE001
        result.update(status="failed", error=str(exc)[-1500:],
                      trace=traceback.format_exc()[-1500:])
    finally:
        try:
            sh(["git", "worktree", "remove", worktree, "--force"], cwd=AM)
        except Exception:  # noqa: BLE001
            shutil.rmtree(worktree, ignore_errors=True)
        result["finished_at"] = datetime.now(timezone.utc).isoformat()
        (job_dir / "result.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
