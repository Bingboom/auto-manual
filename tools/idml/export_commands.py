"""Flow modes and final result reporting for the IDML exporter.

Rendering and file writers are injected by the CLI facade; this module owns
only their command-specific order and the existing result messages.
"""
from __future__ import annotations

from argparse import Namespace
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tools.idml.design_handoff import HandoffOutputs
    from tools.idml.flow_idml import FlowOutputs
    from tools.idml.reference_story_flow import ReferenceStoryEmitter
    from tools.idml.writer import IdmlWriter


def run_flow(
    args: Namespace, *, root: Path, data_root: Path, bundle_root: Path,
    layout_params_csv: Path, layout_param_overlays: tuple[Path, ...],
    build_command: list[str], flow_writer: Callable[..., FlowOutputs],
    emit_sidecar: Callable[..., Path | None],
) -> int:
    flow = flow_writer(
        root=root, model=args.model, region=args.region, lang=args.lang, data_root=data_root,
        bundle_root=bundle_root, layout_params_csv=layout_params_csv,
        layout_param_overlays=layout_param_overlays, build_command=build_command)
    emit_sidecar(
        root=root, bundle_root=bundle_root, out_dir=flow.idml.parent,
        model=args.model, region=args.region, lang=args.lang, data_root=data_root,
        category=args.category,
        layout_params_csv=layout_params_csv,
        layout_param_overlays=layout_param_overlays)
    print(f"[export-idml] FLOW OK: {flow.markdown} | FLOW IDML OK: {flow.idml}")
    return 0


def write_combined_outputs(
    args: Namespace, *, root: Path, data_root: Path, bundle_root: Path,
    layout_params_csv: Path, layout_param_overlays: tuple[Path, ...],
    build_command: list[str], flow_writer: Callable[..., FlowOutputs],
    out: Path, write_handoff: Callable[..., HandoffOutputs],
) -> None:
    flow = flow_writer(
        root=root, model=args.model, region=args.region, lang=args.lang, data_root=data_root,
        bundle_root=bundle_root, layout_params_csv=layout_params_csv,
        layout_param_overlays=layout_param_overlays, build_command=build_command)
    print(f"[export-idml] FLOW OK: {flow.markdown} | FLOW IDML OK: {flow.idml}")
    handoff = write_handoff(
        root=root, model=args.model, region=args.region, lang=args.lang,
        data_root=data_root, bundle_root=bundle_root,
        production_idml=out, flow=flow, build_command=build_command)
    print(f"[export-idml] HANDOFF OK: {handoff.root}")


def report_production(
    out: Path, issues: list[str], w: IdmlWriter, story_emitter: ReferenceStoryEmitter,
    sections: list[dict[str, Any]], lcd_rows: list[dict[str, Any]], trouble_rows: list[tuple[str, str]],
    *, prose_pages: int, skipped_raw: int,
) -> int:
    n_rows = sum(len(s["rows"]) for s in sections)
    print(f"[export-idml] {'OK' if not issues else 'WROTE WITH ISSUES'}: {out}")
    story_emitter.report_spans()
    print(f"[export-idml] stories={len(w.stories)} spreads={len(w.spreads)} "
          f"prose pages={prose_pages} skipped raw blocks={skipped_raw} | "
          f"spec rows={n_rows} lcd rows={len(lcd_rows)} trouble rows={len(trouble_rows)}")
    return 1 if issues else 0
