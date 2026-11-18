"""``python -m tools.product_matrix_base.publish``: put a product-matrix check's result up for review.

After ``check --write --refresh`` the checkout holds the snapshot and status.json the check wrote. This opens or
updates one content PR (branch ``chore/product-matrix-refresh``) with whichever of the two should change on main:
the snapshot when the check refreshed it, the status when ``sync.worth_committing`` says so (a new verdict, new
content, or a confirmation older than ``CONFIRM_AFTER_DAYS``). The PR always waits for review: the snapshot holds
project numbers, and no merge of it is automatic. It reuses the workspace refresh's PR submission
(``tools/workspace_refresh_publish.submit_files``).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from tools.product_matrix_base import snapshot, sync
from tools.rtd.product_library import SNAPSHOT
from tools.utils.path_utils import PathSegments

BRANCH = "chore/product-matrix-refresh"
TITLE = "chore(knowledge): refresh product matrix snapshot"
BODY = ("按飞书产品信息矩阵刷新私有站的产品快照与同步状态；飞书保持权威，需审核后合入。\n\n"
        "- 范围：仅 docs/knowledge/product-matrix/ 的 snapshot.json 与 status.json。\n"
        "- 判断：status.json 的 lag 写明快照是否落后及原因；last_success 是最近一次确认与飞书一致的时间。\n"
        "- 人负责的字段（核实、裁定、说明）只在飞书里改，本 PR 不改。\n"
        "- 执行证据：status.json 的 execution。\n")


def directory(root: Path) -> Path:
    return root / PathSegments.DOCS / PathSegments.KNOWLEDGE / SNAPSHOT.parent


def candidates(root: Path, status: dict) -> list[tuple[Path, Path]]:
    folder = directory(root)
    paths = [folder / snapshot.FILE_NAME] if status.get("status") == "refreshed" else []
    return [(path, path) for path in [*paths, folder / sync.STATUS_FILE] if path.is_file()]


def skip(source: Path, target: Path) -> bool:
    """Leave a file out when main already says the same (the snapshot byte for byte, the status by verdict)."""
    if not target.exists():
        return False
    if source.name == sync.STATUS_FILE:
        return not sync.worth_committing(sync.read_json(source) or {}, sync.read_json(target))
    return source.read_bytes() == target.read_bytes()


def submit(root: Path, state: dict | None = None) -> str:
    from tools.workspace_refresh_publish import submit_files

    status = sync.read_json(directory(root) / sync.STATUS_FILE) or {}
    files = candidates(root, status)
    if not files:
        return "no-change"
    folder = directory(root)
    return submit_files(root, branch=BRANCH, directory=folder,
                        allowed={folder / snapshot.FILE_NAME, folder / sync.STATUS_FILE}, candidates=files,
                        skip=skip, message=TITLE, title=TITLE, body=BODY, state=state)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--report", type=Path, help="the check's --log; the PR's outcome is added to it")
    args = parser.parse_args(argv)
    report = (sync.read_json(args.report) if args.report else None) or {"kind": sync.KIND}
    try:
        outcome = submit(args.root.resolve())
    except (RuntimeError, OSError, ValueError, KeyError, TypeError) as exc:
        report.update(review={"status": "failed", "error_type": type(exc).__name__})
        print("Snapshot and status kept in this run; the review submission failed. Retry the workflow.")
        code = 1
    else:
        report["review"] = {"status": "not-needed" if outcome == "no-change" else "awaiting-review", "url": outcome}
        print(outcome)
        code = 0
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
