"""Draft a target-assembly plan skeleton from a built Manual IR.

The target-assembly JSON is the one artifact of a new product line that had no
scaffold: JBP-2000B_US's plan is ~600 hand-written lines, and the acceptance
review of that round measured it as the single slowest step of standing up a
line. Everything mechanical in it, though, is derivable: page roles come from
``classify_page_role``, each role maps to exactly one composition type, pages
group into compositions by (language, composition type) adjacency, and start
pages are sequential. Only the *judgment* fields — ``composition_data`` variant
selections, ``flow_split`` decisions, and any packing that merges compositions
onto one physical page — need a human.

This module emits that mechanical skeleton and names the judgment explicitly:

* the JSON draft is loadable as-is (``normalize_target_assembly_plan`` is run
  in-process and its verdict reported), with ``status: candidate`` and
  ``production_eligible: false`` hard-coded — a scaffold never claims approval;
* every judgment left to the author lands in a sidecar ``*.todos.md`` next to
  the draft, keyed by source page, so nothing hides inside the JSON.

Usage (after ``build.py idml`` has produced the IR)::

    python -m tools.idml.target_assembly_scaffold \\
        --ir docs/_build/<MODEL>/<REGION>/idml/manual.ir.json \\
        --physical-pages 28 \\
        --out docs/renderers/contracts/target_assembly/<target>_v1_candidate.json

The role→composition mapping below is the shared compact-page vocabulary that
``target_assembly_render.SPECIAL_COMPOSITION_TYPES`` dispatches plus the
standard story-flow types. A role outside the table becomes a ``TODO_<role>``
composition type: the draft then fails normalization on exactly those pages,
which is the report of what still needs a decision — not a silent guess.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from tools.manual_ir import ManualIR
from tools.manual_ir.serialize import read_manual_ir

from .page_roles import PageRole, classify_page_role
from .target_assembly_plan import (
    SCHEMA_VERSION,
    TargetAssemblyPlanError,
    normalize_target_assembly_plan,
)

# One composition type per page role. Multiple roles mapping to the same type
# express the shared physical pages (safety+symbols, fcc+inbox+overview, ...)
# exactly as the JBP-2000B_US reference plan groups them.
ROLE_COMPOSITION: dict[PageRole, str] = {
    PageRole.COVER: "front_cover",
    PageRole.PREFACE: "preface",
    PageRole.TOC: "toc",
    PageRole.SAFETY: "safety_symbols",
    PageRole.SYMBOLS: "safety_symbols",
    PageRole.FCC: "fcc_inbox_overview",
    PageRole.INBOX: "fcc_inbox_overview",
    PageRole.PRODUCT_OVERVIEW: "fcc_inbox_overview",
    PageRole.LCD: "lcd_operations",
    PageRole.OPERATION_GUIDE: "lcd_operations",
    PageRole.CONNECTIONS: "connections",
    PageRole.TROUBLESHOOTING_DATA: "troubleshooting",
    PageRole.CHARGING: "charging",
    PageRole.STORAGE_MAINTENANCE: "storage_specifications",
    PageRole.SPEC: "storage_specifications",
    PageRole.WARRANTY: "warranty",
    PageRole.REGULATORY_COMPLIANCE: "regulatory_compliance",
    PageRole.BACK_COVER: "back_cover",
}

# Compositions that appear once per book rather than once per language keep the
# bare type name as their id, matching the reference plan's naming.
BARE_COMPOSITION_IDS = frozenset({"front_cover", "preface", "toc", "back_cover"})

# Judgment the author must supply per composition type, phrased as the exact
# fields the validator knows about. The scaffold never invents values for
# these; it only names them in the sidecar.
JUDGMENT_HINTS: dict[str, str] = {
    "charging": (
        "composition_data.charging = {image_role, h2_suffix_pill_indices} — "
        "语义图角色与胶囊标题索引（validator: target_assembly_plan.py 的 charging 分支）"
    ),
    "connections": (
        "composition_data.connections = {image_role, layout_variant} — "
        "并考虑 flow_split（尾部溢出到哪个后续 composition）"
    ),
    "lcd_operations": (
        "composition_data.lcd —— 批准的 LCD profile 选择"
    ),
    "storage_specifications": (
        "composition_data.specifications = {layout_variant: compact, section_groups}"
    ),
    "troubleshooting": (
        "composition_data.troubleshooting —— 行高/变体选择，并检查是否需要 flow_split"
    ),
    "warranty": (
        "composition_data.warranty = {layout_variant} — 词汇表见 "
        "target_assembly_plan.WARRANTY_LAYOUT_VARIANTS"
    ),
}


def _reference_pdf_stub(
    reference_pdf: Path | None,
    physical_pages: int,
    todos: list[str],
) -> dict[str, Any]:
    """Real hashes when the shipped PDF is at hand; loud TODOs when it is not."""
    if reference_pdf is None:
        todos.append(
            "reference_pdf: 未提供出货书 PDF —— file_name/sha256/byte_size 为占位，"
            "拿到 PDF 后用 --reference-pdf 重跑或手工回填"
        )
        return {
            "file_name": "TODO-shipped-reference.pdf",
            "sha256": "TODO",
            "byte_size": 0,
            "page_count": physical_pages,
        }
    data = reference_pdf.read_bytes()
    return {
        "file_name": reference_pdf.name,
        "sha256": hashlib.sha256(data).hexdigest(),
        "byte_size": len(data),
        "page_count": physical_pages,
    }


def scaffold_plan(
    ir: ManualIR,
    *,
    physical_pages: int,
    reference_pdf: Path | None = None,
) -> tuple[dict[str, Any], list[str]]:
    """Return (draft payload, todo list) for the IR's page sequence."""
    todos: list[str] = []
    pages: list[dict[str, Any]] = []
    order: list[str] = []          # composition ids in first-appearance order
    seen: set[str] = set()
    previous_cid: str | None = None

    for page in ir.pages:
        role = classify_page_role(Path(page.source_ref))
        ctype = ROLE_COMPOSITION.get(role)
        if ctype is None:
            ctype = f"TODO_{role.value}"
            todos.append(
                f"{page.source_ref}: 角色 {role.value} 没有脚手架映射 —— "
                "人工选定 composition_type（该页会阻塞 normalize，属预期）"
            )
        cid = ctype if ctype in BARE_COMPOSITION_IDS else f"{page.language}_{ctype}"
        if cid != previous_cid and cid in seen:
            # The same composition recurring non-adjacently would break the
            # renderer's contiguous dispatch; keep the draft loadable and say so.
            todos.append(
                f"{page.source_ref}: composition {cid} 非相邻复现，"
                f"已改名 {cid}_2 —— 请人工决定页序或合并"
            )
            cid = f"{cid}_2"
        if cid not in seen:
            seen.add(cid)
            order.append(cid)
        previous_cid = cid
        pages.append(
            {
                "source_ref": page.source_ref,
                "language": page.language,
                "page_role": role.value,
                "composition_id": cid,
                "composition_type": ctype,
                "start_page": 0,   # filled below once the order is final
                "page_count": 1,
            }
        )

    start_by_cid = {cid: index + 1 for index, cid in enumerate(order)}
    for entry in pages:
        entry["start_page"] = start_by_cid[entry["composition_id"]]

    if len(order) != physical_pages:
        todos.append(
            f"页数预算不符：脚手架得到 {len(order)} 个 composition，"
            f"--physical-pages 说 {physical_pages} —— 需要人工打包"
            "（合并 composition 或调整 page_count），出货书页序是判断依据"
        )

    for ctype in sorted({entry["composition_type"] for entry in pages}):
        hint = JUDGMENT_HINTS.get(ctype)
        if hint:
            todos.append(f"[{ctype}] {hint}")

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": "candidate",
        "production_eligible": False,
        "target": {
            "model": ir.model,
            "region": ir.region,
            "languages": _languages(ir),
        },
        "reference_pdf": _reference_pdf_stub(reference_pdf, physical_pages, todos),
        "physical_page_count": physical_pages,
        "pages": pages,
    }
    return payload, todos


