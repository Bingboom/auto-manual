"""``python -m tools.product_matrix_base``: extract the published manuals' specification rows, stage and load them.

    extract  --root <Hello-Docs checkout> --out <file outside git>
    stage    --extraction <file> [--models A,B] [--markets US,EU] [--attributes k1,k2] [--report <file outside git>]
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
    TABLES, LoadError, lark_runner, plan, records_shape, stage_rows, write,
)

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


def _stage(args: argparse.Namespace) -> int:
    extraction = json.loads(args.extraction.read_text(encoding="utf-8"))
    staged = stage_rows(extraction, _catalog(args.root), models=_split(args.models), markets=_split(args.markets),
                        attributes=_split(args.attributes))
    print("staged: " + ", ".join(f"{table} {len(staged[table])}" for table in TABLES))
    base = args.base_token or os.environ.get(BASE_ENV)
    report: dict[str, Any] = {"staged": staged}
    if not base:
        print("no base given: offline staging only, nothing compared or written")
    else:
        run = lark_runner(base, profile=args.profile, identity=args.identity, lark_cli=args.lark_cli)
        try:
            planned = plan(run, staged)
        except LoadError as exc:
            print(f"ERROR   {exc}")
            return 2
        for table in TABLES:
            info = planned["tables"].get(table)
            if info:
                print(f"  {table}: 待新建 {len(info['create'])}，已存在不动 {info['existing']}（表内现有 {info['rows_before']} 行）")
        for problem in planned["problems"]:
            print(f"PROBLEM {problem}")
        report["plan"] = {t: {k: v for k, v in i.items() if k != "create"} for t, i in planned["tables"].items()}
        if args.write and args.yes:
            try:
                written = write(run, planned, use_records_shape=records_shape(args.lark_cli))
            except LoadError as exc:
                print(f"ERROR   {exc}")
                return 2
            for table, entry in written.items():
                print(f"  {table}: 发送 {entry['sent']}，读回 {entry['read_back']}，缺失 {len(entry['missing'])}，"
                      f"字段不符 {len(entry['mismatched'])}，表内现有 {entry['rows_after']} 行")
            report["written"] = written
            failed = any(e["missing"] or e["mismatched"] for e in written.values())
        else:
            if args.write:
                print("--write ignored: add --yes once the dry run above has been confirmed")
            print("dry run: nothing written")
            failed = False
    if args.report:
        _out(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"report: {args.report}")
    return 1 if base and args.write and args.yes and failed else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Product information matrix: extract, stage and load.")
    sub = parser.add_subparsers(dest="command", required=True)
    ex = sub.add_parser("extract", help="every specification-table row of every published Web manual")
    ex.add_argument("--root", type=Path, required=True, help="checkout whose docs/publish holds the publication")
    ex.add_argument("--dictionary", type=Path, default=DICTIONARY)
    ex.add_argument("--out", type=Path, required=True, help="output file, outside any git work tree")
    ex.set_defaults(func=_extract)
    st = sub.add_parser("stage", help="stage 产品/属性/来源/事实 rows; with a base, plan or write them")
    st.add_argument("--extraction", type=Path, required=True)
    st.add_argument("--root", type=Path, help="checkout holding the 产品分类 snapshot (default: this one)")
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
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
