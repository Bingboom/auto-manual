#!/usr/bin/env python3
"""Measure structural and visual parity between an approved PDF and InDesign."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ModuleNotFoundError:  # direct script execution
    from script_bootstrap import bootstrap_repo_root


ROOT = bootstrap_repo_root(__file__, parent_count=1)

from tools.idml import pdf_parity_visual as _visual  # noqa: E402
from tools.idml.pdf_parity_contract import (  # noqa: E402
    APPROVED_PLAN_SCHEMA,
    _approved_contract_report,
    _idml_editability_gate,
    _parse_page_sizes,
    _parse_pdfinfo,
    _pdf_info,
    _pdf_output_contract,
    _preflight_gate,
    _read_reference_plan,
    _reference_plan_path,
    _sha256,
    _structure_report,
)
from tools.idml.pdf_parity_visual import (  # noqa: E402
    DEFAULT_DISPLAY_ICC,
    _occupancy_report,
    _page_text_counts,
    _render_page,
    _render_settings,
    _selected_pages,
    _visual_metrics,
)
from tools.manual_ir import read_manual_ir  # noqa: E402


__all__ = [
    "APPROVED_PLAN_SCHEMA",
    "DEFAULT_DISPLAY_ICC",
    "_approved_contract_report",
    "_idml_editability_gate",
    "_occupancy_report",
    "_page_text_counts",
    "_parse_page_sizes",
    "_parse_pdfinfo",
    "_pdf_info",
    "_pdf_output_contract",
    "_preflight_gate",
    "_read_reference_plan",
    "_reference_plan_path",
    "_render_page",
    "_render_settings",
    "_selected_pages",
    "_sha256",
    "_structure_report",
    "_visual_metrics",
    "_visual_report",
    "build_report",
    "main",
]


def _visual_report(
    reference_pdf: Path,
    indesign_pdf: Path,
    pages: list[int],
    *,
    expected_page_count: int,
    settings: dict[str, Any],
) -> dict[str, Any]:
    """Preserve the legacy patch point while delegating visual comparison."""
    return _visual._visual_report(
        reference_pdf,
        indesign_pdf,
        pages,
        expected_page_count=expected_page_count,
        settings=settings,
        render_page=_render_page,
    )


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    reference_pdf = Path(args.latex_pdf)
    indesign_pdf = Path(args.indesign_pdf)
    manual_ir_path = Path(args.manual_ir)
    manual_ir_model = read_manual_ir(manual_ir_path)
    manual_ir = manual_ir_model.to_dict()
    plan_path = _reference_plan_path(args, manual_ir_path)
    plan = _read_reference_plan(plan_path, manual_ir_model)
    reference = _pdf_info(reference_pdf)
    indesign = _pdf_info(indesign_pdf)
    approved_contract = _approved_contract_report(
        plan_path=plan_path,
        plan=plan,
        manual_ir=manual_ir,
        reference=reference,
    )
    structure = _structure_report(
        reference,
        indesign,
        plan=plan,
        fallback_tolerance=args.page_size_tolerance,
    )
    expected_page_count = structure["expected_page_count"]
    preflight = _preflight_gate(
        json.loads(Path(args.preflight).read_text(encoding="utf-8")),
        indesign_pdf=indesign_pdf,
        expected_page_count=expected_page_count,
        plan=plan,
    )
    pages = _selected_pages(
        args.pages,
        min(reference["page_count"], indesign["page_count"]),
    )
    settings = _render_settings(args, plan)
    visual = _visual_report(
        reference_pdf,
        indesign_pdf,
        pages,
        expected_page_count=expected_page_count,
        settings=settings,
    )
    occupancy = _occupancy_report(
        _page_text_counts(reference_pdf), _page_text_counts(indesign_pdf),
    )
    output_contract = _pdf_output_contract(indesign_pdf, indesign, plan)
    idml_path = Path(args.idml) if args.idml else None
    editability = _idml_editability_gate(idml_path, plan)
    artifacts = {"reference_pdf": reference, "indesign_pdf": indesign}
    for key in ("idml", "indd"):
        value = getattr(args, key, None)
        if value:
            path = Path(value)
            artifacts[key] = {"path": str(path.resolve()), "sha256": _sha256(path)}
    accepted = all((
        approved_contract["pass"],
        structure["pass"],
        preflight["pass"],
        occupancy["pass"],
        output_contract["pass"],
        editability["pass"],
        visual["pass"],
    ))
    return {
        "schema_version": "approved-reference-parity/v2",
        "source_identity": {
            "content_sha256": manual_ir.get("content_sha256"),
            "bundle_sha256": manual_ir.get("bundle_sha256"),
            "snapshot_sha256": manual_ir.get("snapshot_sha256"),
            "style_contract_sha256": manual_ir.get("style_contract_sha256"),
            "layout_params_sha256": manual_ir.get("layout_params_sha256"),
        },
        "approved_reference_contract": approved_contract,
        "artifacts": artifacts,
        "structure": structure,
        "indesign_preflight": preflight,
        "pdf_output_contract": output_contract,
        "idml_editability": editability,
        "content_occupancy": occupancy,
        "visual_delta": visual,
        "accepted": accepted,
    }


def _markdown(report: dict[str, Any]) -> str:
    visual = report["visual_delta"]
    ranked = sorted(
        visual["pages"],
        key=lambda item: item.get("rgb_mad", -1),
        reverse=True,
    )[:10]
    rows = "\n".join(
        f"| {item['page']} | {item.get('rgb_mad', 'n/a')} | "
        f"{item.get('changed_pixel_ratio', 'n/a')} | "
        f"{item.get('pass', False)} |"
        for item in ranked
    )
    failed = ", ".join(str(page) for page in visual["failed_pages"]) or "none"
    return (
        "# Approved PDF / InDesign Parity\n\n"
        f"- Accepted: **{report['accepted']}**\n"
        f"- Approved reference contract: "
        f"{report['approved_reference_contract']['pass']}\n"
        f"- Page count and size: {report['structure']['pass']}\n"
        f"- InDesign preflight: {report['indesign_preflight']['pass']}\n"
        f"- PDF/X output contract: {report['pdf_output_contract']['pass']}\n"
        f"- Native IDML editability: {report['idml_editability']['pass']}\n"
        f"- Content occupancy: {report['content_occupancy']['pass']}\n"
        f"- Visual hard gate: {visual['pass']}\n"
        f"- Compared pages: {visual['compared_page_count']} / "
        f"{visual['expected_page_count']}\n"
        f"- Failed pages: {failed}\n"
        f"- Mean RGB MAD: {visual['mean_rgb_mad']}\n"
        f"- Mean changed-pixel ratio: {visual['mean_changed_pixel_ratio']}\n\n"
        "## Largest visual deltas\n\n"
        "| Page | RGB MAD | Changed pixel ratio | Pass |\n"
        "| ---: | ---: | ---: | :---: |\n"
        f"{rows}\n"
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    # Retain the historical flag name so existing operator commands keep working.
    parser.add_argument("--latex-pdf", required=True, help="approved reference PDF")
    parser.add_argument("--indesign-pdf", required=True)
    parser.add_argument("--preflight", required=True)
    parser.add_argument("--manual-ir", required=True)
    parser.add_argument("--reference-layout-plan")
    parser.add_argument("--idml")
    parser.add_argument("--indd")
    parser.add_argument("--pages", default="all")
    parser.add_argument("--dpi", type=int)
    parser.add_argument("--raster-width", type=int)
    parser.add_argument("--raster-height", type=int)
    parser.add_argument("--display-icc")
    parser.add_argument("--gaussian-blur", type=float)
    parser.add_argument("--max-rgb-mad", type=float)
    parser.add_argument("--max-changed-pixel-ratio", type=float)
    parser.add_argument("--changed-channel-threshold", type=int)
    parser.add_argument("--page-size-tolerance", type=float, default=0.02)
    parser.add_argument("--out", required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    report = build_report(args)
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )
    output.with_suffix(".md").write_text(_markdown(report), encoding="utf-8")
    print(f"[idml-pdf-parity] {'OK' if report['accepted'] else 'FAIL'}: {output}")
    return 0 if report["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
