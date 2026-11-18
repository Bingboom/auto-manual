"""``python -m tools.product_matrix_base``: read the published manuals, stage and load the matrix base.

    read     --root <Hello-Docs checkout> --out <file outside git>
    stage    --reading <file> | --staged <file> [--root <checkout>] [--models A,B] [--markets US,EU]
             [--batch <label>] [--report <file outside git>] [--base-token ... --profile ...]
             [--write --yes] [--correct]
    projects [--write --yes]          # fill 产品.项目号（仅飞书） from 网页文档 (counts only)
    matrix   [--write --yes] [--drop-unused] [--manifest <manifest>]
    snapshot [--out <Hello-Docs>/docs/knowledge/product-matrix] [--write]
    check    --out <Hello-Docs>/docs/knowledge/product-matrix [--write [--refresh]] [--now <ISO time>] [--log <file>]

With a base, ``stage`` is a dry run that lists per table the rows to create, the rows already there, and the
existing rows whose values the current reading prints differently. ``--write --yes`` creates the absent rows;
``--correct`` (with ``--write --yes``) also corrects those differing 事实 rows in place, only while they are still
候选. Every file this command writes must lie outside any git work tree, except the snapshot and its status.json
(``snapshot``, ``check``), which go only to docs/knowledge/ of the Hello-Docs mirror, and ``check --log``, the run's
copy of that status (times, hashes and counts, no product data). Contract:
``code-as-doc/dev/product_matrix_base.md``.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools.product_matrix_base.reader import ReadingError, inside_git_work_tree, read_publication
from tools.product_matrix_base.rows import stage_rows
from tools.product_matrix_base.stage import (
    TABLES, LoadError, PartialWrite, correct, correction_plan, lark_runner, plan, provenance, read_rows, records_shape, write,
)
from tools.rtd.production_evidence import read_publications
from tools.utils.path_utils import Paths, PathSegments, docs_publish_of

CATALOG = Path("tools") / "rtd_portal_assets" / "product_catalog.json"
BASE_ENV = "FEISHU_PUBLISHED_DOCS_BASE_TOKEN"


def _split(raw: str | None) -> list[str] | None:
    return [item.strip() for item in raw.split(",") if item.strip()] if raw else None


def _out(path: Path) -> Path:
    if inside_git_work_tree(path.parent if not path.exists() else path):
        raise SystemExit(f"refusing to write {path}: product data stays outside every git work tree")
    return path


def _catalog(root: Path | None) -> dict[str, Any]:
    for base in ([root] if root else []) + [Path.cwd()]:
        path = base / CATALOG
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8")).get("models", {})
    return {}


def _read(args: argparse.Namespace) -> int:
    out = _out(args.out)
    try:
        reading = read_publication(args.root)
    except (ReadingError, OSError, ValueError) as exc:
        print(f"ERROR   {exc}")
        return 2
    out.write_text(json.dumps(reading, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for problem in reading["problems"]:
        print(f"PROBLEM {problem}")
    print(f"wrote {out}: " + ", ".join(f"{k} {v}" for k, v in reading["summary"].items()))
    return 0


def _write(run: Any, planned: dict[str, Any], lark_cli: str, report: dict[str, Any]) -> bool:
    """Write the planned rows and print the read-back; True when every row came back as written."""
    try:
        written = write(run, planned, use_records_shape=records_shape(lark_cli))
    except PartialWrite as exc:
        report["written"] = exc.report
        _print_written(exc.report)
        raise
    _print_written(written)
    report["written"] = written
    return not any(e["missing"] or e["mismatched"] for e in written.values())


def _print_written(written: dict[str, Any]) -> None:
    for table, entry in written.items():
        print(f"  {table}: 发送 {entry['sent']}，读回 {entry['read_back']}，缺失 {len(entry['missing'])}，"
              f"字段不符 {len(entry['mismatched'])}，表内现有 {entry['rows_after']} 行")


def _live(args: argparse.Namespace, base: str, staged: dict[str, Any], report: dict[str, Any]) -> int:
    run = lark_runner(base, profile=args.profile, identity=args.identity, lark_cli=args.lark_cli)
    try:
        planned = plan(run, staged)
        # After 不收录 filtering: a kept fact citing an excluded product's source surfaces here, before any write.
        planned["problems"] += provenance(planned["staged"], read_rows(run, planned["ids"]["来源"], ["来源键", "来源类型"]),
                                          _publications(args.root))
        if planned["skipped"]:
            print(f"  不收录产品 {len(planned['excluded'])} 个，跳过其行："
                  + "，".join(f"{t} {n}" for t, n in planned["skipped"].items()))
        for table in TABLES:
            info = planned["tables"].get(table)
            if info:
                print(f"  {table}: 待新建 {len(info['create'])}，已存在不动 {info['existing']}"
                      f"（表内现有 {info['rows_before']} 行）")
            if info and info["differ"]:
                fields = sorted({name for item in info["differ"] for name in item["fields"]})
                print(f"  {table}: 已存在但本次读取不同 {len(info['differ'])} 行（字段：{'、'.join(fields)}）")
        _print_corrections(planned, report)
        for problem in planned["problems"]:
            print(f"PROBLEM {problem}")
        report["plan"] = {t: {k: v for k, v in i.items() if k != "create"} for t, i in planned["tables"].items()}
        if not (args.write and args.yes):
            if args.write or args.correct:
                print("--write/--correct ignored: add --write --yes once the dry run above has been confirmed")
            print("dry run: nothing written")
            return 0
        if not _write(run, planned, args.lark_cli, report):
            print("ERROR   created rows did not read back as written; no correction attempted")
            return 1
        return _correct(run, planned, args.batch, report) if args.correct else 0
    except LoadError as exc:
        print(f"ERROR   {exc}")
        return 2


def _print_corrections(planned: dict[str, Any], report: dict[str, Any]) -> None:
    chosen = correction_plan(planned)
    if not chosen["correct"] and not chosen["decide"]:
        return
    fields = Counter(name for item in chosen["correct"] for name in item["fields"])
    print(f"  事实: 可原地修正 {len(chosen['correct'])} 行（"
          + "，".join(f"{name} {count}" for name, count in sorted(fields.items())) + "）")
    reasons = Counter(entry["reason"] for entry in chosen["decide"])
    for reason, count in sorted(reasons.items()):
        print(f"  事实: 需人决定 {count} 行：{reason}")
    report["correction_plan"] = {"correct": [item["key"] for item in chosen["correct"]], "decide": chosen["decide"]}


def _correct(run: Any, planned: dict[str, Any], batch: str, report: dict[str, Any]) -> int:
    try:
        fixed = correct(run, planned, batch)
    except PartialWrite as exc:
        report["corrected"] = exc.report
        print(f"  事实: 中途失败，已修正并读回 {exc.report['事实']['corrected']} 行")
        raise
    report["corrected"] = fixed
    print(f"  事实: 原地修正 {fixed['corrected']}（" + "，".join(f"{n} {c}" for n, c in sorted(fixed["fields"].items()))
          + f"），需人决定 {len(fixed['needs_decision'])}，读回不符 {len(fixed['mismatched'])}")
    return 1 if fixed["mismatched"] else 0


def _publications(root: Path | None) -> list[dict[str, Any]]:
    """The publish manifest's targets, the only publications a 网页说明书 source may name."""
    manifest = docs_publish_of(Paths(root or Path.cwd()).docs_dir) / PathSegments.PUBLISH_MANIFEST_JSON
    targets, _built = read_publications(manifest)
    if targets is None:
        raise LoadError(f"{manifest} is missing or malformed: provenance cannot be checked")
    return targets


