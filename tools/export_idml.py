"""IDML exporter — route B of the InDesign handoff plan.

Produces an editable .idml package from the same prepared-bundle IR as LaTeX,
so designers can fine-tune pipeline output instead of retouching PDFs.

Usage:
  python tools/export_idml.py --model JE-1000F --region US [--lang en]
      [--data-root data/phase2] [--out docs/_build/.../manual.idml]
  python tools/export_idml.py --check <file.idml>   # structural validation
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

try:
    from tools.script_bootstrap import bootstrap_repo_root
    from tools.idml import check as _check
    from tools.idml import export_cli as _export_cli
    from tools.idml import export_paths as _export_paths
    from tools.idml import flow_idml as _flow_idml
    from tools.idml import loaders as _loaders
    from tools.idml import params as _params
    from tools.idml import prose_flow as _prose_flow
    from tools.idml.writer import IdmlWriter
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root
    from idml import check as _check  # type: ignore
    from idml import export_cli as _export_cli  # type: ignore
    from idml import export_paths as _export_paths  # type: ignore
    from idml import flow_idml as _flow_idml  # type: ignore
    from idml import loaders as _loaders  # type: ignore
    from idml import params as _params  # type: ignore
    from idml import prose_flow as _prose_flow  # type: ignore
    from idml.writer import IdmlWriter  # type: ignore

ROOT = bootstrap_repo_root(__file__, parent_count=1)
from tools.idml import ir_sidecar as _ir_sidecar
from tools.idml import ir_projection as _ir_projection
from tools.idml import reference_export as _reference_export

MIMETYPE = _params.MIMETYPE
IDPKG = _params.IDPKG
MM_TO_PT = _params.MM_TO_PT
load_layout_params = _params.load_layout_params
param_pt = _params.param_pt
brand_cmyk = _params.brand_cmyk
normalize_lang = _loaders.normalize_lang
load_spec_sections = _loaders.load_spec_sections
load_lcd_rows = _loaders.load_lcd_rows
load_spec_annotations = _loaders.load_spec_annotations
load_symbols_rows = _loaders.load_symbols_rows
load_trouble_rows = _loaders.load_trouble_rows

check_idml = _check.check_idml
split_safety_first_page = _prose_flow.split_safety_first_page


def default_bundle_root(model: str, region: str, lang: str) -> Path:
    return _export_paths.default_bundle_root(ROOT, model, region, lang)


def default_output_path(model: str, region: str, lang: str, bundle_root: Path) -> Path:
    return _export_paths.default_output_path(ROOT, model, region, lang, bundle_root)


def _new_production_writer(
    params: dict[str, tuple[str, str]],
    *,
    model: str,
    region: str,
    language: str,
    page_plan: dict | None,
    registered_components: bool = False,
) -> IdmlWriter:
    """Create the production writer with page-plan asset strictness.

    Approved reference composition is a hard rendering contract: falling back
    from a governed component to a generic table would produce a valid IDML
    package with the wrong design. Other production plans keep the historical
    permissive behavior.
    """
    return IdmlWriter(
        params,
        model=model,
        region=region,
        language=language,
        strict_component_assets=(
            (page_plan or {}).get("plan_source") == "approved-reference"
        ),
        native_structure_markers=(
            (page_plan or {}).get("plan_source")
            in {"approved-reference", "target-assembly"}
        ),
        registered_components=registered_components,
    )

# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def _cmd_check(args: argparse.Namespace) -> int:
    return _check.run_check_cli(args.check)


def _cmd_flow(
    args: argparse.Namespace, *, data_root: Any, bundle_root: Path,
    layout_params_csv: Any, layout_param_overlays: Any,
) -> int:
    flow = _flow_idml.write_flow_outputs(
        root=ROOT, model=args.model, region=args.region, lang=args.lang, data_root=data_root,
        bundle_root=bundle_root, layout_params_csv=layout_params_csv,
        layout_param_overlays=layout_param_overlays, build_command=sys.argv)
    _ir_sidecar.emit_manual_ir_sidecar(
        root=ROOT, bundle_root=bundle_root, out_dir=flow.idml.parent,
        model=args.model, region=args.region, lang=args.lang, data_root=data_root,
        category=args.category,
        layout_params_csv=layout_params_csv,
        layout_param_overlays=layout_param_overlays)
    print(f"[export-idml] FLOW OK: {flow.markdown} | FLOW IDML OK: {flow.idml}")
    return 0


def _cmd_reference(
    args: argparse.Namespace, *, data_root: Any, bundle_root: Path,
    layout_params_csv: Any, layout_param_overlays: Any,
) -> int:
    params = load_layout_params(layout_params_csv, layout_param_overlays)
    try:
        manual_ir = _ir_projection.build_same_source_ir(
            root=ROOT, bundle_root=bundle_root, model=args.model, region=args.region,
            lang=args.lang, data_root=data_root, category=args.category,
            layout_params_csv=layout_params_csv,
            layout_param_overlays=layout_param_overlays)
        assembly_plan = Path(args.assembly_plan) if args.assembly_plan else None
        component_target = _ir_projection.resolve_component_target(
            manual_ir, root=ROOT, language=args.lang, assembly_plan=assembly_plan)
        page_plan = _ir_projection.build_reference_page_plan(
            manual_ir, root=ROOT, bundle_root=bundle_root,
            target_assembly_plan=assembly_plan, component_target=component_target)
    except ValueError as exc:
        print(f"[export-idml] ERROR: same-source IDML preparation failed: {exc}")
        _export_cli.dump_prepared_bundle_debug(
            ROOT, bundle_root, model=args.model, region=args.region,
        )
        return 1
    return _reference_export.ReferenceExport(
        root=ROOT, args=args, data_root=data_root,
        layout_params_csv=layout_params_csv, layout_param_overlays=layout_param_overlays,
        bundle_root=bundle_root, params=params, manual_ir=manual_ir,
        component_target=component_target, page_plan=page_plan,
        new_writer=_new_production_writer, default_output_path=default_output_path,
    ).run()


def main() -> int:
    ap = _export_cli.build_parser(__doc__)
    args = ap.parse_args()

    if args.check:
        return _cmd_check(args)
    if not args.model:
        ap.error("the following arguments are required: --model")
    data_root, layout_params_csv, layout_param_overlays = (
        _export_cli.resolve_input_paths(ROOT, args)
    )
    bundle_root = Path(args.bundle_root) if args.bundle_root else (
        default_bundle_root(args.model, args.region, args.lang))
    handler = _cmd_flow if args.mode == "flow" else _cmd_reference
    return handler(
        args, data_root=data_root, bundle_root=bundle_root,
        layout_params_csv=layout_params_csv, layout_param_overlays=layout_param_overlays,
    )

if __name__ == "__main__":
    sys.exit(main())
