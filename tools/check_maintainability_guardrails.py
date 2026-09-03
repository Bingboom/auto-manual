#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools import check_language_literal_ratchet


# Thresholds are set ~25-100 lines above the current size of files that have
# either grown past ~700 LOC or caused recent maintenance incidents. They are a
# regrowth alarm, not a hard architectural limit. When a file legitimately
# needs to grow past its threshold, raise the threshold in the same PR and
# explain why in the PR description.
HOTSPOT_LINE_THRESHOLDS: dict[str, int] = {
    # +11: the publish asset gate needs one injected entrypoint wrapper
    # (import + 7-line resolver + call site). Bundle-path resolution lives in
    # tools/release_asset_lineage.py, so this is the irreducible minimum.
    "build.py": 761,
    "tools/build_docs.py": 860,
    "tools/process_build_queue.py": 650,
    "tools/validate_spec_master_runtime.py": 880,
    "tools/check_docs_generated.py": 880,
    "tools/word_bundle_docx.py": 740,
    "tools/word_bundle_docx_styles.py": 1080,
    "tools/queue_query.py": 1200,
    "tools/spec_master_rebuild.py": 1150,
    "tools/process_docs/build_review_preview_targets.py": 430,
    "tools/queue_lark_ops.py": 360,
    # Backport / data-sync surface — previously ungoverned and grew unchecked
    # (cloud_doc_backport.py reached 4183 lines outside any threshold). Now capped.
    # cloud_doc_backport.py is set EXACTLY at its current size (no headroom) so the
    # in-progress decomposition can only push it DOWN, never up.
    "tools/cloud_doc_backport.py": 210,
    # G0 split of the former 1400-line CLI conductor: dispatcher / argparse /
    # single-command runners / multi-step orchestration, one-way imports only.
    "tools/cloud_doc_backport_cli.py": 260,
    "tools/cloud_doc_backport_args.py": 470,
    "tools/cloud_doc_backport_commands.py": 550,
    # 880 -> 950: the cross-page-ambiguity plan pass and the per-page gate check
    # (apply-safety fixes) are correctness guards that belong next to the apply
    # loops they protect.
    "tools/cloud_doc_backport_orchestration.py": 950,
    # 880 -> 900: the delete-verify block-presence check (apply-parity accuracy
    # fix) is a correctness guard that belongs next to the verify verdicts.
    "tools/cloud_doc_backport_reports.py": 900,
    "tools/sync_data_runtime.py": 900,
    "tools/content_lint.py": 800,
    "tools/translation_memory.py": 790,
    "tools/source_record_index.py": 500,
    "tools/source_table_sync.py": 500,
    # Web manual presentation surface — source styles are component modules but
    # assemble into one public RTD asset. Keep the orchestration façade, reusable
    # reference component helper, and stylesheet assembler independently pinned.
    "tools/web_presentation.py": 2134,
    "tools/web_reference_components.py": 161,
    # Component migrations add ordered stylesheet modules while the assembler
    # remains intentionally logic-free and stays at its existing line cap.
    "tools/web_stylesheets.py": 40,
    "tools/web_fcc_component.py": 150,
    "tools/web_inbox_component.py": 120,
    "tools/component_specs/fcc.py": 280,
    "tools/component_specs/fcc_adapters.py": 150,
    "tools/component_specs/fcc_html.py": 220,
    "tools/component_specs/inbox.py": 220,
    "tools/component_specs/inbox_adapters.py": 160,
    "tools/component_specs/inbox_html.py": 140,
    # Overview semantics and target geometry are intentionally separate:
    # source/HTML parsing, four adapters, and the versioned target validator
    # may grow independently without rebuilding web_presentation.py.
    "tools/component_specs/overview.py": 370,
    "tools/component_specs/overview_adapters.py": 220,
    "tools/component_specs/overview_html.py": 240,
    "tools/component_specs/overview_instance.py": 430,
    "tools/web_overview_component.py": 190,
    "tools/idml/page_overview.py": 570,
    "tools/word_bundle_html_render.py": 330,
    "tools/word_inbox_component.py": 150,
    # Registered 2026-08-03 at 469 lines with 31 lines of growth headroom.
    "tools/sync_web_composites.py": 500,
    # Registered 2026-08-03 at 434 lines with 31 lines of growth headroom.
    "tools/publish_branch_assembly.py": 465,
    # Registered 2026-08-03 at 347 lines with 33 lines of growth headroom.
    "tools/web_composite_manifest.py": 380,
    # Registered 2026-08-03 at 202 lines with 38 lines of growth headroom.
    "tools/web_composite_presentation.py": 240,
    # Registered 2026-08-03 at 139 lines with 41 lines of growth headroom.
    "tools/web_symbol_components.py": 180,
    # Registered 2026-08-03 at 201 lines with 39 lines of growth headroom.
    "tools/dingtalk_delivery_map.py": 240,
    # Registered 2026-08-03 at 517 lines with 43 lines of growth headroom.
    "tools/delivery_outbox.py": 560,
    "docs/renderers/contracts/web_manual.css": 1905,
    "docs/renderers/contracts/web_app_components.css": 128,
    "docs/renderers/contracts/web_fcc_components.css": 120,
    "docs/renderers/contracts/web_inbox_components.css": 180,
    # Registered 2026-08-03 at 128 lines with 32 lines of growth headroom.
    "docs/renderers/contracts/web_symbols_fcc_components.css": 160,
    # IDML surface — pinned EXACTLY at current size (no headroom) during the
    # componentization plan (reports/idml_componentization/20260705-01): the
    # decomposition into tools/idml/ may only push the façade DOWN, never up.
    # P1 moved params/loaders/primitives/styles/check out (2001 -> 1470);
    # P2 moved the component renderers into tools/idml/components/
    # (1470 -> 1260; extractor +9 for the parity constant); P3 moved the
    # story builders and composed-page assemblers out (1260 -> 647); P4 moved
    # package assembly (spread chain / designmap / zip) out (647 -> 563).
    "tools/export_idml.py": 607,  # back-cover placement policy lives in tools/idml/page_placed.py
    "tools/idml_rst_extract.py": 520,
    "tools/idml/primitives.py": 300,
    "tools/idml/styles.py": 220,
    # loaders 220 -> 290: the spec footnote ①-marker mirror (PDF-renderer
    # parity, test-enforced) lives beside the loaders it decorates.
    "tools/idml/loaders.py": 318,  # +31: localized spec-section/page-title loaders (per-language data pages)
    "tools/idml/components/callout.py": 200,
    # +2 per-language data-page titles/sids (parity); +9 target-declared
    # figure callouts -- one planning call, one lookup, and the skip for a
    # label table now printed over the art (tools/idml/components/prose_image.py).
    "tools/idml/stories.py": 256,
    "tools/idml/pages.py": 500,
    "tools/idml/package.py": 160,
}