def _stage(args: argparse.Namespace) -> int:
    if args.report:
        _out(args.report)  # refuse a bad output path before anything is written
    if args.staged:
        staged = json.loads(args.staged.read_text(encoding="utf-8"))
        staged = {table: staged.get(table, []) for table in TABLES}
    else:
        reading = json.loads(args.reading.read_text(encoding="utf-8"))
        names = {(model, market): name for model, market, name in reading.get("names", [])}
        staged = stage_rows(reading, _catalog(args.root), batch=args.batch, names=names,
                            models=_split(args.models), markets=_split(args.markets))
    print("staged: " + ", ".join(f"{table} {len(staged[table])}" for table in TABLES))
    report: dict[str, Any] = {"staged": staged}
    base = args.base_token or os.environ.get(BASE_ENV)
    if base:
        status = _live(args, base, staged, report)
    else:
        print("no base given: offline staging only, nothing compared or written")
        status = 0
    if args.report:
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"report: {args.report}")
    return status


def _matrix(args: argparse.Namespace) -> int:
    from tools.product_matrix_base import matrix

    base = args.base_token or os.environ.get(BASE_ENV)
    if not base:
        print("ERROR   no base given")
        return 2
    if args.report:
        _out(args.report)  # refuse a bad output path before anything is written
    run = lark_runner(base, profile=args.profile, identity=args.identity, lark_cli=args.lark_cli)
    try:
        snapshot = matrix.read_base(run)
        built = matrix.build(snapshot["products"], snapshot["attributes"], snapshot["facts"], snapshot["sources"])
        planned = matrix.plan(run, snapshot, built)
        planned["remove"] = matrix.select_removal(planned, args.remove_row)
        _print_matrix_plan(built, planned)
        if args.manifest:
            _update_manifest(args.manifest, matrix.manifest_fields(built))
        if args.report:
            _out(args.report).write_text(json.dumps({"columns": built["columns"], "empty": built["empty"],
                                                     "plan": _plan_summary(planned)},
                                                    ensure_ascii=False, indent=1, default=str) + "\n",
                                         encoding="utf-8")
        if not (args.write and args.yes):
            print("dry run: nothing written")
            return 0
        try:
            written = matrix.write(run, planned)
        except PartialWrite as exc:
            print(f"  中途失败，已读回：{json.dumps(exc.report, ensure_ascii=False)}")
            raise
        print(f"  加列 {written['columns_added']}，新建 {written['created']}，更新 {written['updated']}，"
              f"删行 {written['removed']}，缺失 {len(written['missing'])}，字段不符 {len(written['mismatched'])}，"
              f"未删掉 {len(written['lingering'])}，表内现有 {written['rows_after']} 行"
              f"（应为 {written['rows_expected']}）")
        if written["removed_keys"]:
            print("  已删行：" + "、".join(written["removed_keys"]))
        if args.drop and (written["missing"] or written["mismatched"]):
            print("  读回有缺失或不符，不删列")
        elif args.drop:
            print(f"  删除空列 {len(matrix.drop_columns(run, planned, args.drop))}")
        failed = written["missing"] or written["mismatched"] or written["lingering"] or not written["row_count_ok"]
        return 1 if failed else 0
    except LoadError as exc:
        print(f"ERROR   {exc}")
        return 2


