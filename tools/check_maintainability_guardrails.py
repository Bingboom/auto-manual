#!/usr/bin/env python3

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


# Thresholds are set ~25-100 lines above the current size of files that have
# either grown past ~700 LOC or caused recent maintenance incidents. They are a
# regrowth alarm, not a hard architectural limit. When a file legitimately
# needs to grow past its threshold, raise the threshold in the same PR and
# explain why in the PR description.
HOTSPOT_LINE_THRESHOLDS: dict[str, int] = {
    "build.py": 750,
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
    # IDML surface — pinned EXACTLY at current size (no headroom) during the
    # componentization plan (reports/idml_componentization/20260705-01): the
    # decomposition into tools/idml/ may only push the façade DOWN, never up.
    # P1 moved params/loaders/primitives/styles/check out (2001 -> 1470);
    # P2 moved the component renderers into tools/idml/components/
    # (1470 -> 1260; extractor +9 for the parity constant); P3 moved the
    # story builders and composed-page assemblers out (1260 -> 647); P4 moved
    # package assembly (spread chain / designmap / zip) out (647 -> 563).
    "tools/export_idml.py": 592,  # +7 placed-page hook, +14 TOC hooks (template-parity P2)
    "tools/idml_rst_extract.py": 520,
    "tools/idml/primitives.py": 300,
    "tools/idml/styles.py": 220,
    # loaders 220 -> 290: the spec footnote ①-marker mirror (PDF-renderer
    # parity, test-enforced) lives beside the loaders it decorates.
    "tools/idml/loaders.py": 290,
    "tools/idml/components/callout.py": 200,
    "tools/idml/stories.py": 244,  # +4: flowed H1 -> rounded capsule component (parity)
    "tools/idml/pages.py": 500,
    "tools/idml/package.py": 160,
}


@dataclass(frozen=True)
class GuardrailFailure:
    path: str
    actual_lines: int
    max_lines: int


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

    print(
        f"[maintainability] Guardrails OK for {len(HOTSPOT_LINE_THRESHOLDS)} hotspot files."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
