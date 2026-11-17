"""``python -m tools.product_matrix_base``: extract the published manuals' specification rows, stage and load them.

    extract  --root <Hello-Docs checkout> --out <file outside git>
    stage    --extraction <file> | --staged <file> [--models A,B] [--markets US,EU] [--attributes k1,k2] [--report <file outside git>]
             [--base-token ... --profile ...]   # with a base: compare with the live tables (dry run)
             [--write --yes]                    # create the absent rows, then read every one back

Extraction output, staging plans and read-back reports are internal product data: every file this command writes
must lie outside any git work tree. Without ``--write --yes`` nothing is written to the base. Contract:
``code-as-doc/dev/product_matrix_base.md``.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from tools.product_matrix_base.extract import DICTIONARY, ExtractionError, extract, inside_git_work_tree
from tools.product_matrix_base.stage import (
    TABLES, LoadError, PartialWrite, lark_runner, plan, provenance, read_rows, records_shape, stage_rows, write,
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


def _extract(args: argparse.Namespace) -> int:
    out = _out(args.out)
    try:
        document = extract(args.root, args.dictionary, _catalog(args.root))
    except (ExtractionError, OSError, ValueError) as exc:
        print(f"ERROR   {exc}")
        return 2
    out.write_text(json.dumps(document, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for problem in document["problems"]:
        print(f"PROBLEM {problem}")
    print(f"wrote {out}: " + ", ".join(f"{k} {v}" for k, v in document["summary"].items()))
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
        planned["problems"] += provenance(staged, read_rows(run, planned["ids"]["来源"], ["来源键", "来源类型"]),
                                          _publications(args.root))
        for table in TABLES:
            info = planned["tables"].get(table)
            if info:
                print(f"  {table}: 待新建 {len(info['create'])}，已存在不动 {info['existing']}"
                      f"（表内现有 {info['rows_before']} 行）")
        for problem in planned["problems"]:
            print(f"PROBLEM {problem}")
        report["plan"] = {t: {k: v for k, v in i.items() if k != "create"} for t, i in planned["tables"].items()}
        if not (args.write and args.yes):
            if args.write:
                print("--write ignored: add --yes once the dry run above has been confirmed")
            print("dry run: nothing written")
            return 0
        return 0 if _write(run, planned, args.lark_cli, report) else 1
    except LoadError as exc:
        print(f"ERROR   {exc}")
        return 2


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
        extraction = json.loads(args.extraction.read_text(encoding="utf-8"))
        staged = stage_rows(extraction, _catalog(args.root), models=_split(args.models),
                            markets=_split(args.markets), attributes=_split(args.attributes))
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


def _update_manifest(path: Path, matrix_fields: list[dict[str, str]]) -> None:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    for table in manifest["tables"]:
        if table["name"] == "矩阵":
            table["fields"] = matrix_fields
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"manifest: {path} 矩阵 {len(matrix_fields)} fields")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Product information matrix: extract, stage and load.")
    sub = parser.add_subparsers(dest="command", required=True)
    ex = sub.add_parser("extract", help="every specification-table row of every published Web manual")
    ex.add_argument("--root", type=Path, required=True, help="checkout whose docs/publish holds the publication")
    ex.add_argument("--dictionary", type=Path, default=DICTIONARY)
    ex.add_argument("--out", type=Path, required=True, help="output file, outside any git work tree")
    ex.set_defaults(func=_extract)
    st = sub.add_parser("stage", help="stage 产品/属性/来源/事实 rows; with a base, plan or write them")
    given = st.add_mutually_exclusive_group(required=True)
    given.add_argument("--extraction", type=Path, help="an extraction from the extract command")
    given.add_argument("--staged", type=Path,
                       help="rows already staged per table ({\"产品\": [...], ...}), e.g. converted from another read")
    st.add_argument("--root", type=Path, help="checkout holding the publish manifest and the 产品分类 snapshot "
                                              "(default: this one); every 来源 must be one of its publications")
    st.add_argument("--models")
    st.add_argument("--markets")
    st.add_argument("--attributes")
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
    sn.set_defaults(func=_snapshot)
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
