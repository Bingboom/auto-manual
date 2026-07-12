"""Emit the renderer-neutral manual IR beside an IDML artifact."""
from __future__ import annotations

from pathlib import Path

from tools.idml_rst_extract import bundle_page_order
from tools.manual_ir import build_manual_ir, validate_manual_ir, write_manual_ir
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
) -> Path | None:
    if not bundle_page_order(bundle_root):
        return None
    manual_ir = build_manual_ir(
        root=root,
        bundle_root=bundle_root,
        model=model,
        region=region,
        lang=lang,
        source="prepared-bundle",
        data_root=data_root,
    )
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