def _print_matrix_plan(built: dict[str, Any], planned: dict[str, Any]) -> None:
    from tools.product_matrix_base import matrix

    filled, possible = matrix.filled_cells(built)
    print(f"矩阵: {len(built['rows'])} 行，属性列 {len(built['columns'])}（数值列 "
          f"{sum(c['type'] == 'number' for c in built['columns'])}），有值单元格 {filled}/{possible}，"
          f"有组件事实的产品 {built['components']}，数值缺失留空 {len(built['empty'])}")
    print(f"  待加列 {len(planned['add'])}，待新建行 {len(planned['create'])}，待更新行 {len(planned['update'])}，"
          f"不再使用的列 {len(planned['unused'])}，类型冲突列 {len(planned['clash'])}")
    if planned["removable"]:
        print(f"  可删候选 {len(planned['removable'])} 行（产品表已没有或标了不收录；不加 --remove-row 不删）："
              + "、".join(item["key"] for item in planned["removable"]))
    print(f"  本次删除 {len(planned['remove'])} 行" + (
        "：" + "、".join(item["key"] for item in planned["remove"]) if planned["remove"] else ""))


def _plan_summary(planned: dict[str, Any]) -> dict[str, Any]:
    """The matrix plan without row contents: rows carry the project index, which never leaves Feishu."""
    return {"add": planned["add"], "clash": planned["clash"], "unused": planned["unused"],
            "create": [row["产品键"] for row in planned["create"]], "removable": [r["key"] for r in planned["removable"]], "remove": [r["key"] for r in planned["remove"]],
            "update": [{"key": u["key"], "fields": sorted(u["fields"])} for u in planned["update"]]}