def _languages(ir: ManualIR) -> list[str]:
    languages: list[str] = []
    for page in ir.pages:
        if page.language in {"", "cover", "toc"} or page.language in languages:
            continue
        languages.append(page.language)
    return languages


def _self_check(payload: dict[str, Any], ir: ManualIR, out: Path) -> list[str]:
    """Run the real validator on the draft; return its blocking issues."""
    try:
        normalize_target_assembly_plan(payload, ir, source_path=out)
    except TargetAssemblyPlanError as exc:
        return str(exc).split("; ")
    return []


def _todo_sidecar(out: Path, todos: list[str], blocking: list[str]) -> Path:
    sidecar = out.with_suffix(".todos.md")
    lines = [
        f"# {out.name} — 脚手架遗留判断",
        "",
        "脚手架只生成机械字段。以下每一条都需要人工裁决后写回 JSON；",
        "写完删除本文件。",
        "",
    ]
    lines += [f"- [ ] {item}" for item in todos] or ["- （无 —— 机械字段即完整）"]
    if blocking:
        lines += ["", "## normalize 当前阻塞项", ""]
        lines += [f"- {item}" for item in blocking]
    else:
        lines += ["", "normalize 自校验：**通过**（判断字段为纯增量，可直接构建预览）。"]
    sidecar.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return sidecar


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Draft a target-assembly plan skeleton from a built Manual IR.",
    )
    parser.add_argument("--ir", required=True, type=Path,
                        help="manual.ir.json produced by build.py idml")
    parser.add_argument("--physical-pages", required=True, type=int,
                        help="shipped book's physical page budget")
    parser.add_argument("--out", required=True, type=Path,
                        help="draft plan path (a .todos.md sidecar lands next to it)")
    parser.add_argument("--reference-pdf", type=Path, default=None,
                        help="shipped reference PDF, to pin file_name/sha256/bytes")
    parser.add_argument("--force", action="store_true",
                        help="overwrite an existing draft")
    args = parser.parse_args(argv)

    if args.out.exists() and not args.force:
        parser.error(f"{args.out} already exists; pass --force to overwrite")

    ir = read_manual_ir(args.ir)
    payload, todos = scaffold_plan(
        ir,
        physical_pages=args.physical_pages,
        reference_pdf=args.reference_pdf,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    blocking = _self_check(payload, ir, args.out)
    sidecar = _todo_sidecar(args.out, todos, blocking)

    print(f"[scaffold] draft: {args.out} ({len(payload['pages'])} pages, "
          f"{len({p['composition_id'] for p in payload['pages']})} compositions)")
    print(f"[scaffold] todos: {sidecar} ({len(todos)} item(s))")
    if blocking:
        print(f"[scaffold] normalize: {len(blocking)} blocking issue(s) — "
              "expected when TODO roles remain; see the sidecar")
    else:
        print("[scaffold] normalize: PASS — the draft loads as-is")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