@dataclass(frozen=True)
class GuardrailFailure:
    path: str
    actual_lines: int
    max_lines: int


@dataclass(frozen=True)
class TargetScopedIdmlPagePredicate:
    path: str
    line: int
    identifier: str


_TARGET_SCOPED_IDML_PAGE_PREDICATE_RE = re.compile(
    r"\b(is_[a-z][a-z0-9]*\d[a-z0-9]*_[a-z]{2}"
    r"(?:_[a-z]{2})?_[a-z0-9_]*(?:page|owner)[a-z0-9_]*)\b"
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Low-noise maintainability guardrails for known hotspot files."
    )
    parser.add_argument(
        "--repo-root",
        default=Path(__file__).resolve().parents[1],
        type=Path,
        help="Repository root to inspect.",
    )
    return parser.parse_args(argv)


def _count_lines(path: Path) -> int:
    return len(path.read_text(encoding="utf-8", errors="ignore").splitlines())


def collect_hotspot_failures(
    repo_root: Path,
    *,
    thresholds: dict[str, int] | None = None,
) -> list[GuardrailFailure]:
    active_thresholds = thresholds or HOTSPOT_LINE_THRESHOLDS
    failures: list[GuardrailFailure] = []

    for relative_path, max_lines in active_thresholds.items():
        path = repo_root / relative_path
        if not path.exists():
            raise RuntimeError(f"Guardrail target does not exist: {relative_path}")

        actual_lines = _count_lines(path)
        if actual_lines > max_lines:
            failures.append(
                GuardrailFailure(
                    path=relative_path,
                    actual_lines=actual_lines,
                    max_lines=max_lines,
                )
            )

    return failures


def collect_target_scoped_idml_page_predicates(
    repo_root: Path,
) -> list[TargetScopedIdmlPagePredicate]:
    """Reject product/region-named page ownership branches in IDML code."""

    idml_root = repo_root / "tools" / "idml"
    if not idml_root.is_dir():
        return []
    failures: list[TargetScopedIdmlPagePredicate] = []
    for path in sorted(idml_root.rglob("*.py")):
        for line_number, line in enumerate(
            path.read_text(encoding="utf-8", errors="ignore").splitlines(),
            start=1,
        ):
            for match in _TARGET_SCOPED_IDML_PAGE_PREDICATE_RE.finditer(line):
                failures.append(TargetScopedIdmlPagePredicate(
                    path=path.relative_to(repo_root).as_posix(),
                    line=line_number,
                    identifier=match.group(1),
                ))
    return failures


def _render_failure(failure: GuardrailFailure) -> str:
    over_by = failure.actual_lines - failure.max_lines
    return (
        f"[maintainability] {failure.path} has grown to {failure.actual_lines} lines "
        f"(limit {failure.max_lines}, +{over_by})."
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    failures = collect_hotspot_failures(args.repo_root.resolve())
    if failures:
        print("[maintainability] Guardrail failures detected:")
        for failure in failures:
            print(_render_failure(failure))
        return 1

    target_predicates = collect_target_scoped_idml_page_predicates(
        args.repo_root.resolve(),
    )
    if target_predicates:
        print("[maintainability] Target-scoped IDML page predicates detected:")
        for failure in target_predicates:
            print(
                f"[maintainability] {failure.path}:{failure.line}: "
                f"{failure.identifier}"
            )
        return 1

    language_literals = check_language_literal_ratchet.check_repository(args.repo_root.resolve())
    if language_literals.exit_code:
        return language_literals.exit_code

    print(
        f"[maintainability] Guardrails OK for {len(HOTSPOT_LINE_THRESHOLDS)} hotspot files."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