def _projects(args: argparse.Namespace) -> int:
    from tools.product_matrix_base import projects

    base = args.base_token or os.environ.get(BASE_ENV)
    if not base:
        print("ERROR   no base given")
        return 2
    if args.report:
        _out(args.report)
    run = lark_runner(base, profile=args.profile, identity=args.identity, lark_cli=args.lark_cli)
    try:
        planned = projects.plan(run)
        print(f"项目号: 产品 {planned['products']} 个，已有 {len(planned['filled'])}，可唯一补齐 {len(planned['fill'])}，"
              f"对到多个项目 {len(planned['ambiguous'])}，查不到 {len(planned['unknown'])}"
              f"（涉及项目 {planned['projects']} 个；项目号本身不打印、不写报告）")
        status = 0
        if planned["differs"]:
            print(f"  已有项目号但与网页文档不同 {len(planned['differs'])} 个（不改，按产品键列在报告里）")
        summary = projects.summary(planned)
        if args.write and args.yes:
            try:
                written = projects.write(run, planned)
            except PartialWrite as exc:
                summary["written"] = exc.report
                _projects_report(args.report, summary)
                print(f"  中途失败：已写 {exc.report['sent']}，读回一致 {exc.report['matched']}，"
                      f"未写 {len(exc.report['not_written'])}（产品键见报告）")
                raise
            print(f"  写入 {written['sent']}，读回一致 {written['matched']}，不一致或缺失 {len(written['problems'])}")
            summary["written"] = written
            status = 1 if written["problems"] else 0
        else:
            print("dry run: nothing written")
        _projects_report(args.report, summary)
        return status
    except LoadError as exc:
        print(f"ERROR   {exc}")
        return 2


