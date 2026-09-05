"""Emit the renderer-neutral manual IR beside an IDML artifact."""
from __future__ import annotations

from pathlib import Path

from tools.manual_ir import ManualIR, build_manual_ir_from_source, validate_manual_ir, write_manual_ir
from tools.manual_ir.prepared_rst import load_prepared_rst_source
from tools.utils.path_utils import PathSegments


def emit_manual_ir_sidecar(
    *,
    root: Path,
    bundle_root: Path,
    out_dir: Path,
    model: str,
    region: str,
    lang: str,
    data_root: Path,
    category: str | None = None,
    layout_params_csv: Path | None = None,
    layout_param_overlays: tuple[Path, ...] = (),
) -> Path | None:
    prepared = load_prepared_rst_source(
        root=root,
        bundle_root=bundle_root,
        model=model,
        region=region,
        lang=lang,
        source="prepared-bundle",
        category=category,
        data_root=data_root,
        layout_params_csv=layout_params_csv,
        layout_param_overlays=layout_param_overlays,
        missing_ok=True,
    )
    if prepared is None:
        return None
    manual_ir = build_manual_ir_from_source(prepared)
    issues = validate_manual_ir(manual_ir)
    if issues:
        raise RuntimeError("manual IR validation failed: " + "; ".join(issues))
    ir_path = out_dir / PathSegments.MANUAL_IR_JSON
    write_manual_ir(manual_ir, ir_path)
    print(
        f"[export-idml] IR OK: {ir_path} | pages={len(manual_ir.pages)} "
        f"blocks={manual_ir.metadata['block_count']} "
        f"skipped_raw={manual_ir.metadata['skipped_raw']}"
    )
    return ir_path


def write_manual_ir_sidecar(manual_ir: ManualIR, out_dir: Path) -> Path:
    """Write the exact IR object consumed by production IDML."""
    issues = validate_manual_ir(manual_ir)
    if issues:
        raise RuntimeError("manual IR validation failed: " + "; ".join(issues))
    ir_path = out_dir / PathSegments.MANUAL_IR_JSON
    write_manual_ir(manual_ir, ir_path)
    print(
        f"[export-idml] IR OK: {ir_path} | pages={len(manual_ir.pages)} "
        f"blocks={manual_ir.metadata['block_count']} "
        f"skipped_raw={manual_ir.metadata['skipped_raw']}"
    )
    return ir_path
