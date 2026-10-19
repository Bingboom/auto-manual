#!/usr/bin/env python3
"""Use one existing GitHub issue per failed source/stage, without repeat comments."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import tempfile

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.workspace_refresh_publish import command


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", required=True, choices=("deliverables", "corpus", "publication", "mirror"))
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--failed", action="store_true")
    args = parser.parse_args()
    report = json.loads(args.report.read_text()) if args.report.exists() else {}
    failed = args.failed or report.get("status") == "failed"
    repository = os.environ["GITHUB_REPOSITORY"]
    title = "Workspace data update: " + args.kind
    issues = json.loads(command(["gh", "issue", "list", "--repo", repository, "--state", "open",
                                 "--search", title + " in:title", "--json", "number,title"]))
    existing = next((v for v in issues if v["title"] == title), None)
    if not failed:
        if existing:
            command(["gh", "issue", "close", str(existing["number"]), "--repo", repository])
        return 0
    if existing:
        return 0  # Same incident: evidence stays in execution logs; no repeated notification.
    run_url = f"https://github.com/{repository}/actions/runs/{os.environ.get('GITHUB_RUN_ID', '')}"
    body = (f"来源：{args.kind}\n\n上次有效数据：{report.get('last_success') or '见来源快照'}\n\n"
            f"失败阶段：{report.get('stage') or 'review-submission'}\n\n日志：{run_url}\n\n"
            f"补做：{report.get('resume') or '重新运行该工作流的失败任务；无需重跑生产'}\n\n"
            "已完成的生产保持有效；快照导出或构建成功不代表工作台已更新。\n")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "body.md"
        path.write_text(body, encoding="utf-8")
        print(command(["gh", "issue", "create", "--repo", repository, "--title", title, "--body-file", str(path)]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