def _projects_report(path: Path | None, summary: dict[str, Any]) -> None:
    if path:
        path.write_text(json.dumps(summary, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def _snapshot(args: argparse.Namespace) -> int:
    from tools.product_matrix_base import snapshot

    try:
        target = snapshot.safe_destination(args.out) if args.out else None
    except snapshot.SnapshotError as exc:
        print(f"ERROR   {exc}")
        return 2
    base = args.base_token or os.environ.get(BASE_ENV)
    if not base:
        print("ERROR   no base given")
        return 2
    run = lark_runner(base, profile=args.profile, identity=args.identity, lark_cli=args.lark_cli)
    try:
        document = snapshot.build_snapshot(run)
    except LoadError as exc:
        print(f"ERROR   {exc}")
        for kind, fact, source in getattr(exc, "rows", []) if args.explain_references else []:
            print(f"  {kind}: 事实键 {fact}" + (f"，来源键 {source}" if source else ""))  # keys only, printed locally
        return 2
    print(f"快照: {snapshot.summary(document)}")
    if not (args.write and target):
        print("dry run: nothing written" + ("" if target else " (give --out <Hello-Docs>/docs/knowledge/<dir>)"))
        return 0
    try:
        snapshot.write_snapshot(target, document)
    except snapshot.SnapshotError as exc:
        print(f"ERROR   {exc}")
        return 2
    print(f"wrote {target.name} under the Hello-Docs knowledge directory")
    return 0


def _no_base(_args: list[str]) -> dict[str, Any]:
    raise LoadError("no base given")


def _when(text: str) -> datetime:
    """--now: an ISO time (UTC when it names no offset), so a check can be replayed at a fixed moment."""
    from tools.product_matrix_base.sync import parse_time

    moment = parse_time(text)
    if moment is None:
        raise argparse.ArgumentTypeError(f"not an ISO time: {text!r}")
    return moment


def _check(args: argparse.Namespace) -> int:
    """Compare the base with the committed snapshot; record the verdict in status.json (and, with --refresh, the
    snapshot the check read when the base has moved on). Exit 0 current or refreshed, 1 behind, 2 failed."""
    from tools.product_matrix_base import snapshot, sync

    if args.refresh and not args.write:
        print("ERROR   --refresh writes the snapshot: add --write")
        return 2
    try:
        target = snapshot.safe_destination(args.out)
    except snapshot.SnapshotError as exc:
        print(f"ERROR   {exc}")
        return 2
    status_path = target.with_name(sync.STATUS_FILE)
    base = args.base_token or os.environ.get(BASE_ENV)
    if not base:
        print("ERROR   no base given")
    run = lark_runner(base, profile=args.profile, identity=args.identity, lark_cli=args.lark_cli) if base else _no_base
    status, fresh = sync.check(run, sync.read_json(target), sync.read_json(status_path),
                               now=args.now or datetime.now(timezone.utc), refresh=args.refresh,
                               execution=sync.execution_url())
    # Counts and times only: the reason never names a product, a project or a key.
    print(f"检查: {status['status']} · {status['lag']['reason']} · 最近同步成功 {status['last_success'] or '无记录'}")
    if args.write:
        try:
            if fresh is not None:
                snapshot.write_snapshot(target, fresh)
                print(f"快照: {snapshot.summary(fresh)}")
            snapshot.write_snapshot(status_path, status)
        except snapshot.SnapshotError as exc:
            print(f"ERROR   {exc}")
            return 2
        print(f"wrote {sync.STATUS_FILE}" + (f" and {target.name}" if fresh is not None else "")
              + " under the Hello-Docs knowledge directory")
    else:
        print("dry run: nothing written")
    if args.log:
        args.log.parent.mkdir(parents=True, exist_ok=True)
        args.log.write_text(json.dumps(status, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return {"current": 0, "refreshed": 0, "behind": 1}.get(status["status"], 2)


def _update_manifest(path: Path, matrix_fields: list[dict[str, str]]) -> None:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    for table in manifest["tables"]:
        if table["name"] == "矩阵":
            table["fields"] = matrix_fields
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"manifest: {path} 矩阵 {len(matrix_fields)} fields")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Product information matrix: read, stage, load and generate.")
    sub = parser.add_subparsers(dest="command", required=True)
    rd = sub.add_parser("read", help="every specification row of every published Web manual, and its facts")
    rd.add_argument("--root", type=Path, required=True, help="checkout whose docs/publish holds the publication")
    rd.add_argument("--out", type=Path, required=True, help="output file, outside any git work tree")
    rd.set_defaults(func=_read)
    st = sub.add_parser("stage", help="stage 产品/属性/来源/事实 rows; with a base, plan or write them")
    given = st.add_mutually_exclusive_group(required=True)
    given.add_argument("--reading", type=Path, help="a reading from the read command")
    given.add_argument("--staged", type=Path,
                       help="rows already staged per table ({\"产品\": [...], ...}), e.g. converted from another read")
    st.add_argument("--root", type=Path, help="checkout holding the publish manifest and the 产品分类 snapshot "
                                              "(default: this one); every 来源 must be one of its publications")
    st.add_argument("--models")
    st.add_argument("--markets")
    st.add_argument("--batch", default=f"extract-{datetime.now(timezone.utc):%Y%m%d}",
                    help="写入批次 label for new and corrected rows (default: extract-<UTC date>)")
    st.add_argument("--correct", action="store_true",
                    help="with --write --yes: correct differing 事实 rows in place while they are still 候选")
    st.add_argument("--report", type=Path, help="plan / read-back report, outside any git work tree")
    st.add_argument("--base-token", help=f"the matrix base (default: ${BASE_ENV})")
    st.add_argument("--profile", help="lark-cli profile")
    st.add_argument("--identity", default="bot", choices=["bot", "user"])
    st.add_argument("--lark-cli", default="lark-cli")
    st.add_argument("--write", action="store_true", help="create the absent rows (needs --yes)")
    st.add_argument("--yes", action="store_true", help="confirm the dry run was reviewed")
    st.set_defaults(func=_stage)
    pj = sub.add_parser("projects", help="fill 产品.项目号（仅飞书） from the base's 网页文档 table (counts only)")
    pj.add_argument("--base-token", help=f"the matrix base (default: ${BASE_ENV})")
    pj.add_argument("--profile")
    pj.add_argument("--identity", default="bot", choices=["bot", "user"])
    pj.add_argument("--lark-cli", default="lark-cli")
    pj.add_argument("--report", type=Path, help="产品键 lists by outcome (no project codes), outside any git work tree")
    pj.add_argument("--write", action="store_true")
    pj.add_argument("--yes", action="store_true")
    pj.set_defaults(func=_projects)
    sn = sub.add_parser("snapshot", help="read-only snapshot of the base for the private site (Hello-Docs only)")
    sn.add_argument("--base-token", help=f"the matrix base (default: ${BASE_ENV})")
    sn.add_argument("--profile")
    sn.add_argument("--identity", default="bot", choices=["bot", "user"])
    sn.add_argument("--lark-cli", default="lark-cli")
    sn.add_argument("--out", type=Path, help="directory under docs/knowledge/ of a Hello-Docs mirror checkout")
    sn.add_argument("--write", action="store_true", help="write the snapshot (else print counts only)")
    sn.add_argument("--explain-references", action="store_true",
                    help="when the reference check fails, print the fact and source keys behind it (local use only)")
    sn.set_defaults(func=_snapshot)
    ck = sub.add_parser("check", help="compare the base with the committed snapshot and record status.json")
    ck.add_argument("--base-token", help=f"the matrix base (default: ${BASE_ENV})")
    ck.add_argument("--profile")
    ck.add_argument("--identity", default="bot", choices=["bot", "user"])
    ck.add_argument("--lark-cli", default="lark-cli")
    ck.add_argument("--out", type=Path, required=True,
                    help="the snapshot's directory under docs/knowledge/ of a Hello-Docs mirror checkout")
    ck.add_argument("--write", action="store_true", help="write status.json (else print the verdict only)")
    ck.add_argument("--refresh", action="store_true", help="with --write: when the base has moved on, also write "
                                                           "the snapshot this check read")
    ck.add_argument("--now", type=_when, help="the check's time, ISO (tests and replays; default: the clock)")
    ck.add_argument("--log", type=Path, help="also write the status here (the workflow's run evidence)")
    ck.set_defaults(func=_check)
    mx = sub.add_parser("matrix", help="generate the 矩阵 table from the facts in the base")
    mx.add_argument("--base-token", help=f"the matrix base (default: ${BASE_ENV})")
    mx.add_argument("--profile")
    mx.add_argument("--identity", default="bot", choices=["bot", "user"])
    mx.add_argument("--lark-cli", default="lark-cli")
    mx.add_argument("--manifest", type=Path, help="rewrite this schema manifest's 矩阵 fields to the generated columns")
    mx.add_argument("--report", type=Path, help="columns, empty cells and plan, outside any git work tree")
    mx.add_argument("--write", action="store_true")
    mx.add_argument("--yes", action="store_true")
    mx.add_argument("--drop", action="append", default=[], metavar="COLUMN",
                    help="after a clean write, delete this matrix column if the generator no longer produces it and "
                         "every row is empty (repeat per column; nothing is dropped by sweep)")
    mx.add_argument("--remove-row", action="append", default=[], metavar="产品键",
                    help="delete this matrix row; only a row whose product left 产品 or is marked 不收录 (repeat per "
                         "row; a normal refresh lists such rows but never deletes them)")
    mx.set_defaults(func=_matrix)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
